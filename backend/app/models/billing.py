"""Billing domain models — Invoices, payments, proofs, webhooks, fee structures.

Reference: Pack C4 (Data Model — Billing section), Sprint 1 story S-018.
Migration group: G5-Billing (depends on G1-IAM, G2-ERP for user/period FKs).
Phase 11B: Added FeeStructure, FeeAssignment models; retry + reminder fields.
"""

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
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

from app.core.database import Base, TimestampMixin


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


class Invoice(TimestampMixin, Base):
    """Invoice issued to a parent for a period."""

    __tablename__ = "invoices"

    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
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


class PaymentAttempt(TimestampMixin, Base):
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
    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
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


class ProviderWebhookEvent(TimestampMixin, Base):
    """Webhook event received from a payment provider.

    INV-BIL-WEBHOOK: duplicate provider_event_id = no-op.
    """

    __tablename__ = "provider_webhook_events"

    payment_attempt_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("payment_attempts.id", ondelete="SET NULL"), nullable=True
    )
    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
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


# ---------------------------------------------------------------------------
# Fee Structures & Assignments (Phase 11B)
# ---------------------------------------------------------------------------


class FeeStructure(TimestampMixin, Base):
    """Fee structure — defines a recurring or one-time fee for a school.

    Examples: "Frais de scolarité 1ère année" (ANNUAL, 15000 MAD),
              "Frais de transport" (MONTHLY, 500 MAD).
    """

    __tablename__ = "fee_structures"

    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
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


class FeeAssignment(TimestampMixin, Base):
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
    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
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
