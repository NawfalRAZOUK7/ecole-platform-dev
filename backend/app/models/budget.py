"""Budget domain models for class-level decentralized spending workflows."""

from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.core.database import Base, SchoolScopedMixin, TimestampMixin

ALLOWED_BUDGET_CURRENCIES = {"MAD"}


def _short_id(value: object | None) -> str:
    return str(value)[:8] if value is not None else "None"


def _enum_values(enum_cls: type[enum.Enum]) -> list[str]:
    return [item.value for item in enum_cls]


class MicroBudgetStatus(str, enum.Enum):
    """Lifecycle states for a micro-budget."""

    ACTIVE = "active"
    FROZEN = "frozen"
    CLOSED = "closed"


class BudgetAllocationStatus(str, enum.Enum):
    """Lifecycle states for a budget allocation."""

    ACTIVE = "active"
    EXHAUSTED = "exhausted"
    FROZEN = "frozen"


class BudgetRequestStatus(str, enum.Enum):
    """Review states for a budget request."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class BudgetTransactionType(str, enum.Enum):
    """Transaction categories recorded against allocations."""

    ALLOCATION = "allocation"
    EXPENSE = "expense"
    REFUND = "refund"
    ADJUSTMENT = "adjustment"


class MicroBudget(TimestampMixin, SchoolScopedMixin, Base):
    """School budget envelope for a given academic year."""

    __tablename__ = "micro_budgets"

    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("academic_years.id", ondelete="CASCADE"),
        nullable=False,
    )
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    allocated_amount: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )
    remaining_amount: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="MAD")
    status: Mapped[str] = mapped_column(
        PgEnum(
            MicroBudgetStatus,
            name="micro_budget_status_enum",
            create_type=False,
            values_callable=_enum_values,
        ),
        nullable=False,
        default=MicroBudgetStatus.ACTIVE.value,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    academic_year = relationship("AcademicYear", foreign_keys=[academic_year_id])
    creator = relationship("User", foreign_keys=[created_by])
    allocations: Mapped[list["BudgetAllocation"]] = relationship(
        back_populates="budget",
        cascade="all, delete-orphan",
        order_by="BudgetAllocation.allocated_at",
    )

    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="ck_micro_budgets_total_amount"),
        CheckConstraint(
            "allocated_amount >= 0",
            name="ck_micro_budgets_allocated_amount",
        ),
        CheckConstraint(
            "remaining_amount >= 0",
            name="ck_micro_budgets_remaining_amount",
        ),
        CheckConstraint(
            "allocated_amount <= total_amount",
            name="ck_micro_budgets_allocated_lte_total",
        ),
        Index(
            "idx_micro_budgets_school_year_status",
            "school_id",
            "academic_year_id",
            "status",
        ),
        Index("idx_micro_budgets_creator", "created_by"),
        Index("idx_micro_budgets_academic_year_id", "academic_year_id"),
        Index("idx_micro_budgets_created_by", "created_by"),
    )

    @validates("currency")
    def validate_currency(self, key: str, value: str) -> str:
        cleaned = value.strip().upper()
        if cleaned not in ALLOWED_BUDGET_CURRENCIES:
            raise ValueError("Budget currency must be MAD")
        return cleaned

    def __repr__(self) -> str:
        return (
            f"<MicroBudget id={_short_id(self.id)} total={self.total_amount} "
            f"status={self.status}>"
        )


class BudgetAllocation(TimestampMixin, Base):
    """Budget slice allocated to a class or a teacher."""

    __tablename__ = "budget_allocations"

    budget_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("micro_budgets.id", ondelete="CASCADE"),
        nullable=False,
    )
    class_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("classes.id", ondelete="SET NULL"),
        nullable=True,
    )
    teacher_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    spent: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    remaining: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=0,
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="MAD")
    allocated_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    allocated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    status: Mapped[str] = mapped_column(
        PgEnum(
            BudgetAllocationStatus,
            name="budget_allocation_status_enum",
            create_type=False,
            values_callable=_enum_values,
        ),
        nullable=False,
        default=BudgetAllocationStatus.ACTIVE.value,
    )

    budget: Mapped["MicroBudget"] = relationship(back_populates="allocations")
    school_class = relationship("Class", foreign_keys=[class_id])
    teacher = relationship("User", foreign_keys=[teacher_id])
    allocator = relationship("User", foreign_keys=[allocated_by])
    requests: Mapped[list["BudgetRequest"]] = relationship(
        back_populates="allocation",
        cascade="all, delete-orphan",
        order_by="BudgetRequest.created_at",
    )
    transactions: Mapped[list["BudgetTransaction"]] = relationship(
        back_populates="allocation",
        cascade="all, delete-orphan",
        order_by="BudgetTransaction.recorded_at",
    )

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_budget_allocations_amount"),
        CheckConstraint("spent >= 0", name="ck_budget_allocations_spent"),
        CheckConstraint("remaining >= 0", name="ck_budget_allocations_remaining"),
        CheckConstraint(
            "spent <= amount",
            name="ck_budget_allocations_spent_lte_amount",
        ),
        CheckConstraint(
            "class_id IS NOT NULL OR teacher_id IS NOT NULL",
            name="ck_budget_allocations_target_present",
        ),
        Index("idx_budget_allocations_budget_status", "budget_id", "status"),
        Index("idx_budget_allocations_class", "class_id"),
        Index("idx_budget_allocations_teacher", "teacher_id"),
        Index("idx_budget_allocations_budget_id", "budget_id"),
        Index("idx_budget_allocations_class_id", "class_id"),
        Index("idx_budget_allocations_teacher_id", "teacher_id"),
        Index("idx_budget_allocations_allocated_by", "allocated_by"),
    )

    @validates("currency")
    def validate_currency(self, key: str, value: str) -> str:
        cleaned = value.strip().upper()
        if cleaned not in ALLOWED_BUDGET_CURRENCIES:
            raise ValueError("Budget currency must be MAD")
        return cleaned

    @validates("label")
    def validate_label(self, key: str, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Allocation label is required")
        return cleaned

    def __repr__(self) -> str:
        return (
            f"<BudgetAllocation id={_short_id(self.id)} amount={self.amount} "
            f"status={self.status}>"
        )


class BudgetRequest(TimestampMixin, Base):
    """Spending request raised against an allocation."""

    __tablename__ = "budget_requests"

    allocation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("budget_allocations.id", ondelete="CASCADE"),
        nullable=False,
    )
    requester_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="MAD")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    justification: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        PgEnum(
            BudgetRequestStatus,
            name="budget_request_status_enum",
            create_type=False,
            values_callable=_enum_values,
        ),
        nullable=False,
        default=BudgetRequestStatus.PENDING.value,
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    review_comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    allocation: Mapped["BudgetAllocation"] = relationship(back_populates="requests")
    requester = relationship("User", foreign_keys=[requester_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    transactions: Mapped[list["BudgetTransaction"]] = relationship(
        back_populates="request",
        order_by="BudgetTransaction.recorded_at",
    )

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_budget_requests_amount"),
        Index("idx_budget_requests_allocation_status", "allocation_id", "status"),
        Index("idx_budget_requests_requester_status", "requester_id", "status"),
        Index("idx_budget_requests_reviewed_by", "reviewed_by"),
    )

    @validates("currency")
    def validate_currency(self, key: str, value: str) -> str:
        cleaned = value.strip().upper()
        if cleaned not in ALLOWED_BUDGET_CURRENCIES:
            raise ValueError("Budget currency must be MAD")
        return cleaned

    @validates("description")
    def validate_description(self, key: str, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Budget request description is required")
        return cleaned

    def __repr__(self) -> str:
        return (
            f"<BudgetRequest id={_short_id(self.id)} amount={self.amount} "
            f"status={self.status}>"
        )


class BudgetTransaction(TimestampMixin, Base):
    """Ledger entry recorded against an allocation."""

    __tablename__ = "budget_transactions"

    allocation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("budget_allocations.id", ondelete="CASCADE"),
        nullable=False,
    )
    request_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("budget_requests.id", ondelete="SET NULL"),
        nullable=True,
    )
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    transaction_type: Mapped[str] = mapped_column(
        PgEnum(
            BudgetTransactionType,
            name="budget_transaction_type_enum",
            create_type=False,
            values_callable=_enum_values,
        ),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    receipt_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    recorded_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    allocation: Mapped["BudgetAllocation"] = relationship(back_populates="transactions")
    request: Mapped["BudgetRequest | None"] = relationship(
        back_populates="transactions"
    )
    recorder = relationship("User", foreign_keys=[recorded_by])

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_budget_transactions_amount"),
        Index(
            "idx_budget_transactions_allocation_recorded",
            "allocation_id",
            "recorded_at",
        ),
        Index("idx_budget_transactions_request", "request_id"),
        Index("idx_budget_transactions_allocation_id", "allocation_id"),
        Index("idx_budget_transactions_request_id", "request_id"),
        Index("idx_budget_transactions_recorded_by", "recorded_by"),
    )

    @validates("description")
    def validate_description(self, key: str, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Budget transaction description is required")
        return cleaned

    def __repr__(self) -> str:
        return (
            f"<BudgetTransaction id={_short_id(self.id)} amount={self.amount} "
            f"type={self.transaction_type}>"
        )


__all__ = [
    "BudgetAllocation",
    "BudgetAllocationStatus",
    "BudgetRequest",
    "BudgetRequestStatus",
    "BudgetTransaction",
    "BudgetTransactionType",
    "MicroBudget",
    "MicroBudgetStatus",
]
