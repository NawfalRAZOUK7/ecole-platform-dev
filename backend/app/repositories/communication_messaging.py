"""Repository helpers for messaging conversations and parent feed."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.filtering import FilterSpec, SortSpec, apply_filters, apply_sort
from app.core.response import decode_cursor
from app.core.search import apply_search
from app.models.com import (
    Conversation,
    ConversationParticipant,
    Message,
    MessageReadReceipt,
    ParentFeedItem,
)
from app.models.erp import Enrollment
from app.models.iam import Membership, ParentChildLink, User
from app.repositories.base import BaseRepository


class MessagingRepository(BaseRepository):
    """Data access for communication workflows."""

    async def get_user(
        self,
        user_id: uuid.UUID,
    ) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_membership(
        self,
        *,
        user_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> Membership | None:
        result = await self.db.execute(
            select(Membership).where(
                Membership.user_id == user_id,
                Membership.school_id == school_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_membership_role(
        self,
        *,
        user_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> str | None:
        result = await self.db.execute(
            select(Membership.role_code).where(
                Membership.user_id == user_id,
                Membership.school_id == school_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_parent_child_ids(
        self,
        *,
        parent_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> set[uuid.UUID]:
        result = await self.db.execute(
            select(ParentChildLink.child_user_id).where(
                ParentChildLink.parent_user_id == parent_id,
                ParentChildLink.school_id == school_id,
                ParentChildLink.status == "active",
            )
        )
        return set(result.scalars().all())

    async def list_class_ids_for_students(
        self,
        *,
        student_ids: set[uuid.UUID],
        school_id: uuid.UUID,
    ) -> set[uuid.UUID]:
        if not student_ids:
            return set()
        result = await self.db.execute(
            select(Enrollment.class_id).where(
                Enrollment.student_id.in_(student_ids),
                Enrollment.school_id == school_id,
                Enrollment.status == "active",
            )
        )
        return set(result.scalars().all())

    async def list_student_ids_for_classes(
        self,
        *,
        class_ids: set[uuid.UUID],
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

    async def list_teacher_ids_for_classes(
        self,
        *,
        class_ids: set[uuid.UUID],
        school_id: uuid.UUID,
    ) -> set[uuid.UUID]:
        if not class_ids:
            return set()
        from app.models.erp import TeacherAssignment

        result = await self.db.execute(
            select(TeacherAssignment.teacher_id).where(
                TeacherAssignment.class_id.in_(class_ids),
                TeacherAssignment.school_id == school_id,
            )
        )
        return set(result.scalars().all())

    async def list_teacher_class_ids(
        self,
        *,
        teacher_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> set[uuid.UUID]:
        from app.models.erp import TeacherAssignment

        result = await self.db.execute(
            select(TeacherAssignment.class_id).where(
                TeacherAssignment.teacher_id == teacher_id,
                TeacherAssignment.school_id == school_id,
            )
        )
        return set(result.scalars().all())

    async def list_parent_ids_for_students(
        self,
        *,
        student_ids: set[uuid.UUID],
        school_id: uuid.UUID,
    ) -> set[uuid.UUID]:
        if not student_ids:
            return set()
        result = await self.db.execute(
            select(ParentChildLink.parent_user_id).where(
                ParentChildLink.child_user_id.in_(student_ids),
                ParentChildLink.school_id == school_id,
                ParentChildLink.status == "active",
            )
        )
        return set(result.scalars().all())

    async def create_conversation(
        self,
        **kwargs: Any,
    ) -> Conversation:
        conversation = Conversation(**kwargs)
        self.db.add(conversation)
        await self.db.flush()
        return conversation

    async def create_conversation_participants(
        self,
        participants_data: list[dict[str, Any]],
    ) -> list[ConversationParticipant]:
        participants = [ConversationParticipant(**data) for data in participants_data]
        if participants:
            self.db.add_all(participants)
            await self.db.flush()
        return participants

    async def get_conversation(
        self,
        conversation_id: uuid.UUID,
    ) -> Conversation | None:
        result = await self.db.execute(
            select(Conversation)
            .options(selectinload(Conversation.participants))
            .where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def create_message(
        self,
        **kwargs: Any,
    ) -> Message:
        message = Message(**kwargs)
        self.db.add(message)
        await self.db.flush()
        return message

    async def search_messages(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        query_text: str,
        limit: int,
    ) -> list[Message]:
        conversation_ids = (
            select(ConversationParticipant.conversation_id)
            .where(ConversationParticipant.user_id == user_id)
            .scalar_subquery()
        )
        ts_query = func.plainto_tsquery("simple", query_text)
        ts_vector = func.to_tsvector("simple", func.coalesce(Message.body, ""))
        rank = func.ts_rank(ts_vector, ts_query)
        result = await self.db.execute(
            select(Message)
            .join(Conversation, Conversation.id == Message.conversation_id)
            .where(
                Conversation.school_id == school_id,
                Message.conversation_id.in_(conversation_ids),
                ts_vector.op("@@")(ts_query),
            )
            .order_by(rank.desc(), Message.sent_at.desc(), Message.id.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_conversations_for_user(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[tuple[Conversation, datetime | None]], bool]:
        my_conversation_ids = (
            select(ConversationParticipant.conversation_id)
            .where(ConversationParticipant.user_id == user_id)
            .scalar_subquery()
        )
        last_message_subquery = (
            select(
                Message.conversation_id,
                func.max(Message.sent_at).label("last_sent"),
            )
            .group_by(Message.conversation_id)
            .subquery()
        )
        query = (
            select(Conversation, last_message_subquery.c.last_sent)
            .options(selectinload(Conversation.participants))
            .outerjoin(
                last_message_subquery,
                Conversation.id == last_message_subquery.c.conversation_id,
            )
            .where(
                Conversation.id.in_(my_conversation_ids),
                Conversation.school_id == school_id,
            )
            .order_by(
                last_message_subquery.c.last_sent.desc().nullslast(),
                Conversation.created_at.desc(),
            )
        )
        if cursor:
            cursor_id, _ = decode_cursor(cursor)
            query = query.where(Conversation.id != cursor_id)

        result = await self.db.execute(query.limit(limit + 1))
        rows = list(result.all())
        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]
        return [(row[0], row[1]) for row in rows], has_more

    async def get_message_sent_at(
        self,
        message_id: uuid.UUID,
    ) -> datetime | None:
        result = await self.db.execute(
            select(Message.sent_at).where(Message.id == message_id)
        )
        return result.scalar_one_or_none()

    async def list_conversation_messages(
        self,
        *,
        conversation_id: uuid.UUID,
        before_sent_at: datetime | None,
        limit: int,
    ) -> tuple[list[Message], bool]:
        query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.sent_at.desc())
        )
        if before_sent_at:
            query = query.where(Message.sent_at < before_sent_at)
        result = await self.db.execute(query.limit(limit + 1))
        items = list(result.scalars().all())
        has_more = len(items) > limit
        if has_more:
            items = items[:limit]
        return items, has_more

    async def get_message_in_conversation(
        self,
        *,
        conversation_id: uuid.UUID,
        message_id: uuid.UUID,
    ) -> Message | None:
        result = await self.db.execute(
            select(Message).where(
                Message.id == message_id,
                Message.conversation_id == conversation_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_unread_message_ids(
        self,
        *,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        up_to_sent_at: datetime,
    ) -> list[uuid.UUID]:
        result = await self.db.execute(
            select(Message.id).where(
                Message.conversation_id == conversation_id,
                Message.sent_at <= up_to_sent_at,
                Message.sender_id != user_id,
                ~Message.id.in_(
                    select(MessageReadReceipt.message_id).where(
                        MessageReadReceipt.user_id == user_id
                    )
                ),
            )
        )
        return list(result.scalars().all())

    async def create_read_receipts(
        self,
        receipts_data: list[dict[str, Any]],
    ) -> list[MessageReadReceipt]:
        receipts = [MessageReadReceipt(**data) for data in receipts_data]
        if receipts:
            self.db.add_all(receipts)
            await self.db.flush()
        return receipts

    async def list_read_receipts(
        self,
        *,
        conversation_id: uuid.UUID,
        message_id: uuid.UUID | None,
    ) -> list[MessageReadReceipt]:
        query = (
            select(MessageReadReceipt)
            .join(Message, MessageReadReceipt.message_id == Message.id)
            .where(Message.conversation_id == conversation_id)
        )
        if message_id:
            query = query.where(MessageReadReceipt.message_id == message_id)
        query = query.order_by(MessageReadReceipt.read_at.desc()).limit(200)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_parent_feed_items(
        self,
        *,
        school_id: uuid.UUID,
        parent_id: uuid.UUID,
        student_id: uuid.UUID | None,
        filters: FilterSpec,
        sort: SortSpec,
        search: str | None,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[ParentFeedItem], bool]:
        query = select(ParentFeedItem).where(
            ParentFeedItem.school_id == school_id,
            ParentFeedItem.parent_id == parent_id,
        )
        if student_id:
            query = query.where(ParentFeedItem.student_id == student_id)

        query = apply_filters(query, ParentFeedItem, filters)
        if search:
            query = apply_search(query, ParentFeedItem, search)
        query = apply_sort(
            query,
            ParentFeedItem,
            sort,
            default_column=ParentFeedItem.created_at.desc(),
        )

        if cursor:
            last_id, _ = decode_cursor(cursor)
            query = query.where(ParentFeedItem.id > last_id)

        result = await self.db.execute(query.limit(limit + 1))
        items = list(result.scalars().all())
        has_more = len(items) > limit
        if has_more:
            items = items[:limit]
        return items, has_more
