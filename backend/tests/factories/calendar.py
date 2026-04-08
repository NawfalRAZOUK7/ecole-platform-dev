"""Calendar factories."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import factory

from app.models.calendar import (
    Event,
    EventRSVP,
    EventRsvpStatus,
    EventType,
    EventVisibility,
)
from tests.factories.base import AsyncSQLAlchemyFactory
from tests.factories.iam import UserFactory
from tests.factories.school import SchoolFactory


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EventFactory(AsyncSQLAlchemyFactory):
    """Factory for calendar events."""

    class Meta:
        model = Event
        exclude = ("school", "creator")

    id = factory.LazyFunction(uuid.uuid4)
    school = factory.SubFactory(SchoolFactory)
    creator = factory.SubFactory(UserFactory, school=factory.SelfAttribute("..school"))
    school_id = factory.LazyAttribute(lambda o: o.school.id)
    title_fr = "Réunion parents"
    title_ar = "اجتماع الآباء"
    title_en = "Parents meeting"
    description = "Réunion de suivi pédagogique"
    type = EventType.MEETING.value
    visibility = EventVisibility.SCHOOL.value
    start_at = factory.LazyFunction(lambda: _utc_now() + timedelta(days=7))
    end_at = factory.LazyAttribute(lambda o: o.start_at + timedelta(hours=2))
    location = "Casablanca"
    latitude = None
    longitude = None
    capacity = None
    rsvp_deadline = None
    recurrence_rule = None
    created_by = factory.LazyAttribute(lambda o: o.creator.id)
    class_id = None
    role_codes = None
    is_all_day = False


class EventRSVPFactory(AsyncSQLAlchemyFactory):
    """Factory for event RSVPs."""

    class Meta:
        model = EventRSVP
        exclude = ("event", "user")

    id = factory.LazyFunction(uuid.uuid4)
    event = factory.SubFactory(EventFactory)
    user = factory.SubFactory(UserFactory)
    event_id = factory.LazyAttribute(lambda o: o.event.id)
    user_id = factory.LazyAttribute(lambda o: o.user.id)
    status = EventRsvpStatus.ATTENDING.value
    responded_at = factory.LazyFunction(_utc_now)
