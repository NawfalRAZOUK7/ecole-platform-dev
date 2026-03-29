"""Phase 13 notification center coverage.

Integration tests run against the Docker-backed backend + postgres + redis stack.
Seed data must be loaded before execution (make seed).

Run:
  python -m pytest tests/test_phase13_notifications.py -v
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, call

import httpx
import pytest

from app.services.email import _render_template
from app.services.push_config import PushConfigService

STUDENT_1_ID = "10000000-0000-4000-8000-000000000007"


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _unread_count(client: httpx.AsyncClient, token: str) -> int:
    response = await client.get(
        "/notifications/unread-count",
        headers=_auth_headers(token),
    )
    assert response.status_code == 200
    return response.json()["data"]["unread_count"]


async def _find_notification(
    client: httpx.AsyncClient,
    token: str,
    *,
    title: str,
    category: str,
) -> dict:
    response = await client.get(
        "/notifications",
        headers=_auth_headers(token),
        params={"limit": 20, "category": category},
    )
    assert response.status_code == 200
    items = response.json()["data"]
    notification = next((item for item in items if item["title"] == title), None)
    assert notification is not None, f"Notification with title '{title}' not found"
    return notification


class TestNotificationHubIntegration:
    @pytest.mark.asyncio
    async def test_parent_preferences_and_digest_round_trip(
        self,
        client: httpx.AsyncClient,
        parent_token: str,
    ):
        headers = _auth_headers(parent_token)

        original_preferences_response = await client.get(
            "/notifications/preferences",
            headers=headers,
        )
        assert original_preferences_response.status_code == 200
        original_preferences = original_preferences_response.json()["data"]["preferences"]
        assert len(original_preferences) >= 20

        target_preference = next(
            item
            for item in original_preferences
            if item["channel"] == "email" and item["category"] == "billing"
        )
        updated_preferences = [dict(item) for item in original_preferences]
        for item in updated_preferences:
            if item["channel"] == "email" and item["category"] == "billing":
                item["enabled"] = not target_preference["enabled"]

        original_digest_response = await client.get(
            "/notifications/digest/preferences",
            headers=headers,
        )
        assert original_digest_response.status_code == 200
        original_digest = original_digest_response.json()["data"]["digest_frequency"]

        try:
            update_response = await client.post(
                "/notifications/preferences",
                headers=headers,
                json={"preferences": updated_preferences},
            )
            assert update_response.status_code == 200
            saved_preferences = update_response.json()["data"]["preferences"]
            billing_email = next(
                item
                for item in saved_preferences
                if item["channel"] == "email" and item["category"] == "billing"
            )
            assert billing_email["enabled"] is (not target_preference["enabled"])

            digest_update_response = await client.post(
                "/notifications/digest/preferences",
                headers=headers,
                json={"digest_frequency": "weekly"},
            )
            assert digest_update_response.status_code == 200
            assert (
                digest_update_response.json()["data"]["digest_frequency"] == "weekly"
            )

            digest_get_response = await client.get(
                "/notifications/digest/preferences",
                headers=headers,
            )
            assert digest_get_response.status_code == 200
            assert digest_get_response.json()["data"]["digest_frequency"] == "weekly"
        finally:
            await client.post(
                "/notifications/preferences",
                headers=headers,
                json={"preferences": original_preferences},
            )
            await client.post(
                "/notifications/digest/preferences",
                headers=headers,
                json={"digest_frequency": original_digest},
            )

    @pytest.mark.asyncio
    async def test_admin_batch_create_routes_channels_and_student_can_read(
        self,
        client: httpx.AsyncClient,
        admin_token: str,
        student_token: str,
    ):
        title = f"Phase13 routing {uuid.uuid4()}"
        student_headers = _auth_headers(student_token)
        notification_id: str | None = None

        unread_before = await _unread_count(client, student_token)

        try:
            create_response = await client.post(
                "/notifications/batch",
                headers=_auth_headers(admin_token),
                json={
                    "title": title,
                    "body": "Critical billing reminder",
                    "category": "billing",
                    "priority": "critical",
                    "user_ids": [STUDENT_1_ID],
                    "action_url": "/billing/invoices",
                    "event_ref": "phase13.integration",
                    "silent_push": False,
                },
            )
            assert create_response.status_code == 200
            result = create_response.json()["data"]
            assert result["requested_recipients"] == 1
            assert result["notifications_created"] == 1
            assert "in_app" in result["routed_channels"]
            assert "push" in result["routed_channels"]
            assert "email" in result["routed_channels"]

            notification = await _find_notification(
                client,
                student_token,
                title=title,
                category="billing",
            )
            notification_id = notification["id"]
            assert notification["action_url"] == "/billing/invoices"
            assert "in_app" in notification["channels"]
            assert "push" in notification["channels"]
            assert "email" in notification["channels"]
            assert notification["is_read"] is False

            unread_after_create = await _unread_count(client, student_token)
            assert unread_after_create >= unread_before + 1

            mark_read_response = await client.patch(
                f"/notifications/{notification_id}/read",
                headers=student_headers,
                json={"read": True},
            )
            assert mark_read_response.status_code == 200
            assert mark_read_response.json()["data"]["read"] is True

            unread_after_read = await _unread_count(client, student_token)
            assert unread_after_read <= unread_after_create - 1

            mark_unread_response = await client.patch(
                f"/notifications/{notification_id}/read",
                headers=student_headers,
                json={"read": False},
            )
            assert mark_unread_response.status_code == 200
            assert mark_unread_response.json()["data"]["read"] is False

            mark_all_response = await client.patch(
                "/notifications/mark-all-read",
                headers=student_headers,
            )
            assert mark_all_response.status_code == 200
            assert mark_all_response.json()["data"]["read"] is True

            unread_after_mark_all = await _unread_count(client, student_token)
            assert unread_after_mark_all == 0
        finally:
            if notification_id:
                await client.delete(
                    f"/notifications/{notification_id}",
                    headers=student_headers,
                )

    @pytest.mark.asyncio
    async def test_device_registration_lifecycle(
        self,
        client: httpx.AsyncClient,
        parent_token: str,
    ):
        headers = _auth_headers(parent_token)
        token_value = f"phase13-device-{uuid.uuid4().hex}-abcdefghijklmnopqrstuvwxyz"

        register_response = await client.post(
            "/devices/register",
            headers=headers,
            json={
                "token": token_value,
                "platform": "android",
                "device_name": "Pixel 8 Test",
            },
        )
        assert register_response.status_code == 200
        device = register_response.json()["data"]
        device_id = device["id"]
        assert device["platform"] == "android"
        assert device["device_name"] == "Pixel 8 Test"

        try:
            list_response = await client.get("/devices", headers=headers)
            assert list_response.status_code == 200
            devices = list_response.json()["data"]
            assert any(item["id"] == device_id for item in devices)
        finally:
            delete_response = await client.delete(
                f"/devices/{device_id}",
                headers=headers,
            )
            assert delete_response.status_code == 200

        final_list_response = await client.get("/devices", headers=headers)
        assert final_list_response.status_code == 200
        assert all(
            item["id"] != device_id for item in final_list_response.json()["data"]
        )


class TestNotificationDenyOrdering:
    @pytest.mark.asyncio
    async def test_batch_requires_authentication_before_authorization(
        self,
        client: httpx.AsyncClient,
        student_token: str,
    ):
        payload = {
            "title": f"Phase13 deny {uuid.uuid4()}",
            "body": "Unauthorized batch attempt",
            "category": "system",
            "priority": "normal",
            "user_ids": [STUDENT_1_ID],
        }

        unauthenticated_response = await client.post(
            "/notifications/batch",
            json=payload,
        )
        assert unauthenticated_response.status_code == 401

        forbidden_response = await client.post(
            "/notifications/batch",
            headers=_auth_headers(student_token),
            json=payload,
        )
        assert forbidden_response.status_code == 403

    @pytest.mark.asyncio
    async def test_mark_read_returns_404_for_scoped_out_notification(
        self,
        client: httpx.AsyncClient,
        admin_token: str,
        parent_token: str,
        student_token: str,
    ):
        title = f"Phase13 scoped notification {uuid.uuid4()}"
        notification_id: str | None = None

        create_response = await client.post(
            "/notifications/batch",
            headers=_auth_headers(admin_token),
            json={
                "title": title,
                "body": "Scoped notification",
                "category": "academic",
                "priority": "high",
                "user_ids": [STUDENT_1_ID],
                "event_ref": "phase13.scoped",
            },
        )
        assert create_response.status_code == 200

        try:
            notification = await _find_notification(
                client,
                student_token,
                title=title,
                category="academic",
            )
            notification_id = notification["id"]

            unauthenticated_response = await client.patch(
                f"/notifications/{notification_id}/read",
                json={"read": True},
            )
            assert unauthenticated_response.status_code == 401

            not_found_response = await client.patch(
                f"/notifications/{notification_id}/read",
                headers=_auth_headers(parent_token),
                json={"read": True},
            )
            assert not_found_response.status_code == 404
        finally:
            if notification_id:
                await client.delete(
                    f"/notifications/{notification_id}",
                    headers=_auth_headers(student_token),
                )

    @pytest.mark.asyncio
    async def test_student_cannot_manage_digest_preferences(self, client, student_token):
        response = await client.post(
            "/notifications/digest/preferences",
            headers=_auth_headers(student_token),
            json={"digest_frequency": "daily"},
        )
        assert response.status_code == 403


class TestPushDeliveryRetries:
    @pytest.mark.asyncio
    async def test_send_with_retry_retries_transient_failures(self, monkeypatch):
        from app.services import push_config

        service = PushConfigService(db=None)  # type: ignore[arg-type]
        attempts = {"count": 0}

        def fake_send(_message):
            attempts["count"] += 1
            if attempts["count"] < 3:
                raise RuntimeError("transient push failure")
            return "provider-message-id"

        sleep_mock = AsyncMock()
        monkeypatch.setattr(push_config, "messaging", SimpleNamespace(send=fake_send))
        monkeypatch.setattr(push_config.asyncio, "sleep", sleep_mock)
        monkeypatch.setattr(
            push_config.settings,
            "push_retry_max_attempts",
            3,
            raising=False,
        )
        monkeypatch.setattr(
            push_config.settings,
            "push_retry_base_delay_seconds",
            1,
            raising=False,
        )

        result = await service._send_with_retry(object())

        assert result == "provider-message-id"
        assert attempts["count"] == 3
        sleep_mock.assert_has_awaits([call(1), call(2)])

    @pytest.mark.asyncio
    async def test_send_with_retry_raises_after_max_attempts(self, monkeypatch):
        from app.services import push_config

        service = PushConfigService(db=None)  # type: ignore[arg-type]
        attempts = {"count": 0}

        def fake_send(_message):
            attempts["count"] += 1
            raise RuntimeError("permanent push failure")

        sleep_mock = AsyncMock()
        monkeypatch.setattr(push_config, "messaging", SimpleNamespace(send=fake_send))
        monkeypatch.setattr(push_config.asyncio, "sleep", sleep_mock)
        monkeypatch.setattr(
            push_config.settings,
            "push_retry_max_attempts",
            3,
            raising=False,
        )
        monkeypatch.setattr(
            push_config.settings,
            "push_retry_base_delay_seconds",
            1,
            raising=False,
        )

        with pytest.raises(RuntimeError, match="permanent push failure"):
            await service._send_with_retry(object())

        assert attempts["count"] == 3
        sleep_mock.assert_has_awaits([call(1), call(2)])


class TestNotificationEmailTemplates:
    @pytest.mark.parametrize("lang", ["fr", "ar", "en"])
    def test_notification_alert_template_renders_links(self, lang):
        html = _render_template(
            "notification_alert",
            lang,
            title="Phase 13 alert",
            body="Critical billing reminder",
            category="billing",
            action_url="https://example.test/billing/invoices",
            unsubscribe_url="https://example.test/unsubscribe?token=abc",
            open_tracking_url="https://example.test/email-open?token=abc",
        )

        assert "Phase 13 alert" in html
        assert "https://example.test/billing/invoices" in html
        assert "https://example.test/unsubscribe?token=abc" in html
        assert "https://example.test/email-open?token=abc" in html
        if lang == "ar":
            assert 'dir="rtl"' in html

    def test_notification_digest_template_renders_grouped_notifications(self):
        html = _render_template(
            "notification_digest",
            "ar",
            title="ملخص الإشعارات",
            grouped_notifications={
                "attendance": [
                    {
                        "title": "Absence aujourd'hui",
                        "body": "Justification requise",
                        "created_at": datetime(
                            2026, 3, 27, 7, 0, tzinfo=timezone.utc
                        ).isoformat(),
                        "action_url": "https://example.test/attendance/1",
                    }
                ],
                "academic": [
                    {
                        "title": "Math quiz published",
                        "body": "Open the new quiz",
                        "created_at": datetime(
                            2026, 3, 27, 7, 5, tzinfo=timezone.utc
                        ).isoformat(),
                        "action_url": "https://example.test/quizzes/1",
                    }
                ],
            },
            generated_at=datetime(2026, 3, 27, 7, 0, tzinfo=timezone.utc),
            unsubscribe_url="https://example.test/unsubscribe?token=abc",
            open_tracking_url="https://example.test/email-open?token=abc",
            action_base_url="https://example.test",
            is_rtl=True,
        )

        assert 'dir="rtl"' in html
        assert "attendance" in html
        assert "academic" in html
        assert (
            "Absence aujourd'hui" in html
            or "Absence aujourd&#39;hui" in html
        )
        assert "Math quiz published" in html
        assert "https://example.test/attendance/1" in html
        assert "https://example.test/quizzes/1" in html
        assert "https://example.test/unsubscribe?token=abc" in html
