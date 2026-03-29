"""Repository helpers for school entities."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import and_, or_, select

from app.core.response import clamp_page_size, decode_cursor, encode_cursor
from app.models.school import School
from app.repositories.base import BaseRepository


class SchoolRepository(BaseRepository):
    """Persistence helpers for the schools table."""

    async def create_school(self, data: dict[str, Any]) -> School:
        school = School(**data)
        self.db.add(school)
        await self.db.flush()
        return school

    async def get_school(
        self,
        school_id: uuid.UUID,
        *,
        include_deleted: bool = False,
    ) -> School | None:
        query = select(School).where(School.id == school_id)
        if not include_deleted:
            query = query.where(School.deleted_at.is_(None))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_schools(
        self,
        cursor: str | None,
        limit: int,
        filters: dict[str, Any] | None = None,
    ) -> tuple[list[School], str | None, bool]:
        filters = filters or {}
        page_size = clamp_page_size(limit)
        include_deleted = bool(filters.get("include_deleted"))

        query = select(School)
        if not include_deleted:
            query = query.where(School.deleted_at.is_(None))
        if status := filters.get("status"):
            query = query.where(School.status == status)
        if city := filters.get("city"):
            query = query.where(School.city == city)

        query = query.order_by(School.created_at.desc(), School.id.desc()).limit(
            page_size + 1
        )

        if cursor:
            last_id, last_created_at = decode_cursor(cursor)
            if last_created_at:
                cursor_created_at = datetime.fromisoformat(last_created_at)
                query = query.where(
                    or_(
                        School.created_at < cursor_created_at,
                        and_(
                            School.created_at == cursor_created_at,
                            School.id < last_id,
                        ),
                    )
                )

        result = await self.db.execute(query)
        items = list(result.scalars().all())
        has_more = len(items) > page_size
        if has_more:
            items = items[:page_size]

        next_cursor = None
        if items and has_more:
            last_item = items[-1]
            next_cursor = encode_cursor(last_item.id, last_item.created_at.isoformat())

        return items, next_cursor, has_more

    async def update_school(
        self,
        school_id: uuid.UUID,
        data: dict[str, Any],
    ) -> School | None:
        school = await self.get_school(school_id, include_deleted=True)
        if school is None:
            return None
        for field, value in data.items():
            setattr(school, field, value)
        self.db.add(school)
        await self.db.flush()
        return school

    async def soft_delete_school(
        self,
        school_id: uuid.UUID,
    ) -> School | None:
        school = await self.get_school(school_id, include_deleted=False)
        if school is None:
            return None
        school.soft_delete()
        self.db.add(school)
        await self.db.flush()
        return school
