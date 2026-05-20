"""GDPR compliance endpoints — data export, data deletion, and consent history."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.permissions import PERM_GDPR_DATA_DELETE, PERM_IAM_SESSION_LIST
from app.core.request_utils import get_client_ip
from app.core.response import success_response
from app.services.user.gdpr import GDPRService

router = APIRouter(prefix="/users", tags=["gdpr"])


@router.get(
    "/{user_id}/data-export",
    summary="Export all user data (GDPR)",
    response_description="Structured GDPR data export",
)
async def data_export(
    user_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_IAM_SESSION_LIST)),
    db: AsyncSession = Depends(get_db),
):
    service = GDPRService(db)
    return success_response(
        await service.data_export(
            user_id=user_id,
            auth=auth,
            client_ip=get_client_ip(request),
        )
    )


@router.post(
    "/{user_id}/data-deletion",
    summary="Anonymize user data (GDPR)",
    response_description="Anonymization status",
)
async def data_deletion(
    user_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_GDPR_DATA_DELETE)),
    db: AsyncSession = Depends(get_db),
):
    service = GDPRService(db)
    return success_response(
        await service.data_deletion(
            user_id=user_id,
            auth=auth,
            client_ip=get_client_ip(request),
        )
    )


@router.get(
    "/{user_id}/consent-log",
    summary="Consent change history (GDPR)",
    response_description="Current consent preferences and audit history",
)
async def consent_log(
    user_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_IAM_SESSION_LIST)),
    db: AsyncSession = Depends(get_db),
):
    service = GDPRService(db)
    return success_response(
        await service.consent_log(
            user_id=user_id,
            auth=auth,
            client_ip=get_client_ip(request),
        )
    )
