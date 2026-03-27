"""Student progress aggregation service — Phase 11D.

Reference: Phase 11D — Student Progress Visualization Backend
Aggregates data from grades, content progress, activity sessions, and attendance
into chart-ready structures (labels + datasets arrays for recharts/fl_chart).

Redis caching with 15-min TTL on all aggregated results.

Usage:
    from app.services.progress import ProgressService
    svc = ProgressService(db)
    data = await svc.get_student_progress(student_id, school_id)
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import redis_client
from app.models.erp import (
    AttendanceRecord,
    AttendanceSession,
    Class,
    Enrollment,
)
from app.models.iam import ParentChildLink, User
from app.models.lms import (
    ActivitySession,
    Assignment,
    AssessmentResult,
    ContentProgress,
    Course,
    Grade,
    Submission,
)

logger = logging.getLogger(__name__)

CACHE_TTL = 900  # 15 minutes


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------
def _cache_key(prefix: str, *parts: Any) -> str:
    """Build a deterministic Redis cache key."""
    raw = ":".join(str(p) for p in parts)
    return f"progress:{prefix}:{raw}"


async def _get_cached(key: str) -> dict | None:
    """Read from Redis cache. Returns None on miss or error."""
    try:
        data = await redis_client.get(key)
        if data:
            return json.loads(data)
    except Exception:
        logger.debug("Cache miss/error for %s", key)
    return None


async def _set_cached(key: str, data: dict, ttl: int = CACHE_TTL) -> None:
    """Write to Redis cache. Fire-and-forget, never raises."""
    try:
        await redis_client.set(key, json.dumps(data, default=str), ex=ttl)
    except Exception:
        logger.debug("Cache write error for %s", key)


# ---------------------------------------------------------------------------
# Progress Service
# ---------------------------------------------------------------------------
class ProgressService:
    """Aggregates student progress data for visualization endpoints."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # -------------------------------------------------------------------
    # Grade trends — monthly average score
    # -------------------------------------------------------------------
    async def get_grade_trends(
        self,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Monthly average grade for the student (last 12 months).

        Returns chart-ready: { labels: ["Jan 2026", ...], datasets: [{ label, data }] }
        """
        cache_key = _cache_key("grades", student_id, school_id)
        cached = await _get_cached(cache_key)
        if cached:
            return cached

        # Join: Grade → Submission → Assignment → Course (school scoped)
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
        rows = result.all()

        labels = []
        scores = []
        counts = []
        for row in rows:
            labels.append(row.month)
            scores.append(round(float(row.avg_score), 2))
            counts.append(row.count)

        data = {
            "labels": labels,
            "datasets": [
                {"label": "Moyenne des notes", "data": scores},
                {"label": "Nombre de notes", "data": counts},
            ],
        }
        await _set_cached(cache_key, data)
        return data

    # -------------------------------------------------------------------
    # Content completion — done vs total
    # -------------------------------------------------------------------
    async def get_content_completion(
        self,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Content items: completed / in_progress / not_started.

        Returns chart-ready for a donut/pie chart.
        """
        cache_key = _cache_key("content", student_id, school_id)
        cached = await _get_cached(cache_key)
        if cached:
            return cached

        result = await self.db.execute(
            select(
                ContentProgress.status,
                func.count(ContentProgress.id).label("cnt"),
            )
            .where(ContentProgress.student_id == student_id)
            .group_by(ContentProgress.status)
        )
        rows = result.all()

        status_counts = {"completed": 0, "in_progress": 0, "not_started": 0}
        for row in rows:
            if row.status in status_counts:
                status_counts[row.status] = row.cnt

        total = sum(status_counts.values())

        data = {
            "labels": ["Terminé", "En cours", "Non commencé"],
            "datasets": [
                {
                    "label": "Contenu",
                    "data": [
                        status_counts["completed"],
                        status_counts["in_progress"],
                        status_counts["not_started"],
                    ],
                }
            ],
            "summary": {
                "total": total,
                "completed": status_counts["completed"],
                "completion_rate": round(
                    (status_counts["completed"] / total * 100) if total > 0 else 0, 1
                ),
            },
        }
        await _set_cached(cache_key, data)
        return data

    # -------------------------------------------------------------------
    # Activity scores over time
    # -------------------------------------------------------------------
    async def get_activity_scores(
        self,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Activity session scores over time (completed sessions).

        Returns chart-ready line chart data.
        """
        cache_key = _cache_key("activities", student_id, school_id)
        cached = await _get_cached(cache_key)
        if cached:
            return cached

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
        rows = result.all()

        labels = []
        scores = []
        session_counts = []
        for row in rows:
            labels.append(row.month)
            scores.append(round(float(row.avg_score), 2))
            session_counts.append(row.sessions)

        data = {
            "labels": labels,
            "datasets": [
                {"label": "Score moyen", "data": scores},
                {"label": "Sessions complétées", "data": session_counts},
            ],
        }
        await _set_cached(cache_key, data)
        return data

    # -------------------------------------------------------------------
    # Attendance rates — present/absent/excused/late percentages
    # -------------------------------------------------------------------
    async def get_attendance_rates(
        self,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Attendance breakdown: present, absent, excused, late.

        Returns chart-ready data (donut + monthly trend).
        """
        cache_key = _cache_key("attendance", student_id, school_id)
        cached = await _get_cached(cache_key)
        if cached:
            return cached

        # Overall breakdown
        overall_result = await self.db.execute(
            select(
                AttendanceRecord.status,
                func.count(AttendanceRecord.id).label("cnt"),
            )
            .where(
                AttendanceRecord.student_id == student_id,
                AttendanceRecord.school_id == school_id,
            )
            .group_by(AttendanceRecord.status)
        )
        overall_rows = overall_result.all()

        status_map = {"present": 0, "absent": 0, "excused": 0, "late": 0}
        for row in overall_rows:
            if row.status in status_map:
                status_map[row.status] = row.cnt

        total = sum(status_map.values())

        # Monthly trend
        monthly_result = await self.db.execute(
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
        monthly_rows = monthly_result.all()

        month_labels = []
        presence_rates = []
        for row in monthly_rows:
            month_labels.append(row.month)
            rate = round(
                (row.present_count / row.total_records * 100)
                if row.total_records > 0
                else 0,
                1,
            )
            presence_rates.append(rate)

        data = {
            "overview": {
                "labels": ["Présent", "Absent", "Excusé", "En retard"],
                "datasets": [
                    {
                        "label": "Présence",
                        "data": [
                            status_map["present"],
                            status_map["absent"],
                            status_map["excused"],
                            status_map["late"],
                        ],
                    }
                ],
                "summary": {
                    "total": total,
                    "present": status_map["present"],
                    "attendance_rate": round(
                        (status_map["present"] / total * 100) if total > 0 else 0, 1
                    ),
                },
            },
            "trend": {
                "labels": month_labels,
                "datasets": [
                    {
                        "label": "Taux de présence (%)",
                        "data": presence_rates,
                    }
                ],
            },
        }
        await _set_cached(cache_key, data)
        return data

    # -------------------------------------------------------------------
    # Assessment results
    # -------------------------------------------------------------------
    async def get_assessment_results(
        self,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Assessment results for the student.

        Returns chart-ready bar chart data.
        """
        cache_key = _cache_key("assessments", student_id, school_id)
        cached = await _get_cached(cache_key)
        if cached:
            return cached

        from app.models.lms import Assessment

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
        rows = result.all()

        labels = []
        scores = []
        max_scores = []
        for row in rows:
            labels.append(row.title[:30])
            scores.append(float(row.score))
            max_scores.append(row.total_points)

        # Reverse to chronological order
        labels.reverse()
        scores.reverse()
        max_scores.reverse()

        data = {
            "labels": labels,
            "datasets": [
                {"label": "Score obtenu", "data": scores},
                {"label": "Score maximum", "data": max_scores},
            ],
        }
        await _set_cached(cache_key, data)
        return data

    # -------------------------------------------------------------------
    # Full student progress (combines all above)
    # -------------------------------------------------------------------
    async def get_student_progress(
        self,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Full student progress dashboard — aggregates all dimensions."""
        cache_key = _cache_key("student_full", student_id, school_id)
        cached = await _get_cached(cache_key)
        if cached:
            return cached

        # Get student name
        user_result = await self.db.execute(
            select(User.full_name).where(User.id == student_id)
        )
        student_name = user_result.scalar_one_or_none() or "Élève"

        grades = await self.get_grade_trends(student_id, school_id)
        content = await self.get_content_completion(student_id, school_id)
        activities = await self.get_activity_scores(student_id, school_id)
        attendance = await self.get_attendance_rates(student_id, school_id)
        assessments = await self.get_assessment_results(student_id, school_id)

        data = {
            "student_id": str(student_id),
            "student_name": student_name,
            "grade_trends": grades,
            "content_completion": content,
            "activity_scores": activities,
            "attendance": attendance,
            "assessment_results": assessments,
        }
        await _set_cached(cache_key, data)
        return data

    # -------------------------------------------------------------------
    # Class-wide summary (for teachers/admins)
    # -------------------------------------------------------------------
    async def get_class_progress(
        self,
        class_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Class-wide progress summary for teacher/admin view.

        Aggregates averages across all enrolled students.
        """
        cache_key = _cache_key("class", class_id, school_id)
        cached = await _get_cached(cache_key)
        if cached:
            return cached

        # Get class info
        class_result = await self.db.execute(
            select(Class.name, Class.code).where(
                Class.id == class_id,
                Class.school_id == school_id,
            )
        )
        class_row = class_result.one_or_none()
        class_name = f"{class_row.name} ({class_row.code})" if class_row else "Classe"

        # Get enrolled students
        enroll_result = await self.db.execute(
            select(Enrollment.student_id, User.full_name)
            .join(User, Enrollment.student_id == User.id)
            .where(
                Enrollment.class_id == class_id,
                Enrollment.school_id == school_id,
                Enrollment.status == "active",
            )
        )
        students = enroll_result.all()
        student_ids = [s.student_id for s in students]

        if not student_ids:
            data = {
                "class_id": str(class_id),
                "class_name": class_name,
                "student_count": 0,
                "students": [],
                "class_averages": {
                    "grade_average": None,
                    "attendance_rate": None,
                    "content_completion_rate": None,
                },
            }
            await _set_cached(cache_key, data)
            return data

        # --- Class-wide grade average ---
        grade_result = await self.db.execute(
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
        grade_rows = {
            row.student_id: float(row.avg_score) for row in grade_result.all()
        }

        # --- Class-wide attendance ---
        att_result = await self.db.execute(
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
        att_rows = {
            row.student_id: round(row.present / row.total * 100, 1)
            if row.total > 0
            else 0
            for row in att_result.all()
        }

        # --- Class-wide content completion ---
        content_result = await self.db.execute(
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
        content_rows = {
            row.student_id: round(row.completed / row.total * 100, 1)
            if row.total > 0
            else 0
            for row in content_result.all()
        }

        # Build per-student summary
        student_summaries = []
        all_grades = []
        all_attendance = []
        all_content = []

        for s in students:
            sid = s.student_id
            grade_avg = grade_rows.get(sid)
            att_rate = att_rows.get(sid)
            cont_rate = content_rows.get(sid)

            student_summaries.append(
                {
                    "student_id": str(sid),
                    "student_name": s.full_name,
                    "grade_average": round(grade_avg, 2)
                    if grade_avg is not None
                    else None,
                    "attendance_rate": att_rate,
                    "content_completion_rate": cont_rate,
                }
            )

            if grade_avg is not None:
                all_grades.append(grade_avg)
            if att_rate is not None:
                all_attendance.append(att_rate)
            if cont_rate is not None:
                all_content.append(cont_rate)

        # Sort by name
        student_summaries.sort(key=lambda x: x["student_name"])

        # Class-level averages
        class_grade_avg = (
            round(sum(all_grades) / len(all_grades), 2) if all_grades else None
        )
        class_att_avg = (
            round(sum(all_attendance) / len(all_attendance), 1)
            if all_attendance
            else None
        )
        class_content_avg = (
            round(sum(all_content) / len(all_content), 1) if all_content else None
        )

        # Chart-ready: student names as labels, metrics as datasets
        data = {
            "class_id": str(class_id),
            "class_name": class_name,
            "student_count": len(student_ids),
            "students": student_summaries,
            "class_averages": {
                "grade_average": class_grade_avg,
                "attendance_rate": class_att_avg,
                "content_completion_rate": class_content_avg,
            },
            "charts": {
                "grade_comparison": {
                    "labels": [s["student_name"] for s in student_summaries],
                    "datasets": [
                        {
                            "label": "Moyenne des notes",
                            "data": [s["grade_average"] for s in student_summaries],
                        }
                    ],
                },
                "attendance_comparison": {
                    "labels": [s["student_name"] for s in student_summaries],
                    "datasets": [
                        {
                            "label": "Taux de présence (%)",
                            "data": [s["attendance_rate"] for s in student_summaries],
                        }
                    ],
                },
            },
        }
        await _set_cached(cache_key, data)
        return data

    # -------------------------------------------------------------------
    # Parent multi-child overview
    # -------------------------------------------------------------------
    async def get_children_progress(
        self,
        parent_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Parent view: summary for all linked children.

        Returns a compact overview per child with key metrics.
        """
        cache_key = _cache_key("children", parent_id, school_id)
        cached = await _get_cached(cache_key)
        if cached:
            return cached

        # Get linked children
        link_result = await self.db.execute(
            select(ParentChildLink.child_user_id, User.full_name)
            .join(User, ParentChildLink.child_user_id == User.id)
            .where(
                ParentChildLink.parent_user_id == parent_id,
                ParentChildLink.school_id == school_id,
                ParentChildLink.status == "active",
            )
        )
        children = link_result.all()

        if not children:
            data = {"children": [], "child_count": 0}
            await _set_cached(cache_key, data)
            return data

        children_data = []
        for child in children:
            child_id = child.child_user_id
            child_name = child.full_name

            # Grade average
            grade_result = await self.db.execute(
                select(func.avg(Grade.score).label("avg_score"))
                .join(Submission, Grade.submission_id == Submission.id)
                .join(Assignment, Submission.assignment_id == Assignment.id)
                .join(Course, Assignment.course_id == Course.id)
                .where(
                    Submission.student_id == child_id,
                    Course.school_id == school_id,
                    Grade.published_at.isnot(None),
                )
            )
            grade_avg = grade_result.scalar_one_or_none()

            # Attendance rate
            att_result = await self.db.execute(
                select(
                    func.count(AttendanceRecord.id).label("total"),
                    func.count(
                        case(
                            (AttendanceRecord.status == "present", AttendanceRecord.id),
                            else_=None,
                        )
                    ).label("present"),
                ).where(
                    AttendanceRecord.student_id == child_id,
                    AttendanceRecord.school_id == school_id,
                )
            )
            att_row = att_result.one()
            att_rate = (
                round(att_row.present / att_row.total * 100, 1)
                if att_row.total > 0
                else None
            )

            # Content completion
            cont_result = await self.db.execute(
                select(
                    func.count(ContentProgress.id).label("total"),
                    func.count(
                        case(
                            (ContentProgress.status == "completed", ContentProgress.id),
                            else_=None,
                        )
                    ).label("completed"),
                ).where(ContentProgress.student_id == child_id)
            )
            cont_row = cont_result.one()
            cont_rate = (
                round(cont_row.completed / cont_row.total * 100, 1)
                if cont_row.total > 0
                else None
            )

            # Latest grade (most recent)
            latest_grade_result = await self.db.execute(
                select(Grade.score, Assignment.title)
                .join(Submission, Grade.submission_id == Submission.id)
                .join(Assignment, Submission.assignment_id == Assignment.id)
                .join(Course, Assignment.course_id == Course.id)
                .where(
                    Submission.student_id == child_id,
                    Course.school_id == school_id,
                    Grade.published_at.isnot(None),
                )
                .order_by(Grade.published_at.desc())
                .limit(1)
            )
            latest = latest_grade_result.one_or_none()

            children_data.append(
                {
                    "student_id": str(child_id),
                    "student_name": child_name,
                    "grade_average": round(float(grade_avg), 2) if grade_avg else None,
                    "attendance_rate": att_rate,
                    "content_completion_rate": cont_rate,
                    "latest_grade": {
                        "score": float(latest.score),
                        "assignment": latest.title,
                    }
                    if latest
                    else None,
                }
            )

        # Chart-ready: children comparison
        data = {
            "child_count": len(children_data),
            "children": children_data,
            "charts": {
                "comparison": {
                    "labels": [c["student_name"] for c in children_data],
                    "datasets": [
                        {
                            "label": "Moyenne des notes",
                            "data": [c["grade_average"] for c in children_data],
                        },
                        {
                            "label": "Taux de présence (%)",
                            "data": [c["attendance_rate"] for c in children_data],
                        },
                        {
                            "label": "Contenu terminé (%)",
                            "data": [
                                c["content_completion_rate"] for c in children_data
                            ],
                        },
                    ],
                },
            },
        }
        await _set_cached(cache_key, data)
        return data
