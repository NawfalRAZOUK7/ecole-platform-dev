"""Edge and validation tests for budget models, schemas, and analytics."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from pydantic import ValidationError as PydanticValidationError

from app.schemas.billing.budget import (
    BudgetAllocationCreateRequest,
    BudgetRequestCreateRequest,
    BudgetTransactionCreateRequest,
    MicroBudgetCreateRequest,
)
from app.services.billing.budget_service import BudgetService


@pytest_asyncio.fixture(autouse=True)
async def clear_analytics_cache():
    yield


@pytest_asyncio.fixture(autouse=True)
async def override_test_redis():
    yield


@pytest_asyncio.fixture(autouse=True)
async def dispose_app_engine_pool():
    yield


class TestBudgetModelValidation:
    def test_micro_budget_currency_rejects_non_mad(self) -> None:
        from app.models.budget import MicroBudget

        budget = MicroBudget()

        with pytest.raises(ValueError, match="currency must be MAD"):
            budget.validate_currency("currency", "EUR")

    def test_budget_allocation_label_rejects_blank_value(self) -> None:
        from app.models.budget import BudgetAllocation

        allocation = BudgetAllocation()

        with pytest.raises(ValueError, match="label is required"):
            allocation.validate_label("label", "   ")

    def test_budget_request_description_rejects_blank_value(self) -> None:
        from app.models.budget import BudgetRequest

        request = BudgetRequest()

        with pytest.raises(ValueError, match="description is required"):
            request.validate_description("description", "   ")

    def test_budget_transaction_description_rejects_blank_value(self) -> None:
        from app.models.budget import BudgetTransaction

        transaction = BudgetTransaction()

        with pytest.raises(ValueError, match="description is required"):
            transaction.validate_description("description", "   ")


class TestBudgetSchemaValidation:
    def test_budget_create_request_rejects_negative_amount(self) -> None:
        with pytest.raises(PydanticValidationError):
            MicroBudgetCreateRequest(
                academic_year_id="10000000-0000-4000-8000-000000000001",
                total_amount=-1,
            )

    def test_allocation_request_requires_positive_amount(self) -> None:
        with pytest.raises(PydanticValidationError):
            BudgetAllocationCreateRequest(
                teacher_id="10000000-0000-4000-8000-000000000002",
                label="Budget Test",
                amount=0,
            )

    def test_budget_request_requires_description(self) -> None:
        with pytest.raises(PydanticValidationError):
            BudgetRequestCreateRequest(amount=100, description="")

    def test_transaction_request_rejects_unknown_type(self) -> None:
        with pytest.raises(PydanticValidationError):
            BudgetTransactionCreateRequest(
                amount=100,
                transaction_type="unknown",
                description="Invalid type",
            )


class TestBudgetServiceEdges:
    @pytest.mark.asyncio
    async def test_budget_analytics_returns_zeroes_for_empty_dataset(self) -> None:
        service = BudgetService(AsyncMock())
        service.repo = AsyncMock()
        service.repo.list_budgets.return_value = []
        service.repo.list_allocations.return_value = []
        service.repo.list_requests.return_value = []
        service.repo.list_transactions.return_value = []

        result = await service.get_budget_analytics(
            auth=type(
                "AuthStub",
                (),
                {"school_id": "10000000-0000-4000-8000-000000000001"},
            )(),
            academic_year_id=None,
        )

        assert result == {
            "school_id": "10000000-0000-4000-8000-000000000001",
            "academic_year_id": None,
            "budget_count": 0,
            "allocation_count": 0,
            "request_count": 0,
            "transaction_count": 0,
            "total_budget_amount": 0.0,
            "total_allocated_amount": 0.0,
            "total_remaining_unallocated": 0.0,
            "total_spent_amount": 0.0,
            "total_allocation_remaining": 0.0,
            "pending_request_amount": 0.0,
            "approved_request_amount": 0.0,
            "utilization_rate": 0.0,
        }
