"""Rewards endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    AuthContext,
    get_current_user,
    requires_permission,
    requires_role,
)
from app.core.permissions import (
    ADM,
    STD,
    SUP,
    SYS,
    PERM_REWARDS_AWARD,
    PERM_REWARDS_VIEW,
)
from app.core.response import clamp_page_size, list_response, success_response
from app.schemas.rewards import AwardRewardRequest, BadgeCreateRequest
from app.services.rewards_service import RewardsService

router = APIRouter(prefix="/rewards", tags=["Rewards"])


@router.post("/award", summary="Award stars and XP to a student")
async def award_reward(
    body: AwardRewardRequest,
    auth: AuthContext = Depends(requires_permission(PERM_REWARDS_AWARD)),
    db: AsyncSession = Depends(get_db),
):
    service = RewardsService(db)
    await service.verify_student_award_access(student_id=body.student_id, auth=auth)
    return success_response(
        await service.award(
            student_id=body.student_id,
            event_type=body.event_type,
            stars=body.stars_earned,
            xp=body.xp_earned,
            source_type=body.source_type,
            source_id=body.source_id,
            metadata=body.metadata,
        )
    )


@router.get("/me", summary="Get my rewards profile")
async def get_my_rewards(
    auth: AuthContext = Depends(requires_role(STD)),
    db: AsyncSession = Depends(get_db),
):
    service = RewardsService(db)
    return success_response(await service.get_student_rewards(student_id=auth.user_id))


@router.get("/student/{student_id}", summary="Get rewards for one student")
async def get_student_rewards(
    student_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_REWARDS_VIEW)),
    db: AsyncSession = Depends(get_db),
):
    service = RewardsService(db)
    await service.verify_student_view_access(student_id=student_id, auth=auth)
    return success_response(await service.get_student_rewards(student_id=student_id))


@router.get("/student/{student_id}/history", summary="Get reward event history")
async def get_reward_history(
    student_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=100),
    auth: AuthContext = Depends(requires_permission(PERM_REWARDS_VIEW)),
    db: AsyncSession = Depends(get_db),
):
    service = RewardsService(db)
    await service.verify_student_view_access(student_id=student_id, auth=auth)
    items = await service.get_event_history(
        student_id=student_id,
        limit=clamp_page_size(limit),
    )
    return list_response(items, has_more=False)


@router.get("/leaderboard/{class_id}", summary="Get class rewards leaderboard")
async def get_rewards_leaderboard(
    class_id: uuid.UUID,
    limit: int = Query(10, ge=1, le=100),
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = RewardsService(db)
    await service.verify_class_access(class_id=class_id, auth=auth)
    items = await service.get_leaderboard(
        class_id=class_id,
        limit=clamp_page_size(limit),
    )
    return list_response(items, has_more=False)


@router.get("/badges", summary="List available reward badges")
async def list_reward_badges(
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = RewardsService(db)
    items = await service.list_badges()
    return list_response(items, has_more=False)


@router.post("/badges", status_code=201, summary="Create a reward badge")
async def create_reward_badge(
    body: BadgeCreateRequest,
    auth: AuthContext = Depends(requires_role(ADM, SUP, SYS)),
    db: AsyncSession = Depends(get_db),
):
    service = RewardsService(db)
    return success_response(await service.create_badge(body=body))
