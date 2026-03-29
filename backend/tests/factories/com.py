"""Communication factories."""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timezone

import factory

from app.models.com import (
    Conversation,
    ConversationType,
    Message,
    Notification,
    NotificationCategory,
    NotificationPriority,
)
from tests.factories.base import AsyncSQLAlchemyFactory
from tests.factories.iam import UserFactory
from tests.factories.school import SchoolFactory


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class NotificationFactory(AsyncSQLAlchemyFactory):
    """Factory for notifications."""

    class Meta:
        model = Notification
        exclude = ("school", "parent")

    id = factory.LazyFunction(uuid.uuid4)
    school = factory.SubFactory(SchoolFactory)
    parent = factory.SubFactory(UserFactory, school=factory.SelfAttribute("..school"))
    school_id = factory.LazyAttribute(lambda o: o.school.id)
    parent_id = factory.LazyAttribute(lambda o: o.parent.id)
    event_ref = None
    idempotency_key = factory.LazyFunction(lambda: f"notif-{secrets.token_hex(8)}")
    category = NotificationCategory.SYSTEM.value
    priority = NotificationPriority.NORMAL.value
    title = "Notification"
    body = "Contenu"
    action_url = None
    action_payload = None
    read_at = None


class ConversationFactory(AsyncSQLAlchemyFactory):
    """Factory for conversations."""

    class Meta:
        model = Conversation
        exclude = ("school", "creator")

    id = factory.LazyFunction(uuid.uuid4)
    school = factory.SubFactory(SchoolFactory)
    creator = factory.SubFactory(UserFactory, school=factory.SelfAttribute("..school"))
    school_id = factory.LazyAttribute(lambda o: o.school.id)
    type = ConversationType.DIRECT.value
    created_by = factory.LazyAttribute(lambda o: o.creator.id)
    subject = "Conversation test"


class MessageFactory(AsyncSQLAlchemyFactory):
    """Factory for messages."""

    class Meta:
        model = Message
        exclude = ("conversation", "sender")

    id = factory.LazyFunction(uuid.uuid4)
    conversation = factory.SubFactory(ConversationFactory)
    sender = factory.SubFactory(UserFactory)
    conversation_id = factory.LazyAttribute(lambda o: o.conversation.id)
    sender_id = factory.LazyAttribute(lambda o: o.sender.id)
    attachment_id = None
    body = "Bonjour"
    sent_at = factory.LazyFunction(_utc_now)
    edited_at = None
