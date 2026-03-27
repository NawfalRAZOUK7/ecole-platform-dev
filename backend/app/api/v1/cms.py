"""CMS endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.permissions import (
    PERM_CMS_CONTENT_CREATE,
    PERM_CMS_CONTENT_DELETE,
    PERM_CMS_CONTENT_MANAGE,
    PERM_CMS_CONTENT_REVIEW,
)
from app.core.request_utils import get_client_ip
from app.core.response import clamp_page_size, list_response, success_response
from app.schemas.cms import (
    CmsContentCreateRequest,
    CmsContentUpdateRequest,
    ReviewDecisionRequest,
)
from app.services.cms import CMSService

router = APIRouter(prefix="/cms", tags=["cms"])


@router.post("/content", status_code=201, summary="Create platform content")
async def create_cms_content(
    body: CmsContentCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_CMS_CONTENT_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    service = CMSService(db)
    return success_response(
        await service.create_platform_content(
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get("/content", summary="List platform content")
async def list_cms_content(
    content_type: str | None = Query(None),
    level_band: str | None = Query(None),
    subject: str | None = Query(None),
    status: str | None = Query(None),
    origin: str | None = Query(None),
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    auth: AuthContext = Depends(requires_permission(PERM_CMS_CONTENT_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    service = CMSService(db)
    items, next_cursor, has_more = await service.list_platform_content(
        content_type=content_type,
        level_band=level_band,
        subject=subject,
        status=status,
        origin=origin,
        cursor=cursor,
        limit=clamp_page_size(limit),
    )
    return list_response(items, next_cursor=next_cursor, has_more=has_more)


@router.put("/content/{content_id}", summary="Update platform content")
async def update_cms_content(
    content_id: uuid.UUID,
    body: CmsContentUpdateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_CMS_CONTENT_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    service = CMSService(db)
    return success_response(
        await service.update_platform_content(
            content_id=content_id,
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.delete("/content/{content_id}", summary="Archive platform content")
async def delete_cms_content(
    content_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_CMS_CONTENT_DELETE)),
    db: AsyncSession = Depends(get_db),
):
    service = CMSService(db)
    return success_response(
        await service.archive_platform_content(
            content_id=content_id,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get("/submissions", summary="List teacher submissions for review")
async def list_submissions(
    status: str | None = Query(None),
    subject: str | None = Query(None),
    level_band: str | None = Query(None),
    school_id: str | None = Query(None),
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    auth: AuthContext = Depends(requires_permission(PERM_CMS_CONTENT_REVIEW)),
    db: AsyncSession = Depends(get_db),
):
    service = CMSService(db)
    items, next_cursor, has_more = await service.list_review_submissions(
        status=status,
        subject=subject,
        level_band=level_band,
        school_id=school_id,
        cursor=cursor,
        limit=clamp_page_size(limit),
    )
    return list_response(items, next_cursor=next_cursor, has_more=has_more)


@router.post("/submissions/{submission_id}/review", summary="Review a teacher submission")
async def review_submission(
    submission_id: uuid.UUID,
    body: ReviewDecisionRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_CMS_CONTENT_REVIEW)),
    db: AsyncSession = Depends(get_db),
):
    service = CMSService(db)
    return success_response(
        await service.review_submission(
            submission_id=submission_id,
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )
