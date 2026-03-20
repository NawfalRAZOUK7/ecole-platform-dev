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
from app.core.filtering import FilterSpec, SortSpec, apply_filters, apply_sort, parse_filters, parse_sort
from app.core.response import (
    clamp_page_size,
    decode_cursor,
    encode_cursor,
    list_response,
)
from app.core.search import apply_search, parse_search
from app.models.com import ParentFeedItem

router = APIRouter(prefix="/feed", tags=["com-feed"])


@router.get("", summary="List parent feed items", response_description="Paginated activity feed")
async def list_feed(
    student_id: uuid.UUID | None = Query(None),
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    filters: FilterSpec = Depends(parse_filters),
    sort: SortSpec = Depends(parse_sort),
    search: str | None = Depends(parse_search),
    auth: AuthContext = Depends(requires_permission("PERM-COM:notification:read")),
    db: AsyncSession = Depends(get_db),
):
    """List parent feed items with filtering, sorting, and full-text search.

    PAR only — sees their own feed items.
    Filters: ?filter[source_type]=grade&filter[student_id]=...
    Sort: ?sort=-created_at (default)
    Search: ?search=bulletin
    Legacy param student_id still supported.
    """
    page_size = clamp_page_size(limit)

    query = select(ParentFeedItem).where(
        ParentFeedItem.school_id == auth.school_id,
        ParentFeedItem.parent_id == auth.user_id,
    )

    if student_id:
        query = query.where(ParentFeedItem.student_id == student_id)

    # Phase 3D
    query = apply_filters(query, ParentFeedItem, filters)
    if search:
        query = apply_search(query, ParentFeedItem, search)
    query = apply_sort(query, ParentFeedItem, sort, default_column=ParentFeedItem.created_at.desc())

    if cursor:
        last_id, _ = decode_cursor(cursor)
        query = query.where(ParentFeedItem.id > last_id)

    query = query.limit(page_size + 1)
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
    return list_response(
        items,
        next_cursor=next_cursor,
        has_more=has_more,
        filters_applied=filters.as_dict() if filters.items else None,
        sort_by=sort.as_list() if sort.fields else None,
        search_term=search,
    )
