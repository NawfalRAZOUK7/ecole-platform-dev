"""Unit tests for app/services/auth/sms_2fa.py (Sms2FAService).

Covers client construction (mock vs real Twilio), OTP generation format,
verification, and the send paths: dev-mode logging, real Twilio success, and
graceful failure handling.
"""

import logging

import pytest

from app.services.auth import sms_2fa


# ---------------------------------------------------------------------------
# Client construction
# ---------------------------------------------------------------------------
class TestClientConstruction:
    def test_mock_sms_does_not_create_twilio_client(self, monkeypatch):
        monkeypatch.setattr(sms_2fa.settings, "sms_enabled", True)
        monkeypatch.setattr(sms_2fa.settings, "mock_sms_enabled", True)
        monkeypatch.setattr(sms_2fa.settings, "sms_provider", "twilio")

        def fail_twilio_client(*args, **kwargs):
            raise AssertionError("Twilio client must not be created in mock mode")

        monkeypatch.setattr(sms_2fa, "TwilioClient", fail_twilio_client)
        assert sms_2fa.Sms2FAService().twilio_client is None

    def test_real_mode_creates_twilio_client_with_credentials(self, monkeypatch):
        monkeypatch.setattr(sms_2fa.settings, "sms_enabled", True)
        monkeypatch.setattr(sms_2fa.settings, "mock_sms_enabled", False)
        monkeypatch.setattr(sms_2fa.settings, "sms_provider", "twilio")
        monkeypatch.setattr(sms_2fa.settings, "twilio_account_sid", "AC-sid")
        monkeypatch.setattr(sms_2fa.settings, "twilio_auth_token", "tok")

        captured = {}

        def fake_client(sid, token):
            captured["sid"] = sid
            captured["token"] = token
            return object()

        monkeypatch.setattr(sms_2fa, "TwilioClient", fake_client)
        service = sms_2fa.Sms2FAService()
        assert service.twilio_client is not None
        assert captured == {"sid": "AC-sid", "token": "tok"}

    def test_disabled_sms_does_not_create_client(self, monkeypatch):
        monkeypatch.setattr(sms_2fa.settings, "sms_enabled", False)
        monkeypatch.setattr(sms_2fa.settings, "mock_sms_enabled", False)
        monkeypatch.setattr(sms_2fa, "TwilioClient", lambda *a, **k: object())
        assert sms_2fa.Sms2FAService().twilio_client is None

    def test_non_twilio_provider_does_not_create_client(self, monkeypatch):
        monkeypatch.setattr(sms_2fa.settings, "sms_enabled", True)
        monkeypatch.setattr(sms_2fa.settings, "mock_sms_enabled", False)
        monkeypatch.setattr(sms_2fa.settings, "sms_provider", "vonage")
        monkeypatch.setattr(sms_2fa, "TwilioClient", lambda *a, **k: object())
        assert sms_2fa.Sms2FAService().twilio_client is None


# ---------------------------------------------------------------------------
# OTP generation + verification
# ---------------------------------------------------------------------------
class TestOtp:
    def test_generate_otp_is_six_numeric_digits(self, monkeypatch):
        monkeypatch.setattr(sms_2fa.settings, "mock_sms_enabled", True)
        otp = sms_2fa.Sms2FAService().generate_otp()
        assert len(otp) == 6
        assert otp.isdigit()

    def test_generate_otp_varies(self, monkeypatch):
        monkeypatch.setattr(sms_2fa.settings, "mock_sms_enabled", True)
        svc = sms_2fa.Sms2FAService()
        # Extremely unlikely to collide across 20 draws if RNG works.
        assert len({svc.generate_otp() for _ in range(20)}) > 1

    def test_verify_otp_matches(self, monkeypatch):
        monkeypatch.setattr(sms_2fa.settings, "mock_sms_enabled", True)
        svc = sms_2fa.Sms2FAService()
        assert svc.verify_otp("123456", "123456") is True

    def test_verify_otp_rejects_mismatch(self, monkeypatch):
        monkeypatch.setattr(sms_2fa.settings, "mock_sms_enabled", True)
        svc = sms_2fa.Sms2FAService()
        assert svc.verify_otp("000000", "123456") is False


# ---------------------------------------------------------------------------
# Send paths
# ---------------------------------------------------------------------------
class TestSend:
    @pytest.mark.asyncio
    async def test_mock_sms_send_logs_otp(self, monkeypatch, caplog):
        monkeypatch.setattr(sms_2fa.settings, "sms_enabled", True)
        monkeypatch.setattr(sms_2fa.settings, "mock_sms_enabled", True)
        service = sms_2fa.Sms2FAService()
        # Dev-mode OTP is emitted via logger.debug (was print()), so assert on logs.
        with caplog.at_level(logging.DEBUG, logger="app.services.auth.sms_2fa"):
            assert await service.send_otp("+212600000099", "123456") is True
        assert "[SMS 2FA - DEV MODE] OTP for +212600000099: 123456" in caplog.text

    @pytest.mark.asyncio
    async def test_real_send_calls_twilio_and_returns_true(self, monkeypatch):
        monkeypatch.setattr(sms_2fa.settings, "sms_enabled", True)
        monkeypatch.setattr(sms_2fa.settings, "mock_sms_enabled", False)
        monkeypatch.setattr(sms_2fa.settings, "sms_provider", "twilio")
        monkeypatch.setattr(sms_2fa.settings, "twilio_from_number", "+1222")

        sent = {}

        class _Messages:
            def create(self, *, body, from_, to):
                sent.update(body=body, from_=from_, to=to)

        class _Client:
            messages = _Messages()

        monkeypatch.setattr(sms_2fa, "TwilioClient", lambda *a, **k: _Client())
        service = sms_2fa.Sms2FAService()
        assert await service.send_otp("+212611112222", "654321") is True
        assert sent["to"] == "+212611112222"
        assert "654321" in sent["body"]
        assert sent["from_"] == "+1222"

    @pytest.mark.asyncio
    async def test_real_send_failure_returns_false(self, monkeypatch):
        monkeypatch.setattr(sms_2fa.settings, "sms_enabled", True)
        monkeypatch.setattr(sms_2fa.settings, "mock_sms_enabled", False)
        monkeypatch.setattr(sms_2fa.settings, "sms_provider", "twilio")

        class _Messages:
            def create(self, **kwargs):
                raise RuntimeError("twilio down")

        class _Client:
            messages = _Messages()

        monkeypatch.setattr(sms_2fa, "TwilioClient", lambda *a, **k: _Client())
        service = sms_2fa.Sms2FAService()
        assert await service.send_otp("+212600000000", "111111") is False
