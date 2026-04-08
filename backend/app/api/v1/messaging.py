"""Messaging endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_any_permission
from app.core.permissions import (
    PERM_COM_CONVERSATION_CREATE,
    PERM_COM_CONVERSATION_READ,
    PERM_COM_MESSAGE_SEND,
    PERM_COM_STD_MESSAGE_READ,
    PERM_COM_STD_MESSAGE_SEND,
)
from app.core.request_utils import get_client_ip
from app.core.response import clamp_page_size, list_response, success_response
from app.schemas.com import (
    ConversationCreateRequest,
    MarkReadRequest,
    MessageCreateRequest,
)
from app.services.communication import CommunicationService

router = APIRouter(prefix="/messages", tags=["messaging"])


@router.post(
    "/conversations",
    status_code=201,
    summary="Start a new conversation",
    response_description="Created conversation with first message",
)
async def create_conversation(
    body: ConversationCreateRequest,
    request: Request,
    auth: AuthContext = Depends(
        requires_any_permission(
            PERM_COM_CONVERSATION_CREATE,
            PERM_COM_STD_MESSAGE_SEND,
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    service = CommunicationService(db)
    return success_response(
        await service.create_conversation(
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "/conversations",
    summary="List user's conversations",
    response_description="Paginated list of conversations",
)
async def list_conversations(
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None),
    auth: AuthContext = Depends(
        requires_any_permission(
            PERM_COM_CONVERSATION_READ,
            PERM_COM_STD_MESSAGE_READ,
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    service = CommunicationService(db)
    items, next_cursor, has_more = await service.list_conversations(
        cursor=cursor,
        limit=clamp_page_size(limit),
        auth=auth,
    )
    return list_response(items, next_cursor=next_cursor, has_more=has_more)


@router.get(
    "/search",
    summary="Search messages across accessible conversations",
    response_description="List of matching messages",
)
async def search_messages(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    auth: AuthContext = Depends(
        requires_any_permission(
            PERM_COM_CONVERSATION_READ,
            PERM_COM_STD_MESSAGE_READ,
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    service = CommunicationService(db)
    items = await service.search_messages(
        query_text=q,
        limit=clamp_page_size(limit),
        auth=auth,
    )
    return list_response(items, next_cursor=None, has_more=False)


@router.get(
    "/conversations/{conversation_id}/messages",
    summary="List messages in a conversation",
    response_description="Paginated list of messages",
)
async def list_messages(
    conversation_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=100),
    cursor: str | None = Query(None),
    auth: AuthContext = Depends(
        requires_any_permission(
            PERM_COM_CONVERSATION_READ,
            PERM_COM_STD_MESSAGE_READ,
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    service = CommunicationService(db)
    items, next_cursor, has_more = await service.list_messages(
        conversation_id=conversation_id,
        cursor=cursor,
        limit=clamp_page_size(limit),
        auth=auth,
    )
    return list_response(items, next_cursor=next_cursor, has_more=has_more)


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
    auth: AuthContext = Depends(
        requires_any_permission(
            PERM_COM_MESSAGE_SEND,
            PERM_COM_STD_MESSAGE_SEND,
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    service = CommunicationService(db)
    return success_response(
        await service.send_message(
            conversation_id=conversation_id,
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.post(
    "/conversations/{conversation_id}/read",
    summary="Mark messages as read",
    response_description="Read receipt confirmation",
)
async def mark_read(
    conversation_id: uuid.UUID,
    body: MarkReadRequest,
    auth: AuthContext = Depends(
        requires_any_permission(
            PERM_COM_CONVERSATION_READ,
            PERM_COM_STD_MESSAGE_READ,
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    service = CommunicationService(db)
    return success_response(
        await service.mark_read(
            conversation_id=conversation_id,
            body=body,
            auth=auth,
        )
    )


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
    auth: AuthContext = Depends(
        requires_any_permission(
            PERM_COM_CONVERSATION_READ,
            PERM_COM_STD_MESSAGE_READ,
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    service = CommunicationService(db)
    return list_response(
        await service.get_read_status(
            conversation_id=conversation_id,
            message_id=message_id,
            auth=auth,
        )
    )
