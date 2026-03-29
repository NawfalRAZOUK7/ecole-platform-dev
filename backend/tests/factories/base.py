"""Base async factory utilities for SQLAlchemy models."""

from __future__ import annotations

from typing import TypeVar

import factory
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class AsyncSQLAlchemyFactory(factory.Factory):
    """Minimal factory-boy base with async SQLAlchemy persistence helpers."""

    class Meta:
        abstract = True

    @classmethod
    async def create(cls, session: AsyncSession, **kwargs) -> ModelT:
        obj = cls.build(**kwargs)
        session.add(obj)
        await session.flush()
        await session.refresh(obj)
        return obj

    @classmethod
    async def create_batch(cls, session: AsyncSession, size: int, **kwargs) -> list[ModelT]:
        return [await cls.create(session, **kwargs) for _ in range(size)]
