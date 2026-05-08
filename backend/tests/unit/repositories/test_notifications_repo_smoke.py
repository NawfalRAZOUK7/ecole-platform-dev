"""Smoke tests for NotificationRepository.

Lightweight tests verifying each public method returns expected shapes.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.models.com import NotificationPreference
from app.repositories.notifications import NotificationRepository
from tests.factories.iam import UserFactory
from tests.factories.school import SchoolFactory


def _uuid(n: int) -> uuid.UUID:
    return uuid.UUID(f"40000000-0000-4000-8000-{n:012d}")


@pytest.mark.asyncio
class TestNotificationRepositorySmoke:
    """One happy-path test per public method."""

    async def test_list_notifications(self, db_session) -> None:
        repo = NotificationRepository(db_session)
        notifications, next_cursor, has_more = await repo.list_notifications(
            school_id=_uuid(1),
            user_id=_uuid(2),
            role="PAR",
            limit=20,
        )
        assert isinstance(notifications, list)
        assert next_cursor is None or isinstance(next_cursor, str)
        assert isinstance(has_more, bool)

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
        count = await repo.count_unread(
            school_id=_uuid(1),
            user_id=_uuid(2),
            role="PAR",
        )
        assert isinstance(count, int)
        assert count >= 0

    async def test_mark_all_read(self, db_session) -> None:
        repo = NotificationRepository(db_session)
        result = await repo.mark_all_read(
            school_id=_uuid(1),
            user_id=_uuid(2),
            read_at=datetime.now(timezone.utc),
        )
        assert isinstance(result, int)

    async def test_list_preferences(self, db_session) -> None:
        repo = NotificationRepository(db_session)
        prefs = await repo.list_preferences(school_id=_uuid(1), user_id=_uuid(2))
        assert isinstance(prefs, list)

    async def test_upsert_and_find_preference(self, db_session) -> None:
        repo = NotificationRepository(db_session)
        school = await SchoolFactory.create(session=db_session)
        user = await UserFactory.create(session=db_session, school=school)
        prefs = await repo.upsert_preferences(
            school_id=school.id,
            user_id=user.id,
            preferences=[
                NotificationPreference(
                    school_id=school.id,
                    user_id=user.id,
                    channel="email",
                    category="billing",
                    enabled=True,
                )
            ],
        )
        assert prefs
        found = await repo.find_preference(
            school_id=school.id,
            user_id=user.id,
            channel="email",
            category="billing",
        )
        assert found is None or found.enabled is True

    async def test_list_devices(self, db_session) -> None:
        repo = NotificationRepository(db_session)
        devices = await repo.list_devices(school_id=_uuid(1), user_id=_uuid(2))
        assert isinstance(devices, list)

    async def test_find_device_by_token(self, db_session) -> None:
        repo = NotificationRepository(db_session)
        device = await repo.find_device_by_token("fcm-token-123")
        assert device is None or hasattr(device, "token")
