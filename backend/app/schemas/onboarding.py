"""Schemas for onboarding applications + SuperAdmin review."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, EmailStr, Field


class FormalSchoolApplicationRequest(BaseModel):
    applicant_name: str = Field(..., min_length=2, max_length=200)
    applicant_email: EmailStr
    applicant_phone: str | None = Field(None, max_length=30)
    city: str | None = Field(None, max_length=120)
    language: str | None = Field(None, max_length=10)
    org_name: str = Field(..., min_length=2, max_length=250)
    address: str | None = Field(None, max_length=300)
    level_band: str | None = Field(None, max_length=50)
    subjects: list[str] | None = None
    notes: str | None = None


class MicroSchoolApplicationRequest(BaseModel):
    applicant_name: str = Field(..., min_length=2, max_length=200)
    applicant_email: EmailStr
    applicant_phone: str | None = Field(None, max_length=30)
    city: str | None = Field(None, max_length=120)
    language: str | None = Field(None, max_length=10)
    org_name: str = Field(..., min_length=2, max_length=250)
    neighborhood: str | None = Field(None, max_length=200)
    address: str | None = Field(None, max_length=300)
    max_capacity: int | None = Field(None, ge=1, le=500)
    notes: str | None = None


class ApplicationAttachmentResponse(BaseModel):
    id: str
    file_path: str
    mime_type: str | None = None
    file_size: int | None = None
    kind: str


class ApplicationResponse(BaseModel):
    id: str
    application_type: str
    status: str
    applicant_name: str
    applicant_email: str
    applicant_phone: str | None = None
    city: str | None = None
    language: str | None = None
    org_name: str
    address: str | None = None
    neighborhood: str | None = None
    max_capacity: int | None = None
    level_band: str | None = None
    subjects: Any | None = None
    notes: str | None = None
    review_notes: str | None = None
    created_school_id: str | None = None
    created_at: str | None = None
    attachments: list[ApplicationAttachmentResponse] = []


class ApplicationReviewRequest(BaseModel):
    review_notes: str | None = Field(None, max_length=2000)


class ApplicationApproveResponse(BaseModel):
    application_id: str
    status: str
    created_school_id: str
    created_user_id: str
    role_target: str
    # One-click set-password link emailed to the owner; the plaintext token is
    # also surfaced (dev convenience) so the reviewer can relay it if needed.
    activation_url: str
    activation_token: str
