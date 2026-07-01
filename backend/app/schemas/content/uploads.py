"""Pydantic schemas for Phase 8 direct-to-MinIO upload endpoints."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class UploadKind(str, enum.Enum):
    assignment_pdf = "assignment_pdf"
    submission_file = "submission_file"
    content_asset = "content_asset"
    video = "video"
    audio = "audio"


class UploadScope(BaseModel):
    school_id: uuid.UUID
    assignment_id: uuid.UUID | None = None
    submission_id: uuid.UUID | None = None
    content_item_id: uuid.UUID | None = None


class InitUploadRequest(BaseModel):
    kind: UploadKind
    filename: str = Field(min_length=1, max_length=500)
    mime_type: str = Field(min_length=1, max_length=150)
    size_bytes: int = Field(gt=0)
    scope: UploadScope


class InitUploadResponse(BaseModel):
    upload_id: uuid.UUID
    upload_url: str
    object_key: str
    expires_at: datetime
    max_size_bytes: int
    required_headers: dict[str, str]


class CompleteUploadRequest(BaseModel):
    upload_id: uuid.UUID
    sha256: str | None = Field(
        default=None,
        min_length=64,
        max_length=64,
        description="Hex SHA-256 of the uploaded file, used for integrity check",
    )
    size_bytes: int = Field(gt=0)


class CompleteUploadResponse(BaseModel):
    upload_id: uuid.UUID
    state: str
    status_url: str


class UploadStatusResponse(BaseModel):
    upload_id: uuid.UUID
    state: str
    kind: str
    target_id: uuid.UUID | None
    target_kind: str | None
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None
    scanned_at: datetime | None
