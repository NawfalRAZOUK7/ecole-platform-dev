"""Financial health domain events."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.domain.events.base import DomainEvent


@dataclass(frozen=True)
class RetentionMetricComputed(DomainEvent):
    metric_id: UUID = None
    school_id: UUID = None
    academic_year_from: str = ""
    academic_year_to: str = ""


@dataclass(frozen=True)
class CashflowForecastComputed(DomainEvent):
    forecast_id: UUID = None
    school_id: UUID = None
    forecast_month: str = ""


@dataclass(frozen=True)
class CostPerStudentComputed(DomainEvent):
    analysis_id: UUID = None
    school_id: UUID = None
    academic_year_id: UUID = None


@dataclass(frozen=True)
class FinancialSnapshotComputed(DomainEvent):
    snapshot_id: UUID = None
    school_id: UUID = None
    snapshot_date: str = ""
