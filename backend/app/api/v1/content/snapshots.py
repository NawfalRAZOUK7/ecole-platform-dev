"""Academic snapshot endpoints (Phase 3.3 / G50c).

Routes:
  POST   /academic-snapshots                      — take a new snapshot
  GET    /academic-snapshots/{snapshot_id}        — fetch one
  DELETE /academic-snapshots/{snapshot_id}        — remove a bad snapshot
  GET    /students/{student_id}/snapshots         — list snapshots for a student

Permissions: ADM/DIR can take + delete; ADM/DIR/TCH/PAR/STD can read
their own scope-appropriate snapshots (school-scoping enforced in service).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import HTMLResponse

from app.core.database import get_db
from app.core.dependencies import (
    AuthContext,
    get_current_user,
    requires_permission,
)
from app.core.permissions import PERM_ERP_PROGRAM_MANAGE
from app.core.request_utils import get_client_ip
from app.core.response import list_response, success_response
from app.schemas.academic.programs import AcademicSnapshotCreateRequest
from app.services.content.academic_snapshot_service import AcademicSnapshotService
from app.services.reports.transcript_service import TranscriptService

snapshots_router = APIRouter(prefix="/academic-snapshots", tags=["erp-snapshots"])
student_snapshots_router = APIRouter(prefix="/students", tags=["erp-snapshots"])


@snapshots_router.post(
    "",
    status_code=201,
    summary="Take a new academic snapshot for a (student, academic_year)",
    response_description="Frozen snapshot record",
)
async def create_snapshot(
    body: AcademicSnapshotCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_ERP_PROGRAM_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    service = AcademicSnapshotService(db)
    item = await service.take_snapshot(
        student_id=body.student_id,
        academic_year_id=body.academic_year_id,
        snapshot_kind=body.snapshot_kind,
        auth=auth,
        ip_address=get_client_ip(request),
    )
    return success_response(item)


@snapshots_router.get(
    "/{snapshot_id}",
    summary="Fetch a single snapshot by id",
)
async def get_snapshot(
    snapshot_id: uuid.UUID,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AcademicSnapshotService(db)
    item = await service.get_one(snapshot_id=snapshot_id, auth=auth)
    return success_response(item)


@snapshots_router.get(
    "/{snapshot_id}/transcript",
    summary="Render transcript from a frozen academic snapshot",
)
async def get_snapshot_transcript(
    snapshot_id: uuid.UUID,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TranscriptService(db)
    item = await service.get_snapshot_transcript(
        snapshot_id=snapshot_id,
        auth=auth,
    )
    return success_response(item)


@snapshots_router.get(
    "/{snapshot_id}/transcript/html",
    summary="Render transcript HTML preview from a frozen academic snapshot",
    response_class=HTMLResponse,
)
async def get_snapshot_transcript_html(
    snapshot_id: uuid.UUID,
    lang: str = "fr",
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TranscriptService(db)
    html = await service.render_snapshot_transcript_html(
        snapshot_id=snapshot_id,
        auth=auth,
        lang=lang,
    )
    return HTMLResponse(content=html)


@snapshots_router.get(
    "/{snapshot_id}/transcript/pdf",
    summary="Render transcript PDF from a frozen academic snapshot",
)
async def get_snapshot_transcript_pdf(
    snapshot_id: uuid.UUID,
    lang: str = "fr",
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TranscriptService(db)
    pdf_bytes = await service.download_snapshot_transcript_pdf(
        snapshot_id=snapshot_id,
        auth=auth,
        lang=lang,
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="transcript-snapshot-{snapshot_id}.pdf"'
            )
        },
    )


@snapshots_router.delete(
    "/{snapshot_id}",
    status_code=204,
    summary="Delete a snapshot (e.g. one taken with bad inputs)",
)
async def delete_snapshot(
    snapshot_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_ERP_PROGRAM_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    service = AcademicSnapshotService(db)
    await service.delete_snapshot(
        snapshot_id=snapshot_id,
        auth=auth,
        ip_address=get_client_ip(request),
    )
    return None


@student_snapshots_router.get(
    "/{student_id}/snapshots",
    summary="List academic snapshots for a student (newest first)",
)
async def list_student_snapshots(
    student_id: uuid.UUID,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AcademicSnapshotService(db)
    items = await service.list_for_student(student_id=student_id, auth=auth)
    return list_response(items, next_cursor=None, has_more=False)
