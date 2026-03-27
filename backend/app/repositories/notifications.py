"""Repositories for the Phase 13 notification center."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Iterable, Sequence

from sqlalchemy import and_, delete, distinct, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.response import decode_cursor, encode_cursor
from app.models.com import (
    DeviceToken,
    Notification,
    NotificationDelivery,
    NotificationPreference,
)
from app.models.erp import Enrollment, TeacherAssignment
from app.models.iam import Membership, ParentChildLink, User


class NotificationRepository:
    """Data access for notification entities."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_notifications(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
        category: str | None = None,
        channel: str | None = None,
        read: bool | None = None,
        from_dt: datetime | None = None,
        to_dt: datetime | None = None,
        cursor: str | None = None,
        limit: int = 20,
    ) -> tuple[list[Notification], str | None, bool]:
        query = (
            select(Notification)
            .options(selectinload(Notification.deliveries))
            .where(
                Notification.school_id == school_id,
                Notification.deleted_at.is_(None),
            )
        )

        if role not in {"ADM", "DIR"}:
            query = query.where(Notification.parent_id == user_id)

        if category:
            query = query.where(Notification.category == category)

        if read is True:
            query = query.where(Notification.read_at.is_not(None))
        elif read is False:
            query = query.where(Notification.read_at.is_(None))

        if from_dt:
            query = query.where(Notification.created_at >= from_dt)
        if to_dt:
            query = query.where(Notification.created_at <= to_dt)

        if channel:
            query = query.where(
                Notification.deliveries.any(NotificationDelivery.channel == channel)
            )

        query = query.order_by(Notification.created_at.desc(), Notification.id.desc())

        if cursor:
            last_id, last_created_at = decode_cursor(cursor)
            if last_created_at:
                cursor_created_at = datetime.fromisoformat(last_created_at)
                query = query.where(
                    or_(
                        Notification.created_at < cursor_created_at,
                        and_(
                            Notification.created_at == cursor_created_at,
                            Notification.id < last_id,
                        ),
                    )
                )

        result = await self.db.execute(query.limit(limit + 1))
        items = list(result.scalars().all())
        has_more = len(items) > limit
        if has_more:
            items = items[:limit]

        next_cursor = None
        if items and has_more:
            last_item = items[-1]
            next_cursor = encode_cursor(last_item.id, last_item.created_at.isoformat())
        return items, next_cursor, has_more

    async def get_notification(
        self,
        notification_id: uuid.UUID,
    ) -> Notification | None:
        result = await self.db.execute(
            select(Notification)
            .options(selectinload(Notification.deliveries))
            .where(Notification.id == notification_id)
        )
        return result.scalar_one_or_none()

    async def count_unread(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
    ) -> int:
        query = select(func.count(Notification.id)).where(
            Notification.school_id == school_id,
            Notification.deleted_at.is_(None),
            Notification.read_at.is_(None),
        )
        if role not in {"ADM", "DIR"}:
            query = query.where(Notification.parent_id == user_id)
        result = await self.db.execute(query)
        return int(result.scalar_one() or 0)

    async def mark_all_read(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        read_at: datetime,
    ) -> int:
        result = await self.db.execute(
            select(Notification).where(
                Notification.school_id == school_id,
                Notification.parent_id == user_id,
                Notification.deleted_at.is_(None),
                Notification.read_at.is_(None),
            )
        )
        notifications = list(result.scalars().all())
        for notification in notifications:
            notification.read_at = read_at
        return len(notifications)

    async def create_notifications(
        self,
        notifications: Sequence[Notification],
    ) -> list[Notification]:
        self.db.add_all(notifications)
        await self.db.flush()
        return list(notifications)

    async def create_deliveries(
        self,
        deliveries: Sequence[NotificationDelivery],
    ) -> list[NotificationDelivery]:
        if deliveries:
            self.db.add_all(deliveries)
            await self.db.flush()
        return list(deliveries)

    async def hard_delete(self, notification: Notification) -> None:
        await self.db.delete(notification)

    async def list_preferences(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[NotificationPreference]:
        result = await self.db.execute(
            select(NotificationPreference)
            .where(
                NotificationPreference.school_id == school_id,
                NotificationPreference.user_id == user_id,
            )
            .order_by(
                NotificationPreference.category.asc(),
                NotificationPreference.channel.asc(),
            )
        )
        return list(result.scalars().all())

    async def upsert_preferences(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        preferences: Iterable[NotificationPreference],
    ) -> list[NotificationPreference]:
        for preference in preferences:
            preference.school_id = school_id
            preference.user_id = user_id
            self.db.add(preference)
        await self.db.flush()
        return await self.list_preferences(school_id=school_id, user_id=user_id)

    async def find_preference(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        channel: str,
        category: str,
    ) -> NotificationPreference | None:
        result = await self.db.execute(
            select(NotificationPreference).where(
                NotificationPreference.school_id == school_id,
                NotificationPreference.user_id == user_id,
                NotificationPreference.channel == channel,
                NotificationPreference.category == category,
            )
        )
        return result.scalar_one_or_none()

    async def list_devices(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[DeviceToken]:
        result = await self.db.execute(
            select(DeviceToken)
            .where(
                DeviceToken.school_id == school_id,
                DeviceToken.user_id == user_id,
            )
            .order_by(DeviceToken.last_active_at.desc())
        )
        return list(result.scalars().all())

    async def find_device(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        device_id: uuid.UUID,
    ) -> DeviceToken | None:
        result = await self.db.execute(
            select(DeviceToken).where(
                DeviceToken.id == device_id,
                DeviceToken.school_id == school_id,
                DeviceToken.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def find_device_by_token(self, token: str) -> DeviceToken | None:
        result = await self.db.execute(
            select(DeviceToken).where(DeviceToken.token == token)
        )
        return result.scalar_one_or_none()

    async def save_device(self, device: DeviceToken) -> DeviceToken:
        self.db.add(device)
        await self.db.flush()
        return device

    async def delete_device(self, device: DeviceToken) -> None:
        await self.db.delete(device)

    async def list_push_devices_for_user(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[DeviceToken]:
        result = await self.db.execute(
            select(DeviceToken).where(
                DeviceToken.school_id == school_id,
                DeviceToken.user_id == user_id,
            )
        )
        return list(result.scalars().all())

    async def list_user_contacts(
        self,
        user_ids: Sequence[uuid.UUID],
    ) -> dict[uuid.UUID, User]:
        if not user_ids:
            return {}
        result = await self.db.execute(select(User).where(User.id.in_(user_ids)))
        users = list(result.scalars().all())
        return {user.id: user for user in users}

    async def list_members_by_roles(
        self,
        *,
        school_id: uuid.UUID,
        role_codes: Sequence[str],
    ) -> set[uuid.UUID]:
        if not role_codes:
            return set()
        result = await self.db.execute(
            select(distinct(Membership.user_id)).where(
                Membership.school_id == school_id,
                Membership.role_code.in_(role_codes),
                Membership.status == "active",
            )
        )
        return set(result.scalars().all())

    async def list_students_for_classes(
        self,
        *,
        school_id: uuid.UUID,
        class_ids: Sequence[uuid.UUID],
    ) -> set[uuid.UUID]:
        if not class_ids:
            return set()
        result = await self.db.execute(
            select(distinct(Enrollment.student_id)).where(
                Enrollment.school_id == school_id,
                Enrollment.class_id.in_(class_ids),
                Enrollment.status == "active",
            )
        )
        return set(result.scalars().all())

    async def list_parents_for_students(
        self,
        *,
        school_id: uuid.UUID,
        student_ids: Sequence[uuid.UUID],
    ) -> set[uuid.UUID]:
        if not student_ids:
            return set()
        result = await self.db.execute(
            select(distinct(ParentChildLink.parent_user_id)).where(
                ParentChildLink.school_id == school_id,
                ParentChildLink.child_user_id.in_(student_ids),
                ParentChildLink.status == "active",
            )
        )
        return set(result.scalars().all())

    async def list_teachers_for_classes(
        self,
        *,
        school_id: uuid.UUID,
        class_ids: Sequence[uuid.UUID],
    ) -> set[uuid.UUID]:
        if not class_ids:
            return set()
        result = await self.db.execute(
            select(distinct(TeacherAssignment.teacher_id)).where(
                TeacherAssignment.school_id == school_id,
                TeacherAssignment.class_id.in_(class_ids),
            )
        )
        return set(result.scalars().all())

    async def list_unread_digest_notifications(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        since: datetime | None = None,
    ) -> list[Notification]:
        query = (
            select(Notification)
            .options(selectinload(Notification.deliveries))
            .where(
                Notification.school_id == school_id,
                Notification.parent_id == user_id,
                Notification.deleted_at.is_(None),
                Notification.read_at.is_(None),
            )
            .order_by(Notification.created_at.desc())
        )
        if since:
            query = query.where(Notification.created_at >= since)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_users_with_digest_preferences(
        self,
        *,
        school_id: uuid.UUID | None = None,
        digest_frequency: str,
    ) -> list[NotificationPreference]:
        query = select(NotificationPreference).where(
            NotificationPreference.channel == "email",
            NotificationPreference.digest_frequency == digest_frequency,
            NotificationPreference.enabled.is_(True),
        )
        if school_id:
            query = query.where(NotificationPreference.school_id == school_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def remove_user_notifications_cache(self, user_id: uuid.UUID) -> str:
        return f"notifications:unread-count:{user_id}"


class NotificationDeliveryRepository:
    """Focused helpers for delivery status persistence."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_delivery(
        self,
        *,
        notification_id: uuid.UUID,
        channel: str,
    ) -> NotificationDelivery | None:
        result = await self.db.execute(
            select(NotificationDelivery).where(
                NotificationDelivery.notification_id == notification_id,
                NotificationDelivery.channel == channel,
            )
        )
        return result.scalar_one_or_none()

    async def list_deliveries_for_notification(
        self,
        notification_id: uuid.UUID,
    ) -> list[NotificationDelivery]:
        result = await self.db.execute(
            select(NotificationDelivery).where(
                NotificationDelivery.notification_id == notification_id
            )
        )
        return list(result.scalars().all())

    async def delete_deliveries_for_notification(
        self,
        notification_id: uuid.UUID,
    ) -> None:
        await self.db.execute(
            delete(NotificationDelivery).where(
                NotificationDelivery.notification_id == notification_id
            )
        )
