"""Repository helpers for mobile game configuration workflows."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import and_, or_, select

from app.core.response import clamp_page_size, decode_cursor, encode_cursor
from app.models.games import GameConfig
from app.repositories.base import BaseRepository


class GamesRepository(BaseRepository):
    """Data access for game configuration entities."""

    async def list_configs(
        self,
        *,
        school_id: uuid.UUID,
        game_type: str | None,
        difficulty: str | None,
        subject: str | None,
        target_age: int | None,
        is_active: bool | None,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[GameConfig], str | None, bool]:
        page_size = clamp_page_size(limit)

        query = select(GameConfig).where(
            or_(GameConfig.school_id == school_id, GameConfig.school_id.is_(None))
        )

        if game_type is not None:
            query = query.where(GameConfig.game_type == game_type)
        if difficulty is not None:
            query = query.where(GameConfig.difficulty == difficulty)
        if subject is not None:
            query = query.where(GameConfig.subject == subject)
        if target_age is not None:
            query = query.where(
                GameConfig.target_age_min <= target_age,
                GameConfig.target_age_max >= target_age,
            )
        if is_active is not None:
            query = query.where(GameConfig.is_active.is_(is_active))

        query = query.order_by(
            GameConfig.created_at.desc(), GameConfig.id.desc()
        ).limit(page_size + 1)

        if cursor:
            last_id, last_created_at = decode_cursor(cursor)
            if last_created_at is not None:
                cursor_created_at = datetime.fromisoformat(last_created_at)
                query = query.where(
                    or_(
                        GameConfig.created_at < cursor_created_at,
                        and_(
                            GameConfig.created_at == cursor_created_at,
                            GameConfig.id < last_id,
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

    async def get_visible_config(
        self,
        *,
        game_id: uuid.UUID,
        school_id: uuid.UUID,
        active_only: bool = False,
    ) -> GameConfig | None:
        query = select(GameConfig).where(
            GameConfig.id == game_id,
            or_(GameConfig.school_id == school_id, GameConfig.school_id.is_(None)),
        )
        if active_only:
            query = query.where(GameConfig.is_active.is_(True))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_config(
        self,
        game_id: uuid.UUID,
    ) -> GameConfig | None:
        result = await self.db.execute(
            select(GameConfig).where(GameConfig.id == game_id)
        )
        return result.scalar_one_or_none()

    async def create_config(self, **kwargs: Any) -> GameConfig:
        config = GameConfig(**kwargs)
        self.db.add(config)
        await self.db.flush()
        return config

    async def save_config(self, config: GameConfig) -> GameConfig:
        self.db.add(config)
        await self.db.flush()
        return config
