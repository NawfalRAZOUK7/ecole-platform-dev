"""Life-skills passport domain events."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.domain.events.base import DomainEvent


@dataclass(frozen=True)
class SkillDimensionCreated(DomainEvent):
    skill_dimension_id: UUID = None
    code: str = ""


@dataclass(frozen=True)
class SkillMilestoneCreated(DomainEvent):
    skill_milestone_id: UUID = None
    dimension_id: UUID = None
    code: str = ""


@dataclass(frozen=True)
class SkillProgressEvaluated(DomainEvent):
    skill_progress_id: UUID = None
    student_id: UUID = None
    milestone_id: UUID = None
    status: str = ""


@dataclass(frozen=True)
class SkillPassportGenerated(DomainEvent):
    skill_passport_id: UUID = None
    student_id: UUID = None
    academic_year_id: UUID = None
    overall_score: float = 0.0
