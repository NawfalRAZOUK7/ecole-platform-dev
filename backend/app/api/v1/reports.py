"""Phase 14 reports API."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.exceptions import AuthenticationError, ValidationError
from app.core.permissions import PERM_REP_REPORT_GENERATE, PERM_REP_REPORT_READ
from app.core.response import clamp_page_size, list_response, success_response
from app.core.security import decode_access_token
from app.core.storage import storage
from app.core.tasks import enqueue_task
from app.models.iam import Session
from app.schemas.reports import ReportGenerateRequest
from app.services.audit import AuditService
from app.services.reports import ReportsService

router = APIRouter(prefix="/reports", tags=["reports"])

_bearer_scheme = HTTPBearer(auto_error=False)


def _get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


async def _optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> AuthContext | None:
    if credentials is None:
        return None

    payload = decode_access_token(credentials.credentials)
    session_id = uuid.UUID(payload["session_id"])
    session_result = await db.execute(
        select(Session).where(Session.id == session_id, Session.revoke_at.is_(None))
    )
    if session_result.scalar_one_or_none() is None:
        raise AuthenticationError(
            "Session has been revoked",
            error_code="ERR-IAM-401",
        )
    return AuthContext(
        user_id=uuid.UUID(payload["sub"]),
        role=payload["role"],
        school_id=uuid.UUID(payload["school_id"]),
        session_id=session_id,
        permissions=set(),
    )


@router.post(
    "/generate",
    summary="Queue a report generation job",
    response_description="Report job metadata",
)
async def generate_report(
    body: ReportGenerateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_REP_REPORT_GENERATE)),
    db: AsyncSession = Depends(get_db),
):
    service = ReportsService(db)
    audit = AuditService(db)
    payload, cache_hit = await service.submit_report_job(
        school_id=auth.school_id,
        requester_id=auth.user_id,
        requester_role=auth.role,
        request=body,
    )
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="report.generate.request",
        target_type="report_job",
        target_id=uuid.UUID(payload["id"]),
        outcome="success",
        entity_after={"request": body.model_dump(mode="json"), "job": payload},
        ip_address=_get_client_ip(request),
    )
    await db.commit()
    if not cache_hit:
        await enqueue_task("task_generate_report", job_id=payload["id"])
    return success_response(payload)


@router.get(
    "",
    summary="List report jobs",
    response_description="Report history for the current user",
)
async def list_reports(
    type: str | None = Query(None),
    period: uuid.UUID | None = Query(None),
    status: str | None = Query(None),
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    auth: AuthContext = Depends(requires_permission(PERM_REP_REPORT_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = ReportsService(db)
    items, next_cursor, has_more = await service.list_report_jobs(
        school_id=auth.school_id,
        requester_id=auth.user_id,
        requester_role=auth.role,
        report_type=type,
        period_id=period,
        status=status,
        cursor=cursor,
        limit=clamp_page_size(limit),
    )
    return list_response(items, next_cursor=next_cursor, has_more=has_more)


@router.get(
    "/options",
    summary="List role-filtered report parameter options",
    response_description="Available classes, periods, students, and parents",
)
async def get_report_options(
    type: str | None = Query(None),
    class_id: uuid.UUID | None = Query(None),
    auth: AuthContext = Depends(requires_permission(PERM_REP_REPORT_GENERATE)),
    db: AsyncSession = Depends(get_db),
):
    service = ReportsService(db)
    return success_response(
        await service.get_report_options(
            school_id=auth.school_id,
            requester_id=auth.user_id,
            requester_role=auth.role,
            report_type=type,
            class_id=class_id,
        )
    )


@router.get(
    "/{job_id}/status",
    summary="Get report job status",
    response_description="Current status of the report job",
)
async def get_report_status(
    job_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_REP_REPORT_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = ReportsService(db)
    job = await service.get_job_for_reader(
        job_id=job_id,
        school_id=auth.school_id,
        requester_id=auth.user_id,
        requester_role=auth.role,
    )
    return success_response(service.serialize_job(job))


@router.get(
    "/{job_id}/download",
    summary="Download a generated report",
    response_description="PDF report file",
)
async def download_report(
    job_id: uuid.UUID,
    request: Request,
    token: str | None = Query(None),
    auth: AuthContext | None = Depends(_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ReportsService(db)
    audit = AuditService(db)
    if token:
        job = await service.get_job_for_token(token=token)
        actor_id = auth.user_id if auth else job.requester_id
    else:
        if auth is None:
            raise AuthenticationError(
                "Missing Authorization header",
                error_code="ERR-IAM-401",
            )
        job = await service.get_job_for_reader(
            job_id=job_id,
            school_id=auth.school_id,
            requester_id=auth.user_id,
            requester_role=auth.role,
        )
        actor_id = auth.user_id

    if job.id != job_id:
        raise ValidationError(
            "Report token does not match job",
            error_code="ERR-REPORT-422",
        )
    if job.status != "ready" or not job.file_path:
        raise ValidationError("Report is not ready", error_code="ERR-REPORT-422")

    abs_path = await storage.read(job.file_path)
    await audit.log_event(
        school_id=job.school_id,
        actor_id=actor_id,
        action_type="report.download",
        target_type="report_job",
        target_id=job.id,
        outcome="success",
        entity_after={"download_url": service.serialize_job(job).get("download_url")},
        ip_address=_get_client_ip(request),
    )
    filename = f"{job.type}_{job.id}.pdf"
    return FileResponse(
        abs_path,
        media_type=job.mime_type or "application/pdf",
        filename=filename,
    )
