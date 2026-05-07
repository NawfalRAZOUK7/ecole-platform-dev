"""Smoke tests for CalendarRepository.

Lightweight tests verifying each public method returns expected shapes.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

import pytest

from app.repositories.calendar import CalendarRepository


def _uuid(n: int) -> uuid.UUID:
    return uuid.UUID(f"30000000-0000-4000-8000-{n:012d}")


@pytest.mark.asyncio
class TestCalendarRepositorySmoke:
    """One happy-path test per public method."""

    async def test_get_event(self, db_session) -> None:
        repo = CalendarRepository(db_session)
        event = await repo.get_event(_uuid(1))
        assert event is None or hasattr(event, "id")

    async def test_create_and_save_event(self, db_session) -> None:
        repo = CalendarRepository(db_session)
        from app.models.calendar import Event

        event = Event(
            id=uuid.uuid4(),
            school_id=uuid.uuid4(),
            title="Test Event",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow(),
            event_type="meeting",
        )
        created = await repo.create_event(event)
        assert created.title == "Test Event"
        saved = await repo.save_event(created)
        assert saved.id == created.id

    async def test_list_holidays(self, db_session) -> None:
        repo = CalendarRepository(db_session)
        holidays = await repo.list_holidays(school_id=_uuid(1))
        assert isinstance(holidays, list)

    async def test_get_holiday(self, db_session) -> None:
        repo = CalendarRepository(db_session)
        holiday = await repo.get_holiday(_uuid(1))
        assert holiday is None or hasattr(holiday, "name")

    async def test_find_holiday_conflict(self, db_session) -> None:
        repo = CalendarRepository(db_session)
        conflict = await repo.find_holiday_conflict(
            school_id=_uuid(1),
            start_date=date.today(),
            end_date=date.today(),
        )
        assert conflict is None or hasattr(conflict, "name")

    async def test_get_current_academic_year(self, db_session) -> None:
        repo = CalendarRepository(db_session)
        year = await repo.get_current_academic_year(_uuid(1))
        assert year is None or hasattr(year, "start_date")

    async def test_list_school_classes(self, db_session) -> None:
        repo = CalendarRepository(db_session)
        classes = await repo.list_school_classes(_uuid(1))
        assert isinstance(classes, list)

    async def test_get_class(self, db_session) -> None:
        repo = CalendarRepository(db_session)
        klass = await repo.get_class(_uuid(1))
        assert klass is None or hasattr(klass, "code")
