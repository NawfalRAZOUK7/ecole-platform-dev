"""In-app delivery strategy for domain events."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.core.unit_of_work import UnitOfWork
from app.domain.events.base import DomainEvent
from app.models.com import DeliveryChannel, DeliveryStatus
from app.repositories.communication_notifications import (
    NotificationDeliveryRepository,
    NotificationRepository,
)
from app.services.delivery.base import DeliveryStrategy


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class InAppDeliveryStrategy(DeliveryStrategy):
    """Creates persisted in-app notifications for event recipients."""

    async def deliver(
        self,
        event: DomainEvent,
        recipients: list[UUID],
        template_key: str,
        context: dict[str, Any],
    ) -> None:
        if not recipients:
            return

        async with UnitOfWork(self.db) as uow:
            repo = NotificationRepository(uow.session)
            delivery_repo = NotificationDeliveryRepository(uow.session)

            for recipient_id in recipients:
                notification = await self._get_or_create_notification(
                    repo=repo,
                    event=event,
                    recipient_id=recipient_id,
                    template_key=template_key,
                    context=context,
                )
                delivery = await self._get_or_create_delivery(
                    delivery_repo=delivery_repo,
                    notification=notification,
                    channel=DeliveryChannel.IN_APP.value,
                    default_status=DeliveryStatus.DELIVERED.value,
                )
                delivery.status = DeliveryStatus.DELIVERED.value
                delivery.delivered_at = _utc_now()
                delivery.last_error = None
                await delivery_repo.save_delivery(delivery)

            await uow.commit()
