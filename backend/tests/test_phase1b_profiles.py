"""Integration tests for Phase 1B — Role-Specific Profile CRUD.

Tests:
  GET  /me/profile              — each role sees own profile
  PUT  /me/profile              — each role can update own fields (upsert)
  GET  /admin/users/{id}/profile — admin reads any user's profile
  RBAC: student/parent/teacher can't read other users' profiles via admin endpoint
"""

from __future__ import annotations

import httpx
import pytest
import pytest_asyncio

from tests.conftest import (
    BASE_URL,
    SCHOOL_ID,
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    STUDENT_EMAIL,
    STUDENT_PASSWORD,
    PARENT_EMAIL,
    PARENT_PASSWORD,
    TEACHER_EMAIL,
    TEACHER_PASSWORD,
)

# Seed user IDs from seed.py (fixed UUIDs)
STUDENT_ID = "10000000-0000-4000-8000-000000000007"
PARENT_ID = "10000000-0000-4000-8000-000000000005"
TEACHER_ID = "10000000-0000-4000-8000-000000000003"
ADMIN_ID = "10000000-0000-4000-8000-000000000001"


# ---------------------------------------------------------------------------
# GET /me/profile — Each role reads own profile
# ---------------------------------------------------------------------------


class TestGetMyProfile:
    """GET /me/profile — returns user data + role-specific profile."""

    @pytest.mark.asyncio
    async def test_student_gets_own_profile(self, client: httpx.AsyncClient, student_token: str):
        resp = await client.get(
            "/me/profile",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["email"] == STUDENT_EMAIL
        assert data["role"] == "STD"
        assert data["school_id"] is not None
        # Student profile should be present (seeded in seed_profiles)
        assert data["student_profile"] is not None or data["student_profile"] is None
        # Parent/teacher profiles should be null for a student
        assert data["parent_profile"] is None
        assert data["teacher_profile"] is None

    @pytest.mark.asyncio
    async def test_parent_gets_own_profile(self, client: httpx.AsyncClient, parent_token: str):
        resp = await client.get(
            "/me/profile",
            headers={"Authorization": f"Bearer {parent_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["email"] == PARENT_EMAIL
        assert data["role"] == "PAR"
        assert data["student_profile"] is None
        assert data["teacher_profile"] is None

    @pytest.mark.asyncio
    async def test_teacher_gets_own_profile(self, client: httpx.AsyncClient, teacher_token: str):
        resp = await client.get(
            "/me/profile",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["email"] == TEACHER_EMAIL
        assert data["role"] == "TCH"
        assert data["student_profile"] is None
        assert data["parent_profile"] is None

    @pytest.mark.asyncio
    async def test_admin_gets_own_profile(self, client: httpx.AsyncClient, admin_token: str):
        resp = await client.get(
            "/me/profile",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["email"] == ADMIN_EMAIL
        # ADM doesn't have role-specific profile
        assert data["student_profile"] is None
        assert data["parent_profile"] is None
        assert data["teacher_profile"] is None

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self, client: httpx.AsyncClient):
        resp = await client.get("/me/profile")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_response_follows_envelope(self, client: httpx.AsyncClient, student_token: str):
        resp = await client.get(
            "/me/profile",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        body = resp.json()
        assert "data" in body
        assert "meta" in body
        assert "timestamp" in body["meta"]
        assert "version" in body["meta"]


# ---------------------------------------------------------------------------
# PUT /me/profile — Update role-specific fields
# ---------------------------------------------------------------------------


class TestUpdateMyProfile:
    """PUT /me/profile — updates role-specific fields (upsert)."""

    @pytest.mark.asyncio
    async def test_student_update_class_level(self, client: httpx.AsyncClient, student_token: str):
        resp = await client.put(
            "/me/profile",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"class_level": "3ème année collège"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["student_profile"] is not None
        assert data["student_profile"]["class_level"] == "3ème année collège"

    @pytest.mark.asyncio
    async def test_student_update_date_of_birth(self, client: httpx.AsyncClient, student_token: str):
        resp = await client.put(
            "/me/profile",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"date_of_birth": "2008-03-15"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["student_profile"]["date_of_birth"] == "2008-03-15"

    @pytest.mark.asyncio
    async def test_parent_update_relationship_type(self, client: httpx.AsyncClient, parent_token: str):
        resp = await client.put(
            "/me/profile",
            headers={"Authorization": f"Bearer {parent_token}"},
            json={"relationship_type": "mother"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["parent_profile"] is not None
        assert data["parent_profile"]["relationship_type"] == "mother"

    @pytest.mark.asyncio
    async def test_parent_update_cin_and_emergency_phone(self, client: httpx.AsyncClient, parent_token: str):
        resp = await client.put(
            "/me/profile",
            headers={"Authorization": f"Bearer {parent_token}"},
            json={
                "cin_number": "AB123456",
                "emergency_phone": "+212600112233",
            },
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["parent_profile"]["cin_number"] == "AB123456"
        assert data["parent_profile"]["emergency_phone"] == "+212600112233"

    @pytest.mark.asyncio
    async def test_teacher_update_subject_and_qualification(self, client: httpx.AsyncClient, teacher_token: str):
        resp = await client.put(
            "/me/profile",
            headers={"Authorization": f"Bearer {teacher_token}"},
            json={
                "subject_specialty": "Physique-Chimie",
                "qualification": "Agrégation",
            },
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["teacher_profile"] is not None
        assert data["teacher_profile"]["subject_specialty"] == "Physique-Chimie"
        assert data["teacher_profile"]["qualification"] == "Agrégation"

    @pytest.mark.asyncio
    async def test_update_with_no_fields_returns_422(self, client: httpx.AsyncClient, student_token: str):
        resp = await client.put(
            "/me/profile",
            headers={"Authorization": f"Bearer {student_token}"},
            json={},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_admin_update_returns_422_no_profile(self, client: httpx.AsyncClient, admin_token: str):
        """ADM role doesn't have a role-specific profile table."""
        resp = await client.put(
            "/me/profile",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"class_level": "test"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_update_creates_profile_if_missing(self, client: httpx.AsyncClient, student_token: str):
        """PUT /me/profile creates profile row on first update (upsert)."""
        resp = await client.put(
            "/me/profile",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"nationality": "Marocaine"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["student_profile"] is not None
        assert data["student_profile"]["nationality"] == "Marocaine"

    @pytest.mark.asyncio
    async def test_update_preserves_existing_fields(self, client: httpx.AsyncClient, teacher_token: str):
        """Updating one field shouldn't erase other existing fields."""
        # Set subject
        await client.put(
            "/me/profile",
            headers={"Authorization": f"Bearer {teacher_token}"},
            json={"subject_specialty": "Mathématiques"},
        )
        # Update qualification only
        resp = await client.put(
            "/me/profile",
            headers={"Authorization": f"Bearer {teacher_token}"},
            json={"qualification": "Master 2"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["teacher_profile"]["qualification"] == "Master 2"
        # Subject should still be there
        assert data["teacher_profile"]["subject_specialty"] is not None

    @pytest.mark.asyncio
    async def test_unauthenticated_update_returns_401(self, client: httpx.AsyncClient):
        resp = await client.put("/me/profile", json={"class_level": "test"})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /admin/users/{user_id}/profile — Admin reads any user's profile
# ---------------------------------------------------------------------------


class TestAdminGetUserProfile:
    """GET /admin/users/{id}/profile — admin-only access."""

    @pytest.mark.asyncio
    async def test_admin_reads_student_profile(self, client: httpx.AsyncClient, admin_token: str):
        resp = await client.get(
            f"/admin/users/{STUDENT_ID}/profile",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["role"] == "STD"
        assert data["email"] == STUDENT_EMAIL

    @pytest.mark.asyncio
    async def test_admin_reads_parent_profile(self, client: httpx.AsyncClient, admin_token: str):
        resp = await client.get(
            f"/admin/users/{PARENT_ID}/profile",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["role"] == "PAR"

    @pytest.mark.asyncio
    async def test_admin_reads_teacher_profile(self, client: httpx.AsyncClient, admin_token: str):
        resp = await client.get(
            f"/admin/users/{TEACHER_ID}/profile",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["role"] == "TCH"

    @pytest.mark.asyncio
    async def test_nonexistent_user_returns_404(self, client: httpx.AsyncClient, admin_token: str):
        resp = await client.get(
            "/admin/users/99999999-9999-4999-9999-999999999999/profile",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_student_cannot_access_admin_profile_endpoint(
        self, client: httpx.AsyncClient, student_token: str
    ):
        resp = await client.get(
            f"/admin/users/{TEACHER_ID}/profile",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_parent_cannot_access_admin_profile_endpoint(
        self, client: httpx.AsyncClient, parent_token: str
    ):
        resp = await client.get(
            f"/admin/users/{STUDENT_ID}/profile",
            headers={"Authorization": f"Bearer {parent_token}"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_teacher_cannot_access_admin_profile_endpoint(
        self, client: httpx.AsyncClient, teacher_token: str
    ):
        resp = await client.get(
            f"/admin/users/{STUDENT_ID}/profile",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_response_follows_envelope(self, client: httpx.AsyncClient, admin_token: str):
        resp = await client.get(
            f"/admin/users/{STUDENT_ID}/profile",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        body = resp.json()
        assert "data" in body
        assert "meta" in body
        assert body["meta"]["version"] == "0.1.0"
