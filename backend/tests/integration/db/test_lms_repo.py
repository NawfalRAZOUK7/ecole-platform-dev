"""Integration tests for LMSRepository."""

from __future__ import annotations

from uuid import UUID

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.filtering import FilterItem, FilterSpec, SortSpec
from app.core.response import encode_cursor
from app.models.lms import SubmissionStatus
from app.repositories.lms import LMSRepository
from tests.factories.erp import AcademicYearFactory, ClassFactory
from tests.factories.iam import UserFactory
from tests.factories.school import SchoolFactory


def _uuid(n: int) -> UUID:
    return UUID(f"10000000-0000-4000-8000-{n:012d}")


async def _create_course_context(db_session, base: int) -> tuple[UUID, UUID, UUID, UUID]:
    school = await SchoolFactory.create(
        session=db_session,
        id=_uuid(base),
        code=f"school-{base}",
    )
    year = await AcademicYearFactory.create(
        session=db_session,
        id=_uuid(base + 1),
        school_id=school.id,
    )
    klass = await ClassFactory.create(
        session=db_session,
        id=_uuid(base + 2),
        school_id=school.id,
        academic_year_id=year.id,
        code=f"CLS-{base}",
    )
    teacher = await UserFactory.create(
        session=db_session,
        id=_uuid(base + 3),
        school_id=school.id,
        email=f"teacher-{base}@ecole.ma",
    )
    return school.id, year.id, klass.id, teacher.id


async def _create_student(db_session, school_id: UUID, base: int) -> UUID:
    student = await UserFactory.create(
        session=db_session,
        id=_uuid(base),
        school_id=school_id,
        email=f"student-{base}@ecole.ma",
    )
    return student.id


@pytest.mark.asyncio
async def test_create_and_get_course(db_session):
    repo = LMSRepository(db_session)
    school_id, _, class_id, teacher_id = await _create_course_context(db_session, 1)

    created = await repo.create_course(
        id=_uuid(10),
        school_id=school_id,
        class_id=class_id,
        teacher_id=teacher_id,
        title="Math 6A",
        description="Cours principal",
        status="published",
    )
    fetched = await repo.get_course(created.id)

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.title == "Math 6A"
    assert fetched.school_id == school_id


@pytest.mark.asyncio
async def test_list_courses_filters_by_teacher_classes_and_cursor(db_session):
    repo = LMSRepository(db_session)
    school_id, _, class_id, teacher_id = await _create_course_context(db_session, 20)
    _, _, other_class_id, other_teacher_id = await _create_course_context(db_session, 30)

    first = await repo.create_course(
        id=_uuid(40),
        school_id=school_id,
        class_id=class_id,
        teacher_id=teacher_id,
        title="Algebra",
        description="A",
        status="published",
    )
    second = await repo.create_course(
        id=_uuid(41),
        school_id=school_id,
        class_id=class_id,
        teacher_id=teacher_id,
        title="Geometry",
        description="G",
        status="published",
    )
    await repo.create_course(
        id=_uuid(42),
        school_id=school_id,
        class_id=other_class_id,
        teacher_id=other_teacher_id,
        title="Physics",
        description="P",
        status="published",
    )

    page_one, has_more = await repo.list_courses(
        school_id=school_id,
        class_id=None,
        teacher_class_ids={class_id},
        filters=FilterSpec(),
        sort=SortSpec(fields=[("id", "asc")]),
        search=None,
        cursor=None,
        limit=1,
    )

    assert [course.id for course in page_one] == [first.id]
    assert has_more is True

    page_two, second_has_more = await repo.list_courses(
        school_id=school_id,
        class_id=None,
        teacher_class_ids={class_id},
        filters=FilterSpec(),
        sort=SortSpec(fields=[("id", "asc")]),
        search=None,
        cursor=encode_cursor(first.id),
        limit=10,
    )

    assert [course.id for course in page_two] == [second.id]
    assert second_has_more is False


@pytest.mark.asyncio
async def test_list_courses_supports_search_and_status_filters(db_session):
    repo = LMSRepository(db_session)
    school_id, _, class_id, teacher_id = await _create_course_context(db_session, 50)

    await repo.create_course(
        id=_uuid(60),
        school_id=school_id,
        class_id=class_id,
        teacher_id=teacher_id,
        title="Arabic Literature",
        description="lit",
        status="published",
    )
    draft = await repo.create_course(
        id=_uuid(61),
        school_id=school_id,
        class_id=class_id,
        teacher_id=teacher_id,
        title="Arabic Grammar",
        description="grammar",
        status="draft",
    )
    await repo.create_course(
        id=_uuid(62),
        school_id=school_id,
        class_id=class_id,
        teacher_id=teacher_id,
        title="French Literature",
        description="fr",
        status="draft",
    )

    items, has_more = await repo.list_courses(
        school_id=school_id,
        class_id=class_id,
        teacher_class_ids=None,
        filters=FilterSpec(items=[FilterItem(field="status", operator="eq", value="draft")]),
        sort=SortSpec(fields=[("id", "asc")]),
        search="Arabic",
        cursor=None,
        limit=10,
    )

    assert has_more is False
    assert [course.id for course in items] == [draft.id]


@pytest.mark.asyncio
async def test_assignment_queries_return_course_context(db_session):
    repo = LMSRepository(db_session)
    school_id, _, class_id, teacher_id = await _create_course_context(db_session, 70)
    course = await repo.create_course(
        id=_uuid(80),
        school_id=school_id,
        class_id=class_id,
        teacher_id=teacher_id,
        title="History",
        description="course",
        status="published",
    )
    assignment = await repo.create_assignment(
        id=_uuid(81),
        course_id=course.id,
        teacher_id=teacher_id,
        title="Devoir Maison",
        description="Consigne",
        total_points=20,
        grace_period_hours=0,
        late_penalty_per_day=2.0,
        max_late_days=3,
        allow_late=True,
        exercise_type="STANDARD",
    )

    fetched = await repo.get_assignment(assignment.id)
    with_context = await repo.get_assignment_with_course(assignment.id)

    assert fetched is not None
    assert fetched.title == "Devoir Maison"
    assert with_context is not None
    loaded_assignment, loaded_course = with_context
    assert loaded_assignment.id == assignment.id
    assert loaded_course.id == course.id


@pytest.mark.asyncio
async def test_list_assignments_respects_course_filter_and_search(db_session):
    repo = LMSRepository(db_session)
    school_id, _, class_id, teacher_id = await _create_course_context(db_session, 90)
    course = await repo.create_course(
        id=_uuid(100),
        school_id=school_id,
        class_id=class_id,
        teacher_id=teacher_id,
        title="Science",
        description="course",
        status="published",
    )
    matching = await repo.create_assignment(
        id=_uuid(101),
        course_id=course.id,
        teacher_id=teacher_id,
        title="Quiz Chapter 1",
        description="Q1",
        total_points=20,
        grace_period_hours=0,
        late_penalty_per_day=2.0,
        max_late_days=3,
        allow_late=True,
        exercise_type="STANDARD",
    )
    await repo.create_assignment(
        id=_uuid(102),
        course_id=course.id,
        teacher_id=teacher_id,
        title="Essay Chapter 2",
        description="E2",
        total_points=20,
        grace_period_hours=0,
        late_penalty_per_day=2.0,
        max_late_days=3,
        allow_late=True,
        exercise_type="STANDARD",
    )

    items, has_more = await repo.list_assignments(
        school_id=school_id,
        course_id=course.id,
        filters=FilterSpec(),
        sort=SortSpec(fields=[("id", "asc")]),
        search="Quiz",
        cursor=None,
        limit=10,
    )

    assert has_more is False
    assert [item.id for item in items] == [matching.id]


@pytest.mark.asyncio
async def test_submission_queries_return_context_and_active_submission(db_session):
    repo = LMSRepository(db_session)
    school_id, _, class_id, teacher_id = await _create_course_context(db_session, 110)
    student_id = await _create_student(db_session, school_id, 114)
    course = await repo.create_course(
        id=_uuid(115),
        school_id=school_id,
        class_id=class_id,
        teacher_id=teacher_id,
        title="Physics",
        description="course",
        status="published",
    )
    assignment = await repo.create_assignment(
        id=_uuid(116),
        course_id=course.id,
        teacher_id=teacher_id,
        title="Lab Report",
        description="submit",
        total_points=20,
        grace_period_hours=0,
        late_penalty_per_day=2.0,
        max_late_days=3,
        allow_late=True,
        exercise_type="STANDARD",
    )
    submission = await repo.create_submission(
        id=_uuid(117),
        assignment_id=assignment.id,
        student_id=student_id,
        status=SubmissionStatus.SUBMITTED.value,
        submitted_at=None,
    )

    active = await repo.find_active_submission(
        assignment_id=assignment.id,
        student_id=student_id,
    )
    with_context = await repo.get_submission_with_context(submission.id)

    assert active is not None
    assert active.id == submission.id
    assert with_context is not None
    loaded_submission, loaded_assignment, loaded_course = with_context
    assert loaded_submission.id == submission.id
    assert loaded_assignment.id == assignment.id
    assert loaded_course.id == course.id


@pytest.mark.asyncio
async def test_find_active_submission_excludes_graded_rows(db_session):
    repo = LMSRepository(db_session)
    school_id, _, class_id, teacher_id = await _create_course_context(db_session, 130)
    student_id = await _create_student(db_session, school_id, 134)
    course = await repo.create_course(
        id=_uuid(135),
        school_id=school_id,
        class_id=class_id,
        teacher_id=teacher_id,
        title="Biology",
        description="course",
        status="published",
    )
    assignment = await repo.create_assignment(
        id=_uuid(136),
        course_id=course.id,
        teacher_id=teacher_id,
        title="Worksheet",
        description="submit",
        total_points=20,
        grace_period_hours=0,
        late_penalty_per_day=2.0,
        max_late_days=3,
        allow_late=True,
        exercise_type="STANDARD",
    )
    await repo.create_submission(
        id=_uuid(137),
        assignment_id=assignment.id,
        student_id=student_id,
        status=SubmissionStatus.GRADED.value,
        submitted_at=None,
    )

    active = await repo.find_active_submission(
        assignment_id=assignment.id,
        student_id=student_id,
    )

    assert active is None


@pytest.mark.asyncio
async def test_create_and_update_grade_for_submission(db_session):
    repo = LMSRepository(db_session)
    school_id, _, class_id, teacher_id = await _create_course_context(db_session, 150)
    student_id = await _create_student(db_session, school_id, 154)
    course = await repo.create_course(
        id=_uuid(155),
        school_id=school_id,
        class_id=class_id,
        teacher_id=teacher_id,
        title="Chemistry",
        description="course",
        status="published",
    )
    assignment = await repo.create_assignment(
        id=_uuid(156),
        course_id=course.id,
        teacher_id=teacher_id,
        title="Reaction Report",
        description="submit",
        total_points=20,
        grace_period_hours=0,
        late_penalty_per_day=2.0,
        max_late_days=3,
        allow_late=True,
        exercise_type="STANDARD",
    )
    submission = await repo.create_submission(
        id=_uuid(157),
        assignment_id=assignment.id,
        student_id=student_id,
        status=SubmissionStatus.SUBMITTED.value,
        submitted_at=None,
    )
    grade = await repo.create_grade(
        id=_uuid(158),
        submission_id=submission.id,
        teacher_id=teacher_id,
        score=14.5,
        original_score=14.5,
        late_penalty=0.0,
        late_days=0,
        penalty_overridden=False,
        feedback_text="Bon travail",
        published_at=None,
    )

    fetched = await repo.get_grade_for_submission(submission.id)
    assert fetched is not None
    assert float(fetched.score) == pytest.approx(14.5)

    fetched.feedback_text = "Excellent progression"
    updated = await repo.save_grade(fetched)

    assert updated.id == grade.id
    assert updated.feedback_text == "Excellent progression"


@pytest.mark.asyncio
async def test_create_submission_enforces_foreign_keys(db_session):
    repo = LMSRepository(db_session)

    with pytest.raises(IntegrityError):
        await repo.create_submission(
            id=_uuid(180),
            assignment_id=_uuid(181),
            student_id=_uuid(182),
            status=SubmissionStatus.DRAFT.value,
            submitted_at=None,
        )

    await db_session.rollback()
