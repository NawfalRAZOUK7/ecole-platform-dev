"""Shared repository base class."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    """Base repository with shared DB session."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
