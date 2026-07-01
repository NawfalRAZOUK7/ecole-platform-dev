"""Service layer for financial health metrics and dashboard aggregates."""

from __future__ import annotations

import csv
import io
import uuid
from datetime import UTC, date, datetime, time
from typing import Any, cast

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import AuthContext, verify_school_boundary
from app.core.exceptions import NotFoundError, ValidationError
from app.core.unit_of_work import UnitOfWork
from app.domain.events.financial_health import (
    CashflowForecastComputed,
    CostPerStudentComputed,
    FinancialSnapshotComputed,
    RetentionMetricComputed,
)
from app.models.erp import AcademicYear
from app.models.financial_health import (
    CashflowForecast,
    CostPerStudent,
    FinancialSnapshot,
    RetentionMetric,
)
from app.repositories.reports_financial_health import FinancialHealthRepository
from app.schemas.reports.financial_health import (
    CashflowForecastComputeRequest,
    CashflowForecastResponse,
    CostPerStudentComputeRequest,
    CostPerStudentResponse,
    FinancialSnapshotComputeRequest,
    FinancialSnapshotResponse,
    RetentionComputeRequest,
    RetentionMetricResponse,
)
from app.services.platform.audit import AuditService
from app.services.communication.event_dispatcher import EventDispatcher


def _iso(value: datetime | None) -> str | None:
    return value.astimezone(UTC).isoformat() if value is not None else None


def _as_float(value: object | None) -> float:
    if value is None:
        return 0.0
    return float(cast(Any, value))


def _percentage(numerator: float, denominator: float, *, empty: float = 0.0) -> float:
    if denominator <= 0:
        return empty
    return round((numerator / denominator) * 100, 2)


def _first_day_of_month(value: date) -> date:
    return value.replace(day=1)


def _add_months(value: date, months: int) -> date:
    total_month = (value.year * 12 + value.month - 1) + months
    year = total_month // 12
    month = total_month % 12 + 1
    return date(year, month, 1)


def _start_of_day(value: date) -> datetime:
    return datetime.combine(value, time.min, tzinfo=UTC)


def _end_of_day(value: date) -> datetime:
    return datetime.combine(value, time.max, tzinfo=UTC)


class FinancialHealthService:
    """Business logic for retention, cashflow, cost-per-student, and snapshots."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = FinancialHealthRepository(db)
        self.audit = AuditService(db)
        self._dispatcher = EventDispatcher(db)

    def _retention_to_response(self, metric: RetentionMetric) -> dict[str, Any]:
        return RetentionMetricResponse(
            id=str(metric.id),
            school_id=str(metric.school_id),
            academic_year_from=metric.academic_year_from,
            academic_year_to=metric.academic_year_to,
            total_students_start=metric.total_students_start,
            total_students_end=metric.total_students_end,
            retained=metric.retained,
            new_enrollments=metric.new_enrollments,
            withdrawals=metric.withdrawals,
            retention_rate=_as_float(metric.retention_rate),
            computed_at=_iso(metric.computed_at) or "",
            created_at=_iso(metric.created_at) or "",
            updated_at=_iso(metric.updated_at),
        ).model_dump(mode="json")

    def _cashflow_to_response(self, forecast: CashflowForecast) -> dict[str, Any]:
        return CashflowForecastResponse(
            id=str(forecast.id),
            school_id=str(forecast.school_id),
            forecast_month=forecast.forecast_month,
            expected_income=_as_float(forecast.expected_income),
            expected_expenses=_as_float(forecast.expected_expenses),
            actual_income=None
            if forecast.actual_income is None
            else _as_float(forecast.actual_income),
            actual_expenses=None
            if forecast.actual_expenses is None
            else _as_float(forecast.actual_expenses),
            currency=forecast.currency,
            confidence_score=round(_as_float(forecast.confidence_score), 3),
            computed_at=_iso(forecast.computed_at) or "",
            created_at=_iso(forecast.created_at) or "",
            updated_at=_iso(forecast.updated_at),
        ).model_dump(mode="json")

    def _cost_to_response(self, analysis: CostPerStudent) -> dict[str, Any]:
        return CostPerStudentResponse(
            id=str(analysis.id),
            school_id=str(analysis.school_id),
            academic_year_id=str(analysis.academic_year_id),
            total_operational_cost=_as_float(analysis.total_operational_cost),
            total_students=analysis.total_students,
            cost_per_student=_as_float(analysis.cost_per_student),
            revenue_per_student=_as_float(analysis.revenue_per_student),
            margin_per_student=_as_float(analysis.margin_per_student),
            currency=analysis.currency,
            computed_at=_iso(analysis.computed_at) or "",
            created_at=_iso(analysis.created_at) or "",
            updated_at=_iso(analysis.updated_at),
        ).model_dump(mode="json")

    def _snapshot_to_response(self, snapshot: FinancialSnapshot) -> dict[str, Any]:
        return FinancialSnapshotResponse(
            id=str(snapshot.id),
            school_id=str(snapshot.school_id),
            snapshot_date=snapshot.snapshot_date,
            total_receivable=_as_float(snapshot.total_receivable),
            total_collected=_as_float(snapshot.total_collected),
            collection_rate=_as_float(snapshot.collection_rate),
            overdue_amount=_as_float(snapshot.overdue_amount),
            overdue_count=snapshot.overdue_count,
            avg_payment_delay_days=None
            if snapshot.avg_payment_delay_days is None
            else _as_float(snapshot.avg_payment_delay_days),
            currency=snapshot.currency,
            computed_at=_iso(snapshot.computed_at) or "",
            created_at=_iso(snapshot.created_at) or "",
            updated_at=_iso(snapshot.updated_at),
        ).model_dump(mode="json")

    async def _get_academic_year_by_label_or_404(
        self,
        *,
        school_id: uuid.UUID,
        label: str,
    ) -> AcademicYear:
        academic_year = await self.repo.get_academic_year_by_label(
            school_id=school_id,
            label=label,
        )
        if academic_year is None:
            raise NotFoundError(
                "Academic year not found", error_code="ERR-FINHEALTH-404"
            )
        return academic_year

    async def _get_academic_year_or_404(
        self,
        *,
        academic_year_id: uuid.UUID,
        auth: AuthContext,
    ) -> AcademicYear:
        academic_year = await self.repo.get_academic_year(
            academic_year_id,
            school_id=auth.school_id,
        )
        if academic_year is None:
            raise NotFoundError(
                "Academic year not found", error_code="ERR-FINHEALTH-404"
            )
        verify_school_boundary(academic_year.school_id, auth)
        return academic_year

    async def list_retention_metrics(
        self,
        *,
        auth: AuthContext,
        skip: int = 0,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        metrics = await self.repo.list_retention_metrics(
            school_id=auth.school_id,
            skip=skip,
            limit=limit,
        )
        return [self._retention_to_response(metric) for metric in metrics]

    async def compute_retention(
        self,
        *,
        body: RetentionComputeRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        from_year = await self._get_academic_year_by_label_or_404(
            school_id=auth.school_id,
            label=body.academic_year_from,
        )
        to_year = await self._get_academic_year_by_label_or_404(
            school_id=auth.school_id,
            label=body.academic_year_to,
        )

        start_students = await self.repo.list_active_student_ids_for_academic_year(
            school_id=auth.school_id,
            academic_year_id=from_year.id,
        )
        end_students = await self.repo.list_active_student_ids_for_academic_year(
            school_id=auth.school_id,
            academic_year_id=to_year.id,
        )

        retained = len(start_students & end_students)
        total_start = len(start_students)
        total_end = len(end_students)
        new_enrollments = len(end_students - start_students)
        withdrawals = len(start_students - end_students)
        retention_rate = (
            100.0
            if total_start == 0 and total_end == 0
            else _percentage(retained, total_start)
        )

        async with UnitOfWork(self.db) as uow:
            repo = FinancialHealthRepository(uow.session)
            audit = AuditService(uow.session)
            dispatcher = EventDispatcher(uow.session)
            metric = await repo.get_retention_metric(
                school_id=auth.school_id,
                academic_year_from=body.academic_year_from,
                academic_year_to=body.academic_year_to,
            )
            if metric is None:
                metric = await repo.create_retention_metric(
                    school_id=auth.school_id,
                    academic_year_from=body.academic_year_from,
                    academic_year_to=body.academic_year_to,
                    total_students_start=total_start,
                    total_students_end=total_end,
                    retained=retained,
                    new_enrollments=new_enrollments,
                    withdrawals=withdrawals,
                    retention_rate=retention_rate,
                    computed_at=datetime.now(UTC),
                )
            else:
                metric.total_students_start = total_start
                metric.total_students_end = total_end
                metric.retained = retained
                metric.new_enrollments = new_enrollments
                metric.withdrawals = withdrawals
                metric.retention_rate = retention_rate
                metric.computed_at = datetime.now(UTC)
                metric = await repo.save_retention_metric(metric)

            response = self._retention_to_response(metric)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="financial_health.retention.compute",
                outcome="success",
                target_type="retention_metric",
                target_id=metric.id,
                entity_after=response,
                ip_address=ip_address,
            )
            await dispatcher.dispatch(
                RetentionMetricComputed(
                    school_id=auth.school_id,
                    actor_id=auth.user_id,
                    metric_id=metric.id,
                    academic_year_from=metric.academic_year_from,
                    academic_year_to=metric.academic_year_to,
                )
            )
            await uow.commit()
        return response

    async def list_cashflow_forecasts(
        self,
        *,
        auth: AuthContext,
        start_month: date | None = None,
        end_month: date | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        forecasts = await self.repo.list_cashflow_forecasts(
            school_id=auth.school_id,
            start_month=start_month,
            end_month=end_month,
            skip=skip,
            limit=limit,
        )
        return [self._cashflow_to_response(forecast) for forecast in forecasts]

    async def compute_cashflow(
        self,
        *,
        body: CashflowForecastComputeRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> list[dict[str, Any]]:
        current_month = _first_day_of_month(date.today())
        end_month = _add_months(current_month, body.months_ahead - 1)
        history_start_month = _add_months(current_month, -6)
        history_end_month = _add_months(current_month, -1)

        scheduled_income = await self.repo.aggregate_invoice_amounts_by_due_month(
            school_id=auth.school_id,
            start_date=current_month,
            end_date=end_month,
        )
        historical_scheduled_income = (
            await self.repo.aggregate_invoice_amounts_by_due_month(
                school_id=auth.school_id,
                start_date=history_start_month,
                end_date=history_end_month,
            )
        )
        actual_income = await self.repo.aggregate_paid_invoice_amounts_by_month(
            school_id=auth.school_id,
            start_datetime=_start_of_day(history_start_month),
            end_datetime=_end_of_day(end_month),
        )
        monthly_expenses = await self.repo.aggregate_expense_amounts_by_month(
            school_id=auth.school_id,
            start_datetime=_start_of_day(history_start_month),
            end_datetime=_end_of_day(end_month),
        )
        collection_ratio = await self.repo.get_recent_collection_ratio(
            school_id=auth.school_id,
            start_date=history_start_month,
            end_date=history_end_month,
        )

        fallback_income = (
            sum(historical_scheduled_income.values()) / len(historical_scheduled_income)
            if historical_scheduled_income
            else 0.0
        )
        fallback_expenses = (
            sum(monthly_expenses.values()) / len(monthly_expenses)
            if monthly_expenses
            else 0.0
        )

        responses: list[dict[str, Any]] = []
        async with UnitOfWork(self.db) as uow:
            repo = FinancialHealthRepository(uow.session)
            audit = AuditService(uow.session)
            dispatcher = EventDispatcher(uow.session)
            for offset in range(body.months_ahead):
                forecast_month = _add_months(current_month, offset)
                expected_income = round(
                    scheduled_income.get(forecast_month, fallback_income),
                    2,
                )
                expected_expenses = round(
                    monthly_expenses.get(forecast_month, fallback_expenses),
                    2,
                )
                confidence_score = round(
                    max(0.2, min(1.0, collection_ratio - (offset * 0.05))),
                    3,
                )
                existing = await repo.get_cashflow_forecast(
                    school_id=auth.school_id,
                    forecast_month=forecast_month,
                )
                actual_income_value = (
                    round(actual_income.get(forecast_month, 0.0), 2)
                    if forecast_month <= current_month
                    else None
                )
                actual_expenses_value = (
                    round(monthly_expenses.get(forecast_month, 0.0), 2)
                    if forecast_month <= current_month
                    else None
                )

                if existing is None:
                    existing = await repo.create_cashflow_forecast(
                        school_id=auth.school_id,
                        forecast_month=forecast_month,
                        expected_income=expected_income,
                        expected_expenses=expected_expenses,
                        actual_income=actual_income_value,
                        actual_expenses=actual_expenses_value,
                        currency="MAD",
                        confidence_score=confidence_score,
                        computed_at=datetime.now(UTC),
                    )
                else:
                    existing.expected_income = expected_income
                    existing.expected_expenses = expected_expenses
                    existing.actual_income = actual_income_value
                    existing.actual_expenses = actual_expenses_value
                    existing.currency = "MAD"
                    existing.confidence_score = confidence_score
                    existing.computed_at = datetime.now(UTC)
                    existing = await repo.save_cashflow_forecast(existing)

                response = self._cashflow_to_response(existing)
                responses.append(response)
                await dispatcher.dispatch(
                    CashflowForecastComputed(
                        school_id=auth.school_id,
                        actor_id=auth.user_id,
                        forecast_id=existing.id,
                        forecast_month=existing.forecast_month.isoformat(),
                    )
                )

            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="financial_health.cashflow.compute",
                outcome="success",
                target_type="cashflow_forecast",
                entity_after={"months_ahead": body.months_ahead, "items": responses},
                ip_address=ip_address,
            )
            await uow.commit()
        return responses

    async def get_cost_analysis(
        self,
        *,
        academic_year_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict[str, Any]:
        analysis = await self.repo.get_cost_per_student(
            school_id=auth.school_id,
            academic_year_id=academic_year_id,
        )
        if analysis is None:
            return await self.compute_cost(
                body=CostPerStudentComputeRequest(academic_year_id=academic_year_id),
                auth=auth,
            )
        return self._cost_to_response(analysis)

    async def compute_cost(
        self,
        *,
        body: CostPerStudentComputeRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        await self._get_academic_year_or_404(
            academic_year_id=body.academic_year_id, auth=auth
        )
        total_students = await self.repo.count_active_students_for_academic_year(
            school_id=auth.school_id,
            academic_year_id=body.academic_year_id,
        )
        if total_students <= 0:
            raise ValidationError(
                "Cannot compute cost per student without enrolled students",
                error_code="ERR-FINHEALTH-422",
            )

        expense_total = await self.repo.get_expense_total_for_academic_year(
            school_id=auth.school_id,
            academic_year_id=body.academic_year_id,
        )
        budget_total = await self.repo.get_budget_total_for_academic_year(
            school_id=auth.school_id,
            academic_year_id=body.academic_year_id,
        )
        total_operational_cost = round(
            expense_total if expense_total > 0 else budget_total, 2
        )
        revenue_total = await self.repo.get_collected_revenue_for_academic_year(
            school_id=auth.school_id,
            academic_year_id=body.academic_year_id,
        )
        cost_per_student = round(total_operational_cost / total_students, 2)
        revenue_per_student = round(revenue_total / total_students, 2)
        margin_per_student = round(revenue_per_student - cost_per_student, 2)

        async with UnitOfWork(self.db) as uow:
            repo = FinancialHealthRepository(uow.session)
            audit = AuditService(uow.session)
            dispatcher = EventDispatcher(uow.session)
            analysis = await repo.get_cost_per_student(
                school_id=auth.school_id,
                academic_year_id=body.academic_year_id,
            )
            if analysis is None:
                analysis = await repo.create_cost_per_student(
                    school_id=auth.school_id,
                    academic_year_id=body.academic_year_id,
                    total_operational_cost=total_operational_cost,
                    total_students=total_students,
                    cost_per_student=cost_per_student,
                    revenue_per_student=revenue_per_student,
                    margin_per_student=margin_per_student,
                    currency="MAD",
                    computed_at=datetime.now(UTC),
                )
            else:
                analysis.total_operational_cost = total_operational_cost
                analysis.total_students = total_students
                analysis.cost_per_student = cost_per_student
                analysis.revenue_per_student = revenue_per_student
                analysis.margin_per_student = margin_per_student
                analysis.currency = "MAD"
                analysis.computed_at = datetime.now(UTC)
                analysis = await repo.save_cost_per_student(analysis)

            response = self._cost_to_response(analysis)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="financial_health.cost.compute",
                outcome="success",
                target_type="cost_per_student",
                target_id=analysis.id,
                entity_after=response,
                ip_address=ip_address,
            )
            await dispatcher.dispatch(
                CostPerStudentComputed(
                    school_id=auth.school_id,
                    actor_id=auth.user_id,
                    analysis_id=analysis.id,
                    academic_year_id=analysis.academic_year_id,
                )
            )
            await uow.commit()
        return response

    async def get_snapshot(
        self,
        *,
        auth: AuthContext,
        snapshot_date: date | None = None,
    ) -> dict[str, Any]:
        target_date = snapshot_date or date.today()
        snapshot = await self.repo.get_financial_snapshot(
            school_id=auth.school_id,
            snapshot_date=target_date,
        )
        if snapshot is None:
            return await self.compute_snapshot(
                body=FinancialSnapshotComputeRequest(snapshot_date=target_date),
                auth=auth,
            )
        return self._snapshot_to_response(snapshot)

    async def compute_snapshot(
        self,
        *,
        body: FinancialSnapshotComputeRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        snapshot_date = body.snapshot_date or date.today()
        total_receivable = await self.repo.get_total_receivable_as_of(
            school_id=auth.school_id,
            snapshot_date=snapshot_date,
        )
        total_collected = await self.repo.get_total_collected_as_of(
            school_id=auth.school_id,
            snapshot_date=snapshot_date,
        )
        overdue_amount, overdue_count = await self.repo.get_overdue_totals_as_of(
            school_id=auth.school_id,
            snapshot_date=snapshot_date,
        )
        avg_delay = await self.repo.get_average_payment_delay_days_as_of(
            school_id=auth.school_id,
            snapshot_date=snapshot_date,
        )
        collection_rate = _percentage(
            total_collected,
            total_collected + total_receivable,
        )

        async with UnitOfWork(self.db) as uow:
            repo = FinancialHealthRepository(uow.session)
            audit = AuditService(uow.session)
            dispatcher = EventDispatcher(uow.session)
            snapshot = await repo.get_financial_snapshot(
                school_id=auth.school_id,
                snapshot_date=snapshot_date,
            )
            if snapshot is None:
                snapshot = await repo.create_financial_snapshot(
                    school_id=auth.school_id,
                    snapshot_date=snapshot_date,
                    total_receivable=round(total_receivable, 2),
                    total_collected=round(total_collected, 2),
                    collection_rate=collection_rate,
                    overdue_amount=round(overdue_amount, 2),
                    overdue_count=overdue_count,
                    avg_payment_delay_days=None
                    if avg_delay is None
                    else round(avg_delay, 2),
                    currency="MAD",
                    computed_at=datetime.now(UTC),
                )
            else:
                snapshot.total_receivable = round(total_receivable, 2)
                snapshot.total_collected = round(total_collected, 2)
                snapshot.collection_rate = collection_rate
                snapshot.overdue_amount = round(overdue_amount, 2)
                snapshot.overdue_count = overdue_count
                snapshot.avg_payment_delay_days = (
                    None if avg_delay is None else round(avg_delay, 2)
                )
                snapshot.currency = "MAD"
                snapshot.computed_at = datetime.now(UTC)
                snapshot = await repo.save_financial_snapshot(snapshot)

            response = self._snapshot_to_response(snapshot)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="financial_health.snapshot.compute",
                outcome="success",
                target_type="financial_snapshot",
                target_id=snapshot.id,
                entity_after=response,
                ip_address=ip_address,
            )
            await dispatcher.dispatch(
                FinancialSnapshotComputed(
                    school_id=auth.school_id,
                    actor_id=auth.user_id,
                    snapshot_id=snapshot.id,
                    snapshot_date=snapshot.snapshot_date.isoformat(),
                )
            )
            await uow.commit()
        return response

    async def get_dashboard(self, *, auth: AuthContext) -> dict[str, Any]:
        retention = await self.list_retention_metrics(auth=auth, limit=1)
        snapshot = await self.get_snapshot(auth=auth)
        current_month = _first_day_of_month(date.today())
        cashflow = await self.list_cashflow_forecasts(
            auth=auth,
            start_month=current_month,
            end_month=current_month,
            limit=1,
        )
        return {
            "school_id": str(auth.school_id),
            "retention": retention[0] if retention else None,
            "snapshot": snapshot,
            "cashflow": cashflow[0] if cashflow else None,
        }

    async def get_trends(
        self,
        *,
        auth: AuthContext,
        months: int = 12,
    ) -> dict[str, Any]:
        current_month = _first_day_of_month(date.today())
        start_month = _add_months(current_month, -(months - 1))
        retention = await self.list_retention_metrics(auth=auth, limit=months)
        snapshots = await self.repo.list_financial_snapshots(
            school_id=auth.school_id,
            limit=months,
        )
        cashflow = await self.list_cashflow_forecasts(
            auth=auth,
            start_month=start_month,
            end_month=current_month,
            limit=months,
        )
        return {
            "school_id": str(auth.school_id),
            "retention_metrics": retention,
            "snapshots": [self._snapshot_to_response(item) for item in snapshots],
            "cashflow": cashflow,
        }

    async def export_csv(self, *, auth: AuthContext) -> bytes:
        dashboard = await self.get_dashboard(auth=auth)
        trends = await self.get_trends(auth=auth, months=12)

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["section", "metric", "value"])
        snapshot = dashboard.get("snapshot") or {}
        writer.writerow(["dashboard", "school_id", dashboard["school_id"]])
        writer.writerow(
            ["dashboard", "collection_rate", snapshot.get("collection_rate", 0)]
        )
        writer.writerow(
            ["dashboard", "total_receivable", snapshot.get("total_receivable", 0)]
        )
        writer.writerow(
            ["dashboard", "total_collected", snapshot.get("total_collected", 0)]
        )

        for metric in trends.get("retention_metrics", []):
            writer.writerow(
                [
                    "retention",
                    f"{metric['academic_year_from']}->{metric['academic_year_to']}",
                    metric["retention_rate"],
                ]
            )
        for item in trends.get("cashflow", []):
            writer.writerow(
                [
                    "cashflow",
                    item["forecast_month"],
                    item["expected_income"] - item["expected_expenses"],
                ]
            )
        return buffer.getvalue().encode("utf-8")

    async def export_pdf(self, *, auth: AuthContext) -> bytes:
        dashboard = await self.get_dashboard(auth=auth)
        snapshot = dashboard.get("snapshot") or {}
        lines = [
            "Financial Health Dashboard",
            f"School: {dashboard['school_id']}",
            f"Collection rate: {snapshot.get('collection_rate', 0)}%",
            f"Receivable: {snapshot.get('total_receivable', 0)} MAD",
            f"Collected: {snapshot.get('total_collected', 0)} MAD",
        ]
        return "\n".join(lines).encode("utf-8")
