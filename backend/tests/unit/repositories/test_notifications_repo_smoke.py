"""Smoke tests for NotificationRepository.

Lightweight tests verifying each public method returns expected shapes.
"""

from __future__ import annotations

import uuid

import pytest

from app.repositories.notifications import NotificationRepository


def _uuid(n: int) -> uuid.UUID:
    return uuid.UUID(f"40000000-0000-4000-8000-{n:012d}")


@pytest.mark.asyncio
class TestNotificationRepositorySmoke:
    """One happy-path test per public method."""

    async def test_list_notifications(self, db_session) -> None:
        repo = NotificationRepository(db_session)
        notifications = await repo.list_notifications(user_id=_uuid(1), limit=20)
        assert isinstance(notifications, list)

    async def test_get_notification(self, db_session) -> None:
        repo = NotificationRepository(db_session)
        notification = await repo.get_notification(_uuid(1))
        assert notification is None or hasattr(notification, "id")

    async def test_find_notification_by_idempotency_key(self, db_session) -> None:
        repo = NotificationRepository(db_session)
        notification = await repo.find_notification_by_idempotency_key("key-123")
        assert notification is None or hasattr(notification, "id")

    async def test_count_unread(self, db_session) -> None:
        repo = NotificationRepository(db_session)
        count = await repo.count_unread(user_id=_uuid(1))
        assert isinstance(count, int)
        assert count >= 0

    async def test_mark_all_read(self, db_session) -> None:
        repo = NotificationRepository(db_session)
        result = await repo.mark_all_read(user_id=_uuid(1))
        assert result is None or isinstance(result, int)

    async def test_list_preferences(self, db_session) -> None:
        repo = NotificationRepository(db_session)
        prefs = await repo.list_preferences(user_id=_uuid(1))
        assert isinstance(prefs, list)

    async def test_upsert_and_find_preference(self, db_session) -> None:
        repo = NotificationRepository(db_session)
        pref = await repo.upsert_preferences(
            user_id=_uuid(1),
            channel="email",
            category="billing",
            enabled=True,
        )
        assert pref is not None
        found = await repo.find_preference(
            user_id=_uuid(1), channel="email", category="billing"
        )
        assert found is None or found.enabled is True

    async def test_list_devices(self, db_session) -> None:
        repo = NotificationRepository(db_session)
        devices = await repo.list_devices(user_id=_uuid(1))
        assert isinstance(devices, list)

    async def test_find_device_by_token(self, db_session) -> None:
        repo = NotificationRepository(db_session)
        device = await repo.find_device_by_token("fcm-token-123")
        assert device is None or hasattr(device, "token")
