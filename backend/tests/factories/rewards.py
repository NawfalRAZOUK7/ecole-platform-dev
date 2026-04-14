"""Rewards factories."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import factory

from app.models.rewards import RewardEvent, StudentReward
from tests.factories.base import AsyncSQLAlchemyFactory
from tests.factories.iam import UserFactory


def _utc_now() -> datetime:
    return datetime.now(UTC)


class StudentRewardFactory(AsyncSQLAlchemyFactory):
    """Factory for student reward aggregates."""

    class Meta:
        model = StudentReward
        exclude = ("student",)

    id = factory.LazyFunction(uuid.uuid4)
    student = factory.SubFactory(UserFactory)
    student_id = factory.LazyAttribute(lambda o: o.student.id)
    stars = 0
    xp = 0
    level = 1
    streak_days = 0
    last_activity_at = None
    badges = factory.LazyFunction(list)


class RewardEventFactory(AsyncSQLAlchemyFactory):
    """Factory for immutable reward events."""

    class Meta:
        model = RewardEvent
        exclude = ("student",)

    id = factory.LazyFunction(uuid.uuid4)
    student = factory.SubFactory(UserFactory)
    student_id = factory.LazyAttribute(lambda o: o.student.id)
    event_type = "content_completed"
    stars_earned = 10
    xp_earned = 15
    source_type = "content"
    source_id = factory.LazyFunction(uuid.uuid4)
    created_at = factory.LazyFunction(_utc_now)


__all__ = [
    "RewardEventFactory",
    "StudentRewardFactory",
]
