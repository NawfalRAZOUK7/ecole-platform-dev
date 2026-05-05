"""Integration tests for POST /invoices/{id}/pdf endpoint."""

from __future__ import annotations

import uuid

import pytest

from .helpers import INVOICE_ID, auth_header


class TestInvoicePdfApi:
    @pytest.mark.asyncio
    async def test_admin_can_request_invoice_pdf_fr(self, client, admin_token):
        response = await client.post(
            f"/invoices/{INVOICE_ID}/pdf",
            headers=auth_header(admin_token),
            params={"language": "fr"},
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert "id" in data
        assert data["type"] == "invoice_pdf"
        assert data["status"] in ("pending", "processing", "ready")

    @pytest.mark.asyncio
    async def test_admin_can_request_invoice_pdf_ar(self, client, admin_token):
        response = await client.post(
            f"/invoices/{INVOICE_ID}/pdf",
            headers=auth_header(admin_token),
            params={"language": "ar"},
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["type"] == "invoice_pdf"

    @pytest.mark.asyncio
    async def test_parent_can_request_own_invoice_pdf(self, client, parent_token):
        # The seeded parent owns INVOICE_ID
        response = await client.post(
            f"/invoices/{INVOICE_ID}/pdf",
            headers=auth_header(parent_token),
            params={"language": "fr"},
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["type"] == "invoice_pdf"

    @pytest.mark.asyncio
    async def test_student_cannot_request_invoice_pdf(self, client, student_token):
        response = await client.post(
            f"/invoices/{INVOICE_ID}/pdf",
            headers=auth_header(student_token),
            params={"language": "fr"},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_nonexistent_invoice_returns_404(self, client, admin_token):
        fake_id = uuid.uuid4()
        response = await client.post(
            f"/invoices/{fake_id}/pdf",
            headers=auth_header(admin_token),
            params={"language": "fr"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_language_returns_422(self, client, admin_token):
        response = await client.post(
            f"/invoices/{INVOICE_ID}/pdf",
            headers=auth_header(admin_token),
            params={"language": "de"},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_unauthenticated_request_returns_401(self, client):
        response = await client.post(
            f"/invoices/{INVOICE_ID}/pdf",
            params={"language": "fr"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_response_contains_job_id(self, client, admin_token):
        response = await client.post(
            f"/invoices/{INVOICE_ID}/pdf",
            headers=auth_header(admin_token),
            params={"language": "fr"},
        )

        assert response.status_code == 201
        data = response.json()["data"]
        # id must be a valid UUID string
        uuid.UUID(data["id"])
