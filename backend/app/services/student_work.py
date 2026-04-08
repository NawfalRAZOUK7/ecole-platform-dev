"""Unified student work service for assignments, quizzes, and assessments."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.lms import AssignmentRepository, AssessmentRepository
from app.repositories.quiz import QuizRepository


class StudentWorkService:
    """Provides a unified view across all evaluatable LMS work types."""

    def __init__(self, db: AsyncSession) -> None:
        self._assignment_repo = AssignmentRepository(db)
        self._quiz_repo = QuizRepository(db)
        self._assessment_repo = AssessmentRepository(db)

    async def list_all_for_student(
        self,
        school_id: uuid.UUID,
        student_id: uuid.UUID,
    ) -> list[dict]:
        """Return all student work assigned to one student."""
        assignments = await self._assignment_repo.list_for_student(
            school_id, student_id
        )
        quizzes = await self._quiz_repo.list_for_student(school_id, student_id)
        assessments = await self._assessment_repo.list_for_student(
            school_id, student_id
        )
        return self._build_unified_items(
            assignments=assignments,
            quizzes=quizzes,
            assessments=assessments,
        )

    async def list_all_for_class(
        self,
        school_id: uuid.UUID,
        class_id: uuid.UUID,
    ) -> list[dict]:
        """Return all student work configured for one class."""
        assignments = await self._assignment_repo.list_for_class(school_id, class_id)
        quizzes = await self._quiz_repo.list_for_class(school_id, class_id)
        assessments = await self._assessment_repo.list_for_class(school_id, class_id)
        return self._build_unified_items(
            assignments=assignments,
            quizzes=quizzes,
            assessments=assessments,
        )

    def _build_unified_items(
        self,
        *,
        assignments: list[dict],
        quizzes: list[dict],
        assessments: list[dict],
    ) -> list[dict]:
        items: list[dict] = []

        for item in assignments:
            items.append(self._serialize_item(item=item, grading_type="manual"))
        for item in quizzes:
            items.append(self._serialize_item(item=item, grading_type="auto"))
        for item in assessments:
            items.append(self._serialize_item(item=item, grading_type="manual"))

        items.sort(
            key=lambda item: (
                item.get("due_at") is not None,
                item.get("due_at") or "",
                item.get("id") or "",
            ),
            reverse=True,
        )
        return items

    def _serialize_item(
        self,
        *,
        item: dict,
        grading_type: str,
    ) -> dict:
        return {
            "id": item["id"],
            "type": item["type"],
            "title": item["title"],
            "due_at": item.get("due_at"),
            "status": item.get("status"),
            "total_points": int(item.get("total_points") or 0),
            "grading_type": grading_type,
        }
