"""Teacher API endpoints — classes, students, submissions for the teacher dashboard."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.permissions import PERM_ERP_CLASS_READ, PERM_LMS_SUBMISSION_GRADE
from app.core.response import list_response, success_response
from app.services.auth.profile import ProfileService

router = APIRouter(prefix="/teacher", tags=["teacher"])


@router.get(
    "/classes",
    summary="List teacher's assigned classes",
    response_description="Assigned classes with student and course counts",
)
async def list_teacher_classes(
    auth: AuthContext = Depends(requires_permission(PERM_ERP_CLASS_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = ProfileService(db)
    return success_response(await service.list_teacher_classes(auth))


@router.get(
    "/classes/{class_id}/students",
    summary="List students in a class",
    response_description="Enrolled students in the requested class",
)
async def list_class_students(
    class_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_ERP_CLASS_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = ProfileService(db)
    return success_response(
        await service.list_class_students(class_id=class_id, auth=auth)
    )


@router.get(
    "/submissions",
    summary="List submissions for grading",
    response_description="Paginated teacher submissions list",
)
async def list_teacher_submissions(
    auth: AuthContext = Depends(requires_permission(PERM_LMS_SUBMISSION_GRADE)),
    db: AsyncSession = Depends(get_db),
    assignment_id: uuid.UUID | None = Query(None),
    course_id: uuid.UUID | None = Query(None),
    status: str | None = Query(None, description="Filter: submitted, graded, draft"),
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    service = ProfileService(db)
    data, next_cursor, has_more = await service.list_teacher_submissions(
        auth=auth,
        assignment_id=assignment_id,
        course_id=course_id,
        status=status,
        cursor=cursor,
        limit=limit,
    )
    return list_response(data, next_cursor=next_cursor, has_more=has_more)


@router.get(
    "/periods",
    summary="List active periods",
    response_description="Active periods for the teacher's school",
)
async def list_active_periods(
    auth: AuthContext = Depends(requires_permission(PERM_ERP_CLASS_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = ProfileService(db)
    return success_response(await service.list_active_periods(auth))
