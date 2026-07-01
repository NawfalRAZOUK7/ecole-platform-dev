"""Data export API."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.background import BackgroundTask

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.permissions import PERM_REP_EXPORT_CREATE
from app.core.request_utils import get_client_ip
from app.services.reports.data_export import DataExportService

router = APIRouter(prefix="/export", tags=["exports"])


@router.get(
    "/csv",
    summary="Export entity data as CSV",
    response_description="Streaming CSV export",
)
async def export_csv(
    request: Request,
    entity: str = Query(...),
    filters: str | None = Query(None),
    auth: AuthContext = Depends(requires_permission(PERM_REP_EXPORT_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    service = DataExportService(db)
    payload = await service.prepare_csv_download(
        school_id=auth.school_id,
        requester_id=auth.user_id,
        entity=entity,
        filters_json=filters,
        ip_address=get_client_ip(request),
    )
    headers = {"Content-Disposition": f'attachment; filename="{payload["filename"]}"'}
    return StreamingResponse(
        payload["stream"],
        media_type="text/csv; charset=utf-8",
        headers=headers,
    )


@router.get(
    "/xlsx",
    summary="Export entity data as XLSX",
    response_description="Generated XLSX export",
)
async def export_xlsx(
    request: Request,
    entity: str = Query(...),
    filters: str | None = Query(None),
    auth: AuthContext = Depends(requires_permission(PERM_REP_EXPORT_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    service = DataExportService(db)
    payload = await service.prepare_xlsx_download(
        school_id=auth.school_id,
        requester_id=auth.user_id,
        entity=entity,
        filters_json=filters,
        ip_address=get_client_ip(request),
    )
    return FileResponse(
        payload["path"],
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=payload["filename"],
        background=BackgroundTask(Path(payload["path"]).unlink, missing_ok=True),
    )
