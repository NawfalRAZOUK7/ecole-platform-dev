"""Integration tests for rubric endpoints."""

from __future__ import annotations

import pytest

from tests.integration.api.helpers import auth_header, unique_suffix


def rubric_payload(title: str) -> dict:
    return {
        "title": title,
        "description": "Rubrique de correction",
        "total_points": 20,
        "criteria": [
            {
                "title": "Clarity",
                "weight": 1.0,
                "position": 0,
                "levels": [
                    {"label": "Excellent", "points": 10, "position": 0},
                    {"label": "Correct", "points": 5, "position": 1},
                ],
            }
        ],
    }


class TestRubricsApi:
    @pytest.mark.asyncio
    async def test_teacher_can_create_and_get_rubric(self, client, teacher_token):
        title = f"Rubric {unique_suffix()}"
        create_response = await client.post(
            "/rubrics",
            headers=auth_header(teacher_token),
            json=rubric_payload(title),
        )

        assert create_response.status_code == 201
        rubric = create_response.json()["data"]
        assert rubric["title"] == title

        get_response = await client.get(
            f"/rubrics/{rubric['id']}",
            headers=auth_header(teacher_token),
        )

        assert get_response.status_code == 200
        assert get_response.json()["data"]["id"] == rubric["id"]

    @pytest.mark.asyncio
    async def test_teacher_can_list_rubrics(self, client, teacher_token):
        response = await client.get("/rubrics", headers=auth_header(teacher_token))

        assert response.status_code == 200
        assert isinstance(response.json()["data"], list)

    @pytest.mark.asyncio
    async def test_teacher_can_duplicate_rubric(self, client, teacher_token):
        title = f"Rubric {unique_suffix()}"
        create_response = await client.post(
            "/rubrics",
            headers=auth_header(teacher_token),
            json=rubric_payload(title),
        )
        rubric_id = create_response.json()["data"]["id"]

        duplicate_response = await client.post(
            f"/rubrics/{rubric_id}/duplicate",
            headers=auth_header(teacher_token),
        )

        assert duplicate_response.status_code == 201
        duplicated = duplicate_response.json()["data"]
        assert duplicated["id"] != rubric_id
        assert duplicated["title"].startswith(title)

    @pytest.mark.asyncio
    async def test_student_cannot_create_rubric(self, client, student_token):
        response = await client.post(
            "/rubrics",
            headers=auth_header(student_token),
            json=rubric_payload(f"Rubric {unique_suffix()}"),
        )

        assert response.status_code == 403
