"""Upload session tracking model — Phase 8 direct-to-MinIO uploads."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin


class UploadSession(TimestampMixin, Base):
    """Lifecycle record for a single direct-to-MinIO upload.

    Created by POST /uploads/init (state=uploading), updated by
    POST /uploads/complete (state=scanning), and finalised by the
    task_post_upload_scan ARQ worker (state=available|quarantined|failed).

    The target entity (SubmissionFile, ContentItemAsset, etc.) is created
    by the worker only after the scan passes, so existing file-bearing tables
    require no schema changes.
    """

    __tablename__ = "upload_sessions"

    upload_state: Mapped[str] = mapped_column(
        String(20), nullable=False, default="uploading"
        # uploading → scanning → available | quarantined | failed
    )
    kind: Mapped[str] = mapped_column(
        String(30), nullable=False
        # assignment_pdf | submission_file | content_asset | video | audio
    )
    object_key: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str] = mapped_column(Text, nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )  # client-declared at /complete
    school_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False
    )
    uploader_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    scope_data: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
        # {"assignment_id": "...", "submission_id": "...", "content_item_id": "..."}
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )  # presigned PUT URL expiry
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )  # set by POST /uploads/complete
    scanned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )  # set by ARQ worker
    target_id: Mapped[uuid.UUID | None] = mapped_column(
        nullable=True
    )  # populated once state=available
    target_kind: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # e.g. "submission_file", "content_item_asset", "assignment"
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("idx_upload_sessions_state", "upload_state"),
        Index("idx_upload_sessions_school", "school_id"),
        Index("idx_upload_sessions_uploader", "uploader_id"),
        Index("idx_upload_sessions_created", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<UploadSession id={str(self.id)[:8]} kind={self.kind} "
            f"state={self.upload_state}>"
        )
