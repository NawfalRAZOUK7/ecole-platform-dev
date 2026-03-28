"""Question bank schemas for reusable quiz question storage and generation."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class QuestionBankQuestionData(BaseModel):
    question_type: str = Field(
        ..., pattern="^(MCQ|TRUE_FALSE|FILL_IN|DRAG_DROP|MATCHING)$"
    )
    question_text: str = Field(..., min_length=1)
    question_media_path: str | None = None
    options: Any | None = None
    correct_answer: Any = Field(...)
    points: int = Field(default=1, ge=0)
    explanation: str | None = None


class QuestionBankCreateRequest(BaseModel):
    subject: str = Field(..., min_length=1, max_length=120)
    level: str | None = Field(default=None, max_length=50)
    difficulty: str = Field(..., pattern="^(easy|medium|hard)$")
    tags: list[str] = Field(default_factory=list, max_length=20)
    question_data: QuestionBankQuestionData


class QuestionBankItemResponse(BaseModel):
    id: str
    school_id: str
    teacher_id: str
    subject: str
    level: str | None = None
    difficulty: str
    question_type: str
    question_data: dict
    tags: list[str] = Field(default_factory=list)
    usage_count: int
    is_archived: bool


class GenerateQuizFromBankRequest(BaseModel):
    subject: str = Field(..., min_length=1, max_length=120)
    level: str | None = Field(default=None, max_length=50)
    distribution: dict[str, int] = Field(default_factory=dict)
    title: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = None
    shuffle_questions: bool = False
    time_limit_minutes: int | None = Field(default=None, ge=0)
    max_attempts: int = Field(default=1, ge=1)


class QuestionBankImportResponse(BaseModel):
    quiz_id: str
    imported_count: int


class QuestionBankStatsItemResponse(BaseModel):
    subject: str
    difficulty: str
    question_count: int
    total_usage: int
