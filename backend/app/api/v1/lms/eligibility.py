"""Eligibility rules + check endpoints (Phase 3.4 / G50d).

Routes:
  GET    /eligibility/rules                                      — list rules
  POST   /eligibility/rules                                      — create rule
  DELETE /eligibility/rules/{rule_id}                            — delete rule
  GET    /students/{student_id}/eligibility?kind=...&target_program_id=...
                                                                 — run the check
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    AuthContext,
    get_current_user,
    requires_permission,
)
from app.core.permissions import (
    PERM_ERP_PROGRAM_MANAGE,
    PERM_ERP_PROGRAM_READ,
)
from app.core.request_utils import get_client_ip
from app.core.response import list_response, success_response
from app.schemas.academic.programs import EligibilityRuleCreateRequest
from app.services.lms.eligibility_service import EligibilityService

eligibility_router = APIRouter(prefix="/eligibility", tags=["erp-eligibility"])
student_eligibility_router = APIRouter(prefix="/students", tags=["erp-eligibility"])


@eligibility_router.get(
    "/rules",
    summary="List eligibility rules (optionally filtered)",
)
async def list_rules(
    kind: str | None = Query(
        None,
        pattern="^(PROMOTION|ADMISSION|TRANSFER)$",
    ),
    target_program_id: uuid.UUID | None = Query(None),
    active_only: bool = Query(True),
    auth: AuthContext = Depends(requires_permission(PERM_ERP_PROGRAM_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = EligibilityService(db)
    items = await service.list_rules(
        auth=auth,
        kind=kind,
        target_program_id=target_program_id,
        active_only=active_only,
    )
    return list_response(items, next_cursor=None, has_more=False)


@eligibility_router.post(
    "/rules",
    status_code=201,
    summary="Create an eligibility rule",
)
async def create_rule(
    body: EligibilityRuleCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_ERP_PROGRAM_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    service = EligibilityService(db)
    item = await service.create_rule(
        kind=body.kind,
        target_program_id=body.target_program_id,
        condition_type=body.condition_type,
        condition_params=body.condition_params,
        message_key=body.message_key,
        is_active=body.is_active,
        auth=auth,
        ip_address=get_client_ip(request),
    )
    return success_response(item)


@eligibility_router.delete(
    "/rules/{rule_id}",
    status_code=204,
    summary="Delete an eligibility rule",
)
async def delete_rule(
    rule_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_ERP_PROGRAM_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    service = EligibilityService(db)
    await service.delete_rule(
        rule_id=rule_id,
        auth=auth,
        ip_address=get_client_ip(request),
    )
    return None


@student_eligibility_router.get(
    "/{student_id}/eligibility",
    summary="Check eligibility for a student against rules of a kind+target",
)
async def check_eligibility(
    student_id: uuid.UUID,
    kind: str = Query(..., pattern="^(PROMOTION|ADMISSION|TRANSFER)$"),
    target_program_id: uuid.UUID = Query(...),
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = EligibilityService(db)
    result = await service.check_eligibility(
        student_id=student_id,
        target_program_id=target_program_id,
        kind=kind,
        auth=auth,
    )
    return success_response(result)
