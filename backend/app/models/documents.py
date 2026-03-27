"""Document management domain models — Phase 16."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin


class DocumentCategory(str, enum.Enum):
    CERTIFICATE = "certificate"
    REPORT_CARD = "report_card"
    MEDICAL = "medical"
    IDENTITY = "identity"
    TRANSCRIPT = "transcript"
    OTHER = "other"


class ResourceType(str, enum.Enum):
    LESSON_PLAN = "lesson_plan"
    WORKSHEET = "worksheet"
    PRESENTATION = "presentation"
    EXAM_TEMPLATE = "exam_template"
    REFERENCE = "reference"


class ResourceVisibility(str, enum.Enum):
    SCHOOL = "school"
    CLASS = "class"


class Document(TimestampMixin, Base):
    """Uploaded binary asset stored in local or S3-backed storage."""

    __tablename__ = "documents"

    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    uploader_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(150), nullable=False)
    size_bytes: Mapped[int] = mapped_column(nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    category: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default=DocumentCategory.OTHER.value,
    )
    linked_student_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    download_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        Index("idx_documents_school_created", "school_id", "created_at"),
        Index("idx_documents_school_category", "school_id", "category"),
        Index("idx_documents_school_sha", "school_id", "sha256"),
        Index("idx_documents_linked_student", "linked_student_id"),
        Index("idx_documents_deleted_at", "deleted_at"),
        Index("idx_documents_expires_at", "expires_at"),
    )


class Resource(TimestampMixin, Base):
    """Teacher/admin shared resource that points to a document asset."""

    __tablename__ = "resources"

    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    uploader_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    subject: Mapped[str | None] = mapped_column(String(120), nullable=True)
    level: Mapped[str | None] = mapped_column(String(120), nullable=True)
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(String(80)),
        nullable=False,
        default=list,
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    visibility: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ResourceVisibility.SCHOOL.value,
    )
    class_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("classes.id", ondelete="SET NULL"),
        nullable=True,
    )
    download_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_rating: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rating_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        Index("idx_resources_school_created", "school_id", "created_at"),
        Index("idx_resources_school_type", "school_id", "type"),
        Index("idx_resources_school_subject_level", "school_id", "subject", "level"),
        Index("idx_resources_school_visibility", "school_id", "visibility"),
        Index("idx_resources_class_id", "class_id"),
        Index("idx_resources_deleted_at", "deleted_at"),
    )


class ResourceRating(TimestampMixin, Base):
    """Per-teacher rating for a resource."""

    __tablename__ = "resource_ratings"

    resource_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("resource_id", "user_id", name="uq_resource_ratings_resource_user"),
        Index("idx_resource_ratings_resource", "resource_id"),
        Index("idx_resource_ratings_user", "user_id"),
    )


class StudentDocumentRequirement(TimestampMixin, Base):
    """School-scoped required document categories for student onboarding/compliance."""

    __tablename__ = "student_document_requirements"

    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "school_id",
            "category",
            name="uq_student_document_requirements_school_category",
        ),
        Index("idx_student_document_requirements_school", "school_id"),
    )
