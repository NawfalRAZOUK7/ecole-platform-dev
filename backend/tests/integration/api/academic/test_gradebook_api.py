"""Integration tests for gradebook endpoints."""

from __future__ import annotations

import pytest

from tests.integration.api.helpers import CLASS_ID, PERIOD_ID, STUDENT_ID, YEAR_ID, auth_header


def categories_payload() -> dict:
    return {
        "class_id": CLASS_ID,
        "period_id": PERIOD_ID,
        "categories": [
            {"name": "Examens", "weight": 0.6, "position": 0},
            {"name": "Devoirs", "weight": 0.4, "position": 1},
        ],
    }


class TestGradebookApi:
    @pytest.mark.asyncio
    async def test_admin_can_set_and_list_grade_categories(self, client, admin_token):
        create_response = await client.post(
            "/gradebook/categories",
            headers=auth_header(admin_token),
            json=categories_payload(),
        )
        assert create_response.status_code == 201
        assert len(create_response.json()["data"]) == 2

        list_response = await client.get(
            f"/gradebook/categories/{CLASS_ID}/{PERIOD_ID}",
            headers=auth_header(admin_token),
        )

        assert list_response.status_code == 200
        assert len(list_response.json()["data"]) == 2

    @pytest.mark.asyncio
    async def test_admin_can_compute_class_averages(self, client, admin_token):
        await client.post(
            "/gradebook/categories",
            headers=auth_header(admin_token),
            json=categories_payload(),
        )

        response = await client.post(
            f"/gradebook/compute/{CLASS_ID}/{PERIOD_ID}",
            headers=auth_header(admin_token),
        )

        assert response.status_code == 200
        assert isinstance(response.json()["data"], list)

    @pytest.mark.asyncio
    async def test_admin_can_get_gradebook_matrix(self, client, admin_token):
        response = await client.get(
            f"/gradebook/{CLASS_ID}/{PERIOD_ID}",
            headers=auth_header(admin_token),
        )

        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload["class_id"] == CLASS_ID
        assert "rows" in payload

    @pytest.mark.asyncio
    async def test_student_can_get_own_transcript(self, client, student_token):
        response = await client.get(
            f"/gradebook/transcript/{STUDENT_ID}",
            headers=auth_header(student_token),
            params={"academic_year_id": YEAR_ID},
        )

        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload["student_id"] == STUDENT_ID
        assert payload["academic_year_id"] == YEAR_ID
