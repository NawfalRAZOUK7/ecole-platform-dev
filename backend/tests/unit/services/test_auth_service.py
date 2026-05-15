"""Unit tests for auth service."""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.dependencies import AuthContext
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
    RateLimitError,
)
import app.services.auth.auth as auth_module
from app.services.auth.auth import AuthService


def make_auth(role: str = "ADM") -> AuthContext:
    return AuthContext(
        user_id=uuid.uuid4(),
        role=role,
        school_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        permissions=set(),
    )


def make_user(
    school_id: uuid.UUID,
    *,
    status: str = "active",
    totp_enabled: bool = False,
):
    return SimpleNamespace(
        id=uuid.uuid4(),
        email="admin@example.test",
        password_hash="hashed-password",
        full_name="Admin User",
        status=status,
        school_id=school_id,
        totp_enabled=totp_enabled,
    )


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

    async def execute(self) -> None:
        for op in self.ops:
            if op[0] == "incr":
                key = op[1]
                self.redis.store[key] = int(self.redis.store.get(key, 0)) + 1
            elif op[0] == "expire":
                self.redis.expirations[op[1]] = op[2]


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, object] = {}
        self.expirations: dict[str, int] = {}

    async def get(self, key: str):
        return self.store.get(key)

    async def setex(self, key: str, ttl: int, value):
        self.store[key] = value
        self.expirations[key] = ttl

    async def delete(self, *keys: str):
        deleted = 0
        for key in keys:
            if key in self.store:
                deleted += 1
                del self.store[key]
        return deleted

    def pipeline(self) -> FakePipeline:
        return FakePipeline(self)


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.session = AsyncMock()
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def commit(self) -> None:
        self.committed = True


def setup_service():
    redis = FakeRedis()
    service = AuthService(AsyncMock(), redis)
    service.repo = AsyncMock()
    service.audit = AsyncMock()
    service._dispatch_event = AsyncMock()
    return service, redis


def patch_auth_uow(monkeypatch: pytest.MonkeyPatch):
    repo_in_uow = AsyncMock()
    audit = AsyncMock()
    login_history_repo = AsyncMock()
    uow = FakeUnitOfWork()

    monkeypatch.setattr(auth_module, "UnitOfWork", lambda _db: uow)
    monkeypatch.setattr(auth_module, "AuthRepository", lambda _session: repo_in_uow)
    monkeypatch.setattr(auth_module, "AuditService", lambda _session: audit)
    monkeypatch.setattr(
        auth_module,
        "LoginHistoryRepository",
        lambda _session: login_history_repo,
    )

    return repo_in_uow, audit, login_history_repo, uow


class TestAuthHelpers:
    def test_device_fingerprint_masks_ipv4_by_subnet(self):
        service, _redis = setup_service()
        first = service._build_device_fingerprint("Mozilla/5.0", "10.0.0.1")
        second = service._build_device_fingerprint("Mozilla/5.0", "10.0.0.254")
        third = service._build_device_fingerprint("Mozilla/5.0", "10.0.1.1")

        assert first == second
        assert first != third

    def test_device_fingerprint_returns_none_without_inputs(self):
        service, _redis = setup_service()
        assert service._build_device_fingerprint(None, None) is None


class TestLogin:
    @pytest.mark.asyncio
    async def test_rate_limited_login_raises(self):
        service, redis = setup_service()
        user = make_user(uuid.uuid4())
        rate_key = f"login_attempts:{user.email}:{user.school_id}"
        redis.store[rate_key] = 5
        service.repo.get_user_by_email.return_value = user
        service._record_login_history = AsyncMock()

        with pytest.raises(RateLimitError, match="Too many login attempts"):
            await service.login(
                email=user.email,
                password="bad-password",
                school_id=user.school_id,
            )

        service._record_login_history.assert_awaited_once()
        service.audit.log_event.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_wrong_password_increments_attempt_counter(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        service, redis = setup_service()
        school_id = uuid.uuid4()
        user = make_user(school_id)
        service.repo.get_user_by_email.return_value = user
        service._record_login_history = AsyncMock()
        monkeypatch.setattr(auth_module, "verify_password", lambda _pwd, _hash: False)

        with pytest.raises(AuthenticationError, match="Invalid email or password"):
            await service.login(
                email=user.email,
                password="bad-password",
                school_id=school_id,
            )

        assert redis.store[f"login_attempts:{user.email}:{school_id}"] == 1
        service.audit.log_event.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_invalid_school_id_skips_audit_and_returns_401(self):
        service, redis = setup_service()
        school_id = uuid.uuid4()
        email = "admin@example.test"
        service.repo.get_user_by_email.return_value = None
        service.repo.get_school_by_id.return_value = None
        service._record_login_history = AsyncMock()

        with pytest.raises(AuthenticationError, match="Invalid email or password"):
            await service.login(
                email=email,
                password="bad-password",
                school_id=school_id,
            )

        assert redis.store[f"login_attempts:{email}:{school_id}"] == 1
        service.audit.log_event.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_rejects_inactive_user(self, monkeypatch: pytest.MonkeyPatch):
        service, _redis = setup_service()
        school_id = uuid.uuid4()
        user = make_user(school_id, status="inactive")
        service.repo.get_user_by_email.return_value = user
        service._record_login_history = AsyncMock()
        monkeypatch.setattr(auth_module, "verify_password", lambda _pwd, _hash: True)

        with pytest.raises(AuthorizationError, match="Account is not active"):
            await service.login(
                email=user.email,
                password="secret",
                school_id=school_id,
            )

        service._record_login_history.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_rejects_login_without_membership(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        service, _redis = setup_service()
        school_id = uuid.uuid4()
        user = make_user(school_id)
        service.repo.get_user_by_email.return_value = user
        service.repo.get_membership.return_value = None
        service._record_login_history = AsyncMock()
        monkeypatch.setattr(auth_module, "verify_password", lambda _pwd, _hash: True)

        with pytest.raises(NotFoundError, match="No active membership"):
            await service.login(
                email=user.email,
                password="secret",
                school_id=school_id,
            )

    @pytest.mark.asyncio
    async def test_totp_enabled_login_returns_temp_token(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        service, redis = setup_service()
        school_id = uuid.uuid4()
        user = make_user(school_id, totp_enabled=True)
        membership = SimpleNamespace(role_code="STD")
        rate_key = f"login_attempts:{user.email}:{school_id}"
        redis.store[rate_key] = 2
        service.repo.get_user_by_email.return_value = user
        service.repo.get_membership.return_value = membership
        monkeypatch.setattr(auth_module, "verify_password", lambda _pwd, _hash: True)

        result = await service.login(
            email=user.email,
            password="secret",
            school_id=school_id,
            ip_address="10.0.0.1",
            user_agent="Mozilla/5.0",
            device_name="Safari",
        )

        assert result["requires_2fa"] is True
        assert f"2fa_temp:{result['temp_token']}" in redis.store
        assert rate_key not in redis.store
        service.audit.log_event.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_successful_login_revokes_oldest_session_and_dispatches_new_device(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        service, redis = setup_service()
        school_id = uuid.uuid4()
        user = make_user(school_id)
        session_id = uuid.uuid4()
        current_session = SimpleNamespace(id=session_id)
        membership = SimpleNamespace(role_code="TCH")
        rate_key = f"login_attempts:{user.email}:{school_id}"
        redis.store[rate_key] = 1
        service.repo.get_user_by_email.return_value = user
        service.repo.get_membership.return_value = membership
        service._issue_token_bundle = AsyncMock(
            return_value={"access_token": "access", "session_id": session_id}
        )
        monkeypatch.setattr(auth_module, "verify_password", lambda _pwd, _hash: True)
        monkeypatch.setattr(auth_module, "get_correlation_id", lambda: None)
        monkeypatch.setattr(
            auth_module.settings, "max_sessions_per_user", 1, raising=False
        )
        repo_in_uow, audit, login_history_repo, uow = patch_auth_uow(monkeypatch)
        repo_in_uow.count_active_sessions.return_value = 1
        repo_in_uow.get_oldest_active_session.return_value = SimpleNamespace(
            id=uuid.uuid4()
        )
        login_history_repo.get_device_fingerprints.return_value = []
        repo_in_uow.create_session.return_value = current_session

        result = await service.login(
            email=user.email,
            password="secret",
            school_id=school_id,
            ip_address="10.0.0.42",
            user_agent="Mozilla/5.0",
            device_name="Chrome",
        )

        assert result["access_token"] == "access"
        repo_in_uow.revoke_session.assert_awaited_once()
        assert (
            login_history_repo.create_login_record.await_args.kwargs["is_new_device"]
            is True
        )
        service._dispatch_event.assert_awaited_once()
        audit.log_event.assert_awaited()
        assert rate_key not in redis.store
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_successful_login_without_new_device_skips_event(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        service, _redis = setup_service()
        school_id = uuid.uuid4()
        user = make_user(school_id)
        membership = SimpleNamespace(role_code="TCH")
        service.repo.get_user_by_email.return_value = user
        service.repo.get_membership.return_value = membership
        service._issue_token_bundle = AsyncMock(
            return_value={"access_token": "access", "session_id": uuid.uuid4()}
        )
        monkeypatch.setattr(auth_module, "verify_password", lambda _pwd, _hash: True)
        monkeypatch.setattr(auth_module, "get_correlation_id", lambda: None)
        repo_in_uow, _audit, login_history_repo, _uow = patch_auth_uow(monkeypatch)
        repo_in_uow.count_active_sessions.return_value = 0
        repo_in_uow.create_session.return_value = SimpleNamespace(id=uuid.uuid4())
        known = service._build_device_fingerprint("Mozilla/5.0", "10.0.0.42")
        login_history_repo.get_device_fingerprints.return_value = [known]

        await service.login(
            email=user.email,
            password="secret",
            school_id=school_id,
            ip_address="10.0.0.42",
            user_agent="Mozilla/5.0",
        )

        service._dispatch_event.assert_not_awaited()


class TestRefresh:
    @pytest.mark.asyncio
    async def test_refresh_rejects_invalid_csrf(self, monkeypatch: pytest.MonkeyPatch):
        service, redis = setup_service()
        session_id = uuid.uuid4()
        monkeypatch.setattr(
            auth_module,
            "decode_refresh_token",
            lambda _token: {
                "session_id": str(session_id),
                "sub": str(uuid.uuid4()),
                "school_id": str(uuid.uuid4()),
                "jti": "expected-jti",
            },
        )
        redis.store[f"csrf:{session_id}"] = "expected-csrf"

        with pytest.raises(AuthorizationError, match="Invalid CSRF token"):
            await service.refresh("refresh-token", csrf_token="wrong-csrf")

    @pytest.mark.asyncio
    async def test_refresh_rejects_revoked_session(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        service, redis = setup_service()
        session_id = uuid.uuid4()
        user_id = uuid.uuid4()
        school_id = uuid.uuid4()
        monkeypatch.setattr(
            auth_module,
            "decode_refresh_token",
            lambda _token: {
                "session_id": str(session_id),
                "sub": str(user_id),
                "school_id": str(school_id),
                "jti": "expected-jti",
            },
        )
        redis.store[f"csrf:{session_id}"] = "csrf-ok"
        service.repo.get_session_by_id.return_value = None

        with pytest.raises(AuthenticationError, match="Session has been revoked"):
            await service.refresh("refresh-token", csrf_token="csrf-ok")

    @pytest.mark.asyncio
    async def test_refresh_detects_replay_and_revokes_session(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        service, redis = setup_service()
        session_id = uuid.uuid4()
        user_id = uuid.uuid4()
        school_id = uuid.uuid4()
        monkeypatch.setattr(
            auth_module,
            "decode_refresh_token",
            lambda _token: {
                "session_id": str(session_id),
                "sub": str(user_id),
                "school_id": str(school_id),
                "jti": "presented-jti",
            },
        )
        redis.store[f"csrf:{session_id}"] = "csrf-ok"
        redis.store[f"refresh_jti:{session_id}"] = "stored-jti"
        service.repo.get_session_by_id.return_value = SimpleNamespace(id=session_id)

        with pytest.raises(AuthenticationError, match="Token has been rotated"):
            await service.refresh("refresh-token", csrf_token="csrf-ok")

        service.repo.revoke_session.assert_awaited_once()
        assert f"refresh_jti:{session_id}" not in redis.store
        assert f"csrf:{session_id}" not in redis.store

    @pytest.mark.asyncio
    async def test_refresh_rotates_tokens_and_audits(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        service, redis = setup_service()
        session_id = uuid.uuid4()
        user_id = uuid.uuid4()
        school_id = uuid.uuid4()
        monkeypatch.setattr(
            auth_module,
            "decode_refresh_token",
            lambda _token: {
                "session_id": str(session_id),
                "sub": str(user_id),
                "school_id": str(school_id),
                "jti": "stored-jti",
            },
        )
        monkeypatch.setattr(
            auth_module, "create_access_token", lambda *_args: "new-access"
        )
        monkeypatch.setattr(
            auth_module,
            "create_refresh_token",
            lambda *_args: ("new-refresh", "new-jti"),
        )
        monkeypatch.setattr(auth_module, "create_csrf_token", lambda: "new-csrf")
        redis.store[f"csrf:{session_id}"] = "csrf-ok"
        redis.store[f"refresh_jti:{session_id}"] = "stored-jti"
        service.repo.get_session_by_id.return_value = SimpleNamespace(id=session_id)
        service.repo.get_membership.return_value = SimpleNamespace(role_code="ADM")

        result = await service.refresh(
            "refresh-token",
            csrf_token="csrf-ok",
            ip_address="127.0.0.1",
        )

        assert result["access_token"] == "new-access"
        assert result["refresh_token"] == "new-refresh"
        assert redis.store[f"refresh_jti:{session_id}"] == "new-jti"
        assert redis.store[f"csrf:{session_id}"] == "new-csrf"
        service.audit.log_event.assert_awaited_once()


class TestImpersonation:
    @pytest.mark.asyncio
    async def test_impersonate_requires_admin_role(self):
        service, _redis = setup_service()
        auth = make_auth("STD")

        with pytest.raises(AuthorizationError, match="Only ADM, DIR, or SUP"):
            await service.impersonate(target_user_id=uuid.uuid4(), admin_auth=auth)

    @pytest.mark.asyncio
    async def test_impersonate_rejects_self(self):
        service, _redis = setup_service()
        auth = make_auth("ADM")

        with pytest.raises(ConflictError, match="Cannot impersonate your own account"):
            await service.impersonate(target_user_id=auth.user_id, admin_auth=auth)

    @pytest.mark.asyncio
    async def test_impersonate_rejects_sup_target(self):
        service, _redis = setup_service()
        auth = make_auth("ADM")
        target_user_id = uuid.uuid4()
        service.repo.get_user_in_school.return_value = SimpleNamespace(
            id=target_user_id
        )
        service.repo.get_membership.return_value = SimpleNamespace(role_code="SUP")

        with pytest.raises(AuthorizationError, match="Cannot impersonate SUP or SYS"):
            await service.impersonate(target_user_id=target_user_id, admin_auth=auth)

    @pytest.mark.asyncio
    async def test_impersonate_returns_shadow_token_bundle(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        service, _redis = setup_service()
        auth = make_auth("ADM")
        target_user_id = uuid.uuid4()
        shadow_session = SimpleNamespace(id=uuid.uuid4())
        service.repo.get_user_in_school.return_value = SimpleNamespace(
            id=target_user_id
        )
        service.repo.get_membership.return_value = SimpleNamespace(role_code="STD")
        service._issue_token_bundle = AsyncMock(return_value={"access_token": "shadow"})
        repo_in_uow, audit, _history_repo, uow = patch_auth_uow(monkeypatch)
        repo_in_uow.create_session.return_value = shadow_session

        result = await service.impersonate(
            target_user_id=target_user_id,
            admin_auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["access_token"] == "shadow"
        assert result["impersonation_active"] is True
        audit.log_event.assert_awaited_once()
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_stop_impersonation_requires_shadow_session(self):
        service, _redis = setup_service()
        service.repo.get_session_by_id.return_value = SimpleNamespace(
            impersonator_id=None
        )

        with pytest.raises(AuthorizationError, match="not an impersonation session"):
            await service.stop_impersonation(session_id=uuid.uuid4())

    @pytest.mark.asyncio
    async def test_stop_impersonation_reuses_original_session(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        service, _redis = setup_service()
        session_id = uuid.uuid4()
        original_session_id = uuid.uuid4()
        school_id = uuid.uuid4()
        impersonator_id = uuid.uuid4()
        current_session = SimpleNamespace(
            id=session_id,
            user_id=uuid.uuid4(),
            school_id=school_id,
            impersonator_id=impersonator_id,
            correlation_id=original_session_id,
        )
        restored_session = SimpleNamespace(
            id=original_session_id,
            user_id=impersonator_id,
            school_id=school_id,
            impersonator_id=None,
        )
        service.repo.get_session_by_id.return_value = current_session
        service._clear_session_tokens = AsyncMock()
        service._issue_token_bundle = AsyncMock(return_value={"access_token": "admin"})
        repo_in_uow, audit, _history_repo, uow = patch_auth_uow(monkeypatch)
        repo_in_uow.get_session_by_id.side_effect = [current_session, restored_session]
        repo_in_uow.get_membership.return_value = SimpleNamespace(role_code="ADM")

        result = await service.stop_impersonation(
            session_id=session_id,
            ip_address="127.0.0.1",
        )

        assert result["access_token"] == "admin"
        assert result["impersonation_active"] is False
        repo_in_uow.revoke_session.assert_awaited_once()
        repo_in_uow.create_session.assert_not_awaited()
        service._clear_session_tokens.assert_awaited_once_with(session_id)
        audit.log_event.assert_awaited_once()
        assert uow.committed is True
