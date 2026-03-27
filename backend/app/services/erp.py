"""ERP service layer for classes, enrollments, attendance, and timetable."""

from __future__ import annotations

import uuid
from datetime import date, timedelta, time

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    AuthContext,
    verify_parent_child_ownership,
    verify_school_boundary,
    verify_teacher_assignment,
)
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.erp import (
    AbsenceJustification,
    AttendanceRecord,
    AttendanceSession,
    Class,
    JustificationReview,
    TeacherAssignment,
    TimetableException,
    TimetableSlot,
)
from app.repositories.erp import ERPRepository
from app.schemas.erp import (
    AttendanceRecordResponse,
    AttendanceSessionCreateRequest,
    AttendanceSessionResponse,
    EnrollmentResponse,
    JustificationCreateRequest,
    JustificationResponse,
    JustificationReviewRequest,
    JustificationReviewResponse,
    TeacherAssignmentCreateRequest,
    TeacherAssignmentResponse,
    TimetableExceptionCreateRequest,
    TimetableExceptionResponse,
    TimetableSlotBulkCreateRequest,
    TimetableSlotCreateRequest,
    TimetableSlotResponse,
    TimetableSlotUpdateRequest,
    WeeklySlotResponse,
    WeeklyTimetableResponse,
)
from app.services.audit import AuditService


class ERPService:
    """Business logic for ERP domain workflows."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = ERPRepository(db)
        self.audit = AuditService(db)

    def _class_to_response(
        self,
        class_room: Class,
        *,
        teacher_count: int,
        student_count: int,
    ) -> dict:
        return {
            "id": str(class_room.id),
            "code": class_room.code,
            "name": class_room.name,
            "school_id": str(class_room.school_id),
            "academic_year_id": str(class_room.academic_year_id),
            "teacher_count": teacher_count,
            "student_count": student_count,
        }

    def _enrollment_to_response(self, enrollment) -> dict:
        return EnrollmentResponse(
            id=str(enrollment.id),
            student_id=str(enrollment.student_id),
            class_id=str(enrollment.class_id),
            period_id=str(enrollment.period_id),
            school_id=str(enrollment.school_id),
            status=enrollment.status,
        ).model_dump()

    def _teacher_assignment_to_response(
        self,
        assignment: TeacherAssignment,
    ) -> dict:
        return TeacherAssignmentResponse(
            id=str(assignment.id),
            teacher_id=str(assignment.teacher_id),
            class_id=str(assignment.class_id),
            period_id=str(assignment.period_id),
            school_id=str(assignment.school_id),
        ).model_dump()

    def _attendance_record_to_response(self, record: AttendanceRecord) -> dict:
        return AttendanceRecordResponse(
            id=str(record.id),
            student_id=str(record.student_id),
            status=record.status,
            absence_reason=record.absence_reason,
        ).model_dump()

    def _attendance_session_to_response(
        self,
        session: AttendanceSession,
        records: list[AttendanceRecord],
    ) -> dict:
        return AttendanceSessionResponse(
            id=str(session.id),
            class_id=str(session.class_id),
            period_id=str(session.period_id),
            teacher_id=str(session.teacher_id),
            school_id=str(session.school_id),
            session_date=str(session.session_date),
            slot=session.slot,
            records=[
                AttendanceRecordResponse(**self._attendance_record_to_response(record))
                for record in records
            ],
        ).model_dump()

    def _justification_to_response(
        self,
        justification: AbsenceJustification,
    ) -> dict:
        return JustificationResponse(
            id=str(justification.id),
            attendance_record_id=str(justification.attendance_record_id),
            parent_id=str(justification.parent_id),
            school_id=str(justification.school_id),
            status=justification.status,
            reason=justification.reason,
            rejection_reason=justification.rejection_reason,
        ).model_dump()

    def _review_to_response(self, review: JustificationReview) -> dict:
        return JustificationReviewResponse(
            id=str(review.id),
            justification_id=str(review.justification_id),
            reviewer_id=str(review.reviewer_id),
            school_id=str(review.school_id),
            decision=review.decision,
        ).model_dump()

    def _slot_to_response(self, slot: TimetableSlot) -> dict:
        return TimetableSlotResponse(
            id=str(slot.id),
            school_id=str(slot.school_id),
            class_id=str(slot.class_id),
            academic_year_id=str(slot.academic_year_id),
            day_of_week=slot.day_of_week,
            start_time=slot.start_time.strftime("%H:%M"),
            end_time=slot.end_time.strftime("%H:%M"),
            subject=slot.subject,
            teacher_id=str(slot.teacher_id),
            room=slot.room,
            is_recurring=slot.is_recurring,
            effective_from=slot.effective_from.isoformat() if slot.effective_from else None,
            effective_until=slot.effective_until.isoformat()
            if slot.effective_until
            else None,
            created_at=slot.created_at.isoformat(),
            updated_at=slot.updated_at.isoformat() if slot.updated_at else None,
        ).model_dump()

    def _exception_to_response(self, exception: TimetableException) -> dict:
        return TimetableExceptionResponse(
            id=str(exception.id),
            timetable_slot_id=str(exception.timetable_slot_id),
            school_id=str(exception.school_id),
            exception_date=exception.exception_date.isoformat(),
            exception_type=exception.exception_type,
            substitute_teacher_id=str(exception.substitute_teacher_id)
            if exception.substitute_teacher_id
            else None,
            new_room=exception.new_room,
            reason=exception.reason,
            created_at=exception.created_at.isoformat(),
        ).model_dump()

    def _week_bounds(self, target_date: date) -> tuple[date, date]:
        monday = target_date - timedelta(days=target_date.weekday())
        sunday = monday + timedelta(days=6)
        return monday, sunday

    def _empty_weekly_payload(
        self,
        *,
        week_start: date,
        week_end: date,
    ) -> dict:
        return WeeklyTimetableResponse(
            academic_year_id="",
            week_start=week_start.isoformat(),
            week_end=week_end.isoformat(),
            slots=[],
        ).model_dump()

    async def _ensure_no_slot_overlap(
        self,
        *,
        school_id: uuid.UUID,
        class_id: uuid.UUID,
        teacher_id: uuid.UUID,
        academic_year_id: uuid.UUID,
        day_of_week: int,
        start_time: time,
        end_time: time,
        exclude_slot_id: uuid.UUID | None = None,
    ) -> None:
        class_overlap = await self.repo.find_overlapping_class_slot(
            school_id=school_id,
            class_id=class_id,
            academic_year_id=academic_year_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            exclude_slot_id=exclude_slot_id,
        )
        if class_overlap is not None:
            raise ConflictError(
                "Class already has a slot at this time",
                error_code="ERR-ERP-409",
                details={"class_id": str(class_id), "day_of_week": day_of_week},
            )

        teacher_overlap = await self.repo.find_overlapping_teacher_slot(
            school_id=school_id,
            teacher_id=teacher_id,
            academic_year_id=academic_year_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            exclude_slot_id=exclude_slot_id,
        )
        if teacher_overlap is not None:
            raise ConflictError(
                "Teacher already has a slot at this time",
                error_code="ERR-ERP-409",
                details={"teacher_id": str(teacher_id), "day_of_week": day_of_week},
            )

    async def get_class(
        self,
        *,
        class_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict:
        class_room = await self.repo.get_class(class_id)
        if class_room is None:
            raise NotFoundError("Class not found", error_code="ERR-ERP-404")
        verify_school_boundary(class_room.school_id, auth)

        if auth.role == "TCH":
            teacher_classes = await self.repo.list_teacher_class_ids(
                teacher_id=auth.user_id,
                school_id=auth.school_id,
            )
            verify_teacher_assignment(class_id, teacher_classes)

        teacher_count, student_count = await self.repo.get_class_counts(
            class_id=class_id,
            school_id=auth.school_id,
        )
        return self._class_to_response(
            class_room,
            teacher_count=teacher_count,
            student_count=student_count,
        )

    async def create_enrollment(
        self,
        *,
        student_id: uuid.UUID,
        class_id: uuid.UUID,
        period_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        student = await self.repo.get_user_by_id(student_id)
        if student is None:
            raise NotFoundError("Student not found", error_code="ERR-ERP-404")
        verify_school_boundary(student.school_id, auth)

        class_room = await self.repo.get_class(class_id)
        if class_room is None:
            raise NotFoundError("Class not found", error_code="ERR-ERP-404")
        verify_school_boundary(class_room.school_id, auth)

        period = await self.repo.get_period(period_id)
        if period is None:
            raise NotFoundError("Period not found", error_code="ERR-ERP-404")
        verify_school_boundary(period.school_id, auth)

        if period.status != "active":
            raise ConflictError(
                "Period is not active",
                error_code="ERR-ERP-409",
            )

        existing = await self.repo.get_active_enrollment(
            student_id=student_id,
            class_id=class_id,
            period_id=period_id,
        )
        if existing is not None:
            return self._enrollment_to_response(existing)

        conflicting = await self.repo.get_active_enrollment_for_student_period(
            student_id=student_id,
            period_id=period_id,
            school_id=auth.school_id,
        )
        if conflicting is not None:
            raise ConflictError(
                "Student already has an active enrollment for this period",
                error_code="ERR-ERP-409",
                details={
                    "existing_enrollment_id": str(conflicting.id),
                    "existing_class_id": str(conflicting.class_id),
                },
            )

        enrollment = await self.repo.create_enrollment(
            student_id=student_id,
            class_id=class_id,
            period_id=period_id,
            school_id=auth.school_id,
            status="active",
        )

        await self.audit.log_event(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            action_type="ENROLLMENT_ASSIGNED",
            outcome="success",
            target_type="enrollment",
            target_id=enrollment.id,
            entity_after={
                "student_id": str(student_id),
                "class_id": str(class_id),
                "period_id": str(period_id),
                "status": "active",
            },
            ip_address=ip_address,
        )
        return self._enrollment_to_response(enrollment)

    async def create_teacher_assignment(
        self,
        *,
        body: TeacherAssignmentCreateRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        teacher = await self.repo.get_user_by_id(body.teacher_id)
        if teacher is None:
            raise NotFoundError("Teacher not found", error_code="ERR-ERP-404")
        verify_school_boundary(teacher.school_id, auth)

        class_room = await self.repo.get_class(body.class_id)
        if class_room is None:
            raise NotFoundError("Class not found", error_code="ERR-ERP-404")
        verify_school_boundary(class_room.school_id, auth)

        period = await self.repo.get_period(body.period_id)
        if period is None:
            raise NotFoundError("Period not found", error_code="ERR-ERP-404")
        verify_school_boundary(period.school_id, auth)

        existing = await self.repo.get_teacher_assignment(
            teacher_id=body.teacher_id,
            class_id=body.class_id,
            period_id=body.period_id,
            school_id=auth.school_id,
        )
        if existing is not None:
            return self._teacher_assignment_to_response(existing)

        assignment = await self.repo.create_teacher_assignment(
            teacher_id=body.teacher_id,
            class_id=body.class_id,
            period_id=body.period_id,
            school_id=auth.school_id,
        )

        await self.audit.log_event(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            action_type="TEACHER_ASSIGNED",
            outcome="success",
            target_type="teacher_assignment",
            target_id=assignment.id,
            entity_after={
                "teacher_id": str(body.teacher_id),
                "class_id": str(body.class_id),
                "period_id": str(body.period_id),
            },
            ip_address=ip_address,
        )
        return self._teacher_assignment_to_response(assignment)

    async def create_attendance_session(
        self,
        *,
        body: AttendanceSessionCreateRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        class_room = await self.repo.get_class(body.class_id)
        if class_room is None:
            raise NotFoundError("Class not found", error_code="ERR-ERP-404")
        verify_school_boundary(class_room.school_id, auth)

        teacher_classes = await self.repo.list_teacher_class_ids(
            teacher_id=auth.user_id,
            school_id=auth.school_id,
        )
        verify_teacher_assignment(body.class_id, teacher_classes)

        period = await self.repo.get_period(body.period_id)
        if period is None:
            raise NotFoundError("Period not found", error_code="ERR-ERP-404")
        verify_school_boundary(period.school_id, auth)
        if period.status != "active":
            raise ConflictError("Period is not active", error_code="ERR-ERP-409")

        existing = await self.repo.get_attendance_session_by_scope(
            class_id=body.class_id,
            session_date=body.session_date,
            slot=body.slot,
        )
        if existing is not None:
            raise ConflictError(
                "Attendance session already exists for this class/date/slot",
                error_code="ERR-ERP-409",
                details={"existing_session_id": str(existing.id)},
            )

        session = await self.repo.create_attendance_session(
            class_id=body.class_id,
            period_id=body.period_id,
            teacher_id=auth.user_id,
            school_id=auth.school_id,
            session_date=body.session_date,
            slot=body.slot,
        )
        records = await self.repo.create_attendance_records(
            [
                {
                    "attendance_session_id": session.id,
                    "student_id": record.student_id,
                    "school_id": auth.school_id,
                    "status": record.status,
                    "absence_reason": record.absence_reason,
                }
                for record in body.records
            ]
        )

        await self.audit.log_event(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            action_type="ATTENDANCE_MARKED",
            outcome="success",
            target_type="attendance_session",
            target_id=session.id,
            entity_after={
                "class_id": str(body.class_id),
                "session_date": str(body.session_date),
                "slot": body.slot,
                "record_count": len(body.records),
            },
            ip_address=ip_address,
        )
        return self._attendance_session_to_response(session, records)

    async def create_justification(
        self,
        *,
        body: JustificationCreateRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        record = await self.repo.get_attendance_record(body.attendance_record_id)
        if record is None:
            raise NotFoundError("Attendance record not found", error_code="ERR-ERP-404")
        verify_school_boundary(record.school_id, auth)

        if record.status not in ("absent", "late"):
            raise ValidationError(
                "Only absent or late records can be justified",
                error_code="ERR-ERP-422",
            )

        child_ids = await self.repo.list_parent_child_ids(
            parent_id=auth.user_id,
            school_id=auth.school_id,
        )
        verify_parent_child_ownership(record.student_id, child_ids)

        existing = await self.repo.get_absence_justification_by_record(
            body.attendance_record_id
        )
        if existing is not None:
            return self._justification_to_response(existing)

        justification = await self.repo.create_absence_justification(
            attendance_record_id=body.attendance_record_id,
            parent_id=auth.user_id,
            school_id=auth.school_id,
            status="pending",
            reason=body.reason,
        )

        await self.audit.log_event(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            action_type="JUSTIFICATION_SUBMITTED",
            outcome="success",
            target_type="absence_justification",
            target_id=justification.id,
            entity_after={
                "attendance_record_id": str(body.attendance_record_id),
                "reason": body.reason,
            },
            ip_address=ip_address,
        )
        return self._justification_to_response(justification)

    async def review_justification(
        self,
        *,
        justification_id: uuid.UUID,
        body: JustificationReviewRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        justification = await self.repo.get_absence_justification(justification_id)
        if justification is None:
            raise NotFoundError("Justification not found", error_code="ERR-ERP-404")
        verify_school_boundary(justification.school_id, auth)

        if justification.status != "pending":
            raise ConflictError(
                "Justification has already been reviewed",
                error_code="ERR-ERP-409",
                details={"current_status": justification.status},
            )

        if body.decision == "rejected" and not body.rejection_reason:
            raise ValidationError(
                "Rejection reason is required when rejecting a justification",
                error_code="ERR-ERP-422",
            )

        justification.status = body.decision
        if body.decision == "rejected":
            justification.rejection_reason = body.rejection_reason
        await self.repo.save_absence_justification(justification)

        if body.decision == "justified":
            record = await self.repo.get_attendance_record(
                justification.attendance_record_id
            )
            if record is not None:
                record.status = "excused"
                await self.repo.save_attendance_record(record)

        review = await self.repo.create_justification_review(
            justification_id=justification_id,
            reviewer_id=auth.user_id,
            school_id=auth.school_id,
            decision=body.decision,
        )

        await self.audit.log_event(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            action_type="JUSTIFICATION_REVIEWED",
            outcome="success",
            target_type="justification_review",
            target_id=review.id,
            entity_after={
                "justification_id": str(justification_id),
                "decision": body.decision,
            },
            ip_address=ip_address,
        )
        return self._review_to_response(review)

    async def create_timetable_slots(
        self,
        *,
        body: TimetableSlotCreateRequest | TimetableSlotBulkCreateRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict | list[dict]:
        if isinstance(body, TimetableSlotCreateRequest):
            slot_requests = [body]
        else:
            slot_requests = body.slots

        created_slots: list[TimetableSlot] = []

        for slot_request in slot_requests:
            if slot_request.end_time <= slot_request.start_time:
                raise ValidationError(
                    "end_time must be after start_time",
                    error_code="ERR-ERP-422",
                    details={
                        "start_time": str(slot_request.start_time),
                        "end_time": str(slot_request.end_time),
                    },
                )

            class_room = await self.repo.get_class(slot_request.class_id)
            if class_room is None:
                raise NotFoundError("Class not found", error_code="ERR-ERP-404")
            verify_school_boundary(class_room.school_id, auth)

            academic_year = await self.repo.get_academic_year(slot_request.academic_year_id)
            if academic_year is None:
                raise NotFoundError("Academic year not found", error_code="ERR-ERP-404")
            verify_school_boundary(academic_year.school_id, auth)

            await self._ensure_no_slot_overlap(
                school_id=auth.school_id,
                class_id=slot_request.class_id,
                teacher_id=slot_request.teacher_id,
                academic_year_id=slot_request.academic_year_id,
                day_of_week=slot_request.day_of_week,
                start_time=slot_request.start_time,
                end_time=slot_request.end_time,
            )

            slot = await self.repo.create_timetable_slot(
                school_id=auth.school_id,
                class_id=slot_request.class_id,
                academic_year_id=slot_request.academic_year_id,
                day_of_week=slot_request.day_of_week,
                start_time=slot_request.start_time,
                end_time=slot_request.end_time,
                subject=slot_request.subject,
                teacher_id=slot_request.teacher_id,
                room=slot_request.room,
                is_recurring=slot_request.is_recurring,
                effective_from=slot_request.effective_from,
                effective_until=slot_request.effective_until,
            )
            created_slots.append(slot)

            await self.audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="timetable_slot.create",
                target_type="timetable_slot",
                target_id=slot.id,
                outcome="success",
                entity_after=self._slot_to_response(slot),
                ip_address=ip_address,
            )

        response_data = [self._slot_to_response(slot) for slot in created_slots]
        if len(response_data) == 1:
            return response_data[0]
        return response_data

    async def list_timetable_slots(
        self,
        *,
        class_id: uuid.UUID | None,
        teacher_id: uuid.UUID | None,
        academic_year_id: uuid.UUID | None,
        day_of_week: int | None,
        auth: AuthContext,
    ) -> list[dict]:
        slots = await self.repo.list_timetable_slots(
            school_id=auth.school_id,
            class_id=class_id,
            teacher_id=teacher_id,
            academic_year_id=academic_year_id,
            day_of_week=day_of_week,
        )
        return [self._slot_to_response(slot) for slot in slots]

    async def update_timetable_slot(
        self,
        *,
        slot_id: uuid.UUID,
        body: TimetableSlotUpdateRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        slot = await self.repo.get_timetable_slot(slot_id)
        if slot is None:
            raise NotFoundError("Timetable slot not found", error_code="ERR-ERP-404")
        verify_school_boundary(slot.school_id, auth)

        entity_before = self._slot_to_response(slot)

        if body.day_of_week is not None:
            slot.day_of_week = body.day_of_week
        if body.start_time is not None:
            slot.start_time = body.start_time
        if body.end_time is not None:
            slot.end_time = body.end_time
        if body.subject is not None:
            slot.subject = body.subject
        if body.teacher_id is not None:
            slot.teacher_id = body.teacher_id
        if body.room is not None:
            slot.room = body.room
        if body.is_recurring is not None:
            slot.is_recurring = body.is_recurring
        if body.effective_from is not None:
            slot.effective_from = body.effective_from
        if body.effective_until is not None:
            slot.effective_until = body.effective_until

        if slot.end_time <= slot.start_time:
            raise ValidationError(
                "end_time must be after start_time",
                error_code="ERR-ERP-422",
            )

        await self._ensure_no_slot_overlap(
            school_id=auth.school_id,
            class_id=slot.class_id,
            teacher_id=slot.teacher_id,
            academic_year_id=slot.academic_year_id,
            day_of_week=slot.day_of_week,
            start_time=slot.start_time,
            end_time=slot.end_time,
            exclude_slot_id=slot.id,
        )

        await self.repo.save_timetable_slot(slot)
        entity_after = self._slot_to_response(slot)

        await self.audit.log_event(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            action_type="timetable_slot.update",
            target_type="timetable_slot",
            target_id=slot.id,
            outcome="success",
            entity_before=entity_before,
            entity_after=entity_after,
            ip_address=ip_address,
        )
        return entity_after

    async def delete_timetable_slot(
        self,
        *,
        slot_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        slot = await self.repo.get_timetable_slot(slot_id)
        if slot is None:
            raise NotFoundError("Timetable slot not found", error_code="ERR-ERP-404")
        verify_school_boundary(slot.school_id, auth)

        entity_before = self._slot_to_response(slot)
        await self.repo.delete_timetable_slot(slot)

        await self.audit.log_event(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            action_type="timetable_slot.delete",
            target_type="timetable_slot",
            target_id=slot.id,
            outcome="success",
            entity_before=entity_before,
            ip_address=ip_address,
        )
        return {"deleted": True, "id": str(slot_id)}

    async def get_class_weekly_timetable(
        self,
        *,
        class_id: uuid.UUID,
        target_date: date | None,
        auth: AuthContext,
    ) -> dict:
        class_room = await self.repo.get_class(class_id)
        if class_room is None:
            raise NotFoundError("Class not found", error_code="ERR-ERP-404")
        verify_school_boundary(class_room.school_id, auth)

        return await self._build_weekly_timetable(
            school_id=auth.school_id,
            target_date=target_date or date.today(),
            class_id=class_id,
        )

    async def get_teacher_weekly_timetable(
        self,
        *,
        teacher_id: uuid.UUID,
        target_date: date | None,
        auth: AuthContext,
    ) -> dict:
        return await self._build_weekly_timetable(
            school_id=auth.school_id,
            target_date=target_date or date.today(),
            teacher_id=teacher_id,
        )

    async def get_my_weekly_timetable(
        self,
        *,
        target_date: date | None,
        auth: AuthContext,
    ) -> dict:
        target = target_date or date.today()

        if auth.role == "TCH":
            return await self._build_weekly_timetable(
                school_id=auth.school_id,
                target_date=target,
                teacher_id=auth.user_id,
            )

        if auth.role == "STD":
            class_id = await self.repo.get_active_student_class_id(
                student_id=auth.user_id,
                school_id=auth.school_id,
            )
            if class_id is None:
                return self._empty_weekly_payload(week_start=target, week_end=target)
            return await self._build_weekly_timetable(
                school_id=auth.school_id,
                target_date=target,
                class_id=class_id,
            )

        if auth.role == "PAR":
            child_ids = await self.repo.list_parent_child_ids(
                parent_id=auth.user_id,
                school_id=auth.school_id,
            )
            if not child_ids:
                return self._empty_weekly_payload(week_start=target, week_end=target)

            first_child_id = next(iter(child_ids))
            class_id = await self.repo.get_active_student_class_id(
                student_id=first_child_id,
                school_id=auth.school_id,
            )
            if class_id is None:
                return self._empty_weekly_payload(week_start=target, week_end=target)
            return await self._build_weekly_timetable(
                school_id=auth.school_id,
                target_date=target,
                class_id=class_id,
            )

        monday, sunday = self._week_bounds(target)
        return self._empty_weekly_payload(week_start=monday, week_end=sunday)

    async def create_timetable_exception(
        self,
        *,
        body: TimetableExceptionCreateRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        slot = await self.repo.get_timetable_slot(body.timetable_slot_id)
        if slot is None:
            raise NotFoundError("Timetable slot not found", error_code="ERR-ERP-404")
        verify_school_boundary(slot.school_id, auth)

        if auth.role == "TCH" and slot.teacher_id != auth.user_id:
            raise NotFoundError("Timetable slot not found", error_code="ERR-ERP-404")

        if body.exception_type == "SUBSTITUTED" and body.substitute_teacher_id is None:
            raise ValidationError(
                "substitute_teacher_id is required for SUBSTITUTED exceptions",
                error_code="ERR-ERP-422",
            )
        if body.exception_type == "ROOM_CHANGED" and body.new_room is None:
            raise ValidationError(
                "new_room is required for ROOM_CHANGED exceptions",
                error_code="ERR-ERP-422",
            )

        duplicate = await self.repo.get_timetable_exception_by_slot_and_date(
            timetable_slot_id=body.timetable_slot_id,
            exception_date=body.exception_date,
        )
        if duplicate is not None:
            raise ConflictError(
                "An exception already exists for this slot on this date",
                error_code="ERR-ERP-409",
            )

        exception = await self.repo.create_timetable_exception(
            timetable_slot_id=body.timetable_slot_id,
            school_id=auth.school_id,
            exception_date=body.exception_date,
            exception_type=body.exception_type,
            substitute_teacher_id=body.substitute_teacher_id,
            new_room=body.new_room,
            reason=body.reason,
        )

        response = self._exception_to_response(exception)
        await self.audit.log_event(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            action_type="timetable_exception.create",
            target_type="timetable_exception",
            target_id=exception.id,
            outcome="success",
            entity_after=response,
            ip_address=ip_address,
        )
        return response

    async def list_timetable_exceptions(
        self,
        *,
        timetable_slot_id: uuid.UUID | None,
        date_from: date | None,
        date_to: date | None,
        exception_type: str | None,
        auth: AuthContext,
    ) -> list[dict]:
        exceptions = await self.repo.list_timetable_exceptions(
            school_id=auth.school_id,
            timetable_slot_id=timetable_slot_id,
            date_from=date_from,
            date_to=date_to,
            exception_type=exception_type,
        )
        return [self._exception_to_response(exception) for exception in exceptions]

    async def _build_weekly_timetable(
        self,
        *,
        school_id: uuid.UUID,
        target_date: date,
        class_id: uuid.UUID | None = None,
        teacher_id: uuid.UUID | None = None,
    ) -> dict:
        monday, sunday = self._week_bounds(target_date)

        slots = await self.repo.list_weekly_timetable_slots(
            school_id=school_id,
            monday=monday,
            sunday=sunday,
            class_id=class_id,
            teacher_id=teacher_id,
        )
        if not slots:
            return self._empty_weekly_payload(week_start=monday, week_end=sunday)

        slot_ids = [slot.id for slot in slots]
        exceptions = await self.repo.list_timetable_exceptions_for_slot_ids(
            slot_ids=slot_ids,
            monday=monday,
            sunday=sunday,
        )
        exception_map: dict[uuid.UUID, dict[date, TimetableException]] = {}
        for exception in exceptions:
            exception_map.setdefault(exception.timetable_slot_id, {})[
                exception.exception_date
            ] = exception

        class_map = {
            class_room.id: class_room.name
            for class_room in await self.repo.list_classes_by_ids(
                list({slot.class_id for slot in slots})
            )
        }

        weekly_slots = []
        for slot in slots:
            slot_date = monday + timedelta(days=slot.day_of_week)
            exception = exception_map.get(slot.id, {}).get(slot_date)
            weekly_slots.append(
                WeeklySlotResponse(
                    id=str(slot.id),
                    day_of_week=slot.day_of_week,
                    start_time=slot.start_time.strftime("%H:%M"),
                    end_time=slot.end_time.strftime("%H:%M"),
                    subject=slot.subject,
                    teacher_id=str(slot.teacher_id),
                    room=slot.room,
                    is_recurring=slot.is_recurring,
                    class_id=str(slot.class_id),
                    class_name=class_map.get(slot.class_id),
                    exception=(
                        TimetableExceptionResponse(
                            **self._exception_to_response(exception)
                        )
                        if exception
                        else None
                    ),
                ).model_dump()
            )

        return WeeklyTimetableResponse(
            academic_year_id=str(slots[0].academic_year_id) if slots else "",
            week_start=monday.isoformat(),
            week_end=sunday.isoformat(),
            slots=weekly_slots,
        ).model_dump()
