"""Onboarding applications — public school / educator registration requests.

A prospective formal school or micro-école (educator) submits an application.
A SuperAdmin reviews it and, on approval, the platform provisions the tenant +
owner account. Nothing here is school-scoped: an application has no school yet.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ENUM as PgEnum, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.core.database import Base, TimestampMixin
from app.models.taxonomy import Language, enum_values as _enum_values


class ApplicationType(str, enum.Enum):
    FORMAL_SCHOOL = "formal_school"
    MICRO_SCHOOL = "micro_school"


class ApplicationStatus(str, enum.Enum):
    PENDING = "pending"
    NEEDS_INFO = "needs_info"
    APPROVED = "approved"
    REJECTED = "rejected"


class AttachmentKind(str, enum.Enum):
    ID_DOC = "id_doc"
    AUTHORIZATION = "authorization"
    PHOTO = "photo"
    OTHER = "other"


class SchoolApplication(TimestampMixin, Base):
    """A pending onboarding request for a formal school or a micro-école."""

    __tablename__ = "school_applications"

    application_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ApplicationStatus.PENDING.value
    )

    # Applicant (the person submitting)
    applicant_name: Mapped[str] = mapped_column(String(200), nullable=False)
    applicant_email: Mapped[str] = mapped_column(String(255), nullable=False)
    applicant_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    language: Mapped[str | None] = mapped_column(
        PgEnum(
            Language,
            name="language_enum",
            create_type=False,
            values_callable=_enum_values,
        ),
        nullable=True,
    )

    # Organisation (the school / micro-école being requested)
    org_name: Mapped[str] = mapped_column(String(250), nullable=False)
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    neighborhood: Mapped[str | None] = mapped_column(String(200), nullable=True)
    max_capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    level_band: Mapped[str | None] = mapped_column(String(50), nullable=True)
    subjects: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Review / outcome
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_school_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("schools.id", ondelete="SET NULL"), nullable=True
    )
    created_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    attachments: Mapped[list["SchoolApplicationAttachment"]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_school_applications_status_type", "status", "application_type"),
        Index("idx_school_applications_email", "applicant_email"),
    )

    @validates("application_type")
    def _validate_type(self, key: str, value: str) -> str:
        normalized = (value or "").lower().strip()
        if normalized not in {item.value for item in ApplicationType}:
            raise ValueError("Unsupported application type")
        return normalized

    @validates("status")
    def _validate_status(self, key: str, value: str | None) -> str:
        normalized = (value or ApplicationStatus.PENDING.value).lower().strip()
        if normalized not in {item.value for item in ApplicationStatus}:
            raise ValueError("Unsupported application status")
        return normalized


class SchoolApplicationAttachment(TimestampMixin, Base):
    """A document/photo attached to an onboarding application."""

    __tablename__ = "school_application_attachments"

    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("school_applications.id", ondelete="CASCADE"), nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    kind: Mapped[str] = mapped_column(
        String(30), nullable=False, default=AttachmentKind.OTHER.value
    )

    application: Mapped["SchoolApplication"] = relationship(
        back_populates="attachments"
    )

    __table_args__ = (
        Index("idx_school_app_attachments_application", "application_id"),
    )
