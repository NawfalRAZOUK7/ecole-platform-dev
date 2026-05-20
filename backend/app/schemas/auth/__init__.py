"""Pydantic schemas for auth endpoints.

Reference: S-030 through S-033, S-040, S-041 — Auth, invitation, and recovery flows.
Phase 2B: TOTP 2FA schemas (setup, verify, disable) and email verification.
Phase 2C: Registration with invitation code.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
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
    expires_in: int = Field(3600, description="Token lifetime in seconds")


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
    role_target: str = Field(
        ..., description="Role code for the invited user (e.g. TCH, PAR, STD)"
    )
    expires_in_hours: int = Field(
        default=72, ge=1, le=720, description="Hours until code expires"
    )
    target_student_id: UUID | None = Field(
        None,
        description="Student user ID to auto-link when a PAR registers with this code",
    )


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
    new_password: str = Field(
        ..., min_length=12, description="New password (min 12 chars, Phase 2A policy)"
    )


# ---------------------------------------------------------------------------
# Password change (Phase 2A)
# ---------------------------------------------------------------------------
class ChangePasswordRequest(BaseModel):
    current_password: str = Field(
        ..., min_length=1, description="Current password for verification"
    )
    new_password: str = Field(
        ..., min_length=12, description="New password (min 12 chars, Phase 2A policy)"
    )


# ---------------------------------------------------------------------------
# Two-Factor Authentication — TOTP (Phase 2B)
# ---------------------------------------------------------------------------
class TwoFactorVerifySetupRequest(BaseModel):
    code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="6-digit TOTP code from authenticator app",
    )


class TwoFactorDisableRequest(BaseModel):
    code: str = Field(..., min_length=6, description="TOTP code or backup code")


class TwoFactorVerifyLoginRequest(BaseModel):
    temp_token: str = Field(
        ..., min_length=1, description="Temporary token from login response"
    )
    code: str = Field(
        ..., min_length=6, max_length=8, description="TOTP code or backup code"
    )


# ---------------------------------------------------------------------------
# Email verification (Phase 2B)
# ---------------------------------------------------------------------------
class EmailVerifyRequest(BaseModel):
    user_id: UUID
    school_id: UUID
    otp: str = Field(
        ..., min_length=6, max_length=6, description="6-digit email verification OTP"
    )


# ---------------------------------------------------------------------------
# Registration with invitation code (Phase 2C)
# ---------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    code: str = Field(
        ..., min_length=8, max_length=8, description="8-char invitation code"
    )
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=200)
    phone: str | None = Field(None, max_length=20)
    password: str = Field(
        ..., min_length=12, description="Password (min 12 chars, Phase 2A policy)"
    )
    profile_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Role-specific profile fields (e.g. date_of_birth for STD, relationship_type for PAR)",
    )


class BatchRegisterItem(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=200)
    role: str = Field(..., description="Role code: STD, PAR, TCH")
    phone: str | None = Field(None, max_length=20)
    class_code: str | None = Field(
        None, description="Class code for auto-enrollment (optional)"
    )
    target_student_id: UUID | None = Field(
        None, description="Student user ID to auto-link for PAR role"
    )


# ---------------------------------------------------------------------------
# WebAuthn / Passkeys (Phase 10)
# ---------------------------------------------------------------------------
class WebAuthnRegistrationRequest(BaseModel):
    device_name: str = Field(..., max_length=100)
    device_type: str = Field(
        default="single_device", description="single_device or multi_device"
    )


class WebAuthnRegistrationResponse(BaseModel):
    id: str
    raw_id: str
    response: dict[str, Any]


class WebAuthnAuthenticationRequest(BaseModel):
    pass  # Challenge is stored in Redis/session


class WebAuthnAuthenticationResponse(BaseModel):
    id: str
    raw_id: str
    response: dict[str, Any]


class WebAuthnCredentialData(BaseModel):
    id: UUID
    credential_id: str
    device_name: str
    device_type: str
    transports: str | None
    is_backup: bool
    is_active: bool
    created_at: datetime


# ---------------------------------------------------------------------------
# OAuth / Social Login (Phase 10)
# ---------------------------------------------------------------------------
class OAuthLoginRequest(BaseModel):
    provider: str = Field(..., description="Provider: google, microsoft, apple")
    code: str = Field(..., description="OAuth authorization code")
    redirect_uri: str = Field(..., description="OAuth redirect URI")
    school_id: UUID


class OAuthAccountData(BaseModel):
    id: UUID
    provider: str
    provider_user_id: str
    provider_email: str | None
    created_at: datetime


# ---------------------------------------------------------------------------
# SMS 2FA (Phase 10)
# ---------------------------------------------------------------------------
class Sms2FASetupRequest(BaseModel):
    phone: str = Field(..., max_length=20)


class Sms2FAVerifyRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)


class Sms2FADisableRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)


class BatchRegisterRequest(BaseModel):
    users: list[BatchRegisterItem] = Field(..., min_length=1, max_length=100)
