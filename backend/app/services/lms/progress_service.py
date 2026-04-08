"""Assessment, results, and dashboard progress LMS service."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    AuthContext,
    verify_parent_child_ownership,
    verify_school_boundary,
    verify_teacher_assignment,
)
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.filtering import FilterSpec, SortSpec
from app.core.permissions import PAR, STD, TCH
from app.core.response import encode_cursor
from app.core.unit_of_work import UnitOfWork
from app.repositories.lms import LMSRepository
from app.schemas.lms import AssessmentCreateRequest, AssessmentResultSubmitRequest
from app.services.audit import AuditService
from app.services.lms._helpers import LMSServiceBase
from app.services.progress import ProgressService as DashboardProgressService


class ProgressService(LMSServiceBase):
    """Handles assessments, result listings, and dashboard progress delegation."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self._dashboard = DashboardProgressService(db)

    async def create_assessment(
        self,
        *,
        body: AssessmentCreateRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        class_room = await self.repo.get_class(body.class_id)
        if class_room is None:
            raise NotFoundError("Class not found", error_code="ERR-LMS-404")
        verify_school_boundary(class_room.school_id, auth)

        if auth.role == TCH:
            teacher_classes = await self.repo.list_teacher_class_ids(
                teacher_id=auth.user_id,
                school_id=auth.school_id,
            )
            verify_teacher_assignment(body.class_id, teacher_classes)

        async with UnitOfWork(self.db) as uow:
            repo = LMSRepository(uow.session)
            audit = AuditService(uow.session)
            assessment = await repo.create_assessment(
                class_id=body.class_id,
                teacher_id=auth.user_id,
                title=body.title,
                due_at=body.due_at,
                window_end=body.window_end,
                total_points=body.total_points,
                status=body.status,
            )
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="ASSESSMENT_CREATED",
                outcome="success",
                target_type="assessment",
                target_id=assessment.id,
                entity_after={
                    "class_id": str(body.class_id),
                    "title": body.title,
                    "status": body.status,
                },
                ip_address=ip_address,
            )
            await uow.commit()

        return self._assessment_to_dict(assessment)

    async def list_assessments(
        self,
        *,
        class_id: uuid.UUID | None,
        status: str | None,
        filters: FilterSpec,
        sort: SortSpec,
        search: str | None,
        cursor: str | None,
        limit: int,
        auth: AuthContext,
    ) -> tuple[list[dict], str | None, bool]:
        teacher_class_ids: set[uuid.UUID] | None = None
        if auth.role == TCH:
            teacher_class_ids = await self.repo.list_teacher_class_ids(
                teacher_id=auth.user_id,
                school_id=auth.school_id,
            )

        assessments, has_more = await self.repo.list_assessments(
            school_id=auth.school_id,
            class_id=class_id,
            status=status,
            teacher_class_ids=teacher_class_ids,
            filters=filters,
            sort=sort,
            search=search,
            cursor=cursor,
            limit=limit,
        )
        items = [self._assessment_to_dict(assessment) for assessment in assessments]
        next_cursor = (
            encode_cursor(assessments[-1].id) if has_more and assessments else None
        )
        return items, next_cursor, has_more

    async def publish_assessment(
        self,
        *,
        assessment_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        bundle = await self.repo.get_assessment_with_class(assessment_id)
        if bundle is None:
            raise NotFoundError("Assessment not found", error_code="ERR-LMS-404")
        assessment, class_room = bundle
        verify_school_boundary(class_room.school_id, auth)

        if assessment.status != "draft":
            raise ConflictError(
                "Assessment can only be published from draft status",
                error_code="ERR-LMS-409",
                details={"current_status": assessment.status},
            )

        async with UnitOfWork(self.db) as uow:
            repo = LMSRepository(uow.session)
            audit = AuditService(uow.session)
            assessment.status = "published"
            await repo.save_assessment(assessment)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="ASSESSMENT_PUBLISHED",
                outcome="success",
                target_type="assessment",
                target_id=assessment.id,
                entity_after={"status": "published"},
                ip_address=ip_address,
            )
            await uow.commit()

        return self._assessment_to_dict(assessment)

    async def submit_assessment_result(
        self,
        *,
        assessment_id: uuid.UUID,
        body: AssessmentResultSubmitRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        bundle = await self.repo.get_assessment_with_class(assessment_id)
        if bundle is None:
            raise NotFoundError("Assessment not found", error_code="ERR-LMS-404")
        assessment, class_room = bundle
        verify_school_boundary(class_room.school_id, auth)

        if assessment.status != "published":
            raise ValidationError(
                "Assessment must be published to accept results",
                error_code="ERR-LMS-422",
            )

        existing = await self.repo.get_assessment_result(
            assessment_id=assessment_id,
            student_id=auth.user_id,
        )
        if existing is not None:
            return {
                "id": str(existing.id),
                "assessment_id": str(existing.assessment_id),
                "student_id": str(existing.student_id),
                "score": float(existing.score) if existing.score is not None else None,
                "status": existing.status,
            }

        async with UnitOfWork(self.db) as uow:
            repo = LMSRepository(uow.session)
            audit = AuditService(uow.session)
            result_obj = await repo.create_assessment_result(
                assessment_id=assessment_id,
                student_id=auth.user_id,
                score=body.score,
                status="submitted",
            )
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="ASSESSMENT_RESULT_SUBMITTED",
                outcome="success",
                target_type="assessment_result",
                target_id=result_obj.id,
                entity_after={
                    "assessment_id": str(assessment_id),
                    "score": float(body.score) if body.score is not None else None,
                },
                ip_address=ip_address,
            )
            await uow.commit()

        return {
            "id": str(result_obj.id),
            "assessment_id": str(result_obj.assessment_id),
            "student_id": str(result_obj.student_id),
            "score": float(result_obj.score) if result_obj.score is not None else None,
            "status": result_obj.status,
        }

    async def list_results(
        self,
        *,
        student_id: uuid.UUID | None,
        cursor: str | None,
        limit: int,
        auth: AuthContext,
    ) -> tuple[list[dict], str | None, bool]:
        if auth.role == STD:
            student_ids: set[uuid.UUID] | None = {auth.user_id}
        elif auth.role == PAR:
            child_ids = await self.repo.list_parent_child_ids(
                parent_id=auth.user_id,
                school_id=auth.school_id,
            )
            if student_id is None:
                student_ids = child_ids if child_ids else None
            else:
                verify_parent_child_ownership(student_id, child_ids)
                student_ids = {student_id}
        else:
            student_ids = {student_id} if student_id is not None else None

        rows, has_more = await self.repo.list_results(
            school_id=auth.school_id,
            student_ids=student_ids,
            cursor=cursor,
            limit=limit,
        )
        items = [
            {
                "assignment_id": str(assignment.id),
                "assignment_title": assignment.title,
                "course_title": course.title,
                "submission_id": str(submission.id),
                "status": submission.status,
                "score": float(grade.score) if grade.score is not None else None,
                "feedback_text": grade.feedback_text,
                "total_points": assignment.total_points,
                "due_at": assignment.due_at.isoformat() if assignment.due_at else None,
            }
            for assignment, submission, grade, course in rows
        ]
        next_cursor = encode_cursor(rows[-1][0].id) if has_more and rows else None
        return items, next_cursor, has_more

    async def get_student_progress_for_user(
        self,
        *,
        student_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict:
        return await self._dashboard.get_student_progress_for_user(
            student_id=student_id,
            auth=auth,
        )

    async def get_class_progress_for_user(
        self,
        *,
        class_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict:
        return await self._dashboard.get_class_progress_for_user(
            class_id=class_id,
            auth=auth,
        )

    async def get_my_progress(self, *, auth: AuthContext) -> dict:
        return await self._dashboard.get_my_progress(auth=auth)

    async def get_children_progress_for_parent(self, *, auth: AuthContext) -> dict:
        return await self._dashboard.get_children_progress_for_parent(auth=auth)
