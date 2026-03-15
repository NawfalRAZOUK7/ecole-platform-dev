"""Notification API endpoint: GET /notifications.

Reference: S-065 — List notifications (PAR, TCH).
PAR sees own notifications. TCH sees school notifications.
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
from app.models.com import Notification

router = APIRouter(prefix="/notifications", tags=["com-notifications"])


@router.get("")
async def list_notifications(
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    auth: AuthContext = Depends(requires_permission("PERM-COM:notification:read")),
    db: AsyncSession = Depends(get_db),
):
    """List notifications.

    PAR: sees own notifications only (parent_id = user_id).
    TCH/ADM: sees all school notifications.
    """
    page_size = clamp_page_size(limit)

    query = select(Notification).where(Notification.school_id == auth.school_id)

    # PAR: filter to own notifications
    if auth.role == "PAR":
        query = query.where(Notification.parent_id == auth.user_id)

    if cursor:
        last_id, _ = decode_cursor(cursor)
        query = query.where(Notification.id > last_id)

    # Newest first
    query = query.order_by(Notification.created_at.desc()).limit(page_size + 1)
    result = await db.execute(query)
    notifications = list(result.scalars().all())

    has_more = len(notifications) > page_size
    if has_more:
        notifications = notifications[:page_size]

    items = [
        {
            "id": str(n.id),
            "school_id": str(n.school_id),
            "parent_id": str(n.parent_id),
            "event_ref": n.event_ref,
            "title": n.title,
            "body": n.body,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in notifications
    ]

    next_cursor = encode_cursor(notifications[-1].id) if has_more and notifications else None
    return list_response(items, next_cursor=next_cursor, has_more=has_more)
