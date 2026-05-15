"""AI & Analytics domain Pydantic schemas — request/response models.

Reference: S-142 to S-146, Pack G3 — AI Governance
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Writing Assistance (S-143)
# ---------------------------------------------------------------------------
class WritingAttemptRequest(BaseModel):
    """POST /writing-attempts — student writing assistance request."""

    text: str = Field(..., min_length=1, max_length=5000)
    subject: str | None = Field(default=None, max_length=200)
    language: str | None = Field(default=None, pattern="^(fr|ar|en)$")


class WritingAttemptResponse(BaseModel):
    id: str
    student_id: str
    status: str
    suggestion: str | None = None
    hints: list[str] = Field(default_factory=list)
    prompt_id: str | None = None
    prompt_version: int | None = None
    warnings: list[str] = Field(default_factory=list)
    created_at: str


# ---------------------------------------------------------------------------
# AI Opt-out Preference (S-144, DEC-009)
# ---------------------------------------------------------------------------
class AIOptOutRequest(BaseModel):
    """POST /ai/preferences/opt-out — parent opts out of AI personalization."""

    opt_out: bool = Field(..., description="True to opt out, False to opt back in")
    target_user_id: uuid.UUID | None = Field(
        default=None,
        description="Child user ID (parent opting out for child). Null = self.",
    )


class AIOptOutResponse(BaseModel):
    id: str
    user_id: str
    target_user_id: str
    opt_out: bool
    updated_at: str


# ---------------------------------------------------------------------------
# Learning Recommendations (S-145)
# ---------------------------------------------------------------------------
class RecommendationItem(BaseModel):
    title: str
    reason_code: str  # Mandatory per G3
    priority: str
    content_type: str | None = None


class RecommendationsResponse(BaseModel):
    status: str
    recommendations: list[RecommendationItem] = Field(default_factory=list)
    prompt_id: str | None = None
    prompt_version: int | None = None
    expires_at: str | None = None


# ---------------------------------------------------------------------------
# KPI Query Results (S-140)
# ---------------------------------------------------------------------------
class KPIResult(BaseModel):
    kpi_id: str
    name: str
    value: float | None = None
    unit: str | None = None
    threshold: str | None = None
    period: str | None = None
    computed_at: str


class KPIDashboardResponse(BaseModel):
    kpis: list[KPIResult] = Field(default_factory=list)
    period: str
    computed_at: str


# ---------------------------------------------------------------------------
# Event Schema Registry (S-146)
# ---------------------------------------------------------------------------
class EventSchemaEntry(BaseModel):
    event_name: str
    event_version: int
    schema_version: int
    required_properties: list[str] = Field(default_factory=list)
    pii_risk: str = "low"
    status: str = "known"


class EventSchemaRegistryResponse(BaseModel):
    schema_version: int
    events: list[EventSchemaEntry] = Field(default_factory=list)
    total: int
