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
