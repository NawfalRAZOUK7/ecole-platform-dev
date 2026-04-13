"""Service layer for mobile game configuration and completion flows."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import AuthContext, verify_school_boundary
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.core.permissions import PLATFORM_ROLES
from app.core.unit_of_work import UnitOfWork
from app.models.games import GameConfig, GameDifficulty, GameType
from app.repositories.games import GamesRepository
from app.schemas.games import (
    GameCompletionRequest,
    GameCompletionResponse,
    GameConfigCreateRequest,
    GameConfigResponse,
    GameConfigUpdateRequest,
)
from app.schemas.rewards import BadgeResponse, StudentRewardResponse
from app.services.rewards_service import RewardsService


def _iso(value: datetime | None) -> str | None:
    return value.astimezone(UTC).isoformat() if value is not None else None


def _normalize_game_type(raw: str) -> str:
    cleaned = raw.strip().lower()
    allowed = {item.value for item in GameType}
    if cleaned not in allowed:
        raise ValidationError(
            "Unsupported game type",
            error_code="ERR-GAME-422",
            details={"allowed": sorted(allowed), "received": raw},
        )
    return cleaned


def _normalize_difficulty(raw: str) -> str:
    cleaned = raw.strip().lower()
    allowed = {item.value for item in GameDifficulty}
    if cleaned not in allowed:
        raise ValidationError(
            "Unsupported game difficulty",
            error_code="ERR-GAME-422",
            details={"allowed": sorted(allowed), "received": raw},
        )
    return cleaned


class GameService:
    """Business logic for mobile game configurations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = GamesRepository(db)

    def _to_response(self, config: GameConfig) -> dict[str, Any]:
        return GameConfigResponse(
            id=str(config.id),
            game_type=config.game_type,
            title=config.title,
            title_ar=config.title_ar,
            title_fr=config.title_fr,
            subject=config.subject,
            difficulty=config.difficulty,
            target_age_min=config.target_age_min,
            target_age_max=config.target_age_max,
            config=dict(config.config),
            reward_stars=config.reward_stars,
            reward_xp=config.reward_xp,
            school_id=str(config.school_id) if config.school_id is not None else None,
            is_active=config.is_active,
            created_at=_iso(config.created_at) or "",
            updated_at=_iso(config.updated_at),
        ).model_dump()

    def _creation_school_id(self, auth: AuthContext) -> uuid.UUID | None:
        if auth.role in PLATFORM_ROLES:
            return None
        return auth.school_id

    def _ensure_manage_access(self, config: GameConfig, auth: AuthContext) -> None:
        if config.school_id is None:
            if auth.role not in PLATFORM_ROLES:
                raise AuthorizationError(
                    "Only platform roles can manage platform game configs",
                    error_code="ERR-GAME-403",
                )
            return
        verify_school_boundary(config.school_id, auth)

    async def list_configs(
        self,
        *,
        auth: AuthContext,
        game_type: str | None,
        difficulty: str | None,
        subject: str | None,
        target_age: int | None,
        is_active: bool | None,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[dict[str, Any]], str | None, bool]:
        normalized_game_type = (
            _normalize_game_type(game_type) if game_type is not None else None
        )
        normalized_difficulty = (
            _normalize_difficulty(difficulty) if difficulty is not None else None
        )
        items, next_cursor, has_more = await self.repo.list_configs(
            school_id=auth.school_id,
            game_type=normalized_game_type,
            difficulty=normalized_difficulty,
            subject=subject,
            target_age=target_age,
            is_active=is_active,
            cursor=cursor,
            limit=limit,
        )
        return [self._to_response(item) for item in items], next_cursor, has_more

    async def get_config(
        self,
        *,
        game_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict[str, Any]:
        config = await self.repo.get_visible_config(
            game_id=game_id,
            school_id=auth.school_id,
        )
        if config is None:
            raise NotFoundError("Game config not found", error_code="ERR-GAME-404")
        return self._to_response(config)

    async def create_config(
        self,
        *,
        body: GameConfigCreateRequest,
        auth: AuthContext,
    ) -> dict[str, Any]:
        async with UnitOfWork(self.db) as uow:
            repo = GamesRepository(uow.session)
            config = await repo.create_config(
                game_type=_normalize_game_type(body.game_type),
                title=body.title,
                title_ar=body.title_ar,
                title_fr=body.title_fr,
                subject=body.subject,
                difficulty=_normalize_difficulty(body.difficulty),
                target_age_min=body.target_age_min,
                target_age_max=body.target_age_max,
                config=dict(body.config),
                reward_stars=body.reward_stars,
                reward_xp=body.reward_xp,
                school_id=self._creation_school_id(auth),
                is_active=body.is_active,
            )
            await uow.commit()
            return self._to_response(config)

    async def update_config(
        self,
        *,
        game_id: uuid.UUID,
        body: GameConfigUpdateRequest,
        auth: AuthContext,
    ) -> dict[str, Any]:
        config = await self.repo.get_config(game_id)
        if config is None:
            raise NotFoundError("Game config not found", error_code="ERR-GAME-404")
        self._ensure_manage_access(config, auth)

        updates = body.model_dump(exclude_unset=True)
        if "game_type" in updates and updates["game_type"] is not None:
            updates["game_type"] = _normalize_game_type(updates["game_type"])
        if "difficulty" in updates and updates["difficulty"] is not None:
            updates["difficulty"] = _normalize_difficulty(updates["difficulty"])
        if "config" in updates and updates["config"] is not None:
            updates["config"] = dict(updates["config"])

        for field, value in updates.items():
            setattr(config, field, value)

        async with UnitOfWork(self.db) as uow:
            repo = GamesRepository(uow.session)
            await repo.save_config(config)
            await uow.commit()
            return self._to_response(config)

    async def complete_config(
        self,
        *,
        game_id: uuid.UUID,
        body: GameCompletionRequest,
        auth: AuthContext,
    ) -> dict[str, Any]:
        config = await self.repo.get_visible_config(
            game_id=game_id,
            school_id=auth.school_id,
            active_only=True,
        )
        if config is None:
            raise NotFoundError("Game config not found", error_code="ERR-GAME-404")

        reward_payload = await RewardsService(self.db).award(
            student_id=auth.user_id,
            event_type="game_won",
            stars=config.reward_stars,
            xp=config.reward_xp,
            source_type="game",
            source_id=config.id,
            metadata={
                "score": body.score,
                "time_seconds": body.time_seconds,
                "game_type": config.game_type,
                "difficulty": config.difficulty,
                "subject": config.subject,
            },
        )

        reward = StudentRewardResponse.model_validate(
            {
                key: value
                for key, value in reward_payload.items()
                if key != "newly_earned_badges"
            }
        )
        response = GameCompletionResponse(
            reward=reward,
            newly_earned_badges=[
                BadgeResponse.model_validate(item)
                for item in reward_payload.get("newly_earned_badges", [])
            ],
        )
        return response.model_dump()
