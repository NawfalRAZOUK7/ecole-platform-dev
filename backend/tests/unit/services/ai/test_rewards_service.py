"""Unit tests for rewards service."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.dependencies import AuthContext
from app.core.exceptions import NotFoundError
import app.services.ai.rewards_service as rewards_module
from app.services.ai.rewards_service import RewardsService


def make_auth(role: str = "ADM") -> AuthContext:
    return AuthContext(
        user_id=uuid.uuid4(),
        role=role,
        school_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        permissions=set(),
    )


def make_reward(
    student_id: uuid.UUID,
    *,
    stars: int = 10,
    xp: int = 100,
    level: int = 1,
):
    now = datetime(2026, 3, 1, tzinfo=timezone.utc)
    return SimpleNamespace(
        id=uuid.uuid4(),
        student_id=student_id,
        school_id=uuid.uuid4(),
        stars=stars,
        xp=xp,
        level=level,
        streak_days=0,
        longest_streak=0,
        badges=[],
        last_activity_at=now,
        created_at=now,
        updated_at=now,
    )


def make_student(school_id: uuid.UUID) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        school_id=school_id,
        full_name="Test Student",
    )


class FakeUnitOfWork:
    def __init__(self, repo: AsyncMock) -> None:
        self.session = AsyncMock()
        self._repo = repo

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def commit(self) -> None:
        pass


def setup_service(monkeypatch: pytest.MonkeyPatch) -> tuple[RewardsService, AsyncMock]:
    service = RewardsService(AsyncMock())
    mock_repo = AsyncMock()
    service.repo = mock_repo

    uow = FakeUnitOfWork(mock_repo)
    uow.session = AsyncMock()

    inner_repo = AsyncMock()
    monkeypatch.setattr(rewards_module, "UnitOfWork", lambda _db: uow)
    monkeypatch.setattr(
        rewards_module, "RewardsRepository", lambda _session: inner_repo
    )

    return service, mock_repo, inner_repo


class TestRewardsServiceAward:
    @pytest.mark.asyncio
    async def test_award_accumulates_stars_and_xp(self, monkeypatch):
        service, mock_repo, inner_repo = setup_service(monkeypatch)
        student_id = uuid.uuid4()
        school_id = uuid.uuid4()

        student = make_student(school_id)
        reward = make_reward(student_id, stars=5, xp=50)

        mock_repo.get_user.return_value = student
        inner_repo.get_student_reward.return_value = reward
        inner_repo.create_reward_event.return_value = None
        inner_repo.save_student_reward.return_value = None

        result = await service.award(
            student_id=student_id,
            event_type="quiz_completion",
            stars=3,
            xp=30,
            source_type=None,
            source_id=None,
        )

        assert result["stars"] == 8
        assert result["xp"] == 80

    @pytest.mark.asyncio
    async def test_award_raises_not_found_for_missing_student(self, monkeypatch):
        service, mock_repo, _inner_repo = setup_service(monkeypatch)
        mock_repo.get_user.return_value = None

        with pytest.raises(NotFoundError):
            await service.award(
                student_id=uuid.uuid4(),
                event_type="quiz_completion",
                stars=1,
                xp=10,
                source_type=None,
                source_id=None,
            )

    @pytest.mark.asyncio
    async def test_award_zero_stars_is_valid(self, monkeypatch):
        service, mock_repo, inner_repo = setup_service(monkeypatch)
        student_id = uuid.uuid4()
        student = make_student(uuid.uuid4())
        reward = make_reward(student_id, stars=0, xp=0)

        mock_repo.get_user.return_value = student
        inner_repo.get_student_reward.return_value = reward
        inner_repo.create_reward_event.return_value = None
        inner_repo.save_student_reward.return_value = None

        result = await service.award(
            student_id=student_id,
            event_type="login",
            stars=0,
            xp=5,
            source_type=None,
            source_id=None,
        )

        assert result["stars"] == 0
        assert result["xp"] == 5


class TestRewardsServiceGetRewards:
    @pytest.mark.asyncio
    async def test_get_student_rewards_returns_existing(self, monkeypatch):
        service, mock_repo, _inner = setup_service(monkeypatch)
        student_id = uuid.uuid4()
        student = make_student(uuid.uuid4())
        reward = make_reward(student_id, stars=20, xp=200, level=2)

        mock_repo.get_user.return_value = student
        mock_repo.get_student_reward.return_value = reward

        result = await service.get_student_rewards(student_id=student_id)

        assert result["stars"] == 20
        assert result["xp"] == 200
        assert result["level"] == 2

    @pytest.mark.asyncio
    async def test_get_student_rewards_raises_for_missing_student(self, monkeypatch):
        service, mock_repo, _inner = setup_service(monkeypatch)
        mock_repo.get_user.return_value = None

        with pytest.raises(NotFoundError):
            await service.get_student_rewards(student_id=uuid.uuid4())
