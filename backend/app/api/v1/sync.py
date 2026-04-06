"""Local-first sync API endpoints."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.permissions import (
    PERM_SYNC_CONFLICT_READ,
    PERM_SYNC_CONFLICT_RESOLVE,
    PERM_SYNC_DEVICE_READ,
    PERM_SYNC_DEVICE_REGISTER,
    PERM_SYNC_PULL,
    PERM_SYNC_PUSH,
    PERM_SYNC_STATUS_READ,
)
from app.core.request_utils import get_client_ip
from app.core.response import list_response, success_response
from app.schemas.sync_queue import (
    PushPayload,
    RegisterDeviceRequest,
    ResolveConflictRequest,
    SyncCheckpointCreateRequest,
)
from app.services.sync_queue_service import SyncService

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post(
    "/devices",
    status_code=201,
    summary="Register sync device",
    description="Registers a device for offline synchronization and returns the stored device record used for future push and pull operations.",
    response_description="Registered sync device",
)
async def register_device(
    body: RegisterDeviceRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_SYNC_DEVICE_REGISTER)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Register a sync-capable device for the authenticated school."""
    service = SyncService(db)
    return success_response(
        await service.register_device(
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "/devices",
    summary="List sync devices",
    description="Returns sync-capable devices for the authenticated school. Supports filtering by activation state and device type.",
    response_description="List of sync devices",
)
async def list_devices(
    is_active: bool | None = Query(None),
    device_type: str | None = Query(None, pattern="^(local_server|mobile|browser)$"),
    auth: AuthContext = Depends(requires_permission(PERM_SYNC_DEVICE_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List registered sync devices for the authenticated school."""
    service = SyncService(db)
    return list_response(
        await service.list_devices(
            auth=auth,
            is_active=is_active,
            device_type=device_type,
        )
    )


@router.post(
    "/push",
    status_code=202,
    summary="Push offline changes",
    description="Accepts queued offline changes from a device, validates them within school scope, and returns the accepted sync queue items.",
    response_description="Accepted queue items for sync",
)
async def push_changes(
    body: PushPayload,
    request: Request,
    device_id: uuid.UUID = Query(...),
    auth: AuthContext = Depends(requires_permission(PERM_SYNC_PUSH)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Accept queued offline changes from a device."""
    service = SyncService(db)
    return success_response(
        await service.push_changes(
            device_id=device_id,
            payload=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.post(
    "/pull",
    summary="Pull synced changes",
    description="Returns server-side changes available to a device after an optional checkpoint, with a configurable batch limit for incremental sync.",
    response_description="Queued server changes since the checkpoint",
)
async def pull_changes(
    device_id: uuid.UUID = Query(...),
    since_checkpoint: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    auth: AuthContext = Depends(requires_permission(PERM_SYNC_PULL)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Return synced server-side changes for a device."""
    service = SyncService(db)
    return success_response(
        await service.pull_changes(
            device_id=device_id,
            auth=auth,
            since_checkpoint=since_checkpoint,
            limit=limit,
        )
    )


@router.get(
    "/status",
    summary="Get sync status",
    description="Returns queue counters and current synchronization status for a specific device in the authenticated school.",
    response_description="Per-device queue status counts",
)
async def get_sync_status(
    device_id: uuid.UUID = Query(...),
    auth: AuthContext = Depends(requires_permission(PERM_SYNC_STATUS_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Return queue status counts for a device."""
    service = SyncService(db)
    return success_response(
        await service.get_sync_status(
            device_id=device_id,
            auth=auth,
        )
    )


@router.get(
    "/conflicts",
    summary="List sync conflicts",
    description="Lists sync conflicts visible to the authenticated school. Supports filtering by resolution state and limiting the result set.",
    response_description="List of sync conflicts",
)
async def list_conflicts(
    resolution: str | None = Query(
        "pending",
        pattern="^(pending|client_wins|server_wins|manual)$",
    ),
    limit: int = Query(100, ge=1, le=500),
    auth: AuthContext = Depends(requires_permission(PERM_SYNC_CONFLICT_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List sync conflicts for the authenticated school."""
    service = SyncService(db)
    return list_response(
        await service.list_conflicts(
            auth=auth,
            resolution=resolution,
            limit=limit,
        )
    )


@router.post(
    "/conflicts/{conflict_id}/resolve",
    summary="Resolve sync conflict",
    description="Applies a resolution decision to a queued sync conflict and returns the updated conflict record for auditability.",
    response_description="Resolved sync conflict",
)
async def resolve_conflict(
    conflict_id: uuid.UUID,
    body: ResolveConflictRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_SYNC_CONFLICT_RESOLVE)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Resolve a queued sync conflict."""
    service = SyncService(db)
    return success_response(
        await service.resolve_conflict(
            conflict_id=conflict_id,
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "/checkpoints",
    summary="List sync checkpoints",
    description="Returns stored sync checkpoints for the authenticated school, optionally filtered to a specific device.",
    response_description="List of sync checkpoints",
)
async def list_checkpoints(
    device_id: uuid.UUID | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    auth: AuthContext = Depends(requires_permission(PERM_SYNC_DEVICE_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List device sync checkpoints."""
    service = SyncService(db)
    return list_response(
        await service.list_checkpoints(
            auth=auth,
            device_id=device_id,
            limit=limit,
        )
    )


@router.post(
    "/checkpoint",
    status_code=201,
    summary="Create sync checkpoint",
    description="Creates a checkpoint for a device so future pull operations can request only changes after the recorded sync marker.",
    response_description="Created sync checkpoint",
)
async def create_checkpoint(
    body: SyncCheckpointCreateRequest,
    request: Request,
    device_id: uuid.UUID = Query(...),
    auth: AuthContext = Depends(requires_permission(PERM_SYNC_PUSH)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a checkpoint for incremental sync pulls."""
    service = SyncService(db)
    return success_response(
        await service.create_checkpoint(
            device_id=device_id,
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "/health",
    summary="Get sync device health",
    description="Returns the current sync health summary for a device, including queue backlogs and recent synchronization signals.",
    response_description="Current sync health for a device",
)
async def get_sync_health(
    device_id: uuid.UUID = Query(...),
    auth: AuthContext = Depends(requires_permission(PERM_SYNC_STATUS_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Return the current health summary for a sync device."""
    service = SyncService(db)
    return success_response(
        await service.get_device_health(
            device_id=device_id,
            auth=auth,
        )
    )
