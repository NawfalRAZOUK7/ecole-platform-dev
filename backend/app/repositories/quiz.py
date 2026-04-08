"""Repository helpers for quiz CRUD, attempts, grading, and analytics."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import func, select

from app.core.response import decode_cursor
from app.models.erp import Enrollment
from app.models.lms import (
    Assignment,
    Course,
    Quiz,
    QuizAttempt,
    QuizQuestion,
    QuizResponse,
)
from app.repositories.base import BaseRepository


class QuizRepository(BaseRepository):
    """Data access helpers for quiz workflows."""

    async def _paginate_scalars(
        self,
        query,
        *,
        limit: int,
    ) -> tuple[list[Any], bool]:
        result = await self.db.execute(query.limit(limit + 1))
        items = list(result.scalars().all())
        has_more = len(items) > limit
        if has_more:
            items = items[:limit]
        return items, has_more

    async def get_quiz(
        self,
        quiz_id: uuid.UUID,
    ) -> Quiz | None:
        result = await self.db.execute(select(Quiz).where(Quiz.id == quiz_id))
        return result.scalar_one_or_none()

    async def create_quiz(
        self,
        **kwargs: Any,
    ) -> Quiz:
        quiz = Quiz(**kwargs)
        self.db.add(quiz)
        await self.db.flush()
        return quiz

    async def save_quiz(
        self,
        quiz: Quiz,
    ) -> Quiz:
        self.db.add(quiz)
        await self.db.flush()
        return quiz

    async def list_quizzes_for_actor(
        self,
        *,
        role: str,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        subject: str | None,
        level_band: str | None,
        status: str | None,
        difficulty: str | None,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[Quiz], bool]:
        if role == "STD":
            query = select(Quiz).where(
                Quiz.status == "published",
                (Quiz.school_id == school_id) | (Quiz.school_id.is_(None)),
            )
        elif role == "CONTENT_MGR":
            query = select(Quiz).where(Quiz.school_id.is_(None))
        else:
            query = select(Quiz).where(
                (Quiz.created_by == user_id)
                | ((Quiz.status == "published") & (Quiz.school_id.is_(None)))
            )

        if subject:
            query = query.where(Quiz.subject == subject)
        if level_band:
            query = query.where(Quiz.level_band == level_band)
        if status:
            query = query.where(Quiz.status == status)
        if difficulty:
            query = query.where(Quiz.difficulty == difficulty)

        query = query.order_by(Quiz.id)

        if cursor:
            last_id, _ = decode_cursor(cursor)
            query = query.where(Quiz.id > last_id)

        return await self._paginate_scalars(query, limit=limit)

    async def get_question_counts(
        self,
        quiz_ids: list[uuid.UUID],
    ) -> dict[uuid.UUID, tuple[int, int]]:
        if not quiz_ids:
            return {}
        result = await self.db.execute(
            select(
                QuizQuestion.quiz_id,
                func.count(QuizQuestion.id),
                func.sum(QuizQuestion.points),
            )
            .where(QuizQuestion.quiz_id.in_(quiz_ids))
            .group_by(QuizQuestion.quiz_id)
        )
        return {row[0]: (int(row[1] or 0), int(row[2] or 0)) for row in result.all()}

    async def list_quiz_questions(
        self,
        quiz_id: uuid.UUID,
    ) -> list[QuizQuestion]:
        result = await self.db.execute(
            select(QuizQuestion)
            .where(QuizQuestion.quiz_id == quiz_id)
            .order_by(QuizQuestion.order)
        )
        return list(result.scalars().all())

    async def get_quiz_question(
        self,
        *,
        quiz_id: uuid.UUID,
        question_id: uuid.UUID,
    ) -> QuizQuestion | None:
        result = await self.db.execute(
            select(QuizQuestion).where(
                QuizQuestion.id == question_id,
                QuizQuestion.quiz_id == quiz_id,
            )
        )
        return result.scalar_one_or_none()

    async def delete_quiz_questions(
        self,
        quiz_id: uuid.UUID,
    ) -> None:
        questions = await self.list_quiz_questions(quiz_id)
        for question in questions:
            await self.db.delete(question)
        await self.db.flush()

    async def create_quiz_questions(
        self,
        questions_data: list[dict[str, Any]],
    ) -> list[QuizQuestion]:
        questions = [QuizQuestion(**data) for data in questions_data]
        if questions:
            self.db.add_all(questions)
            await self.db.flush()
        return questions

    async def count_quiz_questions(
        self,
        quiz_id: uuid.UUID,
    ) -> int:
        result = await self.db.execute(
            select(func.count(QuizQuestion.id)).where(QuizQuestion.quiz_id == quiz_id)
        )
        return int(result.scalar() or 0)

    async def sum_quiz_points(
        self,
        quiz_id: uuid.UUID,
    ) -> int:
        result = await self.db.execute(
            select(func.sum(QuizQuestion.points)).where(QuizQuestion.quiz_id == quiz_id)
        )
        return int(result.scalar() or 0)

    async def get_quiz_attempt(
        self,
        attempt_id: uuid.UUID,
    ) -> QuizAttempt | None:
        result = await self.db.execute(
            select(QuizAttempt).where(QuizAttempt.id == attempt_id)
        )
        return result.scalar_one_or_none()

    async def get_latest_attempt_for_student(
        self,
        *,
        quiz_id: uuid.UUID,
        student_id: uuid.UUID,
    ) -> QuizAttempt | None:
        result = await self.db.execute(
            select(QuizAttempt)
            .where(
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.student_id == student_id,
            )
            .order_by(QuizAttempt.attempt_no.desc(), QuizAttempt.started_at.desc())
        )
        return result.scalars().first()

    async def create_quiz_attempt(
        self,
        **kwargs: Any,
    ) -> QuizAttempt:
        attempt = QuizAttempt(**kwargs)
        self.db.add(attempt)
        await self.db.flush()
        return attempt

    async def save_quiz_attempt(
        self,
        attempt: QuizAttempt,
    ) -> QuizAttempt:
        self.db.add(attempt)
        await self.db.flush()
        return attempt

    async def count_student_attempts(
        self,
        *,
        quiz_id: uuid.UUID,
        student_id: uuid.UUID,
    ) -> int:
        result = await self.db.execute(
            select(func.count(QuizAttempt.id)).where(
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.student_id == student_id,
            )
        )
        return int(result.scalar() or 0)

    async def get_active_attempt(
        self,
        *,
        quiz_id: uuid.UUID,
        student_id: uuid.UUID,
    ) -> QuizAttempt | None:
        result = await self.db.execute(
            select(QuizAttempt).where(
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.student_id == student_id,
                QuizAttempt.status == "STARTED",
            )
        )
        return result.scalar_one_or_none()

    async def get_quiz_response(
        self,
        *,
        attempt_id: uuid.UUID,
        question_id: uuid.UUID,
    ) -> QuizResponse | None:
        result = await self.db.execute(
            select(QuizResponse).where(
                QuizResponse.attempt_id == attempt_id,
                QuizResponse.question_id == question_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_quiz_response(
        self,
        **kwargs: Any,
    ) -> QuizResponse:
        response = QuizResponse(**kwargs)
        self.db.add(response)
        await self.db.flush()
        return response

    async def save_quiz_response(
        self,
        response: QuizResponse,
    ) -> QuizResponse:
        self.db.add(response)
        await self.db.flush()
        return response

    async def list_attempt_responses(
        self,
        attempt_id: uuid.UUID,
    ) -> list[QuizResponse]:
        result = await self.db.execute(
            select(QuizResponse).where(QuizResponse.attempt_id == attempt_id)
        )
        return list(result.scalars().all())

    async def list_attempt_responses_with_questions(
        self,
        attempt_id: uuid.UUID,
    ) -> list[tuple[QuizResponse, QuizQuestion]]:
        result = await self.db.execute(
            select(QuizResponse, QuizQuestion)
            .join(QuizQuestion, QuizResponse.question_id == QuizQuestion.id)
            .where(QuizResponse.attempt_id == attempt_id)
            .order_by(QuizQuestion.order)
        )
        return list(result.all())

    async def get_attempt_stats(
        self,
        quiz_id: uuid.UUID,
    ) -> tuple[int, int, float | None, float | None, float | None]:
        result = await self.db.execute(
            select(
                func.count(QuizAttempt.id),
                func.count(QuizAttempt.id).filter(QuizAttempt.status == "COMPLETED"),
                func.avg(QuizAttempt.score).filter(QuizAttempt.status == "COMPLETED"),
                func.max(QuizAttempt.score).filter(QuizAttempt.status == "COMPLETED"),
                func.min(QuizAttempt.score).filter(QuizAttempt.status == "COMPLETED"),
            ).where(QuizAttempt.quiz_id == quiz_id)
        )
        total_attempts, completed, avg_score, max_achieved, min_achieved = result.one()
        return (
            int(total_attempts or 0),
            int(completed or 0),
            float(avg_score) if avg_score is not None else None,
            float(max_achieved) if max_achieved is not None else None,
            float(min_achieved) if min_achieved is not None else None,
        )

    async def get_question_response_stats(
        self,
        question_id: uuid.UUID,
    ) -> tuple[int, int]:
        result = await self.db.execute(
            select(
                func.count(QuizResponse.id),
                func.count(QuizResponse.id).filter(QuizResponse.is_correct),
            ).where(QuizResponse.question_id == question_id)
        )
        total_responses, correct_responses = result.one()
        return int(total_responses or 0), int(correct_responses or 0)

    async def list_for_class(
        self,
        school_id: uuid.UUID,
        class_id: uuid.UUID,
        *,
        status: str | None = None,
    ) -> list[dict]:
        query = (
            select(Quiz, Assignment)
            .join(Assignment, Assignment.quiz_id == Quiz.id)
            .join(Course, Course.id == Assignment.course_id)
            .where(
                Course.school_id == school_id,
                Course.class_id == class_id,
            )
            .order_by(Assignment.due_at.asc(), Quiz.id.asc())
        )
        if status is not None:
            query = query.where(Quiz.status == status)

        result = await self.db.execute(query)
        rows = list(result.all())
        question_counts = await self.get_question_counts(
            [quiz.id for quiz, _assignment in rows]
        )
        return [
            self._serialize_evaluatable(
                quiz=quiz,
                due_at=assignment.due_at,
                total_points=question_counts.get(quiz.id, (0, 0))[1],
                status=quiz.status,
                assignment_id=assignment.id,
            )
            for quiz, assignment in rows
        ]

    async def list_for_student(
        self,
        school_id: uuid.UUID,
        student_id: uuid.UUID,
    ) -> list[dict]:
        class_result = await self.db.execute(
            select(Enrollment.class_id).where(
                Enrollment.student_id == student_id,
                Enrollment.school_id == school_id,
                Enrollment.status == "active",
            )
        )
        class_ids = list(class_result.scalars().all())
        if not class_ids:
            return []

        result = await self.db.execute(
            select(Quiz, Assignment)
            .join(Assignment, Assignment.quiz_id == Quiz.id)
            .join(Course, Course.id == Assignment.course_id)
            .where(
                Course.school_id == school_id,
                Course.class_id.in_(class_ids),
            )
            .order_by(Assignment.due_at.asc(), Quiz.id.asc())
        )
        rows = list(result.all())
        question_counts = await self.get_question_counts(
            [quiz.id for quiz, _assignment in rows]
        )

        items: list[dict] = []
        for quiz, assignment in rows:
            attempt = await self.get_latest_attempt_for_student(
                quiz_id=quiz.id,
                student_id=student_id,
            )
            items.append(
                self._serialize_evaluatable(
                    quiz=quiz,
                    due_at=assignment.due_at,
                    total_points=question_counts.get(quiz.id, (0, 0))[1],
                    status=attempt.status if attempt is not None else quiz.status,
                    assignment_id=assignment.id,
                )
            )
        return items

    async def get_detail(self, item_id: uuid.UUID) -> dict | None:
        quiz = await self.get_quiz(item_id)
        if quiz is None:
            return None

        question_count, total_points = (await self.get_question_counts([item_id])).get(
            item_id,
            (0, 0),
        )
        return {
            **self._serialize_evaluatable(
                quiz=quiz,
                due_at=None,
                total_points=total_points,
                status=quiz.status,
            ),
            "description": quiz.description,
            "subject": quiz.subject,
            "level_band": quiz.level_band,
            "difficulty": quiz.difficulty,
            "max_attempts": quiz.max_attempts,
            "question_count": question_count,
        }

    async def get_results(self, item_id: uuid.UUID) -> list[dict]:
        result = await self.db.execute(
            select(QuizAttempt)
            .where(QuizAttempt.quiz_id == item_id)
            .order_by(QuizAttempt.started_at.desc(), QuizAttempt.attempt_no.desc())
        )
        attempts = list(result.scalars().all())
        return [
            {
                "student_id": str(attempt.student_id),
                "attempt_id": str(attempt.id),
                "attempt_no": attempt.attempt_no,
                "status": attempt.status,
                "score": float(attempt.score) if attempt.score is not None else None,
                "max_score": int(attempt.max_score or 0),
                "started_at": _dt_to_iso(attempt.started_at),
                "completed_at": _dt_to_iso(attempt.completed_at),
            }
            for attempt in attempts
        ]

    def _serialize_evaluatable(
        self,
        *,
        quiz: Quiz,
        due_at: datetime | None,
        total_points: int,
        status: str,
        assignment_id: uuid.UUID | None = None,
    ) -> dict:
        return {
            "id": str(quiz.id),
            "title": quiz.title,
            "type": "quiz",
            "due_at": _dt_to_iso(due_at),
            "status": status,
            "total_points": int(total_points or 0),
            "assignment_id": str(assignment_id) if assignment_id else None,
        }


def _dt_to_iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None
