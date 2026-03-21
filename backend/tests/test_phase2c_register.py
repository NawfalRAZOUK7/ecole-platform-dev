"""Integration tests for Phase 2C — Registration with Invitation Code.

Tests:
  POST /auth/register — register STD, PAR, TCH with invitation codes
  Validates: response envelope, profile creation, code consumption,
             email uniqueness, invalid/expired codes, password policy
  POST /admin/register-batch — bulk registration
"""

from __future__ import annotations

import uuid

import httpx
import pytest
import pytest_asyncio

from tests.conftest import (
    BASE_URL,
    SCHOOL_ID,
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
)


# Strong password meeting policy (12+ chars, upper, lower, digit, special)
STRONG_PASSWORD = "SecurePass123!"


@pytest_asyncio.fixture
async def create_invite(client: httpx.AsyncClient, admin_token: str):
    """Factory fixture: creates an invitation code for a given role.

    Returns the plaintext 8-char code.
    """

    async def _create(role: str) -> str:
        resp = await client.post(
            "/invites/create",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"role_target": role, "expires_in_hours": 24},
        )
        assert resp.status_code == 201, f"Failed to create invite: {resp.text}"
        return resp.json()["data"]["code"]

    return _create


# ---------------------------------------------------------------------------
# POST /auth/register — Register a student
# ---------------------------------------------------------------------------


class TestRegisterStudent:
    """Register a new student account with invitation code."""

    @pytest.mark.asyncio
    async def test_register_student_success(
        self, client: httpx.AsyncClient, create_invite
    ):
        code = await create_invite("STD")
        email = f"test.student.{uuid.uuid4().hex[:8]}@ecole-test.ma"

        resp = await client.post(
            "/auth/register",
            json={
                "code": code,
                "email": email,
                "full_name": "Élève Test",
                "password": STRONG_PASSWORD,
                "profile_data": {
                    "date_of_birth": "2010-05-15",
                    "class_level": "6ème primaire",
                },
            },
        )
        assert resp.status_code == 201
        data = resp.json()["data"]

        # Verify response fields
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0
        assert data["role"] == "STD"
        assert data["school_id"] == SCHOOL_ID
        assert data["user_id"] is not None
        assert "email_verification_required" in data

    @pytest.mark.asyncio
    async def test_register_student_creates_profile(
        self, client: httpx.AsyncClient, create_invite
    ):
        """After registration, GET /me/profile returns the student profile."""
        code = await create_invite("STD")
        email = f"test.profile.{uuid.uuid4().hex[:8]}@ecole-test.ma"

        reg_resp = await client.post(
            "/auth/register",
            json={
                "code": code,
                "email": email,
                "full_name": "Profil Test",
                "password": STRONG_PASSWORD,
                "profile_data": {
                    "class_level": "1ère bac",
                    "nationality": "Marocaine",
                },
            },
        )
        assert reg_resp.status_code == 201
        token = reg_resp.json()["data"]["access_token"]

        # Verify profile was created
        profile_resp = await client.get(
            "/me/profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert profile_resp.status_code == 200
        profile = profile_resp.json()["data"]
        assert profile["role"] == "STD"
        assert profile["email"] == email
        assert profile["student_profile"] is not None
        assert profile["student_profile"]["class_level"] == "1ère bac"
        assert profile["student_profile"]["nationality"] == "Marocaine"


# ---------------------------------------------------------------------------
# POST /auth/register — Register a parent
# ---------------------------------------------------------------------------


class TestRegisterParent:
    """Register a new parent account with invitation code."""

    @pytest.mark.asyncio
    async def test_register_parent_success(
        self, client: httpx.AsyncClient, create_invite
    ):
        code = await create_invite("PAR")
        email = f"test.parent.{uuid.uuid4().hex[:8]}@ecole-test.ma"

        resp = await client.post(
            "/auth/register",
            json={
                "code": code,
                "email": email,
                "full_name": "Parent Test",
                "phone": "+212600998877",
                "password": STRONG_PASSWORD,
                "profile_data": {
                    "relationship_type": "father",
                    "cin_number": "CD789012",
                    "profession": "Ingénieur",
                },
            },
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["role"] == "PAR"
        assert data["access_token"] is not None

    @pytest.mark.asyncio
    async def test_register_parent_creates_profile(
        self, client: httpx.AsyncClient, create_invite
    ):
        code = await create_invite("PAR")
        email = f"test.pprofile.{uuid.uuid4().hex[:8]}@ecole-test.ma"

        reg_resp = await client.post(
            "/auth/register",
            json={
                "code": code,
                "email": email,
                "full_name": "Parent Profil",
                "password": STRONG_PASSWORD,
                "profile_data": {
                    "relationship_type": "mother",
                    "emergency_phone": "+212611223344",
                },
            },
        )
        assert reg_resp.status_code == 201
        token = reg_resp.json()["data"]["access_token"]

        profile_resp = await client.get(
            "/me/profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert profile_resp.status_code == 200
        profile = profile_resp.json()["data"]
        assert profile["parent_profile"] is not None
        assert profile["parent_profile"]["relationship_type"] == "mother"
        assert profile["parent_profile"]["emergency_phone"] == "+212611223344"


# ---------------------------------------------------------------------------
# POST /auth/register — Register a teacher
# ---------------------------------------------------------------------------


class TestRegisterTeacher:
    """Register a new teacher account with invitation code."""

    @pytest.mark.asyncio
    async def test_register_teacher_success(
        self, client: httpx.AsyncClient, create_invite
    ):
        code = await create_invite("TCH")
        email = f"test.teacher.{uuid.uuid4().hex[:8]}@ecole-test.ma"

        resp = await client.post(
            "/auth/register",
            json={
                "code": code,
                "email": email,
                "full_name": "Enseignant Test",
                "password": STRONG_PASSWORD,
                "profile_data": {
                    "subject_specialty": "Mathématiques",
                    "qualification": "Agrégation",
                },
            },
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["role"] == "TCH"
        assert data["access_token"] is not None

    @pytest.mark.asyncio
    async def test_register_teacher_creates_profile(
        self, client: httpx.AsyncClient, create_invite
    ):
        code = await create_invite("TCH")
        email = f"test.tprofile.{uuid.uuid4().hex[:8]}@ecole-test.ma"

        reg_resp = await client.post(
            "/auth/register",
            json={
                "code": code,
                "email": email,
                "full_name": "Prof Profil",
                "password": STRONG_PASSWORD,
                "profile_data": {
                    "subject_specialty": "Physique",
                    "qualification": "Master",
                },
            },
        )
        assert reg_resp.status_code == 201
        token = reg_resp.json()["data"]["access_token"]

        profile_resp = await client.get(
            "/me/profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert profile_resp.status_code == 200
        profile = profile_resp.json()["data"]
        assert profile["teacher_profile"] is not None
        assert profile["teacher_profile"]["subject_specialty"] == "Physique"
        assert profile["teacher_profile"]["qualification"] == "Master"


# ---------------------------------------------------------------------------
# Validation & error cases
# ---------------------------------------------------------------------------


class TestRegisterValidation:
    """Registration error cases — invalid code, weak password, duplicate email, etc."""

    @pytest.mark.asyncio
    async def test_invalid_code_returns_error(self, client: httpx.AsyncClient):
        resp = await client.post(
            "/auth/register",
            json={
                "code": "ZZZZZZZZ",
                "email": "nobody@ecole-test.ma",
                "full_name": "Nobody",
                "password": STRONG_PASSWORD,
            },
        )
        assert resp.status_code in (404, 422)

    @pytest.mark.asyncio
    async def test_short_code_returns_422(self, client: httpx.AsyncClient):
        resp = await client.post(
            "/auth/register",
            json={
                "code": "SHORT",
                "email": "nobody@ecole-test.ma",
                "full_name": "Nobody",
                "password": STRONG_PASSWORD,
            },
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_weak_password_rejected(
        self, client: httpx.AsyncClient, create_invite
    ):
        code = await create_invite("STD")

        resp = await client.post(
            "/auth/register",
            json={
                "code": code,
                "email": f"weak.{uuid.uuid4().hex[:8]}@ecole-test.ma",
                "full_name": "Weak Pass",
                "password": "short",  # Too short, no upper/digit/special
            },
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_duplicate_email_rejected(
        self, client: httpx.AsyncClient, create_invite
    ):
        """Same email in same school cannot register twice."""
        code1 = await create_invite("STD")
        code2 = await create_invite("STD")
        email = f"dup.{uuid.uuid4().hex[:8]}@ecole-test.ma"

        # First registration succeeds
        resp1 = await client.post(
            "/auth/register",
            json={
                "code": code1,
                "email": email,
                "full_name": "First User",
                "password": STRONG_PASSWORD,
            },
        )
        assert resp1.status_code == 201

        # Second registration with same email fails
        resp2 = await client.post(
            "/auth/register",
            json={
                "code": code2,
                "email": email,
                "full_name": "Second User",
                "password": STRONG_PASSWORD,
            },
        )
        assert resp2.status_code == 409

    @pytest.mark.asyncio
    async def test_code_consumed_after_register(
        self, client: httpx.AsyncClient, create_invite
    ):
        """Once a code is used, it cannot be reused."""
        code = await create_invite("STD")

        # First use succeeds
        resp1 = await client.post(
            "/auth/register",
            json={
                "code": code,
                "email": f"first.{uuid.uuid4().hex[:8]}@ecole-test.ma",
                "full_name": "First",
                "password": STRONG_PASSWORD,
            },
        )
        assert resp1.status_code == 201

        # Reuse fails
        resp2 = await client.post(
            "/auth/register",
            json={
                "code": code,
                "email": f"second.{uuid.uuid4().hex[:8]}@ecole-test.ma",
                "full_name": "Second",
                "password": STRONG_PASSWORD,
            },
        )
        assert resp2.status_code == 409

    @pytest.mark.asyncio
    async def test_missing_email_returns_422(self, client: httpx.AsyncClient):
        resp = await client.post(
            "/auth/register",
            json={
                "code": "ABCDEFGH",
                "full_name": "No Email",
                "password": STRONG_PASSWORD,
            },
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_password_returns_422(self, client: httpx.AsyncClient):
        resp = await client.post(
            "/auth/register",
            json={
                "code": "ABCDEFGH",
                "email": "nopass@ecole-test.ma",
                "full_name": "No Pass",
            },
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Response envelope & auth token validation
# ---------------------------------------------------------------------------


class TestRegisterResponseFormat:
    """Verify response format matches the standard envelope."""

    @pytest.mark.asyncio
    async def test_response_follows_envelope(
        self, client: httpx.AsyncClient, create_invite
    ):
        code = await create_invite("STD")
        email = f"envelope.{uuid.uuid4().hex[:8]}@ecole-test.ma"

        resp = await client.post(
            "/auth/register",
            json={
                "code": code,
                "email": email,
                "full_name": "Envelope Test",
                "password": STRONG_PASSWORD,
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert "data" in body
        assert "meta" in body
        assert "timestamp" in body["meta"]
        assert "version" in body["meta"]

    @pytest.mark.asyncio
    async def test_token_works_for_me_endpoint(
        self, client: httpx.AsyncClient, create_invite
    ):
        """The token returned by register should work for /auth/me."""
        code = await create_invite("STD")
        email = f"tokentest.{uuid.uuid4().hex[:8]}@ecole-test.ma"

        reg_resp = await client.post(
            "/auth/register",
            json={
                "code": code,
                "email": email,
                "full_name": "Token Test",
                "password": STRONG_PASSWORD,
            },
        )
        assert reg_resp.status_code == 201
        token = reg_resp.json()["data"]["access_token"]

        # Use the token
        me_resp = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_resp.status_code == 200
        me_data = me_resp.json()["data"]
        assert me_data["email"] == email
        assert me_data["full_name"] == "Token Test"
        assert me_data["role"] == "STD"

    @pytest.mark.asyncio
    async def test_registered_user_can_login(
        self, client: httpx.AsyncClient, create_invite
    ):
        """After registration, the user can log in with the same credentials."""
        code = await create_invite("TCH")
        email = f"logintest.{uuid.uuid4().hex[:8]}@ecole-test.ma"

        reg_resp = await client.post(
            "/auth/register",
            json={
                "code": code,
                "email": email,
                "full_name": "Login Test",
                "password": STRONG_PASSWORD,
            },
        )
        assert reg_resp.status_code == 201

        # Login
        login_resp = await client.post(
            "/auth/login",
            json={
                "email": email,
                "password": STRONG_PASSWORD,
                "school_id": SCHOOL_ID,
            },
        )
        assert login_resp.status_code == 200
        assert "access_token" in login_resp.json()["data"]


# ---------------------------------------------------------------------------
# POST /admin/register-batch — Bulk registration
# ---------------------------------------------------------------------------


class TestBatchRegister:
    """POST /admin/register-batch — admin bulk creates accounts."""

    @pytest.mark.asyncio
    async def test_batch_register_success(
        self, client: httpx.AsyncClient, admin_token: str
    ):
        users = [
            {
                "email": f"batch.std.{uuid.uuid4().hex[:8]}@ecole-test.ma",
                "full_name": "Batch Student",
                "role": "STD",
            },
            {
                "email": f"batch.tch.{uuid.uuid4().hex[:8]}@ecole-test.ma",
                "full_name": "Batch Teacher",
                "role": "TCH",
            },
        ]

        resp = await client.post(
            "/admin/register-batch",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"users": users},
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert "created" in data
        assert len(data["created"]) == 2
        # Each created entry should have a temp password
        for entry in data["created"]:
            assert "temp_password" in entry
            assert "email" in entry

    @pytest.mark.asyncio
    async def test_batch_register_duplicate_email_skipped(
        self, client: httpx.AsyncClient, admin_token: str
    ):
        """If email already exists, it should be in errors, not created."""
        email = f"batch.dup.{uuid.uuid4().hex[:8]}@ecole-test.ma"

        # First batch succeeds
        resp1 = await client.post(
            "/admin/register-batch",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"users": [{"email": email, "full_name": "Dup Test", "role": "STD"}]},
        )
        assert resp1.status_code == 201

        # Second batch with same email — error entry
        resp2 = await client.post(
            "/admin/register-batch",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"users": [{"email": email, "full_name": "Dup Test 2", "role": "STD"}]},
        )
        assert resp2.status_code == 201
        data = resp2.json()["data"]
        assert len(data.get("errors", [])) >= 1

    @pytest.mark.asyncio
    async def test_batch_register_invalid_role_skipped(
        self, client: httpx.AsyncClient, admin_token: str
    ):
        resp = await client.post(
            "/admin/register-batch",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "users": [
                    {
                        "email": f"bad.role.{uuid.uuid4().hex[:8]}@ecole-test.ma",
                        "full_name": "Bad Role",
                        "role": "INVALID",
                    }
                ]
            },
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert len(data.get("errors", [])) >= 1

    @pytest.mark.asyncio
    async def test_batch_register_requires_admin(
        self, client: httpx.AsyncClient, student_token: str
    ):
        resp = await client.post(
            "/admin/register-batch",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "users": [
                    {
                        "email": "unauthorized@ecole-test.ma",
                        "full_name": "Unauthorized",
                        "role": "STD",
                    }
                ]
            },
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_batch_register_created_user_can_login(
        self, client: httpx.AsyncClient, admin_token: str
    ):
        """Users created via batch register can login with temp password."""
        email = f"batch.login.{uuid.uuid4().hex[:8]}@ecole-test.ma"

        resp = await client.post(
            "/admin/register-batch",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"users": [{"email": email, "full_name": "Batch Login", "role": "STD"}]},
        )
        assert resp.status_code == 201
        temp_password = resp.json()["data"]["created"][0]["temp_password"]

        # Login with temp password
        login_resp = await client.post(
            "/auth/login",
            json={
                "email": email,
                "password": temp_password,
                "school_id": SCHOOL_ID,
            },
        )
        assert login_resp.status_code == 200
        assert "access_token" in login_resp.json()["data"]
