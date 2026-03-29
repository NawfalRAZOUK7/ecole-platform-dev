"""Service layer for messaging conversations and parent feed."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.abac import validate_parent_child_access, validate_student_teacher_access
from app.core.dependencies import AuthContext, verify_school_boundary
from app.core.exceptions import NotFoundError, ValidationError
from app.core.filtering import FilterSpec, SortSpec
from app.core.response import decode_cursor, encode_cursor
from app.core.unit_of_work import UnitOfWork
from app.models.com import Conversation, Message
from app.repositories.documents import DocumentsRepository
from app.repositories.messaging import MessagingRepository
from app.schemas.com import (
    ConversationCreateRequest,
    ConversationParticipantResponse,
    ConversationResponse,
    MarkReadRequest,
    MessageCreateRequest,
    MessageResponse,
    ReadReceiptResponse,
)
from app.services.audit import AuditService
from app.services.realtime import publish_message_created


class CommunicationService:
    """Business logic for conversations, messages, and feed."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = MessagingRepository(db)
        self.audit = AuditService(db)

    def _conversation_to_response(
        self,
        conversation: Conversation,
        *,
        last_message_at: str | None = None,
    ) -> dict:
        participants = []
        if conversation.participants:
            participants = [
                ConversationParticipantResponse(
                    user_id=str(participant.user_id),
                    role_in_conversation=participant.role_in_conversation,
                    joined_at=participant.joined_at.isoformat(),
                    muted=participant.muted,
                ).model_dump()
                for participant in conversation.participants
            ]

        return ConversationResponse(
            id=str(conversation.id),
            school_id=str(conversation.school_id),
            type=conversation.type,
            created_by=str(conversation.created_by),
            subject=conversation.subject,
            participants=participants,
            last_message_at=last_message_at,
            created_at=conversation.created_at.isoformat(),
        ).model_dump()

    def _message_to_response(self, message: Message) -> dict:
        return MessageResponse(
            id=str(message.id),
            conversation_id=str(message.conversation_id),
            sender_id=str(message.sender_id),
            body=message.body,
            sent_at=message.sent_at.isoformat(),
            edited_at=message.edited_at.isoformat() if message.edited_at else None,
            created_at=message.created_at.isoformat(),
        ).model_dump()

    async def _verify_participant(
        self,
        *,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Conversation:
        conversation = await self.repo.get_conversation(conversation_id)
        if conversation is None:
            raise NotFoundError("Conversation not found", error_code="ERR-COM-404")

        participant_ids = {participant.user_id for participant in conversation.participants}
        if user_id not in participant_ids:
            raise NotFoundError("Conversation not found", error_code="ERR-COM-404")
        return conversation

    async def _validate_messaging_abac(
        self,
        *,
        auth: AuthContext,
        participant_ids: list[uuid.UUID],
    ) -> None:
        if auth.role in ("ADM", "DIR"):
            return

        if auth.role == "PAR":
            child_ids = await self.repo.list_parent_child_ids(
                parent_id=auth.user_id,
                school_id=auth.school_id,
            )
            if not child_ids:
                raise ValidationError("No linked children found", error_code="ERR-COM-422")

            child_class_ids = await self.repo.list_class_ids_for_students(
                student_ids=child_ids,
                school_id=auth.school_id,
            )
            allowed_teacher_ids = await self.repo.list_teacher_ids_for_classes(
                class_ids=child_class_ids,
                school_id=auth.school_id,
            )

            for participant_id in participant_ids:
                user = await self.repo.get_user(participant_id)
                if user is None:
                    raise NotFoundError("User not found", error_code="ERR-COM-404")
                role = await self.repo.get_membership_role(
                    user_id=participant_id,
                    school_id=auth.school_id,
                )
                if role == "TCH" and participant_id not in allowed_teacher_ids:
                    raise ValidationError(
                        "Cannot message a teacher not assigned to your children's classes",
                        error_code="ERR-COM-403",
                    )
                if role not in ("TCH", "ADM", "DIR"):
                    raise ValidationError(
                        "Parents can only message teachers, admins, or directors",
                        error_code="ERR-COM-403",
                    )
            return

        if auth.role == "TCH":
            teacher_class_ids = await self.repo.list_teacher_class_ids(
                teacher_id=auth.user_id,
                school_id=auth.school_id,
            )
            if not teacher_class_ids:
                raise ValidationError("No class assignments found", error_code="ERR-COM-422")

            class_student_ids = await self.repo.list_student_ids_for_classes(
                class_ids=teacher_class_ids,
                school_id=auth.school_id,
            )
            allowed_parent_ids = await self.repo.list_parent_ids_for_students(
                student_ids=class_student_ids,
                school_id=auth.school_id,
            )

            for participant_id in participant_ids:
                user = await self.repo.get_user(participant_id)
                if user is None:
                    raise NotFoundError("User not found", error_code="ERR-COM-404")
                role = await self.repo.get_membership_role(
                    user_id=participant_id,
                    school_id=auth.school_id,
                )
                if role == "PAR" and participant_id not in allowed_parent_ids:
                    raise ValidationError(
                        "Cannot message a parent whose children are not in your classes",
                        error_code="ERR-COM-403",
                    )
                if role not in ("PAR", "ADM", "DIR", "TCH"):
                    raise ValidationError(
                        "Teachers can only message parents, admins, directors, or other teachers",
                        error_code="ERR-COM-403",
                    )
            return

        if auth.role == "STD":
            for participant_id in participant_ids:
                user = await self.repo.get_user(participant_id)
                if user is None:
                    raise NotFoundError("User not found", error_code="ERR-COM-404")
                role = await self.repo.get_membership_role(
                    user_id=participant_id,
                    school_id=auth.school_id,
                )
                if role != "TCH":
                    raise ValidationError(
                        "Students can only message teachers",
                        error_code="ERR-COM-403",
                    )
                is_valid = await validate_student_teacher_access(
                    self.db,
                    student_id=auth.user_id,
                    teacher_id=participant_id,
                )
                if not is_valid:
                    raise ValidationError(
                        "Students can only message teachers of their classes",
                        error_code="ERR-COM-403",
                    )

    async def _validate_attachment_ownership(
        self,
        *,
        attachment_id: uuid.UUID | None,
        auth: AuthContext,
    ) -> None:
        if attachment_id is None:
            return
        document = await DocumentsRepository(self.db).get_document(attachment_id)
        if (
            document is None
            or document.school_id != auth.school_id
            or document.deleted_at is not None
        ):
            raise NotFoundError("Attachment not found", error_code="ERR-DOC-404")
        if document.uploader_id != auth.user_id:
            raise ValidationError(
                "Attachment must belong to the sender",
                error_code="ERR-COM-403",
            )

    async def create_conversation(
        self,
        *,
        body: ConversationCreateRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        now = datetime.now(timezone.utc)
        if auth.role == "STD" and body.type != "DIRECT":
            raise ValidationError(
                "Students can only create direct conversations",
                error_code="ERR-COM-422",
            )
        if body.type == "DIRECT" and len(body.participant_ids) != 1:
            raise ValidationError(
                "DIRECT conversations require exactly 1 other participant",
                error_code="ERR-COM-422",
            )
        if auth.user_id in body.participant_ids:
            raise ValidationError(
                "Cannot include yourself as a participant",
                error_code="ERR-COM-422",
            )

        for participant_id in body.participant_ids:
            membership = await self.repo.get_membership(
                user_id=participant_id,
                school_id=auth.school_id,
            )
            if membership is None:
                raise NotFoundError(
                    "Participant not found in this school",
                    error_code="ERR-COM-404",
                )

        await self._validate_messaging_abac(auth=auth, participant_ids=body.participant_ids)

        async with UnitOfWork(self.db) as uow:
            repo = MessagingRepository(uow.session)
            audit = AuditService(uow.session)
            conversation = await repo.create_conversation(
                school_id=auth.school_id,
                type=body.type,
                created_by=auth.user_id,
                subject=body.subject,
            )
            await repo.create_conversation_participants(
                [
                    {
                        "conversation_id": conversation.id,
                        "user_id": auth.user_id,
                        "role_in_conversation": "INITIATOR",
                        "joined_at": now,
                        "muted": False,
                    },
                    *[
                        {
                            "conversation_id": conversation.id,
                            "user_id": participant_id,
                            "role_in_conversation": "PARTICIPANT",
                            "joined_at": now,
                            "muted": False,
                        }
                        for participant_id in body.participant_ids
                    ],
                ]
            )
            message = await repo.create_message(
                conversation_id=conversation.id,
                sender_id=auth.user_id,
                body=body.initial_message,
                sent_at=now,
            )
            conversation = await repo.get_conversation(conversation.id)
            response = self._conversation_to_response(
                conversation,
                last_message_at=now.isoformat(),
            )
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="conversation.create",
                target_type="conversation",
                target_id=conversation.id,
                outcome="success",
                entity_after=response,
                ip_address=ip_address,
            )
            await uow.commit()

        for participant_id in body.participant_ids:
            await publish_message_created(
                recipient_id=participant_id,
                conversation_id=conversation.id,
                message_id=message.id,
                sender_id=auth.user_id,
                body=body.initial_message,
                sent_at=now.isoformat(),
            )

        return response

    async def list_conversations(
        self,
        *,
        cursor: str | None,
        limit: int,
        auth: AuthContext,
    ) -> tuple[list[dict], str | None, bool]:
        rows, has_more = await self.repo.list_conversations_for_user(
            school_id=auth.school_id,
            user_id=auth.user_id,
            cursor=cursor,
            limit=limit,
        )
        items = [
            self._conversation_to_response(
                conversation,
                last_message_at=last_message_at.isoformat() if last_message_at else None,
            )
            for conversation, last_message_at in rows
        ]
        next_cursor = encode_cursor(uuid.UUID(items[-1]["id"])) if has_more and items else None
        return items, next_cursor, has_more

    async def list_messages(
        self,
        *,
        conversation_id: uuid.UUID,
        cursor: str | None,
        limit: int,
        auth: AuthContext,
    ) -> tuple[list[dict], str | None, bool]:
        conversation = await self._verify_participant(
            conversation_id=conversation_id,
            user_id=auth.user_id,
        )
        verify_school_boundary(conversation.school_id, auth)

        before_sent_at = None
        if cursor:
            cursor_id, _ = decode_cursor(cursor)
            before_sent_at = await self.repo.get_message_sent_at(cursor_id)

        messages, has_more = await self.repo.list_conversation_messages(
            conversation_id=conversation_id,
            before_sent_at=before_sent_at,
            limit=limit,
        )
        items = [self._message_to_response(message) for message in messages]
        next_cursor = encode_cursor(messages[-1].id) if has_more and messages else None
        return items, next_cursor, has_more

    async def send_message(
        self,
        *,
        conversation_id: uuid.UUID,
        body: MessageCreateRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        now = datetime.now(timezone.utc)
        conversation = await self._verify_participant(
            conversation_id=conversation_id,
            user_id=auth.user_id,
        )
        verify_school_boundary(conversation.school_id, auth)
        await self._validate_attachment_ownership(
            attachment_id=body.attachment_id,
            auth=auth,
        )

        async with UnitOfWork(self.db) as uow:
            repo = MessagingRepository(uow.session)
            audit = AuditService(uow.session)
            message = await repo.create_message(
                conversation_id=conversation_id,
                sender_id=auth.user_id,
                attachment_id=body.attachment_id,
                body=body.body,
                sent_at=now,
            )
            response = self._message_to_response(message)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="message.send",
                target_type="message",
                target_id=message.id,
                outcome="success",
                entity_after=response,
                ip_address=ip_address,
            )
            await uow.commit()

        for participant in conversation.participants:
            if participant.user_id != auth.user_id and not participant.muted:
                await publish_message_created(
                    recipient_id=participant.user_id,
                    conversation_id=conversation_id,
                    message_id=message.id,
                    sender_id=auth.user_id,
                    body=body.body,
                    sent_at=now.isoformat(),
                )

        return response

    async def search_messages(
        self,
        *,
        query_text: str,
        limit: int,
        auth: AuthContext,
    ) -> list[dict]:
        if not query_text.strip():
            raise ValidationError(
                "Search query cannot be empty",
                error_code="ERR-COM-422",
            )
        messages = await self.repo.search_messages(
            school_id=auth.school_id,
            user_id=auth.user_id,
            query_text=query_text.strip(),
            limit=limit,
        )
        return [self._message_to_response(message) for message in messages]

    async def mark_read(
        self,
        *,
        conversation_id: uuid.UUID,
        body: MarkReadRequest,
        auth: AuthContext,
    ) -> dict:
        now = datetime.now(timezone.utc)
        conversation = await self._verify_participant(
            conversation_id=conversation_id,
            user_id=auth.user_id,
        )
        verify_school_boundary(conversation.school_id, auth)

        message = await self.repo.get_message_in_conversation(
            conversation_id=conversation_id,
            message_id=body.message_id,
        )
        if message is None:
            raise NotFoundError("Message not found", error_code="ERR-COM-404")

        unread_message_ids = await self.repo.list_unread_message_ids(
            conversation_id=conversation_id,
            user_id=auth.user_id,
            up_to_sent_at=message.sent_at,
        )
        async with UnitOfWork(self.db) as uow:
            repo = MessagingRepository(uow.session)
            await repo.create_read_receipts(
                [
                    {
                        "message_id": message_id,
                        "user_id": auth.user_id,
                        "read_at": now,
                    }
                    for message_id in unread_message_ids
                ]
            )
            await uow.commit()
        return {
            "marked_read": len(unread_message_ids),
            "up_to_message_id": str(body.message_id),
        }

    async def get_read_status(
        self,
        *,
        conversation_id: uuid.UUID,
        message_id: uuid.UUID | None,
        auth: AuthContext,
    ) -> list[dict]:
        conversation = await self._verify_participant(
            conversation_id=conversation_id,
            user_id=auth.user_id,
        )
        verify_school_boundary(conversation.school_id, auth)

        receipts = await self.repo.list_read_receipts(
            conversation_id=conversation_id,
            message_id=message_id,
        )
        return [
            ReadReceiptResponse(
                user_id=str(receipt.user_id),
                read_at=receipt.read_at.isoformat(),
            ).model_dump()
            for receipt in receipts
        ]

    async def list_feed(
        self,
        *,
        student_id: uuid.UUID | None,
        filters: FilterSpec,
        sort: SortSpec,
        search: str | None,
        cursor: str | None,
        limit: int,
        auth: AuthContext,
    ) -> tuple[list[dict], str | None, bool]:
        if auth.role == "PAR" and student_id is not None:
            has_access = await validate_parent_child_access(
                self.db,
                parent_id=auth.user_id,
                student_id=student_id,
            )
            if not has_access:
                raise NotFoundError("Student not found", error_code="ERR-COM-404")
        items_list, has_more = await self.repo.list_parent_feed_items(
            school_id=auth.school_id,
            parent_id=auth.user_id,
            student_id=student_id,
            filters=filters,
            sort=sort,
            search=search,
            cursor=cursor,
            limit=limit,
        )
        items = [
            {
                "id": str(item.id),
                "school_id": str(item.school_id),
                "parent_id": str(item.parent_id),
                "student_id": str(item.student_id) if item.student_id else None,
                "source_type": item.source_type,
                "source_ref": item.source_ref,
                "title": item.title,
                "body": item.body,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            for item in items_list
        ]
        next_cursor = encode_cursor(items_list[-1].id) if has_more and items_list else None
        return items, next_cursor, has_more
