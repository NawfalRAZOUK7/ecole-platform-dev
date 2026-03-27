"""Student progress visualization API endpoints — Phase 11D.

Reference: Phase 11D — Student Progress Visualization Backend
Endpoints:
  GET  /progress/student/{id}  — Full student dashboard (ABAC: own, child, class student, admin)
  GET  /progress/class/{id}    — Class summary (TCH, ADM, DIR)
  GET  /progress/me            — Current student's progress (STD shortcut)
  GET  /progress/children      — Parent's children overview (PAR)

Response format: chart-ready (labels + datasets arrays for recharts/fl_chart).
All responses are cached in Redis with 15-min TTL.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    AuthContext,
    get_parent_child_ids,
    get_teacher_class_ids,
    requires_permission,
    verify_parent_child_ownership,
    verify_school_boundary,
    verify_teacher_assignment,
)
from app.core.exceptions import NotFoundError, ValidationError
from app.core.response import success_response
from app.models.erp import Class, Enrollment
from app.models.iam import User
from app.services.progress import ProgressService

router = APIRouter(prefix="/progress", tags=["progress"])


# ---------------------------------------------------------------------------
# Helpers — ABAC checks
# ---------------------------------------------------------------------------
async def _verify_student_access(
    student_id: uuid.UUID,
    auth: AuthContext,
    db: AsyncSession,
) -> None:
    """ABAC: verify the caller can view this student's progress.

    - STD: can only view own
    - PAR: can only view linked children
    - TCH: can only view students in their assigned classes
    - ADM/DIR: any student in their school
    """
    if auth.role in ("ADM", "DIR"):
        # Verify student exists and is in the same school
        result = await db.execute(select(User.school_id).where(User.id == student_id))
        student_school_id = result.scalar_one_or_none()
        if student_school_id is None:
            raise NotFoundError("Student not found", error_code="ERR-PROGRESS-404")
        verify_school_boundary(student_school_id, auth)
        return

    if auth.role == "STD":
        if student_id != auth.user_id:
            raise NotFoundError("Student not found", error_code="ERR-PROGRESS-404")
        return

    if auth.role == "PAR":
        child_ids = await get_parent_child_ids(auth.user_id, auth.school_id, db)
        verify_parent_child_ownership(student_id, child_ids)
        return

    if auth.role == "TCH":
        teacher_class_ids = await get_teacher_class_ids(
            auth.user_id, auth.school_id, db
        )
        # Check if student is enrolled in any of the teacher's classes
        enroll_result = await db.execute(
            select(Enrollment.class_id).where(
                Enrollment.student_id == student_id,
                Enrollment.school_id == auth.school_id,
                Enrollment.status == "active",
                Enrollment.class_id.in_(teacher_class_ids),
            )
        )
        if enroll_result.scalar_one_or_none() is None:
            raise NotFoundError("Student not found", error_code="ERR-PROGRESS-404")
        return

    raise NotFoundError("Student not found", error_code="ERR-PROGRESS-404")


async def _verify_class_access(
    class_id: uuid.UUID,
    auth: AuthContext,
    db: AsyncSession,
) -> None:
    """ABAC: verify the caller can view this class's progress.

    - TCH: must be assigned to the class
    - ADM/DIR: any class in their school
    """
    result = await db.execute(select(Class.school_id).where(Class.id == class_id))
    class_school_id = result.scalar_one_or_none()
    if class_school_id is None:
        raise NotFoundError("Class not found", error_code="ERR-PROGRESS-404")
    verify_school_boundary(class_school_id, auth)

    if auth.role == "TCH":
        teacher_class_ids = await get_teacher_class_ids(
            auth.user_id, auth.school_id, db
        )
        verify_teacher_assignment(class_id, teacher_class_ids)


# ---------------------------------------------------------------------------
# GET /progress/student/{student_id} — Full student dashboard
# ---------------------------------------------------------------------------
@router.get(
    "/student/{student_id}",
    summary="Get student progress dashboard",
    response_description="Chart-ready student progress data",
)
async def get_student_progress(
    student_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission("PERM-LMS:progress:read")),
    db: AsyncSession = Depends(get_db),
):
    """Full student progress dashboard with grade trends, content completion,
    activity scores, attendance rates, and assessment results.

    ABAC enforced:
    - STD: own progress only
    - PAR: linked children only
    - TCH: students in assigned classes only
    - ADM/DIR: any student in school

    All data is cached in Redis (15-min TTL).
    Response format: chart-ready (labels + datasets arrays).
    """
    await _verify_student_access(student_id, auth, db)

    svc = ProgressService(db)
    data = await svc.get_student_progress(student_id, auth.school_id)

    return success_response(data)


# ---------------------------------------------------------------------------
# GET /progress/class/{class_id} — Class-wide summary
# ---------------------------------------------------------------------------
@router.get(
    "/class/{class_id}",
    summary="Get class progress summary",
    response_description="Chart-ready class progress data",
)
async def get_class_progress(
    class_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission("PERM-LMS:progress:class-read")),
    db: AsyncSession = Depends(get_db),
):
    """Class-wide progress summary for teachers and admins.

    Shows per-student metrics and class-level averages.
    ABAC: TCH (assigned classes), ADM/DIR (any class in school).

    Response format: chart-ready (labels + datasets arrays).
    """
    await _verify_class_access(class_id, auth, db)

    svc = ProgressService(db)
    data = await svc.get_class_progress(class_id, auth.school_id)

    return success_response(data)


# ---------------------------------------------------------------------------
# GET /progress/me — Student shortcut (own progress)
# ---------------------------------------------------------------------------
@router.get(
    "/me",
    summary="Get my progress (student shortcut)",
    response_description="Chart-ready progress data for current student",
)
async def get_my_progress(
    auth: AuthContext = Depends(requires_permission("PERM-LMS:progress:read")),
    db: AsyncSession = Depends(get_db),
):
    """Shortcut for students to view their own progress.

    Equivalent to GET /progress/student/{my_user_id}.
    Only available for STD role (other roles should use /student/{id}).
    """
    if auth.role != "STD":
        raise ValidationError(
            "This endpoint is for students only. Use /progress/student/{id} instead.",
            error_code="ERR-PROGRESS-422",
        )

    svc = ProgressService(db)
    data = await svc.get_student_progress(auth.user_id, auth.school_id)

    return success_response(data)


# ---------------------------------------------------------------------------
# GET /progress/children — Parent's children overview
# ---------------------------------------------------------------------------
@router.get(
    "/children",
    summary="Get children's progress overview (parent)",
    response_description="Chart-ready progress overview for all linked children",
)
async def get_children_progress(
    auth: AuthContext = Depends(requires_permission("PERM-LMS:progress:read")),
    db: AsyncSession = Depends(get_db),
):
    """Parent view: progress summary for all linked children.

    Shows key metrics per child with comparison charts.
    Only available for PAR role.
    """
    if auth.role != "PAR":
        raise ValidationError(
            "This endpoint is for parents only. Use /progress/student/{id} instead.",
            error_code="ERR-PROGRESS-422",
        )

    svc = ProgressService(db)
    data = await svc.get_children_progress(auth.user_id, auth.school_id)

    return success_response(data)
