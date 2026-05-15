"""Integration tests for attendance session and justification endpoints."""

from __future__ import annotations

import pytest

from tests.integration.api.helpers import CLASS_ID, PERIOD_ID, STUDENT_ID, auth_header, login_token

ADMIN_EMAIL = "admin@ecole-benani.ma"
ADMIN_PASSWORD = "admin123"
TEACHER_EMAIL = "prof.math@ecole-benani.ma"
TEACHER_PASSWORD = "teacher123"
STUDENT_EMAIL = "yassine.alaoui@ecole-benani.ma"
STUDENT_PASSWORD = "student123"
PARENT_EMAIL = "parent.alaoui@gmail.com"
PARENT_PASSWORD = "parent123"

# Use a date that does not conflict with the seed attendance session (2026-01-15)
NEW_SESSION_DATE = "2026-02-20"


class TestAttendanceApi:
    @pytest.mark.asyncio
    async def test_teacher_can_create_attendance_session(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )

        response = await client.post(
            "/attendance/sessions",
            headers=auth_header(token),
            json={
                "class_id": CLASS_ID,
                "period_id": PERIOD_ID,
                "session_date": NEW_SESSION_DATE,
                "slot": "morning",
                "records": [
                    {"student_id": STUDENT_ID, "status": "present"},
                ],
            },
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["class_id"] == CLASS_ID
        assert len(data["records"]) == 1

    @pytest.mark.asyncio
    async def test_student_cannot_create_attendance_session(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )

        response = await client.post(
            "/attendance/sessions",
            headers=auth_header(token),
            json={
                "class_id": CLASS_ID,
                "period_id": PERIOD_ID,
                "session_date": NEW_SESSION_DATE,
                "slot": "afternoon",
                "records": [{"student_id": STUDENT_ID, "status": "present"}],
            },
        )
        assert response.status_code in (403, 404)

    @pytest.mark.asyncio
    async def test_parent_can_submit_justification(self, client, legacy_api_seed):
        _ = legacy_api_seed
        # The seeded attendance record (ATTENDANCE_RECORD_ID) has status "absent"
        from tests.integration.api.conftest import ATTENDANCE_RECORD_ID

        parent_token = await login_token(
            client, email=PARENT_EMAIL, password=PARENT_PASSWORD
        )
        response = await client.post(
            "/attendance/justifications",
            headers=auth_header(parent_token),
            json={
                "attendance_record_id": str(ATTENDANCE_RECORD_ID),
                "reason": "Medical appointment",
            },
        )
        # 201 created or 409 if already justified from a previous test run
        assert response.status_code in (201, 409)

    @pytest.mark.asyncio
    async def test_duplicate_session_rejected(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )

        payload = {
            "class_id": CLASS_ID,
            "period_id": PERIOD_ID,
            "session_date": "2026-03-10",
            "slot": "morning",
            "records": [{"student_id": STUDENT_ID, "status": "present"}],
        }
        first = await client.post(
            "/attendance/sessions", headers=auth_header(token), json=payload
        )
        assert first.status_code == 201

        second = await client.post(
            "/attendance/sessions", headers=auth_header(token), json=payload
        )
        assert second.status_code == 409
