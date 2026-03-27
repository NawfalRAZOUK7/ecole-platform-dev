"""Timetable API endpoints — Phase 11A.

Reference: Phase 11A — Timetable / Schedule Management
Endpoints:
  POST   /timetable/slots               — Create slot(s) (ADM)
  GET    /timetable/slots               — List slots with filters (ADM, TCH, PAR, STD)
  PUT    /timetable/slots/{id}          — Update a slot (ADM)
  DELETE /timetable/slots/{id}          — Delete a slot (ADM)
  GET    /timetable/class/{id}/weekly   — Weekly view for a class
  GET    /timetable/teacher/{id}/weekly — Weekly view for a teacher
  GET    /timetable/me/weekly           — Weekly view for current user
  POST   /timetable/exceptions          — Create exception (ADM, TCH)
  GET    /timetable/exceptions          — List exceptions with filters
"""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, get_current_user, requires_permission
from app.core.response import list_response, success_response
from app.core.request_utils import get_client_ip
from app.schemas.erp import (
    TimetableExceptionCreateRequest,
    TimetableSlotBulkCreateRequest,
    TimetableSlotCreateRequest,
    TimetableSlotUpdateRequest,
)
from app.services.erp import ERPService

router = APIRouter(prefix="/timetable", tags=["erp-timetable"])


@router.post(
    "/slots",
    status_code=201,
    summary="Create timetable slot(s)",
    response_description="Created timetable slot(s)",
)
async def create_timetable_slots(
    body: TimetableSlotCreateRequest | TimetableSlotBulkCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-ERP:timetable:create")),
    db: AsyncSession = Depends(get_db),
):
    """Create one or more timetable slots."""
    service = ERPService(db)
    result = await service.create_timetable_slots(
        body=body,
        auth=auth,
        ip_address=get_client_ip(request),
    )
    return success_response(result)


@router.get(
    "/slots",
    summary="List timetable slots",
    response_description="Filtered list of timetable slots",
)
async def list_timetable_slots(
    class_id: uuid.UUID | None = Query(None),
    teacher_id: uuid.UUID | None = Query(None),
    academic_year_id: uuid.UUID | None = Query(None),
    day_of_week: int | None = Query(None, ge=0, le=6),
    auth: AuthContext = Depends(requires_permission("PERM-ERP:timetable:read")),
    db: AsyncSession = Depends(get_db),
):
    """List timetable slots with optional filters."""
    service = ERPService(db)
    result = await service.list_timetable_slots(
        class_id=class_id,
        teacher_id=teacher_id,
        academic_year_id=academic_year_id,
        day_of_week=day_of_week,
        auth=auth,
    )
    return list_response(result)


@router.put(
    "/slots/{slot_id}",
    summary="Update timetable slot",
    response_description="Updated timetable slot",
)
async def update_timetable_slot(
    slot_id: uuid.UUID,
    body: TimetableSlotUpdateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-ERP:timetable:update")),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing timetable slot."""
    service = ERPService(db)
    result = await service.update_timetable_slot(
        slot_id=slot_id,
        body=body,
        auth=auth,
        ip_address=get_client_ip(request),
    )
    return success_response(result)


@router.delete(
    "/slots/{slot_id}",
    status_code=200,
    summary="Delete timetable slot",
    response_description="Deletion confirmation",
)
async def delete_timetable_slot(
    slot_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-ERP:timetable:delete")),
    db: AsyncSession = Depends(get_db),
):
    """Delete a timetable slot and all its exceptions."""
    service = ERPService(db)
    result = await service.delete_timetable_slot(
        slot_id=slot_id,
        auth=auth,
        ip_address=get_client_ip(request),
    )
    return success_response(result)


@router.get(
    "/class/{class_id}/weekly",
    summary="Weekly timetable for a class",
    response_description="Weekly timetable with exceptions",
)
async def get_class_weekly_timetable(
    class_id: uuid.UUID,
    target_date: date | None = Query(
        None, description="Any date in the target week (defaults to today)"
    ),
    auth: AuthContext = Depends(requires_permission("PERM-ERP:timetable:read")),
    db: AsyncSession = Depends(get_db),
):
    """Get the weekly timetable for a class, with exception overlays."""
    service = ERPService(db)
    result = await service.get_class_weekly_timetable(
        class_id=class_id,
        target_date=target_date,
        auth=auth,
    )
    return success_response(result)


@router.get(
    "/teacher/{teacher_id}/weekly",
    summary="Weekly timetable for a teacher",
    response_description="Weekly timetable with exceptions",
)
async def get_teacher_weekly_timetable(
    teacher_id: uuid.UUID,
    target_date: date | None = Query(
        None, description="Any date in the target week (defaults to today)"
    ),
    auth: AuthContext = Depends(requires_permission("PERM-ERP:timetable:read")),
    db: AsyncSession = Depends(get_db),
):
    """Get the weekly timetable for a teacher, with exception overlays."""
    service = ERPService(db)
    result = await service.get_teacher_weekly_timetable(
        teacher_id=teacher_id,
        target_date=target_date,
        auth=auth,
    )
    return success_response(result)


@router.get(
    "/me/weekly",
    summary="My weekly timetable",
    response_description="Weekly timetable for current user",
)
async def get_my_weekly_timetable(
    target_date: date | None = Query(
        None, description="Any date in the target week (defaults to today)"
    ),
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the weekly timetable for the current user."""
    service = ERPService(db)
    result = await service.get_my_weekly_timetable(
        target_date=target_date,
        auth=auth,
    )
    return success_response(result)


@router.post(
    "/exceptions",
    status_code=201,
    summary="Create timetable exception",
    response_description="Created timetable exception",
)
async def create_timetable_exception(
    body: TimetableExceptionCreateRequest,
    request: Request,
    auth: AuthContext = Depends(
        requires_permission("PERM-ERP:timetable-exception:create")
    ),
    db: AsyncSession = Depends(get_db),
):
    """Create an exception for a timetable slot."""
    service = ERPService(db)
    result = await service.create_timetable_exception(
        body=body,
        auth=auth,
        ip_address=get_client_ip(request),
    )
    return success_response(result)


@router.get(
    "/exceptions",
    summary="List timetable exceptions",
    response_description="Filtered list of timetable exceptions",
)
async def list_timetable_exceptions(
    timetable_slot_id: uuid.UUID | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    exception_type: str | None = Query(
        None, pattern="^(CANCELED|SUBSTITUTED|ROOM_CHANGED)$"
    ),
    auth: AuthContext = Depends(
        requires_permission("PERM-ERP:timetable-exception:read")
    ),
    db: AsyncSession = Depends(get_db),
):
    """List timetable exceptions with optional filters."""
    service = ERPService(db)
    result = await service.list_timetable_exceptions(
        timetable_slot_id=timetable_slot_id,
        date_from=date_from,
        date_to=date_to,
        exception_type=exception_type,
        auth=auth,
    )
    return list_response(result)
