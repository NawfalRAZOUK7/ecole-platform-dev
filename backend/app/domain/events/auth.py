"""Authentication domain events."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.domain.events.base import DomainEvent


@dataclass(frozen=True)
class UserRegistered(DomainEvent):
    user_id: UUID = None
    role: str = ""
    school_id: UUID = None


@dataclass(frozen=True)
class PasswordChanged(DomainEvent):
    user_id: UUID = None


@dataclass(frozen=True)
class TwoFactorEnabled(DomainEvent):
    user_id: UUID = None
