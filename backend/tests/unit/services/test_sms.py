"""Unit tests for app/services/communication/sms.py — full branch coverage."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

import app.services.communication.sms as sms_module
from app.services.communication.sms import (
    SMS_DAILY_LIMIT,
    SMSProvider,
    SMSService,
    StubSMSProvider,
    _check_rate_limit,
    _increment_rate_limit,
    _today_key,
    sms_service,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fresh_uid() -> uuid.UUID:
    return uuid.uuid4()


def _clear_counts():
    """Reset the in-memory rate-limit counters between tests."""
    sms_module._daily_counts.clear()


# ---------------------------------------------------------------------------
# _today_key
# ---------------------------------------------------------------------------

def test_today_key_returns_string():
    key = _today_key()
    assert isinstance(key, str)
    # Format: YYYY-MM-DD
    parts = key.split("-")
    assert len(parts) == 3


# ---------------------------------------------------------------------------
# _check_rate_limit / _increment_rate_limit
# ---------------------------------------------------------------------------

def test_check_rate_limit_fresh_user_is_allowed():
    _clear_counts()
    uid = _fresh_uid()
    assert _check_rate_limit(uid) is True


def test_check_rate_limit_at_limit_is_denied():
    _clear_counts()
    uid = _fresh_uid()
    key = _today_key()
    sms_module._daily_counts[key][str(uid)] = SMS_DAILY_LIMIT
    assert _check_rate_limit(uid) is False


def test_check_rate_limit_one_below_limit_is_allowed():
    _clear_counts()
    uid = _fresh_uid()
    key = _today_key()
    sms_module._daily_counts[key][str(uid)] = SMS_DAILY_LIMIT - 1
    assert _check_rate_limit(uid) is True


def test_increment_rate_limit_increments_count():
    _clear_counts()
    uid = _fresh_uid()
    _increment_rate_limit(uid)
    key = _today_key()
    assert sms_module._daily_counts[key][str(uid)] == 1


def test_increment_rate_limit_accumulates():
    _clear_counts()
    uid = _fresh_uid()
    for _ in range(3):
        _increment_rate_limit(uid)
    key = _today_key()
    assert sms_module._daily_counts[key][str(uid)] == 3


# ---------------------------------------------------------------------------
# StubSMSProvider
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_stub_provider_send_returns_true_mock_enabled():
    provider = StubSMSProvider()
    mock_settings = type("S", (), {"mock_sms_enabled": True})()
    with patch("app.services.communication.sms.settings", mock_settings):
        result = await provider.send(to="+212600000000", body="code: 123456")
    assert result is True


@pytest.mark.asyncio
async def test_stub_provider_send_returns_true_mock_disabled():
    provider = StubSMSProvider()
    mock_settings = type("S", (), {"mock_sms_enabled": False})()
    with patch("app.services.communication.sms.settings", mock_settings):
        result = await provider.send(to="+212600000001", body="msg")
    assert result is True


@pytest.mark.asyncio
async def test_stub_provider_send_accepts_kwargs():
    provider = StubSMSProvider()
    mock_settings = type("S", (), {"mock_sms_enabled": False})()
    with patch("app.services.communication.sms.settings", mock_settings):
        result = await provider.send(to="+1", body="hello", extra="ignored")
    assert result is True


# ---------------------------------------------------------------------------
# SMSProvider Protocol
# ---------------------------------------------------------------------------

def test_sms_provider_protocol_conformance():
    assert isinstance(StubSMSProvider(), SMSProvider)


@pytest.mark.asyncio
async def test_sms_provider_protocol_send_default_body():
    """Protocol.send() body is Ellipsis — callable as an unbound method."""
    result = await SMSProvider.send(None, to="+1", body="test")  # type: ignore[arg-type]
    assert result is None  # ... evaluates to None


# ---------------------------------------------------------------------------
# SMSService.send_sms — happy path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_sms_success_under_limit():
    _clear_counts()
    uid = _fresh_uid()
    mock_provider = AsyncMock(spec=SMSProvider)
    mock_provider.send = AsyncMock(return_value=True)
    svc = SMSService(provider=mock_provider)

    result = await svc.send_sms(to="+212600000000", body="Hello", user_id=uid)

    assert result is True
    mock_provider.send.assert_awaited_once_with(to="+212600000000", body="Hello")


@pytest.mark.asyncio
async def test_send_sms_increments_count_on_success():
    _clear_counts()
    uid = _fresh_uid()
    mock_provider = AsyncMock()
    mock_provider.send = AsyncMock(return_value=True)
    svc = SMSService(provider=mock_provider)

    await svc.send_sms(to="+212600000000", body="msg", user_id=uid)

    key = _today_key()
    assert sms_module._daily_counts[key][str(uid)] == 1


@pytest.mark.asyncio
async def test_send_sms_provider_returns_false_no_increment():
    _clear_counts()
    uid = _fresh_uid()
    mock_provider = AsyncMock()
    mock_provider.send = AsyncMock(return_value=False)
    svc = SMSService(provider=mock_provider)

    result = await svc.send_sms(to="+212600000000", body="msg", user_id=uid)

    assert result is False
    key = _today_key()
    assert sms_module._daily_counts[key][str(uid)] == 0


# ---------------------------------------------------------------------------
# SMSService.send_sms — rate limited
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_sms_rate_limited_returns_false():
    _clear_counts()
    uid = _fresh_uid()
    key = _today_key()
    sms_module._daily_counts[key][str(uid)] = SMS_DAILY_LIMIT

    mock_provider = AsyncMock()
    mock_provider.send = AsyncMock()
    svc = SMSService(provider=mock_provider)

    result = await svc.send_sms(to="+212600000000", body="msg", user_id=uid)

    assert result is False
    mock_provider.send.assert_not_awaited()


# ---------------------------------------------------------------------------
# SMSService.send_sms — provider exception
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_sms_provider_exception_returns_false():
    _clear_counts()
    uid = _fresh_uid()
    mock_provider = AsyncMock()
    mock_provider.send = AsyncMock(side_effect=RuntimeError("Twilio error"))
    svc = SMSService(provider=mock_provider)

    result = await svc.send_sms(to="+212600000000", body="msg", user_id=uid)

    assert result is False
    key = _today_key()
    assert sms_module._daily_counts[key][str(uid)] == 0


# ---------------------------------------------------------------------------
# SMSService.send_sms — kwargs forwarded
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_sms_forwards_kwargs_to_provider():
    _clear_counts()
    uid = _fresh_uid()
    mock_provider = AsyncMock()
    mock_provider.send = AsyncMock(return_value=True)
    svc = SMSService(provider=mock_provider)

    await svc.send_sms(to="+1", body="hi", user_id=uid, sender_id="ECOLE")

    mock_provider.send.assert_awaited_once_with(
        to="+1", body="hi", sender_id="ECOLE"
    )


# ---------------------------------------------------------------------------
# SMSService.send_notification_fallback
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_notification_fallback_short_no_body():
    _clear_counts()
    uid = _fresh_uid()
    mock_provider = AsyncMock()
    mock_provider.send = AsyncMock(return_value=True)
    svc = SMSService(provider=mock_provider)

    result = await svc.send_notification_fallback(
        to="+212600000000", title="Alert", body=None, user_id=uid
    )

    assert result is True
    call_kwargs = mock_provider.send.call_args.kwargs
    assert "Alert" in call_kwargs["body"]


@pytest.mark.asyncio
async def test_send_notification_fallback_with_body():
    _clear_counts()
    uid = _fresh_uid()
    mock_provider = AsyncMock()
    mock_provider.send = AsyncMock(return_value=True)
    svc = SMSService(provider=mock_provider)

    await svc.send_notification_fallback(
        to="+212600000000", title="Alert", body="Details here", user_id=uid
    )

    call_kwargs = mock_provider.send.call_args.kwargs
    assert "Alert: Details here" in call_kwargs["body"]


@pytest.mark.asyncio
async def test_send_notification_fallback_truncates_long_message():
    _clear_counts()
    uid = _fresh_uid()
    mock_provider = AsyncMock()
    mock_provider.send = AsyncMock(return_value=True)
    svc = SMSService(provider=mock_provider)

    long_body = "X" * 200

    await svc.send_notification_fallback(
        to="+212600000000", title="T", body=long_body, user_id=uid
    )

    call_kwargs = mock_provider.send.call_args.kwargs
    assert len(call_kwargs["body"]) <= 160
    assert call_kwargs["body"].endswith("...")


@pytest.mark.asyncio
async def test_send_notification_fallback_exactly_160_not_truncated():
    _clear_counts()
    uid = _fresh_uid()
    mock_provider = AsyncMock()
    mock_provider.send = AsyncMock(return_value=True)
    svc = SMSService(provider=mock_provider)

    title = "T" * 5
    body = "B" * (160 - len(f"{title}: ") - 1)
    combined = f"{title}: {body}"
    assert len(combined) <= 160

    await svc.send_notification_fallback(
        to="+212600000000", title=title, body=body, user_id=uid
    )

    call_kwargs = mock_provider.send.call_args.kwargs
    assert not call_kwargs["body"].endswith("...")


# ---------------------------------------------------------------------------
# SMSService default provider
# ---------------------------------------------------------------------------

def test_sms_service_default_provider_is_stub():
    svc = SMSService()
    assert isinstance(svc.provider, StubSMSProvider)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

def test_module_singleton_is_sms_service():
    assert isinstance(sms_service, SMSService)
