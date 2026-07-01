"""Progress endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.permissions import PERM_PROGRESS_CLASS_READ, PERM_PROGRESS_READ
from app.core.response import success_response
from app.services.lms import ProgressService

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get(
    "/student/{student_id}",
    summary="Get student progress dashboard",
    response_description="Chart-ready student progress data",
)
async def get_student_progress(
    student_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_PROGRESS_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = ProgressService(db)
    return success_response(
        await service.get_student_progress_for_user(student_id=student_id, auth=auth)
    )


@router.get(
    "/class/{class_id}",
    summary="Get class progress summary",
    response_description="Chart-ready class progress data",
)
async def get_class_progress(
    class_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_PROGRESS_CLASS_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = ProgressService(db)
    return success_response(
        await service.get_class_progress_for_user(class_id=class_id, auth=auth)
    )


@router.get(
    "/me",
    summary="Get my progress (student shortcut)",
    response_description="Chart-ready progress data for current student",
)
async def get_my_progress(
    auth: AuthContext = Depends(requires_permission(PERM_PROGRESS_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = ProgressService(db)
    return success_response(await service.get_my_progress(auth=auth))


@router.get(
    "/children",
    summary="Get children's progress overview (parent)",
    response_description="Chart-ready progress overview for all linked children",
)
async def get_children_progress(
    auth: AuthContext = Depends(requires_permission(PERM_PROGRESS_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = ProgressService(db)
    return success_response(await service.get_children_progress_for_parent(auth=auth))
