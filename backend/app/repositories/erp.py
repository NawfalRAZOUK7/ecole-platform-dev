"""Repository helpers for ERP classes, enrollments, attendance, and timetable."""

from __future__ import annotations

import uuid
from datetime import date, time
from typing import Any

from sqlalchemy import and_, func, select

from app.models.erp import (
    AbsenceJustification,
    AcademicYear,
    AttendanceRecord,
    AttendanceSession,
    Class,
    Enrollment,
    JustificationReview,
    Period,
    TeacherAssignment,
    TimetableException,
    TimetableSlot,
)
from app.models.iam import ParentChildLink, User
from app.repositories.base import BaseRepository


class ERPRepository(BaseRepository):
    """Data access for ERP workflows."""

    async def get_user_by_id(
        self,
        user_id: uuid.UUID,
    ) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_academic_year(
        self,
        academic_year_id: uuid.UUID,
    ) -> AcademicYear | None:
        result = await self.db.execute(
            select(AcademicYear).where(AcademicYear.id == academic_year_id)
        )
        return result.scalar_one_or_none()

    async def get_period(
        self,
        period_id: uuid.UUID,
    ) -> Period | None:
        result = await self.db.execute(select(Period).where(Period.id == period_id))
        return result.scalar_one_or_none()

    async def get_class(
        self,
        class_id: uuid.UUID,
    ) -> Class | None:
        result = await self.db.execute(select(Class).where(Class.id == class_id))
        return result.scalar_one_or_none()

    async def list_classes(
        self,
        *,
        school_id: uuid.UUID,
    ) -> list[Class]:
        result = await self.db.execute(
            select(Class)
            .where(Class.school_id == school_id)
            .order_by(Class.name.asc(), Class.code.asc())
        )
        return list(result.scalars().all())

    async def get_class_counts(
        self,
        *,
        class_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> tuple[int, int]:
        teacher_count_result = await self.db.execute(
            select(func.count())
            .select_from(TeacherAssignment)
            .where(
                TeacherAssignment.class_id == class_id,
                TeacherAssignment.school_id == school_id,
            )
        )
        student_count_result = await self.db.execute(
            select(func.count())
            .select_from(Enrollment)
            .where(
                Enrollment.class_id == class_id,
                Enrollment.school_id == school_id,
                Enrollment.status == "active",
            )
        )
        teacher_count = int(teacher_count_result.scalar() or 0)
        student_count = int(student_count_result.scalar() or 0)
        return teacher_count, student_count

    async def list_teacher_class_ids(
        self,
        *,
        teacher_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> set[uuid.UUID]:
        result = await self.db.execute(
            select(TeacherAssignment.class_id).where(
                TeacherAssignment.teacher_id == teacher_id,
                TeacherAssignment.school_id == school_id,
            )
        )
        return set(result.scalars().all())

    async def get_active_enrollment(
        self,
        *,
        student_id: uuid.UUID,
        class_id: uuid.UUID,
        period_id: uuid.UUID,
    ) -> Enrollment | None:
        result = await self.db.execute(
            select(Enrollment).where(
                Enrollment.student_id == student_id,
                Enrollment.class_id == class_id,
                Enrollment.period_id == period_id,
                Enrollment.status == "active",
            )
        )
        return result.scalar_one_or_none()

    async def get_active_enrollment_for_student_period(
        self,
        *,
        student_id: uuid.UUID,
        period_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> Enrollment | None:
        result = await self.db.execute(
            select(Enrollment).where(
                Enrollment.student_id == student_id,
                Enrollment.period_id == period_id,
                Enrollment.school_id == school_id,
                Enrollment.status == "active",
            )
        )
        return result.scalar_one_or_none()

    async def create_enrollment(self, **kwargs: Any) -> Enrollment:
        enrollment = Enrollment(**kwargs)
        self.db.add(enrollment)
        await self.db.flush()
        return enrollment

    async def get_teacher_assignment(
        self,
        *,
        teacher_id: uuid.UUID,
        class_id: uuid.UUID,
        period_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> TeacherAssignment | None:
        result = await self.db.execute(
            select(TeacherAssignment).where(
                TeacherAssignment.teacher_id == teacher_id,
                TeacherAssignment.class_id == class_id,
                TeacherAssignment.period_id == period_id,
                TeacherAssignment.school_id == school_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_teacher_assignment(self, **kwargs: Any) -> TeacherAssignment:
        assignment = TeacherAssignment(**kwargs)
        self.db.add(assignment)
        await self.db.flush()
        return assignment

    async def get_attendance_session_by_scope(
        self,
        *,
        class_id: uuid.UUID,
        session_date: date,
        slot: str,
    ) -> AttendanceSession | None:
        result = await self.db.execute(
            select(AttendanceSession).where(
                AttendanceSession.class_id == class_id,
                AttendanceSession.session_date == session_date,
                AttendanceSession.slot == slot,
            )
        )
        return result.scalar_one_or_none()

    async def create_attendance_session(self, **kwargs: Any) -> AttendanceSession:
        session = AttendanceSession(**kwargs)
        self.db.add(session)
        await self.db.flush()
        return session

    async def create_attendance_records(
        self,
        records_data: list[dict[str, Any]],
    ) -> list[AttendanceRecord]:
        records = [AttendanceRecord(**data) for data in records_data]
        if records:
            self.db.add_all(records)
            await self.db.flush()
        return records

    async def get_attendance_record(
        self,
        attendance_record_id: uuid.UUID,
    ) -> AttendanceRecord | None:
        result = await self.db.execute(
            select(AttendanceRecord).where(AttendanceRecord.id == attendance_record_id)
        )
        return result.scalar_one_or_none()

    async def save_attendance_record(
        self,
        record: AttendanceRecord,
    ) -> AttendanceRecord:
        self.db.add(record)
        await self.db.flush()
        return record

    async def get_absence_justification_by_record(
        self,
        attendance_record_id: uuid.UUID,
    ) -> AbsenceJustification | None:
        result = await self.db.execute(
            select(AbsenceJustification).where(
                AbsenceJustification.attendance_record_id == attendance_record_id
            )
        )
        return result.scalar_one_or_none()

    async def get_absence_justification(
        self,
        justification_id: uuid.UUID,
    ) -> AbsenceJustification | None:
        result = await self.db.execute(
            select(AbsenceJustification).where(AbsenceJustification.id == justification_id)
        )
        return result.scalar_one_or_none()

    async def create_absence_justification(
        self,
        **kwargs: Any,
    ) -> AbsenceJustification:
        justification = AbsenceJustification(**kwargs)
        self.db.add(justification)
        await self.db.flush()
        return justification

    async def save_absence_justification(
        self,
        justification: AbsenceJustification,
    ) -> AbsenceJustification:
        self.db.add(justification)
        await self.db.flush()
        return justification

    async def create_justification_review(
        self,
        **kwargs: Any,
    ) -> JustificationReview:
        review = JustificationReview(**kwargs)
        self.db.add(review)
        await self.db.flush()
        return review

    async def get_timetable_slot(
        self,
        slot_id: uuid.UUID,
    ) -> TimetableSlot | None:
        result = await self.db.execute(
            select(TimetableSlot).where(TimetableSlot.id == slot_id)
        )
        return result.scalar_one_or_none()

    async def list_timetable_slots(
        self,
        *,
        school_id: uuid.UUID,
        class_id: uuid.UUID | None = None,
        teacher_id: uuid.UUID | None = None,
        academic_year_id: uuid.UUID | None = None,
        day_of_week: int | None = None,
    ) -> list[TimetableSlot]:
        query = select(TimetableSlot).where(TimetableSlot.school_id == school_id)

        if class_id:
            query = query.where(TimetableSlot.class_id == class_id)
        if teacher_id:
            query = query.where(TimetableSlot.teacher_id == teacher_id)
        if academic_year_id:
            query = query.where(TimetableSlot.academic_year_id == academic_year_id)
        if day_of_week is not None:
            query = query.where(TimetableSlot.day_of_week == day_of_week)

        result = await self.db.execute(
            query.order_by(TimetableSlot.day_of_week, TimetableSlot.start_time)
        )
        return list(result.scalars().all())

    async def find_overlapping_class_slot(
        self,
        *,
        school_id: uuid.UUID,
        class_id: uuid.UUID,
        academic_year_id: uuid.UUID,
        day_of_week: int,
        start_time: time,
        end_time: time,
        exclude_slot_id: uuid.UUID | None = None,
    ) -> TimetableSlot | None:
        query = select(TimetableSlot).where(
            TimetableSlot.school_id == school_id,
            TimetableSlot.class_id == class_id,
            TimetableSlot.academic_year_id == academic_year_id,
            TimetableSlot.day_of_week == day_of_week,
            TimetableSlot.start_time < end_time,
            TimetableSlot.end_time > start_time,
        )
        if exclude_slot_id:
            query = query.where(TimetableSlot.id != exclude_slot_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def find_overlapping_teacher_slot(
        self,
        *,
        school_id: uuid.UUID,
        teacher_id: uuid.UUID,
        academic_year_id: uuid.UUID,
        day_of_week: int,
        start_time: time,
        end_time: time,
        exclude_slot_id: uuid.UUID | None = None,
    ) -> TimetableSlot | None:
        query = select(TimetableSlot).where(
            TimetableSlot.school_id == school_id,
            TimetableSlot.teacher_id == teacher_id,
            TimetableSlot.academic_year_id == academic_year_id,
            TimetableSlot.day_of_week == day_of_week,
            TimetableSlot.start_time < end_time,
            TimetableSlot.end_time > start_time,
        )
        if exclude_slot_id:
            query = query.where(TimetableSlot.id != exclude_slot_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_timetable_slot(self, **kwargs: Any) -> TimetableSlot:
        slot = TimetableSlot(**kwargs)
        self.db.add(slot)
        await self.db.flush()
        return slot

    async def save_timetable_slot(
        self,
        slot: TimetableSlot,
    ) -> TimetableSlot:
        self.db.add(slot)
        await self.db.flush()
        return slot

    async def delete_timetable_slot(
        self,
        slot: TimetableSlot,
    ) -> None:
        await self.db.delete(slot)

    async def get_timetable_exception_by_slot_and_date(
        self,
        *,
        timetable_slot_id: uuid.UUID,
        exception_date: date,
    ) -> TimetableException | None:
        result = await self.db.execute(
            select(TimetableException).where(
                TimetableException.timetable_slot_id == timetable_slot_id,
                TimetableException.exception_date == exception_date,
            )
        )
        return result.scalar_one_or_none()

    async def create_timetable_exception(
        self,
        **kwargs: Any,
    ) -> TimetableException:
        exception = TimetableException(**kwargs)
        self.db.add(exception)
        await self.db.flush()
        return exception

    async def list_timetable_exceptions(
        self,
        *,
        school_id: uuid.UUID,
        timetable_slot_id: uuid.UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        exception_type: str | None = None,
    ) -> list[TimetableException]:
        query = select(TimetableException).where(
            TimetableException.school_id == school_id
        )

        if timetable_slot_id:
            query = query.where(TimetableException.timetable_slot_id == timetable_slot_id)
        if date_from:
            query = query.where(TimetableException.exception_date >= date_from)
        if date_to:
            query = query.where(TimetableException.exception_date <= date_to)
        if exception_type:
            query = query.where(TimetableException.exception_type == exception_type)

        result = await self.db.execute(
            query.order_by(TimetableException.exception_date.desc())
        )
        return list(result.scalars().all())

    async def get_active_student_class_id(
        self,
        *,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> uuid.UUID | None:
        result = await self.db.execute(
            select(Enrollment.class_id)
            .where(
                Enrollment.student_id == student_id,
                Enrollment.school_id == school_id,
                Enrollment.status == "active",
            )
            .limit(1)
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

    async def list_weekly_timetable_slots(
        self,
        *,
        school_id: uuid.UUID,
        monday: date,
        sunday: date,
        class_id: uuid.UUID | None = None,
        teacher_id: uuid.UUID | None = None,
    ) -> list[TimetableSlot]:
        query = select(TimetableSlot).where(TimetableSlot.school_id == school_id)
        if class_id:
            query = query.where(TimetableSlot.class_id == class_id)
        if teacher_id:
            query = query.where(TimetableSlot.teacher_id == teacher_id)

        query = query.where(
            and_(
                (TimetableSlot.effective_from.is_(None))
                | (TimetableSlot.effective_from <= sunday),
                (TimetableSlot.effective_until.is_(None))
                | (TimetableSlot.effective_until >= monday),
            )
        )

        result = await self.db.execute(
            query.order_by(TimetableSlot.day_of_week, TimetableSlot.start_time)
        )
        return list(result.scalars().all())

    async def list_timetable_exceptions_for_slot_ids(
        self,
        *,
        slot_ids: list[uuid.UUID],
        monday: date,
        sunday: date,
    ) -> list[TimetableException]:
        if not slot_ids:
            return []

        result = await self.db.execute(
            select(TimetableException).where(
                TimetableException.timetable_slot_id.in_(slot_ids),
                TimetableException.exception_date >= monday,
                TimetableException.exception_date <= sunday,
            )
        )
        return list(result.scalars().all())

    async def list_classes_by_ids(
        self,
        class_ids: list[uuid.UUID],
    ) -> list[Class]:
        if not class_ids:
            return []

        result = await self.db.execute(select(Class).where(Class.id.in_(class_ids)))
        return list(result.scalars().all())
