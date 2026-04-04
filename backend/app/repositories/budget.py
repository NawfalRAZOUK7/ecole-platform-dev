"""Repository helpers for class micro-budget workflows."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.budget import (
    BudgetAllocation,
    BudgetRequest,
    BudgetTransaction,
    MicroBudget,
)
from app.models.erp import AcademicYear, Class
from app.models.iam import User
from app.repositories.base import BaseRepository


class BudgetRepository(BaseRepository):
    """Data access for budgets, allocations, requests, transactions, and analytics."""

    async def get_user(self, user_id: uuid.UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_academic_year(self, academic_year_id: uuid.UUID) -> AcademicYear | None:
        result = await self.db.execute(
            select(AcademicYear).where(AcademicYear.id == academic_year_id)
        )
        return result.scalar_one_or_none()

    async def get_class(self, class_id: uuid.UUID) -> Class | None:
        result = await self.db.execute(select(Class).where(Class.id == class_id))
        return result.scalar_one_or_none()

    async def get_budget(
        self,
        budget_id: uuid.UUID,
        *,
        school_id: uuid.UUID | None = None,
        include_allocations: bool = False,
    ) -> MicroBudget | None:
        query = select(MicroBudget).where(MicroBudget.id == budget_id)
        if school_id is not None:
            query = query.where(MicroBudget.school_id == school_id)
        if include_allocations:
            query = query.options(selectinload(MicroBudget.allocations))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_budgets(
        self,
        *,
        school_id: uuid.UUID,
        academic_year_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> list[MicroBudget]:
        query = select(MicroBudget).where(MicroBudget.school_id == school_id)
        if academic_year_id is not None:
            query = query.where(MicroBudget.academic_year_id == academic_year_id)
        if status:
            query = query.where(MicroBudget.status == status)
        result = await self.db.execute(
            query.order_by(MicroBudget.created_at.desc(), MicroBudget.id.asc())
        )
        return list(result.scalars().all())

    async def create_budget(self, budget: MicroBudget) -> MicroBudget:
        self.db.add(budget)
        await self.db.flush()
        return budget

    async def save_budget(self, budget: MicroBudget) -> MicroBudget:
        self.db.add(budget)
        await self.db.flush()
        return budget

    async def get_allocation(
        self,
        allocation_id: uuid.UUID,
        *,
        school_id: uuid.UUID | None = None,
        include_budget: bool = False,
        include_requests: bool = False,
        include_transactions: bool = False,
    ) -> BudgetAllocation | None:
        query = select(BudgetAllocation).where(BudgetAllocation.id == allocation_id)
        if school_id is not None:
            query = query.join(MicroBudget, MicroBudget.id == BudgetAllocation.budget_id).where(
                MicroBudget.school_id == school_id
            )
        if include_budget:
            query = query.options(selectinload(BudgetAllocation.budget))
        if include_requests:
            query = query.options(selectinload(BudgetAllocation.requests))
        if include_transactions:
            query = query.options(selectinload(BudgetAllocation.transactions))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_allocations(
        self,
        *,
        school_id: uuid.UUID,
        budget_id: uuid.UUID | None = None,
        class_id: uuid.UUID | None = None,
        teacher_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> list[BudgetAllocation]:
        query = (
            select(BudgetAllocation)
            .join(MicroBudget, MicroBudget.id == BudgetAllocation.budget_id)
            .where(MicroBudget.school_id == school_id)
        )
        if budget_id is not None:
            query = query.where(BudgetAllocation.budget_id == budget_id)
        if class_id is not None:
            query = query.where(BudgetAllocation.class_id == class_id)
        if teacher_id is not None:
            query = query.where(BudgetAllocation.teacher_id == teacher_id)
        if status:
            query = query.where(BudgetAllocation.status == status)
        result = await self.db.execute(
            query.order_by(BudgetAllocation.allocated_at.desc(), BudgetAllocation.id.asc())
        )
        return list(result.scalars().all())

    async def create_allocation(self, allocation: BudgetAllocation) -> BudgetAllocation:
        self.db.add(allocation)
        await self.db.flush()
        return allocation

    async def save_allocation(self, allocation: BudgetAllocation) -> BudgetAllocation:
        self.db.add(allocation)
        await self.db.flush()
        return allocation

    async def get_request(
        self,
        request_id: uuid.UUID,
        *,
        school_id: uuid.UUID | None = None,
        include_allocation: bool = False,
    ) -> BudgetRequest | None:
        query = select(BudgetRequest).where(BudgetRequest.id == request_id)
        if school_id is not None:
            query = (
                query.join(BudgetAllocation, BudgetAllocation.id == BudgetRequest.allocation_id)
                .join(MicroBudget, MicroBudget.id == BudgetAllocation.budget_id)
                .where(MicroBudget.school_id == school_id)
            )
        if include_allocation:
            query = query.options(
                selectinload(BudgetRequest.allocation).selectinload(BudgetAllocation.budget)
            )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_requests(
        self,
        *,
        school_id: uuid.UUID,
        allocation_id: uuid.UUID | None = None,
        requester_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> list[BudgetRequest]:
        query = (
            select(BudgetRequest)
            .join(BudgetAllocation, BudgetAllocation.id == BudgetRequest.allocation_id)
            .join(MicroBudget, MicroBudget.id == BudgetAllocation.budget_id)
            .where(MicroBudget.school_id == school_id)
        )
        if allocation_id is not None:
            query = query.where(BudgetRequest.allocation_id == allocation_id)
        if requester_id is not None:
            query = query.where(BudgetRequest.requester_id == requester_id)
        if status:
            query = query.where(BudgetRequest.status == status)
        result = await self.db.execute(
            query.order_by(BudgetRequest.created_at.desc(), BudgetRequest.id.asc())
        )
        return list(result.scalars().all())

    async def create_request(self, request: BudgetRequest) -> BudgetRequest:
        self.db.add(request)
        await self.db.flush()
        return request

    async def save_request(self, request: BudgetRequest) -> BudgetRequest:
        self.db.add(request)
        await self.db.flush()
        return request

    async def get_transaction(
        self,
        transaction_id: uuid.UUID,
        *,
        school_id: uuid.UUID | None = None,
        include_allocation: bool = False,
    ) -> BudgetTransaction | None:
        query = select(BudgetTransaction).where(BudgetTransaction.id == transaction_id)
        if school_id is not None:
            query = (
                query.join(
                    BudgetAllocation,
                    BudgetAllocation.id == BudgetTransaction.allocation_id,
                )
                .join(MicroBudget, MicroBudget.id == BudgetAllocation.budget_id)
                .where(MicroBudget.school_id == school_id)
            )
        if include_allocation:
            query = query.options(
                selectinload(BudgetTransaction.allocation).selectinload(
                    BudgetAllocation.budget
                )
            )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_transactions(
        self,
        *,
        school_id: uuid.UUID,
        allocation_id: uuid.UUID | None = None,
        request_id: uuid.UUID | None = None,
        transaction_type: str | None = None,
    ) -> list[BudgetTransaction]:
        query = (
            select(BudgetTransaction)
            .join(BudgetAllocation, BudgetAllocation.id == BudgetTransaction.allocation_id)
            .join(MicroBudget, MicroBudget.id == BudgetAllocation.budget_id)
            .where(MicroBudget.school_id == school_id)
        )
        if allocation_id is not None:
            query = query.where(BudgetTransaction.allocation_id == allocation_id)
        if request_id is not None:
            query = query.where(BudgetTransaction.request_id == request_id)
        if transaction_type:
            query = query.where(BudgetTransaction.transaction_type == transaction_type)
        result = await self.db.execute(
            query.order_by(
                BudgetTransaction.recorded_at.desc(),
                BudgetTransaction.id.asc(),
            )
        )
        return list(result.scalars().all())

    async def create_transaction(
        self,
        transaction: BudgetTransaction,
    ) -> BudgetTransaction:
        self.db.add(transaction)
        await self.db.flush()
        return transaction

    async def save_transaction(
        self,
        transaction: BudgetTransaction,
    ) -> BudgetTransaction:
        self.db.add(transaction)
        await self.db.flush()
        return transaction


__all__ = ["BudgetRepository"]
