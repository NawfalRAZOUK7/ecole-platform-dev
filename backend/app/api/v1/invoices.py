"""Invoice API endpoint: GET /invoices.

Reference: S-061 — List invoices (PAR, ADM).
PAR sees own invoices. ADM sees all school invoices.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.filtering import (
    FilterSpec,
    SortSpec,
    parse_filters,
    parse_sort,
)
from app.core.response import list_response, success_response
from app.core.search import parse_search
from app.services.billing import BillingService

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
