"""Integration tests for rewards endpoints."""

from __future__ import annotations

import pytest

from .helpers import STUDENT_ID, auth_header, login_token, unique_suffix

ADMIN_EMAIL = "admin@ecole-benani.ma"
ADMIN_PASSWORD = "admin123"
TEACHER_EMAIL = "prof.math@ecole-benani.ma"
TEACHER_PASSWORD = "teacher123"
STUDENT_EMAIL = "yassine.alaoui@ecole-benani.ma"
STUDENT_PASSWORD = "student123"


def _badge_payload(**overrides) -> dict:
    return {
        "code": f"badge-{unique_suffix()}",
        "title_fr": "Badge Test",
        "title_en": "Test Badge",
        "is_active": True,
        **overrides,
    }


class TestRewardsApi:
    @pytest.mark.asyncio
    async def test_anyone_can_list_badges(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )

        response = await client.get("/rewards/badges", headers=auth_header(token))
        assert response.status_code == 200
        assert isinstance(response.json()["data"], list)

    @pytest.mark.asyncio
    async def test_admin_can_create_badge(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)

        response = await client.post(
            "/rewards/badges",
            headers=auth_header(token),
            json=_badge_payload(),
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_teacher_cannot_create_badge(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )

        response = await client.post(
            "/rewards/badges",
            headers=auth_header(token),
            json=_badge_payload(),
        )
        assert response.status_code in (403, 404)

    @pytest.mark.asyncio
    async def test_teacher_can_award_points(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )

        response = await client.post(
            "/rewards/award",
            headers=auth_header(token),
            json={
                "student_id": STUDENT_ID,
                "event_type": "quiz_completion",
                "stars": 3,
                "xp": 50,
            },
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "total_stars" in data or "stars" in str(data)

    @pytest.mark.asyncio
    async def test_student_can_view_own_rewards(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )

        response = await client.get("/rewards/me", headers=auth_header(token))
        assert response.status_code == 200
        assert response.json()["data"] is not None
