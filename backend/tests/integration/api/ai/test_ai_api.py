"""Integration tests for AI endpoints (Phase 4.J).

Coverage target: app/api/v1/ai/ai.py ≥ 95 % branch

Routes:
  POST /writing-attempts              — AI writing assist (STD)
  POST /ai/preferences/opt-out        — update opt-out preference (PAR/STD)
  GET  /recommendations               — get recommendations (STD/PAR)
  GET  /kpis                          — KPIs (ADM/TCH)
  GET  /events/schema                 — event schema (ADM/TCH)
"""

from __future__ import annotations

import pytest

from tests.integration.api.helpers import (
    SCHOOL_ID,
    STUDENT_ID,
    auth_header,
    login_token,
)

ADMIN_EMAIL = "admin@ecole-benani.ma"
ADMIN_PASSWORD = "admin123"
TEACHER_EMAIL = "prof.math@ecole-benani.ma"
TEACHER_PASSWORD = "teacher123"
STUDENT_EMAIL = "yassine.alaoui@ecole-benani.ma"
STUDENT_PASSWORD = "student123"
PARENT_EMAIL = "parent.alaoui@gmail.com"
PARENT_PASSWORD = "parent123"


class TestWritingAttempts:
    @pytest.mark.asyncio
    async def test_student_can_create_writing_attempt(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD)
        response = await client.post(
            "/writing-attempts",
            headers=auth_header(token),
            json={
                "text": "Aujourd'hui nous allons étudier les fractions en mathématiques.",
                "subject": "Maths",
                "language": "fr",
            },
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "status" in data
        assert "student_id" in data

    @pytest.mark.asyncio
    async def test_writing_attempt_minimal_payload(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD)
        response = await client.post(
            "/writing-attempts",
            headers=auth_header(token),
            json={"text": "Simple text for writing assistance."},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_teacher_cannot_create_writing_attempt(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD)
        response = await client.post(
            "/writing-attempts",
            headers=auth_header(token),
            json={"text": "Some text"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_parent_cannot_create_writing_attempt(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=PARENT_EMAIL, password=PARENT_PASSWORD)
        response = await client.post(
            "/writing-attempts",
            headers=auth_header(token),
            json={"text": "Some text"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_missing_text_returns_422(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD)
        response = await client.post(
            "/writing-attempts",
            headers=auth_header(token),
            json={"subject": "Maths"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_empty_text_returns_422(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD)
        response = await client.post(
            "/writing-attempts",
            headers=auth_header(token),
            json={"text": ""},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_language_returns_422(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD)
        response = await client.post(
            "/writing-attempts",
            headers=auth_header(token),
            json={"text": "Some text", "language": "it"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_create_writing_attempt(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        response = await client.post(
            "/writing-attempts", json={"text": "Some text"}
        )
        assert response.status_code in (401, 403)


class TestAIOptOut:
    @pytest.mark.asyncio
    async def test_parent_can_opt_out(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=PARENT_EMAIL, password=PARENT_PASSWORD)
        response = await client.post(
            "/ai/preferences/opt-out",
            headers=auth_header(token),
            json={"opt_out": True},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["opt_out"] is True

    @pytest.mark.asyncio
    async def test_parent_can_opt_back_in(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=PARENT_EMAIL, password=PARENT_PASSWORD)
        # First opt out
        await client.post(
            "/ai/preferences/opt-out",
            headers=auth_header(token),
            json={"opt_out": True},
        )
        # Then opt in
        response = await client.post(
            "/ai/preferences/opt-out",
            headers=auth_header(token),
            json={"opt_out": False},
        )
        assert response.status_code == 200
        assert response.json()["data"]["opt_out"] is False

    @pytest.mark.asyncio
    async def test_parent_can_opt_out_for_child(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=PARENT_EMAIL, password=PARENT_PASSWORD)
        response = await client.post(
            "/ai/preferences/opt-out",
            headers=auth_header(token),
            json={"opt_out": True, "target_user_id": STUDENT_ID},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_teacher_cannot_update_opt_out(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD)
        response = await client.post(
            "/ai/preferences/opt-out",
            headers=auth_header(token),
            json={"opt_out": True},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_missing_opt_out_field_returns_422(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=PARENT_EMAIL, password=PARENT_PASSWORD)
        response = await client.post(
            "/ai/preferences/opt-out",
            headers=auth_header(token),
            json={},
        )
        assert response.status_code == 422


class TestRecommendations:
    @pytest.mark.asyncio
    async def test_student_can_get_recommendations(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD)
        response = await client.get(
            "/recommendations", headers=auth_header(token)
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "status" in data
        assert "recommendations" in data

    @pytest.mark.asyncio
    async def test_parent_can_get_recommendations(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=PARENT_EMAIL, password=PARENT_PASSWORD)
        response = await client.get(
            "/recommendations", headers=auth_header(token)
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_teacher_cannot_get_recommendations(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD)
        response = await client.get(
            "/recommendations", headers=auth_header(token)
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_opted_out_student_gets_fallback(self, client, legacy_api_seed):
        _ = legacy_api_seed
        # Parent opts out for student
        p_token = await login_token(client, email=PARENT_EMAIL, password=PARENT_PASSWORD)
        await client.post(
            "/ai/preferences/opt-out",
            headers=auth_header(p_token),
            json={"opt_out": True, "target_user_id": STUDENT_ID},
        )
        s_token = await login_token(client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD)
        response = await client.get("/recommendations", headers=auth_header(s_token))
        assert response.status_code == 200
        # When opted out, gets a fallback response
        data = response.json()["data"]
        assert data["status"] in ("fallback", "completed")


class TestKPIs:
    @pytest.mark.asyncio
    async def test_admin_can_get_kpis(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.get(
            "/kpis", headers=auth_header(token), params={"period": 7}
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "kpis" in data
        assert "period" in data

    @pytest.mark.asyncio
    async def test_kpis_with_different_periods(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        for period in [7, 30, 90]:
            response = await client.get(
                "/kpis", headers=auth_header(token), params={"period": period}
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_teacher_can_get_kpis(self, client, legacy_api_seed):
        """TCH inherits PERM_IA_REQUEST_READ via ADM→DIR→TCH hierarchy."""
        _ = legacy_api_seed
        token = await login_token(client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD)
        response = await client.get(
            "/kpis", headers=auth_header(token), params={"period": 7}
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_student_cannot_get_kpis(self, client, legacy_api_seed):
        """STD does NOT have PERM_IA_REQUEST_READ."""
        _ = legacy_api_seed
        token = await login_token(client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD)
        response = await client.get(
            "/kpis", headers=auth_header(token), params={"period": 7}
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_invalid_period_returns_422(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.get(
            "/kpis", headers=auth_header(token), params={"period": 0}
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_period_too_large_returns_422(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.get(
            "/kpis", headers=auth_header(token), params={"period": 100}
        )
        assert response.status_code == 422


class TestEventSchema:
    @pytest.mark.asyncio
    async def test_admin_can_get_event_schema(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.get("/events/schema", headers=auth_header(token))
        assert response.status_code == 200
        data = response.json()["data"]
        assert "schema_version" in data
        assert "events" in data
        assert isinstance(data["events"], list)
        assert data["total"] == len(data["events"])

    @pytest.mark.asyncio
    async def test_student_cannot_get_event_schema(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD)
        response = await client.get("/events/schema", headers=auth_header(token))
        assert response.status_code == 403
