"""Financial health dashboard API endpoints."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.permissions import (
    PERM_FINHEALTH_CASHFLOW_READ,
    PERM_FINHEALTH_COMPUTE,
    PERM_FINHEALTH_COST_READ,
    PERM_FINHEALTH_EXPORT,
    PERM_FINHEALTH_RETENTION_READ,
    PERM_FINHEALTH_SNAPSHOT_READ,
)
from app.core.request_utils import get_client_ip
from app.core.response import list_response, success_response
from app.schemas.reports.financial_health import (
    CashflowForecastComputeRequest,
    CostPerStudentComputeRequest,
    FinancialSnapshotComputeRequest,
    RetentionComputeRequest,
)
from app.services.reports.financial_health_service import FinancialHealthService

router = APIRouter(prefix="/financial-health", tags=["financial-health"])


@router.get(
    "/retention",
    summary="List retention metrics",
    description="Returns stored retention metrics for the authenticated school using offset pagination parameters.",
    response_description="List of retention metrics",
)
async def list_retention_metrics(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    auth: AuthContext = Depends(requires_permission(PERM_FINHEALTH_RETENTION_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List stored retention metrics."""
    service = FinancialHealthService(db)
    return list_response(
        await service.list_retention_metrics(
            auth=auth,
            skip=skip,
            limit=limit,
        )
    )


@router.post(
    "/retention/compute",
    status_code=202,
    summary="Compute retention metric",
    description="Computes a retention metric for the requested academic-year comparison and returns the generated metric payload.",
    response_description="Computed retention metric",
)
async def compute_retention(
    body: RetentionComputeRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_FINHEALTH_COMPUTE)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Compute a retention metric for two academic years."""
    service = FinancialHealthService(db)
    return success_response(
        await service.compute_retention(
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "/cashflow",
    summary="List cashflow forecasts",
    description="Returns stored cashflow forecasts for the authenticated school. Supports filtering by month range and offset pagination.",
    response_description="List of cashflow forecasts",
)
async def list_cashflow_forecasts(
    start_month: date | None = Query(None),
    end_month: date | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    auth: AuthContext = Depends(requires_permission(PERM_FINHEALTH_CASHFLOW_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List stored cashflow forecasts."""
    service = FinancialHealthService(db)
    return list_response(
        await service.list_cashflow_forecasts(
            auth=auth,
            start_month=start_month,
            end_month=end_month,
            skip=skip,
            limit=limit,
        )
    )


@router.post(
    "/cashflow/compute",
    status_code=202,
    summary="Compute cashflow forecast",
    description="Computes forward-looking cashflow forecasts and returns the generated forecast set for the requested parameters.",
    response_description="Computed cashflow forecasts",
)
async def compute_cashflow(
    body: CashflowForecastComputeRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_FINHEALTH_COMPUTE)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Compute forward-looking cashflow forecasts."""
    service = FinancialHealthService(db)
    return success_response(
        await service.compute_cashflow(
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "/cost-per-student",
    summary="Get cost-per-student analysis",
    description="Fetches the stored cost-per-student analysis for a specific academic year within the authenticated school scope.",
    response_description="Cost-per-student analysis",
)
async def get_cost_per_student(
    academic_year_id: uuid.UUID = Query(...),
    auth: AuthContext = Depends(requires_permission(PERM_FINHEALTH_COST_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Fetch the stored cost-per-student analysis."""
    service = FinancialHealthService(db)
    return success_response(
        await service.get_cost_analysis(
            academic_year_id=academic_year_id,
            auth=auth,
        )
    )


@router.post(
    "/cost-per-student/compute",
    status_code=202,
    summary="Compute cost-per-student analysis",
    description="Computes a cost-per-student analysis for an academic year and returns the generated analysis payload.",
    response_description="Computed cost-per-student analysis",
)
async def compute_cost_per_student(
    body: CostPerStudentComputeRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_FINHEALTH_COMPUTE)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Compute cost-per-student analysis for an academic year."""
    service = FinancialHealthService(db)
    return success_response(
        await service.compute_cost(
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "/snapshot",
    summary="Get financial snapshot",
    description="Fetches a stored point-in-time financial snapshot for the authenticated school, optionally scoped to a specific date.",
    response_description="Financial snapshot",
)
async def get_snapshot(
    snapshot_date: date | None = Query(None),
    auth: AuthContext = Depends(requires_permission(PERM_FINHEALTH_SNAPSHOT_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Fetch a stored financial snapshot."""
    service = FinancialHealthService(db)
    return success_response(
        await service.get_snapshot(
            auth=auth,
            snapshot_date=snapshot_date,
        )
    )


@router.post(
    "/snapshot/compute",
    status_code=202,
    summary="Compute financial snapshot",
    description="Computes a financial snapshot for the requested inputs and returns the generated point-in-time summary.",
    response_description="Computed financial snapshot",
)
async def compute_snapshot(
    body: FinancialSnapshotComputeRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_FINHEALTH_COMPUTE)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Compute a point-in-time financial snapshot."""
    service = FinancialHealthService(db)
    return success_response(
        await service.compute_snapshot(
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "/dashboard",
    summary="Get financial health dashboard",
    description="Returns the consolidated financial health dashboard for the authenticated school across retention, cashflow, and cost metrics.",
    response_description="Financial dashboard summary",
)
async def get_dashboard(
    auth: AuthContext = Depends(requires_permission(PERM_FINHEALTH_RETENTION_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Return the financial health dashboard summary."""
    service = FinancialHealthService(db)
    return success_response(await service.get_dashboard(auth=auth))


@router.get(
    "/trends",
    summary="Get financial health trends",
    description="Returns financial health trend series for the requested number of months to support dashboard charting.",
    response_description="Financial trend series",
)
async def get_trends(
    months: int = Query(12, ge=1, le=24),
    auth: AuthContext = Depends(requires_permission(PERM_FINHEALTH_RETENTION_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Return financial health trend series."""
    service = FinancialHealthService(db)
    return success_response(await service.get_trends(auth=auth, months=months))


@router.get(
    "/export/csv",
    summary="Export financial health CSV",
    description="Exports the financial health dashboard data as a CSV file for spreadsheet analysis or offline reporting.",
    response_description="CSV export",
)
async def export_financial_health_csv(
    auth: AuthContext = Depends(requires_permission(PERM_FINHEALTH_EXPORT)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Export the financial health dashboard as CSV."""
    service = FinancialHealthService(db)
    csv_bytes = await service.export_csv(auth=auth)
    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="financial-health.csv"'},
    )


@router.get(
    "/export/pdf",
    summary="Export financial health PDF",
    description="Exports the financial health dashboard as a PDF document for sharing and archival purposes.",
    response_description="PDF export",
)
async def export_financial_health_pdf(
    auth: AuthContext = Depends(requires_permission(PERM_FINHEALTH_EXPORT)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Export the financial health dashboard as PDF."""
    service = FinancialHealthService(db)
    pdf_bytes = await service.export_pdf(auth=auth)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="financial-health.pdf"'},
    )
