"""Auth business logic — login, refresh, logout, me, 2FA, email verification.

Reference: S-030 through S-033, Pack D6 — Security Pipeline
Phase 2B: TOTP 2FA (setup, verify-setup, disable, verify-login), email verification
Layer: Service (called by Router, uses Repository)
"""

from __future__ import annotations

import hashlib
import json
import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from app.core.middleware import get_correlation_id
from app.core.permissions import get_permissions_for_role
from app.core.security import (
    create_access_token,
    create_csrf_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.core.password_policy import password_validator
from app.repositories.auth import AuthRepository
from app.schemas.profile import (
    ParentProfileUpdate,
    StudentProfileUpdate,
    TeacherProfileUpdate,
)
from app.services.audit import AuditService

logger = logging.getLogger(__name__)

# Rate limiting constants
RATE_LIMIT_MAX_ATTEMPTS = 5
RATE_LIMIT_WINDOW_SECONDS = 900  # 15 minutes

# Recovery constants
RECOVERY_MAX_ATTEMPTS = 5
RECOVERY_LOCK_MINUTES = 30
RECOVERY_EXPIRE_MINUTES = 15
OTP_LENGTH = 6

# 2FA temp token TTL (5 minutes to enter TOTP code after password check)
TOTP_TEMP_TOKEN_TTL = 300

# Email verification OTP TTL
EMAIL_VERIFY_EXPIRE_MINUTES = 30


def _normalize_profile_data(role: str, profile_data: dict[str, Any]) -> dict[str, Any]:
    """Coerce role-specific registration payloads through the profile schemas."""
    if role == "STD":
        return StudentProfileUpdate(**profile_data).model_dump(exclude_unset=True)
    if role == "PAR":
        return ParentProfileUpdate(**profile_data).model_dump(exclude_unset=True)
    if role == "TCH":
        return TeacherProfileUpdate(**profile_data).model_dump(exclude_unset=True)
    return {}


class AuthService:
    """Handles authentication operations: login, refresh, logout, profile."""

    def __init__(self, db: AsyncSession, redis: aioredis.Redis) -> None:
        self.db = db
        self.redis = redis
        self.repo = AuthRepository(db)
        self.audit = AuditService(db)

    # ------------------------------------------------------------------
    # Login (S-030, Phase 2A: device info)
    # ------------------------------------------------------------------
    async def login(
        self,
        email: str,
        password: str,
        school_id: uuid.UUID,
        source: str = "web",
        ip_address: str | None = None,
        user_agent: str | None = None,
        device_name: str | None = None,
    ) -> dict[str, Any]:
        """Authenticate user and create a session.

        Returns dict with access_token, refresh_token, csrf_token, and metadata.
        Raises: AuthenticationError (401), AuthorizationError (403), RateLimitError (429)
        """
        # 1. Rate limiting — max 5 failed attempts per email per 15 minutes
        rate_key = f"login_attempts:{email}:{school_id}"
        attempt_count = await self.redis.get(rate_key)
        if attempt_count and int(attempt_count) >= RATE_LIMIT_MAX_ATTEMPTS:
            await self.audit.log_event(
                school_id=school_id,
                action_type="AUTH_LOGIN_RATE_LIMITED",
                outcome="denied",
                error_code="ERR-RATE-429",
                ip_address=ip_address,
            )
            raise RateLimitError(
                "Too many login attempts. Please try again later.",
                error_code="ERR-RATE-429",
            )

        # 2. Find user by email + school_id
        user = await self.repo.get_user_by_email(email, school_id)

        if user is None or not verify_password(password, user.password_hash):
            # Increment failed attempts
            pipe = self.redis.pipeline()
            pipe.incr(rate_key)
            pipe.expire(rate_key, RATE_LIMIT_WINDOW_SECONDS)
            await pipe.execute()

            await self.audit.log_event(
                school_id=school_id,
                action_type="AUTH_LOGIN_FAILED",
                outcome="denied",
                error_code="ERR-IAM-401",
                ip_address=ip_address,
            )
            raise AuthenticationError(
                "Invalid email or password",
                error_code="ERR-IAM-401",
            )

        # 3. Check user status is active
        if user.status != "active":
            await self.audit.log_event(
                school_id=school_id,
                actor_id=user.id,
                action_type="AUTH_LOGIN_INACTIVE",
                outcome="denied",
                error_code="ERR-IAM-403",
                ip_address=ip_address,
            )
            raise AuthorizationError(
                "Account is not active",
                error_code="ERR-IAM-403",
            )

        # 4. Check active membership for user + school
        membership = await self.repo.get_membership(user.id, school_id)
        if membership is None:
            await self.audit.log_event(
                school_id=school_id,
                actor_id=user.id,
                action_type="AUTH_LOGIN_NO_MEMBERSHIP",
                outcome="denied",
                error_code="ERR-IAM-404",
                ip_address=ip_address,
            )
            raise NotFoundError(
                "No active membership for this school",
                error_code="ERR-IAM-404",
            )

        # 5. Phase 2B — Check if 2FA is enabled
        role = membership.role_code
        if user.totp_enabled:
            # Generate a temp token and store context in Redis
            temp_token = secrets.token_urlsafe(48)
            temp_data = json.dumps(
                {
                    "user_id": str(user.id),
                    "school_id": str(school_id),
                    "role": role,
                    "source": source,
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                    "device_name": device_name,
                }
            )
            await self.redis.setex(
                f"2fa_temp:{temp_token}",
                TOTP_TEMP_TOKEN_TTL,
                temp_data,
            )

            # Clear rate limit on successful password check
            await self.redis.delete(rate_key)

            # Audit
            await self.audit.log_event(
                school_id=school_id,
                actor_id=user.id,
                action_type="AUTH_2FA_REQUIRED",
                outcome="pending",
                ip_address=ip_address,
            )

            return {
                "requires_2fa": True,
                "temp_token": temp_token,
                "message": "Two-factor authentication required. Please provide your TOTP code.",
            }

        # 6. Create session record (Phase 2A: include device info)
        cid = get_correlation_id()
        session = await self.repo.create_session(
            user_id=user.id,
            school_id=school_id,
            source=source,
            correlation_id=uuid.UUID(cid) if cid else None,
            user_agent=user_agent[:500] if user_agent else None,
            ip_address=ip_address[:45] if ip_address else None,
            device_name=device_name[:200] if device_name else None,
        )

        # 7. Generate tokens
        access_token = create_access_token(user.id, role, school_id, session.id)
        refresh_token, refresh_jti = create_refresh_token(
            user.id, school_id, session.id
        )
        csrf_token = create_csrf_token()

        # 8. Store refresh JTI in Redis for rotation tracking
        await self.redis.setex(
            f"refresh_jti:{session.id}",
            settings.refresh_token_expire_days * 86400,  # TTL in seconds
            refresh_jti,
        )

        # 9. Store CSRF token in Redis
        await self.redis.setex(
            f"csrf:{session.id}",
            settings.refresh_token_expire_days * 86400,
            csrf_token,
        )

        # 10. Clear rate limit on successful login
        await self.redis.delete(rate_key)

        # 11. Audit event
        await self.audit.log_event(
            school_id=school_id,
            actor_id=user.id,
            action_type="AUTH_SESSION_OPENED",
            outcome="success",
            target_type="session",
            target_id=session.id,
            ip_address=ip_address,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "csrf_token": csrf_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
            "session_id": session.id,
        }

    # ------------------------------------------------------------------
    # Register with invitation code (Phase 2C)
    # ------------------------------------------------------------------
    async def register(
        self,
        code: str,
        email: str,
        full_name: str,
        password: str,
        phone: str | None = None,
        profile_data: dict | None = None,
        source: str = "web",
        ip_address: str | None = None,
        user_agent: str | None = None,
        device_name: str | None = None,
    ) -> dict[str, Any]:
        """Register a new user with an invitation code.

        Validates code, enforces password policy, creates user + membership +
        role-specific profile in a single transaction. Auto-creates parent_child_link
        if code has target_student_id and role is PAR.
        Returns JWT tokens so the user is logged in immediately.
        """
        # 1. Validate invitation code
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        invite = await self.repo.get_invitation_by_code_hash(code_hash)

        if invite is None:
            raise NotFoundError("Invalid invitation code", error_code="ERR-IAM-404")

        if invite.expires_at and invite.expires_at < datetime.now(timezone.utc):
            raise AuthenticationError(
                "Invitation code has expired",
                error_code="ERR-IAM-EXPIRED",
            )

        if invite.consumed_by is not None:
            raise ConflictError(
                "Invitation code has already been used",
                error_code="ERR-IAM-CONFLICT",
            )

        school_id = invite.school_id
        role = invite.role_target
        profile_data = _normalize_profile_data(
            role=role,
            profile_data=profile_data or {},
        )

        # 2. Check email uniqueness within this school
        existing_user = await self.repo.get_user_by_email(email, school_id)
        if existing_user is not None:
            raise ConflictError(
                "An account with this email already exists for this school",
                error_code="ERR-IAM-CONFLICT",
            )

        # 3. Enforce password policy
        password_validator.validate(password, email=email, full_name=full_name)

        # 4. Create user
        user = await self.repo.create_user(
            email=email,
            full_name=full_name,
            phone=phone,
            password_hash=hash_password(password),
            status="active",
            school_id=school_id,
        )

        # 5. Create membership
        membership = await self.repo.create_membership(
            user_id=user.id,
            school_id=school_id,
            role_code=role,
            status="active",
        )

        # 6. Create role-specific profile
        if role == "STD":
            await self.repo.create_student_profile(
                user_id=user.id,
                school_id=school_id,
                **profile_data,
            )
        elif role == "PAR":
            await self.repo.create_parent_profile(
                user_id=user.id,
                school_id=school_id,
                **profile_data,
            )
        elif role == "TCH":
            await self.repo.create_teacher_profile(
                user_id=user.id,
                school_id=school_id,
                **profile_data,
            )

        # 7. Auto-create parent_child_link if code has target_student_id
        if role == "PAR" and invite.target_student_id:
            await self.repo.create_parent_child_link(
                parent_user_id=user.id,
                child_user_id=invite.target_student_id,
                school_id=school_id,
                status="active",
                linked_at=datetime.now(timezone.utc),
                linked_by=invite.issuer_user_id,
            )

        # 8. Consume the invitation code
        await self.repo.consume_invitation(
            invite.id,
            user_id=user.id,
            consumed_at=datetime.now(timezone.utc),
        )

        # 9. Create session and generate tokens
        cid = get_correlation_id()
        session = await self.repo.create_session(
            user_id=user.id,
            school_id=school_id,
            source=source,
            correlation_id=uuid.UUID(cid) if cid else None,
            user_agent=user_agent[:500] if user_agent else None,
            ip_address=ip_address[:45] if ip_address else None,
            device_name=device_name[:200] if device_name else None,
        )

        access_token = create_access_token(user.id, role, school_id, session.id)
        refresh_token, refresh_jti = create_refresh_token(
            user.id, school_id, session.id
        )
        csrf_token = create_csrf_token()

        # Store refresh JTI and CSRF in Redis
        await self.redis.setex(
            f"refresh_jti:{session.id}",
            settings.refresh_token_expire_days * 86400,
            refresh_jti,
        )
        await self.redis.setex(
            f"csrf:{session.id}",
            settings.refresh_token_expire_days * 86400,
            csrf_token,
        )

        # 10. Audit event
        await self.audit.log_event(
            school_id=school_id,
            actor_id=user.id,
            action_type="USER_REGISTERED",
            outcome="success",
            target_type="user",
            target_id=user.id,
            ip_address=ip_address,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "csrf_token": csrf_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
            "user_id": user.id,
            "school_id": school_id,
            "role": role,
            "email_verification_required": True,
        }

    # ------------------------------------------------------------------
    # Refresh (S-031)
    # ------------------------------------------------------------------
    async def refresh(
        self,
        refresh_token_str: str,
        csrf_token: str | None = None,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        """Refresh the access token using a valid refresh token.

        Implements token rotation: old refresh token invalidated, new one issued.
        Requires CSRF double-submit cookie validation.
        """
        # 1. Decode refresh token
        payload = decode_refresh_token(refresh_token_str)
        session_id = uuid.UUID(payload["session_id"])
        user_id = uuid.UUID(payload["sub"])
        school_id = uuid.UUID(payload["school_id"])
        token_jti = payload["jti"]

        # 2. CSRF validation (double-submit cookie pattern)
        stored_csrf = await self.redis.get(f"csrf:{session_id}")
        if stored_csrf is None or csrf_token is None or csrf_token != stored_csrf:
            raise AuthorizationError(
                "Invalid CSRF token",
                error_code="ERR-IAM-403",
            )

        # 3. Verify session is active
        session = await self.repo.get_session_by_id(session_id, active_only=True)
        if session is None:
            raise AuthenticationError(
                "Session has been revoked",
                error_code="ERR-IAM-401",
            )

        # 4. Verify JTI matches (rotation check)
        stored_jti = await self.redis.get(f"refresh_jti:{session_id}")
        if stored_jti != token_jti:
            # Possible replay attack — revoke session entirely
            await self.repo.revoke_session(session_id, datetime.now(timezone.utc))
            await self.redis.delete(f"refresh_jti:{session_id}")
            await self.redis.delete(f"csrf:{session_id}")
            logger.warning(
                "Refresh token replay detected for session %s, revoking", session_id
            )
            raise AuthenticationError(
                "Token has been rotated — session revoked for security",
                error_code="ERR-IAM-401",
            )

        # 5. Get user's active role for this school
        membership = await self.repo.get_membership(user_id, school_id)
        if membership is None:
            raise AuthenticationError(
                "No active membership",
                error_code="ERR-IAM-401",
            )

        role = membership.role_code

        # 6. Issue new tokens (rotation)
        new_access = create_access_token(user_id, role, school_id, session_id)
        new_refresh, new_jti = create_refresh_token(user_id, school_id, session_id)
        new_csrf = create_csrf_token()

        # 7. Update Redis with new JTI and CSRF
        ttl = settings.refresh_token_expire_days * 86400
        await self.redis.setex(f"refresh_jti:{session_id}", ttl, new_jti)
        await self.redis.setex(f"csrf:{session_id}", ttl, new_csrf)

        # 8. Audit
        await self.audit.log_event(
            school_id=school_id,
            actor_id=user_id,
            action_type="AUTH_TOKEN_REFRESHED",
            outcome="success",
            target_type="session",
            target_id=session_id,
            ip_address=ip_address,
        )

        return {
            "access_token": new_access,
            "refresh_token": new_refresh,
            "csrf_token": new_csrf,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
        }

    # ------------------------------------------------------------------
    # Logout (S-032)
    # ------------------------------------------------------------------
    async def logout(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        school_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> None:
        """Revoke the user's session and clean up tokens.

        Idempotent: calling logout on an already-revoked session is a no-op.
        """
        # 1. Revoke session (set revoke_at)
        await self.repo.revoke_session(session_id, datetime.now(timezone.utc))

        # 2. Clean up Redis
        await self.redis.delete(f"refresh_jti:{session_id}")
        await self.redis.delete(f"csrf:{session_id}")

        # 3. Audit
        await self.audit.log_event(
            school_id=school_id,
            actor_id=user_id,
            action_type="AUTH_SESSION_CLOSED",
            outcome="success",
            target_type="session",
            target_id=session_id,
            ip_address=ip_address,
        )

    # ------------------------------------------------------------------
    # Me / Profile (S-033)
    # ------------------------------------------------------------------
    async def get_profile(
        self,
        user_id: uuid.UUID,
        school_id: uuid.UUID,
        role: str,
    ) -> dict[str, Any]:
        """Get the authenticated user's profile with permissions and memberships."""
        # 1. Load user
        user = await self.repo.get_user_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found", error_code="ERR-IAM-404")

        # 2. Load all memberships for this user
        memberships = await self.repo.list_memberships(user_id, active_only=True)

        # 3. Get permissions for current role
        permissions = sorted(get_permissions_for_role(role))

        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": role,
            "school_id": school_id,
            "permissions": permissions,
            "memberships": [
                {
                    "school_id": m.school_id,
                    "role": m.role_code,
                    "status": m.status,
                }
                for m in memberships
            ],
        }

    # ------------------------------------------------------------------
    # Session listing (Phase 2A)
    # ------------------------------------------------------------------
    async def list_sessions(
        self,
        user_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> list[dict[str, Any]]:
        """List active sessions for the authenticated user.

        Returns sessions with device info (user_agent, ip_address, device_name).
        Only returns non-revoked sessions for the user's current school.
        """
        sessions = await self.repo.list_active_sessions(
            user_id=user_id,
            school_id=school_id,
        )

        return [
            {
                "session_id": s.id,
                "source": s.source,
                "user_agent": s.user_agent,
                "ip_address": s.ip_address,
                "device_name": s.device_name,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "last_active": s.updated_at.isoformat() if s.updated_at else None,
            }
            for s in sessions
        ]

    # ------------------------------------------------------------------
    # Session revocation (Phase 2A)
    # ------------------------------------------------------------------
    async def revoke_session(
        self,
        target_session_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        actor_school_id: uuid.UUID,
        actor_role: str,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        """Revoke a specific session.

        Users can revoke their own sessions.
        ADM can revoke any session within their school.
        """
        # Find the target session
        session = await self.repo.get_session_by_id(target_session_id, active_only=True)

        if session is None:
            raise NotFoundError("Session not found", error_code="ERR-IAM-404")

        # School boundary check
        if session.school_id != actor_school_id:
            raise NotFoundError("Session not found", error_code="ERR-IAM-404")

        # Authorization: owner or ADM
        if session.user_id != actor_user_id and actor_role != "ADM":
            raise AuthorizationError(
                "Cannot revoke another user's session",
                error_code="ERR-AUTHZ-001",
            )

        # Revoke
        session.revoke_at = datetime.now(timezone.utc)
        await self.repo.save_session(session)

        # Clean up Redis tokens
        await self.redis.delete(f"refresh_jti:{target_session_id}")
        await self.redis.delete(f"csrf:{target_session_id}")

        # Audit
        await self.audit.log_event(
            school_id=actor_school_id,
            actor_id=actor_user_id,
            action_type="AUTH_SESSION_REVOKED",
            outcome="success",
            target_type="session",
            target_id=target_session_id,
            ip_address=ip_address,
        )

        return {"message": "Session revoked successfully"}

    # ------------------------------------------------------------------
    # Password change (Phase 2A)
    # ------------------------------------------------------------------
    async def change_password(
        self,
        user_id: uuid.UUID,
        school_id: uuid.UUID,
        current_password: str,
        new_password: str,
        current_session_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        """Change user's password (requires current password).

        Enforces password policy on the new password.
        Revokes all other sessions (keeps current one).
        """
        # Load user
        user = await self.repo.get_user_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found", error_code="ERR-IAM-404")

        # Verify current password
        if not verify_password(current_password, user.password_hash):
            raise AuthenticationError(
                "Current password is incorrect",
                error_code="ERR-IAM-401",
            )

        # Enforce password policy
        from app.core.password_policy import password_validator

        password_validator.validate(
            new_password,
            email=user.email,
            full_name=user.full_name,
        )

        # Update password
        user.password_hash = hash_password(new_password)
        await self.repo.save_user(user)

        # Revoke all OTHER active sessions (keep current one)
        await self.repo.revoke_all_sessions(
            user_id,
            datetime.now(timezone.utc),
            exclude_session_id=current_session_id,
        )

        # Audit
        await self.audit.log_event(
            school_id=school_id,
            actor_id=user_id,
            action_type="PASSWORD_CHANGED",
            outcome="success",
            target_type="user",
            target_id=user_id,
            ip_address=ip_address,
        )

        return {"message": "Password changed successfully"}


class InvitationService:
    """Handles invitation code operations: create, consume, revoke (S-040)."""

    def __init__(self, db: AsyncSession, redis: aioredis.Redis) -> None:
        self.db = db
        self.redis = redis
        self.repo = AuthRepository(db)
        self.audit = AuditService(db)

    async def create_invite(
        self,
        school_id: uuid.UUID,
        issuer_user_id: uuid.UUID,
        role_target: str,
        expires_in_hours: int = 72,
        target_student_id: uuid.UUID | None = None,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        """Create a new invitation code.

        Generates an 8-char alphanumeric code, hashes it with SHA-256 before storage.
        Returns the plaintext code (shown once, never stored).
        If target_student_id is provided (PAR invites), validates the student exists
        in the same school and persists the link target on the invitation.
        """
        # Validate target_student_id if provided
        if target_student_id is not None:
            if role_target != "PAR":
                from app.core.exceptions import ValidationError

                raise ValidationError(
                    "target_student_id is only valid for PAR invitations",
                    error_code="ERR-VAL-001",
                )
            # Check student exists in the same school with STD role
            student = await self.repo.get_student_in_school(target_student_id, school_id)
            if student is None:
                from app.core.exceptions import NotFoundError

                raise NotFoundError(
                    "Target student not found in this school",
                    error_code="ERR-RES-404",
                )

        # Generate 8-char code
        code = secrets.token_hex(4).upper()  # 8 hex chars

        # Hash for storage
        code_hash = hashlib.sha256(code.encode()).hexdigest()

        expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)

        invite = await self.repo.create_invitation(
            school_id=school_id,
            issuer_user_id=issuer_user_id,
            code_hash=code_hash,
            role_target=role_target,
            expires_at=expires_at,
            target_student_id=target_student_id,
        )

        # Audit
        await self.audit.log_event(
            school_id=school_id,
            actor_id=issuer_user_id,
            action_type="INVITE_ACTIVATED",
            outcome="success",
            target_type="invitation_code",
            target_id=invite.id,
            ip_address=ip_address,
        )

        return {
            "invite_id": invite.id,
            "code": code,
            "role_target": role_target,
            "expires_at": expires_at,
        }

    async def consume_invite(
        self,
        code: str,
        user_id: uuid.UUID,
        school_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        """Consume an invitation code and create a membership.

        Validates: hash match, not expired, not consumed, school scope.
        Creates membership for the user with the code's role_target.
        Idempotent: same code + same user = returns existing membership.
        """
        code_hash = hashlib.sha256(code.encode()).hexdigest()

        # Find the invitation
        invite = await self.repo.get_invitation_by_code_hash(code_hash)

        if invite is None:
            raise NotFoundError("Invalid invitation code", error_code="ERR-IAM-404")

        # Check school scope
        if invite.school_id != school_id:
            raise NotFoundError("Invalid invitation code", error_code="ERR-IAM-404")

        # Check not expired
        if invite.expires_at and invite.expires_at < datetime.now(timezone.utc):
            raise AuthenticationError(
                "Invitation code has expired",
                error_code="ERR-IAM-EXPIRED",
            )

        # Check not already consumed
        if invite.consumed_by is not None:
            if invite.consumed_by == user_id:
                # Idempotent: same user consuming again
                return {
                    "message": "Invitation already consumed",
                    "role": invite.role_target,
                }
            raise ConflictError(
                "Invitation code has already been used",
                error_code="ERR-IAM-CONFLICT",
            )

        # Consume: update invitation
        await self.repo.consume_invitation(
            invite.id,
            user_id=user_id,
            consumed_at=datetime.now(timezone.utc),
        )

        # Create membership for user
        membership = await self.repo.create_membership(
            user_id=user_id,
            school_id=school_id,
            role_code=invite.role_target,
            status="active",
        )

        user = await self.repo.get_user_by_id(user_id)
        email_verification_required = False
        if user and user.email_verified_at is None:
            email_service = EmailVerificationService(self.db, self.redis)
            await email_service.send_verification_otp(
                user_id=user_id,
                school_id=school_id,
                email=user.email,
                ip_address=ip_address,
            )
            email_verification_required = True

        # Audit
        await self.audit.log_event(
            school_id=school_id,
            actor_id=user_id,
            action_type="IAM_CODE_CONSUMED",
            outcome="success",
            target_type="invitation_code",
            target_id=invite.id,
            ip_address=ip_address,
        )

        return {
            "message": "Invitation consumed successfully",
            "role": invite.role_target,
            "membership_id": membership.id,
            "email_verification_required": email_verification_required,
        }

    async def revoke_invite(
        self,
        invite_id: uuid.UUID,
        school_id: uuid.UUID,
        actor_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        """Soft-revoke an invitation code.

        Idempotent: revoking an already-revoked code is a no-op.
        """
        invite = await self.repo.get_invitation_by_id(invite_id, school_id)

        if invite is None:
            raise NotFoundError("Invitation not found", error_code="ERR-IAM-404")

        # Set consumed_at to mark as revoked (if not already consumed)
        if invite.consumed_by is None:
            invite.consumed_at = datetime.now(timezone.utc)
            # Set expires_at to now to effectively revoke
            invite.expires_at = datetime.now(timezone.utc)
            await self.repo.save_invitation(invite)

        # Audit
        await self.audit.log_event(
            school_id=school_id,
            actor_id=actor_id,
            action_type="INVITE_REVOKED",
            outcome="success",
            target_type="invitation_code",
            target_id=invite.id,
            ip_address=ip_address,
        )

        return {"message": "Invitation revoked"}


class RecoveryService:
    """Handles account recovery: request, verify OTP, reset password (S-041)."""

    def __init__(self, db: AsyncSession, redis: aioredis.Redis) -> None:
        self.db = db
        self.redis = redis
        self.repo = AuthRepository(db)
        self.audit = AuditService(db)

    async def request_recovery(
        self,
        email: str,
        school_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        """Request account recovery — always returns 200 to prevent email enumeration.

        If user exists: creates recovery request and generates OTP (logged in dev).
        If user doesn't exist: returns success anyway (no enumeration).
        """
        # Find user (but don't reveal if not found)
        user = await self.repo.get_user_by_email(email, school_id)

        if user is None:
            # Don't reveal that user doesn't exist — return same response
            return {
                "request_id": uuid.uuid4(),
                "message": "If the email exists, a recovery code has been sent.",
            }

        # Generate OTP
        otp = "".join([str(secrets.randbelow(10)) for _ in range(OTP_LENGTH)])
        otp_hash = hashlib.sha256(otp.encode()).hexdigest()

        # Create recovery request
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=RECOVERY_EXPIRE_MINUTES
        )
        recovery = await self.repo.create_recovery_request(
            user_id=user.id,
            school_id=school_id,
            status="pending",
            expires_at=expires_at,
        )

        # Store OTP hash in Redis with TTL
        await self.redis.setex(
            f"recovery_otp:{recovery.id}",
            RECOVERY_EXPIRE_MINUTES * 60,
            otp_hash,
        )

        # Log OTP in dev + enqueue email (Phase 3E)
        logger.info(
            "Recovery OTP for %s (request %s): %s",
            email,
            recovery.id,
            otp,
        )
        try:
            from app.core.tasks import enqueue_email

            await enqueue_email(
                to=email,
                template_name="otp",
                lang="fr",
                otp_code=otp,
                expire_minutes=RECOVERY_EXPIRE_MINUTES,
            )
        except Exception:
            logger.warning("Failed to enqueue OTP email for %s", email, exc_info=True)

        # Audit
        await self.audit.log_event(
            school_id=school_id,
            actor_id=user.id,
            action_type="RECOVERY_REQUESTED",
            outcome="success",
            target_type="recovery_request",
            target_id=recovery.id,
            ip_address=ip_address,
        )

        return {
            "request_id": recovery.id,
            "message": "If the email exists, a recovery code has been sent.",
        }

    async def verify_otp(
        self,
        request_id: uuid.UUID,
        otp: str,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        """Verify recovery OTP. Transitions status: pending -> verified."""
        # Find recovery request
        recovery = await self.repo.get_recovery_request(request_id)

        if recovery is None:
            raise NotFoundError("Recovery request not found", error_code="ERR-IAM-404")

        # Check status
        if recovery.status != "pending":
            raise ConflictError(
                "Recovery request is not in pending state",
                error_code="ERR-IAM-CONFLICT",
            )

        # Check expiry
        if recovery.expires_at and recovery.expires_at < datetime.now(timezone.utc):
            raise AuthenticationError(
                "Recovery request has expired",
                error_code="ERR-IAM-EXPIRED",
            )

        # Check lockout
        if recovery.lock_until and recovery.lock_until > datetime.now(timezone.utc):
            raise RateLimitError(
                "Too many failed attempts. Please wait.",
                error_code="ERR-RATE-429",
            )

        # Verify OTP
        stored_otp_hash = await self.redis.get(f"recovery_otp:{request_id}")
        if stored_otp_hash is None:
            raise AuthenticationError(
                "Recovery OTP has expired",
                error_code="ERR-IAM-EXPIRED",
            )

        otp_hash = hashlib.sha256(otp.encode()).hexdigest()
        if otp_hash != stored_otp_hash:
            # Increment attempt counter
            recovery.attempts = (recovery.attempts or 0) + 1
            if recovery.attempts >= RECOVERY_MAX_ATTEMPTS:
                recovery.lock_until = datetime.now(timezone.utc) + timedelta(
                    minutes=RECOVERY_LOCK_MINUTES
                )
            await self.repo.save_recovery_request(recovery)

            raise AuthenticationError(
                "Invalid OTP",
                error_code="ERR-IAM-401",
            )

        # Success — transition to verified
        recovery.status = "verified"
        await self.repo.save_recovery_request(recovery)

        # Clean up OTP from Redis
        await self.redis.delete(f"recovery_otp:{request_id}")

        # Audit
        await self.audit.log_event(
            school_id=recovery.school_id,
            actor_id=recovery.user_id,
            action_type="RECOVERY_VERIFIED",
            outcome="success",
            target_type="recovery_request",
            target_id=recovery.id,
            ip_address=ip_address,
        )

        return {"message": "OTP verified successfully"}

    async def reset_password(
        self,
        request_id: uuid.UUID,
        new_password: str,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        """Reset user's password. Requires status=verified.

        Phase 2A: enforces password policy before accepting the new password.
        """
        # Find recovery request
        recovery = await self.repo.get_recovery_request(request_id)

        if recovery is None:
            raise NotFoundError("Recovery request not found", error_code="ERR-IAM-404")

        if recovery.status != "verified":
            raise ConflictError(
                "Recovery request must be verified before resetting password",
                error_code="ERR-IAM-CONFLICT",
            )

        # Phase 2A: load user to get email/name for password policy check
        user = await self.repo.get_user_by_id(recovery.user_id)

        # Phase 2A: enforce password policy
        from app.core.password_policy import password_validator

        password_validator.validate(
            new_password,
            email=user.email if user else None,
            full_name=user.full_name if user else None,
        )

        # Update password
        if user is not None:
            user.password_hash = hash_password(new_password)
            await self.repo.save_user(user)

        # Transition: verified -> reset
        recovery.status = "reset"
        await self.repo.save_recovery_request(recovery)

        # Revoke all active sessions for this user (force re-login)
        await self.repo.revoke_all_sessions(
            recovery.user_id,
            datetime.now(timezone.utc),
        )

        # Audit
        await self.audit.log_event(
            school_id=recovery.school_id,
            actor_id=recovery.user_id,
            action_type="RECOVERY_COMPLETED",
            outcome="success",
            target_type="recovery_request",
            target_id=recovery.id,
            ip_address=ip_address,
        )

        return {"message": "Password reset successfully"}


class TwoFactorService:
    """Handles TOTP 2FA operations: setup, verify-setup, disable, verify-login (Phase 2B)."""

    def __init__(self, db: AsyncSession, redis: aioredis.Redis) -> None:
        self.db = db
        self.redis = redis
        self.repo = AuthRepository(db)
        self.audit = AuditService(db)

    # ------------------------------------------------------------------
    # 2FA Setup — generate TOTP secret + QR code URI
    # ------------------------------------------------------------------
    async def setup(
        self,
        user_id: uuid.UUID,
        school_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        """Generate a new TOTP secret and provisioning URI for the user.

        Returns the secret + QR URI. 2FA is NOT yet active — user must call
        verify-setup with a valid code to activate.
        Raises ConflictError if 2FA is already enabled.
        """
        from app.core.totp import generate_totp_secret, get_provisioning_uri

        user = await self.repo.get_user_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found", error_code="ERR-IAM-404")

        if user.totp_enabled:
            raise ConflictError(
                "Two-factor authentication is already enabled",
                error_code="ERR-2FA-CONFLICT",
            )

        # Generate new secret (overwrite any pending setup)
        secret = generate_totp_secret()
        user.totp_secret = secret
        user.totp_enabled = False
        user.totp_verified_at = None
        user.backup_codes = None
        await self.repo.save_user(user)

        provisioning_uri = get_provisioning_uri(secret, user.email)

        await self.audit.log_event(
            school_id=school_id,
            actor_id=user_id,
            action_type="2FA_SETUP_STARTED",
            outcome="success",
            target_type="user",
            target_id=user_id,
            ip_address=ip_address,
        )

        return {
            "secret": secret,
            "provisioning_uri": provisioning_uri,
            "message": "Scan the QR code with your authenticator app, then verify with a code.",
        }

    # ------------------------------------------------------------------
    # 2FA Verify Setup — activate 2FA after valid code + generate backup codes
    # ------------------------------------------------------------------
    async def verify_setup(
        self,
        user_id: uuid.UUID,
        school_id: uuid.UUID,
        code: str,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        """Verify a TOTP code to activate 2FA. Returns backup codes.

        This is the second step of setup: user scans QR, enters the code,
        and if valid, 2FA is activated and 10 backup codes are generated.
        """
        from app.core.totp import (
            generate_backup_codes,
            hash_backup_codes,
            verify_totp_code,
        )

        user = await self.repo.get_user_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found", error_code="ERR-IAM-404")

        if user.totp_enabled:
            raise ConflictError(
                "Two-factor authentication is already enabled",
                error_code="ERR-2FA-CONFLICT",
            )

        if not user.totp_secret:
            raise ValidationError(
                "No 2FA setup in progress. Call /auth/2fa/setup first.",
                error_code="ERR-2FA-NO-SETUP",
            )

        # Verify the TOTP code against the pending secret
        if not verify_totp_code(user.totp_secret, code):
            raise AuthenticationError(
                "Invalid TOTP code",
                error_code="ERR-2FA-INVALID",
            )

        # Generate backup codes
        plain_codes = generate_backup_codes()
        hashed_codes = hash_backup_codes(plain_codes)

        # Activate 2FA
        user.totp_enabled = True
        user.totp_verified_at = datetime.now(timezone.utc)
        user.backup_codes = json.dumps(hashed_codes)
        await self.repo.save_user(user)

        await self.audit.log_event(
            school_id=school_id,
            actor_id=user_id,
            action_type="2FA_ENABLED",
            outcome="success",
            target_type="user",
            target_id=user_id,
            ip_address=ip_address,
        )

        return {
            "message": "Two-factor authentication enabled successfully.",
            "backup_codes": plain_codes,
        }

    # ------------------------------------------------------------------
    # 2FA Disable — deactivate 2FA (requires current TOTP or backup code)
    # ------------------------------------------------------------------
    async def disable(
        self,
        user_id: uuid.UUID,
        school_id: uuid.UUID,
        code: str,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        """Disable 2FA. Requires a valid TOTP code or backup code."""
        from app.core.totp import verify_backup_code, verify_totp_code

        user = await self.repo.get_user_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found", error_code="ERR-IAM-404")

        if not user.totp_enabled:
            raise ConflictError(
                "Two-factor authentication is not enabled",
                error_code="ERR-2FA-CONFLICT",
            )

        # Try TOTP code first, then backup code
        valid = False
        if len(code) == 6 and code.isdigit():
            valid = verify_totp_code(user.totp_secret, code)

        if not valid:
            # Try backup code
            hashed_codes = json.loads(user.backup_codes) if user.backup_codes else []
            idx = verify_backup_code(code, hashed_codes)
            if idx is not None:
                valid = True
                # Consume the backup code
                hashed_codes.pop(idx)
                user.backup_codes = json.dumps(hashed_codes)

        if not valid:
            raise AuthenticationError(
                "Invalid TOTP code or backup code",
                error_code="ERR-2FA-INVALID",
            )

        # Disable 2FA — clear all TOTP fields
        user.totp_secret = None
        user.totp_enabled = False
        user.totp_verified_at = None
        user.backup_codes = None
        await self.repo.save_user(user)

        await self.audit.log_event(
            school_id=school_id,
            actor_id=user_id,
            action_type="2FA_DISABLED",
            outcome="success",
            target_type="user",
            target_id=user_id,
            ip_address=ip_address,
        )

        return {"message": "Two-factor authentication disabled successfully."}

    # ------------------------------------------------------------------
    # 2FA Verify Login — complete login after TOTP verification
    # ------------------------------------------------------------------
    async def verify_login(
        self,
        temp_token: str,
        code: str,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        """Verify TOTP code during login flow and issue full tokens.

        Called after password check when user has totp_enabled=True.
        Uses the temp_token from Redis to retrieve login context.
        """
        from app.core.totp import verify_backup_code, verify_totp_code

        # 1. Retrieve temp token data from Redis
        temp_data_raw = await self.redis.get(f"2fa_temp:{temp_token}")
        if temp_data_raw is None:
            raise AuthenticationError(
                "Invalid or expired 2FA token",
                error_code="ERR-2FA-EXPIRED",
            )

        temp_data = json.loads(temp_data_raw)
        user_id = uuid.UUID(temp_data["user_id"])
        school_id = uuid.UUID(temp_data["school_id"])
        role = temp_data["role"]
        source = temp_data.get("source", "web")
        stored_ip = temp_data.get("ip_address")
        user_agent = temp_data.get("user_agent")
        device_name = temp_data.get("device_name")

        # 2. Load user
        user = await self.repo.get_user_by_id(user_id)
        if user is None or not user.totp_enabled:
            raise AuthenticationError(
                "Invalid 2FA state",
                error_code="ERR-2FA-INVALID",
            )

        # 3. Verify TOTP code or backup code
        valid = False
        used_backup = False
        if len(code) == 6 and code.isdigit():
            valid = verify_totp_code(user.totp_secret, code)

        if not valid:
            hashed_codes = json.loads(user.backup_codes) if user.backup_codes else []
            idx = verify_backup_code(code, hashed_codes)
            if idx is not None:
                valid = True
                used_backup = True
                # Consume the backup code
                hashed_codes.pop(idx)
                user.backup_codes = json.dumps(hashed_codes)
                await self.repo.save_user(user)

        if not valid:
            raise AuthenticationError(
                "Invalid TOTP code or backup code",
                error_code="ERR-2FA-INVALID",
            )

        # 4. Consume temp token (single use)
        await self.redis.delete(f"2fa_temp:{temp_token}")

        # 5. Create session (same logic as normal login)
        cid = get_correlation_id()
        session = await self.repo.create_session(
            user_id=user.id,
            school_id=school_id,
            source=source,
            correlation_id=uuid.UUID(cid) if cid else None,
            user_agent=user_agent[:500] if user_agent else None,
            ip_address=stored_ip[:45] if stored_ip else None,
            device_name=device_name[:200] if device_name else None,
        )

        # 6. Generate tokens
        access_token = create_access_token(user.id, role, school_id, session.id)
        refresh_token, refresh_jti = create_refresh_token(
            user.id, school_id, session.id
        )
        csrf_token = create_csrf_token()

        ttl = settings.refresh_token_expire_days * 86400
        await self.redis.setex(f"refresh_jti:{session.id}", ttl, refresh_jti)
        await self.redis.setex(f"csrf:{session.id}", ttl, csrf_token)

        # 7. Audit
        action = "AUTH_2FA_VERIFIED_BACKUP" if used_backup else "AUTH_2FA_VERIFIED"
        await self.audit.log_event(
            school_id=school_id,
            actor_id=user.id,
            action_type=action,
            outcome="success",
            target_type="session",
            target_id=session.id,
            ip_address=ip_address,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "csrf_token": csrf_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
            "session_id": session.id,
        }


class EmailVerificationService:
    """Handles email verification via OTP sent during invite consumption (Phase 2B)."""

    def __init__(self, db: AsyncSession, redis: aioredis.Redis) -> None:
        self.db = db
        self.redis = redis
        self.repo = AuthRepository(db)
        self.audit = AuditService(db)

    async def send_verification_otp(
        self,
        user_id: uuid.UUID,
        school_id: uuid.UUID,
        email: str,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        """Generate and store an email verification OTP.

        In dev: logs OTP. In production: would send via email.
        Called automatically during invite consumption.
        """
        otp = "".join([str(secrets.randbelow(10)) for _ in range(OTP_LENGTH)])
        otp_hash = hashlib.sha256(otp.encode()).hexdigest()

        await self.redis.setex(
            f"email_verify_otp:{user_id}:{school_id}",
            EMAIL_VERIFY_EXPIRE_MINUTES * 60,
            otp_hash,
        )

        logger.info(
            "Email verification OTP for %s (user %s): %s",
            email,
            user_id,
            otp,
        )

        await self.audit.log_event(
            school_id=school_id,
            actor_id=user_id,
            action_type="EMAIL_VERIFY_OTP_SENT",
            outcome="success",
            target_type="user",
            target_id=user_id,
            ip_address=ip_address,
        )

        return {"message": "Verification email sent."}

    async def verify_email(
        self,
        user_id: uuid.UUID,
        school_id: uuid.UUID,
        otp: str,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        """Verify email via OTP. Sets email_verified_at on success."""
        # Load user
        user = await self.repo.get_user_in_school(user_id, school_id)
        if user is None:
            raise NotFoundError("User not found", error_code="ERR-IAM-404")

        if user.email_verified_at is not None:
            return {"message": "Email already verified."}

        # Verify OTP
        stored_hash = await self.redis.get(f"email_verify_otp:{user_id}:{school_id}")
        if stored_hash is None:
            raise AuthenticationError(
                "Verification OTP has expired. Request a new one.",
                error_code="ERR-VERIFY-EXPIRED",
            )

        otp_hash = hashlib.sha256(otp.encode()).hexdigest()
        if otp_hash != stored_hash:
            raise AuthenticationError(
                "Invalid verification OTP",
                error_code="ERR-VERIFY-INVALID",
            )

        # Mark email as verified
        user.email_verified_at = datetime.now(timezone.utc)
        await self.repo.save_user(user)

        # Cleanup
        await self.redis.delete(f"email_verify_otp:{user_id}:{school_id}")

        await self.audit.log_event(
            school_id=school_id,
            actor_id=user_id,
            action_type="EMAIL_VERIFIED",
            outcome="success",
            target_type="user",
            target_id=user_id,
            ip_address=ip_address,
        )

        return {"message": "Email verified successfully."}
