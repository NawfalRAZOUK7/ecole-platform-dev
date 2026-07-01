"""Pydantic schemas for local-first sync workflows."""

from __future__ import annotations

import uuid
from datetime import datetime as datetime_type
from typing import Any

from pydantic import BaseModel, Field


class RegisterDeviceRequest(BaseModel):
    """Payload for registering a sync device."""

    device_name: str = Field(..., min_length=1, max_length=200)
    device_type: str = Field(..., pattern="^(local_server|mobile|browser)$")
    firmware_version: str | None = Field(None, max_length=50)


class SyncDeviceResponse(BaseModel):
    """Serialized sync device response."""

    id: str
    school_id: str
    device_name: str
    device_type: str
    last_seen_at: str
    firmware_version: str | None = None
    is_active: bool
    created_at: str
    updated_at: str | None = None


class QueueItemCreateRequest(BaseModel):
    """Payload for enqueuing a sync item."""

    entity_type: str = Field(..., min_length=1, max_length=100)
    entity_id: uuid.UUID
    operation: str = Field(..., pattern="^(create|update|delete)$")
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime_type | None = None


class QueueItemResponse(BaseModel):
    """Serialized sync queue item response."""

    id: str
    school_id: str
    device_id: str
    entity_type: str
    entity_id: str
    operation: str
    payload: dict[str, Any]
    status: str
    retry_count: int
    synced_at: str | None = None
    created_at: str
    updated_at: str | None = None


class PushPayload(BaseModel):
    """Batch payload for pushed sync changes."""

    items: list[QueueItemCreateRequest] = Field(..., min_length=1, max_length=500)


class PushResponse(BaseModel):
    """Summary response for a push operation."""

    device_id: str
    accepted_count: int
    conflict_count: int
    queued_items: list[QueueItemResponse]
    conflict_ids: list[str]


class PullResponse(BaseModel):
    """Summary response for a pull operation."""

    device_id: str
    since_checkpoint: str | None = None
    changes: list[QueueItemResponse]
    next_checkpoint_id: str | None = None
    conflict_count: int


class ResolveConflictRequest(BaseModel):
    """Payload for resolving a sync conflict."""

    resolution: str = Field(
        ...,
        pattern="^(pending|client_wins|server_wins|manual)$",
    )


class SyncConflictResponse(BaseModel):
    """Serialized sync conflict response."""

    id: str
    school_id: str
    queue_item_id: str
    entity_type: str
    entity_id: str
    client_payload: dict[str, Any]
    server_payload: dict[str, Any]
    resolution: str
    resolved_by: str | None = None
    resolved_at: str | None = None
    created_at: str
    updated_at: str | None = None


class SyncCheckpointCreateRequest(BaseModel):
    """Payload for creating a sync checkpoint."""

    last_entity_type: str = Field(..., min_length=1, max_length=100)
    last_entity_id: uuid.UUID
    records_synced: int = Field(0, ge=0)


class SyncCheckpointResponse(BaseModel):
    """Serialized sync checkpoint response."""

    id: str
    school_id: str
    device_id: str
    last_sync_at: str
    last_entity_type: str
    last_entity_id: str
    records_synced: int
    created_at: str
    updated_at: str | None = None


class SyncStatusResponse(BaseModel):
    """Serialized sync status response."""

    device_id: str
    pending_count: int
    synced_count: int
    conflict_count: int
    failed_count: int
    last_checkpoint_id: str | None = None
    last_sync_at: str | None = None


class HealthResponse(BaseModel):
    """Serialized sync health response."""

    device_id: str
    health: str
    is_active: bool
    pending_count: int
    conflict_count: int
    failed_count: int
    last_seen_at: str
    last_sync_at: str | None = None


__all__ = [
    "RegisterDeviceRequest",
    "SyncDeviceResponse",
    "QueueItemCreateRequest",
    "QueueItemResponse",
    "PushPayload",
    "PushResponse",
    "PullResponse",
    "ResolveConflictRequest",
    "SyncConflictResponse",
    "SyncCheckpointCreateRequest",
    "SyncCheckpointResponse",
    "SyncStatusResponse",
    "HealthResponse",
]
