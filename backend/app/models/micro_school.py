"""Micro-school domain models for informal education cohorts and activity tracking."""

from __future__ import annotations

import enum
import uuid
from datetime import UTC, date, datetime

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
)
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.core.database import Base, TimestampMixin

ALLOWED_MICRO_CURRENCIES = {"MAD", "EUR", "USD"}
ALLOWED_MICRO_LANGUAGES = {"ar", "fr", "en"}


def _short_id(value: object | None) -> str:
    return str(value)[:8] if value is not None else "None"


def _enum_values(enum_cls: type[enum.Enum]) -> list[str]:
    return [item.value for item in enum_cls]


class MicroSchoolStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class MicroEnrollmentStatus(str, enum.Enum):
    ACTIVE = "active"
    WITHDRAWN = "withdrawn"


class MicroPaymentPeriodType(str, enum.Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class MicroPaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"


class MicroResourceType(str, enum.Enum):
    ACTIVITY_SHEET = "activity_sheet"
    SONG = "song"
    GAME = "game"
    LESSON_PLAN = "lesson_plan"


class MicroSchool(TimestampMixin, Base):
    """Small informal education unit owned by an educator."""

    __tablename__ = "micro_schools"

    educator_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    neighborhood: Mapped[str] = mapped_column(String(200), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    max_capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    status: Mapped[str] = mapped_column(
        PgEnum(
            MicroSchoolStatus,
            name="micro_school_status_enum",
            create_type=False,
            values_callable=_enum_values,
        ),
        nullable=False,
        default=MicroSchoolStatus.ACTIVE.value,
    )

    educator = relationship("User", foreign_keys=[educator_id])
    groups: Mapped[list["MicroGroup"]] = relationship(
        back_populates="micro_school",
        cascade="all, delete-orphan",
        order_by="MicroGroup.created_at",
    )
    payments: Mapped[list["MicroPayment"]] = relationship(
        back_populates="micro_school",
        cascade="all, delete-orphan",
        order_by="MicroPayment.created_at",
    )

    __table_args__ = (
        CheckConstraint("max_capacity > 0", name="ck_micro_schools_max_capacity"),
        Index("idx_micro_schools_educator", "educator_id"),
        Index("idx_micro_schools_city_status", "city", "status"),
    )

    @validates("phone")
    def validate_phone(self, key: str, value: str) -> str:
        cleaned = value.strip().replace(" ", "").replace("-", "")
        if not cleaned.startswith("+212"):
            raise ValueError("Micro-school phone must use Moroccan format (+212...)")
        return cleaned

    def __repr__(self) -> str:
        return f"<MicroSchool id={_short_id(self.id)} name={self.name} status={self.status}>"


class MicroGroup(TimestampMixin, Base):
    """Age-banded learning group inside a micro-school."""

    __tablename__ = "micro_groups"

    micro_school_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("micro_schools.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, default="المجموعة")
    age_range_min: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    age_range_max: Mapped[int] = mapped_column(Integer, nullable=False, default=6)

    micro_school: Mapped["MicroSchool"] = relationship(back_populates="groups")
    enrollments: Mapped[list["MicroEnrollment"]] = relationship(
        back_populates="micro_group",
        cascade="all, delete-orphan",
        order_by="MicroEnrollment.created_at",
    )

    __table_args__ = (
        CheckConstraint(
            "age_range_min >= 2 AND age_range_min <= 6",
            name="ck_micro_groups_age_range_min",
        ),
        CheckConstraint(
            "age_range_max >= 2 AND age_range_max <= 6",
            name="ck_micro_groups_age_range_max",
        ),
        CheckConstraint(
            "age_range_max >= age_range_min",
            name="ck_micro_groups_age_range_order",
        ),
        Index("idx_micro_groups_school", "micro_school_id"),
    )

    def __repr__(self) -> str:
        return f"<MicroGroup id={_short_id(self.id)} name={self.name}>"


class MicroEnrollment(TimestampMixin, Base):
    """Child enrollment in a micro-school group."""

    __tablename__ = "micro_enrollments"

    micro_group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("micro_groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    child_name: Mapped[str] = mapped_column(String(200), nullable=False)
    parent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    status: Mapped[str] = mapped_column(
        PgEnum(
            MicroEnrollmentStatus,
            name="micro_enrollment_status_enum",
            create_type=False,
            values_callable=_enum_values,
        ),
        nullable=False,
        default=MicroEnrollmentStatus.ACTIVE.value,
    )

    micro_group: Mapped["MicroGroup"] = relationship(back_populates="enrollments")
    parent = relationship("User", foreign_keys=[parent_id])
    payments: Mapped[list["MicroPayment"]] = relationship(
        back_populates="child_enrollment",
        cascade="all, delete-orphan",
        order_by="MicroPayment.created_at",
    )
    progress_logs: Mapped[list["MicroProgressLog"]] = relationship(
        back_populates="micro_enrollment",
        cascade="all, delete-orphan",
        order_by="MicroProgressLog.date",
    )

    __table_args__ = (
        Index("idx_micro_enrollments_group_status", "micro_group_id", "status"),
        Index("idx_micro_enrollments_parent_status", "parent_id", "status"),
    )

    @validates("child_name")
    def validate_child_name(self, key: str, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Child name is required")
        return cleaned

    def __repr__(self) -> str:
        return (
            f"<MicroEnrollment id={_short_id(self.id)} "
            f"child_name={self.child_name} status={self.status}>"
        )


class MicroPayment(TimestampMixin, Base):
    """Payment record for a child enrolled in a micro-school."""

    __tablename__ = "micro_payments"

    micro_school_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("micro_schools.id", ondelete="CASCADE"),
        nullable=False,
    )
    parent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    child_enrollment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("micro_enrollments.id", ondelete="CASCADE"),
        nullable=False,
    )
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="MAD")
    period_type: Mapped[str] = mapped_column(
        PgEnum(
            MicroPaymentPeriodType,
            name="micro_payment_period_type_enum",
            create_type=False,
            values_callable=_enum_values,
        ),
        nullable=False,
        default=MicroPaymentPeriodType.MONTHLY.value,
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(
        PgEnum(
            MicroPaymentStatus,
            name="micro_payment_status_enum",
            create_type=False,
            values_callable=_enum_values,
        ),
        nullable=False,
        default=MicroPaymentStatus.PENDING.value,
    )

    micro_school: Mapped["MicroSchool"] = relationship(back_populates="payments")
    parent = relationship("User", foreign_keys=[parent_id])
    child_enrollment: Mapped["MicroEnrollment"] = relationship(back_populates="payments")

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_micro_payments_amount"),
        CheckConstraint(
            "period_end >= period_start",
            name="ck_micro_payments_period_window",
        ),
        Index("idx_micro_payments_school_status", "micro_school_id", "status"),
        Index("idx_micro_payments_parent_period", "parent_id", "period_start"),
    )

    @validates("currency")
    def validate_currency(self, key: str, value: str) -> str:
        cleaned = value.strip().upper()
        if cleaned not in ALLOWED_MICRO_CURRENCIES:
            allowed = ", ".join(sorted(ALLOWED_MICRO_CURRENCIES))
            raise ValueError(f"Currency must be one of: {allowed}")
        return cleaned

    def __repr__(self) -> str:
        return (
            f"<MicroPayment id={_short_id(self.id)} amount={self.amount} "
            f"status={self.status}>"
        )


class MicroResource(TimestampMixin, Base):
    """Reusable resource for micro-school educators and parents."""

    __tablename__ = "micro_resources"

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    resource_type: Mapped[str] = mapped_column(
        PgEnum(
            MicroResourceType,
            name="micro_resource_type_enum",
            create_type=False,
            values_callable=_enum_values,
        ),
        nullable=False,
    )
    age_group: Mapped[str] = mapped_column(String(20), nullable=False)
    language: Mapped[str] = mapped_column(String(5), nullable=False, default="ar")
    file_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_premium: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        Index(
            "idx_micro_resources_type_language_age",
            "resource_type",
            "language",
            "age_group",
        ),
    )

    @validates("language")
    def validate_language(self, key: str, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in ALLOWED_MICRO_LANGUAGES:
            allowed = ", ".join(sorted(ALLOWED_MICRO_LANGUAGES))
            raise ValueError(f"Language must be one of: {allowed}")
        return cleaned

    def __repr__(self) -> str:
        return f"<MicroResource id={_short_id(self.id)} title={self.title}>"


class MicroProgressLog(TimestampMixin, Base):
    """Daily progress note for a child in a micro-school."""

    __tablename__ = "micro_progress_logs"

    micro_enrollment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("micro_enrollments.id", ondelete="CASCADE"),
        nullable=False,
    )
    educator_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    milestone_tag: Mapped[str | None] = mapped_column(String(50), nullable=True)

    micro_enrollment: Mapped["MicroEnrollment"] = relationship(back_populates="progress_logs")
    educator = relationship("User", foreign_keys=[educator_id])

    __table_args__ = (
        Index(
            "idx_micro_progress_logs_enrollment_date",
            "micro_enrollment_id",
            "date",
        ),
        Index("idx_micro_progress_logs_educator_date", "educator_id", "date"),
    )

    @validates("note")
    def validate_note(self, key: str, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Progress note is required")
        return cleaned

    def __repr__(self) -> str:
        return f"<MicroProgressLog id={_short_id(self.id)} date={self.date}>"


__all__ = [
    "MicroSchoolStatus",
    "MicroEnrollmentStatus",
    "MicroPaymentPeriodType",
    "MicroPaymentStatus",
    "MicroResourceType",
    "MicroSchool",
    "MicroGroup",
    "MicroEnrollment",
    "MicroPayment",
    "MicroResource",
    "MicroProgressLog",
]
