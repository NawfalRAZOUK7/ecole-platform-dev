"""Student progress aggregation service."""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    AuthContext,
    verify_parent_child_ownership,
    verify_school_boundary,
    verify_teacher_assignment,
)
from app.core.exceptions import NotFoundError, ValidationError
from app.core.permissions import ADM, DIR, PAR, STD, TCH
from app.core.redis import redis_client
from app.repositories.progress import ProgressRepository

logger = logging.getLogger(__name__)

CACHE_TTL = 900


def _cache_key(prefix: str, *parts: Any) -> str:
    raw = ":".join(str(part) for part in parts)
    return f"progress:{prefix}:{raw}"


async def _get_cached(key: str) -> dict | None:
    try:
        data = await redis_client.get(key)
        if data:
            return json.loads(data)
    except Exception:
        logger.debug("Cache miss/error for %s", key)
    return None


async def _set_cached(key: str, data: dict, ttl: int = CACHE_TTL) -> None:
    try:
        await redis_client.set(key, json.dumps(data, default=str), ex=ttl)
    except Exception:
        logger.debug("Cache write error for %s", key)


class ProgressService:
    """Aggregates student and class progress for chart-ready endpoints."""

    def __init__(self, db: AsyncSession) -> None:
        self.repo = ProgressRepository(db)

    async def verify_student_access(
        self,
        *,
        student_id: uuid.UUID,
        auth: AuthContext,
    ) -> None:
        if auth.role in (ADM, DIR):
            student_school_id = await self.repo.get_student_school_id(student_id)
            if student_school_id is None:
                raise NotFoundError("Student not found", error_code="ERR-PROGRESS-404")
            verify_school_boundary(student_school_id, auth)
            return

        if auth.role == STD:
            if student_id != auth.user_id:
                raise NotFoundError("Student not found", error_code="ERR-PROGRESS-404")
            return

        if auth.role == PAR:
            child_ids = await self.repo.list_parent_child_ids(
                parent_id=auth.user_id,
                school_id=auth.school_id,
            )
            verify_parent_child_ownership(student_id, child_ids)
            return

        if auth.role == TCH:
            teacher_class_ids = await self.repo.list_teacher_class_ids(
                teacher_id=auth.user_id,
                school_id=auth.school_id,
            )
            enrolled = await self.repo.student_is_enrolled_in_classes(
                student_id=student_id,
                school_id=auth.school_id,
                class_ids=teacher_class_ids,
            )
            if not enrolled:
                raise NotFoundError("Student not found", error_code="ERR-PROGRESS-404")
            return

        raise NotFoundError("Student not found", error_code="ERR-PROGRESS-404")

    async def verify_class_access(
        self,
        *,
        class_id: uuid.UUID,
        auth: AuthContext,
    ) -> None:
        class_school_id = await self.repo.get_class_school_id(class_id)
        if class_school_id is None:
            raise NotFoundError("Class not found", error_code="ERR-PROGRESS-404")
        verify_school_boundary(class_school_id, auth)

        if auth.role == TCH:
            teacher_class_ids = await self.repo.list_teacher_class_ids(
                teacher_id=auth.user_id,
                school_id=auth.school_id,
            )
            verify_teacher_assignment(class_id, teacher_class_ids)

    async def get_grade_trends(
        self,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> dict[str, Any]:
        cache_key = _cache_key("grades", student_id, school_id)
        cached = await _get_cached(cache_key)
        if cached:
            return cached

        rows = await self.repo.list_grade_trend_rows(
            student_id=student_id,
            school_id=school_id,
        )
        data = {
            "labels": [row["month"] for row in rows],
            "datasets": [
                {
                    "label": "Moyenne des notes",
                    "data": [round(row["avg_score"], 2) for row in rows],
                },
                {
                    "label": "Nombre de notes",
                    "data": [row["count"] for row in rows],
                },
            ],
        }
        await _set_cached(cache_key, data)
        return data

    async def get_content_completion(
        self,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> dict[str, Any]:
        cache_key = _cache_key("content", student_id, school_id)
        cached = await _get_cached(cache_key)
        if cached:
            return cached

        status_counts = await self.repo.get_content_completion_counts(student_id=student_id)
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
                    (status_counts["completed"] / total * 100) if total > 0 else 0,
                    1,
                ),
            },
        }
        await _set_cached(cache_key, data)
        return data

    async def get_activity_scores(
        self,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> dict[str, Any]:
        cache_key = _cache_key("activities", student_id, school_id)
        cached = await _get_cached(cache_key)
        if cached:
            return cached

        rows = await self.repo.list_activity_score_rows(student_id=student_id)
        data = {
            "labels": [row["month"] for row in rows],
            "datasets": [
                {
                    "label": "Score moyen",
                    "data": [round(row["avg_score"], 2) for row in rows],
                },
                {
                    "label": "Sessions complétées",
                    "data": [row["sessions"] for row in rows],
                },
            ],
        }
        await _set_cached(cache_key, data)
        return data

    async def get_attendance_rates(
        self,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> dict[str, Any]:
        cache_key = _cache_key("attendance", student_id, school_id)
        cached = await _get_cached(cache_key)
        if cached:
            return cached

        status_map = await self.repo.get_attendance_overview_counts(
            student_id=student_id,
            school_id=school_id,
        )
        total = sum(status_map.values())

        monthly_rows = await self.repo.list_attendance_monthly_rows(
            student_id=student_id,
            school_id=school_id,
        )
        trend_labels = []
        presence_rates = []
        for row in monthly_rows:
            trend_labels.append(row["month"])
            rate = round(
                (row["present_count"] / row["total_records"] * 100)
                if row["total_records"] > 0
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
                        (status_map["present"] / total * 100) if total > 0 else 0,
                        1,
                    ),
                },
            },
            "trend": {
                "labels": trend_labels,
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

    async def get_assessment_results(
        self,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> dict[str, Any]:
        cache_key = _cache_key("assessments", student_id, school_id)
        cached = await _get_cached(cache_key)
        if cached:
            return cached

        rows = await self.repo.list_assessment_result_rows(
            student_id=student_id,
            school_id=school_id,
        )
        labels = [row["title"][:30] for row in rows]
        scores = [row["score"] for row in rows]
        max_scores = [row["total_points"] for row in rows]
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

    async def get_student_progress(
        self,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> dict[str, Any]:
        cache_key = _cache_key("student_full", student_id, school_id)
        cached = await _get_cached(cache_key)
        if cached:
            return cached

        student_name = await self.repo.get_student_name(student_id) or "Élève"
        data = {
            "student_id": str(student_id),
            "student_name": student_name,
            "grade_trends": await self.get_grade_trends(student_id, school_id),
            "content_completion": await self.get_content_completion(student_id, school_id),
            "activity_scores": await self.get_activity_scores(student_id, school_id),
            "attendance": await self.get_attendance_rates(student_id, school_id),
            "assessment_results": await self.get_assessment_results(student_id, school_id),
        }
        await _set_cached(cache_key, data)
        return data

    async def get_class_progress(
        self,
        class_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> dict[str, Any]:
        cache_key = _cache_key("class", class_id, school_id)
        cached = await _get_cached(cache_key)
        if cached:
            return cached

        class_info = await self.repo.get_class_info(class_id=class_id, school_id=school_id)
        class_name = f"{class_info[0]} ({class_info[1]})" if class_info else "Classe"

        students = await self.repo.list_class_students(class_id=class_id, school_id=school_id)
        student_ids = [student_id for student_id, _ in students]
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

        grade_rows = await self.repo.get_grade_averages_for_students(
            student_ids=student_ids,
            school_id=school_id,
        )
        attendance_rows = await self.repo.get_attendance_rates_for_students(
            student_ids=student_ids,
            school_id=school_id,
        )
        content_rows = await self.repo.get_content_completion_rates_for_students(
            student_ids=student_ids,
        )

        student_summaries = []
        all_grades: list[float] = []
        all_attendance: list[float] = []
        all_content: list[float] = []

        for student_id, full_name in students:
            grade_avg = grade_rows.get(student_id)
            attendance_rate = attendance_rows.get(student_id)
            content_rate = content_rows.get(student_id)
            student_summaries.append(
                {
                    "student_id": str(student_id),
                    "student_name": full_name,
                    "grade_average": round(grade_avg, 2)
                    if grade_avg is not None
                    else None,
                    "attendance_rate": attendance_rate,
                    "content_completion_rate": content_rate,
                }
            )
            if grade_avg is not None:
                all_grades.append(grade_avg)
            if attendance_rate is not None:
                all_attendance.append(attendance_rate)
            if content_rate is not None:
                all_content.append(content_rate)

        student_summaries.sort(key=lambda item: item["student_name"])
        class_grade_avg = round(sum(all_grades) / len(all_grades), 2) if all_grades else None
        class_att_avg = (
            round(sum(all_attendance) / len(all_attendance), 1) if all_attendance else None
        )
        class_content_avg = (
            round(sum(all_content) / len(all_content), 1) if all_content else None
        )

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
                    "labels": [student["student_name"] for student in student_summaries],
                    "datasets": [
                        {
                            "label": "Moyenne des notes",
                            "data": [student["grade_average"] for student in student_summaries],
                        }
                    ],
                },
                "attendance_comparison": {
                    "labels": [student["student_name"] for student in student_summaries],
                    "datasets": [
                        {
                            "label": "Taux de présence (%)",
                            "data": [student["attendance_rate"] for student in student_summaries],
                        }
                    ],
                },
            },
        }
        await _set_cached(cache_key, data)
        return data

    async def get_children_progress(
        self,
        parent_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> dict[str, Any]:
        cache_key = _cache_key("children", parent_id, school_id)
        cached = await _get_cached(cache_key)
        if cached:
            return cached

        children = await self.repo.list_children(parent_id=parent_id, school_id=school_id)
        if not children:
            data = {"children": [], "child_count": 0}
            await _set_cached(cache_key, data)
            return data

        children_data = []
        for child_id, child_name in children:
            grade_average = await self.repo.get_student_grade_average(
                student_id=child_id,
                school_id=school_id,
            )
            attendance_rate = await self.repo.get_student_attendance_rate(
                student_id=child_id,
                school_id=school_id,
            )
            content_completion_rate = await self.repo.get_student_content_completion_rate(
                student_id=child_id,
            )
            latest_grade = await self.repo.get_latest_grade(
                student_id=child_id,
                school_id=school_id,
            )
            children_data.append(
                {
                    "student_id": str(child_id),
                    "student_name": child_name,
                    "grade_average": round(grade_average, 2)
                    if grade_average is not None
                    else None,
                    "attendance_rate": attendance_rate,
                    "content_completion_rate": content_completion_rate,
                    "latest_grade": latest_grade,
                }
            )

        data = {
            "child_count": len(children_data),
            "children": children_data,
            "charts": {
                "comparison": {
                    "labels": [child["student_name"] for child in children_data],
                    "datasets": [
                        {
                            "label": "Moyenne des notes",
                            "data": [child["grade_average"] for child in children_data],
                        },
                        {
                            "label": "Taux de présence (%)",
                            "data": [child["attendance_rate"] for child in children_data],
                        },
                        {
                            "label": "Contenu terminé (%)",
                            "data": [
                                child["content_completion_rate"]
                                for child in children_data
                            ],
                        },
                    ],
                },
            },
        }
        await _set_cached(cache_key, data)
        return data

    async def get_student_progress_for_user(
        self,
        *,
        student_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict[str, Any]:
        await self.verify_student_access(student_id=student_id, auth=auth)
        return await self.get_student_progress(student_id, auth.school_id)

    async def get_class_progress_for_user(
        self,
        *,
        class_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict[str, Any]:
        await self.verify_class_access(class_id=class_id, auth=auth)
        return await self.get_class_progress(class_id, auth.school_id)

    async def get_my_progress(
        self,
        *,
        auth: AuthContext,
    ) -> dict[str, Any]:
        if auth.role != STD:
            raise ValidationError(
                "This endpoint is for students only. Use /progress/student/{id} instead.",
                error_code="ERR-PROGRESS-422",
            )
        return await self.get_student_progress(auth.user_id, auth.school_id)

    async def get_children_progress_for_parent(
        self,
        *,
        auth: AuthContext,
    ) -> dict[str, Any]:
        if auth.role != PAR:
            raise ValidationError(
                "This endpoint is for parents only. Use /progress/student/{id} instead.",
                error_code="ERR-PROGRESS-422",
            )
        return await self.get_children_progress(auth.user_id, auth.school_id)
