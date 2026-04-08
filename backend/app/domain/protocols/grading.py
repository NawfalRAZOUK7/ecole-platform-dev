"""Grading strategies for different evaluatable types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol
from uuid import UUID

from app.domain.value_objects.grade import MoroccanGrade


class QuizAttemptLike(Protocol):
    """Structural protocol for quiz attempts used by grading strategies."""

    id: UUID


class QuizQuestionLike(Protocol):
    """Structural protocol for quiz question rows."""

    id: UUID
    question_type: str
    correct_answer: Any
    points: int


class QuizResponseLike(Protocol):
    """Structural protocol for quiz response rows."""

    question_id: UUID
    student_answer: Any


class QuizGradingRepository(Protocol):
    """Minimum quiz repository surface required for auto-grading."""

    async def get_latest_attempt_for_student(
        self,
        *,
        quiz_id: UUID,
        student_id: UUID,
    ) -> QuizAttemptLike | None: ...

    async def list_quiz_questions(self, quiz_id: UUID) -> list[QuizQuestionLike]: ...

    async def list_attempt_responses(
        self, attempt_id: UUID
    ) -> list[QuizResponseLike]: ...


class GradingStrategy(ABC):
    """Abstract grading strategy."""

    @abstractmethod
    async def grade(
        self, item_id: UUID, student_id: UUID, **kwargs: Any
    ) -> MoroccanGrade:
        """Compute the Moroccan-scale grade for one student work item."""
        ...

    @abstractmethod
    async def can_auto_grade(self) -> bool:
        """Return whether this strategy grades without teacher input."""
        ...


class QuizAutoGradeStrategy(GradingStrategy):
    """Auto-grades quiz attempts from stored JSON answers."""

    def __init__(self, quiz_repository: QuizGradingRepository) -> None:
        self._quiz_repository = quiz_repository

    async def grade(
        self, item_id: UUID, student_id: UUID, **kwargs: Any
    ) -> MoroccanGrade:
        attempt = await self._quiz_repository.get_latest_attempt_for_student(
            quiz_id=item_id,
            student_id=student_id,
        )
        if attempt is None:
            raise ValueError("Quiz attempt not found for student")

        questions = {
            question.id: question
            for question in await self._quiz_repository.list_quiz_questions(item_id)
        }
        responses = await self._quiz_repository.list_attempt_responses(attempt.id)

        max_points = sum(int(question.points or 0) for question in questions.values())
        if max_points <= 0:
            return MoroccanGrade.from_float(0.0)

        total_points = 0.0
        for response in responses:
            question = questions.get(response.question_id)
            if question is None:
                continue
            _is_correct, points_earned = _grade_response(
                question_type=question.question_type,
                student_answer=response.student_answer,
                correct_answer=question.correct_answer,
                points=int(question.points or 0),
            )
            total_points += points_earned

        normalized_score = (total_points / max_points) * 20
        return MoroccanGrade.from_float(normalized_score)

    async def can_auto_grade(self) -> bool:
        return True


class ManualGradeStrategy(GradingStrategy):
    """Manual grading by teacher for assignments and assessments."""

    async def grade(
        self, item_id: UUID, student_id: UUID, **kwargs: Any
    ) -> MoroccanGrade:
        score = kwargs.get("score")
        if score is None:
            raise ValueError("Manual grading requires a score")
        return MoroccanGrade.from_float(float(score))

    async def can_auto_grade(self) -> bool:
        return False


def _grade_response(
    *,
    question_type: str,
    student_answer: Any,
    correct_answer: Any,
    points: int,
) -> tuple[bool, float]:
    if student_answer is None:
        return False, 0.0

    grader = _QUIZ_GRADERS.get(question_type)
    if grader is None:
        return False, 0.0

    is_correct = grader(student_answer, correct_answer)
    return is_correct, float(points) if is_correct else 0.0


def _grade_mcq(student: Any, correct: Any) -> bool:
    if isinstance(student, str):
        student = [student]
    if isinstance(correct, str):
        correct = [correct]
    return sorted(str(value) for value in student) == sorted(
        str(value) for value in correct
    )


def _grade_true_false(student: Any, correct: Any) -> bool:
    if isinstance(student, str):
        student = student.lower() in {"true", "1", "yes", "vrai"}
    if isinstance(correct, str):
        correct = correct.lower() in {"true", "1", "yes", "vrai"}
    return bool(student) == bool(correct)


def _grade_fill_in(student: Any, correct: Any) -> bool:
    student_value = str(student).strip().lower()
    if isinstance(correct, list):
        return student_value in [str(item).strip().lower() for item in correct]
    return student_value == str(correct).strip().lower()


def _grade_mapping(student: Any, correct: Any) -> bool:
    if not isinstance(student, dict) or not isinstance(correct, dict):
        return False
    return {str(key): str(value) for key, value in student.items()} == {
        str(key): str(value) for key, value in correct.items()
    }


_QUIZ_GRADERS = {
    "MCQ": _grade_mcq,
    "TRUE_FALSE": _grade_true_false,
    "FILL_IN": _grade_fill_in,
    "DRAG_DROP": _grade_mapping,
    "MATCHING": _grade_mapping,
}
