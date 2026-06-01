"""Supplementary coverage tests for reports.py and reports_analytics.py
with correct method signatures.
"""
from __future__ import annotations

import uuid
from datetime import datetime, date, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.repositories.reports import ReportsRepository
from app.repositories.reports_analytics import AnalyticsRepository


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

    def one(self):
        # For methods that call result.one() to unpack a single-row aggregate
        if self._v is not None:
            return self._v
        return (0, 0)  # default tuple for aggregate queries

    def one_or_none(self):
        return self._v

    def mappings(self):
        return SimpleNamespace(all=lambda: self._many)

    def __iter__(self):
        return iter(self._many)


def _db(result=None, *, side_effects=None):
    r = result if result is not None else _FR()
    db = SimpleNamespace(
        execute=AsyncMock(return_value=r),
        add=Mock(),
        flush=AsyncMock(),
        commit=AsyncMock(),
        merge=AsyncMock(),
        delete=AsyncMock(),
    )
    if side_effects:
        db.execute.side_effect = side_effects
    return db


# ===========================================================================
# ReportsRepository — correct method signatures
# ===========================================================================

class TestReportsRepositoryCorrect:
    @pytest.mark.asyncio
    async def test_create_report_job(self):
        job = SimpleNamespace(id=_uid())
        db = _db()
        result = await ReportsRepository(db).create_report_job(job)
        db.add.assert_called_once_with(job)

    @pytest.mark.asyncio
    async def test_save_report_job(self):
        job = SimpleNamespace(id=_uid())
        db = _db()
        result = await ReportsRepository(db).save_report_job(job)
        assert result is job

    @pytest.mark.asyncio
    async def test_get_report_job(self):
        obj = object()
        db = _db(_FR(v=obj))
        assert await ReportsRepository(db).get_report_job(_uid()) is obj

    @pytest.mark.asyncio
    async def test_find_cached_report(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await ReportsRepository(db).find_cached_report(
            school_id=_uid(),
            requester_id=_uid(),
            report_type="grade_summary",
            parameters_hash="hash123",
            since=_now(),
            now=_now(),
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_report_jobs_minimal(self):
        items = []
        db = _db(_FR(many=items))
        result, cursor, has_more = await ReportsRepository(db).list_report_jobs(
            school_id=_uid(),
            requester_id=_uid(),
            requester_role="ADM",
            report_type=None,
            period_id=None,
            status=None,
            cursor=None,
            limit=10,
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_report_jobs_non_admin(self):
        items = []
        db = _db(_FR(many=items))
        result, cursor, has_more = await ReportsRepository(db).list_report_jobs(
            school_id=_uid(),
            requester_id=_uid(),
            requester_role="TCH",
            report_type="grade",
            period_id=_uid(),
            status="completed",
            cursor=None,
            limit=10,
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_report_jobs_with_cursor(self):
        now = _now()
        items = [SimpleNamespace(id=_uid(), created_at=now) for _ in range(6)]
        db = _db(_FR(many=items))
        with patch("app.repositories.reports.decode_cursor", return_value=(_uid(), now.isoformat())):
            result, cursor, has_more = await ReportsRepository(db).list_report_jobs(
                school_id=_uid(),
                requester_id=_uid(),
                requester_role="ADM",
                report_type=None,
                period_id=None,
                status=None,
                cursor="cur",
                limit=5,
            )
        assert has_more is True

    @pytest.mark.asyncio
    async def test_list_expired_report_jobs(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ReportsRepository(db).list_expired_report_jobs(now=_now())
        assert result == items

    @pytest.mark.asyncio
    async def test_create_export_log(self):
        export = SimpleNamespace(id=_uid())
        db = _db()
        result = await ReportsRepository(db).create_export_log(export)
        db.add.assert_called_once_with(export)

    @pytest.mark.asyncio
    async def test_get_user_in_school(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await ReportsRepository(db).get_user_in_school(
            user_id=_uid(), school_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_period_in_school(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await ReportsRepository(db).get_period_in_school(
            period_id=_uid(), school_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_class_in_school(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await ReportsRepository(db).get_class_in_school(
            class_id=_uid(), school_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_class_academic_year_not_found(self):
        db = _db(_FR(v=None))
        result = await ReportsRepository(db).get_class_academic_year(
            class_id=_uid(), school_id=_uid()
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_list_parent_child_ids(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await ReportsRepository(db).list_parent_child_ids(
            parent_id=_uid(), school_id=_uid()
        )
        assert isinstance(result, set)

    @pytest.mark.asyncio
    async def test_list_periods(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ReportsRepository(db).list_periods(school_id=_uid())
        assert result == items

    @pytest.mark.asyncio
    async def test_list_classes(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ReportsRepository(db).list_classes(school_id=_uid())
        assert result == items

    @pytest.mark.asyncio
    async def test_list_classes_for_teacher(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ReportsRepository(db).list_classes_for_teacher(
            teacher_id=_uid(), school_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_students_for_class(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ReportsRepository(db).list_students_for_class(
            class_id=_uid(), school_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_users_by_role(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ReportsRepository(db).list_users_by_role(
            school_id=_uid(), role_code="TCH"
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_children(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ReportsRepository(db).list_children(
            parent_id=_uid(), school_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_get_student_class_context_no_period(self):
        db = _db(_FR(v=None))
        result = await ReportsRepository(db).get_student_class_context(
            student_id=_uid(), school_id=_uid()
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_get_student_class_context_with_period(self):
        # Returns None when nothing found (multi-join query)
        db = _db(_FR(v=None))
        result = await ReportsRepository(db).get_student_class_context(
            student_id=_uid(), school_id=_uid(), period_id=_uid()
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_list_teacher_class_ids(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await ReportsRepository(db).list_teacher_class_ids(
            teacher_id=_uid(), school_id=_uid()
        )
        assert isinstance(result, set)

    @pytest.mark.asyncio
    async def test_list_class_student_ids_no_period(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await ReportsRepository(db).list_class_student_ids(
            class_id=_uid(), school_id=_uid()
        )
        assert result == ids

    @pytest.mark.asyncio
    async def test_list_class_student_ids_with_period(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await ReportsRepository(db).list_class_student_ids(
            class_id=_uid(), school_id=_uid(), period_id=_uid()
        )
        assert result == ids

    @pytest.mark.asyncio
    async def test_list_user_names_by_ids_empty(self):
        db = _db()
        result = await ReportsRepository(db).list_user_names_by_ids([])
        assert result == {}

    @pytest.mark.asyncio
    async def test_list_user_names_by_ids_nonempty(self):
        uid = _uid()
        # Result iterates over (id, full_name) pairs
        row = SimpleNamespace(id=uid, full_name="Ahmed Benali")
        db = _db(_FR(many=[row]))
        result = await ReportsRepository(db).list_user_names_by_ids([uid])
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_list_student_report_grade_rows(self):
        # Uses list(result) which iterates the result object
        db = _db(_FR(many=[]))
        result = await ReportsRepository(db).list_student_report_grade_rows(
            school_id=_uid(), student_id=_uid(), from_dt=_now(), to_dt=_now()
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_get_student_report_attendance_summary(self):
        # result.one() returns a row with .total, .present etc attributes
        row = SimpleNamespace(total=5, present=3, absent=1, excused=1, late=0)
        db = _db(_FR(v=row))
        result = await ReportsRepository(db).get_student_report_attendance_summary(
            school_id=_uid(), student_id=_uid(), from_date=_today(), to_date=_today()
        )
        assert isinstance(result, tuple)

    @pytest.mark.asyncio
    async def test_list_class_subject_averages(self):
        # Uses list(result) pattern
        db = _db(_FR(many=[]))
        result = await ReportsRepository(db).list_class_subject_averages(
            school_id=_uid(), class_id=_uid(), from_dt=_now(), to_dt=_now()
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_list_class_student_grade_averages(self):
        db = _db(_FR(many=[]))
        result = await ReportsRepository(db).list_class_student_grade_averages(
            school_id=_uid(), class_id=_uid(), student_ids=[_uid()],
            from_dt=_now(), to_dt=_now()
        )
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_list_class_student_attendance_rates(self):
        db = _db(_FR(many=[]))
        result = await ReportsRepository(db).list_class_student_attendance_rates(
            school_id=_uid(), class_id=_uid(), student_ids=[_uid()],
            from_date=_today(), to_date=_today()
        )
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_list_attendance_summary_rows(self):
        db = _db(_FR(many=[]))
        result = await ReportsRepository(db).list_attendance_summary_rows(
            school_id=_uid(), class_id=_uid(), student_ids=[_uid()],
            from_date=_today(), to_date=_today()
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_list_attendance_trends(self):
        db = _db(_FR(many=[]))
        result = await ReportsRepository(db).list_attendance_trends(
            school_id=_uid(), class_id=_uid(), from_date=_today(), to_date=_today()
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_list_invoices_for_parent(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ReportsRepository(db).list_invoices_for_parent(
            school_id=_uid(), parent_id=_uid(), from_date=_today(), to_date=_today()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_payment_attempts_for_invoice_ids_empty(self):
        db = _db()
        result = await ReportsRepository(db).list_payment_attempts_for_invoice_ids([])
        assert result == []

    @pytest.mark.asyncio
    async def test_list_payment_attempts_for_invoice_ids_nonempty(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ReportsRepository(db).list_payment_attempts_for_invoice_ids([_uid()])
        assert result == items

    @pytest.mark.asyncio
    async def test_count_export_rows_students(self):
        db = _db(_FR(v=42))
        result = await ReportsRepository(db).count_export_rows(
            school_id=_uid(), entity="students", filters={}
        )
        assert result == 42

    @pytest.mark.asyncio
    async def test_fetch_export_rows_students(self):
        row = SimpleNamespace(_mapping={"id": str(_uid())})
        db = _db(_FR(many=[row]))
        result = await ReportsRepository(db).fetch_export_rows(
            school_id=_uid(), entity="students", filters={}, offset=0, limit=100
        )
        assert len(result) == 1


# ===========================================================================
# AnalyticsRepository — correct method signatures
# ===========================================================================

class TestAnalyticsRepositoryCorrect:
    @pytest.mark.asyncio
    async def test_count_active_users(self):
        db = _db(_FR(v=50))
        result = await AnalyticsRepository(db).count_active_users(
            school_id=_uid(), from_dt=_now(), to_dt=_now()
        )
        assert result == 50

    @pytest.mark.asyncio
    async def test_count_users(self):
        db = _db(_FR(v=100))
        result = await AnalyticsRepository(db).count_users(school_id=_uid())
        assert result == 100

    @pytest.mark.asyncio
    async def test_count_active_accounts(self):
        db = _db(_FR(v=80))
        result = await AnalyticsRepository(db).count_active_accounts(school_id=_uid())
        assert result == 80

    @pytest.mark.asyncio
    async def test_attendance_summary_no_class(self):
        # result.one() returns tuple(total, present)
        row = (5, 2)
        db = _db(_FR(v=row))
        result = await AnalyticsRepository(db).attendance_summary(
            school_id=_uid(), from_date=_today(), to_date=_today()
        )
        assert isinstance(result, tuple)

    @pytest.mark.asyncio
    async def test_attendance_summary_with_class(self):
        row = (3, 1)
        db = _db(_FR(v=row))
        result = await AnalyticsRepository(db).attendance_summary(
            school_id=_uid(), from_date=_today(), to_date=_today(), class_id=_uid()
        )
        assert isinstance(result, tuple)

    @pytest.mark.asyncio
    async def test_average_grade(self):
        db = _db(_FR(scalar=78.5))
        result = await AnalyticsRepository(db).average_grade(
            school_id=_uid(), from_dt=_now(), to_dt=_now()
        )
        assert isinstance(result, float)

    @pytest.mark.asyncio
    async def test_billing_summary(self):
        # 3 separate execute() calls: invoiced, paid, outstanding - all return scalar_one()
        db = _db(side_effects=[
            _FR(v=None),   # invoiced sum → None → 0.0
            _FR(v=None),   # paid sum
            _FR(v=None),   # outstanding
        ])
        result = await AnalyticsRepository(db).billing_summary(
            school_id=_uid(), from_date=_today(), to_date=_today()
        )
        assert isinstance(result, tuple)

    @pytest.mark.asyncio
    async def test_engagement_summary(self):
        # Multiple execute calls for engagement metrics
        db = _db(side_effects=[
            _FR(scalar=10),
            _FR(scalar=5),
            _FR(scalar=3),
        ])
        result = await AnalyticsRepository(db).engagement_summary(
            school_id=_uid(), from_dt=_now(), to_dt=_now()
        )
        assert isinstance(result, tuple)

    @pytest.mark.asyncio
    async def test_count_invitations_created(self):
        db = _db(_FR(scalar=7))
        result = await AnalyticsRepository(db).count_invitations_created(
            school_id=_uid(), from_dt=_now()
        )
        assert result == 7

    @pytest.mark.asyncio
    async def test_count_invitations_consumed(self):
        db = _db(_FR(scalar=5))
        result = await AnalyticsRepository(db).count_invitations_consumed(
            school_id=_uid(), from_dt=_now()
        )
        assert result == 5

    @pytest.mark.asyncio
    async def test_list_enrollment_by_class(self):
        db = _db(_FR(many=[]))
        result = await AnalyticsRepository(db).list_enrollment_by_class(school_id=_uid())
        assert result == []

    @pytest.mark.asyncio
    async def test_list_teacher_class_ids(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await AnalyticsRepository(db).list_teacher_class_ids(
            teacher_id=_uid(), school_id=_uid()
        )
        assert isinstance(result, set)

    @pytest.mark.asyncio
    async def test_list_active_user_series(self):
        # Returns list of dicts; result iterates rows
        db = _db(_FR(many=[]))
        result = await AnalyticsRepository(db).list_active_user_series(
            school_id=_uid(), from_dt=_now(), to_dt=_now(), bucket="day"
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_list_grade_scores(self):
        # result.scalars().all()
        db = _db(_FR(many=[75.0, 85.0]))
        result = await AnalyticsRepository(db).list_grade_scores(
            school_id=_uid(), from_dt=_now(), to_dt=_now(), subject="math"
        )
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_list_billing_series(self):
        # Iterates rows
        db = _db(_FR(many=[]))
        result = await AnalyticsRepository(db).list_billing_series(
            school_id=_uid(), from_date=_today(), to_date=_today(), bucket="month"
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_count_distinct_audit_users(self):
        db = _db(_FR(v=15))
        result = await AnalyticsRepository(db).count_distinct_audit_users(
            school_id=_uid(), from_dt=_now(), to_dt=_now()
        )
        assert result == 15

    @pytest.mark.asyncio
    async def test_list_engaged_user_series(self):
        db = _db(_FR(many=[]))
        result = await AnalyticsRepository(db).list_engaged_user_series(
            school_id=_uid(), from_dt=_now(), to_dt=_now(), bucket="day"
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_count_audit_events(self):
        db = _db(_FR(v=42))
        result = await AnalyticsRepository(db).count_audit_events(
            school_id=_uid(), from_dt=_now()
        )
        assert result == 42

    @pytest.mark.asyncio
    async def test_count_audit_events_with_action_types(self):
        db = _db(_FR(v=10))
        result = await AnalyticsRepository(db).count_audit_events(
            school_id=_uid(), from_dt=_now(), action_types=["login", "logout"]
        )
        assert result == 10
