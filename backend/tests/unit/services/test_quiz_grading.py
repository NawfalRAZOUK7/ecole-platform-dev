"""Unit tests for app/services/lms/quiz_grading.py — full branch coverage.

Pure grading functions are tested directly.
grade_attempt() is tested with both UoW paths via a fake QuizRepository.
"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.lms.quiz_grading import (
    _grade_drag_drop,
    _grade_fill_in,
    _grade_matching,
    _grade_mcq,
    _grade_true_false,
    grade_attempt,
    grade_response,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _question(*, id=None, question_type="MCQ", correct_answer=None, points=10):
    return SimpleNamespace(
        id=id or uuid.uuid4(),
        question_type=question_type,
        correct_answer=correct_answer,
        points=points,
    )


def _response(*, question_id=None, student_answer=None):
    r = SimpleNamespace(
        question_id=question_id or uuid.uuid4(),
        student_answer=student_answer,
        is_correct=None,
        points_earned=None,
    )
    return r


def _attempt_model(*, id=None, quiz_id=None, score=0, max_score=0, status="IN_PROGRESS"):
    return SimpleNamespace(
        id=id or uuid.uuid4(),
        quiz_id=quiz_id or uuid.uuid4(),
        score=score,
        max_score=max_score,
        status=status,
        completed_at=None,
    )


class FakeQuizRepository:
    def __init__(
        self,
        *,
        attempt=None,
        questions=None,
        responses=None,
    ):
        self._attempt = attempt
        self._questions = questions or []
        self._responses = responses or []
        self.saved_attempt = None

    async def get_quiz_attempt(self, attempt_id):
        return self._attempt

    async def list_quiz_questions(self, quiz_id):
        return self._questions

    async def list_attempt_responses(self, attempt_id):
        return self._responses

    async def save_quiz_attempt(self, attempt):
        self.saved_attempt = attempt


class _FakeUoW:
    def __init__(self, session=None):
        self.session = session or AsyncMock()
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def commit(self):
        self.committed = True


# ---------------------------------------------------------------------------
# grade_response — None student_answer
# ---------------------------------------------------------------------------

def test_grade_response_none_answer():
    is_correct, pts = grade_response("MCQ", None, ["a"], 10)
    assert is_correct is False
    assert pts == 0.0


def test_grade_response_unknown_type():
    is_correct, pts = grade_response("UNKNOWN", "answer", "correct", 5)
    assert is_correct is False
    assert pts == 0.0


# ---------------------------------------------------------------------------
# grade_response — MCQ
# ---------------------------------------------------------------------------

def test_grade_response_mcq_correct():
    is_correct, pts = grade_response("MCQ", ["a", "b"], ["a", "b"], 10)
    assert is_correct is True
    assert pts == 10.0


def test_grade_response_mcq_incorrect():
    is_correct, pts = grade_response("MCQ", ["a"], ["b"], 10)
    assert is_correct is False
    assert pts == 0.0


def test_grade_response_returns_zero_pts_on_incorrect():
    _, pts = grade_response("MCQ", "wrong", ["correct"], 5)
    assert pts == 0.0


# ---------------------------------------------------------------------------
# _grade_mcq — all branches
# ---------------------------------------------------------------------------

def test_grade_mcq_list_match():
    assert _grade_mcq(["a", "b"], ["b", "a"]) is True


def test_grade_mcq_list_mismatch():
    assert _grade_mcq(["a"], ["b"]) is False


def test_grade_mcq_student_is_string():
    assert _grade_mcq("a", ["a"]) is True


def test_grade_mcq_correct_is_string():
    assert _grade_mcq(["a"], "a") is True


def test_grade_mcq_both_strings():
    assert _grade_mcq("x", "x") is True


def test_grade_mcq_multi_select_correct():
    assert _grade_mcq(["c", "a"], ["a", "c"]) is True


def test_grade_mcq_multi_select_incorrect():
    assert _grade_mcq(["a", "c"], ["a", "b"]) is False


# ---------------------------------------------------------------------------
# _grade_true_false — all branches
# ---------------------------------------------------------------------------

def test_grade_true_false_both_bool():
    assert _grade_true_false(True, True) is True
    assert _grade_true_false(False, True) is False


def test_grade_true_false_student_string_true():
    assert _grade_true_false("true", True) is True
    assert _grade_true_false("1", True) is True
    assert _grade_true_false("yes", True) is True
    assert _grade_true_false("vrai", True) is True


def test_grade_true_false_student_string_false():
    assert _grade_true_false("false", False) is True
    assert _grade_true_false("no", False) is True


def test_grade_true_false_correct_string():
    assert _grade_true_false(True, "true") is True
    assert _grade_true_false(False, "false") is True


def test_grade_true_false_string_mismatch():
    assert _grade_true_false("true", "false") is False


# ---------------------------------------------------------------------------
# _grade_fill_in — all branches
# ---------------------------------------------------------------------------

def test_grade_fill_in_correct_list():
    assert _grade_fill_in("Paris", ["paris", "PARIS"]) is True


def test_grade_fill_in_wrong_list():
    assert _grade_fill_in("Lyon", ["paris"]) is False


def test_grade_fill_in_case_insensitive():
    assert _grade_fill_in("PARIS", ["paris"]) is True


def test_grade_fill_in_single_string_correct():
    assert _grade_fill_in("paris", "paris") is True


def test_grade_fill_in_single_string_wrong():
    assert _grade_fill_in("paris", "london") is False


def test_grade_fill_in_strips_whitespace():
    assert _grade_fill_in("  paris  ", ["paris"]) is True


# ---------------------------------------------------------------------------
# _grade_drag_drop — all branches
# ---------------------------------------------------------------------------

def test_grade_drag_drop_correct():
    assert _grade_drag_drop({"a": "z1", "b": "z2"}, {"a": "z1", "b": "z2"}) is True


def test_grade_drag_drop_wrong():
    assert _grade_drag_drop({"a": "z1"}, {"a": "z2"}) is False


def test_grade_drag_drop_student_not_dict():
    assert _grade_drag_drop("not_a_dict", {"a": "z1"}) is False


def test_grade_drag_drop_correct_not_dict():
    assert _grade_drag_drop({"a": "z1"}, "not_a_dict") is False


def test_grade_drag_drop_both_not_dict():
    assert _grade_drag_drop(None, None) is False


def test_grade_drag_drop_string_coercion():
    # Keys and values are coerced to str
    assert _grade_drag_drop({1: 2}, {"1": "2"}) is True


# ---------------------------------------------------------------------------
# _grade_matching — all branches
# ---------------------------------------------------------------------------

def test_grade_matching_correct():
    assert _grade_matching({"left1": "right1"}, {"left1": "right1"}) is True


def test_grade_matching_wrong():
    assert _grade_matching({"left1": "right2"}, {"left1": "right1"}) is False


def test_grade_matching_student_not_dict():
    assert _grade_matching("not_dict", {"left1": "right1"}) is False


def test_grade_matching_correct_not_dict():
    assert _grade_matching({"left1": "right1"}, None) is False


def test_grade_matching_string_coercion():
    assert _grade_matching({1: 2}, {"1": "2"}) is True


# ---------------------------------------------------------------------------
# grade_attempt — with UoW depth (direct session path)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_grade_attempt_with_uow_depth_scores_correctly():
    quiz_id = uuid.uuid4()
    attempt_id = uuid.uuid4()
    q_id = uuid.uuid4()

    q = _question(id=q_id, question_type="MCQ", correct_answer=["a"], points=10)
    resp = _response(question_id=q_id, student_answer=["a"])
    att = _attempt_model(id=attempt_id, quiz_id=quiz_id)

    fake_repo = FakeQuizRepository(attempt=att, questions=[q], responses=[resp])
    mock_db = AsyncMock()
    mock_db.info = {"_uow_depth": 1}

    with patch("app.services.lms.quiz_grading.QuizRepository", return_value=fake_repo):
        total, max_s = await grade_attempt(attempt_id, mock_db)

    assert total == 10.0
    assert max_s == 10
    assert resp.is_correct is True
    assert resp.points_earned == 10.0
    assert att.status == "COMPLETED"
    assert att.score == 10.0
    assert att.max_score == 10
    assert att.completed_at is not None
    assert fake_repo.saved_attempt is att


@pytest.mark.asyncio
async def test_grade_attempt_with_uow_depth_wrong_answer():
    quiz_id = uuid.uuid4()
    attempt_id = uuid.uuid4()
    q_id = uuid.uuid4()

    q = _question(id=q_id, question_type="MCQ", correct_answer=["a"], points=10)
    resp = _response(question_id=q_id, student_answer=["b"])
    att = _attempt_model(id=attempt_id, quiz_id=quiz_id)

    fake_repo = FakeQuizRepository(attempt=att, questions=[q], responses=[resp])
    mock_db = AsyncMock()
    mock_db.info = {"_uow_depth": 1}

    with patch("app.services.lms.quiz_grading.QuizRepository", return_value=fake_repo):
        total, max_s = await grade_attempt(attempt_id, mock_db)

    assert total == 0.0
    assert max_s == 10
    assert resp.is_correct is False
    assert resp.points_earned == 0.0


@pytest.mark.asyncio
async def test_grade_attempt_attempt_not_found_raises():
    mock_db = AsyncMock()
    mock_db.info = {"_uow_depth": 1}
    fake_repo = FakeQuizRepository(attempt=None)

    with patch("app.services.lms.quiz_grading.QuizRepository", return_value=fake_repo):
        with pytest.raises(ValueError, match="not found"):
            await grade_attempt(uuid.uuid4(), mock_db)


@pytest.mark.asyncio
async def test_grade_attempt_empty_responses():
    quiz_id = uuid.uuid4()
    attempt_id = uuid.uuid4()
    q = _question(id=uuid.uuid4(), question_type="MCQ", correct_answer=["a"], points=5)
    att = _attempt_model(id=attempt_id, quiz_id=quiz_id)

    fake_repo = FakeQuizRepository(attempt=att, questions=[q], responses=[])
    mock_db = AsyncMock()
    mock_db.info = {"_uow_depth": 1}

    with patch("app.services.lms.quiz_grading.QuizRepository", return_value=fake_repo):
        total, max_s = await grade_attempt(attempt_id, mock_db)

    assert total == 0.0
    assert max_s == 5


@pytest.mark.asyncio
async def test_grade_attempt_response_question_not_in_map():
    """Response refers to a question_id not in the questions dict → skipped."""
    quiz_id = uuid.uuid4()
    attempt_id = uuid.uuid4()
    att = _attempt_model(id=attempt_id, quiz_id=quiz_id)
    # No questions, but one response → question not found → continue
    resp = _response(question_id=uuid.uuid4(), student_answer=["a"])

    fake_repo = FakeQuizRepository(attempt=att, questions=[], responses=[resp])
    mock_db = AsyncMock()
    mock_db.info = {"_uow_depth": 1}

    with patch("app.services.lms.quiz_grading.QuizRepository", return_value=fake_repo):
        total, max_s = await grade_attempt(attempt_id, mock_db)

    assert total == 0.0
    assert max_s == 0


@pytest.mark.asyncio
async def test_grade_attempt_multiple_questions_mixed():
    quiz_id = uuid.uuid4()
    attempt_id = uuid.uuid4()
    q1_id = uuid.uuid4()
    q2_id = uuid.uuid4()

    q1 = _question(id=q1_id, question_type="MCQ", correct_answer=["a"], points=10)
    q2 = _question(id=q2_id, question_type="FILL_IN", correct_answer=["paris"], points=5)
    r1 = _response(question_id=q1_id, student_answer=["a"])   # correct
    r2 = _response(question_id=q2_id, student_answer="london")  # wrong
    att = _attempt_model(id=attempt_id, quiz_id=quiz_id)

    fake_repo = FakeQuizRepository(attempt=att, questions=[q1, q2], responses=[r1, r2])
    mock_db = AsyncMock()
    mock_db.info = {"_uow_depth": 1}

    with patch("app.services.lms.quiz_grading.QuizRepository", return_value=fake_repo):
        total, max_s = await grade_attempt(attempt_id, mock_db)

    assert total == 10.0
    assert max_s == 15


# ---------------------------------------------------------------------------
# grade_attempt — without UoW depth (creates own UoW)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_grade_attempt_without_uow_depth_commits():
    quiz_id = uuid.uuid4()
    attempt_id = uuid.uuid4()
    att = _attempt_model(id=attempt_id, quiz_id=quiz_id)
    fake_repo = FakeQuizRepository(attempt=att, questions=[], responses=[])

    mock_db = AsyncMock()
    mock_db.info = {}  # no _uow_depth

    fake_uow = _FakeUoW(session=mock_db)

    with (
        patch("app.services.lms.quiz_grading.UnitOfWork", return_value=fake_uow),
        patch("app.services.lms.quiz_grading.QuizRepository", return_value=fake_repo),
    ):
        total, max_s = await grade_attempt(attempt_id, mock_db)

    assert total == 0.0
    assert fake_uow.committed is True


@pytest.mark.asyncio
async def test_grade_attempt_without_uow_depth_scores():
    quiz_id = uuid.uuid4()
    attempt_id = uuid.uuid4()
    q_id = uuid.uuid4()
    q = _question(id=q_id, question_type="TRUE_FALSE", correct_answer=True, points=4)
    resp = _response(question_id=q_id, student_answer=True)
    att = _attempt_model(id=attempt_id, quiz_id=quiz_id)

    fake_repo = FakeQuizRepository(attempt=att, questions=[q], responses=[resp])
    mock_db = AsyncMock()
    mock_db.info = {}
    fake_uow = _FakeUoW(session=mock_db)

    with (
        patch("app.services.lms.quiz_grading.UnitOfWork", return_value=fake_uow),
        patch("app.services.lms.quiz_grading.QuizRepository", return_value=fake_repo),
    ):
        total, max_s = await grade_attempt(attempt_id, mock_db)

    assert total == 4.0
    assert max_s == 4
    assert fake_uow.committed is True


# ---------------------------------------------------------------------------
# grade_response — all 5 types via grade_response wrapper
# ---------------------------------------------------------------------------

def test_grade_response_true_false():
    is_correct, pts = grade_response("TRUE_FALSE", True, True, 3)
    assert is_correct is True
    assert pts == 3.0


def test_grade_response_fill_in():
    is_correct, pts = grade_response("FILL_IN", "paris", ["paris", "Paris"], 2)
    assert is_correct is True
    assert pts == 2.0


def test_grade_response_drag_drop():
    is_correct, pts = grade_response(
        "DRAG_DROP", {"a": "z1"}, {"a": "z1"}, 5
    )
    assert is_correct is True
    assert pts == 5.0


def test_grade_response_matching():
    is_correct, pts = grade_response(
        "MATCHING", {"l1": "r1"}, {"l1": "r1"}, 4
    )
    assert is_correct is True
    assert pts == 4.0
