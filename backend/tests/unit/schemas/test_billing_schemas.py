"""Unit tests for Billing Pydantic schemas.

Validates invoice, payment, fee structure, and webhook schemas.
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.billing import (
    InvoiceItemResponse,
    InvoiceResponse,
    PaymentInitiateRequest,
    PaymentAttemptResponse,
    WebhookEventRequest,
)
from app.schemas.billing_enhancements import (
    FeeStructureCreateRequest,
    FeeStructureResponse,
)


# ---------------------------------------------------------------------------
# Invoice schemas
# ---------------------------------------------------------------------------
class TestInvoiceSchemas:
    """Tests for invoice request/response schemas."""

    def test_invoice_item_response(self) -> None:
        item = InvoiceItemResponse(
            id="item-1",
            description="Tuition Fee",
            amount=1500.0,
            unit_price=1500.0,
            quantity=1,
        )
        assert item.quantity == 1

    def test_invoice_response_defaults(self) -> None:
        inv = InvoiceResponse(
            id="inv-1",
            school_id="sch-1",
            parent_id="par-1",
            status="pending",
            total_amount=1500.0,
            currency="MAD",
            issued_date="2024-09-01",
            due_date="2024-09-15",
        )
        assert inv.items == []
        assert inv.period_id is None

    def test_invoice_response_with_items(self) -> None:
        item = InvoiceItemResponse(
            id="item-1", description="Fee", amount=500.0, unit_price=500.0, quantity=1
        )
        inv = InvoiceResponse(
            id="inv-1",
            school_id="sch-1",
            parent_id="par-1",
            status="paid",
            total_amount=500.0,
            currency="MAD",
            issued_date="2024-09-01",
            due_date="2024-09-15",
            items=[item],
        )
        assert len(inv.items) == 1


# ---------------------------------------------------------------------------
# Payment schemas
# ---------------------------------------------------------------------------
class TestPaymentSchemas:
    """Tests for payment initiation and attempt schemas."""

    def test_payment_initiate_request(self) -> None:
        req = PaymentInitiateRequest(
            invoice_id=uuid.uuid4(),
            idempotency_key="key-123",
        )
        assert req.idempotency_key == "key-123"

    def test_payment_initiate_missing_idempotency_key(self) -> None:
        with pytest.raises(ValidationError):
            PaymentInitiateRequest(invoice_id=uuid.uuid4())

    def test_payment_initiate_idempotency_key_too_long(self) -> None:
        with pytest.raises(ValidationError):
            PaymentInitiateRequest(
                invoice_id=uuid.uuid4(),
                idempotency_key="x" * 300,
            )

    def test_payment_attempt_response(self) -> None:
        resp = PaymentAttemptResponse(
            id="pay-1",
            invoice_id="inv-1",
            parent_id="par-1",
            school_id="sch-1",
            idempotency_key="key-1",
            status="pending",
        )
        assert resp.finalized_at is None


# ---------------------------------------------------------------------------
# Webhook schemas
# ---------------------------------------------------------------------------
class TestWebhookSchemas:
    """Tests for webhook event schema."""

    def test_webhook_event_request(self) -> None:
        req = WebhookEventRequest(
            event_type="invoice.paid",
            payload={"invoice_id": "inv-1"},
            signature="sha256=abc123",
        )
        assert req.event_type == "invoice.paid"


# ---------------------------------------------------------------------------
# Fee structure schemas
# ---------------------------------------------------------------------------
class TestFeeStructureSchemas:
    """Tests for fee structure creation and response schemas."""

    def test_fee_structure_create_request(self) -> None:
        req = FeeStructureCreateRequest(
            school_id=uuid.uuid4(),
            name="Standard Tuition",
            amount=1500.0,
            currency="MAD",
            frequency="monthly",
            academic_year="2024-2025",
        )
        assert req.frequency == "monthly"

    def test_fee_structure_response(self) -> None:
        resp = FeeStructureResponse(
            id="fee-1",
            school_id="sch-1",
            name="Standard Tuition",
            amount=1500.0,
            currency="MAD",
            frequency="monthly",
            academic_year="2024-2025",
            created_at=date.today(),
        )
        assert resp.name == "Standard Tuition"
