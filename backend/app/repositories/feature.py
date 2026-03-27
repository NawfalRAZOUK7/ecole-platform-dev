"""Repository helpers for feature toggle CRUD."""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.models.feature import FeatureToggle
from app.repositories.base import BaseRepository


class FeatureRepository(BaseRepository):
    """Data access for feature toggle records."""

    async def get_toggle_by_feature_key(
        self,
        feature_key: str,
    ) -> FeatureToggle | None:
        result = await self.db.execute(
            select(FeatureToggle).where(FeatureToggle.feature_key == feature_key)
        )
        return result.scalar_one_or_none()

    async def get_toggle_by_id(self, toggle_id: uuid.UUID) -> FeatureToggle | None:
        result = await self.db.execute(
            select(FeatureToggle).where(FeatureToggle.id == toggle_id)
        )
        return result.scalar_one_or_none()

    async def list_toggles(self) -> list[FeatureToggle]:
        result = await self.db.execute(
            select(FeatureToggle).order_by(FeatureToggle.feature_key)
        )
        return list(result.scalars().all())

    async def create_toggle(self, toggle: FeatureToggle) -> FeatureToggle:
        self.db.add(toggle)
        await self.db.flush()
        return toggle

    async def save_toggle(self, toggle: FeatureToggle) -> FeatureToggle:
        self.db.add(toggle)
        await self.db.flush()
        return toggle

    async def delete_toggle(self, toggle: FeatureToggle) -> None:
        await self.db.delete(toggle)
        await self.db.flush()
