"""Reporting domain models — report generation jobs and export audit logs.

Reference: Phase 14 — Reports & Analytics
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin


class ReportType(str, enum.Enum):
    STUDENT_REPORT_CARD = "student_report_card"
    CLASS_SUMMARY = "class_summary"
    ATTENDANCE_REPORT = "attendance_report"
    BILLING_STATEMENT = "billing_statement"
    SCHOOL_ANALYTICS = "school_analytics"


class ReportJobStatus(str, enum.Enum):
    PENDING = "pending"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


class DataExportFormat(str, enum.Enum):
    CSV = "csv"
    XLSX = "xlsx"


class ReportSchedule(TimestampMixin, Base):
    """Scheduled report generation with role-targeted email delivery."""

    __tablename__ = "report_schedules"

    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    frequency: Mapped[str] = mapped_column(String(20), nullable=False)
    parameters: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    recipient_roles: Mapped[list[str]] = mapped_column(
        ARRAY(String(20)),
        nullable=False,
        default=list,
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    next_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        Index("idx_report_schedules_school", "school_id"),
        Index("idx_report_schedules_next_run", "next_run_at"),
    )


class ReportJob(TimestampMixin, Base):
    """Asynchronous PDF report generation job."""

    __tablename__ = "report_jobs"

    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    requester_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    parameters: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    parameters_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ReportJobStatus.PENDING.value,
    )
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        Index("idx_report_jobs_school_requester_created", "school_id", "requester_id", "created_at"),
        Index("idx_report_jobs_school_type_status", "school_id", "type", "status"),
        Index("idx_report_jobs_school_params_hash_created", "school_id", "parameters_hash", "created_at"),
        Index("idx_report_jobs_expires_at", "expires_at"),
    )


class DataExport(TimestampMixin, Base):
    """Audit log for CSV/XLSX exports."""

    __tablename__ = "data_exports"

    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    requester_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    entity: Mapped[str] = mapped_column(String(50), nullable=False)
    filters: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    format: Mapped[str] = mapped_column(String(10), nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        Index("idx_data_exports_school_created", "school_id", "created_at"),
        Index("idx_data_exports_requester_created", "requester_id", "created_at"),
        Index("idx_data_exports_entity_format", "entity", "format"),
    )
