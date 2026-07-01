"""Course endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.filtering import FilterSpec, SortSpec, parse_filters, parse_sort
from app.core.permissions import PERM_LMS_COURSE_PUBLISH
from app.core.request_utils import get_client_ip
from app.core.response import clamp_page_size, list_response, success_response
from app.core.search import parse_search
from app.schemas.lms import CourseCreateRequest
from app.services.lms import CourseService

router = APIRouter(prefix="/courses", tags=["lms-courses"])


@router.post(
    "",
    status_code=201,
    summary="Create a course",
    response_description="Created course record",
)
async def create_course(
    body: CourseCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_LMS_COURSE_PUBLISH)),
    db: AsyncSession = Depends(get_db),
):
    service = CourseService(db)
    return success_response(
        await service.create_course(
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "",
    summary="List courses",
    response_description="Paginated list of courses",
)
async def list_courses(
    class_id: uuid.UUID | None = Query(None),
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    filters: FilterSpec = Depends(parse_filters),
    sort: SortSpec = Depends(parse_sort),
    search: str | None = Depends(parse_search),
    auth: AuthContext = Depends(requires_permission(PERM_LMS_COURSE_PUBLISH)),
    db: AsyncSession = Depends(get_db),
):
    service = CourseService(db)
    items, next_cursor, has_more = await service.list_courses(
        class_id=class_id,
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
