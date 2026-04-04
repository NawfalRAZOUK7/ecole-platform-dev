"""Local-first sync domain events."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.domain.events.base import DomainEvent


@dataclass(frozen=True)
class SyncDeviceRegistered(DomainEvent):
    device_id: UUID = None
    school_id: UUID = None
    device_type: str = ""


@dataclass(frozen=True)
class SyncQueueItemEnqueued(DomainEvent):
    queue_item_id: UUID = None
    device_id: UUID = None
    entity_type: str = ""
    operation: str = ""


@dataclass(frozen=True)
class SyncConflictDetected(DomainEvent):
    conflict_id: UUID = None
    queue_item_id: UUID = None
    entity_type: str = ""


@dataclass(frozen=True)
class SyncConflictResolved(DomainEvent):
    conflict_id: UUID = None
    resolution: str = ""
    resolved_by: UUID = None


@dataclass(frozen=True)
class SyncCheckpointCreated(DomainEvent):
    checkpoint_id: UUID = None
    device_id: UUID = None
    records_synced: int = 0
