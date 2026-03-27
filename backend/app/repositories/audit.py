"""Repository helpers for audit log persistence and queries."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import and_, or_, select

from app.core.response import decode_cursor, encode_cursor
from app.models.audit import AuditLog
from app.repositories.base import BaseRepository


class AuditRepository(BaseRepository):
    """Data access for audit log entries."""

    async def create_log(self, **kwargs: Any) -> AuditLog:
        entry = AuditLog(**kwargs)
        self.db.add(entry)
        await self.db.flush()
        return entry

    async def list_logs(
        self,
        *,
        filters: dict[str, Any] | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> tuple[list[AuditLog], str | None, bool]:
        filters = filters or {}
        query = select(AuditLog)

        school_id = filters.get("school_id")
        actor_id = filters.get("actor_id")
        action_type = filters.get("action_type")
        target_type = filters.get("target_type")
        outcome = filters.get("outcome")
        error_code = filters.get("error_code")
        correlation_id = filters.get("correlation_id")
        from_dt = filters.get("from_dt")
        to_dt = filters.get("to_dt")

        if school_id:
            query = query.where(AuditLog.school_id == school_id)
        if actor_id:
            query = query.where(AuditLog.actor_id == actor_id)
        if action_type:
            query = query.where(AuditLog.action_type == action_type)
        if target_type:
            query = query.where(AuditLog.target_type == target_type)
        if outcome:
            query = query.where(AuditLog.outcome == outcome)
        if error_code:
            query = query.where(AuditLog.error_code == error_code)
        if correlation_id:
            query = query.where(AuditLog.correlation_id == correlation_id)
        if from_dt:
            query = query.where(AuditLog.created_at >= from_dt)
        if to_dt:
            query = query.where(AuditLog.created_at <= to_dt)

        query = query.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        if cursor:
            last_id, last_created_at = decode_cursor(cursor)
            if last_created_at:
                cursor_dt = datetime.fromisoformat(last_created_at)
                query = query.where(
                    or_(
                        AuditLog.created_at < cursor_dt,
                        and_(
                            AuditLog.created_at == cursor_dt,
                            AuditLog.id < last_id,
                        ),
                    )
                )

        result = await self.db.execute(query.limit(limit + 1))
        rows = list(result.scalars().all())
        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        next_cursor = None
        if rows and has_more:
            next_cursor = encode_cursor(rows[-1].id, rows[-1].created_at.isoformat())

        return rows, next_cursor, has_more
