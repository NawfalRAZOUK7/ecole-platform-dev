"""Assessment API endpoints.

Reference: S-060 — Assessment CRUD (TCH create/publish, ADM read, STD submit result).
Roles:
  TCH/ADM — PERM-LMS:assessment:create (create assessment)
  TCH/ADM — PERM-LMS:assessment:publish (publish assessment)
  STD     — PERM-LMS:assessment:submit (submit result)
  STD/ADM — PERM-LMS:assessment:read (list/get assessments)
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
from app.core.exceptions import AuthorizationError, ConflictError, NotFoundError, ValidationError
from app.core.filtering import FilterSpec, SortSpec, apply_filters, apply_sort, parse_filters, parse_sort
from app.core.response import (
    clamp_page_size,
    decode_cursor,
    encode_cursor,
    list_response,
    success_response,
)
from app.core.search import apply_search, parse_search
from app.models.erp import Class
from app.models.lms import Assessment, AssessmentResult
from app.schemas.lms import AssessmentCreateRequest, AssessmentResultSubmitRequest
from app.services.audit import AuditService

router = APIRouter(prefix="/assessments", tags=["lms-assessments"])


def _get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


# ---------------------------------------------------------------------------
# POST /assessments — Create assessment (TCH, ADM)
# ---------------------------------------------------------------------------
@router.post("", status_code=201, summary="Create an assessment", response_description="Created assessment record")
async def create_assessment(
    body: AssessmentCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-LMS:assessment:create")),
    db: AsyncSession = Depends(get_db),
):
    """Create a formal assessment for a class.

    Validates:
    1. Class exists and is in the same school
    2. TCH: must be assigned to the class (ABAC)
    """
    audit = AuditService(db)

    # 1. Validate class + school boundary
    class_result = await db.execute(select(Class).where(Class.id == body.class_id))
    cls = class_result.scalar_one_or_none()
    if cls is None:
        raise NotFoundError("Class not found", error_code="ERR-LMS-404")
    verify_school_boundary(cls.school_id, auth)

    # 2. ABAC: Teacher must be assigned
    if auth.role == "TCH":
        teacher_classes = await get_teacher_class_ids(auth.user_id, auth.school_id, db)
        verify_teacher_assignment(body.class_id, teacher_classes)

    # 3. Create assessment
    assessment = Assessment(
        class_id=body.class_id,
        teacher_id=auth.user_id,
        title=body.title,
        due_at=body.due_at,
        window_end=body.window_end,
        total_points=body.total_points,
        status=body.status,
    )
    db.add(assessment)
    await db.flush()

    # 4. Audit
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="ASSESSMENT_CREATED",
        outcome="success",
        target_type="assessment",
        target_id=assessment.id,
        entity_after={
            "class_id": str(body.class_id),
            "title": body.title,
            "status": body.status,
        },
        ip_address=_get_client_ip(request),
    )

    return success_response({
        "id": str(assessment.id),
        "class_id": str(assessment.class_id),
        "teacher_id": str(assessment.teacher_id),
        "title": assessment.title,
        "due_at": assessment.due_at.isoformat() if assessment.due_at else None,
        "window_end": assessment.window_end.isoformat() if assessment.window_end else None,
        "total_points": assessment.total_points,
        "status": assessment.status,
    })


# ---------------------------------------------------------------------------
# GET /assessments — List assessments (STD, ADM, TCH)
# ---------------------------------------------------------------------------
@router.get("", summary="List assessments", response_description="Paginated list of assessments")
async def list_assessments(
    class_id: uuid.UUID | None = Query(None),
    status: str | None = Query(None),
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    filters: FilterSpec = Depends(parse_filters),
    sort: SortSpec = Depends(parse_sort),
    search: str | None = Depends(parse_search),
    auth: AuthContext = Depends(requires_permission("PERM-LMS:assessment:read")),
    db: AsyncSession = Depends(get_db),
):
    """List assessments with filtering, sorting, and full-text search.

    Filters: ?filter[status]=published&filter[title__like]=exam
    Sort: ?sort=-due_at
    Search: ?search=final
    Legacy params class_id, status still supported.
    """
    page_size = clamp_page_size(limit)

    query = select(Assessment).join(Class).where(Class.school_id == auth.school_id)

    if class_id:
        query = query.where(Assessment.class_id == class_id)
    if status:
        query = query.where(Assessment.status == status)

    # ABAC: TCH sees only assigned classes
    if auth.role == "TCH":
        teacher_classes = await get_teacher_class_ids(auth.user_id, auth.school_id, db)
        if teacher_classes:
            query = query.where(Assessment.class_id.in_(teacher_classes))
        else:
            return list_response([], next_cursor=None, has_more=False)

    # Phase 3D
    query = apply_filters(query, Assessment, filters)
    if search:
        query = apply_search(query, Assessment, search)
    query = apply_sort(query, Assessment, sort, default_column=Assessment.id)

    if cursor:
        last_id, _ = decode_cursor(cursor)
        query = query.where(Assessment.id > last_id)

    query = query.limit(page_size + 1)
    result = await db.execute(query)
    assessments = list(result.scalars().all())

    has_more = len(assessments) > page_size
    if has_more:
        assessments = assessments[:page_size]

    items = [
        {
            "id": str(a.id),
            "class_id": str(a.class_id),
            "teacher_id": str(a.teacher_id),
            "title": a.title,
            "due_at": a.due_at.isoformat() if a.due_at else None,
            "window_end": a.window_end.isoformat() if a.window_end else None,
            "total_points": a.total_points,
            "status": a.status,
        }
        for a in assessments
    ]

    next_cursor = encode_cursor(assessments[-1].id) if has_more and assessments else None
    return list_response(
        items,
        next_cursor=next_cursor,
        has_more=has_more,
        filters_applied=filters.as_dict() if filters.items else None,
        sort_by=sort.as_list() if sort.fields else None,
        search_term=search,
    )


# ---------------------------------------------------------------------------
# POST /assessments/{id}/publish — Publish assessment (TCH, ADM)
# ---------------------------------------------------------------------------
@router.post("/{assessment_id}/publish", status_code=200, summary="Publish an assessment", response_description="Published assessment")
async def publish_assessment(
    assessment_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-LMS:assessment:publish")),
    db: AsyncSession = Depends(get_db),
):
    """Publish an assessment (change status from draft to published)."""
    audit = AuditService(db)

    result = await db.execute(
        select(Assessment).where(Assessment.id == assessment_id)
    )
    assessment = result.scalar_one_or_none()
    if assessment is None:
        raise NotFoundError("Assessment not found", error_code="ERR-LMS-404")

    # School boundary via class
    class_result = await db.execute(select(Class).where(Class.id == assessment.class_id))
    cls = class_result.scalar_one_or_none()
    if cls is None:
        raise NotFoundError("Class not found", error_code="ERR-LMS-404")
    verify_school_boundary(cls.school_id, auth)

    if assessment.status != "draft":
        raise ConflictError(
            "Assessment can only be published from draft status",
            error_code="ERR-LMS-409",
            details={"current_status": assessment.status},
        )

    assessment.status = "published"
    await db.flush()

    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="ASSESSMENT_PUBLISHED",
        outcome="success",
        target_type="assessment",
        target_id=assessment.id,
        entity_after={"status": "published"},
        ip_address=_get_client_ip(request),
    )

    return success_response({
        "id": str(assessment.id),
        "class_id": str(assessment.class_id),
        "teacher_id": str(assessment.teacher_id),
        "title": assessment.title,
        "due_at": assessment.due_at.isoformat() if assessment.due_at else None,
        "window_end": assessment.window_end.isoformat() if assessment.window_end else None,
        "total_points": assessment.total_points,
        "status": assessment.status,
    })


# ---------------------------------------------------------------------------
# POST /assessments/{id}/results — Submit assessment result (STD)
# ---------------------------------------------------------------------------
@router.post("/{assessment_id}/results", status_code=201, summary="Submit assessment result", response_description="Assessment result record")
async def submit_assessment_result(
    assessment_id: uuid.UUID,
    body: AssessmentResultSubmitRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-LMS:assessment:submit")),
    db: AsyncSession = Depends(get_db),
):
    """Submit a result for an assessment (student self-report or auto-graded).

    Validates:
    1. Assessment exists and is published
    2. No duplicate result for same student+assessment (idempotent)
    """
    audit = AuditService(db)

    # 1. Validate assessment exists
    assess_result = await db.execute(
        select(Assessment).where(Assessment.id == assessment_id)
    )
    assessment = assess_result.scalar_one_or_none()
    if assessment is None:
        raise NotFoundError("Assessment not found", error_code="ERR-LMS-404")

    # School boundary via class
    class_result = await db.execute(select(Class).where(Class.id == assessment.class_id))
    cls = class_result.scalar_one_or_none()
    if cls is None:
        raise NotFoundError("Class not found", error_code="ERR-LMS-404")
    verify_school_boundary(cls.school_id, auth)

    # Must be published
    if assessment.status != "published":
        raise ValidationError(
            "Assessment must be published to accept results",
            error_code="ERR-LMS-422",
        )

    # 2. Check for existing result (idempotent)
    existing_result = await db.execute(
        select(AssessmentResult).where(
            AssessmentResult.assessment_id == assessment_id,
            AssessmentResult.student_id == auth.user_id,
        )
    )
    existing = existing_result.scalar_one_or_none()
    if existing is not None:
        return success_response({
            "id": str(existing.id),
            "assessment_id": str(existing.assessment_id),
            "student_id": str(existing.student_id),
            "score": float(existing.score) if existing.score is not None else None,
            "status": existing.status,
        })

    # 3. Create result
    result_obj = AssessmentResult(
        assessment_id=assessment_id,
        student_id=auth.user_id,
        score=body.score,
        status="submitted",
    )
    db.add(result_obj)
    await db.flush()

    # 4. Audit
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="ASSESSMENT_RESULT_SUBMITTED",
        outcome="success",
        target_type="assessment_result",
        target_id=result_obj.id,
        entity_after={
            "assessment_id": str(assessment_id),
            "score": float(body.score) if body.score is not None else None,
        },
        ip_address=_get_client_ip(request),
    )

    return success_response({
        "id": str(result_obj.id),
        "assessment_id": str(result_obj.assessment_id),
        "student_id": str(result_obj.student_id),
        "score": float(result_obj.score) if result_obj.score is not None else None,
        "status": result_obj.status,
    })
