"""Integration tests for the DifficultyAdapter service."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.lms.difficulty_adapter import DifficultyAdapter


def _make_attempt(score: float, max_score: float, difficulty: str) -> MagicMock:
    attempt = MagicMock()
    attempt.score = score
    attempt.max_score = max_score
    attempt.quiz = MagicMock()
    attempt.quiz.difficulty = difficulty
    return attempt


@pytest.mark.asyncio
async def test_new_student_defaults_to_easy():
    """New students with fewer than 2 attempts get EASY."""
    adapter = DifficultyAdapter(db=AsyncMock())
    adapter._get_recent_attempts = AsyncMock(return_value=[])

    result = await adapter.get_recommended_difficulty(uuid.uuid4(), "math")
    assert result == "EASY"


@pytest.mark.asyncio
async def test_new_student_one_attempt_defaults_to_easy():
    adapter = DifficultyAdapter(db=AsyncMock())
    adapter._get_recent_attempts = AsyncMock(
        return_value=[_make_attempt(80, 100, "EASY")]
    )

    result = await adapter.get_recommended_difficulty(uuid.uuid4(), "math")
    assert result == "EASY"


@pytest.mark.asyncio
async def test_promotion_after_two_high_scores():
    """Two consecutive scores >= 80% at EASY → promote to MEDIUM."""
    db = AsyncMock()
    db.flush = AsyncMock()
    db.add = MagicMock()

    adapter = DifficultyAdapter(db=db)
    adapter._get_recent_attempts = AsyncMock(
        return_value=[
            _make_attempt(85, 100, "EASY"),
            _make_attempt(90, 100, "EASY"),
        ]
    )

    with patch.object(adapter, "_log_adaptation", new=AsyncMock()) as mock_log:
        result = await adapter.get_recommended_difficulty(uuid.uuid4(), "math")
        mock_log.assert_called_once()
        call_kwargs = mock_log.call_args.kwargs
        assert call_kwargs["reason"] == "promoted_high_scores"
        assert call_kwargs["new"] == "MEDIUM"

    assert result == "MEDIUM"


@pytest.mark.asyncio
async def test_promotion_at_medium_goes_to_hard():
    """Two consecutive high scores at MEDIUM → HARD."""
    db = AsyncMock()
    adapter = DifficultyAdapter(db=db)
    adapter._get_recent_attempts = AsyncMock(
        return_value=[
            _make_attempt(95, 100, "MEDIUM"),
            _make_attempt(85, 100, "MEDIUM"),
        ]
    )
    with patch.object(adapter, "_log_adaptation", new=AsyncMock()):
        result = await adapter.get_recommended_difficulty(uuid.uuid4(), "math")
    assert result == "HARD"


@pytest.mark.asyncio
async def test_already_at_hard_stays_hard_on_promotion():
    """Cannot promote above HARD."""
    db = AsyncMock()
    adapter = DifficultyAdapter(db=db)
    adapter._get_recent_attempts = AsyncMock(
        return_value=[
            _make_attempt(100, 100, "HARD"),
            _make_attempt(95, 100, "HARD"),
        ]
    )
    # No adaptation logged since level doesn't change
    with patch.object(adapter, "_log_adaptation", new=AsyncMock()) as mock_log:
        result = await adapter.get_recommended_difficulty(uuid.uuid4(), "math")
        mock_log.assert_not_called()
    assert result == "HARD"


@pytest.mark.asyncio
async def test_demotion_after_two_low_scores():
    """Two consecutive scores <= 40% at MEDIUM → EASY."""
    db = AsyncMock()
    adapter = DifficultyAdapter(db=db)
    adapter._get_recent_attempts = AsyncMock(
        return_value=[
            _make_attempt(30, 100, "MEDIUM"),
            _make_attempt(40, 100, "MEDIUM"),
        ]
    )
    with patch.object(adapter, "_log_adaptation", new=AsyncMock()) as mock_log:
        result = await adapter.get_recommended_difficulty(uuid.uuid4(), "math")
        call_kwargs = mock_log.call_args.kwargs
        assert call_kwargs["reason"] == "demoted_low_scores"
    assert result == "EASY"


@pytest.mark.asyncio
async def test_already_at_easy_stays_easy_on_demotion():
    """Cannot demote below EASY."""
    db = AsyncMock()
    adapter = DifficultyAdapter(db=db)
    adapter._get_recent_attempts = AsyncMock(
        return_value=[
            _make_attempt(10, 100, "EASY"),
            _make_attempt(20, 100, "EASY"),
        ]
    )
    with patch.object(adapter, "_log_adaptation", new=AsyncMock()) as mock_log:
        result = await adapter.get_recommended_difficulty(uuid.uuid4(), "math")
        mock_log.assert_not_called()
    assert result == "EASY"


@pytest.mark.asyncio
async def test_stable_when_mixed_scores():
    """Mixed scores keep the current difficulty."""
    db = AsyncMock()
    adapter = DifficultyAdapter(db=db)
    adapter._get_recent_attempts = AsyncMock(
        return_value=[
            _make_attempt(70, 100, "MEDIUM"),
            _make_attempt(50, 100, "MEDIUM"),
        ]
    )
    with patch.object(adapter, "_log_adaptation", new=AsyncMock()) as mock_log:
        result = await adapter.get_recommended_difficulty(uuid.uuid4(), "math")
        mock_log.assert_not_called()
    assert result == "MEDIUM"


@pytest.mark.asyncio
async def test_boundary_exactly_80_promotes():
    """Exactly 80% counts as a high score."""
    db = AsyncMock()
    adapter = DifficultyAdapter(db=db)
    adapter._get_recent_attempts = AsyncMock(
        return_value=[
            _make_attempt(80, 100, "EASY"),
            _make_attempt(80, 100, "EASY"),
        ]
    )
    with patch.object(adapter, "_log_adaptation", new=AsyncMock()):
        result = await adapter.get_recommended_difficulty(uuid.uuid4(), "math")
    assert result == "MEDIUM"


@pytest.mark.asyncio
async def test_boundary_exactly_40_demotes():
    """Exactly 40% counts as a low score."""
    db = AsyncMock()
    adapter = DifficultyAdapter(db=db)
    adapter._get_recent_attempts = AsyncMock(
        return_value=[
            _make_attempt(40, 100, "MEDIUM"),
            _make_attempt(40, 100, "MEDIUM"),
        ]
    )
    with patch.object(adapter, "_log_adaptation", new=AsyncMock()):
        result = await adapter.get_recommended_difficulty(uuid.uuid4(), "math")
    assert result == "EASY"
