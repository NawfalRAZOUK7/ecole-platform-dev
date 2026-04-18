"""Rewards endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ConflictError, NotFoundError
from app.core.dependencies import AuthContext, get_current_user, requires_role
from app.core.permissions import ADM, STD, SYS
from app.core.response import clamp_page_size, list_response, success_response
from app.models.rewards import RewardBadge
from app.schemas.rewards import (
    AwardRewardRequest,
    RewardBadgeCreateRequest,
    RewardBadgeResponse,
    RewardBadgeUpdateRequest,
)
from app.services.rewards_service import RewardsService

router = APIRouter(prefix="/rewards", tags=["Rewards"])


def _serialize_badge(badge: RewardBadge) -> dict[str, object]:
    return RewardBadgeResponse(
        id=str(badge.id),
        code=badge.code,
        title_en=badge.title_en,
        title_fr=badge.title_fr,
        title_ar=badge.title_ar,
        description_en=badge.description_en,
        description_fr=badge.description_fr,
        description_ar=badge.description_ar,
        icon=badge.icon,
        criteria_type=badge.criteria_type,
        criteria_value=badge.criteria_value,
        display_order=badge.display_order,
        is_active=badge.is_active,
    ).model_dump()


@router.get("/badges", summary="List reward badge definitions")
async def list_badges(
    _auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RewardBadge).order_by(RewardBadge.display_order, RewardBadge.code)
    )
    return list_response(
        [_serialize_badge(badge) for badge in result.scalars().all()],
        has_more=False,
    )


@router.post("/badges", status_code=201, summary="Create a reward badge")
async def create_badge(
    body: RewardBadgeCreateRequest,
    _auth: AuthContext = Depends(requires_role(ADM, SYS)),
    db: AsyncSession = Depends(get_db),
):
    badge = RewardBadge(**body.model_dump())
    db.add(badge)

    try:
        await db.flush()
    except IntegrityError as exc:
        raise ConflictError(
            "Badge code already exists",
            error_code="ERR-REWARD-409",
        ) from exc

    return success_response(_serialize_badge(badge))


@router.put("/badges/{badge_id}", summary="Update a reward badge")
async def update_badge(
    badge_id: uuid.UUID,
    body: RewardBadgeUpdateRequest,
    _auth: AuthContext = Depends(requires_role(ADM, SYS)),
    db: AsyncSession = Depends(get_db),
):
    badge = await db.get(RewardBadge, badge_id)
    if badge is None:
        raise NotFoundError("Badge not found", error_code="ERR-REWARD-404")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(badge, field, value)

    try:
        await db.flush()
    except IntegrityError as exc:
        raise ConflictError(
            "Badge code already exists",
            error_code="ERR-REWARD-409",
        ) from exc

    return success_response(_serialize_badge(badge))


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
