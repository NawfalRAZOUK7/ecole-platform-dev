"""Shared review endpoints — parent views child's learning sessions and adds comments.

Phase B1: Interface de révision partagée parent-enfant.
Endpoints:
  GET  /shared-reviews/{child_id}/sessions              — list child's recent sessions
  GET  /shared-reviews/{child_id}/sessions/{session_id}  — session detail
  POST /shared-reviews/{child_id}/sessions/{session_id}/comments — add comment
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.permissions import PERM_PROGRESS_READ
from app.core.response import success_response
from app.services.shared_review import SharedReviewService

router = APIRouter(prefix="/shared-reviews", tags=["shared-review"])


class CommentCreate(BaseModel):
    """Request body for adding a comment."""

    text: str = Field(..., min_length=1, max_length=1000)
    emoji: str | None = Field(None, max_length=10)


@router.get(
    "/{child_id}/sessions",
    summary="List child's recent learning sessions",
    response_description="Unified list of quiz attempts, content, writing, activities",
)
async def list_child_sessions(
    child_id: uuid.UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    auth: AuthContext = Depends(requires_permission(PERM_PROGRESS_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = SharedReviewService(db)
    data = await service.list_child_sessions(
        child_id=child_id,
        auth=auth,
        limit=limit,
        offset=offset,
    )
    return success_response(data)


@router.get(
    "/{child_id}/sessions/{session_id}",
    summary="Get session detail with comments",
    response_description="Detailed session info including parent comments",
)
async def get_session_detail(
    child_id: uuid.UUID,
    session_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_PROGRESS_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = SharedReviewService(db)
    data = await service.get_session_detail(
        child_id=child_id,
        session_id=session_id,
        auth=auth,
    )
    return success_response(data)


@router.post(
    "/{child_id}/sessions/{session_id}/comments",
    summary="Add parent comment/encouragement",
    response_description="Created comment",
)
async def add_comment(
    child_id: uuid.UUID,
    session_id: uuid.UUID,
    body: CommentCreate,
    auth: AuthContext = Depends(requires_permission(PERM_PROGRESS_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = SharedReviewService(db)
    data = await service.add_comment(
        child_id=child_id,
        session_id=session_id,
        text=body.text,
        emoji=body.emoji,
        auth=auth,
    )
    return success_response(data)
