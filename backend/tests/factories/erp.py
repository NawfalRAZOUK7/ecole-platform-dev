"""ERP factories."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

import factory
from faker import Faker

from app.models.erp import (
    AcademicYear,
    AttendanceRecord,
    AttendanceSession,
    AttendanceStatus,
    Class,
    Enrollment,
    EnrollmentStatus,
    Period,
    PeriodStatus,
)
from tests.factories.base import AsyncSQLAlchemyFactory
from tests.factories.iam import UserFactory
from tests.factories.school import SchoolFactory

fake = Faker("fr_FR")


def _today() -> date:
    return date.today()


class AcademicYearFactory(AsyncSQLAlchemyFactory):
    """Factory for academic years."""

    class Meta:
        model = AcademicYear
        exclude = ("school",)

    id = factory.LazyFunction(uuid.uuid4)
    school = factory.SubFactory(SchoolFactory)
    school_id = factory.LazyAttribute(lambda o: o.school.id)
    label = factory.Sequence(lambda n: f"2025-2026-{n}")
    date_start = date(2025, 9, 1)
    date_end = date(2026, 7, 15)


class PeriodFactory(AsyncSQLAlchemyFactory):
    """Factory for school periods."""

    class Meta:
        model = Period
        exclude = ("school", "academic_year")

    id = factory.LazyFunction(uuid.uuid4)
    school = factory.SubFactory(SchoolFactory)
    academic_year = factory.SubFactory(
        AcademicYearFactory, school=factory.SelfAttribute("..school")
    )
    school_id = factory.LazyAttribute(lambda o: o.school.id)
    academic_year_id = factory.LazyAttribute(lambda o: o.academic_year.id)
    label = factory.Sequence(lambda n: f"Trimester {n}")
    status = PeriodStatus.ACTIVE.value
    date_start = date(2025, 9, 1)
    date_end = date(2025, 12, 31)


class ClassFactory(AsyncSQLAlchemyFactory):
    """Factory for classes."""

    class Meta:
        model = Class
        exclude = ("school", "academic_year")

    id = factory.LazyFunction(uuid.uuid4)
    school = factory.SubFactory(SchoolFactory)
    academic_year = factory.SubFactory(
        AcademicYearFactory, school=factory.SelfAttribute("..school")
    )
    school_id = factory.LazyAttribute(lambda o: o.school.id)
    academic_year_id = factory.LazyAttribute(lambda o: o.academic_year.id)
    code = factory.Sequence(lambda n: f"CLS-{n:03d}")
    name = factory.Sequence(lambda n: f"Classe {n}")


class EnrollmentFactory(AsyncSQLAlchemyFactory):
    """Factory for student enrollments."""

    class Meta:
        model = Enrollment
        exclude = ("school", "academic_year", "class_obj", "period", "student")

    id = factory.LazyFunction(uuid.uuid4)
    school = factory.SubFactory(SchoolFactory)
    academic_year = factory.SubFactory(
        AcademicYearFactory, school=factory.SelfAttribute("..school")
    )
    class_obj = factory.SubFactory(
        ClassFactory,
        school=factory.SelfAttribute("..school"),
        academic_year=factory.SelfAttribute("..academic_year"),
    )
    period = factory.SubFactory(
        PeriodFactory,
        school=factory.SelfAttribute("..school"),
        academic_year=factory.SelfAttribute("..academic_year"),
    )
    student = factory.SubFactory(UserFactory, school=factory.SelfAttribute("..school"))
    school_id = factory.LazyAttribute(lambda o: o.school.id)
    student_id = factory.LazyAttribute(lambda o: o.student.id)
    class_id = factory.LazyAttribute(lambda o: o.class_obj.id)
    period_id = factory.LazyAttribute(lambda o: o.period.id)
    status = EnrollmentStatus.ACTIVE.value


class AttendanceSessionFactory(AsyncSQLAlchemyFactory):
    """Factory for attendance sessions."""

    class Meta:
        model = AttendanceSession
        exclude = ("school", "academic_year", "class_obj", "period", "teacher")

    id = factory.LazyFunction(uuid.uuid4)
    school = factory.SubFactory(SchoolFactory)
    academic_year = factory.SubFactory(
        AcademicYearFactory, school=factory.SelfAttribute("..school")
    )
    class_obj = factory.SubFactory(
        ClassFactory,
        school=factory.SelfAttribute("..school"),
        academic_year=factory.SelfAttribute("..academic_year"),
    )
    period = factory.SubFactory(
        PeriodFactory,
        school=factory.SelfAttribute("..school"),
        academic_year=factory.SelfAttribute("..academic_year"),
    )
    teacher = factory.SubFactory(UserFactory, school=factory.SelfAttribute("..school"))
    school_id = factory.LazyAttribute(lambda o: o.school.id)
    class_id = factory.LazyAttribute(lambda o: o.class_obj.id)
    period_id = factory.LazyAttribute(lambda o: o.period.id)
    teacher_id = factory.LazyAttribute(lambda o: o.teacher.id)
    session_date = factory.LazyFunction(_today)
    slot = "morning"


class AttendanceRecordFactory(AsyncSQLAlchemyFactory):
    """Factory for attendance records."""

    class Meta:
        model = AttendanceRecord
        exclude = ("attendance_session", "student")

    id = factory.LazyFunction(uuid.uuid4)
    attendance_session = factory.SubFactory(AttendanceSessionFactory)
    student = factory.SubFactory(UserFactory)
    school_id = factory.LazyAttribute(lambda o: o.attendance_session.school_id)
    attendance_session_id = factory.LazyAttribute(lambda o: o.attendance_session.id)
    student_id = factory.LazyAttribute(lambda o: o.student.id)
    status = AttendanceStatus.PRESENT.value
    absence_reason = None
