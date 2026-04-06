"""Pydantic schemas for financial health workflows."""

from __future__ import annotations

import uuid
from datetime import date as date_type

from pydantic import BaseModel, Field


class RetentionComputeRequest(BaseModel):
    """Payload for computing a retention metric."""

    academic_year_from: str = Field(..., min_length=1, max_length=10)
    academic_year_to: str = Field(..., min_length=1, max_length=10)


class RetentionMetricResponse(BaseModel):
    """Serialized retention metric response."""

    id: str
    school_id: str
    academic_year_from: str
    academic_year_to: str
    total_students_start: int
    total_students_end: int
    retained: int
    new_enrollments: int
    withdrawals: int
    retention_rate: float
    computed_at: str
    created_at: str
    updated_at: str | None = None


class CashflowForecastComputeRequest(BaseModel):
    """Payload for computing cashflow forecasts."""

    months_ahead: int = Field(6, ge=1, le=24)


class CashflowForecastResponse(BaseModel):
    """Serialized cashflow forecast response."""

    id: str
    school_id: str
    forecast_month: date_type
    expected_income: float
    expected_expenses: float
    actual_income: float | None = None
    actual_expenses: float | None = None
    currency: str
    confidence_score: float
    computed_at: str
    created_at: str
    updated_at: str | None = None


class CostPerStudentComputeRequest(BaseModel):
    """Payload for computing cost-per-student analysis."""

    academic_year_id: uuid.UUID


class CostPerStudentResponse(BaseModel):
    """Serialized cost-per-student response."""

    id: str
    school_id: str
    academic_year_id: str
    total_operational_cost: float
    total_students: int
    cost_per_student: float
    revenue_per_student: float
    margin_per_student: float
    currency: str
    computed_at: str
    created_at: str
    updated_at: str | None = None


class FinancialSnapshotComputeRequest(BaseModel):
    """Payload for computing a financial snapshot."""

    snapshot_date: date_type | None = None


class FinancialSnapshotResponse(BaseModel):
    """Serialized financial snapshot response."""

    id: str
    school_id: str
    snapshot_date: date_type
    total_receivable: float
    total_collected: float
    collection_rate: float
    overdue_amount: float
    overdue_count: int
    avg_payment_delay_days: float | None = None
    currency: str
    computed_at: str
    created_at: str
    updated_at: str | None = None


__all__ = [
    "RetentionComputeRequest",
    "RetentionMetricResponse",
    "CashflowForecastComputeRequest",
    "CashflowForecastResponse",
    "CostPerStudentComputeRequest",
    "CostPerStudentResponse",
    "FinancialSnapshotComputeRequest",
    "FinancialSnapshotResponse",
]
