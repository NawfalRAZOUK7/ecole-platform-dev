"""Billing enhancement schemas for policies, late fees, and payment plans."""

from __future__ import annotations

import uuid

from app.schemas.billing import FeeStructureCreateRequest, FeeStructureResponse
from pydantic import BaseModel, Field


class SiblingDiscountPolicyUpdateRequest(BaseModel):
    enabled: bool = True
    second_child_percent: float = Field(10.0, ge=0, le=100)
    third_child_percent: float = Field(20.0, ge=0, le=100)
    fourth_plus_percent: float = Field(30.0, ge=0, le=100)
    apply_to_oldest_first: bool = True


class SiblingDiscountPolicyResponse(BaseModel):
    id: str | None = None
    school_id: str
    enabled: bool
    second_child_percent: float
    third_child_percent: float
    fourth_plus_percent: float
    apply_to_oldest_first: bool
    created_at: str | None = None
    updated_at: str | None = None


class LateFeePolicyUpdateRequest(BaseModel):
    enabled: bool = False
    fee_type: str = Field("fixed", pattern="^(fixed|percent)$")
    amount: float = Field(0.0, ge=0)
    frequency: str = Field("once", pattern="^(once|daily|weekly)$")
    grace_days: int = Field(5, ge=0)
    max_fee: float | None = Field(None, ge=0)


class LateFeePolicyResponse(BaseModel):
    id: str | None = None
    school_id: str
    enabled: bool
    fee_type: str
    amount: float
    frequency: str
    grace_days: int
    max_fee: float | None = None
    created_at: str | None = None
    updated_at: str | None = None


class PaymentPlanCreateRequest(BaseModel):
    invoice_id: uuid.UUID
    num_installments: int = Field(..., ge=1, le=24)


class InstallmentResponse(BaseModel):
    id: str
    plan_id: str
    installment_number: int
    amount: float
    due_date: str
    paid_at: str | None = None
    status: str


class PaymentPlanSummaryResponse(BaseModel):
    id: str
    invoice_id: str
    school_id: str
    parent_id: str
    total_installments: int
    status: str
    currency: str
    invoice_total_amount: float
    issued_date: str
    due_date: str
    created_at: str
    updated_at: str | None = None
    installments_paid: int = 0
    installments_pending: int = 0


class PaymentPlanDetailResponse(PaymentPlanSummaryResponse):
    installments: list[InstallmentResponse] = Field(default_factory=list)
