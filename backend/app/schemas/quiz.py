"""Quiz Engine Pydantic schemas — Phase 9B.

Request/response models for quiz CRUD, attempts, responses, and analytics.
"""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Quiz CRUD
# ---------------------------------------------------------------------------
class QuizQuestionInput(BaseModel):
    question_type: str = Field(
        ..., pattern="^(MCQ|TRUE_FALSE|FILL_IN|DRAG_DROP|MATCHING)$"
    )
    question_text: str = Field(..., min_length=1)
    question_media_path: str | None = None
    options: Any | None = None
    correct_answer: Any = Field(...)
    points: int = Field(default=1, ge=0)
    order: int = Field(default=0, ge=0)
    explanation: str | None = None


class QuizCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    description: str | None = None
    subject: str | None = Field(None, max_length=50)
    level_band: str | None = Field(None, max_length=50)
    difficulty: str | None = Field(None, pattern="^(EASY|MEDIUM|HARD)$")
    time_limit_minutes: int | None = Field(None, ge=0)
    max_attempts: int = Field(default=1, ge=1)
    shuffle_questions: bool = False
    questions: list[QuizQuestionInput] = Field(default_factory=list)


class QuizUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=300)
    description: str | None = None
    subject: str | None = Field(None, max_length=50)
    level_band: str | None = Field(None, max_length=50)
    difficulty: str | None = Field(None, pattern="^(EASY|MEDIUM|HARD)$")
    time_limit_minutes: int | None = Field(None, ge=0)
    max_attempts: int | None = Field(None, ge=1)
    shuffle_questions: bool | None = None
    questions: list[QuizQuestionInput] | None = None


class QuizQuestionResponse(BaseModel):
    id: str
    question_type: str
    question_text: str
    question_media_path: str | None = None
    options: Any | None = None
    points: int
    order: int
    explanation: str | None = None
    # correct_answer omitted for students, included for creators


class QuizResponse(BaseModel):
    id: str
    school_id: str | None = None
    created_by: str
    title: str
    description: str | None = None
    subject: str | None = None
    level_band: str | None = None
    difficulty: str | None = None
    time_limit_minutes: int | None = None
    max_attempts: int
    shuffle_questions: bool
    status: str
    total_points: int = 0
    question_count: int = 0


class QuizDetailResponse(QuizResponse):
    questions: list[QuizQuestionResponse] = []


# ---------------------------------------------------------------------------
# Attempts + Responses
# ---------------------------------------------------------------------------
class QuizRespondRequest(BaseModel):
    question_id: uuid.UUID
    student_answer: Any


class AttemptResponse(BaseModel):
    id: str
    quiz_id: str
    student_id: str
    attempt_no: int
    started_at: str
    completed_at: str | None = None
    score: float | None = None
    max_score: int
    status: str


class ResponseResultItem(BaseModel):
    question_id: str
    question_type: str
    question_text: str
    student_answer: Any | None = None
    correct_answer: Any | None = None
    is_correct: bool | None = None
    points_earned: float | None = None
    points: int
    explanation: str | None = None


class AttemptResultResponse(BaseModel):
    attempt: AttemptResponse
    responses: list[ResponseResultItem] = []


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------
class QuizAnalyticsResponse(BaseModel):
    quiz_id: str
    title: str
    total_attempts: int
    completed_attempts: int
    average_score: float | None = None
    max_score_achieved: float | None = None
    min_score_achieved: float | None = None
    average_percentage: float | None = None
    question_stats: list[dict] = []
