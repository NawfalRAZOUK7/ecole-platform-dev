"""Phase 16 document management schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class DocumentLinkRequest(BaseModel):
    document_id: uuid.UUID
    category: str = Field(
        ...,
        pattern="^(certificate|report_card|medical|identity|transcript|other)$",
    )
    expires_at: datetime | None = None


class DocumentBulkRequest(BaseModel):
    document_ids: list[uuid.UUID] = Field(..., min_length=1, max_length=100)


class StudentDocumentRequirementItem(BaseModel):
    category: str
    required: bool
    description: str | None = None
    status: str
    expires_at: str | None = None
    document: dict | None = None


class DocumentListItem(BaseModel):
    id: str
    original_filename: str
    filename: str
    mime_type: str
    size_bytes: int
    category: str
    sha256: str
    linked_student_id: str | None = None
    linked_student_name: str | None = None
    uploader_id: str
    uploader_name: str | None = None
    expires_at: str | None = None
    is_expired: bool = False
    is_expiring_soon: bool = False
    download_count: int = 0
    thumbnail_url: str | None = None
    preview_url: str | None = None
    download_url: str | None = None
    created_at: str
    deleted_at: str | None = None
    deduplicated: bool = False
    can_delete: bool = False
    can_hard_delete: bool = False
