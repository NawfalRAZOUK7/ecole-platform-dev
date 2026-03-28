"""Repository helpers for timetable constraints and generation jobs."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import delete, func, select

from app.models.erp import (
    AcademicYear,
    Class,
    Enrollment,
    TeacherAssignment,
    TimetableConstraint,
    TimetableGenerationJob,
    TimetableSlot,
)
from app.repositories.base import BaseRepository


class TimetableGenerationRepository(BaseRepository):
    """Data access for timetable generation workflows."""

    async def get_academic_year(
        self,
        academic_year_id: uuid.UUID,
    ) -> AcademicYear | None:
        result = await self.db.execute(
            select(AcademicYear).where(AcademicYear.id == academic_year_id)
        )
        return result.scalar_one_or_none()

    async def list_constraints(
        self,
        *,
        school_id: uuid.UUID,
        academic_year_id: uuid.UUID,
    ) -> list[TimetableConstraint]:
        result = await self.db.execute(
            select(TimetableConstraint)
            .where(
                TimetableConstraint.school_id == school_id,
                TimetableConstraint.academic_year_id == academic_year_id,
            )
            .order_by(TimetableConstraint.created_at.asc(), TimetableConstraint.id.asc())
        )
        return list(result.scalars().all())

    async def delete_constraints(
        self,
        *,
        school_id: uuid.UUID,
        academic_year_id: uuid.UUID,
    ) -> None:
        await self.db.execute(
            delete(TimetableConstraint).where(
                TimetableConstraint.school_id == school_id,
                TimetableConstraint.academic_year_id == academic_year_id,
            )
        )

    async def create_constraint(self, **kwargs: Any) -> TimetableConstraint:
        constraint = TimetableConstraint(**kwargs)
        self.db.add(constraint)
        await self.db.flush()
        return constraint

    async def get_job(
        self,
        job_id: uuid.UUID,
    ) -> TimetableGenerationJob | None:
        result = await self.db.execute(
            select(TimetableGenerationJob).where(TimetableGenerationJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def create_job(self, **kwargs: Any) -> TimetableGenerationJob:
        job = TimetableGenerationJob(**kwargs)
        self.db.add(job)
        await self.db.flush()
        return job

    async def save_job(
        self,
        job: TimetableGenerationJob,
    ) -> TimetableGenerationJob:
        self.db.add(job)
        await self.db.flush()
        return job

    async def list_classes_for_academic_year(
        self,
        *,
        school_id: uuid.UUID,
        academic_year_id: uuid.UUID,
    ) -> list[Class]:
        result = await self.db.execute(
            select(Class)
            .where(
                Class.school_id == school_id,
                Class.academic_year_id == academic_year_id,
            )
            .order_by(Class.name.asc(), Class.code.asc())
        )
        return list(result.scalars().all())

    async def get_class_student_counts(
        self,
        *,
        school_id: uuid.UUID,
        academic_year_id: uuid.UUID,
    ) -> dict[uuid.UUID, int]:
        result = await self.db.execute(
            select(Enrollment.class_id, func.count(Enrollment.id))
            .join(Class, Class.id == Enrollment.class_id)
            .where(
                Enrollment.school_id == school_id,
                Enrollment.status == "active",
                Class.academic_year_id == academic_year_id,
            )
            .group_by(Enrollment.class_id)
        )
        return {class_id: int(count or 0) for class_id, count in result.all()}

    async def list_teacher_assignments_for_academic_year(
        self,
        *,
        school_id: uuid.UUID,
        academic_year_id: uuid.UUID,
    ) -> list[tuple[uuid.UUID, uuid.UUID]]:
        result = await self.db.execute(
            select(
                TeacherAssignment.class_id,
                TeacherAssignment.teacher_id,
            )
            .join(Class, Class.id == TeacherAssignment.class_id)
            .where(
                TeacherAssignment.school_id == school_id,
                Class.academic_year_id == academic_year_id,
            )
            .distinct()
            .order_by(TeacherAssignment.class_id.asc(), TeacherAssignment.teacher_id.asc())
        )
        return [(class_id, teacher_id) for class_id, teacher_id in result.all()]

    async def list_existing_subject_teacher_pairs(
        self,
        *,
        school_id: uuid.UUID,
        academic_year_id: uuid.UUID,
    ) -> list[tuple[uuid.UUID, str, uuid.UUID]]:
        result = await self.db.execute(
            select(
                TimetableSlot.class_id,
                TimetableSlot.subject,
                TimetableSlot.teacher_id,
            )
            .where(
                TimetableSlot.school_id == school_id,
                TimetableSlot.academic_year_id == academic_year_id,
            )
            .distinct()
        )
        return [
            (class_id, subject, teacher_id)
            for class_id, subject, teacher_id in result.all()
        ]

    async def list_existing_room_names(
        self,
        *,
        school_id: uuid.UUID,
        academic_year_id: uuid.UUID,
    ) -> list[str]:
        result = await self.db.execute(
            select(TimetableSlot.room)
            .where(
                TimetableSlot.school_id == school_id,
                TimetableSlot.academic_year_id == academic_year_id,
                TimetableSlot.room.is_not(None),
            )
            .distinct()
            .order_by(TimetableSlot.room.asc())
        )
        return [room for room in result.scalars().all() if room]

    async def delete_timetable_slots_for_academic_year(
        self,
        *,
        school_id: uuid.UUID,
        academic_year_id: uuid.UUID,
    ) -> None:
        await self.db.execute(
            delete(TimetableSlot).where(
                TimetableSlot.school_id == school_id,
                TimetableSlot.academic_year_id == academic_year_id,
            )
        )

    async def create_timetable_slot(self, **kwargs: Any) -> TimetableSlot:
        slot = TimetableSlot(**kwargs)
        self.db.add(slot)
        await self.db.flush()
        return slot
