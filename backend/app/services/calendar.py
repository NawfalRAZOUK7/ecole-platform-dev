"""Phase 15 calendar service."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.core.permissions import ADM, DIR, PAR, STD, TCH
from app.core.unit_of_work import UnitOfWork
from app.domain.events.calendar import EventCreated, EventUpdated
from app.models.calendar import (
    Event,
    EventReminderPreference,
    EventType,
    EventVisibility,
    MoroccanHoliday,
)
from app.repositories.calendar import CalendarRepository
from app.schemas.calendar import (
    EventCreateRequest,
    EventDetailResponse,
    EventListItem,
    EventRSVPItem,
    EventUpdateRequest,
    HolidayCreateRequest,
    HolidayUpdateRequest,
)
from app.services.event_dispatcher import EventDispatcher

ICAL_ACTION = "calendar.ical"
SYSTEM_NAMESPACE = uuid.UUID("9e09e90d-12fb-4e70-9f8a-a2d8d77d1d31")
DEFAULT_EVENT_TYPES = tuple(item.value for item in EventType)
EVENT_TYPE_COLORS = {
    EventType.HOLIDAY.value: "#E8F5E9",
    EventType.EXAM.value: "#FFEBEE",
    EventType.MEETING.value: "#E3F2FD",
    EventType.EXCURSION.value: "#FFF3E0",
    EventType.CEREMONY.value: "#F3E5F5",
    EventType.CUSTOM.value: "#F5F5F5",
}
logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _day_window(from_date: date, to_date: date) -> tuple[datetime, datetime]:
    start_dt = datetime.combine(from_date, time.min, tzinfo=timezone.utc)
    end_dt = datetime.combine(to_date + timedelta(days=1), time.min, tzinfo=timezone.utc)
    return start_dt, end_dt


def _dt_to_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


@dataclass(slots=True)
class CalendarActor:
    user_id: uuid.UUID
    role: str
    school_id: uuid.UUID


@dataclass(slots=True)
class EventOccurrence:
    base_id: uuid.UUID
    instance_id: str
    source: str
    start_at: datetime
    end_at: datetime
    is_recurring: bool


class CalendarService:
    """Visibility filtering, recurrence expansion, and iCal generation."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = CalendarRepository(db)
        self._dispatcher = EventDispatcher(self.db)

    async def list_events(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
        from_date: date,
        to_date: date,
        event_type: str | None,
        class_id: uuid.UUID | None,
    ) -> list[dict[str, Any]]:
        actor = CalendarActor(user_id=user_id, role=role, school_id=school_id)
        class_scope = await self._get_class_scope(actor)
        if class_id and role in {STD, PAR} and class_id not in class_scope:
            raise NotFoundError("Class not found", error_code="ERR-CAL-404")

        from_dt, to_dt = _day_window(from_date, to_date)
        events = await self.repo.list_candidate_events(
            school_id=school_id,
            from_dt=from_dt,
            to_dt=to_dt,
            event_type=event_type,
            class_id=class_id,
        )
        rsvp_counts = await self.repo.list_rsvp_counts([event.id for event in events])
        my_rsvps = await self.repo.list_user_rsvps(
            user_id=user_id,
            event_ids=[event.id for event in events],
        )

        items: list[dict[str, Any]] = []
        for event in events:
            if not self._can_view_event(event, actor, class_scope):
                continue
            for occurrence in self._expand_occurrences(event, from_dt=from_dt, to_dt=to_dt):
                items.append(
                    self._serialize_event(
                        event,
                        actor=actor,
                        occurrence=occurrence,
                        counts=rsvp_counts.get(event.id, {}),
                        my_rsvp=my_rsvps.get(event.id),
                    )
                )

        if event_type in (None, EventType.HOLIDAY.value):
            holidays = await self.repo.list_holidays(from_date=from_date, to_date=to_date)
            items.extend(self._serialize_holiday(holiday, actor=actor) for holiday in holidays)

        if event_type in (None, EventType.CUSTOM.value):
            periods, academic_years = await self.repo.list_period_boundaries(
                school_id=school_id,
                from_date=from_date,
                to_date=to_date,
            )
            items.extend(self._serialize_period_start(period) for period in periods if from_date <= period.date_start <= to_date)
            items.extend(self._serialize_period_end(period) for period in periods if from_date <= period.date_end <= to_date)
            items.extend(self._serialize_academic_year_start(year) for year in academic_years if from_date <= year.date_start <= to_date)
            items.extend(self._serialize_academic_year_end(year) for year in academic_years if from_date <= year.date_end <= to_date)

        items.sort(key=lambda item: (item["start_at"], item["instance_id"]))
        return items

    async def get_event_detail(
        self,
        *,
        event_id: uuid.UUID,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
    ) -> dict[str, Any]:
        actor = CalendarActor(user_id=user_id, role=role, school_id=school_id)
        event = await self.repo.get_event(event_id)
        if event is not None:
            accessible = await self.get_accessible_event(
                event_id=event_id,
                school_id=school_id,
                user_id=user_id,
                role=role,
            )
            counts = (await self.repo.list_rsvp_counts([accessible.id])).get(accessible.id, {})
            my_rsvp = (
                await self.repo.list_user_rsvps(
                    user_id=user_id,
                    event_ids=[accessible.id],
                )
            ).get(accessible.id)
            item = self._serialize_event(
                accessible,
                actor=actor,
                occurrence=EventOccurrence(
                    base_id=accessible.id,
                    instance_id=str(accessible.id),
                    source="event",
                    start_at=accessible.start_at,
                    end_at=accessible.end_at,
                    is_recurring=accessible.recurrence_rule is not None,
                ),
                counts=counts,
                my_rsvp=my_rsvp,
            )
            if role in {ADM, DIR} or accessible.created_by == user_id:
                item["rsvps"] = await self._serialize_rsvps(
                    event_id=accessible.id,
                    school_id=school_id,
                )
            return EventDetailResponse(**item).model_dump()

        holiday = await self.repo.get_holiday(event_id)
        if holiday is None:
            raise NotFoundError("Event not found", error_code="ERR-CAL-404")
        return EventDetailResponse(**self._serialize_holiday(holiday, actor=actor)).model_dump()

    async def list_holidays(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
        academic_year_id: uuid.UUID | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[dict[str, Any]]:
        actor = CalendarActor(user_id=user_id, role=role, school_id=school_id)
        window_start, window_end = await self._resolve_holiday_window(
            school_id=school_id,
            academic_year_id=academic_year_id,
            from_date=from_date,
            to_date=to_date,
        )
        holidays = await self.repo.list_holidays(
            from_date=window_start,
            to_date=window_end,
        )
        return [self._serialize_holiday(item, actor=actor) for item in holidays]

    async def create_holiday(
        self,
        *,
        body: HolidayCreateRequest,
    ) -> MoroccanHoliday:
        conflict = await self.repo.find_holiday_conflict(
            code=body.code,
            holiday_date=body.holiday_date,
        )
        if conflict is not None:
            raise ValidationError(
                "Holiday already exists for this date",
                error_code="ERR-CAL-422",
            )
        async with UnitOfWork(self.db) as uow:
            repo = CalendarRepository(uow.session)
            holiday = MoroccanHoliday(
                code=body.code,
                holiday_date=body.holiday_date,
                name_fr=body.name_fr,
                name_ar=body.name_ar,
                name_en=body.name_en,
                description=body.description,
                is_all_day=body.is_all_day,
            )
            created = await repo.create_holiday(holiday)
            await uow.commit()
            return created

    async def update_holiday(
        self,
        *,
        holiday_id: uuid.UUID,
        body: HolidayUpdateRequest,
    ) -> MoroccanHoliday:
        holiday = await self.repo.get_holiday(holiday_id)
        if holiday is None:
            raise NotFoundError("Holiday not found", error_code="ERR-CAL-404")

        payload = body.model_dump(exclude_unset=True)
        next_code = payload.get("code", holiday.code)
        next_date = payload.get("holiday_date", holiday.holiday_date)
        conflict = await self.repo.find_holiday_conflict(
            code=next_code,
            holiday_date=next_date,
            exclude_id=holiday_id,
        )
        if conflict is not None:
            raise ValidationError(
                "Holiday already exists for this date",
                error_code="ERR-CAL-422",
            )
        async with UnitOfWork(self.db) as uow:
            repo = CalendarRepository(uow.session)
            holiday = await repo.get_holiday(holiday_id)
            if holiday is None:
                raise NotFoundError("Holiday not found", error_code="ERR-CAL-404")
            for field, value in payload.items():
                setattr(holiday, field, value)
            saved = await repo.save_holiday(holiday)
            await uow.commit()
            return saved

    async def delete_holiday(
        self,
        *,
        holiday_id: uuid.UUID,
    ) -> MoroccanHoliday:
        async with UnitOfWork(self.db) as uow:
            repo = CalendarRepository(uow.session)
            holiday = await repo.get_holiday(holiday_id)
            if holiday is None:
                raise NotFoundError("Holiday not found", error_code="ERR-CAL-404")
            await repo.delete_holiday(holiday)
            await uow.commit()
            return holiday

    async def create_event(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
        body: EventCreateRequest,
    ) -> Event:
        actor = CalendarActor(user_id=user_id, role=role, school_id=school_id)
        await self._validate_create_request(actor, body)

        async with UnitOfWork(self.db) as uow:
            repo = CalendarRepository(uow.session)
            event = Event(
                school_id=school_id,
                title_fr=body.title_fr,
                title_ar=body.title_ar,
                title_en=body.title_en,
                description=body.description,
                type=body.type,
                visibility=body.visibility,
                start_at=body.start_at,
                end_at=body.end_at,
                location=body.location,
                latitude=body.latitude,
                longitude=body.longitude,
                capacity=body.capacity,
                rsvp_deadline=body.rsvp_deadline,
                recurrence_rule=body.recurrence_rule.model_dump(mode="json")
                if body.recurrence_rule
                else None,
                created_by=user_id,
                class_id=body.class_id,
                role_codes=body.role_codes,
                is_all_day=body.is_all_day,
            )
            created = await repo.create_event(event)
            await uow.commit()

        try:
            await self._dispatcher.dispatch(
                EventCreated(
                    school_id=school_id,
                    actor_id=user_id,
                    event_id=created.id,
                    title=created.title_en or created.title_fr or created.title_ar or "",
                    start_at=created.start_at.isoformat(),
                    class_id=created.class_id,
                )
            )
        except Exception:
            logger.exception("Failed to dispatch EventCreated for %s", created.id)

        return created

    async def update_event(
        self,
        *,
        event_id: uuid.UUID,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
        body: EventUpdateRequest,
    ) -> Event:
        actor = CalendarActor(user_id=user_id, role=role, school_id=school_id)
        event = await self.get_accessible_event(
            event_id=event_id,
            school_id=school_id,
            user_id=user_id,
            role=role,
        )
        self._verify_edit_permission(event, actor)

        payload = body.model_dump(exclude_unset=True, mode="json")
        next_visibility = payload.get("visibility", event.visibility)
        next_class_id = payload.get("class_id", event.class_id)
        next_role_codes = payload.get("role_codes", event.role_codes)

        if next_visibility == EventVisibility.CLASS.value and next_class_id is None:
            raise ValidationError("class_id is required for class visibility", error_code="ERR-CAL-422")
        if next_visibility == EventVisibility.ROLE.value and not next_role_codes:
            raise ValidationError("role_codes are required for role visibility", error_code="ERR-CAL-422")

        async with UnitOfWork(self.db) as uow:
            repo = CalendarRepository(uow.session)
            event = await repo.get_event(event_id)
            if event is None or event.deleted_at is not None or event.school_id != school_id:
                raise NotFoundError("Event not found", error_code="ERR-CAL-404")
            for field, value in payload.items():
                if field == "recurrence_rule" and value is not None:
                    setattr(event, field, value)
                else:
                    setattr(event, field, value)

            if event.end_at < event.start_at:
                raise ValidationError("end_at must be after start_at", error_code="ERR-CAL-422")
            if event.rsvp_deadline and event.rsvp_deadline > event.start_at:
                raise ValidationError("rsvp_deadline must be before start_at", error_code="ERR-CAL-422")
            if role == TCH and event.visibility != EventVisibility.CLASS.value:
                raise AuthorizationError(
                    "Teachers can only create class events",
                    error_code="ERR-CAL-403",
                )
            if event.class_id:
                class_obj = await repo.get_class(event.class_id)
                if class_obj is None or class_obj.school_id != school_id:
                    raise NotFoundError("Class not found", error_code="ERR-CAL-404")
                if role == TCH:
                    teacher_classes = await repo.list_teacher_class_ids(
                        teacher_id=user_id,
                        school_id=school_id,
                    )
                    if event.class_id not in teacher_classes:
                        raise NotFoundError("Class not found", error_code="ERR-CAL-404")

            saved = await repo.save_event(event)
            await uow.commit()

        try:
            await self._dispatcher.dispatch(
                EventUpdated(
                    school_id=school_id,
                    actor_id=user_id,
                    event_id=saved.id,
                    title=saved.title_en or saved.title_fr or saved.title_ar or "",
                    changes=payload,
                )
            )
        except Exception:
            logger.exception("Failed to dispatch EventUpdated for %s", saved.id)

        return saved

    async def delete_event(
        self,
        *,
        event_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> Event:
        async with UnitOfWork(self.db) as uow:
            repo = CalendarRepository(uow.session)
            event = await repo.get_event(event_id)
            if event is None or event.school_id != school_id or event.deleted_at is not None:
                raise NotFoundError("Event not found", error_code="ERR-CAL-404")
            event.deleted_at = _utc_now()
            saved = await repo.save_event(event)
            await uow.commit()
            return saved

    async def get_accessible_event(
        self,
        *,
        event_id: uuid.UUID,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
    ) -> Event:
        event = await self.repo.get_event(event_id)
        if event is None or event.deleted_at is not None or event.school_id != school_id:
            raise NotFoundError("Event not found", error_code="ERR-CAL-404")
        actor = CalendarActor(user_id=user_id, role=role, school_id=school_id)
        class_scope = await self._get_class_scope(actor)
        if not self._can_view_event(event, actor, class_scope):
            raise NotFoundError("Event not found", error_code="ERR-CAL-404")
        return event

    async def get_visible_classes(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
    ) -> list[dict[str, str]]:
        actor = CalendarActor(user_id=user_id, role=role, school_id=school_id)
        if role in {ADM, DIR}:
            classes = await self.repo.list_school_classes(school_id)
        elif role == TCH:
            classes = await self.repo.list_teacher_classes(
                teacher_id=user_id,
                school_id=school_id,
            )
        else:
            class_ids = await self._get_class_scope(actor)
            classes = [
                item
                for item in await self.repo.list_school_classes(school_id)
                if item.id in class_ids
            ]
        return [
            {"id": str(item.id), "code": item.code, "name": item.name}
            for item in classes
        ]

    async def list_reminder_preferences(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[dict[str, Any]]:
        if self.db.info.get("_uow_depth"):
            repo = CalendarRepository(self.db)
            await self._ensure_default_reminder_preferences_with_repo(
                repo=repo,
                school_id=school_id,
                user_id=user_id,
            )
            preferences = await repo.list_reminder_preferences(
                school_id=school_id,
                user_id=user_id,
            )
        else:
            async with UnitOfWork(self.db) as uow:
                repo = CalendarRepository(uow.session)
                await self._ensure_default_reminder_preferences_with_repo(
                    repo=repo,
                    school_id=school_id,
                    user_id=user_id,
                )
                preferences = await repo.list_reminder_preferences(
                    school_id=school_id,
                    user_id=user_id,
                )
                await uow.commit()
        return [
            {
                "event_type": item.event_type,
                "enabled": item.enabled,
            }
            for item in preferences
        ]

    async def update_reminder_preferences(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        preferences: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        async with UnitOfWork(self.db) as uow:
            repo = CalendarRepository(uow.session)
            await self._ensure_default_reminder_preferences_with_repo(
                repo=repo,
                school_id=school_id,
                user_id=user_id,
            )
            for item in preferences:
                pref = await repo.find_reminder_preference(
                    school_id=school_id,
                    user_id=user_id,
                    event_type=item["event_type"],
                )
                if pref is None:
                    pref = EventReminderPreference(
                        school_id=school_id,
                        user_id=user_id,
                        event_type=item["event_type"],
                        enabled=item["enabled"],
                    )
                else:
                    pref.enabled = item["enabled"]
                await repo.save_reminder_preference(pref)
            updated = await repo.list_reminder_preferences(
                school_id=school_id,
                user_id=user_id,
            )
            await uow.commit()

        return [
            {
                "event_type": item.event_type,
                "enabled": item.enabled,
            }
            for item in updated
        ]

    def build_ical_token(
        self,
        *,
        user_id: uuid.UUID,
        school_id: uuid.UUID,
        role: str,
        expires_at: datetime | None = None,
    ) -> str:
        payload = {
            "sub": str(user_id),
            "school_id": str(school_id),
            "role": role,
            "action": ICAL_ACTION,
            "exp": expires_at
            or (_utc_now() + timedelta(days=settings.calendar_ical_ttl_days)),
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    def parse_ical_token(self, token: str) -> CalendarActor:
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
            )
        except JWTError as exc:
            raise NotFoundError("Calendar feed not found", error_code="ERR-CAL-404") from exc
        if payload.get("action") != ICAL_ACTION:
            raise NotFoundError("Calendar feed not found", error_code="ERR-CAL-404")
        return CalendarActor(
            user_id=uuid.UUID(payload["sub"]),
            role=payload["role"],
            school_id=uuid.UUID(payload["school_id"]),
        )

    async def build_ical_url(
        self,
        *,
        user_id: uuid.UUID,
        school_id: uuid.UUID,
        role: str,
        base_url: str,
        lang: str = "fr",
    ) -> str:
        token = self.build_ical_token(
            user_id=user_id,
            school_id=school_id,
            role=role,
        )
        root = base_url.rstrip("/")
        return f"{root}/api/v1/calendar/ical?token={token}&lang={lang}"

    async def render_ical_feed(
        self,
        *,
        actor: CalendarActor,
        lang: str = "fr",
    ) -> str:
        start_date = date.today() - timedelta(days=30)
        end_date = date.today() + timedelta(days=365)
        items = await self.list_events(
            school_id=actor.school_id,
            user_id=actor.user_id,
            role=actor.role,
            from_date=start_date,
            to_date=end_date,
            event_type=None,
            class_id=None,
        )
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Ecole Platform//Calendar Feed//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "X-WR-CALNAME:École Platform",
        ]
        stamp = _utc_now().strftime("%Y%m%dT%H%M%SZ")
        for item in items:
            summary = self._localized_title(item, lang)
            description = (item.get("description") or "").replace("\n", "\\n")
            lines.extend(
                [
                    "BEGIN:VEVENT",
                    f"UID:{item['instance_id']}@ecole-platform.ma",
                    f"DTSTAMP:{stamp}",
                    self._ical_dt("DTSTART", item["start_at"], all_day=item["is_all_day"]),
                    self._ical_dt("DTEND", item["end_at"], all_day=item["is_all_day"]),
                    f"SUMMARY:{summary}",
                    f"DESCRIPTION:{description}",
                    f"LOCATION:{item.get('location') or ''}",
                    f"URL:{settings.web_app_base_url.rstrip('/')}/events/{item['id']}",
                    "END:VEVENT",
                ]
            )
        lines.append("END:VCALENDAR")
        return "\r\n".join(lines) + "\r\n"

    def _ical_dt(self, label: str, value: str, *, all_day: bool) -> str:
        parsed = datetime.fromisoformat(value)
        if all_day:
            return f"{label};VALUE=DATE:{parsed.date().strftime('%Y%m%d')}"
        return f"{label}:{parsed.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"

    def _localized_title(self, item: dict[str, Any], lang: str) -> str:
        if lang == "ar" and item.get("title_ar"):
            return item["title_ar"]
        if lang == "en" and item.get("title_en"):
            return item["title_en"]
        return item["title_fr"]

    async def _validate_create_request(
        self,
        actor: CalendarActor,
        body: EventCreateRequest,
    ) -> None:
        if actor.role == TCH and body.visibility != EventVisibility.CLASS.value:
            raise AuthorizationError(
                "Teachers can only create class events",
                error_code="ERR-CAL-403",
            )
        if body.class_id:
            class_obj = await self.repo.get_class(body.class_id)
            if class_obj is None or class_obj.school_id != actor.school_id:
                raise NotFoundError("Class not found", error_code="ERR-CAL-404")
            if actor.role == TCH:
                teacher_classes = await self.repo.list_teacher_class_ids(
                    teacher_id=actor.user_id,
                    school_id=actor.school_id,
                )
                if body.class_id not in teacher_classes:
                    raise NotFoundError("Class not found", error_code="ERR-CAL-404")

    def _verify_edit_permission(self, event: Event, actor: CalendarActor) -> None:
        if actor.role in {ADM, DIR}:
            return
        if event.created_by != actor.user_id:
            raise AuthorizationError(
                "Only the event creator can update this event",
                error_code="ERR-CAL-403",
            )

    async def _get_class_scope(self, actor: CalendarActor) -> set[uuid.UUID]:
        if actor.role == STD:
            return await self.repo.list_student_class_ids(
                student_id=actor.user_id,
                school_id=actor.school_id,
            )
        if actor.role == PAR:
            return await self.repo.list_parent_class_ids(
                parent_id=actor.user_id,
                school_id=actor.school_id,
            )
        if actor.role == TCH:
            return await self.repo.list_teacher_class_ids(
                teacher_id=actor.user_id,
                school_id=actor.school_id,
            )
        return set()

    async def _resolve_holiday_window(
        self,
        *,
        school_id: uuid.UUID,
        academic_year_id: uuid.UUID | None,
        from_date: date | None,
        to_date: date | None,
    ) -> tuple[date, date]:
        if academic_year_id is not None:
            academic_year = await self.repo.get_academic_year(
                school_id=school_id,
                academic_year_id=academic_year_id,
            )
            if academic_year is None:
                raise NotFoundError("Academic year not found", error_code="ERR-CAL-404")
            return academic_year.date_start, academic_year.date_end
        if (from_date is None) != (to_date is None):
            raise ValidationError(
                "from_date and to_date must be provided together",
                error_code="ERR-CAL-422",
            )
        if from_date is not None and to_date is not None:
            return from_date, to_date
        current_year = await self.repo.get_current_academic_year(
            school_id=school_id,
            on_date=date.today(),
        )
        if current_year is not None:
            return current_year.date_start, current_year.date_end
        today = date.today()
        return date(today.year, 1, 1), date(today.year, 12, 31)

    def _can_view_event(
        self,
        event: Event,
        actor: CalendarActor,
        class_scope: set[uuid.UUID],
    ) -> bool:
        if actor.role in {ADM, DIR, TCH}:
            return True
        if event.visibility == EventVisibility.SCHOOL.value:
            return True
        if event.visibility == EventVisibility.CLASS.value:
            return bool(event.class_id and event.class_id in class_scope)
        return actor.role in set(event.role_codes or [])

    def _expand_occurrences(
        self,
        event: Event,
        *,
        from_dt: datetime,
        to_dt: datetime,
    ) -> list[EventOccurrence]:
        if event.recurrence_rule is None:
            if event.end_at < from_dt or event.start_at > to_dt:
                return []
            return [
                EventOccurrence(
                    base_id=event.id,
                    instance_id=str(event.id),
                    source="event",
                    start_at=event.start_at,
                    end_at=event.end_at,
                    is_recurring=False,
                )
            ]

        frequency = (event.recurrence_rule or {}).get("frequency")
        interval = int((event.recurrence_rule or {}).get("interval") or 1)
        until_raw = (event.recurrence_rule or {}).get("until")
        until_dt = datetime.fromisoformat(until_raw) if until_raw else to_dt
        horizon = min(until_dt, to_dt)
        duration = event.end_at - event.start_at
        occurrences: list[EventOccurrence] = []
        current_start = event.start_at

        while current_start <= horizon:
            current_end = current_start + duration
            if current_end >= from_dt and current_start <= to_dt:
                occurrences.append(
                    EventOccurrence(
                        base_id=event.id,
                        instance_id=f"{event.id}:{current_start.isoformat()}",
                        source="event",
                        start_at=current_start,
                        end_at=current_end,
                        is_recurring=True,
                    )
                )
            if frequency == "weekly":
                current_start = current_start + timedelta(weeks=interval)
            elif frequency == "annual":
                try:
                    current_start = current_start.replace(
                        year=current_start.year + interval
                    )
                except ValueError:
                    current_start = current_start.replace(
                        month=3,
                        day=1,
                        year=current_start.year + interval,
                    )
            else:
                break
        return occurrences

    def _event_color(self, event_type: str) -> str:
        return EVENT_TYPE_COLORS.get(event_type, EVENT_TYPE_COLORS[EventType.CUSTOM.value])

    def _serialize_event(
        self,
        event: Event,
        *,
        actor: CalendarActor,
        occurrence: EventOccurrence,
        counts: dict[str, int],
        my_rsvp: str | None,
    ) -> dict[str, Any]:
        can_edit = actor.role in {ADM, DIR} or event.created_by == actor.user_id
        can_delete = actor.role in {ADM, DIR}
        can_rsvp = actor.role in {PAR, STD, TCH} and event.type != EventType.HOLIDAY.value

        return EventListItem(
            id=str(event.id),
            instance_id=occurrence.instance_id,
            source=occurrence.source,
            title_fr=event.title_fr,
            title_ar=event.title_ar,
            title_en=event.title_en,
            description=event.description,
            type=event.type,
            visibility=event.visibility,
            start_at=_dt_to_iso(occurrence.start_at),
            end_at=_dt_to_iso(occurrence.end_at),
            location=event.location,
            latitude=event.latitude,
            longitude=event.longitude,
            class_id=str(event.class_id) if event.class_id else None,
            role_codes=list(event.role_codes or []),
            capacity=event.capacity,
            rsvp_deadline=event.rsvp_deadline.isoformat() if event.rsvp_deadline else None,
            attendee_count=counts.get("attending", 0),
            maybe_count=counts.get("maybe", 0),
            declined_count=counts.get("declined", 0),
            my_rsvp=my_rsvp,
            is_all_day=event.is_all_day,
            is_recurring=occurrence.is_recurring,
            recurrence_rule=event.recurrence_rule,
            color=self._event_color(event.type),
            can_edit=can_edit,
            can_delete=can_delete,
            can_rsvp=can_rsvp,
            is_holiday=False,
        ).model_dump()

    def _serialize_holiday(
        self,
        holiday: MoroccanHoliday,
        *,
        actor: CalendarActor,
    ) -> dict[str, Any]:
        start_dt = datetime.combine(holiday.holiday_date, time.min, tzinfo=timezone.utc)
        end_dt = start_dt + timedelta(days=1)
        can_manage = actor.role in {ADM, DIR}
        return EventListItem(
            id=str(holiday.id),
            instance_id=str(holiday.id),
            source="holiday",
            title_fr=holiday.name_fr,
            title_ar=holiday.name_ar,
            title_en=holiday.name_en,
            description=holiday.description,
            type=EventType.HOLIDAY.value,
            visibility=EventVisibility.SCHOOL.value,
            start_at=_dt_to_iso(start_dt),
            end_at=_dt_to_iso(end_dt),
            location=None,
            attendee_count=0,
            maybe_count=0,
            declined_count=0,
            my_rsvp=None,
            is_all_day=holiday.is_all_day,
            is_recurring=False,
            recurrence_rule=None,
            color=self._event_color(EventType.HOLIDAY.value),
            can_edit=can_manage,
            can_delete=can_manage,
            can_rsvp=False,
            is_holiday=True,
        ).model_dump()

    def _serialize_period_start(self, period) -> dict[str, Any]:
        event_id = uuid.uuid5(SYSTEM_NAMESPACE, f"period:start:{period.id}")
        start_dt = datetime.combine(period.date_start, time.min, tzinfo=timezone.utc)
        end_dt = start_dt + timedelta(days=1)
        return EventListItem(
            id=str(event_id),
            instance_id=str(event_id),
            source="period_start",
            title_fr=f"Début de période • {period.label or 'Période'}",
            title_ar=f"بداية الفترة • {period.label or 'الفترة'}",
            title_en=f"Period starts • {period.label or 'Period'}",
            type=EventType.CUSTOM.value,
            visibility=EventVisibility.SCHOOL.value,
            start_at=_dt_to_iso(start_dt),
            end_at=_dt_to_iso(end_dt),
            attendee_count=0,
            maybe_count=0,
            declined_count=0,
            my_rsvp=None,
            is_all_day=True,
            is_recurring=False,
            color=self._event_color(EventType.CUSTOM.value),
            can_edit=False,
            can_delete=False,
            can_rsvp=False,
            is_holiday=False,
        ).model_dump()

    def _serialize_period_end(self, period) -> dict[str, Any]:
        event_id = uuid.uuid5(SYSTEM_NAMESPACE, f"period:end:{period.id}")
        start_dt = datetime.combine(period.date_end, time.min, tzinfo=timezone.utc)
        end_dt = start_dt + timedelta(days=1)
        return EventListItem(
            id=str(event_id),
            instance_id=str(event_id),
            source="period_end",
            title_fr=f"Fin de période • {period.label or 'Période'}",
            title_ar=f"نهاية الفترة • {period.label or 'الفترة'}",
            title_en=f"Period ends • {period.label or 'Period'}",
            type=EventType.CUSTOM.value,
            visibility=EventVisibility.SCHOOL.value,
            start_at=_dt_to_iso(start_dt),
            end_at=_dt_to_iso(end_dt),
            attendee_count=0,
            maybe_count=0,
            declined_count=0,
            my_rsvp=None,
            is_all_day=True,
            is_recurring=False,
            color=self._event_color(EventType.CUSTOM.value),
            can_edit=False,
            can_delete=False,
            can_rsvp=False,
            is_holiday=False,
        ).model_dump()

    def _serialize_academic_year_start(self, academic_year) -> dict[str, Any]:
        event_id = uuid.uuid5(SYSTEM_NAMESPACE, f"academic-year:start:{academic_year.id}")
        start_dt = datetime.combine(academic_year.date_start, time.min, tzinfo=timezone.utc)
        end_dt = start_dt + timedelta(days=1)
        return EventListItem(
            id=str(event_id),
            instance_id=str(event_id),
            source="academic_year_start",
            title_fr=f"Rentrée scolaire • {academic_year.label or 'Année scolaire'}",
            title_ar=f"بداية السنة الدراسية • {academic_year.label or 'السنة الدراسية'}",
            title_en=f"Academic year starts • {academic_year.label or 'Academic year'}",
            type=EventType.CUSTOM.value,
            visibility=EventVisibility.SCHOOL.value,
            start_at=_dt_to_iso(start_dt),
            end_at=_dt_to_iso(end_dt),
            attendee_count=0,
            maybe_count=0,
            declined_count=0,
            my_rsvp=None,
            is_all_day=True,
            is_recurring=False,
            color=self._event_color(EventType.CUSTOM.value),
            can_edit=False,
            can_delete=False,
            can_rsvp=False,
            is_holiday=False,
        ).model_dump()

    def _serialize_academic_year_end(self, academic_year) -> dict[str, Any]:
        event_id = uuid.uuid5(SYSTEM_NAMESPACE, f"academic-year:end:{academic_year.id}")
        start_dt = datetime.combine(academic_year.date_end, time.min, tzinfo=timezone.utc)
        end_dt = start_dt + timedelta(days=1)
        return EventListItem(
            id=str(event_id),
            instance_id=str(event_id),
            source="academic_year_end",
            title_fr=f"Fin de l'année scolaire • {academic_year.label or 'Année scolaire'}",
            title_ar=f"نهاية السنة الدراسية • {academic_year.label or 'السنة الدراسية'}",
            title_en=f"Academic year ends • {academic_year.label or 'Academic year'}",
            type=EventType.CUSTOM.value,
            visibility=EventVisibility.SCHOOL.value,
            start_at=_dt_to_iso(start_dt),
            end_at=_dt_to_iso(end_dt),
            attendee_count=0,
            maybe_count=0,
            declined_count=0,
            my_rsvp=None,
            is_all_day=True,
            is_recurring=False,
            color=self._event_color(EventType.CUSTOM.value),
            can_edit=False,
            can_delete=False,
            can_rsvp=False,
            is_holiday=False,
        ).model_dump()

    async def _serialize_rsvps(
        self,
        *,
        event_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> list[dict[str, Any]]:
        rows = await self.repo.list_event_rsvps(
            event_id=event_id,
            school_id=school_id,
        )
        return [
            EventRSVPItem(
                user_id=str(user.id),
                full_name=user.full_name,
                role=role_code or "",
                status=rsvp.status,
                responded_at=rsvp.responded_at.isoformat(),
            ).model_dump()
            for rsvp, user, role_code in rows
        ]

    async def _ensure_default_reminder_preferences(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        await self._ensure_default_reminder_preferences_with_repo(
            repo=self.repo,
            school_id=school_id,
            user_id=user_id,
        )

    async def _ensure_default_reminder_preferences_with_repo(
        self,
        *,
        repo: CalendarRepository,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        existing = await repo.list_reminder_preferences(
            school_id=school_id,
            user_id=user_id,
        )
        existing_types = {item.event_type for item in existing}
        for event_type in DEFAULT_EVENT_TYPES:
            if event_type in existing_types:
                continue
            await repo.save_reminder_preference(
                EventReminderPreference(
                    school_id=school_id,
                    user_id=user_id,
                    event_type=event_type,
                    enabled=True,
                )
            )
