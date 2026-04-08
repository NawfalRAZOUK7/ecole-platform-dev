"""Phase 15 calendar and events API."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.permissions import (
    PERM_CAL_EVENT_CREATE,
    PERM_CAL_EVENT_DELETE,
    PERM_CAL_EVENT_READ,
    PERM_CAL_EVENT_UPDATE,
    PERM_CAL_HOLIDAY_MANAGE,
    PERM_CAL_RSVP_RESPOND,
)
from app.core.response import list_response, success_response
from app.core.request_utils import get_client_ip, request_locale
from app.schemas.calendar import (
    CalendarOptionsResponse,
    EventCreateRequest,
    EventRSVPRequest,
    EventUpdateRequest,
    HolidayCreateRequest,
    HolidayUpdateRequest,
    ReminderPreferencesRequest,
)
from app.services.audit import AuditService
from app.services.calendar import CalendarService
from app.services.reminders import ReminderService
from app.services.rsvp import RSVPService

router = APIRouter(tags=["calendar"])


@router.get(
    "/events",
    summary="List calendar events",
    response_description="Role-filtered calendar events",
)
async def list_events(
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    type: str | None = Query(None),
    class_id: uuid.UUID | None = Query(None),
    auth: AuthContext = Depends(requires_permission(PERM_CAL_EVENT_READ)),
    db: AsyncSession = Depends(get_db),
):
    calendar = CalendarService(db)
    items = await calendar.list_events(
        school_id=auth.school_id,
        user_id=auth.user_id,
        role=auth.role,
        from_date=from_date,
        to_date=to_date,
        event_type=type,
        class_id=class_id,
    )
    return list_response(items)


@router.get(
    "/calendar/holidays",
    summary="List holidays",
    response_description="Holiday calendar rows for the selected academic year or date range",
)
async def list_holidays(
    academic_year_id: uuid.UUID | None = Query(None),
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    auth: AuthContext = Depends(requires_permission(PERM_CAL_EVENT_READ)),
    db: AsyncSession = Depends(get_db),
):
    calendar = CalendarService(db)
    items = await calendar.list_holidays(
        school_id=auth.school_id,
        user_id=auth.user_id,
        role=auth.role,
        academic_year_id=academic_year_id,
        from_date=from_date,
        to_date=to_date,
    )
    return list_response(items)


@router.post(
    "/calendar/holidays",
    status_code=201,
    summary="Create a holiday",
    response_description="Created holiday",
)
async def create_holiday(
    body: HolidayCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_CAL_HOLIDAY_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    calendar = CalendarService(db)
    audit = AuditService(db)
    holiday = await calendar.create_holiday(body=body)
    payload = await calendar.get_event_detail(
        event_id=holiday.id,
        school_id=auth.school_id,
        user_id=auth.user_id,
        role=auth.role,
    )
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="calendar.holiday.create",
        target_type="holiday",
        target_id=holiday.id,
        outcome="success",
        entity_after=payload,
        ip_address=get_client_ip(request),
    )
    await db.commit()
    return success_response(payload)


@router.put(
    "/calendar/holidays/{holiday_id}",
    summary="Update a holiday",
    response_description="Updated holiday",
)
async def update_holiday(
    holiday_id: uuid.UUID,
    body: HolidayUpdateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_CAL_HOLIDAY_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    calendar = CalendarService(db)
    audit = AuditService(db)
    before = await calendar.get_event_detail(
        event_id=holiday_id,
        school_id=auth.school_id,
        user_id=auth.user_id,
        role=auth.role,
    )
    holiday = await calendar.update_holiday(
        holiday_id=holiday_id,
        body=body,
    )
    after = await calendar.get_event_detail(
        event_id=holiday.id,
        school_id=auth.school_id,
        user_id=auth.user_id,
        role=auth.role,
    )
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="calendar.holiday.update",
        target_type="holiday",
        target_id=holiday.id,
        outcome="success",
        entity_before=before,
        entity_after=after,
        ip_address=get_client_ip(request),
    )
    await db.commit()
    return success_response(after)


@router.delete(
    "/calendar/holidays/{holiday_id}",
    summary="Delete a holiday",
    response_description="Deletion outcome",
)
async def delete_holiday(
    holiday_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_CAL_HOLIDAY_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    calendar = CalendarService(db)
    audit = AuditService(db)
    before = await calendar.get_event_detail(
        event_id=holiday_id,
        school_id=auth.school_id,
        user_id=auth.user_id,
        role=auth.role,
    )
    holiday = await calendar.delete_holiday(holiday_id=holiday_id)
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="calendar.holiday.delete",
        target_type="holiday",
        target_id=holiday.id,
        outcome="success",
        entity_before=before,
        entity_after={"deleted": True, "id": str(holiday.id)},
        ip_address=get_client_ip(request),
    )
    await db.commit()
    return success_response({"deleted": True, "id": str(holiday.id)})


@router.post(
    "/events",
    status_code=201,
    summary="Create an event",
    response_description="Created event",
)
async def create_event(
    body: EventCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_CAL_EVENT_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    calendar = CalendarService(db)
    reminders = ReminderService(db)
    audit = AuditService(db)

    event = await calendar.create_event(
        school_id=auth.school_id,
        user_id=auth.user_id,
        role=auth.role,
        body=body,
    )
    await reminders.sync_event_reminders(
        event=event,
        reminder_offsets_minutes=body.reminder_offsets_minutes,
    )
    payload = await calendar.get_event_detail(
        event_id=event.id,
        school_id=auth.school_id,
        user_id=auth.user_id,
        role=auth.role,
    )
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="calendar.event.create",
        target_type="event",
        target_id=event.id,
        outcome="success",
        entity_after=payload,
        ip_address=get_client_ip(request),
    )
    await db.commit()
    return success_response(payload)


@router.get(
    "/events/{event_id}",
    summary="Get event detail",
    response_description="Calendar event detail",
)
async def get_event(
    event_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_CAL_EVENT_READ)),
    db: AsyncSession = Depends(get_db),
):
    calendar = CalendarService(db)
    payload = await calendar.get_event_detail(
        event_id=event_id,
        school_id=auth.school_id,
        user_id=auth.user_id,
        role=auth.role,
    )
    return success_response(payload)


@router.put(
    "/events/{event_id}",
    summary="Update an event",
    response_description="Updated event detail",
)
async def update_event(
    event_id: uuid.UUID,
    body: EventUpdateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_CAL_EVENT_UPDATE)),
    db: AsyncSession = Depends(get_db),
):
    calendar = CalendarService(db)
    reminders = ReminderService(db)
    audit = AuditService(db)

    before = await calendar.get_event_detail(
        event_id=event_id,
        school_id=auth.school_id,
        user_id=auth.user_id,
        role=auth.role,
    )
    event = await calendar.update_event(
        event_id=event_id,
        school_id=auth.school_id,
        user_id=auth.user_id,
        role=auth.role,
        body=body,
    )
    await reminders.sync_event_reminders(
        event=event,
        reminder_offsets_minutes=body.reminder_offsets_minutes,
    )
    after = await calendar.get_event_detail(
        event_id=event.id,
        school_id=auth.school_id,
        user_id=auth.user_id,
        role=auth.role,
    )
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="calendar.event.update",
        target_type="event",
        target_id=event.id,
        outcome="success",
        entity_before=before,
        entity_after=after,
        ip_address=get_client_ip(request),
    )
    await db.commit()
    return success_response(after)


@router.delete(
    "/events/{event_id}",
    summary="Delete an event",
    response_description="Deletion outcome",
)
async def delete_event(
    event_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_CAL_EVENT_DELETE)),
    db: AsyncSession = Depends(get_db),
):
    calendar = CalendarService(db)
    reminders = ReminderService(db)
    audit = AuditService(db)

    before = await calendar.get_event_detail(
        event_id=event_id,
        school_id=auth.school_id,
        user_id=auth.user_id,
        role=auth.role,
    )
    event = await calendar.delete_event(event_id=event_id, school_id=auth.school_id)
    await reminders.clear_event_reminders(event_id=event.id)
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="calendar.event.delete",
        target_type="event",
        target_id=event.id,
        outcome="success",
        entity_before=before,
        entity_after={"deleted": True, "id": str(event.id)},
        ip_address=get_client_ip(request),
    )
    await db.commit()
    return success_response({"deleted": True, "id": str(event.id)})


@router.post(
    "/events/{event_id}/rsvp",
    summary="Respond to an event RSVP",
    response_description="Updated RSVP state",
)
async def respond_to_event(
    event_id: uuid.UUID,
    body: EventRSVPRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_CAL_RSVP_RESPOND)),
    db: AsyncSession = Depends(get_db),
):
    service = RSVPService(db)
    audit = AuditService(db)
    payload = await service.respond(
        event_id=event_id,
        school_id=auth.school_id,
        user_id=auth.user_id,
        role=auth.role,
        status=body.status,
    )
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="calendar.event.rsvp",
        target_type="event",
        target_id=event_id,
        outcome="success",
        entity_after=payload,
        ip_address=get_client_ip(request),
    )
    await db.commit()
    return success_response(payload)


@router.get(
    "/events/{event_id}/rsvp",
    summary="Get current user's RSVP state",
    response_description="Own RSVP state for the event",
)
async def get_own_rsvp(
    event_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_CAL_EVENT_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = RSVPService(db)
    payload = await service.get_own_rsvp(
        event_id=event_id,
        school_id=auth.school_id,
        user_id=auth.user_id,
        role=auth.role,
    )
    return success_response(payload)


@router.get(
    "/events/{event_id}/rsvps",
    summary="List all event RSVPs",
    response_description="RSVP list with counts",
)
async def list_event_rsvps(
    event_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_CAL_EVENT_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = RSVPService(db)
    payload = await service.list_rsvps(
        event_id=event_id,
        school_id=auth.school_id,
        user_id=auth.user_id,
        role=auth.role,
    )
    return success_response(payload)


@router.post(
    "/events/reminder-preferences",
    summary="Update reminder preferences",
    response_description="Reminder preferences for the current user",
)
async def update_reminder_preferences(
    body: ReminderPreferencesRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_CAL_EVENT_READ)),
    db: AsyncSession = Depends(get_db),
):
    calendar = CalendarService(db)
    audit = AuditService(db)
    before = await calendar.list_reminder_preferences(
        school_id=auth.school_id,
        user_id=auth.user_id,
    )
    after = await calendar.update_reminder_preferences(
        school_id=auth.school_id,
        user_id=auth.user_id,
        preferences=[item.model_dump() for item in body.preferences],
    )
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="calendar.reminder_preferences.update",
        target_type="event_reminder_preferences",
        target_id=auth.user_id,
        outcome="success",
        entity_before={"preferences": before},
        entity_after={"preferences": after},
        ip_address=get_client_ip(request),
    )
    await db.commit()
    return success_response({"preferences": after})


@router.get(
    "/calendar/options",
    summary="Calendar UI options",
    response_description="Visible classes, signed iCal URL, and reminder preferences",
)
async def calendar_options(
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_CAL_EVENT_READ)),
    db: AsyncSession = Depends(get_db),
):
    calendar = CalendarService(db)
    payload = CalendarOptionsResponse(
        classes=await calendar.get_visible_classes(
            school_id=auth.school_id,
            user_id=auth.user_id,
            role=auth.role,
        ),
        ical_url=await calendar.build_ical_url(
            user_id=auth.user_id,
            school_id=auth.school_id,
            role=auth.role,
            base_url=str(request.base_url),
            lang=request_locale(request),
        ),
        reminder_preferences=await calendar.list_reminder_preferences(
            school_id=auth.school_id,
            user_id=auth.user_id,
        ),
    ).model_dump()
    return success_response(payload)


@router.get(
    "/calendar/ical",
    summary="iCal subscription feed",
    response_description="Signed iCal calendar feed",
)
async def calendar_ical_feed(
    token: str = Query(...),
    lang: str = Query("fr"),
    db: AsyncSession = Depends(get_db),
):
    calendar = CalendarService(db)
    actor = calendar.parse_ical_token(token)
    feed = await calendar.render_ical_feed(actor=actor, lang=lang)
    return Response(content=feed, media_type="text/calendar; charset=utf-8")
