"""Integration tests for content age-filtering (G46).

Tests that:
- Students with a date_of_birth get auto-filtered content based on age
- Students without a date_of_birth see all content
- Teachers with explicit target_age see filtered content
- Teachers without filter see all content
- Content without target_age is always visible
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.models.lms import ClassContentAssignment
from tests.integration.api.helpers import auth_header


async def _make_content_visible(
    session_factory, api_context, content_id: uuid.UUID, level_band: str
) -> None:
    """Make platform content discoverable under the new ABAC content scoping.

    Students see only content assigned to their class; teachers see only content
    matching their taught level band. Align both for the api_context class.
    """
    async with session_factory() as session:
        await session.execute(
            text("UPDATE classes SET level_band = :lb WHERE id = :cid"),
            {"lb": level_band, "cid": api_context["class"].id},
        )
        session.add(
            ClassContentAssignment(
                teacher_id=api_context["teacher"]["user"].id,
                class_id=api_context["class"].id,
                content_item_id=content_id,
                school_id=api_context["school"].id,
                assigned_at=datetime.now(timezone.utc),
            )
        )
        await session.commit()


async def _create_content(
    client,
    token: str,
    session_factory,
    api_context,
    *,
    title: str,
    target_age_min: int | None,
    target_age_max: int | None,
    status: str = "published",
) -> dict:
    level_band = "1AEP"
    payload: dict = {
        "title": title,
        "content_type": "story",
        "level_band": level_band,
        "language": "fr",
        "status": status,
    }
    if target_age_min is not None:
        payload["target_age_min"] = target_age_min
    if target_age_max is not None:
        payload["target_age_max"] = target_age_max

    response = await client.post(
        "/cms/content",
        headers=auth_header(token),
        json=payload,
    )
    assert response.status_code == 201, response.text
    data = response.json()["data"]
    await _make_content_visible(
        session_factory, api_context, uuid.UUID(data["id"]), level_band
    )
    return data


async def _set_student_dob(
    session_factory,
    user_id: uuid.UUID,
    dob: date | None,
    school_id: uuid.UUID | None = None,
) -> None:
    """Upsert the student's date_of_birth on their StudentProfile record."""
    async with session_factory() as session:
        # Check if profile exists
        result = await session.execute(
            text("SELECT id FROM student_profiles WHERE user_id = :uid"),
            {"uid": user_id},
        )
        row = result.one_or_none()

        if row is None and school_id is not None:
            # Create the profile if it doesn't exist
            await session.execute(
                text(
                    """
                    INSERT INTO student_profiles
                      (id, user_id, school_id, date_of_birth, created_at)
                    VALUES
                      (gen_random_uuid(), :uid, :school_id, :dob, now())
                    """
                ),
                {"uid": user_id, "school_id": school_id, "dob": dob},
            )
        elif row is not None:
            await session.execute(
                text(
                    "UPDATE student_profiles SET date_of_birth = :dob WHERE user_id = :uid"
                ),
                {"dob": dob, "uid": user_id},
            )
        await session.commit()


@pytest.mark.asyncio
async def test_student_without_dob_sees_all_content(
    client, api_context, session_factory
):
    """Student without date_of_birth is not filtered — sees all published content."""
    cm_token = api_context["content_manager"]["token"]

    # Create age-restricted content
    await _create_content(
        client,
        cm_token,
        session_factory,
        api_context,
        title="Age Restricted Story",
        target_age_min=10,
        target_age_max=15,
    )
    # Create no-age-restriction content
    await _create_content(
        client,
        cm_token,
        session_factory,
        api_context,
        title="Universal Story",
        target_age_min=None,
        target_age_max=None,
    )

    # Ensure student has no DOB (profile may not exist yet; that's fine)
    await _set_student_dob(
        session_factory,
        api_context["student"]["user"].id,
        None,
        school_id=api_context["school"].id,
    )

    response = await client.get(
        "/content-items?content_type=story",
        headers=auth_header(api_context["student"]["token"]),
    )
    assert response.status_code == 200, response.text
    titles = [item["title"] for item in response.json()["data"]]
    assert "Age Restricted Story" in titles
    assert "Universal Story" in titles


@pytest.mark.asyncio
async def test_student_with_dob_gets_age_filtered(client, api_context, session_factory):
    """Student with date_of_birth=today-6years sees content for age 6, not content for age 10-15."""
    cm_token = api_context["content_manager"]["token"]

    suffix = uuid.uuid4().hex[:6]
    await _create_content(
        client,
        cm_token,
        session_factory,
        api_context,
        title=f"Young Story {suffix}",
        target_age_min=5,
        target_age_max=8,
    )
    await _create_content(
        client,
        cm_token,
        session_factory,
        api_context,
        title=f"Older Story {suffix}",
        target_age_min=10,
        target_age_max=15,
    )
    await _create_content(
        client,
        cm_token,
        session_factory,
        api_context,
        title=f"Ageless Story {suffix}",
        target_age_min=None,
        target_age_max=None,
    )

    # Set student age to 6 years
    dob = date.today() - timedelta(days=365 * 6 + 10)
    await _set_student_dob(
        session_factory,
        api_context["student"]["user"].id,
        dob,
        school_id=api_context["school"].id,
    )

    response = await client.get(
        "/content-items?content_type=story",
        headers=auth_header(api_context["student"]["token"]),
    )
    assert response.status_code == 200, response.text
    titles = [item["title"] for item in response.json()["data"]]

    # Age 6 should see the 5-8 story and the ageless story, NOT the 10-15 story
    assert f"Young Story {suffix}" in titles
    assert f"Ageless Story {suffix}" in titles
    assert f"Older Story {suffix}" not in titles


@pytest.mark.asyncio
async def test_teacher_with_explicit_target_age_sees_filtered(
    client, api_context, session_factory
):
    """Teacher with explicit target_age=6 sees only age-appropriate content."""
    cm_token = api_context["content_manager"]["token"]
    suffix = uuid.uuid4().hex[:6]

    await _create_content(
        client,
        cm_token,
        session_factory,
        api_context,
        title=f"Young TCH Story {suffix}",
        target_age_min=5,
        target_age_max=8,
    )
    await _create_content(
        client,
        cm_token,
        session_factory,
        api_context,
        title=f"Older TCH Story {suffix}",
        target_age_min=12,
        target_age_max=15,
    )

    response = await client.get(
        "/content-items?content_type=story&target_age=6",
        headers=auth_header(api_context["teacher"]["token"]),
    )
    assert response.status_code == 200, response.text
    titles = [item["title"] for item in response.json()["data"]]
    assert f"Young TCH Story {suffix}" in titles
    assert f"Older TCH Story {suffix}" not in titles


@pytest.mark.asyncio
async def test_teacher_without_filter_sees_all(client, api_context, session_factory):
    """Teacher without target_age filter sees all published content."""
    cm_token = api_context["content_manager"]["token"]
    suffix = uuid.uuid4().hex[:6]

    await _create_content(
        client,
        cm_token,
        session_factory,
        api_context,
        title=f"Any Age Story {suffix}",
        target_age_min=5,
        target_age_max=8,
    )
    await _create_content(
        client,
        cm_token,
        session_factory,
        api_context,
        title=f"High Age Story {suffix}",
        target_age_min=14,
        target_age_max=17,
    )

    response = await client.get(
        "/content-items?content_type=story",
        headers=auth_header(api_context["teacher"]["token"]),
    )
    assert response.status_code == 200, response.text
    titles = [item["title"] for item in response.json()["data"]]
    assert f"Any Age Story {suffix}" in titles
    assert f"High Age Story {suffix}" in titles


@pytest.mark.asyncio
async def test_content_without_age_always_visible(client, api_context, session_factory):
    """Content with no target_age_min/max is always visible regardless of student age."""
    cm_token = api_context["content_manager"]["token"]
    suffix = uuid.uuid4().hex[:6]

    await _create_content(
        client,
        cm_token,
        session_factory,
        api_context,
        title=f"No Age Story {suffix}",
        target_age_min=None,
        target_age_max=None,
    )

    # Student is 15 years old
    dob = date.today() - timedelta(days=365 * 15 + 10)
    await _set_student_dob(
        session_factory,
        api_context["peer_student"]["user"].id,
        dob,
        school_id=api_context["school"].id,
    )

    response = await client.get(
        "/content-items?content_type=story",
        headers=auth_header(api_context["peer_student"]["token"]),
    )
    assert response.status_code == 200, response.text
    titles = [item["title"] for item in response.json()["data"]]
    assert f"No Age Story {suffix}" in titles
