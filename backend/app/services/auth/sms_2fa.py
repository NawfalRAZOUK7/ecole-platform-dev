"""SMS 2FA service for phone-based authentication.

Reference: Phase 10 — SMS 2FA Support
"""

import secrets

from twilio.rest import Client as TwilioClient

from app.core.config import settings


class Sms2FAService:
    """Service for SMS 2FA operations using Twilio."""

    def __init__(self):
        self.twilio_client = None
        if settings.sms_enabled and settings.sms_provider == "twilio":
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
        if not settings.sms_enabled or not self.twilio_client:
            # In development mode, log the OTP instead
            print(f"[SMS 2FA - DEV MODE] OTP for {phone}: {otp}")
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
        except Exception as e:
            print(f"Failed to send SMS: {e}")
            return False

    def verify_otp(
        self,
        provided_otp: str,
        expected_otp: str,
    ) -> bool:
        """Verify the OTP code."""
        return provided_otp == expected_otp
