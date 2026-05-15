"""Gradebook schemas for weighted averages, matrix views, and transcripts."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class GradeCategoryInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    weight: float = Field(..., gt=0, le=1)
    position: int = Field(default=0, ge=0)


class GradeCategorySetRequest(BaseModel):
    class_id: uuid.UUID
    period_id: uuid.UUID
    categories: list[GradeCategoryInput] = Field(default_factory=list)


class GradeCategoryResponse(BaseModel):
    id: str
    school_id: str
    class_id: str
    period_id: str
    name: str
    weight: float
    position: int


class CategoryAverageResponse(BaseModel):
    category_id: str
    category_name: str
    weight: float
    average: float | None = None


class GradebookAssignmentResponse(BaseModel):
    assignment_id: str
    title: str
    category_id: str | None = None
    category_name: str | None = None
    total_points: int
    due_at: str | None = None


class GradebookCellResponse(BaseModel):
    assignment_id: str
    assignment_title: str
    category_id: str | None = None
    category_name: str | None = None
    score: float | None = None
    total_points: int
    published_at: str | None = None


class ClassAverageResponse(BaseModel):
    student_id: str
    student_name: str
    weighted_average: float
    mention: str
    class_rank: int | None = None
    total_students: int | None = None
    computed_at: str | None = None


class GradebookStudentRowResponse(BaseModel):
    student_id: str
    student_name: str
    assignments: list[GradebookCellResponse] = Field(default_factory=list)
    category_averages: list[CategoryAverageResponse] = Field(default_factory=list)
    weighted_average: float
    mention: str
    class_rank: int | None = None
    total_students: int | None = None


class GradebookMatrixResponse(BaseModel):
    class_id: str
    class_name: str
    period_id: str
    period_label: str | None = None
    categories: list[GradeCategoryResponse] = Field(default_factory=list)
    assignments: list[GradebookAssignmentResponse] = Field(default_factory=list)
    rows: list[GradebookStudentRowResponse] = Field(default_factory=list)


class TranscriptPeriodResponse(BaseModel):
    class_id: str
    class_name: str
    period_id: str
    period_label: str | None = None
    weighted_average: float
    mention: str
    class_rank: int | None = None
    total_students: int | None = None
    computed_at: str | None = None


class StudentTranscriptResponse(BaseModel):
    student_id: str
    academic_year_id: str
    periods: list[TranscriptPeriodResponse] = Field(default_factory=list)
