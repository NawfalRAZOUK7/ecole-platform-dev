"""Phase 15 calendar and events coverage.

Integration tests run against the Docker-backed backend + postgres + redis stack.
Seed data must be loaded before execution (make seed).

Run:
  python -m pytest tests/integration/api/admin/test_calendar_events.py -v
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from sqlalchemy import select

from app.models.calendar import EventReminder
from app.services.communication.reminders import ReminderService


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _teacher_class_id(client: httpx.AsyncClient, token: str) -> str:
    response = await client.get(
        "/calendar/options",
        headers=_auth_headers(token),
    )
    assert response.status_code == 200
    classes = response.json()["data"]["classes"]
    assert classes, "Expected at least one visible class"
    return classes[0]["id"]


async def _create_event(
    client: httpx.AsyncClient,
    token: str,
    payload: dict,
) -> dict:
    response = await client.post(
        "/events",
        headers=_auth_headers(token),
        json=payload,
    )
    assert response.status_code in {200, 201}, response.text
    return response.json()["data"]


class TestCalendarEventsIntegration:
    @pytest.mark.asyncio
    async def test_teacher_class_event_recurs_and_student_can_view(
        self,
        client: httpx.AsyncClient,
        admin_token: str,
        student_token: str,
    ):
        start_at = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(
            days=2, hours=2
        )
        end_at = start_at + timedelta(hours=2)
        title = f"Phase15 recurrence {uuid.uuid4()}"

        created = await _create_event(
            client,
            admin_token,
            {
                "title_fr": title,
                "type": "meeting",
                "visibility": "school",
                "start_at": start_at.isoformat(),
                "end_at": end_at.isoformat(),
                "recurrence_rule": {
                    "frequency": "weekly",
                    "interval": 1,
                    "until": (start_at + timedelta(days=21)).isoformat(),
                },
                "reminder_offsets_minutes": [60],
            },
        )

        try:
            list_response = await client.get(
                "/events",
                headers=_auth_headers(student_token),
                params={
                    "from": start_at.date().isoformat(),
                    "to": (start_at.date() + timedelta(days=14)).isoformat(),
                },
            )
            assert list_response.status_code == 200
            items = [
                item
                for item in list_response.json()["data"]
                if item["id"] == created["id"]
            ]
            assert len(items) >= 2
            assert len({item["instance_id"] for item in items}) >= 2
        finally:
            await client.delete(
                f"/events/{created['id']}",
                headers=_auth_headers(admin_token),
            )

    @pytest.mark.asyncio
    async def test_capacity_limit_blocks_second_attendee(
        self,
        client: httpx.AsyncClient,
        admin_token: str,
        student_token: str,
        parent_token: str,
    ):
        start_at = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(
            days=1, hours=3
        )
        end_at = start_at + timedelta(hours=1)
        title = f"Phase15 capacity {uuid.uuid4()}"
        created = await _create_event(
            client,
            admin_token,
            {
                "title_fr": title,
                "type": "custom",
                "visibility": "school",
                "start_at": start_at.isoformat(),
                "end_at": end_at.isoformat(),
                "capacity": 1,
                "reminder_offsets_minutes": [60],
            },
        )

        try:
            first = await client.post(
                f"/events/{created['id']}/rsvp",
                headers=_auth_headers(student_token),
                json={"status": "attending"},
            )
            assert first.status_code == 200

            second = await client.post(
                f"/events/{created['id']}/rsvp",
                headers=_auth_headers(parent_token),
                json={"status": "attending"},
            )
            assert second.status_code == 409
        finally:
            await client.delete(
                f"/events/{created['id']}",
                headers=_auth_headers(admin_token),
            )

    @pytest.mark.asyncio
    async def test_signed_ical_feed_works_without_authentication(
        self,
        client: httpx.AsyncClient,
        student_token: str,
    ):
        options_response = await client.get(
            "/calendar/options",
            headers=_auth_headers(student_token),
        )
        assert options_response.status_code == 200
        ical_url = options_response.json()["data"]["ical_url"]
        assert "token=" in ical_url

        path = ical_url.replace("http://localhost:8000/api/v1", "")
        response = await client.get(path)
        assert response.status_code == 200
        assert response.text.startswith("BEGIN:VCALENDAR")
        assert "VERSION:2.0" in response.text
        assert "END:VCALENDAR" in response.text

    @pytest.mark.asyncio
    async def test_reminder_dispatch_creates_notification(
        self,
        client: httpx.AsyncClient,
        admin_token: str,
        student_token: str,
        session_factory,
    ):
        start_at = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(
            hours=2
        )
        end_at = start_at + timedelta(hours=1)
        title = f"Phase15 reminder {uuid.uuid4()}"
        created = await _create_event(
            client,
            admin_token,
            {
                "title_fr": title,
                "type": "meeting",
                "visibility": "school",
                "start_at": start_at.isoformat(),
                "end_at": end_at.isoformat(),
                "reminder_offsets_minutes": [60],
            },
        )

        try:
            async with session_factory() as session:
                result = await session.execute(
                    select(EventReminder).where(
                        EventReminder.event_id == uuid.UUID(created["id"])
                    )
                )
                reminders = result.scalars().all()
                assert reminders
                for reminder in reminders:
                    reminder.remind_at = datetime.now(timezone.utc) - timedelta(
                        minutes=1
                    )
                await session.commit()

            async with session_factory() as session:
                service = ReminderService(session)
                sent = await service.send_due_reminders()
                await session.commit()
                assert sent > 0

            notifications_response = await client.get(
                "/notifications",
                headers=_auth_headers(student_token),
                params={"limit": 20},
            )
            assert notifications_response.status_code == 200
            items = notifications_response.json()["data"]
            assert any(
                item["event_ref"] == f"calendar.reminder:{created['id']}"
                for item in items
            )
        finally:
            await client.delete(
                f"/events/{created['id']}",
                headers=_auth_headers(admin_token),
            )

    @pytest.mark.asyncio
    async def test_event_deny_ordering_for_create_and_hidden_detail(
        self,
        client: httpx.AsyncClient,
        admin_token: str,
        student_token: str,
        teacher_token: str,
    ):
        class_id = await _teacher_class_id(client, teacher_token)
        payload = {
            "title_fr": f"Phase15 deny {uuid.uuid4()}",
            "type": "meeting",
            "visibility": "class",
            "class_id": class_id,
            "start_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            "end_at": (
                datetime.now(timezone.utc) + timedelta(days=1, hours=1)
            ).isoformat(),
        }

        unauthenticated = await client.post("/events", json=payload)
        assert unauthenticated.status_code == 401

        forbidden = await client.post(
            "/events",
            headers=_auth_headers(student_token),
            json=payload,
        )
        assert forbidden.status_code == 403

        hidden_event = await _create_event(
            client,
            admin_token,
            {
                "title_fr": f"Phase15 hidden {uuid.uuid4()}",
                "type": "meeting",
                "visibility": "role",
                "role_codes": ["TCH"],
                "start_at": payload["start_at"],
                "end_at": payload["end_at"],
            },
        )

        try:
            masked = await client.get(
                f"/events/{hidden_event['id']}",
                headers=_auth_headers(student_token),
            )
            assert masked.status_code == 404
        finally:
            await client.delete(
                f"/events/{hidden_event['id']}",
                headers=_auth_headers(admin_token),
            )

    async def _admin_token(self, client: httpx.AsyncClient) -> str:
        response = await client.post(
            "/auth/login",
            json={
                "email": "admin@ecole-benani.ma",
                "password": "admin123",
                "school_id": "00000000-0000-4000-8000-000000000001",
            },
        )
        assert response.status_code == 200
        return response.json()["data"]["access_token"]
