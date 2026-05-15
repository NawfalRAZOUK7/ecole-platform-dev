"""Repository helpers for financial health metrics and source aggregates."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, cast as type_cast

from sqlalchemy import Date, case, cast as sa_cast, distinct, func, select

from app.models.billing import (
    Invoice,
    InvoiceStatus,
    PaymentAttempt,
    PaymentAttemptStatus,
)
from app.models.budget import (
    BudgetAllocation,
    BudgetTransaction,
    BudgetTransactionType,
    MicroBudget,
)
from app.models.erp import AcademicYear, Enrollment, EnrollmentStatus, Period
from app.models.financial_health import (
    CashflowForecast,
    CostPerStudent,
    FinancialSnapshot,
    RetentionMetric,
)
from app.repositories.base import BaseRepository


def _as_float(value: object | None) -> float:
    if value is None:
        return 0.0
    return float(type_cast(Any, value))


class FinancialHealthRepository(BaseRepository):
    """Data access for financial metric snapshots and underlying aggregates."""

    async def get_academic_year(
        self,
        academic_year_id: uuid.UUID,
        *,
        school_id: uuid.UUID | None = None,
    ) -> AcademicYear | None:
        query = select(AcademicYear).where(AcademicYear.id == academic_year_id)
        if school_id is not None:
            query = query.where(AcademicYear.school_id == school_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_academic_year_by_label(
        self,
        *,
        school_id: uuid.UUID,
        label: str,
    ) -> AcademicYear | None:
        result = await self.db.execute(
            select(AcademicYear).where(
                AcademicYear.school_id == school_id,
                func.lower(AcademicYear.label) == label.strip().lower(),
            )
        )
        return result.scalar_one_or_none()

    async def list_active_student_ids_for_academic_year(
        self,
        *,
        school_id: uuid.UUID,
        academic_year_id: uuid.UUID,
    ) -> set[uuid.UUID]:
        result = await self.db.execute(
            select(distinct(Enrollment.student_id))
            .join(Period, Period.id == Enrollment.period_id)
            .where(
                Enrollment.school_id == school_id,
                Enrollment.status == EnrollmentStatus.ACTIVE.value,
                Period.academic_year_id == academic_year_id,
            )
        )
        return set(result.scalars().all())

    async def count_active_students_for_academic_year(
        self,
        *,
        school_id: uuid.UUID,
        academic_year_id: uuid.UUID,
    ) -> int:
        result = await self.db.execute(
            select(func.count(distinct(Enrollment.student_id)))
            .join(Period, Period.id == Enrollment.period_id)
            .where(
                Enrollment.school_id == school_id,
                Enrollment.status == EnrollmentStatus.ACTIVE.value,
                Period.academic_year_id == academic_year_id,
            )
        )
        return int(result.scalar() or 0)

    async def get_retention_metric(
        self,
        *,
        school_id: uuid.UUID,
        academic_year_from: str,
        academic_year_to: str,
    ) -> RetentionMetric | None:
        result = await self.db.execute(
            select(RetentionMetric).where(
                RetentionMetric.school_id == school_id,
                RetentionMetric.academic_year_from == academic_year_from,
                RetentionMetric.academic_year_to == academic_year_to,
            )
        )
        return result.scalar_one_or_none()

    async def list_retention_metrics(
        self,
        *,
        school_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> list[RetentionMetric]:
        result = await self.db.execute(
            select(RetentionMetric)
            .where(RetentionMetric.school_id == school_id)
            .order_by(
                RetentionMetric.academic_year_to.desc(),
                RetentionMetric.computed_at.desc(),
            )
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create_retention_metric(self, **kwargs: Any) -> RetentionMetric:
        metric = RetentionMetric(**kwargs)
        self.db.add(metric)
        await self.db.flush()
        return metric

    async def save_retention_metric(self, metric: RetentionMetric) -> RetentionMetric:
        self.db.add(metric)
        await self.db.flush()
        return metric

    async def get_cashflow_forecast(
        self,
        *,
        school_id: uuid.UUID,
        forecast_month: date,
    ) -> CashflowForecast | None:
        result = await self.db.execute(
            select(CashflowForecast).where(
                CashflowForecast.school_id == school_id,
                CashflowForecast.forecast_month == forecast_month,
            )
        )
        return result.scalar_one_or_none()

    async def list_cashflow_forecasts(
        self,
        *,
        school_id: uuid.UUID,
        start_month: date | None = None,
        end_month: date | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[CashflowForecast]:
        query = select(CashflowForecast).where(CashflowForecast.school_id == school_id)
        if start_month is not None:
            query = query.where(CashflowForecast.forecast_month >= start_month)
        if end_month is not None:
            query = query.where(CashflowForecast.forecast_month <= end_month)
        result = await self.db.execute(
            query.order_by(CashflowForecast.forecast_month.asc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create_cashflow_forecast(self, **kwargs: Any) -> CashflowForecast:
        forecast = CashflowForecast(**kwargs)
        self.db.add(forecast)
        await self.db.flush()
        return forecast

    async def save_cashflow_forecast(
        self,
        forecast: CashflowForecast,
    ) -> CashflowForecast:
        self.db.add(forecast)
        await self.db.flush()
        return forecast

    async def get_cost_per_student(
        self,
        *,
        school_id: uuid.UUID,
        academic_year_id: uuid.UUID,
    ) -> CostPerStudent | None:
        result = await self.db.execute(
            select(CostPerStudent).where(
                CostPerStudent.school_id == school_id,
                CostPerStudent.academic_year_id == academic_year_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_cost_per_student(self, **kwargs: Any) -> CostPerStudent:
        analysis = CostPerStudent(**kwargs)
        self.db.add(analysis)
        await self.db.flush()
        return analysis

    async def save_cost_per_student(self, analysis: CostPerStudent) -> CostPerStudent:
        self.db.add(analysis)
        await self.db.flush()
        return analysis

    async def get_financial_snapshot(
        self,
        *,
        school_id: uuid.UUID,
        snapshot_date: date,
    ) -> FinancialSnapshot | None:
        result = await self.db.execute(
            select(FinancialSnapshot).where(
                FinancialSnapshot.school_id == school_id,
                FinancialSnapshot.snapshot_date == snapshot_date,
            )
        )
        return result.scalar_one_or_none()

    async def list_financial_snapshots(
        self,
        *,
        school_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> list[FinancialSnapshot]:
        result = await self.db.execute(
            select(FinancialSnapshot)
            .where(FinancialSnapshot.school_id == school_id)
            .order_by(FinancialSnapshot.snapshot_date.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create_financial_snapshot(self, **kwargs: Any) -> FinancialSnapshot:
        snapshot = FinancialSnapshot(**kwargs)
        self.db.add(snapshot)
        await self.db.flush()
        return snapshot

    async def save_financial_snapshot(
        self,
        snapshot: FinancialSnapshot,
    ) -> FinancialSnapshot:
        self.db.add(snapshot)
        await self.db.flush()
        return snapshot

    async def aggregate_invoice_amounts_by_due_month(
        self,
        *,
        school_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> dict[date, float]:
        month_bucket = sa_cast(func.date_trunc("month", Invoice.due_date), Date)
        result = await self.db.execute(
            select(month_bucket, func.sum(Invoice.total_amount))
            .where(
                Invoice.school_id == school_id,
                Invoice.due_date >= start_date,
                Invoice.due_date <= end_date,
                Invoice.status != InvoiceStatus.CANCELED.value,
            )
            .group_by(month_bucket)
            .order_by(month_bucket)
        )
        return {row[0]: _as_float(row[1]) for row in result.all()}

    async def aggregate_paid_invoice_amounts_by_month(
        self,
        *,
        school_id: uuid.UUID,
        start_datetime: datetime,
        end_datetime: datetime,
    ) -> dict[date, float]:
        month_bucket = sa_cast(
            func.date_trunc("month", PaymentAttempt.finalized_at), Date
        )
        result = await self.db.execute(
            select(month_bucket, func.sum(Invoice.total_amount))
            .join(Invoice, Invoice.id == PaymentAttempt.invoice_id)
            .where(
                PaymentAttempt.school_id == school_id,
                PaymentAttempt.status == PaymentAttemptStatus.PAID.value,
                PaymentAttempt.finalized_at.is_not(None),
                PaymentAttempt.finalized_at >= start_datetime,
                PaymentAttempt.finalized_at <= end_datetime,
            )
            .group_by(month_bucket)
            .order_by(month_bucket)
        )
        return {row[0]: _as_float(row[1]) for row in result.all()}

    async def aggregate_expense_amounts_by_month(
        self,
        *,
        school_id: uuid.UUID,
        start_datetime: datetime,
        end_datetime: datetime,
    ) -> dict[date, float]:
        month_bucket = sa_cast(
            func.date_trunc("month", BudgetTransaction.recorded_at), Date
        )
        signed_amount = case(
            (
                BudgetTransaction.transaction_type
                == BudgetTransactionType.EXPENSE.value,
                BudgetTransaction.amount,
            ),
            (
                BudgetTransaction.transaction_type
                == BudgetTransactionType.REFUND.value,
                -BudgetTransaction.amount,
            ),
            (
                BudgetTransaction.transaction_type
                == BudgetTransactionType.ADJUSTMENT.value,
                BudgetTransaction.amount,
            ),
            else_=0,
        )
        result = await self.db.execute(
            select(month_bucket, func.sum(signed_amount))
            .join(
                BudgetAllocation, BudgetAllocation.id == BudgetTransaction.allocation_id
            )
            .join(MicroBudget, MicroBudget.id == BudgetAllocation.budget_id)
            .where(
                MicroBudget.school_id == school_id,
                BudgetTransaction.recorded_at >= start_datetime,
                BudgetTransaction.recorded_at <= end_datetime,
                BudgetTransaction.transaction_type.in_(
                    [
                        BudgetTransactionType.EXPENSE.value,
                        BudgetTransactionType.REFUND.value,
                        BudgetTransactionType.ADJUSTMENT.value,
                    ]
                ),
            )
            .group_by(month_bucket)
            .order_by(month_bucket)
        )
        return {row[0]: _as_float(row[1]) for row in result.all()}

    async def get_recent_collection_ratio(
        self,
        *,
        school_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> float:
        result = await self.db.execute(
            select(
                func.sum(Invoice.total_amount),
                func.sum(
                    case(
                        (
                            Invoice.status == InvoiceStatus.PAID.value,
                            Invoice.total_amount,
                        ),
                        else_=0,
                    )
                ),
            ).where(
                Invoice.school_id == school_id,
                Invoice.due_date >= start_date,
                Invoice.due_date <= end_date,
                Invoice.status != InvoiceStatus.CANCELED.value,
            )
        )
        total_scheduled, total_paid = result.one()
        scheduled = _as_float(total_scheduled)
        if scheduled <= 0:
            return 0.5
        return min(1.0, max(0.0, _as_float(total_paid) / scheduled))

    async def get_budget_total_for_academic_year(
        self,
        *,
        school_id: uuid.UUID,
        academic_year_id: uuid.UUID,
    ) -> float:
        result = await self.db.execute(
            select(func.sum(MicroBudget.total_amount)).where(
                MicroBudget.school_id == school_id,
                MicroBudget.academic_year_id == academic_year_id,
            )
        )
        return _as_float(result.scalar())

    async def get_expense_total_for_academic_year(
        self,
        *,
        school_id: uuid.UUID,
        academic_year_id: uuid.UUID,
    ) -> float:
        signed_amount = case(
            (
                BudgetTransaction.transaction_type
                == BudgetTransactionType.EXPENSE.value,
                BudgetTransaction.amount,
            ),
            (
                BudgetTransaction.transaction_type
                == BudgetTransactionType.REFUND.value,
                -BudgetTransaction.amount,
            ),
            (
                BudgetTransaction.transaction_type
                == BudgetTransactionType.ADJUSTMENT.value,
                BudgetTransaction.amount,
            ),
            else_=0,
        )
        result = await self.db.execute(
            select(func.sum(signed_amount))
            .join(
                BudgetAllocation, BudgetAllocation.id == BudgetTransaction.allocation_id
            )
            .join(MicroBudget, MicroBudget.id == BudgetAllocation.budget_id)
            .where(
                MicroBudget.school_id == school_id,
                MicroBudget.academic_year_id == academic_year_id,
                BudgetTransaction.transaction_type.in_(
                    [
                        BudgetTransactionType.EXPENSE.value,
                        BudgetTransactionType.REFUND.value,
                        BudgetTransactionType.ADJUSTMENT.value,
                    ]
                ),
            )
        )
        return _as_float(result.scalar())

    async def get_collected_revenue_for_academic_year(
        self,
        *,
        school_id: uuid.UUID,
        academic_year_id: uuid.UUID,
    ) -> float:
        result = await self.db.execute(
            select(func.sum(Invoice.total_amount))
            .join(Period, Period.id == Invoice.period_id)
            .where(
                Invoice.school_id == school_id,
                Period.academic_year_id == academic_year_id,
                Invoice.status == InvoiceStatus.PAID.value,
            )
        )
        return _as_float(result.scalar())

    async def get_total_receivable_as_of(
        self,
        *,
        school_id: uuid.UUID,
        snapshot_date: date,
    ) -> float:
        result = await self.db.execute(
            select(func.sum(Invoice.total_amount)).where(
                Invoice.school_id == school_id,
                Invoice.issued_date <= snapshot_date,
                Invoice.status.in_(
                    [InvoiceStatus.PENDING.value, InvoiceStatus.FAILED.value]
                ),
            )
        )
        return _as_float(result.scalar())

    async def get_total_collected_as_of(
        self,
        *,
        school_id: uuid.UUID,
        snapshot_date: date,
    ) -> float:
        result = await self.db.execute(
            select(func.sum(Invoice.total_amount))
            .join(PaymentAttempt, PaymentAttempt.invoice_id == Invoice.id)
            .where(
                Invoice.school_id == school_id,
                PaymentAttempt.status == PaymentAttemptStatus.PAID.value,
                PaymentAttempt.finalized_at.is_not(None),
                sa_cast(PaymentAttempt.finalized_at, Date) <= snapshot_date,
            )
        )
        return _as_float(result.scalar())

    async def get_overdue_totals_as_of(
        self,
        *,
        school_id: uuid.UUID,
        snapshot_date: date,
    ) -> tuple[float, int]:
        result = await self.db.execute(
            select(func.sum(Invoice.total_amount), func.count(Invoice.id)).where(
                Invoice.school_id == school_id,
                Invoice.status == InvoiceStatus.PENDING.value,
                Invoice.due_date < snapshot_date,
            )
        )
        overdue_amount, overdue_count = result.one()
        return _as_float(overdue_amount), int(overdue_count or 0)

    async def get_average_payment_delay_days_as_of(
        self,
        *,
        school_id: uuid.UUID,
        snapshot_date: date,
    ) -> float | None:
        delay_days = (
            func.extract(
                "epoch",
                PaymentAttempt.finalized_at - sa_cast(Invoice.due_date, Date),
            )
            / 86400.0
        )
        result = await self.db.execute(
            select(func.avg(delay_days))
            .join(Invoice, Invoice.id == PaymentAttempt.invoice_id)
            .where(
                PaymentAttempt.school_id == school_id,
                PaymentAttempt.status == PaymentAttemptStatus.PAID.value,
                PaymentAttempt.finalized_at.is_not(None),
                sa_cast(PaymentAttempt.finalized_at, Date) <= snapshot_date,
            )
        )
        value = result.scalar_one_or_none()
        return None if value is None else float(value)
