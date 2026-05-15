"""Repository helpers for login history and device fingerprint lookups."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, distinct, or_, select

from app.core.response import clamp_page_size, decode_cursor, encode_cursor
from app.models.iam import LoginHistory
from app.repositories.base import BaseRepository


class LoginHistoryRepository(BaseRepository):
    """Data access for login history and device recognition."""

    async def create_login_record(self, **kwargs) -> LoginHistory:
        record = LoginHistory(**kwargs)
        self.db.add(record)
        await self.db.flush()
        return record

    async def list_user_login_history(
        self,
        user_id: uuid.UUID,
        limit: int,
        cursor: str | None,
    ) -> tuple[list[LoginHistory], str | None, bool]:
        page_size = clamp_page_size(limit)
        since = datetime.now(timezone.utc) - timedelta(days=90)

        query = (
            select(LoginHistory)
            .where(
                LoginHistory.user_id == user_id,
                LoginHistory.created_at >= since,
            )
            .order_by(LoginHistory.created_at.desc(), LoginHistory.id.desc())
            .limit(page_size + 1)
        )

        if cursor:
            last_id, last_created_at = decode_cursor(cursor)
            if last_created_at:
                cursor_created_at = datetime.fromisoformat(last_created_at)
                query = query.where(
                    or_(
                        LoginHistory.created_at < cursor_created_at,
                        and_(
                            LoginHistory.created_at == cursor_created_at,
                            LoginHistory.id < last_id,
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

    async def get_device_fingerprints(
        self,
        user_id: uuid.UUID,
        days: int = 30,
    ) -> set[str]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self.db.execute(
            select(distinct(LoginHistory.device_fingerprint)).where(
                LoginHistory.user_id == user_id,
                LoginHistory.created_at >= since,
                LoginHistory.success.is_(True),
                LoginHistory.device_fingerprint.is_not(None),
            )
        )
        return {
            fingerprint
            for fingerprint in result.scalars().all()
            if isinstance(fingerprint, str) and fingerprint
        }
