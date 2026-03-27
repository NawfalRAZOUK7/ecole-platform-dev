"""Repository helpers for billing, payments, invoices, and fee management."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from app.core.filtering import FilterSpec, SortSpec, apply_filters, apply_sort
from app.core.response import decode_cursor, encode_cursor
from app.core.search import apply_search
from app.models.billing import (
    FeeAssignment,
    FeeStructure,
    Invoice,
    InvoiceItem,
    PaymentAttempt,
    ProviderWebhookEvent,
)
from app.models.com import ConsentPreference
from app.models.erp import AcademicYear, Class, Enrollment
from app.models.iam import ParentChildLink, User
from app.repositories.base import BaseRepository


class BillingRepository(BaseRepository):
    """Data access for billing and payment workflows."""

    async def get_academic_year(
        self,
        academic_year_id: uuid.UUID,
    ) -> AcademicYear | None:
        result = await self.db.execute(
            select(AcademicYear).where(AcademicYear.id == academic_year_id)
        )
        return result.scalar_one_or_none()

    async def get_fee_structure(
        self,
        fee_structure_id: uuid.UUID,
    ) -> FeeStructure | None:
        result = await self.db.execute(
            select(FeeStructure).where(FeeStructure.id == fee_structure_id)
        )
        return result.scalar_one_or_none()

    async def list_fee_structures(
        self,
        *,
        school_id: uuid.UUID,
        academic_year_id: uuid.UUID | None = None,
        status: str | None = None,
        applies_to_level: str | None = None,
    ) -> list[FeeStructure]:
        query = select(FeeStructure).where(FeeStructure.school_id == school_id)

        if academic_year_id:
            query = query.where(FeeStructure.academic_year_id == academic_year_id)
        if status:
            query = query.where(FeeStructure.status == status)
        if applies_to_level:
            query = query.where(FeeStructure.applies_to_level == applies_to_level)

        result = await self.db.execute(query.order_by(FeeStructure.created_at.desc()))
        return list(result.scalars().all())

    async def create_fee_structure(self, **kwargs: Any) -> FeeStructure:
        fee_structure = FeeStructure(**kwargs)
        self.db.add(fee_structure)
        await self.db.flush()
        return fee_structure

    async def save_fee_structure(
        self,
        fee_structure: FeeStructure,
    ) -> FeeStructure:
        self.db.add(fee_structure)
        await self.db.flush()
        return fee_structure

    async def get_user_by_id(
        self,
        user_id: uuid.UUID,
    ) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_class(
        self,
        class_id: uuid.UUID,
    ) -> Class | None:
        result = await self.db.execute(select(Class).where(Class.id == class_id))
        return result.scalar_one_or_none()

    async def get_fee_assignment(
        self,
        *,
        fee_structure_id: uuid.UUID,
        student_id: uuid.UUID,
    ) -> FeeAssignment | None:
        result = await self.db.execute(
            select(FeeAssignment).where(
                FeeAssignment.fee_structure_id == fee_structure_id,
                FeeAssignment.student_id == student_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_fee_assignments(
        self,
        *,
        school_id: uuid.UUID,
        fee_structure_id: uuid.UUID | None = None,
        student_id: uuid.UUID | None = None,
        status: str | None = None,
        student_ids: set[uuid.UUID] | None = None,
    ) -> list[FeeAssignment]:
        query = select(FeeAssignment).where(FeeAssignment.school_id == school_id)

        if fee_structure_id:
            query = query.where(FeeAssignment.fee_structure_id == fee_structure_id)
        if student_id:
            query = query.where(FeeAssignment.student_id == student_id)
        if status:
            query = query.where(FeeAssignment.status == status)
        if student_ids is not None:
            if not student_ids:
                return []
            query = query.where(FeeAssignment.student_id.in_(student_ids))

        result = await self.db.execute(query.order_by(FeeAssignment.created_at.desc()))
        return list(result.scalars().all())

    async def list_existing_assignment_student_ids(
        self,
        *,
        fee_structure_id: uuid.UUID,
        student_ids: list[uuid.UUID],
    ) -> set[uuid.UUID]:
        if not student_ids:
            return set()

        result = await self.db.execute(
            select(FeeAssignment.student_id).where(
                FeeAssignment.fee_structure_id == fee_structure_id,
                FeeAssignment.student_id.in_(student_ids),
            )
        )
        return set(result.scalars().all())

    async def create_fee_assignment(self, **kwargs: Any) -> FeeAssignment:
        assignment = FeeAssignment(**kwargs)
        self.db.add(assignment)
        await self.db.flush()
        return assignment

    async def create_fee_assignments(
        self,
        assignments_data: list[dict[str, Any]],
    ) -> list[FeeAssignment]:
        assignments = [FeeAssignment(**data) for data in assignments_data]
        if assignments:
            self.db.add_all(assignments)
            await self.db.flush()
        return assignments

    async def list_parent_child_ids(
        self,
        *,
        parent_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> set[uuid.UUID]:
        result = await self.db.execute(
            select(ParentChildLink.child_user_id).where(
                ParentChildLink.parent_user_id == parent_id,
                ParentChildLink.school_id == school_id,
                ParentChildLink.status == "active",
            )
        )
        return set(result.scalars().all())

    async def list_active_enrollment_student_ids_for_class(
        self,
        *,
        class_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> list[uuid.UUID]:
        result = await self.db.execute(
            select(Enrollment.student_id).where(
                Enrollment.class_id == class_id,
                Enrollment.school_id == school_id,
                Enrollment.status == "active",
            )
        )
        return list(result.scalars().all())

    async def list_class_ids_by_level(
        self,
        *,
        school_id: uuid.UUID,
        level: str,
    ) -> list[uuid.UUID]:
        result = await self.db.execute(
            select(Class.id).where(
                Class.school_id == school_id,
                Class.code.ilike(f"{level}%"),
            )
        )
        return list(result.scalars().all())

    async def list_active_enrollment_student_ids_for_classes(
        self,
        *,
        class_ids: list[uuid.UUID],
        school_id: uuid.UUID,
    ) -> list[uuid.UUID]:
        if not class_ids:
            return []

        result = await self.db.execute(
            select(Enrollment.student_id).where(
                Enrollment.class_id.in_(class_ids),
                Enrollment.school_id == school_id,
                Enrollment.status == "active",
            )
        )
        return list(result.scalars().all())

    async def list_active_fee_assignments(
        self,
        *,
        fee_structure_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> list[FeeAssignment]:
        result = await self.db.execute(
            select(FeeAssignment).where(
                FeeAssignment.fee_structure_id == fee_structure_id,
                FeeAssignment.school_id == school_id,
                FeeAssignment.status == "ACTIVE",
            )
        )
        return list(result.scalars().all())

    async def list_parent_links_for_students(
        self,
        *,
        student_ids: list[uuid.UUID],
        school_id: uuid.UUID,
    ) -> list[ParentChildLink]:
        if not student_ids:
            return []

        result = await self.db.execute(
            select(ParentChildLink).where(
                ParentChildLink.child_user_id.in_(student_ids),
                ParentChildLink.school_id == school_id,
                ParentChildLink.status == "active",
            )
        )
        return list(result.scalars().all())

    async def create_invoice(self, **kwargs: Any) -> Invoice:
        invoice = Invoice(**kwargs)
        self.db.add(invoice)
        await self.db.flush()
        return invoice

    async def save_invoice(
        self,
        invoice: Invoice,
    ) -> Invoice:
        self.db.add(invoice)
        await self.db.flush()
        return invoice

    async def create_invoice_item(self, **kwargs: Any) -> InvoiceItem:
        item = InvoiceItem(**kwargs)
        self.db.add(item)
        await self.db.flush()
        return item

    async def get_invoice_by_id(
        self,
        invoice_id: uuid.UUID,
        *,
        include_items: bool = False,
    ) -> Invoice | None:
        query = select(Invoice).where(Invoice.id == invoice_id)
        if include_items:
            query = query.options(selectinload(Invoice.items))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_invoices(
        self,
        *,
        school_id: uuid.UUID,
        role: str,
        user_id: uuid.UUID,
        status: str | None,
        cursor: str | None,
        limit: int,
        filters: FilterSpec,
        sort: SortSpec,
        search: str | None,
    ) -> tuple[list[Invoice], str | None, bool]:
        query = (
            select(Invoice)
            .options(selectinload(Invoice.items))
            .where(Invoice.school_id == school_id)
        )

        if role == "PAR":
            query = query.where(Invoice.parent_id == user_id)

        if status:
            query = query.where(Invoice.status == status)

        query = apply_filters(query, Invoice, filters)
        if search:
            query = apply_search(query, Invoice, search)
        query = apply_sort(query, Invoice, sort, default_column=Invoice.id)

        if cursor:
            last_id, _ = decode_cursor(cursor)
            query = query.where(Invoice.id > last_id)

        result = await self.db.execute(query.limit(limit + 1))
        invoices = list(result.scalars().unique().all())
        has_more = len(invoices) > limit
        if has_more:
            invoices = invoices[:limit]

        next_cursor = encode_cursor(invoices[-1].id) if has_more and invoices else None
        return invoices, next_cursor, has_more

    async def get_payment_by_id(
        self,
        payment_id: uuid.UUID,
    ) -> PaymentAttempt | None:
        result = await self.db.execute(
            select(PaymentAttempt).where(PaymentAttempt.id == payment_id)
        )
        return result.scalar_one_or_none()

    async def get_payment_by_idempotency_key(
        self,
        idempotency_key: str,
    ) -> PaymentAttempt | None:
        result = await self.db.execute(
            select(PaymentAttempt).where(
                PaymentAttempt.idempotency_key == idempotency_key,
            )
        )
        return result.scalar_one_or_none()

    async def list_payments(
        self,
        *,
        invoice_id: uuid.UUID,
    ) -> list[PaymentAttempt]:
        result = await self.db.execute(
            select(PaymentAttempt)
            .where(PaymentAttempt.invoice_id == invoice_id)
            .order_by(PaymentAttempt.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_payment(self, **kwargs: Any) -> PaymentAttempt:
        attempt = PaymentAttempt(**kwargs)
        self.db.add(attempt)
        await self.db.flush()
        return attempt

    async def save_payment(
        self,
        payment: PaymentAttempt,
    ) -> PaymentAttempt:
        self.db.add(payment)
        await self.db.flush()
        return payment

    async def get_webhook_event_by_provider_event_id(
        self,
        provider_event_id: str,
    ) -> ProviderWebhookEvent | None:
        result = await self.db.execute(
            select(ProviderWebhookEvent).where(
                ProviderWebhookEvent.provider_event_id == provider_event_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_webhook_event(self, **kwargs: Any) -> ProviderWebhookEvent:
        event = ProviderWebhookEvent(**kwargs)
        self.db.add(event)
        await self.db.flush()
        return event

    async def get_failed_attempts(
        self,
        *,
        now: datetime,
        max_retries: int,
        limit: int = 100,
    ) -> list[PaymentAttempt]:
        result = await self.db.execute(
            select(PaymentAttempt)
            .where(
                PaymentAttempt.status == "failed",
                PaymentAttempt.retry_count < max_retries,
                PaymentAttempt.next_retry_at.isnot(None),
                PaymentAttempt.next_retry_at <= now,
            )
            .order_by(PaymentAttempt.next_retry_at.asc(), PaymentAttempt.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_overdue_invoices(
        self,
        *,
        overdue_cutoff: date,
        reminder_cooldown: datetime,
        max_reminders: int,
        limit: int = 100,
    ) -> list[Invoice]:
        result = await self.db.execute(
            select(Invoice)
            .where(
                Invoice.status == "pending",
                Invoice.due_date < overdue_cutoff,
                Invoice.reminder_count < max_reminders,
                or_(
                    Invoice.reminder_sent_at.is_(None),
                    Invoice.reminder_sent_at < reminder_cooldown,
                ),
            )
            .order_by(Invoice.due_date.asc(), Invoice.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_billing_email_consent(
        self,
        *,
        user_id: uuid.UUID,
    ) -> ConsentPreference | None:
        result = await self.db.execute(
            select(ConsentPreference).where(
                ConsentPreference.user_id == user_id,
                ConsentPreference.topic == "billing",
                ConsentPreference.channel == "email",
            )
        )
        return result.scalar_one_or_none()
