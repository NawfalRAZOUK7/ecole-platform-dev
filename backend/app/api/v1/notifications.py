"""Phase 13 notification center API."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, get_current_user, requires_permission
from app.core.exceptions import AuthorizationError
from app.core.permissions import ADM, PAR, TCH
from app.core.response import clamp_page_size, list_response, success_response
from app.core.request_utils import get_client_ip
from app.schemas.notifications import (
    DigestPreferenceRequest,
    NotificationBatchRequest,
    NotificationPreferencesUpdateRequest,
    NotificationReadRequest,
)
from app.services.audit import AuditService
from app.services.email_digest import EmailDigestService
from app.services.notification_hub import NotificationHubService

router = APIRouter(prefix="/notifications", tags=["com-notifications"])


@router.get(
    "",
    summary="Notification history",
    response_description="Filtered notification history with cursor pagination",
)
async def list_notifications(
    request: Request,
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    category: str | None = Query(None),
    channel: str | None = Query(None),
    read: bool | None = Query(None),
    from_date: datetime | None = Query(None, alias="from"),
    to_date: datetime | None = Query(None, alias="to"),
    auth: AuthContext = Depends(requires_permission("PERM-COM:notification:read")),
    db: AsyncSession = Depends(get_db),
):
    hub = NotificationHubService(db)
    items, next_cursor, has_more = await hub.list_notifications(
        school_id=auth.school_id,
        user_id=auth.user_id,
        role=auth.role,
        category=category,
        channel=channel,
        read=read,
        from_dt=from_date,
        to_dt=to_date,
        cursor=cursor,
        limit=clamp_page_size(limit),
    )
    return list_response(items, next_cursor=next_cursor, has_more=has_more)


@router.get(
    "/unread-count",
    summary="Unread notification count",
    response_description="Unread count with cache metadata",
)
async def unread_count(
    auth: AuthContext = Depends(requires_permission("PERM-COM:notification:read")),
    db: AsyncSession = Depends(get_db),
):
    hub = NotificationHubService(db)
    count, cached = await hub.unread_count(
        school_id=auth.school_id,
        user_id=auth.user_id,
        role=auth.role,
    )
    return success_response(
        {
            "unread_count": count,
            "cached": cached,
            "cache_ttl_seconds": 30,
        }
    )


@router.get(
    "/preferences",
    summary="Get notification preferences",
    response_description="Per-channel and per-category preferences",
)
async def get_preferences(
    auth: AuthContext = Depends(requires_permission("PERM-COM:notification:read")),
    db: AsyncSession = Depends(get_db),
):
    hub = NotificationHubService(db)
    preferences = await hub.list_preferences(
        school_id=auth.school_id,
        user_id=auth.user_id,
    )
    return success_response(
        {
            "user_id": str(auth.user_id),
            "preferences": preferences,
        }
    )


async def _update_preferences(
    body: NotificationPreferencesUpdateRequest,
    request: Request,
    auth: AuthContext,
    db: AsyncSession,
):
    hub = NotificationHubService(db)
    audit = AuditService(db)
    before = await hub.list_preferences(school_id=auth.school_id, user_id=auth.user_id)
    after = await hub.update_preferences(
        school_id=auth.school_id,
        user_id=auth.user_id,
        items=body.preferences,
    )
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="notification.preferences.update",
        target_type="notification_preferences",
        target_id=auth.user_id,
        outcome="success",
        entity_before={"preferences": before},
        entity_after={"preferences": after},
        ip_address=get_client_ip(request),
    )
    return success_response({"user_id": str(auth.user_id), "preferences": after})


@router.post(
    "/preferences",
    summary="Update notification preferences",
    response_description="Updated preferences",
)
async def post_preferences(
    body: NotificationPreferencesUpdateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-COM:notification:read")),
    db: AsyncSession = Depends(get_db),
):
    return await _update_preferences(body, request, auth, db)


@router.put(
    "/preferences",
    summary="Replace notification preferences",
    response_description="Updated preferences",
)
async def put_preferences(
    body: NotificationPreferencesUpdateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-COM:notification:read")),
    db: AsyncSession = Depends(get_db),
):
    return await _update_preferences(body, request, auth, db)


@router.get(
    "/digest/preferences",
    summary="Get digest preference",
    response_description="Digest frequency for the current user",
)
async def get_digest_preferences(
    auth: AuthContext = Depends(requires_permission("PERM-COM:notification:read")),
    db: AsyncSession = Depends(get_db),
):
    email_digest = EmailDigestService(db)
    frequency = await email_digest.get_digest_frequency(
        school_id=auth.school_id,
        user_id=auth.user_id,
    )
    return success_response(
        {
            "user_id": str(auth.user_id),
            "digest_frequency": frequency,
            "send_hour": 7,
            "timezone": "Africa/Casablanca",
        }
    )


@router.post(
    "/digest/preferences",
    summary="Update digest preference",
    response_description="Digest frequency saved for the current user",
)
async def update_digest_preferences(
    body: DigestPreferenceRequest,
    request: Request,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if auth.role not in {PAR, TCH, ADM}:
        raise AuthorizationError(
            "Digest preferences are not available for this role",
            error_code="ERR-COM-403",
        )

    email_digest = EmailDigestService(db)
    audit = AuditService(db)
    before = await email_digest.get_digest_frequency(
        school_id=auth.school_id,
        user_id=auth.user_id,
    )
    after = await email_digest.update_digest_frequency(
        school_id=auth.school_id,
        user_id=auth.user_id,
        digest_frequency=body.digest_frequency,
    )
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="notification.digest.update",
        target_type="notification_preferences",
        target_id=auth.user_id,
        outcome="success",
        entity_before={"digest_frequency": before},
        entity_after={"digest_frequency": after},
        ip_address=get_client_ip(request),
    )
    return success_response(
        {
            "user_id": str(auth.user_id),
            "digest_frequency": after,
            "send_hour": 7,
            "timezone": "Africa/Casablanca",
        }
    )


@router.patch(
    "/mark-all-read",
    summary="Mark all notifications as read",
    response_description="Count of updated notifications",
)
async def mark_all_read(
    auth: AuthContext = Depends(requires_permission("PERM-COM:notification:read")),
    db: AsyncSession = Depends(get_db),
):
    hub = NotificationHubService(db)
    result = await hub.mark_all_read(
        school_id=auth.school_id,
        user_id=auth.user_id,
    )
    return success_response(result)


@router.patch(
    "/{notification_id}/read",
    summary="Mark a notification as read or unread",
    response_description="Updated notification read state",
)
async def mark_notification_read(
    notification_id: uuid.UUID,
    body: NotificationReadRequest,
    auth: AuthContext = Depends(requires_permission("PERM-COM:notification:read")),
    db: AsyncSession = Depends(get_db),
):
    hub = NotificationHubService(db)
    result = await hub.mark_read(
        notification_id=notification_id,
        school_id=auth.school_id,
        user_id=auth.user_id,
        role=auth.role,
        read=body.read,
    )
    return success_response(result)


@router.post(
    "/batch",
    summary="Batch create notifications",
    response_description="Batch creation result",
)
async def batch_notifications(
    body: NotificationBatchRequest,
    request: Request,
    auth: AuthContext = Depends(
        requires_permission("PERM-COM:notification:batch-create")
    ),
    db: AsyncSession = Depends(get_db),
):
    hub = NotificationHubService(db)
    audit = AuditService(db)
    result = await hub.create_batch_notifications(
        school_id=auth.school_id,
        request=body,
    )
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="notification.batch.create",
        target_type="notification",
        outcome="success",
        entity_after={
            "request": body.model_dump(mode="json"),
            "result": result,
        },
        ip_address=get_client_ip(request),
    )
    return success_response(result)


@router.delete(
    "/{notification_id}",
    summary="Delete a notification",
    response_description="Deletion outcome",
)
async def delete_notification(
    notification_id: uuid.UUID,
    hard_delete: bool = Query(False),
    auth: AuthContext = Depends(requires_permission("PERM-COM:notification:read")),
    db: AsyncSession = Depends(get_db),
):
    hub = NotificationHubService(db)
    result = await hub.delete_notification(
        notification_id=notification_id,
        school_id=auth.school_id,
        user_id=auth.user_id,
        role=auth.role,
        hard_delete=hard_delete,
    )
    return success_response(result)


@router.get(
    "/unsubscribe",
    summary="One-click unsubscribe from notification emails",
    response_description="Unsubscribe confirmation",
    response_class=HTMLResponse,
)
async def unsubscribe_notifications(
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    email_digest = EmailDigestService(db)
    school_id, user_id = email_digest.parse_unsubscribe_token(token)
    await email_digest.unsubscribe_all_email(school_id=school_id, user_id=user_id)
    return HTMLResponse(
        "<html><body><h1>Notification emails disabled</h1><p>You have been unsubscribed successfully.</p></body></html>"
    )


@router.get(
    "/email-open",
    summary="Tracking pixel for email opens",
    response_description="1x1 transparent pixel",
)
async def track_email_open(
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    email_digest = EmailDigestService(db)
    delivery_id = email_digest.parse_open_tracking_token(token)
    await email_digest.mark_email_opened(delivery_id=delivery_id)
    return Response(
        content=(
            b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00"
            b"\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b"
        ),
        media_type="image/gif",
    )
