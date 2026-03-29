"""IAM factories."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import factory
from faker import Faker

from app.models.iam import (
    InvitationCode,
    LinkStatus,
    Membership,
    MembershipStatus,
    ParentChildLink,
    RoleCode,
    Session,
    User,
    UserStatus,
)
from tests.factories.base import AsyncSQLAlchemyFactory
from tests.factories.school import SchoolFactory

fake = Faker("fr_FR")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _future_datetime(hours: int = 24) -> datetime:
    return _utc_now() + timedelta(hours=hours)


def _moroccan_phone() -> str:
    return f"+2126{fake.msisdn()[3:11]}"


def _invite_hash() -> str:
    token = f"INV-{secrets.token_hex(8)}"
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class UserFactory(AsyncSQLAlchemyFactory):
    """Factory for platform users."""

    class Meta:
        model = User
        exclude = ("school",)

    id = factory.LazyFunction(uuid.uuid4)
    school = factory.SubFactory(SchoolFactory)
    school_id = factory.LazyAttribute(lambda o: o.school.id)
    email = factory.LazyFunction(lambda: fake.unique.email())
    phone = factory.LazyFunction(_moroccan_phone)
    full_name = factory.LazyFunction(fake.name)
    password_hash = "$2b$12$placeholder_hash_for_testing"
    status = UserStatus.ACTIVE.value
    totp_secret = None
    totp_enabled = False
    totp_verified_at = None
    backup_codes = None
    email_verified_at = None


class MembershipFactory(AsyncSQLAlchemyFactory):
    """Factory for school memberships."""

    class Meta:
        model = Membership
        exclude = ("user",)

    id = factory.LazyFunction(uuid.uuid4)
    user = factory.SubFactory(UserFactory)
    school_id = factory.LazyAttribute(lambda o: o.user.school_id)
    user_id = factory.LazyAttribute(lambda o: o.user.id)
    role_code = RoleCode.STD.value
    status = MembershipStatus.ACTIVE.value


class SessionFactory(AsyncSQLAlchemyFactory):
    """Factory for auth sessions."""

    class Meta:
        model = Session
        exclude = ("user",)

    id = factory.LazyFunction(uuid.uuid4)
    user = factory.SubFactory(UserFactory)
    school_id = factory.LazyAttribute(lambda o: o.user.school_id)
    user_id = factory.LazyAttribute(lambda o: o.user.id)
    revoke_at = None
    source = "web"
    correlation_id = factory.LazyFunction(uuid.uuid4)
    user_agent = "pytest-agent/1.0"
    ip_address = "127.0.0.1"
    device_name = "pytest-device"
    impersonator_id = None


class InvitationCodeFactory(AsyncSQLAlchemyFactory):
    """Factory for invitation codes."""

    class Meta:
        model = InvitationCode
        exclude = ("school",)

    id = factory.LazyFunction(uuid.uuid4)
    school = factory.SubFactory(SchoolFactory)
    school_id = factory.LazyAttribute(lambda o: o.school.id)
    issuer_user_id = None
    code_hash = factory.LazyFunction(_invite_hash)
    role_target = RoleCode.STD.value
    consumed_by = None
    consumed_at = None
    expires_at = factory.LazyFunction(lambda: _future_datetime(72))
    target_student_id = None


class ParentChildLinkFactory(AsyncSQLAlchemyFactory):
    """Factory for parent-child relationships."""

    class Meta:
        model = ParentChildLink
        exclude = ("school", "parent", "child")

    id = factory.LazyFunction(uuid.uuid4)
    school = factory.SubFactory(SchoolFactory)
    parent = factory.SubFactory(UserFactory, school=factory.SelfAttribute("..school"))
    child = factory.SubFactory(UserFactory, school=factory.SelfAttribute("..school"))
    school_id = factory.LazyAttribute(lambda o: o.school.id)
    parent_user_id = factory.LazyAttribute(lambda o: o.parent.id)
    child_user_id = factory.LazyAttribute(lambda o: o.child.id)
    status = LinkStatus.ACTIVE.value
    linked_at = factory.LazyFunction(_utc_now)
    linked_by = factory.LazyAttribute(lambda o: o.parent.id)
