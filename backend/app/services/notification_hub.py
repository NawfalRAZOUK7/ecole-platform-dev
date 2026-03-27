"""Phase 13 notification hub service."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError, NotFoundError
from app.core.redis import redis_client
from app.models.com import (
    DeliveryChannel,
    DeliveryStatus,
    DigestFrequency,
    Notification,
    NotificationCategory,
    NotificationDelivery,
    NotificationPreference,
    NotificationPriority,
)
from app.models.iam import User
from app.repositories.notifications import NotificationRepository
from app.schemas.notifications import (
    NotificationBatchRequest,
    NotificationHistoryItem,
    NotificationPreferenceItem,
)
from app.services.email_digest import EmailDigestService
from app.services.push_config import PushConfigService
from app.services.realtime import publish_event
from app.services.sms import sms_service

DEFAULT_CHANNELS: tuple[str, ...] = (
    DeliveryChannel.IN_APP.value,
    DeliveryChannel.PUSH.value,
    DeliveryChannel.EMAIL.value,
    DeliveryChannel.SMS.value,
)
DEFAULT_CATEGORIES: tuple[str, ...] = (
    NotificationCategory.ACADEMIC.value,
    NotificationCategory.BILLING.value,
    NotificationCategory.ATTENDANCE.value,
    NotificationCategory.SYSTEM.value,
    NotificationCategory.ANNOUNCEMENT.value,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class NotificationHubService:
    """Notification registry, routing engine, and notification lifecycle."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = NotificationRepository(db)
        self.push_service = PushConfigService(db)
        self.email_service = EmailDigestService(db)

    async def list_notifications(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
        category: str | None,
        channel: str | None,
        read: bool | None,
        from_dt: datetime | None,
        to_dt: datetime | None,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[dict], str | None, bool]:
        notifications, next_cursor, has_more = await self.repo.list_notifications(
            school_id=school_id,
            user_id=user_id,
            role=role,
            category=category,
            channel=channel,
            read=read,
            from_dt=from_dt,
            to_dt=to_dt,
            cursor=cursor,
            limit=limit,
        )
        return (
            [self.serialize_notification(notification) for notification in notifications],
            next_cursor,
            has_more,
        )

    async def list_preferences(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[dict]:
        prefs = await self.ensure_default_preferences(
            school_id=school_id,
            user_id=user_id,
        )
        return [
            NotificationPreferenceItem(
                channel=pref.channel,
                category=pref.category,
                enabled=pref.enabled,
                digest_frequency=pref.digest_frequency,
            ).model_dump()
            for pref in prefs
        ]

    async def update_preferences(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        items: Iterable[NotificationPreferenceItem],
    ) -> list[dict]:
        await self.ensure_default_preferences(school_id=school_id, user_id=user_id)

        preferences: list[NotificationPreference] = []
        for item in items:
            pref = await self.repo.find_preference(
                school_id=school_id,
                user_id=user_id,
                channel=item.channel,
                category=item.category,
            )
            if pref is None:
                pref = NotificationPreference(
                    school_id=school_id,
                    user_id=user_id,
                    channel=item.channel,
                    category=item.category,
                )
            pref.enabled = item.enabled
            pref.digest_frequency = item.digest_frequency
            preferences.append(pref)

        updated = await self.repo.upsert_preferences(
            school_id=school_id,
            user_id=user_id,
            preferences=preferences,
        )
        return [
            NotificationPreferenceItem(
                channel=pref.channel,
                category=pref.category,
                enabled=pref.enabled,
                digest_frequency=pref.digest_frequency,
            ).model_dump()
            for pref in updated
        ]

    async def unread_count(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
    ) -> tuple[int, bool]:
        cache_key = self._unread_cache_key(user_id)
        cached = await redis_client.get(cache_key)
        if cached is not None:
            return int(cached), True

        count = await self.repo.count_unread(
            school_id=school_id,
            user_id=user_id,
            role=role,
        )
        await redis_client.set(cache_key, str(count), ex=30)
        return count, False

    async def mark_read(
        self,
        *,
        notification_id: uuid.UUID,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
        read: bool,
    ) -> dict:
        notification = await self._get_scoped_notification(
            notification_id=notification_id,
            school_id=school_id,
            user_id=user_id,
            role=role,
        )
        notification.read_at = _utc_now() if read else None
        await self.repo.save_notification(notification)
        await self.invalidate_unread_count(notification.parent_id)
        return {
            "id": str(notification.id),
            "read": notification.is_read,
            "read_at": notification.read_at.isoformat() if notification.read_at else None,
            "deleted": False,
        }

    async def mark_all_read(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict:
        updated = await self.repo.mark_all_read(
            school_id=school_id,
            user_id=user_id,
            read_at=_utc_now(),
        )
        await self.invalidate_unread_count(user_id)
        return {
            "updated": updated,
            "read": True,
        }

    async def delete_notification(
        self,
        *,
        notification_id: uuid.UUID,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
        hard_delete: bool,
    ) -> dict:
        notification = await self._get_scoped_notification(
            notification_id=notification_id,
            school_id=school_id,
            user_id=user_id,
            role=role,
        )
        if hard_delete:
            if role != "ADM":
                raise AuthorizationError(
                    "Only administrators can hard delete notifications",
                    error_code="ERR-COM-403",
                )
            await self.repo.hard_delete(notification)
        else:
            notification.deleted_at = _utc_now()
            await self.repo.save_notification(notification)
        await self.invalidate_unread_count(notification.parent_id)
        return {
            "id": str(notification.id),
            "read": notification.is_read,
            "deleted": True,
            "hard_deleted": hard_delete,
        }

    async def create_batch_notifications(
        self,
        *,
        school_id: uuid.UUID,
        request: NotificationBatchRequest,
    ) -> dict:
        recipient_ids = await self.resolve_recipient_ids(
            school_id=school_id,
            user_ids=request.user_ids,
            role_codes=request.role_codes,
            class_ids=request.class_ids,
        )
        users = await self.repo.list_user_contacts(list(recipient_ids))

        routed_channels: set[str] = set()
        notifications: list[Notification] = []
        deliveries: list[NotificationDelivery] = []
        for recipient_id in recipient_ids:
            idempotency_key = request.idempotency_key or (
                f"batch:{request.category}:{request.title}:{recipient_id}:{uuid.uuid4()}"
            )
            notification = Notification(
                school_id=school_id,
                parent_id=recipient_id,
                event_ref=request.event_ref,
                idempotency_key=idempotency_key,
                title=request.title,
                body=request.body,
                category=request.category,
                priority=request.priority,
                action_url=request.action_url,
                action_payload=request.action_payload,
            )
            notifications.append(notification)

        await self.repo.create_notifications(notifications)

        for notification in notifications:
            user = users.get(notification.parent_id)
            channels = await self.route_channels(
                school_id=school_id,
                user_id=notification.parent_id,
                category=notification.category,
                priority=notification.priority,
                preferred_channels=request.channels,
            )
            routed_channels.update(channels)
            deliveries.extend(
                await self._deliver_notification(
                    notification=notification,
                    channels=channels,
                    user=user,
                    silent_push=request.silent_push,
                )
            )

        if deliveries:
            await self.repo.create_deliveries(deliveries)

        return {
            "requested_recipients": len(recipient_ids),
            "notifications_created": len(notifications),
            "routed_channels": sorted(routed_channels),
        }

    async def create_single_notification(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        title: str,
        body: str | None,
        category: str,
        priority: str = NotificationPriority.NORMAL.value,
        action_url: str | None = None,
        action_payload: dict | None = None,
        event_ref: str | None = None,
        preferred_channels: list[str] | None = None,
        idempotency_key: str | None = None,
        silent_push: bool = False,
    ) -> Notification:
        notification = Notification(
            school_id=school_id,
            parent_id=user_id,
            event_ref=event_ref,
            idempotency_key=idempotency_key
            or f"{category}:{user_id}:{uuid.uuid4()}",
            title=title,
            body=body,
            category=category,
            priority=priority,
            action_url=action_url,
            action_payload=action_payload,
        )
        await self.repo.create_notifications([notification])
        users = await self.repo.list_user_contacts([user_id])
        channels = await self.route_channels(
            school_id=school_id,
            user_id=user_id,
            category=category,
            priority=priority,
            preferred_channels=preferred_channels,
        )
        deliveries = await self._deliver_notification(
            notification=notification,
            channels=channels,
            user=users.get(user_id),
            silent_push=silent_push,
        )
        if deliveries:
            await self.repo.create_deliveries(deliveries)
        return notification

    async def resolve_recipient_ids(
        self,
        *,
        school_id: uuid.UUID,
        user_ids: Iterable[uuid.UUID],
        role_codes: Iterable[str],
        class_ids: Iterable[uuid.UUID],
    ) -> set[uuid.UUID]:
        recipient_ids = set(user_ids)
        role_codes = list(role_codes)
        class_ids = list(class_ids)

        if role_codes:
            recipient_ids.update(
                await self.repo.list_members_by_roles(
                    school_id=school_id,
                    role_codes=role_codes,
                )
            )

        if class_ids:
            students = await self.repo.list_students_for_classes(
                school_id=school_id,
                class_ids=class_ids,
            )
            teachers = await self.repo.list_teachers_for_classes(
                school_id=school_id,
                class_ids=class_ids,
            )
            parents = await self.repo.list_parents_for_students(
                school_id=school_id,
                student_ids=list(students),
            )

            if not role_codes or "STD" in role_codes:
                recipient_ids.update(students)
            if not role_codes or "TCH" in role_codes:
                recipient_ids.update(teachers)
            if not role_codes or "PAR" in role_codes:
                recipient_ids.update(parents)

        return recipient_ids

    async def ensure_default_preferences(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[NotificationPreference]:
        prefs = await self.repo.list_preferences(school_id=school_id, user_id=user_id)
        existing = {(pref.channel, pref.category) for pref in prefs}
        created = False

        for category in DEFAULT_CATEGORIES:
            for channel in DEFAULT_CHANNELS:
                if (channel, category) in existing:
                    continue
                prefs.append(
                    NotificationPreference(
                        school_id=school_id,
                        user_id=user_id,
                        channel=channel,
                        category=category,
                        enabled=self._default_enabled(channel),
                        digest_frequency=DigestFrequency.DAILY.value
                        if channel == DeliveryChannel.EMAIL.value
                        else DigestFrequency.OFF.value,
                    )
                )
                created = True
        if created:
            await self.repo.upsert_preferences(
                school_id=school_id,
                user_id=user_id,
                preferences=prefs,
            )
        return await self.repo.list_preferences(school_id=school_id, user_id=user_id)

    async def route_channels(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        category: str,
        priority: str,
        preferred_channels: list[str] | None = None,
    ) -> list[str]:
        prefs = await self.ensure_default_preferences(school_id=school_id, user_id=user_id)
        enabled_channels = {
            pref.channel
            for pref in prefs
            if pref.category == category and pref.enabled
        }

        if preferred_channels:
            allowed = [channel for channel in preferred_channels if channel in enabled_channels]
            if allowed:
                return self._normalize_channels(allowed)

        channels = [DeliveryChannel.IN_APP.value]
        if priority in {
            NotificationPriority.HIGH.value,
            NotificationPriority.CRITICAL.value,
        } and DeliveryChannel.PUSH.value in enabled_channels:
            channels.append(DeliveryChannel.PUSH.value)

        if priority == NotificationPriority.CRITICAL.value:
            if DeliveryChannel.EMAIL.value in enabled_channels:
                channels.append(DeliveryChannel.EMAIL.value)
            if DeliveryChannel.SMS.value in enabled_channels:
                channels.append(DeliveryChannel.SMS.value)
        elif (
            priority == NotificationPriority.NORMAL.value
            and category == NotificationCategory.BILLING.value
            and DeliveryChannel.EMAIL.value in enabled_channels
        ):
            channels.append(DeliveryChannel.EMAIL.value)

        channels = [channel for channel in channels if channel in enabled_channels]
        if not channels:
            channels = [DeliveryChannel.IN_APP.value]
        return self._normalize_channels(channels)

    async def invalidate_unread_count(self, user_id: uuid.UUID) -> None:
        await redis_client.delete(self._unread_cache_key(user_id))

    def serialize_notification(self, notification: Notification) -> dict:
        channels = sorted({delivery.channel for delivery in notification.deliveries})
        return NotificationHistoryItem(
            id=str(notification.id),
            school_id=str(notification.school_id),
            user_id=str(notification.parent_id),
            parent_id=str(notification.parent_id),
            event_ref=notification.event_ref,
            title=notification.title,
            body=notification.body,
            category=notification.category,
            priority=notification.priority,
            action_url=notification.action_url,
            action_payload=notification.action_payload,
            is_read=notification.is_read,
            read_at=notification.read_at.isoformat() if notification.read_at else None,
            deleted_at=notification.deleted_at.isoformat()
            if notification.deleted_at
            else None,
            created_at=notification.created_at.isoformat(),
            updated_at=notification.updated_at.isoformat()
            if notification.updated_at
            else None,
            channels=channels,
        ).model_dump()

    async def _deliver_notification(
        self,
        *,
        notification: Notification,
        channels: list[str],
        user: User | None,
        silent_push: bool,
    ) -> list[NotificationDelivery]:
        now = _utc_now()
        deliveries: list[NotificationDelivery] = [
            NotificationDelivery(
                notification_id=notification.id,
                school_id=notification.school_id,
                channel=DeliveryChannel.IN_APP.value,
                status=DeliveryStatus.DELIVERED.value,
                delivered_at=now,
            )
        ]

        await self.invalidate_unread_count(notification.parent_id)
        await publish_event(
            notification.parent_id,
            "notification_created",
            {
                "notification_id": str(notification.id),
                "title": notification.title,
                "body": notification.body,
                "category": notification.category,
                "priority": notification.priority,
                "action_url": notification.action_url or "/notifications",
            },
        )

        if DeliveryChannel.PUSH.value in channels:
            deliveries.append(
                await self.push_service.send_push_for_notification(
                    notification=notification,
                    silent=silent_push,
                )
            )

        if DeliveryChannel.EMAIL.value in channels and user is not None:
            deliveries.append(
                await self.email_service.send_notification_email(
                    notification=notification,
                    user=user,
                )
            )

        if (
            DeliveryChannel.SMS.value in channels
            and user is not None
            and user.phone
        ):
            sms_success = await sms_service.send_notification_fallback(
                to=user.phone,
                title=notification.title,
                body=notification.body,
                user_id=user.id,
            )
            deliveries.append(
                NotificationDelivery(
                    notification_id=notification.id,
                    school_id=notification.school_id,
                    channel=DeliveryChannel.SMS.value,
                    status=(
                        DeliveryStatus.SENT.value
                        if sms_success
                        else DeliveryStatus.FAILED.value
                    ),
                    delivered_at=now if sms_success else None,
                    last_error=None if sms_success else "SMS send failed",
                )
            )

        return deliveries

    async def _get_scoped_notification(
        self,
        *,
        notification_id: uuid.UUID,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
    ) -> Notification:
        notification = await self.repo.get_notification(notification_id)
        if notification is None or notification.school_id != school_id:
            raise NotFoundError("Notification not found", error_code="ERR-COM-404")
        if role not in {"ADM", "DIR"} and notification.parent_id != user_id:
            raise NotFoundError("Notification not found", error_code="ERR-COM-404")
        return notification

    def _default_enabled(self, channel: str) -> bool:
        return channel != DeliveryChannel.SMS.value

    def _normalize_channels(self, channels: Iterable[str]) -> list[str]:
        ordered: list[str] = []
        for channel in channels:
            if channel not in ordered:
                ordered.append(channel)
        return ordered

    def _unread_cache_key(self, user_id: uuid.UUID) -> str:
        return f"notifications:unread-count:{user_id}"
