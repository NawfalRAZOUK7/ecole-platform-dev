"""MEN compliance domain events."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.domain.events.base import DomainEvent


@dataclass(frozen=True)
class MenCurriculumCreated(DomainEvent):
    curriculum_id: UUID = None
    subject: str = ""
    grade: str = ""


@dataclass(frozen=True)
class MenObjectiveCreated(DomainEvent):
    objective_id: UUID = None
    curriculum_id: UUID = None
    code: str = ""


@dataclass(frozen=True)
class CurriculumMapped(DomainEvent):
    mapping_id: UUID = None
    objective_id: UUID = None
    course_id: UUID | None = None
    coverage_percent: int = 0


@dataclass(frozen=True)
class ComplianceReportGenerated(DomainEvent):
    report_id: UUID = None
    curriculum_id: UUID = None
    compliance_percent: float = 0.0


@dataclass(frozen=True)
class MenCurriculumSeeded(DomainEvent):
    curriculum_count: int = 0
    objective_count: int = 0
