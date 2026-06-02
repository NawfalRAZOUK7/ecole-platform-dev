"""Extended coverage tests for lms_quiz.py."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch, MagicMock

import pytest

from app.repositories.lms_quiz import QuizRepository


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
        return SimpleNamespace(all=lambda: many, first=lambda: (many[0] if many else v))

    def first(self):
        return self._many[0] if self._many else self._v

    def one(self):
        return self._v if self._v is not None else (0, 0, None, None, None)

    def one_or_none(self):
        return self._v

    def all(self):
        return self._many

    def mappings(self):
        return SimpleNamespace(all=lambda: self._many)

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
        delete=AsyncMock(),
        refresh=AsyncMock(),
    )
    if side_effects:
        db.execute.side_effect = side_effects
    return db


def _quiz(quiz_id=None, **kwargs):
    q = MagicMock()
    q.id = quiz_id or _uid()
    q.title = kwargs.get("title", "Test Quiz")
    q.status = kwargs.get("status", "published")
    q.subject = kwargs.get("subject", "Math")
    q.level_band = kwargs.get("level_band", "primary")
    q.difficulty = kwargs.get("difficulty", "medium")
    q.max_attempts = kwargs.get("max_attempts", 3)
    q.description = kwargs.get("description", "A quiz")
    q.school_id = kwargs.get("school_id", _uid())
    q.created_by = kwargs.get("created_by", _uid())
    return q


class TestQuizRepositoryExtended:
    """Cover missing lines in lms_quiz.py."""

    @pytest.mark.asyncio
    async def test_list_quizzes_for_actor_student_role(self):
        """Cover STD role branch (line 78)."""
        quiz = _quiz()
        db = _db(_FR(many=[quiz]))
        items, has_more = await QuizRepository(db).list_quizzes_for_actor(
            role="STD",
            school_id=_uid(),
            user_id=_uid(),
            subject=None,
            level_band=None,
            status=None,
            difficulty=None,
            cursor=None,
            limit=10,
        )
        assert items == [quiz]

    @pytest.mark.asyncio
    async def test_list_quizzes_for_actor_content_mgr_role(self):
        """Cover CONTENT_MGR role branch (line 83)."""
        quiz = _quiz()
        db = _db(_FR(many=[quiz]))
        items, has_more = await QuizRepository(db).list_quizzes_for_actor(
            role="CONTENT_MGR",
            school_id=_uid(),
            user_id=_uid(),
            subject=None,
            level_band=None,
            status=None,
            difficulty=None,
            cursor=None,
            limit=10,
        )
        assert items == [quiz]

    @pytest.mark.asyncio
    async def test_list_quizzes_for_actor_other_role_with_filters(self):
        """Cover else/default branch with optional filters (line 85+)."""
        quiz = _quiz()
        db = _db(_FR(many=[quiz]))
        items, has_more = await QuizRepository(db).list_quizzes_for_actor(
            role="TCH",
            school_id=_uid(),
            user_id=_uid(),
            subject="Math",
            level_band="primary",
            status="published",
            difficulty="easy",
            cursor=None,
            limit=10,
        )
        assert items == [quiz]

    @pytest.mark.asyncio
    async def test_list_quizzes_for_actor_with_cursor(self):
        """Cover cursor branch (lines 101-103)."""
        from app.core.response import encode_cursor

        cursor = encode_cursor(_uid())
        db = _db(_FR(many=[]))
        items, has_more = await QuizRepository(db).list_quizzes_for_actor(
            role="ADM",
            school_id=_uid(),
            user_id=_uid(),
            subject=None,
            level_band=None,
            status=None,
            difficulty=None,
            cursor=cursor,
            limit=10,
        )
        assert items == []

    @pytest.mark.asyncio
    async def test_get_question_counts_empty(self):
        """Cover empty quiz_ids early return (line 113)."""
        db = _db()
        result = await QuizRepository(db).get_question_counts([])
        assert result == {}
        db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_question_counts_nonempty(self):
        """Cover non-empty path (lines 113-122)."""
        quiz_id = _uid()
        row = (quiz_id, 5, 50)
        db = _db(_FR(many=[row]))
        result = await QuizRepository(db).get_question_counts([quiz_id])
        assert quiz_id in result
        assert result[quiz_id] == (5, 50)

    @pytest.mark.asyncio
    async def test_delete_quiz_questions_empty(self):
        """Cover empty questions list in delete_quiz_questions (line 155)."""
        db = _db(_FR(many=[]))
        await QuizRepository(db).delete_quiz_questions(_uid())
        db.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_quiz_questions_empty(self):
        """Cover empty questions list (lines 163-166)."""
        db = _db()
        result = await QuizRepository(db).create_quiz_questions([])
        assert result == []
        db.add_all.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_quiz_questions_nonempty(self):
        """Cover non-empty questions list."""
        from unittest.mock import MagicMock

        questions_data = [{"quiz_id": _uid(), "body": "Q1"}]
        db = _db()
        mock_q = MagicMock()
        with patch(
            "app.repositories.lms_quiz.QuizQuestion",
            side_effect=lambda **kw: mock_q,
        ):
            await QuizRepository(db).create_quiz_questions(questions_data)
        db.add_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_quiz_attempts_no_cursor(self):
        """Cover list_quiz_attempts without cursor (lines 336-337)."""
        attempt = MagicMock()
        attempt.id = _uid()
        attempt.started_at = _now()
        db = _db(_FR(many=[(attempt, "Student Name")]))
        items, next_cursor, has_more = await QuizRepository(db).list_quiz_attempts(
            _uid(), cursor=None, limit=10
        )
        assert items == [(attempt, "Student Name")]
        assert has_more is False
        assert next_cursor is None

    @pytest.mark.asyncio
    async def test_list_quiz_attempts_with_cursor(self):
        """Cover cursor branch (line 343)."""
        from app.core.response import encode_cursor

        cursor = encode_cursor(_uid())
        db = _db(_FR(many=[]))
        items, next_cursor, has_more = await QuizRepository(db).list_quiz_attempts(
            _uid(), cursor=cursor, limit=10
        )
        assert items == []

    @pytest.mark.asyncio
    async def test_list_quiz_attempts_has_more(self):
        """Cover has_more path with next_cursor generation."""
        attempt = MagicMock()
        attempt.id = _uid()
        attempts_rows = [(attempt, f"Student {i}") for i in range(3)]
        db = _db(_FR(many=attempts_rows))
        items, next_cursor, has_more = await QuizRepository(db).list_quiz_attempts(
            _uid(), cursor=None, limit=2
        )
        assert has_more is True
        assert next_cursor is not None
        assert len(items) == 2

    @pytest.mark.asyncio
    async def test_list_quiz_attempts_invalid_cursor(self):
        """Cover invalid cursor ValueError exception path."""
        db = _db(_FR(many=[]))
        items, next_cursor, has_more = await QuizRepository(db).list_quiz_attempts(
            _uid(), cursor="invalid_cursor_string", limit=10
        )
        assert items == []

    @pytest.mark.asyncio
    async def test_list_for_class_no_status(self):
        """Cover list_for_class without status filter (lines 391-418)."""
        quiz_id = _uid()
        quiz = _quiz(quiz_id=quiz_id)
        assignment = MagicMock()
        assignment.id = _uid()
        assignment.due_at = None

        # Two calls: first for the join, second for get_question_counts
        db = _db(
            side_effects=[
                _FR(many=[(quiz, assignment)]),  # main query
                _FR(many=[]),  # get_question_counts
            ]
        )
        result = await QuizRepository(db).list_for_class(
            school_id=_uid(), class_id=_uid()
        )
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_list_for_class_with_status(self):
        """Cover status filter branch (line 401)."""
        quiz_id = _uid()
        quiz = _quiz(quiz_id=quiz_id, status="published")
        assignment = MagicMock()
        assignment.id = _uid()
        assignment.due_at = None

        db = _db(
            side_effects=[
                _FR(many=[(quiz, assignment)]),
                _FR(many=[]),  # get_question_counts
            ]
        )
        result = await QuizRepository(db).list_for_class(
            school_id=_uid(), class_id=_uid(), status="published"
        )
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_list_for_class_empty(self):
        """Empty result from list_for_class."""
        db = _db(
            side_effects=[
                _FR(many=[]),  # main query
            ]
        )
        result = await QuizRepository(db).list_for_class(
            school_id=_uid(), class_id=_uid()
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_list_for_student_no_classes(self):
        """list_for_student returns [] when student not enrolled (lines 425-434)."""
        db = _db(_FR(many=[]))
        result = await QuizRepository(db).list_for_student(
            school_id=_uid(), student_id=_uid()
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_list_for_student_with_classes_and_attempt(self):
        """Cover the main path with quiz + attempt (lines 436-466)."""
        class_id = _uid()
        quiz_id = _uid()
        quiz = _quiz(quiz_id=quiz_id)
        assignment = MagicMock()
        assignment.id = _uid()
        assignment.due_at = None

        attempt = MagicMock()
        attempt.status = "COMPLETED"

        db = _db(
            side_effects=[
                _FR(many=[class_id]),  # list class_ids
                _FR(many=[(quiz, assignment)]),  # list quizzes
                _FR(many=[]),  # get_question_counts
                _FR(v=attempt),  # scalars().first() for attempt
            ]
        )
        result = await QuizRepository(db).list_for_student(
            school_id=_uid(), student_id=_uid()
        )
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_list_for_student_no_attempt(self):
        """Cover attempt=None path (line 462)."""
        class_id = _uid()
        quiz_id = _uid()
        quiz = _quiz(quiz_id=quiz_id)
        assignment = MagicMock()
        assignment.id = _uid()
        assignment.due_at = None

        db = _db(
            side_effects=[
                _FR(many=[class_id]),  # list class_ids
                _FR(many=[(quiz, assignment)]),  # list quizzes
                _FR(many=[]),  # get_question_counts
                _FR(v=None),  # scalars().first() returns None
            ]
        )
        result = await QuizRepository(db).list_for_student(
            school_id=_uid(), student_id=_uid()
        )
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_detail_not_found(self):
        """Cover get_detail returns None when quiz doesn't exist (lines 469-477)."""
        db = _db(_FR(v=None))
        result = await QuizRepository(db).get_detail(_uid())
        assert result is None

    @pytest.mark.asyncio
    async def test_get_detail_found(self):
        """Cover get_detail happy path."""
        quiz_id = _uid()
        quiz = _quiz(quiz_id=quiz_id)
        db = _db(
            side_effects=[
                _FR(v=quiz),  # get_quiz
                _FR(many=[]),  # get_question_counts
            ]
        )
        result = await QuizRepository(db).get_detail(quiz_id)
        assert result is not None
        assert result["id"] == str(quiz_id)

    @pytest.mark.asyncio
    async def test_get_results_empty(self):
        """Cover get_results with empty list (lines 493-499)."""
        db = _db(_FR(many=[]))
        result = await QuizRepository(db).get_results(_uid())
        assert result == []

    @pytest.mark.asyncio
    async def test_get_results_with_attempts(self):
        """Cover get_results with attempts."""
        attempt = MagicMock()
        attempt.student_id = _uid()
        attempt.id = _uid()
        attempt.attempt_no = 1
        attempt.status = "COMPLETED"
        attempt.score = 85.0
        attempt.max_score = 100
        attempt.started_at = _now()
        attempt.completed_at = _now()
        db = _db(_FR(many=[attempt]))
        result = await QuizRepository(db).get_results(_uid())
        assert len(result) == 1
        assert result[0]["score"] == 85.0

    @pytest.mark.asyncio
    async def test_get_results_attempt_no_score(self):
        """Cover attempt.score = None path."""
        attempt = MagicMock()
        attempt.student_id = _uid()
        attempt.id = _uid()
        attempt.attempt_no = 1
        attempt.status = "STARTED"
        attempt.score = None
        attempt.max_score = 100
        attempt.started_at = _now()
        attempt.completed_at = None
        db = _db(_FR(many=[attempt]))
        result = await QuizRepository(db).get_results(_uid())
        assert len(result) == 1
        assert result[0]["score"] is None

    @pytest.mark.asyncio
    async def test_count_quiz_questions(self):
        """Cover count_quiz_questions (line 522)."""
        db = _db(_FR(scalar=5))
        result = await QuizRepository(db).count_quiz_questions(_uid())
        assert result == 5

    @pytest.mark.asyncio
    async def test_sum_quiz_points(self):
        """Cover sum_quiz_points (line 534)."""
        db = _db(_FR(scalar=100))
        result = await QuizRepository(db).sum_quiz_points(_uid())
        assert result == 100

    @pytest.mark.asyncio
    async def test_get_attempt_stats_no_attempts(self):
        """Cover get_attempt_stats with zeros."""
        db = _db(_FR(v=(0, 0, None, None, None)))
        result = await QuizRepository(db).get_attempt_stats(_uid())
        total, completed, avg, hi, lo = result
        assert total == 0
        assert completed == 0
        assert avg is None

    @pytest.mark.asyncio
    async def test_get_attempt_stats_with_data(self):
        """Cover get_attempt_stats happy path."""
        db = _db(_FR(v=(10, 8, 75.5, 100.0, 50.0)))
        result = await QuizRepository(db).get_attempt_stats(_uid())
        total, completed, avg, hi, lo = result
        assert total == 10
        assert completed == 8
        assert avg == 75.5
