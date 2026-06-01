"""Mock-based unit tests for app/repositories/school.py."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.repositories.school import SchoolRepository


def _uid():
    return uuid.uuid4()


class _FR:
    def __init__(self, v=None, many=None):
        self._v = v
        self._many = many or []

    def scalar_one_or_none(self):
        return self._v

    def scalars(self):
        return SimpleNamespace(all=lambda: self._many)

    def all(self):
        return self._many


def _db(result=None):
    r = result if result is not None else _FR()
    return SimpleNamespace(
        execute=AsyncMock(return_value=r),
        add=Mock(),
        flush=AsyncMock(),
        commit=AsyncMock(),
    )


def _repo(db):
    return SchoolRepository(db)


@pytest.mark.asyncio
async def test_create_school():
    fake = SimpleNamespace(id=_uid())
    db = _db()
    with patch("app.repositories.school.School", return_value=fake):
        result = await _repo(db).create_school({"name": "École Test"})
    assert result is fake
    db.add.assert_called_once_with(fake)


@pytest.mark.asyncio
async def test_get_school_exists():
    obj = SimpleNamespace(id=_uid(), deleted_at=None)
    db = _db(_FR(v=obj))
    result = await _repo(db).get_school(_uid())
    assert result is obj


@pytest.mark.asyncio
async def test_get_school_include_deleted():
    obj = SimpleNamespace(id=_uid())
    db = _db(_FR(v=obj))
    result = await _repo(db).get_school(_uid(), include_deleted=True)
    assert result is obj


@pytest.mark.asyncio
async def test_get_school_not_found():
    db = _db(_FR(v=None))
    result = await _repo(db).get_school(_uid())
    assert result is None


@pytest.mark.asyncio
async def test_list_schools_no_cursor_no_filters():
    now = datetime.now(timezone.utc)
    items = [SimpleNamespace(id=_uid(), created_at=now) for _ in range(3)]
    # simulate no has_more (limit 10, only 3 items)
    db = _db(_FR(many=items))
    result, next_cursor, has_more = await _repo(db).list_schools(None, 10)
    assert result == items
    assert has_more is False
    assert next_cursor is None


@pytest.mark.asyncio
async def test_list_schools_with_cursor_and_filters():
    now = datetime.now(timezone.utc)
    # Return page_size+1 items so has_more=True
    items = [SimpleNamespace(id=_uid(), created_at=now) for _ in range(6)]
    db = _db(_FR(many=items))
    from app.core.response import encode_cursor
    cursor = encode_cursor(_uid(), now.isoformat())
    result, next_cursor, has_more = await _repo(db).list_schools(
        cursor, 5, filters={"status": "active", "city": "Casablanca"}
    )
    assert has_more is True
    assert len(result) == 5
    assert next_cursor is not None


@pytest.mark.asyncio
async def test_list_schools_include_deleted_filter():
    now = datetime.now(timezone.utc)
    items = [SimpleNamespace(id=_uid(), created_at=now)]
    db = _db(_FR(many=items))
    result, _, _ = await _repo(db).list_schools(None, 10, filters={"include_deleted": True})
    assert result == items


@pytest.mark.asyncio
async def test_update_school_found():
    school_id = _uid()
    obj = SimpleNamespace(id=school_id, name="Old", deleted_at=None)
    db = _db(_FR(v=obj))
    result = await _repo(db).update_school(school_id, {"name": "New"})
    assert result.name == "New"


@pytest.mark.asyncio
async def test_update_school_not_found():
    db = _db(_FR(v=None))
    result = await _repo(db).update_school(_uid(), {"name": "New"})
    assert result is None


@pytest.mark.asyncio
async def test_soft_delete_school_found():
    obj = SimpleNamespace(id=_uid(), deleted_at=None)
    obj.soft_delete = Mock()
    db = _db(_FR(v=obj))
    result = await _repo(db).soft_delete_school(obj.id)
    obj.soft_delete.assert_called_once()
    assert result is obj


@pytest.mark.asyncio
async def test_soft_delete_school_not_found():
    db = _db(_FR(v=None))
    result = await _repo(db).soft_delete_school(_uid())
    assert result is None
