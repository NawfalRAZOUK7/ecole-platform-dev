"""Consent API endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.permissions import PERM_COM_CONSENT_UPDATE
from app.core.request_utils import get_client_ip
from app.core.response import list_response, success_response
from app.schemas.communication import ConsentUpdateRequest
from app.services.user.gdpr import GDPRService

router = APIRouter(prefix="/consents", tags=["com-consents"])


@router.get(
    "",
    summary="List consent preferences",
    response_description="List of consent settings",
)
async def list_consents(
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    auth: AuthContext = Depends(requires_permission(PERM_COM_CONSENT_UPDATE)),
    db: AsyncSession = Depends(get_db),
):
    service = GDPRService(db)
    items, next_cursor, has_more = await service.list_consents(
        auth=auth,
        cursor=cursor,
        limit=limit,
    )
    return list_response(items, next_cursor=next_cursor, has_more=has_more)


@router.put(
    "/{consent_id}",
    summary="Update consent preference",
    response_description="Updated consent record",
)
async def update_consent(
    consent_id: uuid.UUID,
    body: ConsentUpdateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_COM_CONSENT_UPDATE)),
    db: AsyncSession = Depends(get_db),
):
    service = GDPRService(db)
    return success_response(
        await service.update_consent(
            consent_id=consent_id,
            status=body.status,
            auth=auth,
            client_ip=get_client_ip(request),
        )
    )
