"""Pydantic schemas for class micro-budget workflows."""

from __future__ import annotations

import uuid
from datetime import datetime as datetime_type

from pydantic import BaseModel, Field


class MicroBudgetCreateRequest(BaseModel):
    academic_year_id: uuid.UUID
    total_amount: float = Field(..., ge=0)
    currency: str = Field("MAD", pattern="^MAD$")
    status: str = Field("active", pattern="^(active|frozen|closed)$")


class MicroBudgetUpdateRequest(BaseModel):
    total_amount: float | None = Field(None, ge=0)
    currency: str | None = Field(None, pattern="^MAD$")
    status: str | None = Field(None, pattern="^(active|frozen|closed)$")


class MicroBudgetResponse(BaseModel):
    id: str
    school_id: str
    academic_year_id: str
    total_amount: float
    allocated_amount: float
    remaining_amount: float
    currency: str
    status: str
    created_by: str
    created_at: str
    updated_at: str | None = None


class BudgetAllocationCreateRequest(BaseModel):
    class_id: uuid.UUID | None = None
    teacher_id: uuid.UUID | None = None
    label: str = Field(..., min_length=1, max_length=200)
    amount: float = Field(..., gt=0)
    currency: str = Field("MAD", pattern="^MAD$")
    status: str = Field("active", pattern="^(active|exhausted|frozen)$")


class BudgetAllocationUpdateRequest(BaseModel):
    class_id: uuid.UUID | None = None
    teacher_id: uuid.UUID | None = None
    label: str | None = Field(None, min_length=1, max_length=200)
    amount: float | None = Field(None, gt=0)
    currency: str | None = Field(None, pattern="^MAD$")
    status: str | None = Field(None, pattern="^(active|exhausted|frozen)$")


class BudgetAllocationResponse(BaseModel):
    id: str
    budget_id: str
    class_id: str | None = None
    teacher_id: str | None = None
    label: str
    amount: float
    spent: float
    remaining: float
    currency: str
    allocated_by: str
    allocated_at: str
    status: str
    created_at: str
    updated_at: str | None = None


class BudgetRequestCreateRequest(BaseModel):
    amount: float = Field(..., gt=0)
    currency: str = Field("MAD", pattern="^MAD$")
    description: str = Field(..., min_length=1, max_length=4000)
    justification: str | None = Field(None, max_length=4000)


class BudgetRequestUpdateRequest(BaseModel):
    amount: float | None = Field(None, gt=0)
    currency: str | None = Field(None, pattern="^MAD$")
    description: str | None = Field(None, min_length=1, max_length=4000)
    justification: str | None = Field(None, max_length=4000)
    status: str | None = Field(None, pattern="^(pending|approved|rejected|cancelled)$")


class BudgetRequestReviewRequest(BaseModel):
    review_comment: str | None = Field(None, max_length=4000)


class BudgetRequestResponse(BaseModel):
    id: str
    allocation_id: str
    requester_id: str
    amount: float
    currency: str
    description: str
    justification: str | None = None
    status: str
    reviewed_by: str | None = None
    reviewed_at: str | None = None
    review_comment: str | None = None
    created_at: str
    updated_at: str | None = None


class BudgetTransactionCreateRequest(BaseModel):
    request_id: uuid.UUID | None = None
    amount: float = Field(..., gt=0)
    transaction_type: str = Field(
        ...,
        pattern="^(allocation|expense|refund|adjustment)$",
    )
    description: str = Field(..., min_length=1, max_length=300)
    receipt_url: str | None = Field(None, max_length=500)


class BudgetTransactionUpdateRequest(BaseModel):
    description: str | None = Field(None, min_length=1, max_length=300)
    receipt_url: str | None = Field(None, max_length=500)


class BudgetTransactionResponse(BaseModel):
    id: str
    allocation_id: str
    request_id: str | None = None
    amount: float
    transaction_type: str
    description: str
    receipt_url: str | None = None
    recorded_by: str
    recorded_at: str
    created_at: str
    updated_at: str | None = None


class BudgetAnalyticsResponse(BaseModel):
    school_id: str
    academic_year_id: str | None = None
    budget_count: int
    allocation_count: int
    request_count: int
    transaction_count: int
    total_budget_amount: float
    total_allocated_amount: float
    total_remaining_unallocated: float
    total_spent_amount: float
    total_allocation_remaining: float
    pending_request_amount: float
    approved_request_amount: float
    utilization_rate: float


__all__ = [
    "MicroBudgetCreateRequest",
    "MicroBudgetUpdateRequest",
    "MicroBudgetResponse",
    "BudgetAllocationCreateRequest",
    "BudgetAllocationUpdateRequest",
    "BudgetAllocationResponse",
    "BudgetRequestCreateRequest",
    "BudgetRequestUpdateRequest",
    "BudgetRequestReviewRequest",
    "BudgetRequestResponse",
    "BudgetTransactionCreateRequest",
    "BudgetTransactionUpdateRequest",
    "BudgetTransactionResponse",
    "BudgetAnalyticsResponse",
]
