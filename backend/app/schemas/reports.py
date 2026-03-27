"""Phase 14 reports and export schemas."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from pydantic import BaseModel, Field, model_validator


class ReportGenerateRequest(BaseModel):
    type: str = Field(
        ...,
        pattern="^(student_report_card|class_summary|attendance_report|billing_statement|school_analytics)$",
    )
    period_id: uuid.UUID | None = None
    class_id: uuid.UUID | None = None
    student_id: uuid.UUID | None = None
    parent_id: uuid.UUID | None = None
    from_date: date | None = None
    to_date: date | None = None
    locale: str = Field(default="fr", pattern="^(fr|ar|en)$")
    compare: bool = False

    @model_validator(mode="after")
    def validate_dates(self):
        if self.from_date and self.to_date and self.from_date > self.to_date:
            raise ValueError("from_date must be before to_date")
        return self


class ReportJobItem(BaseModel):
    id: str
    type: str
    status: str
    parameters: dict[str, Any]
    file_path: str | None = None
    error_message: str | None = None
    created_at: str
    completed_at: str | None = None
    expires_at: str | None = None
    download_url: str | None = None
    cache_hit: bool = False


class ReportStatusResponse(ReportJobItem):
    pass


class ExportFilters(BaseModel):
    period_id: uuid.UUID | None = None
    class_id: uuid.UUID | None = None
    student_id: uuid.UUID | None = None
    parent_id: uuid.UUID | None = None
    from_date: date | None = None
    to_date: date | None = None
    status: str | None = None
    subject: str | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.from_date and self.to_date and self.from_date > self.to_date:
            raise ValueError("from_date must be before to_date")
        return self


class ExportLogItem(BaseModel):
    id: str
    entity: str
    format: str
    row_count: int
    created_at: str
