"""Repository helpers for dynamic role-profile loading."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select

from app.models.iam import (
    AdminProfile,
    ContentManagerProfile,
    ParentProfile,
    StudentProfile,
    TeacherProfile,
)
from app.repositories.base import BaseRepository


_PROFILE_TYPE_MAP: dict[str, type[Any]] = {
    "student": StudentProfile,
    "parent": ParentProfile,
    "teacher": TeacherProfile,
    "admin": AdminProfile,
    "content_manager": ContentManagerProfile,
}


class ProfileLoaderRepository(BaseRepository):
    """Loads and creates role-specific profile rows."""

    async def find_student_profile(self, user_id) -> StudentProfile | None:
        result = await self.db.execute(
            select(StudentProfile).where(StudentProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def find_parent_profile(self, user_id) -> ParentProfile | None:
        result = await self.db.execute(
            select(ParentProfile).where(ParentProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def find_teacher_profile(self, user_id) -> TeacherProfile | None:
        result = await self.db.execute(
            select(TeacherProfile).where(TeacherProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def find_admin_profile(self, user_id) -> AdminProfile | None:
        result = await self.db.execute(
            select(AdminProfile).where(AdminProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def find_content_manager_profile(
        self,
        user_id,
    ) -> ContentManagerProfile | None:
        result = await self.db.execute(
            select(ContentManagerProfile).where(
                ContentManagerProfile.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def find_profile(self, user_id, profile_type: str) -> Any:
        if profile_type == "student":
            return await self.find_student_profile(user_id)
        if profile_type == "parent":
            return await self.find_parent_profile(user_id)
        if profile_type == "teacher":
            return await self.find_teacher_profile(user_id)
        if profile_type == "admin":
            return await self.find_admin_profile(user_id)
        if profile_type == "content_manager":
            return await self.find_content_manager_profile(user_id)
        return None

    async def create_profile(
        self,
        user_id: uuid.UUID,
        school_id: uuid.UUID,
        profile_type: str,
    ) -> Any:
        profile_cls = _PROFILE_TYPE_MAP.get(profile_type)
        if profile_cls is None:
            return None
        profile = profile_cls(
            user_id=user_id,
            school_id=school_id,
        )
        self.db.add(profile)
        await self.db.flush()
        await self.db.refresh(profile)
        return profile
