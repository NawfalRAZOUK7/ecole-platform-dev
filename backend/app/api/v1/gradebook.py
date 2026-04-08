"""Weighted gradebook endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.request_utils import get_client_ip
from app.core.response import list_response, success_response
from app.schemas.gradebook import GradeCategorySetRequest
from app.services.gradebook import GradebookService

router = APIRouter(prefix="/gradebook", tags=["gradebook"])


@router.post(
    "/categories", status_code=201, summary="Set grade categories for a class period"
)
async def set_grade_categories(
    body: GradeCategorySetRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-LMS:gradebook:manage")),
    db: AsyncSession = Depends(get_db),
):
    service = GradebookService(db)
    items = await service.set_grade_categories(
        body=body,
        auth=auth,
        ip_address=get_client_ip(request),
    )
    return list_response(items, next_cursor=None, has_more=False)


@router.get(
    "/categories/{class_id}/{period_id}",
    summary="List grade categories for a class period",
)
async def list_grade_categories(
    class_id: uuid.UUID,
    period_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission("PERM-LMS:gradebook:read")),
    db: AsyncSession = Depends(get_db),
):
    service = GradebookService(db)
    items = await service.list_grade_categories(
        class_id=class_id,
        period_id=period_id,
        auth=auth,
    )
    return list_response(items, next_cursor=None, has_more=False)


@router.post(
    "/compute/{class_id}/{period_id}",
    summary="Compute weighted averages for a class period",
)
async def compute_class_averages(
    class_id: uuid.UUID,
    period_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-LMS:gradebook:manage")),
    db: AsyncSession = Depends(get_db),
):
    service = GradebookService(db)
    items = await service.compute_class_averages(
        class_id=class_id,
        period_id=period_id,
        auth=auth,
        ip_address=get_client_ip(request),
    )
    return list_response(items, next_cursor=None, has_more=False)


@router.get(
    "/transcript/{student_id}",
    summary="Get a student's transcript for an academic year",
)
async def get_student_transcript(
    student_id: uuid.UUID,
    academic_year_id: uuid.UUID = Query(...),
    auth: AuthContext = Depends(requires_permission("PERM-LMS:gradebook:read")),
    db: AsyncSession = Depends(get_db),
):
    service = GradebookService(db)
    return success_response(
        await service.get_student_transcript(
            student_id=student_id,
            academic_year_id=academic_year_id,
            auth=auth,
        )
    )


@router.get(
    "/{class_id}/{period_id}",
    summary="Get the gradebook matrix for a class period",
)
async def get_gradebook(
    class_id: uuid.UUID,
    period_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission("PERM-LMS:gradebook:read")),
    db: AsyncSession = Depends(get_db),
):
    service = GradebookService(db)
    return success_response(
        await service.get_gradebook(
            class_id=class_id,
            period_id=period_id,
            auth=auth,
        )
    )
