"""Parent Feed API endpoint: GET /feed.

Reference: S-067 — Parent feed (PAR).
Chronological feed of school events for a parent.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.response import (
    clamp_page_size,
    decode_cursor,
    encode_cursor,
    list_response,
)
from app.models.com import ParentFeedItem

router = APIRouter(prefix="/feed", tags=["com-feed"])


@router.get("")
async def list_feed(
    student_id: uuid.UUID | None = Query(None),
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    auth: AuthContext = Depends(requires_permission("PERM-COM:notification:read")),
    db: AsyncSession = Depends(get_db),
):
    """List parent feed items.

    PAR only — sees their own feed items.
    Optionally filtered by student_id.
    Ordered by created_at descending (newest first).
    """
    page_size = clamp_page_size(limit)

    query = select(ParentFeedItem).where(
        ParentFeedItem.school_id == auth.school_id,
        ParentFeedItem.parent_id == auth.user_id,
    )

    if student_id:
        query = query.where(ParentFeedItem.student_id == student_id)

    if cursor:
        last_id, _ = decode_cursor(cursor)
        query = query.where(ParentFeedItem.id > last_id)

    query = query.order_by(ParentFeedItem.created_at.desc()).limit(page_size + 1)
    result = await db.execute(query)
    items_list = list(result.scalars().all())

    has_more = len(items_list) > page_size
    if has_more:
        items_list = items_list[:page_size]

    items = [
        {
            "id": str(fi.id),
            "school_id": str(fi.school_id),
            "parent_id": str(fi.parent_id),
            "student_id": str(fi.student_id) if fi.student_id else None,
            "source_type": fi.source_type,
            "source_ref": fi.source_ref,
            "title": fi.title,
            "body": fi.body,
            "created_at": fi.created_at.isoformat() if fi.created_at else None,
        }
        for fi in items_list
    ]

    next_cursor = encode_cursor(items_list[-1].id) if has_more and items_list else None
    return list_response(items, next_cursor=next_cursor, has_more=has_more)
