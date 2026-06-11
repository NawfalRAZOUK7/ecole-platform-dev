"""Fluent builders for onboarding test data.

Produce either an HTTP *apply* payload (dict for the public endpoints) or a
``SchoolApplication`` model instance (for service/DB tests)::

    from tests._support.builders import SchoolApplicationBuilder

    payload = SchoolApplicationBuilder().micro_school().with_email("x@y.ma").as_payload()
    model   = SchoolApplicationBuilder().formal_school().as_model()
"""

from __future__ import annotations

import uuid

from app.models.onboarding import ApplicationStatus, ApplicationType, SchoolApplication


class SchoolApplicationBuilder:
    def __init__(self) -> None:
        self._type: str = ApplicationType.MICRO_SCHOOL.value
        self._name: str = "Mr Idrissi"
        self._email: str | None = None
        self._org: str = "Micro-école Espoir"
        self._language: str = "fr"
        self._status: str = ApplicationStatus.PENDING.value

    def micro_school(self) -> "SchoolApplicationBuilder":
        self._type = ApplicationType.MICRO_SCHOOL.value
        return self

    def formal_school(self) -> "SchoolApplicationBuilder":
        self._type = ApplicationType.FORMAL_SCHOOL.value
        return self

    def with_name(self, name: str) -> "SchoolApplicationBuilder":
        self._name = name
        return self

    def with_email(self, email: str) -> "SchoolApplicationBuilder":
        self._email = email
        return self

    def with_org(self, org_name: str) -> "SchoolApplicationBuilder":
        self._org = org_name
        return self

    def in_language(self, language: str) -> "SchoolApplicationBuilder":
        self._language = language
        return self

    def _resolved_email(self) -> str:
        return self._email or f"owner.{uuid.uuid4().hex[:8]}@example.ma"

    def as_payload(self) -> dict[str, str]:
        """Dict suitable for POST /applications/{formal-school,micro-school}."""
        return {
            "applicant_name": self._name,
            "applicant_email": self._resolved_email(),
            "org_name": self._org,
            "language": self._language,
        }

    def as_model(self) -> SchoolApplication:
        """A persistable ``SchoolApplication`` instance (status=pending)."""
        return SchoolApplication(
            application_type=self._type,
            status=self._status,
            applicant_name=self._name,
            applicant_email=self._resolved_email(),
            org_name=self._org,
            language=self._language,
        )
