"""Integration tests for attendance analytics endpoints."""

from __future__ import annotations

import pytest

from tests.integration.api.helpers import CLASS_ID, PERIOD_ID, STUDENT_ID, auth_header


class TestAttendanceAnalyticsApi:
    @pytest.mark.asyncio
    async def test_admin_can_get_student_attendance_analytics(
        self, client, admin_token
    ):
        response = await client.get(
            f"/analytics/attendance/student/{STUDENT_ID}",
            headers=auth_header(admin_token),
            params={"period_id": PERIOD_ID},
        )

        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload["student_id"] == STUDENT_ID
        assert "absence_rate" in payload

    @pytest.mark.asyncio
    async def test_admin_can_get_class_attendance_analytics(self, client, admin_token):
        response = await client.get(
            f"/analytics/attendance/class/{CLASS_ID}",
            headers=auth_header(admin_token),
            params={"period_id": PERIOD_ID},
        )

        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload["class_id"] == CLASS_ID
        assert "students" in payload

    @pytest.mark.asyncio
    async def test_admin_can_get_attendance_trends(self, client, admin_token):
        response = await client.get(
            f"/analytics/attendance/trends/{CLASS_ID}",
            headers=auth_header(admin_token),
            params={"period_id": PERIOD_ID, "granularity": "weekly"},
        )

        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload["class_id"] == CLASS_ID
        assert "points" in payload

    @pytest.mark.asyncio
    async def test_admin_can_list_attendance_alerts(self, client, admin_token):
        response = await client.get(
            "/analytics/attendance/alerts",
            headers=auth_header(admin_token),
            params={"period_id": PERIOD_ID},
        )

        assert response.status_code == 200
        assert isinstance(response.json()["data"], list)

    @pytest.mark.asyncio
    async def test_admin_can_run_threshold_check(self, client, admin_token):
        response = await client.post(
            "/analytics/attendance/check-thresholds",
            headers=auth_header(admin_token),
            json={"period_id": PERIOD_ID},
        )

        assert response.status_code == 200
        payload = response.json()["data"]
        assert "created" in payload
        assert "skipped" in payload
