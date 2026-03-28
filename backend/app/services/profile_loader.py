"""Loads role-specific profiles for a user."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.unit_of_work import UnitOfWork
from app.repositories.profile_loader import ProfileLoaderRepository


ROLE_PROFILE_MAP: dict[str, str] = {
    "STD": "student",
    "PAR": "parent",
    "TCH": "teacher",
    "ADM": "admin",
    "DIR": "admin",
    "CONTENT_MGR": "content_manager",
}


class ProfileLoader:
    """Loads all applicable profiles for a user based on their roles."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._repo = ProfileLoaderRepository(db)

    async def load(self, user_id: UUID, role_codes: list[str]) -> dict[str, Any]:
        """Returns {profile_type: profile_data} for all roles that have profiles.

        Example: {"teacher": TeacherProfile(...), "parent": ParentProfile(...)}
        """
        profiles: dict[str, Any] = {}
        seen_types: set[str] = set()

        for role in role_codes:
            profile_type = ROLE_PROFILE_MAP.get(role)
            if profile_type and profile_type not in seen_types:
                seen_types.add(profile_type)
                profile = await self._repo.find_profile(user_id, profile_type)
                if profile:
                    profiles[profile_type] = profile

        return profiles

    async def ensure_profile(self, user_id: UUID, school_id: UUID, role: str) -> Any:
        """Creates a profile for the role if it doesn't exist yet."""
        profile_type = ROLE_PROFILE_MAP.get(role)
        if not profile_type:
            return None
        existing = await self._repo.find_profile(user_id, profile_type)
        if existing:
            return existing

        if self.db.info.get("_uow_depth"):
            repo = ProfileLoaderRepository(self.db)
            return await repo.create_profile(user_id, school_id, profile_type)

        async with UnitOfWork(self.db) as uow:
            repo = ProfileLoaderRepository(uow.session)
            profile = await repo.create_profile(user_id, school_id, profile_type)
            await uow.commit()
            return profile
