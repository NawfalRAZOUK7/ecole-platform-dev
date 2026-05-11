"""Helper utilities for G49 program lifecycle integration tests."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.models.erp import Enrollment, EnrollmentStatus


async def _active_enrollment_id(
    session_factory: async_sessionmaker,
    student_uuid: uuid.UUID,
) -> str | None:
    """Return the active enrollment id for the given student."""
    async with session_factory() as session:
        result = await session.execute(
            select(Enrollment).where(
                Enrollment.student_id == student_uuid,
                Enrollment.status == EnrollmentStatus.ACTIVE.value,
            )
        )
        enrollment = result.scalar_one_or_none()
        return str(enrollment.id) if enrollment else None
