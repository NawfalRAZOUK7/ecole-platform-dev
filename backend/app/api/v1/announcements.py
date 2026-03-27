"""Announcement endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.permissions import (
    PERM_COM_ANNOUNCEMENT_CREATE,
    PERM_COM_ANNOUNCEMENT_PUBLISH,
    PERM_COM_ANNOUNCEMENT_READ,
)
from app.core.request_utils import get_client_ip
from app.core.response import clamp_page_size, list_response, success_response
from app.schemas.com import AnnouncementCreateRequest, AnnouncementUpdateRequest
from app.services.cms import CMSService

router = APIRouter(prefix="/announcements", tags=["announcements"])


@router.post(
    "",
    status_code=201,
    summary="Create announcement",
    response_description="Created announcement (draft)",
)
async def create_announcement(
    body: AnnouncementCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_COM_ANNOUNCEMENT_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    service = CMSService(db)
    return success_response(
        await service.create_announcement(
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "",
    summary="List announcements",
    response_description="Paginated list of announcements",
)
async def list_announcements(
    status: str | None = Query(None, pattern="^(DRAFT|PUBLISHED|ARCHIVED)$"),
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None),
    auth: AuthContext = Depends(requires_permission(PERM_COM_ANNOUNCEMENT_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = CMSService(db)
    items, next_cursor, has_more = await service.list_announcements(
        status=status,
        cursor=cursor,
        limit=clamp_page_size(limit),
        auth=auth,
    )
    return list_response(items, next_cursor=next_cursor, has_more=has_more)


@router.put(
    "/{announcement_id}",
    summary="Update draft announcement",
    response_description="Updated announcement",
)
async def update_announcement(
    announcement_id: uuid.UUID,
    body: AnnouncementUpdateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_COM_ANNOUNCEMENT_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    service = CMSService(db)
    return success_response(
        await service.update_announcement(
            announcement_id=announcement_id,
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.post(
    "/{announcement_id}/publish",
    summary="Publish announcement",
    response_description="Published announcement + notification summary",
)
async def publish_announcement(
    announcement_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_COM_ANNOUNCEMENT_PUBLISH)),
    db: AsyncSession = Depends(get_db),
):
    service = CMSService(db)
    return success_response(
        await service.publish_announcement(
            announcement_id=announcement_id,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )
