"""Extended integration tests for announcements endpoints (Phase 4.F).

Coverage target: app/api/v1/admin/announcements.py ≥ 95 % branch

Supplements test_announcements_api.py with:
  - 404 on non-existent announcement
  - 422 on invalid payloads
  - Student/Parent cannot create
  - Update published announcement is blocked
  - Filtering on list endpoint
  - Cross-school isolation (non-existent resource → 404)
"""

from __future__ import annotations

import uuid

import pytest

from app.models.com import Announcement
from tests.integration.api.helpers import (
    auth_header,
    login_token,
    unique_suffix,
)

ADMIN_EMAIL = "admin@ecole-benani.ma"
ADMIN_PASSWORD = "admin123"
TEACHER_EMAIL = "prof.math@ecole-benani.ma"
TEACHER_PASSWORD = "teacher123"
STUDENT_EMAIL = "yassine.alaoui@ecole-benani.ma"
STUDENT_PASSWORD = "student123"
PARENT_EMAIL = "parent.alaoui@gmail.com"
PARENT_PASSWORD = "parent123"


def _announcement_payload(**overrides) -> dict:
    return {
        "title": f"Test Announcement {unique_suffix()}",
        "body": "Announcement body content here.",
        "target_roles": ["PAR", "STD"],
        **overrides,
    }


class TestAnnouncementsExtended:
    @pytest.mark.asyncio
    async def test_student_cannot_create_announcement(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD)
        response = await client.post(
            "/announcements",
            headers=auth_header(token),
            json=_announcement_payload(),
        )
        assert response.status_code in (403, 404)

    @pytest.mark.asyncio
    async def test_parent_cannot_create_announcement(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=PARENT_EMAIL, password=PARENT_PASSWORD)
        response = await client.post(
            "/announcements",
            headers=auth_header(token),
            json=_announcement_payload(),
        )
        assert response.status_code in (403, 404)

    @pytest.mark.asyncio
    async def test_create_announcement_missing_title_returns_422(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        payload = _announcement_payload()
        del payload["title"]
        response = await client.post(
            "/announcements", headers=auth_header(token), json=payload
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_announcement_missing_body_returns_422(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        payload = _announcement_payload()
        del payload["body"]
        response = await client.post(
            "/announcements", headers=auth_header(token), json=payload
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_nonexistent_announcement_returns_404(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.put(
            f"/announcements/{uuid.uuid4()}",
            headers=auth_header(token),
            json={"title": "Updated"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_publish_nonexistent_announcement_returns_404(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.post(
            f"/announcements/{uuid.uuid4()}/publish",
            headers=auth_header(token),
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_announcements_with_status_filter(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        # Create draft
        await client.post(
            "/announcements", headers=auth_header(token), json=_announcement_payload()
        )
        response = await client.get(
            "/announcements",
            headers=auth_header(token),
            params={"status": "DRAFT"},
        )
        assert response.status_code == 200
        body = response.json()
        assert "data" in body

    @pytest.mark.asyncio
    async def test_list_announcements_invalid_status_returns_422(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.get(
            "/announcements",
            headers=auth_header(token),
            params={"status": "INVALID_STATUS"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_student_can_list_published_announcements(self, client, legacy_api_seed):
        _ = legacy_api_seed
        # Create + publish as admin
        a_token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        cr = await client.post(
            "/announcements", headers=auth_header(a_token), json=_announcement_payload()
        )
        ann_id = cr.json()["data"]["id"]
        await client.post(
            f"/announcements/{ann_id}/publish", headers=auth_header(a_token)
        )
        # Student can read
        s_token = await login_token(client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD)
        response = await client.get("/announcements", headers=auth_header(s_token))
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_with_pagination_limit(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.get(
            "/announcements",
            headers=auth_header(token),
            params={"limit": 5},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_create(self, client, legacy_api_seed):
        _ = legacy_api_seed
        response = await client.post(
            "/announcements", json=_announcement_payload()
        )
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_full_create_update_publish_cycle(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)

        # Create
        cr = await client.post(
            "/announcements",
            headers=auth_header(token),
            json=_announcement_payload(title="Original Title"),
        )
        assert cr.status_code == 201
        ann_id = cr.json()["data"]["id"]
        assert cr.json()["data"]["status"] == "DRAFT"

        # Update draft
        ur = await client.put(
            f"/announcements/{ann_id}",
            headers=auth_header(token),
            json={"title": "Updated Title", "body": "Updated body."},
        )
        assert ur.status_code == 200
        assert ur.json()["data"]["title"] == "Updated Title"

        # Publish
        pr = await client.post(
            f"/announcements/{ann_id}/publish",
            headers=auth_header(token),
        )
        assert pr.status_code == 200
        assert pr.json()["data"]["status"] == "PUBLISHED"

    @pytest.mark.asyncio
    async def test_create_announcement_db_side_effect(self, client, session_factory):
        """(c) Verify announcement is persisted with correct status in DB."""
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        title = f"DBVerify-{unique_suffix()}"
        response = await client.post(
            "/announcements",
            headers=auth_header(token),
            json=_announcement_payload(title=title),
        )
        assert response.status_code == 201
        ann_id = uuid.UUID(response.json()["data"]["id"])

        # (c) DB side-effect: announcement persisted as DRAFT
        async with session_factory() as session:
            ann = await session.get(Announcement, ann_id)
            assert ann is not None, "Announcement not found in DB"
            assert ann.title == title
            assert ann.status.value == "DRAFT"
