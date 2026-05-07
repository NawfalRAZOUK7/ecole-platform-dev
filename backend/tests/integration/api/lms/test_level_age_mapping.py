"""Integration tests for the level-age mapping API (G46)."""

from __future__ import annotations

import pytest

from tests.integration.api.helpers import auth_header


@pytest.mark.asyncio
async def test_get_levels_returns_13_defaults(client, api_context):
    """GET /levels returns all 13 default platform mappings in display order."""
    response = await client.get(
        "/levels",
        headers=auth_header(api_context["admin"]["token"]),
    )
    assert response.status_code == 200, response.text
    items = response.json()["data"]
    assert len(items) == 13

    # Check ordering by display_order
    orders = [item["display_order"] for item in items]
    assert orders == sorted(orders)

    # Check first and last entries
    codes = [item["level_code"] for item in items]
    assert codes[0] == "maternelle"
    assert codes[-1] == "terminale"


@pytest.mark.asyncio
async def test_get_levels_includes_age_range(client, api_context):
    """Each mapping has valid age range fields."""
    response = await client.get(
        "/levels",
        headers=auth_header(api_context["admin"]["token"]),
    )
    assert response.status_code == 200, response.text
    items = response.json()["data"]
    for item in items:
        assert isinstance(item["default_age_min"], int)
        assert isinstance(item["default_age_max"], int)
        assert item["default_age_min"] < item["default_age_max"]

    # Check CP specifically
    cp = next(i for i in items if i["level_code"] == "cp")
    assert cp["default_age_min"] == 5
    assert cp["default_age_max"] == 6


@pytest.mark.asyncio
async def test_put_level_school_override_as_admin(client, api_context):
    """PUT /levels/cp?school_id=... with admin auth creates a school override."""
    school_id = str(api_context["school"].id)
    response = await client.put(
        f"/levels/cp?school_id={school_id}",
        headers=auth_header(api_context["admin"]["token"]),
        json={"default_age_min": 5, "default_age_max": 7},
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["default_age_min"] == 5
    assert data["default_age_max"] == 7
    assert data["level_code"] == "cp"
    assert data["school_id"] == school_id

    # Verify override appears when school_id query param is passed
    get_resp = await client.get(
        f"/levels?school_id={school_id}",
        headers=auth_header(api_context["admin"]["token"]),
    )
    items = get_resp.json()["data"]
    cp = next(i for i in items if i["level_code"] == "cp")
    assert cp["default_age_max"] == 7


@pytest.mark.asyncio
async def test_put_level_as_teacher_returns_403(client, api_context):
    """PUT /levels/cp with teacher auth returns 403 Forbidden."""
    school_id = str(api_context["school"].id)
    response = await client.put(
        f"/levels/cp?school_id={school_id}",
        headers=auth_header(api_context["teacher"]["token"]),
        json={"default_age_min": 5, "default_age_max": 9},
    )
    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_get_levels_student_accessible(client, api_context):
    """GET /levels is accessible to all authenticated users including students."""
    response = await client.get(
        "/levels",
        headers=auth_header(api_context["student"]["token"]),
    )
    assert response.status_code == 200, response.text
    assert len(response.json()["data"]) == 13


@pytest.mark.asyncio
async def test_get_levels_unauthenticated_returns_401(client):
    """GET /levels without auth returns 401."""
    response = await client.get("/levels")
    assert response.status_code == 401, response.text
