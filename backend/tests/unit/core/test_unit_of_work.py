"""Unit tests for app/core/unit_of_work.py — full branch coverage."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.core.unit_of_work import UnitOfWork


def _mock_session() -> AsyncMock:
    session = AsyncMock()
    session.info = {}
    return session


# ---------------------------------------------------------------------------
# Basic properties
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_session_property():
    session = _mock_session()
    async with UnitOfWork(session) as uow:
        assert uow.session is session


# ---------------------------------------------------------------------------
# commit / rollback
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_commit_calls_session_commit():
    session = _mock_session()
    async with UnitOfWork(session) as uow:
        await uow.commit()
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_rollback_calls_session_rollback():
    session = _mock_session()
    async with UnitOfWork(session) as uow:
        await uow.rollback()
    session.rollback.assert_awaited_once()


# ---------------------------------------------------------------------------
# __aenter__ / __aexit__ — depth tracking
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_single_enter_sets_depth_one():
    session = _mock_session()
    async with UnitOfWork(session):
        assert session.info.get("_uow_depth") == 1


@pytest.mark.asyncio
async def test_nested_uow_increments_depth():
    session = _mock_session()
    async with UnitOfWork(session):
        assert session.info.get("_uow_depth") == 1
        async with UnitOfWork(session):
            assert session.info.get("_uow_depth") == 2
        # After inner exits, depth goes back to 1
        assert session.info.get("_uow_depth") == 1
    # After outer exits, depth key removed
    assert "_uow_depth" not in session.info


@pytest.mark.asyncio
async def test_exit_without_exception_no_rollback():
    session = _mock_session()
    async with UnitOfWork(session):
        pass
    session.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_exit_on_exception_triggers_rollback():
    session = _mock_session()
    with pytest.raises(ValueError):
        async with UnitOfWork(session):
            raise ValueError("test error")
    session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_exit_after_commit_no_rollback_on_exception():
    """If committed before exception, rollback is skipped (committed flag set)."""
    session = _mock_session()
    with pytest.raises(ValueError):
        async with UnitOfWork(session) as uow:
            await uow.commit()
            raise ValueError("after commit")
    session.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_depth_key_removed_after_single_exit():
    session = _mock_session()
    async with UnitOfWork(session):
        pass
    assert "_uow_depth" not in session.info


@pytest.mark.asyncio
async def test_nested_exit_decrements_not_removes():
    session = _mock_session()
    async with UnitOfWork(session):
        inner = UnitOfWork(session)
        await inner.__aenter__()
        await inner.__aexit__(None, None, None)
        # Depth should be 1 (not removed) since outer is still active
        assert session.info.get("_uow_depth") == 1
