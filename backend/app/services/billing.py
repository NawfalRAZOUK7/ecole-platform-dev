"""Billing service layer for fee structures, invoices, and payments."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import AuthContext, verify_school_boundary
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.filtering import FilterSpec, SortSpec
from app.core.response import clamp_page_size
from app.models.billing import FeeAssignment, FeeStructure, Invoice, PaymentAttempt, ProviderWebhookEvent
from app.models.iam import User
from app.repositories.billing import BillingRepository
from app.schemas.billing import (
    FeeAssignmentBulkCreateRequest,
    FeeAssignmentCreateRequest,
    FeeAssignmentResponse,
    FeeStructureCreateRequest,
    FeeStructureResponse,
    FeeStructureUpdateRequest,
    InvoiceGenerateRequest,
    InvoiceItemResponse,
    InvoiceResponse,
    PaymentAttemptResponse,
    PaymentInitiateRequest,
    WebhookEventRequest,
    WebhookEventResponse,
)
from app.services.audit import AuditService
from app.services.realtime import publish_payment_updated


class BillingService:
    """Business logic for billing and payments."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = BillingRepository(db)
        self.audit = AuditService(db)

    def _fee_structure_to_response(self, fee_structure: FeeStructure) -> dict:
        return FeeStructureResponse(
            id=str(fee_structure.id),
            school_id=str(fee_structure.school_id),
            academic_year_id=str(fee_structure.academic_year_id),
            name=fee_structure.name,
            amount=float(fee_structure.amount),
            currency=fee_structure.currency,
            frequency=fee_structure.frequency,
            due_day=fee_structure.due_day,
            applies_to_level=fee_structure.applies_to_level,
            status=fee_structure.status,
            created_at=fee_structure.created_at.isoformat(),
            updated_at=fee_structure.updated_at.isoformat()
            if fee_structure.updated_at
            else None,
        ).model_dump()

    def _fee_assignment_to_response(self, assignment: FeeAssignment) -> dict:
        return FeeAssignmentResponse(
            id=str(assignment.id),
            fee_structure_id=str(assignment.fee_structure_id),
            student_id=str(assignment.student_id),
            school_id=str(assignment.school_id),
            discount_percent=float(assignment.discount_percent)
            if assignment.discount_percent is not None
            else None,
            discount_reason=assignment.discount_reason,
            status=assignment.status,
            created_at=assignment.created_at.isoformat(),
        ).model_dump()

    def _invoice_to_response(self, invoice: Invoice) -> dict:
        return InvoiceResponse(
            id=str(invoice.id),
            school_id=str(invoice.school_id),
            parent_id=str(invoice.parent_id),
            period_id=str(invoice.period_id) if invoice.period_id else None,
            status=invoice.status,
            total_amount=float(invoice.total_amount),
            currency=invoice.currency,
            issued_date=str(invoice.issued_date),
            due_date=str(invoice.due_date),
            items=[
                InvoiceItemResponse(
                    id=str(item.id),
                    description=item.description,
                    amount=float(item.amount),
                    unit_price=float(item.unit_price),
                    quantity=item.quantity,
                )
                for item in invoice.items
            ],
        ).model_dump()

    def _payment_to_response(self, payment: PaymentAttempt) -> dict:
        return PaymentAttemptResponse(
            id=str(payment.id),
            invoice_id=str(payment.invoice_id),
            parent_id=str(payment.parent_id),
            school_id=str(payment.school_id),
            idempotency_key=payment.idempotency_key,
            status=payment.status,
            finalized_at=payment.finalized_at.isoformat()
            if payment.finalized_at
            else None,
        ).model_dump()

    def _webhook_to_response(self, event: ProviderWebhookEvent) -> dict:
        return WebhookEventResponse(
            id=str(event.id),
            provider_event_id=event.provider_event_id,
            payment_attempt_id=str(event.payment_attempt_id)
            if event.payment_attempt_id
            else None,
            school_id=str(event.school_id),
            status=event.status,
            signature_status=event.signature_status,
        ).model_dump()

    def _user_display_name(self, user: User) -> str:
        first_name = getattr(user, "first_name", None)
        return first_name or user.full_name or user.email

    async def create_fee_structure(
        self,
        *,
        body: FeeStructureCreateRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        academic_year = await self.repo.get_academic_year(body.academic_year_id)
        if academic_year is None:
            raise NotFoundError("Academic year not found", error_code="ERR-BIL-404")
        verify_school_boundary(academic_year.school_id, auth)

        fee_structure = await self.repo.create_fee_structure(
            school_id=auth.school_id,
            academic_year_id=body.academic_year_id,
            name=body.name,
            amount=body.amount,
            currency=body.currency,
            frequency=body.frequency,
            due_day=body.due_day,
            applies_to_level=body.applies_to_level,
            status="ACTIVE",
        )

        response = self._fee_structure_to_response(fee_structure)
        await self.audit.log_event(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            action_type="fee_structure.create",
            target_type="fee_structure",
            target_id=fee_structure.id,
            outcome="success",
            entity_after=response,
            ip_address=ip_address,
        )
        return response

    async def list_fee_structures(
        self,
        *,
        auth: AuthContext,
        academic_year_id: uuid.UUID | None = None,
        status: str | None = None,
        applies_to_level: str | None = None,
    ) -> list[dict]:
        structures = await self.repo.list_fee_structures(
            school_id=auth.school_id,
            academic_year_id=academic_year_id,
            status=status,
            applies_to_level=applies_to_level,
        )
        return [self._fee_structure_to_response(item) for item in structures]

    async def update_fee_structure(
        self,
        *,
        fee_structure_id: uuid.UUID,
        body: FeeStructureUpdateRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        fee_structure = await self.repo.get_fee_structure(fee_structure_id)
        if fee_structure is None:
            raise NotFoundError("Fee structure not found", error_code="ERR-BIL-404")
        verify_school_boundary(fee_structure.school_id, auth)

        entity_before = self._fee_structure_to_response(fee_structure)

        if body.name is not None:
            fee_structure.name = body.name
        if body.amount is not None:
            fee_structure.amount = body.amount
        if body.currency is not None:
            fee_structure.currency = body.currency
        if body.frequency is not None:
            fee_structure.frequency = body.frequency
        if body.due_day is not None:
            fee_structure.due_day = body.due_day
        if body.applies_to_level is not None:
            fee_structure.applies_to_level = body.applies_to_level
        if body.status is not None:
            fee_structure.status = body.status

        await self.repo.save_fee_structure(fee_structure)
        entity_after = self._fee_structure_to_response(fee_structure)

        await self.audit.log_event(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            action_type="fee_structure.update",
            target_type="fee_structure",
            target_id=fee_structure.id,
            outcome="success",
            entity_before=entity_before,
            entity_after=entity_after,
            ip_address=ip_address,
        )
        return entity_after

    async def create_fee_assignment(
        self,
        *,
        body: FeeAssignmentCreateRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        fee_structure = await self.repo.get_fee_structure(body.fee_structure_id)
        if fee_structure is None:
            raise NotFoundError("Fee structure not found", error_code="ERR-BIL-404")
        verify_school_boundary(fee_structure.school_id, auth)

        student = await self.repo.get_user_by_id(body.student_id)
        if student is None:
            raise NotFoundError("Student not found", error_code="ERR-BIL-404")

        duplicate = await self.repo.get_fee_assignment(
            fee_structure_id=body.fee_structure_id,
            student_id=body.student_id,
        )
        if duplicate is not None:
            raise ConflictError(
                "Fee already assigned to this student",
                error_code="ERR-BIL-409",
            )

        assignment = await self.repo.create_fee_assignment(
            fee_structure_id=body.fee_structure_id,
            student_id=body.student_id,
            school_id=auth.school_id,
            discount_percent=body.discount_percent,
            discount_reason=body.discount_reason,
            status="ACTIVE",
        )

        response = self._fee_assignment_to_response(assignment)
        await self.audit.log_event(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            action_type="fee_assignment.create",
            target_type="fee_assignment",
            target_id=assignment.id,
            outcome="success",
            entity_after=response,
            ip_address=ip_address,
        )
        return response

    async def bulk_create_fee_assignments(
        self,
        *,
        body: FeeAssignmentBulkCreateRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        if not body.class_id and not body.level:
            raise ValidationError(
                "Either class_id or level must be provided",
                error_code="ERR-BIL-422",
            )

        fee_structure = await self.repo.get_fee_structure(body.fee_structure_id)
        if fee_structure is None:
            raise NotFoundError("Fee structure not found", error_code="ERR-BIL-404")
        verify_school_boundary(fee_structure.school_id, auth)

        student_ids: list[uuid.UUID] = []
        if body.class_id:
            class_room = await self.repo.get_class(body.class_id)
            if class_room is None:
                raise NotFoundError("Class not found", error_code="ERR-BIL-404")
            verify_school_boundary(class_room.school_id, auth)
            student_ids = await self.repo.list_active_enrollment_student_ids_for_class(
                class_id=body.class_id,
                school_id=auth.school_id,
            )
        elif body.level:
            class_ids = await self.repo.list_class_ids_by_level(
                school_id=auth.school_id,
                level=body.level,
            )
            if class_ids:
                student_ids = (
                    await self.repo.list_active_enrollment_student_ids_for_classes(
                        class_ids=class_ids,
                        school_id=auth.school_id,
                    )
                )

        if not student_ids:
            return {
                "created": 0,
                "skipped": 0,
                "assignments": [],
            }

        existing_ids = await self.repo.list_existing_assignment_student_ids(
            fee_structure_id=body.fee_structure_id,
            student_ids=student_ids,
        )
        created = await self.repo.create_fee_assignments(
            [
                {
                    "fee_structure_id": body.fee_structure_id,
                    "student_id": student_id,
                    "school_id": auth.school_id,
                    "discount_percent": body.discount_percent,
                    "discount_reason": body.discount_reason,
                    "status": "ACTIVE",
                }
                for student_id in student_ids
                if student_id not in existing_ids
            ]
        )

        await self.audit.log_event(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            action_type="fee_assignment.bulk_create",
            target_type="fee_assignment",
            outcome="success",
            entity_after={
                "fee_structure_id": str(body.fee_structure_id),
                "created": len(created),
                "skipped": len(existing_ids),
            },
            ip_address=ip_address,
        )

        return {
            "created": len(created),
            "skipped": len(existing_ids),
            "assignments": [
                self._fee_assignment_to_response(assignment) for assignment in created
            ],
        }

    async def list_fee_assignments(
        self,
        *,
        auth: AuthContext,
        fee_structure_id: uuid.UUID | None = None,
        student_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> list[dict]:
        student_ids: set[uuid.UUID] | None = None
        if auth.role == "PAR":
            student_ids = await self.repo.list_parent_child_ids(
                parent_id=auth.user_id,
                school_id=auth.school_id,
            )
            if not student_ids:
                return []

        assignments = await self.repo.list_fee_assignments(
            school_id=auth.school_id,
            fee_structure_id=fee_structure_id,
            student_id=student_id,
            status=status,
            student_ids=student_ids,
        )
        return [self._fee_assignment_to_response(item) for item in assignments]

    async def generate_invoices(
        self,
        *,
        body: InvoiceGenerateRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        if body.due_date < body.issued_date:
            raise ValidationError(
                "due_date must be on or after issued_date",
                error_code="ERR-BIL-422",
            )

        fee_structure = await self.repo.get_fee_structure(body.fee_structure_id)
        if fee_structure is None:
            raise NotFoundError("Fee structure not found", error_code="ERR-BIL-404")
        verify_school_boundary(fee_structure.school_id, auth)

        if fee_structure.status != "ACTIVE":
            raise ValidationError(
                "Fee structure is not active",
                error_code="ERR-BIL-422",
            )

        assignments = await self.repo.list_active_fee_assignments(
            fee_structure_id=body.fee_structure_id,
            school_id=auth.school_id,
        )
        if not assignments:
            return {
                "generated": 0,
                "skipped": 0,
                "total_amount": 0,
            }

        parent_links = await self.repo.list_parent_links_for_students(
            student_ids=[assignment.student_id for assignment in assignments],
            school_id=auth.school_id,
        )
        student_to_parent: dict[uuid.UUID, uuid.UUID] = {}
        for link in parent_links:
            if link.child_user_id not in student_to_parent:
                student_to_parent[link.child_user_id] = link.parent_user_id

        generated = 0
        skipped = 0
        total_generated_amount = 0.0

        for assignment in assignments:
            parent_id = student_to_parent.get(assignment.student_id)
            if parent_id is None:
                skipped += 1
                continue

            base_amount = float(fee_structure.amount)
            if assignment.discount_percent:
                discount = base_amount * float(assignment.discount_percent) / 100
                final_amount = round(base_amount - discount, 2)
            else:
                final_amount = base_amount

            if final_amount <= 0:
                skipped += 1
                continue

            invoice = await self.repo.create_invoice(
                school_id=auth.school_id,
                parent_id=parent_id,
                period_id=body.period_id,
                status="pending",
                total_amount=final_amount,
                currency=fee_structure.currency,
                issued_date=body.issued_date,
                due_date=body.due_date,
                fee_structure_id=fee_structure.id,
            )

            description = fee_structure.name
            if assignment.discount_percent:
                description += f" (remise {float(assignment.discount_percent):.0f}%)"

            await self.repo.create_invoice_item(
                invoice_id=invoice.id,
                description=description,
                amount=final_amount,
                unit_price=base_amount,
                quantity=1,
            )

            generated += 1
            total_generated_amount += final_amount

        await self.audit.log_event(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            action_type="invoice.generate_from_fees",
            target_type="fee_structure",
            target_id=fee_structure.id,
            outcome="success",
            entity_after={
                "fee_structure_id": str(fee_structure.id),
                "generated": generated,
                "skipped": skipped,
                "total_amount": total_generated_amount,
            },
            ip_address=ip_address,
        )

        return {
            "generated": generated,
            "skipped": skipped,
            "total_amount": total_generated_amount,
            "currency": fee_structure.currency,
        }

    async def initiate_payment(
        self,
        *,
        body: PaymentInitiateRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        invoice = await self.repo.get_invoice_by_id(body.invoice_id)
        if invoice is None:
            raise NotFoundError("Invoice not found", error_code="ERR-BIL-404")
        verify_school_boundary(invoice.school_id, auth)

        if invoice.parent_id != auth.user_id:
            raise NotFoundError("Invoice not found", error_code="ERR-BIL-404")

        if invoice.status != "pending":
            raise ConflictError(
                "Invoice is not in pending status",
                error_code="ERR-BIL-409",
                details={"current_status": invoice.status},
            )

        existing = await self.repo.get_payment_by_idempotency_key(body.idempotency_key)
        if existing is not None:
            return self._payment_to_response(existing)

        payment = await self.repo.create_payment(
            invoice_id=body.invoice_id,
            parent_id=auth.user_id,
            school_id=auth.school_id,
            idempotency_key=body.idempotency_key,
            status="pending",
        )

        await self.audit.log_event(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            action_type="PAYMENT_INITIATED",
            outcome="success",
            target_type="payment_attempt",
            target_id=payment.id,
            entity_after={
                "invoice_id": str(body.invoice_id),
                "idempotency_key": body.idempotency_key,
            },
            ip_address=ip_address,
        )
        return self._payment_to_response(payment)

    async def get_payment_status(
        self,
        *,
        attempt_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict:
        payment = await self.repo.get_payment_by_id(attempt_id)
        if payment is None:
            raise NotFoundError("Payment attempt not found", error_code="ERR-BIL-404")

        verify_school_boundary(payment.school_id, auth)
        if auth.role == "PAR" and payment.parent_id != auth.user_id:
            raise NotFoundError("Payment attempt not found", error_code="ERR-BIL-404")

        return self._payment_to_response(payment)

    async def handle_provider_webhook(
        self,
        *,
        body: WebhookEventRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        now = datetime.now(timezone.utc)

        existing = await self.repo.get_webhook_event_by_provider_event_id(
            body.provider_event_id
        )
        if existing is not None:
            return self._webhook_to_response(existing)

        payment_attempt = None
        if body.payment_attempt_id:
            payment_attempt = await self.repo.get_payment_by_id(body.payment_attempt_id)

        webhook_event = await self.repo.create_webhook_event(
            payment_attempt_id=body.payment_attempt_id,
            school_id=auth.school_id,
            provider_event_id=body.provider_event_id,
            signature_status="valid" if body.signature else "unchecked",
            status="processed",
            provider_event_received_at=now,
        )

        if payment_attempt is not None:
            if body.status == "paid":
                payment_attempt.status = "paid"
                payment_attempt.finalized_at = now
                await self.repo.save_payment(payment_attempt)

                invoice = await self.repo.get_invoice_by_id(payment_attempt.invoice_id)
                if invoice is not None:
                    invoice.status = "paid"
                    await self.repo.save_invoice(invoice)
            elif body.status == "failed":
                payment_attempt.status = "failed"
                payment_attempt.finalized_at = now
                await self.repo.save_payment(payment_attempt)

                try:
                    from app.services.payment_retry import schedule_retry_for_failed_payment

                    await schedule_retry_for_failed_payment(payment_attempt.id, self.db)
                except Exception:
                    pass
            elif body.status == "canceled":
                payment_attempt.status = "canceled"
                payment_attempt.finalized_at = now
                await self.repo.save_payment(payment_attempt)

        if payment_attempt is not None and body.status in ("paid", "failed", "canceled"):
            await publish_payment_updated(
                parent_id=payment_attempt.parent_id,
                payment_attempt_id=payment_attempt.id,
                status=body.status,
                invoice_id=payment_attempt.invoice_id,
            )

        await self.audit.log_event(
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
            ip_address=ip_address,
        )
        return self._webhook_to_response(webhook_event)

    async def list_invoices(
        self,
        *,
        status: str | None,
        cursor: str | None,
        limit: int | None,
        filters: FilterSpec,
        sort: SortSpec,
        search: str | None,
        auth: AuthContext,
    ) -> dict:
        page_size = clamp_page_size(limit)
        invoices, next_cursor, has_more = await self.repo.list_invoices(
            school_id=auth.school_id,
            role=auth.role,
            user_id=auth.user_id,
            status=status,
            cursor=cursor,
            limit=page_size,
            filters=filters,
            sort=sort,
            search=search,
        )

        return {
            "items": [self._invoice_to_response(invoice) for invoice in invoices],
            "next_cursor": next_cursor,
            "has_more": has_more,
            "filters_applied": filters.as_dict() if filters.items else None,
            "sort_by": sort.as_list() if sort.fields else None,
            "search_term": search,
        }

    async def get_invoice(
        self,
        *,
        invoice_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict:
        invoice = await self.repo.get_invoice_by_id(invoice_id, include_items=True)
        if invoice is None:
            raise NotFoundError("Invoice not found", error_code="ERR-BIL-404")

        verify_school_boundary(invoice.school_id, auth)
        if auth.role == "PAR" and invoice.parent_id != auth.user_id:
            raise NotFoundError("Invoice not found", error_code="ERR-BIL-404")

        return self._invoice_to_response(invoice)
