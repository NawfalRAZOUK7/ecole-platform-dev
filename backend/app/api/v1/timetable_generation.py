"""Timetable constraint management and generation endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.request_utils import get_client_ip
from app.core.response import list_response, success_response
from app.schemas.timetable_generation import (
    TimetableConstraintSetRequest,
    TimetableGenerateRequest,
)
from app.services.timetable_generator import TimetableGeneratorService

router = APIRouter(prefix="/timetable", tags=["erp-timetable-generation"])


@router.post("/constraints", summary="Replace timetable generation constraints")
async def set_timetable_constraints(
    body: TimetableConstraintSetRequest,
    request: Request,
    auth: AuthContext = Depends(
        requires_permission("PERM-ERP:timetable-constraint:manage")
    ),
    db: AsyncSession = Depends(get_db),
):
    service = TimetableGeneratorService(db)
    items = await service.set_constraints(
        body=body,
        auth=auth,
        ip_address=get_client_ip(request),
    )
    return list_response(items, next_cursor=None, has_more=False)


@router.get("/constraints", summary="List timetable generation constraints")
async def list_timetable_constraints(
    academic_year_id: uuid.UUID = Query(...),
    auth: AuthContext = Depends(
        requires_permission("PERM-ERP:timetable-constraint:manage")
    ),
    db: AsyncSession = Depends(get_db),
):
    service = TimetableGeneratorService(db)
    items = await service.list_constraints(
        academic_year_id=academic_year_id,
        auth=auth,
    )
    return list_response(items, next_cursor=None, has_more=False)


@router.post("/generate", summary="Generate a timetable preview job")
async def generate_timetable(
    body: TimetableGenerateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-ERP:timetable:generate")),
    db: AsyncSession = Depends(get_db),
):
    service = TimetableGeneratorService(db)
    return success_response(
        await service.generate(
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get("/generate/{job_id}", summary="Get timetable generation job status")
async def get_timetable_generation_job(
    job_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission("PERM-ERP:timetable:generate")),
    db: AsyncSession = Depends(get_db),
):
    service = TimetableGeneratorService(db)
    return success_response(
        await service.get_job_status(
            job_id=job_id,
            auth=auth,
        )
    )


@router.get(
    "/generate/{job_id}/preview",
    summary="Preview generated timetable slots without applying them",
)
async def preview_generated_timetable(
    job_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission("PERM-ERP:timetable:generate")),
    db: AsyncSession = Depends(get_db),
):
    service = TimetableGeneratorService(db)
    return success_response(
        await service.preview_generated(
            job_id=job_id,
            auth=auth,
        )
    )


@router.post("/generate/{job_id}/apply", summary="Apply a generated timetable preview")
async def apply_generated_timetable(
    job_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-ERP:timetable:generate")),
    db: AsyncSession = Depends(get_db),
):
    service = TimetableGeneratorService(db)
    return success_response(
        await service.apply_generated(
            job_id=job_id,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )
