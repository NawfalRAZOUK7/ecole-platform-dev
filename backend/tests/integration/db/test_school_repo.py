"""Integration tests for SchoolRepository."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import pytest

from app.models.school import SchoolStatus
from app.repositories.school import SchoolRepository


def _uuid(n: int) -> UUID:
    return UUID(f"00000000-0000-4000-8000-{n:012d}")


@pytest.mark.asyncio
async def test_create_and_get_school(db_session):
    repo = SchoolRepository(db_session)

    created = await repo.create_school(
        {
            "id": _uuid(1),
            "name": "Ecole Repo",
            "code": "repo-school-1",
            "city": "Casablanca",
            "email": "repo1@ecole.ma",
            "settings": {"timezone": "Africa/Casablanca"},
        }
    )

    fetched = await repo.get_school(created.id)

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.code == "repo-school-1"
    assert fetched.deleted_at is None


@pytest.mark.asyncio
async def test_list_schools_applies_filters_and_cursor_pagination(db_session):
    repo = SchoolRepository(db_session)

    oldest = await repo.create_school(
        {
            "id": _uuid(11),
            "name": "Ecole Oldest",
            "code": "repo-school-11",
            "city": "Rabat",
            "status": SchoolStatus.TRIAL.value,
            "settings": {"timezone": "Africa/Casablanca"},
        }
    )
    middle = await repo.create_school(
        {
            "id": _uuid(12),
            "name": "Ecole Middle",
            "code": "repo-school-12",
            "city": "Casablanca",
            "status": SchoolStatus.ACTIVE.value,
            "settings": {"timezone": "Africa/Casablanca"},
        }
    )
    newest = await repo.create_school(
        {
            "id": _uuid(13),
            "name": "Ecole Newest",
            "code": "repo-school-13",
            "city": "Casablanca",
            "status": SchoolStatus.ACTIVE.value,
            "settings": {"timezone": "Africa/Casablanca"},
        }
    )

    oldest.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    middle.created_at = datetime(2025, 1, 2, tzinfo=timezone.utc)
    newest.created_at = datetime(2025, 1, 3, tzinfo=timezone.utc)
    await db_session.flush()

    first_page, cursor, has_more = await repo.list_schools(
        cursor=None,
        limit=1,
        filters={"status": SchoolStatus.ACTIVE.value, "city": "Casablanca"},
    )

    assert [school.id for school in first_page] == [newest.id]
    assert cursor is not None
    assert has_more is True

    second_page, next_cursor, second_has_more = await repo.list_schools(
        cursor=cursor,
        limit=1,
        filters={"status": SchoolStatus.ACTIVE.value, "city": "Casablanca"},
    )

    assert [school.id for school in second_page] == [middle.id]
    assert next_cursor is None
    assert second_has_more is False


@pytest.mark.asyncio
async def test_update_school_returns_updated_instance(db_session):
    repo = SchoolRepository(db_session)
    school = await repo.create_school(
        {
            "id": _uuid(21),
            "name": "Ecole Update",
            "code": "repo-school-21",
            "city": "Casablanca",
            "settings": {"timezone": "Africa/Casablanca"},
        }
    )

    updated = await repo.update_school(
        school.id,
        {
            "status": SchoolStatus.SUSPENDED.value,
            "city": "Marrakech",
            "email": "updated@ecole.ma",
        },
    )

    assert updated is not None
    assert updated.status == SchoolStatus.SUSPENDED.value
    assert updated.city == "Marrakech"
    assert updated.email == "updated@ecole.ma"


@pytest.mark.asyncio
async def test_soft_delete_hides_school_from_default_reads(db_session):
    repo = SchoolRepository(db_session)
    school = await repo.create_school(
        {
            "id": _uuid(31),
            "name": "Ecole Delete",
            "code": "repo-school-31",
            "city": "Casablanca",
            "settings": {"timezone": "Africa/Casablanca"},
        }
    )

    deleted = await repo.soft_delete_school(school.id)

    assert deleted is not None
    assert deleted.deleted_at is not None
    assert await repo.get_school(school.id) is None

    included = await repo.get_school(school.id, include_deleted=True)
    assert included is not None
    assert included.is_deleted is True


@pytest.mark.asyncio
async def test_list_schools_include_deleted_flag_controls_soft_deleted_rows(db_session):
    repo = SchoolRepository(db_session)
    active_school = await repo.create_school(
        {
            "id": _uuid(41),
            "name": "Ecole Active",
            "code": "repo-school-41",
            "city": "Casablanca",
            "settings": {"timezone": "Africa/Casablanca"},
        }
    )
    deleted_school = await repo.create_school(
        {
            "id": _uuid(42),
            "name": "Ecole Archived",
            "code": "repo-school-42",
            "city": "Casablanca",
            "settings": {"timezone": "Africa/Casablanca"},
        }
    )
    await repo.soft_delete_school(deleted_school.id)

    visible, _, _ = await repo.list_schools(cursor=None, limit=10, filters={})
    with_deleted, _, _ = await repo.list_schools(
        cursor=None,
        limit=10,
        filters={"include_deleted": True},
    )

    visible_ids = {school.id for school in visible}
    with_deleted_ids = {school.id for school in with_deleted}

    assert active_school.id in visible_ids
    assert deleted_school.id not in visible_ids
    assert {active_school.id, deleted_school.id}.issubset(with_deleted_ids)
