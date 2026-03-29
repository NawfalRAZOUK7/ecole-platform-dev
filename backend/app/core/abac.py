"""Attribute-based access control helpers for owner and relationship scoping."""

from __future__ import annotations

import uuid

from sqlalchemy import Select, exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import AuthContext


def apply_owner_scope(
    query: Select,
    *,
    auth: AuthContext,
    owner_field: str = "user_id",
    teacher_field: str | None = "teacher_id",
    parent_field: str | None = "parent_id",
    student_field: str | None = "student_id",
    admin_roles: tuple[str, ...] = ("ADM", "DIR", "SUP"),
) -> Select:
    """Apply a common owner-scope filter for the authenticated actor."""
    if auth.role in admin_roles:
        return query

    if auth.role == "TCH" and teacher_field:
        return query.filter_by(**{teacher_field: auth.user_id})
    if auth.role == "PAR" and parent_field:
        return query.filter_by(**{parent_field: auth.user_id})
    if auth.role == "STD" and student_field:
        return query.filter_by(**{student_field: auth.user_id})

    return query.filter_by(**{owner_field: auth.user_id})


async def validate_parent_child_access(
    db: AsyncSession,
    *,
    parent_id: uuid.UUID,
    student_id: uuid.UUID,
) -> bool:
    """Verify that a parent has an active link to a student.

    The architecture examples reference legacy `verified=True` fields, but the
    live schema uses `parent_user_id`, `child_user_id`, and `status='active'`.
    """
    from app.models.iam import ParentChildLink

    result = await db.execute(
        select(ParentChildLink.id).where(
            ParentChildLink.parent_user_id == parent_id,
            ParentChildLink.child_user_id == student_id,
            ParentChildLink.status == "active",
        )
    )
    return result.scalar_one_or_none() is not None


async def validate_teacher_class_access(
    db: AsyncSession,
    *,
    teacher_id: uuid.UUID,
    class_id: uuid.UUID,
) -> bool:
    """Verify that a teacher is assigned to a class."""
    from app.models.erp import TeacherAssignment

    result = await db.execute(
        select(TeacherAssignment.id).where(
            TeacherAssignment.teacher_id == teacher_id,
            TeacherAssignment.class_id == class_id,
        )
    )
    return result.scalar_one_or_none() is not None


async def validate_student_teacher_access(
    db: AsyncSession,
    *,
    student_id: uuid.UUID,
    teacher_id: uuid.UUID,
) -> bool:
    """Verify that a student and teacher share at least one active class."""
    from app.models.erp import Enrollment, EnrollmentStatus, TeacherAssignment

    student_classes = select(Enrollment.class_id).where(
        Enrollment.student_id == student_id,
        Enrollment.status == EnrollmentStatus.ACTIVE.value,
    )
    teacher_classes = select(TeacherAssignment.class_id).where(
        TeacherAssignment.teacher_id == teacher_id,
    )
    result = await db.execute(select(exists(student_classes.intersect(teacher_classes))))
    return bool(result.scalar())
