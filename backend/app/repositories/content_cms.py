"""Repository helpers for CMS content, announcements, and review workflows."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select

from app.core.response import decode_cursor
from app.models.com import Announcement, Notification
from app.models.erp import Enrollment
from app.models.iam import Membership, TeacherProfile, User
from app.models.lms import ContentItem, ContentSubmission
from app.repositories.base import BaseRepository


class CMSRepository(BaseRepository):
    """Data access for content management workflows."""

    async def create_content_item(
        self,
        **kwargs: Any,
    ) -> ContentItem:
        content_item = ContentItem(**kwargs)
        self.db.add(content_item)
        await self.db.flush()
        return content_item

    async def save_content_item(
        self,
        content_item: ContentItem,
    ) -> ContentItem:
        self.db.add(content_item)
        await self.db.flush()
        return content_item

    async def get_platform_content(
        self,
        content_id: uuid.UUID,
    ) -> ContentItem | None:
        result = await self.db.execute(
            select(ContentItem).where(
                ContentItem.id == content_id,
                ContentItem.school_id.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_content_item(
        self,
        content_id: uuid.UUID,
    ) -> ContentItem | None:
        result = await self.db.execute(
            select(ContentItem).where(ContentItem.id == content_id)
        )
        return result.scalar_one_or_none()

    async def list_platform_content(
        self,
        *,
        content_type: str | None,
        level_band: str | None,
        subject: str | None,
        status: str | None,
        origin: str | None,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[ContentItem], bool]:
        query = select(ContentItem).where(ContentItem.school_id.is_(None))
        if content_type:
            query = query.where(ContentItem.content_type == content_type)
        if level_band:
            query = query.where(ContentItem.level_band == level_band)
        if subject:
            query = query.where(ContentItem.subject == subject)
        if status:
            query = query.where(ContentItem.status == status)
        if origin:
            query = query.where(ContentItem.origin == origin)
        query = query.order_by(ContentItem.id)
        if cursor:
            last_id, _ = decode_cursor(cursor)
            query = query.where(ContentItem.id > last_id)
        result = await self.db.execute(query.limit(limit + 1))
        items = list(result.scalars().all())
        has_more = len(items) > limit
        if has_more:
            items = items[:limit]
        return items, has_more

    async def list_submission_review_queue(
        self,
        *,
        status: str | None,
        subject: str | None,
        level_band: str | None,
        school_id_filter: uuid.UUID | None,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[tuple[ContentSubmission, ContentItem, User]], bool]:
        query = (
            select(ContentSubmission, ContentItem, User)
            .join(ContentItem, ContentSubmission.content_item_id == ContentItem.id)
            .join(User, ContentSubmission.submitted_by == User.id)
        )
        if status:
            query = query.where(ContentSubmission.status == status)
        if subject:
            query = query.where(ContentItem.subject == subject)
        if level_band:
            query = query.where(ContentItem.level_band == level_band)
        if school_id_filter:
            query = query.where(ContentSubmission.school_id == school_id_filter)
        query = query.order_by(ContentSubmission.id)
        if cursor:
            last_id, _ = decode_cursor(cursor)
            query = query.where(ContentSubmission.id > last_id)
        result = await self.db.execute(query.limit(limit + 1))
        rows = list(result.all())
        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]
        return [(row[0], row[1], row[2]) for row in rows], has_more

    async def get_content_submission(
        self,
        submission_id: uuid.UUID,
    ) -> ContentSubmission | None:
        result = await self.db.execute(
            select(ContentSubmission).where(ContentSubmission.id == submission_id)
        )
        return result.scalar_one_or_none()

    async def save_content_submission(
        self,
        submission: ContentSubmission,
    ) -> ContentSubmission:
        self.db.add(submission)
        await self.db.flush()
        return submission

    async def get_teacher_profile(
        self,
        user_id: uuid.UUID,
    ) -> TeacherProfile | None:
        result = await self.db.execute(
            select(TeacherProfile).where(TeacherProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_notification(
        self,
        **kwargs: Any,
    ) -> Notification:
        notification = Notification(**kwargs)
        self.db.add(notification)
        await self.db.flush()
        return notification

    async def create_notifications(
        self,
        notifications_data: list[dict[str, Any]],
    ) -> list[Notification]:
        notifications = [Notification(**data) for data in notifications_data]
        if notifications:
            self.db.add_all(notifications)
            await self.db.flush()
        return notifications

    async def create_announcement(
        self,
        **kwargs: Any,
    ) -> Announcement:
        announcement = Announcement(**kwargs)
        self.db.add(announcement)
        await self.db.flush()
        return announcement

    async def get_announcement(
        self,
        announcement_id: uuid.UUID,
    ) -> Announcement | None:
        result = await self.db.execute(
            select(Announcement).where(Announcement.id == announcement_id)
        )
        return result.scalar_one_or_none()

    async def save_announcement(
        self,
        announcement: Announcement,
    ) -> Announcement:
        self.db.add(announcement)
        await self.db.flush()
        return announcement

    async def list_announcements(
        self,
        *,
        school_id: uuid.UUID,
        requester_role: str,
        status: str | None,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[Announcement], bool]:
        query = select(Announcement).where(Announcement.school_id == school_id)
        if requester_role not in ("ADM", "DIR"):
            query = query.where(Announcement.status == "PUBLISHED")
            query = query.where(Announcement.target_roles.contains([requester_role]))
        elif status:
            query = query.where(Announcement.status == status)

        query = query.order_by(Announcement.created_at.desc())
        if cursor:
            cursor_id, _ = decode_cursor(cursor)
            cursor_result = await self.db.execute(
                select(Announcement.created_at).where(Announcement.id == cursor_id)
            )
            cursor_created = cursor_result.scalar_one_or_none()
            if cursor_created:
                query = query.where(Announcement.created_at < cursor_created)

        result = await self.db.execute(query.limit(limit + 1))
        items = list(result.scalars().all())
        has_more = len(items) > limit
        if has_more:
            items = items[:limit]
        return items, has_more

    async def list_membership_user_ids_by_roles(
        self,
        *,
        school_id: uuid.UUID,
        roles: list[str],
    ) -> list[uuid.UUID]:
        if not roles:
            return []
        result = await self.db.execute(
            select(Membership.user_id).where(
                Membership.school_id == school_id,
                Membership.role_code.in_(roles),
            )
        )
        return list(result.scalars().all())

    async def list_student_ids_in_classes(
        self,
        *,
        class_ids: list[uuid.UUID],
        school_id: uuid.UUID,
    ) -> set[uuid.UUID]:
        if not class_ids:
            return set()
        result = await self.db.execute(
            select(Enrollment.student_id).where(
                Enrollment.class_id.in_(class_ids),
                Enrollment.school_id == school_id,
                Enrollment.status == "active",
            )
        )
        return set(result.scalars().all())
