"""Schemas for scheduled report generation."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator

_ALLOWED_REPORT_TYPES = (
    "student_report_card",
    "class_summary",
    "attendance_report",
    "billing_statement",
    "school_analytics",
)
_ALLOWED_FREQUENCIES = ("daily", "weekly", "monthly", "end_of_period")
_ALLOWED_RECIPIENT_ROLES = {"ADM", "DIR", "TCH", "PAR", "STD"}


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


class ReportScheduleCreateRequest(BaseModel):
    report_type: str = Field(
        ...,
        pattern="^(student_report_card|class_summary|attendance_report|billing_statement|school_analytics)$",
    )
    frequency: str = Field(
        ...,
        pattern="^(daily|weekly|monthly|end_of_period)$",
    )
    parameters: dict[str, Any] = Field(default_factory=dict)
    recipient_roles: list[str] = Field(default_factory=list, min_length=1)
    enabled: bool = True
    next_run_at: datetime | None = None

    @model_validator(mode="after")
    def validate_payload(self):
        roles = [str(role).upper() for role in self.recipient_roles]
        invalid = [role for role in roles if role not in _ALLOWED_RECIPIENT_ROLES]
        if invalid:
            raise ValueError(f"Unsupported recipient roles: {', '.join(sorted(set(invalid)))}")
        self.recipient_roles = _dedupe(roles)
        return self


class ReportScheduleUpdateRequest(BaseModel):
    report_type: str | None = Field(
        default=None,
        pattern="^(student_report_card|class_summary|attendance_report|billing_statement|school_analytics)$",
    )
    frequency: str | None = Field(
        default=None,
        pattern="^(daily|weekly|monthly|end_of_period)$",
    )
    parameters: dict[str, Any] | None = None
    recipient_roles: list[str] | None = None
    enabled: bool | None = None
    next_run_at: datetime | None = None

    @model_validator(mode="after")
    def validate_payload(self):
        if self.recipient_roles is None:
            return self
        roles = [str(role).upper() for role in self.recipient_roles]
        invalid = [role for role in roles if role not in _ALLOWED_RECIPIENT_ROLES]
        if invalid:
            raise ValueError(f"Unsupported recipient roles: {', '.join(sorted(set(invalid)))}")
        if not roles:
            raise ValueError("recipient_roles cannot be empty")
        self.recipient_roles = _dedupe(roles)
        return self


class ReportScheduleResponse(BaseModel):
    id: str
    school_id: str
    created_by: str
    report_type: str
    frequency: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    recipient_roles: list[str] = Field(default_factory=list)
    enabled: bool
    last_run_at: str | None = None
    next_run_at: str | None = None
    created_at: str
    updated_at: str | None = None


class ReportScheduleRunResponse(BaseModel):
    schedule: ReportScheduleResponse
    job: dict[str, Any]
