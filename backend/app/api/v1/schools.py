"""School management API endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission, requires_role
from app.core.permissions import (
    PERM_ADM_SCHOOL_MANAGE,
    PERM_ADM_SCHOOL_READ,
    SUP,
)
from app.core.response import list_response, success_response
from app.schemas.school import SchoolCreateRequest, SchoolUpdateRequest
from app.services.school import SchoolService

router = APIRouter(prefix="/schools", tags=["schools"])


@router.post(
    "",
    status_code=201,
    summary="Create a school",
    response_description="Created school",
)
async def create_school(
    body: SchoolCreateRequest,
    auth: AuthContext = Depends(requires_role(SUP)),
    db: AsyncSession = Depends(get_db),
):
    service = SchoolService(db)
    return success_response(await service.create_school(body=body, auth=auth))


@router.get(
    "",
    summary="List schools",
    response_description="List of schools",
)
async def list_schools(
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = Query(None, pattern="^(active|suspended|trial)$"),
    auth: AuthContext = Depends(requires_permission(PERM_ADM_SCHOOL_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = SchoolService(db)
    items, next_cursor, has_more = await service.list_schools(
        auth=auth,
        cursor=cursor,
        limit=limit,
        status=status,
    )
    return list_response(items, next_cursor=next_cursor, has_more=has_more)


@router.get(
    "/{school_id}",
    summary="Get a school",
    response_description="School details",
)
async def get_school(
    school_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_ADM_SCHOOL_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = SchoolService(db)
    return success_response(await service.get_school(school_id=school_id, auth=auth))


@router.patch(
    "/{school_id}",
    summary="Update a school",
    response_description="Updated school",
)
async def update_school(
    school_id: uuid.UUID,
    body: SchoolUpdateRequest,
    auth: AuthContext = Depends(requires_permission(PERM_ADM_SCHOOL_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    service = SchoolService(db)
    return success_response(
        await service.update_school(
            school_id=school_id,
            body=body,
            auth=auth,
        )
    )


@router.delete(
    "/{school_id}",
    summary="Deactivate a school",
    response_description="Soft-deleted school",
)
async def delete_school(
    school_id: uuid.UUID,
    auth: AuthContext = Depends(requires_role(SUP)),
    db: AsyncSession = Depends(get_db),
):
    service = SchoolService(db)
    return success_response(
        await service.deactivate_school(
            school_id=school_id,
            auth=auth,
        )
    )
