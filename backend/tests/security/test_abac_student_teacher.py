"""Student-teacher messaging ABAC tests."""

from __future__ import annotations

import pytest

from .conftest import ADMIN_ID, PARENT_ID, STUDENT_ID, TEACHER_ID, auth_header


async def create_direct_conversation(client, *, token: str, participant_id: str, message: str):
    return await client.post(
        "/messages/conversations",
        headers=auth_header(token),
        json={
            "participant_ids": [participant_id],
            "type": "DIRECT",
            "initial_message": message,
        },
    )


@pytest.mark.asyncio
async def test_student_can_message_enrolled_teacher(client, student_token):
    response = await create_direct_conversation(
        client,
        token=student_token,
        participant_id=TEACHER_ID,
        message="Bonjour professeur, j'ai une question.",
    )

    assert response.status_code == 201, response.text
    payload = response.json()["data"]
    assert payload["type"] == "DIRECT"


@pytest.mark.asyncio
async def test_student_can_list_own_conversations_after_creation(client, student_token):
    create_response = await create_direct_conversation(
        client,
        token=student_token,
        participant_id=TEACHER_ID,
        message="Conversation visible pour l'etudiant",
    )
    assert create_response.status_code == 201, create_response.text
    conversation_id = create_response.json()["data"]["id"]

    list_response = await client.get(
        "/messages/conversations",
        headers=auth_header(student_token),
    )

    assert list_response.status_code == 200, list_response.text
    ids = {item["id"] for item in list_response.json()["data"]}
    assert conversation_id in ids


@pytest.mark.asyncio
async def test_student_can_send_message_in_own_conversation(client, student_token):
    create_response = await create_direct_conversation(
        client,
        token=student_token,
        participant_id=TEACHER_ID,
        message="Premier message",
    )
    assert create_response.status_code == 201, create_response.text
    conversation_id = create_response.json()["data"]["id"]

    response = await client.post(
        f"/messages/conversations/{conversation_id}/messages",
        headers=auth_header(student_token),
        json={"body": "Deuxieme message dans la meme conversation"},
    )

    assert response.status_code == 201, response.text
    assert response.json()["data"]["conversation_id"] == conversation_id


@pytest.mark.asyncio
async def test_student_can_search_own_messages(client, student_token):
    create_response = await create_direct_conversation(
        client,
        token=student_token,
        participant_id=TEACHER_ID,
        message="motcle-securite-professeur",
    )
    assert create_response.status_code == 201, create_response.text

    response = await client.get(
        "/messages/search",
        headers=auth_header(student_token),
        params={"q": "motcle-securite-professeur"},
    )

    assert response.status_code == 200, response.text
    assert any("motcle-securite-professeur" in item["body"] for item in response.json()["data"])


@pytest.mark.asyncio
async def test_student_cannot_message_unrelated_teacher(
    client,
    student_token,
    other_teacher_actor,
):
    response = await create_direct_conversation(
        client,
        token=student_token,
        participant_id=str(other_teacher_actor.user_id),
        message="Tentative vers enseignant non lie",
    )

    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_student_cannot_message_parent(client, student_token):
    response = await create_direct_conversation(
        client,
        token=student_token,
        participant_id=PARENT_ID,
        message="Tentative vers parent",
    )

    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_student_cannot_message_admin(client, student_token):
    response = await create_direct_conversation(
        client,
        token=student_token,
        participant_id=ADMIN_ID,
        message="Tentative vers admin",
    )

    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_student_cannot_create_group_conversation(client, student_token):
    response = await client.post(
        "/messages/conversations",
        headers=auth_header(student_token),
        json={
            "participant_ids": [TEACHER_ID],
            "type": "GROUP",
            "subject": "Groupe interdit",
            "initial_message": "Tentative de groupe",
        },
    )

    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_student_direct_conversation_requires_exactly_one_participant(
    client,
    student_token,
    other_teacher_actor,
):
    response = await client.post(
        "/messages/conversations",
        headers=auth_header(student_token),
        json={
            "participant_ids": [TEACHER_ID, str(other_teacher_actor.user_id)],
            "type": "DIRECT",
            "initial_message": "Deux participants dans un direct",
        },
    )

    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_student_cannot_include_self_in_conversation(client, student_token):
    response = await client.post(
        "/messages/conversations",
        headers=auth_header(student_token),
        json={
            "participant_ids": [STUDENT_ID],
            "type": "DIRECT",
            "initial_message": "Je me parle a moi-meme",
        },
    )

    assert response.status_code == 422, response.text
