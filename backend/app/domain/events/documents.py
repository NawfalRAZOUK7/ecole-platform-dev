"""Document and resource domain events."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.domain.events.base import DomainEvent


@dataclass(frozen=True)
class DocumentUploaded(DomainEvent):
    document_id: UUID = None
    filename: str = ""
    student_id: UUID = None


@dataclass(frozen=True)
class DocumentExpiring(DomainEvent):
    document_id: UUID = None
    student_id: UUID = None
    document_name: str = ""
    expires_at: str = ""


@dataclass(frozen=True)
class ResourceShared(DomainEvent):
    resource_id: UUID = None
    title: str = ""
    class_id: UUID = None
