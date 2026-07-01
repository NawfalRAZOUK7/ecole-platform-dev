"""Tests for ReportsRepository._build_export_query and AnalyticsRepository methods."""

from __future__ import annotations

import uuid
from datetime import datetime, date, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.repositories.reports import ReportsRepository, AnalyticsRepository


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


class TestReportsExportEntityGrades:
    """Tests covering _build_export_query for 'grades' entity (lines 816-851)."""

    @pytest.mark.asyncio
    async def test_count_export_rows_grades(self):
        db = _db(_FR(v=25))
        result = await ReportsRepository(db).count_export_rows(
            school_id=_uid(), entity="grades", filters={}
        )
        assert result == 25

    @pytest.mark.asyncio
    async def test_count_export_rows_grades_with_student_filter(self):
        db = _db(_FR(v=10))
        result = await ReportsRepository(db).count_export_rows(
            school_id=_uid(),
            entity="grades",
            filters={"student_id": str(_uid()), "class_id": str(_uid())},
        )
        assert result == 10

    @pytest.mark.asyncio
    async def test_count_export_rows_grades_with_date_filters(self):
        db = _db(_FR(v=5))
        result = await ReportsRepository(db).count_export_rows(
            school_id=_uid(),
            entity="grades",
            filters={"from_date": "2024-01-01", "to_date": "2024-12-31"},
        )
        assert result == 5

    @pytest.mark.asyncio
    async def test_fetch_export_rows_grades(self):
        row = SimpleNamespace(
            _mapping={
                "student_id": str(_uid()),
                "subject": "Math",
                "score": 85.0,
            }
        )
        db = _db(_FR(many=[row]))
        result = await ReportsRepository(db).fetch_export_rows(
            school_id=_uid(), entity="grades", filters={}, offset=0, limit=100
        )
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_fetch_export_rows_grades_with_filters(self):
        uid = _uid()
        row = SimpleNamespace(_mapping={"student_id": str(uid), "score": 90.0})
        db = _db(_FR(many=[row]))
        result = await ReportsRepository(db).fetch_export_rows(
            school_id=_uid(),
            entity="grades",
            filters={
                "student_id": str(uid),
                "class_id": str(_uid()),
                "from_date": "2024-01-01",
                "to_date": "2024-12-31",
            },
            offset=0,
            limit=50,
        )
        assert len(result) == 1


class TestReportsExportEntityAttendance:
    """Tests covering _build_export_query for 'attendance' entity (lines 853-904)."""

    @pytest.mark.asyncio
    async def test_count_export_rows_attendance(self):
        db = _db(_FR(v=40))
        result = await ReportsRepository(db).count_export_rows(
            school_id=_uid(), entity="attendance", filters={}
        )
        assert result == 40

    @pytest.mark.asyncio
    async def test_count_export_rows_attendance_no_rows(self):
        db = _db(_FR(v=None))
        result = await ReportsRepository(db).count_export_rows(
            school_id=_uid(), entity="attendance", filters={}
        )
        assert result == 0

    @pytest.mark.asyncio
    async def test_count_export_rows_attendance_with_filters(self):
        db = _db(_FR(v=12))
        result = await ReportsRepository(db).count_export_rows(
            school_id=_uid(),
            entity="attendance",
            filters={
                "class_id": str(_uid()),
                "student_id": str(_uid()),
                "status": "absent",
                "from_date": "2024-01-01",
                "to_date": "2024-06-30",
            },
        )
        assert result == 12

    @pytest.mark.asyncio
    async def test_fetch_export_rows_attendance(self):
        row = SimpleNamespace(
            _mapping={
                "student_id": str(_uid()),
                "status": "present",
                "session_date": "2024-03-01",
            }
        )
        db = _db(_FR(many=[row]))
        result = await ReportsRepository(db).fetch_export_rows(
            school_id=_uid(), entity="attendance", filters={}, offset=0, limit=100
        )
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_fetch_export_rows_attendance_all_filters(self):
        row = SimpleNamespace(_mapping={"student_id": str(_uid()), "status": "absent"})
        db = _db(_FR(many=[row]))
        result = await ReportsRepository(db).fetch_export_rows(
            school_id=_uid(),
            entity="attendance",
            filters={
                "class_id": str(_uid()),
                "student_id": str(_uid()),
                "status": "absent",
                "from_date": _d().isoformat(),
                "to_date": _d().isoformat(),
            },
            offset=0,
            limit=50,
        )
        assert len(result) == 1


class TestReportsExportEntityInvoices:
    """Tests covering _build_export_query for 'invoices' entity (lines 906-935)."""

    @pytest.mark.asyncio
    async def test_count_export_rows_invoices(self):
        db = _db(_FR(v=15))
        result = await ReportsRepository(db).count_export_rows(
            school_id=_uid(), entity="invoices", filters={}
        )
        assert result == 15

    @pytest.mark.asyncio
    async def test_count_export_rows_invoices_with_parent_status(self):
        db = _db(_FR(v=8))
        result = await ReportsRepository(db).count_export_rows(
            school_id=_uid(),
            entity="invoices",
            filters={
                "parent_id": str(_uid()),
                "status": "paid",
                "from_date": "2024-01-01",
                "to_date": "2024-12-31",
            },
        )
        assert result == 8

    @pytest.mark.asyncio
    async def test_fetch_export_rows_invoices(self):
        row = SimpleNamespace(
            _mapping={
                "invoice_id": str(_uid()),
                "status": "paid",
                "total_amount": 100.0,
            }
        )
        db = _db(_FR(many=[row]))
        result = await ReportsRepository(db).fetch_export_rows(
            school_id=_uid(), entity="invoices", filters={}, offset=0, limit=100
        )
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_fetch_export_rows_invoices_with_filters(self):
        row = SimpleNamespace(_mapping={"invoice_id": str(_uid()), "status": "unpaid"})
        db = _db(_FR(many=[row]))
        result = await ReportsRepository(db).fetch_export_rows(
            school_id=_uid(),
            entity="invoices",
            filters={
                "parent_id": str(_uid()),
                "status": "unpaid",
                "from_date": _d().isoformat(),
                "to_date": _d().isoformat(),
            },
            offset=0,
            limit=50,
        )
        assert len(result) == 1


class TestReportsExportEntityPayments:
    """Tests covering _build_export_query for 'payments' entity (lines 937-976)."""

    @pytest.mark.asyncio
    async def test_count_export_rows_payments(self):
        db = _db(_FR(v=20))
        result = await ReportsRepository(db).count_export_rows(
            school_id=_uid(), entity="payments", filters={}
        )
        assert result == 20

    @pytest.mark.asyncio
    async def test_count_export_rows_payments_with_filters(self):
        db = _db(_FR(v=7))
        result = await ReportsRepository(db).count_export_rows(
            school_id=_uid(),
            entity="payments",
            filters={
                "parent_id": str(_uid()),
                "status": "succeeded",
                "from_date": "2024-01-01",
                "to_date": "2024-12-31",
            },
        )
        assert result == 7

    @pytest.mark.asyncio
    async def test_fetch_export_rows_payments(self):
        row = SimpleNamespace(
            _mapping={
                "payment_attempt_id": str(_uid()),
                "status": "succeeded",
                "invoice_amount": 200.0,
            }
        )
        db = _db(_FR(many=[row]))
        result = await ReportsRepository(db).fetch_export_rows(
            school_id=_uid(), entity="payments", filters={}, offset=0, limit=100
        )
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_fetch_export_rows_payments_with_filters(self):
        row = SimpleNamespace(_mapping={"payment_attempt_id": str(_uid())})
        db = _db(_FR(many=[row]))
        result = await ReportsRepository(db).fetch_export_rows(
            school_id=_uid(),
            entity="payments",
            filters={
                "parent_id": str(_uid()),
                "status": "failed",
                "from_date": _d().isoformat(),
                "to_date": _d().isoformat(),
            },
            offset=0,
            limit=50,
        )
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_build_export_query_unsupported_entity(self):
        db = _db(_FR(v=0))
        with pytest.raises(ValueError, match="Unsupported export entity"):
            await ReportsRepository(db).count_export_rows(
                school_id=_uid(), entity="unknown_entity", filters={}
            )


class TestReportsExportStudentsFilters:
    """Cover branches in 'students' export entity (lines 757-814)."""

    @pytest.mark.asyncio
    async def test_count_export_rows_students_no_filters(self):
        db = _db(_FR(v=30))
        result = await ReportsRepository(db).count_export_rows(
            school_id=_uid(), entity="students", filters={}
        )
        assert result == 30

    @pytest.mark.asyncio
    async def test_count_export_rows_students_with_class_period(self):
        db = _db(_FR(v=15))
        result = await ReportsRepository(db).count_export_rows(
            school_id=_uid(),
            entity="students",
            filters={"class_id": str(_uid()), "period_id": str(_uid())},
        )
        assert result == 15

    @pytest.mark.asyncio
    async def test_count_export_rows_students_with_student_id(self):
        db = _db(_FR(v=1))
        result = await ReportsRepository(db).count_export_rows(
            school_id=_uid(),
            entity="students",
            filters={"student_id": str(_uid())},
        )
        assert result == 1

    @pytest.mark.asyncio
    async def test_fetch_export_rows_students_with_class_period(self):
        row = SimpleNamespace(
            _mapping={
                "student_id": str(_uid()),
                "student_name": "Ahmed",
                "class_code": "CP-A",
            }
        )
        db = _db(_FR(many=[row]))
        result = await ReportsRepository(db).fetch_export_rows(
            school_id=_uid(),
            entity="students",
            filters={"class_id": str(_uid()), "period_id": str(_uid())},
            offset=0,
            limit=100,
        )
        assert len(result) == 1


class TestAnalyticsRepositoryReports:
    """Tests for AnalyticsRepository methods in reports.py (lines 991-1126)."""

    @pytest.mark.asyncio
    async def test_count_active_users(self):
        db = _db(_FR(v=10))
        result = await AnalyticsRepository(db).count_active_users(
            school_id=_uid(), from_dt=_now(), to_dt=_now()
        )
        assert result == 10

    @pytest.mark.asyncio
    async def test_count_active_users_zero(self):
        db = _db(_FR(v=None))
        result = await AnalyticsRepository(db).count_active_users(
            school_id=_uid(), from_dt=_now(), to_dt=_now()
        )
        assert result == 0

    @pytest.mark.asyncio
    async def test_count_users(self):
        db = _db(_FR(v=50))
        result = await AnalyticsRepository(db).count_users(school_id=_uid())
        assert result == 50

    @pytest.mark.asyncio
    async def test_count_users_zero(self):
        db = _db(_FR(v=None))
        result = await AnalyticsRepository(db).count_users(school_id=_uid())
        assert result == 0

    @pytest.mark.asyncio
    async def test_attendance_summary_no_class(self):
        db = _db(_FR(v=(10, 7)))
        result = await AnalyticsRepository(db).attendance_summary(
            school_id=_uid(), from_date=_d(), to_date=_d()
        )
        assert result == (10, 7)

    @pytest.mark.asyncio
    async def test_attendance_summary_with_class(self):
        db = _db(_FR(v=(5, 4)))
        result = await AnalyticsRepository(db).attendance_summary(
            school_id=_uid(), from_date=_d(), to_date=_d(), class_id=_uid()
        )
        assert result == (5, 4)

    @pytest.mark.asyncio
    async def test_average_grade_no_filters(self):
        db = _db(_FR(v=78.5))
        result = await AnalyticsRepository(db).average_grade(
            school_id=_uid(), from_dt=_now(), to_dt=_now()
        )
        assert result == 78.5

    @pytest.mark.asyncio
    async def test_average_grade_with_class_and_subject(self):
        db = _db(_FR(v=90.0))
        result = await AnalyticsRepository(db).average_grade(
            school_id=_uid(),
            from_dt=_now(),
            to_dt=_now(),
            class_id=_uid(),
            subject="Math",
        )
        assert result == 90.0

    @pytest.mark.asyncio
    async def test_average_grade_none_result(self):
        db = _db(_FR(v=None))
        result = await AnalyticsRepository(db).average_grade(
            school_id=_uid(), from_dt=_now(), to_dt=_now()
        )
        assert result == 0.0

    @pytest.mark.asyncio
    async def test_billing_summary(self):
        db = _db(
            side_effects=[
                _FR(v=1000.0),
                _FR(v=600.0),
                _FR(v=400.0),
            ]
        )
        invoiced, paid, outstanding = await AnalyticsRepository(db).billing_summary(
            school_id=_uid(), from_date=_d(), to_date=_d()
        )
        assert invoiced == 1000.0
        assert paid == 600.0
        assert outstanding == 400.0

    @pytest.mark.asyncio
    async def test_billing_summary_nulls(self):
        db = _db(
            side_effects=[
                _FR(v=None),
                _FR(v=None),
                _FR(v=None),
            ]
        )
        invoiced, paid, outstanding = await AnalyticsRepository(db).billing_summary(
            school_id=_uid(), from_date=_d(), to_date=_d()
        )
        assert invoiced == 0.0
        assert paid == 0.0
        assert outstanding == 0.0

    @pytest.mark.asyncio
    async def test_engagement_summary(self):
        # count_users (scalar_one) → count_active_users (scalar_one) → engaged (scalar_one)
        db = _db(
            side_effects=[
                _FR(v=100),  # count_users
                _FR(v=60),  # count_active_users
                _FR(v=40),  # engaged
            ]
        )
        registered, active, engaged = await AnalyticsRepository(db).engagement_summary(
            school_id=_uid(), from_dt=_now(), to_dt=_now()
        )
        assert registered == 100
        assert active == 60
        assert engaged == 40
