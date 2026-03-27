"""Repository helpers for Phase 15 calendar, RSVP, and reminders."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Iterable

from sqlalchemy import and_, func, or_, select

from app.models.calendar import (
    Event,
    EventReminder,
    EventReminderPreference,
    EventRSVP,
    MoroccanHoliday,
)
from app.models.erp import AcademicYear, Class, Enrollment, Period, TeacherAssignment
from app.models.iam import Membership, ParentChildLink, User
from app.repositories.base import BaseRepository


class CalendarRepository(BaseRepository):

    async def get_event(self, event_id: uuid.UUID) -> Event | None:
        result = await self.db.execute(select(Event).where(Event.id == event_id))
        return result.scalar_one_or_none()

    async def create_event(self, event: Event) -> Event:
        self.db.add(event)
        await self.db.flush()
        return event

    async def save_event(self, event: Event) -> Event:
        self.db.add(event)
        await self.db.flush()
        return event

    async def list_candidate_events(
        self,
        *,
        school_id: uuid.UUID,
        from_dt: datetime,
        to_dt: datetime,
        event_type: str | None = None,
        class_id: uuid.UUID | None = None,
    ) -> list[Event]:
        query = select(Event).where(
            Event.school_id == school_id,
            Event.deleted_at.is_(None),
            Event.start_at <= to_dt,
            or_(
                Event.end_at >= from_dt,
                Event.recurrence_rule.is_not(None),
            ),
        )
        if event_type:
            query = query.where(Event.type == event_type)
        if class_id:
            query = query.where(
                or_(
                    Event.class_id == class_id,
                    Event.visibility == "school",
                )
            )
        query = query.order_by(Event.start_at.asc(), Event.id.asc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_holidays(
        self,
        *,
        from_date: date,
        to_date: date,
    ) -> list[MoroccanHoliday]:
        result = await self.db.execute(
            select(MoroccanHoliday)
            .where(
                MoroccanHoliday.holiday_date >= from_date,
                MoroccanHoliday.holiday_date <= to_date,
            )
            .order_by(MoroccanHoliday.holiday_date.asc())
        )
        return list(result.scalars().all())

    async def get_holiday(self, holiday_id: uuid.UUID) -> MoroccanHoliday | None:
        result = await self.db.execute(
            select(MoroccanHoliday).where(MoroccanHoliday.id == holiday_id)
        )
        return result.scalar_one_or_none()

    async def list_period_boundaries(
        self,
        *,
        school_id: uuid.UUID,
        from_date: date,
        to_date: date,
    ) -> tuple[list[Period], list[AcademicYear]]:
        periods_result = await self.db.execute(
            select(Period)
            .where(
                Period.school_id == school_id,
                or_(
                    and_(Period.date_start >= from_date, Period.date_start <= to_date),
                    and_(Period.date_end >= from_date, Period.date_end <= to_date),
                ),
            )
            .order_by(Period.date_start.asc())
        )
        academic_years_result = await self.db.execute(
            select(AcademicYear)
            .where(
                AcademicYear.school_id == school_id,
                or_(
                    and_(
                        AcademicYear.date_start >= from_date,
                        AcademicYear.date_start <= to_date,
                    ),
                    and_(
                        AcademicYear.date_end >= from_date,
                        AcademicYear.date_end <= to_date,
                    ),
                ),
            )
            .order_by(AcademicYear.date_start.asc())
        )
        return (
            list(periods_result.scalars().all()),
            list(academic_years_result.scalars().all()),
        )

    async def get_class(self, class_id: uuid.UUID) -> Class | None:
        result = await self.db.execute(select(Class).where(Class.id == class_id))
        return result.scalar_one_or_none()

    async def list_school_classes(self, school_id: uuid.UUID) -> list[Class]:
        result = await self.db.execute(
            select(Class)
            .where(Class.school_id == school_id)
            .order_by(Class.code.asc(), Class.name.asc())
        )
        return list(result.scalars().all())

    async def list_teacher_classes(
        self,
        *,
        teacher_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> list[Class]:
        result = await self.db.execute(
            select(Class)
            .join(TeacherAssignment, TeacherAssignment.class_id == Class.id)
            .where(
                Class.school_id == school_id,
                TeacherAssignment.school_id == school_id,
                TeacherAssignment.teacher_id == teacher_id,
            )
            .order_by(Class.code.asc(), Class.name.asc())
        )
        return list(result.scalars().all())

    async def list_student_class_ids(
        self,
        *,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> set[uuid.UUID]:
        result = await self.db.execute(
            select(Enrollment.class_id).where(
                Enrollment.school_id == school_id,
                Enrollment.student_id == student_id,
                Enrollment.status == "active",
            )
        )
        return set(result.scalars().all())

    async def list_parent_class_ids(
        self,
        *,
        parent_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> set[uuid.UUID]:
        result = await self.db.execute(
            select(Enrollment.class_id)
            .join(
                ParentChildLink,
                ParentChildLink.child_user_id == Enrollment.student_id,
            )
            .where(
                Enrollment.school_id == school_id,
                Enrollment.status == "active",
                ParentChildLink.school_id == school_id,
                ParentChildLink.parent_user_id == parent_id,
                ParentChildLink.status == "active",
            )
        )
        return set(result.scalars().all())

    async def list_teacher_class_ids(
        self,
        *,
        teacher_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> set[uuid.UUID]:
        result = await self.db.execute(
            select(TeacherAssignment.class_id).where(
                TeacherAssignment.school_id == school_id,
                TeacherAssignment.teacher_id == teacher_id,
            )
        )
        return set(result.scalars().all())

    async def list_rsvp_counts(
        self,
        event_ids: Iterable[uuid.UUID],
    ) -> dict[uuid.UUID, dict[str, int]]:
        event_ids = list(event_ids)
        if not event_ids:
            return {}
        result = await self.db.execute(
            select(
                EventRSVP.event_id,
                EventRSVP.status,
                func.count(EventRSVP.id),
            )
            .where(EventRSVP.event_id.in_(event_ids))
            .group_by(EventRSVP.event_id, EventRSVP.status)
        )
        counts: dict[uuid.UUID, dict[str, int]] = {}
        for event_id, status, count in result.all():
            counts.setdefault(event_id, {})[status] = int(count or 0)
        return counts

    async def list_user_rsvps(
        self,
        *,
        user_id: uuid.UUID,
        event_ids: Iterable[uuid.UUID],
    ) -> dict[uuid.UUID, str]:
        event_ids = list(event_ids)
        if not event_ids:
            return {}
        result = await self.db.execute(
            select(EventRSVP.event_id, EventRSVP.status).where(
                EventRSVP.user_id == user_id,
                EventRSVP.event_id.in_(event_ids),
            )
        )
        return {event_id: status for event_id, status in result.all()}

    async def get_user_rsvp(
        self,
        *,
        event_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> EventRSVP | None:
        result = await self.db.execute(
            select(EventRSVP).where(
                EventRSVP.event_id == event_id,
                EventRSVP.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def save_rsvp(self, rsvp: EventRSVP) -> EventRSVP:
        self.db.add(rsvp)
        await self.db.flush()
        return rsvp

    async def list_event_rsvps(
        self,
        *,
        event_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> list[tuple[EventRSVP, User, str | None]]:
        result = await self.db.execute(
            select(EventRSVP, User, Membership.role_code)
            .join(User, User.id == EventRSVP.user_id)
            .outerjoin(
                Membership,
                and_(
                    Membership.user_id == User.id,
                    Membership.school_id == school_id,
                    Membership.status == "active",
                ),
            )
            .where(EventRSVP.event_id == event_id)
            .order_by(EventRSVP.responded_at.desc())
        )
        return list(result.all())

    async def count_attending(
        self,
        *,
        event_id: uuid.UUID,
    ) -> int:
        result = await self.db.execute(
            select(func.count(EventRSVP.id)).where(
                EventRSVP.event_id == event_id,
                EventRSVP.status == "attending",
            )
        )
        return int(result.scalar_one() or 0)

    async def list_school_user_ids(self, school_id: uuid.UUID) -> set[uuid.UUID]:
        result = await self.db.execute(
            select(User.id)
            .join(Membership, Membership.user_id == User.id)
            .where(
                User.school_id == school_id,
                User.status == "active",
                Membership.school_id == school_id,
                Membership.status == "active",
            )
        )
        return set(result.scalars().all())

    async def list_role_user_ids(
        self,
        *,
        school_id: uuid.UUID,
        role_codes: Iterable[str],
    ) -> set[uuid.UUID]:
        role_codes = list(role_codes)
        if not role_codes:
            return set()
        result = await self.db.execute(
            select(Membership.user_id).where(
                Membership.school_id == school_id,
                Membership.status == "active",
                Membership.role_code.in_(role_codes),
            )
        )
        return set(result.scalars().all())

    async def list_class_recipient_ids(
        self,
        *,
        school_id: uuid.UUID,
        class_id: uuid.UUID,
    ) -> set[uuid.UUID]:
        student_result = await self.db.execute(
            select(Enrollment.student_id).where(
                Enrollment.school_id == school_id,
                Enrollment.class_id == class_id,
                Enrollment.status == "active",
            )
        )
        student_ids = set(student_result.scalars().all())

        parent_ids: set[uuid.UUID] = set()
        if student_ids:
            parent_result = await self.db.execute(
                select(ParentChildLink.parent_user_id).where(
                    ParentChildLink.school_id == school_id,
                    ParentChildLink.child_user_id.in_(student_ids),
                    ParentChildLink.status == "active",
                )
            )
            parent_ids = set(parent_result.scalars().all())

        teacher_result = await self.db.execute(
            select(TeacherAssignment.teacher_id).where(
                TeacherAssignment.school_id == school_id,
                TeacherAssignment.class_id == class_id,
            )
        )
        teacher_ids = set(teacher_result.scalars().all())
        return student_ids | parent_ids | teacher_ids

    async def list_disabled_reminder_user_ids(
        self,
        *,
        school_id: uuid.UUID,
        event_type: str,
        user_ids: Iterable[uuid.UUID],
    ) -> set[uuid.UUID]:
        user_ids = list(user_ids)
        if not user_ids:
            return set()
        result = await self.db.execute(
            select(EventReminderPreference.user_id).where(
                EventReminderPreference.school_id == school_id,
                EventReminderPreference.event_type == event_type,
                EventReminderPreference.user_id.in_(user_ids),
                EventReminderPreference.enabled.is_(False),
            )
        )
        return set(result.scalars().all())

    async def list_reminder_preferences(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[EventReminderPreference]:
        result = await self.db.execute(
            select(EventReminderPreference)
            .where(
                EventReminderPreference.school_id == school_id,
                EventReminderPreference.user_id == user_id,
            )
            .order_by(EventReminderPreference.event_type.asc())
        )
        return list(result.scalars().all())

    async def find_reminder_preference(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        event_type: str,
    ) -> EventReminderPreference | None:
        result = await self.db.execute(
            select(EventReminderPreference).where(
                EventReminderPreference.school_id == school_id,
                EventReminderPreference.user_id == user_id,
                EventReminderPreference.event_type == event_type,
            )
        )
        return result.scalar_one_or_none()

    async def save_reminder_preference(
        self,
        preference: EventReminderPreference,
    ) -> EventReminderPreference:
        self.db.add(preference)
        await self.db.flush()
        return preference

    async def delete_unsent_reminders_for_event(self, event_id: uuid.UUID) -> None:
        reminders = await self.db.execute(
            select(EventReminder).where(
                EventReminder.event_id == event_id,
                EventReminder.sent.is_(False),
            )
        )
        for reminder in reminders.scalars().all():
            await self.db.delete(reminder)
        await self.db.flush()

    async def create_event_reminders(
        self,
        reminders: Iterable[EventReminder],
    ) -> None:
        for reminder in reminders:
            self.db.add(reminder)
        await self.db.flush()

    async def list_due_reminders(
        self,
        *,
        now: datetime,
    ) -> list[tuple[EventReminder, Event]]:
        result = await self.db.execute(
            select(EventReminder, Event)
            .join(Event, Event.id == EventReminder.event_id)
            .where(
                EventReminder.sent.is_(False),
                EventReminder.remind_at <= now,
                Event.deleted_at.is_(None),
            )
            .order_by(EventReminder.remind_at.asc())
        )
        return list(result.all())

    async def mark_reminders_sent(
        self,
        reminder_ids: Iterable[uuid.UUID],
        *,
        sent_at: datetime,
    ) -> None:
        reminder_ids = list(reminder_ids)
        if not reminder_ids:
            return
        result = await self.db.execute(
            select(EventReminder).where(EventReminder.id.in_(reminder_ids))
        )
        for reminder in result.scalars().all():
            reminder.sent = True
            reminder.sent_at = sent_at
        await self.db.flush()
