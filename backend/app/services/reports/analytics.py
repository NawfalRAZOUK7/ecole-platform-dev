"""Analytics event emitter — canonical schema per G2 tracking contract.

Reference: S-138 — Analytics event emitter, Pack G2 — Analytics & Tracking Contract
Event schema fields: event_name, event_version, schema_version, occurred_at,
    env, actor_type, actor_id (pseudonymized), correlation_id, client_platform,
    client_version, properties (whitelisted), pii_flags, redaction_applied.

PII handling (G2.5):
  - Raw PII (email, phone, full_name) MUST NOT be emitted
  - actor_id MUST be pseudonymized via HMAC-SHA256
  - properties follow a per-event whitelist
  - pii_flags array tracks any PII-adjacent fields present

Design:
  - Async event emission (non-blocking, fire-and-forget to logger)
  - Structured JSON logging for Loki/Promtail ingestion
  - Schema version tracking for CI drift detection (S-146)
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings
from app.core.middleware import get_correlation_id
from app.core.permissions import ADM, DIR, PAR, STD, SUP, SYS, TCH

logger = logging.getLogger("analytics")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SCHEMA_VERSION = 1  # Increment on breaking schema changes (S-146)
ANALYTICS_HMAC_KEY = "ecole-analytics-pseudonymize-v1"  # Salt for actor_id hashing

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ActorType(str, Enum):
    STUDENT = "student"
    PARENT = "parent"
    TEACHER = "teacher"
    ADMIN = "admin"
    SUPPORT = "support"
    SYSTEM = "system"


class ClientPlatform(str, Enum):
    WEB = "web"
    IOS = "ios"
    ANDROID = "android"
    SERVER = "server"


# Role → ActorType mapping
_ROLE_TO_ACTOR: dict[str, ActorType] = {
    STD: ActorType.STUDENT,
    PAR: ActorType.PARENT,
    TCH: ActorType.TEACHER,
    ADM: ActorType.ADMIN,
    DIR: ActorType.ADMIN,
    SUP: ActorType.SUPPORT,
    SYS: ActorType.SYSTEM,
}


# ---------------------------------------------------------------------------
# PII patterns to block from properties (POL-G3-001, G2.5)
# ---------------------------------------------------------------------------
_PII_FIELD_BLOCKLIST = frozenset(
    {
        "email",
        "phone",
        "full_name",
        "password",
        "password_hash",
        "token",
        "refresh_token",
        "access_token",
        "otp",
        "code",
        "credit_card",
        "card_number",
        "ssn",
        "national_id",
    }
)


# ---------------------------------------------------------------------------
# Per-event property whitelists (G2.3 — Event Dictionary P0)
# ---------------------------------------------------------------------------
_EVENT_PROPERTY_WHITELIST: dict[str, frozenset[str]] = {
    # Auth events (EVT-001 to EVT-006)
    "auth_login_attempt": frozenset({"screen_id", "route", "client_platform"}),
    "auth_login_success": frozenset({"endpoint", "http_status", "correlation_id"}),
    "auth_login_failure": frozenset({"endpoint", "http_status", "error_code"}),
    "auth_refresh_success": frozenset({"endpoint", "http_status", "correlation_id"}),
    "auth_refresh_failure": frozenset({"endpoint", "http_status", "error_code"}),
    "auth_logout": frozenset({"endpoint", "http_status"}),
    # Feed events (EVT-007, EVT-008)
    "feed_view": frozenset({"screen_id", "route", "cursor_used"}),
    "feed_item_open": frozenset({"screen_id", "item_type", "item_id"}),
    # Content events (EVT-009, EVT-010)
    "content_list_view": frozenset({"sort_field", "sort_order", "cursor_used"}),
    "content_item_open": frozenset({"content_item_id", "route"}),
    # Notification events (EVT-011, EVT-012)
    "notifications_view": frozenset({"sort_field", "sort_order"}),
    "notifications_mark_read": frozenset({"notification_id", "http_status"}),
    # Invoice events (EVT-013, EVT-014)
    "invoices_view_list": frozenset({"screen_id", "route", "sort_field"}),
    "invoices_view_detail": frozenset({"invoice_id", "route"}),
    # Consent events (EVT-015, EVT-016)
    "consent_view": frozenset({"screen_id", "consent_id"}),
    "consent_update": frozenset({"consent_id", "http_status"}),
    # Error events (EVT-017)
    "error_api_received": frozenset({"error_code", "http_status", "endpoint"}),
    # P0 KPI events
    "content_progress_updated": frozenset(
        {"content_item_id", "status", "previous_status"}
    ),
    "notification_delivered": frozenset(
        {"notification_id", "channel", "delivery_status"}
    ),
    "payment_completed": frozenset({"payment_id", "outcome", "amount_currency"}),
    # AI events
    "ai_request_submitted": frozenset({"request_type", "prompt_id", "prompt_version"}),
    "ai_request_completed": frozenset(
        {"request_type", "prompt_id", "status", "latency_ms"}
    ),
    "ai_opt_out_updated": frozenset({"opt_out", "target_user_id_hash"}),
    "ai_fallback_used": frozenset({"reason", "request_type"}),
    "writing_attempt_created": frozenset({"subject", "word_count"}),
    "recommendation_served": frozenset({"reason_code", "item_count"}),
}

# Default whitelist for unknown events
_DEFAULT_WHITELIST = frozenset({"endpoint", "http_status", "error_code", "status"})


# ---------------------------------------------------------------------------
# Canonical Event Model (G2.2)
# ---------------------------------------------------------------------------
class AnalyticsEvent(BaseModel):
    """Canonical analytics event per G2.2 schema."""

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
        }
    )

    event_name: str
    event_version: int = 1
    schema_version: int = SCHEMA_VERSION
    occurred_at: str  # ISO 8601 UTC
    env: str
    actor_type: str
    actor_id: str  # Pseudonymized (HMAC-SHA256)
    session_id: str | None = None
    correlation_id: str | None = None
    client_platform: str = "server"
    client_version: str = "0.1.0"
    properties: dict[str, Any] = Field(default_factory=dict)
    pii_flags: list[str] = Field(default_factory=list)
    redaction_applied: bool = False


# ---------------------------------------------------------------------------
# Pseudonymization (DEC-G2-021, D6)
# ---------------------------------------------------------------------------
def pseudonymize_actor_id(actor_id: uuid.UUID) -> str:
    """HMAC-SHA256 pseudonymize an actor UUID.

    Uses a stable key so the same actor_id always maps to the same hash,
    enabling analytics joins without exposing real IDs.
    """
    return hmac.new(
        ANALYTICS_HMAC_KEY.encode(),
        str(actor_id).encode(),
        hashlib.sha256,
    ).hexdigest()[:32]


# ---------------------------------------------------------------------------
# Property sanitization (G2.5, POL-G3-001)
# ---------------------------------------------------------------------------
def _sanitize_properties(
    event_name: str,
    raw_properties: dict[str, Any],
) -> tuple[dict[str, Any], list[str], bool]:
    """Sanitize event properties per whitelist and PII blocklist.

    Returns:
        (sanitized_properties, pii_flags, redaction_applied)
    """
    whitelist = _EVENT_PROPERTY_WHITELIST.get(event_name, _DEFAULT_WHITELIST)
    pii_flags: list[str] = []
    redaction_applied = False

    sanitized: dict[str, Any] = {}
    for key, value in raw_properties.items():
        # Block PII fields
        if key.lower() in _PII_FIELD_BLOCKLIST:
            pii_flags.append(key)
            redaction_applied = True
            continue
        # Only include whitelisted fields
        if key in whitelist:
            sanitized[key] = value

    return sanitized, pii_flags, redaction_applied


# ---------------------------------------------------------------------------
# Event Emitter
# ---------------------------------------------------------------------------
def emit_event(
    event_name: str,
    *,
    actor_id: uuid.UUID | None = None,
    actor_role: str = SYS,
    session_id: uuid.UUID | None = None,
    client_platform: str = "server",
    client_version: str = "0.1.0",
    event_version: int = 1,
    properties: dict[str, Any] | None = None,
) -> AnalyticsEvent:
    """Emit a canonical analytics event.

    Events are logged as structured JSON for Loki/Promtail ingestion.
    Non-blocking — does not await or raise on failure.

    Args:
        event_name: Snake_case event name (e.g., 'auth_login_success')
        actor_id: Raw user UUID (will be pseudonymized)
        actor_role: Role code (ADM, TCH, PAR, STD, etc.)
        session_id: Session UUID if available
        client_platform: web, ios, android, server
        client_version: Client version string
        event_version: Event-specific version (for prompt versioning etc.)
        properties: Event-specific properties (will be sanitized)
    """
    # Pseudonymize actor_id
    pseudo_actor = pseudonymize_actor_id(actor_id) if actor_id else "anonymous"

    # Get correlation_id from request context
    cid = get_correlation_id()

    # Sanitize properties
    raw_props = properties or {}
    sanitized_props, pii_flags, redacted = _sanitize_properties(event_name, raw_props)

    # Map role to actor_type
    actor_type = _ROLE_TO_ACTOR.get(actor_role, ActorType.SYSTEM).value

    event = AnalyticsEvent(
        event_name=event_name,
        event_version=event_version,
        schema_version=SCHEMA_VERSION,
        occurred_at=datetime.now(timezone.utc).isoformat(),
        env=settings.app_env,
        actor_type=actor_type,
        actor_id=pseudo_actor,
        session_id=str(session_id) if session_id else None,
        correlation_id=cid,
        client_platform=client_platform,
        client_version=client_version,
        properties=sanitized_props,
        pii_flags=pii_flags,
        redaction_applied=redacted,
    )

    # Emit as structured JSON log line (picked up by Promtail → Loki)
    logger.info(
        "ANALYTICS_EVENT %s",
        event.model_dump_json(),
        extra={"event_name": event_name, "actor_type": actor_type},
    )

    return event


# ---------------------------------------------------------------------------
# Convenience emitters for P0 events (S-139)
# ---------------------------------------------------------------------------
def emit_auth_login_success(
    actor_id: uuid.UUID,
    role: str,
    session_id: uuid.UUID,
    client_platform: str = "server",
) -> AnalyticsEvent:
    """EVT-002: auth_login_success — POST /auth/login status=200."""
    return emit_event(
        "auth_login_success",
        actor_id=actor_id,
        actor_role=role,
        session_id=session_id,
        client_platform=client_platform,
        properties={
            "endpoint": "/auth/login",
            "http_status": 200,
        },
    )


def emit_auth_login_failure(
    actor_id: uuid.UUID | None,
    role: str = "PUBLIC",
    error_code: str = "ERR-IAM-401",
    client_platform: str = "server",
) -> AnalyticsEvent:
    """EVT-003: auth_login_failure — POST /auth/login status!=200."""
    return emit_event(
        "auth_login_failure",
        actor_id=actor_id,
        actor_role=role,
        client_platform=client_platform,
        properties={
            "endpoint": "/auth/login",
            "http_status": 401,
            "error_code": error_code,
        },
    )


def emit_feed_item_open(
    actor_id: uuid.UUID,
    role: str,
    item_type: str,
    item_id: str,
    client_platform: str = "server",
) -> AnalyticsEvent:
    """EVT-008: feed_item_open — feed item click/open."""
    return emit_event(
        "feed_item_open",
        actor_id=actor_id,
        actor_role=role,
        client_platform=client_platform,
        properties={
            "screen_id": "feed",
            "item_type": item_type,
            "item_id": item_id,
        },
    )


def emit_notification_delivered(
    actor_id: uuid.UUID,
    role: str,
    notification_id: str,
    channel: str = "in_app",
    delivery_status: str = "delivered",
) -> AnalyticsEvent:
    """P0: notification_delivered — notification delivery confirmation."""
    return emit_event(
        "notification_delivered",
        actor_id=actor_id,
        actor_role=role,
        properties={
            "notification_id": notification_id,
            "channel": channel,
            "delivery_status": delivery_status,
        },
    )


def emit_content_progress_updated(
    actor_id: uuid.UUID,
    role: str,
    content_item_id: str,
    status: str,
    previous_status: str | None = None,
) -> AnalyticsEvent:
    """P0: content_progress_updated — student progress change."""
    return emit_event(
        "content_progress_updated",
        actor_id=actor_id,
        actor_role=role,
        properties={
            "content_item_id": content_item_id,
            "status": status,
            "previous_status": previous_status or "none",
        },
    )


def emit_payment_completed(
    actor_id: uuid.UUID,
    role: str,
    payment_id: str,
    outcome: str,
    amount_currency: str = "MAD",
) -> AnalyticsEvent:
    """P0: payment_completed — payment outcome (paid/failed/canceled)."""
    return emit_event(
        "payment_completed",
        actor_id=actor_id,
        actor_role=role,
        properties={
            "payment_id": payment_id,
            "outcome": outcome,
            "amount_currency": amount_currency,
        },
    )
