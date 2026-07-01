"""Push delivery strategy for domain events."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from app.core.unit_of_work import UnitOfWork
from app.domain.events.base import DomainEvent
from app.repositories.communication_notifications import (
    NotificationDeliveryRepository,
    NotificationRepository,
)
from app.services.delivery.base import DeliveryStrategy
from app.services.communication.push_config import PushConfigService

logger = logging.getLogger(__name__)


class PushDeliveryStrategy(DeliveryStrategy):
    """Persists notifications and dispatches push delivery."""

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
            push_service = PushConfigService(uow.session)

            for recipient_id in recipients:
                try:
                    notification = await self._get_or_create_notification(
                        repo=repo,
                        event=event,
                        recipient_id=recipient_id,
                        template_key=template_key,
                        context=context,
                    )
                    delivery = await push_service.send_push_for_notification(
                        notification=notification,
                        silent=bool(context.get("silent_push", False)),
                    )
                    await delivery_repo.save_delivery(delivery)
                except Exception:
                    logger.exception(
                        "Push delivery failed for %s to recipient %s",
                        type(event).__name__,
                        recipient_id,
                    )

            await uow.commit()
