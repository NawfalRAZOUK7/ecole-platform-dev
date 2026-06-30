"""SMS 2FA service for phone-based authentication.

Reference: Phase 10 — SMS 2FA Support
"""

import logging
import secrets

from twilio.rest import Client as TwilioClient

from app.core.config import settings

logger = logging.getLogger(__name__)


class Sms2FAService:
    """Service for SMS 2FA operations using Twilio."""

    def __init__(self):
        self.twilio_client = None
        if (
            settings.sms_enabled
            and not settings.mock_sms_enabled
            and settings.sms_provider == "twilio"
        ):
            self.twilio_client = TwilioClient(
                settings.twilio_account_sid,
                settings.twilio_auth_token,
            )

    def generate_otp(self) -> str:
        """Generate a 6-digit OTP code using cryptographically secure RNG."""
        return "".join(str(secrets.randbelow(10)) for _ in range(6))

    async def send_otp(
        self,
        phone: str,
        otp: str,
    ) -> bool:
        """Send OTP code via SMS."""
        if (
            settings.mock_sms_enabled
            or not settings.sms_enabled
            or not self.twilio_client
        ):
            # In development mode, log the OTP instead
            logger.debug("[SMS 2FA - DEV MODE] OTP for %s: %s", phone, otp)
            return True

        try:
            message = (
                f"Your École Platform verification code is: {otp}. Valid for 5 minutes."
            )
            self.twilio_client.messages.create(
                body=message,
                from_=settings.twilio_from_number,
                to=phone,
            )
            return True
        except Exception:
            logger.warning("Failed to send SMS to %s", phone, exc_info=True)
            return False

    def verify_otp(
        self,
        provided_otp: str,
        expected_otp: str,
    ) -> bool:
        """Verify the OTP code."""
        return provided_otp == expected_otp
