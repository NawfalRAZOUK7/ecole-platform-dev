"""Content Library endpoints — teachers browse/assign/submit, students view class content.

Phase 9A: Content Library Backend
- GET /content/library — Teachers browse platform + school content
- POST /content/assign — Teacher assigns content to class
- DELETE /content/assign/{id} — Teacher unassigns content
- POST /content/submit-for-review — Teacher submits content for platform promotion
- GET /content/my-submissions — Teacher tracks submission status
- GET /classes/{class_id}/content — Students see assigned content
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

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
from app.core.exceptions import NotFoundError, ValidationError
from app.core.response import (
    clamp_page_size,
    decode_cursor,
    encode_cursor,
    list_response,
    success_response,
)
from app.models.lms import ClassContentAssignment, ContentItem, ContentSubmission
from app.schemas.cms import ContentAssignRequest, ContentSubmitForReviewRequest
from app.services.audit import AuditService

router = APIRouter(tags=["content-library"])


def _get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


# ---------------------------------------------------------------------------
# GET /content/library — Teacher browses content
# ---------------------------------------------------------------------------
@router.get("/content/library", summary="Browse content library")
async def browse_content_library(
    content_type: str | None = Query(None),
    level_band: str | None = Query(None),
    subject: str | None = Query(None),
    language: str | None = Query(None),
    origin: str | None = Query(None),
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    auth: AuthContext = Depends(requires_permission("PERM-LMS:content:read")),
    db: AsyncSession = Depends(get_db),
):
    """Teachers browse platform-wide (school_id=NULL) + their school's published content."""
    page_size = clamp_page_size(limit)

    query = select(ContentItem).where(
        ContentItem.status == "published",
        (ContentItem.school_id == auth.school_id) | (ContentItem.school_id.is_(None)),
    )

    if content_type:
        query = query.where(ContentItem.content_type == content_type)
    if level_band:
        query = query.where(ContentItem.level_band == level_band)
    if subject:
        query = query.where(ContentItem.subject == subject)
    if language:
        query = query.where(ContentItem.language == language)
    if origin:
        query = query.where(ContentItem.origin == origin)

    query = query.order_by(ContentItem.id)

    if cursor:
        last_id, _ = decode_cursor(cursor)
        query = query.where(ContentItem.id > last_id)

    query = query.limit(page_size + 1)
    result = await db.execute(query)
    items_list = list(result.scalars().all())

    has_more = len(items_list) > page_size
    if has_more:
        items_list = items_list[:page_size]

    items = [
        {
            "id": str(ci.id),
            "school_id": str(ci.school_id) if ci.school_id else None,
            "title": ci.title,
            "content_type": ci.content_type,
            "level_band": ci.level_band,
            "language": ci.language,
            "subject": ci.subject,
            "description": ci.description,
            "origin": ci.origin,
            "status": ci.status,
        }
        for ci in items_list
    ]

    next_cursor = encode_cursor(items_list[-1].id) if has_more and items_list else None
    return list_response(items, next_cursor=next_cursor, has_more=has_more)


# ---------------------------------------------------------------------------
# POST /content/assign — Teacher assigns content to class
# ---------------------------------------------------------------------------
@router.post("/content/assign", status_code=201, summary="Assign content to class")
async def assign_content_to_class(
    body: ContentAssignRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-CMS:content:assign")),
    db: AsyncSession = Depends(get_db),
):
    """Teacher assigns a content item to one of their classes."""
    audit = AuditService(db)

    # Verify teacher is assigned to this class
    teacher_classes = await get_teacher_class_ids(auth.user_id, auth.school_id, db)
    verify_teacher_assignment(body.class_id, teacher_classes)

    # Verify content item exists and is accessible
    ci_result = await db.execute(
        select(ContentItem).where(
            ContentItem.id == body.content_item_id,
            ContentItem.status == "published",
        )
    )
    ci = ci_result.scalar_one_or_none()
    if ci is None:
        raise NotFoundError("Content item not found", error_code="ERR-CMS-404")

    # School boundary: content must be same school or platform-wide
    if ci.school_id is not None and ci.school_id != auth.school_id:
        raise NotFoundError("Content item not found", error_code="ERR-CMS-404")

    # Check for duplicate assignment
    dup_result = await db.execute(
        select(ClassContentAssignment).where(
            ClassContentAssignment.class_id == body.class_id,
            ClassContentAssignment.content_item_id == body.content_item_id,
        )
    )
    if dup_result.scalar_one_or_none() is not None:
        raise ValidationError(
            "Content already assigned to this class",
            error_code="ERR-CMS-409",
        )

    assignment = ClassContentAssignment(
        teacher_id=auth.user_id,
        class_id=body.class_id,
        content_item_id=body.content_item_id,
        school_id=auth.school_id,
        assigned_at=datetime.now(timezone.utc),
        notes=body.notes,
    )
    db.add(assignment)
    await db.flush()

    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="CONTENT_ASSIGNED_TO_CLASS",
        outcome="success",
        target_type="class_content_assignment",
        target_id=assignment.id,
        entity_after={
            "class_id": str(body.class_id),
            "content_item_id": str(body.content_item_id),
        },
        ip_address=_get_client_ip(request),
    )

    return success_response(
        {
            "id": str(assignment.id),
            "teacher_id": str(assignment.teacher_id),
            "class_id": str(assignment.class_id),
            "content_item_id": str(assignment.content_item_id),
            "school_id": str(assignment.school_id),
            "assigned_at": assignment.assigned_at.isoformat(),
            "notes": assignment.notes,
        }
    )


# ---------------------------------------------------------------------------
# DELETE /content/assign/{id} — Teacher unassigns content
# ---------------------------------------------------------------------------
@router.delete("/content/assign/{assignment_id}", summary="Unassign content from class")
async def unassign_content(
    assignment_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-CMS:content:assign")),
    db: AsyncSession = Depends(get_db),
):
    """Teacher removes a content assignment from their class."""
    audit = AuditService(db)

    result = await db.execute(
        select(ClassContentAssignment).where(ClassContentAssignment.id == assignment_id)
    )
    assignment = result.scalar_one_or_none()
    if assignment is None:
        raise NotFoundError("Assignment not found", error_code="ERR-CMS-404")

    # Must be same school
    verify_school_boundary(assignment.school_id, auth)

    # Must be assigned to one of teacher's classes
    teacher_classes = await get_teacher_class_ids(auth.user_id, auth.school_id, db)
    verify_teacher_assignment(assignment.class_id, teacher_classes)

    entity_before = {
        "id": str(assignment.id),
        "class_id": str(assignment.class_id),
        "content_item_id": str(assignment.content_item_id),
    }
    await db.delete(assignment)
    await db.flush()

    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="CONTENT_UNASSIGNED_FROM_CLASS",
        outcome="success",
        target_type="class_content_assignment",
        target_id=uuid.UUID(entity_before["id"]),
        entity_before=entity_before,
        ip_address=_get_client_ip(request),
    )

    return success_response({"deleted": True, "id": entity_before["id"]})


# ---------------------------------------------------------------------------
# POST /content/submit-for-review — Teacher submits for platform promotion
# ---------------------------------------------------------------------------
@router.post(
    "/content/submit-for-review",
    status_code=201,
    summary="Submit content for platform review",
)
async def submit_for_review(
    body: ContentSubmitForReviewRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-CMS:content:submit")),
    db: AsyncSession = Depends(get_db),
):
    """Teacher submits their school-scoped content for platform promotion."""
    audit = AuditService(db)

    # Verify content exists and belongs to teacher's school
    ci_result = await db.execute(
        select(ContentItem).where(ContentItem.id == body.content_item_id)
    )
    ci = ci_result.scalar_one_or_none()
    if ci is None:
        raise NotFoundError("Content item not found", error_code="ERR-CMS-404")

    if ci.school_id is None:
        raise ValidationError(
            "Platform-wide content cannot be submitted for review",
            error_code="ERR-CMS-400",
        )

    verify_school_boundary(ci.school_id, auth)

    # Check for existing pending/under_review submission
    existing_result = await db.execute(
        select(ContentSubmission).where(
            ContentSubmission.content_item_id == body.content_item_id,
            ContentSubmission.submitted_by == auth.user_id,
            ContentSubmission.status.in_(["PENDING", "UNDER_REVIEW"]),
        )
    )
    if existing_result.scalar_one_or_none() is not None:
        raise ValidationError(
            "A submission for this content is already pending review",
            error_code="ERR-CMS-409",
        )

    submission = ContentSubmission(
        content_item_id=body.content_item_id,
        submitted_by=auth.user_id,
        school_id=auth.school_id,
        status="PENDING",
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(submission)
    await db.flush()

    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="CONTENT_SUBMITTED_FOR_REVIEW",
        outcome="success",
        target_type="content_submission",
        target_id=submission.id,
        entity_after={
            "content_item_id": str(body.content_item_id),
            "status": "PENDING",
        },
        ip_address=_get_client_ip(request),
    )

    return success_response(
        {
            "id": str(submission.id),
            "content_item_id": str(submission.content_item_id),
            "status": submission.status,
            "submitted_at": submission.submitted_at.isoformat(),
        }
    )


# ---------------------------------------------------------------------------
# GET /content/my-submissions — Teacher tracks submission status
# ---------------------------------------------------------------------------
@router.get("/content/my-submissions", summary="List my content submissions")
async def list_my_submissions(
    status: str | None = Query(None),
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    auth: AuthContext = Depends(requires_permission("PERM-CMS:content:submit")),
    db: AsyncSession = Depends(get_db),
):
    """Teacher sees status of their submitted content."""
    page_size = clamp_page_size(limit)

    query = (
        select(ContentSubmission, ContentItem)
        .join(ContentItem, ContentSubmission.content_item_id == ContentItem.id)
        .where(
            ContentSubmission.submitted_by == auth.user_id,
        )
    )

    if status:
        query = query.where(ContentSubmission.status == status)

    query = query.order_by(ContentSubmission.id)

    if cursor:
        last_id, _ = decode_cursor(cursor)
        query = query.where(ContentSubmission.id > last_id)

    query = query.limit(page_size + 1)
    result = await db.execute(query)
    rows = list(result.all())

    has_more = len(rows) > page_size
    if has_more:
        rows = rows[:page_size]

    items = [
        {
            "id": str(sub.id),
            "content_item_id": str(sub.content_item_id),
            "content_title": ci.title,
            "status": sub.status,
            "submitted_at": sub.submitted_at.isoformat() if sub.submitted_at else None,
            "review_notes": sub.review_notes,
            "promoted_content_id": str(sub.promoted_content_id)
            if sub.promoted_content_id
            else None,
        }
        for sub, ci in rows
    ]

    next_cursor = encode_cursor(rows[-1][0].id) if has_more and rows else None
    return list_response(items, next_cursor=next_cursor, has_more=has_more)


# ---------------------------------------------------------------------------
# GET /classes/{class_id}/content — Students see assigned content
# ---------------------------------------------------------------------------
@router.get("/classes/{class_id}/content", summary="List content assigned to class")
async def list_class_content(
    class_id: uuid.UUID,
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    auth: AuthContext = Depends(requires_permission("PERM-LMS:content:read")),
    db: AsyncSession = Depends(get_db),
):
    """Students (and parents/teachers) see content assigned to a class."""
    page_size = clamp_page_size(limit)

    query = (
        select(ClassContentAssignment, ContentItem)
        .join(ContentItem, ClassContentAssignment.content_item_id == ContentItem.id)
        .where(
            ClassContentAssignment.class_id == class_id,
            ClassContentAssignment.school_id == auth.school_id,
            ContentItem.status == "published",
        )
    )

    query = query.order_by(ClassContentAssignment.id)

    if cursor:
        last_id, _ = decode_cursor(cursor)
        query = query.where(ClassContentAssignment.id > last_id)

    query = query.limit(page_size + 1)
    result = await db.execute(query)
    rows = list(result.all())

    has_more = len(rows) > page_size
    if has_more:
        rows = rows[:page_size]

    items = [
        {
            "id": str(cca.id),
            "content_item_id": str(cca.content_item_id),
            "title": ci.title,
            "content_type": ci.content_type,
            "level_band": ci.level_band,
            "language": ci.language,
            "subject": ci.subject,
            "description": ci.description,
            "assigned_at": cca.assigned_at.isoformat() if cca.assigned_at else None,
            "teacher_notes": cca.notes,
        }
        for cca, ci in rows
    ]

    next_cursor = encode_cursor(rows[-1][0].id) if has_more and rows else None
    return list_response(items, next_cursor=next_cursor, has_more=has_more)
