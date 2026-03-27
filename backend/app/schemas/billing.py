"""Billing domain Pydantic schemas — request/response models.

Reference: Pack D5 — API Implementation Plan, Sprint 3 stories S-061 to S-064
Phase 11B: Added fee structure, fee assignment, and invoice generation schemas.
"""

from __future__ import annotations

import uuid
from datetime import date

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


# ---------------------------------------------------------------------------
# Fee Structure (Phase 11B)
# ---------------------------------------------------------------------------
class FeeStructureCreateRequest(BaseModel):
    academic_year_id: uuid.UUID
    name: str = Field(..., min_length=1, max_length=200)
    amount: float = Field(..., gt=0)
    currency: str = Field("MAD", max_length=3)
    frequency: str = Field(..., pattern="^(MONTHLY|TRIMESTRIAL|ANNUAL|ONE_TIME)$")
    due_day: int = Field(..., ge=1, le=28, description="Day of month when fee is due")
    applies_to_level: str | None = Field(None, max_length=50)


class FeeStructureUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    amount: float | None = Field(None, gt=0)
    currency: str | None = Field(None, max_length=3)
    frequency: str | None = Field(
        None, pattern="^(MONTHLY|TRIMESTRIAL|ANNUAL|ONE_TIME)$"
    )
    due_day: int | None = Field(None, ge=1, le=28)
    applies_to_level: str | None = Field(None, max_length=50)
    status: str | None = Field(None, pattern="^(ACTIVE|ARCHIVED)$")


class FeeStructureResponse(BaseModel):
    id: str
    school_id: str
    academic_year_id: str
    name: str
    amount: float
    currency: str
    frequency: str
    due_day: int
    applies_to_level: str | None = None
    status: str
    created_at: str
    updated_at: str | None = None


# ---------------------------------------------------------------------------
# Fee Assignment (Phase 11B)
# ---------------------------------------------------------------------------
class FeeAssignmentCreateRequest(BaseModel):
    fee_structure_id: uuid.UUID
    student_id: uuid.UUID
    discount_percent: float | None = Field(None, ge=0, le=100)
    discount_reason: str | None = Field(None, max_length=2000)


class FeeAssignmentBulkCreateRequest(BaseModel):
    """Bulk assign a fee to all students in a class or level."""

    fee_structure_id: uuid.UUID
    class_id: uuid.UUID | None = None
    level: str | None = Field(None, max_length=50)
    discount_percent: float | None = Field(None, ge=0, le=100)
    discount_reason: str | None = Field(None, max_length=2000)


class FeeAssignmentResponse(BaseModel):
    id: str
    fee_structure_id: str
    student_id: str
    school_id: str
    discount_percent: float | None = None
    discount_reason: str | None = None
    status: str
    created_at: str


# ---------------------------------------------------------------------------
# Invoice Generation (Phase 11B)
# ---------------------------------------------------------------------------
class InvoiceGenerateRequest(BaseModel):
    """Generate invoices from fee structures for a period."""

    fee_structure_id: uuid.UUID
    period_id: uuid.UUID | None = None
    issued_date: date
    due_date: date
