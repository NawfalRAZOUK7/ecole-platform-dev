"""Extended coverage tests for communication_notifications.py."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.repositories.communication_notifications import (
    NotificationRepository,
    NotificationDeliveryRepository,
)


def _uid():
    return uuid.uuid4()


def _now():
    return datetime.now(timezone.utc)


class _FR:
    def __init__(self, v=None, many=None, scalar=None, rowcount=1):
        self._v = v
        self._many = many or []
        self._scalar = scalar
        self.rowcount = rowcount

    def scalar_one_or_none(self):
        return self._v

    def scalar_one(self):
        return self._v

    def scalar(self):
        return self._scalar

    def scalars(self):
        many = self._many
        v = self._v
        return SimpleNamespace(all=lambda: many, first=lambda: (many[0] if many else v))

    def first(self):
        return self._many[0] if self._many else self._v

    def one(self):
        return self._v if self._v is not None else (0, 0)

    def one_or_none(self):
        return self._v

    def all(self):
        return self._many

    def mappings(self):
        return SimpleNamespace(all=lambda: self._many)

    def __iter__(self):
        return iter(self._many)


def _db(result=None, *, side_effects=None):
    r = result if result is not None else _FR()
    db = SimpleNamespace(
        execute=AsyncMock(return_value=r),
        add=Mock(),
        add_all=Mock(),
        flush=AsyncMock(),
        commit=AsyncMock(),
        delete=AsyncMock(),
        refresh=AsyncMock(),
    )
    if side_effects:
        db.execute.side_effect = side_effects
    return db


class TestNotificationRepositoryExtended:
    """Cover missing lines in communication_notifications.py."""

    @pytest.mark.asyncio
    async def test_list_notifications_admin_role(self):
        """ADM role does not filter by parent_id (branch 50->51 not taken)."""
        items = [SimpleNamespace(id=_uid(), created_at=_now())]
        db = _db(_FR(many=items))
        notifs, cursor, has_more = await NotificationRepository(db).list_notifications(
            school_id=_uid(),
            user_id=_uid(),
            role="ADM",
            limit=20,
        )
        assert notifs == items
        assert has_more is False

    @pytest.mark.asyncio
    async def test_list_notifications_non_admin_role(self):
        """Non-ADM role filters by parent_id (line 51)."""
        items = [SimpleNamespace(id=_uid(), created_at=_now())]
        db = _db(_FR(many=items))
        notifs, cursor, has_more = await NotificationRepository(db).list_notifications(
            school_id=_uid(),
            user_id=_uid(),
            role="PAR",
            limit=20,
        )
        assert notifs == items

    @pytest.mark.asyncio
    async def test_list_notifications_with_category_filter(self):
        """Cover category filter branch (line 54)."""
        db = _db(_FR(many=[]))
        notifs, _, _ = await NotificationRepository(db).list_notifications(
            school_id=_uid(),
            user_id=_uid(),
            role="ADM",
            category="academic",
            limit=10,
        )
        assert notifs == []

    @pytest.mark.asyncio
    async def test_list_notifications_read_true(self):
        """Cover read=True branch (line 57)."""
        db = _db(_FR(many=[]))
        notifs, _, _ = await NotificationRepository(db).list_notifications(
            school_id=_uid(),
            user_id=_uid(),
            role="ADM",
            read=True,
            limit=10,
        )
        assert notifs == []

    @pytest.mark.asyncio
    async def test_list_notifications_read_false(self):
        """Cover read=False branch (line 59)."""
        db = _db(_FR(many=[]))
        notifs, _, _ = await NotificationRepository(db).list_notifications(
            school_id=_uid(),
            user_id=_uid(),
            role="ADM",
            read=False,
            limit=10,
        )
        assert notifs == []

    @pytest.mark.asyncio
    async def test_list_notifications_from_dt(self):
        """Cover from_dt filter (line 62)."""
        db = _db(_FR(many=[]))
        notifs, _, _ = await NotificationRepository(db).list_notifications(
            school_id=_uid(),
            user_id=_uid(),
            role="ADM",
            from_dt=_now(),
            limit=10,
        )
        assert notifs == []

    @pytest.mark.asyncio
    async def test_list_notifications_to_dt(self):
        """Cover to_dt filter (line 64)."""
        db = _db(_FR(many=[]))
        notifs, _, _ = await NotificationRepository(db).list_notifications(
            school_id=_uid(),
            user_id=_uid(),
            role="ADM",
            to_dt=_now(),
            limit=10,
        )
        assert notifs == []

    @pytest.mark.asyncio
    async def test_list_notifications_channel_filter(self):
        """Cover channel filter (line 67)."""
        db = _db(_FR(many=[]))
        notifs, _, _ = await NotificationRepository(db).list_notifications(
            school_id=_uid(),
            user_id=_uid(),
            role="ADM",
            channel="email",
            limit=10,
        )
        assert notifs == []

    @pytest.mark.asyncio
    async def test_list_notifications_with_cursor(self):
        """Cover cursor decoding path (lines 74-77)."""
        from app.core.response import encode_cursor

        uid = _uid()
        cursor = encode_cursor(uid, _now().isoformat())
        db = _db(_FR(many=[]))
        notifs, _, _ = await NotificationRepository(db).list_notifications(
            school_id=_uid(),
            user_id=_uid(),
            role="ADM",
            cursor=cursor,
            limit=10,
        )
        assert notifs == []

    @pytest.mark.asyncio
    async def test_list_notifications_has_more(self):
        """When items > limit, has_more = True and next_cursor is generated."""
        items = [
            SimpleNamespace(id=_uid(), created_at=_now()) for _ in range(3)
        ]
        db = _db(_FR(many=items))
        notifs, next_cursor, has_more = await NotificationRepository(
            db
        ).list_notifications(
            school_id=_uid(),
            user_id=_uid(),
            role="ADM",
            limit=2,
        )
        assert has_more is True
        assert len(notifs) == 2
        assert next_cursor is not None

    @pytest.mark.asyncio
    async def test_count_unread_non_admin(self):
        """Cover non-admin branch in count_unread (line 137)."""
        db = _db(_FR(v=5))
        result = await NotificationRepository(db).count_unread(
            school_id=_uid(), user_id=_uid(), role="PAR"
        )
        assert result == 5

    @pytest.mark.asyncio
    async def test_count_unread_admin(self):
        """ADM role: no parent_id filter."""
        db = _db(_FR(v=0))
        result = await NotificationRepository(db).count_unread(
            school_id=_uid(), user_id=_uid(), role="ADM"
        )
        assert result == 0

    @pytest.mark.asyncio
    async def test_mark_all_read(self):
        """Cover mark_all_read (line 158)."""
        notif = SimpleNamespace(read_at=None)
        db = _db(_FR(many=[notif]))
        count = await NotificationRepository(db).mark_all_read(
            school_id=_uid(), user_id=_uid(), read_at=_now()
        )
        assert count == 1

    @pytest.mark.asyncio
    async def test_create_deliveries_empty(self):
        """Cover empty deliveries branch (lines 173-176)."""
        db = _db()
        result = await NotificationRepository(db).create_deliveries([])
        assert result == []
        db.add_all.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_deliveries_nonempty(self):
        """Cover non-empty deliveries path."""
        delivery = SimpleNamespace(id=_uid())
        db = _db()
        result = await NotificationRepository(db).create_deliveries([delivery])
        db.add_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_user_contacts_empty(self):
        """Cover empty user_ids early return (line 297)."""
        db = _db()
        result = await NotificationRepository(db).list_user_contacts([])
        assert result == {}
        db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_list_user_contacts_nonempty(self):
        """Cover non-empty path."""
        uid = _uid()
        user = SimpleNamespace(id=uid)
        db = _db(_FR(many=[user]))
        result = await NotificationRepository(db).list_user_contacts([uid])
        assert uid in result

    @pytest.mark.asyncio
    async def test_list_members_by_roles_empty(self):
        """Cover empty role_codes early return (line 309)."""
        db = _db()
        result = await NotificationRepository(db).list_members_by_roles(
            school_id=_uid(), role_codes=[]
        )
        assert result == set()
        db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_list_members_by_roles_nonempty(self):
        uid = _uid()
        db = _db(_FR(many=[uid]))
        result = await NotificationRepository(db).list_members_by_roles(
            school_id=_uid(), role_codes=["ADM", "DIR"]
        )
        assert uid in result

    @pytest.mark.asyncio
    async def test_list_students_for_classes_empty(self):
        """Cover empty class_ids early return (line 339)."""
        db = _db()
        result = await NotificationRepository(db).list_students_for_classes(
            school_id=_uid(), class_ids=[]
        )
        assert result == set()
        db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_list_students_for_classes_nonempty(self):
        uid = _uid()
        db = _db(_FR(many=[uid]))
        result = await NotificationRepository(db).list_students_for_classes(
            school_id=_uid(), class_ids=[_uid()]
        )
        assert uid in result

    @pytest.mark.asyncio
    async def test_list_parents_for_students_empty(self):
        """Cover empty student_ids early return (line 356)."""
        db = _db()
        result = await NotificationRepository(db).list_parents_for_students(
            school_id=_uid(), student_ids=[]
        )
        assert result == set()
        db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_list_parents_for_students_nonempty(self):
        uid = _uid()
        db = _db(_FR(many=[uid]))
        result = await NotificationRepository(db).list_parents_for_students(
            school_id=_uid(), student_ids=[_uid()]
        )
        assert uid in result

    @pytest.mark.asyncio
    async def test_list_teachers_for_classes_empty(self):
        """Cover empty class_ids early return (line 373)."""
        db = _db()
        result = await NotificationRepository(db).list_teachers_for_classes(
            school_id=_uid(), class_ids=[]
        )
        assert result == set()
        db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_list_teachers_for_classes_nonempty(self):
        uid = _uid()
        db = _db(_FR(many=[uid]))
        result = await NotificationRepository(db).list_teachers_for_classes(
            school_id=_uid(), class_ids=[_uid()]
        )
        assert uid in result

    @pytest.mark.asyncio
    async def test_list_unread_digest_notifications_no_since(self):
        """Cover list_unread_digest_notifications without since (lines 400-403)."""
        notif = SimpleNamespace(id=_uid())
        db = _db(_FR(many=[notif]))
        result = await NotificationRepository(db).list_unread_digest_notifications(
            school_id=_uid(), user_id=_uid()
        )
        assert result == [notif]

    @pytest.mark.asyncio
    async def test_list_unread_digest_notifications_with_since(self):
        """Cover since filter branch (line 401)."""
        db = _db(_FR(many=[]))
        result = await NotificationRepository(db).list_unread_digest_notifications(
            school_id=_uid(), user_id=_uid(), since=_now()
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_list_users_with_digest_preferences_no_school(self):
        """Cover list_users_with_digest_preferences without school_id (lines 411-419)."""
        db = _db(_FR(many=[]))
        result = await NotificationRepository(db).list_users_with_digest_preferences(
            digest_frequency="daily"
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_list_users_with_digest_preferences_with_school(self):
        """Cover school_id filter branch (line 417)."""
        pref = SimpleNamespace(id=_uid())
        db = _db(_FR(many=[pref]))
        result = await NotificationRepository(db).list_users_with_digest_preferences(
            school_id=_uid(), digest_frequency="weekly"
        )
        assert result == [pref]

    @pytest.mark.asyncio
    async def test_remove_user_notifications_cache(self):
        """Cover remove_user_notifications_cache (line 422)."""
        db = _db()
        uid = _uid()
        result = await NotificationRepository(db).remove_user_notifications_cache(uid)
        assert str(uid) in result


class TestNotificationDeliveryRepositoryExtended:
    """Cover NotificationDeliveryRepository methods (lines 434-479)."""

    @pytest.mark.asyncio
    async def test_get_delivery(self):
        """Cover get_delivery (lines 434-440)."""
        delivery = SimpleNamespace(id=_uid())
        db = _db(_FR(v=delivery))
        result = await NotificationDeliveryRepository(db).get_delivery(
            notification_id=_uid(), channel="email"
        )
        assert result is delivery

    @pytest.mark.asyncio
    async def test_get_delivery_not_found(self):
        db = _db(_FR(v=None))
        result = await NotificationDeliveryRepository(db).get_delivery(
            notification_id=_uid(), channel="push"
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_list_deliveries_for_notification(self):
        """Cover list_deliveries_for_notification (lines 446-451)."""
        delivery = SimpleNamespace(id=_uid())
        db = _db(_FR(many=[delivery]))
        result = await NotificationDeliveryRepository(
            db
        ).list_deliveries_for_notification(_uid())
        assert result == [delivery]

    @pytest.mark.asyncio
    async def test_get_delivery_by_id(self):
        """Cover get_delivery_by_id (lines 457-460)."""
        delivery = SimpleNamespace(id=_uid())
        db = _db(_FR(v=delivery))
        result = await NotificationDeliveryRepository(db).get_delivery_by_id(_uid())
        assert result is delivery

    @pytest.mark.asyncio
    async def test_save_delivery(self):
        """Cover save_delivery (lines 466-468)."""
        delivery = SimpleNamespace(id=_uid())
        db = _db()
        result = await NotificationDeliveryRepository(db).save_delivery(delivery)
        db.add.assert_called_once_with(delivery)
        assert result is delivery

    @pytest.mark.asyncio
    async def test_delete_deliveries_for_notification(self):
        """Cover delete_deliveries_for_notification (lines 474)."""
        db = _db()
        await NotificationDeliveryRepository(db).delete_deliveries_for_notification(
            _uid()
        )
        db.execute.assert_awaited_once()
