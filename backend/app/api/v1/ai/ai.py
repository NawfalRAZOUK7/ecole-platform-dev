"""AI & Data endpoints — writing assistance, opt-out, recommendations, KPIs."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.permissions import (
    PERM_IA_PREFERENCE_UPDATE,
    PERM_IA_RECOMMENDATION_READ,
    PERM_IA_REQUEST_READ,
    PERM_IA_WRITING_ATTEMPT_CREATE,
)
from app.core.request_utils import get_client_ip
from app.core.response import success_response
from app.schemas.ai import AIOptOutRequest, WritingAttemptRequest
from app.services.ai import AIService

router = APIRouter(tags=["ai"])


@router.post(
    "/writing-attempts",
    status_code=200,
    summary="Create writing attempt",
    response_description="AI writing feedback",
)
async def create_writing_attempt(
    body: WritingAttemptRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_IA_WRITING_ATTEMPT_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    service = AIService(db)
    return success_response(
        await service.create_writing_attempt(
            auth=auth,
            body=body,
            client_ip=get_client_ip(request),
        )
    )


@router.post(
    "/ai/preferences/opt-out",
    status_code=200,
    summary="Update AI opt-out preference",
    response_description="Updated AI preferences",
)
async def update_ai_opt_out(
    body: AIOptOutRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_IA_PREFERENCE_UPDATE)),
    db: AsyncSession = Depends(get_db),
):
    service = AIService(db)
    return success_response(
        await service.update_opt_out(
            auth=auth,
            body=body,
            client_ip=get_client_ip(request),
        )
    )


@router.get(
    "/recommendations",
    summary="Get learning recommendations",
    response_description="Personalized recommendations",
)
async def get_recommendations(
    auth: AuthContext = Depends(requires_permission(PERM_IA_RECOMMENDATION_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = AIService(db)
    return success_response(await service.get_recommendations_for_user(auth=auth))


@router.get(
    "/kpis",
    summary="Get school KPIs",
    response_description="Key performance indicators",
)
async def get_kpis(
    period: int = Query(default=7, ge=1, le=90, description="Period in days"),
    auth: AuthContext = Depends(requires_permission(PERM_IA_REQUEST_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = AIService(db)
    return success_response(
        await service.get_kpis(school_id=auth.school_id, period=period)
    )


@router.get(
    "/events/schema",
    summary="Get analytics event schema",
    response_description="Event schema definition",
)
async def get_event_schema(
    auth: AuthContext = Depends(requires_permission(PERM_IA_REQUEST_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = AIService(db)
    return success_response(await service.get_event_schema())
