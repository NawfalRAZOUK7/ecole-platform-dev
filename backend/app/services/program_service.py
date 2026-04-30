"""Academic program management & student academic history (G49).

Service layer for:
- Program CRUD (school-scoped catalog of filières / tracks).
- Program assignment to an enrollment (soft-replace pattern + event log).
- Read helpers: program history (event log) + academic timeline (enrollment-
  joined view) + current program convenience.

Design references:
- Hybrid L2 + L3 versioning shim — Academic Program Management & Student
  Academic History.
- Soft-replace transfer flow: marks the previous active enrollment as
  TRANSFERRED, creates a new active enrollment with the new program, and
  always writes a ``ProgramAssignmentEvent`` row in the same transaction.
- Append-only enforcement: the service never UPDATEs / DELETEs
  ``program_assignment_events`` rows; a Postgres trigger gives defence in
  depth.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    AuthContext,
    get_parent_child_ids,
    verify_parent_child_ownership,
    verify_school_boundary,
)
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.permissions import ADM, DIR, PAR, STD, SUP, SYS, TCH
from app.core.unit_of_work import UnitOfWork
from app.models.erp import (
    AcademicYear,
    Class,
    Enrollment,
    EnrollmentStatus,
    Period,
    Program,
    ProgramAssignmentEvent,
    ProgramAssignmentReason,
    ProgramEquivalence,
    ProgramVersion,
)
from app.repositories.erp import ERPRepository
from app.services.audit import AuditService


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _short(value: object | None) -> str | None:
    return str(value) if value is not None else None


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------
class ProgramService:
    """Business logic for programs and program-assignment history."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = ERPRepository(db)
        self.audit = AuditService(db)

    # ------------------------------------------------------------------
    # Serializers
    # ------------------------------------------------------------------
    def _program_to_response(self, program: Program) -> dict:
        return {
            "id": str(program.id),
            "school_id": str(program.school_id),
            "code": program.code,
            "name": program.name,
            "level": program.level,
            "description": program.description,
            "is_active": program.is_active,
            "version_label": program.version_label,
            "effective_from": (
                program.effective_from.isoformat()
                if program.effective_from is not None
                else None
            ),
            "created_at": program.created_at.isoformat(),
            "updated_at": (
                program.updated_at.isoformat()
                if program.updated_at is not None
                else None
            ),
        }

    def _event_to_response(self, event: ProgramAssignmentEvent) -> dict:
        return {
            "id": str(event.id),
            "school_id": str(event.school_id),
            "student_id": str(event.student_id),
            "academic_year_id": str(event.academic_year_id),
            "period_id": _short(event.period_id),
            "from_program_id": _short(event.from_program_id),
            "to_program_id": str(event.to_program_id),
            "from_enrollment_id": _short(event.from_enrollment_id),
            "to_enrollment_id": _short(event.to_enrollment_id),
            "reason_code": event.reason_code,
            "reason_note": event.reason_note,
            "actor_user_id": _short(event.actor_user_id),
            "occurred_at": event.occurred_at.isoformat(),
        }

    def _program_summary(self, program: Program | None) -> dict | None:
        if program is None:
            return None
        return {
            "id": str(program.id),
            "code": program.code,
            "name": program.name,
            "version_label": program.version_label,
        }

    # ------------------------------------------------------------------
    # Program catalog — CRUD
    # ------------------------------------------------------------------
    async def list_programs(
        self,
        *,
        auth: AuthContext,
        active_only: bool = True,
    ) -> list[dict]:
        """List programs in the caller's school. ``active_only`` defaults to True."""
        stmt = select(Program).where(Program.school_id == auth.school_id)
        if active_only:
            stmt = stmt.where(Program.is_active.is_(True))
        stmt = stmt.order_by(Program.level.asc().nulls_last(), Program.code.asc())
        result = await self.db.execute(stmt)
        return [self._program_to_response(p) for p in result.scalars().all()]

    async def get_program(
        self,
        *,
        program_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict:
        program = await self._fetch_program(program_id)
        if program is None:
            raise NotFoundError("Program not found", error_code="ERR-ERP-404")
        verify_school_boundary(program.school_id, auth)
        return self._program_to_response(program)

    async def create_program(
        self,
        *,
        code: str,
        name: str,
        level: str | None,
        description: str | None,
        version_label: str,
        effective_from,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        # Idempotency: if a program with the same code already exists for the
        # school, return it (mirrors enrollment create behaviour).
        existing = await self._fetch_program_by_code(
            school_id=auth.school_id,
            code=code.strip().upper().replace(" ", "-"),
        )
        if existing is not None:
            return self._program_to_response(existing)

        async with UnitOfWork(self.db) as uow:
            program = Program(
                school_id=auth.school_id,
                code=code,
                name=name,
                level=level,
                description=description,
                version_label=version_label or "1.0",
                effective_from=effective_from,
                is_active=True,
            )
            uow.session.add(program)
            await uow.session.flush()

            initial_version = ProgramVersion(
                school_id=program.school_id,
                program_id=program.id,
                version_label=program.version_label,
                description=description,
                effective_from=program.effective_from,
                is_active=True,
            )
            uow.session.add(initial_version)
            await uow.session.flush()

            audit = AuditService(uow.session)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="PROGRAM_CREATED",
                outcome="success",
                target_type="program",
                target_id=program.id,
                entity_after={
                    "code": program.code,
                    "name": program.name,
                    "version_label": program.version_label,
                },
                ip_address=ip_address,
            )
            await uow.commit()
        return self._program_to_response(program)

    async def update_program(
        self,
        *,
        program_id: uuid.UUID,
        name: str | None,
        level: str | None,
        description: str | None,
        is_active: bool | None,
        version_label: str | None,
        effective_from,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        program = await self._fetch_program(program_id)
        if program is None:
            raise NotFoundError("Program not found", error_code="ERR-ERP-404")
        verify_school_boundary(program.school_id, auth)

        before = {
            "name": program.name,
            "level": program.level,
            "is_active": program.is_active,
            "version_label": program.version_label,
        }

        async with UnitOfWork(self.db) as uow:
            attached = await uow.session.get(Program, program.id)
            if attached is None:
                raise NotFoundError("Program not found", error_code="ERR-ERP-404")
            if name is not None:
                attached.name = name
            if level is not None:
                attached.level = level
            if description is not None:
                attached.description = description
            if is_active is not None:
                attached.is_active = is_active
            if version_label is not None:
                attached.version_label = version_label
            if effective_from is not None:
                attached.effective_from = effective_from
            attached.updated_at = _utc_now()
            await uow.session.flush()

            audit = AuditService(uow.session)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="PROGRAM_UPDATED",
                outcome="success",
                target_type="program",
                target_id=attached.id,
                entity_before=before,
                entity_after={
                    "name": attached.name,
                    "level": attached.level,
                    "is_active": attached.is_active,
                    "version_label": attached.version_label,
                },
                ip_address=ip_address,
            )
            await uow.commit()
            program = attached
        return self._program_to_response(program)

    # ------------------------------------------------------------------
    # Program versions (Phase 3.1)
    # ------------------------------------------------------------------
    def _version_to_response(self, version: ProgramVersion) -> dict:
        return {
            "id": str(version.id),
            "school_id": str(version.school_id),
            "program_id": str(version.program_id),
            "version_label": version.version_label,
            "description": version.description,
            "effective_from": (
                version.effective_from.isoformat()
                if version.effective_from is not None
                else None
            ),
            "retired_at": (
                version.retired_at.isoformat()
                if version.retired_at is not None
                else None
            ),
            "is_active": version.is_active,
            "created_at": version.created_at.isoformat(),
            "updated_at": (
                version.updated_at.isoformat()
                if version.updated_at is not None
                else None
            ),
        }

    async def list_program_versions(
        self,
        *,
        program_id: uuid.UUID,
        auth: AuthContext,
    ) -> list[dict]:
        program = await self._fetch_program(program_id)
        if program is None:
            raise NotFoundError("Program not found", error_code="ERR-ERP-404")
        verify_school_boundary(program.school_id, auth)

        result = await self.db.execute(
            select(ProgramVersion)
            .where(ProgramVersion.program_id == program_id)
            .order_by(
                ProgramVersion.is_active.desc(),
                ProgramVersion.effective_from.desc().nulls_last(),
                ProgramVersion.created_at.desc(),
            )
        )
        return [self._version_to_response(v) for v in result.scalars().all()]

    async def create_program_version(
        self,
        *,
        program_id: uuid.UUID,
        version_label: str,
        description: str | None,
        effective_from,
        is_active: bool,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        program = await self._fetch_program(program_id)
        if program is None:
            raise NotFoundError("Program not found", error_code="ERR-ERP-404")
        verify_school_boundary(program.school_id, auth)

        # Idempotency on (program_id, version_label) — return the existing
        # row instead of raising 409, mirroring the program-create idiom.
        result = await self.db.execute(
            select(ProgramVersion).where(
                ProgramVersion.program_id == program_id,
                ProgramVersion.version_label == version_label.strip(),
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            return self._version_to_response(existing)

        async with UnitOfWork(self.db) as uow:
            version = ProgramVersion(
                school_id=program.school_id,
                program_id=program.id,
                version_label=version_label,
                description=description,
                effective_from=effective_from,
                is_active=is_active,
            )
            uow.session.add(version)
            await uow.session.flush()

            audit = AuditService(uow.session)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="PROGRAM_VERSION_CREATED",
                outcome="success",
                target_type="program_version",
                target_id=version.id,
                entity_after={
                    "program_id": str(program.id),
                    "version_label": version.version_label,
                    "is_active": version.is_active,
                },
                ip_address=ip_address,
            )
            await uow.commit()
        return self._version_to_response(version)

    async def update_program_version(
        self,
        *,
        version_id: uuid.UUID,
        description: str | None,
        effective_from,
        retired_at,
        is_active: bool | None,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        result = await self.db.execute(
            select(ProgramVersion).where(ProgramVersion.id == version_id)
        )
        version = result.scalar_one_or_none()
        if version is None:
            raise NotFoundError(
                "Program version not found", error_code="ERR-ERP-404"
            )
        verify_school_boundary(version.school_id, auth)

        before = {
            "description": version.description,
            "effective_from": (
                version.effective_from.isoformat()
                if version.effective_from is not None
                else None
            ),
            "retired_at": (
                version.retired_at.isoformat()
                if version.retired_at is not None
                else None
            ),
            "is_active": version.is_active,
        }

        async with UnitOfWork(self.db) as uow:
            attached = await uow.session.get(ProgramVersion, version.id)
            if attached is None:
                raise NotFoundError(
                    "Program version not found", error_code="ERR-ERP-404"
                )
            if description is not None:
                attached.description = description
            if effective_from is not None:
                attached.effective_from = effective_from
            if retired_at is not None:
                attached.retired_at = retired_at
            if is_active is not None:
                attached.is_active = is_active
            attached.updated_at = _utc_now()
            await uow.session.flush()

            audit = AuditService(uow.session)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="PROGRAM_VERSION_UPDATED",
                outcome="success",
                target_type="program_version",
                target_id=attached.id,
                entity_before=before,
                entity_after={
                    "description": attached.description,
                    "is_active": attached.is_active,
                },
                ip_address=ip_address,
            )
            await uow.commit()
            version = attached
        return self._version_to_response(version)

    # ------------------------------------------------------------------
    # Program equivalences (Phase 3.2)
    # ------------------------------------------------------------------
    def _equivalence_to_response(self, eq: ProgramEquivalence) -> dict:
        return {
            "id": str(eq.id),
            "school_id": str(eq.school_id),
            "from_program_id": str(eq.from_program_id),
            "to_program_id": str(eq.to_program_id),
            "kind": eq.kind,
            "note": eq.note,
            "ratified_at": (
                eq.ratified_at.isoformat()
                if eq.ratified_at is not None
                else None
            ),
            "ratified_by": (
                str(eq.ratified_by)
                if eq.ratified_by is not None
                else None
            ),
            "created_at": eq.created_at.isoformat(),
            "updated_at": (
                eq.updated_at.isoformat()
                if eq.updated_at is not None
                else None
            ),
        }

    async def list_program_equivalences(
        self,
        *,
        auth: AuthContext,
        program_id: uuid.UUID | None = None,
    ) -> list[dict]:
        stmt = select(ProgramEquivalence).where(
            ProgramEquivalence.school_id == auth.school_id
        )
        if program_id is not None:
            from sqlalchemy import or_

            stmt = stmt.where(
                or_(
                    ProgramEquivalence.from_program_id == program_id,
                    ProgramEquivalence.to_program_id == program_id,
                )
            )
        stmt = stmt.order_by(desc(ProgramEquivalence.created_at))
        result = await self.db.execute(stmt)
        return [self._equivalence_to_response(eq) for eq in result.scalars().all()]

    async def create_program_equivalence(
        self,
        *,
        from_program_id: uuid.UUID,
        to_program_id: uuid.UUID,
        kind: str,
        note: str | None,
        ratified_at,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        if from_program_id == to_program_id:
            raise ValidationError(
                "from_program_id and to_program_id must differ",
                error_code="ERR-VAL-422",
            )

        from_program = await self._fetch_program(from_program_id)
        to_program = await self._fetch_program(to_program_id)
        if from_program is None or to_program is None:
            raise NotFoundError("Program not found", error_code="ERR-ERP-404")
        verify_school_boundary(from_program.school_id, auth)
        verify_school_boundary(to_program.school_id, auth)

        # Idempotent on (school, from, to)
        result = await self.db.execute(
            select(ProgramEquivalence).where(
                ProgramEquivalence.school_id == auth.school_id,
                ProgramEquivalence.from_program_id == from_program_id,
                ProgramEquivalence.to_program_id == to_program_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            return self._equivalence_to_response(existing)

        async with UnitOfWork(self.db) as uow:
            eq = ProgramEquivalence(
                school_id=auth.school_id,
                from_program_id=from_program_id,
                to_program_id=to_program_id,
                kind=kind,
                note=note,
                ratified_at=ratified_at,
                ratified_by=auth.user_id,
            )
            uow.session.add(eq)
            await uow.session.flush()

            audit = AuditService(uow.session)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="PROGRAM_EQUIVALENCE_CREATED",
                outcome="success",
                target_type="program_equivalence",
                target_id=eq.id,
                entity_after={
                    "from_program_id": str(from_program_id),
                    "to_program_id": str(to_program_id),
                    "kind": kind,
                },
                ip_address=ip_address,
            )
            await uow.commit()
        return self._equivalence_to_response(eq)

    async def delete_program_equivalence(
        self,
        *,
        equivalence_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str | None,
    ) -> None:
        result = await self.db.execute(
            select(ProgramEquivalence).where(
                ProgramEquivalence.id == equivalence_id
            )
        )
        eq = result.scalar_one_or_none()
        if eq is None:
            raise NotFoundError(
                "Equivalence not found", error_code="ERR-ERP-404"
            )
        verify_school_boundary(eq.school_id, auth)

        async with UnitOfWork(self.db) as uow:
            attached = await uow.session.get(ProgramEquivalence, eq.id)
            if attached is None:
                raise NotFoundError(
                    "Equivalence not found", error_code="ERR-ERP-404"
                )
            await uow.session.delete(attached)
            await uow.session.flush()

            audit = AuditService(uow.session)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="PROGRAM_EQUIVALENCE_DELETED",
                outcome="success",
                target_type="program_equivalence",
                target_id=eq.id,
                entity_before={
                    "from_program_id": str(eq.from_program_id),
                    "to_program_id": str(eq.to_program_id),
                    "kind": eq.kind,
                },
                ip_address=ip_address,
            )
            await uow.commit()

    async def equivalent_program_ids(
        self,
        *,
        auth: AuthContext,
        program_id: uuid.UUID,
    ) -> set[uuid.UUID]:
        """Resolve the closure of programs declared equivalent to ``program_id``
        (BFS over the directed equivalence graph in this school)."""
        from collections import deque
        from sqlalchemy import or_

        seen: set[uuid.UUID] = {program_id}
        queue: deque[uuid.UUID] = deque([program_id])
        while queue:
            current = queue.popleft()
            result = await self.db.execute(
                select(ProgramEquivalence).where(
                    ProgramEquivalence.school_id == auth.school_id,
                    or_(
                        ProgramEquivalence.from_program_id == current,
                        ProgramEquivalence.to_program_id == current,
                    ),
                )
            )
            for eq in result.scalars().all():
                neighbour = (
                    eq.to_program_id
                    if eq.from_program_id == current
                    else eq.from_program_id
                )
                if neighbour not in seen:
                    seen.add(neighbour)
                    queue.append(neighbour)
        return seen

    # ------------------------------------------------------------------
    # Program assignment — write side
    # ------------------------------------------------------------------
    async def assign_program_to_enrollment(
        self,
        *,
        enrollment_id: uuid.UUID,
        program_id: uuid.UUID,
        reason_code: str,
        reason_note: str | None,
        auth: AuthContext,
        ip_address: str | None,
        program_version_id: uuid.UUID | None = None,
    ) -> dict:
        """Assign or change the program on an existing enrollment.

        Behaviour:
        - INITIAL set on an enrollment with no program: in-place update
          (no soft-replace; nothing to preserve).
        - Real change (existing program ≠ new program): soft-replace
          — mark current enrollment ``transferred``, create a new active
          enrollment with the new program, write the event.
        - No-op (existing program == new program): rejected as 409 to
          surface accidental double-writes early.

        Always writes one ``ProgramAssignmentEvent`` row in the same
        transaction as the data change. Append-only: never UPDATEs the
        event log.
        """
        reason = (reason_code or "").strip().upper()
        allowed = {r.value for r in ProgramAssignmentReason}
        if reason not in allowed:
            raise ValidationError(
                "Invalid reason_code",
                error_code="ERR-VAL-422",
                details={"allowed": sorted(allowed)},
            )

        enrollment = await self._fetch_enrollment(enrollment_id)
        if enrollment is None:
            raise NotFoundError("Enrollment not found", error_code="ERR-ERP-404")
        verify_school_boundary(enrollment.school_id, auth)

        program = await self._fetch_program(program_id)
        if program is None:
            raise NotFoundError("Program not found", error_code="ERR-ERP-404")
        verify_school_boundary(program.school_id, auth)
        if not program.is_active:
            raise ConflictError(
                "Program is not active",
                error_code="ERR-ERP-409",
            )

        # G50a: validate program_version_id (if provided) belongs to the
        # selected program AND school AND is active.
        program_version = None
        if program_version_id is not None:
            pv_result = await self.db.execute(
                select(ProgramVersion).where(
                    ProgramVersion.id == program_version_id
                )
            )
            program_version = pv_result.scalar_one_or_none()
            if program_version is None:
                raise NotFoundError(
                    "Program version not found", error_code="ERR-ERP-404"
                )
            verify_school_boundary(program_version.school_id, auth)
            if program_version.program_id != program.id:
                raise ValidationError(
                    "program_version_id does not belong to program_id",
                    error_code="ERR-VAL-422",
                )
            if not program_version.is_active:
                raise ConflictError(
                    "Program version is not active",
                    error_code="ERR-ERP-409",
                )

        # Looking up the period to denormalize academic_year_id onto the
        # event row for fast year-based queries.
        period = await self.repo.get_period(enrollment.period_id)
        if period is None:
            raise NotFoundError("Period not found", error_code="ERR-ERP-404")
        academic_year_id = (
            await self._academic_year_id_for_period(period.id)
        )

        previous_program_id = enrollment.program_id
        previous_program_version_id = enrollment.program_version_id

        # No-op detection — refuse to write a duplicate "no change" event.
        if previous_program_id == program.id:
            raise ConflictError(
                "Enrollment already assigned to this program",
                error_code="ERR-ERP-409",
                details={
                    "enrollment_id": str(enrollment.id),
                    "program_id": str(program.id),
                },
            )

        # First-assignment fast path: no soft-replace needed when the
        # enrollment had no program yet.
        is_first_assignment = previous_program_id is None
        if is_first_assignment and reason != ProgramAssignmentReason.INITIAL.value:
            # Don't fail hard — just normalize the reason for clarity.
            # Callers can still pass CORRECTION etc. explicitly.
            pass

        async with UnitOfWork(self.db) as uow:
            session = uow.session
            attached_enrollment = await session.get(Enrollment, enrollment.id)
            if attached_enrollment is None:
                raise NotFoundError(
                    "Enrollment not found", error_code="ERR-ERP-404"
                )

            from_enrollment_id = attached_enrollment.id
            to_enrollment_id: uuid.UUID

            if is_first_assignment:
                # In-place — no historical fidelity to preserve yet.
                attached_enrollment.program_id = program.id
                attached_enrollment.program_version_id = program_version_id
                attached_enrollment.updated_at = _utc_now()
                await session.flush()
                to_enrollment_id = attached_enrollment.id
            else:
                # Soft-replace: deactivate previous, create new active row
                # with the new program. The partial unique index
                # ``uq_enrollments_school_student_period_active`` is
                # satisfied because the old row's status flips to
                # ``transferred`` before the new row is inserted.
                attached_enrollment.status = EnrollmentStatus.TRANSFERRED.value
                attached_enrollment.updated_at = _utc_now()
                await session.flush()

                replacement = Enrollment(
                    school_id=attached_enrollment.school_id,
                    student_id=attached_enrollment.student_id,
                    class_id=attached_enrollment.class_id,
                    period_id=attached_enrollment.period_id,
                    program_id=program.id,
                    program_version_id=program_version_id,
                    status=EnrollmentStatus.ACTIVE.value,
                )
                session.add(replacement)
                await session.flush()
                to_enrollment_id = replacement.id

            # Append-only event log.
            now = _utc_now()
            event = ProgramAssignmentEvent(
                school_id=auth.school_id,
                student_id=attached_enrollment.student_id,
                academic_year_id=academic_year_id,
                period_id=attached_enrollment.period_id,
                from_program_id=previous_program_id,
                to_program_id=program.id,
                from_program_version_id=previous_program_version_id,
                to_program_version_id=program_version_id,
                from_enrollment_id=from_enrollment_id,
                to_enrollment_id=to_enrollment_id,
                reason_code=reason,
                reason_note=reason_note,
                actor_user_id=auth.user_id,
                occurred_at=now,
                created_at=now,
            )
            session.add(event)
            await session.flush()

            audit = AuditService(session)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="PROGRAM_ASSIGNED",
                outcome="success",
                target_type="enrollment",
                target_id=to_enrollment_id,
                entity_before={
                    "program_id": _short(previous_program_id),
                    "enrollment_id": str(from_enrollment_id),
                },
                entity_after={
                    "program_id": str(program.id),
                    "enrollment_id": str(to_enrollment_id),
                    "reason_code": reason,
                },
                ip_address=ip_address,
            )
            await uow.commit()

        return self._event_to_response(event)

    # ------------------------------------------------------------------
    # Read views — history + timeline + current
    # ------------------------------------------------------------------
    async def get_program_history(
        self,
        *,
        student_id: uuid.UUID,
        auth: AuthContext,
    ) -> list[dict]:
        """Return all program-assignment events for a student, newest first."""
        await self._authorize_student_read(student_id=student_id, auth=auth)
        stmt = (
            select(ProgramAssignmentEvent)
            .where(
                ProgramAssignmentEvent.school_id == auth.school_id,
                ProgramAssignmentEvent.student_id == student_id,
            )
            .order_by(desc(ProgramAssignmentEvent.occurred_at))
        )
        result = await self.db.execute(stmt)
        return [self._event_to_response(e) for e in result.scalars().all()]

    async def get_academic_timeline(
        self,
        *,
        student_id: uuid.UUID,
        auth: AuthContext,
    ) -> list[dict]:
        """Per-(year, period) view of every enrollment a student has held.

        Returned chronologically (oldest first) so the frontend can render
        a vertical timeline without reversing.
        """
        await self._authorize_student_read(student_id=student_id, auth=auth)

        stmt = (
            select(Enrollment, Class, Period, AcademicYear, Program)
            .join(Class, Class.id == Enrollment.class_id)
            .join(Period, Period.id == Enrollment.period_id)
            .join(AcademicYear, AcademicYear.id == Class.academic_year_id)
            .outerjoin(Program, Program.id == Enrollment.program_id)
            .where(
                Enrollment.school_id == auth.school_id,
                Enrollment.student_id == student_id,
            )
            .order_by(
                AcademicYear.date_start.asc(),
                Period.date_start.asc(),
                Enrollment.created_at.asc(),
            )
        )
        result = await self.db.execute(stmt)
        items: list[dict] = []
        for enrollment, class_, period, ay, program in result.all():
            items.append(
                {
                    "enrollment_id": str(enrollment.id),
                    "academic_year_id": str(ay.id),
                    "academic_year_label": ay.label,
                    "academic_year_start": ay.date_start.isoformat(),
                    "academic_year_end": ay.date_end.isoformat(),
                    "period_id": str(period.id),
                    "period_label": period.label,
                    "period_start": period.date_start.isoformat(),
                    "period_end": period.date_end.isoformat(),
                    "class_id": str(class_.id),
                    "class_code": class_.code,
                    "class_name": class_.name,
                    "program": self._program_summary(program),
                    "status": enrollment.status,
                }
            )
        return items

    async def get_current_program(
        self,
        *,
        student_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict:
        """Latest active enrollment's program for the student in this school."""
        await self._authorize_student_read(student_id=student_id, auth=auth)

        stmt = (
            select(Enrollment, Period, Class, Program)
            .join(Class, Class.id == Enrollment.class_id)
            .join(Period, Period.id == Enrollment.period_id)
            .outerjoin(Program, Program.id == Enrollment.program_id)
            .where(
                Enrollment.school_id == auth.school_id,
                Enrollment.student_id == student_id,
                Enrollment.status == EnrollmentStatus.ACTIVE.value,
            )
            .order_by(desc(Period.date_start), desc(Enrollment.created_at))
            .limit(1)
        )
        result = await self.db.execute(stmt)
        row = result.first()
        if row is None:
            return {
                "student_id": str(student_id),
                "academic_year_id": None,
                "period_id": None,
                "enrollment_id": None,
                "program": None,
            }
        enrollment, period, class_, program = row
        return {
            "student_id": str(student_id),
            "academic_year_id": str(class_.academic_year_id),
            "period_id": str(period.id),
            "enrollment_id": str(enrollment.id),
            "program": self._program_summary(program),
        }

    # ------------------------------------------------------------------
    # Admin list — used by the Phase 2.b EnrollmentsPage
    # ------------------------------------------------------------------
    async def list_enrollments_for_admin(
        self,
        *,
        auth: AuthContext,
        class_id: uuid.UUID | None = None,
        period_id: uuid.UUID | None = None,
        status: str | None = None,
        missing_program: bool = False,
        cursor: str | None = None,
        limit: int = 20,
    ) -> tuple[list[dict], str | None, bool]:
        """Paginated, school-scoped list of enrollments for admin UIs.

        Filters:
            - class_id, period_id, status — direct equality.
            - missing_program=True — only enrollments where program_id IS NULL
              (the "needs program assignment" backlog from the Phase 1 design).

        Cursor pagination orders by (created_at DESC, id DESC). The cursor is a
        base64-encoded ``"<id>|<iso-datetime>"`` produced by
        ``app.core.response.encode_cursor``.

        Returns ``(items, next_cursor, has_more)`` to match the existing
        list-endpoint contract.
        """
        from app.core.response import decode_cursor, encode_cursor

        # Joined load — student name, class label, period label, program summary
        # all returned in a single query.
        from app.models.iam import User as UserModel

        stmt = (
            select(Enrollment, UserModel, Class, Period, AcademicYear, Program)
            .join(UserModel, UserModel.id == Enrollment.student_id)
            .join(Class, Class.id == Enrollment.class_id)
            .join(Period, Period.id == Enrollment.period_id)
            .join(AcademicYear, AcademicYear.id == Class.academic_year_id)
            .outerjoin(Program, Program.id == Enrollment.program_id)
            .where(Enrollment.school_id == auth.school_id)
        )
        if class_id is not None:
            stmt = stmt.where(Enrollment.class_id == class_id)
        if period_id is not None:
            stmt = stmt.where(Enrollment.period_id == period_id)
        if status is not None:
            stmt = stmt.where(Enrollment.status == status)
        if missing_program:
            stmt = stmt.where(Enrollment.program_id.is_(None))

        if cursor:
            try:
                last_id, sort_value = decode_cursor(cursor)
            except ValueError as exc:
                raise ValidationError(
                    "Invalid cursor", error_code="ERR-VAL-422"
                ) from exc
            if sort_value:
                # cursor format encodes an ISO datetime in sort_value
                from datetime import datetime as _dt

                try:
                    boundary = _dt.fromisoformat(sort_value)
                except ValueError as exc:
                    raise ValidationError(
                        "Invalid cursor", error_code="ERR-VAL-422"
                    ) from exc
                stmt = stmt.where(
                    (Enrollment.created_at < boundary)
                    | (
                        (Enrollment.created_at == boundary)
                        & (Enrollment.id < last_id)
                    )
                )
            else:
                stmt = stmt.where(Enrollment.id < last_id)

        stmt = stmt.order_by(
            desc(Enrollment.created_at),
            desc(Enrollment.id),
        ).limit(limit + 1)

        result = await self.db.execute(stmt)
        rows = list(result.all())
        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        items: list[dict] = []
        for enrollment, student, class_, period, academic_year, program in rows:
            items.append(
                {
                    "id": str(enrollment.id),
                    "school_id": str(enrollment.school_id),
                    "status": enrollment.status,
                    "created_at": enrollment.created_at.isoformat()
                    if enrollment.created_at is not None
                    else None,
                    "student": {
                        "id": str(student.id),
                        "full_name": student.full_name,
                        "email": student.email,
                    },
                    "class_": {
                        "id": str(class_.id),
                        "code": class_.code,
                        "name": class_.name,
                    },
                    "period": {
                        "id": str(period.id),
                        "label": period.label,
                        "date_start": period.date_start.isoformat(),
                        "date_end": period.date_end.isoformat(),
                    },
                    "academic_year": {
                        "id": str(academic_year.id),
                        "label": academic_year.label,
                    },
                    "program": self._program_summary(program),
                }
            )

        next_cursor = None
        if has_more and rows:
            last_enrollment = rows[-1][0]
            next_cursor = encode_cursor(
                last_enrollment.id,
                last_enrollment.created_at.isoformat()
                if last_enrollment.created_at is not None
                else None,
            )
        return items, next_cursor, has_more

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    async def _fetch_program(self, program_id: uuid.UUID) -> Program | None:
        result = await self.db.execute(
            select(Program).where(Program.id == program_id)
        )
        return result.scalar_one_or_none()

    async def _fetch_program_by_code(
        self,
        *,
        school_id: uuid.UUID,
        code: str,
    ) -> Program | None:
        result = await self.db.execute(
            select(Program).where(
                Program.school_id == school_id,
                Program.code == code,
            )
        )
        return result.scalar_one_or_none()

    async def _fetch_enrollment(
        self, enrollment_id: uuid.UUID
    ) -> Enrollment | None:
        result = await self.db.execute(
            select(Enrollment).where(Enrollment.id == enrollment_id)
        )
        return result.scalar_one_or_none()

    async def _academic_year_id_for_period(
        self, period_id: uuid.UUID
    ) -> uuid.UUID:
        result = await self.db.execute(
            select(Period.academic_year_id).where(Period.id == period_id)
        )
        ay_id = result.scalar_one_or_none()
        if ay_id is None:
            raise NotFoundError("Period not found", error_code="ERR-ERP-404")
        return ay_id

    async def _authorize_student_read(
        self,
        *,
        student_id: uuid.UUID,
        auth: AuthContext,
    ) -> None:
        """Allow STD self-read; PAR linked-children read; ADM/DIR/TCH school-scope."""
        student = await self.repo.get_user_by_id(student_id)
        if student is None:
            raise NotFoundError("Student not found", error_code="ERR-ERP-404")
        verify_school_boundary(student.school_id, auth)

        if auth.role == STD:
            if auth.user_id != student_id:
                raise NotFoundError(
                    "Resource not found", error_code="ERR-RES-404"
                )
            return

        if auth.role == PAR:
            allowed = await get_parent_child_ids(
                parent_user_id=auth.user_id,
                school_id=auth.school_id,
                db=self.db,
            )
            verify_parent_child_ownership(student_id, allowed)
            return

        # ADM / DIR / TCH / SUP / SYS — school boundary is enough; specific
        # write permissions are gated at the route layer.
        if auth.role in (ADM, DIR, TCH, SUP, SYS):
            return

        # Anything else: deny via scope masking.
        raise NotFoundError("Resource not found", error_code="ERR-RES-404")
