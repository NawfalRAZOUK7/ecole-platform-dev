"""Payment plan service for installment creation and retrieval."""

from __future__ import annotations

import calendar
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_DOWN

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import AuthContext, verify_school_boundary
from app.core.exceptions import AuthorizationError, ConflictError, NotFoundError
from app.core.permissions import (
    PAR,
    PERM_BIL_PAYMENT_PLAN_CREATE,
    PERM_BIL_PAYMENT_PLAN_READ,
    role_has_permission,
)
from app.core.unit_of_work import UnitOfWork
from app.domain.value_objects.money import Money
from app.repositories.billing import BillingRepository
from app.repositories.billing_enhancements import BillingEnhancementsRepository
from app.schemas.billing.enhancements import (
    InstallmentResponse,
    PaymentPlanCreateRequest,
    PaymentPlanDetailResponse,
    PaymentPlanSummaryResponse,
)
from app.services.platform.audit import AuditService


class PaymentPlanService:
    """Business logic for invoice installment plans."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.billing_repo = BillingRepository(db)
        self.repo = BillingEnhancementsRepository(db)
        self.audit = AuditService(db)

    def _ensure_can_create(self, auth: AuthContext) -> None:
        if role_has_permission(auth.role, PERM_BIL_PAYMENT_PLAN_CREATE):
            return
        raise AuthorizationError(
            "Insufficient permissions",
            error_code="ERR-AUTHZ-001",
            details={"required": [PERM_BIL_PAYMENT_PLAN_CREATE], "role": auth.role},
        )

    def _ensure_can_read(self, auth: AuthContext) -> None:
        if role_has_permission(auth.role, PERM_BIL_PAYMENT_PLAN_READ):
            return
        raise AuthorizationError(
            "Insufficient permissions",
            error_code="ERR-AUTHZ-001",
            details={"required": [PERM_BIL_PAYMENT_PLAN_READ], "role": auth.role},
        )

    def _installment_to_response(self, installment) -> dict:
        return InstallmentResponse(
            id=str(installment.id),
            plan_id=str(installment.plan_id),
            installment_number=installment.installment_number,
            amount=float(installment.amount),
            due_date=installment.due_date.isoformat(),
            paid_at=installment.paid_at.isoformat() if installment.paid_at else None,
            status=installment.status,
        ).model_dump()

    def _plan_to_summary(self, plan) -> dict:
        paid_count = sum(1 for item in plan.installments if item.status == "paid")
        pending_count = len(plan.installments) - paid_count
        invoice = plan.invoice
        return PaymentPlanSummaryResponse(
            id=str(plan.id),
            invoice_id=str(plan.invoice_id),
            school_id=str(plan.school_id),
            parent_id=str(invoice.parent_id),
            total_installments=plan.total_installments,
            status=plan.status,
            currency=invoice.currency,
            invoice_total_amount=float(invoice.total_amount),
            issued_date=invoice.issued_date.isoformat(),
            due_date=invoice.due_date.isoformat(),
            created_at=plan.created_at.isoformat(),
            updated_at=plan.updated_at.isoformat() if plan.updated_at else None,
            installments_paid=paid_count,
            installments_pending=pending_count,
        ).model_dump()

    def _plan_to_detail(self, plan) -> dict:
        summary = self._plan_to_summary(plan)
        return PaymentPlanDetailResponse(
            **summary,
            installments=[
                self._installment_to_response(item)
                for item in sorted(
                    plan.installments,
                    key=lambda installment: installment.installment_number,
                )
            ],
        ).model_dump()

    def _split_amounts(self, total: Money, count: int) -> list[Money]:
        base_amount = (total.amount / count).quantize(
            Decimal("0.01"),
            rounding=ROUND_DOWN,
        )
        amounts = [Money(base_amount, total.currency) for _ in range(count)]
        remainder = total.amount - (base_amount * count)
        cents_remaining = int((remainder * 100).quantize(Decimal("1")))
        cent = Money(Decimal("0.01"), total.currency)
        for index in range(cents_remaining):
            amounts[index] = amounts[index] + cent
        return amounts

    def _add_months(self, source_date: date, months: int) -> date:
        month_index = source_date.month - 1 + months
        year = source_date.year + (month_index // 12)
        month = (month_index % 12) + 1
        last_day = calendar.monthrange(year, month)[1]
        day = min(source_date.day, last_day)
        return date(year, month, day)

    def _to_due_datetime(self, source_date: date) -> datetime:
        return datetime(
            source_date.year,
            source_date.month,
            source_date.day,
            tzinfo=timezone.utc,
        )

    async def create_plan(
        self,
        *,
        body: PaymentPlanCreateRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        self._ensure_can_create(auth)

        invoice = await self.billing_repo.get_invoice_by_id(
            body.invoice_id,
            include_items=True,
        )
        if invoice is None:
            raise NotFoundError("Invoice not found", error_code="ERR-BIL-404")
        verify_school_boundary(invoice.school_id, auth)

        if auth.role == PAR and invoice.parent_id != auth.user_id:
            raise NotFoundError("Invoice not found", error_code="ERR-BIL-404")
        if invoice.status == "paid":
            raise ConflictError(
                "Cannot create a payment plan for a paid invoice",
                error_code="ERR-BIL-409",
            )

        existing_plan = await self.repo.get_active_payment_plan_for_invoice(invoice.id)
        if existing_plan is not None:
            raise ConflictError(
                "An active payment plan already exists for this invoice",
                error_code="ERR-BIL-409",
            )

        total_amount = Money.from_float(float(invoice.total_amount), invoice.currency)
        installment_amounts = self._split_amounts(total_amount, body.num_installments)

        async with UnitOfWork(self.db) as uow:
            repo = BillingEnhancementsRepository(uow.session)
            audit = AuditService(uow.session)
            plan = await repo.create_payment_plan(
                invoice_id=invoice.id,
                school_id=invoice.school_id,
                total_installments=body.num_installments,
                status="active",
            )
            await repo.create_installments(
                [
                    {
                        "plan_id": plan.id,
                        "installment_number": index,
                        "amount": float(amount.amount),
                        "due_date": self._to_due_datetime(
                            self._add_months(invoice.due_date, index - 1)
                        ),
                        "status": "pending",
                    }
                    for index, amount in enumerate(installment_amounts, start=1)
                ]
            )
            saved_plan = await repo.get_payment_plan(plan.id, include_installments=True)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="billing.payment_plan.create",
                target_type="payment_plan",
                target_id=plan.id,
                outcome="success",
                entity_after={
                    "invoice_id": str(invoice.id),
                    "num_installments": body.num_installments,
                    "total_amount": float(total_amount.amount),
                },
                ip_address=ip_address,
            )
            await uow.commit()

        if saved_plan is None:
            raise NotFoundError("Payment plan not found", error_code="ERR-BIL-404")
        return self._plan_to_detail(saved_plan)

    async def list_plans(
        self,
        *,
        auth: AuthContext,
        parent_id: uuid.UUID | None = None,
    ) -> list[dict]:
        self._ensure_can_read(auth)

        scoped_parent_id = parent_id
        if auth.role == PAR:
            scoped_parent_id = auth.user_id

        plans = await self.repo.list_payment_plans(
            school_id=auth.school_id,
            parent_id=scoped_parent_id,
        )
        return [self._plan_to_summary(plan) for plan in plans]

    async def get_plan(
        self,
        *,
        plan_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict:
        self._ensure_can_read(auth)

        plan = await self.repo.get_payment_plan(plan_id, include_installments=True)
        if plan is None:
            raise NotFoundError("Payment plan not found", error_code="ERR-BIL-404")

        verify_school_boundary(plan.school_id, auth)
        if auth.role == PAR and plan.invoice.parent_id != auth.user_id:
            raise NotFoundError("Payment plan not found", error_code="ERR-BIL-404")

        return self._plan_to_detail(plan)

    async def mark_installment_paid(
        self,
        *,
        installment_id: uuid.UUID,
        paid_at: datetime | None = None,
        actor_id: uuid.UUID | None = None,
    ) -> dict:
        installment = await self.repo.get_installment(installment_id)
        if installment is None:
            raise NotFoundError("Installment not found", error_code="ERR-BIL-404")

        if installment.status == "paid" and installment.paid_at is not None:
            return self._installment_to_response(installment)

        paid_timestamp = paid_at or datetime.now(timezone.utc)

        async with UnitOfWork(self.db) as uow:
            repo = BillingEnhancementsRepository(uow.session)
            billing_repo = BillingRepository(uow.session)
            audit = AuditService(uow.session)
            installment = await repo.get_installment(installment_id)
            if installment is None:
                raise NotFoundError("Installment not found", error_code="ERR-BIL-404")

            installment.status = "paid"
            installment.paid_at = paid_timestamp
            await repo.save_installment(installment)

            plan = installment.plan
            if all(item.status == "paid" for item in plan.installments):
                plan.status = "completed"
                await repo.save_payment_plan(plan)
                invoice = plan.invoice
                invoice.status = "paid"
                await billing_repo.save_invoice(invoice)

            await audit.log_event(
                school_id=plan.school_id,
                actor_id=actor_id,
                action_type="billing.installment.mark_paid",
                target_type="installment",
                target_id=installment.id,
                outcome="success",
                entity_after={
                    "plan_id": str(plan.id),
                    "invoice_id": str(plan.invoice_id),
                    "paid_at": paid_timestamp.isoformat(),
                },
            )
            await uow.commit()

        return self._installment_to_response(installment)
