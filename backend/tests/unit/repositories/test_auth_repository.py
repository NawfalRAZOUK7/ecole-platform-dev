"""Mock-based unit tests for app/repositories/auth.py.

Every public method is exercised at least once; branch-creating optional
parameters (school_id, active_only, exclude_session_id, user_id) are
exercised in both their truthy and falsy forms so branch coverage is complete.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from app.repositories.auth import AuthRepository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _uid() -> uuid.UUID:
    return uuid.uuid4()


def _now() -> datetime:
    return datetime.now(timezone.utc)


class _FR:
    """Fake SQLAlchemy execute result."""

    def __init__(self, v=None, many=None, scalar=None, rowcount=1):
        self._v = v
        self._many = many or []
        self._scalar = scalar
        self.rowcount = rowcount

    def scalar_one_or_none(self):
        return self._v

    def scalar_one(self):
        return self._v

    def scalar(self):
        return self._scalar

    def scalars(self):
        return SimpleNamespace(all=lambda: self._many)

    def all(self):
        return self._many


def _db(result=None, *, flush_raises=None):
    """Build a minimal fake async DB session."""
    r = result if result is not None else _FR()
    db = SimpleNamespace(
        execute=AsyncMock(return_value=r),
        add=Mock(),
        flush=AsyncMock(),
        commit=AsyncMock(),
        rollback=AsyncMock(),
        merge=AsyncMock(return_value=r._v),
    )
    if flush_raises:
        db.flush.side_effect = flush_raises
    return db


def _repo(db):
    return AuthRepository(db)


# ---------------------------------------------------------------------------
# get_user_by_email
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_user_by_email_no_school():
    obj = object()
    db = _db(_FR(v=obj))
    result = await _repo(db).get_user_by_email("a@b.ma")
    assert result is obj


@pytest.mark.asyncio
async def test_get_user_by_email_with_school():
    obj = object()
    db = _db(_FR(v=obj))
    result = await _repo(db).get_user_by_email("a@b.ma", school_id=_uid())
    assert result is obj


# ---------------------------------------------------------------------------
# get_user_by_id / get_school_by_id / get_user_in_school
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_user_by_id():
    obj = object()
    db = _db(_FR(v=obj))
    assert await _repo(db).get_user_by_id(_uid()) is obj


@pytest.mark.asyncio
async def test_get_school_by_id():
    obj = object()
    db = _db(_FR(v=obj))
    assert await _repo(db).get_school_by_id(_uid()) is obj


@pytest.mark.asyncio
async def test_get_user_in_school():
    obj = object()
    db = _db(_FR(v=obj))
    assert await _repo(db).get_user_in_school(_uid(), _uid()) is obj


# ---------------------------------------------------------------------------
# get_user_with_memberships
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_user_with_memberships():
    obj = object()
    db = _db(_FR(v=obj))
    assert await _repo(db).get_user_with_memberships(_uid()) is obj


# ---------------------------------------------------------------------------
# create_user / save_user / update_user
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_user():
    school_id = _uid()
    db = _db()
    fake_user = SimpleNamespace(id=_uid(), email="x@test.ma")
    with patch("app.repositories.auth.User", return_value=fake_user):
        result = await _repo(db).create_user(
            school_id=school_id, email="x@test.ma", password_hash="h", full_name="X"
        )
    assert result is fake_user
    db.add.assert_called_once_with(fake_user)
    db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_save_user():
    user = SimpleNamespace(id=_uid())
    db = _db(_FR(v=user))
    result = await _repo(db).save_user(user)
    assert result is user
    db.add.assert_called_once_with(user)


@pytest.mark.asyncio
async def test_update_user():
    obj = object()
    db = _db(_FR(v=obj))
    result = await _repo(db).update_user(_uid(), full_name="New")
    assert result is obj


# ---------------------------------------------------------------------------
# create_membership / get_membership / list_memberships
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_membership():
    fake = SimpleNamespace(id=_uid())
    db = _db()
    with patch("app.repositories.auth.Membership", return_value=fake):
        result = await _repo(db).create_membership(
            user_id=_uid(), school_id=_uid(), role_code="TCH", status="active"
        )
    assert result is fake


@pytest.mark.asyncio
async def test_get_membership_active_only():
    obj = object()
    db = _db(_FR(v=obj))
    result = await _repo(db).get_membership(_uid(), _uid(), active_only=True)
    assert result is obj


@pytest.mark.asyncio
async def test_get_membership_all():
    obj = object()
    db = _db(_FR(v=obj))
    result = await _repo(db).get_membership(_uid(), _uid(), active_only=False)
    assert result is obj


@pytest.mark.asyncio
async def test_list_memberships_default():
    items = [object(), object()]
    db = _db(_FR(many=items))
    result = await _repo(db).list_memberships(_uid())
    assert result == items


@pytest.mark.asyncio
async def test_list_memberships_active_only():
    items = [object()]
    db = _db(_FR(many=items))
    result = await _repo(db).list_memberships(_uid(), active_only=True)
    assert result == items


# ---------------------------------------------------------------------------
# create_*_profile
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_student_profile():
    fake = SimpleNamespace(id=_uid())
    db = _db()
    with patch("app.repositories.auth.StudentProfile", return_value=fake):
        result = await _repo(db).create_student_profile(
            user_id=_uid(), school_id=_uid()
        )
    assert result is fake


@pytest.mark.asyncio
async def test_create_parent_profile():
    fake = SimpleNamespace(id=_uid())
    db = _db()
    with patch("app.repositories.auth.ParentProfile", return_value=fake):
        result = await _repo(db).create_parent_profile(user_id=_uid(), school_id=_uid())
    assert result is fake


@pytest.mark.asyncio
async def test_create_teacher_profile():
    fake = SimpleNamespace(id=_uid())
    db = _db()
    with patch("app.repositories.auth.TeacherProfile", return_value=fake):
        result = await _repo(db).create_teacher_profile(
            user_id=_uid(), school_id=_uid()
        )
    assert result is fake


# ---------------------------------------------------------------------------
# ParentChildLink
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_parent_child_link():
    fake = SimpleNamespace(id=_uid())
    db = _db()
    with patch("app.repositories.auth.ParentChildLink", return_value=fake):
        result = await _repo(db).create_parent_child_link(
            parent_user_id=_uid(), child_user_id=_uid()
        )
    assert result is fake


# ---------------------------------------------------------------------------
# Session CRUD
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_session():
    fake = SimpleNamespace(id=_uid())
    db = _db()
    with patch("app.repositories.auth.Session", return_value=fake):
        result = await _repo(db).create_session(user_id=_uid(), school_id=_uid())
    assert result is fake


@pytest.mark.asyncio
async def test_save_session():
    sess = SimpleNamespace(id=_uid())
    db = _db(_FR(v=sess))
    result = await _repo(db).save_session(sess)
    assert result is sess


@pytest.mark.asyncio
async def test_get_session_by_id_any():
    obj = object()
    db = _db(_FR(v=obj))
    assert await _repo(db).get_session_by_id(_uid()) is obj


@pytest.mark.asyncio
async def test_get_session_by_id_active_only():
    obj = object()
    db = _db(_FR(v=obj))
    assert await _repo(db).get_session_by_id(_uid(), active_only=True) is obj


@pytest.mark.asyncio
async def test_list_active_sessions():
    items = [object()]
    db = _db(_FR(many=items))
    result = await _repo(db).list_active_sessions(user_id=_uid(), school_id=_uid())
    assert result == items


@pytest.mark.asyncio
async def test_count_active_sessions():
    db = _db(_FR(v=7))
    result = await _repo(db).count_active_sessions(_uid(), _uid())
    assert result == 7


@pytest.mark.asyncio
async def test_count_active_sessions_zero():
    db = _db(_FR(v=None))
    result = await _repo(db).count_active_sessions(_uid(), _uid())
    assert result == 0


@pytest.mark.asyncio
async def test_get_oldest_active_session():
    obj = object()
    db = _db(_FR(v=obj))
    assert await _repo(db).get_oldest_active_session(_uid(), _uid()) is obj


@pytest.mark.asyncio
async def test_revoke_session():
    db = _db()
    await _repo(db).revoke_session(_uid(), _now())
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_revoke_all_sessions_no_exclude():
    fr = _FR()
    fr.rowcount = 3
    db = _db(fr)
    result = await _repo(db).revoke_all_sessions(_uid(), _now())
    assert result == 3


@pytest.mark.asyncio
async def test_revoke_all_sessions_with_exclude():
    fr = _FR()
    fr.rowcount = 2
    db = _db(fr)
    result = await _repo(db).revoke_all_sessions(
        _uid(), _now(), exclude_session_id=_uid()
    )
    assert result == 2


# ---------------------------------------------------------------------------
# InvitationCode
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_invitation_by_code_hash():
    obj = object()
    db = _db(_FR(v=obj))
    assert await _repo(db).get_invitation_by_code_hash("hash123") is obj


@pytest.mark.asyncio
async def test_get_invitation_by_id_no_school():
    obj = object()
    db = _db(_FR(v=obj))
    assert await _repo(db).get_invitation_by_id(_uid()) is obj


@pytest.mark.asyncio
async def test_get_invitation_by_id_with_school():
    obj = object()
    db = _db(_FR(v=obj))
    assert await _repo(db).get_invitation_by_id(_uid(), school_id=_uid()) is obj


@pytest.mark.asyncio
async def test_create_invitation():
    fake = SimpleNamespace(id=_uid())
    db = _db()
    with patch("app.repositories.auth.InvitationCode", return_value=fake):
        result = await _repo(db).create_invitation(school_id=_uid())
    assert result is fake


@pytest.mark.asyncio
async def test_save_invitation():
    invite = SimpleNamespace(id=_uid())
    db = _db(_FR(v=invite))
    result = await _repo(db).save_invitation(invite)
    assert result is invite


@pytest.mark.asyncio
async def test_consume_invitation_found():
    invite_id = _uid()
    invite = SimpleNamespace(id=invite_id, consumed_by=None, consumed_at=None)
    db = _db(_FR(v=invite))
    result = await _repo(db).consume_invitation(
        invite_id, user_id=_uid(), consumed_at=_now()
    )
    assert result is invite


@pytest.mark.asyncio
async def test_consume_invitation_not_found():
    db = _db(_FR(v=None))
    result = await _repo(db).consume_invitation(
        _uid(), user_id=_uid(), consumed_at=_now()
    )
    assert result is None


# ---------------------------------------------------------------------------
# get_student_in_school
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_student_in_school():
    obj = object()
    db = _db(_FR(v=obj))
    assert await _repo(db).get_student_in_school(_uid(), _uid()) is obj


# ---------------------------------------------------------------------------
# AccountRecoveryRequest
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_recovery_request():
    fake = SimpleNamespace(id=_uid())
    db = _db()
    with patch("app.repositories.auth.AccountRecoveryRequest", return_value=fake):
        result = await _repo(db).create_recovery_request(user_id=_uid())
    assert result is fake


@pytest.mark.asyncio
async def test_get_recovery_request():
    obj = object()
    db = _db(_FR(v=obj))
    assert await _repo(db).get_recovery_request(_uid()) is obj


@pytest.mark.asyncio
async def test_save_recovery_request():
    recovery = SimpleNamespace(id=_uid())
    db = _db()
    await _repo(db).save_recovery_request(recovery)
    db.merge.assert_awaited_once_with(recovery)


# ---------------------------------------------------------------------------
# WebAuthn
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_webauthn_credential():
    fake = SimpleNamespace(id=_uid())
    db = _db()
    with patch("app.repositories.auth.WebAuthnCredential", return_value=fake):
        result = await _repo(db).create_webauthn_credential(user_id=_uid())
    assert result is fake


@pytest.mark.asyncio
async def test_get_webauthn_credentials_by_user():
    items = [object()]
    db = _db(_FR(many=items))
    result = await _repo(db).get_webauthn_credentials_by_user(_uid())
    assert list(result) == items


@pytest.mark.asyncio
async def test_get_webauthn_credential_by_id():
    obj = object()
    db = _db(_FR(v=obj))
    assert await _repo(db).get_webauthn_credential_by_id("cred-id") is obj


@pytest.mark.asyncio
async def test_update_webauthn_credential():
    cred = SimpleNamespace(credential_id="abc")
    db = _db()
    await _repo(db).update_webauthn_credential(cred)
    db.merge.assert_awaited_once_with(cred)


@pytest.mark.asyncio
async def test_delete_webauthn_credential():
    fr = _FR()
    fr.rowcount = 1
    db = _db(fr)
    result = await _repo(db).delete_webauthn_credential("cred-id")
    assert result is True


@pytest.mark.asyncio
async def test_delete_webauthn_credential_not_found():
    fr = _FR()
    fr.rowcount = 0
    db = _db(fr)
    result = await _repo(db).delete_webauthn_credential("missing")
    assert result is False


# ---------------------------------------------------------------------------
# OAuthAccount
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_oauth_account():
    fake = SimpleNamespace(id=_uid())
    db = _db()
    with patch("app.repositories.auth.OAuthAccount", return_value=fake):
        result = await _repo(db).create_oauth_account(user_id=_uid())
    assert result is fake


@pytest.mark.asyncio
async def test_get_oauth_account_by_provider_user_id():
    obj = object()
    db = _db(_FR(v=obj))
    result = await _repo(db).get_oauth_account_by_provider_user_id("google", "uid-123")
    assert result is obj


@pytest.mark.asyncio
async def test_get_oauth_accounts_by_user():
    items = [object()]
    db = _db(_FR(many=items))
    result = await _repo(db).get_oauth_accounts_by_user(_uid())
    assert list(result) == items


@pytest.mark.asyncio
async def test_update_oauth_account():
    acct = SimpleNamespace(id=_uid())
    db = _db()
    await _repo(db).update_oauth_account(acct)
    db.merge.assert_awaited_once_with(acct)


@pytest.mark.asyncio
async def test_delete_oauth_account():
    fr = _FR()
    fr.rowcount = 1
    db = _db(fr)
    assert await _repo(db).delete_oauth_account(_uid()) is True


@pytest.mark.asyncio
async def test_delete_oauth_account_not_found():
    fr = _FR()
    fr.rowcount = 0
    db = _db(fr)
    assert await _repo(db).delete_oauth_account(_uid()) is False


# ---------------------------------------------------------------------------
# PasswordHistory
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_password_history():
    fake = SimpleNamespace(id=_uid())
    db = _db()
    with patch("app.repositories.auth.PasswordHistory", return_value=fake):
        result = await _repo(db).create_password_history(user_id=_uid())
    assert result is fake


@pytest.mark.asyncio
async def test_get_password_history_by_user():
    items = [object(), object()]
    db = _db(_FR(many=items))
    result = await _repo(db).get_password_history_by_user(_uid())
    assert list(result) == items


@pytest.mark.asyncio
async def test_delete_old_password_history():
    db = _db()
    await _repo(db).delete_old_password_history(_uid(), keep_count=5)
    assert db.execute.await_count == 1


# ---------------------------------------------------------------------------
# FailedLoginAttempt
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_failed_login_attempt_success():
    fake = SimpleNamespace(id=_uid())
    db = _db()
    with patch("app.repositories.auth.FailedLoginAttempt", return_value=fake):
        result = await _repo(db).create_failed_login_attempt(
            email="bad@test.ma", school_id=_uid()
        )
    assert result is fake


@pytest.mark.asyncio
async def test_create_failed_login_attempt_integrity_error():
    fake = SimpleNamespace(id=_uid())
    db = _db(flush_raises=IntegrityError("stmt", "params", Exception("fk")))
    db.rollback = AsyncMock()
    with patch("app.repositories.auth.FailedLoginAttempt", return_value=fake):
        result = await _repo(db).create_failed_login_attempt(
            email="bad@test.ma", school_id=_uid()
        )
    assert result is None
    db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_count_failed_login_attempts_no_user_id():
    db = _db(_FR(scalar=3))
    result = await _repo(db).count_failed_login_attempts("bad@test.ma")
    assert result == 3


@pytest.mark.asyncio
async def test_count_failed_login_attempts_with_user_id():
    db = _db(_FR(scalar=1))
    result = await _repo(db).count_failed_login_attempts("bad@test.ma", user_id=_uid())
    assert result == 1


@pytest.mark.asyncio
async def test_count_failed_login_attempts_none_returns_zero():
    db = _db(_FR(scalar=None))
    result = await _repo(db).count_failed_login_attempts("bad@test.ma")
    assert result == 0


@pytest.mark.asyncio
async def test_delete_old_failed_login_attempts():
    db = _db()
    await _repo(db).delete_old_failed_login_attempts(days=7)
    db.execute.assert_awaited_once()


# ---------------------------------------------------------------------------
# KnownLocation / KnownDevice
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_known_location():
    fake = SimpleNamespace(id=_uid())
    db = _db()
    with patch("app.repositories.auth.KnownLocation", return_value=fake):
        result = await _repo(db).create_known_location(
            user_id=_uid(), ip_address="1.2.3.4"
        )
    assert result is fake


@pytest.mark.asyncio
async def test_get_known_location_by_user_ip():
    obj = object()
    db = _db(_FR(v=obj))
    result = await _repo(db).get_known_location_by_user_ip(_uid(), "1.2.3.4")
    assert result is obj


@pytest.mark.asyncio
async def test_get_known_locations_by_user():
    items = [object()]
    db = _db(_FR(many=items))
    result = await _repo(db).get_known_locations_by_user(_uid())
    assert list(result) == items


@pytest.mark.asyncio
async def test_update_known_location():
    loc = SimpleNamespace(id=_uid())
    db = _db()
    await _repo(db).update_known_location(loc)
    db.merge.assert_awaited_once_with(loc)


@pytest.mark.asyncio
async def test_create_known_device():
    fake = SimpleNamespace(id=_uid())
    db = _db()
    with patch("app.repositories.auth.KnownDevice", return_value=fake):
        result = await _repo(db).create_known_device(
            user_id=_uid(), device_fingerprint="fp"
        )
    assert result is fake


@pytest.mark.asyncio
async def test_get_known_device_by_user_fingerprint():
    obj = object()
    db = _db(_FR(v=obj))
    result = await _repo(db).get_known_device_by_user_fingerprint(_uid(), "fp")
    assert result is obj


@pytest.mark.asyncio
async def test_get_known_devices_by_user():
    items = [object()]
    db = _db(_FR(many=items))
    result = await _repo(db).get_known_devices_by_user(_uid())
    assert list(result) == items


@pytest.mark.asyncio
async def test_update_known_device():
    device = SimpleNamespace(id=_uid())
    db = _db()
    await _repo(db).update_known_device(device)
    db.merge.assert_awaited_once_with(device)
