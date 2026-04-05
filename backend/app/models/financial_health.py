"""Financial health metrics derived from billing and enrollment activity."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.core.database import Base, SchoolScopedMixin, TimestampMixin


def _short_id(value: object | None) -> str:
    return str(value)[:8] if value is not None else "None"


ALLOWED_CURRENCIES = {"MAD", "EUR", "USD"}


class RetentionMetric(TimestampMixin, SchoolScopedMixin, Base):
    """Year-over-year student retention metric for a school."""

    __tablename__ = "retention_metrics"

    academic_year_from: Mapped[str] = mapped_column(String(10), nullable=False)
    academic_year_to: Mapped[str] = mapped_column(String(10), nullable=False)
    total_students_start: Mapped[int] = mapped_column(Integer, nullable=False)
    total_students_end: Mapped[int] = mapped_column(Integer, nullable=False)
    retained: Mapped[int] = mapped_column(Integer, nullable=False)
    new_enrollments: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    withdrawals: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    retention_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        UniqueConstraint(
            "school_id",
            "academic_year_from",
            "academic_year_to",
            name="uq_retention_metrics_school_year_pair",
        ),
        CheckConstraint(
            "total_students_start >= 0",
            name="ck_retention_metrics_total_students_start",
        ),
        CheckConstraint(
            "total_students_end >= 0",
            name="ck_retention_metrics_total_students_end",
        ),
        CheckConstraint("retained >= 0", name="ck_retention_metrics_retained"),
        CheckConstraint(
            "new_enrollments >= 0",
            name="ck_retention_metrics_new_enrollments",
        ),
        CheckConstraint("withdrawals >= 0", name="ck_retention_metrics_withdrawals"),
        CheckConstraint(
            "retention_rate >= 0 AND retention_rate <= 100",
            name="ck_retention_metrics_retention_rate",
        ),
        Index(
            "idx_retention_metrics_school_computed_at",
            "school_id",
            "computed_at",
        ),
        Index(
            "idx_retention_metrics_school_year_pair",
            "school_id",
            "academic_year_from",
            "academic_year_to",
        ),
    )

    @validates("academic_year_from", "academic_year_to")
    def validate_academic_year(self, key: str, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError(f"{key} is required")
        return cleaned

    def __repr__(self) -> str:
        return (
            f"<RetentionMetric id={_short_id(self.id)} "
            f"school_id={_short_id(self.school_id)} rate={self.retention_rate}>"
        )


class CashflowForecast(TimestampMixin, SchoolScopedMixin, Base):
    """Projected monthly cashflow for a school."""

    __tablename__ = "cashflow_forecasts"

    forecast_month: Mapped[date] = mapped_column(Date, nullable=False)
    expected_income: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    expected_expenses: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    actual_income: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    actual_expenses: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="MAD")
    confidence_score: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        UniqueConstraint(
            "school_id",
            "forecast_month",
            name="uq_cashflow_forecasts_school_month",
        ),
        CheckConstraint(
            "expected_income >= 0",
            name="ck_cashflow_forecasts_expected_income",
        ),
        CheckConstraint(
            "expected_expenses >= 0",
            name="ck_cashflow_forecasts_expected_expenses",
        ),
        CheckConstraint(
            "actual_income IS NULL OR actual_income >= 0",
            name="ck_cashflow_forecasts_actual_income",
        ),
        CheckConstraint(
            "actual_expenses IS NULL OR actual_expenses >= 0",
            name="ck_cashflow_forecasts_actual_expenses",
        ),
        CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1",
            name="ck_cashflow_forecasts_confidence_score",
        ),
        Index(
            "idx_cashflow_forecasts_school_month",
            "school_id",
            "forecast_month",
        ),
        Index(
            "idx_cashflow_forecasts_school_computed_at",
            "school_id",
            "computed_at",
        ),
    )

    @validates("currency")
    def validate_currency(self, key: str, value: str) -> str:
        cleaned = value.strip().upper()
        if cleaned not in ALLOWED_CURRENCIES:
            allowed = ", ".join(sorted(ALLOWED_CURRENCIES))
            raise ValueError(f"Cashflow forecast currency must be one of: {allowed}")
        return cleaned

    @validates("forecast_month")
    def validate_forecast_month(self, key: str, value: date) -> date:
        if value.day != 1:
            raise ValueError("Forecast month must be the first day of the month")
        return value

    def __repr__(self) -> str:
        return (
            f"<CashflowForecast id={_short_id(self.id)} "
            f"month={self.forecast_month} confidence={self.confidence_score}>"
        )


class CostPerStudent(TimestampMixin, SchoolScopedMixin, Base):
    """Computed yearly cost and margin per student."""

    __tablename__ = "cost_per_student"

    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("academic_years.id", ondelete="CASCADE"),
        nullable=False,
    )
    total_operational_cost: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    total_students: Mapped[int] = mapped_column(Integer, nullable=False)
    cost_per_student: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    revenue_per_student: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    margin_per_student: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="MAD")
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    academic_year = relationship("AcademicYear", foreign_keys=[academic_year_id])

    __table_args__ = (
        UniqueConstraint(
            "school_id",
            "academic_year_id",
            name="uq_cost_per_student_school_year",
        ),
        CheckConstraint(
            "total_operational_cost >= 0",
            name="ck_cost_per_student_total_operational_cost",
        ),
        CheckConstraint(
            "total_students > 0",
            name="ck_cost_per_student_total_students",
        ),
        CheckConstraint(
            "cost_per_student >= 0",
            name="ck_cost_per_student_cost_per_student",
        ),
        CheckConstraint(
            "revenue_per_student >= 0",
            name="ck_cost_per_student_revenue_per_student",
        ),
        Index(
            "idx_cost_per_student_school_year",
            "school_id",
            "academic_year_id",
        ),
        Index(
            "idx_cost_per_student_school_computed_at",
            "school_id",
            "computed_at",
        ),
    )

    @validates("currency")
    def validate_currency(self, key: str, value: str) -> str:
        cleaned = value.strip().upper()
        if cleaned not in ALLOWED_CURRENCIES:
            allowed = ", ".join(sorted(ALLOWED_CURRENCIES))
            raise ValueError(f"Cost-per-student currency must be one of: {allowed}")
        return cleaned

    def __repr__(self) -> str:
        return (
            f"<CostPerStudent id={_short_id(self.id)} "
            f"year_id={_short_id(self.academic_year_id)} cost={self.cost_per_student}>"
        )


class FinancialSnapshot(TimestampMixin, SchoolScopedMixin, Base):
    """Point-in-time aggregate of receivables and collections."""

    __tablename__ = "financial_snapshots"

    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_receivable: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    total_collected: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    collection_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    overdue_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    overdue_count: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_payment_delay_days: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="MAD")
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        UniqueConstraint(
            "school_id",
            "snapshot_date",
            name="uq_financial_snapshots_school_date",
        ),
        CheckConstraint(
            "total_receivable >= 0",
            name="ck_financial_snapshots_total_receivable",
        ),
        CheckConstraint(
            "total_collected >= 0",
            name="ck_financial_snapshots_total_collected",
        ),
        CheckConstraint(
            "collection_rate >= 0 AND collection_rate <= 100",
            name="ck_financial_snapshots_collection_rate",
        ),
        CheckConstraint(
            "overdue_amount >= 0",
            name="ck_financial_snapshots_overdue_amount",
        ),
        CheckConstraint(
            "overdue_count >= 0",
            name="ck_financial_snapshots_overdue_count",
        ),
        CheckConstraint(
            "avg_payment_delay_days IS NULL OR avg_payment_delay_days >= 0",
            name="ck_financial_snapshots_avg_payment_delay_days",
        ),
        Index(
            "idx_financial_snapshots_school_date",
            "school_id",
            "snapshot_date",
        ),
        Index(
            "idx_financial_snapshots_school_computed_at",
            "school_id",
            "computed_at",
        ),
    )

    @validates("currency")
    def validate_currency(self, key: str, value: str) -> str:
        cleaned = value.strip().upper()
        if cleaned not in ALLOWED_CURRENCIES:
            allowed = ", ".join(sorted(ALLOWED_CURRENCIES))
            raise ValueError(f"Financial snapshot currency must be one of: {allowed}")
        return cleaned

    def __repr__(self) -> str:
        return (
            f"<FinancialSnapshot id={_short_id(self.id)} "
            f"date={self.snapshot_date} rate={self.collection_rate}>"
        )
