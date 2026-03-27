"""Course API endpoint: POST /courses.

Reference: S-051 — Create course (TCH).
Role: TCH (PERM-LMS:course:publish)
Validates: class exists, teacher assignment (ABAC), school boundary.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    AuthContext,
    get_teacher_class_ids,
    requires_permission,
    verify_school_boundary,
    verify_teacher_assignment,
)
from app.core.exceptions import NotFoundError
from app.core.filtering import (
    FilterSpec,
    SortSpec,
    apply_filters,
    apply_sort,
    parse_filters,
    parse_sort,
)
from app.core.response import (
    clamp_page_size,
    decode_cursor,
    encode_cursor,
    list_response,
    success_response,
)
from app.core.search import apply_search, parse_search
from app.core.request_utils import get_client_ip
from app.models.erp import Class
from app.models.lms import Course
from app.schemas.lms import CourseCreateRequest
from app.services.audit import AuditService

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
    auth: AuthContext = Depends(requires_permission("PERM-LMS:course:publish")),
    db: AsyncSession = Depends(get_db),
):
    """Create a course for a class.

    Validates:
    1. Class exists and is in the same school
    2. Teacher is assigned to the class (ABAC)
    3. Creates course
    """
    audit = AuditService(db)

    # 1. Validate class exists + school boundary
    class_result = await db.execute(select(Class).where(Class.id == body.class_id))
    cls = class_result.scalar_one_or_none()
    if cls is None:
        raise NotFoundError("Class not found", error_code="ERR-LMS-404")
    verify_school_boundary(cls.school_id, auth)

    # 2. ABAC: Teacher must be assigned to this class
    teacher_classes = await get_teacher_class_ids(auth.user_id, auth.school_id, db)
    verify_teacher_assignment(body.class_id, teacher_classes)

    # 3. Create course
    course = Course(
        school_id=auth.school_id,
        class_id=body.class_id,
        teacher_id=auth.user_id,
        title=body.title,
        description=body.description,
        status=body.status,
    )
    db.add(course)
    await db.flush()

    # 4. Audit
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="COURSE_CREATED",
        outcome="success",
        target_type="course",
        target_id=course.id,
        entity_after={
            "class_id": str(body.class_id),
            "title": body.title,
            "status": body.status,
        },
        ip_address=get_client_ip(request),
    )

    return success_response(
        {
            "id": str(course.id),
            "school_id": str(course.school_id),
            "class_id": str(course.class_id),
            "teacher_id": str(course.teacher_id),
            "title": course.title,
            "description": course.description,
            "status": course.status,
        }
    )


@router.get(
    "", summary="List courses", response_description="Paginated list of courses"
)
async def list_courses(
    class_id: uuid.UUID | None = Query(None),
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    filters: FilterSpec = Depends(parse_filters),
    sort: SortSpec = Depends(parse_sort),
    search: str | None = Depends(parse_search),
    auth: AuthContext = Depends(requires_permission("PERM-LMS:course:publish")),
    db: AsyncSession = Depends(get_db),
):
    """List courses with filtering, sorting, and full-text search.

    TCH: only sees courses for assigned classes.
    Filters: ?filter[status]=published&filter[title__like]=math
    Sort: ?sort=-created_at,title
    Search: ?search=mathematiques
    """
    page_size = clamp_page_size(limit)

    query = select(Course).where(Course.school_id == auth.school_id)

    # Filter by class if specified
    if class_id is not None:
        query = query.where(Course.class_id == class_id)

    # ABAC: Teacher only sees assigned classes
    if auth.role == "TCH":
        teacher_classes = await get_teacher_class_ids(auth.user_id, auth.school_id, db)
        if teacher_classes:
            query = query.where(Course.class_id.in_(teacher_classes))
        else:
            return list_response([], next_cursor=None, has_more=False)

    # Phase 3D: filters, search, sort
    query = apply_filters(query, Course, filters)
    if search:
        query = apply_search(query, Course, search)
    query = apply_sort(query, Course, sort, default_column=Course.id)

    # Cursor pagination
    if cursor:
        last_id, _ = decode_cursor(cursor)
        query = query.where(Course.id > last_id)

    query = query.limit(page_size + 1)
    result = await db.execute(query)
    courses = list(result.scalars().all())

    has_more = len(courses) > page_size
    if has_more:
        courses = courses[:page_size]

    items = [
        {
            "id": str(c.id),
            "school_id": str(c.school_id),
            "class_id": str(c.class_id),
            "teacher_id": str(c.teacher_id),
            "title": c.title,
            "description": c.description,
            "status": c.status,
        }
        for c in courses
    ]

    next_cursor = encode_cursor(courses[-1].id) if has_more and courses else None
    return list_response(
        items,
        next_cursor=next_cursor,
        has_more=has_more,
        filters_applied=filters.as_dict() if filters.items else None,
        sort_by=sort.as_list() if sort.fields else None,
        search_term=search,
    )
