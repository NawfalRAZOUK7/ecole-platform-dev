"""Result endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.permissions import PERM_LMS_RESULT_READ
from app.core.response import clamp_page_size, list_response
from app.services.lms import LMSService

router = APIRouter(prefix="/results", tags=["lms-results"])


@router.get(
    "",
    summary="List student results",
    response_description="Paginated list of grades and results",
)
async def list_results(
    student_id: uuid.UUID | None = Query(None),
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    auth: AuthContext = Depends(requires_permission(PERM_LMS_RESULT_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = LMSService(db)
    items, next_cursor, has_more = await service.list_results(
        student_id=student_id,
        cursor=cursor,
        limit=clamp_page_size(limit),
        auth=auth,
    )
    return list_response(items, next_cursor=next_cursor, has_more=has_more)
