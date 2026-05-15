"""Billing fee management API endpoints — Phase 11B.

Reference: Phase 11B — Billing Enhancements
Endpoints:
  POST   /billing/fee-structures           — Create fee structure (ADM)
  GET    /billing/fee-structures           — List fee structures
  PUT    /billing/fee-structures/{id}      — Update fee structure (ADM)
  POST   /billing/fee-assignments          — Assign fee to student (ADM)
  POST   /billing/fee-assignments/bulk     — Bulk assign fee (ADM)
  GET    /billing/fee-assignments          — List fee assignments
  POST   /billing/generate-invoices        — Generate invoices from fee structure (ADM)
  GET    /billing/sibling-policy           — Get sibling discount policy
  PUT    /billing/sibling-policy           — Update sibling discount policy
  GET    /billing/late-fee-policy          — Get late fee policy
  PUT    /billing/late-fee-policy          — Update late fee policy
  POST   /billing/payment-plans            — Create payment plan
  GET    /billing/payment-plans            — List payment plans
  GET    /billing/payment-plans/{id}       — Get payment plan details
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.response import list_response, success_response
from app.core.request_utils import get_client_ip
from app.schemas.billing import (
    FeeAssignmentBulkCreateRequest,
    FeeAssignmentCreateRequest,
    FeeStructureCreateRequest,
    FeeStructureUpdateRequest,
    InvoiceGenerateRequest,
)
from app.schemas.billing.enhancements import (
    LateFeePolicyUpdateRequest,
    PaymentPlanCreateRequest,
    SiblingDiscountPolicyUpdateRequest,
)
from app.services.billing.billing import BillingService
from app.services.billing.payment_plan import PaymentPlanService

router = APIRouter(prefix="/billing", tags=["billing-fees"])


# ---------------------------------------------------------------------------
# POST /billing/fee-structures — Create fee structure (ADM)
# ---------------------------------------------------------------------------
@router.post(
    "/fee-structures",
    status_code=201,
    summary="Create fee structure",
    response_description="Created fee structure",
)
async def create_fee_structure(
    body: FeeStructureCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-BIL:fee:create")),
    db: AsyncSession = Depends(get_db),
):
    """Create a fee structure for the school.

    Validates:
    1. Academic year exists and belongs to the same school
    """
    service = BillingService(db)
    result = await service.create_fee_structure(
        body=body,
        auth=auth,
        ip_address=get_client_ip(request),
    )
    return success_response(result)


# ---------------------------------------------------------------------------
# GET /billing/fee-structures — List fee structures
# ---------------------------------------------------------------------------
@router.get(
    "/fee-structures",
    summary="List fee structures",
    response_description="List of fee structures",
)
async def list_fee_structures(
    academic_year_id: uuid.UUID | None = Query(None),
    status: str | None = Query(None, pattern="^(ACTIVE|ARCHIVED)$"),
    applies_to_level: str | None = Query(None),
    auth: AuthContext = Depends(requires_permission("PERM-BIL:fee:read")),
    db: AsyncSession = Depends(get_db),
):
    """List fee structures with optional filters.

    Always scoped to the user's school.
    """
    service = BillingService(db)
    result = await service.list_fee_structures(
        auth=auth,
        academic_year_id=academic_year_id,
        status=status,
        applies_to_level=applies_to_level,
    )
    return list_response(result)


# ---------------------------------------------------------------------------
# PUT /billing/fee-structures/{id} — Update fee structure (ADM)
# ---------------------------------------------------------------------------
@router.put(
    "/fee-structures/{fee_structure_id}",
    summary="Update fee structure",
    response_description="Updated fee structure",
)
async def update_fee_structure(
    fee_structure_id: uuid.UUID,
    body: FeeStructureUpdateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-BIL:fee:update")),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing fee structure."""
    service = BillingService(db)
    result = await service.update_fee_structure(
        fee_structure_id=fee_structure_id,
        body=body,
        auth=auth,
        ip_address=get_client_ip(request),
    )
    return success_response(result)


# ---------------------------------------------------------------------------
# POST /billing/fee-assignments — Assign fee to student (ADM)
# ---------------------------------------------------------------------------
@router.post(
    "/fee-assignments",
    status_code=201,
    summary="Assign fee to student",
    response_description="Created fee assignment",
)
async def create_fee_assignment(
    body: FeeAssignmentCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-BIL:fee:assign")),
    db: AsyncSession = Depends(get_db),
):
    """Assign a fee structure to a student.

    Validates:
    1. Fee structure exists and belongs to the same school
    2. Student exists
    3. No duplicate assignment for the same fee + student
    """
    service = BillingService(db)
    result = await service.create_fee_assignment(
        body=body,
        auth=auth,
        ip_address=get_client_ip(request),
    )
    return success_response(result)


# ---------------------------------------------------------------------------
# POST /billing/fee-assignments/bulk — Bulk assign fee (ADM)
# ---------------------------------------------------------------------------
@router.post(
    "/fee-assignments/bulk",
    status_code=201,
    summary="Bulk assign fee to class/level",
    response_description="Bulk assignment results",
)
async def bulk_create_fee_assignments(
    body: FeeAssignmentBulkCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-BIL:fee:assign")),
    db: AsyncSession = Depends(get_db),
):
    """Bulk assign a fee structure to all students in a class or level.

    Provide class_id OR level (not both). Skips students who already have
    this fee assigned.
    """
    service = BillingService(db)
    result = await service.bulk_create_fee_assignments(
        body=body,
        auth=auth,
        ip_address=get_client_ip(request),
    )
    return success_response(result)


# ---------------------------------------------------------------------------
# GET /billing/fee-assignments — List fee assignments
# ---------------------------------------------------------------------------
@router.get(
    "/fee-assignments",
    summary="List fee assignments",
    response_description="List of fee assignments",
)
async def list_fee_assignments(
    fee_structure_id: uuid.UUID | None = Query(None),
    student_id: uuid.UUID | None = Query(None),
    status: str | None = Query(None, pattern="^(ACTIVE|EXEMPTED|ARCHIVED)$"),
    auth: AuthContext = Depends(requires_permission("PERM-BIL:fee:read")),
    db: AsyncSession = Depends(get_db),
):
    """List fee assignments with optional filters.

    PAR can only see assignments for their own children.
    """
    service = BillingService(db)
    result = await service.list_fee_assignments(
        auth=auth,
        fee_structure_id=fee_structure_id,
        student_id=student_id,
        status=status,
    )
    return list_response(result)


# ---------------------------------------------------------------------------
# POST /billing/generate-invoices — Generate invoices from fee structure (ADM)
# ---------------------------------------------------------------------------
@router.post(
    "/generate-invoices",
    status_code=201,
    summary="Generate invoices from fee structure",
    response_description="Generated invoices summary",
)
async def generate_invoices(
    body: InvoiceGenerateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-BIL:invoice:generate")),
    db: AsyncSession = Depends(get_db),
):
    """Generate invoices for all active fee assignments of a fee structure.

    For each assigned student:
    1. Find their parent (via parent_child_links)
    2. Calculate amount after discount
    3. Create invoice + line item

    Skips students without a linked parent.
    Due dates must satisfy due_date >= issued_date.
    """
    service = BillingService(db)
    result = await service.generate_invoices(
        body=body,
        auth=auth,
        ip_address=get_client_ip(request),
    )
    return success_response(result)


@router.get(
    "/sibling-policy",
    summary="Get sibling discount policy",
    response_description="Current school sibling discount policy",
)
async def get_sibling_policy(
    auth: AuthContext = Depends(requires_permission("PERM-BIL:sibling-policy:manage")),
    db: AsyncSession = Depends(get_db),
):
    service = BillingService(db)
    return success_response(await service.get_sibling_policy(auth=auth))


@router.put(
    "/sibling-policy",
    summary="Update sibling discount policy",
    response_description="Updated sibling discount policy",
)
async def update_sibling_policy(
    body: SiblingDiscountPolicyUpdateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-BIL:sibling-policy:manage")),
    db: AsyncSession = Depends(get_db),
):
    service = BillingService(db)
    return success_response(
        await service.update_sibling_policy(
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "/late-fee-policy",
    summary="Get late fee policy",
    response_description="Current school late fee policy",
)
async def get_late_fee_policy(
    auth: AuthContext = Depends(requires_permission("PERM-BIL:late-fee:manage")),
    db: AsyncSession = Depends(get_db),
):
    service = BillingService(db)
    return success_response(await service.get_late_fee_policy(auth=auth))


@router.put(
    "/late-fee-policy",
    summary="Update late fee policy",
    response_description="Updated late fee policy",
)
async def update_late_fee_policy(
    body: LateFeePolicyUpdateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-BIL:late-fee:manage")),
    db: AsyncSession = Depends(get_db),
):
    service = BillingService(db)
    return success_response(
        await service.update_late_fee_policy(
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.post(
    "/payment-plans",
    status_code=201,
    summary="Create payment plan",
    response_description="Created payment plan with installments",
)
async def create_payment_plan(
    body: PaymentPlanCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-BIL:payment-plan:create")),
    db: AsyncSession = Depends(get_db),
):
    service = PaymentPlanService(db)
    return success_response(
        await service.create_plan(
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "/payment-plans",
    summary="List payment plans",
    response_description="List of payment plans",
)
async def list_payment_plans(
    parent_id: uuid.UUID | None = Query(None),
    auth: AuthContext = Depends(requires_permission("PERM-BIL:payment-plan:read")),
    db: AsyncSession = Depends(get_db),
):
    service = PaymentPlanService(db)
    items = await service.list_plans(
        auth=auth,
        parent_id=parent_id,
    )
    return list_response(items, next_cursor=None, has_more=False)


@router.get(
    "/payment-plans/{plan_id}",
    summary="Get payment plan details",
    response_description="Payment plan with installments",
)
async def get_payment_plan(
    plan_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission("PERM-BIL:payment-plan:read")),
    db: AsyncSession = Depends(get_db),
):
    service = PaymentPlanService(db)
    return success_response(await service.get_plan(plan_id=plan_id, auth=auth))
