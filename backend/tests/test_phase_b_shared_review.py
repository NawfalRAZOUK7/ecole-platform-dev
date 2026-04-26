"""Integration tests for Phase B1 — Shared Review API.

Tests:
  GET  /shared-reviews/{child_id}/sessions              — parent lists child sessions
  GET  /shared-reviews/{child_id}/sessions/{session_id}  — parent views session detail
  POST /shared-reviews/{child_id}/sessions/{session_id}/comments — parent adds comment
  RBAC: student cannot access shared-review endpoints
  Ownership: parent cannot view another parent's child sessions
"""

from __future__ import annotations

import uuid

import httpx
import pytest
import pytest_asyncio

from tests.conftest import (
    BASE_URL,
    LOGIN_TIMEOUT,
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    PARENT_EMAIL,
    PARENT_PASSWORD,
    STUDENT_EMAIL,
    STUDENT_PASSWORD,
    TEACHER_EMAIL,
    TEACHER_PASSWORD,
)

# Seed student UUID from seed.py
STUDENT_ID = "10000000-0000-4000-8000-000000000007"
RANDOM_CHILD_ID = "00000000-dead-beef-0000-000000000099"


@pytest_asyncio.fixture
async def client():
    async with httpx.AsyncClient(
        base_url=BASE_URL, timeout=LOGIN_TIMEOUT
    ) as c:
        yield c


async def _login(client: httpx.AsyncClient, email: str, password: str) -> str:
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, f"Login failed for {email}: {resp.text}"
    return resp.json()["data"]["access_token"]


@pytest_asyncio.fixture
async def parent_token(client: httpx.AsyncClient) -> str:
    return await _login(client, PARENT_EMAIL, PARENT_PASSWORD)


@pytest_asyncio.fixture
async def student_token(client: httpx.AsyncClient) -> str:
    return await _login(client, STUDENT_EMAIL, STUDENT_PASSWORD)


@pytest_asyncio.fixture
async def teacher_token(client: httpx.AsyncClient) -> str:
    return await _login(client, TEACHER_EMAIL, TEACHER_PASSWORD)


# ---------------------------------------------------------------------------
# Test: Parent can list child's sessions
# ---------------------------------------------------------------------------
class TestListChildSessions:
    @pytest.mark.asyncio
    async def test_parent_lists_child_sessions(
        self, client: httpx.AsyncClient, parent_token: str
    ):
        """Parent should be able to list their linked child's sessions."""
        resp = await client.get(
            f"/shared-reviews/{STUDENT_ID}/sessions",
            headers={"Authorization": f"Bearer {parent_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "sessions" in data
        assert "total" in data
        assert isinstance(data["sessions"], list)

    @pytest.mark.asyncio
    async def test_parent_lists_sessions_with_pagination(
        self, client: httpx.AsyncClient, parent_token: str
    ):
        """Pagination params should be accepted."""
        resp = await client.get(
            f"/shared-reviews/{STUDENT_ID}/sessions",
            headers={"Authorization": f"Bearer {parent_token}"},
            params={"limit": 5, "offset": 0},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["sessions"]) <= 5

    @pytest.mark.asyncio
    async def test_parent_cannot_view_unlinked_child(
        self, client: httpx.AsyncClient, parent_token: str
    ):
        """Parent should get 403 when viewing a child they are not linked to."""
        resp = await client.get(
            f"/shared-reviews/{RANDOM_CHILD_ID}/sessions",
            headers={"Authorization": f"Bearer {parent_token}"},
        )
        assert resp.status_code in (403, 404)

    @pytest.mark.asyncio
    async def test_student_cannot_access_shared_review(
        self, client: httpx.AsyncClient, student_token: str
    ):
        """Students should not be able to access the shared review endpoint."""
        resp = await client.get(
            f"/shared-reviews/{STUDENT_ID}/sessions",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        # Should be 403 (forbidden) — student doesn't have PERM_PROGRESS_READ
        # or might be 403 from ownership check. Either way, not 200.
        assert resp.status_code in (403, 404)

    @pytest.mark.asyncio
    async def test_unauthenticated_request_rejected(
        self, client: httpx.AsyncClient
    ):
        """Unauthenticated request should be rejected."""
        resp = await client.get(f"/shared-reviews/{STUDENT_ID}/sessions")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Test: Session detail
# ---------------------------------------------------------------------------
class TestSessionDetail:
    @pytest.mark.asyncio
    async def test_nonexistent_session_returns_404(
        self, client: httpx.AsyncClient, parent_token: str
    ):
        """Unknown session ID should return 404."""
        fake_session_id = str(uuid.uuid4())
        resp = await client.get(
            f"/shared-reviews/{STUDENT_ID}/sessions/{fake_session_id}",
            headers={"Authorization": f"Bearer {parent_token}"},
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Test: Add comment
# ---------------------------------------------------------------------------
class TestAddComment:
    @pytest.mark.asyncio
    async def test_comment_validation(
        self, client: httpx.AsyncClient, parent_token: str
    ):
        """Empty comment text should be rejected (validation error)."""
        fake_session_id = str(uuid.uuid4())
        resp = await client.post(
            f"/shared-reviews/{STUDENT_ID}/sessions/{fake_session_id}/comments",
            headers={"Authorization": f"Bearer {parent_token}"},
            json={"text": "", "emoji": None},
        )
        assert resp.status_code == 422  # validation error for min_length=1

    @pytest.mark.asyncio
    async def test_comment_text_too_long(
        self, client: httpx.AsyncClient, parent_token: str
    ):
        """Comment exceeding 1000 chars should be rejected."""
        fake_session_id = str(uuid.uuid4())
        resp = await client.post(
            f"/shared-reviews/{STUDENT_ID}/sessions/{fake_session_id}/comments",
            headers={"Authorization": f"Bearer {parent_token}"},
            json={"text": "x" * 1001},
        )
        assert resp.status_code == 422
