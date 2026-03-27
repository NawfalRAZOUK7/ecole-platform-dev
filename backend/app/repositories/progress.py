"""Repository helpers for student and class progress analytics."""

from __future__ import annotations

import uuid

from sqlalchemy import case, func, select

from app.models.erp import AttendanceRecord, AttendanceSession, Class, Enrollment
from app.models.iam import ParentChildLink, User
from app.models.lms import (
    ActivitySession,
    Assessment,
    AssessmentResult,
    Assignment,
    ContentProgress,
    Course,
    Grade,
    Submission,
)
from app.repositories.base import BaseRepository


class ProgressRepository(BaseRepository):
    """Data access for progress dashboards."""

    async def get_student_school_id(
        self,
        student_id: uuid.UUID,
    ) -> uuid.UUID | None:
        result = await self.db.execute(
            select(User.school_id).where(User.id == student_id)
        )
        return result.scalar_one_or_none()

    async def list_parent_child_ids(
        self,
        *,
        parent_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> set[uuid.UUID]:
        result = await self.db.execute(
            select(ParentChildLink.child_user_id).where(
                ParentChildLink.parent_user_id == parent_id,
                ParentChildLink.school_id == school_id,
                ParentChildLink.status == "active",
            )
        )
        return set(result.scalars().all())

    async def list_teacher_class_ids(
        self,
        *,
        teacher_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> set[uuid.UUID]:
        from app.models.erp import TeacherAssignment

        result = await self.db.execute(
            select(TeacherAssignment.class_id).where(
                TeacherAssignment.teacher_id == teacher_id,
                TeacherAssignment.school_id == school_id,
            )
        )
        return set(result.scalars().all())

    async def student_is_enrolled_in_classes(
        self,
        *,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
        class_ids: set[uuid.UUID],
    ) -> bool:
        if not class_ids:
            return False
        result = await self.db.execute(
            select(Enrollment.class_id).where(
                Enrollment.student_id == student_id,
                Enrollment.school_id == school_id,
                Enrollment.status == "active",
                Enrollment.class_id.in_(class_ids),
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_class_school_id(
        self,
        class_id: uuid.UUID,
    ) -> uuid.UUID | None:
        result = await self.db.execute(
            select(Class.school_id).where(Class.id == class_id)
        )
        return result.scalar_one_or_none()

    async def get_student_name(
        self,
        student_id: uuid.UUID,
    ) -> str | None:
        result = await self.db.execute(
            select(User.full_name).where(User.id == student_id)
        )
        return result.scalar_one_or_none()

    async def list_grade_trend_rows(
        self,
        *,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> list[dict]:
        result = await self.db.execute(
            select(
                func.to_char(Grade.published_at, "YYYY-MM").label("month"),
                func.avg(Grade.score).label("avg_score"),
                func.count(Grade.id).label("count"),
            )
            .join(Submission, Grade.submission_id == Submission.id)
            .join(Assignment, Submission.assignment_id == Assignment.id)
            .join(Course, Assignment.course_id == Course.id)
            .where(
                Submission.student_id == student_id,
                Course.school_id == school_id,
                Grade.published_at.isnot(None),
            )
            .group_by("month")
            .order_by("month")
            .limit(12)
        )
        return [
            {
                "month": row.month,
                "avg_score": float(row.avg_score or 0),
                "count": int(row.count or 0),
            }
            for row in result
        ]

    async def get_content_completion_counts(
        self,
        *,
        student_id: uuid.UUID,
    ) -> dict[str, int]:
        result = await self.db.execute(
            select(ContentProgress.status, func.count(ContentProgress.id).label("cnt"))
            .where(ContentProgress.student_id == student_id)
            .group_by(ContentProgress.status)
        )
        counts = {"completed": 0, "in_progress": 0, "not_started": 0}
        for row in result:
            if row.status in counts:
                counts[row.status] = int(row.cnt or 0)
        return counts

    async def list_activity_score_rows(
        self,
        *,
        student_id: uuid.UUID,
    ) -> list[dict]:
        result = await self.db.execute(
            select(
                func.to_char(ActivitySession.created_at, "YYYY-MM").label("month"),
                func.avg(ActivitySession.score).label("avg_score"),
                func.count(ActivitySession.id).label("sessions"),
            )
            .where(
                ActivitySession.student_id == student_id,
                ActivitySession.status == "completed",
                ActivitySession.score.isnot(None),
            )
            .group_by("month")
            .order_by("month")
            .limit(12)
        )
        return [
            {
                "month": row.month,
                "avg_score": float(row.avg_score or 0),
                "sessions": int(row.sessions or 0),
            }
            for row in result
        ]

    async def get_attendance_overview_counts(
        self,
        *,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> dict[str, int]:
        result = await self.db.execute(
            select(AttendanceRecord.status, func.count(AttendanceRecord.id).label("cnt"))
            .where(
                AttendanceRecord.student_id == student_id,
                AttendanceRecord.school_id == school_id,
            )
            .group_by(AttendanceRecord.status)
        )
        counts = {"present": 0, "absent": 0, "excused": 0, "late": 0}
        for row in result:
            if row.status in counts:
                counts[row.status] = int(row.cnt or 0)
        return counts

    async def list_attendance_monthly_rows(
        self,
        *,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> list[dict]:
        result = await self.db.execute(
            select(
                func.to_char(AttendanceSession.session_date, "YYYY-MM").label("month"),
                func.count(AttendanceRecord.id).label("total_records"),
                func.count(
                    case(
                        (AttendanceRecord.status == "present", AttendanceRecord.id),
                        else_=None,
                    )
                ).label("present_count"),
            )
            .join(
                AttendanceSession,
                AttendanceRecord.attendance_session_id == AttendanceSession.id,
            )
            .where(
                AttendanceRecord.student_id == student_id,
                AttendanceRecord.school_id == school_id,
            )
            .group_by("month")
            .order_by("month")
            .limit(12)
        )
        return [
            {
                "month": row.month,
                "total_records": int(row.total_records or 0),
                "present_count": int(row.present_count or 0),
            }
            for row in result
        ]

    async def list_assessment_result_rows(
        self,
        *,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> list[dict]:
        result = await self.db.execute(
            select(
                Assessment.title,
                AssessmentResult.score,
                Assessment.total_points,
            )
            .join(Assessment, AssessmentResult.assessment_id == Assessment.id)
            .join(Class, Assessment.class_id == Class.id)
            .where(
                AssessmentResult.student_id == student_id,
                Class.school_id == school_id,
                AssessmentResult.score.isnot(None),
            )
            .order_by(Assessment.created_at.desc())
            .limit(20)
        )
        return [
            {
                "title": row.title,
                "score": float(row.score or 0),
                "total_points": int(row.total_points or 0),
            }
            for row in result
        ]

    async def get_class_info(
        self,
        *,
        class_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> tuple[str, str] | None:
        result = await self.db.execute(
            select(Class.name, Class.code).where(
                Class.id == class_id,
                Class.school_id == school_id,
            )
        )
        row = result.one_or_none()
        if row is None:
            return None
        return row.name, row.code

    async def list_class_students(
        self,
        *,
        class_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> list[tuple[uuid.UUID, str]]:
        result = await self.db.execute(
            select(Enrollment.student_id, User.full_name)
            .join(User, Enrollment.student_id == User.id)
            .where(
                Enrollment.class_id == class_id,
                Enrollment.school_id == school_id,
                Enrollment.status == "active",
            )
        )
        return [(row.student_id, row.full_name) for row in result]

    async def get_grade_averages_for_students(
        self,
        *,
        student_ids: list[uuid.UUID],
        school_id: uuid.UUID,
    ) -> dict[uuid.UUID, float]:
        if not student_ids:
            return {}
        result = await self.db.execute(
            select(
                Submission.student_id,
                func.avg(Grade.score).label("avg_score"),
            )
            .join(Submission, Grade.submission_id == Submission.id)
            .join(Assignment, Submission.assignment_id == Assignment.id)
            .join(Course, Assignment.course_id == Course.id)
            .where(
                Submission.student_id.in_(student_ids),
                Course.school_id == school_id,
                Grade.published_at.isnot(None),
            )
            .group_by(Submission.student_id)
        )
        return {
            row.student_id: float(row.avg_score or 0)
            for row in result
        }

    async def get_attendance_rates_for_students(
        self,
        *,
        student_ids: list[uuid.UUID],
        school_id: uuid.UUID,
    ) -> dict[uuid.UUID, float]:
        if not student_ids:
            return {}
        result = await self.db.execute(
            select(
                AttendanceRecord.student_id,
                func.count(AttendanceRecord.id).label("total"),
                func.count(
                    case(
                        (AttendanceRecord.status == "present", AttendanceRecord.id),
                        else_=None,
                    )
                ).label("present"),
            )
            .where(
                AttendanceRecord.student_id.in_(student_ids),
                AttendanceRecord.school_id == school_id,
            )
            .group_by(AttendanceRecord.student_id)
        )
        return {
            row.student_id: round(((row.present or 0) / row.total) * 100, 1)
            if row.total
            else 0.0
            for row in result
        }

    async def get_content_completion_rates_for_students(
        self,
        *,
        student_ids: list[uuid.UUID],
    ) -> dict[uuid.UUID, float]:
        if not student_ids:
            return {}
        result = await self.db.execute(
            select(
                ContentProgress.student_id,
                func.count(ContentProgress.id).label("total"),
                func.count(
                    case(
                        (ContentProgress.status == "completed", ContentProgress.id),
                        else_=None,
                    )
                ).label("completed"),
            )
            .where(ContentProgress.student_id.in_(student_ids))
            .group_by(ContentProgress.student_id)
        )
        return {
            row.student_id: round(((row.completed or 0) / row.total) * 100, 1)
            if row.total
            else 0.0
            for row in result
        }

    async def list_children(
        self,
        *,
        parent_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> list[tuple[uuid.UUID, str]]:
        result = await self.db.execute(
            select(ParentChildLink.child_user_id, User.full_name)
            .join(User, ParentChildLink.child_user_id == User.id)
            .where(
                ParentChildLink.parent_user_id == parent_id,
                ParentChildLink.school_id == school_id,
                ParentChildLink.status == "active",
            )
        )
        return [(row.child_user_id, row.full_name) for row in result]

    async def get_student_grade_average(
        self,
        *,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> float | None:
        result = await self.db.execute(
            select(func.avg(Grade.score).label("avg_score"))
            .join(Submission, Grade.submission_id == Submission.id)
            .join(Assignment, Submission.assignment_id == Assignment.id)
            .join(Course, Assignment.course_id == Course.id)
            .where(
                Submission.student_id == student_id,
                Course.school_id == school_id,
                Grade.published_at.isnot(None),
            )
        )
        value = result.scalar_one_or_none()
        return float(value) if value is not None else None

    async def get_student_attendance_rate(
        self,
        *,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> float | None:
        result = await self.db.execute(
            select(
                func.count(AttendanceRecord.id).label("total"),
                func.count(
                    case(
                        (AttendanceRecord.status == "present", AttendanceRecord.id),
                        else_=None,
                    )
                ).label("present"),
            ).where(
                AttendanceRecord.student_id == student_id,
                AttendanceRecord.school_id == school_id,
            )
        )
        row = result.one()
        if not row.total:
            return None
        return round(((row.present or 0) / row.total) * 100, 1)

    async def get_student_content_completion_rate(
        self,
        *,
        student_id: uuid.UUID,
    ) -> float | None:
        result = await self.db.execute(
            select(
                func.count(ContentProgress.id).label("total"),
                func.count(
                    case(
                        (ContentProgress.status == "completed", ContentProgress.id),
                        else_=None,
                    )
                ).label("completed"),
            ).where(ContentProgress.student_id == student_id)
        )
        row = result.one()
        if not row.total:
            return None
        return round(((row.completed or 0) / row.total) * 100, 1)

    async def get_latest_grade(
        self,
        *,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> dict | None:
        result = await self.db.execute(
            select(Grade.score, Assignment.title)
            .join(Submission, Grade.submission_id == Submission.id)
            .join(Assignment, Submission.assignment_id == Assignment.id)
            .join(Course, Assignment.course_id == Course.id)
            .where(
                Submission.student_id == student_id,
                Course.school_id == school_id,
                Grade.published_at.isnot(None),
            )
            .order_by(Grade.published_at.desc())
            .limit(1)
        )
        row = result.one_or_none()
        if row is None:
            return None
        return {"score": float(row.score or 0), "assignment": row.title}
