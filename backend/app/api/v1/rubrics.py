"""Rubric engine endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, get_current_user, requires_permission
from app.core.exceptions import NotFoundError
from app.core.permissions import (
    PERM_LMS_RUBRIC_CREATE,
    PERM_LMS_RUBRIC_READ,
    PERM_LMS_SUBMISSION_GRADE,
)
from app.core.request_utils import get_client_ip
from app.core.response import list_response, success_response
from app.schemas.rubric import RubricCreateRequest, RubricScoreInput
from app.services.audit import AuditService
from app.core.unit_of_work import UnitOfWork
from app.repositories.rubric import RubricRepository
from app.services.rubric import RubricService

router = APIRouter(tags=["rubric-engine"])


@router.post("/rubrics", status_code=201, summary="Create a rubric")
async def create_rubric(
    body: RubricCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_LMS_RUBRIC_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    service = RubricService(db)
    return success_response(
        await service.create_rubric(
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get("/rubrics", summary="List rubrics")
async def list_rubrics(
    auth: AuthContext = Depends(requires_permission(PERM_LMS_RUBRIC_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = RubricService(db)
    items = await service.list_rubrics(auth=auth)
    return list_response(items, next_cursor=None, has_more=False)


@router.get("/rubrics/{rubric_id}", summary="Get rubric details with criteria and levels")
async def get_rubric(
    rubric_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_LMS_RUBRIC_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = RubricService(db)
    return success_response(await service.get_rubric(rubric_id=rubric_id, auth=auth))


@router.put("/rubrics/{rubric_id}", summary="Compatibility: update rubric")
async def update_rubric(
    rubric_id: uuid.UUID,
    body: RubricCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_LMS_RUBRIC_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    service = RubricService(db)
    source = await service.rubric_repo.get_rubric(rubric_id)
    if source is None:
        raise NotFoundError("Rubric not found", error_code="ERR-LMS-404")
    service._ensure_can_duplicate_rubric(source, auth)

    async with UnitOfWork(db) as uow:
        repo = RubricRepository(uow.session)
        audit = AuditService(uow.session)
        rubric = await repo.get_rubric(rubric_id)
        if rubric is None:
            raise NotFoundError("Rubric not found", error_code="ERR-LMS-404")

        rubric.title = body.title
        rubric.description = body.description
        rubric.total_points = body.total_points
        rubric.is_template = body.is_template
        rubric.criteria.clear()
        await uow.session.flush()

        for criterion_index, criterion_input in enumerate(body.criteria):
            criterion = await repo.create_criterion(
                rubric_id=rubric.id,
                title=criterion_input.title,
                description=criterion_input.description,
                weight=criterion_input.weight,
                position=criterion_input.position
                if criterion_input.position >= 0
                else criterion_index,
            )
            for level_index, level_input in enumerate(criterion_input.levels):
                await repo.create_level(
                    criterion_id=criterion.id,
                    label=level_input.label,
                    description=level_input.description,
                    points=level_input.points,
                    position=level_input.position
                    if level_input.position >= 0
                    else level_index,
                )

        updated = await repo.get_rubric(rubric_id)
        await audit.log_event(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            action_type="RUBRIC_UPDATED",
            outcome="success",
            target_type="rubric",
            target_id=rubric_id,
            entity_after={
                "title": body.title,
                "criterion_count": len(body.criteria),
            },
            ip_address=get_client_ip(request),
        )
        await uow.commit()

    return success_response(service._rubric_to_dict(updated))


@router.post("/rubrics/{rubric_id}/duplicate", status_code=201, summary="Duplicate a rubric")
async def duplicate_rubric(
    rubric_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_LMS_RUBRIC_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    service = RubricService(db)
    return success_response(
        await service.duplicate_rubric(
            rubric_id=rubric_id,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.post(
    "/submissions/{submission_id}/grade-rubric",
    status_code=201,
    summary="Grade a submission with its rubric",
)
async def grade_submission_with_rubric(
    submission_id: uuid.UUID,
    scores: list[RubricScoreInput],
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_LMS_SUBMISSION_GRADE)),
    db: AsyncSession = Depends(get_db),
):
    service = RubricService(db)
    return success_response(
        await service.grade_with_rubric(
            submission_id=submission_id,
            scores=scores,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "/submissions/{submission_id}/rubric-results",
    summary="View rubric results for a submission",
)
async def get_rubric_results(
    submission_id: uuid.UUID,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = RubricService(db)
    return success_response(
        await service.get_rubric_results(
            submission_id=submission_id,
            auth=auth,
        )
    )
