"""Role boundary tests for common privilege-escalation attempts."""

from __future__ import annotations

import uuid

import pytest

from .conftest import PERIOD_ID, SCHOOL_ID, STUDENT_ID, YEAR_ID, auth_header


@pytest.mark.asyncio
async def test_student_cannot_list_schools(client, student_token):
    response = await client.get("/schools", headers=auth_header(student_token))

    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_parent_cannot_impersonate_users(client, parent_token):
    response = await client.post(
        f"/admin/impersonate/{STUDENT_ID}",
        headers=auth_header(parent_token),
    )

    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_teacher_cannot_update_school_settings(client, teacher_token):
    response = await client.patch(
        f"/schools/{SCHOOL_ID}",
        headers=auth_header(teacher_token),
        json={"city": "Rabat"},
    )

    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_content_manager_cannot_update_school_settings(client, content_mgr_token):
    response = await client.patch(
        f"/schools/{SCHOOL_ID}",
        headers=auth_header(content_mgr_token),
        json={"city": "Rabat"},
    )

    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_student_cannot_create_fee_structure(client, student_token):
    response = await client.post(
        "/billing/fee-structures",
        headers=auth_header(student_token),
        json={
            "academic_year_id": YEAR_ID,
            "name": "Tentative etudiant",
            "amount": 500.0,
            "currency": "MAD",
            "frequency": "MONTHLY",
            "due_day": 5,
            "applies_to_level": "6eme",
        },
    )

    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_parent_cannot_run_attendance_thresholds(client, parent_token):
    response = await client.post(
        "/analytics/attendance/check-thresholds",
        headers=auth_header(parent_token),
        json={"period_id": PERIOD_ID},
    )

    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_teacher_cannot_manage_timetable_constraints(client, teacher_token):
    response = await client.get(
        "/timetable/constraints",
        headers=auth_header(teacher_token),
        params={"academic_year_id": YEAR_ID},
    )

    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_director_cannot_create_school_without_superadmin_role(
    client, director_token
):
    suffix = uuid.uuid4().hex[:8]
    response = await client.post(
        "/schools",
        headers=auth_header(director_token),
        json={
            "name": f"Ecole Escalade {suffix}",
            "code": f"escalade-{suffix}",
            "city": "Casablanca",
            "email": f"escalade-{suffix}@ecole.ma",
        },
    )

    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_admin_cannot_create_school_without_superadmin_role(client, admin_token):
    suffix = uuid.uuid4().hex[:8]
    response = await client.post(
        "/schools",
        headers=auth_header(admin_token),
        json={
            "name": f"Ecole Admin {suffix}",
            "code": f"admin-{suffix}",
            "city": "Casablanca",
            "email": f"admin-{suffix}@ecole.ma",
        },
    )

    assert response.status_code == 403, response.text
