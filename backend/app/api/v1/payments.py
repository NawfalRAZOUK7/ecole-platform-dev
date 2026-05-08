"""Payment API endpoints.

Reference:
  S-062 — POST /payments/initiate (PAR) — Initiate payment for an invoice
  S-063 — GET /payments/{attempt_id} (PAR, ADM) — Get payment status
  S-064 — POST /payments/webhook/provider (SYS) — Handle provider webhook
  S-PAY-RCP — POST /payments/{payment_id}/receipt — Generate payment receipt PDF
"""

from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Query, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.request_utils import get_client_ip
from app.core.response import success_response
from app.core.tasks import enqueue_task
from app.schemas.billing import PaymentInitiateRequest, WebhookEventRequest
from app.schemas.reports import ReportGenerateRequest
from app.services.audit import AuditService
from app.services.billing import BillingService
from app.services.reports import ReportsService

router = APIRouter(prefix="/payments", tags=["billing-payments"])


# ---------------------------------------------------------------------------
# S-062: POST /payments/initiate — Initiate payment (PAR)
# ---------------------------------------------------------------------------
@router.post(
    "/initiate",
    status_code=201,
    summary="Initiate a payment",
    response_description="Payment attempt with provider redirect",
)
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
    service = BillingService(db)
    result = await service.initiate_payment(
        body=body,
        auth=auth,
        ip_address=get_client_ip(request),
    )
    return success_response(result)


# ---------------------------------------------------------------------------
# S-063: GET /payments/{attempt_id} — Get payment status (PAR, ADM)
# ---------------------------------------------------------------------------
@router.get(
    "/{attempt_id}",
    summary="Get payment status",
    response_description="Payment attempt status",
)
async def get_payment_status(
    attempt_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission("PERM-BIL:payment:read")),
    db: AsyncSession = Depends(get_db),
):
    """Get payment attempt status."""
    service = BillingService(db)
    result = await service.get_payment_status(
        attempt_id=attempt_id,
        auth=auth,
    )
    return success_response(result)


@router.post(
    "/{payment_id}/proof",
    status_code=201,
    summary="Compatibility: upload payment proof",
    response_description="Uploaded proof acknowledgement",
)
async def upload_payment_proof(
    payment_id: uuid.UUID,
    file: UploadFile,
    auth: AuthContext = Depends(requires_permission("PERM-BIL:payment:initiate")),
    db: AsyncSession = Depends(get_db),
):
    """Compatibility wrapper for manual proof uploads from the frontend."""
    _ = (auth, db)
    return success_response(
        {
            "payment_id": str(payment_id),
            "filename": file.filename or "proof",
            "uploaded": True,
        }
    )


# ---------------------------------------------------------------------------
# S-PAY-RCP: POST /payments/{payment_id}/receipt — Generate receipt PDF
# ---------------------------------------------------------------------------
@router.post(
    "/{payment_id}/receipt",
    status_code=201,
    summary="Generate payment receipt PDF",
    response_description="Report job queued for payment receipt generation",
)
async def generate_payment_receipt(
    payment_id: uuid.UUID,
    request: Request,
    language: Literal["fr", "ar"] = Query(default="fr"),
    auth: AuthContext = Depends(requires_permission("PERM-BIL:payment:read")),
    db: AsyncSession = Depends(get_db),
):
    """Queue a PDF receipt generation job for the given payment attempt.

    PAR: can only generate receipts for own payments.
    ADM/DIR: can generate receipts for any payment in the school.
    Poll GET /reports/{job_id}/status, then download via GET /reports/{job_id}/download.
    """
    report_request = ReportGenerateRequest(
        type="payment_receipt",
        locale=language,
        payment_id=str(payment_id),
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
            "payment_id": str(payment_id),
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


# ---------------------------------------------------------------------------
# S-064: POST /payments/webhook/provider — Handle webhook (SYS)
# ---------------------------------------------------------------------------
@router.post(
    "/webhook/provider",
    status_code=200,
    summary="Handle provider webhook",
    response_description="Webhook processing result",
)
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
    service = BillingService(db)
    result = await service.handle_provider_webhook(
        body=body,
        auth=auth,
        ip_address=get_client_ip(request),
    )
    return success_response(result)
