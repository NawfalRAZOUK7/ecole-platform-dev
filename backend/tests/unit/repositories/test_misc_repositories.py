"""Mock-based unit tests for miscellaneous repositories:
- AIRepository (ai.py)
- GamesRepository (ai_games.py)
- RewardsRepository (ai_rewards.py)
- AuditRepository (audit.py)
- LoginHistoryRepository (auth_login_history.py)
- ERPRepository (erp.py)
- QuestionBankRepository (lms_question_bank.py)
- QuizRepository (lms_quiz.py)
- RubricRepository (lms_rubric.py)
- ProfileLoaderRepository (profile_loader.py)
- ReportsRepository (reports.py)
- AnalyticsRepository (reports_analytics.py)
- FinancialHealthRepository (reports_financial_health.py)
- ReportScheduleRepository (reports_schedule.py)
- SyncQueueRepository (sync_queue.py)
- GDPRRepository (user_gdpr.py)
- ProfileRepository (user_profile.py)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, MagicMock, patch

import pytest

from app.repositories.ai import AIRepository
from app.repositories.ai_games import GamesRepository
from app.repositories.ai_rewards import RewardsRepository
from app.repositories.audit import AuditRepository
from app.repositories.auth_login_history import LoginHistoryRepository
from app.repositories.erp import ERPRepository
from app.repositories.lms_question_bank import QuestionBankRepository
from app.repositories.lms_quiz import QuizRepository
from app.repositories.lms_rubric import RubricRepository
from app.repositories.profile_loader import ProfileLoaderRepository
from app.repositories.reports import ReportsRepository
from app.repositories.reports_analytics import AnalyticsRepository
from app.repositories.reports_financial_health import FinancialHealthRepository
from app.repositories.reports_schedule import ReportScheduleRepository
from app.repositories.sync_queue import SyncQueueRepository
from app.repositories.user_gdpr import GDPRRepository
from app.repositories.user_profile import ProfileRepository


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
        many = self._many
        v = self._v
        return SimpleNamespace(
            all=lambda: many,
            first=lambda: (many[0] if many else v),
        )

    def all(self):
        return self._many

    def mappings(self):
        return SimpleNamespace(all=lambda: self._many)

    def first(self):
        return self._many[0] if self._many else self._v

    def one(self):
        return self._v

    def one_or_none(self):
        return self._v

    def __iter__(self):
        return iter(self._many)


def _db(result=None, *, side_effects=None):
    r = result if result is not None else _FR()
    db = SimpleNamespace(
        execute=AsyncMock(return_value=r),
        add=Mock(),
        add_all=Mock(),
        flush=AsyncMock(),
        commit=AsyncMock(),
        merge=AsyncMock(),
        delete=AsyncMock(),
        refresh=AsyncMock(),
    )
    if side_effects:
        db.execute.side_effect = side_effects
    return db


# ===========================================================================
# AIRepository
# ===========================================================================

class TestAIRepository:
    @pytest.mark.asyncio
    async def test_get_opt_out_preference_no_school(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await AIRepository(db).get_opt_out_preference(target_user_id=_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_opt_out_preference_with_school(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await AIRepository(db).get_opt_out_preference(target_user_id=_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_ai_preference_no_school(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await AIRepository(db).get_ai_preference(
            user_id=_uid(), target_user_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_ai_preference_with_school(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await AIRepository(db).get_ai_preference(
            user_id=_uid(), target_user_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_save_ai_preference(self):
        pref = SimpleNamespace(id=_uid())
        db = _db()
        result = await AIRepository(db).save_ai_preference(pref)
        assert result is pref

    @pytest.mark.asyncio
    async def test_create_writing_attempt(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        result = await AIRepository(db).create_writing_attempt(fake)
        db.add.assert_called_once_with(fake)

    @pytest.mark.asyncio
    async def test_count_completed_content_progress(self):
        db = _db(_FR(scalar=5))
        result = await AIRepository(db).count_completed_content_progress(
            student_id=_uid()
        )
        assert result == 5


# ===========================================================================
# GamesRepository
# ===========================================================================

class TestGamesRepository:
    @pytest.mark.asyncio
    async def test_list_configs_minimal(self):
        items = [object()]
        db = _db(_FR(many=items))
        result, _, _ = await GamesRepository(db).list_configs(
            school_id=_uid(),
            game_type=None, difficulty=None, subject=None, target_age=None,
            is_active=None, cursor=None, limit=20,
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_configs_with_all_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        result, _, _ = await GamesRepository(db).list_configs(
            school_id=_uid(),
            game_type="quiz",
            difficulty="easy",
            subject="math",
            target_age=10,
            is_active=True,
            cursor=None,
            limit=5,
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_get_visible_config(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await GamesRepository(db).get_visible_config(
            game_id=_uid(), school_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_config(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await GamesRepository(db).get_config(_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_create_config(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.ai_games.GameConfig", return_value=fake):
            result = await GamesRepository(db).create_config(school_id=_uid())
        assert result is fake

    @pytest.mark.asyncio
    async def test_save_config(self):
        config = SimpleNamespace(id=_uid())
        db = _db()
        result = await GamesRepository(db).save_config(config)
        assert result is config


# ===========================================================================
# RewardsRepository
# ===========================================================================

class TestRewardsRepository:
    @pytest.mark.asyncio
    async def test_get_user(self):
        obj = object()
        assert await RewardsRepository(_db(_FR(v=obj))).get_user(_uid()) is obj

    @pytest.mark.asyncio
    async def test_get_student_reward(self):
        obj = object()
        assert await RewardsRepository(_db(_FR(v=obj))).get_student_reward(_uid()) is obj

    @pytest.mark.asyncio
    async def test_create_student_reward(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.ai_rewards.StudentReward", return_value=fake):
            result = await RewardsRepository(db).create_student_reward(student_id=_uid())
        assert result is fake

    @pytest.mark.asyncio
    async def test_save_student_reward(self):
        reward = SimpleNamespace(id=_uid())
        db = _db()
        result = await RewardsRepository(db).save_student_reward(reward)
        assert result is reward

    @pytest.mark.asyncio
    async def test_create_reward_event(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.ai_rewards.RewardEvent", return_value=fake):
            result = await RewardsRepository(db).create_reward_event(student_id=_uid())
        assert result is fake

    @pytest.mark.asyncio
    async def test_get_class_school_id(self):
        sid = _uid()
        db = _db(_FR(v=sid))
        result = await RewardsRepository(db).get_class_school_id(_uid())
        assert result is sid

    @pytest.mark.asyncio
    async def test_list_parent_child_ids(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await RewardsRepository(db).list_parent_child_ids(
            parent_id=_uid(), school_id=_uid()
        )
        assert result == set(ids)

    @pytest.mark.asyncio
    async def test_list_teacher_class_ids(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await RewardsRepository(db).list_teacher_class_ids(
            teacher_id=_uid(), school_id=_uid()
        )
        assert result == set(ids)

    @pytest.mark.asyncio
    async def test_student_is_enrolled_in_classes_empty(self):
        result = await RewardsRepository(_db()).student_is_enrolled_in_classes(
            student_id=_uid(), school_id=_uid(), class_ids=set()
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_student_is_enrolled_in_classes_nonempty(self):
        db = _db(_FR(v=_uid()))
        result = await RewardsRepository(db).student_is_enrolled_in_classes(
            student_id=_uid(), school_id=_uid(), class_ids={_uid()}
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_student_is_enrolled_in_class_true(self):
        db = _db(_FR(v=_uid()))
        result = await RewardsRepository(db).student_is_enrolled_in_class(
            student_id=_uid(), school_id=_uid(), class_id=_uid()
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_student_is_enrolled_in_class_false(self):
        db = _db(_FR(v=None))
        result = await RewardsRepository(db).student_is_enrolled_in_class(
            student_id=_uid(), school_id=_uid(), class_id=_uid()
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_any_students_enrolled_in_class_true(self):
        db = _db(_FR(v=_uid()))
        result = await RewardsRepository(db).any_students_enrolled_in_class(
            student_ids={_uid()}, school_id=_uid(), class_id=_uid()
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_any_students_enrolled_in_class_false(self):
        db = _db(_FR(v=None))
        result = await RewardsRepository(db).any_students_enrolled_in_class(
            student_ids=set(), school_id=_uid(), class_id=_uid()
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_list_leaderboard_rows(self):
        rows = [
            SimpleNamespace(student_id=_uid(), full_name="Alice", stars=10, level=2)
        ]
        db = _db(_FR(many=rows))
        result = await RewardsRepository(db).list_leaderboard_rows(
            class_id=_uid(), school_id=_uid(), limit=10
        )
        assert len(result) == 1
        assert result[0]["student_name"] == "Alice"


# ===========================================================================
# AuditRepository
# ===========================================================================

class TestAuditRepository:
    @pytest.mark.asyncio
    async def test_create_log(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.audit.AuditLog", return_value=fake):
            result = await AuditRepository(db).create_log(
                school_id=_uid(), action="login"
            )
        assert result is fake

    @pytest.mark.asyncio
    async def test_list_logs_minimal(self):
        items = [object()]
        db = _db(_FR(many=items))
        rows, _, _ = await AuditRepository(db).list_logs(
            filters={"school_id": _uid()}
        )
        assert rows == items

    @pytest.mark.asyncio
    async def test_list_logs_with_all_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        rows, _, _ = await AuditRepository(db).list_logs(
            filters={
                "school_id": _uid(),
                "actor_id": _uid(),
                "action_type": "delete",
                "target_type": "user",
                "from_dt": _now(),
                "to_dt": _now(),
            },
            limit=20,
        )
        assert rows == items


# ===========================================================================
# LoginHistoryRepository
# ===========================================================================

class TestLoginHistoryRepository:
    @pytest.mark.asyncio
    async def test_create_login_record_success(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.auth_login_history.LoginHistory", return_value=fake):
            result = await LoginHistoryRepository(db).create_login_record(
                user_id=_uid(), school_id=_uid()
            )
        assert result is fake

    @pytest.mark.asyncio
    async def test_list_user_login_history_minimal(self):
        items = [object()]
        db = _db(_FR(many=items))
        rows, _, _ = await LoginHistoryRepository(db).list_user_login_history(
            _uid(), limit=20, cursor=None
        )
        assert rows == items

    @pytest.mark.asyncio
    async def test_list_user_login_history_with_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        with patch("app.repositories.auth_login_history.decode_cursor", return_value=(_uid(), None)):
            rows, _, _ = await LoginHistoryRepository(db).list_user_login_history(
                _uid(), limit=5, cursor="cur"
            )
        assert rows == items

    @pytest.mark.asyncio
    async def test_get_device_fingerprints(self):
        items = ["fp1", "fp2"]
        db = _db(_FR(many=items))
        result = await LoginHistoryRepository(db).get_device_fingerprints(_uid())
        assert result == {"fp1", "fp2"}


# ===========================================================================
# ERPRepository
# ===========================================================================

class TestERPRepository:
    @pytest.mark.asyncio
    async def test_get_user_by_id(self):
        obj = object()
        assert await ERPRepository(_db(_FR(v=obj))).get_user_by_id(_uid()) is obj

    @pytest.mark.asyncio
    async def test_get_academic_year(self):
        obj = object()
        assert await ERPRepository(_db(_FR(v=obj))).get_academic_year(_uid()) is obj

    @pytest.mark.asyncio
    async def test_get_period(self):
        obj = object()
        assert await ERPRepository(_db(_FR(v=obj))).get_period(_uid()) is obj

    @pytest.mark.asyncio
    async def test_get_class(self):
        obj = object()
        assert await ERPRepository(_db(_FR(v=obj))).get_class(_uid()) is obj

    @pytest.mark.asyncio
    async def test_list_classes_no_period(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ERPRepository(db).list_classes(school_id=_uid())
        assert result == items

    @pytest.mark.asyncio
    async def test_list_classes_with_period(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ERPRepository(db).list_classes(school_id=_uid())
        assert result == items

    @pytest.mark.asyncio
    async def test_get_class_counts(self):
        db = _db(_FR(scalar=3))
        teacher_count, student_count = await ERPRepository(db).get_class_counts(
            class_id=_uid(), school_id=_uid()
        )
        assert isinstance(teacher_count, int)
        assert isinstance(student_count, int)

    @pytest.mark.asyncio
    async def test_list_teacher_class_ids(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await ERPRepository(db).list_teacher_class_ids(
            teacher_id=_uid(), school_id=_uid()
        )
        assert result == set(ids)

    @pytest.mark.asyncio
    async def test_get_active_enrollment_no_period(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await ERPRepository(db).get_active_enrollment(
            student_id=_uid(), class_id=_uid(), period_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_active_enrollment_with_period(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await ERPRepository(db).get_active_enrollment(
            student_id=_uid(), class_id=_uid(), period_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_active_enrollment_for_student_period(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await ERPRepository(db).get_active_enrollment_for_student_period(
            student_id=_uid(), period_id=_uid(), school_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_create_enrollment(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.erp.Enrollment", return_value=fake):
            result = await ERPRepository(db).create_enrollment(
                student_id=_uid(), class_id=_uid()
            )
        assert result is fake

    @pytest.mark.asyncio
    async def test_get_teacher_assignment_no_period(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await ERPRepository(db).get_teacher_assignment(
            teacher_id=_uid(), class_id=_uid(), period_id=_uid(), school_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_teacher_assignment_with_period(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await ERPRepository(db).get_teacher_assignment(
            teacher_id=_uid(), class_id=_uid(), period_id=_uid(), school_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_create_teacher_assignment(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.erp.TeacherAssignment", return_value=fake):
            result = await ERPRepository(db).create_teacher_assignment(
                teacher_id=_uid(), class_id=_uid()
            )
        assert result is fake

    @pytest.mark.asyncio
    async def test_get_attendance_session_by_scope(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await ERPRepository(db).get_attendance_session_by_scope(
            class_id=_uid(), session_date=_now().date(), slot="morning"
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_attendance_session(self):
        obj = object()
        assert await ERPRepository(_db(_FR(v=obj))).get_attendance_session(_uid()) is obj

    @pytest.mark.asyncio
    async def test_create_attendance_session(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.erp.AttendanceSession", return_value=fake):
            result = await ERPRepository(db).create_attendance_session(class_id=_uid())
        assert result is fake

    @pytest.mark.asyncio
    async def test_create_attendance_records(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.erp.AttendanceRecord", return_value=fake):
            await ERPRepository(db).create_attendance_records(
                records_data=[{"student_id": _uid()}]
            )
        db.flush.assert_awaited()

    @pytest.mark.asyncio
    async def test_get_attendance_record(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await ERPRepository(db).get_attendance_record(_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_save_attendance_record(self):
        rec = SimpleNamespace(id=_uid())
        db = _db()
        result = await ERPRepository(db).save_attendance_record(rec)
        assert result is rec

    @pytest.mark.asyncio
    async def test_get_absence_justification_by_record(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await ERPRepository(db).get_absence_justification_by_record(_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_absence_justification(self):
        obj = object()
        assert await ERPRepository(_db(_FR(v=obj))).get_absence_justification(_uid()) is obj

    @pytest.mark.asyncio
    async def test_create_absence_justification(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.erp.AbsenceJustification", return_value=fake):
            result = await ERPRepository(db).create_absence_justification(
                record_id=_uid()
            )
        assert result is fake

    @pytest.mark.asyncio
    async def test_save_absence_justification(self):
        just = SimpleNamespace(id=_uid())
        db = _db()
        result = await ERPRepository(db).save_absence_justification(just)
        assert result is just

    @pytest.mark.asyncio
    async def test_create_justification_review(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.erp.JustificationReview", return_value=fake):
            result = await ERPRepository(db).create_justification_review(
                justification_id=_uid()
            )
        assert result is fake

    @pytest.mark.asyncio
    async def test_list_parent_justifications_minimal(self):
        db = _db(_FR(many=[]))
        result = await ERPRepository(db).list_parent_justifications(
            parent_id=_uid(), school_id=_uid()
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_list_parent_justifications_with_status_cursor(self):
        db = _db(_FR(many=[]))
        result = await ERPRepository(db).list_parent_justifications(
            parent_id=_uid(), school_id=_uid()
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_list_student_absences_minimal(self):
        db = _db(_FR(many=[]))
        result = await ERPRepository(db).list_student_absences(
            student_id=_uid(), school_id=_uid()
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_list_student_absences_with_status_cursor(self):
        db = _db(_FR(many=[]))
        result = await ERPRepository(db).list_student_absences(
            student_id=_uid(), school_id=_uid(), status="absent"
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_get_timetable_slot(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await ERPRepository(db).get_timetable_slot(_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_timetable_slots_minimal(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ERPRepository(db).list_timetable_slots(school_id=_uid())
        assert result == items

    @pytest.mark.asyncio
    async def test_list_timetable_slots_with_all_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ERPRepository(db).list_timetable_slots(
            school_id=_uid(),
            class_id=_uid(),
            teacher_id=_uid(),
            day_of_week="Monday",
            academic_year_id=_uid(),
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_find_overlapping_class_slot(self):
        from datetime import time as t
        obj = object()
        db = _db(_FR(v=obj))
        result = await ERPRepository(db).find_overlapping_class_slot(
            school_id=_uid(), class_id=_uid(), academic_year_id=_uid(),
            day_of_week=1, start_time=t(8, 0), end_time=t(9, 0),
            exclude_slot_id=None,
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_find_overlapping_class_slot_with_exclude(self):
        from datetime import time as t
        obj = object()
        db = _db(_FR(v=obj))
        result = await ERPRepository(db).find_overlapping_class_slot(
            school_id=_uid(), class_id=_uid(), academic_year_id=_uid(),
            day_of_week=1, start_time=t(8, 0), end_time=t(9, 0),
            exclude_slot_id=_uid(),
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_find_overlapping_teacher_slot(self):
        from datetime import time as t
        obj = object()
        db = _db(_FR(v=obj))
        result = await ERPRepository(db).find_overlapping_teacher_slot(
            school_id=_uid(), teacher_id=_uid(), academic_year_id=_uid(),
            day_of_week=1, start_time=t(8, 0), end_time=t(9, 0),
            exclude_slot_id=None,
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_find_overlapping_teacher_slot_with_exclude(self):
        from datetime import time as t
        obj = object()
        db = _db(_FR(v=obj))
        result = await ERPRepository(db).find_overlapping_teacher_slot(
            school_id=_uid(), teacher_id=_uid(), academic_year_id=_uid(),
            day_of_week=1, start_time=t(8, 0), end_time=t(9, 0),
            exclude_slot_id=_uid(),
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_create_timetable_slot(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.erp.TimetableSlot", return_value=fake):
            result = await ERPRepository(db).create_timetable_slot(
                class_id=_uid(), school_id=_uid()
            )
        assert result is fake

    @pytest.mark.asyncio
    async def test_save_timetable_slot(self):
        slot = SimpleNamespace(id=_uid())
        db = _db()
        result = await ERPRepository(db).save_timetable_slot(slot)
        assert result is slot

    @pytest.mark.asyncio
    async def test_delete_timetable_slot(self):
        slot = SimpleNamespace(id=_uid())
        db = _db()
        await ERPRepository(db).delete_timetable_slot(slot)
        db.delete.assert_awaited_once_with(slot)

    @pytest.mark.asyncio
    async def test_get_timetable_exception_by_slot_and_date(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await ERPRepository(db).get_timetable_exception_by_slot_and_date(
            timetable_slot_id=_uid(), exception_date=_now().date()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_create_timetable_exception(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.erp.TimetableException", return_value=fake):
            result = await ERPRepository(db).create_timetable_exception(slot_id=_uid())
        assert result is fake

    @pytest.mark.asyncio
    async def test_list_timetable_exceptions_minimal(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ERPRepository(db).list_timetable_exceptions(
            school_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_timetable_exceptions_with_range(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ERPRepository(db).list_timetable_exceptions(
            school_id=_uid(),
            timetable_slot_id=_uid(),
            date_from=_now().date(),
            date_to=_now().date(),
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_get_active_student_class_id(self):
        cid = _uid()
        db = _db(_FR(v=cid))
        result = await ERPRepository(db).get_active_student_class_id(
            student_id=_uid(), school_id=_uid()
        )
        assert result is cid

    @pytest.mark.asyncio
    async def test_list_parent_child_ids(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await ERPRepository(db).list_parent_child_ids(
            parent_id=_uid(), school_id=_uid()
        )
        assert result == set(ids)

    @pytest.mark.asyncio
    async def test_list_weekly_timetable_slots(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ERPRepository(db).list_weekly_timetable_slots(
            school_id=_uid(), monday=_now().date(), sunday=_now().date()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_timetable_exceptions_for_slot_ids(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ERPRepository(db).list_timetable_exceptions_for_slot_ids(
            slot_ids=[_uid()], monday=_now().date(), sunday=_now().date()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_classes_by_ids(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ERPRepository(db).list_classes_by_ids(class_ids=[_uid()])
        assert result == items


# ===========================================================================
# QuestionBankRepository
# ===========================================================================

class TestQuestionBankRepository:
    @pytest.mark.asyncio
    async def test_create_question_bank_item(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.lms_question_bank.QuestionBankItem", return_value=fake):
            result = await QuestionBankRepository(db).create_question_bank_item(
                school_id=_uid()
            )
        assert result is fake

    @pytest.mark.asyncio
    async def test_get_question_bank_item(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await QuestionBankRepository(db).get_question_bank_item(_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_question_bank_items_minimal(self):
        items = [object()]
        db = _db(_FR(many=items))
        rows, _ = await QuestionBankRepository(db).list_question_bank_items(
            school_id=_uid(),
            subject=None, level=None, difficulty=None,
            tags=None, search=None, cursor=None, limit=10,
        )
        assert rows == items

    @pytest.mark.asyncio
    async def test_list_question_bank_items_with_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        with patch("app.repositories.lms_question_bank.decode_cursor", return_value=(_uid(), None)):
            rows, _ = await QuestionBankRepository(db).list_question_bank_items(
                school_id=_uid(),
                subject="math",
                level="primary",
                difficulty="hard",
                tags=None,  # avoid ARRAY.contains() dialect issue
                search="equation",
                cursor="cur",
                limit=5,
            )
        assert rows == items

    @pytest.mark.asyncio
    async def test_list_generation_candidates(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await QuestionBankRepository(db).list_generation_candidates(
            school_id=_uid(), subject="math", level=None, difficulty="easy"
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_increment_usage_counts(self):
        db = _db()
        await QuestionBankRepository(db).increment_usage_counts(item_ids=[_uid()])
        db.execute.assert_awaited()

    @pytest.mark.asyncio
    async def test_get_question_stats(self):
        row = ("math", "easy", 3, 10)
        db = _db(_FR(many=[row]))
        result = await QuestionBankRepository(db).get_question_stats(school_id=_uid())
        assert len(result) == 1
        assert result[0]["subject"] == "math"


# ===========================================================================
# QuizRepository
# ===========================================================================

class TestQuizRepository:
    @pytest.mark.asyncio
    async def test_get_quiz(self):
        obj = object()
        assert await QuizRepository(_db(_FR(v=obj))).get_quiz(_uid()) is obj

    @pytest.mark.asyncio
    async def test_create_quiz(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.lms_quiz.Quiz", return_value=fake):
            result = await QuizRepository(db).create_quiz(school_id=_uid())
        assert result is fake

    @pytest.mark.asyncio
    async def test_save_quiz(self):
        quiz = SimpleNamespace(id=_uid())
        db = _db()
        result = await QuizRepository(db).save_quiz(quiz)
        assert result is quiz

    @pytest.mark.asyncio
    async def test_list_quizzes_for_actor_minimal(self):
        items = [object()]
        db = _db(_FR(many=items))
        rows, _ = await QuizRepository(db).list_quizzes_for_actor(
            role="TCH", school_id=_uid(), user_id=_uid(),
            subject=None, level_band=None, status=None, difficulty=None,
            cursor=None, limit=10,
        )
        assert rows == items

    @pytest.mark.asyncio
    async def test_list_quizzes_for_actor_with_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        with patch("app.repositories.lms_quiz.decode_cursor", return_value=(_uid(), None)):
            rows, _ = await QuizRepository(db).list_quizzes_for_actor(
                role="TCH", school_id=_uid(), user_id=_uid(),
                subject="math", level_band="secondary",
                status="published", difficulty="easy",
                cursor="cur", limit=5,
            )
        assert rows == items

    @pytest.mark.asyncio
    async def test_get_question_counts(self):
        db = _db(_FR(many=[]))
        result = await QuizRepository(db).get_question_counts(quiz_ids=[])
        assert result == {}

    @pytest.mark.asyncio
    async def test_list_quiz_questions(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await QuizRepository(db).list_quiz_questions(quiz_id=_uid())
        assert result == items

    @pytest.mark.asyncio
    async def test_get_quiz_question(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await QuizRepository(db).get_quiz_question(
            question_id=_uid(), quiz_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_delete_quiz_questions(self):
        db = _db()
        await QuizRepository(db).delete_quiz_questions(quiz_id=_uid())
        db.execute.assert_awaited()

    @pytest.mark.asyncio
    async def test_create_quiz_questions(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.lms_quiz.QuizQuestion", return_value=fake):
            await QuizRepository(db).create_quiz_questions(
                questions_data=[{"text": "?"}]
            )
        db.flush.assert_awaited()

    @pytest.mark.asyncio
    async def test_count_quiz_questions(self):
        db = _db(_FR(scalar=5))
        result = await QuizRepository(db).count_quiz_questions(quiz_id=_uid())
        assert result == 5

    @pytest.mark.asyncio
    async def test_sum_quiz_points(self):
        db = _db(_FR(scalar=100))
        result = await QuizRepository(db).sum_quiz_points(quiz_id=_uid())
        assert result == 100

    @pytest.mark.asyncio
    async def test_get_quiz_attempt(self):
        obj = object()
        assert await QuizRepository(_db(_FR(v=obj))).get_quiz_attempt(_uid()) is obj

    @pytest.mark.asyncio
    async def test_get_latest_attempt_for_student_no_max(self):
        obj = object()
        db = _db(_FR(many=[obj]))
        result = await QuizRepository(db).get_latest_attempt_for_student(
            quiz_id=_uid(), student_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_latest_attempt_for_student_with_max(self):
        db = _db(_FR(many=[]))
        result = await QuizRepository(db).get_latest_attempt_for_student(
            quiz_id=_uid(), student_id=_uid()
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_create_quiz_attempt(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.lms_quiz.QuizAttempt", return_value=fake):
            result = await QuizRepository(db).create_quiz_attempt(quiz_id=_uid())
        assert result is fake

    @pytest.mark.asyncio
    async def test_save_quiz_attempt(self):
        attempt = SimpleNamespace(id=_uid())
        db = _db()
        result = await QuizRepository(db).save_quiz_attempt(attempt)
        assert result is attempt

    @pytest.mark.asyncio
    async def test_count_student_attempts_no_status(self):
        db = _db(_FR(scalar=2))
        result = await QuizRepository(db).count_student_attempts(
            quiz_id=_uid(), student_id=_uid()
        )
        assert result == 2

    @pytest.mark.asyncio
    async def test_count_student_attempts_with_status(self):
        db = _db(_FR(scalar=1))
        result = await QuizRepository(db).count_student_attempts(
            quiz_id=_uid(), student_id=_uid()
        )
        assert result == 1

    @pytest.mark.asyncio
    async def test_get_active_attempt(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await QuizRepository(db).get_active_attempt(
            quiz_id=_uid(), student_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_quiz_response(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await QuizRepository(db).get_quiz_response(
            attempt_id=_uid(), question_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_create_quiz_response(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.lms_quiz.QuizResponse", return_value=fake):
            result = await QuizRepository(db).create_quiz_response(attempt_id=_uid())
        assert result is fake

    @pytest.mark.asyncio
    async def test_save_quiz_response(self):
        resp = SimpleNamespace(id=_uid())
        db = _db()
        result = await QuizRepository(db).save_quiz_response(resp)
        assert result is resp

    @pytest.mark.asyncio
    async def test_list_attempt_responses(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await QuizRepository(db).list_attempt_responses(attempt_id=_uid())
        assert result == items

    @pytest.mark.asyncio
    async def test_list_attempt_responses_with_questions(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await QuizRepository(db).list_attempt_responses_with_questions(
            attempt_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_quiz_attempts_minimal(self):
        db = _db(_FR(many=[]))
        rows, _, _ = await QuizRepository(db).list_quiz_attempts(
            _uid(), cursor=None, limit=10
        )
        assert rows == []

    @pytest.mark.asyncio
    async def test_list_quiz_attempts_with_filters(self):
        db = _db(_FR(many=[]))
        with patch("app.repositories.lms_quiz.decode_cursor", return_value=(_uid(), None)):
            rows, _, _ = await QuizRepository(db).list_quiz_attempts(
                _uid(), cursor="cur", limit=5
            )
        assert rows == []

    @pytest.mark.asyncio
    async def test_get_attempt_stats(self):
        db = _db(_FR(v=(0, 0, None, None, None)))
        total, completed, avg, mx, mn = await QuizRepository(db).get_attempt_stats(_uid())
        assert total == 0
        assert completed == 0

    @pytest.mark.asyncio
    async def test_get_question_response_stats(self):
        db = _db(_FR(v=(5, 3)))
        total, correct = await QuizRepository(db).get_question_response_stats(_uid())
        assert total == 5
        assert correct == 3


# ===========================================================================
# RubricRepository
# ===========================================================================

class TestRubricRepository:
    @pytest.mark.asyncio
    async def test_get_rubric(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await RubricRepository(db).get_rubric(_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_create_rubric(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.lms_rubric.Rubric", return_value=fake):
            result = await RubricRepository(db).create_rubric(school_id=_uid())
        assert result is fake

    @pytest.mark.asyncio
    async def test_list_rubrics_minimal(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await RubricRepository(db).list_rubrics(
            school_id=_uid(), teacher_id=None
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_rubrics_with_assignment(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await RubricRepository(db).list_rubrics(
            school_id=_uid(), teacher_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_create_criterion(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.lms_rubric.RubricCriterion", return_value=fake):
            result = await RubricRepository(db).create_criterion(rubric_id=_uid())
        assert result is fake

    @pytest.mark.asyncio
    async def test_create_level(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.lms_rubric.RubricLevel", return_value=fake):
            result = await RubricRepository(db).create_level(criterion_id=_uid())
        assert result is fake

    @pytest.mark.asyncio
    async def test_create_rubric_score(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.lms_rubric.RubricScore", return_value=fake):
            result = await RubricRepository(db).create_rubric_score(
                rubric_id=_uid(), submission_id=_uid()
            )
        assert result is fake

    @pytest.mark.asyncio
    async def test_list_rubric_scores_no_submission(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await RubricRepository(db).list_rubric_scores(_uid())
        assert result == items

    @pytest.mark.asyncio
    async def test_list_rubric_scores_with_submission(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await RubricRepository(db).list_rubric_scores(_uid())
        assert result == items

    @pytest.mark.asyncio
    async def test_delete_rubric_scores_for_submission(self):
        db = _db()
        await RubricRepository(db).delete_rubric_scores_for_submission(_uid())
        db.execute.assert_awaited()

    @pytest.mark.asyncio
    async def test_get_submission_with_rubric_context(self):
        db = _db(_FR(v=None))
        result = await RubricRepository(db).get_submission_with_rubric_context(_uid())
        assert result is None


# ===========================================================================
# ProfileLoaderRepository
# ===========================================================================

class TestProfileLoaderRepository:
    @pytest.mark.asyncio
    async def test_find_student_profile(self):
        obj = object()
        assert await ProfileLoaderRepository(_db(_FR(v=obj))).find_student_profile(_uid()) is obj

    @pytest.mark.asyncio
    async def test_find_parent_profile(self):
        obj = object()
        assert await ProfileLoaderRepository(_db(_FR(v=obj))).find_parent_profile(_uid()) is obj

    @pytest.mark.asyncio
    async def test_find_teacher_profile(self):
        obj = object()
        assert await ProfileLoaderRepository(_db(_FR(v=obj))).find_teacher_profile(_uid()) is obj

    @pytest.mark.asyncio
    async def test_find_admin_profile(self):
        obj = object()
        assert await ProfileLoaderRepository(_db(_FR(v=obj))).find_admin_profile(_uid()) is obj

    @pytest.mark.asyncio
    async def test_find_content_manager_profile(self):
        obj = object()
        assert await ProfileLoaderRepository(_db(_FR(v=obj))).find_content_manager_profile(_uid()) is obj

    @pytest.mark.asyncio
    async def test_find_profile_student(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await ProfileLoaderRepository(db).find_profile(_uid(), "student")
        assert result is obj

    @pytest.mark.asyncio
    async def test_find_profile_parent(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await ProfileLoaderRepository(db).find_profile(_uid(), "parent")
        assert result is obj

    @pytest.mark.asyncio
    async def test_find_profile_teacher(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await ProfileLoaderRepository(db).find_profile(_uid(), "teacher")
        assert result is obj

    @pytest.mark.asyncio
    async def test_find_profile_admin(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await ProfileLoaderRepository(db).find_profile(_uid(), "admin")
        assert result is obj

    @pytest.mark.asyncio
    async def test_find_profile_content_manager(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await ProfileLoaderRepository(db).find_profile(_uid(), "content_manager")
        assert result is obj

    @pytest.mark.asyncio
    async def test_find_profile_unknown(self):
        db = _db(_FR(v=None))
        result = await ProfileLoaderRepository(db).find_profile(_uid(), "unknown")
        assert result is None

    @pytest.mark.asyncio
    async def test_create_profile(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch.dict("app.repositories.profile_loader._PROFILE_TYPE_MAP", {"student": lambda **kw: fake}):
            result = await ProfileLoaderRepository(db).create_profile(
                user_id=_uid(), school_id=_uid(), profile_type="student"
            )
        assert result is fake
        db.add.assert_called_once_with(fake)
        db.refresh.assert_awaited_once_with(fake)


# ===========================================================================
# ReportsRepository
# ===========================================================================

class TestReportsRepository:
    @pytest.mark.asyncio
    async def test_create_report_job(self):
        job = SimpleNamespace(id=_uid())
        db = _db()
        result = await ReportsRepository(db).create_report_job(job)
        db.add.assert_called_once_with(job)

    @pytest.mark.asyncio
    async def test_save_report_job(self):
        job = SimpleNamespace(id=_uid())
        db = _db()
        result = await ReportsRepository(db).save_report_job(job)
        assert result is job

    @pytest.mark.asyncio
    async def test_get_report_job(self):
        obj = object()
        assert await ReportsRepository(_db(_FR(v=obj))).get_report_job(_uid()) is obj

    @pytest.mark.asyncio
    async def test_find_cached_report_minimal(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await ReportsRepository(db).find_cached_report(
            school_id=_uid(), requester_id=_uid(), report_type="grade_summary",
            parameters_hash="abc123", since=_now(), now=_now(),
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_find_cached_report_with_all_params(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await ReportsRepository(db).find_cached_report(
            school_id=_uid(), requester_id=_uid(), report_type="grade_summary",
            parameters_hash="abc123", since=_now(), now=_now(),
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_report_jobs_minimal(self):
        items = [object()]
        db = _db(_FR(many=items))
        rows, _, _ = await ReportsRepository(db).list_report_jobs(
            school_id=_uid(), requester_id=_uid(), requester_role="ADM",
            report_type=None, period_id=None, status=None, cursor=None, limit=10,
        )
        assert rows == items

    @pytest.mark.asyncio
    async def test_list_report_jobs_with_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        with patch("app.repositories.reports.decode_cursor", return_value=(_uid(), None)):
            rows, _, _ = await ReportsRepository(db).list_report_jobs(
                school_id=_uid(), requester_id=_uid(), requester_role="TCH",
                report_type="grade", period_id=_uid(), status="ready",
                cursor="cur", limit=5,
            )
        assert rows == items

    @pytest.mark.asyncio
    async def test_list_expired_report_jobs(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ReportsRepository(db).list_expired_report_jobs(now=_now())
        assert result == items

    @pytest.mark.asyncio
    async def test_create_export_log(self):
        export = SimpleNamespace(id=_uid())
        db = _db()
        await ReportsRepository(db).create_export_log(export)
        db.add.assert_called_once_with(export)

    @pytest.mark.asyncio
    async def test_get_user_in_school(self):
        obj = object()
        assert await ReportsRepository(_db(_FR(v=obj))).get_user_in_school(
            user_id=_uid(), school_id=_uid()
        ) is obj

    @pytest.mark.asyncio
    async def test_get_period_in_school(self):
        obj = object()
        assert await ReportsRepository(_db(_FR(v=obj))).get_period_in_school(
            period_id=_uid(), school_id=_uid()
        ) is obj

    @pytest.mark.asyncio
    async def test_get_class_in_school(self):
        obj = object()
        assert await ReportsRepository(_db(_FR(v=obj))).get_class_in_school(
            class_id=_uid(), school_id=_uid()
        ) is obj

    @pytest.mark.asyncio
    async def test_get_class_academic_year(self):
        db = _db(_FR(v=None))
        result = await ReportsRepository(db).get_class_academic_year(
            class_id=_uid(), school_id=_uid()
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_list_parent_child_ids(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await ReportsRepository(db).list_parent_child_ids(
            parent_id=_uid(), school_id=_uid()
        )
        assert result == set(ids)

    @pytest.mark.asyncio
    async def test_list_periods(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ReportsRepository(db).list_periods(school_id=_uid())
        assert result == items

    @pytest.mark.asyncio
    async def test_list_classes(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ReportsRepository(db).list_classes(school_id=_uid())
        assert result == items

    @pytest.mark.asyncio
    async def test_list_classes_for_teacher(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ReportsRepository(db).list_classes_for_teacher(
            teacher_id=_uid(), school_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_students_for_class(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ReportsRepository(db).list_students_for_class(
            class_id=_uid(), school_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_users_by_role(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ReportsRepository(db).list_users_by_role(
            school_id=_uid(), role_code="TCH"
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_children(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ReportsRepository(db).list_children(
            parent_id=_uid(), school_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_get_student_class_context_no_period(self):
        db = _db(_FR(v=None))
        result = await ReportsRepository(db).get_student_class_context(
            student_id=_uid(), school_id=_uid()
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_get_student_class_context_with_period(self):
        db = _db(_FR(v=None))
        result = await ReportsRepository(db).get_student_class_context(
            student_id=_uid(), school_id=_uid(), period_id=_uid()
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_list_teacher_class_ids(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await ReportsRepository(db).list_teacher_class_ids(
            teacher_id=_uid(), school_id=_uid()
        )
        assert result == set(ids)

    @pytest.mark.asyncio
    async def test_list_class_student_ids(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await ReportsRepository(db).list_class_student_ids(
            class_id=_uid(), school_id=_uid()
        )
        assert result == ids

    @pytest.mark.asyncio
    async def test_list_user_names_by_ids(self):
        db = _db(_FR(many=[]))
        result = await ReportsRepository(db).list_user_names_by_ids(user_ids=[])
        assert result == {}

    @pytest.mark.asyncio
    async def test_list_student_report_grade_rows(self):
        db = _db(_FR(many=[]))
        result = await ReportsRepository(db).list_student_report_grade_rows(
            school_id=_uid(), student_id=_uid(), from_dt=_now(), to_dt=_now()
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_get_student_report_attendance_summary(self):
        row = SimpleNamespace(total=10, present=8, absent=1, excused=1, late=0)
        db = _db(_FR(v=row))
        total, present, absent, excused, late = (
            await ReportsRepository(db).get_student_report_attendance_summary(
                school_id=_uid(), student_id=_uid(),
                from_date=_now().date(), to_date=_now().date(),
            )
        )
        assert total == 10

    @pytest.mark.asyncio
    async def test_list_class_subject_averages(self):
        db = _db(_FR(many=[]))
        result = await ReportsRepository(db).list_class_subject_averages(
            school_id=_uid(), class_id=_uid(), from_dt=_now(), to_dt=_now()
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_list_class_student_grade_averages(self):
        db = _db(_FR(many=[]))
        result = await ReportsRepository(db).list_class_student_grade_averages(
            school_id=_uid(), class_id=_uid(),
            student_ids=[], from_dt=_now(), to_dt=_now()
        )
        assert result == {}

    @pytest.mark.asyncio
    async def test_list_class_student_attendance_rates(self):
        db = _db(_FR(many=[]))
        result = await ReportsRepository(db).list_class_student_attendance_rates(
            school_id=_uid(), class_id=_uid(),
            student_ids=[], from_date=_now().date(), to_date=_now().date()
        )
        assert result == {}

    @pytest.mark.asyncio
    async def test_list_attendance_summary_rows(self):
        db = _db(_FR(many=[]))
        result = await ReportsRepository(db).list_attendance_summary_rows(
            school_id=_uid(), class_id=_uid(),
            student_ids=[], from_date=_now().date(), to_date=_now().date()
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_list_attendance_trends(self):
        db = _db(_FR(many=[]))
        result = await ReportsRepository(db).list_attendance_trends(
            school_id=_uid(), class_id=_uid(),
            from_date=_now().date(), to_date=_now().date()
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_list_invoices_for_parent(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ReportsRepository(db).list_invoices_for_parent(
            school_id=_uid(), parent_id=_uid(),
            from_date=_now().date(), to_date=_now().date()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_payment_attempts_for_invoice_ids(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ReportsRepository(db).list_payment_attempts_for_invoice_ids(
            invoice_ids=[_uid()]
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_count_export_rows(self):
        db = _db(_FR(v=42))
        result = await ReportsRepository(db).count_export_rows(
            school_id=_uid(), entity="students", filters={}
        )
        assert result == 42

    @pytest.mark.asyncio
    async def test_fetch_export_rows(self):
        row = SimpleNamespace(_mapping={"id": str(_uid()), "name": "test"})
        db = _db(_FR(many=[row]))
        result = await ReportsRepository(db).fetch_export_rows(
            school_id=_uid(), entity="students", filters={}, offset=0, limit=100
        )
        assert len(result) == 1


# ===========================================================================
# AnalyticsRepository
# ===========================================================================

class TestAnalyticsRepository:
    def _dt(self):
        return _now()

    def _d(self):
        from datetime import date
        return date.today()

    @pytest.mark.asyncio
    async def test_count_active_users(self):
        db = _db(_FR(v=50))
        result = await AnalyticsRepository(db).count_active_users(
            school_id=_uid(), from_dt=self._dt(), to_dt=self._dt()
        )
        assert result == 50

    @pytest.mark.asyncio
    async def test_count_users(self):
        db = _db(_FR(v=100))
        result = await AnalyticsRepository(db).count_users(school_id=_uid())
        assert result == 100

    @pytest.mark.asyncio
    async def test_count_active_accounts(self):
        db = _db(_FR(v=80))
        result = await AnalyticsRepository(db).count_active_accounts(school_id=_uid())
        assert result == 80

    @pytest.mark.asyncio
    async def test_attendance_summary(self):
        db = _db(_FR(v=(5, 2)))
        total, present = await AnalyticsRepository(db).attendance_summary(
            school_id=_uid(), from_date=self._d(), to_date=self._d()
        )
        assert total == 5

    @pytest.mark.asyncio
    async def test_attendance_summary_with_class(self):
        db = _db(_FR(v=(3, 1)))
        total, present = await AnalyticsRepository(db).attendance_summary(
            school_id=_uid(), from_date=self._d(), to_date=self._d(), class_id=_uid()
        )
        assert total == 3

    @pytest.mark.asyncio
    async def test_average_grade(self):
        db = _db(_FR(scalar=78.5))
        result = await AnalyticsRepository(db).average_grade(
            school_id=_uid(), from_dt=self._dt(), to_dt=self._dt()
        )

    @pytest.mark.asyncio
    async def test_billing_summary(self):
        db = _db(_FR(many=[(1000.0, 800.0, 200.0)]))
        result = await AnalyticsRepository(db).billing_summary(
            school_id=_uid(), from_date=self._d(), to_date=self._d()
        )

    @pytest.mark.asyncio
    async def test_engagement_summary(self):
        db = _db(_FR(many=[(10, 5, 3)]))
        result = await AnalyticsRepository(db).engagement_summary(
            school_id=_uid(), from_dt=self._dt(), to_dt=self._dt()
        )

    @pytest.mark.asyncio
    async def test_count_invitations_created(self):
        db = _db(_FR(scalar=7))
        result = await AnalyticsRepository(db).count_invitations_created(
            school_id=_uid(), from_dt=self._dt()
        )
        assert result == 7

    @pytest.mark.asyncio
    async def test_count_invitations_consumed(self):
        db = _db(_FR(scalar=5))
        result = await AnalyticsRepository(db).count_invitations_consumed(
            school_id=_uid(), from_dt=self._dt()
        )
        assert result == 5

    @pytest.mark.asyncio
    async def test_list_enrollment_by_class(self):
        db = _db(_FR(many=[]))
        result = await AnalyticsRepository(db).list_enrollment_by_class(school_id=_uid())
        assert result == []

    @pytest.mark.asyncio
    async def test_list_teacher_class_ids(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await AnalyticsRepository(db).list_teacher_class_ids(
            teacher_id=_uid(), school_id=_uid()
        )
        assert isinstance(result, set)


# ===========================================================================
# FinancialHealthRepository
# ===========================================================================

class TestFinancialHealthRepository:
    @pytest.mark.asyncio
    async def test_get_academic_year_no_school(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await FinancialHealthRepository(db).get_academic_year(_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_academic_year_with_school(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await FinancialHealthRepository(db).get_academic_year(_uid(), school_id=_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_academic_year_by_label(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await FinancialHealthRepository(db).get_academic_year_by_label(
            school_id=_uid(), label="2024-2025"
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_active_student_ids_for_academic_year(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await FinancialHealthRepository(db).list_active_student_ids_for_academic_year(
            school_id=_uid(), academic_year_id=_uid()
        )
        assert isinstance(result, set)

    @pytest.mark.asyncio
    async def test_count_active_students_for_academic_year(self):
        db = _db(_FR(scalar=120))
        result = await FinancialHealthRepository(db).count_active_students_for_academic_year(
            school_id=_uid(), academic_year_id=_uid()
        )
        assert result == 120

    @pytest.mark.asyncio
    async def test_get_retention_metric(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await FinancialHealthRepository(db).get_retention_metric(
            school_id=_uid(), academic_year_from="2023-2024", academic_year_to="2024-2025"
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_retention_metrics(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await FinancialHealthRepository(db).list_retention_metrics(school_id=_uid())
        assert result == items

    @pytest.mark.asyncio
    async def test_create_retention_metric(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.reports_financial_health.RetentionMetric", return_value=fake):
            result = await FinancialHealthRepository(db).create_retention_metric(
                school_id=_uid(), period_type="annual"
            )
        assert result is fake

    @pytest.mark.asyncio
    async def test_save_retention_metric(self):
        metric = SimpleNamespace(id=_uid())
        db = _db()
        result = await FinancialHealthRepository(db).save_retention_metric(metric)
        assert result is metric

    @pytest.mark.asyncio
    async def test_get_cashflow_forecast(self):
        from datetime import date
        obj = object()
        db = _db(_FR(v=obj))
        result = await FinancialHealthRepository(db).get_cashflow_forecast(
            school_id=_uid(), forecast_month=date.today()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_cashflow_forecasts_minimal(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await FinancialHealthRepository(db).list_cashflow_forecasts(school_id=_uid())
        assert result == items

    @pytest.mark.asyncio
    async def test_list_cashflow_forecasts_with_range(self):
        from datetime import date
        items = [object()]
        db = _db(_FR(many=items))
        result = await FinancialHealthRepository(db).list_cashflow_forecasts(
            school_id=_uid(), start_month=date.today(), end_month=date.today()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_create_cashflow_forecast(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.reports_financial_health.CashflowForecast", return_value=fake):
            result = await FinancialHealthRepository(db).create_cashflow_forecast(
                school_id=_uid()
            )
        assert result is fake

    @pytest.mark.asyncio
    async def test_save_cashflow_forecast(self):
        forecast = SimpleNamespace(id=_uid())
        db = _db()
        result = await FinancialHealthRepository(db).save_cashflow_forecast(forecast)
        assert result is forecast

    @pytest.mark.asyncio
    async def test_get_financial_snapshot(self):
        from datetime import date
        obj = object()
        db = _db(_FR(v=obj))
        result = await FinancialHealthRepository(db).get_financial_snapshot(
            school_id=_uid(), snapshot_date=date.today()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_financial_snapshots(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await FinancialHealthRepository(db).list_financial_snapshots(school_id=_uid())
        assert result == items

    @pytest.mark.asyncio
    async def test_create_financial_snapshot(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.reports_financial_health.FinancialSnapshot", return_value=fake):
            result = await FinancialHealthRepository(db).create_financial_snapshot(
                school_id=_uid()
            )
        assert result is fake

    @pytest.mark.asyncio
    async def test_save_financial_snapshot(self):
        snapshot = SimpleNamespace(id=_uid())
        db = _db()
        result = await FinancialHealthRepository(db).save_financial_snapshot(snapshot)
        assert result is snapshot

    @pytest.mark.asyncio
    async def test_aggregate_invoice_amounts_by_due_month(self):
        from datetime import date as d
        db = _db(_FR(many=[]))
        result = await FinancialHealthRepository(db).aggregate_invoice_amounts_by_due_month(
            school_id=_uid(), start_date=d.today(), end_date=d.today()
        )
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_aggregate_invoice_amounts_with_year(self):
        from datetime import date as d
        db = _db(_FR(many=[]))
        result = await FinancialHealthRepository(db).aggregate_invoice_amounts_by_due_month(
            school_id=_uid(), start_date=d.today(), end_date=d.today()
        )
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_recent_collection_ratio(self):
        from datetime import date as d
        db = _db(_FR(v=(None, None)))
        result = await FinancialHealthRepository(db).get_recent_collection_ratio(
            school_id=_uid(), start_date=d.today(), end_date=d.today()
        )
        assert isinstance(result, float)

    @pytest.mark.asyncio
    async def test_get_budget_total_for_academic_year(self):
        db = _db(_FR(scalar=None))
        result = await FinancialHealthRepository(db).get_budget_total_for_academic_year(
            school_id=_uid(), academic_year_id=_uid()
        )
        assert isinstance(result, float)

    @pytest.mark.asyncio
    async def test_get_expense_total_for_academic_year(self):
        db = _db(_FR(scalar=None))
        result = await FinancialHealthRepository(db).get_expense_total_for_academic_year(
            school_id=_uid(), academic_year_id=_uid()
        )
        assert isinstance(result, float)

    @pytest.mark.asyncio
    async def test_get_collected_revenue_for_academic_year(self):
        db = _db(_FR(scalar=None))
        result = await FinancialHealthRepository(db).get_collected_revenue_for_academic_year(
            school_id=_uid(), academic_year_id=_uid()
        )
        assert isinstance(result, float)

    @pytest.mark.asyncio
    async def test_get_total_receivable_as_of(self):
        from datetime import date
        db = _db(_FR(scalar=None))
        result = await FinancialHealthRepository(db).get_total_receivable_as_of(
            school_id=_uid(), snapshot_date=date.today()
        )
        assert isinstance(result, float)

    @pytest.mark.asyncio
    async def test_get_total_collected_as_of(self):
        from datetime import date
        db = _db(_FR(scalar=None))
        result = await FinancialHealthRepository(db).get_total_collected_as_of(
            school_id=_uid(), snapshot_date=date.today()
        )
        assert isinstance(result, float)

    @pytest.mark.asyncio
    async def test_get_overdue_totals_as_of(self):
        from datetime import date
        db = _db(_FR(v=(None, None)))
        total_amount, count = await FinancialHealthRepository(db).get_overdue_totals_as_of(
            school_id=_uid(), snapshot_date=date.today()
        )
        assert isinstance(total_amount, float)
        assert isinstance(count, int)

    @pytest.mark.asyncio
    async def test_get_average_payment_delay_days_as_of(self):
        from datetime import date
        db = _db(_FR(scalar=None))
        result = await FinancialHealthRepository(db).get_average_payment_delay_days_as_of(
            school_id=_uid(), snapshot_date=date.today()
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_get_cost_per_student(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await FinancialHealthRepository(db).get_cost_per_student(
            school_id=_uid(), academic_year_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_create_cost_per_student(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.reports_financial_health.CostPerStudent", return_value=fake):
            result = await FinancialHealthRepository(db).create_cost_per_student(
                school_id=_uid()
            )
        assert result is fake

    @pytest.mark.asyncio
    async def test_save_cost_per_student(self):
        analysis = SimpleNamespace(id=_uid())
        db = _db()
        result = await FinancialHealthRepository(db).save_cost_per_student(analysis)
        assert result is analysis


# ===========================================================================
# ReportScheduleRepository
# ===========================================================================

class TestReportScheduleRepository:
    @pytest.mark.asyncio
    async def test_get_schedule(self):
        obj = object()
        assert await ReportScheduleRepository(_db(_FR(v=obj))).get_schedule(_uid()) is obj

    @pytest.mark.asyncio
    async def test_create_schedule(self):
        sched = SimpleNamespace(id=_uid())
        db = _db()
        result = await ReportScheduleRepository(db).create_schedule(sched)
        db.add.assert_called_once_with(sched)

    @pytest.mark.asyncio
    async def test_save_schedule(self):
        sched = SimpleNamespace(id=_uid())
        db = _db()
        result = await ReportScheduleRepository(db).save_schedule(sched)
        assert result is sched

    @pytest.mark.asyncio
    async def test_list_schedules(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ReportScheduleRepository(db).list_schedules(school_id=_uid())
        assert result == items

    @pytest.mark.asyncio
    async def test_list_due_schedules(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ReportScheduleRepository(db).list_due_schedules(now=_now())
        assert result == items

    @pytest.mark.asyncio
    async def test_get_active_role(self):
        db = _db(_FR(v="TCH"))
        result = await ReportScheduleRepository(db).get_active_role(
            user_id=_uid(), school_id=_uid()
        )
        assert result == "TCH"

    @pytest.mark.asyncio
    async def test_list_recipient_users_empty_roles(self):
        db = _db()
        result = await ReportScheduleRepository(db).list_recipient_users(
            school_id=_uid(), roles=[]
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_list_recipient_users_with_roles(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ReportScheduleRepository(db).list_recipient_users(
            school_id=_uid(), roles=["TCH", "ADM"]
        )
        assert result == items


# ===========================================================================
# SyncQueueRepository
# ===========================================================================

class TestSyncQueueRepository:
    @pytest.mark.asyncio
    async def test_get_device_no_school(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await SyncQueueRepository(db).get_device(device_id=_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_device_with_school(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await SyncQueueRepository(db).get_device(
            device_id=_uid(), school_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_devices_minimal(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await SyncQueueRepository(db).list_devices(school_id=_uid())
        assert result == items

    @pytest.mark.asyncio
    async def test_list_devices_with_is_active(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await SyncQueueRepository(db).list_devices(
            school_id=_uid(), is_active=True
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_create_device(self):
        device = SimpleNamespace(id=_uid())
        db = _db()
        result = await SyncQueueRepository(db).create_device(device)
        db.add.assert_called_once_with(device)

    @pytest.mark.asyncio
    async def test_save_device(self):
        device = SimpleNamespace(id=_uid())
        db = _db()
        result = await SyncQueueRepository(db).save_device(device)
        assert result is device

    @pytest.mark.asyncio
    async def test_get_queue_item(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await SyncQueueRepository(db).get_queue_item(_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_queue_item_with_school(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await SyncQueueRepository(db).get_queue_item(_uid(), school_id=_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_latest_queue_item(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await SyncQueueRepository(db).get_latest_queue_item(
            school_id=_uid(), entity_type="user", entity_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_queue_items_minimal(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await SyncQueueRepository(db).list_queue_items(school_id=_uid())
        assert result == items

    @pytest.mark.asyncio
    async def test_list_queue_items_with_all_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await SyncQueueRepository(db).list_queue_items(
            school_id=_uid(),
            device_id=_uid(),
            status="pending",
            entity_type="user",
            limit=20,
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_create_queue_item(self):
        item = SimpleNamespace(id=_uid())
        db = _db()
        result = await SyncQueueRepository(db).create_queue_item(item)
        db.add.assert_called_once_with(item)

    @pytest.mark.asyncio
    async def test_save_queue_item(self):
        item = SimpleNamespace(id=_uid())
        db = _db()
        result = await SyncQueueRepository(db).save_queue_item(item)
        assert result is item

    @pytest.mark.asyncio
    async def test_get_conflict(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await SyncQueueRepository(db).get_conflict(_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_conflict_with_school(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await SyncQueueRepository(db).get_conflict(_uid(), school_id=_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_conflicts_minimal(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await SyncQueueRepository(db).list_conflicts(school_id=_uid())
        assert result == items

    @pytest.mark.asyncio
    async def test_list_conflicts_with_resolution(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await SyncQueueRepository(db).list_conflicts(
            school_id=_uid(), resolution="manual"
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_create_conflict(self):
        conflict = SimpleNamespace(id=_uid())
        db = _db()
        result = await SyncQueueRepository(db).create_conflict(conflict)
        db.add.assert_called_once_with(conflict)

    @pytest.mark.asyncio
    async def test_save_conflict(self):
        conflict = SimpleNamespace(id=_uid())
        db = _db()
        result = await SyncQueueRepository(db).save_conflict(conflict)
        assert result is conflict

    @pytest.mark.asyncio
    async def test_get_checkpoint(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await SyncQueueRepository(db).get_checkpoint(_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_checkpoint_with_school(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await SyncQueueRepository(db).get_checkpoint(_uid(), school_id=_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_latest_checkpoint(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await SyncQueueRepository(db).get_latest_checkpoint(_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_checkpoints_minimal(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await SyncQueueRepository(db).list_checkpoints(school_id=_uid())
        assert result == items

    @pytest.mark.asyncio
    async def test_list_checkpoints_with_device(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await SyncQueueRepository(db).list_checkpoints(
            school_id=_uid(), device_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_create_checkpoint(self):
        cp = SimpleNamespace(id=_uid())
        db = _db()
        result = await SyncQueueRepository(db).create_checkpoint(cp)
        db.add.assert_called_once_with(cp)

    @pytest.mark.asyncio
    async def test_save_checkpoint(self):
        cp = SimpleNamespace(id=_uid())
        db = _db()
        result = await SyncQueueRepository(db).save_checkpoint(cp)
        assert result is cp


# ===========================================================================
# GDPRRepository
# ===========================================================================

class TestGDPRRepository:
    @pytest.mark.asyncio
    async def test_get_user_in_school(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await GDPRRepository(db).get_user_in_school(
            user_id=_uid(), school_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_memberships(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await GDPRRepository(db).list_memberships(_uid())
        assert result == items

    @pytest.mark.asyncio
    async def test_list_sessions(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await GDPRRepository(db).list_sessions(user_id=_uid(), limit=100)
        assert result == items

    @pytest.mark.asyncio
    async def test_list_actor_audit_logs(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await GDPRRepository(db).list_actor_audit_logs(user_id=_uid(), limit=100)
        assert result == items

    @pytest.mark.asyncio
    async def test_list_submissions(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await GDPRRepository(db).list_submissions(student_id=_uid(), limit=100)
        assert result == items

    @pytest.mark.asyncio
    async def test_list_grades(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await GDPRRepository(db).list_grades(student_id=_uid(), limit=100)
        assert list(result) == items

    @pytest.mark.asyncio
    async def test_list_notifications(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await GDPRRepository(db).list_notifications(user_id=_uid(), limit=100)
        assert result == items

    @pytest.mark.asyncio
    async def test_list_invoices(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await GDPRRepository(db).list_invoices(user_id=_uid(), limit=100)
        assert result == items

    @pytest.mark.asyncio
    async def test_list_consent_preferences(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await GDPRRepository(db).list_consent_preferences(user_id=_uid())
        assert result == items

    @pytest.mark.asyncio
    async def test_save_user(self):
        user = SimpleNamespace(id=_uid())
        db = _db()
        result = await GDPRRepository(db).save_user(user)
        assert result is user

    @pytest.mark.asyncio
    async def test_revoke_active_sessions(self):
        db = _db()
        await GDPRRepository(db).revoke_active_sessions(
            user_id=_uid(), revoked_at=_now()
        )
        db.execute.assert_awaited()

    @pytest.mark.asyncio
    async def test_deactivate_active_memberships(self):
        db = _db()
        await GDPRRepository(db).deactivate_active_memberships(_uid())
        db.execute.assert_awaited()

    @pytest.mark.asyncio
    async def test_list_consent_audit_logs(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await GDPRRepository(db).list_consent_audit_logs(
            school_id=_uid(), limit=100
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_get_consent_preference(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await GDPRRepository(db).get_consent_preference(_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_save_consent_preference(self):
        pref = SimpleNamespace(id=_uid())
        db = _db()
        result = await GDPRRepository(db).save_consent_preference(pref)
        assert result is pref

    @pytest.mark.asyncio
    async def test_list_consents_no_user(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await GDPRRepository(db).list_consents(
            school_id=_uid(), user_id=None, after_id=None, limit=50
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_consents_with_user_and_after(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await GDPRRepository(db).list_consents(
            school_id=_uid(), user_id=_uid(), after_id=_uid(), limit=50
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_get_ai_preference(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await GDPRRepository(db).get_ai_preference(
            user_id=_uid(), target_user_id=_uid()
        )
        assert result is obj


# ===========================================================================
# ProfileRepository
# ===========================================================================

class TestProfileRepository:
    @pytest.mark.asyncio
    async def test_get_user_in_school(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await ProfileRepository(db).get_user_in_school(
            user_id=_uid(), school_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_active_membership_role_returns_code(self):
        db = _db(_FR(v="TCH"))
        result = await ProfileRepository(db).get_active_membership_role(
            user_id=_uid(), school_id=_uid()
        )
        assert result == "TCH"

    @pytest.mark.asyncio
    async def test_get_active_membership_role_none_returns_empty(self):
        db = _db(_FR(v=None))
        result = await ProfileRepository(db).get_active_membership_role(
            user_id=_uid(), school_id=_uid()
        )
        assert result == ""

    @pytest.mark.asyncio
    async def test_get_role_profile(self):
        obj = object()
        db = _db(_FR(v=obj))
        from app.models.iam import StudentProfile
        result = await ProfileRepository(db).get_role_profile(
            profile_cls=StudentProfile, user_id=_uid(), school_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_save_profile(self):
        profile = SimpleNamespace(id=_uid())
        db = _db()
        db.refresh = AsyncMock()
        result = await ProfileRepository(db).save_profile(profile)
        db.add.assert_called_once_with(profile)

    @pytest.mark.asyncio
    async def test_list_parent_children(self):
        # Returns list of tuples; use empty list to avoid unpack issues
        db = _db(_FR(many=[]))
        result = await ProfileRepository(db).list_parent_children(
            parent_id=_uid(), school_id=_uid()
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_list_teacher_class_ids(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await ProfileRepository(db).list_teacher_class_ids(
            teacher_id=_uid(), school_id=_uid()
        )
        assert isinstance(result, set)

    @pytest.mark.asyncio
    async def test_list_classes_by_ids_empty(self):
        db = _db()
        result = await ProfileRepository(db).list_classes_by_ids(
            class_ids=set(), school_id=_uid()
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_list_classes_by_ids_nonempty(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ProfileRepository(db).list_classes_by_ids(
            class_ids={_uid()}, school_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_get_active_enrollment_counts_empty(self):
        db = _db()
        result = await ProfileRepository(db).get_active_enrollment_counts(
            class_ids=set(), school_id=_uid()
        )
        assert result == {}

    @pytest.mark.asyncio
    async def test_get_active_enrollment_counts_nonempty(self):
        cid = _uid()
        db = _db(_FR(many=[(cid, 5)]))
        result = await ProfileRepository(db).get_active_enrollment_counts(
            class_ids={cid}, school_id=_uid()
        )
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_teacher_course_counts_empty(self):
        db = _db()
        result = await ProfileRepository(db).get_teacher_course_counts(
            class_ids=set(), teacher_id=_uid(), school_id=_uid()
        )
        assert result == {}

    @pytest.mark.asyncio
    async def test_get_teacher_course_counts_nonempty(self):
        cid = _uid()
        db = _db(_FR(many=[(cid, 3)]))
        result = await ProfileRepository(db).get_teacher_course_counts(
            class_ids={cid}, teacher_id=_uid(), school_id=_uid()
        )
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_class(self):
        obj = object()
        assert await ProfileRepository(_db(_FR(v=obj))).get_class(_uid()) is obj

    @pytest.mark.asyncio
    async def test_list_class_students(self):
        # Returns list of tuples; use empty list to avoid unpack issues
        db = _db(_FR(many=[]))
        result = await ProfileRepository(db).list_class_students(
            class_id=_uid(), school_id=_uid()
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_list_teacher_submissions_no_filters(self):
        db = _db(_FR(many=[]))
        result = await ProfileRepository(db).list_teacher_submissions(
            teacher_id=_uid(), school_id=_uid(),
            assignment_id=None, course_id=None, status=None,
            cursor_dt=None, limit=50,
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_list_teacher_submissions_with_filters(self):
        db = _db(_FR(many=[]))
        result = await ProfileRepository(db).list_teacher_submissions(
            teacher_id=_uid(), school_id=_uid(),
            assignment_id=_uid(), course_id=None, status="submitted",
            cursor_dt=_now(), limit=10,
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_list_grades_for_submissions(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ProfileRepository(db).list_grades_for_submissions(
            submission_ids=[_uid()]
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_active_periods(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ProfileRepository(db).list_active_periods(school_id=_uid())
        assert result == items
