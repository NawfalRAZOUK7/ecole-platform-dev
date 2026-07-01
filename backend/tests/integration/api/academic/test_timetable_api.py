"""Integration tests for timetable generation endpoints."""

from __future__ import annotations

import pytest

from tests.integration.api.helpers import YEAR_ID, auth_header


def constraints_payload() -> dict:
    return {
        "academic_year_id": YEAR_ID,
        "constraints": [
            {
                "constraint_type": "max_consecutive_classes",
                "params": {"max": 3},
            },
            {
                "constraint_type": "room_capacity",
                "params": {"room": "Lab A", "max_students": 30},
            },
        ],
    }


class TestTimetableApi:
    @pytest.mark.asyncio
    async def test_admin_can_set_and_list_constraints(self, client, admin_token):
        set_response = await client.post(
            "/timetable/constraints",
            headers=auth_header(admin_token),
            json=constraints_payload(),
        )
        assert set_response.status_code == 200
        assert isinstance(set_response.json()["data"], list)

        list_response = await client.get(
            "/timetable/constraints",
            headers=auth_header(admin_token),
            params={"academic_year_id": YEAR_ID},
        )

        assert list_response.status_code == 200
        assert isinstance(list_response.json()["data"], list)
        assert any(
            item["constraint_type"] == "max_consecutive_classes"
            and item["params"]["max"] == 3
            for item in list_response.json()["data"]
        )

    @pytest.mark.asyncio
    async def test_admin_can_generate_and_preview_timetable_job(
        self, client, admin_token
    ):
        generate_response = await client.post(
            "/timetable/generate",
            headers=auth_header(admin_token),
            json={"academic_year_id": YEAR_ID},
        )

        assert generate_response.status_code == 200
        job = generate_response.json()["data"]
        assert job["id"]

        status_response = await client.get(
            f"/timetable/generate/{job['id']}",
            headers=auth_header(admin_token),
        )
        assert status_response.status_code == 200

        preview_response = await client.get(
            f"/timetable/generate/{job['id']}/preview",
            headers=auth_header(admin_token),
        )

        assert preview_response.status_code == 200
        assert preview_response.json()["data"]["job"]["id"] == job["id"]

    @pytest.mark.asyncio
    async def test_student_cannot_generate_timetable(self, client, student_token):
        response = await client.post(
            "/timetable/generate",
            headers=auth_header(student_token),
            json={"academic_year_id": YEAR_ID},
        )

        assert response.status_code == 403
