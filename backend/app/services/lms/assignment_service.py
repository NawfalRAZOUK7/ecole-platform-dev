"""Assignment, submission, and grading LMS service."""

from __future__ import annotations

import uuid
from typing import BinaryIO

from app.core.dependencies import AuthContext, verify_school_boundary
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.core.filtering import FilterSpec, SortSpec
from app.core.response import encode_cursor
from app.core.storage import storage, validate_mime_type
from app.core.unit_of_work import UnitOfWork
from app.repositories.lms import LMSRepository
from app.schemas.lms import (
    AssignmentCreateRequest,
    GradeRequest,
    SubmissionCreateRequest,
)
from app.services.audit import AuditService
from app.services.lms._helpers import (
    LMSServiceBase,
    MAX_FILES_PER_SUBMISSION,
    calculate_late_penalty,
    _utc_now,
)


class AssignmentService(LMSServiceBase):
    """Handles assignments, submissions, grades, and submission files."""

    async def create_assignment(
        self,
        *,
        body: AssignmentCreateRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        course = await self.repo.get_course(body.course_id)
        if course is None:
            raise NotFoundError("Course not found", error_code="ERR-LMS-404")
        verify_school_boundary(course.school_id, auth)

        if course.teacher_id != auth.user_id:
            raise AuthorizationError(
                "You can only create assignments for your own courses",
                error_code="ERR-AUTHZ-001",
            )

        async with UnitOfWork(self.db) as uow:
            repo = LMSRepository(uow.session)
            audit = AuditService(uow.session)
            assignment = await repo.create_assignment(
                course_id=body.course_id,
                teacher_id=auth.user_id,
                title=body.title,
                description=body.description,
                due_at=body.due_at,
                total_points=body.total_points,
                grace_period_hours=body.grace_period_hours,
                late_penalty_per_day=body.late_penalty_per_day,
                max_late_days=body.max_late_days,
                allow_late=body.allow_late,
                exercise_type=body.exercise_type,
                quiz_id=body.quiz_id,
            )
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="ASSIGNMENT_CREATED",
                outcome="success",
                target_type="assignment",
                target_id=assignment.id,
                entity_after={
                    "course_id": str(body.course_id),
                    "title": body.title,
                    "total_points": body.total_points,
                    "grace_period_hours": body.grace_period_hours,
                    "late_penalty_per_day": body.late_penalty_per_day,
                    "max_late_days": body.max_late_days,
                    "allow_late": body.allow_late,
                    "exercise_type": body.exercise_type,
                },
                ip_address=ip_address,
            )
            await uow.commit()

        await self._dispatch_assignment_created(
            assignment=assignment,
            course=course,
            actor_id=auth.user_id,
        )
        return self._assignment_to_dict(assignment)

    async def list_assignments(
        self,
        *,
        course_id: uuid.UUID | None,
        filters: FilterSpec,
        sort: SortSpec,
        search: str | None,
        cursor: str | None,
        limit: int,
        auth: AuthContext,
    ) -> tuple[list[dict], str | None, bool]:
        if course_id is not None:
            course = await self.repo.get_course(course_id)
            if course is None:
                raise NotFoundError("Course not found", error_code="ERR-LMS-404")
            verify_school_boundary(course.school_id, auth)

        assignments, has_more = await self.repo.list_assignments(
            school_id=auth.school_id,
            course_id=course_id,
            filters=filters,
            sort=sort,
            search=search,
            cursor=cursor,
            limit=limit,
        )
        items = [self._assignment_to_dict(assignment) for assignment in assignments]
        next_cursor = encode_cursor(assignments[-1].id) if has_more and assignments else None
        return items, next_cursor, has_more

    async def upload_exercise_pdf(
        self,
        *,
        assignment_id: uuid.UUID,
        file: BinaryIO,
        filename: str,
        mime_type: str,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        bundle = await self.repo.get_assignment_with_course(assignment_id)
        if bundle is None:
            raise NotFoundError("Assignment not found", error_code="ERR-LMS-404")
        assignment, course = bundle
        verify_school_boundary(course.school_id, auth)

        if course.teacher_id != auth.user_id:
            raise AuthorizationError(
                "You can only upload PDFs for your own assignments",
                error_code="ERR-AUTHZ-001",
            )
        if assignment.exercise_type != "PRINTABLE_PDF":
            raise ValidationError(
                "Exercise PDF upload is only allowed for PRINTABLE_PDF assignments",
                error_code="ERR-LMS-422",
            )
        if mime_type != "application/pdf":
            raise ValidationError(
                "Only PDF files are accepted for exercise upload",
                error_code="ERR-UPLOAD-415",
            )

        if assignment.exercise_pdf_path:
            await storage.delete(assignment.exercise_pdf_path)

        relative_path, checksum, file_size = await storage.save(
            file,
            filename or "exercise.pdf",
            subdirectory=f"exercises/{assignment_id}",
        )
        async with UnitOfWork(self.db) as uow:
            repo = LMSRepository(uow.session)
            audit = AuditService(uow.session)
            assignment.exercise_pdf_path = relative_path
            await repo.save_assignment(assignment)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="EXERCISE_PDF_UPLOADED",
                outcome="success",
                target_type="assignment",
                target_id=assignment.id,
                entity_after={
                    "exercise_pdf_path": relative_path,
                    "checksum": checksum,
                    "file_size": file_size,
                },
                ip_address=ip_address,
            )
            await uow.commit()

        return {
            "id": str(assignment.id),
            "exercise_pdf_path": relative_path,
            "checksum": checksum,
            "file_size": file_size,
        }

    async def create_submission(
        self,
        *,
        body: SubmissionCreateRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        bundle = await self.repo.get_assignment_with_course(body.assignment_id)
        if bundle is None:
            raise NotFoundError("Assignment not found", error_code="ERR-LMS-404")
        assignment, course = bundle
        verify_school_boundary(course.school_id, auth)

        existing = await self.repo.find_active_submission(
            assignment_id=body.assignment_id,
            student_id=auth.user_id,
        )
        if existing is not None:
            return self._submission_to_dict(existing)

        now = _utc_now()
        is_pdf_exercise = assignment.exercise_type == "PRINTABLE_PDF"
        initial_status = "draft" if is_pdf_exercise else "submitted"
        async with UnitOfWork(self.db) as uow:
            repo = LMSRepository(uow.session)
            audit = AuditService(uow.session)
            submission = await repo.create_submission(
                assignment_id=body.assignment_id,
                student_id=auth.user_id,
                status=initial_status,
                submitted_at=None if is_pdf_exercise else now,
            )
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="SUBMISSION_CREATED",
                outcome="success",
                target_type="submission",
                target_id=submission.id,
                entity_after={
                    "assignment_id": str(body.assignment_id),
                    "status": initial_status,
                },
                ip_address=ip_address,
            )
            await uow.commit()

        if initial_status == "submitted":
            await self._dispatch_submission_received(
                submission=submission,
                assignment=assignment,
                course=course,
                actor_id=auth.user_id,
            )
        return self._submission_to_dict(submission)

    async def grade_submission(
        self,
        *,
        submission_id: uuid.UUID,
        body: GradeRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        bundle = await self.repo.get_submission_with_context(submission_id)
        if bundle is None:
            raise NotFoundError("Submission not found", error_code="ERR-LMS-404")
        submission, assignment, course = bundle
        verify_school_boundary(course.school_id, auth)

        if course.teacher_id != auth.user_id:
            raise AuthorizationError(
                "You can only grade submissions for your own courses",
                error_code="ERR-AUTHZ-001",
            )
        if assignment.rubric_id is not None:
            raise ValidationError(
                "This assignment uses rubric grading. Use /submissions/{id}/grade-rubric instead.",
                error_code="ERR-LMS-422",
            )
        if submission.status not in ("submitted", "graded"):
            raise ValidationError(
                "Submission must be in submitted or graded status to be graded",
                error_code="ERR-LMS-422",
            )
        if assignment.total_points > 0 and body.score > assignment.total_points:
            raise ValidationError(
                f"Score cannot exceed total points ({assignment.total_points})",
                error_code="ERR-LMS-422",
            )

        penalty_data = calculate_late_penalty(
            assignment=assignment,
            submission=submission,
            original_score=float(body.score),
        )
        published_at = _utc_now() if body.publish else None
        async with UnitOfWork(self.db) as uow:
            repo = LMSRepository(uow.session)
            audit = AuditService(uow.session)
            grade = await repo.get_grade_for_submission(submission_id)

            if grade is not None:
                grade.score = penalty_data["adjusted_score"]
                grade.original_score = penalty_data["original_score"]
                grade.late_penalty = penalty_data["late_penalty"]
                grade.late_days = penalty_data["late_days"]
                grade.penalty_overridden = False
                grade.feedback_text = body.feedback_text
                if body.publish:
                    grade.published_at = published_at
                await repo.save_grade(grade)
            else:
                grade = await repo.create_grade(
                    submission_id=submission_id,
                    teacher_id=auth.user_id,
                    score=penalty_data["adjusted_score"],
                    original_score=penalty_data["original_score"],
                    late_penalty=penalty_data["late_penalty"],
                    late_days=penalty_data["late_days"],
                    penalty_overridden=False,
                    feedback_text=body.feedback_text,
                    published_at=published_at,
                )

            submission.status = "graded"
            await repo.save_submission(submission)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="SUBMISSION_GRADED",
                outcome="success",
                target_type="grade",
                target_id=grade.id,
                entity_after={
                    "submission_id": str(submission_id),
                    "score": float(penalty_data["adjusted_score"]),
                    "original_score": float(penalty_data["original_score"]),
                    "late_penalty": float(penalty_data["late_penalty"]),
                    "late_days": int(penalty_data["late_days"]),
                    "published": body.publish,
                },
                ip_address=ip_address,
            )
            await uow.commit()

        if body.publish:
            await self._dispatch_grade_published(
                grade=grade,
                submission=submission,
                assignment=assignment,
                course=course,
                actor_id=auth.user_id,
                score=float(penalty_data["adjusted_score"]),
                feedback_text=body.feedback_text,
            )
        return self._grade_to_dict(grade)

    async def override_late_penalty(
        self,
        *,
        submission_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        bundle = await self.repo.get_submission_with_context(submission_id)
        if bundle is None:
            raise NotFoundError("Submission not found", error_code="ERR-LMS-404")
        submission, _assignment, course = bundle
        verify_school_boundary(course.school_id, auth)

        if course.teacher_id != auth.user_id:
            raise AuthorizationError(
                "You can only override penalties for your own courses",
                error_code="ERR-AUTHZ-001",
            )

        grade = await self.repo.get_grade_for_submission(submission_id)
        if grade is None:
            raise NotFoundError("Grade not found", error_code="ERR-LMS-404")
        if grade.original_score is None or float(grade.late_penalty or 0.0) <= 0:
            raise ValidationError(
                "This grade does not have a late penalty to override",
                error_code="ERR-LMS-422",
            )
        if grade.penalty_overridden:
            return self._grade_to_dict(grade)

        async with UnitOfWork(self.db) as uow:
            repo = LMSRepository(uow.session)
            audit = AuditService(uow.session)
            grade.score = float(grade.original_score)
            grade.penalty_overridden = True
            await repo.save_grade(grade)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="LATE_PENALTY_OVERRIDDEN",
                outcome="success",
                target_type="grade",
                target_id=grade.id,
                entity_after={
                    "submission_id": str(submission_id),
                    "restored_score": float(grade.score),
                    "late_penalty": float(grade.late_penalty),
                    "late_days": int(grade.late_days),
                },
                ip_address=ip_address,
            )
            await uow.commit()

        return self._grade_to_dict(grade)

    async def upload_submission_file(
        self,
        *,
        submission_id: uuid.UUID,
        file: BinaryIO,
        filename: str,
        mime_type: str,
        file_type_hint: str | None,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        bundle = await self.repo.get_submission_with_context(submission_id)
        if bundle is None:
            raise NotFoundError("Submission not found", error_code="ERR-LMS-404")
        submission, _assignment, course = bundle

        if submission.student_id != auth.user_id:
            raise NotFoundError("Submission not found", error_code="ERR-LMS-404")
        verify_school_boundary(course.school_id, auth)

        if submission.status not in ("draft", "submitted"):
            raise ValidationError(
                "Cannot upload files to a graded or returned submission",
                error_code="ERR-LMS-422",
            )

        current_count = await self.repo.count_submission_files(submission_id)
        if current_count >= MAX_FILES_PER_SUBMISSION:
            raise ValidationError(
                f"Maximum of {MAX_FILES_PER_SUBMISSION} files per submission",
                error_code="ERR-UPLOAD-422",
            )

        valid_hints = {"SOLUTION_SCAN", "SOLUTION_PHOTO", "DOCUMENT"}
        if file_type_hint and file_type_hint not in valid_hints:
            raise ValidationError(
                f"file_type_hint must be one of: {', '.join(sorted(valid_hints))}",
                error_code="ERR-LMS-422",
            )

        validate_mime_type(mime_type)
        relative_path, checksum, file_size = await storage.save(
            file,
            filename or "upload",
            subdirectory=f"submissions/{submission_id}",
        )
        async with UnitOfWork(self.db) as uow:
            repo = LMSRepository(uow.session)
            audit = AuditService(uow.session)
            submission_file = await repo.create_submission_file(
                submission_id=submission_id,
                file_path=relative_path,
                checksum=checksum,
                mime_type=mime_type,
                file_size=file_size,
                file_type_hint=file_type_hint,
            )
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="SUBMISSION_FILE_UPLOADED",
                outcome="success",
                target_type="submission_file",
                target_id=submission_file.id,
                entity_after={
                    "submission_id": str(submission_id),
                    "file_path": relative_path,
                    "mime_type": mime_type,
                    "file_size": file_size,
                    "checksum": checksum,
                    "file_type_hint": file_type_hint,
                },
                ip_address=ip_address,
            )
            await uow.commit()

        return {
            "id": str(submission_file.id),
            "submission_id": str(submission_file.submission_id),
            "file_path": submission_file.file_path,
            "checksum": submission_file.checksum,
            "mime_type": submission_file.mime_type,
            "file_size": submission_file.file_size,
            "file_type_hint": submission_file.file_type_hint,
        }

    async def finalize_submission(
        self,
        *,
        submission_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        bundle = await self.repo.get_submission_with_context(submission_id)
        if bundle is None:
            raise NotFoundError("Submission not found", error_code="ERR-LMS-404")
        submission, assignment, course = bundle

        if submission.student_id != auth.user_id:
            raise NotFoundError("Submission not found", error_code="ERR-LMS-404")
        verify_school_boundary(course.school_id, auth)

        if submission.status != "draft":
            raise ValidationError(
                "Only draft submissions can be finalized",
                error_code="ERR-LMS-422",
            )
        if assignment.exercise_type == "PRINTABLE_PDF":
            file_count = await self.repo.count_submission_files(submission_id)
            if file_count == 0:
                raise ValidationError(
                    "PRINTABLE_PDF submissions require at least one uploaded solution file",
                    error_code="ERR-LMS-422",
                )

        async with UnitOfWork(self.db) as uow:
            repo = LMSRepository(uow.session)
            audit = AuditService(uow.session)
            submission.status = "submitted"
            submission.submitted_at = _utc_now()
            await repo.save_submission(submission)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="SUBMISSION_FINALIZED",
                outcome="success",
                target_type="submission",
                target_id=submission.id,
                entity_after={
                    "assignment_id": str(submission.assignment_id),
                    "status": "submitted",
                    "exercise_type": assignment.exercise_type,
                },
                ip_address=ip_address,
            )
            await uow.commit()

        await self._dispatch_submission_received(
            submission=submission,
            assignment=assignment,
            course=course,
            actor_id=auth.user_id,
        )
        return self._submission_to_dict(submission)
