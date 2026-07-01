"""Smoke tests for CalendarRepository.

Lightweight tests verifying each public method returns expected shapes.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

import pytest

from app.models.calendar import Event, EventType, EventVisibility
from app.repositories.communication_calendar import CalendarRepository
from tests.factories.iam import UserFactory
from tests.factories.school import SchoolFactory


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
        school = await SchoolFactory.create(session=db_session)
        creator = await UserFactory.create(session=db_session, school=school)
        now = datetime.now(timezone.utc)

        event = Event(
            id=uuid.uuid4(),
            school_id=school.id,
            title_fr="Test Event",
            type=EventType.MEETING.value,
            visibility=EventVisibility.SCHOOL.value,
            start_at=now,
            end_at=now,
            created_by=creator.id,
        )
        created = await repo.create_event(event)
        assert created.title_fr == "Test Event"
        saved = await repo.save_event(created)
        assert saved.id == created.id

    async def test_list_holidays(self, db_session) -> None:
        repo = CalendarRepository(db_session)
        holidays = await repo.list_holidays(
            from_date=date.today(),
            to_date=date.today(),
        )
        assert isinstance(holidays, list)

    async def test_get_holiday(self, db_session) -> None:
        repo = CalendarRepository(db_session)
        holiday = await repo.get_holiday(_uuid(1))
        assert holiday is None or hasattr(holiday, "name_fr")

    async def test_find_holiday_conflict(self, db_session) -> None:
        repo = CalendarRepository(db_session)
        conflict = await repo.find_holiday_conflict(
            code="test-holiday",
            holiday_date=date.today(),
        )
        assert conflict is None or hasattr(conflict, "name_fr")

    async def test_get_current_academic_year(self, db_session) -> None:
        repo = CalendarRepository(db_session)
        year = await repo.get_current_academic_year(
            school_id=_uuid(1),
            on_date=date.today(),
        )
        assert year is None or hasattr(year, "date_start")

    async def test_list_school_classes(self, db_session) -> None:
        repo = CalendarRepository(db_session)
        classes = await repo.list_school_classes(_uuid(1))
        assert isinstance(classes, list)

    async def test_get_class(self, db_session) -> None:
        repo = CalendarRepository(db_session)
        klass = await repo.get_class(_uuid(1))
        assert klass is None or hasattr(klass, "code")
