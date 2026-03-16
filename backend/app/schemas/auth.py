"""Pydantic schemas for auth endpoints.

Reference: S-030 through S-033, S-040, S-041 — Auth, invitation, and recovery flows.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Login (S-030)
# ---------------------------------------------------------------------------
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)
    school_id: UUID


class LoginData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token lifetime in seconds")


# ---------------------------------------------------------------------------
# Refresh (S-031)
# ---------------------------------------------------------------------------
# No request body — refresh token comes from HttpOnly cookie


# ---------------------------------------------------------------------------
# Me (S-033)
# ---------------------------------------------------------------------------
class MembershipInfo(BaseModel):
    school_id: UUID
    role: str
    status: str


class MeData(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    school_id: UUID
    permissions: list[str]
    memberships: list[MembershipInfo]


# ---------------------------------------------------------------------------
# Invitation codes (S-040)
# ---------------------------------------------------------------------------
class InviteCreateRequest(BaseModel):
    role_target: str = Field(..., description="Role code for the invited user (e.g. TCH, PAR, STD)")
    expires_in_hours: int = Field(default=72, ge=1, le=720, description="Hours until code expires")


class InviteCreateData(BaseModel):
    invite_id: UUID
    code: str = Field(..., description="Plaintext code (shown once, never stored)")
    role_target: str
    expires_at: datetime


class InviteConsumeRequest(BaseModel):
    code: str = Field(..., min_length=8, max_length=8)


class InviteRevokeRequest(BaseModel):
    invite_id: UUID


# ---------------------------------------------------------------------------
# Account recovery (S-041)
# ---------------------------------------------------------------------------
class RecoveryRequestCreate(BaseModel):
    email: EmailStr
    school_id: UUID


class RecoveryRequestData(BaseModel):
    request_id: UUID
    message: str = "If the email exists, a recovery code has been sent."


class RecoveryVerifyRequest(BaseModel):
    request_id: UUID
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP")


class RecoveryResetRequest(BaseModel):
    request_id: UUID
    new_password: str = Field(..., min_length=12, description="New password (min 12 chars, Phase 2A policy)")


# ---------------------------------------------------------------------------
# Password change (Phase 2A)
# ---------------------------------------------------------------------------
class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, description="Current password for verification")
    new_password: str = Field(..., min_length=12, description="New password (min 12 chars, Phase 2A policy)")
