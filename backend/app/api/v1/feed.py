"""Parent feed endpoint."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.filtering import FilterSpec, SortSpec, parse_filters, parse_sort
from app.core.permissions import PERM_COM_NOTIFICATION_READ
from app.core.response import clamp_page_size, list_response
from app.core.search import parse_search
from app.services.communication import CommunicationService

router = APIRouter(prefix="/feed", tags=["com-feed"])


@router.get(
    "",
    summary="List parent feed items",
    response_description="Paginated activity feed",
)
async def list_feed(
    student_id: uuid.UUID | None = Query(None),
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    filters: FilterSpec = Depends(parse_filters),
    sort: SortSpec = Depends(parse_sort),
    search: str | None = Depends(parse_search),
    auth: AuthContext = Depends(requires_permission(PERM_COM_NOTIFICATION_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = CommunicationService(db)
    items, next_cursor, has_more = await service.list_feed(
        student_id=student_id,
        filters=filters,
        sort=sort,
        search=search,
        cursor=cursor,
        limit=clamp_page_size(limit),
        auth=auth,
    )
    return list_response(
        items,
        next_cursor=next_cursor,
        has_more=has_more,
        filters_applied=filters.as_dict() if filters.items else None,
        sort_by=sort.as_list() if sort.fields else None,
        search_term=search,
    )
