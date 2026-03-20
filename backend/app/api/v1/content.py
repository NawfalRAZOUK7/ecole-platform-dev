"""Content Items API endpoints.

Reference:
  S-056 — GET /content-items, GET /content-items/{id} (STD, PAR)
  S-057 — POST /content-items/{id}/progress (STD)
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission, verify_school_boundary
from app.core.exceptions import NotFoundError
from app.core.response import (
    clamp_page_size,
    decode_cursor,
    encode_cursor,
    list_response,
    success_response,
)
from app.models.lms import ContentItem, ContentProgress
from app.schemas.lms import ContentProgressRequest
from app.services.audit import AuditService

router = APIRouter(prefix="/content-items", tags=["lms-content"])


def _get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


# ---------------------------------------------------------------------------
# S-056: GET /content-items — List content items (STD, PAR)
# ---------------------------------------------------------------------------
@router.get("", summary="List content items", response_description="Paginated list of learning materials")
async def list_content_items(
    content_type: str | None = Query(None),
    level_band: str | None = Query(None),
    language: str | None = Query(None),
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    auth: AuthContext = Depends(requires_permission("PERM-LMS:content:read")),
    db: AsyncSession = Depends(get_db),
):
    """List published content items.

    Filters by content_type, level_band, language.
    Shows school-specific + platform-wide content (school_id IS NULL).
    """
    page_size = clamp_page_size(limit)

    # School-specific or platform-wide content
    query = select(ContentItem).where(
        ContentItem.status == "published",
        (ContentItem.school_id == auth.school_id) | (ContentItem.school_id.is_(None)),
    )

    if content_type:
        query = query.where(ContentItem.content_type == content_type)
    if level_band:
        query = query.where(ContentItem.level_band == level_band)
    if language:
        query = query.where(ContentItem.language == language)

    if cursor:
        last_id, _ = decode_cursor(cursor)
        query = query.where(ContentItem.id > last_id)

    query = query.order_by(ContentItem.id).limit(page_size + 1)
    result = await db.execute(query)
    items_list = list(result.scalars().all())

    has_more = len(items_list) > page_size
    if has_more:
        items_list = items_list[:page_size]

    items = [
        {
            "id": str(ci.id),
            "school_id": str(ci.school_id) if ci.school_id else None,
            "title": ci.title,
            "content_type": ci.content_type,
            "level_band": ci.level_band,
            "language": ci.language,
            "status": ci.status,
        }
        for ci in items_list
    ]

    next_cursor = encode_cursor(items_list[-1].id) if has_more and items_list else None
    return list_response(items, next_cursor=next_cursor, has_more=has_more)


# ---------------------------------------------------------------------------
# S-056: GET /content-items/{id} — Get content item detail (STD, PAR)
# ---------------------------------------------------------------------------
@router.get("/{content_item_id}", summary="Get content item details", response_description="Content item with assets")
async def get_content_item(
    content_item_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission("PERM-LMS:content:read")),
    db: AsyncSession = Depends(get_db),
):
    """Get a content item by ID.

    Only published items visible. School boundary or platform-wide.
    """
    result = await db.execute(
        select(ContentItem).where(ContentItem.id == content_item_id)
    )
    ci = result.scalar_one_or_none()
    if ci is None:
        raise NotFoundError("Content item not found", error_code="ERR-LMS-404")

    # School boundary: must be same school or platform-wide (school_id IS NULL)
    if ci.school_id is not None:
        verify_school_boundary(ci.school_id, auth)

    # Only published items
    if ci.status != "published":
        raise NotFoundError("Content item not found", error_code="ERR-LMS-404")

    return success_response({
        "id": str(ci.id),
        "school_id": str(ci.school_id) if ci.school_id else None,
        "title": ci.title,
        "content_type": ci.content_type,
        "level_band": ci.level_band,
        "language": ci.language,
        "status": ci.status,
    })


# ---------------------------------------------------------------------------
# S-057: POST /content-items/{id}/progress — Track progress (STD)
# ---------------------------------------------------------------------------
@router.post("/{content_item_id}/progress", status_code=200, summary="Update content progress", response_description="Updated progress record")
async def update_content_progress(
    content_item_id: uuid.UUID,
    body: ContentProgressRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-LMS:content-progress:write")),
    db: AsyncSession = Depends(get_db),
):
    """Update student progress on a content item.

    Upsert: creates or updates progress record.
    Unique per (student_id, content_item_id).
    """
    audit = AuditService(db)

    # Validate content item exists
    ci_result = await db.execute(
        select(ContentItem).where(ContentItem.id == content_item_id)
    )
    ci = ci_result.scalar_one_or_none()
    if ci is None:
        raise NotFoundError("Content item not found", error_code="ERR-LMS-404")

    if ci.school_id is not None:
        verify_school_boundary(ci.school_id, auth)

    # Upsert progress
    existing_result = await db.execute(
        select(ContentProgress).where(
            ContentProgress.student_id == auth.user_id,
            ContentProgress.content_item_id == content_item_id,
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing is not None:
        existing.status = body.status
        await db.flush()
        progress = existing
    else:
        progress = ContentProgress(
            student_id=auth.user_id,
            content_item_id=content_item_id,
            status=body.status,
        )
        db.add(progress)
        await db.flush()

    # Audit
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="CONTENT_PROGRESS_UPDATED",
        outcome="success",
        target_type="content_progress",
        target_id=progress.id,
        entity_after={
            "content_item_id": str(content_item_id),
            "status": body.status,
        },
        ip_address=_get_client_ip(request),
    )

    return success_response({
        "id": str(progress.id),
        "student_id": str(progress.student_id),
        "content_item_id": str(progress.content_item_id),
        "status": progress.status,
    })
