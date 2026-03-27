"""Phase 13 device registration API."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.exceptions import NotFoundError
from app.core.response import list_response, success_response
from app.schemas.notifications import DeviceRegistrationRequest
from app.services.audit import AuditService
from app.services.push_config import PushConfigService

router = APIRouter(prefix="/devices", tags=["com-notifications"])


def _get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def _serialize_device(device) -> dict:
    token = device.token or ""
    preview = f"{token[:12]}...{token[-6:]}" if len(token) > 20 else token
    return {
        "id": str(device.id),
        "user_id": str(device.user_id),
        "platform": device.platform,
        "device_name": device.device_name,
        "token_preview": preview,
        "last_active_at": device.last_active_at.isoformat(),
        "created_at": device.created_at.isoformat(),
    }


@router.get(
    "",
    summary="List current user's registered devices",
    response_description="Registered device tokens for the authenticated user",
)
async def list_devices(
    auth: AuthContext = Depends(requires_permission("PERM-COM:notification:read")),
    db: AsyncSession = Depends(get_db),
):
    service = PushConfigService(db)
    devices = await service.list_devices(school_id=auth.school_id, user_id=auth.user_id)
    return list_response([_serialize_device(device) for device in devices])


@router.post(
    "/register",
    summary="Register a device token",
    response_description="Registered device",
)
async def register_device(
    body: DeviceRegistrationRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-COM:notification:read")),
    db: AsyncSession = Depends(get_db),
):
    service = PushConfigService(db)
    audit = AuditService(db)
    device = await service.register_device(
        school_id=auth.school_id,
        user_id=auth.user_id,
        token=body.token,
        platform=body.platform,
        device_name=body.device_name,
    )
    payload = _serialize_device(device)
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="notification.device.register",
        target_type="device_token",
        target_id=device.id,
        outcome="success",
        entity_after=payload,
        ip_address=_get_client_ip(request),
    )
    return success_response(payload)


@router.delete(
    "/{device_id}",
    summary="Deregister a device token",
    response_description="Deletion outcome",
)
async def delete_device(
    device_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-COM:notification:read")),
    db: AsyncSession = Depends(get_db),
):
    service = PushConfigService(db)
    audit = AuditService(db)
    device = await service.deregister_device(
        school_id=auth.school_id,
        user_id=auth.user_id,
        device_id=device_id,
    )
    if device is None:
        raise NotFoundError("Device not found", error_code="ERR-COM-404")

    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="notification.device.delete",
        target_type="device_token",
        target_id=device.id,
        outcome="success",
        entity_before=_serialize_device(device),
        ip_address=_get_client_ip(request),
    )
    return success_response({"deleted": True, "id": str(device.id)})
