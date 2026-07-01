"""Integration tests for timetable slot/exception endpoints (Phase 4.C).

Coverage target: app/api/v1/academic/timetable.py ≥ 95 % branch

Routes:
  POST/GET/PUT/DELETE /timetable/slots
  GET /timetable/class/{id}/weekly
  GET /timetable/teacher/{id}/weekly
  GET /timetable/me/weekly
  POST/GET /timetable/exceptions
"""

from __future__ import annotations

import uuid

import pytest

from app.models.erp import TimetableSlot
from tests.integration.api.helpers import (
    CLASS_ID,
    SCHOOL_ID,
    YEAR_ID,
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

TEACHER_ID = "10000000-0000-4000-8000-000000000003"


def _slot_payload(**overrides) -> dict:
    return {
        "class_id": CLASS_ID,
        "academic_year_id": YEAR_ID,
        "day_of_week": 1,
        "start_time": "08:00:00",
        "end_time": "09:00:00",
        "subject": f"Maths-{unique_suffix()}",
        "teacher_id": TEACHER_ID,
        "room": "Salle A",
        **overrides,
    }


class TestTimetableSlotCreate:
    @pytest.mark.asyncio
    async def test_admin_can_create_single_slot(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.post(
            "/timetable/slots",
            headers=auth_header(token),
            json=_slot_payload(),
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["school_id"] == SCHOOL_ID
        assert data["class_id"] == CLASS_ID

    @pytest.mark.asyncio
    async def test_create_slot_db_side_effect(self, client, session_factory):
        """(c) Verify slot is persisted in DB with correct school_id scope."""
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        subj = f"Subj-{unique_suffix()}"
        response = await client.post(
            "/timetable/slots",
            headers=auth_header(token),
            json=_slot_payload(subject=subj),
        )
        assert response.status_code == 201
        slot_id = uuid.UUID(response.json()["data"]["id"])
        async with session_factory() as session:
            slot = await session.get(TimetableSlot, slot_id)
            assert slot is not None, "TimetableSlot not found in DB"
            assert slot.subject == subj
            assert str(slot.school_id) == SCHOOL_ID

    @pytest.mark.asyncio
    async def test_admin_can_create_bulk_slots(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.post(
            "/timetable/slots",
            headers=auth_header(token),
            json={
                "slots": [_slot_payload(day_of_week=2), _slot_payload(day_of_week=4)]
            },
        )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_teacher_cannot_create_slot(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.post(
            "/timetable/slots",
            headers=auth_header(token),
            json=_slot_payload(),
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_student_cannot_create_slot(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        response = await client.post(
            "/timetable/slots",
            headers=auth_header(token),
            json=_slot_payload(),
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_missing_class_id_returns_422(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        payload = _slot_payload()
        del payload["class_id"]
        response = await client.post(
            "/timetable/slots", headers=auth_header(token), json=payload
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_day_of_week_returns_422(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.post(
            "/timetable/slots",
            headers=auth_header(token),
            json=_slot_payload(day_of_week=9),
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_subject_returns_422(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        payload = _slot_payload()
        del payload["subject"]
        response = await client.post(
            "/timetable/slots", headers=auth_header(token), json=payload
        )
        assert response.status_code == 422


class TestTimetableSlotList:
    @pytest.mark.asyncio
    async def test_teacher_can_list_slots(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.get("/timetable/slots", headers=auth_header(token))
        assert response.status_code == 200
        assert isinstance(response.json()["data"], list)

    @pytest.mark.asyncio
    async def test_student_can_list_slots(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        response = await client.get("/timetable/slots", headers=auth_header(token))
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_parent_can_list_slots(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=PARENT_EMAIL, password=PARENT_PASSWORD)
        response = await client.get("/timetable/slots", headers=auth_header(token))
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_slots_filter_by_class(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        await client.post(
            "/timetable/slots", headers=auth_header(token), json=_slot_payload()
        )
        response = await client.get(
            "/timetable/slots",
            headers=auth_header(token),
            params={"class_id": CLASS_ID},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_slots_filter_by_day(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.get(
            "/timetable/slots",
            headers=auth_header(token),
            params={"day_of_week": 1},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_invalid_day_filter_returns_422(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.get(
            "/timetable/slots",
            headers=auth_header(token),
            params={"day_of_week": 8},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401_or_403(self, client, legacy_api_seed):
        _ = legacy_api_seed
        response = await client.get("/timetable/slots")
        assert response.status_code in (401, 403)


class TestTimetableSlotUpdateDelete:
    async def _create_slot(self, client, token) -> str:
        r = await client.post(
            "/timetable/slots", headers=auth_header(token), json=_slot_payload()
        )
        assert r.status_code == 201
        return r.json()["data"]["id"]

    @pytest.mark.asyncio
    async def test_admin_can_update_slot(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        slot_id = await self._create_slot(client, token)
        response = await client.put(
            f"/timetable/slots/{slot_id}",
            headers=auth_header(token),
            json={"subject": "Sciences"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["subject"] == "Sciences"

    @pytest.mark.asyncio
    async def test_update_nonexistent_slot_returns_404(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.put(
            f"/timetable/slots/{uuid.uuid4()}",
            headers=auth_header(token),
            json={"subject": "Sciences"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_teacher_cannot_update_slot(self, client, legacy_api_seed):
        _ = legacy_api_seed
        a_token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        slot_id = await self._create_slot(client, a_token)
        t_token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.put(
            f"/timetable/slots/{slot_id}",
            headers=auth_header(t_token),
            json={"subject": "Hack"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_can_delete_slot(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        slot_id = await self._create_slot(client, token)
        response = await client.delete(
            f"/timetable/slots/{slot_id}", headers=auth_header(token)
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_nonexistent_slot_returns_404(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.delete(
            f"/timetable/slots/{uuid.uuid4()}", headers=auth_header(token)
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_teacher_cannot_delete_slot(self, client, legacy_api_seed):
        _ = legacy_api_seed
        a_token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        slot_id = await self._create_slot(client, a_token)
        t_token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.delete(
            f"/timetable/slots/{slot_id}", headers=auth_header(t_token)
        )
        assert response.status_code == 403


class TestTimetableWeeklyViews:
    @pytest.mark.asyncio
    async def test_student_gets_class_weekly(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        response = await client.get(
            f"/timetable/class/{CLASS_ID}/weekly", headers=auth_header(token)
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_class_weekly_with_date(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.get(
            f"/timetable/class/{CLASS_ID}/weekly",
            headers=auth_header(token),
            params={"target_date": "2026-01-20"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_nonexistent_class_weekly_returns_404(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.get(
            f"/timetable/class/{uuid.uuid4()}/weekly", headers=auth_header(token)
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_teacher_gets_teacher_weekly(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.get(
            f"/timetable/teacher/{TEACHER_ID}/weekly", headers=auth_header(token)
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_me_weekly_student(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        response = await client.get("/timetable/me/weekly", headers=auth_header(token))
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_me_weekly_teacher(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.get("/timetable/me/weekly", headers=auth_header(token))
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_me_weekly_parent(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=PARENT_EMAIL, password=PARENT_PASSWORD)
        response = await client.get("/timetable/me/weekly", headers=auth_header(token))
        assert response.status_code == 200


class TestTimetableExceptions:
    async def _create_slot_id(self, client, token) -> str:
        r = await client.post(
            "/timetable/slots", headers=auth_header(token), json=_slot_payload()
        )
        assert r.status_code == 201
        return r.json()["data"]["id"]

    @pytest.mark.asyncio
    async def test_teacher_can_create_exception(self, client, legacy_api_seed):
        _ = legacy_api_seed
        a_token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        slot_id = await self._create_slot_id(client, a_token)
        t_token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.post(
            "/timetable/exceptions",
            headers=auth_header(t_token),
            json={
                "timetable_slot_id": slot_id,
                "exception_date": "2026-03-15",
                "exception_type": "CANCELED",
                "reason": "Teacher sick",
            },
        )
        assert response.status_code == 201
        assert response.json()["data"]["exception_type"] == "CANCELED"

    @pytest.mark.asyncio
    async def test_admin_can_create_exception(self, client, legacy_api_seed):
        _ = legacy_api_seed
        a_token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        slot_id = await self._create_slot_id(client, a_token)
        response = await client.post(
            "/timetable/exceptions",
            headers=auth_header(a_token),
            json={
                "timetable_slot_id": slot_id,
                "exception_date": "2026-04-10",
                "exception_type": "SUBSTITUTED",
                "substitute_teacher_id": TEACHER_ID,
            },
        )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_student_cannot_create_exception(self, client, legacy_api_seed):
        _ = legacy_api_seed
        a_token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        slot_id = await self._create_slot_id(client, a_token)
        s_token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        response = await client.post(
            "/timetable/exceptions",
            headers=auth_header(s_token),
            json={
                "timetable_slot_id": slot_id,
                "exception_date": "2026-03-15",
                "exception_type": "CANCELED",
            },
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_invalid_exception_type_returns_422(self, client, legacy_api_seed):
        _ = legacy_api_seed
        t_token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.post(
            "/timetable/exceptions",
            headers=auth_header(t_token),
            json={
                "timetable_slot_id": str(uuid.uuid4()),
                "exception_date": "2026-03-15",
                "exception_type": "INVALID",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_nonexistent_slot_exception_returns_404(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        t_token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.post(
            "/timetable/exceptions",
            headers=auth_header(t_token),
            json={
                "timetable_slot_id": str(uuid.uuid4()),
                "exception_date": "2026-03-15",
                "exception_type": "CANCELED",
            },
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_exceptions(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        response = await client.get("/timetable/exceptions", headers=auth_header(token))
        assert response.status_code == 200
        assert isinstance(response.json()["data"], list)

    @pytest.mark.asyncio
    async def test_list_exceptions_with_slot_filter(self, client, legacy_api_seed):
        _ = legacy_api_seed
        a_token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        slot_id = await self._create_slot_id(client, a_token)
        response = await client.get(
            "/timetable/exceptions",
            headers=auth_header(a_token),
            params={"timetable_slot_id": slot_id},
        )
        assert response.status_code == 200
