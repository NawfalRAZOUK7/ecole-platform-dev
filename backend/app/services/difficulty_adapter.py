"""Rule-based difficulty adaptation based on student quiz performance."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.lms import Quiz, QuizAttempt, QuizAttemptStatus


class DifficultyAdapter:
    """Recommends the next quiz difficulty level using rule-based logic.

    Promotes after 2 consecutive high scores (>=80%), demotes after 2
    consecutive low scores (<=40%), otherwise stays at current level.
    """

    PROMOTE_THRESHOLD = 0.80
    DEMOTE_THRESHOLD = 0.40
    WINDOW = 3
    DIFFICULTY_ORDER = ["EASY", "MEDIUM", "HARD"]

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_recommended_difficulty(
        self,
        student_id: uuid.UUID,
        subject: str,
    ) -> str:
        """Return recommended difficulty for a student + subject."""
        attempts = await self._get_recent_attempts(student_id, subject)
        if len(attempts) < 2:
            return "EASY"

        last_two_ratios = [
            float(a.score or 0) / float(a.max_score) if a.max_score else 0.0
            for a in attempts[:2]
        ]
        current_difficulty = (attempts[0].quiz.difficulty or "MEDIUM").upper()
        current_idx = self._difficulty_idx(current_difficulty)

        if all(s >= self.PROMOTE_THRESHOLD for s in last_two_ratios):
            new_idx = min(current_idx + 1, len(self.DIFFICULTY_ORDER) - 1)
            reason = "promoted_high_scores"
        elif all(s <= self.DEMOTE_THRESHOLD for s in last_two_ratios):
            new_idx = max(current_idx - 1, 0)
            reason = "demoted_low_scores"
        else:
            new_idx = current_idx
            reason = "stable"

        recommended = self.DIFFICULTY_ORDER[new_idx]
        if recommended != current_difficulty:
            await self._log_adaptation(
                student_id=student_id,
                subject=subject,
                previous=current_difficulty,
                new=recommended,
                reason=reason,
            )

        return recommended

    async def _get_recent_attempts(
        self,
        student_id: uuid.UUID,
        subject: str,
    ) -> list[QuizAttempt]:
        stmt = (
            select(QuizAttempt)
            .join(QuizAttempt.quiz)
            .where(
                QuizAttempt.student_id == student_id,
                QuizAttempt.status == QuizAttemptStatus.GRADED.value,
                Quiz.subject == subject,
                QuizAttempt.max_score > 0,
            )
            .options(selectinload(QuizAttempt.quiz))
            .order_by(QuizAttempt.completed_at.desc())
            .limit(self.WINDOW)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    def _difficulty_idx(self, difficulty: str) -> int:
        try:
            return self.DIFFICULTY_ORDER.index(difficulty.upper())
        except ValueError:
            return 1  # default to MEDIUM index

    async def _log_adaptation(
        self,
        student_id: uuid.UUID,
        subject: str,
        previous: str,
        new: str,
        reason: str,
    ) -> None:
        from app.models.difficulty_adaptation import DifficultyAdaptation

        record = DifficultyAdaptation(
            student_id=student_id,
            subject=subject,
            previous_difficulty=previous,
            new_difficulty=new,
            reason=reason,
        )
        self.db.add(record)
        # flush without commit — callers own the transaction
        await self.db.flush()
