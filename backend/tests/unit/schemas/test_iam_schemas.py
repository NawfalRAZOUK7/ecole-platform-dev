"""Unit tests for IAM Pydantic schemas.

Validates request/response models, field constraints, defaults, and validators
for authentication, profile, and identity-related schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.auth import (
    LoginRequest,
    LoginData,
    MembershipInfo,
    MeData,
    InviteCreateRequest,
)
from app.schemas.profile import (
    ProfileUpdateRequest,
    ProfileResponse,
    ProfileAvatarResponse,
)


# ---------------------------------------------------------------------------
# Auth schemas — LoginRequest
# ---------------------------------------------------------------------------
class TestLoginRequest:
    """Tests for LoginRequest schema."""

    def test_valid_login_request(self) -> None:
        data = {
            "email": "teacher@school.ma",
            "password": "secure_password_123",
            "school_id": str(uuid.uuid4()),
        }
        model = LoginRequest(**data)
        assert model.email == data["email"]
        assert model.password == data["password"]

    @pytest.mark.parametrize(
        "payload,expected_error",
        [
            ({"email": "invalid", "password": "pass", "school_id": str(uuid.uuid4())}, "value is not a valid email address"),
            ({"email": "a@b.c", "password": "", "school_id": str(uuid.uuid4())}, "String should have at least 1 character"),
            ({"password": "pass", "school_id": str(uuid.uuid4())}, "Field required"),
            ({"email": "a@b.c", "password": "pass"}, "Field required"),
        ],
    )
    def test_invalid_login_request(self, payload: dict, expected_error: str) -> None:
        with pytest.raises(ValidationError) as exc:
            LoginRequest(**payload)
        assert expected_error in str(exc.value)


# ---------------------------------------------------------------------------
# Auth schemas — LoginData
# ---------------------------------------------------------------------------
class TestLoginData:
    """Tests for LoginData response schema."""

    def test_defaults(self) -> None:
        model = LoginData(access_token="tok_123")
        assert model.token_type == "bearer"
        assert model.access_token == "tok_123"

    def test_custom_expires_in(self) -> None:
        model = LoginData(access_token="tok_123", expires_in=3600)
        assert model.expires_in == 3600


# ---------------------------------------------------------------------------
# Auth schemas — MembershipInfo / MeData
# ---------------------------------------------------------------------------
class TestMeData:
    """Tests for MeData and MembershipInfo schemas."""

    def test_membership_info(self) -> None:
        sid = uuid.uuid4()
        m = MembershipInfo(school_id=sid, role="teacher", status="active")
        assert m.school_id == sid
        assert m.role == "teacher"

    def test_me_data(self) -> None:
        sid = uuid.uuid4()
        uid = uuid.uuid4()
        me = MeData(
            id=uid,
            email="t@example.com",
            full_name="Test User",
            role="teacher",
            school_id=sid,
            permissions=["read:students"],
            memberships=[MembershipInfo(school_id=sid, role="teacher", status="active")],
        )
        assert me.full_name == "Test User"
        assert len(me.permissions) == 1


# ---------------------------------------------------------------------------
# Auth schemas — InviteCreateRequest
# ---------------------------------------------------------------------------
class TestInviteCreateRequest:
    """Tests for invitation creation schema."""

    def test_valid_invite(self) -> None:
        model = InviteCreateRequest(
            email="new@school.ma",
            role="teacher",
            school_id=uuid.uuid4(),
            expires_in_hours=48,
        )
        assert model.role == "teacher"

    def test_missing_required(self) -> None:
        with pytest.raises(ValidationError):
            InviteCreateRequest(role="teacher")


# ---------------------------------------------------------------------------
# Profile schemas
# ---------------------------------------------------------------------------
class TestProfileSchemas:
    """Tests for profile-related schemas."""

    def test_profile_update_request(self) -> None:
        model = ProfileUpdateRequest(
            full_name="Updated Name",
            phone="+212600000000",
        )
        assert model.full_name == "Updated Name"

    def test_profile_response(self) -> None:
        uid = uuid.uuid4()
        model = ProfileResponse(
            id=uid,
            email="user@school.ma",
            full_name="User",
            role="parent",
            school_id=uuid.uuid4(),
            created_at=datetime.utcnow(),
        )
        assert model.email == "user@school.ma"

    def test_profile_avatar_response(self) -> None:
        model = ProfileAvatarResponse(
            avatar_url="https://cdn.example.com/avatar.png",
            updated_at=datetime.utcnow(),
        )
        assert "avatar.png" in model.avatar_url
