"""Integration tests for POST /payments/{id}/receipt endpoint."""

from __future__ import annotations

import uuid

import pytest

from .helpers import INVOICE_ID, auth_header


async def _create_payment(client, parent_token: str) -> str:
    """Create a payment attempt for the seeded invoice and return its ID."""
    response = await client.post(
        "/payments/initiate",
        headers=auth_header(parent_token),
        json={
            "invoice_id": INVOICE_ID,
            "amount": 100.0,
            "method": "card",
            "idempotency_key": str(uuid.uuid4()),
        },
    )
    assert response.status_code in (201, 200), response.text
    return response.json()["data"]["id"]


class TestPaymentReceiptApi:
    @pytest.mark.asyncio
    async def test_admin_can_request_receipt_fr(self, client, admin_token, parent_token):
        payment_id = await _create_payment(client, parent_token)

        response = await client.post(
            f"/payments/{payment_id}/receipt",
            headers=auth_header(admin_token),
            params={"language": "fr"},
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert "id" in data
        assert data["type"] == "payment_receipt"
        assert data["status"] in ("pending", "processing", "ready")

    @pytest.mark.asyncio
    async def test_admin_can_request_receipt_ar(self, client, admin_token, parent_token):
        payment_id = await _create_payment(client, parent_token)

        response = await client.post(
            f"/payments/{payment_id}/receipt",
            headers=auth_header(admin_token),
            params={"language": "ar"},
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["type"] == "payment_receipt"

    @pytest.mark.asyncio
    async def test_parent_can_request_own_receipt(self, client, parent_token):
        payment_id = await _create_payment(client, parent_token)

        response = await client.post(
            f"/payments/{payment_id}/receipt",
            headers=auth_header(parent_token),
            params={"language": "fr"},
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["type"] == "payment_receipt"

    @pytest.mark.asyncio
    async def test_student_cannot_request_receipt(self, client, student_token, parent_token):
        payment_id = await _create_payment(client, parent_token)

        response = await client.post(
            f"/payments/{payment_id}/receipt",
            headers=auth_header(student_token),
            params={"language": "fr"},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_nonexistent_payment_returns_404(self, client, admin_token):
        fake_id = uuid.uuid4()
        response = await client.post(
            f"/payments/{fake_id}/receipt",
            headers=auth_header(admin_token),
            params={"language": "fr"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_language_returns_422(self, client, admin_token, parent_token):
        payment_id = await _create_payment(client, parent_token)

        response = await client.post(
            f"/payments/{payment_id}/receipt",
            headers=auth_header(admin_token),
            params={"language": "es"},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_unauthenticated_request_returns_401(self, client, parent_token):
        payment_id = await _create_payment(client, parent_token)

        response = await client.post(
            f"/payments/{payment_id}/receipt",
            params={"language": "fr"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_response_contains_job_id(self, client, admin_token, parent_token):
        payment_id = await _create_payment(client, parent_token)

        response = await client.post(
            f"/payments/{payment_id}/receipt",
            headers=auth_header(admin_token),
            params={"language": "fr"},
        )

        assert response.status_code == 201
        data = response.json()["data"]
        uuid.UUID(data["id"])
