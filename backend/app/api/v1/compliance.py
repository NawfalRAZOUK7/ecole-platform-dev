"""MEN compliance API endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.permissions import (
    PERM_COMPLY_CURRICULUM_MANAGE,
    PERM_COMPLY_CURRICULUM_READ,
    PERM_COMPLY_MAPPING_CREATE,
    PERM_COMPLY_MAPPING_READ,
    PERM_COMPLY_OBJECTIVE_READ,
    PERM_COMPLY_REPORT_GENERATE,
    PERM_COMPLY_REPORT_READ,
)
from app.core.request_utils import get_client_ip
from app.core.response import list_response, success_response
from app.schemas.men_compliance import (
    ComplianceReportGenerateRequest,
    CurriculumMappingCreateRequest,
    MenCurriculumCreateRequest,
    MenObjectiveCreateRequest,
)
from app.services.compliance_service import ComplianceService

router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.get(
    "/curricula",
    summary="List MEN curricula",
    response_description="List of MEN curricula",
)
async def list_curricula(
    level: str | None = Query(None),
    grade: str | None = Query(None),
    subject: str | None = Query(None),
    academic_year: str | None = Query(None),
    is_active: bool | None = Query(None),
    auth: AuthContext = Depends(requires_permission(PERM_COMPLY_CURRICULUM_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = ComplianceService(db)
    return list_response(
        await service.list_curricula(
            level=level,
            grade=grade,
            subject=subject,
            academic_year=academic_year,
            is_active=is_active,
        )
    )


@router.post(
    "/curricula",
    status_code=201,
    summary="Create MEN curriculum",
    response_description="Created MEN curriculum",
)
async def create_curriculum(
    body: MenCurriculumCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_COMPLY_CURRICULUM_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    service = ComplianceService(db)
    return success_response(
        await service.create_curriculum(
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "/curricula/{curriculum_id}/objectives",
    summary="List MEN objectives for a curriculum",
    response_description="List of MEN objectives",
)
async def list_objectives(
    curriculum_id: uuid.UUID,
    trimester: int | None = Query(None, ge=1, le=3),
    auth: AuthContext = Depends(requires_permission(PERM_COMPLY_OBJECTIVE_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = ComplianceService(db)
    return list_response(
        await service.list_objectives(
            curriculum_id=curriculum_id,
            trimester=trimester,
        )
    )


@router.post(
    "/curricula/{curriculum_id}/objectives",
    status_code=201,
    summary="Create MEN objective",
    response_description="Created MEN objective",
)
async def create_objective(
    curriculum_id: uuid.UUID,
    body: MenObjectiveCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_COMPLY_CURRICULUM_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    service = ComplianceService(db)
    return success_response(
        await service.create_objective(
            curriculum_id=curriculum_id,
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.post(
    "/mappings",
    status_code=201,
    summary="Create curriculum mapping",
    response_description="Created mapping",
)
async def create_mapping(
    body: CurriculumMappingCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_COMPLY_MAPPING_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    service = ComplianceService(db)
    return success_response(
        await service.create_mapping(
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "/mappings",
    summary="List curriculum mappings",
    response_description="List of curriculum mappings",
)
async def list_mappings(
    curriculum_id: uuid.UUID | None = Query(None),
    objective_id: uuid.UUID | None = Query(None),
    course_id: uuid.UUID | None = Query(None),
    content_item_id: uuid.UUID | None = Query(None),
    auth: AuthContext = Depends(requires_permission(PERM_COMPLY_MAPPING_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = ComplianceService(db)
    return list_response(
        await service.list_mappings(
            auth=auth,
            curriculum_id=curriculum_id,
            objective_id=objective_id,
            course_id=course_id,
            content_item_id=content_item_id,
        )
    )


@router.delete(
    "/mappings/{mapping_id}",
    status_code=204,
    summary="Delete curriculum mapping",
    response_description="Mapping deleted",
)
async def delete_mapping(
    mapping_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_COMPLY_MAPPING_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    service = ComplianceService(db)
    await service.delete_mapping(
        mapping_id=mapping_id,
        auth=auth,
        ip_address=get_client_ip(request),
    )
    return Response(status_code=204)


@router.get(
    "/dashboard",
    summary="Get MEN compliance dashboard",
    response_description="Compliance dashboard summary",
)
async def get_dashboard(
    academic_year_id: uuid.UUID = Query(...),
    level: str | None = Query(None),
    grade: str | None = Query(None),
    subject: str | None = Query(None),
    auth: AuthContext = Depends(requires_permission(PERM_COMPLY_REPORT_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = ComplianceService(db)
    return success_response(
        await service.get_dashboard(
            auth=auth,
            academic_year_id=academic_year_id,
            level=level,
            grade=grade,
            subject=subject,
        )
    )


@router.post(
    "/reports/generate",
    status_code=202,
    summary="Generate compliance report",
    response_description="Generated compliance report",
)
async def generate_report(
    body: ComplianceReportGenerateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_COMPLY_REPORT_GENERATE)),
    db: AsyncSession = Depends(get_db),
):
    service = ComplianceService(db)
    return success_response(
        await service.generate_report(
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "/reports",
    summary="List compliance reports",
    response_description="List of compliance reports",
)
async def list_reports(
    curriculum_id: uuid.UUID | None = Query(None),
    academic_year_id: uuid.UUID | None = Query(None),
    auth: AuthContext = Depends(requires_permission(PERM_COMPLY_REPORT_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = ComplianceService(db)
    return list_response(
        await service.list_reports(
            auth=auth,
            curriculum_id=curriculum_id,
            academic_year_id=academic_year_id,
        )
    )


@router.get(
    "/reports/{report_id}",
    summary="Get compliance report detail",
    response_description="Compliance report detail",
)
async def get_report(
    report_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_COMPLY_REPORT_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = ComplianceService(db)
    return success_response(await service.get_report(report_id=report_id, auth=auth))


@router.get(
    "/reports/{report_id}/download",
    summary="Download compliance report PDF",
    response_description="PDF bytes",
)
async def download_report(
    report_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_COMPLY_REPORT_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = ComplianceService(db)
    pdf_bytes = await service.download_pdf(report_id=report_id, auth=auth)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="compliance-report-{report_id}.pdf"'
        },
    )
