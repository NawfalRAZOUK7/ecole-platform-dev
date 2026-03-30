"""Integration tests for schools endpoints."""

from __future__ import annotations

import pytest

from .helpers import SCHOOL_ID, SUPERADMIN_EMAIL, SUPERADMIN_PASSWORD, auth_header, login_token, unique_suffix


class TestSchoolsApi:
    @pytest.mark.asyncio
    async def test_admin_can_list_schools(self, client, admin_token):
        response = await client.get("/schools", headers=auth_header(admin_token))

        assert response.status_code == 200
        payload = response.json()
        assert payload["data"]
        assert payload["data"][0]["id"] == SCHOOL_ID

    @pytest.mark.asyncio
    async def test_admin_can_get_seeded_school(self, client, admin_token):
        response = await client.get(f"/schools/{SCHOOL_ID}", headers=auth_header(admin_token))

        assert response.status_code == 200
        assert response.json()["data"]["id"] == SCHOOL_ID

    @pytest.mark.asyncio
    async def test_student_cannot_list_schools(self, client, student_token):
        response = await client.get("/schools", headers=auth_header(student_token))

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_superadmin_can_create_and_delete_school(self, client):
        sup_token = await login_token(
            client,
            email=SUPERADMIN_EMAIL,
            password=SUPERADMIN_PASSWORD,
        )
        suffix = unique_suffix()
        create_response = await client.post(
            "/schools",
            headers=auth_header(sup_token),
            json={
                "name": f"Ecole Test {suffix}",
                "code": f"ecole-{suffix}",
                "city": "Casablanca",
                "email": f"test-{suffix}@ecole.ma",
            },
        )

        assert create_response.status_code == 201
        school_id = create_response.json()["data"]["id"]

        delete_response = await client.delete(
            f"/schools/{school_id}",
            headers=auth_header(sup_token),
        )

        assert delete_response.status_code == 200
        assert delete_response.json()["data"]["deleted_at"] is not None
