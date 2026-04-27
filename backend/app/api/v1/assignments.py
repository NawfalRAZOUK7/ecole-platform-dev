"""Assignment endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    AuthContext,
    requires_any_permission,
    requires_permission,
)
from app.core.filtering import FilterSpec, SortSpec, parse_filters, parse_sort
from app.core.permissions import PERM_LMS_ASSIGNMENT_CREATE, PERM_LMS_ASSIGNMENT_READ
from app.core.request_utils import get_client_ip
from app.core.response import clamp_page_size, list_response, success_response
from app.core.search import parse_search
from app.schemas.lms import AssignmentCreateRequest
from app.services.lms import AssignmentService

router = APIRouter(prefix="/assignments", tags=["lms-assignments"])


@router.post(
    "",
    status_code=201,
    summary="Create an assignment",
    response_description="Created assignment record",
)
async def create_assignment(
    body: AssignmentCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_LMS_ASSIGNMENT_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    service = AssignmentService(db)
    return success_response(
        await service.create_assignment(
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "",
    summary="List assignments",
    response_description="Paginated list of assignments",
)
async def list_assignments(
    course_id: uuid.UUID | None = Query(None),
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    filters: FilterSpec = Depends(parse_filters),
    sort: SortSpec = Depends(parse_sort),
    search: str | None = Depends(parse_search),
    auth: AuthContext = Depends(
        requires_any_permission(PERM_LMS_ASSIGNMENT_READ, PERM_LMS_ASSIGNMENT_CREATE)
    ),
    db: AsyncSession = Depends(get_db),
):
    service = AssignmentService(db)
    items, next_cursor, has_more = await service.list_assignments(
        course_id=course_id,
        filters=filters,
        sort=sort,
        search=search,
        cursor=cursor,
        limit=clamp_page_size(limit),
        auth=auth,
    )
    return list_response(
        items,
        next_cursor=next_cursor,
        has_more=has_more,
        filters_applied=filters.as_dict() if filters.items else None,
        sort_by=sort.as_list() if sort.fields else None,
        search_term=search,
    )


@router.post(
    "/{assignment_id}/exercise-pdf",
    status_code=201,
    summary="Upload exercise PDF for a PRINTABLE_PDF assignment",
)
async def upload_exercise_pdf(
    assignment_id: uuid.UUID,
    file: UploadFile = File(...),
    request: Request = None,
    auth: AuthContext = Depends(requires_permission(PERM_LMS_ASSIGNMENT_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    service = AssignmentService(db)
    return success_response(
        await service.upload_exercise_pdf(
            assignment_id=assignment_id,
            file=file.file,
            filename=file.filename or "exercise.pdf",
            mime_type=file.content_type or "application/octet-stream",
            auth=auth,
            ip_address=get_client_ip(request) if request else None,
        )
    )


@router.get(
    "/{assignment_id}/exercise-pdf",
    summary="Download the exercise PDF",
    response_description="PDF file binary",
)
async def download_exercise_pdf(
    assignment_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_LMS_ASSIGNMENT_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    service = AssignmentService(db)
    path, media_type, filename = await service.get_exercise_pdf(
        assignment_id=assignment_id,
        auth=auth,
    )
    return FileResponse(path=path, media_type=media_type, filename=filename)
