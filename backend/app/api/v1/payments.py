"""Payment API endpoints.

Reference:
  S-062 — POST /payments/initiate (PAR) — Initiate payment for an invoice
  S-063 — GET /payments/{attempt_id} (PAR, ADM) — Get payment status
  S-064 — POST /payments/webhook/provider (SYS) — Handle provider webhook
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission, verify_school_boundary
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.response import success_response
from app.models.billing import Invoice, PaymentAttempt, ProviderWebhookEvent
from app.schemas.billing import PaymentInitiateRequest, WebhookEventRequest
from app.services.audit import AuditService
from app.services.realtime import publish_payment_updated

router = APIRouter(prefix="/payments", tags=["billing-payments"])


def _get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


# ---------------------------------------------------------------------------
# S-062: POST /payments/initiate — Initiate payment (PAR)
# ---------------------------------------------------------------------------
@router.post("/initiate", status_code=201, summary="Initiate a payment", response_description="Payment attempt with provider redirect")
async def initiate_payment(
    body: PaymentInitiateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-BIL:payment:initiate")),
    db: AsyncSession = Depends(get_db),
):
    """Initiate a payment attempt for an invoice.

    Validates:
    1. Invoice exists, is in same school, belongs to the parent
    2. Invoice is in pending status
    3. Idempotency via idempotency_key (returns existing if same key)
    """
    audit = AuditService(db)

    # 1. Validate invoice
    inv_result = await db.execute(
        select(Invoice).where(Invoice.id == body.invoice_id)
    )
    invoice = inv_result.scalar_one_or_none()
    if invoice is None:
        raise NotFoundError("Invoice not found", error_code="ERR-BIL-404")
    verify_school_boundary(invoice.school_id, auth)

    # Parent can only pay own invoices
    if invoice.parent_id != auth.user_id:
        raise NotFoundError("Invoice not found", error_code="ERR-BIL-404")

    # 2. Invoice must be pending
    if invoice.status != "pending":
        raise ConflictError(
            "Invoice is not in pending status",
            error_code="ERR-BIL-409",
            details={"current_status": invoice.status},
        )

    # 3. Idempotency check via idempotency_key
    existing_result = await db.execute(
        select(PaymentAttempt).where(
            PaymentAttempt.idempotency_key == body.idempotency_key,
        )
    )
    existing = existing_result.scalar_one_or_none()
    if existing is not None:
        return success_response({
            "id": str(existing.id),
            "invoice_id": str(existing.invoice_id),
            "parent_id": str(existing.parent_id),
            "school_id": str(existing.school_id),
            "idempotency_key": existing.idempotency_key,
            "status": existing.status,
            "finalized_at": existing.finalized_at.isoformat() if existing.finalized_at else None,
        })

    # 4. Create payment attempt
    attempt = PaymentAttempt(
        invoice_id=body.invoice_id,
        parent_id=auth.user_id,
        school_id=auth.school_id,
        idempotency_key=body.idempotency_key,
        status="pending",
    )
    db.add(attempt)
    await db.flush()

    # 5. Audit
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="PAYMENT_INITIATED",
        outcome="success",
        target_type="payment_attempt",
        target_id=attempt.id,
        entity_after={
            "invoice_id": str(body.invoice_id),
            "idempotency_key": body.idempotency_key,
        },
        ip_address=_get_client_ip(request),
    )

    return success_response({
        "id": str(attempt.id),
        "invoice_id": str(attempt.invoice_id),
        "parent_id": str(attempt.parent_id),
        "school_id": str(attempt.school_id),
        "idempotency_key": attempt.idempotency_key,
        "status": attempt.status,
        "finalized_at": None,
    })


# ---------------------------------------------------------------------------
# S-063: GET /payments/{attempt_id} — Get payment status (PAR, ADM)
# ---------------------------------------------------------------------------
@router.get("/{attempt_id}", summary="Get payment status", response_description="Payment attempt status")
async def get_payment_status(
    attempt_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission("PERM-BIL:payment:read")),
    db: AsyncSession = Depends(get_db),
):
    """Get payment attempt status."""
    result = await db.execute(
        select(PaymentAttempt).where(PaymentAttempt.id == attempt_id)
    )
    attempt = result.scalar_one_or_none()
    if attempt is None:
        raise NotFoundError("Payment attempt not found", error_code="ERR-BIL-404")

    verify_school_boundary(attempt.school_id, auth)

    # PAR can only see own payment attempts
    if auth.role == "PAR" and attempt.parent_id != auth.user_id:
        raise NotFoundError("Payment attempt not found", error_code="ERR-BIL-404")

    return success_response({
        "id": str(attempt.id),
        "invoice_id": str(attempt.invoice_id),
        "parent_id": str(attempt.parent_id),
        "school_id": str(attempt.school_id),
        "idempotency_key": attempt.idempotency_key,
        "status": attempt.status,
        "finalized_at": attempt.finalized_at.isoformat() if attempt.finalized_at else None,
    })


# ---------------------------------------------------------------------------
# S-064: POST /payments/webhook/provider — Handle webhook (SYS)
# ---------------------------------------------------------------------------
@router.post("/webhook/provider", status_code=200, summary="Handle provider webhook", response_description="Webhook processing result")
async def handle_provider_webhook(
    body: WebhookEventRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-BIL:payment:reconcile")),
    db: AsyncSession = Depends(get_db),
):
    """Handle a webhook event from a payment provider.

    INV-BIL-WEBHOOK: duplicate provider_event_id = no-op (idempotent).

    Flow:
    1. Check for duplicate provider_event_id
    2. Find matching payment attempt (optional)
    3. Update payment attempt status if found
    4. Update invoice status if payment is finalized
    5. Store webhook event
    """
    audit = AuditService(db)
    now = datetime.now(timezone.utc)

    # 1. Duplicate check — INV-BIL-WEBHOOK
    existing_result = await db.execute(
        select(ProviderWebhookEvent).where(
            ProviderWebhookEvent.provider_event_id == body.provider_event_id,
        )
    )
    existing = existing_result.scalar_one_or_none()
    if existing is not None:
        return success_response({
            "id": str(existing.id),
            "provider_event_id": existing.provider_event_id,
            "payment_attempt_id": str(existing.payment_attempt_id) if existing.payment_attempt_id else None,
            "school_id": str(existing.school_id),
            "status": existing.status,
            "signature_status": existing.signature_status,
        })

    # 2. Find payment attempt if provided
    payment_attempt = None
    if body.payment_attempt_id:
        attempt_result = await db.execute(
            select(PaymentAttempt).where(PaymentAttempt.id == body.payment_attempt_id)
        )
        payment_attempt = attempt_result.scalar_one_or_none()

    # 3. Create webhook event
    webhook_event = ProviderWebhookEvent(
        payment_attempt_id=body.payment_attempt_id,
        school_id=auth.school_id,
        provider_event_id=body.provider_event_id,
        signature_status="valid" if body.signature else "unchecked",
        status="processed",
        provider_event_received_at=now,
    )
    db.add(webhook_event)

    # 4. Update payment attempt and invoice status if applicable
    if payment_attempt is not None:
        if body.status == "paid":
            payment_attempt.status = "paid"
            payment_attempt.finalized_at = now
            # Update invoice
            inv_result = await db.execute(
                select(Invoice).where(Invoice.id == payment_attempt.invoice_id)
            )
            invoice = inv_result.scalar_one_or_none()
            if invoice:
                invoice.status = "paid"
        elif body.status == "failed":
            payment_attempt.status = "failed"
            payment_attempt.finalized_at = now
            # Phase 11B: Schedule retry for failed payment
            try:
                from app.services.payment_retry import schedule_retry_for_failed_payment
                await schedule_retry_for_failed_payment(payment_attempt.id, db)
            except Exception:
                pass  # Retry scheduling is best-effort
        elif body.status == "canceled":
            payment_attempt.status = "canceled"
            payment_attempt.finalized_at = now

    await db.flush()

    # 5. Real-time push (Phase 3C) — notify parent of payment status change
    if payment_attempt is not None and body.status in ("paid", "failed", "canceled"):
        await publish_payment_updated(
            parent_id=payment_attempt.parent_id,
            payment_attempt_id=payment_attempt.id,
            status=body.status,
            invoice_id=payment_attempt.invoice_id,
        )

    # 6. Audit
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="WEBHOOK_PROCESSED",
        outcome="success",
        target_type="provider_webhook_event",
        target_id=webhook_event.id,
        entity_after={
            "provider_event_id": body.provider_event_id,
            "event_type": body.event_type,
            "status": body.status,
        },
        ip_address=_get_client_ip(request),
    )

    return success_response({
        "id": str(webhook_event.id),
        "provider_event_id": webhook_event.provider_event_id,
        "payment_attempt_id": str(webhook_event.payment_attempt_id) if webhook_event.payment_attempt_id else None,
        "school_id": str(webhook_event.school_id),
        "status": webhook_event.status,
        "signature_status": webhook_event.signature_status,
    })
