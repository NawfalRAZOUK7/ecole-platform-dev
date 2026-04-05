"""Unit tests for financial health service workflows."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio

from app.core.dependencies import AuthContext
from app.core.exceptions import NotFoundError, ValidationError
from app.services import financial_health_service as fin_module
from app.services.financial_health_service import FinancialHealthService


@pytest_asyncio.fixture(autouse=True)
async def clear_analytics_cache():
    yield


@pytest_asyncio.fixture(autouse=True)
async def override_test_redis():
    yield


@pytest_asyncio.fixture(autouse=True)
async def dispose_app_engine_pool():
    yield


def make_auth(role: str = "ADM") -> AuthContext:
    return AuthContext(
        user_id=uuid.uuid4(),
        role=role,
        school_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        permissions=set(),
    )


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.session = AsyncMock()
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def commit(self) -> None:
        self.committed = True


def make_academic_year(auth: AuthContext, *, label: str, year_id: uuid.UUID | None = None):
    return SimpleNamespace(
        id=year_id or uuid.uuid4(),
        school_id=auth.school_id,
        label=label,
    )


def make_retention_metric(auth: AuthContext, *, metric_id: uuid.UUID | None = None):
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=metric_id or uuid.uuid4(),
        school_id=auth.school_id,
        academic_year_from="2024-2025",
        academic_year_to="2025-2026",
        total_students_start=20,
        total_students_end=22,
        retained=18,
        new_enrollments=4,
        withdrawals=2,
        retention_rate=90.0,
        computed_at=now,
        created_at=now,
        updated_at=now,
    )


def make_cashflow(auth: AuthContext, *, forecast_month: date):
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=uuid.uuid4(),
        school_id=auth.school_id,
        forecast_month=forecast_month,
        expected_income=12000.0,
        expected_expenses=8000.0,
        actual_income=11500.0,
        actual_expenses=7600.0,
        currency="MAD",
        confidence_score=0.85,
        computed_at=now,
        created_at=now,
        updated_at=now,
    )


def make_cost_analysis(auth: AuthContext, *, academic_year_id: uuid.UUID):
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=uuid.uuid4(),
        school_id=auth.school_id,
        academic_year_id=academic_year_id,
        total_operational_cost=30000.0,
        total_students=25,
        cost_per_student=1200.0,
        revenue_per_student=1500.0,
        margin_per_student=300.0,
        currency="MAD",
        computed_at=now,
        created_at=now,
        updated_at=now,
    )


def make_snapshot(auth: AuthContext, *, snapshot_date: date):
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=uuid.uuid4(),
        school_id=auth.school_id,
        snapshot_date=snapshot_date,
        total_receivable=6000.0,
        total_collected=14000.0,
        collection_rate=70.0,
        overdue_amount=2500.0,
        overdue_count=3,
        avg_payment_delay_days=4.5,
        currency="MAD",
        computed_at=now,
        created_at=now,
        updated_at=now,
    )


def setup_service(monkeypatch: pytest.MonkeyPatch):
    service = FinancialHealthService(AsyncMock())
    service.repo = AsyncMock()
    service.audit = AsyncMock()
    service._dispatcher = SimpleNamespace(dispatch=AsyncMock())

    repo_in_uow = AsyncMock()
    audit_in_uow = AsyncMock()
    dispatcher_in_uow = SimpleNamespace(dispatch=AsyncMock())
    uow = FakeUnitOfWork()

    monkeypatch.setattr(fin_module, "UnitOfWork", lambda _db: uow)
    monkeypatch.setattr(
        fin_module,
        "FinancialHealthRepository",
        lambda _session: repo_in_uow,
    )
    monkeypatch.setattr(fin_module, "AuditService", lambda _session: audit_in_uow)
    monkeypatch.setattr(
        fin_module,
        "EventDispatcher",
        lambda _session: dispatcher_in_uow,
    )

    return service, repo_in_uow, audit_in_uow, dispatcher_in_uow, uow


class TestFinancialHealthService:
    @pytest.mark.asyncio
    async def test_list_retention_metrics_serializes_items(self) -> None:
        auth = make_auth()
        service = FinancialHealthService(AsyncMock())
        service.repo = AsyncMock()
        service.repo.list_retention_metrics.return_value = [make_retention_metric(auth)]

        result = await service.list_retention_metrics(auth=auth)

        assert result[0]["school_id"] == str(auth.school_id)
        assert result[0]["retention_rate"] == 90.0

    @pytest.mark.asyncio
    async def test_compute_retention_creates_metric_when_missing(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth()
        service, repo_in_uow, audit, dispatcher, uow = setup_service(monkeypatch)
        from_year = make_academic_year(auth, label="2024-2025")
        to_year = make_academic_year(auth, label="2025-2026")
        created = make_retention_metric(auth)
        service.repo.get_academic_year_by_label.side_effect = [from_year, to_year]
        service.repo.list_active_student_ids_for_academic_year.side_effect = [
            {uuid.uuid4(), uuid.uuid4(), uuid.uuid4()},
            {uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4()},
        ]
        repo_in_uow.get_retention_metric.return_value = None
        repo_in_uow.create_retention_metric.return_value = created

        result = await service.compute_retention(
            body=fin_module.RetentionComputeRequest(
                academic_year_from="2024-2025",
                academic_year_to="2025-2026",
            ),
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["school_id"] == str(auth.school_id)
        audit.log_event.assert_awaited_once()
        dispatcher.dispatch.assert_awaited_once()
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_compute_retention_updates_existing_metric(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth()
        service, repo_in_uow, _, _, _ = setup_service(monkeypatch)
        from_year = make_academic_year(auth, label="2024-2025")
        to_year = make_academic_year(auth, label="2025-2026")
        existing = make_retention_metric(auth)
        service.repo.get_academic_year_by_label.side_effect = [from_year, to_year]
        shared_student = uuid.uuid4()
        service.repo.list_active_student_ids_for_academic_year.side_effect = [
            {shared_student, uuid.uuid4()},
            {shared_student, uuid.uuid4(), uuid.uuid4()},
        ]
        repo_in_uow.get_retention_metric.return_value = existing
        repo_in_uow.save_retention_metric.return_value = existing

        result = await service.compute_retention(
            body=fin_module.RetentionComputeRequest(
                academic_year_from="2024-2025",
                academic_year_to="2025-2026",
            ),
            auth=auth,
        )

        assert result["retained"] == 1
        assert existing.total_students_end == 3
        repo_in_uow.save_retention_metric.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_compute_retention_raises_when_year_missing(self) -> None:
        auth = make_auth()
        service = FinancialHealthService(AsyncMock())
        service.repo = AsyncMock()
        service.repo.get_academic_year_by_label.return_value = None

        with pytest.raises(NotFoundError):
            await service.compute_retention(
                body=fin_module.RetentionComputeRequest(
                    academic_year_from="2024-2025",
                    academic_year_to="2025-2026",
                ),
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_list_cashflow_forecasts_serializes_items(self) -> None:
        auth = make_auth()
        service = FinancialHealthService(AsyncMock())
        service.repo = AsyncMock()
        service.repo.list_cashflow_forecasts.return_value = [
            make_cashflow(auth, forecast_month=date(2026, 4, 1))
        ]

        result = await service.list_cashflow_forecasts(auth=auth)

        assert result[0]["forecast_month"] == "2026-04-01"
        assert result[0]["currency"] == "MAD"

    @pytest.mark.asyncio
    async def test_compute_cashflow_creates_requested_months(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth()
        service, repo_in_uow, audit, dispatcher, uow = setup_service(monkeypatch)
        service.repo.aggregate_invoice_amounts_by_due_month.side_effect = [
            {date.today().replace(day=1): 12000.0},
            {date.today().replace(day=1): 10000.0},
        ]
        service.repo.aggregate_paid_invoice_amounts_by_month.return_value = {
            date.today().replace(day=1): 11000.0
        }
        service.repo.aggregate_expense_amounts_by_month.return_value = {
            date.today().replace(day=1): 7000.0
        }
        service.repo.get_recent_collection_ratio.return_value = 0.9
        repo_in_uow.get_cashflow_forecast.side_effect = [None, None]
        repo_in_uow.create_cashflow_forecast.side_effect = [
            make_cashflow(auth, forecast_month=fin_module._first_day_of_month(date.today())),
            make_cashflow(
                auth,
                forecast_month=fin_module._add_months(
                    fin_module._first_day_of_month(date.today()),
                    1,
                ),
            ),
        ]

        result = await service.compute_cashflow(
            body=fin_module.CashflowForecastComputeRequest(months_ahead=2),
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert len(result) == 2
        assert audit.log_event.await_count == 1
        assert dispatcher.dispatch.await_count == 2
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_compute_cashflow_uses_fallback_values_without_history(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth()
        service, repo_in_uow, _, _, _ = setup_service(monkeypatch)
        service.repo.aggregate_invoice_amounts_by_due_month.side_effect = [{}, {}]
        service.repo.aggregate_paid_invoice_amounts_by_month.return_value = {}
        service.repo.aggregate_expense_amounts_by_month.return_value = {}
        service.repo.get_recent_collection_ratio.return_value = 0.5
        created = make_cashflow(auth, forecast_month=fin_module._first_day_of_month(date.today()))
        repo_in_uow.get_cashflow_forecast.return_value = None
        repo_in_uow.create_cashflow_forecast.return_value = created

        result = await service.compute_cashflow(
            body=fin_module.CashflowForecastComputeRequest(months_ahead=1),
            auth=auth,
        )

        assert result[0]["expected_income"] == 12000.0
        assert result[0]["confidence_score"] >= 0.2

    @pytest.mark.asyncio
    async def test_get_cost_analysis_returns_existing_analysis(self) -> None:
        auth = make_auth()
        service = FinancialHealthService(AsyncMock())
        service.repo = AsyncMock()
        analysis = make_cost_analysis(auth, academic_year_id=uuid.uuid4())
        service.repo.get_cost_per_student.return_value = analysis

        result = await service.get_cost_analysis(
            academic_year_id=analysis.academic_year_id,
            auth=auth,
        )

        assert result["margin_per_student"] == 300.0

    @pytest.mark.asyncio
    async def test_get_cost_analysis_computes_when_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        auth = make_auth()
        service = FinancialHealthService(AsyncMock())
        service.repo = AsyncMock()
        service.repo.get_cost_per_student.return_value = None
        expected = {"id": "generated", "margin_per_student": 10.0}
        service.compute_cost = AsyncMock(return_value=expected)

        result = await service.get_cost_analysis(
            academic_year_id=uuid.uuid4(),
            auth=auth,
        )

        assert result == expected
        service.compute_cost.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_compute_cost_raises_for_zero_students(self) -> None:
        auth = make_auth()
        service = FinancialHealthService(AsyncMock())
        service.repo = AsyncMock()
        academic_year = make_academic_year(auth, label="2025-2026")
        service.repo.get_academic_year.return_value = academic_year
        service.repo.count_active_students_for_academic_year.return_value = 0

        with pytest.raises(ValidationError, match="without enrolled students"):
            await service.compute_cost(
                body=fin_module.CostPerStudentComputeRequest(academic_year_id=academic_year.id),
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_compute_cost_prefers_expense_total_over_budget_total(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth()
        service, repo_in_uow, audit, dispatcher, uow = setup_service(monkeypatch)
        academic_year = make_academic_year(auth, label="2025-2026")
        created = make_cost_analysis(auth, academic_year_id=academic_year.id)
        service.repo.get_academic_year.return_value = academic_year
        service.repo.count_active_students_for_academic_year.return_value = 10
        service.repo.get_expense_total_for_academic_year.return_value = 20000.0
        service.repo.get_budget_total_for_academic_year.return_value = 30000.0
        service.repo.get_collected_revenue_for_academic_year.return_value = 25000.0
        repo_in_uow.get_cost_per_student.return_value = None
        repo_in_uow.create_cost_per_student.return_value = created

        result = await service.compute_cost(
            body=fin_module.CostPerStudentComputeRequest(academic_year_id=academic_year.id),
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["cost_per_student"] == 1200.0
        audit.log_event.assert_awaited_once()
        dispatcher.dispatch.assert_awaited_once()
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_compute_cost_falls_back_to_budget_total(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth()
        service, repo_in_uow, _, _, _ = setup_service(monkeypatch)
        academic_year = make_academic_year(auth, label="2025-2026")
        created = make_cost_analysis(auth, academic_year_id=academic_year.id)
        service.repo.get_academic_year.return_value = academic_year
        service.repo.count_active_students_for_academic_year.return_value = 20
        service.repo.get_expense_total_for_academic_year.return_value = 0.0
        service.repo.get_budget_total_for_academic_year.return_value = 30000.0
        service.repo.get_collected_revenue_for_academic_year.return_value = 20000.0
        repo_in_uow.get_cost_per_student.return_value = None
        repo_in_uow.create_cost_per_student.return_value = created

        await service.compute_cost(
            body=fin_module.CostPerStudentComputeRequest(academic_year_id=academic_year.id),
            auth=auth,
        )

        create_kwargs = repo_in_uow.create_cost_per_student.await_args.kwargs
        assert create_kwargs["total_operational_cost"] == 30000.0

    @pytest.mark.asyncio
    async def test_get_snapshot_returns_existing_snapshot(self) -> None:
        auth = make_auth()
        service = FinancialHealthService(AsyncMock())
        service.repo = AsyncMock()
        snapshot = make_snapshot(auth, snapshot_date=date(2026, 4, 5))
        service.repo.get_financial_snapshot.return_value = snapshot

        result = await service.get_snapshot(auth=auth, snapshot_date=snapshot.snapshot_date)

        assert result["overdue_count"] == 3

    @pytest.mark.asyncio
    async def test_get_snapshot_computes_when_missing(self) -> None:
        auth = make_auth()
        service = FinancialHealthService(AsyncMock())
        service.repo = AsyncMock()
        service.repo.get_financial_snapshot.return_value = None
        expected = {"id": "snapshot-1", "collection_rate": 80.0}
        service.compute_snapshot = AsyncMock(return_value=expected)

        result = await service.get_snapshot(auth=auth)

        assert result == expected
        service.compute_snapshot.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_compute_snapshot_updates_existing_snapshot(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth()
        service, repo_in_uow, audit, dispatcher, uow = setup_service(monkeypatch)
        existing = make_snapshot(auth, snapshot_date=date(2026, 4, 5))
        service.repo.get_total_receivable_as_of.return_value = 5000.0
        service.repo.get_total_collected_as_of.return_value = 15000.0
        service.repo.get_overdue_totals_as_of.return_value = (2500.0, 3)
        service.repo.get_average_payment_delay_days_as_of.return_value = 4.5
        repo_in_uow.get_financial_snapshot.return_value = existing
        repo_in_uow.save_financial_snapshot.return_value = existing

        result = await service.compute_snapshot(
            body=fin_module.FinancialSnapshotComputeRequest(snapshot_date=existing.snapshot_date),
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["collection_rate"] == 75.0
        audit.log_event.assert_awaited_once()
        dispatcher.dispatch.assert_awaited_once()
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_compute_snapshot_uses_zero_collection_rate_for_empty_totals(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth()
        service, repo_in_uow, _, _, _ = setup_service(monkeypatch)
        created = make_snapshot(auth, snapshot_date=date(2026, 4, 5))
        service.repo.get_total_receivable_as_of.return_value = 0.0
        service.repo.get_total_collected_as_of.return_value = 0.0
        service.repo.get_overdue_totals_as_of.return_value = (0.0, 0)
        service.repo.get_average_payment_delay_days_as_of.return_value = None
        repo_in_uow.get_financial_snapshot.return_value = None
        repo_in_uow.create_financial_snapshot.return_value = created

        await service.compute_snapshot(
            body=fin_module.FinancialSnapshotComputeRequest(snapshot_date=created.snapshot_date),
            auth=auth,
        )

        create_kwargs = repo_in_uow.create_financial_snapshot.await_args.kwargs
        assert create_kwargs["collection_rate"] == 0.0
        assert create_kwargs["avg_payment_delay_days"] is None

    @pytest.mark.asyncio
    async def test_get_dashboard_combines_metric_sections(self) -> None:
        auth = make_auth()
        service = FinancialHealthService(AsyncMock())
        service.list_retention_metrics = AsyncMock(return_value=[{"id": "ret-1"}])
        service.get_snapshot = AsyncMock(return_value={"id": "snap-1"})
        service.list_cashflow_forecasts = AsyncMock(return_value=[{"id": "cf-1"}])

        result = await service.get_dashboard(auth=auth)

        assert result["retention"]["id"] == "ret-1"
        assert result["snapshot"]["id"] == "snap-1"
        assert result["cashflow"]["id"] == "cf-1"

    @pytest.mark.asyncio
    async def test_get_trends_serializes_snapshot_history(self) -> None:
        auth = make_auth()
        service = FinancialHealthService(AsyncMock())
        service.list_retention_metrics = AsyncMock(return_value=[{"id": "ret-1"}])
        service.list_cashflow_forecasts = AsyncMock(return_value=[{"id": "cf-1"}])
        service.repo = AsyncMock()
        service.repo.list_financial_snapshots.return_value = [
            make_snapshot(auth, snapshot_date=date(2026, 4, 5))
        ]

        result = await service.get_trends(auth=auth, months=6)

        assert result["retention_metrics"][0]["id"] == "ret-1"
        assert result["snapshots"][0]["snapshot_date"] == "2026-04-05"
        assert result["cashflow"][0]["id"] == "cf-1"

    @pytest.mark.asyncio
    async def test_export_csv_returns_dashboard_rows(self) -> None:
        auth = make_auth()
        service = FinancialHealthService(AsyncMock())
        service.get_dashboard = AsyncMock(
            return_value={
                "school_id": str(auth.school_id),
                "snapshot": {
                    "collection_rate": 80.0,
                    "total_receivable": 5000.0,
                    "total_collected": 20000.0,
                },
            }
        )
        service.get_trends = AsyncMock(
            return_value={
                "retention_metrics": [
                    {
                        "academic_year_from": "2024-2025",
                        "academic_year_to": "2025-2026",
                        "retention_rate": 92.0,
                    }
                ],
                "cashflow": [
                    {
                        "forecast_month": date(2026, 4, 1),
                        "expected_income": 10000.0,
                        "expected_expenses": 7000.0,
                    }
                ],
            }
        )

        payload = await service.export_csv(auth=auth)

        assert b"collection_rate" in payload
        assert b"2024-2025->2025-2026" in payload

    @pytest.mark.asyncio
    async def test_export_pdf_returns_plain_bytes(self) -> None:
        auth = make_auth()
        service = FinancialHealthService(AsyncMock())
        service.get_dashboard = AsyncMock(
            return_value={
                "school_id": str(auth.school_id),
                "snapshot": {
                    "collection_rate": 75.0,
                    "total_receivable": 3000.0,
                    "total_collected": 9000.0,
                },
            }
        )

        payload = await service.export_pdf(auth=auth)

        assert b"Financial Health Dashboard" in payload
        assert str(auth.school_id).encode("utf-8") in payload
