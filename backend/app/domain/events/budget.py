"""Budget domain events."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.domain.events.base import DomainEvent


@dataclass(frozen=True)
class BudgetCreated(DomainEvent):
    budget_id: UUID = None
    academic_year_id: UUID = None
    total_amount: float = 0.0


@dataclass(frozen=True)
class BudgetAllocated(DomainEvent):
    allocation_id: UUID = None
    budget_id: UUID = None
    amount: float = 0.0


@dataclass(frozen=True)
class BudgetRequestSubmitted(DomainEvent):
    request_id: UUID = None
    allocation_id: UUID = None
    requester_id: UUID = None
    amount: float = 0.0


@dataclass(frozen=True)
class BudgetRequestReviewed(DomainEvent):
    request_id: UUID = None
    allocation_id: UUID = None
    decision: str = ""


@dataclass(frozen=True)
class BudgetTransactionRecorded(DomainEvent):
    transaction_id: UUID = None
    allocation_id: UUID = None
    transaction_type: str = ""
    amount: float = 0.0
