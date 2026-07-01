"""factory_boy factories for onboarding models (not present in tests/factories/).

Follows the project's AsyncSQLAlchemyFactory pattern::

    app = await SchoolApplicationFactory.create(session, applicant_email="x@y.ma")
"""

from __future__ import annotations

import uuid

import factory

from app.models.onboarding import (
    ApplicationStatus,
    ApplicationType,
    AttachmentKind,
    SchoolApplication,
    SchoolApplicationAttachment,
)
from tests.factories.base import AsyncSQLAlchemyFactory


class SchoolApplicationFactory(AsyncSQLAlchemyFactory):
    class Meta:
        model = SchoolApplication

    id = factory.LazyFunction(uuid.uuid4)
    application_type = ApplicationType.MICRO_SCHOOL.value
    status = ApplicationStatus.PENDING.value
    applicant_name = factory.Sequence(lambda n: f"Applicant {n}")
    applicant_email = factory.Sequence(lambda n: f"applicant.{n}@example.ma")
    org_name = factory.Sequence(lambda n: f"Micro-école {n}")
    language = "fr"


class SchoolApplicationAttachmentFactory(AsyncSQLAlchemyFactory):
    class Meta:
        model = SchoolApplicationAttachment

    id = factory.LazyFunction(uuid.uuid4)
    file_path = factory.Sequence(lambda n: f"onboarding/doc-{n}.pdf")
    mime_type = "application/pdf"
    file_size = 1024
    kind = AttachmentKind.OTHER.value
