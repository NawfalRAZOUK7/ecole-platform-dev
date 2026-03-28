"""Phase 13 email digest and email notification service."""

from __future__ import annotations

import logging
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.unit_of_work import UnitOfWork
from app.models.com import (
    DeliveryStatus,
    DigestFrequency,
    Notification,
    NotificationCategory,
    NotificationDelivery,
    NotificationPreference,
)
from app.models.iam import User
from app.repositories.notifications import NotificationDeliveryRepository, NotificationRepository
from app.services.email import email_service

logger = logging.getLogger(__name__)

JWT_ALGORITHM = settings.jwt_algorithm
UNSUBSCRIBE_ACTION = "notifications.unsubscribe"
OPEN_TRACK_ACTION = "notifications.email-open"

NOTIFICATION_CATEGORIES = (
    NotificationCategory.ACADEMIC.value,
    NotificationCategory.BILLING.value,
    NotificationCategory.ATTENDANCE.value,
    NotificationCategory.SYSTEM.value,
    NotificationCategory.ANNOUNCEMENT.value,
)


class EmailDigestService:
    """Digest scheduling, unsubscribe tokens, and email delivery tracking."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.notification_repo = NotificationRepository(db)
        self.delivery_repo = NotificationDeliveryRepository(db)

    async def get_digest_frequency(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> str:
        prefs = await self.notification_repo.list_preferences(
            school_id=school_id,
            user_id=user_id,
        )
        email_prefs = [pref for pref in prefs if pref.channel == "email"]
        if not email_prefs:
            return DigestFrequency.OFF.value
        for pref in email_prefs:
            if pref.digest_frequency != DigestFrequency.OFF.value:
                return pref.digest_frequency
        return DigestFrequency.OFF.value

    async def update_digest_frequency(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        digest_frequency: str,
    ) -> str:
        if self.db.info.get("_uow_depth"):
            return await self._update_digest_frequency_with_repo(
                notification_repo=self.notification_repo,
                school_id=school_id,
                user_id=user_id,
                digest_frequency=digest_frequency,
            )

        async with UnitOfWork(self.db) as uow:
            notification_repo = NotificationRepository(uow.session)
            updated = await self._update_digest_frequency_with_repo(
                notification_repo=notification_repo,
                school_id=school_id,
                user_id=user_id,
                digest_frequency=digest_frequency,
            )
            await uow.commit()
            return updated

    async def unsubscribe_all_email(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        if self.db.info.get("_uow_depth"):
            await self._unsubscribe_all_email_with_repo(
                notification_repo=self.notification_repo,
                school_id=school_id,
                user_id=user_id,
            )
            return

        async with UnitOfWork(self.db) as uow:
            notification_repo = NotificationRepository(uow.session)
            await self._unsubscribe_all_email_with_repo(
                notification_repo=notification_repo,
                school_id=school_id,
                user_id=user_id,
            )
            await uow.commit()

    async def send_notification_email(
        self,
        *,
        notification: Notification,
        user: User,
        locale: str = "fr",
    ) -> NotificationDelivery:
        delivery = await self.delivery_repo.get_delivery(
            notification_id=notification.id,
            channel="email",
        )
        if delivery is None:
            delivery = NotificationDelivery(
                notification_id=notification.id,
                school_id=notification.school_id,
                channel="email",
                status=DeliveryStatus.QUEUED.value,
            )

        if not user.email:
            delivery.status = DeliveryStatus.FAILED.value
            delivery.last_error = "User has no email"
            return delivery

        tracking_token = self.build_open_tracking_token(
            delivery_id=delivery.id,
            school_id=notification.school_id,
            user_id=user.id,
        )
        unsubscribe_token = self.build_unsubscribe_token(
            school_id=notification.school_id,
            user_id=user.id,
        )
        success = await email_service.send_email(
            to=user.email,
            template_name="notification_alert",
            lang=locale,
            title=notification.title,
            body=notification.body,
            action_url=self._resolve_action_url(notification),
            unsubscribe_url=self.unsubscribe_url(unsubscribe_token),
            open_tracking_url=self.open_tracking_url(tracking_token),
            is_rtl=locale == "ar",
            category=notification.category,
        )

        delivery.status = (
            DeliveryStatus.SENT.value if success else DeliveryStatus.BOUNCED.value
        )
        delivery.delivered_at = _utc_now() if success else None
        delivery.last_error = None if success else "SMTP delivery failed"
        return delivery

    async def send_digest_email(
        self,
        *,
        user: User,
        school_id: uuid.UUID,
        notifications: list[Notification],
        locale: str = "fr",
    ) -> bool:
        if not notifications or not user.email:
            return False

        if self.db.info.get("_uow_depth"):
            return await self._send_digest_email_with_repos(
                notification_repo=self.notification_repo,
                delivery_repo=self.delivery_repo,
                user=user,
                school_id=school_id,
                notifications=notifications,
                locale=locale,
            )

        async with UnitOfWork(self.db) as uow:
            notification_repo = NotificationRepository(uow.session)
            delivery_repo = NotificationDeliveryRepository(uow.session)
            success = await self._send_digest_email_with_repos(
                notification_repo=notification_repo,
                delivery_repo=delivery_repo,
                user=user,
                school_id=school_id,
                notifications=notifications,
                locale=locale,
            )
            await uow.commit()
            return success

    async def mark_email_opened(
        self,
        *,
        delivery_id: uuid.UUID,
    ) -> NotificationDelivery | None:
        if self.db.info.get("_uow_depth"):
            delivery = await self.delivery_repo.get_delivery_by_id(delivery_id)
            if delivery is None:
                return None
            delivery.status = DeliveryStatus.OPENED.value
            delivery.clicked_at = _utc_now()
            return delivery

        async with UnitOfWork(self.db) as uow:
            delivery_repo = NotificationDeliveryRepository(uow.session)
            delivery = await delivery_repo.get_delivery_by_id(delivery_id)
            if delivery is None:
                return None
            delivery.status = DeliveryStatus.OPENED.value
            delivery.clicked_at = _utc_now()
            await uow.commit()
            return delivery

    async def users_due_for_digest(
        self,
        *,
        now: datetime | None = None,
        frequency: str | None = None,
    ) -> list[tuple[uuid.UUID, uuid.UUID]]:
        current_time = now or _utc_now()
        tz = ZoneInfo(settings.notifications_digest_timezone)
        localized_now = current_time.astimezone(tz)

        if localized_now.hour != settings.notifications_digest_send_hour:
            return []

        if frequency is None:
            frequency = DigestFrequency.DAILY.value

        if frequency == DigestFrequency.WEEKLY.value and localized_now.weekday() != 0:
            return []

        prefs = await self.notification_repo.list_users_with_digest_preferences(
            digest_frequency=frequency
        )
        return list({(pref.school_id, pref.user_id) for pref in prefs})

    def build_unsubscribe_token(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> str:
        payload = {
            "sub": str(user_id),
            "school_id": str(school_id),
            "action": UNSUBSCRIBE_ACTION,
            "exp": _utc_now()
            + timedelta(hours=settings.notifications_unsubscribe_ttl_hours),
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm=JWT_ALGORITHM)

    def parse_unsubscribe_token(self, token: str) -> tuple[uuid.UUID, uuid.UUID]:
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[JWT_ALGORITHM],
            )
        except JWTError as exc:  # pragma: no cover - invalid token handling
            raise ValueError("Invalid unsubscribe token") from exc

        if payload.get("action") != UNSUBSCRIBE_ACTION:
            raise ValueError("Invalid unsubscribe token")
        return uuid.UUID(payload["school_id"]), uuid.UUID(payload["sub"])

    def build_open_tracking_token(
        self,
        *,
        delivery_id: uuid.UUID,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> str:
        payload = {
            "delivery_id": str(delivery_id),
            "school_id": str(school_id),
            "sub": str(user_id),
            "action": OPEN_TRACK_ACTION,
            "exp": _utc_now() + timedelta(days=30),
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm=JWT_ALGORITHM)

    def parse_open_tracking_token(self, token: str) -> uuid.UUID:
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[JWT_ALGORITHM],
            )
        except JWTError as exc:  # pragma: no cover - invalid token handling
            raise ValueError("Invalid open tracking token") from exc

        if payload.get("action") != OPEN_TRACK_ACTION:
            raise ValueError("Invalid open tracking token")
        return uuid.UUID(payload["delivery_id"])

    def unsubscribe_url(self, token: str) -> str:
        return (
            f"{settings.web_app_base_url.rstrip('/')}/api/v1/notifications/unsubscribe"
            f"?token={token}"
        )

    def open_tracking_url(self, token: str) -> str:
        return (
            f"{settings.web_app_base_url.rstrip('/')}/api/v1/notifications/email-open"
            f"?token={token}"
        )

    async def _ensure_email_deliveries(
        self,
        *,
        notification_repo: NotificationRepository,
        delivery_repo: NotificationDeliveryRepository,
        notifications: list[Notification],
    ) -> list[NotificationDelivery]:
        deliveries: list[NotificationDelivery] = []
        pending: list[NotificationDelivery] = []
        for notification in notifications:
            delivery = await delivery_repo.get_delivery(
                notification_id=notification.id,
                channel="email",
            )
            if delivery is None:
                delivery = NotificationDelivery(
                    notification_id=notification.id,
                    school_id=notification.school_id,
                    channel="email",
                    status=DeliveryStatus.QUEUED.value,
                )
                pending.append(delivery)
            deliveries.append(delivery)
        if pending:
            await notification_repo.create_deliveries(pending)
        return deliveries

    async def _update_digest_frequency_with_repo(
        self,
        *,
        notification_repo: NotificationRepository,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        digest_frequency: str,
    ) -> str:
        prefs = await notification_repo.list_preferences(
            school_id=school_id,
            user_id=user_id,
        )
        email_prefs = [pref for pref in prefs if pref.channel == "email"]

        if not email_prefs:
            email_prefs = [
                NotificationPreference(
                    school_id=school_id,
                    user_id=user_id,
                    channel="email",
                    category=category,
                    enabled=digest_frequency != DigestFrequency.OFF.value,
                    digest_frequency=digest_frequency,
                )
                for category in NOTIFICATION_CATEGORIES
            ]
            await notification_repo.upsert_preferences(
                school_id=school_id,
                user_id=user_id,
                preferences=email_prefs,
            )
            return digest_frequency

        for pref in email_prefs:
            pref.digest_frequency = digest_frequency
            if digest_frequency == DigestFrequency.OFF.value:
                pref.enabled = False
        return digest_frequency

    async def _unsubscribe_all_email_with_repo(
        self,
        *,
        notification_repo: NotificationRepository,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        prefs = await notification_repo.list_preferences(
            school_id=school_id,
            user_id=user_id,
        )
        for pref in prefs:
            if pref.channel == "email":
                pref.enabled = False
                pref.digest_frequency = DigestFrequency.OFF.value

    async def _send_digest_email_with_repos(
        self,
        *,
        notification_repo: NotificationRepository,
        delivery_repo: NotificationDeliveryRepository,
        user: User,
        school_id: uuid.UUID,
        notifications: list[Notification],
        locale: str,
    ) -> bool:
        deliveries = await self._ensure_email_deliveries(
            notification_repo=notification_repo,
            delivery_repo=delivery_repo,
            notifications=notifications,
        )
        primary_delivery = deliveries[0]
        tracking_token = self.build_open_tracking_token(
            delivery_id=primary_delivery.id,
            school_id=school_id,
            user_id=user.id,
        )
        unsubscribe_token = self.build_unsubscribe_token(
            school_id=school_id,
            user_id=user.id,
        )

        grouped = self._group_notifications(notifications)
        success = await email_service.send_email(
            to=user.email,
            template_name="notification_digest",
            lang=locale,
            grouped_notifications=grouped,
            generated_at=_utc_now(),
            title=self._digest_title(locale),
            unsubscribe_url=self.unsubscribe_url(unsubscribe_token),
            open_tracking_url=self.open_tracking_url(tracking_token),
            action_base_url=settings.web_app_base_url.rstrip("/"),
            is_rtl=locale == "ar",
        )

        for delivery in deliveries:
            delivery.status = (
                DeliveryStatus.SENT.value if success else DeliveryStatus.BOUNCED.value
            )
            delivery.delivered_at = _utc_now() if success else None
            delivery.last_error = None if success else "SMTP delivery failed"
        return success

    def _group_notifications(
        self,
        notifications: list[Notification],
    ) -> dict[str, list[dict[str, str | None]]]:
        grouped: dict[str, list[dict[str, str | None]]] = defaultdict(list)
        for notification in notifications:
            grouped[notification.category].append(
                {
                    "id": str(notification.id),
                    "title": notification.title,
                    "body": notification.body,
                    "created_at": notification.created_at.isoformat(),
                    "action_url": self._resolve_action_url(notification),
                }
            )
        return dict(grouped)

    def _resolve_action_url(self, notification: Notification) -> str:
        if notification.action_url:
            if notification.action_url.startswith("http"):
                return notification.action_url
            return f"{settings.web_app_base_url.rstrip('/')}{notification.action_url}"
        return f"{settings.web_app_base_url.rstrip('/')}/notifications"

    def _digest_title(self, locale: str) -> str:
        if locale == "ar":
            return "ملخص الإشعارات"
        if locale == "en":
            return "Notification Digest"
        return "Résumé des notifications"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)
