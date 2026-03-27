"""Repository helpers for role-specific profiles and teacher dashboard data."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, select

from app.models.erp import Class, Enrollment, Period, TeacherAssignment
from app.models.iam import (
    Membership,
    ParentChildLink,
    StudentProfile,
    User,
)
from app.models.lms import Assignment, Course, Grade, Submission
from app.repositories.base import BaseRepository


class ProfileRepository(BaseRepository):
    """Data access for profile CRUD and teacher-facing dashboards."""

    async def get_user_in_school(
        self,
        *,
        user_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> User | None:
        result = await self.db.execute(
            select(User).where(User.id == user_id, User.school_id == school_id)
        )
        return result.scalar_one_or_none()

    async def get_active_membership_role(
        self,
        *,
        user_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> str:
        result = await self.db.execute(
            select(Membership.role_code).where(
                Membership.user_id == user_id,
                Membership.school_id == school_id,
                Membership.status == "active",
            )
        )
        role_code = result.scalar_one_or_none()
        return role_code or ""

    async def get_role_profile(
        self,
        *,
        profile_cls: type[Any],
        user_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> Any | None:
        result = await self.db.execute(
            select(profile_cls).where(
                profile_cls.user_id == user_id,
                profile_cls.school_id == school_id,
            )
        )
        return result.scalar_one_or_none()

    async def save_profile(self, profile: Any) -> Any:
        self.db.add(profile)
        await self.db.flush()
        await self.db.refresh(profile)
        return profile

    async def list_parent_children(
        self,
        *,
        parent_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> list[tuple[ParentChildLink, User, StudentProfile | None]]:
        result = await self.db.execute(
            select(ParentChildLink, User, StudentProfile)
            .join(User, User.id == ParentChildLink.child_user_id)
            .outerjoin(
                StudentProfile,
                and_(
                    StudentProfile.user_id == ParentChildLink.child_user_id,
                    StudentProfile.school_id == school_id,
                ),
            )
            .where(
                ParentChildLink.parent_user_id == parent_id,
                ParentChildLink.school_id == school_id,
                ParentChildLink.status == "active",
            )
            .order_by(ParentChildLink.linked_at.desc())
        )
        return [(link, user, profile) for link, user, profile in result.all()]

    async def list_teacher_class_ids(
        self,
        *,
        teacher_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> set[uuid.UUID]:
        result = await self.db.execute(
            select(TeacherAssignment.class_id).where(
                TeacherAssignment.teacher_id == teacher_id,
                TeacherAssignment.school_id == school_id,
            )
        )
        return set(result.scalars().all())

    async def list_classes_by_ids(
        self,
        *,
        class_ids: set[uuid.UUID],
        school_id: uuid.UUID,
    ) -> list[Class]:
        if not class_ids:
            return []
        result = await self.db.execute(
            select(Class)
            .where(Class.id.in_(class_ids), Class.school_id == school_id)
            .order_by(Class.name)
        )
        return list(result.scalars().all())

    async def get_active_enrollment_counts(
        self,
        *,
        class_ids: set[uuid.UUID],
        school_id: uuid.UUID,
    ) -> dict[uuid.UUID, int]:
        if not class_ids:
            return {}
        result = await self.db.execute(
            select(Enrollment.class_id, func.count())
            .where(
                Enrollment.class_id.in_(class_ids),
                Enrollment.school_id == school_id,
                Enrollment.status == "active",
            )
            .group_by(Enrollment.class_id)
        )
        return {class_id: int(count or 0) for class_id, count in result.all()}

    async def get_teacher_course_counts(
        self,
        *,
        class_ids: set[uuid.UUID],
        teacher_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> dict[uuid.UUID, int]:
        if not class_ids:
            return {}
        result = await self.db.execute(
            select(Course.class_id, func.count())
            .where(
                Course.class_id.in_(class_ids),
                Course.teacher_id == teacher_id,
                Course.school_id == school_id,
            )
            .group_by(Course.class_id)
        )
        return {class_id: int(count or 0) for class_id, count in result.all()}

    async def get_class(self, class_id: uuid.UUID) -> Class | None:
        result = await self.db.execute(select(Class).where(Class.id == class_id))
        return result.scalar_one_or_none()

    async def list_class_students(
        self,
        *,
        class_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> list[tuple[Enrollment, User]]:
        result = await self.db.execute(
            select(Enrollment, User)
            .join(User, Enrollment.student_id == User.id)
            .where(
                Enrollment.class_id == class_id,
                Enrollment.school_id == school_id,
                Enrollment.status == "active",
            )
            .order_by(User.full_name)
        )
        return [(enrollment, user) for enrollment, user in result.all()]

    async def list_teacher_submissions(
        self,
        *,
        teacher_id: uuid.UUID,
        school_id: uuid.UUID,
        assignment_id: uuid.UUID | None,
        course_id: uuid.UUID | None,
        status: str | None,
        cursor_dt: datetime | None,
        limit: int,
    ) -> list[tuple[Submission, Assignment, User]]:
        query = (
            select(Submission, Assignment, User)
            .join(Assignment, Submission.assignment_id == Assignment.id)
            .join(Course, Assignment.course_id == Course.id)
            .join(User, Submission.student_id == User.id)
            .where(
                Course.teacher_id == teacher_id,
                Course.school_id == school_id,
            )
        )
        if assignment_id:
            query = query.where(Submission.assignment_id == assignment_id)
        if course_id:
            query = query.where(Assignment.course_id == course_id)
        if status:
            query = query.where(Submission.status == status)
        if cursor_dt:
            query = query.where(Submission.created_at < cursor_dt)
        result = await self.db.execute(
            query.order_by(Submission.created_at.desc()).limit(limit + 1)
        )
        return [(submission, assignment, user) for submission, assignment, user in result.all()]

    async def list_grades_for_submissions(
        self,
        submission_ids: list[uuid.UUID],
    ) -> list[Grade]:
        if not submission_ids:
            return []
        result = await self.db.execute(
            select(Grade).where(Grade.submission_id.in_(submission_ids))
        )
        return list(result.scalars().all())

    async def list_active_periods(self, school_id: uuid.UUID) -> list[Period]:
        result = await self.db.execute(
            select(Period)
            .where(Period.school_id == school_id, Period.status == "active")
            .order_by(Period.date_start)
        )
        return list(result.scalars().all())
