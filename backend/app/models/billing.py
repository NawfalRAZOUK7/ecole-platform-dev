"""Billing domain models — Invoices, payments, proofs, webhooks, fee structures.

Reference: Pack C4 (Data Model — Billing section), Sprint 1 story S-018.
Migration group: G5-Billing (depends on G1-IAM, G2-ERP for user/period FKs).
Phase 11B: Added FeeStructure, FeeAssignment models; retry + reminder fields.
"""

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, SchoolScopedMixin, TimestampMixin


def _short_id(value: object | None) -> str:
    return str(value)[:8] if value is not None else "None"


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class InvoiceStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELED = "canceled"


class PaymentAttemptStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PAID = "paid"
    FAILED = "failed"
    CANCELED = "canceled"


class WebhookEventStatus(str, enum.Enum):
    RECEIVED = "received"
    PROCESSED = "processed"
    ERROR = "error"


class FeeFrequency(str, enum.Enum):
    """Fee payment frequency (Phase 11B)."""

    MONTHLY = "MONTHLY"
    TRIMESTRIAL = "TRIMESTRIAL"
    ANNUAL = "ANNUAL"
    ONE_TIME = "ONE_TIME"


class FeeStructureStatus(str, enum.Enum):
    """Fee structure status (Phase 11B)."""

    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class FeeAssignmentStatus(str, enum.Enum):
    """Fee assignment status (Phase 11B)."""

    ACTIVE = "ACTIVE"
    EXEMPTED = "EXEMPTED"
    ARCHIVED = "ARCHIVED"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class Invoice(TimestampMixin, SchoolScopedMixin, Base):
    """Invoice issued to a parent for a period."""

    __tablename__ = "invoices"

    parent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    period_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("periods.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=InvoiceStatus.PENDING.value
    )
    total_amount: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="MAD")
    issued_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    # Phase 11B: Overdue reminder tracking
    reminder_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reminder_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Phase 11B: Optional link to fee structure that generated this invoice
    fee_structure_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("fee_structures.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    items: Mapped[list["InvoiceItem"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan"
    )
    payment_plans: Mapped[list["PaymentPlan"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan"
    )
    payment_attempts: Mapped[list["PaymentAttempt"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="ck_invoices_total_amount"),
        CheckConstraint("due_date >= issued_date", name="ck_invoices_due_after_issued"),
        CheckConstraint("reminder_count >= 0", name="ck_invoices_reminder_count"),
        Index(
            "idx_invoices_parent_status_period",
            "parent_id",
            "status",
            "period_id",
        ),
        Index("idx_invoices_school_status", "school_id", "status"),
        Index("idx_invoices_due_date_status", "due_date", "status"),
    )

    @property
    def is_overdue(self) -> bool:
        return self.status == InvoiceStatus.PENDING.value and self.due_date < date.today()

    @property
    def is_paid(self) -> bool:
        return self.status == InvoiceStatus.PAID.value

    def __repr__(self) -> str:
        return (
            f"<Invoice id={_short_id(self.id)} status={self.status} "
            f"total={self.total_amount}>"
        )


class InvoiceItem(TimestampMixin, Base):
    """Line item on an invoice."""

    __tablename__ = "invoice_items"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Relationships
    invoice: Mapped["Invoice"] = relationship(back_populates="items")

    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_invoice_items_amount"),
        CheckConstraint("quantity > 0", name="ck_invoice_items_quantity"),
    )

    def __repr__(self) -> str:
        return (
            f"<InvoiceItem id={_short_id(self.id)} "
            f"invoice_id={_short_id(self.invoice_id)} amount={self.amount}>"
        )


class PaymentAttempt(TimestampMixin, SchoolScopedMixin, Base):
    """Payment attempt for an invoice.

    INV-BIL-FINALIZATION: finalized_at NOT NULL when status IN (paid, failed, canceled).
    """

    __tablename__ = "payment_attempts"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False
    )
    parent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    idempotency_key: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=PaymentAttemptStatus.PENDING.value
    )
    finalized_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Phase 11B: Retry tracking
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_retry_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_retry_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    invoice: Mapped["Invoice"] = relationship(back_populates="payment_attempts")
    proof: Mapped["PaymentProof | None"] = relationship(
        back_populates="payment_attempt", uselist=False
    )
    webhook_events: Mapped[list["ProviderWebhookEvent"]] = relationship(
        back_populates="payment_attempt", cascade="all, delete-orphan"
    )

    __table_args__ = (
        # INV-BIL-FINALIZATION
        CheckConstraint(
            "NOT (status IN ('paid', 'failed', 'canceled') AND finalized_at IS NULL)",
            name="ck_payment_attempts_finalization",
        ),
        Index(
            "idx_payment_attempts_invoice_created",
            "invoice_id",
            "created_at",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<PaymentAttempt id={_short_id(self.id)} status={self.status} "
            f"invoice_id={_short_id(self.invoice_id)}>"
        )


class PaymentProof(TimestampMixin, Base):
    """Proof of payment (receipt, confirmation from provider)."""

    __tablename__ = "payment_proofs"

    payment_attempt_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("payment_attempts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    proof_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    provider_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Relationships
    payment_attempt: Mapped["PaymentAttempt"] = relationship(back_populates="proof")

    def __repr__(self) -> str:
        return (
            f"<PaymentProof id={_short_id(self.id)} "
            f"payment_attempt_id={_short_id(self.payment_attempt_id)} source={self.source}>"
        )


class ProviderWebhookEvent(TimestampMixin, SchoolScopedMixin, Base):
    """Webhook event received from a payment provider.

    INV-BIL-WEBHOOK: duplicate provider_event_id = no-op.
    """

    __tablename__ = "provider_webhook_events"

    payment_attempt_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("payment_attempts.id", ondelete="SET NULL"), nullable=True
    )
    provider_event_id: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True
    )
    signature_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=WebhookEventStatus.RECEIVED.value
    )
    provider_event_received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Relationships
    payment_attempt: Mapped["PaymentAttempt | None"] = relationship(
        back_populates="webhook_events"
    )

    __table_args__ = (
        Index(
            "idx_webhook_events_school_received",
            "school_id",
            "provider_event_received_at",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<ProviderWebhookEvent id={_short_id(self.id)} status={self.status} "
            f"provider_event_id={self.provider_event_id}>"
        )


# ---------------------------------------------------------------------------
# Fee Structures & Assignments (Phase 11B)
# ---------------------------------------------------------------------------


class FeeStructure(TimestampMixin, SchoolScopedMixin, Base):
    """Fee structure — defines a recurring or one-time fee for a school.

    Examples: "Frais de scolarité 1ère année" (ANNUAL, 15000 MAD),
              "Frais de transport" (MONTHLY, 500 MAD).
    """

    __tablename__ = "fee_structures"

    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="MAD")
    frequency: Mapped[str] = mapped_column(
        String(20), nullable=False, default=FeeFrequency.ANNUAL.value
    )
    due_day: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    applies_to_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=FeeStructureStatus.ACTIVE.value
    )

    # Relationships
    assignments: Mapped[list["FeeAssignment"]] = relationship(
        back_populates="fee_structure", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_fee_structures_amount"),
        CheckConstraint(
            "due_day >= 1 AND due_day <= 28",
            name="ck_fee_structures_due_day",
        ),
        CheckConstraint(
            "frequency IN ('MONTHLY', 'TRIMESTRIAL', 'ANNUAL', 'ONE_TIME')",
            name="ck_fee_structures_frequency",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'ARCHIVED')",
            name="ck_fee_structures_status",
        ),
        Index("idx_fee_structures_school", "school_id"),
        Index("idx_fee_structures_school_year", "school_id", "academic_year_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<FeeStructure id={_short_id(self.id)} name={self.name} "
            f"amount={self.amount}>"
        )


class FeeAssignment(TimestampMixin, SchoolScopedMixin, Base):
    """Assignment of a fee structure to a specific student.

    Supports optional discount (percent-based with reason).
    Unique per (fee_structure_id, student_id).
    """

    __tablename__ = "fee_assignments"

    fee_structure_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fee_structures.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    discount_percent: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    discount_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=FeeAssignmentStatus.ACTIVE.value
    )

    # Relationships
    fee_structure: Mapped["FeeStructure"] = relationship(back_populates="assignments")

    __table_args__ = (
        UniqueConstraint(
            "fee_structure_id",
            "student_id",
            name="uq_fee_assignments_fee_student",
        ),
        CheckConstraint(
            "discount_percent IS NULL OR (discount_percent >= 0 AND discount_percent <= 100)",
            name="ck_fee_assignments_discount",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'EXEMPTED', 'ARCHIVED')",
            name="ck_fee_assignments_status",
        ),
        Index("idx_fee_assignments_school", "school_id"),
        Index("idx_fee_assignments_student", "student_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<FeeAssignment id={_short_id(self.id)} "
            f"student_id={_short_id(self.student_id)} status={self.status}>"
        )


class SiblingDiscountPolicy(TimestampMixin, SchoolScopedMixin, Base):
    """School-level sibling discount tiers for invoice generation."""

    __tablename__ = "sibling_discount_policies"

    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    second_child_percent: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, default=10.0
    )
    third_child_percent: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, default=20.0
    )
    fourth_plus_percent: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, default=30.0
    )
    apply_to_oldest_first: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )

    __table_args__ = (
        UniqueConstraint("school_id"),
        CheckConstraint(
            "second_child_percent >= 0 AND second_child_percent <= 100",
            name="ck_sibling_discount_second_percent",
        ),
        CheckConstraint(
            "third_child_percent >= 0 AND third_child_percent <= 100",
            name="ck_sibling_discount_third_percent",
        ),
        CheckConstraint(
            "fourth_plus_percent >= 0 AND fourth_plus_percent <= 100",
            name="ck_sibling_discount_fourth_percent",
        ),
        Index("idx_sdp_school", "school_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<SiblingDiscountPolicy id={_short_id(self.id)} enabled={self.enabled} "
            f"second_child_percent={self.second_child_percent}>"
        )


class LateFeePolicy(TimestampMixin, SchoolScopedMixin, Base):
    """School-level late-fee policy applied to overdue invoices."""

    __tablename__ = "late_fee_policies"

    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fee_type: Mapped[str] = mapped_column(String(20), nullable=False, default="fixed")
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    frequency: Mapped[str] = mapped_column(String(20), nullable=False, default="once")
    grace_days: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    max_fee: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)

    __table_args__ = (
        UniqueConstraint("school_id"),
        CheckConstraint(
            "fee_type IN ('fixed', 'percent')",
            name="ck_late_fee_policies_type",
        ),
        CheckConstraint(
            "frequency IN ('once', 'daily', 'weekly')",
            name="ck_late_fee_policies_frequency",
        ),
        CheckConstraint("amount >= 0", name="ck_late_fee_policies_amount"),
        CheckConstraint(
            "grace_days >= 0",
            name="ck_late_fee_policies_grace_days",
        ),
        CheckConstraint(
            "max_fee IS NULL OR max_fee >= 0",
            name="ck_late_fee_policies_max_fee",
        ),
        Index("idx_late_fee_policies_school", "school_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<LateFeePolicy id={_short_id(self.id)} fee_type={self.fee_type} "
            f"amount={self.amount}>"
        )


class PaymentPlan(TimestampMixin, SchoolScopedMixin, Base):
    """Installment plan for an invoice."""

    __tablename__ = "payment_plans"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False
    )
    total_installments: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    invoice: Mapped["Invoice"] = relationship(back_populates="payment_plans")
    installments: Mapped[list["Installment"]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "total_installments > 0",
            name="ck_payment_plans_total_installments",
        ),
        CheckConstraint(
            "status IN ('active', 'completed', 'canceled')",
            name="ck_payment_plans_status",
        ),
        Index("idx_payment_plans_school", "school_id"),
        Index("idx_payment_plans_invoice", "invoice_id"),
    )

    @property
    def is_completed(self) -> bool:
        return self.status == "completed"

    def __repr__(self) -> str:
        return (
            f"<PaymentPlan id={_short_id(self.id)} "
            f"invoice_id={_short_id(self.invoice_id)} status={self.status}>"
        )


class Installment(TimestampMixin, Base):
    """Individual installment within a payment plan."""

    __tablename__ = "installments"

    plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("payment_plans.id", ondelete="CASCADE"), nullable=False
    )
    installment_number: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")

    plan: Mapped["PaymentPlan"] = relationship(back_populates="installments")

    __table_args__ = (
        UniqueConstraint(
            "plan_id",
            "installment_number",
            name="uq_installments_plan_number",
        ),
        CheckConstraint(
            "installment_number > 0",
            name="ck_installments_number",
        ),
        CheckConstraint("amount >= 0", name="ck_installments_amount"),
        CheckConstraint(
            "status IN ('pending', 'paid', 'overdue')",
            name="ck_installments_status",
        ),
        Index("idx_installments_plan", "plan_id"),
        Index("idx_installments_due_status", "due_date", "status"),
    )

    @property
    def is_overdue(self) -> bool:
        return self.paid_at is None and self.due_date.date() < date.today()

    def __repr__(self) -> str:
        return (
            f"<Installment id={_short_id(self.id)} plan_id={_short_id(self.plan_id)} "
            f"status={self.status}>"
        )
