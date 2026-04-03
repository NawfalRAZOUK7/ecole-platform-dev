"""Micro-school domain events."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.domain.events.base import DomainEvent


@dataclass(frozen=True)
class MicroSchoolCreated(DomainEvent):
    micro_school_id: UUID = None
    educator_id: UUID = None
    name: str = ""


@dataclass(frozen=True)
class MicroGroupCreated(DomainEvent):
    micro_group_id: UUID = None
    micro_school_id: UUID = None
    group_name: str = ""


@dataclass(frozen=True)
class MicroEnrollmentCreated(DomainEvent):
    micro_enrollment_id: UUID = None
    micro_group_id: UUID = None
    parent_id: UUID = None
    child_name: str = ""


@dataclass(frozen=True)
class MicroPaymentRecorded(DomainEvent):
    micro_payment_id: UUID = None
    micro_school_id: UUID = None
    parent_id: UUID = None
    amount: float = 0.0


@dataclass(frozen=True)
class MicroProgressLogged(DomainEvent):
    micro_progress_log_id: UUID = None
    micro_enrollment_id: UUID = None
    educator_id: UUID = None
    milestone_tag: str = ""
