"""Gradebook service for weighted categories, averages, matrix views, and transcripts."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    AuthContext,
    verify_parent_child_ownership,
    verify_school_boundary,
)
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.core.permissions import (
    PAR,
    PERM_LMS_GRADEBOOK_MANAGE,
    PERM_LMS_GRADEBOOK_READ,
    STD,
    TCH,
    role_has_permission,
)
from app.core.unit_of_work import UnitOfWork
from app.domain.value_objects.grade import MoroccanGrade
from app.repositories.erp import ERPRepository
from app.repositories.gradebook import GradebookRepository
from app.schemas.gradebook import GradeCategorySetRequest
from app.services.audit import AuditService
from app.services.lms._helpers import LMSServiceBase, _utc_now


class GradebookService(LMSServiceBase):
    """Handles weighted grade categories, averages, and transcript views."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self.gradebook_repo = GradebookRepository(db)
        self.erp_repo = ERPRepository(db)

    def _ensure_can_manage(self, auth: AuthContext) -> None:
        if not role_has_permission(auth.role, PERM_LMS_GRADEBOOK_MANAGE):
            raise AuthorizationError(
                "Insufficient permissions",
                error_code="ERR-AUTHZ-001",
                details={"required": [PERM_LMS_GRADEBOOK_MANAGE], "role": auth.role},
            )

    def _ensure_can_read(self, auth: AuthContext) -> None:
        if role_has_permission(auth.role, PERM_LMS_GRADEBOOK_MANAGE):
            return
        if role_has_permission(auth.role, PERM_LMS_GRADEBOOK_READ):
            return
        raise AuthorizationError(
            "Insufficient permissions",
            error_code="ERR-AUTHZ-001",
            details={
                "required_any_of": [
                    PERM_LMS_GRADEBOOK_MANAGE,
                    PERM_LMS_GRADEBOOK_READ,
                ],
                "role": auth.role,
            },
        )

    def _category_to_dict(self, category) -> dict[str, Any]:
        return {
            "id": str(category.id),
            "school_id": str(category.school_id),
            "class_id": str(category.class_id),
            "period_id": str(category.period_id),
            "name": category.name,
            "weight": float(category.weight),
            "position": category.position,
        }

    def _validate_category_weights(self, categories: list[Any]) -> None:
        if not categories:
            raise ValidationError(
                "At least one grade category is required",
                error_code="ERR-LMS-422",
            )

        total_weight = sum(float(category.weight) for category in categories)
        if abs(total_weight - 1.0) > 0.01:
            raise ValidationError(
                "Grade category weights must sum to 1.0",
                error_code="ERR-LMS-422",
                details={"total_weight": round(total_weight, 4)},
            )

    async def _load_class_period(
        self,
        *,
        class_id: uuid.UUID,
        period_id: uuid.UUID,
    ):
        class_room = await self.erp_repo.get_class(class_id)
        if class_room is None:
            raise NotFoundError("Class not found", error_code="ERR-ERP-404")

        period = await self.erp_repo.get_period(period_id)
        if period is None:
            raise NotFoundError("Period not found", error_code="ERR-ERP-404")

        if class_room.academic_year_id != period.academic_year_id:
            raise ValidationError(
                "Class and period must belong to the same academic year",
                error_code="ERR-LMS-422",
            )

        return class_room, period

    async def _ensure_class_access(
        self,
        *,
        class_id: uuid.UUID,
        period_id: uuid.UUID,
        auth: AuthContext,
        manage: bool,
    ):
        if manage:
            self._ensure_can_manage(auth)
        else:
            self._ensure_can_read(auth)

        class_room, period = await self._load_class_period(
            class_id=class_id,
            period_id=period_id,
        )
        verify_school_boundary(class_room.school_id, auth)
        verify_school_boundary(period.school_id, auth)

        if auth.role == TCH:
            teacher_assignment = await self.erp_repo.get_teacher_assignment(
                teacher_id=auth.user_id,
                class_id=class_id,
                period_id=period_id,
                school_id=auth.school_id,
            )
            if teacher_assignment is None:
                raise NotFoundError("Class not found", error_code="ERR-ERP-404")

        return class_room, period

    async def _resolve_visible_student_ids(
        self,
        *,
        class_id: uuid.UUID,
        period_id: uuid.UUID,
        auth: AuthContext,
    ) -> set[uuid.UUID] | None:
        if auth.role == STD:
            enrollment = await self.erp_repo.get_active_enrollment(
                student_id=auth.user_id,
                class_id=class_id,
                period_id=period_id,
            )
            if enrollment is None:
                raise NotFoundError("Gradebook not found", error_code="ERR-LMS-404")
            return {auth.user_id}

        if auth.role == PAR:
            child_ids = await self.repo.list_parent_child_ids(
                parent_id=auth.user_id,
                school_id=auth.school_id,
            )
            students = await self.gradebook_repo.list_class_period_students(
                class_id=class_id,
                period_id=period_id,
            )
            visible_ids = {student_id for student_id, _ in students if student_id in child_ids}
            if not visible_ids:
                raise NotFoundError("Gradebook not found", error_code="ERR-LMS-404")
            return visible_ids

        return None

    def _build_category_average_map(
        self,
        *,
        categories: list[Any],
        student_category_scores: dict[uuid.UUID, list[float]],
    ) -> dict[uuid.UUID, float | None]:
        category_averages: dict[uuid.UUID, float | None] = {}
        for category in categories:
            scores = student_category_scores.get(category.id, [])
            if scores:
                category_averages[category.id] = round(sum(scores) / len(scores), 2)
            else:
                category_averages[category.id] = None
        return category_averages

    def _compute_weighted_average(
        self,
        *,
        categories: list[Any],
        category_averages: dict[uuid.UUID, float | None],
    ) -> MoroccanGrade:
        weighted_total = 0.0
        for category in categories:
            average = category_averages.get(category.id)
            weighted_total += (average or 0.0) * float(category.weight)
        return MoroccanGrade.from_float(weighted_total)

    async def _build_live_metrics(
        self,
        *,
        class_id: uuid.UUID,
        period_id: uuid.UUID,
    ) -> dict[str, Any]:
        categories = await self.gradebook_repo.list_grade_categories(
            class_id=class_id,
            period_id=period_id,
        )
        self._validate_category_weights(categories)

        students = await self.gradebook_repo.list_class_period_students(
            class_id=class_id,
            period_id=period_id,
        )
        assignments = await self.gradebook_repo.list_gradebook_assignments(
            class_id=class_id,
            period_id=period_id,
        )
        grade_entries = await self.gradebook_repo.list_gradebook_grade_entries(
            class_id=class_id,
            period_id=period_id,
        )

        assignment_scores: dict[tuple[uuid.UUID, uuid.UUID], dict[str, Any]] = {}
        category_scores_by_student: dict[uuid.UUID, dict[uuid.UUID, list[float]]] = {}
        for student_id, assignment_id, category_id, score, published_at in grade_entries:
            assignment_scores[(student_id, assignment_id)] = {
                "score": round(float(score), 2),
                "published_at": published_at.isoformat() if published_at else None,
            }
            if category_id is None:
                continue
            category_scores_by_student.setdefault(student_id, {}).setdefault(
                category_id,
                [],
            ).append(float(score))

        ordered_records: list[dict[str, Any]] = []
        ranked_by_student: dict[uuid.UUID, dict[str, Any]] = {}
        category_averages_by_student: dict[uuid.UUID, dict[uuid.UUID, float | None]] = {}
        for student_id, student_name in students:
            category_averages = self._build_category_average_map(
                categories=categories,
                student_category_scores=category_scores_by_student.get(student_id, {}),
            )
            category_averages_by_student[student_id] = category_averages
            weighted_average = self._compute_weighted_average(
                categories=categories,
                category_averages=category_averages,
            )
            ordered_records.append(
                {
                    "student_id": student_id,
                    "student_name": student_name,
                    "weighted_average": weighted_average,
                    "mention": weighted_average.mention,
                }
            )

        ordered_records.sort(
            key=lambda item: (
                -float(item["weighted_average"]),
                item["student_name"].lower(),
                str(item["student_id"]),
            )
        )

        current_rank = 0
        previous_score: float | None = None
        total_students = len(ordered_records)
        for index, record in enumerate(ordered_records):
            score_value = float(record["weighted_average"])
            if previous_score is None or score_value != previous_score:
                current_rank = index + 1
                previous_score = score_value
            record["class_rank"] = current_rank
            record["total_students"] = total_students
            ranked_by_student[record["student_id"]] = record

        return {
            "categories": categories,
            "students": students,
            "assignments": assignments,
            "assignment_scores": assignment_scores,
            "category_averages_by_student": category_averages_by_student,
            "ordered_records": ordered_records,
            "ranked_by_student": ranked_by_student,
        }

    async def set_grade_categories(
        self,
        *,
        body: GradeCategorySetRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> list[dict[str, Any]]:
        class_room, _period = await self._ensure_class_access(
            class_id=body.class_id,
            period_id=body.period_id,
            auth=auth,
            manage=True,
        )
        if not body.categories:
            raise ValidationError(
                "At least one grade category is required",
                error_code="ERR-LMS-422",
            )

        total_weight = sum(float(category.weight) for category in body.categories)
        if abs(total_weight - 1.0) > 0.01:
            raise ValidationError(
                "Grade category weights must sum to 1.0",
                error_code="ERR-LMS-422",
                details={"total_weight": round(total_weight, 4)},
            )

        async with UnitOfWork(self.db) as uow:
            repo = GradebookRepository(uow.session)
            audit = AuditService(uow.session)
            await repo.delete_grade_categories_for_scope(
                class_id=body.class_id,
                period_id=body.period_id,
            )

            categories = []
            for index, category_input in enumerate(body.categories):
                categories.append(
                    await repo.create_grade_category(
                        school_id=auth.school_id,
                        class_id=body.class_id,
                        period_id=body.period_id,
                        name=category_input.name,
                        weight=category_input.weight,
                        position=category_input.position if category_input.position >= 0 else index,
                    )
                )

            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="GRADEBOOK_CATEGORIES_SET",
                outcome="success",
                target_type="class",
                target_id=body.class_id,
                entity_after={
                    "class_id": str(body.class_id),
                    "period_id": str(body.period_id),
                    "category_count": len(categories),
                    "weights_total": round(total_weight, 4),
                },
                ip_address=ip_address,
            )
            await uow.commit()

        return [self._category_to_dict(category) for category in categories]

    async def list_grade_categories(
        self,
        *,
        class_id: uuid.UUID,
        period_id: uuid.UUID,
        auth: AuthContext,
    ) -> list[dict[str, Any]]:
        await self._ensure_class_access(
            class_id=class_id,
            period_id=period_id,
            auth=auth,
            manage=False,
        )
        if auth.role in {PAR, STD}:
            await self._resolve_visible_student_ids(
                class_id=class_id,
                period_id=period_id,
                auth=auth,
            )
        categories = await self.gradebook_repo.list_grade_categories(
            class_id=class_id,
            period_id=period_id,
        )
        return [self._category_to_dict(category) for category in categories]

    async def compute_student_average(
        self,
        *,
        student_id: uuid.UUID,
        class_id: uuid.UUID,
        period_id: uuid.UUID,
    ) -> MoroccanGrade:
        category_rows = await self.gradebook_repo.get_student_grades_by_category(
            student_id=student_id,
            class_id=class_id,
            period_id=period_id,
        )
        categories = [category for category, _ in category_rows]
        self._validate_category_weights(categories)
        category_averages = {
            category.id: round(float(category_average), 2)
            if category_average is not None
            else None
            for category, category_average in category_rows
        }
        return self._compute_weighted_average(
            categories=categories,
            category_averages=category_averages,
        )

    async def compute_class_averages(
        self,
        *,
        class_id: uuid.UUID,
        period_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str | None,
    ) -> list[dict[str, Any]]:
        await self._ensure_class_access(
            class_id=class_id,
            period_id=period_id,
            auth=auth,
            manage=True,
        )
        metrics = await self._build_live_metrics(class_id=class_id, period_id=period_id)
        computed_at = _utc_now()

        async with UnitOfWork(self.db) as uow:
            repo = GradebookRepository(uow.session)
            audit = AuditService(uow.session)
            await repo.delete_student_period_averages_for_scope(
                class_id=class_id,
                period_id=period_id,
            )

            for record in metrics["ordered_records"]:
                await repo.save_student_period_average(
                    student_id=record["student_id"],
                    class_id=class_id,
                    period_id=period_id,
                    school_id=auth.school_id,
                    weighted_average=float(record["weighted_average"]),
                    mention=record["mention"],
                    class_rank=record["class_rank"],
                    total_students=record["total_students"],
                    computed_at=computed_at,
                )

            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="GRADEBOOK_COMPUTED",
                outcome="success",
                target_type="class",
                target_id=class_id,
                entity_after={
                    "class_id": str(class_id),
                    "period_id": str(period_id),
                    "student_count": len(metrics["ordered_records"]),
                },
                ip_address=ip_address,
            )
            await uow.commit()

        return [
            {
                "student_id": str(record["student_id"]),
                "student_name": record["student_name"],
                "weighted_average": float(record["weighted_average"]),
                "mention": record["mention"],
                "class_rank": record["class_rank"],
                "total_students": record["total_students"],
                "computed_at": computed_at.isoformat(),
            }
            for record in metrics["ordered_records"]
        ]

    async def get_gradebook(
        self,
        *,
        class_id: uuid.UUID,
        period_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict[str, Any]:
        class_room, period = await self._ensure_class_access(
            class_id=class_id,
            period_id=period_id,
            auth=auth,
            manage=False,
        )
        visible_student_ids = await self._resolve_visible_student_ids(
            class_id=class_id,
            period_id=period_id,
            auth=auth,
        )
        metrics = await self._build_live_metrics(class_id=class_id, period_id=period_id)

        rows = []
        for record in metrics["ordered_records"]:
            student_id = record["student_id"]
            if visible_student_ids is not None and student_id not in visible_student_ids:
                continue

            assignment_cells = []
            for assignment, category in metrics["assignments"]:
                grade_data = metrics["assignment_scores"].get((student_id, assignment.id))
                assignment_cells.append(
                    {
                        "assignment_id": str(assignment.id),
                        "assignment_title": assignment.title,
                        "category_id": str(category.id),
                        "category_name": category.name,
                        "score": grade_data["score"] if grade_data is not None else None,
                        "total_points": assignment.total_points,
                        "published_at": (
                            grade_data["published_at"] if grade_data is not None else None
                        ),
                    }
                )

            rows.append(
                {
                    "student_id": str(student_id),
                    "student_name": record["student_name"],
                    "assignments": assignment_cells,
                    "category_averages": [
                        {
                            "category_id": str(category.id),
                            "category_name": category.name,
                            "weight": float(category.weight),
                            "average": metrics["category_averages_by_student"]
                            .get(student_id, {})
                            .get(category.id),
                        }
                        for category in metrics["categories"]
                    ],
                    "weighted_average": float(record["weighted_average"]),
                    "mention": record["mention"],
                    "class_rank": record["class_rank"],
                    "total_students": record["total_students"],
                }
            )

        if visible_student_ids is not None and not rows:
            raise NotFoundError("Gradebook not found", error_code="ERR-LMS-404")

        return {
            "class_id": str(class_room.id),
            "class_name": class_room.name,
            "period_id": str(period.id),
            "period_label": period.label,
            "categories": [
                self._category_to_dict(category) for category in metrics["categories"]
            ],
            "assignments": [
                {
                    "assignment_id": str(assignment.id),
                    "title": assignment.title,
                    "category_id": str(category.id),
                    "category_name": category.name,
                    "total_points": assignment.total_points,
                    "due_at": assignment.due_at.isoformat() if assignment.due_at else None,
                }
                for assignment, category in metrics["assignments"]
            ],
            "rows": rows,
        }

    async def get_student_transcript(
        self,
        *,
        student_id: uuid.UUID,
        academic_year_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict[str, Any]:
        self._ensure_can_read(auth)

        academic_year = await self.erp_repo.get_academic_year(academic_year_id)
        if academic_year is None:
            raise NotFoundError("Academic year not found", error_code="ERR-ERP-404")
        verify_school_boundary(academic_year.school_id, auth)

        student = await self.repo.get_user(student_id)
        if student is None:
            raise NotFoundError("Student not found", error_code="ERR-IAM-404")
        verify_school_boundary(student.school_id, auth)

        teacher_class_ids: set[uuid.UUID] | None = None
        if auth.role == STD:
            if student_id != auth.user_id:
                raise NotFoundError("Transcript not found", error_code="ERR-LMS-404")
        elif auth.role == PAR:
            child_ids = await self.repo.list_parent_child_ids(
                parent_id=auth.user_id,
                school_id=auth.school_id,
            )
            verify_parent_child_ownership(student_id, child_ids)
        elif auth.role == TCH:
            teacher_class_ids = await self.repo.list_teacher_class_ids(
                teacher_id=auth.user_id,
                school_id=auth.school_id,
            )

        periods: list[dict[str, Any]] = []
        seen_scope: set[tuple[uuid.UUID, uuid.UUID]] = set()

        cached_rows = await self.gradebook_repo.get_student_transcript(
            student_id=student_id,
            academic_year_id=academic_year_id,
        )
        for average, period, class_room in cached_rows:
            if teacher_class_ids is not None and class_room.id not in teacher_class_ids:
                continue
            verify_school_boundary(class_room.school_id, auth)
            seen_scope.add((class_room.id, period.id))
            periods.append(
                {
                    "_sort_key": period.date_start.isoformat(),
                    "class_id": str(class_room.id),
                    "class_name": class_room.name,
                    "period_id": str(period.id),
                    "period_label": period.label,
                    "weighted_average": round(float(average.weighted_average), 2),
                    "mention": average.mention,
                    "class_rank": average.class_rank,
                    "total_students": average.total_students,
                    "computed_at": average.computed_at.isoformat(),
                }
            )

        enrollments = await self.gradebook_repo.list_student_period_enrollments(
            student_id=student_id,
            academic_year_id=academic_year_id,
        )
        for _enrollment, class_room, period in enrollments:
            if teacher_class_ids is not None and class_room.id not in teacher_class_ids:
                continue
            verify_school_boundary(class_room.school_id, auth)
            scope_key = (class_room.id, period.id)
            if scope_key in seen_scope:
                continue

            metrics = await self._build_live_metrics(
                class_id=class_room.id,
                period_id=period.id,
            )
            record = metrics["ranked_by_student"].get(student_id)
            if record is None:
                continue
            periods.append(
                {
                    "_sort_key": period.date_start.isoformat(),
                    "class_id": str(class_room.id),
                    "class_name": class_room.name,
                    "period_id": str(period.id),
                    "period_label": period.label,
                    "weighted_average": round(float(record["weighted_average"]), 2),
                    "mention": record["mention"],
                    "class_rank": record["class_rank"],
                    "total_students": record["total_students"],
                    "computed_at": None,
                }
            )

        periods.sort(key=lambda item: (item["_sort_key"], item["class_name"]))
        for period in periods:
            period.pop("_sort_key", None)

        return {
            "student_id": str(student_id),
            "academic_year_id": str(academic_year_id),
            "periods": periods,
        }
