"""Assessment endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.filtering import FilterSpec, SortSpec, parse_filters, parse_sort
from app.core.permissions import (
    PERM_LMS_ASSESSMENT_CREATE,
    PERM_LMS_ASSESSMENT_PUBLISH,
    PERM_LMS_ASSESSMENT_READ,
    PERM_LMS_ASSESSMENT_SUBMIT,
)
from app.core.request_utils import get_client_ip
from app.core.response import clamp_page_size, list_response, success_response
from app.core.search import parse_search
from app.schemas.lms import AssessmentCreateRequest, AssessmentResultSubmitRequest
from app.services.lms import ProgressService

router = APIRouter(prefix="/assessments", tags=["lms-assessments"])


@router.post(
    "",
    status_code=201,
    summary="Create an assessment",
    response_description="Created assessment record",
)
async def create_assessment(
    body: AssessmentCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_LMS_ASSESSMENT_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    service = ProgressService(db)
    return success_response(
        await service.create_assessment(
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "",
    summary="List assessments",
    response_description="Paginated list of assessments",
)
async def list_assessments(
    class_id: uuid.UUID | None = Query(None),
    status: str | None = Query(None),
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    filters: FilterSpec = Depends(parse_filters),
    sort: SortSpec = Depends(parse_sort),
    search: str | None = Depends(parse_search),
    auth: AuthContext = Depends(requires_permission(PERM_LMS_ASSESSMENT_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = ProgressService(db)
    items, next_cursor, has_more = await service.list_assessments(
        class_id=class_id,
        status=status,
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
    "/{assessment_id}/publish",
    status_code=200,
    summary="Publish an assessment",
    response_description="Published assessment",
)
async def publish_assessment(
    assessment_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_LMS_ASSESSMENT_PUBLISH)),
    db: AsyncSession = Depends(get_db),
):
    service = ProgressService(db)
    return success_response(
        await service.publish_assessment(
            assessment_id=assessment_id,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.post(
    "/{assessment_id}/results",
    status_code=201,
    summary="Submit assessment result",
    response_description="Assessment result record",
)
async def submit_assessment_result(
    assessment_id: uuid.UUID,
    body: AssessmentResultSubmitRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_LMS_ASSESSMENT_SUBMIT)),
    db: AsyncSession = Depends(get_db),
):
    service = ProgressService(db)
    return success_response(
        await service.submit_assessment_result(
            assessment_id=assessment_id,
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )
