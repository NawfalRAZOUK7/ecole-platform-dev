"""SMS fallback service — abstract provider protocol with stub implementation.

Reference: Phase 11C — Messaging & Communication
Triggers on email delivery failure when the user has SMS consent.
Rate limit: 5 SMS per day per user (enforced at application level).

Usage:
    from app.services.sms import sms_service
    await sms_service.send_sms(to="+212612345678", body="Your code: 123456", user_id=user_id)
"""

from __future__ import annotations

import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rate limit tracking (in-memory; use Redis in production)
# ---------------------------------------------------------------------------
_daily_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
SMS_DAILY_LIMIT = 5


def _today_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _check_rate_limit(user_id: uuid.UUID) -> bool:
    """Check if user is under the daily SMS limit. Returns True if allowed."""
    key = _today_key()
    uid = str(user_id)
    return _daily_counts[key][uid] < SMS_DAILY_LIMIT


def _increment_rate_limit(user_id: uuid.UUID) -> None:
    """Increment the daily SMS count for a user."""
    key = _today_key()
    uid = str(user_id)
    _daily_counts[key][uid] += 1


# ---------------------------------------------------------------------------
# SMS Provider protocol
# ---------------------------------------------------------------------------
@runtime_checkable
class SMSProvider(Protocol):
    """Abstract SMS provider — implement for Twilio, Vonage, etc."""

    async def send(self, to: str, body: str, **kwargs: Any) -> bool:
        """Send an SMS. Returns True on success, False on failure."""
        ...


# ---------------------------------------------------------------------------
# Stub provider (development/testing)
# ---------------------------------------------------------------------------
class StubSMSProvider:
    """Stub SMS provider that logs messages but does not actually send.

    Used in development and testing environments.
    """

    async def send(self, to: str, body: str, **kwargs: Any) -> bool:
        logger.info(
            "[STUB SMS] to=%s body=%s (not actually sent)",
            to,
            body[:100],
        )
        return True


# ---------------------------------------------------------------------------
# SMS Service
# ---------------------------------------------------------------------------
class SMSService:
    """SMS service with rate limiting and provider abstraction."""

    def __init__(self, provider: SMSProvider | None = None) -> None:
        self.provider: SMSProvider = provider or StubSMSProvider()

    async def send_sms(
        self,
        to: str,
        body: str,
        user_id: uuid.UUID,
        **kwargs: Any,
    ) -> bool:
        """Send an SMS with rate limit enforcement.

        Args:
            to: Phone number in E.164 format (e.g., +212612345678).
            body: Message body (max 160 chars for single SMS).
            user_id: User ID for rate limiting.

        Returns:
            True if sent successfully, False if rate-limited or failed.
        """
        if not _check_rate_limit(user_id):
            logger.warning(
                "SMS rate limit exceeded for user %s (limit=%d/day)",
                user_id,
                SMS_DAILY_LIMIT,
            )
            return False

        try:
            success = await self.provider.send(to=to, body=body, **kwargs)
            if success:
                _increment_rate_limit(user_id)
                logger.info("SMS sent to %s for user %s", to, user_id)
            return success
        except Exception:
            logger.warning(
                "Failed to send SMS to %s for user %s",
                to,
                user_id,
                exc_info=True,
            )
            return False

    async def send_notification_fallback(
        self,
        to: str,
        title: str,
        body: str | None,
        user_id: uuid.UUID,
    ) -> bool:
        """Send a notification as SMS fallback (after email failure).

        Truncates to 160 chars for SMS.
        """
        sms_body = title
        if body:
            sms_body = f"{title}: {body}"
        # Truncate to SMS limit
        if len(sms_body) > 160:
            sms_body = sms_body[:157] + "..."

        return await self.send_sms(to=sms_body, body=sms_body, user_id=user_id)


# Module-level singleton
sms_service = SMSService()
