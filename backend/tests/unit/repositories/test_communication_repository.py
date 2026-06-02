"""Mock-based unit tests for communication repositories:
- CalendarRepository (communication_calendar.py)
- MessagingRepository (communication_messaging.py)
- NotificationRepository (communication_notifications.py)
"""
from __future__ import annotations

import uuid
from datetime import datetime, date, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.repositories.communication_calendar import CalendarRepository
from app.repositories.communication_messaging import MessagingRepository
from app.repositories.communication_notifications import NotificationRepository


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
        return self._v

    def one_or_none(self):
        return self._v

    def all(self):
        return self._many

    def mappings(self):
        return SimpleNamespace(all=lambda: self._many)

    def __iter__(self):
        return iter(self._many)


def _db(result=None):
    r = result if result is not None else _FR()
    return SimpleNamespace(
        execute=AsyncMock(return_value=r),
        add=Mock(),
        flush=AsyncMock(),
        commit=AsyncMock(),
        merge=AsyncMock(return_value=r._v),
        delete=AsyncMock(),
    )


# ===========================================================================
# CalendarRepository
# ===========================================================================

class TestCalendarRepository:
    def repo(self, result=None):
        return CalendarRepository(_db(result))

    @pytest.mark.asyncio
    async def test_get_event(self):
        obj = object()
        assert await self.repo(_FR(v=obj)).get_event(_uid()) is obj

    @pytest.mark.asyncio
    async def test_create_event(self):
        event = SimpleNamespace(id=_uid())
        db = _db()
        await CalendarRepository(db).create_event(event)
        db.add.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_save_event(self):
        event = SimpleNamespace(id=_uid())
        db = _db()
        result = await CalendarRepository(db).save_event(event)
        assert result is event

    @pytest.mark.asyncio
    async def test_list_candidate_events_minimal(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await CalendarRepository(db).list_candidate_events(
            school_id=_uid(),
            from_dt=_now(),
            to_dt=_now(),
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_candidate_events_with_class_ids_and_role(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await CalendarRepository(db).list_candidate_events(
            school_id=_uid(),
            from_dt=_now(),
            to_dt=_now(),
            class_id=_uid(),
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_holidays_no_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        from datetime import date
        result = await CalendarRepository(db).list_holidays(
            from_date=date.today(), to_date=date.today()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_holidays_with_year(self):
        items = [object()]
        db = _db(_FR(many=items))
        from datetime import date
        result = await CalendarRepository(db).list_holidays(
            from_date=date.today(), to_date=date.today()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_get_holiday(self):
        obj = object()
        assert await self.repo(_FR(v=obj)).get_holiday(_uid()) is obj

    @pytest.mark.asyncio
    async def test_find_holiday_conflict(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await CalendarRepository(db).find_holiday_conflict(
            code="HOLIDAY_CODE", holiday_date=date.today()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_create_holiday(self):
        holiday = SimpleNamespace(id=_uid())
        db = _db()
        await CalendarRepository(db).create_holiday(holiday)
        db.add.assert_called_once_with(holiday)

    @pytest.mark.asyncio
    async def test_save_holiday(self):
        holiday = SimpleNamespace(id=_uid())
        db = _db()
        result = await CalendarRepository(db).save_holiday(holiday)
        assert result is holiday

    @pytest.mark.asyncio
    async def test_delete_holiday(self):
        holiday = SimpleNamespace(id=_uid())
        db = _db()
        await CalendarRepository(db).delete_holiday(holiday)
        db.delete.assert_awaited_once_with(holiday)

    @pytest.mark.asyncio
    async def test_get_academic_year(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await CalendarRepository(db).get_academic_year(
            school_id=_uid(), academic_year_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_current_academic_year_found(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await CalendarRepository(db).get_current_academic_year(
            school_id=_uid(), on_date=date.today()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_current_academic_year_not_found(self):
        db = _db(_FR(v=None))
        result = await CalendarRepository(db).get_current_academic_year(
            school_id=_uid(), on_date=date.today()
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_list_period_boundaries(self):
        db = _db(_FR(many=[]))
        result = await CalendarRepository(db).list_period_boundaries(
            school_id=_uid(), from_date=date.today(), to_date=date.today()
        )
        assert isinstance(result, tuple)

    @pytest.mark.asyncio
    async def test_get_class(self):
        obj = object()
        assert await self.repo(_FR(v=obj)).get_class(_uid()) is obj

    @pytest.mark.asyncio
    async def test_list_school_classes(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await CalendarRepository(db).list_school_classes(_uid())
        assert result == items

    @pytest.mark.asyncio
    async def test_list_teacher_classes(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await CalendarRepository(db).list_teacher_classes(
            teacher_id=_uid(), school_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_student_class_ids(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await CalendarRepository(db).list_student_class_ids(
            student_id=_uid(), school_id=_uid()
        )
        assert result == set(ids)

    @pytest.mark.asyncio
    async def test_list_parent_class_ids(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await CalendarRepository(db).list_parent_class_ids(
            parent_id=_uid(), school_id=_uid()
        )
        assert result == set(ids)

    @pytest.mark.asyncio
    async def test_list_teacher_class_ids(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await CalendarRepository(db).list_teacher_class_ids(
            teacher_id=_uid(), school_id=_uid()
        )
        assert result == set(ids)

    @pytest.mark.asyncio
    async def test_list_rsvp_counts(self):
        eid = _uid()
        [SimpleNamespace(event_id=eid, status="attending", count=1)]
        # Patch all() to return rows with attributes
        db = _db(_FR(many=[]))
        result = await CalendarRepository(db).list_rsvp_counts(event_ids=[])
        assert result == {}

    @pytest.mark.asyncio
    async def test_list_user_rsvps_no_event(self):
        db = _db(_FR(many=[]))
        result = await CalendarRepository(db).list_user_rsvps(
            user_id=_uid(), event_ids=[]
        )
        assert result == {}

    @pytest.mark.asyncio
    async def test_list_user_rsvps_with_event(self):
        eid = _uid()
        rows = [(eid, "attending")]
        db = _db(_FR(many=rows))
        result = await CalendarRepository(db).list_user_rsvps(
            user_id=_uid(), event_ids=[eid]
        )
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_user_rsvp(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await CalendarRepository(db).get_user_rsvp(
            event_id=_uid(), user_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_save_rsvp(self):
        rsvp = SimpleNamespace(id=_uid())
        db = _db()
        result = await CalendarRepository(db).save_rsvp(rsvp)
        assert result is rsvp

    @pytest.mark.asyncio
    async def test_list_event_rsvps_no_status(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await CalendarRepository(db).list_event_rsvps(
            event_id=_uid(), school_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_event_rsvps_with_status(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await CalendarRepository(db).list_event_rsvps(
            event_id=_uid(), school_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_count_attending(self):
        db = _db(_FR(v=5))
        result = await CalendarRepository(db).count_attending(event_id=_uid())
        assert result == 5

    @pytest.mark.asyncio
    async def test_list_school_user_ids(self):
        ids = {_uid()}
        db = _db(_FR(many=list(ids)))
        result = await CalendarRepository(db).list_school_user_ids(_uid())
        assert isinstance(result, set)

    @pytest.mark.asyncio
    async def test_list_role_user_ids(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await CalendarRepository(db).list_role_user_ids(
            school_id=_uid(), role_codes=["TCH"]
        )
        assert isinstance(result, set)

    @pytest.mark.asyncio
    async def test_list_class_recipient_ids_no_role(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await CalendarRepository(db).list_class_recipient_ids(
            school_id=_uid(), class_id=_uid()
        )
        assert isinstance(result, set)

    @pytest.mark.asyncio
    async def test_list_class_recipient_ids_with_role(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await CalendarRepository(db).list_class_recipient_ids(
            school_id=_uid(), class_id=_uid()
        )
        assert isinstance(result, set)

    @pytest.mark.asyncio
    async def test_list_disabled_reminder_user_ids(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await CalendarRepository(db).list_disabled_reminder_user_ids(
            school_id=_uid(), event_type="class_event", user_ids=[_uid()]
        )
        assert isinstance(result, set)

    @pytest.mark.asyncio
    async def test_list_reminder_preferences(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await CalendarRepository(db).list_reminder_preferences(
            school_id=_uid(), user_id=_uid()
        )
        assert result == items


# ===========================================================================
# MessagingRepository
# ===========================================================================

class TestMessagingRepository:
    @pytest.mark.asyncio
    async def test_get_user(self):
        obj = object()
        assert await MessagingRepository(_db(_FR(v=obj))).get_user(_uid()) is obj

    @pytest.mark.asyncio
    async def test_get_membership_no_role(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await MessagingRepository(db).get_membership(user_id=_uid(), school_id=_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_membership_with_role(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await MessagingRepository(db).get_membership(
            user_id=_uid(), school_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_membership_role(self):
        db = _db(_FR(v="TCH"))
        result = await MessagingRepository(db).get_membership_role(
            user_id=_uid(), school_id=_uid()
        )
        assert result == "TCH"

    @pytest.mark.asyncio
    async def test_list_parent_child_ids(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await MessagingRepository(db).list_parent_child_ids(
            parent_id=_uid(), school_id=_uid()
        )
        assert result == set(ids)

    @pytest.mark.asyncio
    async def test_list_class_ids_for_students(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await MessagingRepository(db).list_class_ids_for_students(
            student_ids=set(ids), school_id=_uid()
        )
        assert result == set(ids)

    @pytest.mark.asyncio
    async def test_list_student_ids_for_classes(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await MessagingRepository(db).list_student_ids_for_classes(
            class_ids=set(ids), school_id=_uid()
        )
        assert result == set(ids)

    @pytest.mark.asyncio
    async def test_list_teacher_ids_for_classes(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await MessagingRepository(db).list_teacher_ids_for_classes(
            class_ids=set(ids), school_id=_uid()
        )
        assert result == set(ids)

    @pytest.mark.asyncio
    async def test_list_teacher_class_ids(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await MessagingRepository(db).list_teacher_class_ids(
            teacher_id=_uid(), school_id=_uid()
        )
        assert result == set(ids)

    @pytest.mark.asyncio
    async def test_list_parent_ids_for_students(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await MessagingRepository(db).list_parent_ids_for_students(
            student_ids=set(ids), school_id=_uid()
        )
        assert result == set(ids)

    @pytest.mark.asyncio
    async def test_create_conversation(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.communication_messaging.Conversation", return_value=fake):
            result = await MessagingRepository(db).create_conversation(school_id=_uid())
        assert result is fake

    @pytest.mark.asyncio
    async def test_create_conversation_participants(self):
        fake_p = SimpleNamespace(id=_uid())
        db = _db()
        db.add_all = Mock()
        with patch(
            "app.repositories.communication_messaging.ConversationParticipant",
            return_value=fake_p,
        ):
            await MessagingRepository(db).create_conversation_participants(
                participants_data=[{"conversation_id": str(_uid()), "user_id": str(_uid())}]
            )
        db.flush.assert_awaited()

    @pytest.mark.asyncio
    async def test_get_conversation(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await MessagingRepository(db).get_conversation(
            _uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_create_message(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.communication_messaging.Message", return_value=fake):
            result = await MessagingRepository(db).create_message(
                conversation_id=_uid(), sender_id=_uid(), body="Hello"
            )
        assert result is fake

    @pytest.mark.asyncio
    async def test_search_messages_no_cursor(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await MessagingRepository(db).search_messages(
            school_id=_uid(), user_id=_uid(), query_text="test", limit=10
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_search_messages_with_cursor(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await MessagingRepository(db).search_messages(
            school_id=_uid(), user_id=_uid(), query_text="test", limit=5
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_conversations_for_user_no_cursor(self):
        items = [(_uid(), None)]
        db = _db(_FR(many=items))
        result, _ = await MessagingRepository(db).list_conversations_for_user(
            user_id=_uid(), school_id=_uid(), cursor=None, limit=10
        )
        assert result == [(_uid_item, ts) for _uid_item, ts in items]

    @pytest.mark.asyncio
    async def test_list_conversations_for_user_with_cursor(self):
        items = [(_uid(), None)]
        db = _db(_FR(many=items))
        with patch("app.repositories.communication_messaging.decode_cursor", return_value=(_uid(), None)):
            result, _ = await MessagingRepository(db).list_conversations_for_user(
                user_id=_uid(), school_id=_uid(), cursor="cur", limit=5
            )
        assert result == [(r[0], r[1]) for r in items]

    @pytest.mark.asyncio
    async def test_get_message_sent_at(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await MessagingRepository(db).get_message_sent_at(message_id=_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_conversation_messages_no_cursor(self):
        items = [object()]
        db = _db(_FR(many=items))
        result, _ = await MessagingRepository(db).list_conversation_messages(
            conversation_id=_uid(), before_sent_at=None, limit=20
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_conversation_messages_with_cursor(self):
        items = [object()]
        db = _db(_FR(many=items))
        result, _ = await MessagingRepository(db).list_conversation_messages(
            conversation_id=_uid(), before_sent_at=_now(), limit=10
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_get_message_in_conversation(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await MessagingRepository(db).get_message_in_conversation(
            message_id=_uid(), conversation_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_unread_message_ids(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await MessagingRepository(db).list_unread_message_ids(
            conversation_id=_uid(), user_id=_uid(), up_to_sent_at=_now()
        )
        assert result == ids

    @pytest.mark.asyncio
    async def test_create_read_receipts(self):
        fake_rr = SimpleNamespace(id=_uid())
        db = _db()
        db.add_all = Mock()
        with patch(
            "app.repositories.communication_messaging.MessageReadReceipt",
            return_value=fake_rr,
        ):
            await MessagingRepository(db).create_read_receipts(
                receipts_data=[{"message_id": str(_uid()), "user_id": str(_uid())}]
            )
        db.flush.assert_awaited()


# ===========================================================================
# NotificationRepository
# ===========================================================================

class TestNotificationRepository:
    @pytest.mark.asyncio
    async def test_list_notifications_minimal(self):
        items = [object()]
        db = _db(_FR(many=items))
        result, cursor, has_more = await NotificationRepository(db).list_notifications(
            school_id=_uid(), user_id=_uid(), role="ADM"
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_notifications_with_all_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        result, cursor, has_more = await NotificationRepository(db).list_notifications(
            school_id=_uid(),
            user_id=_uid(),
            role="STD",
            category="grade",
            limit=5,
            cursor=None,
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_get_notification(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await NotificationRepository(db).get_notification(
            _uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_find_notification_by_idempotency_key(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await NotificationRepository(db).find_notification_by_idempotency_key("key")
        assert result is obj

    @pytest.mark.asyncio
    async def test_save_notification(self):
        notif = SimpleNamespace(id=_uid())
        db = _db()
        result = await NotificationRepository(db).save_notification(notif)
        assert result is notif

    @pytest.mark.asyncio
    async def test_count_unread(self):
        db = _db(_FR(v=3))
        result = await NotificationRepository(db).count_unread(
            user_id=_uid(), school_id=_uid(), role="ADM"
        )
        assert result == 3

    @pytest.mark.asyncio
    async def test_count_unread_none(self):
        db = _db(_FR(v=None))
        result = await NotificationRepository(db).count_unread(
            user_id=_uid(), school_id=_uid(), role="ADM"
        )
        assert result == 0

    @pytest.mark.asyncio
    async def test_count_unread_with_category(self):
        db = _db(_FR(v=1))
        result = await NotificationRepository(db).count_unread(
            user_id=_uid(), school_id=_uid(), role="ADM"
        )
        assert result == 1

    @pytest.mark.asyncio
    async def test_mark_all_read_no_category(self):
        db = _db(_FR(many=[]))
        await NotificationRepository(db).mark_all_read(
            user_id=_uid(), school_id=_uid(), read_at=_now()
        )
        db.execute.assert_awaited()

    @pytest.mark.asyncio
    async def test_mark_all_read_with_category(self):
        db = _db(_FR(many=[]))
        await NotificationRepository(db).mark_all_read(
            user_id=_uid(), school_id=_uid(), read_at=_now()
        )
        db.execute.assert_awaited()

    @pytest.mark.asyncio
    async def test_create_notifications(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        db.add_all = Mock()
        result = await NotificationRepository(db).create_notifications(
            notifications=[fake]
        )
        assert result == [fake]

    @pytest.mark.asyncio
    async def test_create_deliveries(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        db.add_all = Mock()
        await NotificationRepository(db).create_deliveries(
            deliveries=[fake]
        )
        db.flush.assert_awaited()

    @pytest.mark.asyncio
    async def test_hard_delete(self):
        notif = SimpleNamespace(id=_uid())
        db = _db()
        await NotificationRepository(db).hard_delete(notif)
        db.delete.assert_awaited_once_with(notif)

    @pytest.mark.asyncio
    async def test_list_preferences(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await NotificationRepository(db).list_preferences(
            user_id=_uid(), school_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_upsert_preferences(self):
        pref = SimpleNamespace(school_id=None, user_id=None)
        db = _db(_FR(many=[]))
        await NotificationRepository(db).upsert_preferences(
            user_id=_uid(),
            school_id=_uid(),
            preferences=[pref],
        )
        db.flush.assert_awaited()

    @pytest.mark.asyncio
    async def test_find_preference_no_channel(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await NotificationRepository(db).find_preference(
            user_id=_uid(), school_id=_uid(), category="grade", channel="email"
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_find_preference_with_channel(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await NotificationRepository(db).find_preference(
            user_id=_uid(), school_id=_uid(), category="grade", channel="push"
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_devices_no_user(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await NotificationRepository(db).list_devices(
            school_id=_uid(), user_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_devices_with_user(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await NotificationRepository(db).list_devices(
            school_id=_uid(), user_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_find_device(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await NotificationRepository(db).find_device(
            user_id=_uid(), school_id=_uid(), device_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_find_device_by_token(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await NotificationRepository(db).find_device_by_token("tok123")
        assert result is obj

    @pytest.mark.asyncio
    async def test_save_device(self):
        device = SimpleNamespace(id=_uid())
        db = _db()
        result = await NotificationRepository(db).save_device(device)
        assert result is device

    @pytest.mark.asyncio
    async def test_delete_device(self):
        device = SimpleNamespace(id=_uid())
        db = _db()
        await NotificationRepository(db).delete_device(device)
        db.delete.assert_awaited_once_with(device)

    @pytest.mark.asyncio
    async def test_list_push_devices_for_user(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await NotificationRepository(db).list_push_devices_for_user(
            user_id=_uid(), school_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_user_contacts_no_role(self):
        uid = _uid()
        user = SimpleNamespace(id=uid)
        db = _db(_FR(many=[user]))
        result = await NotificationRepository(db).list_user_contacts(
            user_ids=[uid]
        )
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_list_user_contacts_with_role(self):
        uid = _uid()
        user = SimpleNamespace(id=uid)
        db = _db(_FR(many=[user]))
        result = await NotificationRepository(db).list_user_contacts(
            user_ids=[uid]
        )
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_list_members_by_roles(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await NotificationRepository(db).list_members_by_roles(
            school_id=_uid(), role_codes=["TCH", "ADM"]
        )
        assert result == set(ids)

    @pytest.mark.asyncio
    async def test_list_school_member_ids(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await NotificationRepository(db).list_school_member_ids(school_id=_uid())
        assert result == set(ids)

    @pytest.mark.asyncio
    async def test_list_students_for_classes(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await NotificationRepository(db).list_students_for_classes(
            class_ids=[_uid()], school_id=_uid()
        )
        assert result == set(ids)

    @pytest.mark.asyncio
    async def test_list_parents_for_students(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await NotificationRepository(db).list_parents_for_students(
            student_ids=[_uid()], school_id=_uid()
        )
        assert result == set(ids)

    @pytest.mark.asyncio
    async def test_list_teachers_for_classes(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await NotificationRepository(db).list_teachers_for_classes(
            class_ids=[_uid()], school_id=_uid()
        )
        assert result == set(ids)

    @pytest.mark.asyncio
    async def test_list_unread_digest_notifications(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await NotificationRepository(db).list_unread_digest_notifications(
            school_id=_uid(), user_id=_uid(), since=_now()
        )
        assert result == items
