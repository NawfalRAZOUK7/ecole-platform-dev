"""Email delivery strategy for domain events."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.core.unit_of_work import UnitOfWork
from app.domain.events.base import DomainEvent
from app.models.com import DeliveryChannel, DeliveryStatus
from app.models.iam import User
from app.repositories.notifications import (
    NotificationDeliveryRepository,
    NotificationRepository,
)
from app.services.delivery.base import DeliveryStrategy
from app.services.email import email_service

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EmailDeliveryStrategy(DeliveryStrategy):
    """Sends event-driven email notifications using the existing email service."""

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
                        channel=DeliveryChannel.EMAIL.value,
                    )
                    user = users.get(recipient_id)
                    await self._send_email_for_user(
                        user=user,
                        template_key=template_key,
                        context=context,
                        delivery=delivery,
                    )
                    await delivery_repo.save_delivery(delivery)
                except Exception:
                    logger.exception(
                        "Email delivery failed for %s to recipient %s",
                        type(event).__name__,
                        recipient_id,
                    )

            await uow.commit()

    async def _send_email_for_user(
        self,
        *,
        user: User | None,
        template_key: str,
        context: dict[str, Any],
        delivery,
    ) -> None:
        if user is None or not user.email:
            delivery.status = DeliveryStatus.FAILED.value
            delivery.delivered_at = None
            delivery.last_error = "User has no email"
            return

        template_name = self._template_name(template_key)
        lang = str(context.get("locale", "fr") or "fr")
        email_context = self._template_context(
            user=user,
            template_name=template_name,
            context=context,
        )
        success = await email_service.send_email(
            to=user.email,
            template_name=template_name,
            lang=lang,
            **email_context,
        )
        delivery.status = (
            DeliveryStatus.SENT.value if success else DeliveryStatus.BOUNCED.value
        )
        delivery.delivered_at = _utc_now() if success else None
        delivery.last_error = None if success else "SMTP delivery failed"

    def _template_name(self, template_key: str) -> str:
        template_map = {
            "grade_published": "grade_published",
            "invoice_generated": "invoice_reminder",
            "user_registered": "welcome",
            "new_device_login": "notification_alert",
        }
        return template_map.get(template_key, "notification_alert")

    def _template_context(
        self,
        *,
        user: User,
        template_name: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        display_name = user.full_name or user.email

        if template_name == "welcome":
            return {
                "user_name": display_name,
                "school_name": context.get("school_name", "Ecole Platform"),
                "email": user.email,
                "role": context.get("role", "user"),
            }

        if template_name == "invoice_reminder":
            return {
                "parent_name": display_name,
                "invoice_id": str(context.get("invoice_id") or ""),
                "amount": context.get("amount", 0),
                "currency": context.get("currency", "MAD"),
                "due_date": context.get("due_date", ""),
            }

        if template_name == "grade_published":
            return {
                "student_name": display_name,
                "assignment_title": context.get("course_title") or "Course grade",
                "score": context.get("score", 0),
                "total_points": context.get("total_points", 100),
                "feedback": context.get("feedback"),
            }

        return {
            "title": context.get("title", "Notification"),
            "body": context.get("body"),
            "action_url": context.get("action_url"),
            "unsubscribe_url": context.get("unsubscribe_url"),
            "open_tracking_url": context.get("open_tracking_url"),
            "category": context.get("category"),
            "is_rtl": lang_is_rtl(str(context.get("locale", "fr") or "fr")),
        }


def lang_is_rtl(lang: str) -> bool:
    return lang == "ar"
