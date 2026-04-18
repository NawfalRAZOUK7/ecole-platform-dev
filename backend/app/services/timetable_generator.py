"""Timetable constraint management and synchronous generation service."""

from __future__ import annotations

import time as time_module
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, time, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.business_metrics import timetable_generation
from app.core.dependencies import AuthContext, verify_school_boundary
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.permissions import ADM
from app.core.unit_of_work import UnitOfWork
from app.models.erp import TimetableConstraint, TimetableGenerationJob
from app.repositories.timetable_generation import TimetableGenerationRepository
from app.schemas.timetable_generation import (
    GeneratedTimetableSlotResponse,
    TimetableConstraintInput,
    TimetableConstraintResponse,
    TimetableConstraintSetRequest,
    TimetableGenerationApplyResponse,
    TimetableGenerationConflictResponse,
    TimetableGenerationJobResponse,
    TimetableGenerationPreviewResponse,
    TimetableGenerateRequest,
)
from app.services.audit import AuditService

_ALLOWED_CONSTRAINT_TYPES = {
    "teacher_unavailable",
    "room_capacity",
    "max_consecutive_classes",
    "max_hours_per_day",
    "subject_hours_per_week",
    "no_consecutive_same_subject",
}


@dataclass(frozen=True)
class _TimeSlot:
    day_of_week: int
    slot_index: int
    start_time: time
    end_time: time


@dataclass(frozen=True)
class _RequirementUnit:
    requirement_id: str
    class_id: uuid.UUID
    class_name: str
    subject: str
    teacher_ids: tuple[uuid.UUID, ...]
    preferred_room: str | None
    class_size: int
    max_consecutive_classes: int | None
    max_hours_per_day: int | None
    no_consecutive_same_subject: bool


@dataclass
class _PlacedUnit:
    unit: _RequirementUnit
    time_slot: _TimeSlot
    teacher_id: uuid.UUID
    room: str | None


class TimetableGeneratorService:
    """Manages timetable generation constraints and preview/apply jobs."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = TimetableGenerationRepository(db)
        self.audit = AuditService(db)

    def _ensure_admin(self, auth: AuthContext) -> None:
        if auth.role != ADM:
            raise NotFoundError(
                "Timetable generation not found", error_code="ERR-ERP-404"
            )

    def _constraint_to_response(self, constraint: TimetableConstraint) -> dict:
        return TimetableConstraintResponse(
            id=str(constraint.id),
            school_id=str(constraint.school_id),
            academic_year_id=str(constraint.academic_year_id),
            constraint_type=constraint.constraint_type,
            entity_id=str(constraint.entity_id) if constraint.entity_id else None,
            params=constraint.params or {},
            created_at=constraint.created_at.isoformat(),
            updated_at=constraint.updated_at.isoformat()
            if constraint.updated_at
            else None,
        ).model_dump()

    def _job_to_response(self, job: TimetableGenerationJob) -> dict:
        return TimetableGenerationJobResponse(
            id=str(job.id),
            school_id=str(job.school_id),
            academic_year_id=str(job.academic_year_id),
            status=job.status,
            result_slot_count=job.result_slot_count,
            conflicts_found=job.conflicts_found,
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            error_message=job.error_message,
        ).model_dump()

    def _conflict_response(
        self,
        *,
        detail: str,
        class_id: uuid.UUID | None = None,
        class_name: str | None = None,
        subject: str | None = None,
    ) -> dict:
        return TimetableGenerationConflictResponse(
            class_id=str(class_id) if class_id else None,
            class_name=class_name,
            subject=subject,
            detail=detail,
        ).model_dump()

    def _parse_uuid(self, value: object | None) -> uuid.UUID | None:
        if value in (None, ""):
            return None
        if isinstance(value, uuid.UUID):
            return value
        try:
            return uuid.UUID(str(value))
        except (TypeError, ValueError) as exc:
            raise ValidationError(
                "Invalid UUID in constraint payload",
                error_code="ERR-ERP-422",
            ) from exc

    def _parse_time(self, value: object | None) -> time:
        if isinstance(value, time):
            return value
        if not isinstance(value, str):
            raise ValidationError(
                "Constraint time values must use HH:MM format",
                error_code="ERR-ERP-422",
            )
        try:
            hour_text, minute_text = value.split(":", 1)
            return time(hour=int(hour_text), minute=int(minute_text))
        except (TypeError, ValueError) as exc:
            raise ValidationError(
                "Constraint time values must use HH:MM format",
                error_code="ERR-ERP-422",
            ) from exc

    def _validate_constraint_input(self, constraint: TimetableConstraintInput) -> None:
        params = constraint.params or {}
        if constraint.constraint_type not in _ALLOWED_CONSTRAINT_TYPES:
            raise ValidationError(
                "Unsupported timetable constraint type",
                error_code="ERR-ERP-422",
            )
        if constraint.constraint_type == "teacher_unavailable":
            teacher_id = constraint.entity_id or self._parse_uuid(
                params.get("teacher_id")
            )
            day = params.get("day")
            start_value = params.get("start")
            end_value = params.get("end")
            if (
                teacher_id is None
                or day is None
                or start_value is None
                or end_value is None
            ):
                raise ValidationError(
                    "teacher_unavailable requires teacher_id, day, start, and end",
                    error_code="ERR-ERP-422",
                )
            if int(day) < 0 or int(day) > 6:
                raise ValidationError(
                    "Constraint day must be between 0 and 6",
                    error_code="ERR-ERP-422",
                )
            if self._parse_time(start_value) >= self._parse_time(end_value):
                raise ValidationError(
                    "Constraint end time must be after start time",
                    error_code="ERR-ERP-422",
                )
            return
        if constraint.constraint_type == "room_capacity":
            room = str(params.get("room") or "").strip()
            max_students = int(params.get("max_students") or 0)
            if not room or max_students <= 0:
                raise ValidationError(
                    "room_capacity requires room and positive max_students",
                    error_code="ERR-ERP-422",
                )
            return
        if constraint.constraint_type == "max_consecutive_classes":
            max_consecutive = int(params.get("max") or 0)
            if max_consecutive <= 0:
                raise ValidationError(
                    "max_consecutive_classes requires positive max",
                    error_code="ERR-ERP-422",
                )
            return
        if constraint.constraint_type == "max_hours_per_day":
            class_id = constraint.entity_id or self._parse_uuid(params.get("class_id"))
            max_hours = int(params.get("max_hours") or 0)
            if class_id is None or max_hours <= 0:
                raise ValidationError(
                    "max_hours_per_day requires class_id and positive max_hours",
                    error_code="ERR-ERP-422",
                )
            return
        if constraint.constraint_type == "subject_hours_per_week":
            class_id = constraint.entity_id or self._parse_uuid(params.get("class_id"))
            subject = str(params.get("subject") or "").strip()
            hours = int(params.get("hours") or 0)
            if class_id is None or not subject or hours <= 0:
                raise ValidationError(
                    "subject_hours_per_week requires class_id, subject, and positive hours",
                    error_code="ERR-ERP-422",
                )
            return
        if constraint.constraint_type == "no_consecutive_same_subject":
            class_id = constraint.entity_id or self._parse_uuid(params.get("class_id"))
            if class_id is None:
                raise ValidationError(
                    "no_consecutive_same_subject requires class_id",
                    error_code="ERR-ERP-422",
                )

    async def _load_academic_year(
        self,
        *,
        academic_year_id: uuid.UUID,
        auth: AuthContext,
    ):
        academic_year = await self.repo.get_academic_year(academic_year_id)
        if academic_year is None:
            raise NotFoundError("Academic year not found", error_code="ERR-ERP-404")
        verify_school_boundary(academic_year.school_id, auth)
        return academic_year

    def _build_available_time_slots(self) -> list[_TimeSlot]:
        slots: list[_TimeSlot] = []
        for day_of_week in range(5):
            slot_index = 0
            for hour in range(8, 17):
                slots.append(
                    _TimeSlot(
                        day_of_week=day_of_week,
                        slot_index=slot_index,
                        start_time=time(hour=hour, minute=0),
                        end_time=time(hour=hour + 1, minute=0),
                    )
                )
                slot_index += 1
        return slots

    def _room_names_from_constraints(
        self, constraints: list[TimetableConstraint]
    ) -> list[str]:
        names: list[str] = []
        seen: set[str] = set()
        for constraint in constraints:
            room = str((constraint.params or {}).get("room") or "").strip()
            if room and room not in seen:
                names.append(room)
                seen.add(room)
        return names

    def _parse_solver_settings(
        self,
        *,
        constraints: list[TimetableConstraint],
        available_time_slots: list[_TimeSlot],
    ) -> tuple[
        set[tuple[uuid.UUID, int, int]],
        dict[str, int],
        int | None,
        dict[uuid.UUID, int],
        set[uuid.UUID],
    ]:
        teacher_unavailable: set[tuple[uuid.UUID, int, int]] = set()
        room_capacities: dict[str, int] = {}
        max_consecutive_classes: int | None = None
        max_hours_per_day: dict[uuid.UUID, int] = {}
        no_consecutive_same_subject: set[uuid.UUID] = set()

        for constraint in constraints:
            params = constraint.params or {}
            if constraint.constraint_type == "teacher_unavailable":
                teacher_id = constraint.entity_id or self._parse_uuid(
                    params.get("teacher_id")
                )
                day = int(params["day"])
                start_time_value = self._parse_time(params["start"])
                end_time_value = self._parse_time(params["end"])
                for slot in available_time_slots:
                    if slot.day_of_week != day:
                        continue
                    if (
                        slot.start_time < end_time_value
                        and slot.end_time > start_time_value
                    ):
                        teacher_unavailable.add((teacher_id, day, slot.slot_index))
            elif constraint.constraint_type == "room_capacity":
                room = str(params["room"]).strip()
                room_capacities[room] = int(params["max_students"])
            elif constraint.constraint_type == "max_consecutive_classes":
                max_consecutive_classes = int(params["max"])
            elif constraint.constraint_type == "max_hours_per_day":
                class_id = constraint.entity_id or self._parse_uuid(
                    params.get("class_id")
                )
                max_hours_per_day[class_id] = int(params["max_hours"])
            elif constraint.constraint_type == "no_consecutive_same_subject":
                class_id = constraint.entity_id or self._parse_uuid(
                    params.get("class_id")
                )
                no_consecutive_same_subject.add(class_id)

        return (
            teacher_unavailable,
            room_capacities,
            max_consecutive_classes,
            max_hours_per_day,
            no_consecutive_same_subject,
        )

    def _build_requirement_units(
        self,
        *,
        academic_year_id: uuid.UUID,
        constraints: list[TimetableConstraint],
        class_map: dict[uuid.UUID, object],
        class_sizes: dict[uuid.UUID, int],
        class_teachers: dict[uuid.UUID, list[uuid.UUID]],
        subject_teacher_map: dict[tuple[uuid.UUID, str], list[uuid.UUID]],
        max_consecutive_classes: int | None,
        max_hours_per_day: dict[uuid.UUID, int],
        no_consecutive_same_subject: set[uuid.UUID],
        conflicts: list[dict],
    ) -> list[_RequirementUnit]:
        units: list[_RequirementUnit] = []
        for constraint in constraints:
            if constraint.constraint_type != "subject_hours_per_week":
                continue
            params = constraint.params or {}
            class_id = constraint.entity_id or self._parse_uuid(params.get("class_id"))
            subject = str(params.get("subject") or "").strip()
            hours = int(params.get("hours") or 0)
            explicit_teacher_id = self._parse_uuid(params.get("teacher_id"))
            preferred_room = str(params.get("room") or "").strip() or None
            class_room = class_map.get(class_id)
            if class_room is None:
                conflicts.append(
                    self._conflict_response(
                        class_id=class_id,
                        subject=subject or None,
                        detail="Constraint references a class outside this academic year",
                    )
                )
                continue
            teacher_ids: list[uuid.UUID] = []
            if explicit_teacher_id is not None:
                teacher_ids = [explicit_teacher_id]
            elif subject_teacher_map.get((class_id, subject)):
                teacher_ids = list(subject_teacher_map[(class_id, subject)])
            else:
                teacher_ids = list(class_teachers.get(class_id, []))
            for index in range(hours):
                units.append(
                    _RequirementUnit(
                        requirement_id=(
                            f"{academic_year_id}:{class_id}:{subject}:{index}"
                        ),
                        class_id=class_id,
                        class_name=class_room.name,
                        subject=subject,
                        teacher_ids=tuple(teacher_ids),
                        preferred_room=preferred_room,
                        class_size=class_sizes.get(class_id, 0),
                        max_consecutive_classes=max_consecutive_classes,
                        max_hours_per_day=max_hours_per_day.get(class_id),
                        no_consecutive_same_subject=class_id
                        in no_consecutive_same_subject,
                    )
                )
        units.sort(
            key=lambda unit: (
                len(unit.teacher_ids) if unit.teacher_ids else 999,
                unit.class_name.lower(),
                unit.subject.lower(),
            )
        )
        return units

    def _candidate_rooms(
        self,
        *,
        unit: _RequirementUnit,
        room_names: list[str],
        room_capacities: dict[str, int],
    ) -> list[str | None]:
        if unit.preferred_room:
            return [unit.preferred_room]
        if not room_names:
            return [None]
        candidates = [
            room
            for room in room_names
            if room_capacities.get(room, unit.class_size or 10_000) >= unit.class_size
        ]
        return candidates

    def _ordered_time_slots(
        self,
        *,
        unit: _RequirementUnit,
        available_time_slots: list[_TimeSlot],
        class_day_counts: dict[tuple[uuid.UUID, int], int],
        class_subject_day_counts: dict[tuple[uuid.UUID, int, str], int],
    ) -> list[_TimeSlot]:
        return sorted(
            available_time_slots,
            key=lambda slot: (
                class_day_counts[(unit.class_id, slot.day_of_week)],
                class_subject_day_counts[
                    (unit.class_id, slot.day_of_week, unit.subject)
                ],
                slot.day_of_week,
                slot.slot_index,
            ),
        )

    def _candidate_from_placement(self, placement: _PlacedUnit) -> dict:
        return {
            "time_slot": placement.time_slot,
            "teacher_id": placement.teacher_id,
            "room": placement.room,
        }

    def _would_exceed_max_consecutive_classes(
        self,
        *,
        class_id: uuid.UUID,
        day_of_week: int,
        slot_index: int,
        max_consecutive_classes: int | None,
        class_busy: dict[tuple[uuid.UUID, int, int], _PlacedUnit],
    ) -> bool:
        if max_consecutive_classes is None or max_consecutive_classes <= 0:
            return False

        run_length = 1
        previous_index = slot_index - 1
        while (class_id, day_of_week, previous_index) in class_busy:
            run_length += 1
            previous_index -= 1

        next_index = slot_index + 1
        while (class_id, day_of_week, next_index) in class_busy:
            run_length += 1
            next_index += 1

        return run_length > max_consecutive_classes

    def _place(
        self,
        *,
        unit: _RequirementUnit,
        candidate: dict,
        placements: dict[str, _PlacedUnit],
        class_busy: dict[tuple[uuid.UUID, int, int], _PlacedUnit],
        teacher_busy: dict[tuple[uuid.UUID, int, int], _PlacedUnit],
        room_busy: dict[tuple[str, int, int], _PlacedUnit],
        class_day_counts: dict[tuple[uuid.UUID, int], int],
        class_subject_day_counts: dict[tuple[uuid.UUID, int, str], int],
    ) -> _PlacedUnit:
        placement = _PlacedUnit(
            unit=unit,
            time_slot=candidate["time_slot"],
            teacher_id=candidate["teacher_id"],
            room=candidate["room"],
        )
        placements[unit.requirement_id] = placement
        class_busy[
            (
                unit.class_id,
                placement.time_slot.day_of_week,
                placement.time_slot.slot_index,
            )
        ] = placement
        teacher_busy[
            (
                placement.teacher_id,
                placement.time_slot.day_of_week,
                placement.time_slot.slot_index,
            )
        ] = placement
        if placement.room is not None:
            room_busy[
                (
                    placement.room,
                    placement.time_slot.day_of_week,
                    placement.time_slot.slot_index,
                )
            ] = placement
        class_day_counts[(unit.class_id, placement.time_slot.day_of_week)] += 1
        class_subject_day_counts[
            (unit.class_id, placement.time_slot.day_of_week, unit.subject)
        ] += 1
        return placement

    def _unplace(
        self,
        *,
        placement: _PlacedUnit,
        placements: dict[str, _PlacedUnit],
        class_busy: dict[tuple[uuid.UUID, int, int], _PlacedUnit],
        teacher_busy: dict[tuple[uuid.UUID, int, int], _PlacedUnit],
        room_busy: dict[tuple[str, int, int], _PlacedUnit],
        class_day_counts: dict[tuple[uuid.UUID, int], int],
        class_subject_day_counts: dict[tuple[uuid.UUID, int, str], int],
    ) -> None:
        placements.pop(placement.unit.requirement_id, None)
        class_busy.pop(
            (
                placement.unit.class_id,
                placement.time_slot.day_of_week,
                placement.time_slot.slot_index,
            ),
            None,
        )
        teacher_busy.pop(
            (
                placement.teacher_id,
                placement.time_slot.day_of_week,
                placement.time_slot.slot_index,
            ),
            None,
        )
        if placement.room is not None:
            room_busy.pop(
                (
                    placement.room,
                    placement.time_slot.day_of_week,
                    placement.time_slot.slot_index,
                ),
                None,
            )
        class_day_counts[
            (placement.unit.class_id, placement.time_slot.day_of_week)
        ] -= 1
        class_subject_day_counts[
            (
                placement.unit.class_id,
                placement.time_slot.day_of_week,
                placement.unit.subject,
            )
        ] -= 1

    def _find_candidate(
        self,
        *,
        unit: _RequirementUnit,
        available_time_slots: list[_TimeSlot],
        room_names: list[str],
        room_capacities: dict[str, int],
        teacher_unavailable: set[tuple[uuid.UUID, int, int]],
        placements: dict[str, _PlacedUnit],
        class_busy: dict[tuple[uuid.UUID, int, int], _PlacedUnit],
        teacher_busy: dict[tuple[uuid.UUID, int, int], _PlacedUnit],
        room_busy: dict[tuple[str, int, int], _PlacedUnit],
        class_day_counts: dict[tuple[uuid.UUID, int], int],
        class_subject_day_counts: dict[tuple[uuid.UUID, int, str], int],
        collect_single_blocker_candidates: bool = True,
    ) -> tuple[dict | None, list[tuple[dict, _PlacedUnit]]]:
        if not unit.teacher_ids:
            return None, []

        suggestions: list[tuple[dict, _PlacedUnit]] = []
        candidate_rooms = self._candidate_rooms(
            unit=unit,
            room_names=room_names,
            room_capacities=room_capacities,
        )
        if not candidate_rooms:
            return None, []

        for teacher_id in unit.teacher_ids:
            for slot in self._ordered_time_slots(
                unit=unit,
                available_time_slots=available_time_slots,
                class_day_counts=class_day_counts,
                class_subject_day_counts=class_subject_day_counts,
            ):
                if (
                    teacher_id,
                    slot.day_of_week,
                    slot.slot_index,
                ) in teacher_unavailable:
                    continue
                if (
                    unit.max_hours_per_day is not None
                    and class_day_counts[(unit.class_id, slot.day_of_week)]
                    >= unit.max_hours_per_day
                ):
                    continue
                if self._would_exceed_max_consecutive_classes(
                    class_id=unit.class_id,
                    day_of_week=slot.day_of_week,
                    slot_index=slot.slot_index,
                    max_consecutive_classes=unit.max_consecutive_classes,
                    class_busy=class_busy,
                ):
                    continue
                if unit.no_consecutive_same_subject:
                    previous = class_busy.get(
                        (unit.class_id, slot.day_of_week, slot.slot_index - 1)
                    )
                    following = class_busy.get(
                        (unit.class_id, slot.day_of_week, slot.slot_index + 1)
                    )
                    if previous and previous.unit.subject == unit.subject:
                        continue
                    if following and following.unit.subject == unit.subject:
                        continue
                for room in candidate_rooms:
                    blockers: list[_PlacedUnit] = []
                    for placed in (
                        class_busy.get(
                            (unit.class_id, slot.day_of_week, slot.slot_index)
                        ),
                        teacher_busy.get(
                            (teacher_id, slot.day_of_week, slot.slot_index)
                        ),
                        room_busy.get((room, slot.day_of_week, slot.slot_index))
                        if room is not None
                        else None,
                    ):
                        if placed is None:
                            continue
                        if all(
                            existing.unit.requirement_id != placed.unit.requirement_id
                            for existing in blockers
                        ):
                            blockers.append(placed)
                    candidate = {
                        "time_slot": slot,
                        "teacher_id": teacher_id,
                        "room": room,
                    }
                    if not blockers:
                        return candidate, suggestions
                    if collect_single_blocker_candidates and len(blockers) == 1:
                        suggestions.append((candidate, blockers[0]))
        return None, suggestions

    def _run_solver(
        self,
        *,
        academic_year,
        constraints: list[TimetableConstraint],
        class_map: dict[uuid.UUID, object],
        class_sizes: dict[uuid.UUID, int],
        class_teachers: dict[uuid.UUID, list[uuid.UUID]],
        subject_teacher_map: dict[tuple[uuid.UUID, str], list[uuid.UUID]],
        room_names: list[str],
    ) -> dict:
        available_time_slots = self._build_available_time_slots()
        (
            teacher_unavailable,
            room_capacities,
            max_consecutive_classes,
            max_hours_per_day,
            no_consecutive_same_subject,
        ) = self._parse_solver_settings(
            constraints=constraints,
            available_time_slots=available_time_slots,
        )

        conflicts: list[dict] = []
        units = self._build_requirement_units(
            academic_year_id=academic_year.id,
            constraints=constraints,
            class_map=class_map,
            class_sizes=class_sizes,
            class_teachers=class_teachers,
            subject_teacher_map=subject_teacher_map,
            max_consecutive_classes=max_consecutive_classes,
            max_hours_per_day=max_hours_per_day,
            no_consecutive_same_subject=no_consecutive_same_subject,
            conflicts=conflicts,
        )

        placements: dict[str, _PlacedUnit] = {}
        class_busy: dict[tuple[uuid.UUID, int, int], _PlacedUnit] = {}
        teacher_busy: dict[tuple[uuid.UUID, int, int], _PlacedUnit] = {}
        room_busy: dict[tuple[str, int, int], _PlacedUnit] = {}
        class_day_counts: dict[tuple[uuid.UUID, int], int] = defaultdict(int)
        class_subject_day_counts: dict[tuple[uuid.UUID, int, str], int] = defaultdict(
            int
        )
        unresolved: list[tuple[_RequirementUnit, list[tuple[dict, _PlacedUnit]]]] = []
        deadline = time_module.monotonic() + 25.0

        for unit in units:
            if time_module.monotonic() > deadline:
                conflicts.append(
                    self._conflict_response(
                        detail="Generation time limit reached before all requirements could be assigned",
                    )
                )
                unresolved.append((unit, []))
                unresolved.extend(
                    (remaining, []) for remaining in units[units.index(unit) + 1 :]
                )
                break
            candidate, suggestions = self._find_candidate(
                unit=unit,
                available_time_slots=available_time_slots,
                room_names=room_names,
                room_capacities=room_capacities,
                teacher_unavailable=teacher_unavailable,
                placements=placements,
                class_busy=class_busy,
                teacher_busy=teacher_busy,
                room_busy=room_busy,
                class_day_counts=class_day_counts,
                class_subject_day_counts=class_subject_day_counts,
            )
            if candidate is not None:
                self._place(
                    unit=unit,
                    candidate=candidate,
                    placements=placements,
                    class_busy=class_busy,
                    teacher_busy=teacher_busy,
                    room_busy=room_busy,
                    class_day_counts=class_day_counts,
                    class_subject_day_counts=class_subject_day_counts,
                )
            else:
                unresolved.append((unit, suggestions[:12]))

        for unit, suggestions in unresolved:
            resolved = False
            if unit.requirement_id in placements:
                continue
            for candidate, blocker in suggestions:
                self._unplace(
                    placement=blocker,
                    placements=placements,
                    class_busy=class_busy,
                    teacher_busy=teacher_busy,
                    room_busy=room_busy,
                    class_day_counts=class_day_counts,
                    class_subject_day_counts=class_subject_day_counts,
                )
                placed_current = self._place(
                    unit=unit,
                    candidate=candidate,
                    placements=placements,
                    class_busy=class_busy,
                    teacher_busy=teacher_busy,
                    room_busy=room_busy,
                    class_day_counts=class_day_counts,
                    class_subject_day_counts=class_subject_day_counts,
                )
                alternative, _ = self._find_candidate(
                    unit=blocker.unit,
                    available_time_slots=available_time_slots,
                    room_names=room_names,
                    room_capacities=room_capacities,
                    teacher_unavailable=teacher_unavailable,
                    placements=placements,
                    class_busy=class_busy,
                    teacher_busy=teacher_busy,
                    room_busy=room_busy,
                    class_day_counts=class_day_counts,
                    class_subject_day_counts=class_subject_day_counts,
                    collect_single_blocker_candidates=False,
                )
                if alternative is not None:
                    self._place(
                        unit=blocker.unit,
                        candidate=alternative,
                        placements=placements,
                        class_busy=class_busy,
                        teacher_busy=teacher_busy,
                        room_busy=room_busy,
                        class_day_counts=class_day_counts,
                        class_subject_day_counts=class_subject_day_counts,
                    )
                    resolved = True
                    break
                self._unplace(
                    placement=placed_current,
                    placements=placements,
                    class_busy=class_busy,
                    teacher_busy=teacher_busy,
                    room_busy=room_busy,
                    class_day_counts=class_day_counts,
                    class_subject_day_counts=class_subject_day_counts,
                )
                self._place(
                    unit=blocker.unit,
                    candidate=self._candidate_from_placement(blocker),
                    placements=placements,
                    class_busy=class_busy,
                    teacher_busy=teacher_busy,
                    room_busy=room_busy,
                    class_day_counts=class_day_counts,
                    class_subject_day_counts=class_subject_day_counts,
                )
            if not resolved and unit.requirement_id not in placements:
                detail = "No valid slot found"
                if not unit.teacher_ids:
                    detail = "No candidate teacher available for this class subject requirement"
                conflicts.append(
                    self._conflict_response(
                        class_id=unit.class_id,
                        class_name=unit.class_name,
                        subject=unit.subject,
                        detail=detail,
                    )
                )

        preview_slots = [
            GeneratedTimetableSlotResponse(
                class_id=str(placement.unit.class_id),
                class_name=placement.unit.class_name,
                academic_year_id=str(academic_year.id),
                day_of_week=placement.time_slot.day_of_week,
                start_time=placement.time_slot.start_time.strftime("%H:%M"),
                end_time=placement.time_slot.end_time.strftime("%H:%M"),
                subject=placement.unit.subject,
                teacher_id=str(placement.teacher_id),
                room=placement.room,
                is_recurring=True,
                effective_from=academic_year.date_start.isoformat(),
                effective_until=academic_year.date_end.isoformat(),
            ).model_dump()
            for placement in sorted(
                placements.values(),
                key=lambda item: (
                    item.unit.class_name.lower(),
                    item.time_slot.day_of_week,
                    item.time_slot.slot_index,
                    item.unit.subject.lower(),
                ),
            )
        ]

        return {"slots": preview_slots, "conflicts": conflicts}

    async def set_constraints(
        self,
        *,
        body: TimetableConstraintSetRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> list[dict]:
        self._ensure_admin(auth)
        academic_year = await self._load_academic_year(
            academic_year_id=body.academic_year_id,
            auth=auth,
        )
        for constraint in body.constraints:
            self._validate_constraint_input(constraint)

        async with UnitOfWork(self.db) as uow:
            repo = TimetableGenerationRepository(uow.session)
            audit = AuditService(uow.session)
            await repo.delete_constraints(
                school_id=auth.school_id,
                academic_year_id=body.academic_year_id,
            )
            created = [
                await repo.create_constraint(
                    school_id=auth.school_id,
                    academic_year_id=body.academic_year_id,
                    constraint_type=item.constraint_type,
                    entity_id=item.entity_id,
                    params=item.params,
                )
                for item in body.constraints
            ]
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="timetable.constraints.set",
                target_type="academic_year",
                target_id=academic_year.id,
                outcome="success",
                entity_after={
                    "academic_year_id": str(academic_year.id),
                    "constraint_count": len(created),
                },
                ip_address=ip_address,
            )
            await uow.commit()
        return [self._constraint_to_response(item) for item in created]

    async def list_constraints(
        self,
        *,
        academic_year_id: uuid.UUID,
        auth: AuthContext,
    ) -> list[dict]:
        self._ensure_admin(auth)
        await self._load_academic_year(academic_year_id=academic_year_id, auth=auth)
        constraints = await self.repo.list_constraints(
            school_id=auth.school_id,
            academic_year_id=academic_year_id,
        )
        return [self._constraint_to_response(item) for item in constraints]

    async def generate(
        self,
        *,
        body: TimetableGenerateRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        self._ensure_admin(auth)
        academic_year = await self._load_academic_year(
            academic_year_id=body.academic_year_id,
            auth=auth,
        )
        constraints = await self.repo.list_constraints(
            school_id=auth.school_id,
            academic_year_id=body.academic_year_id,
        )
        duration_started_at = time_module.perf_counter()
        constraint_snapshot = {
            "constraints": [self._constraint_to_response(item) for item in constraints]
        }
        started_at = datetime.now(timezone.utc)

        async with UnitOfWork(self.db) as uow:
            repo = TimetableGenerationRepository(uow.session)
            job = await repo.create_job(
                school_id=auth.school_id,
                academic_year_id=body.academic_year_id,
                status="running",
                constraints_snapshot=constraint_snapshot,
                started_at=started_at,
            )
            await uow.commit()

        try:
            classes = await self.repo.list_classes_for_academic_year(
                school_id=auth.school_id,
                academic_year_id=body.academic_year_id,
            )
            class_map = {class_room.id: class_room for class_room in classes}
            class_sizes = await self.repo.get_class_student_counts(
                school_id=auth.school_id,
                academic_year_id=body.academic_year_id,
            )
            class_teachers: dict[uuid.UUID, list[uuid.UUID]] = defaultdict(list)
            for (
                class_id,
                teacher_id,
            ) in await self.repo.list_teacher_assignments_for_academic_year(
                school_id=auth.school_id,
                academic_year_id=body.academic_year_id,
            ):
                if teacher_id not in class_teachers[class_id]:
                    class_teachers[class_id].append(teacher_id)
            subject_teacher_map: dict[tuple[uuid.UUID, str], list[uuid.UUID]] = (
                defaultdict(list)
            )
            for (
                class_id,
                subject,
                teacher_id,
            ) in await self.repo.list_existing_subject_teacher_pairs(
                school_id=auth.school_id,
                academic_year_id=body.academic_year_id,
            ):
                key = (class_id, subject)
                if teacher_id not in subject_teacher_map[key]:
                    subject_teacher_map[key].append(teacher_id)
            room_names = await self.repo.list_existing_room_names(
                school_id=auth.school_id,
                academic_year_id=body.academic_year_id,
            )
            for room in self._room_names_from_constraints(constraints):
                if room not in room_names:
                    room_names.append(room)
            result_payload = self._run_solver(
                academic_year=academic_year,
                constraints=constraints,
                class_map=class_map,
                class_sizes=class_sizes,
                class_teachers=class_teachers,
                subject_teacher_map=subject_teacher_map,
                room_names=room_names,
            )
            completed_at = datetime.now(timezone.utc)
            async with UnitOfWork(self.db) as uow:
                repo = TimetableGenerationRepository(uow.session)
                audit = AuditService(uow.session)
                stored_job = await repo.get_job(job.id)
                stored_job.status = "completed"
                stored_job.result_payload = result_payload
                stored_job.result_slot_count = len(result_payload["slots"])
                stored_job.conflicts_found = len(result_payload["conflicts"])
                stored_job.completed_at = completed_at
                stored_job.error_message = None
                await repo.save_job(stored_job)
                await audit.log_event(
                    school_id=auth.school_id,
                    actor_id=auth.user_id,
                    action_type="timetable.generate",
                    target_type="timetable_generation_job",
                    target_id=stored_job.id,
                    outcome="success",
                    entity_after={
                        "academic_year_id": str(body.academic_year_id),
                        "result_slot_count": stored_job.result_slot_count,
                        "conflicts_found": stored_job.conflicts_found,
                    },
                    ip_address=ip_address,
                )
                await uow.commit()
            return self._job_to_response(stored_job)
        except Exception as exc:
            completed_at = datetime.now(timezone.utc)
            async with UnitOfWork(self.db) as uow:
                repo = TimetableGenerationRepository(uow.session)
                stored_job = await repo.get_job(job.id)
                stored_job.status = "failed"
                stored_job.error_message = str(exc)
                stored_job.completed_at = completed_at
                await repo.save_job(stored_job)
                await uow.commit()
            raise
        finally:
            timetable_generation.labels(
                school_id=str(auth.school_id),
            ).observe(time_module.perf_counter() - duration_started_at)

    async def get_job_status(
        self,
        *,
        job_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict:
        self._ensure_admin(auth)
        job = await self.repo.get_job(job_id)
        if job is None:
            raise NotFoundError(
                "Timetable generation job not found", error_code="ERR-ERP-404"
            )
        verify_school_boundary(job.school_id, auth)
        return self._job_to_response(job)

    async def preview_generated(
        self,
        *,
        job_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict:
        self._ensure_admin(auth)
        job = await self.repo.get_job(job_id)
        if job is None:
            raise NotFoundError(
                "Timetable generation job not found", error_code="ERR-ERP-404"
            )
        verify_school_boundary(job.school_id, auth)
        payload = job.result_payload or {}
        return TimetableGenerationPreviewResponse(
            job=TimetableGenerationJobResponse(**self._job_to_response(job)),
            slots=[
                GeneratedTimetableSlotResponse(**item)
                for item in payload.get("slots", [])
            ],
            conflicts=[
                TimetableGenerationConflictResponse(**item)
                for item in payload.get("conflicts", [])
            ],
        ).model_dump()

    async def apply_generated(
        self,
        *,
        job_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        self._ensure_admin(auth)
        job = await self.repo.get_job(job_id)
        if job is None:
            raise NotFoundError(
                "Timetable generation job not found", error_code="ERR-ERP-404"
            )
        verify_school_boundary(job.school_id, auth)
        if job.status == "applied":
            raise ConflictError(
                "Timetable generation job has already been applied",
                error_code="ERR-ERP-409",
            )
        if job.status != "completed":
            raise ConflictError(
                "Timetable generation job is not ready to apply",
                error_code="ERR-ERP-409",
            )

        payload = job.result_payload or {}
        preview_slots = payload.get("slots", [])

        async with UnitOfWork(self.db) as uow:
            repo = TimetableGenerationRepository(uow.session)
            audit = AuditService(uow.session)
            stored_job = await repo.get_job(job_id)
            await repo.delete_timetable_slots_for_academic_year(
                school_id=stored_job.school_id,
                academic_year_id=stored_job.academic_year_id,
            )
            for slot in preview_slots:
                await repo.create_timetable_slot(
                    school_id=stored_job.school_id,
                    class_id=uuid.UUID(slot["class_id"]),
                    academic_year_id=stored_job.academic_year_id,
                    day_of_week=slot["day_of_week"],
                    start_time=self._parse_time(slot["start_time"]),
                    end_time=self._parse_time(slot["end_time"]),
                    subject=slot["subject"],
                    teacher_id=uuid.UUID(slot["teacher_id"]),
                    room=slot.get("room"),
                    is_recurring=slot.get("is_recurring", True),
                    effective_from=self._parse_date(slot.get("effective_from")),
                    effective_until=self._parse_date(slot.get("effective_until")),
                )
            stored_job.status = "applied"
            stored_job.completed_at = datetime.now(timezone.utc)
            await repo.save_job(stored_job)
            await audit.log_event(
                school_id=stored_job.school_id,
                actor_id=auth.user_id,
                action_type="timetable.apply_generated",
                target_type="timetable_generation_job",
                target_id=stored_job.id,
                outcome="success",
                entity_after={
                    "job_id": str(stored_job.id),
                    "created_count": len(preview_slots),
                },
                ip_address=ip_address,
            )
            await uow.commit()

        return TimetableGenerationApplyResponse(
            job_id=str(job_id),
            status="applied",
            created_count=len(preview_slots),
        ).model_dump()

    def _parse_date(self, value: object | None):
        if value in (None, ""):
            return None
        if hasattr(value, "isoformat") and not isinstance(value, str):
            return value
        try:
            year_text, month_text, day_text = str(value).split("-", 2)
            return datetime(
                year=int(year_text),
                month=int(month_text),
                day=int(day_text),
                tzinfo=timezone.utc,
            ).date()
        except (TypeError, ValueError) as exc:
            raise ValidationError(
                "Generated timetable date payload is invalid",
                error_code="ERR-ERP-422",
            ) from exc
