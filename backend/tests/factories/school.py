"""School factories."""

from __future__ import annotations

import uuid

import factory
from faker import Faker

from app.models.school import School, SchoolStatus
from tests.factories.base import AsyncSQLAlchemyFactory

fake = Faker("fr_FR")


class SchoolFactory(AsyncSQLAlchemyFactory):
    """Factory for school tenants."""

    class Meta:
        model = School

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.LazyFunction(lambda: f"École {fake.last_name()}")
    name_ar = None
    code = factory.Sequence(lambda n: f"SCH-{n:04d}")
    massar_code = None
    status = SchoolStatus.ACTIVE.value
    address = factory.LazyFunction(lambda: fake.address().replace("\n", ", "))
    city = "Casablanca"
    region = "Casablanca-Settat"
    phone = factory.LazyFunction(lambda: f"+2126{fake.msisdn()[3:11]}")
    email = factory.LazyFunction(lambda: fake.unique.company_email())
    website = factory.LazyFunction(lambda: f"https://{fake.domain_word()}.ma")
    logo_path = None
    max_students = 600
    max_teachers = 60
    subscription_plan = "standard"
    subscription_expires_at = None
    timezone = "Africa/Casablanca"
    default_language = "fr"
    grading_scale = "moroccan_20"
    settings = factory.LazyFunction(
        lambda: {
            "timezone": "Africa/Casablanca",
            "default_language": "fr",
            "grading_scale": "moroccan_20",
        }
    )
