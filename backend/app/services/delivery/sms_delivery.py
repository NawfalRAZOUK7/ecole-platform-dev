"""SMS delivery strategy for domain events."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.core.unit_of_work import UnitOfWork
from app.domain.events.base import DomainEvent
from app.models.com import DeliveryChannel, DeliveryStatus
from app.repositories.notifications import (
    NotificationDeliveryRepository,
    NotificationRepository,
)
from app.services.delivery.base import DeliveryStrategy
from app.services.sms import sms_service

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SMSDeliveryStrategy(DeliveryStrategy):
    """Sends SMS notifications using the existing SMS service."""

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
            users = await repo.list_user_contacts(recipients)

            for recipient_id in recipients:
                try:
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
                        channel=DeliveryChannel.SMS.value,
                    )
                    user = users.get(recipient_id)
                    if user is None or not user.phone:
                        delivery.status = DeliveryStatus.FAILED.value
                        delivery.delivered_at = None
                        delivery.last_error = "User has no phone number"
                    else:
                        success = await sms_service.send_notification_fallback(
                            to=user.phone,
                            title=str(context.get("title", "Notification")),
                            body=context.get("body"),
                            user_id=user.id,
                        )
                        delivery.status = (
                            DeliveryStatus.SENT.value
                            if success
                            else DeliveryStatus.FAILED.value
                        )
                        delivery.delivered_at = _utc_now() if success else None
                        delivery.last_error = None if success else "SMS send failed"

                    await delivery_repo.save_delivery(delivery)
                except Exception:
                    logger.exception(
                        "SMS delivery failed for %s to recipient %s",
                        type(event).__name__,
                        recipient_id,
                    )

            await uow.commit()
