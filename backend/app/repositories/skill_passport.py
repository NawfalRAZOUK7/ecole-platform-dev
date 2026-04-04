"""Repository helpers for life-skills passport workflows."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from app.models.erp import AcademicYear, Class, Enrollment
from app.models.iam import ParentChildLink, User
from app.models.lms import (
    Activity,
    ActivitySession,
    ContentProgress,
    Course,
    Quiz,
    QuizAttempt,
    Submission,
    Assignment,
)
from app.models.skill_passport import (
    SkillDimension,
    SkillMilestone,
    SkillPassport,
    SkillProgress,
)
from app.repositories.base import BaseRepository


class SkillPassportRepository(BaseRepository):
    """Data access for skill dimensions, milestones, progress, and passports."""

    async def get_user(self, user_id: uuid.UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_academic_year(self, academic_year_id: uuid.UUID) -> AcademicYear | None:
        result = await self.db.execute(
            select(AcademicYear).where(AcademicYear.id == academic_year_id)
        )
        return result.scalar_one_or_none()

    async def get_class(self, class_id: uuid.UUID) -> Class | None:
        result = await self.db.execute(select(Class).where(Class.id == class_id))
        return result.scalar_one_or_none()

    async def is_parent_of_student(
        self,
        *,
        parent_id: uuid.UUID,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> bool:
        result = await self.db.execute(
            select(ParentChildLink.id).where(
                ParentChildLink.parent_user_id == parent_id,
                ParentChildLink.child_user_id == student_id,
                ParentChildLink.school_id == school_id,
                ParentChildLink.status == "active",
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_dimension(self, dimension_id: uuid.UUID) -> SkillDimension | None:
        result = await self.db.execute(
            select(SkillDimension).where(SkillDimension.id == dimension_id)
        )
        return result.scalar_one_or_none()

    async def get_dimension_by_code(self, code: str) -> SkillDimension | None:
        result = await self.db.execute(
            select(SkillDimension).where(SkillDimension.code == code)
        )
        return result.scalar_one_or_none()

    async def list_dimensions(
        self,
        *,
        is_active: bool | None = None,
    ) -> list[SkillDimension]:
        query = select(SkillDimension)
        if is_active is not None:
            query = query.where(SkillDimension.is_active.is_(is_active))
        result = await self.db.execute(
            query.order_by(SkillDimension.display_order.asc(), SkillDimension.code.asc())
        )
        return list(result.scalars().all())

    async def create_dimension(self, dimension: SkillDimension) -> SkillDimension:
        self.db.add(dimension)
        await self.db.flush()
        return dimension

    async def save_dimension(self, dimension: SkillDimension) -> SkillDimension:
        self.db.add(dimension)
        await self.db.flush()
        return dimension

    async def delete_dimension(self, dimension: SkillDimension) -> None:
        await self.db.delete(dimension)
        await self.db.flush()

    async def get_milestone(
        self,
        milestone_id: uuid.UUID,
        *,
        include_dimension: bool = False,
    ) -> SkillMilestone | None:
        query = select(SkillMilestone).where(SkillMilestone.id == milestone_id)
        if include_dimension:
            query = query.options(selectinload(SkillMilestone.dimension))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_milestone_by_code(
        self,
        *,
        dimension_id: uuid.UUID,
        code: str,
    ) -> SkillMilestone | None:
        result = await self.db.execute(
            select(SkillMilestone).where(
                SkillMilestone.dimension_id == dimension_id,
                SkillMilestone.code == code,
            )
        )
        return result.scalar_one_or_none()

    async def list_milestones(
        self,
        *,
        dimension_id: uuid.UUID | None = None,
        is_active: bool | None = None,
        include_dimension: bool = False,
    ) -> list[SkillMilestone]:
        query = select(SkillMilestone)
        if dimension_id is not None:
            query = query.where(SkillMilestone.dimension_id == dimension_id)
        if is_active is not None:
            query = query.where(SkillMilestone.is_active.is_(is_active))
        if include_dimension:
            query = query.options(selectinload(SkillMilestone.dimension))
        result = await self.db.execute(
            query.order_by(SkillMilestone.level.asc(), SkillMilestone.code.asc())
        )
        return list(result.scalars().all())

    async def count_active_milestones(self) -> int:
        result = await self.db.execute(
            select(func.count(SkillMilestone.id)).where(SkillMilestone.is_active.is_(True))
        )
        return int(result.scalar_one() or 0)

    async def create_milestone(self, milestone: SkillMilestone) -> SkillMilestone:
        self.db.add(milestone)
        await self.db.flush()
        return milestone

    async def save_milestone(self, milestone: SkillMilestone) -> SkillMilestone:
        self.db.add(milestone)
        await self.db.flush()
        return milestone

    async def delete_milestone(self, milestone: SkillMilestone) -> None:
        await self.db.delete(milestone)
        await self.db.flush()

    async def get_progress_record(
        self,
        *,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
        milestone_id: uuid.UUID,
        academic_year_id: uuid.UUID,
    ) -> SkillProgress | None:
        result = await self.db.execute(
            select(SkillProgress).where(
                SkillProgress.student_id == student_id,
                SkillProgress.school_id == school_id,
                SkillProgress.milestone_id == milestone_id,
                SkillProgress.academic_year_id == academic_year_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_progress(
        self,
        *,
        school_id: uuid.UUID,
        academic_year_id: uuid.UUID,
        student_id: uuid.UUID | None = None,
        student_ids: set[uuid.UUID] | None = None,
        status: str | None = None,
        include_milestone: bool = False,
    ) -> list[SkillProgress]:
        query = select(SkillProgress).where(
            SkillProgress.school_id == school_id,
            SkillProgress.academic_year_id == academic_year_id,
        )
        if student_id is not None:
            query = query.where(SkillProgress.student_id == student_id)
        if student_ids is not None:
            if not student_ids:
                return []
            query = query.where(SkillProgress.student_id.in_(student_ids))
        if status:
            query = query.where(SkillProgress.status == status)
        if include_milestone:
            query = query.options(
                selectinload(SkillProgress.milestone).selectinload(
                    SkillMilestone.dimension
                )
            )
        result = await self.db.execute(
            query.order_by(SkillProgress.student_id.asc(), SkillProgress.created_at.asc())
        )
        return list(result.scalars().all())

    async def create_progress(self, progress: SkillProgress) -> SkillProgress:
        self.db.add(progress)
        await self.db.flush()
        return progress

    async def save_progress(self, progress: SkillProgress) -> SkillProgress:
        self.db.add(progress)
        await self.db.flush()
        return progress

    async def get_passport(
        self,
        *,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
        academic_year_id: uuid.UUID,
    ) -> SkillPassport | None:
        result = await self.db.execute(
            select(SkillPassport).where(
                SkillPassport.student_id == student_id,
                SkillPassport.school_id == school_id,
                SkillPassport.academic_year_id == academic_year_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_passport_by_id(
        self,
        passport_id: uuid.UUID,
        *,
        school_id: uuid.UUID,
    ) -> SkillPassport | None:
        result = await self.db.execute(
            select(SkillPassport).where(
                SkillPassport.id == passport_id,
                SkillPassport.school_id == school_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_passports(
        self,
        *,
        school_id: uuid.UUID,
        academic_year_id: uuid.UUID | None = None,
        student_ids: set[uuid.UUID] | None = None,
    ) -> list[SkillPassport]:
        query = select(SkillPassport).where(SkillPassport.school_id == school_id)
        if academic_year_id is not None:
            query = query.where(SkillPassport.academic_year_id == academic_year_id)
        if student_ids is not None:
            if not student_ids:
                return []
            query = query.where(SkillPassport.student_id.in_(student_ids))
        result = await self.db.execute(
            query.order_by(SkillPassport.generated_at.desc(), SkillPassport.id.asc())
        )
        return list(result.scalars().all())

    async def create_passport(self, passport: SkillPassport) -> SkillPassport:
        self.db.add(passport)
        await self.db.flush()
        return passport

    async def save_passport(self, passport: SkillPassport) -> SkillPassport:
        self.db.add(passport)
        await self.db.flush()
        return passport

    async def list_class_student_ids(
        self,
        *,
        class_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> list[uuid.UUID]:
        result = await self.db.execute(
            select(Enrollment.student_id).where(
                Enrollment.class_id == class_id,
                Enrollment.school_id == school_id,
                Enrollment.status == "active",
            )
        )
        return list(result.scalars().all())

    async def list_school_student_ids(
        self,
        *,
        school_id: uuid.UUID,
    ) -> list[uuid.UUID]:
        result = await self.db.execute(
            select(Enrollment.student_id)
            .where(
                Enrollment.school_id == school_id,
                Enrollment.status == "active",
            )
            .distinct()
        )
        return list(result.scalars().all())

    async def count_completed_activity_sessions(
        self,
        *,
        student_id: uuid.UUID,
        since: datetime,
    ) -> int:
        result = await self.db.execute(
            select(func.count(ActivitySession.id)).where(
                ActivitySession.student_id == student_id,
                ActivitySession.status == "completed",
                ActivitySession.created_at >= since,
            )
        )
        return int(result.scalar_one() or 0)

    async def count_completed_content_items(
        self,
        *,
        student_id: uuid.UUID,
        since: datetime,
    ) -> int:
        result = await self.db.execute(
            select(func.count(ContentProgress.id)).where(
                ContentProgress.student_id == student_id,
                ContentProgress.status == "completed",
                ContentProgress.created_at >= since,
            )
        )
        return int(result.scalar_one() or 0)

    async def count_submitted_assignments(
        self,
        *,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
        since: datetime,
        on_time_only: bool = False,
    ) -> int:
        query = (
            select(func.count(Submission.id))
            .join(Assignment, Assignment.id == Submission.assignment_id)
            .join(Course, Course.id == Assignment.course_id)
            .where(
                Submission.student_id == student_id,
                Course.school_id == school_id,
                Submission.submitted_at.is_not(None),
                Submission.submitted_at >= since,
            )
        )
        if on_time_only:
            query = query.where(
                or_(
                    Assignment.due_at.is_(None),
                    Submission.submitted_at <= Assignment.due_at,
                )
            )
        result = await self.db.execute(query)
        return int(result.scalar_one() or 0)

    async def count_quiz_attempts(
        self,
        *,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
        since: datetime,
    ) -> int:
        result = await self.db.execute(
            select(func.count(QuizAttempt.id))
            .join(Quiz, Quiz.id == QuizAttempt.quiz_id)
            .where(
                QuizAttempt.student_id == student_id,
                QuizAttempt.status == "COMPLETED",
                QuizAttempt.completed_at.is_not(None),
                QuizAttempt.completed_at >= since,
                or_(Quiz.school_id == school_id, Quiz.school_id.is_(None)),
            )
        )
        return int(result.scalar_one() or 0)

    async def average_quiz_score_percent(
        self,
        *,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
        since: datetime,
    ) -> float:
        result = await self.db.execute(
            select(
                func.coalesce(
                    func.avg(
                        (QuizAttempt.score * 100.0) / func.nullif(QuizAttempt.max_score, 0)
                    ),
                    0.0,
                )
            )
            .join(Quiz, Quiz.id == QuizAttempt.quiz_id)
            .where(
                QuizAttempt.student_id == student_id,
                QuizAttempt.status == "COMPLETED",
                QuizAttempt.completed_at.is_not(None),
                QuizAttempt.completed_at >= since,
                QuizAttempt.score.is_not(None),
                QuizAttempt.max_score > 0,
                or_(Quiz.school_id == school_id, Quiz.school_id.is_(None)),
            )
        )
        return float(result.scalar_one() or 0.0)

    async def count_activity_types_completed(
        self,
        *,
        student_id: uuid.UUID,
        since: datetime,
    ) -> int:
        result = await self.db.execute(
            select(func.count(func.distinct(Activity.type)))
            .select_from(ActivitySession)
            .join(Activity, Activity.id == ActivitySession.activity_id)
            .where(
                ActivitySession.student_id == student_id,
                ActivitySession.status == "completed",
                ActivitySession.created_at >= since,
            )
        )
        return int(result.scalar_one() or 0)
