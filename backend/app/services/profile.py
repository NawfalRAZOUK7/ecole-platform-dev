"""Profile and teacher dashboard service."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    AuthContext,
    verify_school_boundary,
    verify_teacher_assignment,
)
from app.core.exceptions import NotFoundError, ValidationError
from app.core.permissions import PAR, STD, TCH
from app.core.unit_of_work import UnitOfWork
from app.repositories.profile import ProfileRepository
from app.schemas.profile import (
    ParentProfileResponse,
    ParentProfileUpdate,
    StudentProfileResponse,
    StudentProfileUpdate,
    TeacherProfileResponse,
    TeacherProfileUpdate,
)
from app.services.audit import AuditService
from app.services.profile_loader import ProfileLoader

_ROLE_PROFILE_MAP = {
    STD: "student",
    PAR: "parent",
    TCH: "teacher",
}


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


class ProfileService:
    """Business logic for role-specific profile operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = ProfileRepository(db)
        self.audit = AuditService(db)

    async def _build_user_profile(
        self,
        *,
        user_id: uuid.UUID,
        school_id: uuid.UUID,
        role: str,
    ) -> dict:
        user = await self.repo.get_user_in_school(user_id=user_id, school_id=school_id)
        if not user:
            raise NotFoundError("User not found", error_code="ERR-RES-404")

        result = {
            "user_id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone,
            "role": role,
            "school_id": user.school_id,
            "student_profile": None,
            "parent_profile": None,
            "teacher_profile": None,
        }

        profile_type = _ROLE_PROFILE_MAP.get(role)
        if not profile_type:
            return result

        loader = ProfileLoader(self.db)
        profiles = await loader.load(user_id, [role])
        profile = profiles.get(profile_type)
        if profile is None:
            return result

        if profile_type == "student":
            result["student_profile"] = StudentProfileResponse.model_validate(profile)
        elif profile_type == "parent":
            result["parent_profile"] = ParentProfileResponse.model_validate(profile)
        elif profile_type == "teacher":
            result["teacher_profile"] = TeacherProfileResponse.model_validate(profile)

        return result

    async def get_my_profile(self, auth: AuthContext) -> dict:
        return await self._build_user_profile(
            user_id=auth.user_id,
            school_id=auth.school_id,
            role=auth.role,
        )

    async def update_my_profile(
        self,
        *,
        auth: AuthContext,
        body: dict[str, Any],
        client_ip: str,
    ) -> dict:
        role = auth.role
        profile_type = _ROLE_PROFILE_MAP.get(role)
        if not profile_type:
            raise ValidationError(
                f"Role '{role}' does not have an extended profile",
                error_code="ERR-PROF-001",
            )

        if role == STD:
            update_data = StudentProfileUpdate(**body).model_dump(exclude_unset=True)
        elif role == PAR:
            update_data = ParentProfileUpdate(**body).model_dump(exclude_unset=True)
        else:
            update_data = TeacherProfileUpdate(**body).model_dump(exclude_unset=True)

        if not update_data:
            raise ValidationError("No fields to update", error_code="ERR-PROF-002")

        async with UnitOfWork(self.db) as uow:
            repo = ProfileRepository(uow.session)
            audit = AuditService(uow.session)
            loader = ProfileLoader(uow.session)
            profile = await loader.ensure_profile(auth.user_id, auth.school_id, role)
            if profile is None:
                raise ValidationError(
                    f"Role '{role}' does not have an extended profile",
                    error_code="ERR-PROF-001",
                )
            entity_before = {key: getattr(profile, key) for key in update_data}
            for field, value in update_data.items():
                setattr(profile, field, value)
            profile.updated_at = datetime.now(timezone.utc)
            saved_profile = await repo.save_profile(profile)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="PROFILE_UPDATED",
                target_type="profile",
                target_id=saved_profile.id,
                entity_before=jsonable_encoder(entity_before),
                entity_after=jsonable_encoder(update_data),
                outcome="success",
                ip_address=client_ip,
            )
            await uow.commit()
        return await self.get_my_profile(auth)

    async def get_admin_user_profile(
        self,
        *,
        user_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict:
        target = await self.repo.get_user_in_school(
            user_id=user_id,
            school_id=auth.school_id,
        )
        if not target:
            raise NotFoundError("User not found", error_code="ERR-RES-404")

        target_role = await self.repo.get_active_membership_role(
            user_id=user_id,
            school_id=auth.school_id,
        )
        return await self._build_user_profile(
            user_id=user_id,
            school_id=auth.school_id,
            role=target_role,
        )

    async def get_my_children(self, auth: AuthContext) -> list[dict]:
        if auth.role != PAR:
            raise ValidationError(
                "Only parents can access linked children",
                error_code="ERR-VAL-422",
            )
        rows = await self.repo.list_parent_children(
            parent_id=auth.user_id,
            school_id=auth.school_id,
        )
        return [
            {
                "user_id": str(child.id),
                "full_name": child.full_name,
                "email": child.email,
                "link_id": str(link.id),
                "linked_at": link.linked_at.isoformat() if link.linked_at else None,
                "student_profile": {
                    "class_level": profile.class_level if profile else None,
                    "date_of_birth": str(profile.date_of_birth)
                    if profile and profile.date_of_birth
                    else None,
                    "student_number": profile.student_number if profile else None,
                    "nationality": profile.nationality if profile else None,
                }
                if profile
                else None,
            }
            for link, child, profile in rows
        ]

    async def list_teacher_classes(self, auth: AuthContext) -> list[dict]:
        teacher_class_ids = await self.repo.list_teacher_class_ids(
            teacher_id=auth.user_id,
            school_id=auth.school_id,
        )
        if not teacher_class_ids:
            return []

        classes = await self.repo.list_classes_by_ids(
            class_ids=teacher_class_ids,
            school_id=auth.school_id,
        )
        student_counts = await self.repo.get_active_enrollment_counts(
            class_ids=teacher_class_ids,
            school_id=auth.school_id,
        )
        course_counts = await self.repo.get_teacher_course_counts(
            class_ids=teacher_class_ids,
            teacher_id=auth.user_id,
            school_id=auth.school_id,
        )
        return [
            {
                "id": str(cls.id),
                "code": cls.code,
                "name": cls.name,
                "academic_year_id": str(cls.academic_year_id),
                "student_count": student_counts.get(cls.id, 0),
                "course_count": course_counts.get(cls.id, 0),
            }
            for cls in classes
        ]

    async def list_class_students(
        self,
        *,
        class_id: uuid.UUID,
        auth: AuthContext,
    ) -> list[dict]:
        cls = await self.repo.get_class(class_id)
        if cls is None:
            raise NotFoundError("Class not found", error_code="ERR-ERP-404")

        verify_school_boundary(cls.school_id, auth)
        teacher_classes = await self.repo.list_teacher_class_ids(
            teacher_id=auth.user_id,
            school_id=auth.school_id,
        )
        verify_teacher_assignment(class_id, teacher_classes)

        rows = await self.repo.list_class_students(
            class_id=class_id,
            school_id=auth.school_id,
        )
        return [
            {
                "id": str(enrollment.student_id),
                "full_name": user.full_name,
                "email": user.email,
                "enrollment_status": enrollment.status,
            }
            for enrollment, user in rows
        ]

    async def list_teacher_submissions(
        self,
        *,
        auth: AuthContext,
        assignment_id: uuid.UUID | None,
        course_id: uuid.UUID | None,
        status: str | None,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[dict], str | None, bool]:
        rows = await self.repo.list_teacher_submissions(
            teacher_id=auth.user_id,
            school_id=auth.school_id,
            assignment_id=assignment_id,
            course_id=course_id,
            status=status,
            cursor_dt=_parse_iso_datetime(cursor),
            limit=limit,
        )
        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        grades = await self.repo.list_grades_for_submissions(
            [submission.id for submission, _, _ in rows]
        )
        grades_map = {grade.submission_id: grade for grade in grades}
        data = [
            {
                "id": str(submission.id),
                "assignment_id": str(submission.assignment_id),
                "assignment_title": assignment.title,
                "assignment_total_points": assignment.total_points,
                "student_id": str(submission.student_id),
                "student_name": student.full_name,
                "status": submission.status,
                "submitted_at": submission.submitted_at.isoformat()
                if submission.submitted_at
                else None,
                "grade": {
                    "score": float(grades_map[submission.id].score),
                    "feedback_text": grades_map[submission.id].feedback_text,
                    "published_at": grades_map[submission.id].published_at.isoformat()
                    if grades_map[submission.id].published_at
                    else None,
                }
                if submission.id in grades_map
                else None,
            }
            for submission, assignment, student in rows
        ]
        next_cursor = rows[-1][0].created_at.isoformat() if has_more and rows else None
        return data, next_cursor, has_more

    async def list_active_periods(self, auth: AuthContext) -> list[dict]:
        periods = await self.repo.list_active_periods(auth.school_id)
        return [
            {
                "id": str(period.id),
                "label": period.label,
                "date_start": str(period.date_start),
                "date_end": str(period.date_end),
            }
            for period in periods
        ]
