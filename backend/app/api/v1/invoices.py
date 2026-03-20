"""Invoice API endpoint: GET /invoices.

Reference: S-061 — List invoices (PAR, ADM).
PAR sees own invoices. ADM sees all school invoices.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission, verify_school_boundary
from app.core.exceptions import NotFoundError
from app.core.response import (
    clamp_page_size,
    decode_cursor,
    encode_cursor,
    list_response,
    success_response,
)
from app.models.billing import Invoice, InvoiceItem

router = APIRouter(prefix="/invoices", tags=["billing-invoices"])


@router.get("", summary="List invoices", response_description="Paginated list of invoices")
async def list_invoices(
    status: str | None = Query(None),
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    auth: AuthContext = Depends(requires_permission("PERM-BIL:invoice:read")),
    db: AsyncSession = Depends(get_db),
):
    """List invoices.

    PAR: sees own invoices only.
    ADM: sees all invoices for the school.
    """
    page_size = clamp_page_size(limit)

    query = (
        select(Invoice)
        .options(selectinload(Invoice.items))
        .where(Invoice.school_id == auth.school_id)
    )

    # PAR: filter to own invoices
    if auth.role == "PAR":
        query = query.where(Invoice.parent_id == auth.user_id)

    if status:
        query = query.where(Invoice.status == status)

    if cursor:
        last_id, _ = decode_cursor(cursor)
        query = query.where(Invoice.id > last_id)

    query = query.order_by(Invoice.id).limit(page_size + 1)
    result = await db.execute(query)
    invoices = list(result.scalars().unique().all())

    has_more = len(invoices) > page_size
    if has_more:
        invoices = invoices[:page_size]

    items = [
        {
            "id": str(inv.id),
            "school_id": str(inv.school_id),
            "parent_id": str(inv.parent_id),
            "period_id": str(inv.period_id) if inv.period_id else None,
            "status": inv.status,
            "total_amount": float(inv.total_amount),
            "currency": inv.currency,
            "issued_date": str(inv.issued_date),
            "due_date": str(inv.due_date),
            "items": [
                {
                    "id": str(item.id),
                    "description": item.description,
                    "amount": float(item.amount),
                    "unit_price": float(item.unit_price),
                    "quantity": item.quantity,
                }
                for item in inv.items
            ],
        }
        for inv in invoices
    ]

    next_cursor = encode_cursor(invoices[-1].id) if has_more and invoices else None
    return list_response(items, next_cursor=next_cursor, has_more=has_more)


@router.get("/{invoice_id}", summary="Get invoice details", response_description="Invoice with line items")
async def get_invoice(
    invoice_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission("PERM-BIL:invoice:read")),
    db: AsyncSession = Depends(get_db),
):
    """Get invoice details by ID."""
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.items))
        .where(Invoice.id == invoice_id)
    )
    inv = result.scalar_one_or_none()
    if inv is None:
        raise NotFoundError("Invoice not found", error_code="ERR-BIL-404")

    verify_school_boundary(inv.school_id, auth)

    # PAR can only see own invoices
    if auth.role == "PAR" and inv.parent_id != auth.user_id:
        raise NotFoundError("Invoice not found", error_code="ERR-BIL-404")

    return success_response({
        "id": str(inv.id),
        "school_id": str(inv.school_id),
        "parent_id": str(inv.parent_id),
        "period_id": str(inv.period_id) if inv.period_id else None,
        "status": inv.status,
        "total_amount": float(inv.total_amount),
        "currency": inv.currency,
        "issued_date": str(inv.issued_date),
        "due_date": str(inv.due_date),
        "items": [
            {
                "id": str(item.id),
                "description": item.description,
                "amount": float(item.amount),
                "unit_price": float(item.unit_price),
                "quantity": item.quantity,
            }
            for item in inv.items
        ],
    })
