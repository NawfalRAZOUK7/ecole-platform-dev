"""Onboarding applications — public submission + SuperAdmin review/approval."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, get_current_user
from app.core.exceptions import NotFoundError
from app.core.permissions import SUP
from app.core.request_utils import get_client_ip
from app.core.response import list_response, success_response
from app.models.onboarding import ApplicationStatus, ApplicationType
from app.schemas.onboarding import (
    ApplicationReviewRequest,
    FormalSchoolApplicationRequest,
    MicroSchoolApplicationRequest,
)
from app.services.platform.onboarding import OnboardingService

router = APIRouter(tags=["onboarding"])


def _require_sup(auth: AuthContext) -> None:
    if auth.role != SUP:
        # Hide the endpoint's existence from non-platform users.
        raise NotFoundError("Not found", error_code="ERR-RES-404")


# ── Public (anonymous) application submission ──


@router.post(
    "/applications/formal-school",
    status_code=201,
    summary="Apply to register a formal school (public)",
)
async def apply_formal_school(
    body: FormalSchoolApplicationRequest,
    db: AsyncSession = Depends(get_db),
):
    service = OnboardingService(db)
    return success_response(
        await service.create_application(
            application_type=ApplicationType.FORMAL_SCHOOL.value, body=body
        )
    )


@router.post(
    "/applications/micro-school",
    status_code=201,
    summary="Apply to register a micro-école / educator (public)",
)
async def apply_micro_school(
    body: MicroSchoolApplicationRequest,
    db: AsyncSession = Depends(get_db),
):
    service = OnboardingService(db)
    return success_response(
        await service.create_application(
            application_type=ApplicationType.MICRO_SCHOOL.value, body=body
        )
    )


@router.post(
    "/applications/{application_id}/attachments",
    status_code=201,
    summary="Attach a document/photo to an application (public)",
)
async def add_attachment(
    application_id: uuid.UUID,
    file: UploadFile = File(...),
    kind: str = Form("other"),
    db: AsyncSession = Depends(get_db),
):
    service = OnboardingService(db)
    return success_response(
        await service.add_attachment(
            application_id=application_id, file=file, kind=kind
        )
    )


# ── SuperAdmin platform review ──


@router.get(
    "/platform/applications",
    summary="List onboarding applications (SuperAdmin)",
)
async def list_applications(
    status: str | None = Query(None),
    type: str | None = Query(None),
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_sup(auth)
    service = OnboardingService(db)
    return list_response(
        await service.list_applications(status=status, application_type=type)
    )


@router.get(
    "/platform/applications/{application_id}",
    summary="Get one onboarding application (SuperAdmin)",
)
async def get_application(
    application_id: uuid.UUID,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_sup(auth)
    service = OnboardingService(db)
    return success_response(await service.get_application(application_id))


@router.post(
    "/platform/applications/{application_id}/approve",
    summary="Approve an application — provisions the tenant (SuperAdmin)",
)
async def approve_application(
    application_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_sup(auth)
    service = OnboardingService(db)
    return success_response(
        await service.approve(
            application_id=application_id,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.post(
    "/platform/applications/{application_id}/resend-activation",
    summary="Re-issue the owner's activation link (SuperAdmin)",
)
async def resend_activation(
    application_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_sup(auth)
    service = OnboardingService(db)
    return success_response(
        await service.resend_activation(
            application_id=application_id,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.post(
    "/platform/applications/{application_id}/reject",
    summary="Reject an application (SuperAdmin)",
)
async def reject_application(
    application_id: uuid.UUID,
    body: ApplicationReviewRequest,
    request: Request,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_sup(auth)
    service = OnboardingService(db)
    return success_response(
        await service.review(
            application_id=application_id,
            new_status=ApplicationStatus.REJECTED.value,
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.post(
    "/platform/applications/{application_id}/request-info",
    summary="Request more info on an application (SuperAdmin)",
)
async def request_info_application(
    application_id: uuid.UUID,
    body: ApplicationReviewRequest,
    request: Request,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_sup(auth)
    service = OnboardingService(db)
    return success_response(
        await service.review(
            application_id=application_id,
            new_status=ApplicationStatus.NEEDS_INFO.value,
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )
