"""Rewards endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, get_current_user, requires_role
from app.core.permissions import STD
from app.core.response import clamp_page_size, list_response, success_response
from app.schemas.rewards import AwardRewardRequest
from app.services.rewards_service import RewardsService

router = APIRouter(prefix="/rewards", tags=["Rewards"])


@router.post("/award", summary="Award stars and XP to a student")
async def award_reward(
    body: AwardRewardRequest,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = RewardsService(db)
    await service.verify_student_award_access(student_id=body.student_id, auth=auth)
    return success_response(
        await service.award(
            student_id=body.student_id,
            event_type=body.event_type,
            stars=body.stars,
            xp=body.xp,
            source_type=body.source_type,
            source_id=body.source_id,
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
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = RewardsService(db)
    await service.verify_student_view_access(student_id=student_id, auth=auth)
    return success_response(await service.get_student_rewards(student_id=student_id))


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
