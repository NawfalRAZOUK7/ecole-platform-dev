"""Billing domain models — Invoices, payments, proofs, webhooks.

Reference: Pack C4 (Data Model — Billing section), Sprint 1 story S-018.
Migration group: G5-Billing (depends on G1-IAM, G2-ERP for user/period FKs).
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
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="MAD"
    )
    issued_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)

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
        Index(
            "idx_invoices_parent_status_period",
            "parent_id",
            "status",
            "period_id",
        ),
        Index("idx_invoices_school_status", "school_id", "status"),
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
    proof_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True
    )
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
