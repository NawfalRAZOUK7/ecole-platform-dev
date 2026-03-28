"""Calendar domain events."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from app.domain.events.base import DomainEvent


@dataclass(frozen=True)
class EventCreated(DomainEvent):
    event_id: UUID = None
    title: str = ""
    start_at: str = ""
    class_id: UUID = None


@dataclass(frozen=True)
class EventUpdated(DomainEvent):
    event_id: UUID = None
    title: str = ""
    changes: dict = field(default_factory=dict)


@dataclass(frozen=True)
class HolidayAdded(DomainEvent):
    holiday_name: str = ""
    start_date: str = ""
    end_date: str = ""


@dataclass(frozen=True)
class EventRSVPReceived(DomainEvent):
    event_id: UUID = None
    user_id: UUID = None
    status: str = ""
