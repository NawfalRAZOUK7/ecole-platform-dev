"""Quiz auto-grading service — Phase 9B.

Grades all 5 question types by comparing student_answer to correct_answer.
- MCQ: exact match of selected option IDs (supports multi-select)
- TRUE_FALSE: exact boolean match
- FILL_IN: case-insensitive match against accepted alternatives
- DRAG_DROP: exact zone mapping match
- MATCHING: exact pair mapping match
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.quiz import QuizRepository

logger = logging.getLogger(__name__)


def grade_response(
    question_type: str,
    student_answer: Any,
    correct_answer: Any,
    points: int,
) -> tuple[bool, float]:
    """Grade a single response. Returns (is_correct, points_earned)."""
    if student_answer is None:
        return False, 0.0

    grader = _GRADERS.get(question_type)
    if grader is None:
        logger.warning("Unknown question type: %s", question_type)
        return False, 0.0

    is_correct = grader(student_answer, correct_answer)
    return is_correct, float(points) if is_correct else 0.0


def _grade_mcq(student: Any, correct: Any) -> bool:
    """MCQ: correct_answer is a list of option IDs, e.g. ["a"] or ["a","c"]."""
    if isinstance(student, str):
        student = [student]
    if isinstance(correct, str):
        correct = [correct]
    return sorted(str(s) for s in student) == sorted(str(c) for c in correct)


def _grade_true_false(student: Any, correct: Any) -> bool:
    """TRUE_FALSE: correct_answer is a boolean."""
    if isinstance(student, str):
        student = student.lower() in ("true", "1", "yes", "vrai")
    if isinstance(correct, str):
        correct = correct.lower() in ("true", "1", "yes", "vrai")
    return bool(student) == bool(correct)


def _grade_fill_in(student: Any, correct: Any) -> bool:
    """FILL_IN: correct_answer is a list of accepted alternatives."""
    student_str = str(student).strip().lower()
    if isinstance(correct, list):
        return student_str in [str(c).strip().lower() for c in correct]
    return student_str == str(correct).strip().lower()


def _grade_drag_drop(student: Any, correct: Any) -> bool:
    """DRAG_DROP: correct_answer is {"item_id": "zone_id", ...}."""
    if not isinstance(student, dict) or not isinstance(correct, dict):
        return False
    return {str(k): str(v) for k, v in student.items()} == {
        str(k): str(v) for k, v in correct.items()
    }


def _grade_matching(student: Any, correct: Any) -> bool:
    """MATCHING: correct_answer is {"left_id": "right_id", ...}."""
    if not isinstance(student, dict) or not isinstance(correct, dict):
        return False
    return {str(k): str(v) for k, v in student.items()} == {
        str(k): str(v) for k, v in correct.items()
    }


_GRADERS = {
    "MCQ": _grade_mcq,
    "TRUE_FALSE": _grade_true_false,
    "FILL_IN": _grade_fill_in,
    "DRAG_DROP": _grade_drag_drop,
    "MATCHING": _grade_matching,
}


async def grade_attempt(attempt_id, db: AsyncSession) -> tuple[float, int]:
    """Grade all responses for an attempt. Returns (total_score, max_score).

    Updates each QuizResponse with is_correct and points_earned.
    Updates the QuizAttempt with score, max_score, and status=COMPLETED.
    """
    repo = QuizRepository(db)
    attempt = await repo.get_quiz_attempt(attempt_id)
    if attempt is None:
        raise ValueError(f"Attempt {attempt_id} not found")

    questions = {
        question.id: question
        for question in await repo.list_quiz_questions(attempt.quiz_id)
    }
    responses = await repo.list_attempt_responses(attempt_id)

    total_score = 0.0
    max_score = sum(q.points for q in questions.values())

    for resp in responses:
        question = questions.get(resp.question_id)
        if question is None:
            continue
        is_correct, points_earned = grade_response(
            question.question_type,
            resp.student_answer,
            question.correct_answer,
            question.points,
        )
        resp.is_correct = is_correct
        resp.points_earned = points_earned
        total_score += points_earned

    # Update attempt
    attempt.score = total_score
    attempt.max_score = max_score
    attempt.status = "COMPLETED"
    attempt.completed_at = datetime.now(timezone.utc)

    await repo.save_quiz_attempt(attempt)
    return total_score, max_score
