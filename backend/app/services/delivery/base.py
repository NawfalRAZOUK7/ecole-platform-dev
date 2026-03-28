"""Base delivery strategy helpers for domain event notifications."""

from __future__ import annotations

import hashlib
import json
import re
from abc import ABC, abstractmethod
from dataclasses import asdict, is_dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.events.base import DomainEvent
from app.models.com import (
    DeliveryStatus,
    Notification,
    NotificationCategory,
    NotificationDelivery,
    NotificationPriority,
)
from app.repositories.notifications import (
    NotificationDeliveryRepository,
    NotificationRepository,
)

_CAMEL_CASE_RE = re.compile(r"(?<!^)(?=[A-Z])")


class DeliveryStrategy(ABC):
    """Abstract delivery strategy for domain events."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @abstractmethod
    async def deliver(
        self,
        event: DomainEvent,
        recipients: list[UUID],
        template_key: str,
        context: dict[str, Any],
    ) -> None:
        """Deliver a domain event notification to recipients."""
        ...

    async def _get_or_create_notification(
        self,
        *,
        repo: NotificationRepository,
        event: DomainEvent,
        recipient_id: UUID,
        template_key: str,
        context: dict[str, Any],
    ) -> Notification:
        school_id = context.get("school_id") or getattr(event, "school_id", None)
        if school_id is None:
            raise ValueError("Domain event delivery requires school_id")

        idempotency_key = self._notification_idempotency_key(
            event=event,
            recipient_id=recipient_id,
            template_key=template_key,
        )
        notification = await repo.find_notification_by_idempotency_key(idempotency_key)
        payload = self._notification_payload(event=event, context=context)

        if notification is None:
            notification = Notification(
                school_id=school_id,
                parent_id=recipient_id,
                event_ref=payload["event_ref"],
                idempotency_key=idempotency_key,
                title=payload["title"],
                body=payload["body"],
                category=payload["category"],
                priority=payload["priority"],
                action_url=payload["action_url"],
                action_payload=payload["action_payload"],
            )
            await repo.create_notifications([notification])
            return notification

        notification.title = payload["title"]
        notification.body = payload["body"]
        notification.category = payload["category"]
        notification.priority = payload["priority"]
        notification.event_ref = payload["event_ref"]
        notification.action_url = payload["action_url"]
        notification.action_payload = payload["action_payload"]
        return await repo.save_notification(notification)

    async def _get_or_create_delivery(
        self,
        *,
        delivery_repo: NotificationDeliveryRepository,
        notification: Notification,
        channel: str,
        default_status: str = DeliveryStatus.QUEUED.value,
    ) -> NotificationDelivery:
        delivery = await delivery_repo.get_delivery(
            notification_id=notification.id,
            channel=channel,
        )
        if delivery is not None:
            return delivery

        return NotificationDelivery(
            notification_id=notification.id,
            school_id=notification.school_id,
            channel=channel,
            status=default_status,
        )

    def _notification_payload(
        self,
        *,
        event: DomainEvent,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        title = str(context.get("title") or type(event).__name__)
        return {
            "title": title,
            "body": context.get("body"),
            "category": context.get("category", NotificationCategory.SYSTEM.value),
            "priority": context.get("priority", NotificationPriority.NORMAL.value),
            "action_url": context.get("action_url"),
            "action_payload": {
                "event_type": type(event).__name__,
                "context": self._jsonable_value(context),
            },
            "event_ref": context.get("event_ref", self._snake_case(type(event).__name__)),
        }

    def _notification_idempotency_key(
        self,
        *,
        event: DomainEvent,
        recipient_id: UUID,
        template_key: str,
    ) -> str:
        return (
            f"domain:{self._snake_case(type(event).__name__)}:"
            f"{recipient_id}:{template_key}:{self._event_fingerprint(event)}"
        )

    def _event_fingerprint(self, event: DomainEvent) -> str:
        payload = asdict(event) if is_dataclass(event) else dict(event.__dict__)
        raw = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]

    def _snake_case(self, value: str) -> str:
        return _CAMEL_CASE_RE.sub("_", value).lower()

    def _jsonable_value(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {str(key): self._jsonable_value(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [self._jsonable_value(item) for item in value]
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)
