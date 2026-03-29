"""School entity — the root of multi-tenancy."""

from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.core.database import Base, SoftDeleteMixin, TimestampMixin


class SchoolStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"


class School(TimestampMixin, SoftDeleteMixin, Base):
    """A school (tenant) on the platform."""

    __tablename__ = "schools"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_ar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    massar_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        unique=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=SchoolStatus.ACTIVE.value,
    )
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    logo_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    max_students: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_teachers: Mapped[int | None] = mapped_column(Integer, nullable=True)
    subscription_plan: Mapped[str | None] = mapped_column(String(50), nullable=True)
    subscription_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    timezone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Africa/Casablanca",
    )
    default_language: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
        default="fr",
    )
    grading_scale: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="moroccan_20",
    )
    settings: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    @property
    def is_active(self) -> bool:
        return self.status == SchoolStatus.ACTIVE.value and not self.is_deleted

    @property
    def is_subscription_valid(self) -> bool:
        if not self.subscription_expires_at:
            return True
        return self.subscription_expires_at > datetime.now(timezone.utc)

    @validates("email")
    def validate_email(self, key: str, value: str | None) -> str | None:
        if value and "@" not in value:
            raise ValueError(f"Invalid school email: {value}")
        return value.lower().strip() if value else value

    def __repr__(self) -> str:
        return f"<School id={str(self.id)[:8]} name={self.name} status={self.status}>"
