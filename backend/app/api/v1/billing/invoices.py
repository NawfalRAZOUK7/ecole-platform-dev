"""Invoice API endpoints.

Reference:
  S-061 — GET /invoices (PAR, ADM) — List invoices
  S-061 — GET /invoices/{invoice_id} — Get invoice details
  S-INV-PDF — POST /invoices/{invoice_id}/pdf — Generate invoice PDF
"""

from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.filtering import (
    FilterSpec,
    SortSpec,
    parse_filters,
    parse_sort,
)
from app.core.request_utils import get_client_ip
from app.core.response import list_response, success_response
from app.core.search import parse_search
from app.core.tasks import enqueue_task
from app.schemas.reports import ReportGenerateRequest
from app.services.platform.audit import AuditService
from app.services.billing.billing import BillingService
from app.services.reports.reports import ReportsService

router = APIRouter(prefix="/invoices", tags=["billing-invoices"])


@router.get(
    "", summary="List invoices", response_description="Paginated list of invoices"
)
async def list_invoices(
    status: str | None = Query(None),
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    filters: FilterSpec = Depends(parse_filters),
    sort: SortSpec = Depends(parse_sort),
    search: str | None = Depends(parse_search),
    auth: AuthContext = Depends(requires_permission("PERM-BIL:invoice:read")),
    db: AsyncSession = Depends(get_db),
):
    """List invoices with filtering, sorting, and full-text search.

    PAR: sees own invoices only.
    ADM: sees all invoices for the school.
    Filters: ?filter[status]=paid&filter[total_amount__gte]=100
    Sort: ?sort=-issued_date
    Search: ?search=tuition
    Legacy param status still supported.
    """
    service = BillingService(db)
    result = await service.list_invoices(
        status=status,
        cursor=cursor,
        limit=limit,
        filters=filters,
        sort=sort,
        search=search,
        auth=auth,
    )
    return list_response(
        result["items"],
        next_cursor=result["next_cursor"],
        has_more=result["has_more"],
        filters_applied=result["filters_applied"],
        sort_by=result["sort_by"],
        search_term=result["search_term"],
    )


@router.get(
    "/{invoice_id}",
    summary="Get invoice details",
    response_description="Invoice with line items",
)
async def get_invoice(
    invoice_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission("PERM-BIL:invoice:read")),
    db: AsyncSession = Depends(get_db),
):
    """Get invoice details by ID."""
    service = BillingService(db)
    result = await service.get_invoice(
        invoice_id=invoice_id,
        auth=auth,
    )
    return success_response(result)


# ---------------------------------------------------------------------------
# S-INV-PDF: POST /invoices/{invoice_id}/pdf — Generate invoice PDF
# ---------------------------------------------------------------------------
@router.post(
    "/{invoice_id}/pdf",
    status_code=201,
    summary="Generate invoice PDF",
    response_description="Report job queued for invoice PDF generation",
)
async def generate_invoice_pdf(
    invoice_id: uuid.UUID,
    request: Request,
    language: Literal["fr", "ar"] = Query(default="fr"),
    auth: AuthContext = Depends(requires_permission("PERM-BIL:invoice:read")),
    db: AsyncSession = Depends(get_db),
):
    """Queue a PDF generation job for the given invoice.

    PAR: can only generate PDFs for own invoices.
    ADM/DIR: can generate PDFs for any invoice in the school.
    Poll GET /reports/{job_id}/status, then download via GET /reports/{job_id}/download.
    """
    report_request = ReportGenerateRequest(
        type="invoice_pdf",
        locale=language,
        invoice_id=str(invoice_id),
    )
    service = ReportsService(db)
    audit = AuditService(db)
    payload, cache_hit = await service.submit_report_job(
        school_id=auth.school_id,
        requester_id=auth.user_id,
        requester_role=auth.role,
        request=report_request,
    )
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="report.generate.request",
        target_type="report_job",
        target_id=uuid.UUID(payload["id"]),
        outcome="success",
        entity_after={
            "invoice_id": str(invoice_id),
            "language": language,
            "job": payload,
        },
        ip_address=get_client_ip(request),
    )
    await db.commit()
    if not cache_hit:
        if settings.app_env == "production":
            await enqueue_task("task_generate_report", job_id=payload["id"])
        else:
            job = await service.generate_report_job(uuid.UUID(payload["id"]))
            if job is not None:
                payload = service.serialize_job(job)
    return success_response(payload)
