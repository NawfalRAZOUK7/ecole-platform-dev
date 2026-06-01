"""Additional unit tests for app/core/security.py — uncovered branches."""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest
from jose import jwt

from app.core.exceptions import AuthenticationError
from app.core.security import (
    TOKEN_TYPE_ACCESS,
    TOKEN_TYPE_REFRESH,
    _decode_jwt,
    create_access_token,
    create_csrf_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)


# ---------------------------------------------------------------------------
# create_refresh_token
# ---------------------------------------------------------------------------


def test_create_refresh_token_returns_tuple():
    token, jti = create_refresh_token(
        user_id=uuid.uuid4(),
        school_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
    )
    assert isinstance(token, str)
    assert isinstance(jti, str)
    assert len(jti) == 36  # UUID format


def test_create_refresh_token_default_expire_days():
    from app.core.config import settings

    user_id = uuid.uuid4()
    token, _ = create_refresh_token(
        user_id=user_id,
        school_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
    )
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    assert payload["type"] == TOKEN_TYPE_REFRESH
    assert payload["sub"] == str(user_id)


def test_create_refresh_token_custom_expire_days():
    from app.core.config import settings

    token, jti = create_refresh_token(
        user_id=uuid.uuid4(),
        school_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        expire_days=7.0,
    )
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    assert payload["jti"] == jti


# ---------------------------------------------------------------------------
# create_csrf_token
# ---------------------------------------------------------------------------


def test_create_csrf_token_is_uuid():
    token = create_csrf_token()
    assert isinstance(token, str)
    assert len(token) == 36
    uuid.UUID(token)  # raises if not valid UUID


def test_create_csrf_token_unique():
    tokens = {create_csrf_token() for _ in range(10)}
    assert len(tokens) == 10


# ---------------------------------------------------------------------------
# _decode_jwt — key rotation path
# ---------------------------------------------------------------------------


def test_decode_jwt_falls_back_to_previous_key():
    old_key = "old-secret-key-for-rotation-test"
    with patch("app.core.security.settings") as s:
        s.jwt_algorithm = "HS256"
        s.access_token_expire_minutes = 30
        s.refresh_token_expire_days = 2
        s.jwt_secret_key = old_key
        s.jwt_previous_key = ""
        token = create_access_token(
            uuid.uuid4(), "ADM", uuid.uuid4(), uuid.uuid4()
        )

    # Now current key changed, old key moved to previous
    with patch("app.core.security.settings") as s:
        s.jwt_algorithm = "HS256"
        s.jwt_secret_key = "brand-new-key-12345"
        s.jwt_previous_key = old_key
        payload = _decode_jwt(token)

    assert payload["type"] == TOKEN_TYPE_ACCESS


def test_decode_jwt_raises_when_both_keys_fail():
    from jose import JWTError

    with patch("app.core.security.settings") as s:
        s.jwt_algorithm = "HS256"
        s.jwt_secret_key = "wrong-key"
        s.jwt_previous_key = "also-wrong-key"
        with pytest.raises(JWTError):
            _decode_jwt("invalid.token.here")


def test_decode_jwt_raises_no_previous_key():
    from jose import JWTError

    with patch("app.core.security.settings") as s:
        s.jwt_algorithm = "HS256"
        s.jwt_secret_key = "wrong-key"
        s.jwt_previous_key = None
        with pytest.raises(JWTError):
            _decode_jwt("invalid.token.here")


# ---------------------------------------------------------------------------
# decode_access_token
# ---------------------------------------------------------------------------


def test_decode_access_token_wrong_type_raises():
    token, _ = create_refresh_token(
        user_id=uuid.uuid4(),
        school_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
    )
    with pytest.raises(AuthenticationError, match="Invalid token type"):
        decode_access_token(token)


def test_decode_access_token_invalid_token_raises():
    with pytest.raises(AuthenticationError, match="Invalid or expired access token"):
        decode_access_token("not.a.valid.token")


# ---------------------------------------------------------------------------
# decode_refresh_token
# ---------------------------------------------------------------------------


def test_decode_refresh_token_success():
    user_id = uuid.uuid4()
    token, jti = create_refresh_token(
        user_id=user_id,
        school_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
    )
    payload = decode_refresh_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["jti"] == jti


def test_decode_refresh_token_wrong_type_raises():
    token = create_access_token(
        uuid.uuid4(), "ADM", uuid.uuid4(), uuid.uuid4()
    )
    with pytest.raises(AuthenticationError, match="Invalid token type"):
        decode_refresh_token(token)


def test_decode_refresh_token_invalid_raises():
    with pytest.raises(AuthenticationError, match="Invalid or expired refresh token"):
        decode_refresh_token("totally.wrong.token")


# ---------------------------------------------------------------------------
# hash_password / verify_password
# ---------------------------------------------------------------------------


def test_hash_password_returns_bcrypt_hash():
    hashed = hash_password("MyStr0ng!Pass")
    assert hashed.startswith("$2b$")
    assert len(hashed) == 60


def test_hash_password_different_salts():
    h1 = hash_password("SamePass1!")
    h2 = hash_password("SamePass1!")
    assert h1 != h2


def test_verify_password_correct():
    plain = "TestPass1!"
    hashed = hash_password(plain)
    assert verify_password(plain, hashed) is True


def test_verify_password_wrong():
    hashed = hash_password("CorrectPass1!")
    assert verify_password("WrongPass1!", hashed) is False
