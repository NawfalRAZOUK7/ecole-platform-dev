"""Extended integration tests for billing endpoints (Phase 4.B).

Coverage target: app/api/v1/billing/billing.py ≥ 95 % branch

Routes covered (all in billing.py with prefix /billing):
  POST/GET/PUT /billing/fee-structures
  POST /billing/fee-assignments (single + bulk)
  GET  /billing/fee-assignments
  POST /billing/generate-invoices
  GET/PUT /billing/sibling-policy
  GET/PUT /billing/late-fee-policy
  POST/GET /billing/payment-plans
  GET /billing/payment-plans/{id}

Invoice routes (separate router prefix /invoices):
  GET /invoices
  GET /invoices/{id}
  POST /invoices/{id}/void
"""

from __future__ import annotations

import uuid

import pytest

from tests.integration.api.helpers import (
    INVOICE_ID,
    PERIOD_ID,
    SCHOOL_ID,
    STUDENT_ID,
    YEAR_ID,
    auth_header,
    login_token,
    unique_suffix,
)

ADMIN_EMAIL = "admin@ecole-benani.ma"
ADMIN_PASSWORD = "admin123"
TEACHER_EMAIL = "prof.math@ecole-benani.ma"
TEACHER_PASSWORD = "teacher123"
STUDENT_EMAIL = "yassine.alaoui@ecole-benani.ma"
STUDENT_PASSWORD = "student123"
PARENT_EMAIL = "parent.alaoui@gmail.com"
PARENT_PASSWORD = "parent123"

PARENT_ID = "10000000-0000-4000-8000-000000000005"


def _fee_structure_payload(**overrides) -> dict:
    return {
        "academic_year_id": YEAR_ID,
        "name": f"Scolarite-{unique_suffix()}",
        "amount": 1500.0,
        "currency": "MAD",
        "frequency": "MONTHLY",
        "due_day": 5,
        "applies_to_level": "6eme",
        **overrides,
    }


class TestFeeStructureExtended:
    async def _create_fee_structure(self, client, token) -> str:
        r = await client.post(
            "/billing/fee-structures",
            headers=auth_header(token),
            json=_fee_structure_payload(),
        )
        assert r.status_code == 201
        return r.json()["data"]["id"]

    @pytest.mark.asyncio
    async def test_create_fee_structure_missing_name_returns_422(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        payload = _fee_structure_payload()
        del payload["name"]
        response = await client.post(
            "/billing/fee-structures", headers=auth_header(token), json=payload
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_fee_structure_invalid_frequency_returns_422(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.post(
            "/billing/fee-structures",
            headers=auth_header(token),
            json=_fee_structure_payload(frequency="WEEKLY"),
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_teacher_cannot_create_fee_structure(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD)
        response = await client.post(
            "/billing/fee-structures",
            headers=auth_header(token),
            json=_fee_structure_payload(),
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_student_cannot_create_fee_structure(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD)
        response = await client.post(
            "/billing/fee-structures",
            headers=auth_header(token),
            json=_fee_structure_payload(),
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_list_fee_structures_with_filters(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.get(
            "/billing/fee-structures",
            headers=auth_header(token),
            params={"academic_year_id": YEAR_ID, "status": "ACTIVE"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_fee_structures_invalid_status_422(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.get(
            "/billing/fee-structures",
            headers=auth_header(token),
            params={"status": "INVALID"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_admin_can_update_fee_structure(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        fs_id = await self._create_fee_structure(client, token)
        response = await client.put(
            f"/billing/fee-structures/{fs_id}",
            headers=auth_header(token),
            json={"name": f"Updated-{unique_suffix()}", "amount": 2000.0},
        )
        assert response.status_code == 200
        assert response.json()["data"]["amount"] == 2000.0

    @pytest.mark.asyncio
    async def test_update_nonexistent_fee_structure_returns_404(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.put(
            f"/billing/fee-structures/{uuid.uuid4()}",
            headers=auth_header(token),
            json={"name": "Updated"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_teacher_cannot_update_fee_structure(self, client, legacy_api_seed):
        _ = legacy_api_seed
        a_token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        fs_id = await self._create_fee_structure(client, a_token)
        t_token = await login_token(client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD)
        response = await client.put(
            f"/billing/fee-structures/{fs_id}",
            headers=auth_header(t_token),
            json={"name": "Hack"},
        )
        assert response.status_code == 403


class TestFeeAssignments:
    async def _create_fee_structure_id(self, client, token) -> str:
        r = await client.post(
            "/billing/fee-structures",
            headers=auth_header(token),
            json=_fee_structure_payload(),
        )
        assert r.status_code == 201
        return r.json()["data"]["id"]

    @pytest.mark.asyncio
    async def test_admin_can_assign_fee_to_student(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        fs_id = await self._create_fee_structure_id(client, token)
        response = await client.post(
            "/billing/fee-assignments",
            headers=auth_header(token),
            json={"fee_structure_id": fs_id, "student_id": STUDENT_ID},
        )
        # 201 on success, 409 if already assigned
        assert response.status_code in (201, 409)

    @pytest.mark.asyncio
    async def test_teacher_cannot_create_fee_assignment(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD)
        response = await client.post(
            "/billing/fee-assignments",
            headers=auth_header(token),
            json={"fee_structure_id": str(uuid.uuid4()), "student_id": STUDENT_ID},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_missing_fee_structure_id_returns_422(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.post(
            "/billing/fee-assignments",
            headers=auth_header(token),
            json={"student_id": STUDENT_ID},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_admin_can_bulk_assign_fee_to_class(self, client, legacy_api_seed):
        _ = legacy_api_seed
        from tests.integration.api.helpers import CLASS_ID
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        fs_id = await self._create_fee_structure_id(client, token)
        response = await client.post(
            "/billing/fee-assignments/bulk",
            headers=auth_header(token),
            json={"fee_structure_id": fs_id, "class_id": CLASS_ID},
        )
        assert response.status_code in (201, 200, 409)

    @pytest.mark.asyncio
    async def test_teacher_cannot_bulk_assign(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD)
        response = await client.post(
            "/billing/fee-assignments/bulk",
            headers=auth_header(token),
            json={"fee_structure_id": str(uuid.uuid4()), "class_id": str(uuid.uuid4())},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_can_list_fee_assignments(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.get(
            "/billing/fee-assignments", headers=auth_header(token)
        )
        assert response.status_code == 200
        assert isinstance(response.json()["data"], list)

    @pytest.mark.asyncio
    async def test_teacher_cannot_list_fee_assignments(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD)
        response = await client.get(
            "/billing/fee-assignments", headers=auth_header(token)
        )
        assert response.status_code == 403


class TestGenerateInvoices:
    async def _create_fee_structure_id(self, client, token) -> str:
        r = await client.post(
            "/billing/fee-structures",
            headers=auth_header(token),
            json=_fee_structure_payload(),
        )
        assert r.status_code == 201
        return r.json()["data"]["id"]

    @pytest.mark.asyncio
    async def test_admin_can_generate_invoices(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        fs_id = await self._create_fee_structure_id(client, token)
        response = await client.post(
            "/billing/generate-invoices",
            headers=auth_header(token),
            json={
                "fee_structure_id": fs_id,
                "period_id": PERIOD_ID,
                "issued_date": "2026-02-01",
                "due_date": "2026-02-28",
            },
        )
        # 201 on success, 409 if invoices already exist,
        # 422 if no fee assignments exist for this fee structure
        assert response.status_code in (201, 409, 422)

    @pytest.mark.asyncio
    async def test_teacher_cannot_generate_invoices(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD)
        response = await client.post(
            "/billing/generate-invoices",
            headers=auth_header(token),
            json={
                "fee_structure_id": str(uuid.uuid4()),
                "issued_date": "2026-02-01",
            },
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_missing_issued_date_returns_422(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.post(
            "/billing/generate-invoices",
            headers=auth_header(token),
            json={"fee_structure_id": str(uuid.uuid4())},
        )
        assert response.status_code == 422


class TestSiblingPolicyExtended:
    @pytest.mark.asyncio
    async def test_admin_can_get_sibling_policy(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.get("/billing/sibling-policy", headers=auth_header(token))
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_admin_can_update_sibling_policy(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.put(
            "/billing/sibling-policy",
            headers=auth_header(token),
            json={
                "enabled": True,
                "second_child_percent": 10.0,
                "third_child_percent": 20.0,
                "fourth_plus_percent": 30.0,
                "apply_to_oldest_first": True,
            },
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_teacher_cannot_access_sibling_policy(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD)
        response = await client.get(
            "/billing/sibling-policy", headers=auth_header(token)
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_student_cannot_update_sibling_policy(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD)
        response = await client.put(
            "/billing/sibling-policy",
            headers=auth_header(token),
            json={"enabled": False},
        )
        assert response.status_code == 403


class TestLateFeePolicy:
    @pytest.mark.asyncio
    async def test_admin_can_get_late_fee_policy(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.get(
            "/billing/late-fee-policy", headers=auth_header(token)
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_admin_can_update_late_fee_policy(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.put(
            "/billing/late-fee-policy",
            headers=auth_header(token),
            json={
                "enabled": True,
                "fee_type": "percent",
                "amount": 5.0,
                "frequency": "daily",
                "grace_days": 7,
            },
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_teacher_cannot_access_late_fee_policy(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD)
        response = await client.get(
            "/billing/late-fee-policy", headers=auth_header(token)
        )
        assert response.status_code == 403


class TestPaymentPlansExtended:
    @pytest.mark.asyncio
    async def test_admin_can_create_payment_plan(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.post(
            "/billing/payment-plans",
            headers=auth_header(token),
            json={
                "invoice_id": INVOICE_ID,
                "num_installments": 3,
            },
        )
        # 201 on success, 409 if plan already exists for this invoice
        assert response.status_code in (201, 409)

    @pytest.mark.asyncio
    async def test_missing_invoice_id_returns_422(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.post(
            "/billing/payment-plans",
            headers=auth_header(token),
            json={"num_installments": 3},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_student_cannot_create_payment_plan(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD)
        response = await client.post(
            "/billing/payment-plans",
            headers=auth_header(token),
            json={"invoice_id": INVOICE_ID, "num_installments": 3},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_parent_can_list_payment_plans(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=PARENT_EMAIL, password=PARENT_PASSWORD)
        response = await client.get(
            "/billing/payment-plans", headers=auth_header(token)
        )
        assert response.status_code == 200
        assert isinstance(response.json()["data"], list)

    @pytest.mark.asyncio
    async def test_student_cannot_list_payment_plans(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD)
        response = await client.get(
            "/billing/payment-plans", headers=auth_header(token)
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_nonexistent_plan_returns_404(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.get(
            f"/billing/payment-plans/{uuid.uuid4()}", headers=auth_header(token)
        )
        assert response.status_code == 404


class TestInvoicesExtended:
    @pytest.mark.asyncio
    async def test_parent_can_list_own_invoices(self, client, legacy_api_seed):
        """Invoice router has prefix /invoices (not /billing/invoices)."""
        _ = legacy_api_seed
        token = await login_token(client, email=PARENT_EMAIL, password=PARENT_PASSWORD)
        response = await client.get("/invoices", headers=auth_header(token))
        assert response.status_code == 200
        assert isinstance(response.json()["data"], list)

    @pytest.mark.asyncio
    async def test_student_cannot_list_invoices(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD)
        response = await client.get("/invoices", headers=auth_header(token))
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_can_get_invoice_by_id(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.get(
            f"/invoices/{INVOICE_ID}", headers=auth_header(token)
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_nonexistent_invoice_returns_404(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.get(
            f"/invoices/{uuid.uuid4()}", headers=auth_header(token)
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_uuid_invoice_returns_422(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.get(
            "/invoices/not-a-uuid", headers=auth_header(token)
        )
        assert response.status_code == 422
