"""ERP domain events."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.domain.events.base import DomainEvent


@dataclass(frozen=True)
class AttendanceThresholdExceeded(DomainEvent):
    student_id: UUID = None
    period_id: UUID = None
    student_name: str | None = None
    absence_count: int = 0
    total_sessions: int = 0
    absence_rate: float = 0.0
    threshold_exceeded: str = ""
