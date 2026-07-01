"""Edge and validation tests for financial health models, schemas, and services."""

from __future__ import annotations

import uuid
from datetime import date
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from pydantic import ValidationError as PydanticValidationError

from app.core.dependencies import AuthContext
from app.core.exceptions import NotFoundError, ValidationError
from app.schemas.reports.financial_health import (
    CashflowForecastComputeRequest,
    CostPerStudentComputeRequest,
    FinancialSnapshotComputeRequest,
    RetentionComputeRequest,
)
from app.services.reports.financial_health_service import FinancialHealthService


@pytest_asyncio.fixture(autouse=True)
async def clear_analytics_cache():
    yield


@pytest_asyncio.fixture(autouse=True)
async def override_test_redis():
    yield


@pytest_asyncio.fixture(autouse=True)
async def dispose_app_engine_pool():
    yield


class TestFinancialHealthModelValidation:
    def test_retention_metric_rejects_blank_academic_year(self) -> None:
        from app.models.financial_health import RetentionMetric

        metric = RetentionMetric()

        with pytest.raises(ValueError, match="academic_year_from is required"):
            metric.validate_academic_year("academic_year_from", "   ")

    def test_cashflow_forecast_rejects_invalid_currency(self) -> None:
        from app.models.financial_health import CashflowForecast

        forecast = CashflowForecast()

        with pytest.raises(ValueError, match="must be one of"):
            forecast.validate_currency("currency", "gbp")

    def test_cashflow_forecast_rejects_non_first_day_month(self) -> None:
        from app.models.financial_health import CashflowForecast

        forecast = CashflowForecast()

        with pytest.raises(ValueError, match="first day of the month"):
            forecast.validate_forecast_month("forecast_month", date(2026, 4, 2))

    def test_cost_per_student_rejects_invalid_currency(self) -> None:
        from app.models.financial_health import CostPerStudent

        analysis = CostPerStudent()

        with pytest.raises(ValueError, match="must be one of"):
            analysis.validate_currency("currency", "cad")

    def test_financial_snapshot_rejects_invalid_currency(self) -> None:
        from app.models.financial_health import FinancialSnapshot

        snapshot = FinancialSnapshot()

        with pytest.raises(ValueError, match="must be one of"):
            snapshot.validate_currency("currency", "cad")


class TestFinancialHealthSchemaValidation:
    def test_retention_compute_request_rejects_blank_from_year(self) -> None:
        with pytest.raises(PydanticValidationError):
            RetentionComputeRequest(academic_year_from="", academic_year_to="2025-2026")

    def test_cashflow_compute_request_rejects_zero_months(self) -> None:
        with pytest.raises(PydanticValidationError):
            CashflowForecastComputeRequest(months_ahead=0)

    def test_cost_compute_request_requires_uuid(self) -> None:
        with pytest.raises(PydanticValidationError):
            CostPerStudentComputeRequest(academic_year_id="not-a-uuid")

    def test_snapshot_compute_request_accepts_none(self) -> None:
        payload = FinancialSnapshotComputeRequest(snapshot_date=None)

        assert payload.snapshot_date is None


class TestFinancialHealthServiceEdges:
    @pytest.mark.asyncio
    async def test_compute_cost_raises_not_found_for_foreign_year(self) -> None:
        auth = AuthContext(
            user_id=uuid.uuid4(),
            role="ADM",
            school_id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            permissions=set(),
        )
        service = FinancialHealthService(AsyncMock())
        service.repo = AsyncMock()
        service.repo.get_academic_year.return_value = None

        with pytest.raises(NotFoundError):
            await service.compute_cost(
                body=CostPerStudentComputeRequest(academic_year_id=uuid.uuid4()),
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_compute_retention_raises_when_to_year_missing(self) -> None:
        auth = AuthContext(
            user_id=uuid.uuid4(),
            role="ADM",
            school_id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            permissions=set(),
        )
        service = FinancialHealthService(AsyncMock())
        service.repo = AsyncMock()
        service.repo.get_academic_year_by_label.side_effect = [object(), None]

        with pytest.raises(NotFoundError):
            await service.compute_retention(
                body=RetentionComputeRequest(
                    academic_year_from="2024-2025",
                    academic_year_to="2025-2026",
                ),
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_compute_snapshot_can_return_zero_overdue_metrics(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        auth = AuthContext(
            user_id=uuid.uuid4(),
            role="ADM",
            school_id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            permissions=set(),
        )
        service = FinancialHealthService(AsyncMock())
        service.repo = AsyncMock()
        service.repo.get_total_receivable_as_of.return_value = 0.0
        service.repo.get_total_collected_as_of.return_value = 1000.0
        service.repo.get_overdue_totals_as_of.return_value = (0.0, 0)
        service.repo.get_average_payment_delay_days_as_of.return_value = None

        fake_snapshot = type(
            "SnapshotStub",
            (),
            {
                "id": uuid.uuid4(),
                "school_id": auth.school_id,
                "snapshot_date": date(2026, 4, 5),
                "total_receivable": 0.0,
                "total_collected": 1000.0,
                "collection_rate": 100.0,
                "overdue_amount": 0.0,
                "overdue_count": 0,
                "avg_payment_delay_days": None,
                "currency": "MAD",
                "computed_at": None,
                "created_at": None,
                "updated_at": None,
            },
        )()
        repo_in_uow = AsyncMock()
        repo_in_uow.get_financial_snapshot.return_value = None
        repo_in_uow.create_financial_snapshot.return_value = fake_snapshot
        audit = AsyncMock()
        dispatcher = type("Dispatcher", (), {"dispatch": AsyncMock()})()

        class FakeUnitOfWork:
            def __init__(self):
                self.session = AsyncMock()

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            async def commit(self):
                return None

        monkeypatch.setattr(
            "app.services.reports.financial_health_service.UnitOfWork",
            lambda _db: FakeUnitOfWork(),
        )
        monkeypatch.setattr(
            "app.services.reports.financial_health_service.FinancialHealthRepository",
            lambda _session: repo_in_uow,
        )
        monkeypatch.setattr(
            "app.services.reports.financial_health_service.AuditService",
            lambda _session: audit,
        )
        monkeypatch.setattr(
            "app.services.reports.financial_health_service.EventDispatcher",
            lambda _session: dispatcher,
        )

        result = await service.compute_snapshot(
            body=FinancialSnapshotComputeRequest(snapshot_date=date(2026, 4, 5)),
            auth=auth,
        )

        assert result["collection_rate"] == 100.0
        assert result["overdue_count"] == 0

    @pytest.mark.asyncio
    async def test_export_pdf_works_with_missing_snapshot_values(self) -> None:
        auth = AuthContext(
            user_id=uuid.uuid4(),
            role="ADM",
            school_id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            permissions=set(),
        )
        service = FinancialHealthService(AsyncMock())
        service.get_dashboard = AsyncMock(
            return_value={"school_id": str(auth.school_id)}
        )

        payload = await service.export_pdf(auth=auth)

        assert b"Receivable: 0 MAD" in payload

    @pytest.mark.asyncio
    async def test_get_snapshot_computes_for_missing_date(self) -> None:
        auth = AuthContext(
            user_id=uuid.uuid4(),
            role="ADM",
            school_id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            permissions=set(),
        )
        service = FinancialHealthService(AsyncMock())
        service.repo = AsyncMock()
        service.repo.get_financial_snapshot.return_value = None
        service.compute_snapshot = AsyncMock(return_value={"id": "computed"})

        result = await service.get_snapshot(auth=auth)

        assert result["id"] == "computed"
        service.compute_snapshot.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_compute_cost_rejects_division_by_zero_students(self) -> None:
        auth = AuthContext(
            user_id=uuid.uuid4(),
            role="ADM",
            school_id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            permissions=set(),
        )
        service = FinancialHealthService(AsyncMock())
        service.repo = AsyncMock()
        service.repo.get_academic_year.return_value = type(
            "YearStub",
            (),
            {"id": uuid.uuid4(), "school_id": auth.school_id},
        )()
        service.repo.count_active_students_for_academic_year.return_value = 0

        with pytest.raises(ValidationError):
            await service.compute_cost(
                body=CostPerStudentComputeRequest(academic_year_id=uuid.uuid4()),
                auth=auth,
            )
