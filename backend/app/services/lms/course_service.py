"""Course and activity LMS service."""

from __future__ import annotations

import uuid

from app.core.dependencies import AuthContext, verify_school_boundary, verify_teacher_assignment
from app.core.exceptions import ConflictError, NotFoundError
from app.core.filtering import FilterSpec, SortSpec
from app.core.response import encode_cursor
from app.core.unit_of_work import UnitOfWork
from app.repositories.lms import LMSRepository
from app.schemas.lms import (
    ActivitySessionCompleteRequest,
    ActivitySessionCreateRequest,
    CourseCreateRequest,
)
from app.services.audit import AuditService
from app.services.lms._helpers import LMSServiceBase


class CourseService(LMSServiceBase):
    """Handles course and activity workflows."""

    async def create_course(
        self,
        *,
        body: CourseCreateRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        class_room = await self.repo.get_class(body.class_id)
        if class_room is None:
            raise NotFoundError("Class not found", error_code="ERR-LMS-404")
        verify_school_boundary(class_room.school_id, auth)

        teacher_classes = await self.repo.list_teacher_class_ids(
            teacher_id=auth.user_id,
            school_id=auth.school_id,
        )
        verify_teacher_assignment(body.class_id, teacher_classes)

        async with UnitOfWork(self.db) as uow:
            repo = LMSRepository(uow.session)
            audit = AuditService(uow.session)
            course = await repo.create_course(
                school_id=auth.school_id,
                class_id=body.class_id,
                teacher_id=auth.user_id,
                title=body.title,
                description=body.description,
                status=body.status,
            )
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="COURSE_CREATED",
                outcome="success",
                target_type="course",
                target_id=course.id,
                entity_after={
                    "class_id": str(body.class_id),
                    "title": body.title,
                    "status": body.status,
                },
                ip_address=ip_address,
            )
            await uow.commit()

        return self._course_to_dict(course)

    async def list_courses(
        self,
        *,
        class_id: uuid.UUID | None,
        filters: FilterSpec,
        sort: SortSpec,
        search: str | None,
        cursor: str | None,
        limit: int,
        auth: AuthContext,
    ) -> tuple[list[dict], str | None, bool]:
        teacher_class_ids: set[uuid.UUID] | None = None
        if auth.role == "TCH":
            teacher_class_ids = await self.repo.list_teacher_class_ids(
                teacher_id=auth.user_id,
                school_id=auth.school_id,
            )

        courses, has_more = await self.repo.list_courses(
            school_id=auth.school_id,
            class_id=class_id,
            teacher_class_ids=teacher_class_ids,
            filters=filters,
            sort=sort,
            search=search,
            cursor=cursor,
            limit=limit,
        )
        items = [self._course_to_dict(course) for course in courses]
        next_cursor = encode_cursor(courses[-1].id) if has_more and courses else None
        return items, next_cursor, has_more

    async def list_activities(
        self,
        *,
        activity_type: str | None,
        difficulty: str | None,
        filters: FilterSpec,
        sort: SortSpec,
        search: str | None,
        cursor: str | None,
        limit: int,
        auth: AuthContext,
    ) -> tuple[list[dict], str | None, bool]:
        activities, has_more = await self.repo.list_activities(
            school_id=auth.school_id,
            activity_type=activity_type,
            difficulty=difficulty,
            filters=filters,
            sort=sort,
            search=search,
            cursor=cursor,
            limit=limit,
        )
        items = [self._activity_to_dict(activity) for activity in activities]
        next_cursor = encode_cursor(activities[-1].id) if has_more and activities else None
        return items, next_cursor, has_more

    async def create_activity_session(
        self,
        *,
        body: ActivitySessionCreateRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        activity = await self.repo.get_activity(body.activity_id)
        if activity is None:
            raise NotFoundError("Activity not found", error_code="ERR-LMS-404")
        if activity.school_id is not None:
            verify_school_boundary(activity.school_id, auth)

        attempt_no = await self.repo.get_next_activity_attempt_no(
            student_id=auth.user_id,
            activity_id=body.activity_id,
        )
        async with UnitOfWork(self.db) as uow:
            repo = LMSRepository(uow.session)
            audit = AuditService(uow.session)
            session = await repo.create_activity_session(
                student_id=auth.user_id,
                activity_id=body.activity_id,
                status="started",
                attempt_no=attempt_no,
            )
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="ACTIVITY_SESSION_STARTED",
                outcome="success",
                target_type="activity_session",
                target_id=session.id,
                entity_after={
                    "activity_id": str(body.activity_id),
                    "attempt_no": session.attempt_no,
                },
                ip_address=ip_address,
            )
            await uow.commit()
        return self._activity_session_to_dict(session)

    async def complete_activity_session(
        self,
        *,
        session_id: uuid.UUID,
        body: ActivitySessionCompleteRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        session = await self.repo.get_activity_session(session_id)
        if session is None or session.student_id != auth.user_id:
            raise NotFoundError("Activity session not found", error_code="ERR-LMS-404")
        if session.status != "started":
            raise ConflictError(
                "Session is not in started status",
                error_code="ERR-LMS-409",
                details={"current_status": session.status},
            )

        async with UnitOfWork(self.db) as uow:
            repo = LMSRepository(uow.session)
            audit = AuditService(uow.session)
            session.status = "completed"
            if body.score is not None:
                session.score = body.score
            await repo.save_activity_session(session)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="ACTIVITY_SESSION_COMPLETED",
                outcome="success",
                target_type="activity_session",
                target_id=session.id,
                entity_after={
                    "status": "completed",
                    "score": float(body.score) if body.score is not None else None,
                },
                ip_address=ip_address,
            )
            await uow.commit()
        return self._activity_session_to_dict(session)
