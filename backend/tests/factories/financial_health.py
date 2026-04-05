"""Factories for financial health models."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

import factory

from app.models.financial_health import CashflowForecast, CostPerStudent, FinancialSnapshot, RetentionMetric
from tests.factories.base import AsyncSQLAlchemyFactory
from tests.factories.erp import AcademicYearFactory
from tests.factories.school import SchoolFactory


def _utc_now() -> datetime:
    return datetime.now(UTC)


class RetentionMetricFactory(AsyncSQLAlchemyFactory):
    """Factory for retention metrics."""

    class Meta:
        model = RetentionMetric
        exclude = ("school",)

    id = factory.LazyFunction(uuid.uuid4)
    school = factory.SubFactory(SchoolFactory)
    school_id = factory.LazyAttribute(lambda o: o.school.id)
    academic_year_from = "2024-2025"
    academic_year_to = "2025-2026"
    total_students_start = 20
    total_students_end = 22
    retained = 18
    new_enrollments = 4
    withdrawals = 2
    retention_rate = Decimal("90.00")
    computed_at = factory.LazyFunction(_utc_now)


class CashflowForecastFactory(AsyncSQLAlchemyFactory):
    """Factory for monthly cashflow forecasts."""

    class Meta:
        model = CashflowForecast
        exclude = ("school",)

    id = factory.LazyFunction(uuid.uuid4)
    school = factory.SubFactory(SchoolFactory)
    school_id = factory.LazyAttribute(lambda o: o.school.id)
    forecast_month = date(2026, 4, 1)
    expected_income = Decimal("12000.00")
    expected_expenses = Decimal("8000.00")
    actual_income = Decimal("11500.00")
    actual_expenses = Decimal("7600.00")
    currency = "MAD"
    confidence_score = Decimal("0.850")
    computed_at = factory.LazyFunction(_utc_now)


class CostPerStudentFactory(AsyncSQLAlchemyFactory):
    """Factory for cost-per-student analyses."""

    class Meta:
        model = CostPerStudent
        exclude = ("school", "academic_year")

    id = factory.LazyFunction(uuid.uuid4)
    school = factory.SubFactory(SchoolFactory)
    academic_year = factory.SubFactory(
        AcademicYearFactory,
        school=factory.SelfAttribute("..school"),
    )
    school_id = factory.LazyAttribute(lambda o: o.school.id)
    academic_year_id = factory.LazyAttribute(lambda o: o.academic_year.id)
    total_operational_cost = Decimal("30000.00")
    total_students = 25
    cost_per_student = Decimal("1200.00")
    revenue_per_student = Decimal("1500.00")
    margin_per_student = Decimal("300.00")
    currency = "MAD"
    computed_at = factory.LazyFunction(_utc_now)


class FinancialSnapshotFactory(AsyncSQLAlchemyFactory):
    """Factory for financial snapshots."""

    class Meta:
        model = FinancialSnapshot
        exclude = ("school",)

    id = factory.LazyFunction(uuid.uuid4)
    school = factory.SubFactory(SchoolFactory)
    school_id = factory.LazyAttribute(lambda o: o.school.id)
    snapshot_date = date(2026, 4, 5)
    total_receivable = Decimal("6000.00")
    total_collected = Decimal("14000.00")
    collection_rate = Decimal("70.00")
    overdue_amount = Decimal("2500.00")
    overdue_count = 3
    avg_payment_delay_days = Decimal("4.50")
    currency = "MAD"
    computed_at = factory.LazyFunction(_utc_now)


__all__ = [
    "RetentionMetricFactory",
    "CashflowForecastFactory",
    "CostPerStudentFactory",
    "FinancialSnapshotFactory",
]
