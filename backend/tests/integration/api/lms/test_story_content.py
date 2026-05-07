"""Integration tests for story content and story-reader endpoints."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from app.models.documents import Document
from app.models.lms import ContentProgress
from app.models.rewards import RewardEvent
from tests.integration.api.helpers import auth_header


def _sample_png_bytes() -> bytes:
    return bytes.fromhex(
        "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C489"
        "0000000A49444154789C6360000002000154A24F5D0000000049454E44AE426082"
    )


async def _create_cms_content(
    client,
    token: str,
    *,
    title: str,
    content_type: str = "story",
    **overrides,
) -> dict:
    payload = {
        "title": title,
        "content_type": content_type,
        "level_band": "preschool",
        "language": "ar",
        "subject": "arabic_letters",
        "description": "محتوى اختباري للحروف العربية",
        "page_count": 3,
        "letter": "أ",
        "target_age_min": 4,
        "target_age_max": 7,
        "theme_color": "#7B1FA2",
        "status": "published",
        **overrides,
    }
    response = await client.post(
        "/cms/content",
        headers=auth_header(token),
        json=payload,
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


@pytest.mark.asyncio
async def test_create_story_content_with_new_fields(client, api_context):
    content = await _create_cms_content(
        client,
        api_context["content_manager"]["token"],
        title="حرف الألف",
        page_count=12,
        letter="أ",
        target_age_min=4,
        target_age_max=7,
        theme_color="#7B1FA2",
    )

    assert content["content_type"] == "story"
    assert content["page_count"] == 12
    assert content["letter"] == "أ"
    assert content["target_age_min"] == 4
    assert content["target_age_max"] == 7
    assert content["theme_color"] == "#7B1FA2"


@pytest.mark.asyncio
async def test_list_content_filter_by_letter(client, api_context):
    alif = await _create_cms_content(
        client,
        api_context["content_manager"]["token"],
        title="قصة حرف الألف",
        letter="غ",
    )
    baa = await _create_cms_content(
        client,
        api_context["content_manager"]["token"],
        title="قصة حرف الباء",
        letter="ق",
        theme_color="#009688",
    )

    response = await client.get(
        "/content-items",
        headers=auth_header(api_context["student"]["token"]),
        params={"letter": "غ"},
    )

    assert response.status_code == 200, response.text
    payload = response.json()["data"]
    returned_ids = {item["id"] for item in payload}
    assert alif["id"] in returned_ids
    assert baa["id"] not in returned_ids


@pytest.mark.asyncio
async def test_list_content_filter_by_target_age(client, api_context):
    younger = await _create_cms_content(
        client,
        api_context["content_manager"]["token"],
        title="قصة للصغار",
        target_age_min=11,
        target_age_max=11,
    )
    older = await _create_cms_content(
        client,
        api_context["content_manager"]["token"],
        title="قصة للكبار",
        target_age_min=12,
        target_age_max=12,
        letter="ز",
        theme_color="#3F51B5",
    )

    response = await client.get(
        "/content-items",
        headers=auth_header(api_context["student"]["token"]),
        params={"target_age": 11},
    )

    assert response.status_code == 200, response.text
    payload = response.json()["data"]
    returned_ids = {item["id"] for item in payload}
    assert younger["id"] in returned_ids
    assert older["id"] not in returned_ids


@pytest.mark.asyncio
async def test_get_story_pages_ordered(client, api_context):
    story = await _create_cms_content(
        client,
        api_context["content_manager"]["token"],
        title="قصة الصفحات المرتبة",
    )

    for page_number, has_activity in ((2, True), (1, False), (3, False)):
        response = await client.post(
            f"/content-items/{story['id']}/pages",
            headers=auth_header(api_context["content_manager"]["token"]),
            data={
                "page_number": str(page_number),
                "narration_text": f"الصفحة {page_number}",
                "has_activity": str(has_activity).lower(),
                "asset_type": "page_image",
            },
            files={
                "file": (
                    f"page-{page_number}.png",
                    _sample_png_bytes(),
                    "image/png",
                )
            },
        )
        assert response.status_code == 201, response.text

    pages_response = await client.get(
        f"/content-items/{story['id']}/pages",
        headers=auth_header(api_context["student"]["token"]),
    )

    assert pages_response.status_code == 200, pages_response.text
    payload = pages_response.json()["data"]
    assert [item["page_number"] for item in payload] == [1, 2, 3]
    assert payload[1]["has_activity"] is True
    assert payload[1]["narration_text"] == "الصفحة 2"


@pytest.mark.asyncio
async def test_complete_content_awards_stars(client, api_context, session_factory):
    story = await _create_cms_content(
        client,
        api_context["content_manager"]["token"],
        title="قصة الإكمال",
    )

    response = await client.post(
        f"/content-items/{story['id']}/complete",
        headers=auth_header(api_context["student"]["token"]),
        json={"time_spent_seconds": 95},
    )

    assert response.status_code == 200, response.text
    payload = response.json()["data"]
    assert payload["progress"]["status"] == "completed"
    assert payload["reward"]["stars"] == 10
    assert payload["reward"]["xp"] == 15

    async with session_factory() as session:
        progress = (
            (
                await session.execute(
                    select(ContentProgress).where(
                        ContentProgress.student_id == api_context["student"]["user"].id,
                        ContentProgress.content_item_id == uuid.UUID(story["id"]),
                    )
                )
            )
            .scalars()
            .one()
        )
        event = (
            (
                await session.execute(
                    select(RewardEvent).where(
                        RewardEvent.student_id == api_context["student"]["user"].id,
                        RewardEvent.source_id == uuid.UUID(story["id"]),
                    )
                )
            )
            .scalars()
            .one()
        )

    assert progress.status == "completed"
    assert event.event_type == "content_completed"
    assert event.stars_earned == 10


@pytest.mark.asyncio
async def test_save_coloring_creates_document(client, api_context, session_factory):
    coloring_book = await _create_cms_content(
        client,
        api_context["content_manager"]["token"],
        title="دفتر التلوين",
        content_type="coloring_book",
        letter=None,
        page_count=5,
    )

    response = await client.post(
        f"/content-items/{coloring_book['id']}/coloring/save",
        headers=auth_header(api_context["student"]["token"]),
        files={
            "file": (
                "coloring.png",
                _sample_png_bytes(),
                "image/png",
            )
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()["data"]
    assert payload["reward"]["stars"] == 5
    assert payload["reward"]["xp"] == 8

    async with session_factory() as session:
        document = (
            (
                await session.execute(
                    select(Document).where(
                        Document.id == uuid.UUID(payload["document_id"])
                    )
                )
            )
            .scalars()
            .one()
        )

    assert str(document.linked_student_id) == str(api_context["student"]["user"].id)
    assert document.category == "other"
