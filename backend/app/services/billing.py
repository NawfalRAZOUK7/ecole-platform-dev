"""Billing service layer for fee structures, invoices, and payments."""

from __future__ import annotations

import logging
import math
import uuid
from datetime import date, datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.abac import validate_parent_child_access
from app.core.business_metrics import billing_collection, billing_revenue
from app.core.dependencies import AuthContext, verify_school_boundary
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.filtering import FilterSpec, SortSpec
from app.core.permissions import PAR
from app.core.response import clamp_page_size
from app.core.unit_of_work import UnitOfWork
from app.domain.events.billing import InvoiceGenerated, PaymentFailed, PaymentReceived
from app.domain.value_objects.money import Money
from app.models.billing import (
    FeeAssignment,
    FeeStructure,
    Invoice,
    LateFeePolicy,
    PaymentAttempt,
    ProviderWebhookEvent,
    SiblingDiscountPolicy,
)
from app.models.iam import User
from app.repositories.billing import BillingRepository
from app.repositories.billing_enhancements import BillingEnhancementsRepository
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
from app.schemas.billing_enhancements import (
    LateFeePolicyResponse,
    LateFeePolicyUpdateRequest,
    SiblingDiscountPolicyResponse,
    SiblingDiscountPolicyUpdateRequest,
)
from app.services.audit import AuditService
from app.services.event_dispatcher import EventDispatcher
from app.services.realtime import publish_payment_updated

logger = logging.getLogger(__name__)
LATE_FEE_ITEM_PREFIX = "Late fee"


class BillingService:
    """Business logic for billing and payments."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = BillingRepository(db)
        self.enhancements_repo = BillingEnhancementsRepository(db)
        self.audit = AuditService(db)
        self._dispatcher = EventDispatcher(self.db)

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

    def _sibling_policy_to_response(
        self,
        policy: SiblingDiscountPolicy | None,
        *,
        school_id: uuid.UUID,
    ) -> dict:
        return SiblingDiscountPolicyResponse(
            id=str(policy.id) if policy is not None else None,
            school_id=str(school_id),
            enabled=bool(policy.enabled) if policy is not None else True,
            second_child_percent=float(policy.second_child_percent)
            if policy is not None
            else 10.0,
            third_child_percent=float(policy.third_child_percent)
            if policy is not None
            else 20.0,
            fourth_plus_percent=float(policy.fourth_plus_percent)
            if policy is not None
            else 30.0,
            apply_to_oldest_first=bool(policy.apply_to_oldest_first)
            if policy is not None
            else True,
            created_at=policy.created_at.isoformat() if policy is not None else None,
            updated_at=policy.updated_at.isoformat()
            if policy is not None and policy.updated_at
            else None,
        ).model_dump()

    def _late_fee_policy_to_response(
        self,
        policy: LateFeePolicy | None,
        *,
        school_id: uuid.UUID,
    ) -> dict:
        return LateFeePolicyResponse(
            id=str(policy.id) if policy is not None else None,
            school_id=str(school_id),
            enabled=bool(policy.enabled) if policy is not None else False,
            fee_type=policy.fee_type if policy is not None else "fixed",
            amount=float(policy.amount) if policy is not None else 0.0,
            frequency=policy.frequency if policy is not None else "once",
            grace_days=policy.grace_days if policy is not None else 5,
            max_fee=float(policy.max_fee) if policy is not None and policy.max_fee is not None else None,
            created_at=policy.created_at.isoformat() if policy is not None else None,
            updated_at=policy.updated_at.isoformat()
            if policy is not None and policy.updated_at
            else None,
        ).model_dump()

    def _get_sibling_discount_percent(
        self,
        *,
        policy: SiblingDiscountPolicy | None,
        sibling_rank: int,
    ) -> float:
        if policy is None or not policy.enabled or sibling_rank <= 1:
            return 0.0
        if sibling_rank == 2:
            return float(policy.second_child_percent)
        if sibling_rank == 3:
            return float(policy.third_child_percent)
        return float(policy.fourth_plus_percent)

    def _order_assigned_siblings(
        self,
        sibling_rows: list[tuple[uuid.UUID, str, date | None]],
        *,
        assigned_student_ids: set[uuid.UUID],
        oldest_first: bool,
    ) -> list[uuid.UUID]:
        relevant = [
            {
                "student_id": student_id,
                "full_name": full_name,
                "date_of_birth": date_of_birth,
            }
            for student_id, full_name, date_of_birth in sibling_rows
            if student_id in assigned_student_ids
        ]

        known_birth_dates = [
            item for item in relevant if item["date_of_birth"] is not None
        ]
        known_birth_dates.sort(
            key=lambda item: (
                item["date_of_birth"],
                item["full_name"].lower(),
                str(item["student_id"]),
            ),
            reverse=not oldest_first,
        )

        missing_birth_dates = [
            item for item in relevant if item["date_of_birth"] is None
        ]
        missing_birth_dates.sort(
            key=lambda item: (item["full_name"].lower(), str(item["student_id"]))
        )

        ordered_ids = [
            item["student_id"] for item in [*known_birth_dates, *missing_birth_dates]
        ]
        for student_id in sorted(assigned_student_ids, key=str):
            if student_id not in ordered_ids:
                ordered_ids.append(student_id)
        return ordered_ids

    def _existing_late_fee_total(self, invoice: Invoice) -> Money:
        total = Money.zero(invoice.currency)
        for item in invoice.items:
            if item.description.startswith(LATE_FEE_ITEM_PREFIX):
                total = total + Money.from_float(float(item.amount), invoice.currency)
        return total

    def _invoice_principal_total(self, invoice: Invoice) -> Money:
        total = Money.zero(invoice.currency)
        for item in invoice.items:
            if item.description.startswith(LATE_FEE_ITEM_PREFIX):
                continue
            total = total + Money.from_float(float(item.amount), invoice.currency)
        return total

    def _late_fee_units(
        self,
        *,
        policy: LateFeePolicy,
        overdue_days: int,
    ) -> int:
        if overdue_days <= 0:
            return 0
        if policy.frequency == "once":
            return 1
        if policy.frequency == "daily":
            return overdue_days
        return math.ceil(overdue_days / 7)

    def _calculate_late_fee_target(
        self,
        *,
        invoice: Invoice,
        policy: LateFeePolicy,
        as_of_date: date,
    ) -> tuple[Money, int, int]:
        overdue_days = (as_of_date - invoice.due_date).days - policy.grace_days
        fee_units = self._late_fee_units(policy=policy, overdue_days=overdue_days)
        if fee_units <= 0:
            return Money.zero(invoice.currency), 0, 0

        invoice_principal = self._invoice_principal_total(invoice)
        if policy.fee_type == "fixed":
            target_fee = Money.from_float(float(policy.amount), invoice.currency) * fee_units
        else:
            target_fee = invoice_principal * ((float(policy.amount) * fee_units) / 100)

        if policy.max_fee is not None:
            capped_fee = Money.from_float(float(policy.max_fee), invoice.currency)
            if target_fee.amount > capped_fee.amount:
                target_fee = capped_fee

        return target_fee, overdue_days, fee_units

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
        if auth.role == PAR:
            student_ids = await self.repo.list_parent_child_ids(
                parent_id=auth.user_id,
                school_id=auth.school_id,
            )
            if not student_ids:
                return []
            if student_id is not None:
                has_access = await validate_parent_child_access(
                    self.db,
                    parent_id=auth.user_id,
                    student_id=student_id,
                )
                if not has_access:
                    raise NotFoundError("Student not found", error_code="ERR-BIL-404")
                student_ids = {student_id}

        assignments = await self.repo.list_fee_assignments(
            school_id=auth.school_id,
            fee_structure_id=fee_structure_id,
            student_id=student_id,
            status=status,
            student_ids=student_ids,
        )
        return [self._fee_assignment_to_response(item) for item in assignments]

    async def get_sibling_policy(
        self,
        *,
        auth: AuthContext,
    ) -> dict:
        policy = await self.enhancements_repo.get_sibling_discount_policy(
            school_id=auth.school_id
        )
        return self._sibling_policy_to_response(policy, school_id=auth.school_id)

    async def update_sibling_policy(
        self,
        *,
        body: SiblingDiscountPolicyUpdateRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        async with UnitOfWork(self.db) as uow:
            repo = BillingEnhancementsRepository(uow.session)
            audit = AuditService(uow.session)
            policy = await repo.get_sibling_discount_policy(school_id=auth.school_id)
            entity_before = self._sibling_policy_to_response(
                policy,
                school_id=auth.school_id,
            )

            if policy is None:
                policy = await repo.create_sibling_discount_policy(
                    school_id=auth.school_id,
                    enabled=body.enabled,
                    second_child_percent=body.second_child_percent,
                    third_child_percent=body.third_child_percent,
                    fourth_plus_percent=body.fourth_plus_percent,
                    apply_to_oldest_first=body.apply_to_oldest_first,
                )
            else:
                policy.enabled = body.enabled
                policy.second_child_percent = body.second_child_percent
                policy.third_child_percent = body.third_child_percent
                policy.fourth_plus_percent = body.fourth_plus_percent
                policy.apply_to_oldest_first = body.apply_to_oldest_first
                await repo.save_sibling_discount_policy(policy)

            entity_after = self._sibling_policy_to_response(
                policy,
                school_id=auth.school_id,
            )
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="billing.sibling_policy.update",
                target_type="sibling_discount_policy",
                target_id=policy.id,
                outcome="success",
                entity_before=entity_before,
                entity_after=entity_after,
                ip_address=ip_address,
            )
            await uow.commit()

        return entity_after

    async def get_late_fee_policy(
        self,
        *,
        auth: AuthContext,
    ) -> dict:
        policy = await self.enhancements_repo.get_late_fee_policy(
            school_id=auth.school_id
        )
        return self._late_fee_policy_to_response(policy, school_id=auth.school_id)

    async def update_late_fee_policy(
        self,
        *,
        body: LateFeePolicyUpdateRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        if body.fee_type == "percent" and body.amount > 100:
            raise ValidationError(
                "Percent late fee cannot exceed 100",
                error_code="ERR-BIL-422",
            )

        async with UnitOfWork(self.db) as uow:
            repo = BillingEnhancementsRepository(uow.session)
            audit = AuditService(uow.session)
            policy = await repo.get_late_fee_policy(school_id=auth.school_id)
            entity_before = self._late_fee_policy_to_response(
                policy,
                school_id=auth.school_id,
            )

            if policy is None:
                policy = await repo.create_late_fee_policy(
                    school_id=auth.school_id,
                    enabled=body.enabled,
                    fee_type=body.fee_type,
                    amount=body.amount,
                    frequency=body.frequency,
                    grace_days=body.grace_days,
                    max_fee=body.max_fee,
                )
            else:
                policy.enabled = body.enabled
                policy.fee_type = body.fee_type
                policy.amount = body.amount
                policy.frequency = body.frequency
                policy.grace_days = body.grace_days
                policy.max_fee = body.max_fee
                await repo.save_late_fee_policy(policy)

            entity_after = self._late_fee_policy_to_response(
                policy,
                school_id=auth.school_id,
            )
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="billing.late_fee_policy.update",
                target_type="late_fee_policy",
                target_id=policy.id,
                outcome="success",
                entity_before=entity_before,
                entity_after=entity_after,
                ip_address=ip_address,
            )
            await uow.commit()

        return entity_after

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
        sibling_policy = await self.enhancements_repo.get_sibling_discount_policy(
            school_id=auth.school_id
        )
        student_to_parent: dict[uuid.UUID, uuid.UUID] = {}
        for link in parent_links:
            if link.child_user_id not in student_to_parent:
                student_to_parent[link.child_user_id] = link.parent_user_id

        sibling_discount_map: dict[uuid.UUID, float] = {}
        if sibling_policy is not None and sibling_policy.enabled:
            parent_to_assigned_students: dict[uuid.UUID, set[uuid.UUID]] = {}
            for assignment in assignments:
                parent_id = student_to_parent.get(assignment.student_id)
                if parent_id is None:
                    continue
                parent_to_assigned_students.setdefault(parent_id, set()).add(
                    assignment.student_id
                )

            for parent_id, assigned_student_ids in parent_to_assigned_students.items():
                sibling_rows = await self.enhancements_repo.get_siblings_by_parent(
                    parent_id=parent_id,
                    school_id=auth.school_id,
                )
                ordered_students = self._order_assigned_siblings(
                    sibling_rows,
                    assigned_student_ids=assigned_student_ids,
                    oldest_first=bool(sibling_policy.apply_to_oldest_first),
                )
                for sibling_rank, student_id in enumerate(ordered_students, start=1):
                    sibling_discount_map[student_id] = (
                        self._get_sibling_discount_percent(
                            policy=sibling_policy,
                            sibling_rank=sibling_rank,
                        )
                    )

        generated = 0
        skipped = 0
        total_generated_amount = 0.0
        generated_events: list[InvoiceGenerated] = []

        async with UnitOfWork(self.db) as uow:
            repo = BillingRepository(uow.session)
            audit = AuditService(uow.session)

            for assignment in assignments:
                parent_id = student_to_parent.get(assignment.student_id)
                if parent_id is None:
                    skipped += 1
                    continue

                base_amount = Money.from_float(
                    float(fee_structure.amount),
                    fee_structure.currency,
                )
                manual_discount_percent = float(assignment.discount_percent or 0)
                sibling_discount_percent = sibling_discount_map.get(
                    assignment.student_id,
                    0.0,
                )
                total_discount_percent = min(
                    100.0,
                    manual_discount_percent + sibling_discount_percent,
                )
                discount_amount = base_amount * (total_discount_percent / 100)
                final_amount = base_amount - discount_amount

                if final_amount.amount <= 0:
                    skipped += 1
                    continue

                invoice = await repo.create_invoice(
                    school_id=auth.school_id,
                    parent_id=parent_id,
                    period_id=body.period_id,
                    status="pending",
                    total_amount=float(final_amount.amount),
                    currency=fee_structure.currency,
                    issued_date=body.issued_date,
                    due_date=body.due_date,
                    fee_structure_id=fee_structure.id,
                )

                description = fee_structure.name
                applied_discounts: list[str] = []
                if manual_discount_percent:
                    applied_discounts.append(
                        f"manual {manual_discount_percent:.0f}%"
                    )
                if sibling_discount_percent:
                    applied_discounts.append(
                        f"sibling {sibling_discount_percent:.0f}%"
                    )
                if applied_discounts:
                    description += f" ({', '.join(applied_discounts)})"

                await repo.create_invoice_item(
                    invoice_id=invoice.id,
                    description=description,
                    amount=float(final_amount.amount),
                    unit_price=float(base_amount.amount),
                    quantity=1,
                )
                generated_events.append(
                    InvoiceGenerated(
                        school_id=auth.school_id,
                        actor_id=auth.user_id,
                        invoice_id=invoice.id,
                        student_id=assignment.student_id,
                        amount=float(final_amount.amount),
                        due_date=body.due_date.isoformat(),
                    )
                )

                generated += 1
                total_generated_amount += float(final_amount.amount)

            await audit.log_event(
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
            await uow.commit()

        for event in generated_events:
            try:
                await self._dispatcher.dispatch(event)
            except Exception:
                logger.exception(
                    "Failed to dispatch InvoiceGenerated for %s",
                    event.invoice_id,
                )

        return {
            "generated": generated,
            "skipped": skipped,
            "total_amount": total_generated_amount,
            "currency": fee_structure.currency,
        }

    async def apply_late_fees(
        self,
        *,
        school_id: uuid.UUID,
        actor_id: uuid.UUID | None = None,
        as_of_date: date | None = None,
        limit: int = 500,
    ) -> dict:
        effective_date = as_of_date or datetime.now(timezone.utc).date()
        policy = await self.enhancements_repo.get_late_fee_policy(school_id=school_id)
        if policy is None or not policy.enabled or float(policy.amount) <= 0:
            return {
                "checked": 0,
                "updated": 0,
                "total_fee_applied": 0.0,
            }

        async with UnitOfWork(self.db) as uow:
            repo = BillingRepository(uow.session)
            enhancements_repo = BillingEnhancementsRepository(uow.session)
            audit = AuditService(uow.session)
            policy = await enhancements_repo.get_late_fee_policy(school_id=school_id)
            if policy is None or not policy.enabled or float(policy.amount) <= 0:
                return {
                    "checked": 0,
                    "updated": 0,
                    "total_fee_applied": 0.0,
                }

            overdue_invoices = await enhancements_repo.list_overdue_invoices_for_late_fees(
                school_id=school_id,
                overdue_before=effective_date,
                limit=limit,
            )
            updated = 0
            total_fee_applied = 0.0

            for invoice in overdue_invoices:
                target_fee, overdue_days, fee_units = self._calculate_late_fee_target(
                    invoice=invoice,
                    policy=policy,
                    as_of_date=effective_date,
                )
                if target_fee.amount <= 0:
                    continue

                existing_fee = self._existing_late_fee_total(invoice)
                if target_fee.amount <= existing_fee.amount:
                    continue

                delta_fee = target_fee - existing_fee
                description = (
                    f"{LATE_FEE_ITEM_PREFIX} ({policy.frequency}, "
                    f"{overdue_days} days overdue, {fee_units} charge units)"
                )
                await repo.create_invoice_item(
                    invoice_id=invoice.id,
                    description=description,
                    amount=float(delta_fee.amount),
                    unit_price=float(delta_fee.amount),
                    quantity=1,
                )

                current_total = Money.from_float(
                    float(invoice.total_amount),
                    invoice.currency,
                )
                invoice.total_amount = float((current_total + delta_fee).amount)
                await repo.save_invoice(invoice)
                updated += 1
                total_fee_applied += float(delta_fee.amount)

            if updated:
                await audit.log_event(
                    school_id=school_id,
                    actor_id=actor_id,
                    action_type="billing.late_fees.apply",
                    target_type="invoice_batch",
                    outcome="success",
                    entity_after={
                        "checked": len(overdue_invoices),
                        "updated": updated,
                        "total_fee_applied": round(total_fee_applied, 2),
                        "as_of_date": effective_date.isoformat(),
                    },
                )
            await uow.commit()

        return {
            "checked": len(overdue_invoices),
            "updated": updated,
            "total_fee_applied": round(total_fee_applied, 2),
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

        async with UnitOfWork(self.db) as uow:
            repo = BillingRepository(uow.session)
            audit = AuditService(uow.session)
            payment = await repo.create_payment(
                invoice_id=body.invoice_id,
                parent_id=auth.user_id,
                school_id=auth.school_id,
                idempotency_key=body.idempotency_key,
                status="pending",
            )
            await audit.log_event(
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
            await uow.commit()
        billing_collection.labels(
            school_id=str(auth.school_id),
            status="pending",
        ).inc()
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
        if auth.role == PAR and payment.parent_id != auth.user_id:
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
        payment_event: PaymentReceived | PaymentFailed | None = None
        revenue_amount = 0.0
        revenue_plan = "invoice"
        collection_status: str | None = None

        existing = await self.repo.get_webhook_event_by_provider_event_id(
            body.provider_event_id
        )
        if existing is not None:
            return self._webhook_to_response(existing)

        payment_attempt = None
        if body.payment_attempt_id:
            payment_attempt = await self.repo.get_payment_by_id(body.payment_attempt_id)

        async with UnitOfWork(self.db) as uow:
            repo = BillingRepository(uow.session)
            audit = AuditService(uow.session)
            webhook_event = await repo.create_webhook_event(
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
                    await repo.save_payment(payment_attempt)

                    invoice = await repo.get_invoice_by_id(payment_attempt.invoice_id)
                    if invoice is not None:
                        invoice.status = "paid"
                        await repo.save_invoice(invoice)
                        if invoice.currency == "MAD":
                            revenue_amount = float(invoice.total_amount)
                        if invoice.fee_structure_id is not None:
                            fee_structure = await repo.get_fee_structure(invoice.fee_structure_id)
                            if fee_structure is not None:
                                revenue_plan = fee_structure.frequency.lower()
                        payment_event = PaymentReceived(
                            school_id=auth.school_id,
                            actor_id=auth.user_id,
                            payment_id=payment_attempt.id,
                            invoice_id=payment_attempt.invoice_id,
                            amount=float(invoice.total_amount),
                            method=body.event_type,
                        )
                    collection_status = "success"
                elif body.status == "failed":
                    payment_attempt.status = "failed"
                    payment_attempt.finalized_at = now
                    await repo.save_payment(payment_attempt)
                    payment_event = PaymentFailed(
                        school_id=auth.school_id,
                        actor_id=auth.user_id,
                        payment_id=payment_attempt.id,
                        invoice_id=payment_attempt.invoice_id,
                        reason=body.event_type,
                    )

                    try:
                        from app.services.payment_retry import schedule_retry_for_failed_payment

                        await schedule_retry_for_failed_payment(
                            payment_attempt.id,
                            uow.session,
                        )
                    except Exception:
                        pass
                    collection_status = "failed"
                elif body.status == "canceled":
                    payment_attempt.status = "canceled"
                    payment_attempt.finalized_at = now
                    await repo.save_payment(payment_attempt)
                    collection_status = "failed"

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
                ip_address=ip_address,
            )
            await uow.commit()

        if payment_attempt is not None and body.status in ("paid", "failed", "canceled"):
            await publish_payment_updated(
                parent_id=payment_attempt.parent_id,
                payment_attempt_id=payment_attempt.id,
                status=body.status,
                invoice_id=payment_attempt.invoice_id,
            )
        if collection_status is not None:
            billing_collection.labels(
                school_id=str(auth.school_id),
                status=collection_status,
            ).inc()
        if revenue_amount > 0:
            billing_revenue.labels(
                school_id=str(auth.school_id),
                plan=revenue_plan,
            ).inc(revenue_amount)
        if payment_event is not None:
            try:
                await self._dispatcher.dispatch(payment_event)
            except Exception:
                logger.exception(
                    "Failed to dispatch payment event for %s",
                    payment_attempt.id if payment_attempt is not None else body.payment_attempt_id,
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
        if auth.role == PAR and invoice.parent_id != auth.user_id:
            raise NotFoundError("Invoice not found", error_code="ERR-BIL-404")

        return self._invoice_to_response(invoice)
