"""Integration tests for Phase 2D — Parent-Child Link Management.

Tests:
  POST /invites/create         — target_student_id on PAR invitation
  POST /admin/parent-child-links — admin manually links parent ↔ student
  GET  /admin/parent-child-links — list links with filters + pagination
  DELETE /admin/parent-child-links/{id} — revoke a link
  GET  /me/children             — parent sees linked children
  POST /admin/register-batch    — batch register PAR with target_student_id auto-link
  RBAC: student/teacher cannot access admin parent-child link endpoints
"""

from __future__ import annotations

import uuid

import httpx
import pytest
import pytest_asyncio

from tests.conftest import (
    SCHOOL_ID,
)

# Seed user IDs from seed.py (fixed UUIDs)
STUDENT_ID = "10000000-0000-4000-8000-000000000007"
PARENT_ID = "10000000-0000-4000-8000-000000000005"
TEACHER_ID = "10000000-0000-4000-8000-000000000003"
ADMIN_ID = "10000000-0000-4000-8000-000000000001"

# Strong password meeting policy (12+ chars, upper, lower, digit, special)
STRONG_PASSWORD = "SecurePass123!"


@pytest_asyncio.fixture
async def create_invite(client: httpx.AsyncClient, admin_token: str):
    """Factory fixture: creates an invitation code for a given role,
    optionally with target_student_id."""

    async def _create(role: str, target_student_id: str | None = None) -> str:
        payload: dict = {"role_target": role, "expires_in_hours": 24}
        if target_student_id is not None:
            payload["target_student_id"] = target_student_id
        resp = await client.post(
            "/invites/create",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=payload,
        )
        assert resp.status_code == 201, f"Failed to create invite: {resp.text}"
        return resp.json()["data"]["code"]

    return _create


# ---------------------------------------------------------------------------
# Invite creation with target_student_id
# ---------------------------------------------------------------------------


class TestInviteWithTargetStudent:
    """POST /invites/create — target_student_id for PAR invitations."""

    @pytest.mark.asyncio
    async def test_create_par_invite_with_target_student_id(
        self, client: httpx.AsyncClient, admin_token: str
    ):
        resp = await client.post(
            "/invites/create",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "role_target": "PAR",
                "expires_in_hours": 24,
                "target_student_id": STUDENT_ID,
            },
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert "code" in data
        assert len(data["code"]) == 8

    @pytest.mark.asyncio
    async def test_create_std_invite_with_target_student_id_fails(
        self, client: httpx.AsyncClient, admin_token: str
    ):
        """target_student_id is only valid for PAR role."""
        resp = await client.post(
            "/invites/create",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "role_target": "STD",
                "expires_in_hours": 24,
                "target_student_id": STUDENT_ID,
            },
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_create_par_invite_with_nonexistent_student_fails(
        self, client: httpx.AsyncClient, admin_token: str
    ):
        resp = await client.post(
            "/invites/create",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "role_target": "PAR",
                "expires_in_hours": 24,
                "target_student_id": "99999999-9999-4999-9999-999999999999",
            },
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_register_par_with_target_student_auto_links(
        self, client: httpx.AsyncClient, create_invite, admin_token: str
    ):
        """Register PAR with target_student_id → auto-link created."""
        code = await create_invite("PAR", target_student_id=STUDENT_ID)
        email = f"parent.autolink.{uuid.uuid4().hex[:8]}@test.ma"

        resp = await client.post(
            "/auth/register",
            json={
                "code": code,
                "email": email,
                "full_name": "Parent Auto-Link",
                "password": STRONG_PASSWORD,
                "profile_data": {"relationship_type": "father"},
            },
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        parent_token = data["access_token"]

        # Verify link exists via GET /me/children
        children_resp = await client.get(
            "/me/children",
            headers={"Authorization": f"Bearer {parent_token}"},
        )
        assert children_resp.status_code == 200
        children = children_resp.json()["data"]
        assert len(children) >= 1
        child_ids = [c["user_id"] for c in children]
        assert STUDENT_ID in child_ids


# ---------------------------------------------------------------------------
# Admin parent-child link CRUD
# ---------------------------------------------------------------------------


class TestAdminCreateParentChildLink:
    """POST /admin/parent-child-links — admin manually links parent ↔ student."""

    @pytest.mark.asyncio
    async def test_admin_creates_link(
        self, client: httpx.AsyncClient, admin_token: str
    ):
        resp = await client.post(
            f"/admin/parent-child-links?parent_user_id={PARENT_ID}&child_user_id={STUDENT_ID}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        # Could be 201 (created) or 409 (already exists from seed/previous test)
        assert resp.status_code in (201, 409)
        if resp.status_code == 201:
            data = resp.json()["data"]
            assert data["parent_user_id"] == PARENT_ID
            assert data["child_user_id"] == STUDENT_ID
            assert data["status"] == "active"

    @pytest.mark.asyncio
    async def test_admin_creates_duplicate_link_fails(
        self, client: httpx.AsyncClient, admin_token: str
    ):
        """Creating the same link twice should return 409."""
        # First create
        await client.post(
            f"/admin/parent-child-links?parent_user_id={PARENT_ID}&child_user_id={STUDENT_ID}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        # Second create — should be 409
        resp = await client.post(
            f"/admin/parent-child-links?parent_user_id={PARENT_ID}&child_user_id={STUDENT_ID}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_admin_link_nonexistent_parent_fails(
        self, client: httpx.AsyncClient, admin_token: str
    ):
        resp = await client.post(
            f"/admin/parent-child-links?parent_user_id=99999999-9999-4999-9999-999999999999&child_user_id={STUDENT_ID}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_admin_link_nonexistent_student_fails(
        self, client: httpx.AsyncClient, admin_token: str
    ):
        resp = await client.post(
            f"/admin/parent-child-links?parent_user_id={PARENT_ID}&child_user_id=99999999-9999-4999-9999-999999999999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_admin_link_teacher_as_parent_fails(
        self, client: httpx.AsyncClient, admin_token: str
    ):
        """Teacher is not PAR role — should fail."""
        resp = await client.post(
            f"/admin/parent-child-links?parent_user_id={TEACHER_ID}&child_user_id={STUDENT_ID}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404


class TestAdminListParentChildLinks:
    """GET /admin/parent-child-links — list with filters."""

    @pytest.mark.asyncio
    async def test_admin_list_all_links(
        self, client: httpx.AsyncClient, admin_token: str
    ):
        resp = await client.get(
            "/admin/parent-child-links",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert isinstance(body["data"], list)

    @pytest.mark.asyncio
    async def test_admin_list_filter_by_parent(
        self, client: httpx.AsyncClient, admin_token: str
    ):
        resp = await client.get(
            f"/admin/parent-child-links?parent_id={PARENT_ID}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        for link in data:
            assert link["parent_user_id"] == PARENT_ID

    @pytest.mark.asyncio
    async def test_admin_list_filter_by_student(
        self, client: httpx.AsyncClient, admin_token: str
    ):
        resp = await client.get(
            f"/admin/parent-child-links?student_id={STUDENT_ID}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        for link in data:
            assert link["child_user_id"] == STUDENT_ID

    @pytest.mark.asyncio
    async def test_admin_list_filter_by_status(
        self, client: httpx.AsyncClient, admin_token: str
    ):
        resp = await client.get(
            "/admin/parent-child-links?status=active",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        for link in data:
            assert link["status"] == "active"

    @pytest.mark.asyncio
    async def test_admin_list_follows_envelope(
        self, client: httpx.AsyncClient, admin_token: str
    ):
        resp = await client.get(
            "/admin/parent-child-links",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        body = resp.json()
        assert "data" in body
        assert "meta" in body


class TestAdminRevokeParentChildLink:
    """DELETE /admin/parent-child-links/{link_id} — revoke link."""

    @pytest.mark.asyncio
    async def test_admin_revokes_link(
        self, client: httpx.AsyncClient, admin_token: str, create_invite
    ):
        """Create a fresh parent, link, then revoke."""
        # Register a new parent
        code = await create_invite("PAR")
        email = f"parent.revoke.{uuid.uuid4().hex[:8]}@test.ma"
        reg_resp = await client.post(
            "/auth/register",
            json={
                "code": code,
                "email": email,
                "full_name": "Parent Revoke Test",
                "password": STRONG_PASSWORD,
            },
        )
        assert reg_resp.status_code == 201
        new_parent_id = reg_resp.json()["data"]["user_id"]

        # Admin creates link
        link_resp = await client.post(
            f"/admin/parent-child-links?parent_user_id={new_parent_id}&child_user_id={STUDENT_ID}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert link_resp.status_code == 201
        link_id = link_resp.json()["data"]["id"]

        # Admin revokes link
        del_resp = await client.delete(
            f"/admin/parent-child-links/{link_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert del_resp.status_code == 200
        assert del_resp.json()["data"]["status"] == "revoked"

    @pytest.mark.asyncio
    async def test_revoke_nonexistent_link_returns_404(
        self, client: httpx.AsyncClient, admin_token: str
    ):
        resp = await client.delete(
            "/admin/parent-child-links/99999999-9999-4999-9999-999999999999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_revoke_already_revoked_is_idempotent(
        self, client: httpx.AsyncClient, admin_token: str, create_invite
    ):
        """Revoking an already-revoked link returns 200 with message."""
        # Register a new parent
        code = await create_invite("PAR")
        email = f"parent.idempotent.{uuid.uuid4().hex[:8]}@test.ma"
        reg_resp = await client.post(
            "/auth/register",
            json={
                "code": code,
                "email": email,
                "full_name": "Parent Idempotent",
                "password": STRONG_PASSWORD,
            },
        )
        assert reg_resp.status_code == 201
        new_parent_id = reg_resp.json()["data"]["user_id"]

        # Create + revoke
        link_resp = await client.post(
            f"/admin/parent-child-links?parent_user_id={new_parent_id}&child_user_id={STUDENT_ID}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert link_resp.status_code == 201
        link_id = link_resp.json()["data"]["id"]

        await client.delete(
            f"/admin/parent-child-links/{link_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        # Second revoke — idempotent
        resp = await client.delete(
            f"/admin/parent-child-links/{link_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /me/children — Parent sees linked children
# ---------------------------------------------------------------------------


class TestGetMyChildren:
    """GET /me/children — parent endpoint."""

    @pytest.mark.asyncio
    async def test_parent_sees_children(
        self, client: httpx.AsyncClient, admin_token: str, parent_token: str
    ):
        """After admin links parent → student, parent should see child."""
        # Ensure link exists
        await client.post(
            f"/admin/parent-child-links?parent_user_id={PARENT_ID}&child_user_id={STUDENT_ID}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        resp = await client.get(
            "/me/children",
            headers={"Authorization": f"Bearer {parent_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data, list)
        assert len(data) >= 1
        child_ids = [c["user_id"] for c in data]
        assert STUDENT_ID in child_ids

    @pytest.mark.asyncio
    async def test_parent_child_has_expected_fields(
        self, client: httpx.AsyncClient, admin_token: str, parent_token: str
    ):
        """Each child entry should have user info and link info."""
        # Ensure link exists
        await client.post(
            f"/admin/parent-child-links?parent_user_id={PARENT_ID}&child_user_id={STUDENT_ID}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        resp = await client.get(
            "/me/children",
            headers={"Authorization": f"Bearer {parent_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        child = next((c for c in data if c["user_id"] == STUDENT_ID), None)
        assert child is not None
        assert "full_name" in child
        assert "email" in child
        assert "link_id" in child
        assert "linked_at" in child

    @pytest.mark.asyncio
    async def test_student_cannot_access_children_endpoint(
        self, client: httpx.AsyncClient, student_token: str
    ):
        resp = await client.get(
            "/me/children",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_teacher_cannot_access_children_endpoint(
        self, client: httpx.AsyncClient, teacher_token: str
    ):
        resp = await client.get(
            "/me/children",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self, client: httpx.AsyncClient):
        resp = await client.get("/me/children")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_response_follows_envelope(
        self, client: httpx.AsyncClient, parent_token: str
    ):
        resp = await client.get(
            "/me/children",
            headers={"Authorization": f"Bearer {parent_token}"},
        )
        body = resp.json()
        assert "data" in body
        assert "meta" in body


# ---------------------------------------------------------------------------
# RBAC: non-admin cannot access admin parent-child link endpoints
# ---------------------------------------------------------------------------


class TestParentChildLinksRBAC:
    """Non-admin roles are rejected by parent-child link admin endpoints."""

    @pytest.mark.asyncio
    async def test_student_cannot_create_link(
        self, client: httpx.AsyncClient, student_token: str
    ):
        resp = await client.post(
            f"/admin/parent-child-links?parent_user_id={PARENT_ID}&child_user_id={STUDENT_ID}",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_teacher_cannot_create_link(
        self, client: httpx.AsyncClient, teacher_token: str
    ):
        resp = await client.post(
            f"/admin/parent-child-links?parent_user_id={PARENT_ID}&child_user_id={STUDENT_ID}",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_parent_cannot_create_link(
        self, client: httpx.AsyncClient, parent_token: str
    ):
        resp = await client.post(
            f"/admin/parent-child-links?parent_user_id={PARENT_ID}&child_user_id={STUDENT_ID}",
            headers={"Authorization": f"Bearer {parent_token}"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_student_cannot_list_links(
        self, client: httpx.AsyncClient, student_token: str
    ):
        resp = await client.get(
            "/admin/parent-child-links",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_parent_cannot_list_links(
        self, client: httpx.AsyncClient, parent_token: str
    ):
        resp = await client.get(
            "/admin/parent-child-links",
            headers={"Authorization": f"Bearer {parent_token}"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_student_cannot_revoke_link(
        self, client: httpx.AsyncClient, student_token: str
    ):
        resp = await client.delete(
            "/admin/parent-child-links/99999999-9999-4999-9999-999999999999",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Batch register with target_student_id auto-link
# ---------------------------------------------------------------------------


class TestBatchRegisterWithAutoLink:
    """POST /admin/register-batch — PAR with target_student_id creates auto-link."""

    @pytest.mark.asyncio
    async def test_batch_par_with_target_student_creates_link(
        self, client: httpx.AsyncClient, admin_token: str
    ):
        email = f"batch.parent.{uuid.uuid4().hex[:8]}@test.ma"
        resp = await client.post(
            "/admin/register-batch",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "users": [
                    {
                        "email": email,
                        "full_name": "Batch Parent Link",
                        "role": "PAR",
                        "target_student_id": STUDENT_ID,
                    }
                ]
            },
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["total_created"] == 1
        temp_password = data["created"][0]["temp_password"]

        # Login as the new parent
        login_resp = await client.post(
            "/auth/login",
            json={
                "email": email,
                "password": temp_password,
                "school_id": SCHOOL_ID,
            },
        )
        assert login_resp.status_code == 200
        parent_tok = login_resp.json()["data"]["access_token"]

        # Verify auto-link via GET /me/children
        children_resp = await client.get(
            "/me/children",
            headers={"Authorization": f"Bearer {parent_tok}"},
        )
        assert children_resp.status_code == 200
        children = children_resp.json()["data"]
        child_ids = [c["user_id"] for c in children]
        assert STUDENT_ID in child_ids

    @pytest.mark.asyncio
    async def test_batch_std_with_target_student_id_ignored(
        self, client: httpx.AsyncClient, admin_token: str
    ):
        """target_student_id is silently ignored for non-PAR roles in batch."""
        email = f"batch.std.{uuid.uuid4().hex[:8]}@test.ma"
        resp = await client.post(
            "/admin/register-batch",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "users": [
                    {
                        "email": email,
                        "full_name": "Batch Student",
                        "role": "STD",
                        "target_student_id": STUDENT_ID,
                    }
                ]
            },
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["total_created"] == 1
