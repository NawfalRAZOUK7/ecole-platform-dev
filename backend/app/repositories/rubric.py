"""Repository helpers for rubric CRUD and rubric-based grading."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import delete, or_, select
from sqlalchemy.orm import selectinload

from app.models.lms import (
    Assignment,
    Course,
    Rubric,
    RubricCriterion,
    RubricLevel,
    RubricScore,
    Submission,
)
from app.repositories.base import BaseRepository


class RubricRepository(BaseRepository):
    """Data access helpers for rubric engine workflows."""

    async def get_rubric(
        self,
        rubric_id: uuid.UUID,
    ) -> Rubric | None:
        result = await self.db.execute(
            select(Rubric)
            .options(
                selectinload(Rubric.criteria).selectinload(RubricCriterion.levels),
            )
            .where(Rubric.id == rubric_id)
        )
        return result.scalar_one_or_none()

    async def create_rubric(self, **kwargs: Any) -> Rubric:
        rubric = Rubric(**kwargs)
        self.db.add(rubric)
        await self.db.flush()
        return rubric

    async def list_rubrics(
        self,
        *,
        school_id: uuid.UUID,
        teacher_id: uuid.UUID | None,
    ) -> list[Rubric]:
        query = (
            select(Rubric)
            .options(
                selectinload(Rubric.criteria).selectinload(RubricCriterion.levels),
            )
            .where(Rubric.school_id == school_id)
        )
        if teacher_id is not None:
            query = query.where(
                or_(Rubric.teacher_id == teacher_id, Rubric.is_template.is_(True))
            )
        query = query.order_by(Rubric.is_template.desc(), Rubric.title.asc(), Rubric.id.asc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_criterion(self, **kwargs: Any) -> RubricCriterion:
        criterion = RubricCriterion(**kwargs)
        self.db.add(criterion)
        await self.db.flush()
        return criterion

    async def create_level(self, **kwargs: Any) -> RubricLevel:
        level = RubricLevel(**kwargs)
        self.db.add(level)
        await self.db.flush()
        return level

    async def create_rubric_score(self, **kwargs: Any) -> RubricScore:
        rubric_score = RubricScore(**kwargs)
        self.db.add(rubric_score)
        await self.db.flush()
        return rubric_score

    async def list_rubric_scores(
        self,
        submission_id: uuid.UUID,
    ) -> list[RubricScore]:
        result = await self.db.execute(
            select(RubricScore)
            .options(
                selectinload(RubricScore.criterion),
                selectinload(RubricScore.level),
            )
            .join(RubricCriterion, RubricCriterion.id == RubricScore.criterion_id)
            .where(RubricScore.submission_id == submission_id)
            .order_by(RubricCriterion.position.asc(), RubricScore.id.asc())
        )
        return list(result.scalars().all())

    async def delete_rubric_scores_for_submission(
        self,
        submission_id: uuid.UUID,
    ) -> None:
        await self.db.execute(
            delete(RubricScore).where(RubricScore.submission_id == submission_id)
        )
        await self.db.flush()

    async def get_submission_with_rubric_context(
        self,
        submission_id: uuid.UUID,
    ) -> tuple[Submission, Assignment, Course, Rubric | None] | None:
        result = await self.db.execute(
            select(Submission, Assignment, Course, Rubric)
            .join(Assignment, Assignment.id == Submission.assignment_id)
            .join(Course, Course.id == Assignment.course_id)
            .outerjoin(Rubric, Rubric.id == Assignment.rubric_id)
            .where(Submission.id == submission_id)
        )
        row = result.one_or_none()
        if row is None:
            return None
        submission, assignment, course, rubric = row
        return submission, assignment, course, rubric
