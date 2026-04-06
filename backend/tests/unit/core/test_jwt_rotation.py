"""Tests for JWT dual-key rotation support."""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest

from app.core.exceptions import AuthenticationError
from app.core.security import create_access_token, decode_access_token


def test_token_decodes_with_current_key():
    """Token signed with the current key decodes successfully."""
    user_id = uuid.uuid4()
    token = create_access_token(
        user_id=user_id,
        role="ADM",
        school_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
    )

    payload = decode_access_token(token)

    assert payload["sub"] == str(user_id)


def test_token_decodes_with_previous_key_during_rotation():
    """Token signed with the old key still decodes during the rotation window."""
    old_key = "change-me-in-production-use-a-strong-random-secret"
    user_id = uuid.uuid4()
    token = create_access_token(
        user_id=user_id,
        role="TCH",
        school_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
    )

    with patch("app.core.security.settings") as mock_settings:
        mock_settings.jwt_algorithm = "HS256"
        mock_settings.jwt_secret_key = "brand-new-secret-after-rotation"
        mock_settings.jwt_previous_key = old_key

        payload = decode_access_token(token)

    assert payload["sub"] == str(user_id)


def test_token_fails_with_completely_wrong_key():
    """Token signed with an unknown key raises an authentication error."""
    token = create_access_token(
        user_id=uuid.uuid4(),
        role="STD",
        school_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
    )

    with patch("app.core.security.settings") as mock_settings:
        mock_settings.jwt_algorithm = "HS256"
        mock_settings.jwt_secret_key = "wrong-key"
        mock_settings.jwt_previous_key = "also-wrong-key"

        with pytest.raises(AuthenticationError):
            decode_access_token(token)
