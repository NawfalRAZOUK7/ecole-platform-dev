"""Edge and validation tests for micro-school models and schemas."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from pydantic import ValidationError as PydanticValidationError

from app.schemas.micro_school import (
    MicroGroupCreateRequest,
    MicroPaymentCreateRequest,
    MicroProgressLogCreateRequest,
    MicroSchoolCreateRequest,
)
from app.services.micro_school_service import MicroPaymentService


@pytest_asyncio.fixture(autouse=True)
async def clear_analytics_cache():
    yield


@pytest_asyncio.fixture(autouse=True)
async def override_test_redis():
    yield


@pytest_asyncio.fixture(autouse=True)
async def dispose_app_engine_pool():
    yield


class TestMicroSchoolModelValidation:
    def test_micro_school_phone_rejects_non_moroccan_prefix(self) -> None:
        from app.models.micro_school import MicroSchool

        school = MicroSchool()

        with pytest.raises(ValueError, match="Moroccan format"):
            school.validate_phone("phone", "+33123456789")

    def test_micro_payment_currency_rejects_unsupported_value(self) -> None:
        from app.models.micro_school import MicroPayment

        payment = MicroPayment()

        with pytest.raises(ValueError, match="Currency must be one of"):
            payment.validate_currency("currency", "GBP")

    def test_micro_resource_language_rejects_unsupported_value(self) -> None:
        from app.models.micro_school import MicroResource

        resource = MicroResource()

        with pytest.raises(ValueError, match="Language must be one of"):
            resource.validate_language("language", "es")

    def test_micro_enrollment_rejects_blank_child_name(self) -> None:
        from app.models.micro_school import MicroEnrollment

        enrollment = MicroEnrollment()

        with pytest.raises(ValueError, match="Child name is required"):
            enrollment.validate_child_name("child_name", "   ")

    def test_micro_progress_log_rejects_blank_note(self) -> None:
        from app.models.micro_school import MicroProgressLog

        progress = MicroProgressLog()

        with pytest.raises(ValueError, match="Progress note is required"):
            progress.validate_note("note", "   ")


class TestMicroSchoolSchemaBoundaries:
    def test_micro_school_create_request_rejects_zero_capacity(self) -> None:
        with pytest.raises(PydanticValidationError):
            MicroSchoolCreateRequest(
                name="Micro-Ecole",
                neighborhood="Maarif",
                city="Casablanca",
                phone="+212612345678",
                max_capacity=0,
            )

    def test_micro_group_create_request_rejects_age_below_lower_bound(self) -> None:
        with pytest.raises(PydanticValidationError):
            MicroGroupCreateRequest(
                micro_school_id="10000000-0000-4000-8000-000000000001",
                name="Groupe Petit",
                age_range_min=1,
                age_range_max=3,
            )

    def test_micro_group_create_request_rejects_age_above_upper_bound(self) -> None:
        with pytest.raises(PydanticValidationError):
            MicroGroupCreateRequest(
                micro_school_id="10000000-0000-4000-8000-000000000001",
                name="Groupe Grand",
                age_range_min=3,
                age_range_max=7,
            )

    def test_micro_payment_create_request_rejects_non_positive_amount(self) -> None:
        with pytest.raises(PydanticValidationError):
            MicroPaymentCreateRequest(
                micro_school_id="10000000-0000-4000-8000-000000000001",
                parent_id="10000000-0000-4000-8000-000000000002",
                child_enrollment_id="10000000-0000-4000-8000-000000000003",
                amount=0,
                period_start="2026-04-01",
                period_end="2026-04-30",
            )

    def test_micro_progress_request_rejects_blank_note(self) -> None:
        with pytest.raises(PydanticValidationError):
            MicroProgressLogCreateRequest(
                micro_enrollment_id="10000000-0000-4000-8000-000000000001",
                date="2026-04-03",
                note="",
            )


class TestMicroSchoolServiceEdges:
    @pytest.mark.asyncio
    async def test_payment_analytics_returns_zeroes_for_empty_dataset(self) -> None:
        service = MicroPaymentService(AsyncMock())
        service.repo = AsyncMock()
        service.repo.list_micro_payments.return_value = []

        result = await service.get_payment_analytics(
            auth=type(
                "AuthStub",
                (),
                {"role": "EDUCATOR", "user_id": None, "school_id": None},
            )(),
            micro_school_id=None,
        )

        assert result == {
            "total_amount": 0.0,
            "collected_amount": 0.0,
            "overdue_amount": 0.0,
            "pending_amount": 0.0,
            "paid_count": 0,
            "overdue_count": 0,
            "pending_count": 0,
            "collection_rate": 0.0,
        }
