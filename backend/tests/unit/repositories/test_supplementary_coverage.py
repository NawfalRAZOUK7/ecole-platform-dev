"""Supplementary coverage tests with correct method signatures.

Covers repositories where the primary test files had wrong signatures:
- AuditRepository
- LoginHistoryRepository
- CalendarRepository
- Additional calendar methods (reminders)
"""

from __future__ import annotations

import uuid
from datetime import datetime, date, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.repositories.audit import AuditRepository
from app.repositories.auth_login_history import LoginHistoryRepository
from app.repositories.communication_calendar import CalendarRepository


def _uid():
    return uuid.uuid4()


def _now():
    return datetime.now(timezone.utc)


def _today():
    return date.today()


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
        return SimpleNamespace(all=lambda: self._many)

    def all(self):
        return self._many

    def one_or_none(self):
        return self._v


def _db(result=None, *, side_effects=None, flush_raises=None):
    r = result if result is not None else _FR()
    db = SimpleNamespace(
        execute=AsyncMock(return_value=r),
        add=Mock(),
        add_all=Mock(),
        flush=AsyncMock(),
        commit=AsyncMock(),
        rollback=AsyncMock(),
        merge=AsyncMock(),
        delete=AsyncMock(),
    )
    if flush_raises:
        db.flush.side_effect = flush_raises
    if side_effects:
        db.execute.side_effect = side_effects
    return db


# ===========================================================================
# AuditRepository
# ===========================================================================


class TestAuditRepositoryCorrect:
    @pytest.mark.asyncio
    async def test_create_log(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.audit.AuditLog", return_value=fake):
            result = await AuditRepository(db).create_log(
                action_type="login", outcome="success"
            )
        assert result is fake

    @pytest.mark.asyncio
    async def test_list_logs_no_filters_no_cursor(self):
        items = [object()]
        db = _db(_FR(many=items))
        result, cursor, has_more = await AuditRepository(db).list_logs()
        assert result == items
        assert has_more is False

    @pytest.mark.asyncio
    async def test_list_logs_with_all_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        result, cursor, has_more = await AuditRepository(db).list_logs(
            filters={
                "school_id": _uid(),
                "actor_id": _uid(),
                "action_type": "login",
                "target_type": "user",
                "outcome": "success",
                "error_code": "E001",
                "correlation_id": "corr-123",
                "from_dt": _now(),
                "to_dt": _now(),
            }
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_logs_with_cursor(self):
        now = _now()
        items = [SimpleNamespace(id=_uid(), created_at=now) for _ in range(6)]
        db = _db(_FR(many=items))
        with patch(
            "app.repositories.audit.decode_cursor",
            return_value=(_uid(), now.isoformat()),
        ):
            result, cursor, has_more = await AuditRepository(db).list_logs(
                cursor="cur", limit=5
            )
        assert has_more is True

    @pytest.mark.asyncio
    async def test_list_logs_no_more(self):
        items = [object()]
        db = _db(_FR(many=items))
        result, cursor, has_more = await AuditRepository(db).list_logs(limit=10)
        assert has_more is False
        assert cursor is None


# ===========================================================================
# LoginHistoryRepository
# ===========================================================================


class TestLoginHistoryRepositoryCorrect:
    @pytest.mark.asyncio
    async def test_create_login_record_success(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch(
            "app.repositories.auth_login_history.LoginHistory", return_value=fake
        ):
            result = await LoginHistoryRepository(db).create_login_record(
                user_id=_uid(), school_id=_uid()
            )
        assert result is fake

    @pytest.mark.asyncio
    async def test_create_login_record_integrity_error(self):
        from sqlalchemy.exc import IntegrityError

        fake = SimpleNamespace(id=_uid())
        db = _db(flush_raises=IntegrityError("stmt", "params", Exception("fk")))
        db.rollback = AsyncMock()
        with patch(
            "app.repositories.auth_login_history.LoginHistory", return_value=fake
        ):
            result = await LoginHistoryRepository(db).create_login_record(
                user_id=_uid(), school_id=_uid()
            )
        assert result is None

    @pytest.mark.asyncio
    async def test_list_user_login_history_no_cursor(self):
        items = [object()]
        db = _db(_FR(many=items))
        result, cursor, has_more = await LoginHistoryRepository(
            db
        ).list_user_login_history(_uid(), 20, None)
        assert result == items
        assert has_more is False

    @pytest.mark.asyncio
    async def test_list_user_login_history_has_more(self):
        now = _now()
        items = [SimpleNamespace(id=_uid(), created_at=now) for _ in range(21)]
        db = _db(_FR(many=items))
        result, cursor, has_more = await LoginHistoryRepository(
            db
        ).list_user_login_history(_uid(), 20, None)
        assert has_more is True
        assert len(result) == 20
        assert cursor is not None

    @pytest.mark.asyncio
    async def test_list_user_login_history_with_cursor(self):
        now = _now()
        items = [object()]
        db = _db(_FR(many=items))
        with patch(
            "app.repositories.auth_login_history.decode_cursor",
            return_value=(_uid(), now.isoformat()),
        ):
            result, cursor, has_more = await LoginHistoryRepository(
                db
            ).list_user_login_history(_uid(), 10, "cursor")
        assert result == items

    @pytest.mark.asyncio
    async def test_get_device_fingerprints(self):
        fps = ["fp1", "fp2"]
        db = _db(_FR(many=fps))
        result = await LoginHistoryRepository(db).get_device_fingerprints(_uid())
        assert isinstance(result, set)

    @pytest.mark.asyncio
    async def test_get_device_fingerprints_with_days(self):
        fps = ["fp1"]
        db = _db(_FR(many=fps))
        result = await LoginHistoryRepository(db).get_device_fingerprints(
            _uid(), days=60
        )
        assert isinstance(result, set)


# ===========================================================================
# CalendarRepository (correct signatures)
# ===========================================================================


class TestCalendarRepositoryCorrect:
    @pytest.mark.asyncio
    async def test_list_candidate_events_minimal(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await CalendarRepository(db).list_candidate_events(
            school_id=_uid(), from_dt=_now(), to_dt=_now()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_candidate_events_with_type(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await CalendarRepository(db).list_candidate_events(
            school_id=_uid(), from_dt=_now(), to_dt=_now(), event_type="CLASS"
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_holidays_minimal(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await CalendarRepository(db).list_holidays(
            from_date=_today(), to_date=_today()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_find_holiday_conflict(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await CalendarRepository(db).find_holiday_conflict(
            code="EID", holiday_date=_today()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_find_holiday_conflict_with_exclude(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await CalendarRepository(db).find_holiday_conflict(
            code="EID", holiday_date=_today(), exclude_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_current_academic_year(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await CalendarRepository(db).get_current_academic_year(
            school_id=_uid(), on_date=_today()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_current_academic_year_not_found(self):
        db = _db(_FR(v=None))
        result = await CalendarRepository(db).get_current_academic_year(
            school_id=_uid(), on_date=_today()
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_list_period_boundaries(self):
        periods = [object()]
        years = [object()]
        # list_period_boundaries returns a tuple of (periods, years)
        # It makes 2 DB calls
        db = _db(side_effects=[_FR(many=periods), _FR(many=years)])
        await CalendarRepository(db).list_period_boundaries(
            school_id=_uid(), from_date=_today(), to_date=_today()
        )

    @pytest.mark.asyncio
    async def test_list_student_class_ids(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await CalendarRepository(db).list_student_class_ids(
            student_id=_uid(), school_id=_uid()
        )
        assert isinstance(result, set)

    @pytest.mark.asyncio
    async def test_list_parent_class_ids(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await CalendarRepository(db).list_parent_class_ids(
            parent_id=_uid(), school_id=_uid()
        )
        assert isinstance(result, set)

    @pytest.mark.asyncio
    async def test_list_teacher_class_ids(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await CalendarRepository(db).list_teacher_class_ids(
            teacher_id=_uid(), school_id=_uid()
        )
        assert isinstance(result, set)

    @pytest.mark.asyncio
    async def test_list_rsvp_counts_empty_event_ids(self):
        db = _db()
        result = await CalendarRepository(db).list_rsvp_counts(event_ids=[])
        assert result == {}

    @pytest.mark.asyncio
    async def test_list_rsvp_counts_nonempty(self):
        db = _db(_FR(many=[]))
        result = await CalendarRepository(db).list_rsvp_counts(event_ids=[_uid()])
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_list_user_rsvps_empty_event_ids(self):
        db = _db()
        result = await CalendarRepository(db).list_user_rsvps(
            user_id=_uid(), event_ids=[]
        )
        assert result == {}

    @pytest.mark.asyncio
    async def test_list_user_rsvps_nonempty(self):
        db = _db(_FR(many=[(_uid(), "attending")]))
        result = await CalendarRepository(db).list_user_rsvps(
            user_id=_uid(), event_ids=[_uid()]
        )
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_list_event_rsvps(self):
        db = _db(_FR(many=[]))
        result = await CalendarRepository(db).list_event_rsvps(
            event_id=_uid(), school_id=_uid()
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_count_attending(self):
        db = _db(_FR(v=5))
        result = await CalendarRepository(db).count_attending(event_id=_uid())
        assert result == 5

    @pytest.mark.asyncio
    async def test_list_school_user_ids(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await CalendarRepository(db).list_school_user_ids(_uid())
        assert isinstance(result, set)

    @pytest.mark.asyncio
    async def test_list_role_user_ids_empty(self):
        db = _db()
        result = await CalendarRepository(db).list_role_user_ids(
            school_id=_uid(), role_codes=[]
        )
        assert result == set()

    @pytest.mark.asyncio
    async def test_list_role_user_ids_nonempty(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await CalendarRepository(db).list_role_user_ids(
            school_id=_uid(), role_codes=["TCH"]
        )
        assert isinstance(result, set)

    @pytest.mark.asyncio
    async def test_list_class_recipient_ids(self):
        # Calls execute 3 times: students, parents (if students exist), teachers
        student_ids = [_uid()]
        parent_ids = [_uid()]
        teacher_ids = [_uid()]
        db = _db(
            side_effects=[
                _FR(many=student_ids),
                _FR(many=parent_ids),
                _FR(many=teacher_ids),
            ]
        )
        result = await CalendarRepository(db).list_class_recipient_ids(
            school_id=_uid(), class_id=_uid()
        )
        assert isinstance(result, set)

    @pytest.mark.asyncio
    async def test_list_class_recipient_ids_no_students(self):
        # When no students, parent query is skipped (2 execute calls)
        teacher_ids = [_uid()]
        db = _db(
            side_effects=[
                _FR(many=[]),  # no students
                _FR(many=teacher_ids),  # teachers
            ]
        )
        result = await CalendarRepository(db).list_class_recipient_ids(
            school_id=_uid(), class_id=_uid()
        )
        assert isinstance(result, set)

    @pytest.mark.asyncio
    async def test_list_disabled_reminder_user_ids_empty_user_ids(self):
        db = _db()
        result = await CalendarRepository(db).list_disabled_reminder_user_ids(
            school_id=_uid(), event_type="CLASS", user_ids=[]
        )
        assert result == set()

    @pytest.mark.asyncio
    async def test_list_disabled_reminder_user_ids_nonempty(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await CalendarRepository(db).list_disabled_reminder_user_ids(
            school_id=_uid(), event_type="CLASS", user_ids=[_uid()]
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

    @pytest.mark.asyncio
    async def test_find_reminder_preference(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await CalendarRepository(db).find_reminder_preference(
            school_id=_uid(), user_id=_uid(), event_type="CLASS"
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_save_reminder_preference(self):
        pref = SimpleNamespace(id=_uid())
        db = _db()
        result = await CalendarRepository(db).save_reminder_preference(pref)
        assert result is pref

    @pytest.mark.asyncio
    async def test_list_due_reminders(self):
        db = _db(_FR(many=[]))
        result = await CalendarRepository(db).list_due_reminders(now=_now())
        assert result == []

    @pytest.mark.asyncio
    async def test_mark_reminders_sent_empty(self):
        db = _db()
        await CalendarRepository(db).mark_reminders_sent([], sent_at=_now())
        db.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_mark_reminders_sent_nonempty(self):
        reminder = SimpleNamespace(id=_uid(), sent=False, sent_at=None)
        db = _db(_FR(many=[reminder]))
        await CalendarRepository(db).mark_reminders_sent([_uid()], sent_at=_now())
        db.execute.assert_awaited()

    @pytest.mark.asyncio
    async def test_create_event_reminders(self):
        reminder = SimpleNamespace(id=_uid())
        db = _db()
        await CalendarRepository(db).create_event_reminders([reminder])
        db.add.assert_called_once_with(reminder)

    @pytest.mark.asyncio
    async def test_delete_unsent_reminders_for_event(self):
        reminder = SimpleNamespace(id=_uid())
        db = _db(_FR(many=[reminder]))
        await CalendarRepository(db).delete_unsent_reminders_for_event(_uid())
        db.delete.assert_awaited_once_with(reminder)
