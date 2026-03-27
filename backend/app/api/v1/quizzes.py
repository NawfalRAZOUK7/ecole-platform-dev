"""Quiz endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.permissions import (
    PERM_QUIZ_ANALYTICS,
    PERM_QUIZ_ATTEMPT,
    PERM_QUIZ_CREATE,
    PERM_QUIZ_MANAGE,
    PERM_QUIZ_PUBLISH,
    PERM_QUIZ_READ,
)
from app.core.request_utils import get_client_ip
from app.core.response import clamp_page_size, list_response, success_response
from app.schemas.quiz import QuizCreateRequest, QuizRespondRequest, QuizUpdateRequest
from app.services.lms import LMSService

router = APIRouter(tags=["quiz-engine"])


@router.post("/quizzes", status_code=201, summary="Create a quiz")
async def create_quiz(
    body: QuizCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_QUIZ_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    service = LMSService(db)
    return success_response(
        await service.create_quiz(
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get("/quizzes", summary="List quizzes")
async def list_quizzes(
    subject: str | None = Query(None),
    level_band: str | None = Query(None),
    status: str | None = Query(None),
    difficulty: str | None = Query(None),
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    auth: AuthContext = Depends(requires_permission(PERM_QUIZ_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = LMSService(db)
    items, next_cursor, has_more = await service.list_quizzes(
        subject=subject,
        level_band=level_band,
        status=status,
        difficulty=difficulty,
        cursor=cursor,
        limit=clamp_page_size(limit),
        auth=auth,
    )
    return list_response(items, next_cursor=next_cursor, has_more=has_more)


@router.get("/quizzes/{quiz_id}", summary="Get quiz details with questions")
async def get_quiz(
    quiz_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_QUIZ_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = LMSService(db)
    return success_response(await service.get_quiz(quiz_id=quiz_id, auth=auth))


@router.put("/quizzes/{quiz_id}", summary="Update quiz")
async def update_quiz(
    quiz_id: uuid.UUID,
    body: QuizUpdateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_QUIZ_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    service = LMSService(db)
    return success_response(
        await service.update_quiz(
            quiz_id=quiz_id,
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.post("/quizzes/{quiz_id}/publish", summary="Publish a quiz")
async def publish_quiz(
    quiz_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_QUIZ_PUBLISH)),
    db: AsyncSession = Depends(get_db),
):
    service = LMSService(db)
    return success_response(
        await service.publish_quiz(
            quiz_id=quiz_id,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.post("/quizzes/{quiz_id}/start", status_code=201, summary="Start a quiz attempt")
async def start_attempt(
    quiz_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_QUIZ_ATTEMPT)),
    db: AsyncSession = Depends(get_db),
):
    service = LMSService(db)
    return success_response(
        await service.start_quiz_attempt(
            quiz_id=quiz_id,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.post("/attempts/{attempt_id}/respond", summary="Submit answer for one question")
async def respond_to_question(
    attempt_id: uuid.UUID,
    body: QuizRespondRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_QUIZ_ATTEMPT)),
    db: AsyncSession = Depends(get_db),
):
    service = LMSService(db)
    return success_response(
        await service.respond_to_quiz_question(
            attempt_id=attempt_id,
            body=body,
            auth=auth,
        )
    )


@router.post("/attempts/{attempt_id}/submit", summary="Submit attempt for grading")
async def submit_attempt(
    attempt_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_QUIZ_ATTEMPT)),
    db: AsyncSession = Depends(get_db),
):
    service = LMSService(db)
    return success_response(
        await service.submit_quiz_attempt(
            attempt_id=attempt_id,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get("/attempts/{attempt_id}/results", summary="View attempt results")
async def get_attempt_results(
    attempt_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_QUIZ_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = LMSService(db)
    return success_response(
        await service.get_quiz_attempt_results(
            attempt_id=attempt_id,
            auth=auth,
        )
    )


@router.get("/quizzes/{quiz_id}/analytics", summary="Quiz analytics")
async def quiz_analytics(
    quiz_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_QUIZ_ANALYTICS)),
    db: AsyncSession = Depends(get_db),
):
    service = LMSService(db)
    return success_response(
        await service.get_quiz_analytics(
            quiz_id=quiz_id,
            auth=auth,
        )
    )
