"""Billing domain events."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.domain.events.base import DomainEvent


@dataclass(frozen=True)
class InvoiceGenerated(DomainEvent):
    invoice_id: UUID = None
    student_id: UUID = None
    amount: float = 0.0
    due_date: str = ""


@dataclass(frozen=True)
class PaymentReceived(DomainEvent):
    payment_id: UUID = None
    invoice_id: UUID = None
    amount: float = 0.0
    method: str = ""


@dataclass(frozen=True)
class PaymentFailed(DomainEvent):
    payment_id: UUID = None
    invoice_id: UUID = None
    reason: str = ""
