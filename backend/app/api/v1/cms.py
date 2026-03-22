"""CMS endpoints — CONTENT_MGR manages platform-wide content + reviews teacher submissions.

Phase 9A: Content Library Backend
- POST /cms/content — create platform content (school_id=NULL)
- GET /cms/content — list platform content
- PUT /cms/content/{id} — update platform content
- DELETE /cms/content/{id} — soft-delete (archive)
- GET /cms/submissions — review queue
- POST /cms/submissions/{id}/review — approve or reject
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.exceptions import NotFoundError, ValidationError
from app.core.response import (
    clamp_page_size,
    decode_cursor,
    encode_cursor,
    list_response,
    success_response,
)
from app.models.com import Notification
from app.models.iam import TeacherProfile, User
from app.models.lms import ContentItem, ContentSubmission
from app.schemas.cms import (
    CmsContentCreateRequest,
    CmsContentUpdateRequest,
    ReviewDecisionRequest,
)
from app.services.audit import AuditService

router = APIRouter(prefix="/cms", tags=["cms"])


def _get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def _content_to_dict(ci: ContentItem) -> dict:
    return {
        "id": str(ci.id),
        "title": ci.title,
        "content_type": ci.content_type,
        "level_band": ci.level_band,
        "language": ci.language,
        "subject": ci.subject,
        "description": ci.description,
        "thumbnail_path": ci.thumbnail_path,
        "origin": ci.origin,
        "status": ci.status,
        "created_by": str(ci.created_by) if ci.created_by else None,
        "original_content_id": str(ci.original_content_id) if ci.original_content_id else None,
    }


# ---------------------------------------------------------------------------
# POST /cms/content — Create platform-wide content
# ---------------------------------------------------------------------------
@router.post("/content", status_code=201, summary="Create platform content")
async def create_cms_content(
    body: CmsContentCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-CMS:content:create")),
    db: AsyncSession = Depends(get_db),
):
    """CONTENT_MGR creates platform-wide content (school_id=NULL)."""
    audit = AuditService(db)

    ci = ContentItem(
        school_id=None,
        title=body.title,
        content_type=body.content_type,
        level_band=body.level_band,
        language=body.language,
        subject=body.subject,
        description=body.description,
        status=body.status,
        origin="PLATFORM",
        created_by=auth.user_id,
    )
    db.add(ci)
    await db.flush()

    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="CMS_CONTENT_CREATED",
        outcome="success",
        target_type="content_item",
        target_id=ci.id,
        entity_after=_content_to_dict(ci),
        ip_address=_get_client_ip(request),
    )

    return success_response(_content_to_dict(ci))


# ---------------------------------------------------------------------------
# GET /cms/content — List platform content
# ---------------------------------------------------------------------------
@router.get("/content", summary="List platform content")
async def list_cms_content(
    content_type: str | None = Query(None),
    level_band: str | None = Query(None),
    subject: str | None = Query(None),
    status: str | None = Query(None),
    origin: str | None = Query(None),
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    auth: AuthContext = Depends(requires_permission("PERM-CMS:content:manage")),
    db: AsyncSession = Depends(get_db),
):
    """CONTENT_MGR lists all platform content (school_id IS NULL)."""
    page_size = clamp_page_size(limit)

    query = select(ContentItem).where(ContentItem.school_id.is_(None))

    if content_type:
        query = query.where(ContentItem.content_type == content_type)
    if level_band:
        query = query.where(ContentItem.level_band == level_band)
    if subject:
        query = query.where(ContentItem.subject == subject)
    if status:
        query = query.where(ContentItem.status == status)
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

    items = [_content_to_dict(ci) for ci in items_list]
    next_cursor = encode_cursor(items_list[-1].id) if has_more and items_list else None

    return list_response(items, next_cursor=next_cursor, has_more=has_more)


# ---------------------------------------------------------------------------
# PUT /cms/content/{id} — Update platform content
# ---------------------------------------------------------------------------
@router.put("/content/{content_id}", summary="Update platform content")
async def update_cms_content(
    content_id: uuid.UUID,
    body: CmsContentUpdateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-CMS:content:manage")),
    db: AsyncSession = Depends(get_db),
):
    """CONTENT_MGR updates platform content metadata."""
    audit = AuditService(db)

    result = await db.execute(
        select(ContentItem).where(
            ContentItem.id == content_id,
            ContentItem.school_id.is_(None),
        )
    )
    ci = result.scalar_one_or_none()
    if ci is None:
        raise NotFoundError("Platform content not found", error_code="ERR-CMS-404")

    entity_before = _content_to_dict(ci)

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ci, field, value)
    await db.flush()

    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="CMS_CONTENT_UPDATED",
        outcome="success",
        target_type="content_item",
        target_id=ci.id,
        entity_before=entity_before,
        entity_after=_content_to_dict(ci),
        ip_address=_get_client_ip(request),
    )

    return success_response(_content_to_dict(ci))


# ---------------------------------------------------------------------------
# DELETE /cms/content/{id} — Soft-delete (archive)
# ---------------------------------------------------------------------------
@router.delete("/content/{content_id}", summary="Archive platform content")
async def delete_cms_content(
    content_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-CMS:content:delete")),
    db: AsyncSession = Depends(get_db),
):
    """CONTENT_MGR archives platform content (soft-delete: status→archived)."""
    audit = AuditService(db)

    result = await db.execute(
        select(ContentItem).where(
            ContentItem.id == content_id,
            ContentItem.school_id.is_(None),
        )
    )
    ci = result.scalar_one_or_none()
    if ci is None:
        raise NotFoundError("Platform content not found", error_code="ERR-CMS-404")

    entity_before = _content_to_dict(ci)
    ci.status = "archived"
    await db.flush()

    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="CMS_CONTENT_ARCHIVED",
        outcome="success",
        target_type="content_item",
        target_id=ci.id,
        entity_before=entity_before,
        entity_after=_content_to_dict(ci),
        ip_address=_get_client_ip(request),
    )

    return success_response({"deleted": True, "id": str(content_id)})


# ---------------------------------------------------------------------------
# GET /cms/submissions — Review queue
# ---------------------------------------------------------------------------
@router.get("/submissions", summary="List teacher submissions for review")
async def list_submissions(
    status: str | None = Query(None),
    subject: str | None = Query(None),
    level_band: str | None = Query(None),
    school_id: str | None = Query(None),
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    auth: AuthContext = Depends(requires_permission("PERM-CMS:content:review")),
    db: AsyncSession = Depends(get_db),
):
    """CONTENT_MGR reviews teacher submissions. Filter by status/subject/level/school."""
    page_size = clamp_page_size(limit)

    query = select(ContentSubmission, ContentItem, User).join(
        ContentItem, ContentSubmission.content_item_id == ContentItem.id
    ).join(
        User, ContentSubmission.submitted_by == User.id
    )

    if status:
        query = query.where(ContentSubmission.status == status)
    if subject:
        query = query.where(ContentItem.subject == subject)
    if level_band:
        query = query.where(ContentItem.level_band == level_band)
    if school_id:
        query = query.where(ContentSubmission.school_id == uuid.UUID(school_id))

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
            "submitted_by": str(sub.submitted_by),
            "submitter_name": user.full_name,
            "school_id": str(sub.school_id),
            "status": sub.status,
            "submitted_at": sub.submitted_at.isoformat() if sub.submitted_at else None,
            "reviewed_by": str(sub.reviewed_by) if sub.reviewed_by else None,
            "reviewed_at": sub.reviewed_at.isoformat() if sub.reviewed_at else None,
            "review_notes": sub.review_notes,
            "promoted_content_id": str(sub.promoted_content_id) if sub.promoted_content_id else None,
        }
        for sub, ci, user in rows
    ]

    next_cursor = encode_cursor(rows[-1][0].id) if has_more and rows else None
    return list_response(items, next_cursor=next_cursor, has_more=has_more)


# ---------------------------------------------------------------------------
# POST /cms/submissions/{id}/review — Approve or reject
# ---------------------------------------------------------------------------
@router.post("/submissions/{submission_id}/review", summary="Review a teacher submission")
async def review_submission(
    submission_id: uuid.UUID,
    body: ReviewDecisionRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-CMS:content:review")),
    db: AsyncSession = Depends(get_db),
):
    """CONTENT_MGR approves or rejects a teacher submission.

    Approve: creates platform copy, awards points, notifies teacher.
    Reject: updates status, notifies teacher with feedback.
    """
    audit = AuditService(db)

    result = await db.execute(
        select(ContentSubmission).where(ContentSubmission.id == submission_id)
    )
    sub = result.scalar_one_or_none()
    if sub is None:
        raise NotFoundError("Submission not found", error_code="ERR-CMS-404")

    if sub.status in ("APPROVED", "REJECTED"):
        raise ValidationError(
            f"Submission already {sub.status.lower()}",
            error_code="ERR-CMS-409",
        )

    now = datetime.now(timezone.utc)
    sub.reviewed_by = auth.user_id
    sub.reviewed_at = now
    sub.review_notes = body.review_notes

    if body.decision == "APPROVED":
        sub.status = "APPROVED"

        # Load the original content item
        ci_result = await db.execute(
            select(ContentItem).where(ContentItem.id == sub.content_item_id)
        )
        original = ci_result.scalar_one_or_none()
        if original is None:
            raise NotFoundError("Original content not found", error_code="ERR-CMS-404")

        # Create platform copy
        promoted = ContentItem(
            school_id=None,
            title=original.title,
            content_type=original.content_type,
            level_band=original.level_band,
            language=original.language,
            subject=original.subject,
            description=original.description,
            status="published",
            origin="PROMOTED",
            created_by=original.created_by,
            original_content_id=original.id,
        )
        db.add(promoted)
        await db.flush()

        sub.promoted_content_id = promoted.id

        # Award reward points to teacher
        tp_result = await db.execute(
            select(TeacherProfile).where(TeacherProfile.user_id == sub.submitted_by)
        )
        teacher_profile = tp_result.scalar_one_or_none()
        if teacher_profile is not None:
            teacher_profile.reward_points += body.reward_points

        # Send notification to teacher
        try:
            notif = Notification(
                school_id=sub.school_id,
                parent_id=sub.submitted_by,  # reuses parent_id field for recipient
                event_ref=f"content:submission:approved:{sub.id}",
                idempotency_key=f"cms-approved-{sub.id}",
                title="Contenu approuve",
                body=f'Votre contenu "{original.title}" a ete approuve et ajoute a la bibliotheque de la plateforme.',
            )
            db.add(notif)
        except Exception:
            pass  # Non-critical — notification failure shouldn't block approval

    else:  # REJECTED
        sub.status = "REJECTED"

        # Load original for notification title
        ci_result = await db.execute(
            select(ContentItem).where(ContentItem.id == sub.content_item_id)
        )
        original = ci_result.scalar_one_or_none()
        content_title = original.title if original else "Contenu"

        # Send rejection notification
        try:
            feedback_text = f' Retour: {body.review_notes}' if body.review_notes else ''
            notif = Notification(
                school_id=sub.school_id,
                parent_id=sub.submitted_by,
                event_ref=f"content:submission:rejected:{sub.id}",
                idempotency_key=f"cms-rejected-{sub.id}",
                title="Contenu non retenu",
                body=f'Votre contenu "{content_title}" n\'a pas ete retenu pour la bibliotheque.{feedback_text}',
            )
            db.add(notif)
        except Exception:
            pass

    await db.flush()

    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type=f"CMS_SUBMISSION_{body.decision}",
        outcome="success",
        target_type="content_submission",
        target_id=sub.id,
        entity_after={
            "status": sub.status,
            "review_notes": sub.review_notes,
            "promoted_content_id": str(sub.promoted_content_id) if sub.promoted_content_id else None,
        },
        ip_address=_get_client_ip(request),
    )

    return success_response({
        "id": str(sub.id),
        "status": sub.status,
        "reviewed_by": str(sub.reviewed_by),
        "reviewed_at": sub.reviewed_at.isoformat() if sub.reviewed_at else None,
        "review_notes": sub.review_notes,
        "promoted_content_id": str(sub.promoted_content_id) if sub.promoted_content_id else None,
    })
