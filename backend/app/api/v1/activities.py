"""Activities API endpoints.

Reference:
  S-058 — GET /activities + POST /activity-sessions (STD)
  S-059 — POST /activity-sessions/{id}/complete (STD)
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission, verify_school_boundary
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.filtering import FilterSpec, SortSpec, apply_filters, apply_sort, parse_filters, parse_sort
from app.core.response import (
    clamp_page_size,
    decode_cursor,
    encode_cursor,
    list_response,
    success_response,
)
from app.core.search import apply_search, parse_search
from app.models.lms import Activity, ActivitySession
from app.schemas.lms import ActivitySessionCompleteRequest, ActivitySessionCreateRequest
from app.services.audit import AuditService

router = APIRouter(prefix="/activities", tags=["lms-activities"])


def _get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


# ---------------------------------------------------------------------------
# S-058: GET /activities — List activities (STD)
# ---------------------------------------------------------------------------
@router.get("", summary="List activities", response_description="Paginated list of activities")
async def list_activities(
    activity_type: str | None = Query(None, alias="type"),
    difficulty: str | None = Query(None),
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    filters: FilterSpec = Depends(parse_filters),
    sort: SortSpec = Depends(parse_sort),
    search: str | None = Depends(parse_search),
    auth: AuthContext = Depends(requires_permission("PERM-LMS:activity-session:create")),
    db: AsyncSession = Depends(get_db),
):
    """List available activities with filtering, sorting, and full-text search.

    Shows school-specific + platform-wide activities.
    Filters: ?filter[type]=quiz&filter[difficulty]=easy
    Sort: ?sort=-created_at
    Search: ?search=multiplication
    """
    page_size = clamp_page_size(limit)

    query = select(Activity).where(
        (Activity.school_id == auth.school_id) | (Activity.school_id.is_(None))
    )

    # Legacy explicit filters
    if activity_type:
        query = query.where(Activity.type == activity_type)
    if difficulty:
        query = query.where(Activity.difficulty == difficulty)

    # Phase 3D
    query = apply_filters(query, Activity, filters)
    if search:
        query = apply_search(query, Activity, search)
    query = apply_sort(query, Activity, sort, default_column=Activity.id)

    if cursor:
        last_id, _ = decode_cursor(cursor)
        query = query.where(Activity.id > last_id)

    query = query.limit(page_size + 1)
    result = await db.execute(query)
    activities = list(result.scalars().all())

    has_more = len(activities) > page_size
    if has_more:
        activities = activities[:page_size]

    items = [
        {
            "id": str(a.id),
            "school_id": str(a.school_id) if a.school_id else None,
            "type": a.type,
            "difficulty": a.difficulty,
            "title": a.title,
            "pedagogical_objective": a.pedagogical_objective,
        }
        for a in activities
    ]

    next_cursor = encode_cursor(activities[-1].id) if has_more and activities else None
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
@router.post("/sessions", status_code=201, summary="Start activity session", response_description="Created activity session")
async def create_activity_session(
    body: ActivitySessionCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-LMS:activity-session:create")),
    db: AsyncSession = Depends(get_db),
):
    """Start a new activity session.

    Validates:
    1. Activity exists (school or platform-wide)
    2. Creates session with incremented attempt_no
    """
    audit = AuditService(db)

    # 1. Validate activity exists
    activity_result = await db.execute(
        select(Activity).where(Activity.id == body.activity_id)
    )
    activity = activity_result.scalar_one_or_none()
    if activity is None:
        raise NotFoundError("Activity not found", error_code="ERR-LMS-404")

    if activity.school_id is not None:
        verify_school_boundary(activity.school_id, auth)

    # 2. Get max attempt_no for this student+activity
    max_attempt_result = await db.execute(
        select(func.coalesce(func.max(ActivitySession.attempt_no), 0)).where(
            ActivitySession.student_id == auth.user_id,
            ActivitySession.activity_id == body.activity_id,
        )
    )
    max_attempt = max_attempt_result.scalar() or 0

    # 3. Create session
    session = ActivitySession(
        student_id=auth.user_id,
        activity_id=body.activity_id,
        status="started",
        attempt_no=max_attempt + 1,
    )
    db.add(session)
    await db.flush()

    # 4. Audit
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="ACTIVITY_SESSION_STARTED",
        outcome="success",
        target_type="activity_session",
        target_id=session.id,
        entity_after={
            "activity_id": str(body.activity_id),
            "attempt_no": session.attempt_no,
        },
        ip_address=_get_client_ip(request),
    )

    return success_response({
        "id": str(session.id),
        "student_id": str(session.student_id),
        "activity_id": str(session.activity_id),
        "status": session.status,
        "score": None,
        "attempt_no": session.attempt_no,
    })


# ---------------------------------------------------------------------------
# S-059: POST /activity-sessions/{id}/complete — Complete session (STD)
# ---------------------------------------------------------------------------
@router.post("/sessions/{session_id}/complete", status_code=200, summary="Complete activity session", response_description="Completed session with score")
async def complete_activity_session(
    session_id: uuid.UUID,
    body: ActivitySessionCompleteRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-LMS:activity-session:complete")),
    db: AsyncSession = Depends(get_db),
):
    """Complete an activity session with optional score.

    Validates:
    1. Session exists and belongs to the student
    2. Session is in 'started' status
    3. Updates status to 'completed' and sets score
    """
    audit = AuditService(db)

    # 1. Validate session exists
    sess_result = await db.execute(
        select(ActivitySession).where(ActivitySession.id == session_id)
    )
    session = sess_result.scalar_one_or_none()
    if session is None:
        raise NotFoundError("Activity session not found", error_code="ERR-LMS-404")

    # Must be the student's own session
    if session.student_id != auth.user_id:
        raise NotFoundError("Activity session not found", error_code="ERR-LMS-404")

    # 2. Must be started
    if session.status != "started":
        raise ConflictError(
            "Session is not in started status",
            error_code="ERR-LMS-409",
            details={"current_status": session.status},
        )

    # 3. Complete session
    session.status = "completed"
    if body.score is not None:
        session.score = body.score
    await db.flush()

    # 4. Audit
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="ACTIVITY_SESSION_COMPLETED",
        outcome="success",
        target_type="activity_session",
        target_id=session.id,
        entity_after={
            "status": "completed",
            "score": float(body.score) if body.score is not None else None,
        },
        ip_address=_get_client_ip(request),
    )

    return success_response({
        "id": str(session.id),
        "student_id": str(session.student_id),
        "activity_id": str(session.activity_id),
        "status": session.status,
        "score": float(session.score) if session.score is not None else None,
        "attempt_no": session.attempt_no,
    })
