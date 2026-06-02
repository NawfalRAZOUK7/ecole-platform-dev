"""Integration tests for messaging endpoints (Phase 4.D).

Coverage target: app/api/v1/communication/messaging.py ≥ 95 % branch

Routes:
  POST /messages/conversations           — start conversation
  GET  /messages/conversations           — list conversations
  GET  /messages/search                  — search messages
  GET  /messages/conversations/{id}/messages  — list messages
  POST /messages/conversations/{id}/messages  — send message
  POST /messages/conversations/{id}/read      — mark as read
  GET  /messages/conversations/{id}/read-status
"""

from __future__ import annotations

import uuid

import pytest

from tests.integration.api.helpers import (
    SCHOOL_ID,
    auth_header,
    login_token,
)

ADMIN_EMAIL = "admin@ecole-benani.ma"
ADMIN_PASSWORD = "admin123"
TEACHER_EMAIL = "prof.math@ecole-benani.ma"
TEACHER_PASSWORD = "teacher123"
STUDENT_EMAIL = "yassine.alaoui@ecole-benani.ma"
STUDENT_PASSWORD = "student123"
PARENT_EMAIL = "parent.alaoui@gmail.com"
PARENT_PASSWORD = "parent123"

TEACHER_ID = "10000000-0000-4000-8000-000000000003"
ADMIN_ID = "10000000-0000-4000-8000-000000000001"
PARENT_ID = "10000000-0000-4000-8000-000000000005"


class TestConversationCreate:
    @pytest.mark.asyncio
    async def test_teacher_can_start_direct_conversation(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.post(
            "/messages/conversations",
            headers=auth_header(token),
            json={
                "participant_ids": [PARENT_ID],
                "type": "DIRECT",
                "initial_message": "Hello, I wanted to discuss your child's progress.",
            },
        )
        assert response.status_code in (200, 201)
        data = response.json()["data"]
        assert data["school_id"] == SCHOOL_ID

    @pytest.mark.asyncio
    async def test_parent_can_start_conversation_with_teacher(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        token = await login_token(client, email=PARENT_EMAIL, password=PARENT_PASSWORD)
        response = await client.post(
            "/messages/conversations",
            headers=auth_header(token),
            json={
                "participant_ids": [TEACHER_ID],
                "type": "DIRECT",
                "initial_message": "Hello teacher!",
            },
        )
        assert response.status_code in (200, 201)

    @pytest.mark.asyncio
    async def test_admin_can_start_group_conversation(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.post(
            "/messages/conversations",
            headers=auth_header(token),
            json={
                "participant_ids": [TEACHER_ID, PARENT_ID],
                "type": "GROUP",
                "subject": "Réunion parents-profs",
                "initial_message": "Bonjour à tous.",
            },
        )
        assert response.status_code in (200, 201)

    @pytest.mark.asyncio
    async def test_student_can_start_conversation(self, client, legacy_api_seed):
        """STD uses PERM_COM_STD_MESSAGE_SEND which is accepted by requires_any_permission."""
        _ = legacy_api_seed
        token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        response = await client.post(
            "/messages/conversations",
            headers=auth_header(token),
            json={
                "participant_ids": [TEACHER_ID],
                "type": "DIRECT",
                "initial_message": "Bonjour professeur.",
            },
        )
        assert response.status_code in (200, 201)

    @pytest.mark.asyncio
    async def test_missing_initial_message_returns_422(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.post(
            "/messages/conversations",
            headers=auth_header(token),
            json={"participant_ids": [PARENT_ID], "type": "DIRECT"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_empty_participant_list_returns_422(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.post(
            "/messages/conversations",
            headers=auth_header(token),
            json={"participant_ids": [], "initial_message": "hello"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_conversation_type_returns_422(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.post(
            "/messages/conversations",
            headers=auth_header(token),
            json={
                "participant_ids": [PARENT_ID],
                "type": "BROADCAST",
                "initial_message": "hi",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401_or_403(self, client, legacy_api_seed):
        _ = legacy_api_seed
        response = await client.post(
            "/messages/conversations",
            json={"participant_ids": [PARENT_ID], "initial_message": "hi"},
        )
        assert response.status_code in (401, 403)


class TestConversationList:
    @pytest.mark.asyncio
    async def test_teacher_can_list_conversations(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.get(
            "/messages/conversations", headers=auth_header(token)
        )
        assert response.status_code == 200
        assert isinstance(response.json()["data"], list)

    @pytest.mark.asyncio
    async def test_student_can_list_conversations(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        response = await client.get(
            "/messages/conversations", headers=auth_header(token)
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_conversations_pagination(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.get(
            "/messages/conversations",
            headers=auth_header(token),
            params={"limit": 5},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_conversations_invalid_limit_returns_422(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.get(
            "/messages/conversations",
            headers=auth_header(token),
            params={"limit": 200},
        )
        assert response.status_code == 422


class TestMessageSendList:
    async def _create_conversation(self, client, token, participant_id: str) -> str:
        r = await client.post(
            "/messages/conversations",
            headers=auth_header(token),
            json={
                "participant_ids": [participant_id],
                "type": "DIRECT",
                "initial_message": "Starting conversation",
            },
        )
        return r.json()["data"]["id"]

    @pytest.mark.asyncio
    async def test_teacher_can_list_messages_in_conversation(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        conv_id = await self._create_conversation(client, token, PARENT_ID)
        response = await client.get(
            f"/messages/conversations/{conv_id}/messages",
            headers=auth_header(token),
        )
        assert response.status_code == 200
        assert isinstance(response.json()["data"], list)

    @pytest.mark.asyncio
    async def test_list_messages_nonexistent_conversation_returns_404(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.get(
            f"/messages/conversations/{uuid.uuid4()}/messages",
            headers=auth_header(token),
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_teacher_can_send_message(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        conv_id = await self._create_conversation(client, token, PARENT_ID)
        response = await client.post(
            f"/messages/conversations/{conv_id}/messages",
            headers=auth_header(token),
            json={"body": "Follow-up message."},
        )
        assert response.status_code in (200, 201)

    @pytest.mark.asyncio
    async def test_send_message_empty_body_returns_422(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.post(
            f"/messages/conversations/{uuid.uuid4()}/messages",
            headers=auth_header(token),
            json={"body": ""},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_send_message_nonexistent_conversation_returns_404(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.post(
            f"/messages/conversations/{uuid.uuid4()}/messages",
            headers=auth_header(token),
            json={"body": "Hello"},
        )
        assert response.status_code == 404


class TestMarkRead:
    @pytest.mark.asyncio
    async def test_mark_messages_read(self, client, legacy_api_seed):
        _ = legacy_api_seed
        t_token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        # Create a conversation and get first message id
        cr = await client.post(
            "/messages/conversations",
            headers=auth_header(t_token),
            json={
                "participant_ids": [PARENT_ID],
                "type": "DIRECT",
                "initial_message": "Hello!",
            },
        )
        conv_id = cr.json()["data"]["id"]
        msgs = await client.get(
            f"/messages/conversations/{conv_id}/messages",
            headers=auth_header(t_token),
        )
        messages = msgs.json()["data"]
        if not messages:
            pytest.skip("No messages in conversation")
        msg_id = messages[0]["id"]

        p_token = await login_token(
            client, email=PARENT_EMAIL, password=PARENT_PASSWORD
        )
        response = await client.post(
            f"/messages/conversations/{conv_id}/read",
            headers=auth_header(p_token),
            json={"message_id": msg_id},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_mark_read_missing_message_id_returns_422(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.post(
            f"/messages/conversations/{uuid.uuid4()}/read",
            headers=auth_header(token),
            json={},
        )
        assert response.status_code == 422


class TestSearchMessages:
    @pytest.mark.asyncio
    async def test_teacher_can_search_messages(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        # Create a conversation with searchable content
        await client.post(
            "/messages/conversations",
            headers=auth_header(token),
            json={
                "participant_ids": [PARENT_ID],
                "type": "DIRECT",
                "initial_message": "Bonjour about the lesson",
            },
        )
        response = await client.get(
            "/messages/search",
            headers=auth_header(token),
            params={"q": "lesson"},
        )
        assert response.status_code == 200
        assert isinstance(response.json()["data"], list)

    @pytest.mark.asyncio
    async def test_search_missing_query_returns_422(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.get("/messages/search", headers=auth_header(token))
        assert response.status_code == 422


class TestReadStatus:
    @pytest.mark.asyncio
    async def test_get_read_status_for_conversation(self, client, legacy_api_seed):
        _ = legacy_api_seed
        t_token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        cr = await client.post(
            "/messages/conversations",
            headers=auth_header(t_token),
            json={
                "participant_ids": [PARENT_ID],
                "type": "DIRECT",
                "initial_message": "Hello!",
            },
        )
        conv_id = cr.json()["data"]["id"]
        response = await client.get(
            f"/messages/conversations/{conv_id}/read-status",
            headers=auth_header(t_token),
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_read_status_nonexistent_conversation_returns_404(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.get(
            f"/messages/conversations/{uuid.uuid4()}/read-status",
            headers=auth_header(token),
        )
        assert response.status_code == 404
