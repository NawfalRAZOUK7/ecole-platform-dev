"""E2E email tests using Testmail disposable mailboxes.

Reference: STUDENT_PACK_ROADMAP.md — Testmail integration.

These tests verify that the EmailService can dispatch real emails to
Testmail inboxes. They require:

  1. TESTMAIL_API_KEY  (set via Doppler or .env)
  2. A real SMTP relay  (e.g. Gmail, SendGrid, Mailgun) so emails reach
     the internet and land in Testmail.  If your .env still points to
     localhost:1025 (Mailhog) the test is skipped.
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from tests.utils.testmail import clear_inbox, fresh_email, wait_email

# Skip the whole module if Testmail is not configured.
TESTMAIL_API_KEY = os.getenv("TESTMAIL_API_KEY", "")
TESTMAIL_NAMESPACE = os.getenv("TESTMAIL_NAMESPACE", "ibatt")

pytestmark = pytest.mark.integration

if not TESTMAIL_API_KEY:
    pytest.skip(
        "TESTMAIL_API_KEY not set (add it to Doppler or .env)",
        allow_module_level=True,
    )


def _smtp_is_real_relay() -> bool:
    """Return True if the app is configured with an internet-facing SMTP."""
    from app.core.config import settings

    host = settings.smtp_host
    port = settings.smtp_port
    # localhost / 127.0.0.1 / mailhog ports mean "dev only — can't reach Testmail"
    return host not in ("localhost", "127.0.0.1", "") and port not in (1025, 8025)


@pytest.fixture(scope="module")
def testmail_tag():
    """Generate a unique tag for this test run."""
    import uuid

    tag = f"e2e-{uuid.uuid4().hex[:8]}"
    yield tag
    # Optional: clear the inbox after the module finishes
    clear_inbox(tag)


# ======================================================================
# Direct EmailService → Testmail verification
# ======================================================================
class TestEmailServiceToTestmail:
    """Send real emails via EmailService and verify receipt in Testmail."""

    @pytest.mark.asyncio
    async def test_send_otp_reaches_testmail(self, testmail_tag):
        """EmailService.send_otp() delivers to a Testmail inbox."""
        pytest.importorskip("aiosmtplib")

        if not _smtp_is_real_relay():
            pytest.skip(
                "SMTP is not configured with an internet relay (still localhost/Mailhog)"
            )

        from app.services.auth.email import email_service

        to = fresh_email(testmail_tag)
        result = await email_service.send_otp(
            to=to,
            otp_code="424242",
            expire_minutes=15,
            lang="fr",
        )
        assert result is True, "SMTP reported failure — check credentials"

        email = wait_email(testmail_tag, timeout=60)
        assert email["to"] == to
        assert "424242" in email.get("text", email.get("html", ""))
        assert "code" in email.get("subject", "").lower()

    @pytest.mark.asyncio
    async def test_send_welcome_reaches_testmail(self, testmail_tag):
        """EmailService.send_welcome() delivers to a Testmail inbox."""
        pytest.importorskip("aiosmtplib")

        if not _smtp_is_real_relay():
            pytest.skip(
                "SMTP is not configured with an internet relay (still localhost/Mailhog)"
            )

        from app.services.auth.email import email_service

        to = fresh_email(testmail_tag)
        result = await email_service.send_welcome(
            to=to,
            user_name="Nawfal",
            school_name="École Test",
            role="STD",
            lang="fr",
        )
        assert result is True

        email = wait_email(testmail_tag, timeout=60)
        assert email["to"] == to
        assert "bienvenue" in email.get("subject", "").lower()


# ======================================================================
# Recovery flow  (API → enqueue_email → worker → SMTP → Testmail)
# ======================================================================
class TestRecoveryEmailFlow:
    """Recovery endpoint enqueues an OTP email."""

    async def test_recovery_endpoint_enqueues_email(self, client, api_context):
        """POST /recovery/request returns 200 and enqueues an OTP email."""
        from unittest.mock import AsyncMock

        # Use an existing user email so RecoveryService finds the user
        # and actually calls enqueue_email (random emails hit the
        # enumeration-guard early-return path).
        to = api_context["admin"]["user"].email
        school_id = api_context["school"].id

        # Patch enqueue_email so it fires synchronously inside the test
        # (avoids needing a running ARQ worker)
        with patch(
            "app.core.tasks.enqueue_email", new_callable=AsyncMock
        ) as mock_enqueue:
            resp = await client.post(
                "/recovery/request",
                json={"email": to, "school_id": str(school_id)},
            )
            assert resp.status_code == 200
            mock_enqueue.assert_called_once()
            call_kwargs = mock_enqueue.call_args.kwargs
            assert call_kwargs["to"] == to
            assert call_kwargs["template_name"] == "otp"


# ======================================================================
# Helper sanity check (no SMTP needed)
# ======================================================================
class TestTestmailHelpers:
    """Ensure the Testmail utility functions behave correctly."""

    def test_fresh_email_format(self):
        addr = fresh_email("demo-123")
        assert addr == f"{TESTMAIL_NAMESPACE}.demo-123@inbox.testmail.app"

    def test_wait_email_raises_on_missing_tag(self):
        import uuid

        fake_tag = f"nonexistent-{uuid.uuid4().hex}"
        with pytest.raises(TimeoutError):
            wait_email(fake_tag, timeout=3)
