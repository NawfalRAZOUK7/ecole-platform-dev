"""Repository helpers for weighted gradebook workflows."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Float, cast, delete, func, or_, select

from app.models.erp import Class, Enrollment, Period
from app.models.iam import User
from app.models.lms import (
    Assignment,
    Course,
    Grade,
    GradeCategory,
    StudentPeriodAverage,
    Submission,
)
from app.repositories.base import BaseRepository


class GradebookRepository(BaseRepository):
    """Data access helpers for gradebook categories and averages."""

    async def get_grade_category(
        self,
        category_id: uuid.UUID,
    ) -> GradeCategory | None:
        result = await self.db.execute(
            select(GradeCategory).where(GradeCategory.id == category_id)
        )
        return result.scalar_one_or_none()

    async def list_grade_categories(
        self,
        *,
        class_id: uuid.UUID,
        period_id: uuid.UUID,
    ) -> list[GradeCategory]:
        result = await self.db.execute(
            select(GradeCategory)
            .where(
                GradeCategory.class_id == class_id,
                GradeCategory.period_id == period_id,
            )
            .order_by(GradeCategory.position.asc(), GradeCategory.name.asc())
        )
        return list(result.scalars().all())

    async def create_grade_category(self, **kwargs: Any) -> GradeCategory:
        category = GradeCategory(**kwargs)
        self.db.add(category)
        await self.db.flush()
        return category

    async def delete_grade_categories_for_scope(
        self,
        *,
        class_id: uuid.UUID,
        period_id: uuid.UUID,
    ) -> None:
        await self.db.execute(
            delete(GradeCategory).where(
                GradeCategory.class_id == class_id,
                GradeCategory.period_id == period_id,
            )
        )
        await self.db.flush()

    async def get_student_grades_by_category(
        self,
        *,
        student_id: uuid.UUID,
        class_id: uuid.UUID,
        period_id: uuid.UUID,
    ) -> list[tuple[GradeCategory, float | None]]:
        result = await self.db.execute(
            select(
                GradeCategory,
                func.avg(cast(Grade.score, Float)).label("category_average"),
            )
            .outerjoin(Assignment, Assignment.grade_category_id == GradeCategory.id)
            .outerjoin(Course, Course.id == Assignment.course_id)
            .outerjoin(
                Submission,
                (Submission.assignment_id == Assignment.id)
                & (Submission.student_id == student_id),
            )
            .outerjoin(
                Grade,
                (Grade.submission_id == Submission.id)
                & (Grade.published_at.is_not(None)),
            )
            .where(
                GradeCategory.class_id == class_id,
                GradeCategory.period_id == period_id,
                or_(Assignment.id.is_(None), Course.class_id == class_id),
            )
            .group_by(GradeCategory.id)
            .order_by(GradeCategory.position.asc(), GradeCategory.name.asc())
        )
        return [
            (category, category_average) for category, category_average in result.all()
        ]

    async def delete_student_period_averages_for_scope(
        self,
        *,
        class_id: uuid.UUID,
        period_id: uuid.UUID,
    ) -> None:
        await self.db.execute(
            delete(StudentPeriodAverage).where(
                StudentPeriodAverage.class_id == class_id,
                StudentPeriodAverage.period_id == period_id,
            )
        )
        await self.db.flush()

    async def save_student_period_average(
        self,
        *,
        student_id: uuid.UUID,
        class_id: uuid.UUID,
        period_id: uuid.UUID,
        school_id: uuid.UUID,
        weighted_average: float,
        mention: str,
        class_rank: int | None,
        total_students: int | None,
        computed_at: datetime,
    ) -> StudentPeriodAverage:
        result = await self.db.execute(
            select(StudentPeriodAverage).where(
                StudentPeriodAverage.student_id == student_id,
                StudentPeriodAverage.class_id == class_id,
                StudentPeriodAverage.period_id == period_id,
            )
        )
        average = result.scalar_one_or_none()
        if average is None:
            average = StudentPeriodAverage(
                student_id=student_id,
                class_id=class_id,
                period_id=period_id,
                school_id=school_id,
                weighted_average=weighted_average,
                mention=mention,
                class_rank=class_rank,
                total_students=total_students,
                computed_at=computed_at,
            )
            self.db.add(average)
        else:
            average.school_id = school_id
            average.weighted_average = weighted_average
            average.mention = mention
            average.class_rank = class_rank
            average.total_students = total_students
            average.computed_at = computed_at
            self.db.add(average)

        await self.db.flush()
        return average

    async def get_class_averages(
        self,
        *,
        class_id: uuid.UUID,
        period_id: uuid.UUID,
    ) -> list[tuple[StudentPeriodAverage, User]]:
        result = await self.db.execute(
            select(StudentPeriodAverage, User)
            .join(User, User.id == StudentPeriodAverage.student_id)
            .where(
                StudentPeriodAverage.class_id == class_id,
                StudentPeriodAverage.period_id == period_id,
            )
            .order_by(
                StudentPeriodAverage.class_rank.asc().nulls_last(),
                StudentPeriodAverage.weighted_average.desc(),
                User.full_name.asc(),
            )
        )
        return list(result.all())

    async def get_student_transcript(
        self,
        *,
        student_id: uuid.UUID,
        academic_year_id: uuid.UUID,
    ) -> list[tuple[StudentPeriodAverage, Period, Class]]:
        result = await self.db.execute(
            select(StudentPeriodAverage, Period, Class)
            .join(Period, Period.id == StudentPeriodAverage.period_id)
            .join(Class, Class.id == StudentPeriodAverage.class_id)
            .where(
                StudentPeriodAverage.student_id == student_id,
                Class.academic_year_id == academic_year_id,
            )
            .order_by(Period.date_start.asc(), Class.name.asc())
        )
        return list(result.all())

    async def list_class_period_students(
        self,
        *,
        class_id: uuid.UUID,
        period_id: uuid.UUID,
    ) -> list[tuple[uuid.UUID, str]]:
        result = await self.db.execute(
            select(User.id, User.full_name)
            .join(Enrollment, Enrollment.student_id == User.id)
            .where(
                Enrollment.class_id == class_id,
                Enrollment.period_id == period_id,
                Enrollment.status == "active",
            )
            .order_by(User.full_name.asc(), User.id.asc())
        )
        return [(student_id, full_name) for student_id, full_name in result.all()]

    async def list_gradebook_assignments(
        self,
        *,
        class_id: uuid.UUID,
        period_id: uuid.UUID,
    ) -> list[tuple[Assignment, GradeCategory]]:
        result = await self.db.execute(
            select(Assignment, GradeCategory)
            .join(Course, Course.id == Assignment.course_id)
            .join(GradeCategory, GradeCategory.id == Assignment.grade_category_id)
            .where(
                Course.class_id == class_id,
                GradeCategory.period_id == period_id,
                GradeCategory.class_id == class_id,
            )
            .order_by(
                GradeCategory.position.asc(),
                Assignment.due_at.asc().nulls_last(),
                Assignment.title.asc(),
                Assignment.id.asc(),
            )
        )
        return list(result.all())

    async def list_gradebook_grade_entries(
        self,
        *,
        class_id: uuid.UUID,
        period_id: uuid.UUID,
    ) -> list[tuple[uuid.UUID, uuid.UUID, uuid.UUID | None, float, datetime | None]]:
        result = await self.db.execute(
            select(
                Submission.student_id,
                Assignment.id,
                Assignment.grade_category_id,
                cast(Grade.score, Float).label("score"),
                Grade.published_at,
            )
            .join(Submission, Submission.assignment_id == Assignment.id)
            .join(Grade, Grade.submission_id == Submission.id)
            .join(Course, Course.id == Assignment.course_id)
            .join(GradeCategory, GradeCategory.id == Assignment.grade_category_id)
            .where(
                Course.class_id == class_id,
                GradeCategory.class_id == class_id,
                GradeCategory.period_id == period_id,
                Grade.published_at.is_not(None),
            )
        )
        return [
            (student_id, assignment_id, category_id, score, published_at)
            for student_id, assignment_id, category_id, score, published_at in result.all()
        ]

    async def list_student_period_enrollments(
        self,
        *,
        student_id: uuid.UUID,
        academic_year_id: uuid.UUID,
    ) -> list[tuple[Enrollment, Class, Period]]:
        result = await self.db.execute(
            select(Enrollment, Class, Period)
            .join(Class, Class.id == Enrollment.class_id)
            .join(Period, Period.id == Enrollment.period_id)
            .where(
                Enrollment.student_id == student_id,
                Enrollment.status == "active",
                Class.academic_year_id == academic_year_id,
            )
            .order_by(Period.date_start.asc(), Class.name.asc())
        )
        return list(result.all())
