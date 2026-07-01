"""Phase 15 event reminder scheduling and dispatch."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.unit_of_work import UnitOfWork
from app.models.calendar import (
    Event,
    EventReminder,
    EventReminderChannel,
    EventVisibility,
)
from app.models.com import DeliveryChannel, NotificationCategory, NotificationPriority
from app.repositories.communication_calendar import CalendarRepository
from app.services.communication.calendar import CalendarService
from app.services.communication.notification_hub import NotificationHubService

logger = logging.getLogger(__name__)

CASABLANCA_TZ = ZoneInfo("Africa/Casablanca")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_dispatch_timestamp(value: datetime) -> datetime:
    """Collapse microsecond noise so reminder channels for the same offset coalesce."""
    return value.astimezone(timezone.utc).replace(microsecond=0)


def _default_offsets() -> list[int]:
    offsets: list[int] = []
    for raw in settings.calendar_reminder_default_offsets.split(","):
        raw = raw.strip()
        if not raw:
            continue
        try:
            value = int(raw)
        except ValueError:
            continue
        if value > 0:
            offsets.append(value)
    return offsets or [1440, 60]


class ReminderService:
    """Schedules and sends event reminders through the notification hub."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = CalendarRepository(db)
        self.calendar = CalendarService(db)
        self.notifications = NotificationHubService(db)

    async def sync_event_reminders(
        self,
        *,
        event: Event,
        reminder_offsets_minutes: list[int] | None = None,
    ) -> int:
        offsets = sorted(
            {
                offset
                for offset in (reminder_offsets_minutes or _default_offsets())
                if offset > 0
            },
            reverse=True,
        )
        if not offsets:
            return 0

        now = _utc_now()
        horizon = now + timedelta(days=settings.calendar_reminder_horizon_days)
        occurrences = self.calendar._expand_occurrences(
            event, from_dt=now, to_dt=horizon
        )
        reminders: list[EventReminder] = []

        for occurrence in occurrences:
            for offset in offsets:
                remind_at = occurrence.start_at - timedelta(minutes=offset)
                if remind_at <= now:
                    continue
                for channel in (
                    EventReminderChannel.IN_APP.value,
                    EventReminderChannel.PUSH.value,
                ):
                    reminders.append(
                        EventReminder(
                            event_id=event.id,
                            remind_at=remind_at,
                            channel=channel,
                            sent=False,
                            occurrence_start_at=occurrence.start_at,
                        )
                    )

        async with UnitOfWork(self.db) as uow:
            repo = CalendarRepository(uow.session)
            await repo.delete_unsent_reminders_for_event(event.id)
            if reminders:
                await repo.create_event_reminders(reminders)
            await uow.commit()
            return len(reminders)

    async def clear_event_reminders(self, *, event_id: uuid.UUID) -> None:
        async with UnitOfWork(self.db) as uow:
            repo = CalendarRepository(uow.session)
            await repo.delete_unsent_reminders_for_event(event_id)
            await uow.commit()

    async def send_due_reminders(self, *, now: datetime | None = None) -> int:
        current = now or _utc_now()
        due_rows = await self.repo.list_due_reminders(now=current)
        if not due_rows:
            return 0

        grouped: dict[tuple[uuid.UUID, str, str], dict[str, object]] = {}
        for reminder, event in due_rows:
            normalized_occurrence_start_at = _normalize_dispatch_timestamp(
                reminder.occurrence_start_at or event.start_at
            )
            normalized_remind_at = _normalize_dispatch_timestamp(reminder.remind_at)
            occurrence_key = normalized_occurrence_start_at.isoformat()
            group_key = (
                event.id,
                normalized_remind_at.isoformat(),
                occurrence_key,
            )
            grouped.setdefault(
                group_key,
                {
                    "event": event,
                    "channels": set(),
                    "reminder_ids": [],
                    "occurrence_start_at": normalized_occurrence_start_at,
                    "remind_at": normalized_remind_at,
                },
            )
            grouped[group_key]["channels"].add(reminder.channel)
            grouped[group_key]["reminder_ids"].append(reminder.id)
        notifications_sent = 0
        async with UnitOfWork(self.db) as uow:
            repo = CalendarRepository(uow.session)
            notifications = NotificationHubService(uow.session)
            for payload in grouped.values():
                event = payload["event"]
                channels = sorted(payload["channels"])
                reminder_ids = payload["reminder_ids"]
                occurrence_start_at = payload["occurrence_start_at"]
                remind_at = payload["remind_at"]

                recipient_ids = await self._resolve_recipient_ids(event)
                if not recipient_ids:
                    await repo.mark_reminders_sent(reminder_ids, sent_at=current)
                    continue

                disabled_ids = await repo.list_disabled_reminder_user_ids(
                    school_id=event.school_id,
                    event_type=event.type,
                    user_ids=recipient_ids,
                )
                active_recipient_ids = sorted(recipient_ids - disabled_ids)
                if not active_recipient_ids:
                    await repo.mark_reminders_sent(reminder_ids, sent_at=current)
                    continue

                for recipient_id in active_recipient_ids:
                    await notifications.create_single_notification(
                        school_id=event.school_id,
                        user_id=recipient_id,
                        title=self._notification_title(event),
                        body=self._notification_body(event, occurrence_start_at),
                        category=self._notification_category(event.type),
                        priority=NotificationPriority.HIGH.value,
                        action_url=f"/events/{event.id}",
                        action_payload={
                            "event_id": str(event.id),
                            "occurrence_start_at": occurrence_start_at.isoformat(),
                        },
                        event_ref=f"calendar.reminder:{event.id}",
                        preferred_channels=self._preferred_delivery_channels(channels),
                        idempotency_key=(
                            f"calendar-reminder:{event.id}:{remind_at.isoformat()}:{recipient_id}"
                        ),
                        silent_push=False,
                    )
                    notifications_sent += 1

                await repo.mark_reminders_sent(reminder_ids, sent_at=current)

            await uow.commit()
            return notifications_sent

    async def _resolve_recipient_ids(self, event: Event) -> set[uuid.UUID]:
        if event.visibility == EventVisibility.SCHOOL.value:
            return await self.repo.list_school_user_ids(event.school_id)
        if event.visibility == EventVisibility.CLASS.value and event.class_id:
            return await self.repo.list_class_recipient_ids(
                school_id=event.school_id,
                class_id=event.class_id,
            )
        if event.visibility == EventVisibility.ROLE.value:
            return await self.repo.list_role_user_ids(
                school_id=event.school_id,
                role_codes=event.role_codes or [],
            )
        return set()

    def _preferred_delivery_channels(self, channels: list[str]) -> list[str]:
        resolved: list[str] = []
        for channel in channels:
            if channel == EventReminderChannel.IN_APP.value:
                resolved.append(DeliveryChannel.IN_APP.value)
            if channel == EventReminderChannel.PUSH.value:
                resolved.append(DeliveryChannel.PUSH.value)
        return resolved or [DeliveryChannel.IN_APP.value]

    def _notification_title(self, event: Event) -> str:
        return (
            event.title_fr or event.title_en or event.title_ar or "Rappel d'evenement"
        )

    def _notification_body(self, event: Event, occurrence_start_at: datetime) -> str:
        local_dt = occurrence_start_at.astimezone(CASABLANCA_TZ)
        pieces = [
            local_dt.strftime("%d/%m/%Y %H:%M"),
        ]
        if event.location:
            pieces.append(event.location)
        return " • ".join(pieces)

    def _notification_category(self, event_type: str) -> str:
        if event_type == "exam":
            return NotificationCategory.ACADEMIC.value
        if event_type == "holiday":
            return NotificationCategory.SYSTEM.value
        return NotificationCategory.ANNOUNCEMENT.value
