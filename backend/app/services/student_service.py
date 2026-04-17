"""Student-level service helpers."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.iam import StudentProfile


async def get_student_age(db: AsyncSession, user_id: uuid.UUID) -> int | None:
    """Return the student's age in whole years, or None if DOB is not set."""
    stmt = select(StudentProfile.date_of_birth).where(
        StudentProfile.user_id == user_id
    )
    result = await db.execute(stmt)
    dob = result.scalar_one_or_none()
    if dob is None:
        return None
    today = datetime.now(timezone.utc).date()
    # Handle both date and datetime objects from DB
    if isinstance(dob, datetime):
        dob = dob.date()
    elif not isinstance(dob, date):
        return None
    return (today - dob).days // 365
