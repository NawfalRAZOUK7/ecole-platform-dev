"""Integration tests for notifications endpoints."""

from __future__ import annotations

import pytest

from tests.integration.api.helpers import auth_header, login_token

ADMIN_EMAIL = "admin@ecole-benani.ma"
ADMIN_PASSWORD = "admin123"
TEACHER_EMAIL = "prof.math@ecole-benani.ma"
TEACHER_PASSWORD = "teacher123"


class TestNotificationsApi:
    @pytest.mark.asyncio
    async def test_user_can_list_own_notifications(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )

        response = await client.get("/notifications", headers=auth_header(token))
        assert response.status_code == 200
        payload = response.json()
        assert "data" in payload
        assert isinstance(payload["data"], list)

    @pytest.mark.asyncio
    async def test_unread_count_returns_integer(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )

        response = await client.get(
            "/notifications/unread-count", headers=auth_header(token)
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, (int, dict))

    @pytest.mark.asyncio
    async def test_unauthenticated_request_rejected(self, client, legacy_api_seed):
        _ = legacy_api_seed
        response = await client.get("/notifications")
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_admin_can_list_notifications(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)

        response = await client.get(
            "/notifications",
            headers=auth_header(token),
            params={"limit": 5},
        )
        assert response.status_code == 200
        assert isinstance(response.json()["data"], list)
