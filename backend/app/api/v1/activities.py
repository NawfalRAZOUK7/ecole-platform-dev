"""Activities API endpoints.

Reference:
  S-058 — GET /activities + POST /activity-sessions (STD)
  S-059 — POST /activity-sessions/{id}/complete (STD)
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.filtering import (
    FilterSpec,
    SortSpec,
    parse_filters,
    parse_sort,
)
from app.core.response import (
    clamp_page_size,
    list_response,
    success_response,
)
from app.core.search import parse_search
from app.core.permissions import (
    PERM_LMS_ACTIVITY_SESSION_COMPLETE,
    PERM_LMS_ACTIVITY_SESSION_CREATE,
)
from app.core.request_utils import get_client_ip
from app.schemas.lms import ActivitySessionCompleteRequest, ActivitySessionCreateRequest
from app.services.lms import CourseService

router = APIRouter(prefix="/activities", tags=["lms-activities"])



# ---------------------------------------------------------------------------
# S-058: GET /activities — List activities (STD)
# ---------------------------------------------------------------------------
@router.get(
    "", summary="List activities", response_description="Paginated list of activities"
)
async def list_activities(
    activity_type: str | None = Query(None, alias="type"),
    difficulty: str | None = Query(None),
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    filters: FilterSpec = Depends(parse_filters),
    sort: SortSpec = Depends(parse_sort),
    search: str | None = Depends(parse_search),
    auth: AuthContext = Depends(requires_permission(PERM_LMS_ACTIVITY_SESSION_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    """List available activities with filtering, sorting, and full-text search.

    Shows school-specific + platform-wide activities.
    Filters: ?filter[type]=quiz&filter[difficulty]=easy
    Sort: ?sort=-created_at
    Search: ?search=multiplication
    """
    service = CourseService(db)
    items, next_cursor, has_more = await service.list_activities(
        activity_type=activity_type,
        difficulty=difficulty,
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


# ---------------------------------------------------------------------------
# S-058: POST /activity-sessions — Start activity session (STD)
# ---------------------------------------------------------------------------
@router.post(
    "/sessions",
    status_code=201,
    summary="Start activity session",
    response_description="Created activity session",
)
async def create_activity_session(
    body: ActivitySessionCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_LMS_ACTIVITY_SESSION_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    """Start a new activity session.

    Validates:
    1. Activity exists (school or platform-wide)
    2. Creates session with incremented attempt_no
    """
    service = CourseService(db)
    return success_response(
        await service.create_activity_session(
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


# ---------------------------------------------------------------------------
# S-059: POST /activity-sessions/{id}/complete — Complete session (STD)
# ---------------------------------------------------------------------------
@router.post(
    "/sessions/{session_id}/complete",
    status_code=200,
    summary="Complete activity session",
    response_description="Completed session with score",
)
async def complete_activity_session(
    session_id: uuid.UUID,
    body: ActivitySessionCompleteRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_LMS_ACTIVITY_SESSION_COMPLETE)),
    db: AsyncSession = Depends(get_db),
):
    """Complete an activity session with optional score.

    Validates:
    1. Session exists and belongs to the student
    2. Session is in 'started' status
    3. Updates status to 'completed' and sets score
    """
    service = CourseService(db)
    return success_response(
        await service.complete_activity_session(
            session_id=session_id,
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )
