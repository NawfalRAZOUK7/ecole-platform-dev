"""Assignment API endpoints.

Reference: S-052 — Create assignment (TCH).
Phase 9C — PDF exercise workflow: upload exercise PDF, student download.
Role: TCH (PERM-LMS:assignment:create)
Validates: course exists, teacher owns the course, school boundary.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    AuthContext,
    requires_permission,
    verify_school_boundary,
)
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
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
from app.core.storage import storage
from app.core.request_utils import get_client_ip
from app.models.erp import Enrollment
from app.models.lms import Assignment, Course
from app.schemas.lms import AssignmentCreateRequest
from app.services.audit import AuditService

router = APIRouter(prefix="/assignments", tags=["lms-assignments"])



def _assignment_to_dict(a: Assignment) -> dict:
    """Serialize assignment to dict."""
    return {
        "id": str(a.id),
        "course_id": str(a.course_id),
        "teacher_id": str(a.teacher_id),
        "title": a.title,
        "description": a.description,
        "due_at": a.due_at.isoformat() if a.due_at else None,
        "total_points": a.total_points,
        "exercise_type": a.exercise_type,
        "quiz_id": str(a.quiz_id) if a.quiz_id else None,
        "exercise_pdf_path": a.exercise_pdf_path,
    }


@router.post(
    "",
    status_code=201,
    summary="Create an assignment",
    response_description="Created assignment record",
)
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
        exercise_type=body.exercise_type,
        quiz_id=body.quiz_id,
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
            "exercise_type": body.exercise_type,
        },
        ip_address=get_client_ip(request),
    )

    return success_response(_assignment_to_dict(assignment))


@router.get(
    "", summary="List assignments", response_description="Paginated list of assignments"
)
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

    items = [_assignment_to_dict(a) for a in assignments]

    next_cursor = (
        encode_cursor(assignments[-1].id) if has_more and assignments else None
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
# Phase 9C: POST /assignments/{id}/exercise-pdf — Upload exercise PDF (TCH)
# ---------------------------------------------------------------------------
@router.post(
    "/{assignment_id}/exercise-pdf",
    status_code=201,
    summary="Upload exercise PDF for a PRINTABLE_PDF assignment",
)
async def upload_exercise_pdf(
    assignment_id: uuid.UUID,
    file: UploadFile = File(...),
    request: Request = None,
    auth: AuthContext = Depends(requires_permission("PERM-LMS:assignment:create")),
    db: AsyncSession = Depends(get_db),
):
    """Upload or replace the exercise PDF for a PRINTABLE_PDF assignment.

    Validates:
    1. Assignment exists, teacher owns it
    2. exercise_type must be PRINTABLE_PDF
    3. File must be application/pdf
    """
    audit = AuditService(db)

    # 1. Load assignment + course
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = result.scalar_one_or_none()
    if assignment is None:
        raise NotFoundError("Assignment not found", error_code="ERR-LMS-404")

    course_result = await db.execute(
        select(Course).where(Course.id == assignment.course_id)
    )
    course = course_result.scalar_one_or_none()
    if course is None:
        raise NotFoundError("Course not found", error_code="ERR-LMS-404")
    verify_school_boundary(course.school_id, auth)

    if course.teacher_id != auth.user_id:
        raise AuthorizationError(
            "You can only upload PDFs for your own assignments",
            error_code="ERR-AUTHZ-001",
        )

    # 2. Must be PRINTABLE_PDF type
    if assignment.exercise_type != "PRINTABLE_PDF":
        raise ValidationError(
            "Exercise PDF upload is only allowed for PRINTABLE_PDF assignments",
            error_code="ERR-LMS-422",
        )

    # 3. Validate PDF MIME
    mime = file.content_type or "application/octet-stream"
    if mime != "application/pdf":
        raise ValidationError(
            "Only PDF files are accepted for exercise upload",
            error_code="ERR-UPLOAD-415",
        )

    # 4. Delete old PDF if replacing
    if assignment.exercise_pdf_path:
        await storage.delete(assignment.exercise_pdf_path)

    # 5. Save new PDF
    relative_path, checksum, file_size = await storage.save(
        file.file,
        file.filename or "exercise.pdf",
        subdirectory=f"exercises/{assignment_id}",
    )

    assignment.exercise_pdf_path = relative_path
    await db.flush()

    # 6. Audit
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="EXERCISE_PDF_UPLOADED",
        outcome="success",
        target_type="assignment",
        target_id=assignment.id,
        entity_after={
            "exercise_pdf_path": relative_path,
            "checksum": checksum,
            "file_size": file_size,
        },
        ip_address=get_client_ip(request),
    )

    return success_response(
        {
            "id": str(assignment.id),
            "exercise_pdf_path": relative_path,
            "checksum": checksum,
            "file_size": file_size,
        }
    )


# ---------------------------------------------------------------------------
# Phase 9C: GET /assignments/{id}/exercise-pdf — Download exercise PDF
# ---------------------------------------------------------------------------
@router.get(
    "/{assignment_id}/exercise-pdf",
    summary="Download the exercise PDF",
    response_description="PDF file binary",
)
async def download_exercise_pdf(
    assignment_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission("PERM-LMS:assignment:create")),
    db: AsyncSession = Depends(get_db),
):
    """Download the printable exercise PDF.

    Access: teacher who owns the course, or student enrolled in the class.
    """
    # 1. Load assignment + course
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = result.scalar_one_or_none()
    if assignment is None:
        raise NotFoundError("Assignment not found", error_code="ERR-LMS-404")

    if not assignment.exercise_pdf_path:
        raise NotFoundError("No exercise PDF attached", error_code="ERR-LMS-404")

    course_result = await db.execute(
        select(Course).where(Course.id == assignment.course_id)
    )
    course = course_result.scalar_one_or_none()
    if course is None:
        raise NotFoundError("Course not found", error_code="ERR-LMS-404")
    verify_school_boundary(course.school_id, auth)

    # 2. Access control: teacher owns course OR student enrolled in the class
    if auth.role == "TCH":
        if course.teacher_id != auth.user_id:
            raise NotFoundError("Assignment not found", error_code="ERR-LMS-404")
    elif auth.role == "STD":
        enrolled = await db.execute(
            select(
                exists().where(
                    Enrollment.student_id == auth.user_id,
                    Enrollment.class_id == course.class_id,
                    Enrollment.status == "active",
                )
            )
        )
        if not enrolled.scalar():
            raise NotFoundError("Assignment not found", error_code="ERR-LMS-404")

    # 3. Serve file
    abs_path = await storage.read(assignment.exercise_pdf_path)
    return FileResponse(
        path=str(abs_path),
        media_type="application/pdf",
        filename=f"exercise_{assignment_id}.pdf",
    )
