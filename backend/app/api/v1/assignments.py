"""Assignment API endpoint: POST /assignments.

Reference: S-052 — Create assignment (TCH).
Role: TCH (PERM-LMS:assignment:create)
Validates: course exists, teacher owns the course, school boundary.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission, verify_school_boundary
from app.core.exceptions import AuthorizationError, NotFoundError
from app.core.filtering import FilterSpec, SortSpec, apply_filters, apply_sort, parse_filters, parse_sort
from app.core.response import (
    clamp_page_size,
    decode_cursor,
    encode_cursor,
    list_response,
    success_response,
)
from app.core.search import apply_search, parse_search
from app.models.lms import Assignment, Course
from app.schemas.lms import AssignmentCreateRequest
from app.services.audit import AuditService

router = APIRouter(prefix="/assignments", tags=["lms-assignments"])


def _get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


@router.post("", status_code=201, summary="Create an assignment", response_description="Created assignment record")
async def create_assignment(
    body: AssignmentCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-LMS:assignment:create")),
    db: AsyncSession = Depends(get_db),
):
    """Create an assignment for a course.

    Validates:
    1. Course exists and is in the same school
    2. Teacher owns the course
    3. Creates assignment
    """
    audit = AuditService(db)

    # 1. Validate course exists + school boundary
    course_result = await db.execute(select(Course).where(Course.id == body.course_id))
    course = course_result.scalar_one_or_none()
    if course is None:
        raise NotFoundError("Course not found", error_code="ERR-LMS-404")
    verify_school_boundary(course.school_id, auth)

    # 2. Teacher must own the course
    if course.teacher_id != auth.user_id:
        raise AuthorizationError(
            "You can only create assignments for your own courses",
            error_code="ERR-AUTHZ-001",
        )

    # 3. Create assignment
    assignment = Assignment(
        course_id=body.course_id,
        teacher_id=auth.user_id,
        title=body.title,
        description=body.description,
        due_at=body.due_at,
        total_points=body.total_points,
    )
    db.add(assignment)
    await db.flush()

    # 4. Audit
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="ASSIGNMENT_CREATED",
        outcome="success",
        target_type="assignment",
        target_id=assignment.id,
        entity_after={
            "course_id": str(body.course_id),
            "title": body.title,
            "total_points": body.total_points,
        },
        ip_address=_get_client_ip(request),
    )

    return success_response({
        "id": str(assignment.id),
        "course_id": str(assignment.course_id),
        "teacher_id": str(assignment.teacher_id),
        "title": assignment.title,
        "description": assignment.description,
        "due_at": assignment.due_at.isoformat() if assignment.due_at else None,
        "total_points": assignment.total_points,
    })


@router.get("", summary="List assignments", response_description="Paginated list of assignments")
async def list_assignments(
    course_id: uuid.UUID | None = Query(None),
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    filters: FilterSpec = Depends(parse_filters),
    sort: SortSpec = Depends(parse_sort),
    search: str | None = Depends(parse_search),
    auth: AuthContext = Depends(requires_permission("PERM-LMS:assignment:create")),
    db: AsyncSession = Depends(get_db),
):
    """List assignments with filtering, sorting, and full-text search.

    Filters: ?filter[title__like]=math&filter[total_points__gte]=10
    Sort: ?sort=-due_at,title
    Search: ?search=homework
    Legacy param course_id still supported.
    """
    page_size = clamp_page_size(limit)

    query = select(Assignment)

    if course_id is not None:
        # Verify course exists and is in same school
        course_result = await db.execute(select(Course).where(Course.id == course_id))
        course = course_result.scalar_one_or_none()
        if course is None:
            raise NotFoundError("Course not found", error_code="ERR-LMS-404")
        verify_school_boundary(course.school_id, auth)
        query = query.where(Assignment.course_id == course_id)
    else:
        # Filter by teacher's courses in this school
        query = query.join(Course).where(Course.school_id == auth.school_id)

    # Phase 3D
    query = apply_filters(query, Assignment, filters)
    if search:
        query = apply_search(query, Assignment, search)
    query = apply_sort(query, Assignment, sort, default_column=Assignment.id)

    if cursor:
        last_id, _ = decode_cursor(cursor)
        query = query.where(Assignment.id > last_id)

    query = query.limit(page_size + 1)
    result = await db.execute(query)
    assignments = list(result.scalars().all())

    has_more = len(assignments) > page_size
    if has_more:
        assignments = assignments[:page_size]

    items = [
        {
            "id": str(a.id),
            "course_id": str(a.course_id),
            "teacher_id": str(a.teacher_id),
            "title": a.title,
            "description": a.description,
            "due_at": a.due_at.isoformat() if a.due_at else None,
            "total_points": a.total_points,
        }
        for a in assignments
    ]

    next_cursor = encode_cursor(assignments[-1].id) if has_more and assignments else None
    return list_response(
        items,
        next_cursor=next_cursor,
        has_more=has_more,
        filters_applied=filters.as_dict() if filters.items else None,
        sort_by=sort.as_list() if sort.fields else None,
        search_term=search,
    )
