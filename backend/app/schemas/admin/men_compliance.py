"""Pydantic schemas for MEN compliance workflows."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class MenCurriculumCreateRequest(BaseModel):
    """Payload for creating a MEN curriculum."""

    level: str = Field(..., min_length=1, max_length=50)
    grade: str = Field(..., min_length=1, max_length=20)
    subject: str = Field(..., min_length=1, max_length=100)
    academic_year: str = Field(..., pattern=r"^\d{4}-\d{4}$")
    version: str = Field("1.0", min_length=1, max_length=20)
    is_active: bool = True


class MenCurriculumResponse(BaseModel):
    """Serialized MEN curriculum response."""

    id: str
    level: str
    grade: str
    subject: str
    academic_year: str
    version: str
    is_active: bool
    created_at: str
    updated_at: str | None = None


class MenObjectiveCreateRequest(BaseModel):
    """Payload for creating a MEN objective."""

    code: str = Field(..., min_length=1, max_length=50)
    title_fr: str = Field(..., min_length=1, max_length=500)
    title_ar: str = Field(..., min_length=1, max_length=500)
    description_fr: str | None = Field(None, max_length=4000)
    trimester: int = Field(..., ge=1, le=3)
    unit_number: int = Field(..., ge=1)
    is_mandatory: bool = True
    hours_recommended: float | None = Field(None, ge=0)
    display_order: int = Field(..., ge=0)


class MenObjectiveResponse(BaseModel):
    """Serialized MEN objective response."""

    id: str
    curriculum_id: str
    curriculum_subject: str | None = None
    code: str
    title_fr: str
    title_ar: str
    description_fr: str | None = None
    trimester: int
    unit_number: int
    is_mandatory: bool
    hours_recommended: float | None = None
    display_order: int
    created_at: str
    updated_at: str | None = None


class CurriculumMappingCreateRequest(BaseModel):
    """Payload for creating a curriculum mapping."""

    objective_id: uuid.UUID
    course_id: uuid.UUID | None = None
    content_item_id: uuid.UUID | None = None
    coverage_percent: int = Field(100, ge=0, le=100)
    notes: str | None = Field(None, max_length=4000)


class CurriculumMappingResponse(BaseModel):
    """Serialized curriculum mapping response."""

    id: str
    school_id: str
    objective_id: str
    objective_code: str | None = None
    curriculum_id: str | None = None
    course_id: str | None = None
    content_item_id: str | None = None
    mapped_by: str
    mapped_at: str
    coverage_percent: int
    notes: str | None = None
    created_at: str
    updated_at: str | None = None


class ComplianceDashboardItemResponse(BaseModel):
    """Serialized dashboard row for one curriculum."""

    curriculum_id: str
    level: str
    grade: str
    subject: str
    academic_year: str
    total_objectives: int
    mapped_objectives: int
    unmapped_objectives: int
    compliance_percent: float


class ComplianceDashboardResponse(BaseModel):
    """Serialized MEN compliance dashboard response."""

    school_id: str
    academic_year_id: str | None = None
    curriculum_count: int
    total_objectives: int
    mapped_objectives: int
    overall_compliance_percent: float
    items: list[ComplianceDashboardItemResponse]


class ComplianceReportGenerateRequest(BaseModel):
    """Payload for generating a compliance report."""

    curriculum_id: uuid.UUID
    academic_year_id: uuid.UUID


class ComplianceReportResponse(BaseModel):
    """Serialized compliance report response."""

    id: str
    school_id: str
    curriculum_id: str
    curriculum_subject: str | None = None
    curriculum_grade: str | None = None
    curriculum_level: str | None = None
    generated_at: str
    generated_by: str
    total_objectives: int
    mapped_objectives: int
    compliance_percent: float
    unmapped_objectives: list[str]
    pdf_url: str | None = None
    academic_year_id: str
    created_at: str
    updated_at: str | None = None


__all__ = [
    "MenCurriculumCreateRequest",
    "MenCurriculumResponse",
    "MenObjectiveCreateRequest",
    "MenObjectiveResponse",
    "CurriculumMappingCreateRequest",
    "CurriculumMappingResponse",
    "ComplianceDashboardItemResponse",
    "ComplianceDashboardResponse",
    "ComplianceReportGenerateRequest",
    "ComplianceReportResponse",
]
