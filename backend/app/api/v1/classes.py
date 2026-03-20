"""Class API endpoint: GET /classes/{class_id}.

Reference: S-045 — First ERP endpoint validating the full security pipeline.
Pipeline: AuthN -> RBAC (PERM-ERP:class:read) -> ABAC (school boundary + teacher assignment)
Roles: ADM (all classes in school), TCH (only assigned classes)
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
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
from app.core.response import success_response
from app.models.erp import Class, Enrollment, TeacherAssignment

router = APIRouter(prefix="/classes", tags=["erp-classes"])


@router.get("/{class_id}", summary="Get class details", response_description="Class with capacity, level, academic year")
async def get_class(
    class_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission("PERM-ERP:class:read")),
    db: AsyncSession = Depends(get_db),
):
    """Get class details by ID.

    Full security pipeline:
    1. AuthN — verified by get_current_user (via requires_permission)
    2. RBAC — requires PERM-ERP:class:read
    3. ABAC — school boundary (404 for other school's classes)
    4. ABAC — teacher assignment (TCH only sees assigned classes)
    """
    # 1. Load class
    result = await db.execute(select(Class).where(Class.id == class_id))
    cls = result.scalar_one_or_none()

    if cls is None:
        raise NotFoundError("Class not found", error_code="ERR-ERP-404")

    # 2. School boundary check (returns 404 if different school — masking)
    verify_school_boundary(cls.school_id, auth)

    # 3. Teacher assignment check (TCH can only see assigned classes)
    if auth.role == "TCH":
        teacher_classes = await get_teacher_class_ids(auth.user_id, auth.school_id, db)
        verify_teacher_assignment(class_id, teacher_classes)

    # 4. Count teachers and students for response
    teacher_count_result = await db.execute(
        select(func.count()).select_from(TeacherAssignment).where(
            TeacherAssignment.class_id == class_id,
            TeacherAssignment.school_id == auth.school_id,
        )
    )
    teacher_count = teacher_count_result.scalar() or 0

    student_count_result = await db.execute(
        select(func.count()).select_from(Enrollment).where(
            Enrollment.class_id == class_id,
            Enrollment.school_id == auth.school_id,
            Enrollment.status == "active",
        )
    )
    student_count = student_count_result.scalar() or 0

    return success_response(
        {
            "id": str(cls.id),
            "code": cls.code,
            "name": cls.name,
            "school_id": str(cls.school_id),
            "academic_year_id": str(cls.academic_year_id),
            "teacher_count": teacher_count,
            "student_count": student_count,
        }
    )
