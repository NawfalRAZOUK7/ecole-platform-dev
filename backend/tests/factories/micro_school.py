"""Micro-school factories."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import factory
from faker import Faker

from app.models.micro_school import (
    MicroEnrollment,
    MicroEnrollmentStatus,
    MicroGroup,
    MicroPayment,
    MicroPaymentPeriodType,
    MicroPaymentStatus,
    MicroProgressLog,
    MicroResource,
    MicroResourceType,
    MicroSchool,
    MicroSchoolStatus,
)
from tests.factories.base import AsyncSQLAlchemyFactory
from tests.factories.iam import UserFactory

fake = Faker("fr_FR")


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _moroccan_phone() -> str:
    return f"+2126{fake.msisdn()[3:11]}"


class MicroSchoolFactory(AsyncSQLAlchemyFactory):
    """Factory for micro-schools."""

    class Meta:
        model = MicroSchool
        exclude = ("educator",)

    id = factory.LazyFunction(uuid.uuid4)
    educator = factory.SubFactory(UserFactory)
    educator_id = factory.LazyAttribute(lambda o: o.educator.id)
    name = factory.LazyFunction(lambda: f"Micro-Ecole {fake.city()}")
    neighborhood = factory.LazyFunction(lambda: fake.street_name())
    city = factory.LazyFunction(lambda: fake.city())
    phone = factory.LazyFunction(_moroccan_phone)
    max_capacity = 20
    status = MicroSchoolStatus.ACTIVE.value


class MicroGroupFactory(AsyncSQLAlchemyFactory):
    """Factory for micro-school groups."""

    class Meta:
        model = MicroGroup
        exclude = ("micro_school",)

    id = factory.LazyFunction(uuid.uuid4)
    micro_school = factory.SubFactory(MicroSchoolFactory)
    micro_school_id = factory.LazyAttribute(lambda o: o.micro_school.id)
    name = factory.Sequence(lambda n: f"Groupe {n + 1}")
    age_range_min = 3
    age_range_max = 5


class MicroEnrollmentFactory(AsyncSQLAlchemyFactory):
    """Factory for micro-enrollments."""

    class Meta:
        model = MicroEnrollment
        exclude = ("micro_group", "parent")

    id = factory.LazyFunction(uuid.uuid4)
    micro_group = factory.SubFactory(MicroGroupFactory)
    parent = factory.SubFactory(
        UserFactory,
        school_id=factory.SelfAttribute(
            "..micro_group.micro_school.educator.school_id"
        ),
    )
    micro_group_id = factory.LazyAttribute(lambda o: o.micro_group.id)
    parent_id = factory.LazyAttribute(lambda o: o.parent.id)
    child_name = factory.LazyFunction(fake.first_name)
    date_of_birth = factory.LazyFunction(lambda: date.today() - timedelta(days=4 * 365))
    enrolled_at = factory.LazyFunction(_utc_now)
    status = MicroEnrollmentStatus.ACTIVE.value


class MicroPaymentFactory(AsyncSQLAlchemyFactory):
    """Factory for micro-payments."""

    class Meta:
        model = MicroPayment
        exclude = ("micro_school", "parent", "child_enrollment")

    id = factory.LazyFunction(uuid.uuid4)
    child_enrollment = factory.SubFactory(MicroEnrollmentFactory)
    micro_school = factory.LazyAttribute(
        lambda o: o.child_enrollment.micro_group.micro_school
    )
    parent = factory.LazyAttribute(lambda o: o.child_enrollment.parent)
    micro_school_id = factory.LazyAttribute(lambda o: o.micro_school.id)
    parent_id = factory.LazyAttribute(lambda o: o.parent.id)
    child_enrollment_id = factory.LazyAttribute(lambda o: o.child_enrollment.id)
    amount = Decimal("450.00")
    currency = "MAD"
    period_type = MicroPaymentPeriodType.MONTHLY.value
    period_start = factory.LazyFunction(lambda: date.today().replace(day=1))
    period_end = factory.LazyAttribute(lambda o: o.period_start + timedelta(days=29))
    paid_at = None
    status = MicroPaymentStatus.PENDING.value


class MicroResourceFactory(AsyncSQLAlchemyFactory):
    """Factory for micro learning resources."""

    class Meta:
        model = MicroResource

    id = factory.LazyFunction(uuid.uuid4)
    title = factory.LazyFunction(lambda: f"Ressource {fake.word().title()}")
    description = factory.LazyFunction(lambda: fake.sentence(nb_words=8))
    resource_type = MicroResourceType.ACTIVITY_SHEET.value
    age_group = "3-5"
    language = "fr"
    file_url = factory.LazyFunction(
        lambda: f"https://cdn.ecole.ma/{uuid.uuid4().hex}.pdf"
    )
    is_premium = False


class MicroProgressLogFactory(AsyncSQLAlchemyFactory):
    """Factory for micro progress logs."""

    class Meta:
        model = MicroProgressLog
        exclude = ("micro_enrollment", "educator")

    id = factory.LazyFunction(uuid.uuid4)
    micro_enrollment = factory.SubFactory(MicroEnrollmentFactory)
    educator = factory.LazyAttribute(
        lambda o: o.micro_enrollment.micro_group.micro_school.educator
    )
    micro_enrollment_id = factory.LazyAttribute(lambda o: o.micro_enrollment.id)
    educator_id = factory.LazyAttribute(lambda o: o.educator.id)
    date = factory.LazyFunction(date.today)
    note = factory.LazyFunction(lambda: "Participation active aux activites du jour.")
    photo_url = factory.LazyFunction(
        lambda: f"https://cdn.ecole.ma/{uuid.uuid4().hex}.jpg"
    )
    milestone_tag = "language"


__all__ = [
    "MicroSchoolFactory",
    "MicroGroupFactory",
    "MicroEnrollmentFactory",
    "MicroPaymentFactory",
    "MicroResourceFactory",
    "MicroProgressLogFactory",
]
