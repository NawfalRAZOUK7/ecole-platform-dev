"""MEN compliance factories."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import factory

from app.models.men_compliance import (
    ComplianceReport,
    CurriculumMapping,
    MenCurriculum,
    MenObjective,
)
from tests.factories.base import AsyncSQLAlchemyFactory
from tests.factories.erp import AcademicYearFactory
from tests.factories.iam import UserFactory
from tests.factories.lms import CourseFactory
from tests.factories.school import SchoolFactory


def _utc_now() -> datetime:
    return datetime.now(UTC)


class MenCurriculumFactory(AsyncSQLAlchemyFactory):
    """Factory for MEN curricula."""

    class Meta:
        model = MenCurriculum

    id = factory.LazyFunction(uuid.uuid4)
    level = "college"
    grade = "3eme"
    subject = factory.Sequence(lambda n: f"mathematics_{n}")
    academic_year = "2025-2026"
    version = "1.0"
    is_active = True


class MenObjectiveFactory(AsyncSQLAlchemyFactory):
    """Factory for MEN objectives."""

    class Meta:
        model = MenObjective
        exclude = ("curriculum",)

    id = factory.LazyFunction(uuid.uuid4)
    curriculum = factory.SubFactory(MenCurriculumFactory)
    curriculum_id = factory.LazyAttribute(lambda o: o.curriculum.id)
    code = factory.Sequence(lambda n: f"MATH-3C-{n + 1:02d}")
    title_fr = factory.Sequence(lambda n: f"Objectif {n + 1}")
    title_ar = factory.Sequence(lambda n: f"الهدف {n + 1}")
    description_fr = "Objectif MEN de démonstration"
    trimester = 1
    unit_number = 1
    is_mandatory = True
    hours_recommended = Decimal("2.00")
    display_order = factory.Sequence(lambda n: n + 1)


class CurriculumMappingFactory(AsyncSQLAlchemyFactory):
    """Factory for curriculum mappings."""

    class Meta:
        model = CurriculumMapping
        exclude = ("school", "objective", "course", "mapper")

    id = factory.LazyFunction(uuid.uuid4)
    school = factory.SubFactory(SchoolFactory)
    objective = factory.SubFactory(MenObjectiveFactory)
    course = factory.SubFactory(CourseFactory, school=factory.SelfAttribute("..school"))
    mapper = factory.SubFactory(UserFactory, school=factory.SelfAttribute("..school"))
    school_id = factory.LazyAttribute(lambda o: o.school.id)
    objective_id = factory.LazyAttribute(lambda o: o.objective.id)
    course_id = factory.LazyAttribute(lambda o: o.course.id)
    content_item_id = None
    mapped_by = factory.LazyAttribute(lambda o: o.mapper.id)
    mapped_at = factory.LazyFunction(_utc_now)
    coverage_percent = 100
    notes = "Couverture complète"


class ComplianceReportFactory(AsyncSQLAlchemyFactory):
    """Factory for compliance reports."""

    class Meta:
        model = ComplianceReport
        exclude = ("school", "curriculum", "generator", "academic_year")

    id = factory.LazyFunction(uuid.uuid4)
    school = factory.SubFactory(SchoolFactory)
    curriculum = factory.SubFactory(MenCurriculumFactory)
    generator = factory.SubFactory(
        UserFactory, school=factory.SelfAttribute("..school")
    )
    academic_year = factory.SubFactory(
        AcademicYearFactory,
        school=factory.SelfAttribute("..school"),
    )
    school_id = factory.LazyAttribute(lambda o: o.school.id)
    curriculum_id = factory.LazyAttribute(lambda o: o.curriculum.id)
    generated_at = factory.LazyFunction(_utc_now)
    generated_by = factory.LazyAttribute(lambda o: o.generator.id)
    total_objectives = 10
    mapped_objectives = 7
    compliance_percent = Decimal("70.00")
    unmapped_objectives = factory.LazyFunction(
        lambda: ["MATH-3C-08", "MATH-3C-09", "MATH-3C-10"]
    )
    pdf_url = factory.LazyAttribute(
        lambda o: f"/generated/compliance-reports/{o.id}.pdf"
    )
    academic_year_id = factory.LazyAttribute(lambda o: o.academic_year.id)


__all__ = [
    "MenCurriculumFactory",
    "MenObjectiveFactory",
    "CurriculumMappingFactory",
    "ComplianceReportFactory",
]
