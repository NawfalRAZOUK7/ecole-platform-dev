"""LMS domain events."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.domain.events.base import DomainEvent


@dataclass(frozen=True)
class GradePublished(DomainEvent):
    student_id: UUID = None
    course_title: str = ""
    score: float = 0.0
    teacher_name: str = ""


@dataclass(frozen=True)
class AssignmentCreated(DomainEvent):
    assignment_id: UUID = None
    course_title: str = ""
    due_at: str = ""
    class_id: UUID = None


@dataclass(frozen=True)
class QuizCompleted(DomainEvent):
    student_id: UUID = None
    quiz_title: str = ""
    score_percent: float = 0.0


@dataclass(frozen=True)
class SubmissionReceived(DomainEvent):
    submission_id: UUID = None
    student_name: str = ""
    assignment_title: str = ""
    teacher_id: UUID = None


@dataclass(frozen=True)
class ContentPublished(DomainEvent):
    content_id: UUID = None
    title: str = ""
    class_id: UUID = None
