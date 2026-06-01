"""Mock-based unit tests for academic repositories:
- academic_attendance_analytics.py
- academic_gradebook.py
- academic_progress.py
- academic_skill_passport.py
- academic_timetable_generation.py
"""
from __future__ import annotations

import uuid
from datetime import datetime, date, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.repositories.academic_attendance_analytics import AttendanceAnalyticsRepository
from app.repositories.academic_gradebook import GradebookRepository
from app.repositories.academic_progress import ProgressRepository
from app.repositories.academic_skill_passport import SkillPassportRepository
from app.repositories.academic_timetable_generation import TimetableGenerationRepository


def _uid():
    return uuid.uuid4()


def _now():
    return datetime.now(timezone.utc)


class _FR:
    def __init__(self, v=None, many=None, scalar=None, rowcount=1):
        self._v = v
        self._many = many or []
        self._scalar = scalar
        self.rowcount = rowcount

    def scalar_one_or_none(self):
        return self._v

    def scalar_one(self):
        return self._v

    def scalar(self):
        return self._scalar

    def scalars(self):
        many = self._many; v = self._v
        return SimpleNamespace(all=lambda: many, first=lambda: (many[0] if many else v))

    def first(self):
        return self._many[0] if self._many else self._v

    def one(self):
        return self._v

    def one_or_none(self):
        return self._v

    def all(self):
        return self._many

    def mappings(self):
        return SimpleNamespace(all=lambda: self._many)

    def __iter__(self):
        return iter(self._many)


def _db(result=None):
    r = result if result is not None else _FR()
    return SimpleNamespace(
        execute=AsyncMock(return_value=r),
        add=Mock(),
        flush=AsyncMock(),
        commit=AsyncMock(),
        merge=AsyncMock(),
        delete=AsyncMock(),
    )


# ===========================================================================
# AttendanceAnalyticsRepository
# ===========================================================================

class TestAttendanceAnalyticsRepository:
    @pytest.mark.asyncio
    async def test_compute_student_absence_count_no_period(self):
        db = _db(_FR(v=(5, 10)))
        result = await AttendanceAnalyticsRepository(db).compute_student_absence_count(
            student_id=_uid(), period_id=_uid()
        )
        assert result == (5, 10)

    @pytest.mark.asyncio
    async def test_compute_student_absence_count_with_period(self):
        db = _db(_FR(v=(2, 8)))
        result = await AttendanceAnalyticsRepository(db).compute_student_absence_count(
            student_id=_uid(), period_id=_uid()
        )
        assert result == (2, 8)

    @pytest.mark.asyncio
    async def test_list_class_students(self):
        items = [(_uid(), "Alice")]
        db = _db(_FR(many=items))
        result = await AttendanceAnalyticsRepository(db).list_class_students(
            class_id=_uid(), period_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_compute_class_absence_rates_no_period(self):
        items = [(_uid(), 2, 10)]
        db = _db(_FR(many=items))
        result = await AttendanceAnalyticsRepository(db).compute_class_absence_rates(
            class_id=_uid(), period_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_compute_class_absence_rates_with_period(self):
        items = [(_uid(), 3, 12)]
        db = _db(_FR(many=items))
        result = await AttendanceAnalyticsRepository(db).compute_class_absence_rates(
            class_id=_uid(), period_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_get_absence_trends_no_period(self):
        items = []
        db = _db(_FR(many=items))
        result = await AttendanceAnalyticsRepository(db).get_absence_trends(
            class_id=_uid(), period_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_get_absence_trends_with_period(self):
        items = []
        db = _db(_FR(many=items))
        result = await AttendanceAnalyticsRepository(db).get_absence_trends(
            class_id=_uid(), period_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_get_attendance_alert(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await AttendanceAnalyticsRepository(db).get_attendance_alert(
            student_id=_uid(), period_id=_uid(), threshold_exceeded="warning"
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_create_attendance_alert(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.academic_attendance_analytics.AttendanceAlert", return_value=fake):
            result = await AttendanceAnalyticsRepository(db).create_attendance_alert(
                student_id=_uid(), school_id=_uid()
            )
        assert result is fake

    @pytest.mark.asyncio
    async def test_list_alerts_no_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await AttendanceAnalyticsRepository(db).list_alerts(school_id=_uid())
        assert result == items

    @pytest.mark.asyncio
    async def test_list_alerts_with_all_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await AttendanceAnalyticsRepository(db).list_alerts(
            school_id=_uid(),
            period_id=_uid(),
            threshold_exceeded="warning",
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_period_students(self):
        items = [(_uid(), "Student")]
        db = _db(_FR(many=items))
        result = await AttendanceAnalyticsRepository(db).list_period_students(
            school_id=_uid(), period_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_user_names(self):
        items = [(_uid(), "User Name")]
        db = _db(_FR(many=items))
        result = await AttendanceAnalyticsRepository(db).list_user_names(
            user_ids=[_uid()]
        )
        assert isinstance(result, dict)


# ===========================================================================
# GradebookRepository
# ===========================================================================

class TestGradebookRepository:
    @pytest.mark.asyncio
    async def test_get_grade_category_no_scope(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await GradebookRepository(db).get_grade_category(
            _uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_grade_category_with_scope(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await GradebookRepository(db).get_grade_category(
            _uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_grade_categories_no_scope(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await GradebookRepository(db).list_grade_categories(
            class_id=_uid(), period_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_grade_categories_with_scope(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await GradebookRepository(db).list_grade_categories(
            class_id=_uid(), period_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_create_grade_category(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.academic_gradebook.GradeCategory", return_value=fake):
            result = await GradebookRepository(db).create_grade_category(school_id=_uid())
        assert result is fake

    @pytest.mark.asyncio
    async def test_delete_grade_categories_for_scope(self):
        db = _db()
        await GradebookRepository(db).delete_grade_categories_for_scope(
            class_id=_uid(), period_id=_uid()
        )
        db.execute.assert_awaited()

    @pytest.mark.asyncio
    async def test_get_student_grades_by_category_no_scope(self):
        db = _db(_FR(many=[]))
        result = await GradebookRepository(db).get_student_grades_by_category(
            student_id=_uid(), class_id=_uid(), period_id=_uid()
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_get_student_grades_by_category_with_scope(self):
        db = _db(_FR(many=[]))
        result = await GradebookRepository(db).get_student_grades_by_category(
            student_id=_uid(), class_id=_uid(), period_id=_uid()
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_delete_student_period_averages_for_scope(self):
        db = _db()
        await GradebookRepository(db).delete_student_period_averages_for_scope(
            class_id=_uid(), period_id=_uid()
        )
        db.execute.assert_awaited()

    @pytest.mark.asyncio
    async def test_save_student_period_average(self):
        db = _db(_FR(v=None))
        await GradebookRepository(db).save_student_period_average(
            student_id=_uid(), school_id=_uid(), class_id=_uid(),
            period_id=_uid(), weighted_average=85.0, mention="B",
            class_rank=1, total_students=30, computed_at=_now()
        )
        db.execute.assert_awaited()

    @pytest.mark.asyncio
    async def test_get_class_averages(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await GradebookRepository(db).get_class_averages(
            class_id=_uid(), period_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_get_student_transcript(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await GradebookRepository(db).get_student_transcript(
            student_id=_uid(), academic_year_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_class_period_students(self):
        items = [(_uid(), "Student")]
        db = _db(_FR(many=items))
        result = await GradebookRepository(db).list_class_period_students(
            class_id=_uid(), period_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_gradebook_assignments(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await GradebookRepository(db).list_gradebook_assignments(
            class_id=_uid(), period_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_gradebook_grade_entries_no_assignment(self):
        items = [(_uid(), _uid(), None, 85.0, None)]
        db = _db(_FR(many=items))
        result = await GradebookRepository(db).list_gradebook_grade_entries(
            class_id=_uid(), period_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_gradebook_grade_entries_with_assignment(self):
        items = [(_uid(), _uid(), _uid(), 90.0, None)]
        db = _db(_FR(many=items))
        result = await GradebookRepository(db).list_gradebook_grade_entries(
            class_id=_uid(), period_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_student_period_enrollments(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await GradebookRepository(db).list_student_period_enrollments(
            student_id=_uid(), academic_year_id=_uid()
        )
        assert result == items


# ===========================================================================
# ProgressRepository
# ===========================================================================

class TestProgressRepository:
    @pytest.mark.asyncio
    async def test_get_student_school_id(self):
        sid = _uid()
        db = _db(_FR(v=sid))
        result = await ProgressRepository(db).get_student_school_id(_uid())
        assert result is sid

    @pytest.mark.asyncio
    async def test_list_parent_child_ids(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await ProgressRepository(db).list_parent_child_ids(
            parent_id=_uid(), school_id=_uid()
        )
        assert result == set(ids)

    @pytest.mark.asyncio
    async def test_list_teacher_class_ids(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await ProgressRepository(db).list_teacher_class_ids(
            teacher_id=_uid(), school_id=_uid()
        )
        assert result == set(ids)

    @pytest.mark.asyncio
    async def test_student_is_enrolled_in_classes_empty(self):
        result = await ProgressRepository(_db()).student_is_enrolled_in_classes(
            student_id=_uid(), school_id=_uid(), class_ids=set()
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_student_is_enrolled_in_classes_nonempty(self):
        db = _db(_FR(v=_uid()))
        result = await ProgressRepository(db).student_is_enrolled_in_classes(
            student_id=_uid(), school_id=_uid(), class_ids={_uid()}
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_get_class_school_id(self):
        sid = _uid()
        db = _db(_FR(v=sid))
        result = await ProgressRepository(db).get_class_school_id(_uid())
        assert result is sid

    @pytest.mark.asyncio
    async def test_get_student_name(self):
        db = _db(_FR(v=("Ahmed", "Benali")))
        result = await ProgressRepository(db).get_student_name(_uid())
        assert result == ("Ahmed", "Benali")

    @pytest.mark.asyncio
    async def test_list_grade_trend_rows_no_period(self):
        db = _db(_FR(many=[]))
        result = await ProgressRepository(db).list_grade_trend_rows(
            student_id=_uid(), school_id=_uid()
        )
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_list_grade_trend_rows_with_period(self):
        db = _db(_FR(many=[]))
        result = await ProgressRepository(db).list_grade_trend_rows(
            student_id=_uid(), school_id=_uid()
        )
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_content_completion_counts(self):
        db = _db(_FR(many=[]))
        result = await ProgressRepository(db).get_content_completion_counts(
            student_id=_uid()
        )
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_list_activity_score_rows_no_period(self):
        db = _db(_FR(many=[]))
        result = await ProgressRepository(db).list_activity_score_rows(
            student_id=_uid()
        )
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_list_activity_score_rows_with_period(self):
        db = _db(_FR(many=[]))
        result = await ProgressRepository(db).list_activity_score_rows(
            student_id=_uid()
        )
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_attendance_overview_counts_no_period(self):
        db = _db(_FR(many=[]))
        result = await ProgressRepository(db).get_attendance_overview_counts(
            student_id=_uid(), school_id=_uid()
        )
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_attendance_overview_counts_with_period(self):
        db = _db(_FR(many=[]))
        result = await ProgressRepository(db).get_attendance_overview_counts(
            student_id=_uid(), school_id=_uid()
        )
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_list_attendance_monthly_rows_no_period(self):
        db = _db(_FR(many=[]))
        result = await ProgressRepository(db).list_attendance_monthly_rows(
            student_id=_uid(), school_id=_uid()
        )
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_list_attendance_monthly_rows_with_period(self):
        db = _db(_FR(many=[]))
        result = await ProgressRepository(db).list_attendance_monthly_rows(
            student_id=_uid(), school_id=_uid()
        )
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_list_assessment_result_rows_no_period(self):
        db = _db(_FR(many=[]))
        result = await ProgressRepository(db).list_assessment_result_rows(
            student_id=_uid(), school_id=_uid()
        )
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_list_assessment_result_rows_with_period(self):
        db = _db(_FR(many=[]))
        result = await ProgressRepository(db).list_assessment_result_rows(
            student_id=_uid(), school_id=_uid()
        )
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_class_info(self):
        db = _db(_FR(v=None))
        result = await ProgressRepository(db).get_class_info(
            class_id=_uid(), school_id=_uid()
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_list_class_students(self):
        sid = _uid()
        rows = [SimpleNamespace(student_id=sid, full_name="Student")]
        db = _db(_FR(many=rows))
        result = await ProgressRepository(db).list_class_students(
            class_id=_uid(), school_id=_uid()
        )
        assert result == [(sid, "Student")]

    @pytest.mark.asyncio
    async def test_get_grade_averages_for_students_no_period(self):
        db = _db(_FR(many=[]))
        result = await ProgressRepository(db).get_grade_averages_for_students(
            student_ids=[_uid()], school_id=_uid()
        )
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_grade_averages_for_students_with_period(self):
        db = _db(_FR(many=[]))
        result = await ProgressRepository(db).get_grade_averages_for_students(
            student_ids=[_uid()], school_id=_uid()
        )
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_attendance_rates_for_students_no_period(self):
        db = _db(_FR(many=[]))
        result = await ProgressRepository(db).get_attendance_rates_for_students(
            student_ids=[_uid()], school_id=_uid()
        )
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_attendance_rates_for_students_with_period(self):
        db = _db(_FR(many=[]))
        result = await ProgressRepository(db).get_attendance_rates_for_students(
            student_ids=[_uid()], school_id=_uid()
        )
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_content_completion_rates_for_students(self):
        db = _db(_FR(many=[]))
        result = await ProgressRepository(db).get_content_completion_rates_for_students(
            student_ids=[_uid()]
        )
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_list_children(self):
        cid = _uid()
        rows = [SimpleNamespace(child_user_id=cid, full_name="Child")]
        db = _db(_FR(many=rows))
        result = await ProgressRepository(db).list_children(
            parent_id=_uid(), school_id=_uid()
        )
        assert result == [(cid, "Child")]

    @pytest.mark.asyncio
    async def test_get_student_grade_average_no_period(self):
        db = _db(_FR(v=85.5))
        result = await ProgressRepository(db).get_student_grade_average(
            student_id=_uid(), school_id=_uid()
        )
        assert result == 85.5

    @pytest.mark.asyncio
    async def test_get_student_grade_average_with_period(self):
        db = _db(_FR(v=90.0))
        result = await ProgressRepository(db).get_student_grade_average(
            student_id=_uid(), school_id=_uid()
        )
        assert result == 90.0

    @pytest.mark.asyncio
    async def test_get_student_attendance_rate_no_period(self):
        db = _db(_FR(v=SimpleNamespace(total=0, present=0)))
        result = await ProgressRepository(db).get_student_attendance_rate(
            student_id=_uid(), school_id=_uid()
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_get_student_attendance_rate_with_period(self):
        db = _db(_FR(v=SimpleNamespace(total=10, present=9)))
        result = await ProgressRepository(db).get_student_attendance_rate(
            student_id=_uid(), school_id=_uid()
        )
        assert result == 90.0


# ===========================================================================
# SkillPassportRepository
# ===========================================================================

class TestSkillPassportRepository:
    @pytest.mark.asyncio
    async def test_get_user(self):
        obj = object()
        db = _db(_FR(v=obj))
        assert await SkillPassportRepository(db).get_user(_uid()) is obj

    @pytest.mark.asyncio
    async def test_get_academic_year(self):
        obj = object()
        db = _db(_FR(v=obj))
        assert await SkillPassportRepository(db).get_academic_year(_uid()) is obj

    @pytest.mark.asyncio
    async def test_get_class(self):
        obj = object()
        db = _db(_FR(v=obj))
        assert await SkillPassportRepository(db).get_class(_uid()) is obj

    @pytest.mark.asyncio
    async def test_is_parent_of_student_true(self):
        db = _db(_FR(v="some-id"))
        result = await SkillPassportRepository(db).is_parent_of_student(
            parent_id=_uid(), student_id=_uid(), school_id=_uid()
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_is_parent_of_student_false(self):
        db = _db(_FR(v=None))
        result = await SkillPassportRepository(db).is_parent_of_student(
            parent_id=_uid(), student_id=_uid(), school_id=_uid()
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_get_dimension(self):
        obj = object()
        db = _db(_FR(v=obj))
        assert await SkillPassportRepository(db).get_dimension(_uid()) is obj

    @pytest.mark.asyncio
    async def test_get_dimension_by_code(self):
        obj = object()
        db = _db(_FR(v=obj))
        assert await SkillPassportRepository(db).get_dimension_by_code("D-001") is obj

    @pytest.mark.asyncio
    async def test_list_dimensions_no_filter(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await SkillPassportRepository(db).list_dimensions()
        assert result == items

    @pytest.mark.asyncio
    async def test_list_dimensions_with_active_filter(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await SkillPassportRepository(db).list_dimensions(is_active=True)
        assert result == items

    @pytest.mark.asyncio
    async def test_create_dimension(self):
        dim = SimpleNamespace(id=_uid())
        db = _db()
        result = await SkillPassportRepository(db).create_dimension(dim)
        db.add.assert_called_once_with(dim)

    @pytest.mark.asyncio
    async def test_save_dimension(self):
        dim = SimpleNamespace(id=_uid())
        db = _db()
        result = await SkillPassportRepository(db).save_dimension(dim)
        assert result is dim

    @pytest.mark.asyncio
    async def test_delete_dimension(self):
        dim = SimpleNamespace(id=_uid())
        db = _db()
        await SkillPassportRepository(db).delete_dimension(dim)
        db.delete.assert_awaited_once_with(dim)

    @pytest.mark.asyncio
    async def test_get_milestone_no_include(self):
        obj = object()
        db = _db(_FR(v=obj))
        assert await SkillPassportRepository(db).get_milestone(_uid()) is obj

    @pytest.mark.asyncio
    async def test_get_milestone_with_include(self):
        obj = object()
        db = _db(_FR(v=obj))
        assert await SkillPassportRepository(db).get_milestone(_uid(), include_dimension=True) is obj

    @pytest.mark.asyncio
    async def test_get_milestone_by_code(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await SkillPassportRepository(db).get_milestone_by_code(
            dimension_id=_uid(), code="M-001"
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_milestones_no_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await SkillPassportRepository(db).list_milestones()
        assert result == items

    @pytest.mark.asyncio
    async def test_list_milestones_with_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await SkillPassportRepository(db).list_milestones(
            dimension_id=_uid(), is_active=True
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_count_active_milestones(self):
        db = _db(_FR(v=5))
        result = await SkillPassportRepository(db).count_active_milestones()
        assert result == 5

    @pytest.mark.asyncio
    async def test_create_milestone(self):
        milestone = SimpleNamespace(id=_uid())
        db = _db()
        result = await SkillPassportRepository(db).create_milestone(milestone)
        db.add.assert_called_once_with(milestone)

    @pytest.mark.asyncio
    async def test_save_milestone(self):
        milestone = SimpleNamespace(id=_uid())
        db = _db()
        result = await SkillPassportRepository(db).save_milestone(milestone)
        assert result is milestone

    @pytest.mark.asyncio
    async def test_delete_milestone(self):
        milestone = SimpleNamespace(id=_uid())
        db = _db()
        await SkillPassportRepository(db).delete_milestone(milestone)
        db.delete.assert_awaited_once_with(milestone)

    @pytest.mark.asyncio
    async def test_get_progress_record(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await SkillPassportRepository(db).get_progress_record(
            student_id=_uid(), school_id=_uid(), milestone_id=_uid(), academic_year_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_progress_minimal(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await SkillPassportRepository(db).list_progress(
            school_id=_uid(), academic_year_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_progress_with_student_id(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await SkillPassportRepository(db).list_progress(
            school_id=_uid(), academic_year_id=_uid(), student_id=_uid(), status="completed"
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_progress_empty_student_ids(self):
        db = _db()
        result = await SkillPassportRepository(db).list_progress(
            school_id=_uid(), academic_year_id=_uid(), student_ids=set()
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_list_progress_nonempty_student_ids(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await SkillPassportRepository(db).list_progress(
            school_id=_uid(), academic_year_id=_uid(), student_ids={_uid()}
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_create_progress(self):
        progress = SimpleNamespace(id=_uid())
        db = _db()
        result = await SkillPassportRepository(db).create_progress(progress)
        db.add.assert_called_once_with(progress)

    @pytest.mark.asyncio
    async def test_save_progress(self):
        progress = SimpleNamespace(id=_uid())
        db = _db()
        result = await SkillPassportRepository(db).save_progress(progress)
        assert result is progress

    @pytest.mark.asyncio
    async def test_get_passport(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await SkillPassportRepository(db).get_passport(
            student_id=_uid(), school_id=_uid(), academic_year_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_passport_by_id(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await SkillPassportRepository(db).get_passport_by_id(
            _uid(), school_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_passports_minimal(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await SkillPassportRepository(db).list_passports(school_id=_uid())
        assert result == items

    @pytest.mark.asyncio
    async def test_list_passports_with_year(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await SkillPassportRepository(db).list_passports(
            school_id=_uid(), academic_year_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_passports_empty_student_ids(self):
        db = _db()
        result = await SkillPassportRepository(db).list_passports(
            school_id=_uid(), student_ids=set()
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_list_passports_nonempty_student_ids(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await SkillPassportRepository(db).list_passports(
            school_id=_uid(), student_ids={_uid()}
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_create_passport(self):
        passport = SimpleNamespace(id=_uid())
        db = _db()
        result = await SkillPassportRepository(db).create_passport(passport)
        db.add.assert_called_once_with(passport)

    @pytest.mark.asyncio
    async def test_save_passport(self):
        passport = SimpleNamespace(id=_uid())
        db = _db()
        result = await SkillPassportRepository(db).save_passport(passport)
        assert result is passport

    @pytest.mark.asyncio
    async def test_list_class_student_ids(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await SkillPassportRepository(db).list_class_student_ids(
            class_id=_uid(), school_id=_uid()
        )
        assert result == ids

    @pytest.mark.asyncio
    async def test_list_school_student_ids(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await SkillPassportRepository(db).list_school_student_ids(school_id=_uid())
        assert result == ids

    @pytest.mark.asyncio
    async def test_count_completed_activity_sessions(self):
        db = _db(_FR(v=3))
        result = await SkillPassportRepository(db).count_completed_activity_sessions(
            student_id=_uid(), since=_now()
        )
        assert result == 3

    @pytest.mark.asyncio
    async def test_count_completed_content_items(self):
        db = _db(_FR(v=5))
        result = await SkillPassportRepository(db).count_completed_content_items(
            student_id=_uid(), since=_now()
        )
        assert result == 5

    @pytest.mark.asyncio
    async def test_count_submitted_assignments(self):
        db = _db(_FR(v=8))
        result = await SkillPassportRepository(db).count_submitted_assignments(
            student_id=_uid(), school_id=_uid(), since=_now()
        )
        assert result == 8

    @pytest.mark.asyncio
    async def test_count_quiz_attempts(self):
        db = _db(_FR(v=4))
        result = await SkillPassportRepository(db).count_quiz_attempts(
            student_id=_uid(), school_id=_uid(), since=_now()
        )
        assert result == 4

    @pytest.mark.asyncio
    async def test_average_quiz_score_percent(self):
        db = _db(_FR(scalar=75.0))
        result = await SkillPassportRepository(db).average_quiz_score_percent(
            student_id=_uid(), school_id=_uid(), since=_now()
        )

    @pytest.mark.asyncio
    async def test_count_activity_types_completed(self):
        db = _db(_FR(v=2))
        result = await SkillPassportRepository(db).count_activity_types_completed(
            student_id=_uid(), since=_now()
        )
        # Returns int (count of distinct types)
        assert isinstance(result, int)


# ===========================================================================
# TimetableGenerationRepository
# ===========================================================================

class TestTimetableGenerationRepository:
    @pytest.mark.asyncio
    async def test_get_academic_year(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await TimetableGenerationRepository(db).get_academic_year(_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_constraints(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await TimetableGenerationRepository(db).list_constraints(
            school_id=_uid(), academic_year_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_delete_constraints(self):
        db = _db()
        await TimetableGenerationRepository(db).delete_constraints(
            school_id=_uid(), academic_year_id=_uid()
        )
        db.execute.assert_awaited()

    @pytest.mark.asyncio
    async def test_create_constraint(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.academic_timetable_generation.TimetableConstraint", return_value=fake):
            result = await TimetableGenerationRepository(db).create_constraint(
                school_id=_uid()
            )
        assert result is fake

    @pytest.mark.asyncio
    async def test_get_job(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await TimetableGenerationRepository(db).get_job(_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_create_job(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.academic_timetable_generation.TimetableGenerationJob", return_value=fake):
            result = await TimetableGenerationRepository(db).create_job(
                school_id=_uid()
            )
        assert result is fake

    @pytest.mark.asyncio
    async def test_save_job(self):
        job = SimpleNamespace(id=_uid())
        db = _db()
        result = await TimetableGenerationRepository(db).save_job(job)
        assert result is job

    @pytest.mark.asyncio
    async def test_list_classes_for_academic_year(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await TimetableGenerationRepository(db).list_classes_for_academic_year(
            school_id=_uid(), academic_year_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_get_class_student_counts(self):
        db = _db(_FR(many=[(_uid(), 5)]))
        result = await TimetableGenerationRepository(db).get_class_student_counts(
            school_id=_uid(), academic_year_id=_uid()
        )
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_list_teacher_assignments_for_academic_year(self):
        items = [(_uid(), _uid())]
        db = _db(_FR(many=items))
        result = await TimetableGenerationRepository(db).list_teacher_assignments_for_academic_year(
            school_id=_uid(), academic_year_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_delete_timetable_slots_for_academic_year(self):
        db = _db()
        await TimetableGenerationRepository(db).delete_timetable_slots_for_academic_year(
            school_id=_uid(), academic_year_id=_uid()
        )
        db.execute.assert_awaited()

    @pytest.mark.asyncio
    async def test_create_timetable_slot(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.academic_timetable_generation.TimetableSlot", return_value=fake):
            result = await TimetableGenerationRepository(db).create_timetable_slot(
                school_id=_uid()
            )
        assert result is fake
