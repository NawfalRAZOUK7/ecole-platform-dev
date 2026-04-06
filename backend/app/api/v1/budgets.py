"""Budget API endpoints."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.permissions import (
    PERM_BUDGET_ALLOCATE,
    PERM_BUDGET_ANALYTICS_READ,
    PERM_BUDGET_APPROVE,
    PERM_BUDGET_CREATE,
    PERM_BUDGET_READ,
    PERM_BUDGET_REQUEST_CREATE,
    PERM_BUDGET_REQUEST_READ,
    PERM_BUDGET_TRANSACTION_CREATE,
    PERM_BUDGET_TRANSACTION_READ,
)
from app.core.request_utils import get_client_ip
from app.core.response import list_response, success_response
from app.schemas.budget import (
    BudgetAllocationCreateRequest,
    BudgetRequestCreateRequest,
    BudgetRequestReviewRequest,
    BudgetTransactionCreateRequest,
    MicroBudgetCreateRequest,
)
from app.services.budget_service import BudgetService

router = APIRouter(prefix="/budgets", tags=["budget"])


@router.post(
    "",
    status_code=201,
    summary="Create budget",
    description="Creates a micro-budget for the authenticated school and returns the new budget envelope with its initial allocation totals.",
    response_description="Created budget",
)
async def create_budget(
    body: MicroBudgetCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_BUDGET_CREATE)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a micro-budget for the authenticated school."""
    service = BudgetService(db)
    return success_response(
        await service.create_budget(
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "",
    summary="List budgets",
    description="Returns budgets within the authenticated school scope. Supports filtering by academic year and lifecycle status.",
    response_description="List of budgets",
)
async def list_budgets(
    academic_year_id: uuid.UUID | None = Query(None),
    status: str | None = Query(None, pattern="^(active|frozen|closed)$"),
    auth: AuthContext = Depends(requires_permission(PERM_BUDGET_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List budgets for the authenticated school."""
    service = BudgetService(db)
    return list_response(
        await service.list_budgets(
            auth=auth,
            academic_year_id=academic_year_id,
            status=status,
        )
    )


@router.get(
    "/analytics",
    summary="Get budget analytics",
    description="Returns budget utilization analytics for the authenticated school, optionally scoped to a single academic year.",
    response_description="Budget analytics summary",
)
async def get_budget_analytics(
    academic_year_id: uuid.UUID | None = Query(None),
    auth: AuthContext = Depends(requires_permission(PERM_BUDGET_ANALYTICS_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Return budget analytics for the authenticated school."""
    service = BudgetService(db)
    return success_response(
        await service.get_budget_analytics(
            auth=auth,
            academic_year_id=academic_year_id,
        )
    )


@router.get(
    "/{budget_id}",
    summary="Get budget",
    description="Fetches a single budget by ID and returns its current totals, status, and related academic-year context.",
    response_description="Budget detail",
)
async def get_budget(
    budget_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_BUDGET_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Fetch one budget."""
    service = BudgetService(db)
    return success_response(await service.get_budget(budget_id=budget_id, auth=auth))


@router.post(
    "/{budget_id}/allocations",
    status_code=201,
    summary="Create allocation",
    description="Creates a budget allocation within the selected budget and returns the stored allocation record for downstream request tracking.",
    response_description="Created allocation",
)
async def create_allocation(
    budget_id: uuid.UUID,
    body: BudgetAllocationCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_BUDGET_ALLOCATE)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create an allocation inside a budget."""
    service = BudgetService(db)
    return success_response(
        await service.create_allocation(
            budget_id=budget_id,
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "/{budget_id}/allocations",
    summary="List allocations for budget",
    description="Lists allocations attached to a budget. Supports filtering by class, teacher, and allocation status.",
    response_description="List of allocations",
)
async def list_budget_allocations(
    budget_id: uuid.UUID,
    class_id: uuid.UUID | None = Query(None),
    teacher_id: uuid.UUID | None = Query(None),
    status: str | None = Query(None, pattern="^(active|exhausted|frozen)$"),
    auth: AuthContext = Depends(requires_permission(PERM_BUDGET_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List allocations attached to a budget."""
    service = BudgetService(db)
    return list_response(
        await service.list_allocations(
            auth=auth,
            budget_id=budget_id,
            class_id=class_id,
            teacher_id=teacher_id,
            status=status,
        )
    )


@router.get(
    "/allocations/{allocation_id}",
    summary="Get allocation",
    description="Fetches a single allocation by ID and returns its current balances, ownership, and related budget metadata.",
    response_description="Allocation detail",
)
async def get_allocation(
    allocation_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_BUDGET_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Fetch one budget allocation."""
    service = BudgetService(db)
    return success_response(
        await service.get_allocation(
            allocation_id=allocation_id,
            auth=auth,
        )
    )


@router.post(
    "/allocations/{allocation_id}/requests",
    status_code=201,
    summary="Create budget request",
    description="Creates a spending request for a specific allocation and returns the pending request for review workflows.",
    response_description="Created budget request",
)
async def create_budget_request(
    allocation_id: uuid.UUID,
    body: BudgetRequestCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_BUDGET_REQUEST_CREATE)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a spending request for an allocation."""
    service = BudgetService(db)
    return success_response(
        await service.create_request(
            allocation_id=allocation_id,
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "/allocations/{allocation_id}/requests",
    summary="List budget requests",
    description="Returns spending requests linked to an allocation, with optional filters for requester and approval status.",
    response_description="List of budget requests",
)
async def list_budget_requests(
    allocation_id: uuid.UUID,
    requester_id: uuid.UUID | None = Query(None),
    status: str | None = Query(None, pattern="^(pending|approved|rejected|cancelled)$"),
    auth: AuthContext = Depends(requires_permission(PERM_BUDGET_REQUEST_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List budget requests for an allocation."""
    service = BudgetService(db)
    return list_response(
        await service.list_requests(
            auth=auth,
            allocation_id=allocation_id,
            requester_id=requester_id,
            status=status,
        )
    )


@router.post(
    "/requests/{request_id}/approve",
    summary="Approve budget request",
    description="Approves a pending budget request and returns the updated request record with the applied approval decision.",
    response_description="Approved budget request",
)
async def approve_budget_request(
    request_id: uuid.UUID,
    body: BudgetRequestReviewRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_BUDGET_APPROVE)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Approve a pending budget request."""
    service = BudgetService(db)
    return success_response(
        await service.approve_request(
            request_id=request_id,
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.post(
    "/requests/{request_id}/reject",
    summary="Reject budget request",
    description="Rejects a pending budget request and returns the updated request record, including the reviewer decision details.",
    response_description="Rejected budget request",
)
async def reject_budget_request(
    request_id: uuid.UUID,
    body: BudgetRequestReviewRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_BUDGET_APPROVE)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Reject a pending budget request."""
    service = BudgetService(db)
    return success_response(
        await service.reject_request(
            request_id=request_id,
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "/requests/{request_id}",
    summary="Get budget request",
    description="Fetches a single budget request by ID and returns its request, approval, and allocation metadata.",
    response_description="Budget request detail",
)
async def get_budget_request(
    request_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_BUDGET_REQUEST_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Fetch one budget request."""
    service = BudgetService(db)
    return success_response(await service.get_request(request_id=request_id, auth=auth))


@router.post(
    "/allocations/{allocation_id}/transactions",
    status_code=201,
    summary="Record budget transaction",
    description="Records a transaction against an allocation and returns the saved financial movement for audit and reconciliation flows.",
    response_description="Created budget transaction",
)
async def create_budget_transaction(
    allocation_id: uuid.UUID,
    body: BudgetTransactionCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_BUDGET_TRANSACTION_CREATE)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Record a budget transaction against an allocation."""
    service = BudgetService(db)
    return success_response(
        await service.record_transaction(
            allocation_id=allocation_id,
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "/allocations/{allocation_id}/transactions",
    summary="List budget transactions",
    description="Lists transactions recorded for an allocation, with optional filters for source request and transaction type.",
    response_description="List of budget transactions",
)
async def list_budget_transactions(
    allocation_id: uuid.UUID,
    request_id: uuid.UUID | None = Query(None),
    transaction_type: str | None = Query(
        None,
        pattern="^(allocation|expense|refund|adjustment)$",
    ),
    auth: AuthContext = Depends(requires_permission(PERM_BUDGET_TRANSACTION_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List transactions recorded for an allocation."""
    service = BudgetService(db)
    return list_response(
        await service.list_transactions(
            auth=auth,
            allocation_id=allocation_id,
            request_id=request_id,
            transaction_type=transaction_type,
        )
    )
