"""Life-skills passport factories."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import factory

from app.models.skill_passport import (
    SkillDimension,
    SkillMilestone,
    SkillPassport,
    SkillProgress,
    SkillProgressStatus,
)
from tests.factories.base import AsyncSQLAlchemyFactory
from tests.factories.erp import AcademicYearFactory
from tests.factories.iam import UserFactory
from tests.factories.school import SchoolFactory


def _utc_now() -> datetime:
    return datetime.now(UTC)


class SkillDimensionFactory(AsyncSQLAlchemyFactory):
    """Factory for skill dimensions."""

    class Meta:
        model = SkillDimension

    id = factory.LazyFunction(uuid.uuid4)
    code = factory.Sequence(lambda n: f"autonomy_{n}")
    name_fr = factory.Sequence(lambda n: f"Autonomie {n}")
    name_ar = factory.Sequence(lambda n: f"الاستقلالية {n}")
    name_en = factory.Sequence(lambda n: f"Autonomy {n}")
    description_fr = "Capacite a apprendre et agir avec autonomie."
    icon = "autonomy-icon"
    display_order = factory.Sequence(lambda n: n)
    is_active = True


class SkillMilestoneFactory(AsyncSQLAlchemyFactory):
    """Factory for skill milestones."""

    class Meta:
        model = SkillMilestone
        exclude = ("dimension",)

    id = factory.LazyFunction(uuid.uuid4)
    dimension = factory.SubFactory(SkillDimensionFactory)
    dimension_id = factory.LazyAttribute(lambda o: o.dimension.id)
    code = factory.Sequence(lambda n: f"autonomy_level_{n + 1}")
    name_fr = factory.Sequence(lambda n: f"Niveau {n + 1}")
    name_ar = factory.Sequence(lambda n: f"المستوى {n + 1}")
    level = 1
    rule_config = {
        "metric": "submissions_on_time",
        "threshold": 1,
        "period_days": 30,
    }
    badge_icon = "badge-star"
    is_active = True


class SkillProgressFactory(AsyncSQLAlchemyFactory):
    """Factory for skill progress rows."""

    class Meta:
        model = SkillProgress
        exclude = ("school", "student", "milestone", "academic_year")

    id = factory.LazyFunction(uuid.uuid4)
    school = factory.SubFactory(SchoolFactory)
    student = factory.SubFactory(UserFactory, school=factory.SelfAttribute("..school"))
    academic_year = factory.SubFactory(
        AcademicYearFactory,
        school=factory.SelfAttribute("..school"),
    )
    milestone = factory.SubFactory(SkillMilestoneFactory)
    school_id = factory.LazyAttribute(lambda o: o.school.id)
    student_id = factory.LazyAttribute(lambda o: o.student.id)
    milestone_id = factory.LazyAttribute(lambda o: o.milestone.id)
    unlocked_at = None
    current_value = 0
    status = SkillProgressStatus.LOCKED.value
    evidence = None
    academic_year_id = factory.LazyAttribute(lambda o: o.academic_year.id)


class SkillPassportFactory(AsyncSQLAlchemyFactory):
    """Factory for generated skill passports."""

    class Meta:
        model = SkillPassport
        exclude = ("school", "student", "academic_year")

    id = factory.LazyFunction(uuid.uuid4)
    school = factory.SubFactory(SchoolFactory)
    student = factory.SubFactory(UserFactory, school=factory.SelfAttribute("..school"))
    academic_year = factory.SubFactory(
        AcademicYearFactory,
        school=factory.SelfAttribute("..school"),
    )
    school_id = factory.LazyAttribute(lambda o: o.school.id)
    student_id = factory.LazyAttribute(lambda o: o.student.id)
    academic_year_id = factory.LazyAttribute(lambda o: o.academic_year.id)
    generated_at = factory.LazyFunction(_utc_now)
    pdf_url = factory.LazyAttribute(
        lambda o: f"/generated/skill-passports/{o.id}.pdf"
    )
    total_milestones = 4
    unlocked_milestones = 2
    overall_score = 50


__all__ = [
    "SkillDimensionFactory",
    "SkillMilestoneFactory",
    "SkillProgressFactory",
    "SkillPassportFactory",
]
