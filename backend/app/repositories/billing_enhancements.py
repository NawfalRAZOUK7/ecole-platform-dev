"""Repository helpers for billing sibling policies, late fees, and payment plans."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.billing import (
    Installment,
    Invoice,
    LateFeePolicy,
    PaymentPlan,
    SiblingDiscountPolicy,
)
from app.models.iam import ParentChildLink, StudentProfile, User
from app.repositories.base import BaseRepository


class BillingEnhancementsRepository(BaseRepository):
    """Persistence helpers for ENH-C1 billing enhancements."""

    async def get_sibling_discount_policy(
        self,
        *,
        school_id: uuid.UUID,
    ) -> SiblingDiscountPolicy | None:
        result = await self.db.execute(
            select(SiblingDiscountPolicy).where(
                SiblingDiscountPolicy.school_id == school_id
            )
        )
        return result.scalar_one_or_none()

    async def create_sibling_discount_policy(
        self,
        **kwargs: Any,
    ) -> SiblingDiscountPolicy:
        policy = SiblingDiscountPolicy(**kwargs)
        self.db.add(policy)
        await self.db.flush()
        return policy

    async def save_sibling_discount_policy(
        self,
        policy: SiblingDiscountPolicy,
    ) -> SiblingDiscountPolicy:
        self.db.add(policy)
        await self.db.flush()
        return policy

    async def get_late_fee_policy(
        self,
        *,
        school_id: uuid.UUID,
    ) -> LateFeePolicy | None:
        result = await self.db.execute(
            select(LateFeePolicy).where(LateFeePolicy.school_id == school_id)
        )
        return result.scalar_one_or_none()

    async def create_late_fee_policy(
        self,
        **kwargs: Any,
    ) -> LateFeePolicy:
        policy = LateFeePolicy(**kwargs)
        self.db.add(policy)
        await self.db.flush()
        return policy

    async def save_late_fee_policy(
        self,
        policy: LateFeePolicy,
    ) -> LateFeePolicy:
        self.db.add(policy)
        await self.db.flush()
        return policy

    async def get_siblings_by_parent(
        self,
        *,
        parent_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> list[tuple[uuid.UUID, str, date | None]]:
        result = await self.db.execute(
            select(
                ParentChildLink.child_user_id,
                User.full_name,
                StudentProfile.date_of_birth,
            )
            .join(User, User.id == ParentChildLink.child_user_id)
            .outerjoin(
                StudentProfile,
                StudentProfile.user_id == ParentChildLink.child_user_id,
            )
            .where(
                ParentChildLink.parent_user_id == parent_id,
                ParentChildLink.school_id == school_id,
                ParentChildLink.status == "active",
            )
        )
        return [
            (child_id, full_name, date_of_birth)
            for child_id, full_name, date_of_birth in result.all()
        ]

    async def list_overdue_invoices_for_late_fees(
        self,
        *,
        school_id: uuid.UUID,
        overdue_before: date,
        limit: int = 500,
    ) -> list[Invoice]:
        result = await self.db.execute(
            select(Invoice)
            .options(selectinload(Invoice.items))
            .where(
                Invoice.school_id == school_id,
                Invoice.status == "pending",
                Invoice.due_date < overdue_before,
            )
            .order_by(Invoice.due_date.asc(), Invoice.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().unique().all())

    async def get_payment_plan(
        self,
        plan_id: uuid.UUID,
        *,
        include_installments: bool = False,
    ) -> PaymentPlan | None:
        query = select(PaymentPlan).where(PaymentPlan.id == plan_id)
        if include_installments:
            query = query.options(
                selectinload(PaymentPlan.invoice),
                selectinload(PaymentPlan.installments),
            )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_active_payment_plan_for_invoice(
        self,
        invoice_id: uuid.UUID,
    ) -> PaymentPlan | None:
        result = await self.db.execute(
            select(PaymentPlan)
            .where(
                PaymentPlan.invoice_id == invoice_id,
                PaymentPlan.status == "active",
            )
            .options(selectinload(PaymentPlan.installments))
        )
        return result.scalar_one_or_none()

    async def list_payment_plans(
        self,
        *,
        school_id: uuid.UUID,
        parent_id: uuid.UUID | None = None,
    ) -> list[PaymentPlan]:
        query = (
            select(PaymentPlan)
            .join(Invoice, Invoice.id == PaymentPlan.invoice_id)
            .options(
                selectinload(PaymentPlan.invoice),
                selectinload(PaymentPlan.installments),
            )
            .where(PaymentPlan.school_id == school_id)
            .order_by(PaymentPlan.created_at.desc())
        )
        if parent_id is not None:
            query = query.where(Invoice.parent_id == parent_id)
        result = await self.db.execute(query)
        return list(result.scalars().unique().all())

    async def create_payment_plan(self, **kwargs: Any) -> PaymentPlan:
        plan = PaymentPlan(**kwargs)
        self.db.add(plan)
        await self.db.flush()
        return plan

    async def save_payment_plan(
        self,
        plan: PaymentPlan,
    ) -> PaymentPlan:
        self.db.add(plan)
        await self.db.flush()
        return plan

    async def create_installments(
        self,
        installments_data: list[dict[str, Any]],
    ) -> list[Installment]:
        installments = [Installment(**data) for data in installments_data]
        if installments:
            self.db.add_all(installments)
            await self.db.flush()
        return installments

    async def get_installment(
        self,
        installment_id: uuid.UUID,
    ) -> Installment | None:
        result = await self.db.execute(
            select(Installment)
            .where(Installment.id == installment_id)
            .options(
                selectinload(Installment.plan).selectinload(PaymentPlan.invoice),
                selectinload(Installment.plan).selectinload(PaymentPlan.installments),
            )
        )
        return result.scalar_one_or_none()

    async def save_installment(
        self,
        installment: Installment,
    ) -> Installment:
        self.db.add(installment)
        await self.db.flush()
        return installment
