"""LMS factories."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import factory

from app.models.lms import (
    Assignment,
    Course,
    CourseStatus,
    ExerciseType,
    Grade,
    Quiz,
    QuizStatus,
    Submission,
    SubmissionStatus,
)
from tests.factories.base import AsyncSQLAlchemyFactory
from tests.factories.erp import AcademicYearFactory, ClassFactory
from tests.factories.iam import UserFactory
from tests.factories.school import SchoolFactory


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CourseFactory(AsyncSQLAlchemyFactory):
    """Factory for LMS courses."""

    class Meta:
        model = Course
        exclude = ("school", "academic_year", "class_obj", "teacher")

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
    teacher = factory.SubFactory(UserFactory, school=factory.SelfAttribute("..school"))
    school_id = factory.LazyAttribute(lambda o: o.school.id)
    class_id = factory.LazyAttribute(lambda o: o.class_obj.id)
    teacher_id = factory.LazyAttribute(lambda o: o.teacher.id)
    title = factory.Sequence(lambda n: f"Course {n}")
    description = factory.Sequence(lambda n: f"Description du cours {n}")
    status = CourseStatus.PUBLISHED.value


class AssignmentFactory(AsyncSQLAlchemyFactory):
    """Factory for assignments."""

    class Meta:
        model = Assignment
        exclude = ("course",)

    id = factory.LazyFunction(uuid.uuid4)
    course = factory.SubFactory(CourseFactory)
    course_id = factory.LazyAttribute(lambda o: o.course.id)
    teacher_id = factory.LazyAttribute(lambda o: o.course.teacher_id)
    title = factory.Sequence(lambda n: f"Assignment {n}")
    description = factory.Sequence(lambda n: f"Consigne {n}")
    due_at = factory.LazyFunction(lambda: _utc_now() + timedelta(days=7))
    total_points = 20
    grace_period_hours = 0
    late_penalty_per_day = 2.0
    max_late_days = 3
    allow_late = True
    exercise_type = ExerciseType.STANDARD.value
    rubric_id = None
    grade_category_id = None
    quiz_id = None
    exercise_pdf_path = None


class SubmissionFactory(AsyncSQLAlchemyFactory):
    """Factory for submissions."""

    class Meta:
        model = Submission
        exclude = ("assignment", "student")

    id = factory.LazyFunction(uuid.uuid4)
    assignment = factory.SubFactory(AssignmentFactory)
    student = factory.SubFactory(UserFactory)
    assignment_id = factory.LazyAttribute(lambda o: o.assignment.id)
    student_id = factory.LazyAttribute(lambda o: o.student.id)
    status = SubmissionStatus.DRAFT.value
    submitted_at = None


class GradeFactory(AsyncSQLAlchemyFactory):
    """Factory for grades."""

    class Meta:
        model = Grade
        exclude = ("submission",)

    id = factory.LazyFunction(uuid.uuid4)
    submission = factory.SubFactory(SubmissionFactory)
    submission_id = factory.LazyAttribute(lambda o: o.submission.id)
    teacher_id = factory.LazyAttribute(lambda o: o.submission.assignment.teacher_id)
    score = 15.0
    original_score = 15.0
    late_penalty = 0.0
    late_days = 0
    penalty_overridden = False
    feedback_text = "Bon travail"
    published_at = None


class QuizFactory(AsyncSQLAlchemyFactory):
    """Factory for quizzes."""

    class Meta:
        model = Quiz
        exclude = ("creator",)

    id = factory.LazyFunction(uuid.uuid4)
    creator = factory.SubFactory(UserFactory)
    school_id = factory.LazyAttribute(lambda o: o.creator.school_id)
    created_by = factory.LazyAttribute(lambda o: o.creator.id)
    title = factory.Sequence(lambda n: f"Quiz {n}")
    description = factory.Sequence(lambda n: f"Quiz de révision {n}")
    subject = "Mathématiques"
    level_band = "Collège"
    difficulty = "medium"
    time_limit_minutes = 20
    max_attempts = 1
    shuffle_questions = False
    status = QuizStatus.DRAFT.value
