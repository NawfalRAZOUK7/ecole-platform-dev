"""Rewards factories."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import factory

from app.models.rewards import RewardBadge, RewardEvent, StudentReward
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
    longest_streak = 0
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
    event_metadata = factory.LazyFunction(dict)
    created_at = factory.LazyFunction(_utc_now)


class RewardBadgeFactory(AsyncSQLAlchemyFactory):
    """Factory for badge definitions."""

    class Meta:
        model = RewardBadge

    id = factory.LazyFunction(uuid.uuid4)
    code = factory.Sequence(lambda n: f"badge_{n}")
    title_fr = factory.Sequence(lambda n: f"Badge {n}")
    title_ar = factory.Sequence(lambda n: f"شارة {n}")
    title_en = factory.Sequence(lambda n: f"Badge {n}")
    description_fr = "Badge de test"
    description_ar = "شارة اختبار"
    description_en = "Test badge"
    icon = "star"
    criteria_type = "stars_total"
    criteria_value = 100
    display_order = 0
    is_active = True
    created_at = factory.LazyFunction(_utc_now)


__all__ = [
    "RewardBadgeFactory",
    "RewardEventFactory",
    "StudentRewardFactory",
]
