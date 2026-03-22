"""Real-time event publishing service for WebSocket delivery.

Reference: Phase 3C — WebSocket Real-time Notifications
Publishes structured events to connected users via the ConnectionManager.
Events are fire-and-forget — failures are logged but never block the API response.

Event types:
  - notification:created — new notification for a parent
  - feed:created — new parent feed item
  - grade:published — grade published for a student
  - payment:updated — payment status changed
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from app.core.ws_manager import ws_manager

logger = logging.getLogger(__name__)


async def publish_event(
    user_id: uuid.UUID,
    event_type: str,
    data: dict[str, Any],
) -> None:
    """Publish a real-time event to a user's WebSocket connections.

    Fire-and-forget: errors are logged, never raised.
    """
    try:
        await ws_manager.send_to_user(user_id, {
            "event": event_type,
            "data": data,
        })
    except Exception:
        logger.warning(
            "Failed to publish WS event %s to user %s",
            event_type,
            user_id,
            exc_info=True,
        )


async def publish_notification_created(
    parent_id: uuid.UUID,
    notification_id: uuid.UUID,
    title: str,
    body: str | None = None,
    event_ref: str | None = None,
) -> None:
    """Push a notification:created event to a parent."""
    await publish_event(parent_id, "notification:created", {
        "notification_id": str(notification_id),
        "title": title,
        "body": body,
        "event_ref": event_ref,
    })


async def publish_feed_created(
    parent_id: uuid.UUID,
    feed_item_id: uuid.UUID,
    title: str,
    body: str | None = None,
    source_type: str | None = None,
) -> None:
    """Push a feed:created event to a parent."""
    await publish_event(parent_id, "feed:created", {
        "feed_item_id": str(feed_item_id),
        "title": title,
        "body": body,
        "source_type": source_type,
    })


async def publish_grade_published(
    student_id: uuid.UUID,
    grade_id: uuid.UUID,
    submission_id: uuid.UUID,
    score: float,
    assignment_title: str | None = None,
) -> None:
    """Push a grade:published event to a student."""
    await publish_event(student_id, "grade:published", {
        "grade_id": str(grade_id),
        "submission_id": str(submission_id),
        "score": score,
        "assignment_title": assignment_title,
    })


async def publish_payment_updated(
    parent_id: uuid.UUID,
    payment_attempt_id: uuid.UUID,
    status: str,
    invoice_id: uuid.UUID | None = None,
) -> None:
    """Push a payment:updated event to a parent."""
    await publish_event(parent_id, "payment:updated", {
        "payment_attempt_id": str(payment_attempt_id),
        "status": status,
        "invoice_id": str(invoice_id) if invoice_id else None,
    })


# ---------------------------------------------------------------------------
# Messaging events (Phase 11C)
# ---------------------------------------------------------------------------
async def publish_message_created(
    recipient_id: uuid.UUID,
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
    sender_id: uuid.UUID,
    body: str,
    sent_at: str,
) -> None:
    """Push a message:created event to a conversation participant."""
    await publish_event(recipient_id, "message:created", {
        "conversation_id": str(conversation_id),
        "message_id": str(message_id),
        "sender_id": str(sender_id),
        "body": body[:200],  # Preview only
        "sent_at": sent_at,
    })


async def publish_announcement_published(
    recipient_id: uuid.UUID,
    announcement_id: uuid.UUID,
    title: str,
    author_id: uuid.UUID,
) -> None:
    """Push an announcement:published event to a targeted user."""
    await publish_event(recipient_id, "announcement:published", {
        "announcement_id": str(announcement_id),
        "title": title,
        "author_id": str(author_id),
    })
