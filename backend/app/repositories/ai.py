"""Repository helpers for AI preferences and writing attempts."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select

from app.models.ai import AIPreference, WritingAttempt
from app.models.lms import ContentProgress
from app.repositories.base import BaseRepository


class AIRepository(BaseRepository):
    """Data access for AI preference and usage records."""

    async def get_opt_out_preference(
        self,
        *,
        target_user_id: uuid.UUID,
    ) -> AIPreference | None:
        result = await self.db.execute(
            select(AIPreference).where(
                AIPreference.target_user_id == target_user_id,
                AIPreference.opt_out.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def get_ai_preference(
        self,
        *,
        user_id: uuid.UUID,
        target_user_id: uuid.UUID,
    ) -> AIPreference | None:
        result = await self.db.execute(
            select(AIPreference).where(
                AIPreference.user_id == user_id,
                AIPreference.target_user_id == target_user_id,
            )
        )
        return result.scalar_one_or_none()

    async def save_ai_preference(self, preference: AIPreference) -> AIPreference:
        self.db.add(preference)
        await self.db.flush()
        return preference

    async def create_writing_attempt(self, attempt: WritingAttempt) -> WritingAttempt:
        self.db.add(attempt)
        await self.db.flush()
        return attempt

    async def count_completed_content_progress(
        self,
        *,
        student_id: uuid.UUID,
    ) -> int:
        result = await self.db.execute(
            select(func.count()).where(
                ContentProgress.student_id == student_id,
                ContentProgress.status == "completed",
            )
        )
        return int(result.scalar() or 0)
