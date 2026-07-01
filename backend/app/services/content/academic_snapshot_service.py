"""Academic snapshot service (Phase 3.3 / G50c).

Builds frozen JSONB documents capturing everything about a student for
a given academic year. Used to power audit-grade transcripts and to
protect downstream reports from schema drift.

The snapshot blob includes:
  - student basic profile (id, full_name)
  - academic_year metadata
  - all enrollments for the year (incl. status, class, period, program,
    program_version)
  - program-history events for the year
  - grade summary (assignment-level grades + computed weighted average)
  - attendance summary (counts by status)
  - resolved_at timestamp (when the snapshot was taken)
  - schema_version: a small integer we bump if the JSONB shape changes
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import AuthContext, verify_school_boundary
from app.core.exceptions import NotFoundError
from app.core.unit_of_work import UnitOfWork
from app.models.erp import (
    AcademicSnapshot,
    AcademicYear,
    AttendanceRecord,
    AttendanceSession,
    Class,
    Enrollment,
    Period,
    Program,
    ProgramAssignmentEvent,
    ProgramVersion,
)
from app.models.iam import User
from app.models.lms import Assignment, Course, Grade, Submission
from app.services.platform.audit import AuditService

SNAPSHOT_SCHEMA_VERSION = 1


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AcademicSnapshotService:
    """CRUD + builder for AcademicSnapshot rows."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------
    def _to_response(self, snapshot: AcademicSnapshot) -> dict:
        return {
            "id": str(snapshot.id),
            "school_id": str(snapshot.school_id),
            "student_id": str(snapshot.student_id),
            "academic_year_id": str(snapshot.academic_year_id),
            "snapshot_kind": snapshot.snapshot_kind,
            "snapshot_data": snapshot.snapshot_data,
            "taken_at": snapshot.taken_at.isoformat(),
            "taken_by": (
                str(snapshot.taken_by) if snapshot.taken_by is not None else None
            ),
        }

    async def list_for_student(
        self,
        *,
        student_id: uuid.UUID,
        auth: AuthContext,
    ) -> list[dict]:
        # Cheap school-scope check by looking up the student row.
        student = await self.db.execute(select(User).where(User.id == student_id))
        student_row = student.scalar_one_or_none()
        if student_row is None:
            raise NotFoundError("Student not found", error_code="ERR-ERP-404")
        verify_school_boundary(student_row.school_id, auth)

        result = await self.db.execute(
            select(AcademicSnapshot)
            .where(
                AcademicSnapshot.school_id == auth.school_id,
                AcademicSnapshot.student_id == student_id,
            )
            .order_by(desc(AcademicSnapshot.taken_at))
        )
        return [self._to_response(s) for s in result.scalars().all()]

    async def get_one(
        self,
        *,
        snapshot_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict:
        result = await self.db.execute(
            select(AcademicSnapshot).where(AcademicSnapshot.id == snapshot_id)
        )
        snapshot = result.scalar_one_or_none()
        if snapshot is None:
            raise NotFoundError("Snapshot not found", error_code="ERR-ERP-404")
        verify_school_boundary(snapshot.school_id, auth)
        return self._to_response(snapshot)

    # ------------------------------------------------------------------
    # Take a new snapshot
    # ------------------------------------------------------------------
    async def take_snapshot(
        self,
        *,
        student_id: uuid.UUID,
        academic_year_id: uuid.UUID,
        snapshot_kind: str,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        student_result = await self.db.execute(
            select(User).where(User.id == student_id)
        )
        student = student_result.scalar_one_or_none()
        if student is None:
            raise NotFoundError("Student not found", error_code="ERR-ERP-404")
        verify_school_boundary(student.school_id, auth)

        ay_result = await self.db.execute(
            select(AcademicYear).where(AcademicYear.id == academic_year_id)
        )
        academic_year = ay_result.scalar_one_or_none()
        if academic_year is None:
            raise NotFoundError("Academic year not found", error_code="ERR-ERP-404")
        verify_school_boundary(academic_year.school_id, auth)

        blob = await self._build_blob(
            student=student,
            academic_year=academic_year,
            auth=auth,
        )

        async with UnitOfWork(self.db) as uow:
            now = _utc_now()
            snapshot = AcademicSnapshot(
                school_id=auth.school_id,
                student_id=student_id,
                academic_year_id=academic_year_id,
                snapshot_kind=snapshot_kind,
                snapshot_data=blob,
                taken_at=now,
                taken_by=auth.user_id,
                created_at=now,
            )
            uow.session.add(snapshot)
            await uow.session.flush()

            audit = AuditService(uow.session)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="ACADEMIC_SNAPSHOT_TAKEN",
                outcome="success",
                target_type="academic_snapshot",
                target_id=snapshot.id,
                entity_after={
                    "student_id": str(student_id),
                    "academic_year_id": str(academic_year_id),
                    "kind": snapshot_kind,
                    "schema_version": SNAPSHOT_SCHEMA_VERSION,
                },
                ip_address=ip_address,
            )
            await uow.commit()

        return self._to_response(snapshot)

    async def delete_snapshot(
        self,
        *,
        snapshot_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str | None,
    ) -> None:
        result = await self.db.execute(
            select(AcademicSnapshot).where(AcademicSnapshot.id == snapshot_id)
        )
        snapshot = result.scalar_one_or_none()
        if snapshot is None:
            raise NotFoundError("Snapshot not found", error_code="ERR-ERP-404")
        verify_school_boundary(snapshot.school_id, auth)

        async with UnitOfWork(self.db) as uow:
            attached = await uow.session.get(AcademicSnapshot, snapshot.id)
            if attached is None:
                raise NotFoundError("Snapshot not found", error_code="ERR-ERP-404")
            await uow.session.delete(attached)
            await uow.session.flush()

            audit = AuditService(uow.session)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="ACADEMIC_SNAPSHOT_DELETED",
                outcome="success",
                target_type="academic_snapshot",
                target_id=snapshot.id,
                entity_before={
                    "student_id": str(snapshot.student_id),
                    "academic_year_id": str(snapshot.academic_year_id),
                    "kind": snapshot.snapshot_kind,
                },
                ip_address=ip_address,
            )
            await uow.commit()

    # ------------------------------------------------------------------
    # Blob builder — single source of truth for snapshot shape
    # ------------------------------------------------------------------
    async def _build_blob(
        self,
        *,
        student: User,
        academic_year: AcademicYear,
        auth: AuthContext,
    ) -> dict:
        # Enrollments + class + period + program (+ version) for the year
        enroll_stmt = (
            select(Enrollment, Class, Period, Program, ProgramVersion)
            .join(Class, Class.id == Enrollment.class_id)
            .join(Period, Period.id == Enrollment.period_id)
            .outerjoin(Program, Program.id == Enrollment.program_id)
            .outerjoin(
                ProgramVersion,
                ProgramVersion.id == Enrollment.program_version_id,
            )
            .where(
                Enrollment.school_id == auth.school_id,
                Enrollment.student_id == student.id,
                Class.academic_year_id == academic_year.id,
            )
            .order_by(Period.date_start.asc(), Enrollment.created_at.asc())
        )
        enrollments_result = await self.db.execute(enroll_stmt)
        enrollments = []
        for enrollment, class_, period, program, version in enrollments_result.all():
            enrollments.append(
                {
                    "enrollment_id": str(enrollment.id),
                    "status": enrollment.status,
                    "class": {
                        "id": str(class_.id),
                        "code": class_.code,
                        "name": class_.name,
                    },
                    "period": {
                        "id": str(period.id),
                        "label": period.label,
                        "date_start": period.date_start.isoformat(),
                        "date_end": period.date_end.isoformat(),
                    },
                    "program": (
                        {
                            "id": str(program.id),
                            "code": program.code,
                            "name": program.name,
                        }
                        if program is not None
                        else None
                    ),
                    "program_version": (
                        {
                            "id": str(version.id),
                            "version_label": version.version_label,
                        }
                        if version is not None
                        else None
                    ),
                }
            )

        # Program-history events for the year
        events_result = await self.db.execute(
            select(ProgramAssignmentEvent)
            .where(
                ProgramAssignmentEvent.school_id == auth.school_id,
                ProgramAssignmentEvent.student_id == student.id,
                ProgramAssignmentEvent.academic_year_id == academic_year.id,
            )
            .order_by(ProgramAssignmentEvent.occurred_at.asc())
        )
        events = []
        for event in events_result.scalars().all():
            events.append(
                {
                    "id": str(event.id),
                    "from_program_id": (
                        str(event.from_program_id)
                        if event.from_program_id is not None
                        else None
                    ),
                    "to_program_id": str(event.to_program_id),
                    "reason_code": event.reason_code,
                    "reason_note": event.reason_note,
                    "occurred_at": event.occurred_at.isoformat(),
                }
            )

        # Grades summary — aggregate at the (subject, period) grain
        grades_stmt = (
            select(
                Course.title.label("course_title"),
                func.count(Grade.id).label("count"),
                func.avg(Grade.score).label("avg_score"),
            )
            .select_from(Grade)
            .join(Submission, Submission.id == Grade.submission_id)
            .join(Assignment, Assignment.id == Submission.assignment_id)
            .join(Course, Course.id == Assignment.course_id)
            .where(
                Course.school_id == auth.school_id,
                Submission.student_id == student.id,
            )
            .group_by(Course.title)
        )
        grades_result = await self.db.execute(grades_stmt)
        grades_summary = [
            {
                "course_title": row.course_title,
                "count": int(row.count or 0),
                "average": (
                    float(row.avg_score) if row.avg_score is not None else None
                ),
            }
            for row in grades_result
        ]

        # Attendance summary — record counts by status for the year window
        attendance_stmt = (
            select(
                AttendanceRecord.status,
                func.count(AttendanceRecord.id).label("count"),
            )
            .select_from(AttendanceRecord)
            .join(
                AttendanceSession,
                AttendanceSession.id == AttendanceRecord.attendance_session_id,
            )
            .where(
                AttendanceRecord.school_id == auth.school_id,
                AttendanceRecord.student_id == student.id,
                AttendanceSession.session_date >= academic_year.date_start,
                AttendanceSession.session_date <= academic_year.date_end,
            )
            .group_by(AttendanceRecord.status)
        )
        attendance_result = await self.db.execute(attendance_stmt)
        attendance_summary = {
            row.status: int(row.count or 0) for row in attendance_result
        }

        return {
            "schema_version": SNAPSHOT_SCHEMA_VERSION,
            "resolved_at": _utc_now().isoformat(),
            "student": {
                "id": str(student.id),
                "full_name": student.full_name,
                "email": student.email,
            },
            "academic_year": {
                "id": str(academic_year.id),
                "label": academic_year.label,
                "date_start": academic_year.date_start.isoformat(),
                "date_end": academic_year.date_end.isoformat(),
            },
            "enrollments": enrollments,
            "program_events": events,
            "grades_summary": grades_summary,
            "attendance_summary": attendance_summary,
        }
