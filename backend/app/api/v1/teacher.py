"""Teacher API endpoints — classes, students, submissions for the teacher dashboard.

Reference: Phase 4B — Teacher Dashboard backend endpoints
All endpoints require TCH role (PERM-ERP:class:read or PERM-LMS:submission:grade).
School boundary + teacher assignment (ABAC) enforced on all queries.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    AuthContext,
    get_teacher_class_ids,
    requires_permission,
    verify_school_boundary,
    verify_teacher_assignment,
)
from app.core.exceptions import NotFoundError
from app.core.response import list_response, success_response
from app.models.erp import Class, Enrollment, Period, TeacherAssignment
from app.models.iam import User
from app.models.lms import Assignment, Course, Grade, Submission

router = APIRouter(prefix="/teacher", tags=["teacher"])

TEACHER_CLASS_PERM = "PERM-ERP:class:read"
TEACHER_GRADE_PERM = "PERM-LMS:submission:grade"


# ---------------------------------------------------------------------------
# GET /teacher/classes — List teacher's assigned classes
# ---------------------------------------------------------------------------
@router.get("/classes", summary="List teacher's assigned classes")
async def list_teacher_classes(
    auth: AuthContext = Depends(requires_permission(TEACHER_CLASS_PERM)),
    db: AsyncSession = Depends(get_db),
):
    """List classes assigned to the authenticated teacher with student and course counts."""
    teacher_class_ids = await get_teacher_class_ids(auth.user_id, auth.school_id, db)

    if not teacher_class_ids:
        return success_response([])

    # Get classes
    classes_result = await db.execute(
        select(Class).where(
            Class.id.in_(teacher_class_ids),
            Class.school_id == auth.school_id,
        ).order_by(Class.name)
    )
    classes = list(classes_result.scalars().all())

    # Student counts per class (active enrollments)
    student_counts_result = await db.execute(
        select(Enrollment.class_id, func.count()).where(
            Enrollment.class_id.in_(teacher_class_ids),
            Enrollment.school_id == auth.school_id,
            Enrollment.status == "active",
        ).group_by(Enrollment.class_id)
    )
    student_counts = dict(student_counts_result.all())

    # Course counts per class
    course_counts_result = await db.execute(
        select(Course.class_id, func.count()).where(
            Course.class_id.in_(teacher_class_ids),
            Course.teacher_id == auth.user_id,
            Course.school_id == auth.school_id,
        ).group_by(Course.class_id)
    )
    course_counts = dict(course_counts_result.all())

    data = [
        {
            "id": str(c.id),
            "code": c.code,
            "name": c.name,
            "academic_year_id": str(c.academic_year_id),
            "student_count": student_counts.get(c.id, 0),
            "course_count": course_counts.get(c.id, 0),
        }
        for c in classes
    ]

    return success_response(data)


# ---------------------------------------------------------------------------
# GET /teacher/classes/{class_id}/students — List students in a class
# ---------------------------------------------------------------------------
@router.get("/classes/{class_id}/students", summary="List students in a class")
async def list_class_students(
    class_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(TEACHER_CLASS_PERM)),
    db: AsyncSession = Depends(get_db),
):
    """List enrolled students in a class. Teacher must be assigned to the class."""
    # Validate class exists + school boundary
    class_result = await db.execute(select(Class).where(Class.id == class_id))
    cls = class_result.scalar_one_or_none()
    if cls is None:
        raise NotFoundError("Class not found", error_code="ERR-ERP-404")
    verify_school_boundary(cls.school_id, auth)

    # ABAC: Teacher must be assigned
    teacher_classes = await get_teacher_class_ids(auth.user_id, auth.school_id, db)
    verify_teacher_assignment(class_id, teacher_classes)

    # Get active enrollments with user info
    enrollments_result = await db.execute(
        select(Enrollment, User).join(User, Enrollment.student_id == User.id).where(
            Enrollment.class_id == class_id,
            Enrollment.school_id == auth.school_id,
            Enrollment.status == "active",
        ).order_by(User.full_name)
    )
    rows = enrollments_result.all()

    data = [
        {
            "id": str(enrollment.student_id),
            "full_name": user.full_name,
            "email": user.email,
            "enrollment_status": enrollment.status,
        }
        for enrollment, user in rows
    ]

    return success_response(data)


# ---------------------------------------------------------------------------
# GET /teacher/submissions — List submissions for teacher's assignments
# ---------------------------------------------------------------------------
@router.get("/submissions", summary="List submissions for grading")
async def list_teacher_submissions(
    auth: AuthContext = Depends(requires_permission(TEACHER_GRADE_PERM)),
    db: AsyncSession = Depends(get_db),
    assignment_id: uuid.UUID | None = Query(None),
    course_id: uuid.UUID | None = Query(None),
    status: str | None = Query(None, description="Filter: submitted, graded, draft"),
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    """List submissions for the teacher's courses/assignments.

    Filters: assignment_id, course_id, status.
    Only returns submissions for courses owned by the teacher.
    """
    # Base query: submissions for teacher's courses
    query = (
        select(Submission, Assignment, User)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .join(Course, Assignment.course_id == Course.id)
        .join(User, Submission.student_id == User.id)
        .where(
            Course.teacher_id == auth.user_id,
            Course.school_id == auth.school_id,
        )
    )

    if assignment_id:
        query = query.where(Submission.assignment_id == assignment_id)
    if course_id:
        query = query.where(Assignment.course_id == course_id)
    if status:
        query = query.where(Submission.status == status)

    query = query.order_by(Submission.created_at.desc())

    # Cursor pagination
    if cursor:
        from datetime import datetime
        try:
            cursor_dt = datetime.fromisoformat(cursor)
            query = query.where(Submission.created_at < cursor_dt)
        except ValueError:
            pass

    query = query.limit(limit + 1)
    result = await db.execute(query)
    rows = list(result.all())

    has_more = len(rows) > limit
    if has_more:
        rows = rows[:limit]

    # Get grades for these submissions
    submission_ids = [sub.id for sub, _, _ in rows]
    grades_map: dict[uuid.UUID, Grade] = {}
    if submission_ids:
        grades_result = await db.execute(
            select(Grade).where(Grade.submission_id.in_(submission_ids))
        )
        for g in grades_result.scalars().all():
            grades_map[g.submission_id] = g

    data = [
        {
            "id": str(sub.id),
            "assignment_id": str(sub.assignment_id),
            "assignment_title": assignment.title,
            "assignment_total_points": assignment.total_points,
            "student_id": str(sub.student_id),
            "student_name": student.full_name,
            "status": sub.status,
            "submitted_at": sub.submitted_at.isoformat() if sub.submitted_at else None,
            "grade": {
                "score": float(grades_map[sub.id].score),
                "feedback_text": grades_map[sub.id].feedback_text,
                "published_at": grades_map[sub.id].published_at.isoformat() if grades_map[sub.id].published_at else None,
            } if sub.id in grades_map else None,
        }
        for sub, assignment, student in rows
    ]

    next_cursor = rows[-1][0].created_at.isoformat() if has_more and rows else None
    return list_response(data, next_cursor=next_cursor, has_more=has_more)


# ---------------------------------------------------------------------------
# GET /teacher/periods — List active periods (for attendance form)
# ---------------------------------------------------------------------------
@router.get("/periods", summary="List active periods")
async def list_active_periods(
    auth: AuthContext = Depends(requires_permission(TEACHER_CLASS_PERM)),
    db: AsyncSession = Depends(get_db),
):
    """List active periods for the teacher's school (used in attendance form)."""
    result = await db.execute(
        select(Period).where(
            Period.school_id == auth.school_id,
            Period.status == "active",
        ).order_by(Period.date_start)
    )
    periods = list(result.scalars().all())

    data = [
        {
            "id": str(p.id),
            "label": p.label,
            "date_start": str(p.date_start),
            "date_end": str(p.date_end),
        }
        for p in periods
    ]

    return success_response(data)
