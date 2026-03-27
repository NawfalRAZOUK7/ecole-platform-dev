"""Messaging API endpoints — Phase 11C.

Reference: Phase 11C — Messaging & Communication
Endpoints:
  POST   /messages/conversations                      — Start conversation (PAR↔TCH ABAC)
  GET    /messages/conversations                      — List user's conversations
  GET    /messages/conversations/{id}/messages         — List messages (cursor pagination)
  POST   /messages/conversations/{id}/messages         — Send message
  POST   /messages/conversations/{id}/read             — Mark messages as read
  GET    /messages/conversations/{id}/read-status      — Get read receipts
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import (
    AuthContext,
    get_parent_child_ids,
    get_teacher_class_ids,
    requires_permission,
    verify_school_boundary,
)
from app.core.exceptions import NotFoundError, ValidationError
from app.core.response import (
    clamp_page_size,
    decode_cursor,
    encode_cursor,
    list_response,
    success_response,
)
from app.models.com import (
    Conversation,
    ConversationParticipant,
    Message,
    MessageReadReceipt,
)
from app.models.erp import Enrollment, TeacherAssignment
from app.models.iam import ParentChildLink, User
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

router = APIRouter(prefix="/messages", tags=["messaging"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def _conversation_to_response(
    conv: Conversation,
    last_message_at: str | None = None,
) -> dict:
    participants = []
    if conv.participants:
        participants = [
            ConversationParticipantResponse(
                user_id=str(p.user_id),
                role_in_conversation=p.role_in_conversation,
                joined_at=p.joined_at.isoformat(),
                muted=p.muted,
            ).model_dump()
            for p in conv.participants
        ]

    return ConversationResponse(
        id=str(conv.id),
        school_id=str(conv.school_id),
        type=conv.type,
        created_by=str(conv.created_by),
        subject=conv.subject,
        participants=participants,
        last_message_at=last_message_at,
        created_at=conv.created_at.isoformat(),
    ).model_dump()


def _message_to_response(msg: Message) -> dict:
    return MessageResponse(
        id=str(msg.id),
        conversation_id=str(msg.conversation_id),
        sender_id=str(msg.sender_id),
        body=msg.body,
        sent_at=msg.sent_at.isoformat(),
        edited_at=msg.edited_at.isoformat() if msg.edited_at else None,
        created_at=msg.created_at.isoformat(),
    ).model_dump()


async def _verify_participant(
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> Conversation:
    """Verify user is a participant in the conversation. Returns the conversation."""
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.participants))
        .where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if conv is None:
        raise NotFoundError("Conversation not found", error_code="ERR-COM-404")

    participant_ids = {p.user_id for p in conv.participants}
    if user_id not in participant_ids:
        raise NotFoundError("Conversation not found", error_code="ERR-COM-404")

    return conv


async def _validate_messaging_abac(
    auth: AuthContext,
    participant_ids: list[uuid.UUID],
    db: AsyncSession,
) -> None:
    """ABAC: Parents can only message teachers of their children's classes, and vice versa.

    ADM/DIR can message anyone in their school.
    """
    if auth.role in ("ADM", "DIR"):
        # Admin and director can message anyone in their school
        return

    if auth.role == "PAR":
        # Parent can only message teachers of their children's classes
        child_ids = await get_parent_child_ids(auth.user_id, auth.school_id, db)
        if not child_ids:
            raise ValidationError(
                "No linked children found",
                error_code="ERR-COM-422",
            )

        # Get classes of parent's children
        enroll_result = await db.execute(
            select(Enrollment.class_id).where(
                Enrollment.student_id.in_(child_ids),
                Enrollment.school_id == auth.school_id,
                Enrollment.status == "active",
            )
        )
        child_class_ids = set(enroll_result.scalars().all())

        # Get teachers assigned to those classes
        teacher_result = await db.execute(
            select(TeacherAssignment.teacher_id).where(
                TeacherAssignment.class_id.in_(child_class_ids),
                TeacherAssignment.school_id == auth.school_id,
            )
        )
        allowed_teacher_ids = set(teacher_result.scalars().all())

        for pid in participant_ids:
            # Verify each participant is an allowed teacher
            user_result = await db.execute(select(User).where(User.id == pid))
            user = user_result.scalar_one_or_none()
            if user is None:
                raise NotFoundError("User not found", error_code="ERR-COM-404")

            # Check the user's membership role
            from app.models.iam import Membership

            mem_result = await db.execute(
                select(Membership.role_code).where(
                    Membership.user_id == pid,
                    Membership.school_id == auth.school_id,
                )
            )
            role = mem_result.scalar_one_or_none()

            if role == "TCH" and pid not in allowed_teacher_ids:
                raise ValidationError(
                    "Cannot message a teacher not assigned to your children's classes",
                    error_code="ERR-COM-403",
                )
            elif role not in ("TCH", "ADM", "DIR"):
                raise ValidationError(
                    "Parents can only message teachers, admins, or directors",
                    error_code="ERR-COM-403",
                )

    elif auth.role == "TCH":
        # Teacher can only message parents of students in their classes
        teacher_class_ids = await get_teacher_class_ids(
            auth.user_id, auth.school_id, db
        )
        if not teacher_class_ids:
            raise ValidationError(
                "No class assignments found",
                error_code="ERR-COM-422",
            )

        # Get students in teacher's classes
        student_result = await db.execute(
            select(Enrollment.student_id).where(
                Enrollment.class_id.in_(teacher_class_ids),
                Enrollment.school_id == auth.school_id,
                Enrollment.status == "active",
            )
        )
        class_student_ids = set(student_result.scalars().all())

        # Get parents of those students
        parent_result = await db.execute(
            select(ParentChildLink.parent_user_id).where(
                ParentChildLink.child_user_id.in_(class_student_ids),
                ParentChildLink.school_id == auth.school_id,
                ParentChildLink.status == "active",
            )
        )
        allowed_parent_ids = set(parent_result.scalars().all())

        for pid in participant_ids:
            user_result = await db.execute(select(User).where(User.id == pid))
            user = user_result.scalar_one_or_none()
            if user is None:
                raise NotFoundError("User not found", error_code="ERR-COM-404")

            from app.models.iam import Membership

            mem_result = await db.execute(
                select(Membership.role_code).where(
                    Membership.user_id == pid,
                    Membership.school_id == auth.school_id,
                )
            )
            role = mem_result.scalar_one_or_none()

            if role == "PAR" and pid not in allowed_parent_ids:
                raise ValidationError(
                    "Cannot message a parent whose children are not in your classes",
                    error_code="ERR-COM-403",
                )
            elif role not in ("PAR", "ADM", "DIR", "TCH"):
                raise ValidationError(
                    "Teachers can only message parents, admins, directors, or other teachers",
                    error_code="ERR-COM-403",
                )


# ---------------------------------------------------------------------------
# POST /messages/conversations — Start conversation
# ---------------------------------------------------------------------------
@router.post(
    "/conversations",
    status_code=201,
    summary="Start a new conversation",
    response_description="Created conversation with first message",
)
async def create_conversation(
    body: ConversationCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-COM:conversation:create")),
    db: AsyncSession = Depends(get_db),
):
    """Start a new conversation between participants.

    ABAC enforced: parents can only message teachers of their children's
    classes, and vice versa. ADM/DIR can message anyone.
    """
    audit = AuditService(db)
    now = datetime.now(timezone.utc)

    # Validate DIRECT conversation has exactly 1 other participant
    if body.type == "DIRECT" and len(body.participant_ids) != 1:
        raise ValidationError(
            "DIRECT conversations require exactly 1 other participant",
            error_code="ERR-COM-422",
        )

    # Cannot include self
    if auth.user_id in body.participant_ids:
        raise ValidationError(
            "Cannot include yourself as a participant",
            error_code="ERR-COM-422",
        )

    # Validate all participants exist and are in the same school
    for pid in body.participant_ids:
        from app.models.iam import Membership

        mem_result = await db.execute(
            select(Membership).where(
                Membership.user_id == pid,
                Membership.school_id == auth.school_id,
            )
        )
        if mem_result.scalar_one_or_none() is None:
            raise NotFoundError(
                "Participant not found in this school",
                error_code="ERR-COM-404",
            )

    # ABAC validation
    await _validate_messaging_abac(auth, body.participant_ids, db)

    # Create conversation
    conv = Conversation(
        school_id=auth.school_id,
        type=body.type,
        created_by=auth.user_id,
        subject=body.subject,
    )
    db.add(conv)
    await db.flush()

    # Add initiator as participant
    initiator_participant = ConversationParticipant(
        conversation_id=conv.id,
        user_id=auth.user_id,
        role_in_conversation="INITIATOR",
        joined_at=now,
        muted=False,
    )
    db.add(initiator_participant)

    # Add other participants
    for pid in body.participant_ids:
        participant = ConversationParticipant(
            conversation_id=conv.id,
            user_id=pid,
            role_in_conversation="PARTICIPANT",
            joined_at=now,
            muted=False,
        )
        db.add(participant)

    await db.flush()

    # Create initial message
    msg = Message(
        conversation_id=conv.id,
        sender_id=auth.user_id,
        body=body.initial_message,
        sent_at=now,
    )
    db.add(msg)
    await db.flush()

    # Reload conversation with participants
    conv = await _verify_participant(conv.id, auth.user_id, db)

    resp = _conversation_to_response(conv, last_message_at=now.isoformat())

    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="conversation.create",
        target_type="conversation",
        target_id=conv.id,
        outcome="success",
        entity_after=resp,
        ip_address=_get_client_ip(request),
    )

    await db.commit()

    # Push WebSocket notifications to other participants
    for pid in body.participant_ids:
        await publish_message_created(
            recipient_id=pid,
            conversation_id=conv.id,
            message_id=msg.id,
            sender_id=auth.user_id,
            body=body.initial_message,
            sent_at=now.isoformat(),
        )

    return success_response(resp)


# ---------------------------------------------------------------------------
# GET /messages/conversations — List user's conversations
# ---------------------------------------------------------------------------
@router.get(
    "/conversations",
    summary="List user's conversations",
    response_description="Paginated list of conversations",
)
async def list_conversations(
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None),
    auth: AuthContext = Depends(requires_permission("PERM-COM:conversation:read")),
    db: AsyncSession = Depends(get_db),
):
    """List conversations the current user participates in.

    Ordered by most recent message. Cursor-based pagination.
    """
    page_size = clamp_page_size(limit)

    # Subquery: conversation IDs the user participates in
    my_conv_ids = (
        select(ConversationParticipant.conversation_id)
        .where(ConversationParticipant.user_id == auth.user_id)
        .scalar_subquery()
    )

    # Subquery: last message timestamp per conversation
    last_msg_sub = (
        select(
            Message.conversation_id,
            func.max(Message.sent_at).label("last_sent"),
        )
        .group_by(Message.conversation_id)
        .subquery()
    )

    query = (
        select(Conversation, last_msg_sub.c.last_sent)
        .options(selectinload(Conversation.participants))
        .outerjoin(last_msg_sub, Conversation.id == last_msg_sub.c.conversation_id)
        .where(
            Conversation.id.in_(my_conv_ids),
            Conversation.school_id == auth.school_id,
        )
        .order_by(
            last_msg_sub.c.last_sent.desc().nullslast(), Conversation.created_at.desc()
        )
    )

    if cursor:
        cursor_id, _ = decode_cursor(cursor)
        query = query.where(Conversation.id != cursor_id)

    query = query.limit(page_size + 1)
    result = await db.execute(query)
    rows = result.all()

    has_more = len(rows) > page_size
    rows = rows[:page_size]

    items = []
    for row in rows:
        conv = row[0]
        last_sent = row[1]
        items.append(
            _conversation_to_response(
                conv,
                last_message_at=last_sent.isoformat() if last_sent else None,
            )
        )

    next_cursor = None
    if has_more and items:
        next_cursor = encode_cursor(uuid.UUID(items[-1]["id"]))

    return list_response(items, next_cursor=next_cursor, has_more=has_more)


# ---------------------------------------------------------------------------
# GET /messages/conversations/{id}/messages — List messages
# ---------------------------------------------------------------------------
@router.get(
    "/conversations/{conversation_id}/messages",
    summary="List messages in a conversation",
    response_description="Paginated list of messages",
)
async def list_messages(
    conversation_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=100),
    cursor: str | None = Query(None),
    auth: AuthContext = Depends(requires_permission("PERM-COM:conversation:read")),
    db: AsyncSession = Depends(get_db),
):
    """List messages in a conversation (newest first). Cursor-based pagination."""
    # Verify user is a participant
    conv = await _verify_participant(conversation_id, auth.user_id, db)
    verify_school_boundary(conv.school_id, auth)

    page_size = clamp_page_size(limit)

    query = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.sent_at.desc())
    )

    if cursor:
        cursor_id, _ = decode_cursor(cursor)
        # Get the sent_at of the cursor message
        cursor_msg_result = await db.execute(
            select(Message.sent_at).where(Message.id == cursor_id)
        )
        cursor_sent_at = cursor_msg_result.scalar_one_or_none()
        if cursor_sent_at:
            query = query.where(Message.sent_at < cursor_sent_at)

    query = query.limit(page_size + 1)
    result = await db.execute(query)
    messages = list(result.scalars().all())

    has_more = len(messages) > page_size
    messages = messages[:page_size]

    items = [_message_to_response(m) for m in messages]

    next_cursor = None
    if has_more and messages:
        next_cursor = encode_cursor(messages[-1].id)

    return list_response(items, next_cursor=next_cursor, has_more=has_more)


# ---------------------------------------------------------------------------
# POST /messages/conversations/{id}/messages — Send message
# ---------------------------------------------------------------------------
@router.post(
    "/conversations/{conversation_id}/messages",
    status_code=201,
    summary="Send a message",
    response_description="Created message",
)
async def send_message(
    conversation_id: uuid.UUID,
    body: MessageCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-COM:message:send")),
    db: AsyncSession = Depends(get_db),
):
    """Send a message in an existing conversation.

    User must be a participant. Pushes WebSocket event to other participants.
    """
    audit = AuditService(db)
    now = datetime.now(timezone.utc)

    # Verify user is a participant
    conv = await _verify_participant(conversation_id, auth.user_id, db)
    verify_school_boundary(conv.school_id, auth)

    msg = Message(
        conversation_id=conversation_id,
        sender_id=auth.user_id,
        body=body.body,
        sent_at=now,
    )
    db.add(msg)
    await db.flush()

    resp = _message_to_response(msg)

    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="message.send",
        target_type="message",
        target_id=msg.id,
        outcome="success",
        entity_after=resp,
        ip_address=_get_client_ip(request),
    )

    await db.commit()

    # Push WebSocket notifications to other participants
    for p in conv.participants:
        if p.user_id != auth.user_id and not p.muted:
            await publish_message_created(
                recipient_id=p.user_id,
                conversation_id=conversation_id,
                message_id=msg.id,
                sender_id=auth.user_id,
                body=body.body,
                sent_at=now.isoformat(),
            )

    return success_response(resp)


# ---------------------------------------------------------------------------
# POST /messages/conversations/{id}/read — Mark as read
# ---------------------------------------------------------------------------
@router.post(
    "/conversations/{conversation_id}/read",
    summary="Mark messages as read",
    response_description="Read receipt confirmation",
)
async def mark_read(
    conversation_id: uuid.UUID,
    body: MarkReadRequest,
    auth: AuthContext = Depends(requires_permission("PERM-COM:conversation:read")),
    db: AsyncSession = Depends(get_db),
):
    """Mark a message (and all prior messages) as read in a conversation."""
    now = datetime.now(timezone.utc)

    # Verify user is a participant
    conv = await _verify_participant(conversation_id, auth.user_id, db)
    verify_school_boundary(conv.school_id, auth)

    # Verify message belongs to this conversation
    msg_result = await db.execute(
        select(Message).where(
            Message.id == body.message_id,
            Message.conversation_id == conversation_id,
        )
    )
    msg = msg_result.scalar_one_or_none()
    if msg is None:
        raise NotFoundError("Message not found", error_code="ERR-COM-404")

    # Get all unread messages up to and including this one
    unread_msgs_result = await db.execute(
        select(Message.id).where(
            Message.conversation_id == conversation_id,
            Message.sent_at <= msg.sent_at,
            Message.sender_id != auth.user_id,  # Don't mark own messages
            ~Message.id.in_(
                select(MessageReadReceipt.message_id).where(
                    MessageReadReceipt.user_id == auth.user_id
                )
            ),
        )
    )
    unread_msg_ids = list(unread_msgs_result.scalars().all())

    created = 0
    for mid in unread_msg_ids:
        receipt = MessageReadReceipt(
            message_id=mid,
            user_id=auth.user_id,
            read_at=now,
        )
        db.add(receipt)
        created += 1

    await db.flush()
    await db.commit()

    return success_response(
        {
            "marked_read": created,
            "up_to_message_id": str(body.message_id),
        }
    )


# ---------------------------------------------------------------------------
# GET /messages/conversations/{id}/read-status — Read receipts
# ---------------------------------------------------------------------------
@router.get(
    "/conversations/{conversation_id}/read-status",
    summary="Get read receipts for a conversation",
    response_description="Read status per message",
)
async def get_read_status(
    conversation_id: uuid.UUID,
    message_id: uuid.UUID | None = Query(
        None, description="Filter by specific message"
    ),
    auth: AuthContext = Depends(requires_permission("PERM-COM:conversation:read")),
    db: AsyncSession = Depends(get_db),
):
    """Get read receipts for messages in a conversation."""
    # Verify user is a participant
    conv = await _verify_participant(conversation_id, auth.user_id, db)
    verify_school_boundary(conv.school_id, auth)

    query = (
        select(MessageReadReceipt)
        .join(Message, MessageReadReceipt.message_id == Message.id)
        .where(Message.conversation_id == conversation_id)
    )

    if message_id:
        query = query.where(MessageReadReceipt.message_id == message_id)

    query = query.order_by(MessageReadReceipt.read_at.desc()).limit(200)
    result = await db.execute(query)
    receipts = result.scalars().all()

    items = [
        ReadReceiptResponse(
            user_id=str(r.user_id),
            read_at=r.read_at.isoformat(),
        ).model_dump()
        for r in receipts
    ]

    return list_response(items)
