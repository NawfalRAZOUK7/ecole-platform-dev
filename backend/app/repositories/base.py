"""Shared repository base class."""

from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    """Base repository with shared DB session and school-scoping helpers."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _scoped_query(self, model_class, school_id) -> Select:
        """Create a select query pre-filtered to a single school."""
        return select(model_class).where(model_class.school_id == school_id)

    def _scoped_exists(self, model_class, entity_id, school_id) -> Select:
        """Create a scoped lookup query for one entity within a school."""
        return (
            select(model_class)
            .where(model_class.id == entity_id)
            .where(model_class.school_id == school_id)
        )
