"""Unit tests for notification hub service."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.core.dependencies import AuthContext
from app.core.exceptions import NotFoundError
from app.services import notification_hub as notif_module
from app.services.notification_hub import NotificationHubService


def make_auth(role: str = "ADM") -> AuthContext:
    return AuthContext(
        user_id=uuid.uuid4(),
        role=role,
        school_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        permissions=set(),
    )


def make_notification(
    user_id: uuid.UUID,
    school_id: uuid.UUID,
    *,
    is_read: bool = False,
) -> SimpleNamespace:
    now = datetime(2026, 5, 1, tzinfo=timezone.utc)
    return SimpleNamespace(
        id=uuid.uuid4(),
        parent_id=user_id,
        school_id=school_id,
        title="Test notification",
        body="You have a new message.",
        category="general",
        channel="in_app",
        data={},
        read_at=now if is_read else None,
        is_read=is_read,
        created_at=now,
        updated_at=None,  # Required by serialize_notification in notification_hub.py
        deleted_at=None,  # Required by serialize_notification in notification_hub.py
        deliveries=[],  # Required by serialize_notification in notification_hub.py
        event_ref=None,  # Required by serialize_notification in notification_hub.py
        priority="normal",  # Required by serialize_notification in notification_hub.py
        action_url=None,  # Required by serialize_notification in notification_hub.py
        action_payload=None,  # Required by serialize_notification in notification_hub.py
    )


def setup_service(monkeypatch: pytest.MonkeyPatch):
    service = NotificationHubService(AsyncMock())
    service.repo = AsyncMock()
    service.push_service = AsyncMock()
    service.email_service = AsyncMock()

    # Patch redis_client so tests don't need a running Redis
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = None
    mock_redis.delete.return_value = None
    monkeypatch.setattr(notif_module, "redis_client", mock_redis)

    return service, mock_redis


class TestNotificationHubListNotifications:
    @pytest.mark.asyncio
    async def test_list_notifications_returns_serialized_items(self, monkeypatch):
        service, _redis = setup_service(monkeypatch)
        user_id = uuid.uuid4()
        school_id = uuid.uuid4()

        notif = make_notification(user_id, school_id)
        service.repo.list_notifications.return_value = ([notif], None, False)

        items, next_cursor, has_more = await service.list_notifications(
            school_id=school_id,
            user_id=user_id,
            role="ADM",
            category=None,
            channel=None,
            read=None,
            from_dt=None,
            to_dt=None,
            cursor=None,
            limit=20,
        )

        assert len(items) == 1
        assert items[0]["title"] == "Test notification"
        assert next_cursor is None
        assert has_more is False

    @pytest.mark.asyncio
    async def test_list_notifications_empty_returns_no_cursor(self, monkeypatch):
        service, _redis = setup_service(monkeypatch)
        service.repo.list_notifications.return_value = ([], None, False)

        items, next_cursor, has_more = await service.list_notifications(
            school_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            role="TCH",
            category=None,
            channel=None,
            read=None,
            from_dt=None,
            to_dt=None,
            cursor=None,
            limit=10,
        )

        assert items == []
        assert next_cursor is None
        assert has_more is False


class TestNotificationHubUnreadCount:
    @pytest.mark.asyncio
    async def test_unread_count_from_db_when_cache_miss(self, monkeypatch):
        service, mock_redis = setup_service(monkeypatch)
        mock_redis.get.return_value = None
        service.repo.count_unread.return_value = 7

        count, from_cache = await service.unread_count(
            school_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            role="TCH",
        )

        assert count == 7
        assert from_cache is False
        service.repo.count_unread.assert_called_once()

    @pytest.mark.asyncio
    async def test_unread_count_from_cache_when_hit(self, monkeypatch):
        service, mock_redis = setup_service(monkeypatch)
        mock_redis.get.return_value = b"3"

        count, from_cache = await service.unread_count(
            school_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            role="TCH",
        )

        assert count == 3
        assert from_cache is True
        service.repo.count_unread.assert_not_called()
