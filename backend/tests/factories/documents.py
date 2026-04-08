"""Document factories."""

from __future__ import annotations

import secrets
import uuid

import factory

from app.models.documents import (
    Document,
    DocumentCategory,
    Resource,
    ResourceType,
    ResourceVisibility,
)
from tests.factories.base import AsyncSQLAlchemyFactory
from tests.factories.iam import UserFactory
from tests.factories.school import SchoolFactory


class DocumentFactory(AsyncSQLAlchemyFactory):
    """Factory for uploaded documents."""

    class Meta:
        model = Document
        exclude = ("school", "uploader")

    id = factory.LazyFunction(uuid.uuid4)
    school = factory.SubFactory(SchoolFactory)
    uploader = factory.SubFactory(UserFactory, school=factory.SelfAttribute("..school"))
    school_id = factory.LazyAttribute(lambda o: o.school.id)
    uploader_id = factory.LazyAttribute(lambda o: o.uploader.id)
    filename = "bulletin-test.pdf"
    original_filename = "Bulletin scolaire.pdf"
    mime_type = "application/pdf"
    size_bytes = 1024
    sha256 = factory.LazyFunction(lambda: secrets.token_hex(32))
    storage_path = "/docs/test.pdf"
    thumbnail_path = None
    category = DocumentCategory.REPORT_CARD.value
    linked_student_id = None
    expires_at = None
    download_count = 0


class ResourceFactory(AsyncSQLAlchemyFactory):
    """Factory for shared educational resources."""

    class Meta:
        model = Resource
        exclude = ("school", "uploader", "document")

    id = factory.LazyFunction(uuid.uuid4)
    school = factory.SubFactory(SchoolFactory)
    uploader = factory.SubFactory(UserFactory, school=factory.SelfAttribute("..school"))
    document = factory.SubFactory(
        DocumentFactory,
        school=factory.SelfAttribute("..school"),
        uploader=factory.SelfAttribute("..uploader"),
    )
    school_id = factory.LazyAttribute(lambda o: o.school.id)
    uploader_id = factory.LazyAttribute(lambda o: o.uploader.id)
    title = "Ressource pédagogique"
    description = "Support de cours"
    subject = "Mathématiques"
    level = "1BAC"
    type = ResourceType.LESSON_PLAN.value
    tags = factory.LazyFunction(lambda: ["pedagogie", "maroc"])
    file_id = factory.LazyAttribute(lambda o: o.document.id)
    visibility = ResourceVisibility.SCHOOL.value
    class_id = None
    download_count = 0
    avg_rating = 0.0
    rating_count = 0
