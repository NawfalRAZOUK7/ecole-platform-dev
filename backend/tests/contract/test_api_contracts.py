"""Contract tests for API response envelopes and key typed payloads."""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import TypeAdapter

from app.schemas.billing import FeeStructureResponse, InvoiceResponse
from app.schemas.billing.enhancements import PaymentPlanSummaryResponse
from app.schemas.school import SchoolResponse
from tests.integration.api.helpers import (
    INVOICE_ID,
    SCHOOL_ID,
    YEAR_ID,
    auth_header,
    unique_suffix,
)


class TestSchoolContracts:
    @pytest.mark.asyncio
    async def test_school_list_items_match_schema(self, client, admin_token) -> None:
        response = await client.get("/schools", headers=auth_header(admin_token))

        assert response.status_code == 200
        TypeAdapter(list[SchoolResponse]).validate_python(response.json()["data"])

    @pytest.mark.asyncio
    async def test_school_detail_matches_schema(self, client, admin_token) -> None:
        response = await client.get(
            f"/schools/{SCHOOL_ID}",
            headers=auth_header(admin_token),
        )

        assert response.status_code == 200
        TypeAdapter(SchoolResponse).validate_python(response.json()["data"])

    @pytest.mark.asyncio
    async def test_school_list_meta_contains_cursor_fields(
        self, client, admin_token
    ) -> None:
        response = await client.get(
            "/schools",
            headers=auth_header(admin_token),
            params={"limit": 1},
        )
        meta = response.json()["meta"]

        assert isinstance(meta["has_more"], bool)
        assert "next_cursor" in meta
        datetime.fromisoformat(meta["timestamp"])


class TestBillingContracts:
    @pytest.mark.asyncio
    async def test_fee_structure_list_items_match_schema(
        self, client, admin_token
    ) -> None:
        response = await client.get(
            "/billing/fee-structures",
            headers=auth_header(admin_token),
        )

        assert response.status_code == 200
        TypeAdapter(list[FeeStructureResponse]).validate_python(response.json()["data"])

    @pytest.mark.asyncio
    async def test_fee_structure_create_matches_schema(
        self, client, admin_token
    ) -> None:
        suffix = unique_suffix()
        response = await client.post(
            "/billing/fee-structures",
            headers=auth_header(admin_token),
            json={
                "academic_year_id": YEAR_ID,
                "name": f"Contrat {suffix}",
                "amount": 500.0,
                "currency": "MAD",
                "frequency": "MONTHLY",
                "due_day": 5,
                "applies_to_level": "6eme",
            },
        )

        assert response.status_code == 201
        TypeAdapter(FeeStructureResponse).validate_python(response.json()["data"])

    @pytest.mark.asyncio
    async def test_payment_plan_list_items_match_schema(
        self, client, parent_token
    ) -> None:
        response = await client.get(
            "/billing/payment-plans",
            headers=auth_header(parent_token),
        )

        assert response.status_code == 200
        TypeAdapter(list[PaymentPlanSummaryResponse]).validate_python(
            response.json()["data"]
        )

    @pytest.mark.asyncio
    async def test_invoice_detail_matches_schema(self, client, parent_token) -> None:
        response = await client.get(
            f"/invoices/{INVOICE_ID}",
            headers=auth_header(parent_token),
        )

        assert response.status_code == 200
        TypeAdapter(InvoiceResponse).validate_python(response.json()["data"])

    @pytest.mark.asyncio
    async def test_invoice_list_meta_contains_pagination_fields(
        self, client, parent_token
    ) -> None:
        response = await client.get(
            "/invoices",
            headers=auth_header(parent_token),
            params={"limit": 1},
        )
        meta = response.json()["meta"]

        assert isinstance(meta["has_more"], bool)
        assert "next_cursor" in meta
        datetime.fromisoformat(meta["timestamp"])


class TestEnvelopeContracts:
    @pytest.mark.asyncio
    async def test_success_envelope_contains_data_and_meta(
        self, client, admin_token
    ) -> None:
        response = await client.get(
            f"/schools/{SCHOOL_ID}",
            headers=auth_header(admin_token),
        )
        body = response.json()

        assert response.status_code == 200
        assert "data" in body
        assert "meta" in body
        assert body["meta"]["version"] == "0.1.0"

    @pytest.mark.asyncio
    async def test_list_envelope_contains_data_and_meta(
        self, client, parent_token
    ) -> None:
        response = await client.get(
            "/billing/payment-plans",
            headers=auth_header(parent_token),
        )
        body = response.json()

        assert response.status_code == 200
        assert isinstance(body["data"], list)
        assert "meta" in body
        assert "timestamp" in body["meta"]

    @pytest.mark.asyncio
    async def test_unauthorized_error_envelope_shape(self, client) -> None:
        response = await client.get("/schools")
        error = response.json()["error"]

        assert response.status_code == 401
        for field in (
            "code",
            "message",
            "category",
            "correlation_id",
            "retryable",
            "timestamp",
        ):
            assert field in error
        datetime.fromisoformat(error["timestamp"])

    @pytest.mark.asyncio
    async def test_forbidden_error_envelope_shape(self, client, student_token) -> None:
        response = await client.get(
            "/billing/payment-plans",
            headers=auth_header(student_token),
        )
        error = response.json()["error"]

        assert response.status_code == 403
        assert error["category"] == "authz"
        assert error["retryable"] is False

    @pytest.mark.asyncio
    async def test_error_codes_follow_err_prefix(self, client) -> None:
        response = await client.get("/schools")

        assert response.json()["error"]["code"].startswith("ERR-")
