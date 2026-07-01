"""Phase 15 RSVP service."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError, ConflictError
from app.core.permissions import ADM, DIR
from app.core.unit_of_work import UnitOfWork
from app.models.calendar import EventRsvpStatus, EventRSVP
from app.repositories.communication_calendar import CalendarRepository
from app.services.communication.calendar import CalendarService
from app.services.communication.realtime import publish_event


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RSVPService:
    """Owns RSVP validation, persistence, and attendee list access."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = CalendarRepository(db)
        self.calendar = CalendarService(db)

    async def get_own_rsvp(
        self,
        *,
        event_id: uuid.UUID,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
    ) -> dict[str, Any]:
        event = await self.calendar.get_accessible_event(
            event_id=event_id,
            school_id=school_id,
            user_id=user_id,
            role=role,
        )
        rsvp = await self.repo.get_user_rsvp(event_id=event.id, user_id=user_id)
        return {
            "event_id": str(event.id),
            "status": rsvp.status if rsvp else None,
            "responded_at": rsvp.responded_at.isoformat() if rsvp else None,
        }

    async def respond(
        self,
        *,
        event_id: uuid.UUID,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
        status: str,
    ) -> dict[str, Any]:
        event = await self.calendar.get_accessible_event(
            event_id=event_id,
            school_id=school_id,
            user_id=user_id,
            role=role,
        )
        now = _utc_now()

        if event.rsvp_deadline and now > event.rsvp_deadline:
            raise ConflictError(
                "RSVP deadline has passed",
                error_code="ERR-CAL-409",
            )

        existing = await self.repo.get_user_rsvp(event_id=event.id, user_id=user_id)
        if (
            status == EventRsvpStatus.ATTENDING.value
            and event.capacity is not None
            and (existing is None or existing.status != EventRsvpStatus.ATTENDING.value)
        ):
            attending_count = await self.repo.count_attending(event_id=event.id)
            if attending_count >= event.capacity:
                raise ConflictError(
                    "Event capacity has been reached",
                    error_code="ERR-CAL-409",
                )

        if existing is None:
            existing = EventRSVP(
                event_id=event.id,
                user_id=user_id,
                status=status,
                responded_at=now,
            )
        else:
            existing.status = status
            existing.responded_at = now

        async with UnitOfWork(self.db) as uow:
            repo = CalendarRepository(uow.session)
            await repo.save_rsvp(existing)
            counts = (await repo.list_rsvp_counts([event.id])).get(event.id, {})
            await uow.commit()

        payload = {
            "event_id": str(event.id),
            "status": existing.status,
            "responded_at": existing.responded_at.isoformat(),
            "attendee_count": counts.get(EventRsvpStatus.ATTENDING.value, 0),
            "maybe_count": counts.get(EventRsvpStatus.MAYBE.value, 0),
            "declined_count": counts.get(EventRsvpStatus.DECLINED.value, 0),
        }

        await self._publish_rsvp_update(
            event_id=event.id,
            actor_id=user_id,
            creator_id=event.created_by,
            payload=payload,
        )
        return payload

    async def list_rsvps(
        self,
        *,
        event_id: uuid.UUID,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
    ) -> dict[str, Any]:
        event = await self.calendar.get_accessible_event(
            event_id=event_id,
            school_id=school_id,
            user_id=user_id,
            role=role,
        )
        if role not in {ADM, DIR} and event.created_by != user_id:
            raise AuthorizationError(
                "Only administrators, directors, or the event creator can view RSVPs",
                error_code="ERR-CAL-403",
            )

        rows = await self.repo.list_event_rsvps(event_id=event.id, school_id=school_id)
        counts = (await self.repo.list_rsvp_counts([event.id])).get(event.id, {})
        return {
            "event_id": str(event.id),
            "counts": {
                "attending": counts.get(EventRsvpStatus.ATTENDING.value, 0),
                "maybe": counts.get(EventRsvpStatus.MAYBE.value, 0),
                "declined": counts.get(EventRsvpStatus.DECLINED.value, 0),
            },
            "items": [
                {
                    "user_id": str(user.id),
                    "full_name": user.full_name,
                    "role": role_code or "",
                    "status": rsvp.status,
                    "responded_at": rsvp.responded_at.isoformat(),
                }
                for rsvp, user, role_code in rows
            ],
        }

    async def _publish_rsvp_update(
        self,
        *,
        event_id: uuid.UUID,
        actor_id: uuid.UUID,
        creator_id: uuid.UUID,
        payload: dict[str, Any],
    ) -> None:
        await publish_event(actor_id, "event_rsvp_updated", payload)
        if creator_id != actor_id:
            await publish_event(creator_id, "event_rsvp_updated", payload)
