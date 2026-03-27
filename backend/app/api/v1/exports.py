"""Phase 14 data export API."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import FileResponse, StreamingResponse
from starlette.background import BackgroundTask
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.permissions import PERM_REP_EXPORT_CREATE
from app.services.audit import AuditService
from app.services.data_export import DataExportService

router = APIRouter(prefix="/export", tags=["exports"])


def _get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


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
    audit = AuditService(db)
    parsed_filters = service.parse_filters(filters)
    export_log = await service.prepare_export(
        school_id=auth.school_id,
        requester_id=auth.user_id,
        entity=entity,
        filters=parsed_filters,
        export_format="csv",
    )
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="export.csv.download",
        target_type="data_export",
        target_id=export_log.id,
        outcome="success",
        entity_after={"entity": entity, "filters": parsed_filters, "row_count": export_log.row_count},
        ip_address=_get_client_ip(request),
    )
    headers = {
        "Content-Disposition": f'attachment; filename="{entity}.csv"',
    }
    return StreamingResponse(
        service.stream_csv(
            school_id=auth.school_id,
            entity=entity,
            filters=parsed_filters,
        ),
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
    audit = AuditService(db)
    parsed_filters = service.parse_filters(filters)
    export_log = await service.prepare_export(
        school_id=auth.school_id,
        requester_id=auth.user_id,
        entity=entity,
        filters=parsed_filters,
        export_format="xlsx",
    )
    xlsx_path = await service.build_xlsx(
        school_id=auth.school_id,
        entity=entity,
        filters=parsed_filters,
    )
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="export.xlsx.download",
        target_type="data_export",
        target_id=export_log.id,
        outcome="success",
        entity_after={"entity": entity, "filters": parsed_filters, "row_count": export_log.row_count},
        ip_address=_get_client_ip(request),
    )
    return FileResponse(
        xlsx_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"{entity}.xlsx",
        background=BackgroundTask(Path(xlsx_path).unlink, missing_ok=True),
    )
