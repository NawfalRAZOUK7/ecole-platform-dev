"""Phase 13 push notification configuration and delivery service."""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.unit_of_work import UnitOfWork
from app.models.com import (
    DeliveryStatus,
    DeviceToken,
    Notification,
    NotificationDelivery,
)
from app.repositories.communication_notifications import (
    NotificationDeliveryRepository,
    NotificationRepository,
)

logger = logging.getLogger(__name__)

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
except Exception:  # pragma: no cover - optional dependency in development
    firebase_admin = None
    credentials = None
    messaging = None


_firebase_app = None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PushConfigService:
    """Device registry + FCM sender."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.notification_repo = NotificationRepository(db)
        self.delivery_repo = NotificationDeliveryRepository(db)

    async def list_devices(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[DeviceToken]:
        return await self.notification_repo.list_devices(
            school_id=school_id,
            user_id=user_id,
        )

    async def register_device(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        token: str,
        platform: str,
        device_name: str | None,
    ) -> DeviceToken:
        async with UnitOfWork(self.db) as uow:
            notification_repo = NotificationRepository(uow.session)
            existing = await notification_repo.find_device_by_token(token)
            now = _utc_now()

            if existing:
                existing.school_id = school_id
                existing.user_id = user_id
                existing.platform = platform
                existing.device_name = device_name
                existing.last_active_at = now
                saved = await notification_repo.save_device(existing)
            else:
                device = DeviceToken(
                    school_id=school_id,
                    user_id=user_id,
                    token=token,
                    platform=platform,
                    device_name=device_name,
                    last_active_at=now,
                )
                saved = await notification_repo.save_device(device)

            await uow.commit()
            return saved

    async def deregister_device(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        device_id: uuid.UUID,
    ) -> DeviceToken | None:
        async with UnitOfWork(self.db) as uow:
            notification_repo = NotificationRepository(uow.session)
            device = await notification_repo.find_device(
                school_id=school_id,
                user_id=user_id,
                device_id=device_id,
            )
            if device is None:
                return None
            await notification_repo.delete_device(device)
            await uow.commit()
            return device

    async def send_push_for_notification(
        self,
        *,
        notification: Notification,
        silent: bool = False,
    ) -> NotificationDelivery:
        delivery = await self.delivery_repo.get_delivery(
            notification_id=notification.id,
            channel="push",
        )
        if delivery is None:
            delivery = NotificationDelivery(
                notification_id=notification.id,
                school_id=notification.school_id,
                channel="push",
                status=DeliveryStatus.QUEUED.value,
            )

        devices = await self.notification_repo.list_push_devices_for_user(
            school_id=notification.school_id,
            user_id=notification.parent_id,
        )
        if not devices:
            delivery.status = DeliveryStatus.FAILED.value
            delivery.last_error = "No registered devices"
            return delivery

        app = self._ensure_firebase_app()
        if app is None or messaging is None:
            delivery.status = DeliveryStatus.FAILED.value
            delivery.last_error = "Firebase is not configured"
            return delivery

        data = {
            "id": str(notification.id),
            "type": notification.event_ref or "notification_created",
            "route": notification.action_url or "/notifications",
            "category": notification.category,
            "priority": notification.priority,
        }
        if notification.action_payload:
            data.update(
                {
                    f"payload_{key}": str(value)
                    for key, value in notification.action_payload.items()
                }
            )

        last_error: str | None = None
        for device in devices:
            try:
                message = self._build_message(
                    token=device.token,
                    title=notification.title,
                    body=notification.body,
                    data=data,
                    silent=silent,
                    platform=device.platform,
                )
                response = await self._send_with_retry(message)
                delivery.status = DeliveryStatus.SENT.value
                delivery.provider_message_id = response
                delivery.delivered_at = _utc_now()
                delivery.last_error = None
                return delivery
            except Exception as exc:  # pragma: no cover - network/provider failures
                last_error = str(exc)
                logger.warning(
                    "Push send failed for notification %s on device %s",
                    notification.id,
                    device.id,
                    exc_info=True,
                )

        delivery.status = DeliveryStatus.FAILED.value
        delivery.last_error = last_error
        return delivery

    def _ensure_firebase_app(self):
        global _firebase_app

        if firebase_admin is None:
            return None
        if _firebase_app is not None:
            return _firebase_app

        if settings.firebase_service_account_path:
            cred_path = Path(settings.firebase_service_account_path)
            if cred_path.exists():
                _firebase_app = firebase_admin.initialize_app(
                    credentials.Certificate(str(cred_path)),
                    {"projectId": settings.firebase_project_id or None},
                )
                return _firebase_app

        try:
            _firebase_app = firebase_admin.get_app()
            return _firebase_app
        except Exception:
            return None

    def _build_message(
        self,
        *,
        token: str,
        title: str,
        body: str | None,
        data: dict[str, str],
        silent: bool,
        platform: str,
    ):
        if messaging is None:  # pragma: no cover
            raise RuntimeError("firebase_admin.messaging is unavailable")

        apns_config = messaging.APNSConfig(
            headers={
                "apns-priority": "5" if silent else "10",
            },
            payload=messaging.APNSPayload(
                aps=messaging.Aps(
                    content_available=silent,
                    sound=None if silent else "default",
                )
            ),
        )

        android_config = messaging.AndroidConfig(
            priority="high",
            notification=None
            if silent
            else messaging.AndroidNotification(
                channel_id="ecole_push_channel",
                sound="default",
            ),
        )

        notification = None
        if not silent:
            notification = messaging.Notification(title=title, body=body)

        return messaging.Message(
            token=token,
            data=data,
            notification=notification,
            android=android_config,
            apns=apns_config if platform == "ios" else None,
        )

    async def _send_with_retry(self, message) -> str:
        max_attempts = max(1, settings.push_retry_max_attempts)
        base_delay = max(1, settings.push_retry_base_delay_seconds)
        last_exc: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                return await asyncio.to_thread(messaging.send, message)
            except Exception as exc:  # pragma: no cover - provider failure
                last_exc = exc
                if attempt >= max_attempts:
                    break
                await asyncio.sleep(base_delay * (2 ** (attempt - 1)))

        raise RuntimeError(str(last_exc) if last_exc else "Push send failed")
