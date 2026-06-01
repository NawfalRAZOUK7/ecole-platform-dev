"""Extended coverage tests for reports_analytics.py."""
from __future__ import annotations

import uuid
from datetime import datetime, date, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.repositories.reports_analytics import AnalyticsRepository


def _uid():
    return uuid.uuid4()


def _now():
    return datetime.now(timezone.utc)


def _d():
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


class TestAnalyticsRepositoryExtended:
    """Cover missing lines in reports_analytics.py."""

    @pytest.mark.asyncio
    async def test_list_attendance_series_with_class_and_program(self):
        """Cover class_id and program_id filters in list_attendance_series (lines 157-172)."""
        row = SimpleNamespace(
            bucket=_d(), total=10, present=8, absent=1, excused=1
        )
        db = _db(_FR(many=[row]))
        result = await AnalyticsRepository(db).list_attendance_series(
            school_id=_uid(),
            from_date=_d(),
            to_date=_d(),
            class_id=_uid(),
            bucket="week",
            program_id=_uid(),
        )
        assert len(result) == 1
        assert result[0]["total"] == 10

    @pytest.mark.asyncio
    async def test_list_attendance_series_no_class_no_program(self):
        """Cover basic list_attendance_series (lines 130-183)."""
        db = _db(_FR(many=[]))
        result = await AnalyticsRepository(db).list_attendance_series(
            school_id=_uid(),
            from_date=_d(),
            to_date=_d(),
            class_id=None,
            bucket="day",
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_average_grade_with_class_and_subject(self):
        """Cover average_grade with class_id and subject (lines 206-209)."""
        db = _db(_FR(v=88.5))
        result = await AnalyticsRepository(db).average_grade(
            school_id=_uid(),
            from_dt=_now(),
            to_dt=_now(),
            class_id=_uid(),
            subject="Math",
        )
        assert result == 88.5

    @pytest.mark.asyncio
    async def test_average_grade_no_filters(self):
        """Cover average_grade without optional filters."""
        db = _db(_FR(v=None))
        result = await AnalyticsRepository(db).average_grade(
            school_id=_uid(), from_dt=_now(), to_dt=_now()
        )
        assert result == 0.0

    @pytest.mark.asyncio
    async def test_list_grade_scores_with_subject_and_program(self):
        """Cover list_grade_scores with subject and program_id (lines 234-239)."""
        db = _db(_FR(many=[75.0, 85.0, 90.0]))
        result = await AnalyticsRepository(db).list_grade_scores(
            school_id=_uid(),
            from_dt=_now(),
            to_dt=_now(),
            subject="Math",
            program_id=_uid(),
        )
        assert result == [75.0, 85.0, 90.0]

    @pytest.mark.asyncio
    async def test_list_grade_scores_no_filters(self):
        """Cover list_grade_scores without filters."""
        db = _db(_FR(many=[]))
        result = await AnalyticsRepository(db).list_grade_scores(
            school_id=_uid(), from_dt=_now(), to_dt=_now(), subject=None
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_list_grade_scores_filters_none_values(self):
        """Cover None-filtering in list grade scores."""
        db = _db(_FR(many=[None, 85.0]))
        result = await AnalyticsRepository(db).list_grade_scores(
            school_id=_uid(), from_dt=_now(), to_dt=_now(), subject=None
        )
        assert result == [85.0]

    @pytest.mark.asyncio
    async def test_count_distinct_audit_users_with_filters(self):
        """Cover action_types and outcome filters (lines 334-337)."""
        db = _db(_FR(v=5))
        result = await AnalyticsRepository(db).count_distinct_audit_users(
            school_id=_uid(),
            from_dt=_now(),
            to_dt=_now(),
            action_types=["login", "logout"],
            outcome="success",
        )
        assert result == 5

    @pytest.mark.asyncio
    async def test_count_distinct_audit_users_no_filters(self):
        """Cover no-filter path."""
        db = _db(_FR(v=0))
        result = await AnalyticsRepository(db).count_distinct_audit_users(
            school_id=_uid(), from_dt=_now(), to_dt=_now()
        )
        assert result == 0

    @pytest.mark.asyncio
    async def test_list_engaged_user_series_with_outcome(self):
        """Cover outcome filter in list_engaged_user_series (line 364)."""
        row = SimpleNamespace(bucket=_d(), engaged_users=3)
        db = _db(_FR(many=[row]))
        result = await AnalyticsRepository(db).list_engaged_user_series(
            school_id=_uid(),
            from_dt=_now(),
            to_dt=_now(),
            bucket="day",
            outcome="success",
        )
        assert len(result) == 1
        assert result[0]["engaged_users"] == 3

    @pytest.mark.asyncio
    async def test_list_engaged_user_series_no_outcome(self):
        """Cover no-outcome path."""
        db = _db(_FR(many=[]))
        result = await AnalyticsRepository(db).list_engaged_user_series(
            school_id=_uid(),
            from_dt=_now(),
            to_dt=_now(),
            bucket="month",
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_count_audit_events_with_filters(self):
        """Cover action_types and outcomes filters (line 389)."""
        db = _db(_FR(v=10))
        result = await AnalyticsRepository(db).count_audit_events(
            school_id=_uid(),
            from_dt=_now(),
            action_types=["login"],
            outcomes=["success", "failure"],
        )
        assert result == 10

    @pytest.mark.asyncio
    async def test_count_audit_events_no_filters(self):
        db = _db(_FR(v=0))
        result = await AnalyticsRepository(db).count_audit_events(
            school_id=_uid(), from_dt=_now()
        )
        assert result == 0

    @pytest.mark.asyncio
    async def test_engagement_summary(self):
        """Cover engagement_summary (calls count_users + count_active_users + count_distinct_audit_users)."""
        db = _db(
            side_effects=[
                _FR(v=200),  # count_users
                _FR(v=100),  # count_active_users
                _FR(v=80),   # count_distinct_audit_users
            ]
        )
        registered, active, engaged = await AnalyticsRepository(db).engagement_summary(
            school_id=_uid(), from_dt=_now(), to_dt=_now()
        )
        assert registered == 200
        assert active == 100
        assert engaged == 80
