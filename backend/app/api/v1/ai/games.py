"""Mobile game configuration endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, get_current_user, requires_role
from app.core.permissions import ADM, DIR, STD, SUP, SYS, TCH
from app.services.lms.student_service import get_student_age
from app.core.response import clamp_page_size, list_response, success_response
from app.schemas.ai.games import (
    GameCompletionRequest,
    GameConfigCreateRequest,
    GameConfigUpdateRequest,
)
from app.services.ai.game_service import GameService

router = APIRouter(prefix="/games", tags=["Games"])


@router.get("/configs", summary="List game configs")
async def list_game_configs(
    game_type: str | None = Query(None),
    difficulty: str | None = Query(None),
    subject: str | None = Query(None),
    target_age: int | None = Query(None, ge=0),
    is_active: bool | None = Query(None),
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Auto-inject target_age for students based on their date_of_birth
    if target_age is None and auth.role == STD:
        target_age = await get_student_age(db, auth.user_id)

    service = GameService(db)
    items, next_cursor, has_more = await service.list_configs(
        auth=auth,
        game_type=game_type,
        difficulty=difficulty,
        subject=subject,
        target_age=target_age,
        is_active=is_active,
        cursor=cursor,
        limit=clamp_page_size(limit),
    )
    return list_response(items, next_cursor=next_cursor, has_more=has_more)


@router.get("/configs/{game_id}", summary="Get one game config")
async def get_game_config(
    game_id: uuid.UUID,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = GameService(db)
    return success_response(await service.get_config(game_id=game_id, auth=auth))


@router.post("/configs", status_code=201, summary="Create game config")
async def create_game_config(
    body: GameConfigCreateRequest,
    auth: AuthContext = Depends(requires_role(TCH, DIR, ADM, SUP, SYS)),
    db: AsyncSession = Depends(get_db),
):
    service = GameService(db)
    return success_response(await service.create_config(body=body, auth=auth))


@router.put("/configs/{game_id}", summary="Update game config")
async def update_game_config(
    game_id: uuid.UUID,
    body: GameConfigUpdateRequest,
    auth: AuthContext = Depends(requires_role(TCH, DIR, ADM, SUP, SYS)),
    db: AsyncSession = Depends(get_db),
):
    service = GameService(db)
    return success_response(
        await service.update_config(game_id=game_id, body=body, auth=auth)
    )


@router.post("/configs/{game_id}/complete", summary="Complete a game config")
async def complete_game_config(
    game_id: uuid.UUID,
    body: GameCompletionRequest,
    auth: AuthContext = Depends(requires_role(STD)),
    db: AsyncSession = Depends(get_db),
):
    service = GameService(db)
    return success_response(
        await service.complete_config(game_id=game_id, body=body, auth=auth)
    )
