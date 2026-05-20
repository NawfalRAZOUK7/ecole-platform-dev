"""Question bank endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.permissions import (
    PERM_LMS_QUESTION_BANK_MANAGE,
    PERM_LMS_QUESTION_BANK_READ,
)
from app.core.request_utils import get_client_ip
from app.core.response import clamp_page_size, list_response, success_response
from app.schemas.lms.question_bank import (
    GenerateQuizFromBankRequest,
    QuestionBankCreateRequest,
)
from app.services.lms.question_bank import QuestionBankService

router = APIRouter(tags=["question-bank"])


@router.post(
    "/question-bank", status_code=201, summary="Add a question to the question bank"
)
async def add_question(
    body: QuestionBankCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_LMS_QUESTION_BANK_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    service = QuestionBankService(db)
    return success_response(
        await service.add_question(
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get("/question-bank", summary="List question bank items")
async def list_questions(
    subject: str | None = Query(None),
    level: str | None = Query(None),
    difficulty: str | None = Query(None),
    tags: list[str] | None = Query(None),
    search: str | None = Query(None),
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    auth: AuthContext = Depends(requires_permission(PERM_LMS_QUESTION_BANK_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = QuestionBankService(db)
    items, next_cursor, has_more = await service.list_questions(
        subject=subject,
        level=level,
        difficulty=difficulty,
        tags=tags,
        search=search,
        cursor=cursor,
        limit=clamp_page_size(limit),
        auth=auth,
    )
    return list_response(items, next_cursor=next_cursor, has_more=has_more)


@router.post(
    "/question-bank/import/{quiz_id}",
    status_code=201,
    summary="Import questions from an existing quiz into the bank",
)
async def import_from_quiz(
    quiz_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_LMS_QUESTION_BANK_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    service = QuestionBankService(db)
    return success_response(
        await service.import_from_quiz(
            quiz_id=quiz_id,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.post(
    "/question-bank/generate-quiz",
    status_code=201,
    summary="Generate a draft quiz from question bank items",
)
async def generate_quiz_from_bank(
    body: GenerateQuizFromBankRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_LMS_QUESTION_BANK_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    service = QuestionBankService(db)
    return success_response(
        await service.generate_quiz_from_bank(
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get("/question-bank/stats", summary="Question bank usage statistics")
async def get_question_stats(
    auth: AuthContext = Depends(requires_permission(PERM_LMS_QUESTION_BANK_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = QuestionBankService(db)
    return list_response(
        await service.get_question_stats(auth=auth),
        next_cursor=None,
        has_more=False,
    )
