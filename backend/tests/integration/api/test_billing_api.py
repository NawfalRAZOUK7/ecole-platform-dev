"""Integration tests for billing endpoints."""

from __future__ import annotations

import pytest

from .helpers import YEAR_ID, auth_header, unique_suffix


class TestBillingApi:
    @pytest.mark.asyncio
    async def test_admin_can_list_fee_structures(self, client, admin_token):
        response = await client.get(
            "/billing/fee-structures",
            headers=auth_header(admin_token),
        )

        assert response.status_code == 200
        assert isinstance(response.json()["data"], list)

    @pytest.mark.asyncio
    async def test_admin_can_create_fee_structure(self, client, admin_token):
        suffix = unique_suffix()
        response = await client.post(
            "/billing/fee-structures",
            headers=auth_header(admin_token),
            json={
                "academic_year_id": YEAR_ID,
                "name": f"Scolarite {suffix}",
                "amount": 500.0,
                "currency": "MAD",
                "frequency": "MONTHLY",
                "due_day": 5,
                "applies_to_level": "6eme",
            },
        )

        assert response.status_code == 201
        payload = response.json()["data"]
        assert payload["currency"] == "MAD"
        assert payload["name"].startswith("Scolarite")

    @pytest.mark.asyncio
    async def test_admin_can_get_sibling_policy(self, client, admin_token):
        response = await client.get(
            "/billing/sibling-policy",
            headers=auth_header(admin_token),
        )

        assert response.status_code == 200
        assert "enabled" in response.json()["data"]

    @pytest.mark.asyncio
    async def test_parent_can_list_payment_plans(self, client, parent_token):
        response = await client.get(
            "/billing/payment-plans",
            headers=auth_header(parent_token),
        )

        assert response.status_code == 200
        assert isinstance(response.json()["data"], list)

    @pytest.mark.asyncio
    async def test_student_cannot_list_payment_plans(self, client, student_token):
        response = await client.get(
            "/billing/payment-plans",
            headers=auth_header(student_token),
        )

        assert response.status_code == 403
