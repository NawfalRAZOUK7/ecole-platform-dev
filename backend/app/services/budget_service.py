"""Service layer for class micro-budget workflows."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import AuthContext, verify_school_boundary
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.unit_of_work import UnitOfWork
from app.domain.events.budget import (
    BudgetAllocated,
    BudgetCreated,
    BudgetRequestReviewed,
    BudgetRequestSubmitted,
    BudgetTransactionRecorded,
)
from app.models.budget import (
    BudgetAllocation,
    BudgetRequest,
    BudgetTransaction,
    MicroBudget,
)
from app.repositories.budget import BudgetRepository
from app.schemas.budget import (
    BudgetAllocationCreateRequest,
    BudgetAllocationResponse,
    BudgetAllocationUpdateRequest,
    BudgetAnalyticsResponse,
    BudgetRequestCreateRequest,
    BudgetRequestResponse,
    BudgetRequestReviewRequest,
    BudgetRequestUpdateRequest,
    BudgetTransactionCreateRequest,
    BudgetTransactionResponse,
    BudgetTransactionUpdateRequest,
    MicroBudgetCreateRequest,
    MicroBudgetResponse,
    MicroBudgetUpdateRequest,
)
from app.services.audit import AuditService
from app.services.event_dispatcher import EventDispatcher


def _iso(value: datetime | None) -> str | None:
    return value.astimezone(timezone.utc).isoformat() if value is not None else None


class BudgetService:
    """Business logic for budgets, allocations, requests, transactions, and analytics."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = BudgetRepository(db)
        self.audit = AuditService(db)
        self._dispatcher = EventDispatcher(db)

    def _budget_to_response(self, budget: MicroBudget) -> dict[str, Any]:
        return MicroBudgetResponse(
            id=str(budget.id),
            school_id=str(budget.school_id),
            academic_year_id=str(budget.academic_year_id),
            total_amount=float(budget.total_amount),
            allocated_amount=float(budget.allocated_amount),
            remaining_amount=float(budget.remaining_amount),
            currency=budget.currency,
            status=budget.status,
            created_by=str(budget.created_by),
            created_at=_iso(budget.created_at) or "",
            updated_at=_iso(budget.updated_at),
        ).model_dump()

    def _allocation_to_response(self, allocation: BudgetAllocation) -> dict[str, Any]:
        return BudgetAllocationResponse(
            id=str(allocation.id),
            budget_id=str(allocation.budget_id),
            class_id=str(allocation.class_id)
            if allocation.class_id is not None
            else None,
            teacher_id=str(allocation.teacher_id)
            if allocation.teacher_id is not None
            else None,
            label=allocation.label,
            amount=float(allocation.amount),
            spent=float(allocation.spent),
            remaining=float(allocation.remaining),
            currency=allocation.currency,
            allocated_by=str(allocation.allocated_by),
            allocated_at=_iso(allocation.allocated_at) or "",
            status=allocation.status,
            created_at=_iso(allocation.created_at) or "",
            updated_at=_iso(allocation.updated_at),
        ).model_dump()

    def _request_to_response(self, request: BudgetRequest) -> dict[str, Any]:
        return BudgetRequestResponse(
            id=str(request.id),
            allocation_id=str(request.allocation_id),
            requester_id=str(request.requester_id),
            amount=float(request.amount),
            currency=request.currency,
            description=request.description,
            justification=request.justification,
            status=request.status,
            reviewed_by=str(request.reviewed_by)
            if request.reviewed_by is not None
            else None,
            reviewed_at=_iso(request.reviewed_at),
            review_comment=request.review_comment,
            created_at=_iso(request.created_at) or "",
            updated_at=_iso(request.updated_at),
        ).model_dump()

    def _transaction_to_response(
        self,
        transaction: BudgetTransaction,
    ) -> dict[str, Any]:
        return BudgetTransactionResponse(
            id=str(transaction.id),
            allocation_id=str(transaction.allocation_id),
            request_id=str(transaction.request_id)
            if transaction.request_id is not None
            else None,
            amount=float(transaction.amount),
            transaction_type=transaction.transaction_type,
            description=transaction.description,
            receipt_url=transaction.receipt_url,
            recorded_by=str(transaction.recorded_by),
            recorded_at=_iso(transaction.recorded_at) or "",
            created_at=_iso(transaction.created_at) or "",
            updated_at=_iso(transaction.updated_at),
        ).model_dump()

    async def _get_budget_or_404(
        self, budget_id: uuid.UUID, auth: AuthContext
    ) -> MicroBudget:
        budget = await self.repo.get_budget(budget_id, school_id=auth.school_id)
        if budget is None:
            raise NotFoundError("Budget not found", error_code="ERR-BUDGET-404")
        return budget

    async def _get_allocation_or_404(
        self,
        allocation_id: uuid.UUID,
        auth: AuthContext,
        *,
        include_budget: bool = False,
        include_requests: bool = False,
        include_transactions: bool = False,
    ) -> BudgetAllocation:
        allocation = await self.repo.get_allocation(
            allocation_id,
            school_id=auth.school_id,
            include_budget=include_budget,
            include_requests=include_requests,
            include_transactions=include_transactions,
        )
        if allocation is None:
            raise NotFoundError(
                "Budget allocation not found", error_code="ERR-BUDGET-404"
            )
        return allocation

    async def _get_request_or_404(
        self,
        request_id: uuid.UUID,
        auth: AuthContext,
        *,
        include_allocation: bool = False,
    ) -> BudgetRequest:
        request = await self.repo.get_request(
            request_id,
            school_id=auth.school_id,
            include_allocation=include_allocation,
        )
        if request is None:
            raise NotFoundError("Budget request not found", error_code="ERR-BUDGET-404")
        return request

    async def _ensure_user_in_school(
        self,
        user_id: uuid.UUID,
        auth: AuthContext,
        *,
        label: str,
    ) -> None:
        user = await self.repo.get_user(user_id)
        if user is None:
            raise NotFoundError(f"{label} user not found", error_code="ERR-BUDGET-404")
        verify_school_boundary(user.school_id, auth)

    async def create_budget(
        self,
        *,
        body: MicroBudgetCreateRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        academic_year = await self.repo.get_academic_year(body.academic_year_id)
        if academic_year is None:
            raise NotFoundError("Academic year not found", error_code="ERR-BUDGET-404")
        verify_school_boundary(academic_year.school_id, auth)

        async with UnitOfWork(self.db) as uow:
            repo = BudgetRepository(uow.session)
            audit = AuditService(uow.session)
            dispatcher = EventDispatcher(uow.session)
            budget = MicroBudget(
                school_id=auth.school_id,
                academic_year_id=body.academic_year_id,
                total_amount=body.total_amount,
                allocated_amount=0,
                remaining_amount=body.total_amount,
                currency=body.currency,
                status=body.status,
                created_by=auth.user_id,
            )
            created = await repo.create_budget(budget)
            response = self._budget_to_response(created)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="budget.create",
                outcome="success",
                target_type="micro_budget",
                target_id=created.id,
                entity_after=response,
                ip_address=ip_address,
            )
            await dispatcher.dispatch(
                BudgetCreated(
                    school_id=auth.school_id,
                    actor_id=auth.user_id,
                    budget_id=created.id,
                    academic_year_id=created.academic_year_id,
                    total_amount=float(created.total_amount),
                )
            )
            await uow.commit()
        return response

    async def list_budgets(
        self,
        *,
        auth: AuthContext,
        academic_year_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        budgets = await self.repo.list_budgets(
            school_id=auth.school_id,
            academic_year_id=academic_year_id,
            status=status,
        )
        return [self._budget_to_response(item) for item in budgets]

    async def get_budget(
        self,
        *,
        budget_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict[str, Any]:
        budget = await self._get_budget_or_404(budget_id, auth)
        return self._budget_to_response(budget)

    async def update_budget(
        self,
        *,
        budget_id: uuid.UUID,
        body: MicroBudgetUpdateRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        budget = await self._get_budget_or_404(budget_id, auth)
        payload = body.model_dump(exclude_unset=True)
        if "total_amount" in payload and payload["total_amount"] < float(
            budget.allocated_amount
        ):
            raise ValidationError(
                "Budget total_amount cannot be lower than allocated_amount",
                error_code="ERR-BUDGET-422",
            )

        async with UnitOfWork(self.db) as uow:
            repo = BudgetRepository(uow.session)
            audit = AuditService(uow.session)
            current_budget = await repo.get_budget(budget_id, school_id=auth.school_id)
            if current_budget is None:
                raise NotFoundError("Budget not found", error_code="ERR-BUDGET-404")
            budget = current_budget
            before = self._budget_to_response(budget)
            for field, value in payload.items():
                setattr(budget, field, value)
            if "total_amount" in payload:
                budget.remaining_amount = float(budget.total_amount) - float(
                    budget.allocated_amount
                )
            saved = await repo.save_budget(budget)
            response = self._budget_to_response(saved)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="budget.update",
                outcome="success",
                target_type="micro_budget",
                target_id=saved.id,
                entity_before=before,
                entity_after=response,
                ip_address=ip_address,
            )
            await uow.commit()
        return response

    async def create_allocation(
        self,
        *,
        budget_id: uuid.UUID,
        body: BudgetAllocationCreateRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        budget = await self._get_budget_or_404(budget_id, auth)
        if body.amount > float(budget.remaining_amount):
            raise ValidationError(
                "Budget does not have enough unallocated funds",
                error_code="ERR-BUDGET-422",
            )
        if body.class_id is None and body.teacher_id is None:
            raise ValidationError(
                "Allocation must target a class or a teacher",
                error_code="ERR-BUDGET-422",
            )
        if body.class_id is not None:
            school_class = await self.repo.get_class(body.class_id)
            if school_class is None:
                raise NotFoundError("Class not found", error_code="ERR-BUDGET-404")
            verify_school_boundary(school_class.school_id, auth)
        if body.teacher_id is not None:
            await self._ensure_user_in_school(body.teacher_id, auth, label="Teacher")

        async with UnitOfWork(self.db) as uow:
            repo = BudgetRepository(uow.session)
            audit = AuditService(uow.session)
            dispatcher = EventDispatcher(uow.session)
            current_budget = await repo.get_budget(budget_id, school_id=auth.school_id)
            if current_budget is None:
                raise NotFoundError("Budget not found", error_code="ERR-BUDGET-404")
            budget = current_budget
            allocation = BudgetAllocation(
                budget_id=budget.id,
                class_id=body.class_id,
                teacher_id=body.teacher_id,
                label=body.label,
                amount=body.amount,
                spent=0,
                remaining=body.amount,
                currency=body.currency,
                allocated_by=auth.user_id,
                status=body.status,
            )
            created = await repo.create_allocation(allocation)
            budget.allocated_amount = float(budget.allocated_amount) + body.amount
            budget.remaining_amount = float(budget.total_amount) - float(
                budget.allocated_amount
            )
            await repo.save_budget(budget)
            transaction = BudgetTransaction(
                allocation_id=created.id,
                amount=body.amount,
                transaction_type="allocation",
                description=f"Initial allocation: {created.label}",
                recorded_by=auth.user_id,
                recorded_at=created.allocated_at,
            )
            await repo.create_transaction(transaction)
            response = self._allocation_to_response(created)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="budget.allocate",
                outcome="success",
                target_type="budget_allocation",
                target_id=created.id,
                entity_after=response,
                ip_address=ip_address,
            )
            await dispatcher.dispatch(
                BudgetAllocated(
                    school_id=auth.school_id,
                    actor_id=auth.user_id,
                    allocation_id=created.id,
                    budget_id=created.budget_id,
                    amount=float(created.amount),
                )
            )
            await dispatcher.dispatch(
                BudgetTransactionRecorded(
                    school_id=auth.school_id,
                    actor_id=auth.user_id,
                    transaction_id=transaction.id,
                    allocation_id=created.id,
                    transaction_type=transaction.transaction_type,
                    amount=float(transaction.amount),
                )
            )
            await uow.commit()
        return response

    async def list_allocations(
        self,
        *,
        auth: AuthContext,
        budget_id: uuid.UUID | None = None,
        class_id: uuid.UUID | None = None,
        teacher_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        allocations = await self.repo.list_allocations(
            school_id=auth.school_id,
            budget_id=budget_id,
            class_id=class_id,
            teacher_id=teacher_id,
            status=status,
        )
        return [self._allocation_to_response(item) for item in allocations]

    async def get_allocation(
        self,
        *,
        allocation_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict[str, Any]:
        allocation = await self._get_allocation_or_404(
            allocation_id,
            auth,
            include_budget=True,
        )
        return self._allocation_to_response(allocation)

    async def update_allocation(
        self,
        *,
        allocation_id: uuid.UUID,
        body: BudgetAllocationUpdateRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        allocation = await self._get_allocation_or_404(
            allocation_id,
            auth,
            include_budget=True,
        )
        if allocation.budget is None:
            raise NotFoundError("Budget not found", error_code="ERR-BUDGET-404")
        payload = body.model_dump(exclude_unset=True)
        if "class_id" in payload and payload["class_id"] is not None:
            school_class = await self.repo.get_class(payload["class_id"])
            if school_class is None:
                raise NotFoundError("Class not found", error_code="ERR-BUDGET-404")
            verify_school_boundary(school_class.school_id, auth)
        if "teacher_id" in payload and payload["teacher_id"] is not None:
            await self._ensure_user_in_school(
                payload["teacher_id"], auth, label="Teacher"
            )

        new_amount = payload.get("amount", float(allocation.amount))
        if new_amount < float(allocation.spent):
            raise ValidationError(
                "Allocation amount cannot be lower than spent",
                error_code="ERR-BUDGET-422",
            )
        budget_delta = new_amount - float(allocation.amount)
        if budget_delta > 0 and budget_delta > float(
            allocation.budget.remaining_amount
        ):
            raise ValidationError(
                "Budget does not have enough unallocated funds",
                error_code="ERR-BUDGET-422",
            )

        async with UnitOfWork(self.db) as uow:
            repo = BudgetRepository(uow.session)
            audit = AuditService(uow.session)
            current_allocation = await repo.get_allocation(
                allocation_id,
                school_id=auth.school_id,
                include_budget=True,
            )
            if current_allocation is None or current_allocation.budget is None:
                raise NotFoundError(
                    "Budget allocation not found", error_code="ERR-BUDGET-404"
                )
            allocation = current_allocation
            before = self._allocation_to_response(allocation)
            for field, value in payload.items():
                setattr(allocation, field, value)
            allocation.remaining = float(allocation.amount) - float(allocation.spent)
            if allocation.remaining == 0 and allocation.status == "active":
                allocation.status = "exhausted"
            budget = allocation.budget
            budget.allocated_amount = float(budget.allocated_amount) + budget_delta
            budget.remaining_amount = float(budget.total_amount) - float(
                budget.allocated_amount
            )
            await repo.save_budget(budget)
            saved = await repo.save_allocation(allocation)
            response = self._allocation_to_response(saved)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="budget.allocation.update",
                outcome="success",
                target_type="budget_allocation",
                target_id=saved.id,
                entity_before=before,
                entity_after=response,
                ip_address=ip_address,
            )
            await uow.commit()
        return response

    async def create_request(
        self,
        *,
        allocation_id: uuid.UUID,
        body: BudgetRequestCreateRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        allocation = await self._get_allocation_or_404(allocation_id, auth)
        if body.amount > float(allocation.remaining):
            raise ValidationError(
                "Allocation does not have enough remaining funds",
                error_code="ERR-BUDGET-422",
            )

        async with UnitOfWork(self.db) as uow:
            repo = BudgetRepository(uow.session)
            audit = AuditService(uow.session)
            dispatcher = EventDispatcher(uow.session)
            request = BudgetRequest(
                allocation_id=allocation_id,
                requester_id=auth.user_id,
                amount=body.amount,
                currency=body.currency,
                description=body.description,
                justification=body.justification,
                status="pending",
            )
            created = await repo.create_request(request)
            response = self._request_to_response(created)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="budget.request.create",
                outcome="success",
                target_type="budget_request",
                target_id=created.id,
                entity_after=response,
                ip_address=ip_address,
            )
            await dispatcher.dispatch(
                BudgetRequestSubmitted(
                    school_id=auth.school_id,
                    actor_id=auth.user_id,
                    request_id=created.id,
                    allocation_id=created.allocation_id,
                    requester_id=created.requester_id,
                    amount=float(created.amount),
                )
            )
            await uow.commit()
        return response

    async def list_requests(
        self,
        *,
        auth: AuthContext,
        allocation_id: uuid.UUID | None = None,
        requester_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        requests = await self.repo.list_requests(
            school_id=auth.school_id,
            allocation_id=allocation_id,
            requester_id=requester_id,
            status=status,
        )
        return [self._request_to_response(item) for item in requests]

    async def get_request(
        self,
        *,
        request_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict[str, Any]:
        request = await self._get_request_or_404(request_id, auth)
        return self._request_to_response(request)

    async def update_request(
        self,
        *,
        request_id: uuid.UUID,
        body: BudgetRequestUpdateRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        request = await self._get_request_or_404(
            request_id,
            auth,
            include_allocation=True,
        )
        if request.status != "pending":
            raise ConflictError(
                "Only pending budget requests can be updated",
                error_code="ERR-BUDGET-409",
            )
        if request.requester_id != auth.user_id:
            raise ConflictError(
                "Only the requester can update a pending budget request",
                error_code="ERR-BUDGET-409",
            )
        payload = body.model_dump(exclude_unset=True)
        next_amount = payload.get("amount", float(request.amount))
        if request.allocation is not None and next_amount > float(
            request.allocation.remaining
        ):
            raise ValidationError(
                "Allocation does not have enough remaining funds",
                error_code="ERR-BUDGET-422",
            )

        async with UnitOfWork(self.db) as uow:
            repo = BudgetRepository(uow.session)
            audit = AuditService(uow.session)
            current_request = await repo.get_request(
                request_id,
                school_id=auth.school_id,
                include_allocation=True,
            )
            if current_request is None:
                raise NotFoundError(
                    "Budget request not found", error_code="ERR-BUDGET-404"
                )
            request = current_request
            before = self._request_to_response(request)
            for field, value in payload.items():
                setattr(request, field, value)
            saved = await repo.save_request(request)
            response = self._request_to_response(saved)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="budget.request.update",
                outcome="success",
                target_type="budget_request",
                target_id=saved.id,
                entity_before=before,
                entity_after=response,
                ip_address=ip_address,
            )
            await uow.commit()
        return response

    async def approve_request(
        self,
        *,
        request_id: uuid.UUID,
        body: BudgetRequestReviewRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        request = await self._get_request_or_404(
            request_id,
            auth,
            include_allocation=True,
        )
        if request.status != "pending":
            raise ConflictError(
                "Budget request has already been reviewed",
                error_code="ERR-BUDGET-409",
            )
        if request.allocation is None or request.allocation.budget is None:
            raise NotFoundError(
                "Budget allocation not found", error_code="ERR-BUDGET-404"
            )
        if float(request.amount) > float(request.allocation.remaining):
            raise ValidationError(
                "Allocation does not have enough remaining funds",
                error_code="ERR-BUDGET-422",
            )

        reviewed_at = datetime.now(timezone.utc)
        async with UnitOfWork(self.db) as uow:
            repo = BudgetRepository(uow.session)
            audit = AuditService(uow.session)
            dispatcher = EventDispatcher(uow.session)
            current_request = await repo.get_request(
                request_id,
                school_id=auth.school_id,
                include_allocation=True,
            )
            if (
                current_request is None
                or current_request.allocation is None
                or current_request.allocation.budget is None
            ):
                raise NotFoundError(
                    "Budget request not found", error_code="ERR-BUDGET-404"
                )
            request = current_request
            if request.status != "pending":
                raise ConflictError(
                    "Budget request has already been reviewed",
                    error_code="ERR-BUDGET-409",
                )
            allocation = request.allocation
            if float(request.amount) > float(allocation.remaining):
                raise ValidationError(
                    "Allocation does not have enough remaining funds",
                    error_code="ERR-BUDGET-422",
                )
            before = self._request_to_response(request)
            request.status = "approved"
            request.reviewed_by = auth.user_id
            request.reviewed_at = reviewed_at
            request.review_comment = body.review_comment
            allocation.spent = float(allocation.spent) + float(request.amount)
            allocation.remaining = float(allocation.amount) - float(allocation.spent)
            if allocation.remaining <= 0:
                allocation.remaining = 0
                allocation.status = "exhausted"
            saved_request = await repo.save_request(request)
            await repo.save_allocation(allocation)
            transaction = BudgetTransaction(
                allocation_id=allocation.id,
                request_id=request.id,
                amount=float(request.amount),
                transaction_type="expense",
                description=request.description[:300],
                recorded_by=auth.user_id,
                recorded_at=reviewed_at,
            )
            saved_transaction = await repo.create_transaction(transaction)
            response = self._request_to_response(saved_request)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="budget.request.approve",
                outcome="success",
                target_type="budget_request",
                target_id=saved_request.id,
                entity_before=before,
                entity_after=response,
                ip_address=ip_address,
            )
            await dispatcher.dispatch(
                BudgetRequestReviewed(
                    school_id=auth.school_id,
                    actor_id=auth.user_id,
                    request_id=saved_request.id,
                    allocation_id=saved_request.allocation_id,
                    decision=saved_request.status,
                )
            )
            await dispatcher.dispatch(
                BudgetTransactionRecorded(
                    school_id=auth.school_id,
                    actor_id=auth.user_id,
                    transaction_id=saved_transaction.id,
                    allocation_id=saved_transaction.allocation_id,
                    transaction_type=saved_transaction.transaction_type,
                    amount=float(saved_transaction.amount),
                )
            )
            await uow.commit()
        return response

    async def reject_request(
        self,
        *,
        request_id: uuid.UUID,
        body: BudgetRequestReviewRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        request = await self._get_request_or_404(request_id, auth)
        if request.status != "pending":
            raise ConflictError(
                "Budget request has already been reviewed",
                error_code="ERR-BUDGET-409",
            )

        reviewed_at = datetime.now(timezone.utc)
        async with UnitOfWork(self.db) as uow:
            repo = BudgetRepository(uow.session)
            audit = AuditService(uow.session)
            dispatcher = EventDispatcher(uow.session)
            current_request = await repo.get_request(
                request_id, school_id=auth.school_id
            )
            if current_request is None:
                raise NotFoundError(
                    "Budget request not found", error_code="ERR-BUDGET-404"
                )
            request = current_request
            if request.status != "pending":
                raise ConflictError(
                    "Budget request has already been reviewed",
                    error_code="ERR-BUDGET-409",
                )
            before = self._request_to_response(request)
            request.status = "rejected"
            request.reviewed_by = auth.user_id
            request.reviewed_at = reviewed_at
            request.review_comment = body.review_comment
            saved = await repo.save_request(request)
            response = self._request_to_response(saved)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="budget.request.reject",
                outcome="success",
                target_type="budget_request",
                target_id=saved.id,
                entity_before=before,
                entity_after=response,
                ip_address=ip_address,
            )
            await dispatcher.dispatch(
                BudgetRequestReviewed(
                    school_id=auth.school_id,
                    actor_id=auth.user_id,
                    request_id=saved.id,
                    allocation_id=saved.allocation_id,
                    decision=saved.status,
                )
            )
            await uow.commit()
        return response

    async def record_transaction(
        self,
        *,
        allocation_id: uuid.UUID,
        body: BudgetTransactionCreateRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        allocation = await self._get_allocation_or_404(
            allocation_id,
            auth,
            include_budget=True,
        )
        if allocation.budget is None:
            raise NotFoundError("Budget not found", error_code="ERR-BUDGET-404")
        if body.request_id is not None:
            request = await self.repo.get_request(
                body.request_id, school_id=auth.school_id
            )
            if request is None or request.allocation_id != allocation_id:
                raise NotFoundError(
                    "Budget request not found", error_code="ERR-BUDGET-404"
                )

        async with UnitOfWork(self.db) as uow:
            repo = BudgetRepository(uow.session)
            audit = AuditService(uow.session)
            dispatcher = EventDispatcher(uow.session)
            current_allocation = await repo.get_allocation(
                allocation_id,
                school_id=auth.school_id,
                include_budget=True,
            )
            if current_allocation is None or current_allocation.budget is None:
                raise NotFoundError(
                    "Budget allocation not found", error_code="ERR-BUDGET-404"
                )
            allocation = current_allocation
            budget = allocation.budget

            if body.transaction_type == "expense":
                if body.amount > float(allocation.remaining):
                    raise ValidationError(
                        "Allocation does not have enough remaining funds",
                        error_code="ERR-BUDGET-422",
                    )
                allocation.spent = float(allocation.spent) + body.amount
            elif body.transaction_type == "refund":
                allocation.spent = max(float(allocation.spent) - body.amount, 0.0)
            else:
                if body.amount > float(budget.remaining_amount):
                    raise ValidationError(
                        "Budget does not have enough unallocated funds",
                        error_code="ERR-BUDGET-422",
                    )
                allocation.amount = float(allocation.amount) + body.amount
                budget.allocated_amount = float(budget.allocated_amount) + body.amount
                budget.remaining_amount = float(budget.total_amount) - float(
                    budget.allocated_amount
                )
                await repo.save_budget(budget)

            allocation.remaining = float(allocation.amount) - float(allocation.spent)
            allocation.status = (
                "exhausted" if allocation.remaining <= 0 else allocation.status
            )
            await repo.save_allocation(allocation)
            transaction = BudgetTransaction(
                allocation_id=allocation.id,
                request_id=body.request_id,
                amount=body.amount,
                transaction_type=body.transaction_type,
                description=body.description,
                receipt_url=body.receipt_url,
                recorded_by=auth.user_id,
            )
            created = await repo.create_transaction(transaction)
            response = self._transaction_to_response(created)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="budget.transaction.record",
                outcome="success",
                target_type="budget_transaction",
                target_id=created.id,
                entity_after=response,
                ip_address=ip_address,
            )
            await dispatcher.dispatch(
                BudgetTransactionRecorded(
                    school_id=auth.school_id,
                    actor_id=auth.user_id,
                    transaction_id=created.id,
                    allocation_id=created.allocation_id,
                    transaction_type=created.transaction_type,
                    amount=float(created.amount),
                )
            )
            await uow.commit()
        return response

    async def list_transactions(
        self,
        *,
        auth: AuthContext,
        allocation_id: uuid.UUID | None = None,
        request_id: uuid.UUID | None = None,
        transaction_type: str | None = None,
    ) -> list[dict[str, Any]]:
        transactions = await self.repo.list_transactions(
            school_id=auth.school_id,
            allocation_id=allocation_id,
            request_id=request_id,
            transaction_type=transaction_type,
        )
        return [self._transaction_to_response(item) for item in transactions]

    async def update_transaction(
        self,
        *,
        transaction_id: uuid.UUID,
        body: BudgetTransactionUpdateRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        transaction = await self.repo.get_transaction(
            transaction_id, school_id=auth.school_id
        )
        if transaction is None:
            raise NotFoundError(
                "Budget transaction not found", error_code="ERR-BUDGET-404"
            )

        async with UnitOfWork(self.db) as uow:
            repo = BudgetRepository(uow.session)
            audit = AuditService(uow.session)
            transaction = await repo.get_transaction(
                transaction_id,
                school_id=auth.school_id,
            )
            if transaction is None:
                raise NotFoundError(
                    "Budget transaction not found", error_code="ERR-BUDGET-404"
                )
            before = self._transaction_to_response(transaction)
            for field, value in body.model_dump(exclude_unset=True).items():
                setattr(transaction, field, value)
            saved = await repo.save_transaction(transaction)
            response = self._transaction_to_response(saved)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="budget.transaction.update",
                outcome="success",
                target_type="budget_transaction",
                target_id=saved.id,
                entity_before=before,
                entity_after=response,
                ip_address=ip_address,
            )
            await uow.commit()
        return response

    async def get_budget_analytics(
        self,
        *,
        auth: AuthContext,
        academic_year_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        budgets = await self.repo.list_budgets(
            school_id=auth.school_id,
            academic_year_id=academic_year_id,
        )
        budget_ids = {budget.id for budget in budgets}
        allocations = await self.repo.list_allocations(
            school_id=auth.school_id,
            status=None,
        )
        if budget_ids:
            allocations = [item for item in allocations if item.budget_id in budget_ids]
        else:
            allocations = []
        allocation_ids = {allocation.id for allocation in allocations}
        requests = await self.repo.list_requests(
            school_id=auth.school_id,
            status=None,
        )
        requests = [item for item in requests if item.allocation_id in allocation_ids]
        transactions = await self.repo.list_transactions(
            school_id=auth.school_id,
            transaction_type=None,
        )
        transactions = [
            item for item in transactions if item.allocation_id in allocation_ids
        ]

        total_budget_amount = sum(float(item.total_amount) for item in budgets)
        total_allocated_amount = sum(float(item.allocated_amount) for item in budgets)
        total_remaining_unallocated = sum(
            float(item.remaining_amount) for item in budgets
        )
        total_spent_amount = sum(float(item.spent) for item in allocations)
        total_allocation_remaining = sum(float(item.remaining) for item in allocations)
        pending_request_amount = sum(
            float(item.amount) for item in requests if item.status == "pending"
        )
        approved_request_amount = sum(
            float(item.amount) for item in requests if item.status == "approved"
        )

        return BudgetAnalyticsResponse(
            school_id=str(auth.school_id),
            academic_year_id=str(academic_year_id)
            if academic_year_id is not None
            else None,
            budget_count=len(budgets),
            allocation_count=len(allocations),
            request_count=len(requests),
            transaction_count=len(transactions),
            total_budget_amount=round(total_budget_amount, 2),
            total_allocated_amount=round(total_allocated_amount, 2),
            total_remaining_unallocated=round(total_remaining_unallocated, 2),
            total_spent_amount=round(total_spent_amount, 2),
            total_allocation_remaining=round(total_allocation_remaining, 2),
            pending_request_amount=round(pending_request_amount, 2),
            approved_request_amount=round(approved_request_amount, 2),
            utilization_rate=round(
                (total_spent_amount / total_allocated_amount) * 100
                if total_allocated_amount
                else 0.0,
                2,
            ),
        ).model_dump()


__all__ = ["BudgetService"]
