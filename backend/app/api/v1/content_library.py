"""Content library endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.permissions import (
    PERM_CMS_CONTENT_ASSIGN,
    PERM_CMS_CONTENT_SUBMIT,
    PERM_LMS_CONTENT_READ,
)
from app.core.request_utils import get_client_ip
from app.core.response import clamp_page_size, list_response, success_response
from app.schemas.cms import ContentAssignRequest, ContentSubmitForReviewRequest
from app.services.lms import LMSService

router = APIRouter(tags=["content-library"])


@router.get("/content/library", summary="Browse content library")
async def browse_content_library(
    content_type: str | None = Query(None),
    level_band: str | None = Query(None),
    subject: str | None = Query(None),
    language: str | None = Query(None),
    origin: str | None = Query(None),
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    auth: AuthContext = Depends(requires_permission(PERM_LMS_CONTENT_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = LMSService(db)
    items, next_cursor, has_more = await service.browse_content_library(
        content_type=content_type,
        level_band=level_band,
        subject=subject,
        language=language,
        origin=origin,
        cursor=cursor,
        limit=clamp_page_size(limit),
        auth=auth,
    )
    return list_response(items, next_cursor=next_cursor, has_more=has_more)


@router.post("/content/assign", status_code=201, summary="Assign content to class")
async def assign_content_to_class(
    body: ContentAssignRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_CMS_CONTENT_ASSIGN)),
    db: AsyncSession = Depends(get_db),
):
    service = LMSService(db)
    return success_response(
        await service.assign_content_to_class(
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.delete("/content/assign/{assignment_id}", summary="Unassign content from class")
async def unassign_content(
    assignment_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_CMS_CONTENT_ASSIGN)),
    db: AsyncSession = Depends(get_db),
):
    service = LMSService(db)
    return success_response(
        await service.unassign_content(
            assignment_id=assignment_id,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.post(
    "/content/submit-for-review",
    status_code=201,
    summary="Submit content for platform review",
)
async def submit_for_review(
    body: ContentSubmitForReviewRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_CMS_CONTENT_SUBMIT)),
    db: AsyncSession = Depends(get_db),
):
    service = LMSService(db)
    return success_response(
        await service.submit_content_for_review(
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get("/content/my-submissions", summary="List my content submissions")
async def list_my_submissions(
    status: str | None = Query(None),
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    auth: AuthContext = Depends(requires_permission(PERM_CMS_CONTENT_SUBMIT)),
    db: AsyncSession = Depends(get_db),
):
    service = LMSService(db)
    items, next_cursor, has_more = await service.list_my_content_submissions(
        status=status,
        cursor=cursor,
        limit=clamp_page_size(limit),
        auth=auth,
    )
    return list_response(items, next_cursor=next_cursor, has_more=has_more)


@router.get("/classes/{class_id}/content", summary="List content assigned to class")
async def list_class_content(
    class_id: uuid.UUID,
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    auth: AuthContext = Depends(requires_permission(PERM_LMS_CONTENT_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = LMSService(db)
    items, next_cursor, has_more = await service.list_class_content(
        class_id=class_id,
        cursor=cursor,
        limit=clamp_page_size(limit),
        auth=auth,
    )
    return list_response(items, next_cursor=next_cursor, has_more=has_more)
