"""Integration tests for the rewards API."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

import app.services.rewards_service as rewards_service_module
from app.models.rewards import RewardEvent, StudentReward
from tests.factories.rewards import StudentRewardFactory
from tests.integration.api.helpers import auth_header


def _freeze_rewards_now(monkeypatch: pytest.MonkeyPatch, when: datetime) -> None:
    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            if tz is None:
                return when.replace(tzinfo=None)
            return when.astimezone(tz)

    monkeypatch.setattr(rewards_service_module, "datetime", FrozenDateTime)


@pytest.mark.asyncio
async def test_award_stars_creates_event_and_updates_total(
    client,
    api_context,
    session_factory,
):
    response = await client.post(
        "/rewards/award",
        headers=auth_header(api_context["admin"]["token"]),
        json={
            "student_id": str(api_context["student"]["user"].id),
            "event_type": "content_completed",
            "stars": 15,
            "xp": 40,
            "source_type": "content",
            "source_id": str(uuid.uuid4()),
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()["data"]
    assert payload["stars"] == 15
    assert payload["xp"] == 40
    assert payload["level"] == 1

    async with session_factory() as session:
        reward = (
            (
                await session.execute(
                    select(StudentReward).where(
                        StudentReward.student_id == api_context["student"]["user"].id
                    )
                )
            )
            .scalars()
            .one()
        )
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

    assert reward.stars == 15
    assert reward.xp == 40
    assert len(events) == 1
    assert events[0].event_type == "content_completed"
    assert events[0].stars_earned == 15


@pytest.mark.asyncio
async def test_level_up_on_xp_threshold(client, api_context):
    response = await client.post(
        "/rewards/award",
        headers=auth_header(api_context["admin"]["token"]),
        json={
            "student_id": str(api_context["student"]["user"].id),
            "event_type": "game_won",
            "stars": 0,
            "xp": 100,
            "source_type": "game",
            "source_id": str(uuid.uuid4()),
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()["data"]
    assert payload["xp"] == 100
    assert payload["level"] == 2
    assert payload["level_progress"] == 0.0


@pytest.mark.asyncio
async def test_streak_increments_on_consecutive_days(
    client,
    api_context,
    monkeypatch,
):
    day_one = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)
    day_two = day_one + timedelta(days=1)

    _freeze_rewards_now(monkeypatch, day_one)
    first = await client.post(
        "/rewards/award",
        headers=auth_header(api_context["admin"]["token"]),
        json={
            "student_id": str(api_context["student"]["user"].id),
            "event_type": "daily_login",
            "stars": 1,
            "xp": 1,
            "source_type": "login",
        },
    )
    assert first.status_code == 200, first.text
    assert first.json()["data"]["streak_days"] == 1

    _freeze_rewards_now(monkeypatch, day_two)
    second = await client.post(
        "/rewards/award",
        headers=auth_header(api_context["admin"]["token"]),
        json={
            "student_id": str(api_context["student"]["user"].id),
            "event_type": "daily_login",
            "stars": 1,
            "xp": 1,
            "source_type": "login",
        },
    )

    assert second.status_code == 200, second.text
    assert second.json()["data"]["streak_days"] == 2


@pytest.mark.asyncio
async def test_streak_resets_after_gap(
    client,
    api_context,
    monkeypatch,
):
    day_one = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)
    day_two = day_one + timedelta(days=1)
    day_five = day_one + timedelta(days=4)

    for current_day in (day_one, day_two):
        _freeze_rewards_now(monkeypatch, current_day)
        response = await client.post(
            "/rewards/award",
            headers=auth_header(api_context["admin"]["token"]),
            json={
                "student_id": str(api_context["student"]["user"].id),
                "event_type": "daily_login",
                "stars": 1,
                "xp": 1,
                "source_type": "login",
            },
        )
        assert response.status_code == 200, response.text

    _freeze_rewards_now(monkeypatch, day_five)
    response = await client.post(
        "/rewards/award",
        headers=auth_header(api_context["admin"]["token"]),
        json={
            "student_id": str(api_context["student"]["user"].id),
            "event_type": "daily_login",
            "stars": 1,
            "xp": 1,
            "source_type": "login",
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["data"]["streak_days"] == 1


@pytest.mark.asyncio
async def test_get_my_rewards_returns_student_data(client, api_context):
    response = await client.get(
        "/rewards/me",
        headers=auth_header(api_context["student"]["token"]),
    )

    assert response.status_code == 200, response.text
    payload = response.json()["data"]
    assert payload["student_id"] == str(api_context["student"]["user"].id)
    assert payload["stars"] == 0
    assert payload["level"] == 1


@pytest.mark.asyncio
async def test_leaderboard_returns_ordered_by_stars(
    client,
    api_context,
    session_factory,
):
    async with session_factory() as session:
        await StudentRewardFactory.create(
            session=session,
            student=api_context["student"]["user"],
            stars=40,
            xp=120,
            level=2,
        )
        await StudentRewardFactory.create(
            session=session,
            student=api_context["peer_student"]["user"],
            stars=95,
            xp=310,
            level=3,
        )
        await StudentRewardFactory.create(
            session=session,
            student=api_context["peer_student_two"]["user"],
            stars=60,
            xp=150,
            level=2,
        )
        await session.commit()

    response = await client.get(
        f"/rewards/leaderboard/{api_context['class'].id}",
        headers=auth_header(api_context["admin"]["token"]),
    )

    assert response.status_code == 200, response.text
    payload = response.json()["data"]
    assert [entry["student_id"] for entry in payload] == [
        str(api_context["peer_student"]["user"].id),
        str(api_context["peer_student_two"]["user"].id),
        str(api_context["student"]["user"].id),
    ]
    assert [entry["rank"] for entry in payload] == [1, 2, 3]


@pytest.mark.asyncio
async def test_student_can_award_self(client, api_context):
    response = await client.post(
        "/rewards/award",
        headers=auth_header(api_context["student"]["token"]),
        json={
            "student_id": str(api_context["student"]["user"].id),
            "event_type": "daily_login",
            "stars": 2,
            "xp": 5,
            "source_type": "login",
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()["data"]
    assert payload["stars"] == 2
    assert payload["xp"] == 5


@pytest.mark.asyncio
async def test_student_cannot_award_other_student(client, api_context):
    response = await client.post(
        "/rewards/award",
        headers=auth_header(api_context["student"]["token"]),
        json={
            "student_id": str(api_context["peer_student"]["user"].id),
            "event_type": "content_completed",
            "stars": 10,
            "xp": 15,
            "source_type": "content",
            "source_id": str(uuid.uuid4()),
        },
    )

    assert response.status_code == 404, response.text
