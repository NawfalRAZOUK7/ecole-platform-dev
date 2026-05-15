"""Integration tests for announcements endpoints."""

from __future__ import annotations

import pytest

from tests.integration.api.helpers import SCHOOL_ID, auth_header, login_token, unique_suffix

ADMIN_EMAIL = "admin@ecole-benani.ma"
ADMIN_PASSWORD = "admin123"
TEACHER_EMAIL = "prof.math@ecole-benani.ma"
TEACHER_PASSWORD = "teacher123"


def _create_payload(**overrides) -> dict:
    return {
        "title": f"Test Announcement {unique_suffix()}",
        "body": "Body content for the announcement.",
        "target_roles": ["PAR", "STD"],
        **overrides,
    }


class TestAnnouncementsApi:
    @pytest.mark.asyncio
    async def test_admin_can_create_announcement(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.post(
            "/announcements",
            headers=auth_header(token),
            json=_create_payload(),
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["status"] == "DRAFT"
        assert data["school_id"] == SCHOOL_ID

    @pytest.mark.asyncio
    async def test_teacher_cannot_create_announcement(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.post(
            "/announcements",
            headers=auth_header(token),
            json=_create_payload(),
        )
        assert response.status_code in (403, 404)

    @pytest.mark.asyncio
    async def test_admin_can_list_announcements(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)

        await client.post(
            "/announcements",
            headers=auth_header(token),
            json=_create_payload(),
        )

        list_response = await client.get(
            "/announcements",
            headers=auth_header(token),
        )
        assert list_response.status_code == 200
        payload = list_response.json()
        assert "data" in payload
        assert isinstance(payload["data"], list)

    @pytest.mark.asyncio
    async def test_admin_can_publish_announcement(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)

        create_resp = await client.post(
            "/announcements",
            headers=auth_header(token),
            json=_create_payload(),
        )
        assert create_resp.status_code == 201
        announcement_id = create_resp.json()["data"]["id"]

        publish_resp = await client.post(
            f"/announcements/{announcement_id}/publish",
            headers=auth_header(token),
        )
        assert publish_resp.status_code == 200
        assert publish_resp.json()["data"]["status"] == "PUBLISHED"

    @pytest.mark.asyncio
    async def test_admin_can_update_draft_announcement(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)

        create_resp = await client.post(
            "/announcements",
            headers=auth_header(token),
            json=_create_payload(title="Original Title"),
        )
        announcement_id = create_resp.json()["data"]["id"]

        update_resp = await client.put(
            f"/announcements/{announcement_id}",
            headers=auth_header(token),
            json={"title": "Updated Title"},
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["data"]["title"] == "Updated Title"
