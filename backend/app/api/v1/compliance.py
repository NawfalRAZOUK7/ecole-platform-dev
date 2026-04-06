"""MEN compliance API endpoints."""

from __future__ import annotations

import uuid
from typing import Any

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
    description="Returns MEN curriculum references available to the school context. Supports filtering by level, grade, subject, academic year, and active state.",
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
) -> Any:
    """List MEN curricula available to the school."""
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
    description="Creates a MEN curriculum reference and returns the saved curriculum record for later objective and mapping management.",
    response_description="Created MEN curriculum",
)
async def create_curriculum(
    body: MenCurriculumCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_COMPLY_CURRICULUM_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a MEN curriculum reference."""
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
    description="Lists MEN learning objectives attached to a curriculum, with optional filtering by trimester.",
    response_description="List of MEN objectives",
)
async def list_objectives(
    curriculum_id: uuid.UUID,
    trimester: int | None = Query(None, ge=1, le=3),
    auth: AuthContext = Depends(requires_permission(PERM_COMPLY_OBJECTIVE_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List MEN objectives for a curriculum."""
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
    description="Creates a MEN objective under the specified curriculum and returns the saved objective definition.",
    response_description="Created MEN objective",
)
async def create_objective(
    curriculum_id: uuid.UUID,
    body: MenObjectiveCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_COMPLY_CURRICULUM_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a MEN objective under a curriculum."""
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
    description="Creates a mapping between MEN curriculum content and school learning assets, then returns the stored mapping record.",
    response_description="Created mapping",
)
async def create_mapping(
    body: CurriculumMappingCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_COMPLY_MAPPING_CREATE)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a curriculum-to-course mapping."""
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
    description="Returns curriculum mappings visible to the authenticated school. Supports filtering by curriculum, objective, course, and content item.",
    response_description="List of curriculum mappings",
)
async def list_mappings(
    curriculum_id: uuid.UUID | None = Query(None),
    objective_id: uuid.UUID | None = Query(None),
    course_id: uuid.UUID | None = Query(None),
    content_item_id: uuid.UUID | None = Query(None),
    auth: AuthContext = Depends(requires_permission(PERM_COMPLY_MAPPING_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List curriculum mappings for the school."""
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
    response_class=Response,
    summary="Delete curriculum mapping",
    description="Deletes a curriculum mapping by ID. Returns an empty 204 response when the mapping is removed successfully.",
    response_description="Mapping deleted",
)
async def delete_mapping(
    mapping_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_COMPLY_MAPPING_CREATE)),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Delete a curriculum mapping."""
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
    description="Returns the MEN compliance dashboard summary for the requested academic year, with optional level, grade, and subject filters.",
    response_description="Compliance dashboard summary",
)
async def get_dashboard(
    academic_year_id: uuid.UUID = Query(...),
    level: str | None = Query(None),
    grade: str | None = Query(None),
    subject: str | None = Query(None),
    auth: AuthContext = Depends(requires_permission(PERM_COMPLY_REPORT_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Return the MEN compliance dashboard summary."""
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
    description="Queues or generates a MEN compliance report for the requested scope and returns the created report job payload.",
    response_description="Generated compliance report",
)
async def generate_report(
    body: ComplianceReportGenerateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_COMPLY_REPORT_GENERATE)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Generate a MEN compliance report."""
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
    description="Lists generated MEN compliance reports available to the authenticated school, with optional curriculum and academic-year filters.",
    response_description="List of compliance reports",
)
async def list_reports(
    curriculum_id: uuid.UUID | None = Query(None),
    academic_year_id: uuid.UUID | None = Query(None),
    auth: AuthContext = Depends(requires_permission(PERM_COMPLY_REPORT_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List generated MEN compliance reports."""
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
    description="Fetches a single MEN compliance report by ID and returns its stored metadata and generation outcome.",
    response_description="Compliance report detail",
)
async def get_report(
    report_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_COMPLY_REPORT_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Fetch one MEN compliance report."""
    service = ComplianceService(db)
    return success_response(await service.get_report(report_id=report_id, auth=auth))


@router.get(
    "/reports/{report_id}/download",
    summary="Download compliance report PDF",
    description="Streams the selected MEN compliance report as a PDF download for external review or archival.",
    response_description="PDF bytes",
)
async def download_report(
    report_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_COMPLY_REPORT_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Download a MEN compliance report PDF."""
    service = ComplianceService(db)
    pdf_bytes = await service.download_pdf(report_id=report_id, auth=auth)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="compliance-report-{report_id}.pdf"'
        },
    )
