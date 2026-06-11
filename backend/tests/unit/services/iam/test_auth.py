"""Unit tests for app/services/auth/auth.py — branch coverage expansion.

Covers: helper functions, AuthService remaining branches (register, logout,
get_profile, list_sessions, list_login_history, revoke_session, change_password,
impersonation edge cases), InvitationService, RecoveryService, TwoFactorService,
EmailVerificationService, security non-regression.
"""

from __future__ import annotations

import hashlib
import json
import sys
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import app.services.auth.auth as auth_module
from app.core.dependencies import AuthContext
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from app.core.permissions import ADM, PAR, STD, TCH
from app.services.auth.auth import (
    AuthService,
    EmailVerificationService,
    InvitationService,
    RecoveryService,
    TwoFactorService,
    _normalize_profile_data,
)


# ---------------------------------------------------------------------------
# Fake infrastructure (mirrors test_auth_service.py helpers)
# ---------------------------------------------------------------------------


class FakePipeline:
    def __init__(self, redis):
        self.redis = redis
        self.ops: list[tuple] = []

    def incr(self, key: str):
        self.ops.append(("incr", key))
        return self

    def expire(self, key: str, ttl: int):
        self.ops.append(("expire", key, ttl))
        return self

    async def execute(self):
        for op in self.ops:
            if op[0] == "incr":
                self.redis.store[op[1]] = int(self.redis.store.get(op[1], 0)) + 1
            elif op[0] == "expire":
                self.redis.expirations[op[1]] = op[2]


class FakeRedis:
    def __init__(self):
        self.store: dict = {}
        self.expirations: dict = {}

    async def get(self, key: str):
        return self.store.get(key)

    async def setex(self, key: str, ttl: int, value):
        self.store[key] = value
        self.expirations[key] = ttl

    async def set(self, key: str, value, ex: int = None):
        self.store[key] = value
        if ex:
            self.expirations[key] = ex

    async def delete(self, *keys: str):
        for k in keys:
            self.store.pop(k, None)

    def pipeline(self):
        return FakePipeline(self)


class FakeUnitOfWork:
    def __init__(self):
        self.session = AsyncMock()
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False

    async def commit(self):
        self.committed = True


def make_auth_context(role: str = ADM, user_id=None, school_id=None) -> AuthContext:
    return AuthContext(
        user_id=user_id or uuid.uuid4(),
        role=role,
        school_id=school_id or uuid.uuid4(),
        session_id=uuid.uuid4(),
        permissions=set(),
    )


def make_user(
    school_id=None, *, status="active", totp_enabled=False, email_verified_at=None
):
    return SimpleNamespace(
        id=uuid.uuid4(),
        email="user@test.example",
        password_hash="hashed",
        full_name="Test User",
        status=status,
        school_id=school_id or uuid.uuid4(),
        totp_enabled=totp_enabled,
        totp_secret=None,
        backup_codes=None,
        email_verified_at=email_verified_at,
    )


def setup_service():
    redis = FakeRedis()
    svc = AuthService(AsyncMock(), redis)
    svc.repo = AsyncMock()
    svc.audit = AsyncMock()
    svc._dispatcher = AsyncMock()
    svc._dispatch_event = AsyncMock()
    return svc, redis


def patch_uow(monkeypatch):
    repo_in_uow = AsyncMock()
    audit_in_uow = AsyncMock()
    login_history_in_uow = AsyncMock()
    uow = FakeUnitOfWork()
    monkeypatch.setattr(auth_module, "UnitOfWork", lambda _db: uow)
    monkeypatch.setattr(auth_module, "AuthRepository", lambda _s: repo_in_uow)
    monkeypatch.setattr(auth_module, "AuditService", lambda _s: audit_in_uow)
    monkeypatch.setattr(
        auth_module, "LoginHistoryRepository", lambda _s: login_history_in_uow
    )
    return repo_in_uow, audit_in_uow, login_history_in_uow, uow


# ---------------------------------------------------------------------------
# _normalize_profile_data
# ---------------------------------------------------------------------------


class TestNormalizeProfileData:
    def test_std_role_returns_empty_when_no_fields(self):
        result = _normalize_profile_data(STD, {})
        assert isinstance(result, dict)

    def test_par_role_returns_empty_when_no_fields(self):
        result = _normalize_profile_data(PAR, {})
        assert isinstance(result, dict)

    def test_tch_role_returns_empty_when_no_fields(self):
        result = _normalize_profile_data(TCH, {})
        assert isinstance(result, dict)

    def test_unknown_role_returns_empty_dict(self):
        result = _normalize_profile_data("UNKNOWN", {"foo": "bar"})
        assert result == {}

    def test_adm_role_returns_empty_dict(self):
        result = _normalize_profile_data(ADM, {"anything": "ignored"})
        assert result == {}


# ---------------------------------------------------------------------------
# AuthService._trim_text
# ---------------------------------------------------------------------------


class TestTrimText:
    def test_none_returns_none(self):
        svc, _ = setup_service()
        assert svc._trim_text(None, 100) is None

    def test_short_string_unchanged(self):
        svc, _ = setup_service()
        assert svc._trim_text("hello", 100) == "hello"

    def test_long_string_truncated(self):
        svc, _ = setup_service()
        assert svc._trim_text("abcdef", 3) == "abc"


# ---------------------------------------------------------------------------
# AuthService._ttl_from_days
# ---------------------------------------------------------------------------


class TestTtlFromDays:
    def test_none_uses_settings_refresh_days(self, monkeypatch):
        svc, _ = setup_service()
        monkeypatch.setattr(
            auth_module.settings, "refresh_token_expire_days", 1, raising=False
        )
        assert svc._ttl_from_days(None) == 86400

    def test_explicit_days(self):
        svc, _ = setup_service()
        assert svc._ttl_from_days(2.0) == 172800

    def test_tiny_value_clamped_to_one(self):
        svc, _ = setup_service()
        assert svc._ttl_from_days(0.000001) == 1


# ---------------------------------------------------------------------------
# AuthService._claim_to_datetime
# ---------------------------------------------------------------------------


class TestClaimToDatetime:
    def test_none_returns_none(self):
        svc, _ = setup_service()
        assert svc._claim_to_datetime(None) is None

    def test_datetime_with_tz(self):
        svc, _ = setup_service()
        dt = datetime(2024, 1, 1, tzinfo=timezone.utc)
        result = svc._claim_to_datetime(dt)
        assert result.tzinfo is not None

    def test_datetime_without_tz(self):
        svc, _ = setup_service()
        dt = datetime(2024, 1, 1)
        result = svc._claim_to_datetime(dt)
        assert result.tzinfo == timezone.utc

    def test_float_timestamp(self):
        svc, _ = setup_service()
        ts = datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp()
        result = svc._claim_to_datetime(ts)
        assert result is not None
        assert result.year == 2024

    def test_invalid_value_returns_none(self):
        svc, _ = setup_service()
        assert svc._claim_to_datetime("not-a-date") is None


# ---------------------------------------------------------------------------
# AuthService._refresh_window
# ---------------------------------------------------------------------------


class TestRefreshWindow:
    def test_none_iat_returns_defaults(self):
        svc, _ = setup_service()
        expire_days, ttl = svc._refresh_window({})
        assert expire_days is None

    def test_expired_at_before_issued_returns_defaults(self):
        svc, _ = setup_service()
        now = datetime.now(timezone.utc)
        payload = {
            "iat": now.timestamp(),
            "exp": (now - timedelta(hours=1)).timestamp(),
        }
        expire_days, _ = svc._refresh_window(payload)
        assert expire_days is None

    def test_old_token_extends_refresh(self, monkeypatch):
        svc, _ = setup_service()
        monkeypatch.setattr(
            auth_module.settings, "refresh_token_expire_days", 30, raising=False
        )
        now = datetime.now(timezone.utc)
        issued = now - timedelta(days=25)  # 83% of 30-day window
        expires = issued + timedelta(days=30)
        payload = {"iat": issued.timestamp(), "exp": expires.timestamp()}
        expire_days, _ = svc._refresh_window(payload)
        assert expire_days == 30.0

    def test_fresh_token_preserves_remaining_ttl(self):
        svc, _ = setup_service()
        now = datetime.now(timezone.utc)
        issued = now - timedelta(days=1)  # 3% of 30-day window
        expires = issued + timedelta(days=30)
        payload = {"iat": issued.timestamp(), "exp": expires.timestamp()}
        expire_days, _ = svc._refresh_window(payload)
        assert expire_days is not None
        assert expire_days < 30.0


# ---------------------------------------------------------------------------
# AuthService._network_fingerprint_source
# ---------------------------------------------------------------------------


class TestNetworkFingerprintSource:
    def test_empty_string_returns_empty(self):
        svc, _ = setup_service()
        assert svc._network_fingerprint_source("") == ""

    def test_none_returns_empty(self):
        svc, _ = setup_service()
        assert svc._network_fingerprint_source(None) == ""

    def test_ipv4_returns_subnet(self):
        svc, _ = setup_service()
        assert svc._network_fingerprint_source("192.168.1.42") == "192.168.1"

    def test_ipv4_short_returns_full(self):
        svc, _ = setup_service()
        result = svc._network_fingerprint_source("1.2")
        assert result == "1.2"

    def test_ipv6_returns_first_four_groups(self):
        svc, _ = setup_service()
        result = svc._network_fingerprint_source("2001:db8:85a3::8a2e:370:7334")
        assert result.count(":") >= 3

    def test_ipv6_short_returns_full(self):
        svc, _ = setup_service()
        result = svc._network_fingerprint_source("::1")
        assert ":" in result

    def test_bare_value_returns_itself(self):
        svc, _ = setup_service()
        assert svc._network_fingerprint_source("localhost") == "localhost"


# ---------------------------------------------------------------------------
# AuthService._store_tokens / _clear_session_tokens
# ---------------------------------------------------------------------------


class TestRedisTokenOperations:
    @pytest.mark.asyncio
    async def test_store_tokens_sets_two_redis_keys(self):
        svc, redis = setup_service()
        sid = uuid.uuid4()
        await svc._store_tokens(
            session_id=sid, refresh_jti="jti-val", csrf_token="csrf-val", ttl=3600
        )
        assert redis.store.get(f"refresh_jti:{sid}") == "jti-val"
        assert redis.store.get(f"csrf:{sid}") == "csrf-val"

    @pytest.mark.asyncio
    async def test_clear_session_tokens_removes_both_keys(self):
        svc, redis = setup_service()
        sid = uuid.uuid4()
        redis.store[f"refresh_jti:{sid}"] = "x"
        redis.store[f"csrf:{sid}"] = "y"
        await svc._clear_session_tokens(sid)
        assert f"refresh_jti:{sid}" not in redis.store
        assert f"csrf:{sid}" not in redis.store


# ---------------------------------------------------------------------------
# AuthService._issue_token_bundle
# ---------------------------------------------------------------------------


class TestIssueTokenBundle:
    @pytest.mark.asyncio
    async def test_bundle_contains_expected_fields(self, monkeypatch):
        svc, redis = setup_service()
        monkeypatch.setattr(auth_module, "create_access_token", lambda *_: "acc")
        monkeypatch.setattr(
            auth_module, "create_refresh_token", lambda *_: ("ref", "jti-123")
        )
        monkeypatch.setattr(auth_module, "create_csrf_token", lambda: "csrf-123")
        sid = uuid.uuid4()
        result = await svc._issue_token_bundle(
            user_id=uuid.uuid4(), role=STD, school_id=uuid.uuid4(), session_id=sid
        )
        assert result["access_token"] == "acc"
        assert result["refresh_token"] == "ref"
        assert result["csrf_token"] == "csrf-123"
        assert redis.store.get(f"refresh_jti:{sid}") == "jti-123"
        assert redis.store.get(f"csrf:{sid}") == "csrf-123"


# ---------------------------------------------------------------------------
# AuthService._record_login_history
# ---------------------------------------------------------------------------


class TestRecordLoginHistory:
    @pytest.mark.asyncio
    async def test_skips_when_user_id_none(self, monkeypatch):
        svc, _ = setup_service()
        uow = FakeUnitOfWork()
        monkeypatch.setattr(auth_module, "UnitOfWork", lambda _: uow)
        await svc._record_login_history(
            user_id=None,
            school_id=uuid.uuid4(),
            ip_address=None,
            user_agent=None,
            device_name=None,
            device_fingerprint=None,
            success=False,
        )
        assert not uow.committed

    @pytest.mark.asyncio
    async def test_records_login_on_success(self, monkeypatch):
        svc, _ = setup_service()
        repo_in_uow = AsyncMock()
        uow = FakeUnitOfWork()
        record = SimpleNamespace(id=uuid.uuid4())
        repo_in_uow.create_login_record.return_value = record
        monkeypatch.setattr(auth_module, "UnitOfWork", lambda _: uow)
        monkeypatch.setattr(
            auth_module, "LoginHistoryRepository", lambda _: repo_in_uow
        )
        await svc._record_login_history(
            user_id=uuid.uuid4(),
            school_id=uuid.uuid4(),
            ip_address="1.2.3.4",
            user_agent="UA",
            device_name=None,
            device_fingerprint=None,
            success=True,
        )
        assert uow.committed

    @pytest.mark.asyncio
    async def test_swallows_exception(self, monkeypatch):
        svc, _ = setup_service()
        uow = FakeUnitOfWork()
        repo_in_uow = AsyncMock()
        repo_in_uow.create_login_record.side_effect = RuntimeError("db error")
        monkeypatch.setattr(auth_module, "UnitOfWork", lambda _: uow)
        monkeypatch.setattr(
            auth_module, "LoginHistoryRepository", lambda _: repo_in_uow
        )
        # Should not raise
        await svc._record_login_history(
            user_id=uuid.uuid4(),
            school_id=uuid.uuid4(),
            ip_address=None,
            user_agent=None,
            device_name=None,
            device_fingerprint=None,
            success=False,
        )


# ---------------------------------------------------------------------------
# AuthService._dispatch_event
# ---------------------------------------------------------------------------


class TestDispatchEvent:
    @pytest.mark.asyncio
    async def test_dispatches_event(self):
        # Do NOT mock _dispatch_event itself — we're testing the real method
        redis = FakeRedis()
        svc = AuthService(AsyncMock(), redis)
        svc.repo = AsyncMock()
        svc.audit = AsyncMock()
        svc._dispatcher = AsyncMock()
        event = object()
        await svc._dispatch_event(event)
        svc._dispatcher.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_swallows_dispatch_exception(self):
        redis = FakeRedis()
        svc = AuthService(AsyncMock(), redis)
        svc.repo = AsyncMock()
        svc.audit = AsyncMock()
        svc._dispatcher = AsyncMock()
        svc._dispatcher.dispatch.side_effect = RuntimeError("dispatch failed")
        await svc._dispatch_event(object())  # must not raise


# ---------------------------------------------------------------------------
# AuthService._audit_login_denial
# ---------------------------------------------------------------------------


class TestAuditLoginDenial:
    @pytest.mark.asyncio
    async def test_skips_when_actor_none_and_school_not_found(self):
        svc, _ = setup_service()
        svc.repo.get_school_by_id.return_value = None
        # Should return without calling audit
        await svc._audit_login_denial(
            school_id=uuid.uuid4(),
            actor_id=None,
            action_type="TEST",
            error_code="ERR-000",
            ip_address=None,
        )
        svc.audit.log_event.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_audits_when_actor_none_and_school_found(self):
        svc, _ = setup_service()
        svc.repo.get_school_by_id.return_value = SimpleNamespace(id=uuid.uuid4())
        await svc._audit_login_denial(
            school_id=uuid.uuid4(),
            actor_id=None,
            action_type="AUTH_LOGIN_FAILED",
            error_code="ERR-000",
            ip_address=None,
        )
        svc.audit.log_event.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_audits_when_actor_id_set(self):
        svc, _ = setup_service()
        await svc._audit_login_denial(
            school_id=uuid.uuid4(),
            actor_id=uuid.uuid4(),
            action_type="AUTH_LOGIN_FAILED",
            error_code="ERR-000",
            ip_address=None,
        )
        svc.audit.log_event.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_swallows_audit_exception(self):
        svc, _ = setup_service()
        svc.audit.log_event.side_effect = RuntimeError("audit db error")
        await svc._audit_login_denial(
            school_id=uuid.uuid4(),
            actor_id=uuid.uuid4(),
            action_type="AUTH_LOGIN_FAILED",
            error_code="ERR-000",
            ip_address=None,
        )  # must not raise


# ---------------------------------------------------------------------------
# AuthService.login — account lockout + oldest session None
# ---------------------------------------------------------------------------


class TestLoginEdgeCases:
    @pytest.mark.asyncio
    async def test_account_lockout_raises_authorization_error(self, monkeypatch):
        svc, _ = setup_service()
        monkeypatch.setattr(
            auth_module.settings, "account_lockout_enabled", True, raising=False
        )
        monkeypatch.setattr(
            auth_module.settings, "account_lockout_max_attempts", 5, raising=False
        )
        monkeypatch.setattr(
            auth_module.settings, "account_lockout_duration_minutes", 30, raising=False
        )
        school_id = uuid.uuid4()
        user = make_user(school_id)
        svc.repo.get_user_by_email.return_value = user
        svc.repo.count_failed_login_attempts.return_value = 5
        svc._record_login_history = AsyncMock()

        with pytest.raises(AuthorizationError, match="Account locked"):
            await svc.login(email=user.email, password="x", school_id=school_id)

    @pytest.mark.asyncio
    async def test_failed_login_records_failed_attempt_when_lockout_enabled(
        self, monkeypatch
    ):
        svc, _ = setup_service()
        monkeypatch.setattr(
            auth_module.settings, "account_lockout_enabled", True, raising=False
        )
        monkeypatch.setattr(
            auth_module.settings, "account_lockout_max_attempts", 10, raising=False
        )
        monkeypatch.setattr(
            auth_module.settings, "account_lockout_duration_minutes", 30, raising=False
        )
        monkeypatch.setattr(auth_module, "verify_password", lambda *_: False)
        school_id = uuid.uuid4()
        user = make_user(school_id)
        svc.repo.get_user_by_email.return_value = user
        svc.repo.count_failed_login_attempts.return_value = 0
        svc._record_login_history = AsyncMock()

        with pytest.raises(AuthenticationError):
            await svc.login(email=user.email, password="bad", school_id=school_id)

        svc.repo.create_failed_login_attempt.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_inactive_user_audit_exception_swallowed(self, monkeypatch):
        svc, _ = setup_service()
        monkeypatch.setattr(
            auth_module.settings, "account_lockout_enabled", False, raising=False
        )
        monkeypatch.setattr(auth_module, "verify_password", lambda *_: True)
        school_id = uuid.uuid4()
        user = make_user(school_id, status="inactive")
        svc.repo.get_user_by_email.return_value = user
        svc.audit.log_event.side_effect = RuntimeError("audit error")
        svc._record_login_history = AsyncMock()

        with pytest.raises(AuthorizationError, match="Account is not active"):
            await svc.login(email=user.email, password="secret", school_id=school_id)

    @pytest.mark.asyncio
    async def test_no_membership_audit_exception_swallowed(self, monkeypatch):
        svc, _ = setup_service()
        monkeypatch.setattr(
            auth_module.settings, "account_lockout_enabled", False, raising=False
        )
        monkeypatch.setattr(auth_module, "verify_password", lambda *_: True)
        school_id = uuid.uuid4()
        user = make_user(school_id)
        svc.repo.get_user_by_email.return_value = user
        svc.repo.get_membership.return_value = None
        svc.audit.log_event.side_effect = RuntimeError("audit error")
        svc._record_login_history = AsyncMock()

        with pytest.raises(NotFoundError, match="No active membership"):
            await svc.login(email=user.email, password="secret", school_id=school_id)

    @pytest.mark.asyncio
    async def test_login_oldest_session_none_skips_revoke(self, monkeypatch):
        """Covers branch where count >= max but get_oldest_active_session returns None."""
        svc, _ = setup_service()
        monkeypatch.setattr(
            auth_module.settings, "account_lockout_enabled", False, raising=False
        )
        monkeypatch.setattr(
            auth_module.settings, "suspicious_activity_enabled", False, raising=False
        )
        monkeypatch.setattr(
            auth_module.settings, "max_sessions_per_user", 1, raising=False
        )
        monkeypatch.setattr(auth_module, "verify_password", lambda *_: True)
        monkeypatch.setattr(auth_module, "get_correlation_id", lambda: None)
        school_id = uuid.uuid4()
        user = make_user(school_id)
        membership = SimpleNamespace(role_code=STD)
        svc.repo.get_user_by_email.return_value = user
        svc.repo.get_membership.return_value = membership
        svc._issue_token_bundle = AsyncMock(
            return_value={"access_token": "tok", "session_id": uuid.uuid4()}
        )
        repo_in_uow, _, login_history_in_uow, uow = patch_uow(monkeypatch)
        repo_in_uow.count_active_sessions.return_value = 1
        repo_in_uow.get_oldest_active_session.return_value = None  # ← key branch
        login_history_in_uow.get_device_fingerprints.return_value = []
        repo_in_uow.create_session.return_value = SimpleNamespace(id=uuid.uuid4())

        result = await svc.login(
            email=user.email, password="secret", school_id=school_id
        )
        assert result["access_token"] == "tok"
        repo_in_uow.revoke_session.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_login_suspicious_activity_new_location(self, monkeypatch):
        """Covers suspicious_activity_enabled=True branch."""
        svc, _ = setup_service()
        monkeypatch.setattr(
            auth_module.settings, "account_lockout_enabled", False, raising=False
        )
        monkeypatch.setattr(
            auth_module.settings, "suspicious_activity_enabled", True, raising=False
        )
        monkeypatch.setattr(
            auth_module.settings, "max_sessions_per_user", 100, raising=False
        )
        monkeypatch.setattr(auth_module, "verify_password", lambda *_: True)
        monkeypatch.setattr(auth_module, "get_correlation_id", lambda: None)
        school_id = uuid.uuid4()
        user = make_user(school_id)
        membership = SimpleNamespace(role_code=STD)
        svc.repo.get_user_by_email.return_value = user
        svc.repo.get_membership.return_value = membership
        svc._issue_token_bundle = AsyncMock(
            return_value={"access_token": "tok", "session_id": uuid.uuid4()}
        )
        repo_in_uow, _, login_history_in_uow, uow = patch_uow(monkeypatch)
        repo_in_uow.count_active_sessions.return_value = 0
        login_history_in_uow.get_device_fingerprints.return_value = []
        repo_in_uow.create_session.return_value = SimpleNamespace(id=uuid.uuid4())

        # Mock SuspiciousActivityService via sys.modules
        mock_sus_module = MagicMock()
        sus_svc = MagicMock()
        mock_sus_module.SuspiciousActivityService.return_value = sus_svc
        sus_svc.get_ip_location.return_value = {
            "country_code": "MA",
            "city": "Casa",
            "region": "GC",
        }
        sus_svc.is_new_location.return_value = True
        sus_svc.is_new_device.return_value = False
        svc.repo.get_known_locations_by_user.return_value = []
        svc.repo.get_known_location_by_user_ip.return_value = None
        svc.repo.get_known_devices_by_user.return_value = []
        svc.repo.get_known_device_by_user_fingerprint.return_value = None

        with patch.dict(
            sys.modules, {"app.services.platform.suspicious_activity": mock_sus_module}
        ):
            result = await svc.login(
                email=user.email,
                password="secret",
                school_id=school_id,
                ip_address="1.2.3.4",
                user_agent="UA",
            )

        assert result["access_token"] == "tok"
        svc.repo.create_known_location.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_login_suspicious_activity_known_location_updates(self, monkeypatch):
        """Covers branch where known_location already exists (update path)."""
        svc, _ = setup_service()
        monkeypatch.setattr(
            auth_module.settings, "account_lockout_enabled", False, raising=False
        )
        monkeypatch.setattr(
            auth_module.settings, "suspicious_activity_enabled", True, raising=False
        )
        monkeypatch.setattr(
            auth_module.settings, "max_sessions_per_user", 100, raising=False
        )
        monkeypatch.setattr(auth_module, "verify_password", lambda *_: True)
        monkeypatch.setattr(auth_module, "get_correlation_id", lambda: None)
        school_id = uuid.uuid4()
        user = make_user(school_id)
        svc.repo.get_user_by_email.return_value = user
        svc.repo.get_membership.return_value = SimpleNamespace(role_code=STD)
        svc._issue_token_bundle = AsyncMock(
            return_value={"access_token": "tok", "session_id": uuid.uuid4()}
        )
        repo_in_uow, _, login_history_in_uow, uow = patch_uow(monkeypatch)
        repo_in_uow.count_active_sessions.return_value = 0
        login_history_in_uow.get_device_fingerprints.return_value = []
        repo_in_uow.create_session.return_value = SimpleNamespace(id=uuid.uuid4())

        mock_sus_module = MagicMock()
        sus_svc = MagicMock()
        mock_sus_module.SuspiciousActivityService.return_value = sus_svc
        sus_svc.get_ip_location.return_value = {
            "country_code": "MA",
            "city": "Rabat",
            "region": "RB",
        }
        sus_svc.is_new_location.return_value = False
        sus_svc.is_new_device.return_value = False
        known_loc = SimpleNamespace(
            last_seen_at=None, country_code=None, city=None, region=None
        )
        known_dev = SimpleNamespace(
            last_seen_at=None, device_name=None, user_agent=None
        )
        svc.repo.get_known_locations_by_user.return_value = []
        svc.repo.get_known_location_by_user_ip.return_value = known_loc
        svc.repo.get_known_devices_by_user.return_value = []
        svc.repo.get_known_device_by_user_fingerprint.return_value = known_dev

        with patch.dict(
            sys.modules, {"app.services.platform.suspicious_activity": mock_sus_module}
        ):
            await svc.login(
                email=user.email,
                password="secret",
                school_id=school_id,
                ip_address="2.3.4.5",
                user_agent="UA",
            )

        svc.repo.update_known_location.assert_awaited_once()
        svc.repo.update_known_device.assert_awaited_once()


# ---------------------------------------------------------------------------
# AuthService.register
# ---------------------------------------------------------------------------


class TestRegister:
    def _make_invite(
        self,
        school_id=None,
        role=STD,
        expired=False,
        consumed=False,
        with_student=False,
    ):
        inv = SimpleNamespace(
            id=uuid.uuid4(),
            school_id=school_id or uuid.uuid4(),
            role_target=role,
            expires_at=(datetime.now(timezone.utc) - timedelta(hours=1))
            if expired
            else None,
            consumed_by=uuid.uuid4() if consumed else None,
            target_student_id=uuid.uuid4() if with_student else None,
            issuer_user_id=uuid.uuid4(),
        )
        return inv

    @pytest.mark.asyncio
    async def test_invalid_code_raises_not_found(self):
        svc, _ = setup_service()
        svc.repo.get_invitation_by_code_hash.return_value = None
        with pytest.raises(NotFoundError):
            await svc.register(
                code="BADCODE", email="a@b.com", full_name="A", password="P@ssw0rd!"
            )

    @pytest.mark.asyncio
    async def test_expired_invite_raises_authentication_error(self):
        svc, _ = setup_service()
        svc.repo.get_invitation_by_code_hash.return_value = self._make_invite(
            expired=True
        )
        with pytest.raises(AuthenticationError, match="expired"):
            await svc.register(
                code="C", email="a@b.com", full_name="A", password="P@ssw0rd!"
            )

    @pytest.mark.asyncio
    async def test_consumed_invite_raises_conflict(self):
        svc, _ = setup_service()
        svc.repo.get_invitation_by_code_hash.return_value = self._make_invite(
            consumed=True
        )
        with pytest.raises(ConflictError, match="already been used"):
            await svc.register(
                code="C", email="a@b.com", full_name="A", password="P@ssw0rd!"
            )

    @pytest.mark.asyncio
    async def test_existing_email_raises_conflict(self):
        svc, _ = setup_service()
        invite = self._make_invite()
        svc.repo.get_invitation_by_code_hash.return_value = invite
        svc.repo.get_user_by_email.return_value = SimpleNamespace(id=uuid.uuid4())
        with pytest.raises(ConflictError, match="email already exists"):
            await svc.register(
                code="C", email="a@b.com", full_name="A", password="P@ssw0rd!"
            )

    @pytest.mark.asyncio
    async def test_success_returns_token_bundle(self, monkeypatch):
        svc, redis = setup_service()
        school_id = uuid.uuid4()
        invite = self._make_invite(school_id=school_id, role=STD)
        svc.repo.get_invitation_by_code_hash.return_value = invite
        svc.repo.get_user_by_email.return_value = None
        monkeypatch.setattr(
            auth_module,
            "password_validator",
            SimpleNamespace(validate=lambda *_a, **_k: None),
        )
        monkeypatch.setattr(auth_module, "get_correlation_id", lambda: None)
        monkeypatch.setattr(auth_module, "create_access_token", lambda *_: "acc")
        monkeypatch.setattr(
            auth_module, "create_refresh_token", lambda *_: ("ref", "jti")
        )
        monkeypatch.setattr(auth_module, "create_csrf_token", lambda: "csrf")

        user = SimpleNamespace(id=uuid.uuid4(), email="a@b.com", full_name="A")
        session = SimpleNamespace(
            id=uuid.uuid4(), created_at=datetime.now(timezone.utc)
        )
        repo_in_uow = AsyncMock()
        audit_in_uow = AsyncMock()
        profile_loader = AsyncMock()
        profile_loader.ensure_profile.return_value = None
        uow = FakeUnitOfWork()
        repo_in_uow.create_user.return_value = user
        repo_in_uow.create_session.return_value = session

        monkeypatch.setattr(auth_module, "UnitOfWork", lambda _: uow)
        monkeypatch.setattr(auth_module, "AuthRepository", lambda _: repo_in_uow)
        monkeypatch.setattr(auth_module, "AuditService", lambda _: audit_in_uow)
        monkeypatch.setattr(auth_module, "ProfileLoader", lambda _: profile_loader)

        result = await svc.register(
            code="CODE1234",
            email="a@b.com",
            full_name="A",
            password="P@ssw0rd!1",
            ip_address="1.2.3.4",
            user_agent="UA/1.0",
            device_name="PC",
        )

        assert result["access_token"] == "acc"
        assert result["refresh_token"] == "ref"
        assert result["email_verification_required"] is True

    @pytest.mark.asyncio
    async def test_register_par_with_student_creates_link(self, monkeypatch):
        svc, redis = setup_service()
        school_id = uuid.uuid4()
        invite = self._make_invite(school_id=school_id, role=PAR, with_student=True)
        svc.repo.get_invitation_by_code_hash.return_value = invite
        svc.repo.get_user_by_email.return_value = None
        monkeypatch.setattr(
            auth_module,
            "password_validator",
            SimpleNamespace(validate=lambda *_a, **_k: None),
        )
        monkeypatch.setattr(auth_module, "get_correlation_id", lambda: None)
        monkeypatch.setattr(auth_module, "create_access_token", lambda *_: "acc")
        monkeypatch.setattr(
            auth_module, "create_refresh_token", lambda *_: ("ref", "jti")
        )
        monkeypatch.setattr(auth_module, "create_csrf_token", lambda: "csrf")

        user = SimpleNamespace(id=uuid.uuid4(), email="p@b.com", full_name="P")
        session = SimpleNamespace(
            id=uuid.uuid4(), created_at=datetime.now(timezone.utc)
        )
        repo_in_uow = AsyncMock()
        audit_in_uow = AsyncMock()
        profile_loader = AsyncMock()
        profile_loader.ensure_profile.return_value = None
        uow = FakeUnitOfWork()
        repo_in_uow.create_user.return_value = user
        repo_in_uow.create_session.return_value = session

        monkeypatch.setattr(auth_module, "UnitOfWork", lambda _: uow)
        monkeypatch.setattr(auth_module, "AuthRepository", lambda _: repo_in_uow)
        monkeypatch.setattr(auth_module, "AuditService", lambda _: audit_in_uow)
        monkeypatch.setattr(auth_module, "ProfileLoader", lambda _: profile_loader)

        await svc.register(
            code="C", email="p@b.com", full_name="P", password="P@ssw0rd!1"
        )
        repo_in_uow.create_parent_child_link.assert_awaited_once()


# ---------------------------------------------------------------------------
# AuthService.refresh — membership None
# ---------------------------------------------------------------------------


class TestRefreshEdgeCases:
    @pytest.mark.asyncio
    async def test_refresh_no_membership_raises(self, monkeypatch):
        svc, redis = setup_service()
        session_id = uuid.uuid4()
        monkeypatch.setattr(
            auth_module,
            "decode_refresh_token",
            lambda _: {
                "session_id": str(session_id),
                "sub": str(uuid.uuid4()),
                "school_id": str(uuid.uuid4()),
                "jti": "stored-jti",
            },
        )
        redis.store[f"csrf:{session_id}"] = "csrf-ok"
        redis.store[f"refresh_jti:{session_id}"] = "stored-jti"
        svc.repo.get_session_by_id.return_value = SimpleNamespace(id=session_id)
        svc.repo.get_membership.return_value = None

        with pytest.raises(AuthenticationError, match="No active membership"):
            await svc.refresh("token", csrf_token="csrf-ok")


# ---------------------------------------------------------------------------
# AuthService.logout
# ---------------------------------------------------------------------------


class TestLogout:
    @pytest.mark.asyncio
    async def test_logout_revokes_session_and_clears_redis(self):
        svc, redis = setup_service()
        session_id = uuid.uuid4()
        user_id = uuid.uuid4()
        school_id = uuid.uuid4()
        redis.store[f"refresh_jti:{session_id}"] = "x"
        redis.store[f"csrf:{session_id}"] = "y"

        await svc.logout(session_id=session_id, user_id=user_id, school_id=school_id)

        svc.repo.revoke_session.assert_awaited_once()
        assert f"refresh_jti:{session_id}" not in redis.store
        assert f"csrf:{session_id}" not in redis.store
        svc.audit.log_event.assert_awaited_once()


# ---------------------------------------------------------------------------
# AuthService.get_profile
# ---------------------------------------------------------------------------


class TestGetProfile:
    @pytest.mark.asyncio
    async def test_user_not_found_raises(self):
        svc, _ = setup_service()
        svc.repo.get_user_by_id.return_value = None
        with pytest.raises(NotFoundError):
            await svc.get_profile(uuid.uuid4(), uuid.uuid4(), ADM)

    @pytest.mark.asyncio
    async def test_returns_profile_dict(self, monkeypatch):
        svc, _ = setup_service()
        uid = uuid.uuid4()
        school_id = uuid.uuid4()
        user = SimpleNamespace(id=uid, email="u@e.com", full_name="U")
        svc.repo.get_user_by_id.return_value = user
        membership = SimpleNamespace(
            role_code=ADM, school_id=school_id, status="active"
        )
        svc.repo.list_memberships.return_value = [membership]

        profile_loader = AsyncMock()
        monkeypatch.setattr(auth_module, "ProfileLoader", lambda _: profile_loader)

        result = await svc.get_profile(uid, school_id, ADM)

        assert result["id"] == uid
        assert result["email"] == "u@e.com"
        assert "permissions" in result
        assert "memberships" in result


# ---------------------------------------------------------------------------
# AuthService.list_sessions
# ---------------------------------------------------------------------------


class TestListSessions:
    @pytest.mark.asyncio
    async def test_returns_session_list(self):
        svc, _ = setup_service()
        s = SimpleNamespace(
            id=uuid.uuid4(),
            source="web",
            user_agent="UA",
            ip_address="1.2.3.4",
            device_name="PC",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        svc.repo.list_active_sessions.return_value = [s]
        result = await svc.list_sessions(uuid.uuid4(), uuid.uuid4())
        assert len(result) == 1
        assert result[0]["source"] == "web"

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_sessions(self):
        svc, _ = setup_service()
        svc.repo.list_active_sessions.return_value = []
        result = await svc.list_sessions(uuid.uuid4(), uuid.uuid4())
        assert result == []


# ---------------------------------------------------------------------------
# AuthService.list_login_history
# ---------------------------------------------------------------------------


class TestListLoginHistory:
    def _make_row(self):
        return SimpleNamespace(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            school_id=uuid.uuid4(),
            ip_address="1.2.3.4",
            user_agent="UA",
            device_name="PC",
            device_fingerprint="fp",
            city="Casa",
            country="MA",
            success=True,
            failure_reason=None,
            is_new_device=False,
            created_at=datetime.now(timezone.utc),
        )

    @pytest.mark.asyncio
    async def test_non_admin_viewing_other_raises_authorization_error(self):
        svc, _ = setup_service()
        auth = make_auth_context(STD)
        with pytest.raises(AuthorizationError):
            await svc.list_login_history(target_user_id=uuid.uuid4(), auth=auth)

    @pytest.mark.asyncio
    async def test_target_not_in_school_raises_not_found(self):
        svc, _ = setup_service()
        uid = uuid.uuid4()
        auth = make_auth_context(ADM, user_id=uid)
        svc.repo.get_user_in_school.return_value = None
        with pytest.raises(NotFoundError):
            await svc.list_login_history(target_user_id=uuid.uuid4(), auth=auth)

    @pytest.mark.asyncio
    async def test_self_viewing_own_history_succeeds(self, monkeypatch):
        svc, _ = setup_service()
        uid = uuid.uuid4()
        auth = make_auth_context(STD, user_id=uid)
        svc.repo.get_user_in_school.return_value = SimpleNamespace(id=uid)

        history_repo = AsyncMock()
        row = self._make_row()
        history_repo.list_user_login_history.return_value = ([row], None, False)
        monkeypatch.setattr(
            auth_module, "LoginHistoryRepository", lambda _: history_repo
        )

        rows, cursor, has_more = await svc.list_login_history(
            target_user_id=uid, auth=auth
        )
        assert len(rows) == 1

    @pytest.mark.asyncio
    async def test_admin_viewing_other_history_succeeds(self, monkeypatch):
        svc, _ = setup_service()
        other_id = uuid.uuid4()
        auth = make_auth_context(ADM)
        svc.repo.get_user_in_school.return_value = SimpleNamespace(id=other_id)

        history_repo = AsyncMock()
        history_repo.list_user_login_history.return_value = ([], None, False)
        monkeypatch.setattr(
            auth_module, "LoginHistoryRepository", lambda _: history_repo
        )

        rows, _, _ = await svc.list_login_history(target_user_id=other_id, auth=auth)
        assert rows == []


# ---------------------------------------------------------------------------
# AuthService.impersonate — missing branches
# ---------------------------------------------------------------------------


class TestImpersonateMissingBranches:
    @pytest.mark.asyncio
    async def test_target_user_not_found_raises(self):
        svc, _ = setup_service()
        auth = make_auth_context(ADM)
        svc.repo.get_user_in_school.return_value = None
        with pytest.raises(NotFoundError):
            await svc.impersonate(target_user_id=uuid.uuid4(), admin_auth=auth)

    @pytest.mark.asyncio
    async def test_target_no_membership_raises(self):
        svc, _ = setup_service()
        auth = make_auth_context(ADM)
        svc.repo.get_user_in_school.return_value = SimpleNamespace(id=uuid.uuid4())
        svc.repo.get_membership.return_value = None
        with pytest.raises(NotFoundError, match="no active membership"):
            await svc.impersonate(target_user_id=uuid.uuid4(), admin_auth=auth)


# ---------------------------------------------------------------------------
# AuthService.stop_impersonation — missing branches
# ---------------------------------------------------------------------------


class TestStopImpersonationEdgeCases:
    @pytest.mark.asyncio
    async def test_admin_membership_none_raises(self, monkeypatch):
        svc, _ = setup_service()
        session_id = uuid.uuid4()
        impersonator_id = uuid.uuid4()
        school_id = uuid.uuid4()
        current_session = SimpleNamespace(
            id=session_id,
            impersonator_id=impersonator_id,
            correlation_id=None,
            user_id=uuid.uuid4(),
            school_id=school_id,
        )
        svc.repo.get_session_by_id.return_value = current_session
        svc._clear_session_tokens = AsyncMock()

        repo_in_uow = AsyncMock()
        uow = FakeUnitOfWork()
        repo_in_uow.get_session_by_id.return_value = current_session
        repo_in_uow.get_membership.return_value = None
        monkeypatch.setattr(auth_module, "UnitOfWork", lambda _: uow)
        monkeypatch.setattr(auth_module, "AuthRepository", lambda _: repo_in_uow)
        monkeypatch.setattr(auth_module, "AuditService", lambda _: AsyncMock())

        with pytest.raises(AuthenticationError, match="Impersonator membership"):
            await svc.stop_impersonation(session_id=session_id)

    @pytest.mark.asyncio
    async def test_no_original_session_creates_new(self, monkeypatch):
        """Covers the path where original_session_id is None → create new session."""
        svc, _ = setup_service()
        session_id = uuid.uuid4()
        impersonator_id = uuid.uuid4()
        school_id = uuid.uuid4()
        current_session = SimpleNamespace(
            id=session_id,
            impersonator_id=impersonator_id,
            correlation_id=None,  # ← no original session
            user_id=uuid.uuid4(),
            school_id=school_id,
        )
        restored = SimpleNamespace(id=uuid.uuid4())
        svc.repo.get_session_by_id.return_value = current_session
        svc._clear_session_tokens = AsyncMock()
        svc._issue_token_bundle = AsyncMock(return_value={"access_token": "adm"})

        repo_in_uow = AsyncMock()
        uow = FakeUnitOfWork()
        repo_in_uow.get_session_by_id.return_value = current_session
        repo_in_uow.get_membership.return_value = SimpleNamespace(role_code=ADM)
        repo_in_uow.create_session.return_value = restored
        monkeypatch.setattr(auth_module, "UnitOfWork", lambda _: uow)
        monkeypatch.setattr(auth_module, "AuthRepository", lambda _: repo_in_uow)
        monkeypatch.setattr(auth_module, "AuditService", lambda _: AsyncMock())
        monkeypatch.setattr(auth_module, "get_correlation_id", lambda: None)

        result = await svc.stop_impersonation(session_id=session_id)
        assert result["impersonation_active"] is False
        repo_in_uow.create_session.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_candidate_wrong_user_id_creates_new_session(self, monkeypatch):
        """Covers branch where candidate.user_id != impersonator → restored_session stays None."""
        svc, _ = setup_service()
        session_id = uuid.uuid4()
        original_session_id = uuid.uuid4()
        impersonator_id = uuid.uuid4()
        school_id = uuid.uuid4()
        current_session = SimpleNamespace(
            id=session_id,
            impersonator_id=impersonator_id,
            correlation_id=original_session_id,
            user_id=uuid.uuid4(),
            school_id=school_id,
        )
        # candidate exists but has wrong user_id
        bad_candidate = SimpleNamespace(
            id=original_session_id,
            user_id=uuid.uuid4(),  # ← different from impersonator_id
            school_id=school_id,
            impersonator_id=None,
        )
        restored = SimpleNamespace(id=uuid.uuid4())
        svc.repo.get_session_by_id.return_value = current_session
        svc._clear_session_tokens = AsyncMock()
        svc._issue_token_bundle = AsyncMock(return_value={"access_token": "adm"})

        repo_in_uow = AsyncMock()
        uow = FakeUnitOfWork()
        repo_in_uow.get_session_by_id.side_effect = [current_session, bad_candidate]
        repo_in_uow.get_membership.return_value = SimpleNamespace(role_code=ADM)
        repo_in_uow.create_session.return_value = restored
        monkeypatch.setattr(auth_module, "UnitOfWork", lambda _: uow)
        monkeypatch.setattr(auth_module, "AuthRepository", lambda _: repo_in_uow)
        monkeypatch.setattr(auth_module, "AuditService", lambda _: AsyncMock())
        monkeypatch.setattr(auth_module, "get_correlation_id", lambda: None)

        result = await svc.stop_impersonation(session_id=session_id)
        assert result["impersonation_active"] is False
        repo_in_uow.create_session.assert_awaited_once()


# ---------------------------------------------------------------------------
# AuthService.revoke_session
# ---------------------------------------------------------------------------


class TestRevokeSession:
    @pytest.mark.asyncio
    async def test_session_not_found_raises(self):
        svc, _ = setup_service()
        svc.repo.get_session_by_id.return_value = None
        with pytest.raises(NotFoundError):
            await svc.revoke_session(uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), ADM)

    @pytest.mark.asyncio
    async def test_cross_school_session_raises_not_found(self):
        svc, _ = setup_service()
        school_id = uuid.uuid4()
        session = SimpleNamespace(
            id=uuid.uuid4(), school_id=uuid.uuid4(), user_id=uuid.uuid4()
        )
        svc.repo.get_session_by_id.return_value = session
        with pytest.raises(NotFoundError):
            await svc.revoke_session(session.id, uuid.uuid4(), school_id, ADM)

    @pytest.mark.asyncio
    async def test_non_owner_non_adm_raises_authorization_error(self):
        svc, _ = setup_service()
        school_id = uuid.uuid4()
        actor_id = uuid.uuid4()
        session = SimpleNamespace(
            id=uuid.uuid4(), school_id=school_id, user_id=uuid.uuid4()
        )
        svc.repo.get_session_by_id.return_value = session
        svc.repo.save_session = AsyncMock()
        with pytest.raises(AuthorizationError):
            await svc.revoke_session(session.id, actor_id, school_id, TCH)

    @pytest.mark.asyncio
    async def test_owner_can_revoke_own_session(self):
        svc, redis = setup_service()
        school_id = uuid.uuid4()
        actor_id = uuid.uuid4()
        target_sid = uuid.uuid4()
        session = SimpleNamespace(
            id=target_sid, school_id=school_id, user_id=actor_id, revoke_at=None
        )
        svc.repo.get_session_by_id.return_value = session
        svc.repo.save_session = AsyncMock()
        redis.store[f"refresh_jti:{target_sid}"] = "x"

        result = await svc.revoke_session(target_sid, actor_id, school_id, STD)
        assert result["message"] == "Session revoked successfully"
        svc.repo.save_session.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_adm_can_revoke_any_session(self):
        svc, _ = setup_service()
        school_id = uuid.uuid4()
        session = SimpleNamespace(
            id=uuid.uuid4(), school_id=school_id, user_id=uuid.uuid4(), revoke_at=None
        )
        svc.repo.get_session_by_id.return_value = session
        svc.repo.save_session = AsyncMock()

        result = await svc.revoke_session(session.id, uuid.uuid4(), school_id, ADM)
        assert result["message"] == "Session revoked successfully"


# ---------------------------------------------------------------------------
# AuthService.change_password
# ---------------------------------------------------------------------------


class TestChangePassword:
    @pytest.mark.asyncio
    async def test_user_not_found_raises(self):
        svc, _ = setup_service()
        svc.repo.get_user_by_id.return_value = None
        with pytest.raises(NotFoundError):
            await svc.change_password(
                uuid.uuid4(), uuid.uuid4(), "old", "new", uuid.uuid4()
            )

    @pytest.mark.asyncio
    async def test_wrong_current_password_raises(self, monkeypatch):
        svc, _ = setup_service()
        monkeypatch.setattr(auth_module, "verify_password", lambda *_: False)
        svc.repo.get_user_by_id.return_value = make_user()
        with pytest.raises(AuthenticationError, match="Current password"):
            await svc.change_password(
                uuid.uuid4(), uuid.uuid4(), "bad", "new", uuid.uuid4()
            )

    @pytest.mark.asyncio
    async def test_password_in_history_raises_validation(self, monkeypatch):
        svc, _ = setup_service()
        # verify_password always returns True so both current-password check and history check pass
        monkeypatch.setattr(auth_module, "verify_password", lambda *_: True)
        history_entry = SimpleNamespace(password_hash="any-hash")
        svc.repo.get_password_history_by_user.return_value = [history_entry]
        user = make_user()
        svc.repo.get_user_by_id.return_value = user
        monkeypatch.setattr(
            "app.core.password_policy.password_validator",
            SimpleNamespace(validate=lambda *_a, **_k: None),
        )

        with pytest.raises(ValidationError, match="used recently"):
            await svc.change_password(
                uuid.uuid4(), uuid.uuid4(), "old", "NewP@ss1", uuid.uuid4()
            )

    @pytest.mark.asyncio
    async def test_success_updates_password_and_revokes_sessions(self, monkeypatch):
        svc, _ = setup_service()
        call_count = [0]

        def mock_verify(pwd, hsh):
            call_count[0] += 1
            return call_count[0] == 1  # True only first call (current password)

        monkeypatch.setattr(auth_module, "verify_password", mock_verify)
        monkeypatch.setattr(auth_module, "hash_password", lambda _: "new-hash")
        monkeypatch.setattr(
            "app.core.password_policy.password_validator",
            SimpleNamespace(validate=lambda *_a, **_k: None),
        )
        user = make_user()
        svc.repo.get_user_by_id.return_value = user
        svc.repo.get_password_history_by_user.return_value = []
        svc.repo.save_user = AsyncMock()

        result = await svc.change_password(
            uuid.uuid4(), uuid.uuid4(), "old", "NewP@ss1!", uuid.uuid4()
        )
        assert result["message"] == "Password changed successfully"
        svc.repo.save_user.assert_awaited_once()
        svc.repo.revoke_all_sessions.assert_awaited_once()


# ---------------------------------------------------------------------------
# InvitationService
# ---------------------------------------------------------------------------


def setup_invitation_service():
    redis = FakeRedis()
    svc = InvitationService(AsyncMock(), redis)
    svc.repo = AsyncMock()
    svc.repo.get_school_by_id.return_value = SimpleNamespace(school_type="formal")
    svc.audit = AsyncMock()
    return svc, redis


class TestInvitationService:
    @pytest.mark.asyncio
    async def test_create_invite_success(self):
        svc, _ = setup_invitation_service()
        inv = SimpleNamespace(id=uuid.uuid4())
        svc.repo.create_invitation.return_value = inv
        result = await svc.create_invite(
            school_id=uuid.uuid4(), issuer_user_id=uuid.uuid4(), role_target=STD
        )
        assert "code" in result
        assert len(result["code"]) == 8

    @pytest.mark.asyncio
    async def test_create_invite_rejects_educator_regular_invite(self):
        svc, _ = setup_invitation_service()
        with pytest.raises(ValidationError, match="SuperAdmin"):
            await svc.create_invite(
                school_id=uuid.uuid4(),
                issuer_user_id=uuid.uuid4(),
                role_target="EDUCATOR",
            )

    @pytest.mark.asyncio
    async def test_create_invite_informal_school_rejects_teacher(self):
        svc, _ = setup_invitation_service()
        svc.repo.get_school_by_id.return_value = SimpleNamespace(school_type="informal")
        with pytest.raises(ValidationError, match="Invalid invitation role"):
            await svc.create_invite(
                school_id=uuid.uuid4(),
                issuer_user_id=uuid.uuid4(),
                role_target=TCH,
            )

    @pytest.mark.asyncio
    async def test_create_invite_informal_school_allows_student(self):
        svc, _ = setup_invitation_service()
        svc.repo.get_school_by_id.return_value = SimpleNamespace(school_type="informal")
        svc.repo.create_invitation.return_value = SimpleNamespace(id=uuid.uuid4())
        result = await svc.create_invite(
            school_id=uuid.uuid4(),
            issuer_user_id=uuid.uuid4(),
            role_target=STD,
        )
        assert result["role_target"] == STD

    @pytest.mark.asyncio
    async def test_create_invite_non_par_with_student_id_raises(self):
        svc, _ = setup_invitation_service()
        with pytest.raises(ValidationError, match="only valid for PAR"):
            await svc.create_invite(
                school_id=uuid.uuid4(),
                issuer_user_id=uuid.uuid4(),
                role_target=STD,
                target_student_id=uuid.uuid4(),
            )

    @pytest.mark.asyncio
    async def test_create_invite_par_student_not_found_raises(self):
        svc, _ = setup_invitation_service()
        svc.repo.get_student_in_school.return_value = None
        with pytest.raises(NotFoundError, match="student not found"):
            await svc.create_invite(
                school_id=uuid.uuid4(),
                issuer_user_id=uuid.uuid4(),
                role_target=PAR,
                target_student_id=uuid.uuid4(),
            )

    @pytest.mark.asyncio
    async def test_create_invite_par_with_valid_student(self):
        svc, _ = setup_invitation_service()
        svc.repo.get_student_in_school.return_value = SimpleNamespace(id=uuid.uuid4())
        svc.repo.create_invitation.return_value = SimpleNamespace(id=uuid.uuid4())
        result = await svc.create_invite(
            school_id=uuid.uuid4(),
            issuer_user_id=uuid.uuid4(),
            role_target=PAR,
            target_student_id=uuid.uuid4(),
        )
        assert "code" in result

    @pytest.mark.asyncio
    async def test_consume_invite_not_found_raises(self):
        svc, _ = setup_invitation_service()
        svc.repo.get_invitation_by_code_hash.return_value = None
        with pytest.raises(NotFoundError):
            await svc.consume_invite("CODE", uuid.uuid4(), uuid.uuid4())

    @pytest.mark.asyncio
    async def test_consume_invite_wrong_school_raises(self):
        svc, _ = setup_invitation_service()
        inv = SimpleNamespace(
            id=uuid.uuid4(),
            school_id=uuid.uuid4(),
            expires_at=None,
            consumed_by=None,
            role_target=STD,
        )
        svc.repo.get_invitation_by_code_hash.return_value = inv
        with pytest.raises(NotFoundError):
            await svc.consume_invite(
                "CODE", uuid.uuid4(), uuid.uuid4()
            )  # different school_id

    @pytest.mark.asyncio
    async def test_consume_invite_expired_raises(self):
        svc, _ = setup_invitation_service()
        school_id = uuid.uuid4()
        inv = SimpleNamespace(
            id=uuid.uuid4(),
            school_id=school_id,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            consumed_by=None,
            role_target=STD,
        )
        svc.repo.get_invitation_by_code_hash.return_value = inv
        with pytest.raises(AuthenticationError, match="expired"):
            await svc.consume_invite("CODE", uuid.uuid4(), school_id)

    @pytest.mark.asyncio
    async def test_consume_invite_idempotent_same_user(self):
        svc, _ = setup_invitation_service()
        school_id = uuid.uuid4()
        user_id = uuid.uuid4()
        inv = SimpleNamespace(
            id=uuid.uuid4(),
            school_id=school_id,
            expires_at=None,
            consumed_by=user_id,
            role_target=STD,
        )
        svc.repo.get_invitation_by_code_hash.return_value = inv
        result = await svc.consume_invite("CODE", user_id, school_id)
        assert result["message"] == "Invitation already consumed"

    @pytest.mark.asyncio
    async def test_consume_invite_consumed_by_other_raises_conflict(self):
        svc, _ = setup_invitation_service()
        school_id = uuid.uuid4()
        inv = SimpleNamespace(
            id=uuid.uuid4(),
            school_id=school_id,
            expires_at=None,
            consumed_by=uuid.uuid4(),
            role_target=STD,  # consumed by someone else
        )
        svc.repo.get_invitation_by_code_hash.return_value = inv
        with pytest.raises(ConflictError):
            await svc.consume_invite("CODE", uuid.uuid4(), school_id)

    @pytest.mark.asyncio
    async def test_consume_invite_success(self):
        svc, _ = setup_invitation_service()
        school_id = uuid.uuid4()
        user_id = uuid.uuid4()
        inv = SimpleNamespace(
            id=uuid.uuid4(),
            school_id=school_id,
            expires_at=None,
            consumed_by=None,
            role_target=STD,
        )
        svc.repo.get_invitation_by_code_hash.return_value = inv
        membership = SimpleNamespace(id=uuid.uuid4())
        svc.repo.create_membership.return_value = membership
        user = SimpleNamespace(
            id=user_id, email="u@e.com", email_verified_at=datetime.now(timezone.utc)
        )
        svc.repo.get_user_by_id.return_value = user

        result = await svc.consume_invite("CODE", user_id, school_id)
        assert "membership_id" in result
        svc.repo.consume_invitation.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_consume_invite_unverified_email_sends_otp(self):
        svc, redis = setup_invitation_service()
        school_id = uuid.uuid4()
        user_id = uuid.uuid4()
        inv = SimpleNamespace(
            id=uuid.uuid4(),
            school_id=school_id,
            expires_at=None,
            consumed_by=None,
            role_target=STD,
        )
        svc.repo.get_invitation_by_code_hash.return_value = inv
        svc.repo.create_membership.return_value = SimpleNamespace(id=uuid.uuid4())
        user = SimpleNamespace(id=user_id, email="u@e.com", email_verified_at=None)
        svc.repo.get_user_by_id.return_value = user

        with patch.object(EmailVerificationService, "send_verification_otp", AsyncMock()):
            result = await svc.consume_invite("CODE", user_id, school_id)
        assert result["email_verification_required"] is True

    @pytest.mark.asyncio
    async def test_revoke_invite_not_found_raises(self):
        svc, _ = setup_invitation_service()
        svc.repo.get_invitation_by_id.return_value = None
        with pytest.raises(NotFoundError):
            await svc.revoke_invite(uuid.uuid4(), uuid.uuid4(), uuid.uuid4())

    @pytest.mark.asyncio
    async def test_revoke_invite_already_consumed_is_idempotent(self):
        svc, _ = setup_invitation_service()
        inv = SimpleNamespace(
            id=uuid.uuid4(), consumed_by=uuid.uuid4(), expires_at=None
        )
        svc.repo.get_invitation_by_id.return_value = inv
        result = await svc.revoke_invite(inv.id, uuid.uuid4(), uuid.uuid4())
        assert result["message"] == "Invitation revoked"
        svc.repo.save_invitation.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_revoke_invite_success(self):
        svc, _ = setup_invitation_service()
        inv = SimpleNamespace(
            id=uuid.uuid4(), consumed_by=None, expires_at=None, consumed_at=None
        )
        svc.repo.get_invitation_by_id.return_value = inv
        svc.repo.save_invitation = AsyncMock()
        result = await svc.revoke_invite(inv.id, uuid.uuid4(), uuid.uuid4())
        assert result["message"] == "Invitation revoked"
        svc.repo.save_invitation.assert_awaited_once()


# ---------------------------------------------------------------------------
# RecoveryService
# ---------------------------------------------------------------------------


def setup_recovery_service():
    redis = FakeRedis()
    svc = RecoveryService(AsyncMock(), redis)
    svc.repo = AsyncMock()
    svc.audit = AsyncMock()
    return svc, redis


class TestRecoveryService:
    @pytest.mark.asyncio
    async def test_request_recovery_user_not_found_returns_200(self):
        svc, _ = setup_recovery_service()
        svc.repo.get_user_by_email.return_value = None
        result = await svc.request_recovery(email="x@x.com", school_id=uuid.uuid4())
        assert "request_id" in result

    @pytest.mark.asyncio
    async def test_request_recovery_creates_otp_and_returns_request_id(
        self, monkeypatch
    ):
        svc, redis = setup_recovery_service()
        user = make_user()
        svc.repo.get_user_by_email.return_value = user
        recovery = SimpleNamespace(
            id=uuid.uuid4(), school_id=uuid.uuid4(), user_id=user.id
        )
        svc.repo.create_recovery_request.return_value = recovery
        # Patch email enqueue to avoid import error
        mock_tasks = MagicMock()
        mock_tasks.enqueue_email = AsyncMock()
        with patch.dict(sys.modules, {"app.core.tasks": mock_tasks}):
            result = await svc.request_recovery(
                email=user.email, school_id=uuid.uuid4()
            )
        assert result["request_id"] == recovery.id
        assert f"recovery_otp:{recovery.id}" in redis.store

    @pytest.mark.asyncio
    async def test_request_recovery_debug_reveal_otp(self, monkeypatch):
        svc, redis = setup_recovery_service()
        user = make_user()
        svc.repo.get_user_by_email.return_value = user
        recovery = SimpleNamespace(
            id=uuid.uuid4(), school_id=uuid.uuid4(), user_id=user.id
        )
        svc.repo.create_recovery_request.return_value = recovery
        monkeypatch.setattr(
            auth_module.settings, "app_env", "development", raising=False
        )
        monkeypatch.setattr(
            auth_module.settings, "debug_reveal_otp", True, raising=False
        )
        mock_tasks = MagicMock()
        mock_tasks.enqueue_email = AsyncMock()
        with patch.dict(sys.modules, {"app.core.tasks": mock_tasks}):
            result = await svc.request_recovery(
                email=user.email, school_id=uuid.uuid4()
            )
        assert "otp" in result

    @pytest.mark.asyncio
    async def test_verify_otp_not_found_raises(self):
        svc, _ = setup_recovery_service()
        svc.repo.get_recovery_request.return_value = None
        with pytest.raises(NotFoundError):
            await svc.verify_otp(request_id=uuid.uuid4(), otp="123456")

    @pytest.mark.asyncio
    async def test_verify_otp_not_pending_raises_conflict(self):
        svc, _ = setup_recovery_service()
        recovery = SimpleNamespace(
            id=uuid.uuid4(),
            status="verified",
            expires_at=None,
            lock_until=None,
            school_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            attempts=0,
        )
        svc.repo.get_recovery_request.return_value = recovery
        with pytest.raises(ConflictError):
            await svc.verify_otp(request_id=recovery.id, otp="123456")

    @pytest.mark.asyncio
    async def test_verify_otp_expired_raises(self):
        svc, _ = setup_recovery_service()
        recovery = SimpleNamespace(
            id=uuid.uuid4(),
            status="pending",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            lock_until=None,
            school_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            attempts=0,
        )
        svc.repo.get_recovery_request.return_value = recovery
        with pytest.raises(AuthenticationError, match="expired"):
            await svc.verify_otp(request_id=recovery.id, otp="123456")

    @pytest.mark.asyncio
    async def test_verify_otp_locked_raises_rate_limit(self):
        svc, _ = setup_recovery_service()
        recovery = SimpleNamespace(
            id=uuid.uuid4(),
            status="pending",
            expires_at=None,
            lock_until=datetime.now(timezone.utc) + timedelta(minutes=30),
            school_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            attempts=5,
        )
        svc.repo.get_recovery_request.return_value = recovery
        with pytest.raises(RateLimitError):
            await svc.verify_otp(request_id=recovery.id, otp="123456")

    @pytest.mark.asyncio
    async def test_verify_otp_redis_key_missing_raises(self):
        svc, _ = setup_recovery_service()
        rid = uuid.uuid4()
        recovery = SimpleNamespace(
            id=rid,
            status="pending",
            expires_at=None,
            lock_until=None,
            school_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            attempts=0,
        )
        svc.repo.get_recovery_request.return_value = recovery
        # Don't put anything in redis → OTP key missing
        with pytest.raises(AuthenticationError, match="expired"):
            await svc.verify_otp(request_id=rid, otp="123456")

    @pytest.mark.asyncio
    async def test_verify_otp_wrong_otp_increments_attempts(self):
        svc, redis = setup_recovery_service()
        rid = uuid.uuid4()
        recovery = SimpleNamespace(
            id=rid,
            status="pending",
            expires_at=None,
            lock_until=None,
            school_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            attempts=0,
        )
        svc.repo.get_recovery_request.return_value = recovery
        correct_hash = hashlib.sha256("654321".encode()).hexdigest()
        redis.store[f"recovery_otp:{rid}"] = correct_hash
        svc.repo.save_recovery_request = AsyncMock()

        with pytest.raises(AuthenticationError, match="Invalid OTP"):
            await svc.verify_otp(request_id=rid, otp="111111")

        assert recovery.attempts == 1

    @pytest.mark.asyncio
    async def test_verify_otp_max_attempts_sets_lock(self):
        svc, redis = setup_recovery_service()
        rid = uuid.uuid4()
        recovery = SimpleNamespace(
            id=rid,
            status="pending",
            expires_at=None,
            lock_until=None,
            school_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            attempts=4,
        )
        svc.repo.get_recovery_request.return_value = recovery
        correct_hash = hashlib.sha256("000000".encode()).hexdigest()
        redis.store[f"recovery_otp:{rid}"] = correct_hash
        svc.repo.save_recovery_request = AsyncMock()

        with pytest.raises(AuthenticationError, match="Invalid OTP"):
            await svc.verify_otp(request_id=rid, otp="111111")

        assert recovery.lock_until is not None

    @pytest.mark.asyncio
    async def test_verify_otp_correct_transitions_to_verified(self):
        svc, redis = setup_recovery_service()
        rid = uuid.uuid4()
        correct_otp = "123456"
        correct_hash = hashlib.sha256(correct_otp.encode()).hexdigest()
        recovery = SimpleNamespace(
            id=rid,
            status="pending",
            expires_at=None,
            lock_until=None,
            school_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            attempts=0,
        )
        svc.repo.get_recovery_request.return_value = recovery
        redis.store[f"recovery_otp:{rid}"] = correct_hash
        svc.repo.save_recovery_request = AsyncMock()

        result = await svc.verify_otp(request_id=rid, otp=correct_otp)
        assert result["message"] == "OTP verified successfully"
        assert recovery.status == "verified"
        assert f"recovery_otp:{rid}" not in redis.store

    @pytest.mark.asyncio
    async def test_reset_password_not_found_raises(self):
        svc, _ = setup_recovery_service()
        svc.repo.get_recovery_request.return_value = None
        with pytest.raises(NotFoundError):
            await svc.reset_password(uuid.uuid4(), "NewP@ss1!")

    @pytest.mark.asyncio
    async def test_reset_password_not_verified_raises_conflict(self):
        svc, _ = setup_recovery_service()
        recovery = SimpleNamespace(
            id=uuid.uuid4(),
            status="pending",
            user_id=uuid.uuid4(),
            school_id=uuid.uuid4(),
        )
        svc.repo.get_recovery_request.return_value = recovery
        with pytest.raises(ConflictError, match="verified"):
            await svc.reset_password(recovery.id, "NewP@ss1!")

    @pytest.mark.asyncio
    async def test_reset_password_in_history_raises(self, monkeypatch):
        svc, _ = setup_recovery_service()
        recovery = SimpleNamespace(
            id=uuid.uuid4(),
            status="verified",
            user_id=uuid.uuid4(),
            school_id=uuid.uuid4(),
        )
        svc.repo.get_recovery_request.return_value = recovery
        user = make_user()
        svc.repo.get_user_by_id.return_value = user
        monkeypatch.setattr(
            "app.core.password_policy.password_validator",
            SimpleNamespace(validate=lambda *_a, **_k: None),
        )
        history_entry = SimpleNamespace(password_hash="any-hash")
        # verify_password always returns True so the history check fires
        monkeypatch.setattr(auth_module, "verify_password", lambda *_: True)
        svc.repo.get_password_history_by_user.return_value = [history_entry]

        with pytest.raises(ValidationError, match="used recently"):
            await svc.reset_password(recovery.id, "SameOldPassword1!")

    @pytest.mark.asyncio
    async def test_reset_password_success(self, monkeypatch):
        svc, _ = setup_recovery_service()
        recovery = SimpleNamespace(
            id=uuid.uuid4(),
            status="verified",
            user_id=uuid.uuid4(),
            school_id=uuid.uuid4(),
        )
        svc.repo.get_recovery_request.return_value = recovery
        user = make_user()
        svc.repo.get_user_by_id.return_value = user
        monkeypatch.setattr(
            "app.core.password_policy.password_validator",
            SimpleNamespace(validate=lambda *_a, **_k: None),
        )
        monkeypatch.setattr(auth_module, "verify_password", lambda *_: False)
        monkeypatch.setattr(auth_module, "hash_password", lambda _: "new-hash")
        svc.repo.get_password_history_by_user.return_value = []
        svc.repo.save_user = AsyncMock()
        svc.repo.save_recovery_request = AsyncMock()

        result = await svc.reset_password(recovery.id, "NewP@ss1!")
        assert result["message"] == "Password reset successfully"
        assert recovery.status == "reset"
        svc.repo.revoke_all_sessions.assert_awaited_once()


# ---------------------------------------------------------------------------
# TwoFactorService
# ---------------------------------------------------------------------------


def setup_2fa_service():
    redis = FakeRedis()
    svc = TwoFactorService(AsyncMock(), redis)
    svc.repo = AsyncMock()
    svc.audit = AsyncMock()
    return svc, redis


class TestTwoFactorService:
    @pytest.mark.asyncio
    async def test_setup_user_not_found_raises(self):
        svc, _ = setup_2fa_service()
        svc.repo.get_user_by_id.return_value = None
        with pytest.raises(NotFoundError):
            await svc.setup(uuid.uuid4(), uuid.uuid4())

    @pytest.mark.asyncio
    async def test_setup_already_enabled_raises_conflict(self):
        svc, _ = setup_2fa_service()
        user = make_user(totp_enabled=True)
        svc.repo.get_user_by_id.return_value = user
        with pytest.raises(ConflictError, match="already enabled"):
            await svc.setup(user.id, uuid.uuid4())

    @pytest.mark.asyncio
    async def test_setup_success_returns_secret_and_uri(self, monkeypatch):
        svc, _ = setup_2fa_service()
        user = make_user()
        svc.repo.get_user_by_id.return_value = user
        svc.repo.save_user = AsyncMock()
        monkeypatch.setattr(
            "app.core.totp.generate_totp_secret",
            lambda: "TESTSECRETXXX",
        )
        monkeypatch.setattr(
            "app.core.totp.get_provisioning_uri",
            lambda secret, email: f"otpauth://totp/{email}?secret={secret}",
        )

        result = await svc.setup(user.id, uuid.uuid4())
        assert result["secret"] == "TESTSECRETXXX"
        assert "provisioning_uri" in result

    @pytest.mark.asyncio
    async def test_verify_setup_user_not_found_raises(self):
        svc, _ = setup_2fa_service()
        svc.repo.get_user_by_id.return_value = None
        with pytest.raises(NotFoundError):
            await svc.verify_setup(uuid.uuid4(), uuid.uuid4(), "123456")

    @pytest.mark.asyncio
    async def test_verify_setup_already_enabled_raises_conflict(self):
        svc, _ = setup_2fa_service()
        user = make_user(totp_enabled=True)
        svc.repo.get_user_by_id.return_value = user
        with pytest.raises(ConflictError):
            await svc.verify_setup(user.id, uuid.uuid4(), "123456")

    @pytest.mark.asyncio
    async def test_verify_setup_no_secret_raises_validation(self):
        svc, _ = setup_2fa_service()
        user = make_user()
        user.totp_secret = None
        svc.repo.get_user_by_id.return_value = user
        with pytest.raises(ValidationError, match="No 2FA setup"):
            await svc.verify_setup(user.id, uuid.uuid4(), "123456")

    @pytest.mark.asyncio
    async def test_verify_setup_invalid_code_raises(self, monkeypatch):
        svc, _ = setup_2fa_service()
        user = make_user()
        user.totp_secret = "SECRET"
        svc.repo.get_user_by_id.return_value = user
        monkeypatch.setattr("app.core.totp.verify_totp_code", lambda *_: False)
        with pytest.raises(AuthenticationError, match="Invalid TOTP"):
            await svc.verify_setup(user.id, uuid.uuid4(), "000000")

    @pytest.mark.asyncio
    async def test_verify_setup_success_activates_2fa(self, monkeypatch):
        svc, _ = setup_2fa_service()
        user = make_user()
        user.totp_secret = "SECRET"
        svc.repo.get_user_by_id.return_value = user
        svc.repo.save_user = AsyncMock()
        monkeypatch.setattr("app.core.totp.verify_totp_code", lambda *_: True)
        monkeypatch.setattr(
            "app.core.totp.generate_backup_codes", lambda: ["CODE1", "CODE2"]
        )
        monkeypatch.setattr(
            "app.core.totp.hash_backup_codes", lambda codes: ["H1", "H2"]
        )

        result = await svc.verify_setup(user.id, uuid.uuid4(), "123456")
        assert "backup_codes" in result
        assert user.totp_enabled is True

    @pytest.mark.asyncio
    async def test_disable_user_not_found_raises(self):
        svc, _ = setup_2fa_service()
        svc.repo.get_user_by_id.return_value = None
        with pytest.raises(NotFoundError):
            await svc.disable(uuid.uuid4(), uuid.uuid4(), "123456")

    @pytest.mark.asyncio
    async def test_disable_2fa_not_enabled_raises(self):
        svc, _ = setup_2fa_service()
        user = make_user(totp_enabled=False)
        svc.repo.get_user_by_id.return_value = user
        with pytest.raises(ConflictError, match="not enabled"):
            await svc.disable(user.id, uuid.uuid4(), "123456")

    @pytest.mark.asyncio
    async def test_disable_invalid_code_raises(self, monkeypatch):
        svc, _ = setup_2fa_service()
        user = make_user(totp_enabled=True)
        user.totp_secret = "SECRET"
        user.backup_codes = json.dumps([])
        svc.repo.get_user_by_id.return_value = user
        monkeypatch.setattr("app.core.totp.verify_totp_code", lambda *_: False)
        monkeypatch.setattr("app.core.totp.verify_backup_code", lambda *_: None)
        with pytest.raises(AuthenticationError, match="Invalid"):
            await svc.disable(user.id, uuid.uuid4(), "999999")

    @pytest.mark.asyncio
    async def test_disable_success_with_totp_code(self, monkeypatch):
        svc, _ = setup_2fa_service()
        user = make_user(totp_enabled=True)
        user.totp_secret = "SECRET"
        user.backup_codes = json.dumps(["H1"])
        svc.repo.get_user_by_id.return_value = user
        svc.repo.save_user = AsyncMock()
        monkeypatch.setattr("app.core.totp.verify_totp_code", lambda *_: True)

        result = await svc.disable(user.id, uuid.uuid4(), "123456")
        assert result["message"] == "Two-factor authentication disabled successfully."
        assert user.totp_enabled is False
        assert user.totp_secret is None

    @pytest.mark.asyncio
    async def test_disable_success_with_backup_code(self, monkeypatch):
        svc, _ = setup_2fa_service()
        user = make_user(totp_enabled=True)
        user.totp_secret = "SECRET"
        hashed = ["HASHVALUE"]
        user.backup_codes = json.dumps(hashed)
        svc.repo.get_user_by_id.return_value = user
        svc.repo.save_user = AsyncMock()
        # 8-char code → not 6-digit → goes straight to backup check
        monkeypatch.setattr("app.core.totp.verify_backup_code", lambda code, codes: 0)

        result = await svc.disable(user.id, uuid.uuid4(), "BACKUPC1")
        assert result["message"] == "Two-factor authentication disabled successfully."

    @pytest.mark.asyncio
    async def test_verify_login_expired_temp_token_raises(self):
        svc, _ = setup_2fa_service()
        # Redis has no 2fa_temp key → expired
        with pytest.raises(AuthenticationError, match="expired"):
            await svc.verify_login(temp_token="missing-token", code="123456")

    @pytest.mark.asyncio
    async def test_verify_login_user_not_found_raises(self):
        svc, redis = setup_2fa_service()
        temp_token = "valid-temp-token"
        temp_data = json.dumps(
            {
                "user_id": str(uuid.uuid4()),
                "school_id": str(uuid.uuid4()),
                "role": STD,
                "source": "web",
                "ip_address": None,
                "user_agent": None,
                "device_name": None,
                "device_fingerprint": None,
            }
        )
        redis.store[f"2fa_temp:{temp_token}"] = temp_data
        svc.repo.get_user_by_id.return_value = None

        with pytest.raises(AuthenticationError, match="Invalid 2FA state"):
            await svc.verify_login(temp_token=temp_token, code="123456")

    @pytest.mark.asyncio
    async def test_verify_login_invalid_code_records_failure(self, monkeypatch):
        svc, redis = setup_2fa_service()
        temp_token = "tok"
        user_id = uuid.uuid4()
        school_id = uuid.uuid4()
        temp_data = json.dumps(
            {
                "user_id": str(user_id),
                "school_id": str(school_id),
                "role": STD,
                "source": "web",
                "ip_address": None,
                "user_agent": None,
                "device_name": None,
                "device_fingerprint": None,
            }
        )
        redis.store[f"2fa_temp:{temp_token}"] = temp_data
        user = make_user(totp_enabled=True)
        user.id = user_id
        user.totp_secret = "SECRET"
        user.backup_codes = json.dumps([])
        svc.repo.get_user_by_id.return_value = user
        monkeypatch.setattr("app.core.totp.verify_totp_code", lambda *_: False)
        monkeypatch.setattr("app.core.totp.verify_backup_code", lambda *_: None)

        with patch.object(AuthService, "_record_login_history", AsyncMock()):
            with pytest.raises(AuthenticationError, match="Invalid TOTP"):
                await svc.verify_login(temp_token=temp_token, code="000000")

    @pytest.mark.asyncio
    async def test_verify_login_success_totp(self, monkeypatch):
        svc, redis = setup_2fa_service()
        temp_token = "tok2"
        user_id = uuid.uuid4()
        school_id = uuid.uuid4()
        temp_data = json.dumps(
            {
                "user_id": str(user_id),
                "school_id": str(school_id),
                "role": STD,
                "source": "web",
                "ip_address": "1.2.3.4",
                "user_agent": "UA",
                "device_name": None,
                "device_fingerprint": None,
            }
        )
        redis.store[f"2fa_temp:{temp_token}"] = temp_data
        user = make_user(totp_enabled=True)
        user.id = user_id
        user.totp_secret = "SECRET"
        user.backup_codes = json.dumps([])
        svc.repo.get_user_by_id.return_value = user
        monkeypatch.setattr("app.core.totp.verify_totp_code", lambda *_: True)
        monkeypatch.setattr(auth_module, "get_correlation_id", lambda: None)

        session = SimpleNamespace(id=uuid.uuid4())
        repo_in_uow, audit_in_uow, login_history_in_uow, uow = patch_uow(monkeypatch)
        repo_in_uow.count_active_sessions.return_value = 0
        login_history_in_uow.get_device_fingerprints.return_value = []
        repo_in_uow.create_session.return_value = session

        # Mock _issue_token_bundle on the AuthService created inside verify_login
        mock_bundle = {"access_token": "2fa-acc", "session_id": session.id}
        with patch.object(
            AuthService, "_issue_token_bundle", AsyncMock(return_value=mock_bundle)
        ):
            result = await svc.verify_login(temp_token=temp_token, code="123456")

        assert result["access_token"] == "2fa-acc"
        assert f"2fa_temp:{temp_token}" not in redis.store

    @pytest.mark.asyncio
    async def test_verify_login_backup_code_consumes_code(self, monkeypatch):
        svc, redis = setup_2fa_service()
        temp_token = "tok3"
        user_id = uuid.uuid4()
        school_id = uuid.uuid4()
        temp_data = json.dumps(
            {
                "user_id": str(user_id),
                "school_id": str(school_id),
                "role": STD,
                "source": "web",
                "ip_address": None,
                "user_agent": None,
                "device_name": None,
                "device_fingerprint": None,
            }
        )
        redis.store[f"2fa_temp:{temp_token}"] = temp_data
        user = make_user(totp_enabled=True)
        user.id = user_id
        user.totp_secret = "SECRET"
        user.backup_codes = json.dumps(["H1", "H2"])
        svc.repo.get_user_by_id.return_value = user
        monkeypatch.setattr("app.core.totp.verify_totp_code", lambda *_: False)
        monkeypatch.setattr("app.core.totp.verify_backup_code", lambda code, codes: 0)
        monkeypatch.setattr(auth_module, "get_correlation_id", lambda: None)

        session = SimpleNamespace(id=uuid.uuid4())
        repo_in_uow, audit_in_uow, login_history_in_uow, uow = patch_uow(monkeypatch)
        repo_in_uow.count_active_sessions.return_value = 0
        login_history_in_uow.get_device_fingerprints.return_value = []
        repo_in_uow.create_session.return_value = session
        svc.repo.save_user = AsyncMock()

        mock_bundle = {"access_token": "bk-acc", "session_id": session.id}
        with patch.object(
            AuthService, "_issue_token_bundle", AsyncMock(return_value=mock_bundle)
        ):
            result = await svc.verify_login(temp_token=temp_token, code="BACKUP1")

        assert result["access_token"] == "bk-acc"
        # Backup code consumed (H1 removed from list)
        remaining = json.loads(user.backup_codes)
        assert len(remaining) == 1


# ---------------------------------------------------------------------------
# EmailVerificationService
# ---------------------------------------------------------------------------


def setup_email_service():
    redis = FakeRedis()
    svc = EmailVerificationService(AsyncMock(), redis)
    svc.repo = AsyncMock()
    svc.audit = AsyncMock()
    return svc, redis


class TestEmailVerificationService:
    @pytest.mark.asyncio
    async def test_send_verification_otp_stores_hash_in_redis(self):
        svc, redis = setup_email_service()
        uid = uuid.uuid4()
        school_id = uuid.uuid4()
        result = await svc.send_verification_otp(
            user_id=uid, school_id=school_id, email="u@e.com"
        )
        assert result["message"] == "Verification email sent."
        key = f"email_verify_otp:{uid}:{school_id}"
        assert key in redis.store

    @pytest.mark.asyncio
    async def test_send_verification_otp_debug_reveals_otp(self, monkeypatch):
        svc, redis = setup_email_service()
        monkeypatch.setattr(
            auth_module.settings, "app_env", "development", raising=False
        )
        monkeypatch.setattr(
            auth_module.settings, "debug_reveal_otp", True, raising=False
        )
        uid = uuid.uuid4()
        result = await svc.send_verification_otp(
            user_id=uid, school_id=uuid.uuid4(), email="u@e.com"
        )
        assert "otp" in result

    @pytest.mark.asyncio
    async def test_verify_email_user_not_found_raises(self):
        svc, _ = setup_email_service()
        svc.repo.get_user_in_school.return_value = None
        with pytest.raises(NotFoundError):
            await svc.verify_email(uuid.uuid4(), uuid.uuid4(), "123456")

    @pytest.mark.asyncio
    async def test_verify_email_already_verified_returns_ok(self):
        svc, _ = setup_email_service()
        user = make_user(email_verified_at=datetime.now(timezone.utc))
        svc.repo.get_user_in_school.return_value = user
        result = await svc.verify_email(uuid.uuid4(), uuid.uuid4(), "123456")
        assert "already verified" in result["message"]

    @pytest.mark.asyncio
    async def test_verify_email_otp_expired_raises(self):
        svc, _ = setup_email_service()
        user = make_user(email_verified_at=None)
        svc.repo.get_user_in_school.return_value = user
        # No OTP in redis → expired
        with pytest.raises(AuthenticationError, match="expired"):
            await svc.verify_email(uuid.uuid4(), uuid.uuid4(), "123456")

    @pytest.mark.asyncio
    async def test_verify_email_wrong_otp_raises(self):
        svc, redis = setup_email_service()
        uid = uuid.uuid4()
        school_id = uuid.uuid4()
        user = make_user(email_verified_at=None)
        svc.repo.get_user_in_school.return_value = user
        correct_hash = hashlib.sha256("654321".encode()).hexdigest()
        redis.store[f"email_verify_otp:{uid}:{school_id}"] = correct_hash

        with pytest.raises(AuthenticationError, match="Invalid"):
            await svc.verify_email(uid, school_id, "111111")

    @pytest.mark.asyncio
    async def test_verify_email_success_sets_verified_at(self):
        svc, redis = setup_email_service()
        uid = uuid.uuid4()
        school_id = uuid.uuid4()
        user = make_user(email_verified_at=None)
        svc.repo.get_user_in_school.return_value = user
        svc.repo.save_user = AsyncMock()
        correct_otp = "123456"
        redis.store[f"email_verify_otp:{uid}:{school_id}"] = hashlib.sha256(
            correct_otp.encode()
        ).hexdigest()

        result = await svc.verify_email(uid, school_id, correct_otp)
        assert result["message"] == "Email verified successfully."
        assert user.email_verified_at is not None
        assert f"email_verify_otp:{uid}:{school_id}" not in redis.store


# ---------------------------------------------------------------------------
# Security non-regression: cross-school login
# ---------------------------------------------------------------------------


class TestSecurityNonRegression:
    """Verify that a user from school A cannot log in with school B's ID."""

    @pytest.mark.asyncio
    async def test_cross_school_login_returns_404_no_membership(self, monkeypatch):
        """User exists, correct password, but no membership in target school → 404."""
        svc, _ = setup_service()
        school_b = uuid.uuid4()
        user = make_user()  # user is from school_a
        svc.repo.get_user_by_email.return_value = user
        svc.repo.get_membership.return_value = None  # no membership in school_b
        svc._record_login_history = AsyncMock()
        monkeypatch.setattr(auth_module, "verify_password", lambda *_: True)
        monkeypatch.setattr(
            auth_module.settings, "account_lockout_enabled", False, raising=False
        )

        with pytest.raises(NotFoundError) as exc_info:
            await svc.login(email=user.email, password="correct", school_id=school_b)

        assert exc_info.value.error_code == "ERR-IAM-404"

    @pytest.mark.asyncio
    async def test_cross_school_login_unknown_email_returns_401(self, monkeypatch):
        """Email not found in school B → generic 401, no user enumeration."""
        svc, _ = setup_service()
        school_b = uuid.uuid4()
        svc.repo.get_user_by_email.return_value = None  # not in school_b
        svc.repo.get_school_by_id.return_value = SimpleNamespace(id=school_b)
        svc._record_login_history = AsyncMock()
        monkeypatch.setattr(
            auth_module.settings, "account_lockout_enabled", False, raising=False
        )

        with pytest.raises(AuthenticationError) as exc_info:
            await svc.login(
                email="user@schoola.ma", password="anything", school_id=school_b
            )

        assert exc_info.value.error_code == "ERR-IAM-401"
