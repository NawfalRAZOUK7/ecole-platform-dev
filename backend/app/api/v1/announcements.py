"""Announcements API endpoints — Phase 11C.

Reference: Phase 11C — Messaging & Communication
Endpoints:
  POST   /announcements              — Create announcement (ADM/DIR)
  GET    /announcements              — List announcements
  PUT    /announcements/{id}         — Update draft announcement (ADM/DIR)
  POST   /announcements/{id}/publish — Publish announcement + send notifications
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
    requires_permission,
    verify_school_boundary,
)
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.response import (
    clamp_page_size,
    decode_cursor,
    encode_cursor,
    list_response,
    success_response,
)
from app.models.com import Announcement, Notification, NotificationDelivery
from app.models.erp import Enrollment
from app.models.iam import Membership, User
from app.schemas.com import (
    AnnouncementCreateRequest,
    AnnouncementResponse,
    AnnouncementUpdateRequest,
)
from app.services.audit import AuditService
from app.services.realtime import publish_announcement_published

router = APIRouter(prefix="/announcements", tags=["announcements"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def _announcement_to_response(a: Announcement) -> dict:
    return AnnouncementResponse(
        id=str(a.id),
        school_id=str(a.school_id),
        author_id=str(a.author_id),
        title=a.title,
        body=a.body,
        target_roles=a.target_roles or [],
        target_class_ids=[str(cid) for cid in a.target_class_ids] if a.target_class_ids else None,
        published_at=a.published_at.isoformat() if a.published_at else None,
        status=a.status,
        created_at=a.created_at.isoformat(),
        updated_at=a.updated_at.isoformat() if a.updated_at else None,
    ).model_dump()


# ---------------------------------------------------------------------------
# POST /announcements — Create announcement (ADM/DIR)
# ---------------------------------------------------------------------------
@router.post(
    "",
    status_code=201,
    summary="Create announcement",
    response_description="Created announcement (draft)",
)
async def create_announcement(
    body: AnnouncementCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-COM:announcement:create")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new announcement as a draft.

    Must be published separately via POST /announcements/{id}/publish.
    """
    audit = AuditService(db)

    # Validate target_roles
    valid_roles = {"ADM", "DIR", "TCH", "PAR", "STD"}
    for role in body.target_roles:
        if role not in valid_roles:
            raise ValidationError(
                f"Invalid target role: {role}. Must be one of {valid_roles}",
                error_code="ERR-COM-422",
            )

    announcement = Announcement(
        school_id=auth.school_id,
        author_id=auth.user_id,
        title=body.title,
        body=body.body,
        target_roles=body.target_roles,
        target_class_ids=[str(cid) for cid in body.target_class_ids] if body.target_class_ids else None,
        status="DRAFT",
    )
    db.add(announcement)
    await db.flush()

    resp = _announcement_to_response(announcement)

    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="announcement.create",
        target_type="announcement",
        target_id=announcement.id,
        outcome="success",
        entity_after=resp,
        ip_address=_get_client_ip(request),
    )

    await db.commit()
    return success_response(resp)


# ---------------------------------------------------------------------------
# GET /announcements — List announcements
# ---------------------------------------------------------------------------
@router.get(
    "",
    summary="List announcements",
    response_description="Paginated list of announcements",
)
async def list_announcements(
    status: str | None = Query(None, pattern="^(DRAFT|PUBLISHED|ARCHIVED)$"),
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None),
    auth: AuthContext = Depends(requires_permission("PERM-COM:announcement:read")),
    db: AsyncSession = Depends(get_db),
):
    """List announcements.

    ADM/DIR: see all announcements (including drafts).
    TCH/PAR/STD: see only PUBLISHED announcements targeting their role.
    """
    page_size = clamp_page_size(limit)

    query = select(Announcement).where(Announcement.school_id == auth.school_id)

    # Non-admin roles only see published announcements targeting their role
    if auth.role not in ("ADM", "DIR"):
        query = query.where(Announcement.status == "PUBLISHED")
        # Filter by role targeting — use PostgreSQL JSONB contains
        from sqlalchemy import cast, text
        query = query.where(
            Announcement.target_roles.contains([auth.role])
        )
    elif status:
        query = query.where(Announcement.status == status)

    query = query.order_by(Announcement.created_at.desc())

    if cursor:
        cursor_id, _ = decode_cursor(cursor)
        cursor_result = await db.execute(
            select(Announcement.created_at).where(Announcement.id == cursor_id)
        )
        cursor_created = cursor_result.scalar_one_or_none()
        if cursor_created:
            query = query.where(Announcement.created_at < cursor_created)

    query = query.limit(page_size + 1)
    result = await db.execute(query)
    announcements = list(result.scalars().all())

    has_more = len(announcements) > page_size
    announcements = announcements[:page_size]

    items = [_announcement_to_response(a) for a in announcements]

    next_cursor = None
    if has_more and announcements:
        next_cursor = encode_cursor(announcements[-1].id)

    return list_response(items, next_cursor=next_cursor, has_more=has_more)


# ---------------------------------------------------------------------------
# PUT /announcements/{id} — Update draft announcement
# ---------------------------------------------------------------------------
@router.put(
    "/{announcement_id}",
    summary="Update draft announcement",
    response_description="Updated announcement",
)
async def update_announcement(
    announcement_id: uuid.UUID,
    body: AnnouncementUpdateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-COM:announcement:create")),
    db: AsyncSession = Depends(get_db),
):
    """Update a draft announcement. Cannot update published announcements."""
    audit = AuditService(db)

    result = await db.execute(
        select(Announcement).where(Announcement.id == announcement_id)
    )
    announcement = result.scalar_one_or_none()
    if announcement is None:
        raise NotFoundError("Announcement not found", error_code="ERR-COM-404")
    verify_school_boundary(announcement.school_id, auth)

    if announcement.status != "DRAFT":
        raise ConflictError(
            "Only draft announcements can be updated",
            error_code="ERR-COM-409",
        )

    entity_before = _announcement_to_response(announcement)

    if body.title is not None:
        announcement.title = body.title
    if body.body is not None:
        announcement.body = body.body
    if body.target_roles is not None:
        valid_roles = {"ADM", "DIR", "TCH", "PAR", "STD"}
        for role in body.target_roles:
            if role not in valid_roles:
                raise ValidationError(
                    f"Invalid target role: {role}",
                    error_code="ERR-COM-422",
                )
        announcement.target_roles = body.target_roles
    if body.target_class_ids is not None:
        announcement.target_class_ids = [str(cid) for cid in body.target_class_ids]

    await db.flush()
    entity_after = _announcement_to_response(announcement)

    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="announcement.update",
        target_type="announcement",
        target_id=announcement.id,
        outcome="success",
        entity_before=entity_before,
        entity_after=entity_after,
        ip_address=_get_client_ip(request),
    )

    await db.commit()
    return success_response(entity_after)


# ---------------------------------------------------------------------------
# POST /announcements/{id}/publish — Publish + send notifications
# ---------------------------------------------------------------------------
@router.post(
    "/{announcement_id}/publish",
    summary="Publish announcement",
    response_description="Published announcement + notification summary",
)
async def publish_announcement(
    announcement_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-COM:announcement:publish")),
    db: AsyncSession = Depends(get_db),
):
    """Publish an announcement and send notifications to targeted users.

    1. Changes status to PUBLISHED.
    2. Creates a Notification for each targeted user.
    3. Pushes WebSocket event to online users.
    """
    audit = AuditService(db)
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(Announcement).where(Announcement.id == announcement_id)
    )
    announcement = result.scalar_one_or_none()
    if announcement is None:
        raise NotFoundError("Announcement not found", error_code="ERR-COM-404")
    verify_school_boundary(announcement.school_id, auth)

    if announcement.status != "DRAFT":
        raise ConflictError(
            "Only draft announcements can be published",
            error_code="ERR-COM-409",
        )

    entity_before = _announcement_to_response(announcement)

    # Publish
    announcement.status = "PUBLISHED"
    announcement.published_at = now
    await db.flush()

    # Find targeted users
    target_query = select(Membership.user_id).where(
        Membership.school_id == auth.school_id,
        Membership.role_code.in_(announcement.target_roles),
    )

    # If target_class_ids is set, further filter to users enrolled in those classes
    if announcement.target_class_ids:
        class_uuids = [uuid.UUID(cid) for cid in announcement.target_class_ids]

        # Get students in those classes
        student_result = await db.execute(
            select(Enrollment.student_id).where(
                Enrollment.class_id.in_(class_uuids),
                Enrollment.school_id == auth.school_id,
                Enrollment.status == "active",
            )
        )
        class_student_ids = set(student_result.scalars().all())

        # Filter: only include memberships whose user_id is in the class students
        # (This applies mainly to STD role; PAR/TCH get all if targeted)
        if "STD" in announcement.target_roles:
            # For STD, restrict to class students
            # For other roles, include all
            non_std_query = select(Membership.user_id).where(
                Membership.school_id == auth.school_id,
                Membership.role_code.in_(
                    [r for r in announcement.target_roles if r != "STD"]
                ),
            )
            std_query = select(Membership.user_id).where(
                Membership.school_id == auth.school_id,
                Membership.role_code == "STD",
                Membership.user_id.in_(class_student_ids),
            )
            # Union both
            from sqlalchemy import union_all
            target_query = union_all(non_std_query, std_query)

    target_result = await db.execute(target_query)
    target_user_ids = list(set(target_result.scalars().all()))

    # Create notifications for targeted users
    notif_count = 0
    for uid in target_user_ids:
        if uid == auth.user_id:
            continue  # Don't notify the author

        notif = Notification(
            school_id=auth.school_id,
            parent_id=uid,
            event_ref=f"announcement:{announcement.id}",
            idempotency_key=f"ann-{announcement.id}-{uid}",
            title=announcement.title,
            body=announcement.body[:500] if len(announcement.body) > 500 else announcement.body,
        )
        db.add(notif)
        notif_count += 1

    await db.flush()

    entity_after = _announcement_to_response(announcement)

    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="announcement.publish",
        target_type="announcement",
        target_id=announcement.id,
        outcome="success",
        entity_before=entity_before,
        entity_after={**entity_after, "notifications_sent": notif_count},
        ip_address=_get_client_ip(request),
    )

    await db.commit()

    # Push WebSocket events to targeted users
    for uid in target_user_ids:
        if uid != auth.user_id:
            await publish_announcement_published(
                recipient_id=uid,
                announcement_id=announcement.id,
                title=announcement.title,
                author_id=auth.user_id,
            )

    return success_response({
        **entity_after,
        "notifications_sent": notif_count,
    })
