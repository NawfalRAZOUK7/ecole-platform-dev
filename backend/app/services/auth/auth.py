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
from app.core.dependencies import AuthContext
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from app.core.middleware import get_correlation_id
from app.core.permissions import (
    ADM,
    DIR,
    PAR,
    STD,
    SUP,
    SYS,
    TCH,
    get_permissions_for_role,
)
from app.core.unit_of_work import UnitOfWork
from app.core.security import (
    create_access_token,
    create_csrf_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.core.password_policy import password_validator
from app.domain.events.auth import NewDeviceLogin, UserRegistered
from app.repositories.auth import AuthRepository
from app.repositories.auth_login_history import LoginHistoryRepository
from app.schemas.user.profile import (
    ParentProfileUpdate,
    StudentProfileUpdate,
    TeacherProfileUpdate,
)
from app.services.platform.audit import AuditService
from app.services.communication.event_dispatcher import EventDispatcher
from app.services.user.profile_loader import ProfileLoader

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
IMPERSONATION_ROLES = {ADM, DIR, SUP}


def _normalize_profile_data(role: str, profile_data: dict[str, Any]) -> dict[str, Any]:
    """Coerce role-specific registration payloads through the profile schemas."""
    if role == STD:
        return StudentProfileUpdate(**profile_data).model_dump(exclude_unset=True)
    if role == PAR:
        return ParentProfileUpdate(**profile_data).model_dump(exclude_unset=True)
    if role == TCH:
        return TeacherProfileUpdate(**profile_data).model_dump(exclude_unset=True)
    return {}


class AuthService:
    """Handles authentication operations: login, refresh, logout, profile."""

    def __init__(self, db: AsyncSession, redis: aioredis.Redis) -> None:
        self.db = db
        self.redis = redis
        self.repo = AuthRepository(db)
        self.audit = AuditService(db)
        self._dispatcher = EventDispatcher(self.db)

    def _trim_text(self, value: str | None, max_length: int) -> str | None:
        if value is None:
            return None
        return value[:max_length]

    def _session_ttl(self) -> int:
        return settings.refresh_token_expire_days * 86400

    def _ttl_from_days(self, expire_days: float | None = None) -> int:
        days = (
            expire_days
            if expire_days is not None
            else float(settings.refresh_token_expire_days)
        )
        return max(int(days * 86400), 1)

    def _claim_to_datetime(self, value: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return (
                value.astimezone(timezone.utc)
                if value.tzinfo is not None
                else value.replace(tzinfo=timezone.utc)
            )
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except (TypeError, ValueError, OSError):
            return None

    def _refresh_window(self, payload: dict[str, Any]) -> tuple[float | None, int]:
        """Return refresh expiry days and Redis TTL for sliding-window rotation."""
        issued_at = self._claim_to_datetime(payload.get("iat"))
        expires_at = self._claim_to_datetime(payload.get("exp"))
        if issued_at is None or expires_at is None or expires_at <= issued_at:
            return None, self._session_ttl()

        now = datetime.now(timezone.utc)
        total_seconds = max((expires_at - issued_at).total_seconds(), 1.0)
        remaining_seconds = max((expires_at - now).total_seconds(), 1.0)
        token_age_ratio = max((now - issued_at).total_seconds(), 0.0) / total_seconds
        extend_refresh = token_age_ratio > 0.75

        if extend_refresh:
            return float(settings.refresh_token_expire_days), self._session_ttl()
        return remaining_seconds / 86400, max(int(remaining_seconds), 1)

    def _network_fingerprint_source(self, ip_address: str | None) -> str:
        if not ip_address:
            return ""
        if "." in ip_address:
            parts = ip_address.split(".")
            return ".".join(parts[:3]) if len(parts) >= 3 else ip_address
        if ":" in ip_address:
            parts = ip_address.split(":")
            return ":".join(parts[:4]) if len(parts) >= 4 else ip_address
        return ip_address

    def _build_device_fingerprint(
        self,
        user_agent: str | None,
        ip_address: str | None,
    ) -> str | None:
        if not user_agent and not ip_address:
            return None
        raw = f"{user_agent or ''}|{self._network_fingerprint_source(ip_address)}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    async def _store_tokens(
        self,
        *,
        session_id: uuid.UUID,
        refresh_jti: str,
        csrf_token: str,
        ttl: int | None = None,
    ) -> None:
        expires_in = ttl if ttl is not None else self._session_ttl()
        await self.redis.setex(f"refresh_jti:{session_id}", expires_in, refresh_jti)
        await self.redis.setex(f"csrf:{session_id}", expires_in, csrf_token)

    async def _clear_session_tokens(self, session_id: uuid.UUID) -> None:
        await self.redis.delete(f"refresh_jti:{session_id}")
        await self.redis.delete(f"csrf:{session_id}")

    async def _issue_token_bundle(
        self,
        *,
        user_id: uuid.UUID,
        role: str,
        school_id: uuid.UUID,
        session_id: uuid.UUID,
        refresh_expire_days: float | None = None,
    ) -> dict[str, Any]:
        access_token = create_access_token(user_id, role, school_id, session_id)
        refresh_ttl = self._ttl_from_days(refresh_expire_days)
        refresh_token, refresh_jti = create_refresh_token(
            user_id,
            school_id,
            session_id,
            refresh_expire_days,
        )
        csrf_token = create_csrf_token()
        await self._store_tokens(
            session_id=session_id,
            refresh_jti=refresh_jti,
            csrf_token=csrf_token,
            ttl=refresh_ttl,
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "csrf_token": csrf_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
            "refresh_expires_in": refresh_ttl,
            "session_id": session_id,
        }

    async def _record_login_history(
        self,
        *,
        user_id: uuid.UUID | None,
        school_id: uuid.UUID,
        ip_address: str | None,
        user_agent: str | None,
        device_name: str | None,
        device_fingerprint: str | None,
        success: bool,
        failure_reason: str | None = None,
        is_new_device: bool = False,
    ) -> None:
        if user_id is None:
            return
        try:
            async with UnitOfWork(self.db) as uow:
                repo = LoginHistoryRepository(uow.session)
                record = await repo.create_login_record(
                    user_id=user_id,
                    school_id=school_id,
                    ip_address=self._trim_text(ip_address, 45),
                    user_agent=self._trim_text(user_agent, 500),
                    device_name=self._trim_text(device_name, 200),
                    device_fingerprint=device_fingerprint,
                    success=success,
                    failure_reason=failure_reason,
                    is_new_device=is_new_device,
                )
                if record is not None:
                    await uow.commit()
        except Exception:
            logger.warning(
                "Failed to record login history for user_id=%s school_id=%s",
                user_id,
                school_id,
                exc_info=True,
            )

    async def _dispatch_event(self, event) -> None:
        try:
            await self._dispatcher.dispatch(event)
        except Exception:
            logger.exception("Failed to dispatch %s", type(event).__name__)

    async def _audit_login_denial(
        self,
        *,
        school_id: uuid.UUID,
        actor_id: uuid.UUID | None,
        action_type: str,
        error_code: str,
        ip_address: str | None,
    ) -> None:
        """Best-effort audit for denied login attempts.

        Failed logins can legitimately target a school UUID that does not exist.
        In that case we still return a normal auth error and skip the audit row,
        rather than turning the denial into a 500 due to the FK on audit_logs.
        """
        if actor_id is None:
            school = await self.repo.get_school_by_id(school_id)
            if school is None:
                logger.warning(
                    "Skipping denied login audit for unknown school_id=%s action=%s",
                    school_id,
                    action_type,
                )
                return

        try:
            await self.audit.log_event(
                school_id=school_id,
                actor_id=actor_id,
                action_type=action_type,
                outcome="denied",
                error_code=error_code,
                ip_address=ip_address,
            )
        except Exception:
            logger.warning(
                "Failed to audit denied login for user_id=%s school_id=%s action=%s",
                actor_id,
                school_id,
                action_type,
                exc_info=True,
            )

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
        device_fingerprint = self._build_device_fingerprint(user_agent, ip_address)
        user = await self.repo.get_user_by_email(email, school_id)

        # Account lockout check (Phase 11)
        # Always query DB even if user doesn't exist to prevent timing-based user enumeration
        if settings.account_lockout_enabled:
            failed_attempts = await self.repo.count_failed_login_attempts(
                email,
                user_id=user.id if user else None,
                minutes=settings.account_lockout_duration_minutes,
            )
            if failed_attempts >= settings.account_lockout_max_attempts:
                await self._record_login_history(
                    user_id=user.id if user else None,
                    school_id=school_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    device_name=device_name,
                    device_fingerprint=device_fingerprint,
                    success=False,
                    failure_reason="account_locked",
                )
                await self._audit_login_denial(
                    school_id=school_id,
                    actor_id=user.id if user else None,
                    action_type="AUTH_ACCOUNT_LOCKED",
                    error_code="ERR-IAM-403",
                    ip_address=ip_address,
                )
                raise AuthorizationError(
                    f"Account locked due to too many failed login attempts. Please try again in {settings.account_lockout_duration_minutes} minutes.",
                    error_code="ERR-IAM-403",
                )

        # 1. Rate limiting — max 5 failed attempts per email per 15 minutes
        rate_key = f"login_attempts:{email}:{school_id}"
        attempt_count = await self.redis.get(rate_key)
        if attempt_count and int(attempt_count) >= RATE_LIMIT_MAX_ATTEMPTS:
            await self._record_login_history(
                user_id=user.id if user else None,
                school_id=school_id,
                ip_address=ip_address,
                user_agent=user_agent,
                device_name=device_name,
                device_fingerprint=device_fingerprint,
                success=False,
                failure_reason="rate_limited",
            )
            await self._audit_login_denial(
                school_id=school_id,
                actor_id=user.id if user else None,
                action_type="AUTH_LOGIN_RATE_LIMITED",
                error_code="ERR-RATE-429",
                ip_address=ip_address,
            )
            raise RateLimitError(
                "Too many login attempts. Please try again later.",
                error_code="ERR-RATE-429",
            )

        if user is None or not verify_password(password, user.password_hash):
            # Increment failed attempts
            pipe = self.redis.pipeline()
            pipe.incr(rate_key)
            pipe.expire(rate_key, RATE_LIMIT_WINDOW_SECONDS)
            await pipe.execute()

            # Record failed login attempt (Phase 11)
            if settings.account_lockout_enabled:
                await self.repo.create_failed_login_attempt(
                    user_id=user.id if user else None,
                    school_id=school_id,
                    email=email,
                    ip_address=self._trim_text(ip_address, 45) if ip_address else None,
                    user_agent=self._trim_text(user_agent, 500) if user_agent else None,
                    failure_reason="wrong_password",
                )

            await self._record_login_history(
                user_id=user.id if user else None,
                school_id=school_id,
                ip_address=ip_address,
                user_agent=user_agent,
                device_name=device_name,
                device_fingerprint=device_fingerprint,
                success=False,
                failure_reason="wrong_password",
            )
            await self._audit_login_denial(
                school_id=school_id,
                actor_id=user.id if user else None,
                action_type="AUTH_LOGIN_FAILED",
                error_code="ERR-IAM-401",
                ip_address=ip_address,
            )
            raise AuthenticationError(
                "Invalid email or password",
                error_code="ERR-IAM-401",
            )

        # 3. Check user status is active
        if user.status != "active":
            await self._record_login_history(
                user_id=user.id,
                school_id=school_id,
                ip_address=ip_address,
                user_agent=user_agent,
                device_name=device_name,
                device_fingerprint=device_fingerprint,
                success=False,
                failure_reason="inactive",
            )
            try:
                await self.audit.log_event(
                    school_id=school_id,
                    actor_id=user.id,
                    action_type="AUTH_LOGIN_INACTIVE",
                    outcome="denied",
                    error_code="ERR-IAM-403",
                    ip_address=ip_address,
                )
            except Exception:
                logger.warning(
                    "Failed to audit inactive login for user_id=%s school_id=%s",
                    user.id,
                    school_id,
                    exc_info=True,
                )
            raise AuthorizationError(
                "Account is not active",
                error_code="ERR-IAM-403",
            )

        # 4. Check active membership for user + school
        membership = await self.repo.get_membership(user.id, school_id)
        if membership is None:
            await self._record_login_history(
                user_id=user.id,
                school_id=school_id,
                ip_address=ip_address,
                user_agent=user_agent,
                device_name=device_name,
                device_fingerprint=device_fingerprint,
                success=False,
                failure_reason="no_membership",
            )
            try:
                await self.audit.log_event(
                    school_id=school_id,
                    actor_id=user.id,
                    action_type="AUTH_LOGIN_NO_MEMBERSHIP",
                    outcome="denied",
                    error_code="ERR-IAM-404",
                    ip_address=ip_address,
                )
            except Exception:
                logger.warning(
                    "Failed to audit no-membership login for user_id=%s school_id=%s",
                    user.id,
                    school_id,
                    exc_info=True,
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
                    "device_fingerprint": device_fingerprint,
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
        new_device_event = None
        async with UnitOfWork(self.db) as uow:
            repo = AuthRepository(uow.session)
            audit = AuditService(uow.session)
            login_history_repo = LoginHistoryRepository(uow.session)
            revoked_session_id = None
            active_count = await repo.count_active_sessions(user.id, school_id)
            if active_count >= settings.max_sessions_per_user:
                oldest = await repo.get_oldest_active_session(user.id, school_id)
                if oldest is not None:
                    revoked_session_id = oldest.id
                    await repo.revoke_session(oldest.id, datetime.now(timezone.utc))

            known_fingerprints = await login_history_repo.get_device_fingerprints(
                user.id
            )
            is_new_device = bool(
                device_fingerprint and device_fingerprint not in known_fingerprints
            )
            session = await repo.create_session(
                user_id=user.id,
                school_id=school_id,
                source=source,
                correlation_id=uuid.UUID(cid) if cid else None,
                user_agent=self._trim_text(user_agent, 500),
                ip_address=self._trim_text(ip_address, 45),
                device_name=self._trim_text(device_name, 200),
            )
            await login_history_repo.create_login_record(
                user_id=user.id,
                school_id=school_id,
                ip_address=self._trim_text(ip_address, 45),
                user_agent=self._trim_text(user_agent, 500),
                device_name=self._trim_text(device_name, 200),
                device_fingerprint=device_fingerprint,
                success=True,
                is_new_device=is_new_device,
            )
            if revoked_session_id is not None:
                await audit.log_event(
                    school_id=school_id,
                    actor_id=user.id,
                    action_type="AUTH_SESSION_LIMIT_REACHED",
                    outcome="success",
                    target_type="session",
                    target_id=revoked_session_id,
                    ip_address=ip_address,
                )
            await audit.log_event(
                school_id=school_id,
                actor_id=user.id,
                action_type="AUTH_SESSION_OPENED",
                outcome="success",
                target_type="session",
                target_id=session.id,
                ip_address=ip_address,
            )
            await uow.commit()
            if is_new_device:
                new_device_event = NewDeviceLogin(
                    school_id=school_id,
                    actor_id=user.id,
                    user_id=user.id,
                    device_name=self._trim_text(device_name, 200),
                    ip_address=self._trim_text(ip_address, 45),
                    user_agent=self._trim_text(user_agent, 500),
                )

        token_bundle = await self._issue_token_bundle(
            user_id=user.id,
            role=role,
            school_id=school_id,
            session_id=session.id,
        )

        # 10. Clear rate limit on successful login
        await self.redis.delete(rate_key)

        # Suspicious activity detection (Phase 11)
        is_new_location = False
        if settings.suspicious_activity_enabled and ip_address:
            from app.services.platform.suspicious_activity import (
                SuspiciousActivityService,
            )

            suspicious_service = SuspiciousActivityService()

            # Get location info
            location_info = suspicious_service.get_ip_location(ip_address)

            # Check if new location
            known_locations = await self.repo.get_known_locations_by_user(user.id)
            is_new_location = suspicious_service.is_new_location(
                known_locations,
                location_info["country_code"],
                location_info["city"],
            )

            # Record or update known location
            known_location = await self.repo.get_known_location_by_user_ip(
                user.id, ip_address
            )
            if known_location:
                known_location.last_seen_at = datetime.now(timezone.utc)
                known_location.country_code = location_info["country_code"]
                known_location.city = location_info["city"]
                known_location.region = location_info["region"]
                await self.repo.update_known_location(known_location)
            else:
                await self.repo.create_known_location(
                    user_id=user.id,
                    school_id=school_id,
                    ip_address=ip_address,
                    country_code=location_info["country_code"],
                    city=location_info["city"],
                    region=location_info["region"],
                    last_seen_at=datetime.now(timezone.utc),
                    is_suspicious=is_new_location,
                )

            # Check if new device
            known_devices = await self.repo.get_known_devices_by_user(user.id)
            is_new_device = suspicious_service.is_new_device(
                known_devices,
                device_fingerprint,
            )

            # Record or update known device
            known_device = await self.repo.get_known_device_by_user_fingerprint(
                user.id, device_fingerprint
            )
            if known_device:
                known_device.last_seen_at = datetime.now(timezone.utc)
                known_device.device_name = device_name
                known_device.user_agent = user_agent
                await self.repo.update_known_device(known_device)
            else:
                await self.repo.create_known_device(
                    user_id=user.id,
                    school_id=school_id,
                    device_fingerprint=device_fingerprint,
                    device_name=device_name,
                    user_agent=user_agent,
                    last_seen_at=datetime.now(timezone.utc),
                    is_suspicious=is_new_device,
                )

        if new_device_event is not None:
            await self._dispatch_event(new_device_event)

        return token_bundle

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

        async with UnitOfWork(self.db) as uow:
            repo = AuthRepository(uow.session)
            audit = AuditService(uow.session)
            profile_loader = ProfileLoader(uow.session)

            # 4. Create user
            user = await repo.create_user(
                email=email,
                full_name=full_name,
                phone=phone,
                password_hash=hash_password(password),
                status="active",
                school_id=school_id,
            )

            # 5. Create membership
            await repo.create_membership(
                user_id=user.id,
                school_id=school_id,
                role_code=role,
                status="active",
            )

            # 6. Create role-specific profile
            profile = await profile_loader.ensure_profile(user.id, school_id, role)
            if profile is not None:
                for field, value in profile_data.items():
                    setattr(profile, field, value)

            # 7. Auto-create parent_child_link if code has target_student_id
            if role == PAR and invite.target_student_id:
                await repo.create_parent_child_link(
                    parent_user_id=user.id,
                    child_user_id=invite.target_student_id,
                    school_id=school_id,
                    status="active",
                    linked_at=datetime.now(timezone.utc),
                    linked_by=invite.issuer_user_id,
                )

            # 8. Consume the invitation code
            await repo.consume_invitation(
                invite.id,
                user_id=user.id,
                consumed_at=datetime.now(timezone.utc),
            )

            # 9. Create session and audit registration
            cid = get_correlation_id()
            session = await repo.create_session(
                user_id=user.id,
                school_id=school_id,
                source=source,
                correlation_id=uuid.UUID(cid) if cid else None,
                user_agent=user_agent[:500] if user_agent else None,
                ip_address=ip_address[:45] if ip_address else None,
                device_name=device_name[:200] if device_name else None,
            )
            await audit.log_event(
                school_id=school_id,
                actor_id=user.id,
                action_type="USER_REGISTERED",
                outcome="success",
                target_type="user",
                target_id=user.id,
                ip_address=ip_address,
            )
            await uow.commit()

        try:
            await self._dispatcher.dispatch(
                UserRegistered(
                    school_id=school_id,
                    actor_id=user.id,
                    user_id=user.id,
                    role=role,
                )
            )
        except Exception:
            logger.exception("Failed to dispatch UserRegistered for %s", user.id)

        access_token = create_access_token(user.id, role, school_id, session.id)
        refresh_token, refresh_jti = create_refresh_token(
            user.id, school_id, session.id
        )
        csrf_token = create_csrf_token()
        refresh_ttl = self._session_ttl()

        # Store refresh JTI and CSRF in Redis
        await self.redis.setex(
            f"refresh_jti:{session.id}",
            refresh_ttl,
            refresh_jti,
        )
        await self.redis.setex(
            f"csrf:{session.id}",
            refresh_ttl,
            csrf_token,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "csrf_token": csrf_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
            "refresh_expires_in": refresh_ttl,
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

        # 6. Issue new tokens (rotation + sliding window)
        refresh_expire_days, ttl = self._refresh_window(payload)
        new_access = create_access_token(user_id, role, school_id, session_id)
        new_refresh, new_jti = create_refresh_token(
            user_id,
            school_id,
            session_id,
            refresh_expire_days,
        )
        new_csrf = create_csrf_token()

        # 7. Update Redis with new JTI and CSRF
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
            "refresh_expires_in": ttl,
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
        profile_loader = ProfileLoader(self.db)
        # /auth/me keeps its existing response shape, but now sources role-profile
        # composition through ProfileLoader rather than scattered direct queries.
        await profile_loader.load(
            user_id,
            [
                membership.role_code
                for membership in memberships
                if membership.school_id == school_id
            ],
        )

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

    async def list_login_history(
        self,
        *,
        target_user_id: uuid.UUID,
        auth: AuthContext,
        limit: int = 20,
        cursor: str | None = None,
    ) -> tuple[list[dict[str, Any]], str | None, bool]:
        """List login history for the current user or an allowed admin target."""
        if target_user_id != auth.user_id and auth.role not in IMPERSONATION_ROLES:
            raise AuthorizationError(
                "Insufficient permissions to view another user's login history",
                error_code="ERR-AUTHZ-001",
            )

        target_user = await self.repo.get_user_in_school(target_user_id, auth.school_id)
        if target_user is None:
            raise NotFoundError("User not found", error_code="ERR-IAM-404")

        history_repo = LoginHistoryRepository(self.db)
        rows, next_cursor, has_more = await history_repo.list_user_login_history(
            target_user_id,
            limit,
            cursor,
        )
        return (
            [
                {
                    "id": row.id,
                    "user_id": row.user_id,
                    "school_id": row.school_id,
                    "ip_address": row.ip_address,
                    "user_agent": row.user_agent,
                    "device_name": row.device_name,
                    "device_fingerprint": row.device_fingerprint,
                    "city": row.city,
                    "country": row.country,
                    "success": row.success,
                    "failure_reason": row.failure_reason,
                    "is_new_device": row.is_new_device,
                    "created_at": row.created_at.isoformat()
                    if row.created_at
                    else None,
                }
                for row in rows
            ],
            next_cursor,
            has_more,
        )

    async def impersonate(
        self,
        target_user_id: uuid.UUID,
        admin_auth: AuthContext,
        *,
        source: str = "impersonation",
        ip_address: str | None = None,
        user_agent: str | None = None,
        device_name: str | None = None,
    ) -> dict[str, Any]:
        """Create a shadow session for an admin to impersonate another user."""
        if admin_auth.role not in IMPERSONATION_ROLES:
            raise AuthorizationError(
                "Only ADM, DIR, or SUP can impersonate users",
                error_code="ERR-AUTHZ-001",
            )
        if target_user_id == admin_auth.user_id:
            raise ConflictError(
                "Cannot impersonate your own account",
                error_code="ERR-IAM-CONFLICT",
            )

        target_user = await self.repo.get_user_in_school(
            target_user_id, admin_auth.school_id
        )
        if target_user is None:
            raise NotFoundError("User not found", error_code="ERR-IAM-404")

        target_membership = await self.repo.get_membership(
            target_user_id,
            admin_auth.school_id,
        )
        if target_membership is None:
            raise NotFoundError(
                "Target user has no active membership",
                error_code="ERR-IAM-404",
            )
        if target_membership.role_code in {SUP, SYS}:
            raise AuthorizationError(
                "Cannot impersonate SUP or SYS accounts",
                error_code="ERR-AUTHZ-001",
            )

        shadow_session = None
        async with UnitOfWork(self.db) as uow:
            repo = AuthRepository(uow.session)
            audit = AuditService(uow.session)
            shadow_session = await repo.create_session(
                user_id=target_user.id,
                school_id=admin_auth.school_id,
                source=source,
                correlation_id=admin_auth.session_id,
                user_agent=self._trim_text(user_agent, 500),
                ip_address=self._trim_text(ip_address, 45),
                device_name=self._trim_text(device_name, 200),
                impersonator_id=admin_auth.user_id,
            )
            await audit.log_event(
                school_id=admin_auth.school_id,
                actor_id=admin_auth.user_id,
                action_type="ADMIN_IMPERSONATION_START",
                outcome="success",
                target_type="session",
                target_id=shadow_session.id,
                entity_after={
                    "impersonator_id": str(admin_auth.user_id),
                    "target_user_id": str(target_user.id),
                    "target_role": target_membership.role_code,
                    "original_session_id": str(admin_auth.session_id),
                },
                ip_address=ip_address,
            )
            await uow.commit()

        token_bundle = await self._issue_token_bundle(
            user_id=target_user.id,
            role=target_membership.role_code,
            school_id=admin_auth.school_id,
            session_id=shadow_session.id,
        )
        token_bundle["impersonation_active"] = True
        return token_bundle

    async def stop_impersonation(
        self,
        session_id: uuid.UUID,
        *,
        source: str = "impersonation_return",
        ip_address: str | None = None,
        user_agent: str | None = None,
        device_name: str | None = None,
    ) -> dict[str, Any]:
        """End an impersonation session and return tokens for the impersonator."""
        current_session = await self.repo.get_session_by_id(
            session_id, active_only=True
        )
        if current_session is None or current_session.impersonator_id is None:
            raise AuthorizationError(
                "Current session is not an impersonation session",
                error_code="ERR-AUTHZ-001",
            )

        restored_session = None
        impersonator_id = current_session.impersonator_id
        original_session_id = current_session.correlation_id
        admin_role = None

        async with UnitOfWork(self.db) as uow:
            repo = AuthRepository(uow.session)
            audit = AuditService(uow.session)
            shadow_session = await repo.get_session_by_id(session_id, active_only=True)
            if shadow_session is None or shadow_session.impersonator_id is None:
                raise AuthorizationError(
                    "Current session is not an impersonation session",
                    error_code="ERR-AUTHZ-001",
                )

            admin_membership = await repo.get_membership(
                shadow_session.impersonator_id,
                shadow_session.school_id,
            )
            if admin_membership is None:
                raise AuthenticationError(
                    "Impersonator membership no longer exists",
                    error_code="ERR-IAM-401",
                )
            admin_role = admin_membership.role_code

            if original_session_id is not None:
                candidate = await repo.get_session_by_id(
                    original_session_id, active_only=True
                )
                if (
                    candidate is not None
                    and candidate.user_id == shadow_session.impersonator_id
                    and candidate.school_id == shadow_session.school_id
                    and candidate.impersonator_id is None
                ):
                    restored_session = candidate

            if restored_session is None:
                cid = get_correlation_id()
                restored_session = await repo.create_session(
                    user_id=shadow_session.impersonator_id,
                    school_id=shadow_session.school_id,
                    source=source,
                    correlation_id=uuid.UUID(cid) if cid else None,
                    user_agent=self._trim_text(user_agent, 500),
                    ip_address=self._trim_text(ip_address, 45),
                    device_name=self._trim_text(device_name, 200),
                )

            await repo.revoke_session(shadow_session.id, datetime.now(timezone.utc))
            await audit.log_event(
                school_id=shadow_session.school_id,
                actor_id=shadow_session.impersonator_id,
                action_type="ADMIN_IMPERSONATION_END",
                outcome="success",
                target_type="session",
                target_id=shadow_session.id,
                entity_after={
                    "impersonator_id": str(shadow_session.impersonator_id),
                    "impersonated_user_id": str(shadow_session.user_id),
                    "restored_session_id": str(restored_session.id),
                },
                ip_address=ip_address,
            )
            await uow.commit()

        await self._clear_session_tokens(session_id)
        token_bundle = await self._issue_token_bundle(
            user_id=impersonator_id,
            role=admin_role,
            school_id=current_session.school_id,
            session_id=restored_session.id,
        )
        token_bundle["impersonation_active"] = False
        return token_bundle

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
        if session.user_id != actor_user_id and actor_role != ADM:
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

        # Check password history (Phase 11)
        password_history = await self.repo.get_password_history_by_user(
            user_id,
            limit=settings.password_history_limit,
        )
        for history in password_history:
            if verify_password(new_password, history.password_hash):
                raise ValidationError(
                    "Password has been used recently. Please choose a different password.",
                    error_code="ERR-IAM-409",
                )

        # Hash and update password
        new_password_hash = hash_password(new_password)
        user.password_hash = new_password_hash
        await self.repo.save_user(user)

        # Store new password in history
        await self.repo.create_password_history(
            user_id=user_id,
            school_id=school_id,
            password_hash=new_password_hash,
        )

        # Clean up old password history entries
        await self.repo.delete_old_password_history(
            user_id,
            keep_count=settings.password_history_limit,
        )

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
            if role_target != PAR:
                from app.core.exceptions import ValidationError

                raise ValidationError(
                    "target_student_id is only valid for PAR invitations",
                    error_code="ERR-VAL-001",
                )
            # Check student exists in the same school with STD role
            student = await self.repo.get_student_in_school(
                target_student_id, school_id
            )
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

        # In dev/test mode, return OTP in response for local automation only.
        result = {
            "request_id": recovery.id,
            "message": "If the email exists, a recovery code has been sent.",
        }
        if settings.app_env != "production" and getattr(
            settings, "debug_reveal_otp", False
        ):
            result["otp"] = otp  # Only when explicitly enabled for testing

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

        return result

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

        # Check password history (Phase 11)
        password_history = await self.repo.get_password_history_by_user(
            recovery.user_id,
            limit=settings.password_history_limit,
        )
        for history in password_history:
            if verify_password(new_password, history.password_hash):
                raise ValidationError(
                    "Password has been used recently. Please choose a different password.",
                    error_code="ERR-IAM-409",
                )

        # Update password
        new_password_hash = hash_password(new_password)
        if user is not None:
            user.password_hash = new_password_hash
            await self.repo.save_user(user)

        # Store new password in history
        await self.repo.create_password_history(
            user_id=recovery.user_id,
            school_id=recovery.school_id,
            password_hash=new_password_hash,
        )

        # Clean up old password history entries
        await self.repo.delete_old_password_history(
            recovery.user_id,
            keep_count=settings.password_history_limit,
        )

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
        device_fingerprint = temp_data.get("device_fingerprint")
        auth_service = AuthService(self.db, self.redis)

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

        if not valid:
            await auth_service._record_login_history(
                user_id=user.id,
                school_id=school_id,
                ip_address=stored_ip,
                user_agent=user_agent,
                device_name=device_name,
                device_fingerprint=device_fingerprint,
                success=False,
                failure_reason="invalid_2fa",
            )
            await self.audit.log_event(
                school_id=school_id,
                actor_id=user.id,
                action_type="AUTH_2FA_FAILED",
                outcome="denied",
                error_code="ERR-2FA-INVALID",
                ip_address=ip_address,
            )
            raise AuthenticationError(
                "Invalid TOTP code or backup code",
                error_code="ERR-2FA-INVALID",
            )

        # 4. Create session (same logic as normal login)
        cid = get_correlation_id()
        new_device_event = None
        async with UnitOfWork(self.db) as uow:
            repo = AuthRepository(uow.session)
            audit = AuditService(uow.session)
            login_history_repo = LoginHistoryRepository(uow.session)
            if used_backup:
                await repo.save_user(user)

            revoked_session_id = None
            active_count = await repo.count_active_sessions(user.id, school_id)
            if active_count >= settings.max_sessions_per_user:
                oldest = await repo.get_oldest_active_session(user.id, school_id)
                if oldest is not None:
                    revoked_session_id = oldest.id
                    await repo.revoke_session(oldest.id, datetime.now(timezone.utc))

            known_fingerprints = await login_history_repo.get_device_fingerprints(
                user.id
            )
            is_new_device = bool(
                device_fingerprint and device_fingerprint not in known_fingerprints
            )
            session = await repo.create_session(
                user_id=user.id,
                school_id=school_id,
                source=source,
                correlation_id=uuid.UUID(cid) if cid else None,
                user_agent=auth_service._trim_text(user_agent, 500),
                ip_address=auth_service._trim_text(stored_ip, 45),
                device_name=auth_service._trim_text(device_name, 200),
            )
            await login_history_repo.create_login_record(
                user_id=user.id,
                school_id=school_id,
                ip_address=auth_service._trim_text(stored_ip, 45),
                user_agent=auth_service._trim_text(user_agent, 500),
                device_name=auth_service._trim_text(device_name, 200),
                device_fingerprint=device_fingerprint,
                success=True,
                is_new_device=is_new_device,
            )
            if revoked_session_id is not None:
                await audit.log_event(
                    school_id=school_id,
                    actor_id=user.id,
                    action_type="AUTH_SESSION_LIMIT_REACHED",
                    outcome="success",
                    target_type="session",
                    target_id=revoked_session_id,
                    ip_address=ip_address,
                )
            if is_new_device:
                new_device_event = NewDeviceLogin(
                    school_id=school_id,
                    actor_id=user.id,
                    user_id=user.id,
                    device_name=auth_service._trim_text(device_name, 200),
                    ip_address=auth_service._trim_text(stored_ip, 45),
                    user_agent=auth_service._trim_text(user_agent, 500),
                )
            action = "AUTH_2FA_VERIFIED_BACKUP" if used_backup else "AUTH_2FA_VERIFIED"
            await audit.log_event(
                school_id=school_id,
                actor_id=user.id,
                action_type=action,
                outcome="success",
                target_type="session",
                target_id=session.id,
                ip_address=ip_address,
            )
            await uow.commit()

        # 5. Consume temp token only after the session transaction succeeds
        await self.redis.delete(f"2fa_temp:{temp_token}")

        token_bundle = await auth_service._issue_token_bundle(
            user_id=user.id,
            role=role,
            school_id=school_id,
            session_id=session.id,
        )
        if new_device_event is not None:
            await auth_service._dispatch_event(new_device_event)
        return token_bundle


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

        result = {"message": "Verification email sent."}
        if settings.app_env != "production" and getattr(
            settings, "debug_reveal_otp", False
        ):
            result["otp"] = otp
        return result

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
