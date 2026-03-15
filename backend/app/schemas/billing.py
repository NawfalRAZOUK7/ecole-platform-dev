"""Billing domain Pydantic schemas — request/response models.

Reference: Pack D5 — API Implementation Plan, Sprint 3 stories S-061 to S-064
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Invoice (S-061)
# ---------------------------------------------------------------------------
class InvoiceItemResponse(BaseModel):
    id: str
    description: str
    amount: float
    unit_price: float
    quantity: int


class InvoiceResponse(BaseModel):
    id: str
    school_id: str
    parent_id: str
    period_id: str | None = None
    status: str
    total_amount: float
    currency: str
    issued_date: str
    due_date: str
    items: list[InvoiceItemResponse] = []


# ---------------------------------------------------------------------------
# Payment (S-062, S-063)
# ---------------------------------------------------------------------------
class PaymentInitiateRequest(BaseModel):
    invoice_id: uuid.UUID
    idempotency_key: str = Field(..., min_length=1, max_length=255)


class PaymentAttemptResponse(BaseModel):
    id: str
    invoice_id: str
    parent_id: str
    school_id: str
    idempotency_key: str
    status: str
    finalized_at: str | None = None


# ---------------------------------------------------------------------------
# Webhook (S-064)
# ---------------------------------------------------------------------------
class WebhookEventRequest(BaseModel):
    provider_event_id: str = Field(..., min_length=1, max_length=255)
    payment_attempt_id: uuid.UUID | None = None
    event_type: str = Field(..., min_length=1, max_length=50)
    status: str = Field(..., pattern="^(paid|failed|canceled)$")
    signature: str | None = None


class WebhookEventResponse(BaseModel):
    id: str
    provider_event_id: str
    payment_attempt_id: str | None = None
    school_id: str
    status: str
    signature_status: str | None = None
