"""Integration tests for the games API."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models.rewards import RewardEvent
from tests.factories.games import GameConfigFactory
from tests.integration.api.helpers import auth_header


def _memory_match_payload() -> dict:
    return {
        "game_type": "memory_match",
        "title": "Lettres faciles",
        "title_ar": "مطابقة الحروف السهلة",
        "title_fr": "Memoire lettres faciles",
        "subject": "arabic_letters",
        "difficulty": "easy",
        "target_age_min": 4,
        "target_age_max": 6,
        "config": {
            "pairs": [
                {
                    "front": "أ",
                    "back": "أرنب",
                    "image_url": "https://cdn.example.com/alif.png",
                },
                {
                    "front": "ب",
                    "back": "بطة",
                    "image_url": "https://cdn.example.com/baa.png",
                },
            ],
            "grid_cols": 2,
            "grid_rows": 2,
            "time_limit_seconds": 60,
        },
        "reward_stars": 12,
        "reward_xp": 18,
        "is_active": True,
    }


@pytest.mark.asyncio
async def test_create_game_config_memory_match(client, api_context):
    response = await client.post(
        "/games/configs",
        headers=auth_header(api_context["teacher"]["token"]),
        json=_memory_match_payload(),
    )

    assert response.status_code == 201, response.text
    payload = response.json()["data"]
    assert payload["game_type"] == "memory_match"
    assert payload["difficulty"] == "easy"
    assert payload["reward_stars"] == 12
    assert payload["school_id"] == str(api_context["school"].id)


@pytest.mark.asyncio
async def test_list_configs_filters_by_type(client, api_context, session_factory):
    async with session_factory() as session:
        await GameConfigFactory.create(
            session=session,
            school_id=api_context["school"].id,
            game_type="memory_match",
            title="Memoire alphabet",
            difficulty="easy",
        )
        await GameConfigFactory.create(
            session=session,
            school_id=api_context["school"].id,
            game_type="sorting",
            title="Tri des categories",
            difficulty="medium",
        )
        await session.commit()

    response = await client.get(
        "/games/configs",
        headers=auth_header(api_context["teacher"]["token"]),
        params={"game_type": "memory_match"},
    )

    assert response.status_code == 200, response.text
    payload = response.json()["data"]
    assert len(payload) == 1
    assert payload[0]["game_type"] == "memory_match"
    assert payload[0]["title"] == "Memoire alphabet"


@pytest.mark.asyncio
async def test_complete_game_awards_stars(client, api_context, session_factory):
    async with session_factory() as session:
        config = await GameConfigFactory.create(
            session=session,
            school_id=api_context["school"].id,
            game_type="memory_match",
            reward_stars=14,
            reward_xp=21,
            is_active=True,
        )
        await session.commit()

    response = await client.post(
        f"/games/configs/{config.id}/complete",
        headers=auth_header(api_context["student"]["token"]),
        json={"score": 100, "time_seconds": 54},
    )

    assert response.status_code == 200, response.text
    payload = response.json()["data"]
    assert payload["reward"]["stars"] == 14
    assert payload["reward"]["xp"] == 21
    assert payload["reward"]["student_id"] == str(api_context["student"]["user"].id)

    async with session_factory() as session:
        events = (
            (
                await session.execute(
                    select(RewardEvent).where(
                        RewardEvent.student_id == api_context["student"]["user"].id
                    )
                )
            )
            .scalars()
            .all()
        )

    assert len(events) == 1
    assert events[0].event_type == "game_won"
    assert events[0].source_type == "game"
    assert events[0].source_id == config.id


@pytest.mark.asyncio
async def test_game_config_requires_teacher_permission(client, api_context):
    response = await client.post(
        "/games/configs",
        headers=auth_header(api_context["student"]["token"]),
        json=_memory_match_payload(),
    )

    assert response.status_code == 403, response.text
