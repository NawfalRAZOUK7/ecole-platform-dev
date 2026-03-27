"""Service layer for LMS content, courses, assignments, submissions, assessments, and quizzes."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import BinaryIO

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    AuthContext,
    verify_parent_child_ownership,
    verify_school_boundary,
    verify_teacher_assignment,
)
from app.core.exceptions import AuthorizationError, ConflictError, NotFoundError, ValidationError
from app.core.filtering import FilterSpec, SortSpec
from app.core.response import encode_cursor
from app.core.storage import storage, validate_mime_type
from app.models.lms import (
    Assessment,
    Assignment,
    ContentItem,
    ContentItemAsset,
    ContentProgress,
    ContentSubmission,
    Course,
    Grade,
    Quiz,
    QuizAttempt,
    QuizQuestion,
    QuizResponse,
    Submission,
    SubmissionFile,
)
from app.repositories.lms import LMSRepository
from app.repositories.quiz import QuizRepository
from app.schemas.cms import ContentAssignRequest, ContentSubmitForReviewRequest
from app.schemas.lms import (
    AssessmentCreateRequest,
    AssessmentResultSubmitRequest,
    AssignmentCreateRequest,
    ContentProgressRequest,
    CourseCreateRequest,
    GradeRequest,
    SubmissionCreateRequest,
)
from app.schemas.quiz import QuizCreateRequest, QuizRespondRequest, QuizUpdateRequest
from app.services.audit import AuditService
from app.services.quiz_grading import grade_attempt
from app.services.realtime import publish_grade_published

MAX_FILES_PER_SUBMISSION = 5


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class LMSService:
    """Business logic for LMS and quiz workflows."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = LMSRepository(db)
        self.quiz_repo = QuizRepository(db)
        self.audit = AuditService(db)

    def _course_to_dict(self, course: Course) -> dict:
        return {
            "id": str(course.id),
            "school_id": str(course.school_id),
            "class_id": str(course.class_id),
            "teacher_id": str(course.teacher_id),
            "title": course.title,
            "description": course.description,
            "status": course.status,
        }

    def _assignment_to_dict(self, assignment: Assignment) -> dict:
        return {
            "id": str(assignment.id),
            "course_id": str(assignment.course_id),
            "teacher_id": str(assignment.teacher_id),
            "title": assignment.title,
            "description": assignment.description,
            "due_at": assignment.due_at.isoformat() if assignment.due_at else None,
            "total_points": assignment.total_points,
            "exercise_type": assignment.exercise_type,
            "quiz_id": str(assignment.quiz_id) if assignment.quiz_id else None,
            "exercise_pdf_path": assignment.exercise_pdf_path,
        }

    def _submission_to_dict(self, submission: Submission) -> dict:
        return {
            "id": str(submission.id),
            "assignment_id": str(submission.assignment_id),
            "student_id": str(submission.student_id),
            "status": submission.status,
            "submitted_at": submission.submitted_at.isoformat()
            if submission.submitted_at
            else None,
        }

    def _grade_to_dict(self, grade: Grade) -> dict:
        return {
            "id": str(grade.id),
            "submission_id": str(grade.submission_id),
            "teacher_id": str(grade.teacher_id),
            "score": float(grade.score),
            "feedback_text": grade.feedback_text,
            "published_at": grade.published_at.isoformat()
            if grade.published_at
            else None,
        }

    def _content_item_to_dict(self, content_item: ContentItem) -> dict:
        return {
            "id": str(content_item.id),
            "school_id": str(content_item.school_id) if content_item.school_id else None,
            "title": content_item.title,
            "content_type": content_item.content_type,
            "level_band": content_item.level_band,
            "language": content_item.language,
            "status": content_item.status,
        }

    def _assessment_to_dict(self, assessment: Assessment) -> dict:
        return {
            "id": str(assessment.id),
            "class_id": str(assessment.class_id),
            "teacher_id": str(assessment.teacher_id),
            "title": assessment.title,
            "due_at": assessment.due_at.isoformat() if assessment.due_at else None,
            "window_end": assessment.window_end.isoformat()
            if assessment.window_end
            else None,
            "total_points": assessment.total_points,
            "status": assessment.status,
        }

    def _quiz_to_dict(
        self,
        quiz: Quiz,
        questions: list[QuizQuestion] | None = None,
    ) -> dict:
        total_points = sum(question.points for question in (questions or []))
        return {
            "id": str(quiz.id),
            "school_id": str(quiz.school_id) if quiz.school_id else None,
            "created_by": str(quiz.created_by),
            "title": quiz.title,
            "description": quiz.description,
            "subject": quiz.subject,
            "level_band": quiz.level_band,
            "difficulty": quiz.difficulty,
            "time_limit_minutes": quiz.time_limit_minutes,
            "max_attempts": quiz.max_attempts,
            "shuffle_questions": quiz.shuffle_questions,
            "status": quiz.status,
            "total_points": total_points,
            "question_count": len(questions or []),
        }

    def _quiz_question_to_dict(
        self,
        question: QuizQuestion,
        *,
        include_answer: bool = False,
    ) -> dict:
        payload = {
            "id": str(question.id),
            "question_type": question.question_type,
            "question_text": question.question_text,
            "question_media_path": question.question_media_path,
            "options": question.options,
            "points": question.points,
            "order": question.order,
            "explanation": question.explanation if include_answer else None,
        }
        if include_answer:
            payload["correct_answer"] = question.correct_answer
        return payload

    def _attempt_to_dict(self, attempt: QuizAttempt) -> dict:
        return {
            "id": str(attempt.id),
            "quiz_id": str(attempt.quiz_id),
            "student_id": str(attempt.student_id),
            "attempt_no": attempt.attempt_no,
            "started_at": attempt.started_at.isoformat() if attempt.started_at else None,
            "completed_at": attempt.completed_at.isoformat()
            if attempt.completed_at
            else None,
            "score": float(attempt.score) if attempt.score is not None else None,
            "max_score": attempt.max_score,
            "status": attempt.status,
        }

    async def create_course(
        self,
        *,
        body: CourseCreateRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        class_room = await self.repo.get_class(body.class_id)
        if class_room is None:
            raise NotFoundError("Class not found", error_code="ERR-LMS-404")
        verify_school_boundary(class_room.school_id, auth)

        teacher_classes = await self.repo.list_teacher_class_ids(
            teacher_id=auth.user_id,
            school_id=auth.school_id,
        )
        verify_teacher_assignment(body.class_id, teacher_classes)

        course = await self.repo.create_course(
            school_id=auth.school_id,
            class_id=body.class_id,
            teacher_id=auth.user_id,
            title=body.title,
            description=body.description,
            status=body.status,
        )

        await self.audit.log_event(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            action_type="COURSE_CREATED",
            outcome="success",
            target_type="course",
            target_id=course.id,
            entity_after={
                "class_id": str(body.class_id),
                "title": body.title,
                "status": body.status,
            },
            ip_address=ip_address,
        )

        return self._course_to_dict(course)

    async def list_courses(
        self,
        *,
        class_id: uuid.UUID | None,
        filters: FilterSpec,
        sort: SortSpec,
        search: str | None,
        cursor: str | None,
        limit: int,
        auth: AuthContext,
    ) -> tuple[list[dict], str | None, bool]:
        teacher_class_ids: set[uuid.UUID] | None = None
        if auth.role == "TCH":
            teacher_class_ids = await self.repo.list_teacher_class_ids(
                teacher_id=auth.user_id,
                school_id=auth.school_id,
            )

        courses, has_more = await self.repo.list_courses(
            school_id=auth.school_id,
            class_id=class_id,
            teacher_class_ids=teacher_class_ids,
            filters=filters,
            sort=sort,
            search=search,
            cursor=cursor,
            limit=limit,
        )
        items = [self._course_to_dict(course) for course in courses]
        next_cursor = encode_cursor(courses[-1].id) if has_more and courses else None
        return items, next_cursor, has_more

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

        assignment = await self.repo.create_assignment(
            course_id=body.course_id,
            teacher_id=auth.user_id,
            title=body.title,
            description=body.description,
            due_at=body.due_at,
            total_points=body.total_points,
            exercise_type=body.exercise_type,
            quiz_id=body.quiz_id,
        )

        await self.audit.log_event(
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
                "exercise_type": body.exercise_type,
            },
            ip_address=ip_address,
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
        next_cursor = (
            encode_cursor(assignments[-1].id) if has_more and assignments else None
        )
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
        assignment.exercise_pdf_path = relative_path
        await self.repo.save_assignment(assignment)

        await self.audit.log_event(
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

        return {
            "id": str(assignment.id),
            "exercise_pdf_path": relative_path,
            "checksum": checksum,
            "file_size": file_size,
        }

    async def get_exercise_pdf(
        self,
        *,
        assignment_id: uuid.UUID,
        auth: AuthContext,
    ) -> tuple[str, str, str]:
        bundle = await self.repo.get_assignment_with_course(assignment_id)
        if bundle is None:
            raise NotFoundError("Assignment not found", error_code="ERR-LMS-404")
        assignment, course = bundle

        if not assignment.exercise_pdf_path:
            raise NotFoundError("No exercise PDF attached", error_code="ERR-LMS-404")

        verify_school_boundary(course.school_id, auth)

        if auth.role == "TCH":
            if course.teacher_id != auth.user_id:
                raise NotFoundError("Assignment not found", error_code="ERR-LMS-404")
        elif auth.role == "STD":
            enrolled = await self.repo.student_is_enrolled_in_class(
                student_id=auth.user_id,
                class_id=course.class_id,
            )
            if not enrolled:
                raise NotFoundError("Assignment not found", error_code="ERR-LMS-404")

        abs_path = await storage.read(assignment.exercise_pdf_path)
        return str(abs_path), "application/pdf", f"exercise_{assignment_id}.pdf"

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
        submission = await self.repo.create_submission(
            assignment_id=body.assignment_id,
            student_id=auth.user_id,
            status=initial_status,
            submitted_at=None if is_pdf_exercise else now,
        )

        await self.audit.log_event(
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

        grade = await self.repo.get_grade_for_submission(submission_id)
        published_at = _utc_now() if body.publish else None

        if grade is not None:
            grade.score = body.score
            grade.feedback_text = body.feedback_text
            if body.publish:
                grade.published_at = published_at
            await self.repo.save_grade(grade)
        else:
            grade = await self.repo.create_grade(
                submission_id=submission_id,
                teacher_id=auth.user_id,
                score=body.score,
                feedback_text=body.feedback_text,
                published_at=published_at,
            )

        submission.status = "graded"
        await self.repo.save_submission(submission)

        await self.audit.log_event(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            action_type="SUBMISSION_GRADED",
            outcome="success",
            target_type="grade",
            target_id=grade.id,
            entity_after={
                "submission_id": str(submission_id),
                "score": float(body.score),
                "published": body.publish,
            },
            ip_address=ip_address,
        )

        if body.publish:
            await publish_grade_published(
                student_id=submission.student_id,
                grade_id=grade.id,
                submission_id=submission_id,
                score=float(body.score),
                assignment_title=assignment.title,
            )
            try:
                from app.core.tasks import enqueue_email

                student = await self.repo.get_user(submission.student_id)
                student_name = None
                if student is not None:
                    student_name = getattr(student, "first_name", None) or getattr(
                        student, "full_name", None
                    )
                if student and student.email:
                    await enqueue_email(
                        to=student.email,
                        template_name="grade_published",
                        lang="fr",
                        student_name=student_name or student.email,
                        assignment_title=assignment.title,
                        score=float(body.score),
                        total_points=float(assignment.total_points),
                        feedback=body.feedback_text,
                    )
            except Exception:
                pass

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
        submission, assignment, course = bundle

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
        submission_file = await self.repo.create_submission_file(
            submission_id=submission_id,
            file_path=relative_path,
            checksum=checksum,
            mime_type=mime_type,
            file_size=file_size,
            file_type_hint=file_type_hint,
        )

        await self.audit.log_event(
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

        return {
            "id": str(submission_file.id),
            "submission_id": str(submission_file.submission_id),
            "file_path": submission_file.file_path,
            "checksum": submission_file.checksum,
            "mime_type": submission_file.mime_type,
            "file_size": submission_file.file_size,
            "file_type_hint": submission_file.file_type_hint,
        }

    async def get_submission_file(
        self,
        *,
        submission_id: uuid.UUID,
        file_id: uuid.UUID,
        auth: AuthContext,
    ) -> tuple[str, str, str]:
        submission_file = await self.repo.get_submission_file(
            submission_id=submission_id,
            file_id=file_id,
        )
        if submission_file is None:
            raise NotFoundError("File not found", error_code="ERR-UPLOAD-404")

        bundle = await self.repo.get_submission_with_context(submission_id)
        if bundle is None:
            raise NotFoundError("Submission not found", error_code="ERR-LMS-404")
        submission, _assignment, course = bundle
        verify_school_boundary(course.school_id, auth)

        if auth.role == "STD" and submission.student_id != auth.user_id:
            raise NotFoundError("File not found", error_code="ERR-UPLOAD-404")
        if auth.role == "TCH" and course.teacher_id != auth.user_id:
            raise NotFoundError("File not found", error_code="ERR-UPLOAD-404")

        abs_path = await storage.read(submission_file.file_path)
        return (
            str(abs_path),
            submission_file.mime_type or "application/octet-stream",
            abs_path.name,
        )

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

        submission.status = "submitted"
        submission.submitted_at = _utc_now()
        await self.repo.save_submission(submission)

        await self.audit.log_event(
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

        return self._submission_to_dict(submission)

    async def preview_submission_files(
        self,
        *,
        submission_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict:
        bundle = await self.repo.get_submission_with_context(submission_id)
        if bundle is None:
            raise NotFoundError("Submission not found", error_code="ERR-LMS-404")
        submission, assignment, course = bundle
        verify_school_boundary(course.school_id, auth)

        if auth.role == "TCH" and course.teacher_id != auth.user_id:
            raise NotFoundError("Submission not found", error_code="ERR-LMS-404")

        files = await self.repo.list_submission_files(submission_id)
        items = []
        for file in files:
            mime_type = file.mime_type or ""
            is_previewable = mime_type.startswith("image/") or mime_type == "application/pdf"
            items.append(
                {
                    "id": str(file.id),
                    "file_path": file.file_path,
                    "mime_type": file.mime_type,
                    "file_size": file.file_size,
                    "file_type_hint": file.file_type_hint,
                    "checksum": file.checksum,
                    "is_previewable": is_previewable,
                    "download_url": f"/api/v1/submissions/{submission_id}/files/{file.id}",
                }
            )

        return {
            "submission_id": str(submission_id),
            "assignment_id": str(submission.assignment_id),
            "student_id": str(submission.student_id),
            "status": submission.status,
            "exercise_type": assignment.exercise_type,
            "files": items,
        }

    async def list_content_items(
        self,
        *,
        content_type: str | None,
        level_band: str | None,
        language: str | None,
        filters: FilterSpec,
        sort: SortSpec,
        search: str | None,
        cursor: str | None,
        limit: int,
        auth: AuthContext,
    ) -> tuple[list[dict], str | None, bool]:
        items_list, has_more = await self.repo.list_content_items(
            school_id=auth.school_id,
            content_type=content_type,
            level_band=level_band,
            language=language,
            filters=filters,
            sort=sort,
            search=search,
            cursor=cursor,
            limit=limit,
        )
        items = [self._content_item_to_dict(item) for item in items_list]
        next_cursor = encode_cursor(items_list[-1].id) if has_more and items_list else None
        return items, next_cursor, has_more

    async def get_content_item(
        self,
        *,
        content_item_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict:
        content_item = await self.repo.get_content_item(content_item_id)
        if content_item is None:
            raise NotFoundError("Content item not found", error_code="ERR-LMS-404")

        if content_item.school_id is not None:
            verify_school_boundary(content_item.school_id, auth)
        if content_item.status != "published":
            raise NotFoundError("Content item not found", error_code="ERR-LMS-404")

        return self._content_item_to_dict(content_item)

    async def update_content_progress(
        self,
        *,
        content_item_id: uuid.UUID,
        body: ContentProgressRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        content_item = await self.repo.get_content_item(content_item_id)
        if content_item is None:
            raise NotFoundError("Content item not found", error_code="ERR-LMS-404")

        if content_item.school_id is not None:
            verify_school_boundary(content_item.school_id, auth)

        progress = await self.repo.get_content_progress(
            student_id=auth.user_id,
            content_item_id=content_item_id,
        )
        if progress is not None:
            progress.status = body.status
            await self.repo.save_content_progress(progress)
        else:
            progress = await self.repo.create_content_progress(
                student_id=auth.user_id,
                content_item_id=content_item_id,
                status=body.status,
            )

        await self.audit.log_event(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            action_type="CONTENT_PROGRESS_UPDATED",
            outcome="success",
            target_type="content_progress",
            target_id=progress.id,
            entity_after={
                "content_item_id": str(content_item_id),
                "status": body.status,
            },
            ip_address=ip_address,
        )

        return {
            "id": str(progress.id),
            "student_id": str(progress.student_id),
            "content_item_id": str(progress.content_item_id),
            "status": progress.status,
        }

    async def upload_content_asset(
        self,
        *,
        content_item_id: uuid.UUID,
        file: BinaryIO,
        filename: str,
        mime_type: str,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        content_item = await self.repo.get_content_item(content_item_id)
        if content_item is None:
            raise NotFoundError("Content item not found", error_code="ERR-LMS-404")

        if content_item.school_id is not None:
            verify_school_boundary(content_item.school_id, auth)

        validate_mime_type(mime_type)
        relative_path, checksum, file_size = await storage.save(
            file,
            filename or "asset",
            subdirectory=f"content/{content_item_id}",
        )
        asset = await self.repo.create_content_asset(
            content_item_id=content_item_id,
            file_path=relative_path,
            checksum=checksum,
            mime_type=mime_type,
            file_size=file_size,
        )

        await self.audit.log_event(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            action_type="CONTENT_ASSET_UPLOADED",
            outcome="success",
            target_type="content_item_asset",
            target_id=asset.id,
            entity_after={
                "content_item_id": str(content_item_id),
                "file_path": relative_path,
                "mime_type": mime_type,
                "file_size": file_size,
                "checksum": checksum,
            },
            ip_address=ip_address,
        )

        return {
            "id": str(asset.id),
            "content_item_id": str(asset.content_item_id),
            "file_path": asset.file_path,
            "checksum": asset.checksum,
            "mime_type": asset.mime_type,
            "file_size": asset.file_size,
        }

    async def get_content_asset(
        self,
        *,
        content_item_id: uuid.UUID,
        asset_id: uuid.UUID,
        auth: AuthContext,
    ) -> tuple[str, str, str]:
        asset = await self.repo.get_content_asset(
            content_item_id=content_item_id,
            asset_id=asset_id,
        )
        if asset is None:
            raise NotFoundError("Asset not found", error_code="ERR-UPLOAD-404")

        content_item = await self.repo.get_content_item(content_item_id)
        if content_item is None:
            raise NotFoundError("Content item not found", error_code="ERR-LMS-404")

        if content_item.school_id is not None:
            verify_school_boundary(content_item.school_id, auth)

        abs_path = await storage.read(asset.file_path)
        return str(abs_path), asset.mime_type or "application/octet-stream", abs_path.name

    async def delete_content_asset(
        self,
        *,
        content_item_id: uuid.UUID,
        asset_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        asset = await self.repo.get_content_asset(
            content_item_id=content_item_id,
            asset_id=asset_id,
        )
        if asset is None:
            raise NotFoundError("Asset not found", error_code="ERR-UPLOAD-404")

        content_item = await self.repo.get_content_item(content_item_id)
        if content_item is None:
            raise NotFoundError("Content item not found", error_code="ERR-LMS-404")

        if content_item.school_id is not None:
            verify_school_boundary(content_item.school_id, auth)

        await storage.delete(asset.file_path)
        entity_before = {
            "id": str(asset.id),
            "file_path": asset.file_path,
            "mime_type": asset.mime_type,
            "file_size": asset.file_size,
        }
        await self.repo.delete_content_asset(asset)

        await self.audit.log_event(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            action_type="CONTENT_ASSET_DELETED",
            outcome="success",
            target_type="content_item_asset",
            target_id=asset.id,
            entity_before=entity_before,
            ip_address=ip_address,
        )

        return {"deleted": True, "id": entity_before["id"]}

    async def browse_content_library(
        self,
        *,
        content_type: str | None,
        level_band: str | None,
        subject: str | None,
        language: str | None,
        origin: str | None,
        cursor: str | None,
        limit: int,
        auth: AuthContext,
    ) -> tuple[list[dict], str | None, bool]:
        items_list, has_more = await self.repo.browse_content_library(
            school_id=auth.school_id,
            content_type=content_type,
            level_band=level_band,
            subject=subject,
            language=language,
            origin=origin,
            cursor=cursor,
            limit=limit,
        )
        items = [
            {
                "id": str(content_item.id),
                "school_id": str(content_item.school_id)
                if content_item.school_id
                else None,
                "title": content_item.title,
                "content_type": content_item.content_type,
                "level_band": content_item.level_band,
                "language": content_item.language,
                "subject": content_item.subject,
                "description": content_item.description,
                "origin": content_item.origin,
                "status": content_item.status,
            }
            for content_item in items_list
        ]
        next_cursor = encode_cursor(items_list[-1].id) if has_more and items_list else None
        return items, next_cursor, has_more

    async def assign_content_to_class(
        self,
        *,
        body: ContentAssignRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        teacher_classes = await self.repo.list_teacher_class_ids(
            teacher_id=auth.user_id,
            school_id=auth.school_id,
        )
        verify_teacher_assignment(body.class_id, teacher_classes)

        content_item = await self.repo.get_content_item(body.content_item_id)
        if content_item is None or content_item.status != "published":
            raise NotFoundError("Content item not found", error_code="ERR-CMS-404")
        if content_item.school_id is not None and content_item.school_id != auth.school_id:
            raise NotFoundError("Content item not found", error_code="ERR-CMS-404")

        duplicate = await self.repo.find_class_content_assignment(
            class_id=body.class_id,
            content_item_id=body.content_item_id,
        )
        if duplicate is not None:
            raise ValidationError(
                "Content already assigned to this class",
                error_code="ERR-CMS-409",
            )

        assignment = await self.repo.create_class_content_assignment(
            teacher_id=auth.user_id,
            class_id=body.class_id,
            content_item_id=body.content_item_id,
            school_id=auth.school_id,
            assigned_at=_utc_now(),
            notes=body.notes,
        )

        await self.audit.log_event(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            action_type="CONTENT_ASSIGNED_TO_CLASS",
            outcome="success",
            target_type="class_content_assignment",
            target_id=assignment.id,
            entity_after={
                "class_id": str(body.class_id),
                "content_item_id": str(body.content_item_id),
            },
            ip_address=ip_address,
        )

        return {
            "id": str(assignment.id),
            "teacher_id": str(assignment.teacher_id),
            "class_id": str(assignment.class_id),
            "content_item_id": str(assignment.content_item_id),
            "school_id": str(assignment.school_id),
            "assigned_at": assignment.assigned_at.isoformat(),
            "notes": assignment.notes,
        }

    async def unassign_content(
        self,
        *,
        assignment_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        assignment = await self.repo.get_class_content_assignment(assignment_id)
        if assignment is None:
            raise NotFoundError("Assignment not found", error_code="ERR-CMS-404")

        verify_school_boundary(assignment.school_id, auth)
        teacher_classes = await self.repo.list_teacher_class_ids(
            teacher_id=auth.user_id,
            school_id=auth.school_id,
        )
        verify_teacher_assignment(assignment.class_id, teacher_classes)

        entity_before = {
            "id": str(assignment.id),
            "class_id": str(assignment.class_id),
            "content_item_id": str(assignment.content_item_id),
        }
        await self.repo.delete_class_content_assignment(assignment)

        await self.audit.log_event(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            action_type="CONTENT_UNASSIGNED_FROM_CLASS",
            outcome="success",
            target_type="class_content_assignment",
            target_id=assignment.id,
            entity_before=entity_before,
            ip_address=ip_address,
        )

        return {"deleted": True, "id": entity_before["id"]}

    async def submit_content_for_review(
        self,
        *,
        body: ContentSubmitForReviewRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        content_item = await self.repo.get_content_item(body.content_item_id)
        if content_item is None:
            raise NotFoundError("Content item not found", error_code="ERR-CMS-404")
        if content_item.school_id is None:
            raise ValidationError(
                "Platform-wide content cannot be submitted for review",
                error_code="ERR-CMS-400",
            )
        verify_school_boundary(content_item.school_id, auth)

        existing = await self.repo.find_active_content_submission(
            content_item_id=body.content_item_id,
            submitted_by=auth.user_id,
        )
        if existing is not None:
            raise ValidationError(
                "A submission for this content is already pending review",
                error_code="ERR-CMS-409",
            )

        submission = await self.repo.create_content_submission(
            content_item_id=body.content_item_id,
            submitted_by=auth.user_id,
            school_id=auth.school_id,
            status="PENDING",
            submitted_at=_utc_now(),
        )

        await self.audit.log_event(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            action_type="CONTENT_SUBMITTED_FOR_REVIEW",
            outcome="success",
            target_type="content_submission",
            target_id=submission.id,
            entity_after={
                "content_item_id": str(body.content_item_id),
                "status": "PENDING",
            },
            ip_address=ip_address,
        )

        return {
            "id": str(submission.id),
            "content_item_id": str(submission.content_item_id),
            "status": submission.status,
            "submitted_at": submission.submitted_at.isoformat()
            if submission.submitted_at
            else None,
        }

    async def list_my_content_submissions(
        self,
        *,
        status: str | None,
        cursor: str | None,
        limit: int,
        auth: AuthContext,
    ) -> tuple[list[dict], str | None, bool]:
        rows, has_more = await self.repo.list_my_content_submissions(
            submitted_by=auth.user_id,
            status=status,
            cursor=cursor,
            limit=limit,
        )
        items = [
            {
                "id": str(submission.id),
                "content_item_id": str(submission.content_item_id),
                "content_title": content_item.title,
                "status": submission.status,
                "submitted_at": submission.submitted_at.isoformat()
                if submission.submitted_at
                else None,
                "review_notes": submission.review_notes,
                "promoted_content_id": str(submission.promoted_content_id)
                if submission.promoted_content_id
                else None,
            }
            for submission, content_item in rows
        ]
        next_cursor = encode_cursor(rows[-1][0].id) if has_more and rows else None
        return items, next_cursor, has_more

    async def list_class_content(
        self,
        *,
        class_id: uuid.UUID,
        cursor: str | None,
        limit: int,
        auth: AuthContext,
    ) -> tuple[list[dict], str | None, bool]:
        rows, has_more = await self.repo.list_class_content(
            class_id=class_id,
            school_id=auth.school_id,
            cursor=cursor,
            limit=limit,
        )
        items = [
            {
                "id": str(assignment.id),
                "content_item_id": str(assignment.content_item_id),
                "title": content_item.title,
                "content_type": content_item.content_type,
                "level_band": content_item.level_band,
                "language": content_item.language,
                "subject": content_item.subject,
                "description": content_item.description,
                "assigned_at": assignment.assigned_at.isoformat()
                if assignment.assigned_at
                else None,
                "teacher_notes": assignment.notes,
            }
            for assignment, content_item in rows
        ]
        next_cursor = encode_cursor(rows[-1][0].id) if has_more and rows else None
        return items, next_cursor, has_more

    async def create_assessment(
        self,
        *,
        body: AssessmentCreateRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        class_room = await self.repo.get_class(body.class_id)
        if class_room is None:
            raise NotFoundError("Class not found", error_code="ERR-LMS-404")
        verify_school_boundary(class_room.school_id, auth)

        if auth.role == "TCH":
            teacher_classes = await self.repo.list_teacher_class_ids(
                teacher_id=auth.user_id,
                school_id=auth.school_id,
            )
            verify_teacher_assignment(body.class_id, teacher_classes)

        assessment = await self.repo.create_assessment(
            class_id=body.class_id,
            teacher_id=auth.user_id,
            title=body.title,
            due_at=body.due_at,
            window_end=body.window_end,
            total_points=body.total_points,
            status=body.status,
        )

        await self.audit.log_event(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            action_type="ASSESSMENT_CREATED",
            outcome="success",
            target_type="assessment",
            target_id=assessment.id,
            entity_after={
                "class_id": str(body.class_id),
                "title": body.title,
                "status": body.status,
            },
            ip_address=ip_address,
        )

        return self._assessment_to_dict(assessment)

    async def list_assessments(
        self,
        *,
        class_id: uuid.UUID | None,
        status: str | None,
        filters: FilterSpec,
        sort: SortSpec,
        search: str | None,
        cursor: str | None,
        limit: int,
        auth: AuthContext,
    ) -> tuple[list[dict], str | None, bool]:
        teacher_class_ids: set[uuid.UUID] | None = None
        if auth.role == "TCH":
            teacher_class_ids = await self.repo.list_teacher_class_ids(
                teacher_id=auth.user_id,
                school_id=auth.school_id,
            )

        assessments, has_more = await self.repo.list_assessments(
            school_id=auth.school_id,
            class_id=class_id,
            status=status,
            teacher_class_ids=teacher_class_ids,
            filters=filters,
            sort=sort,
            search=search,
            cursor=cursor,
            limit=limit,
        )
        items = [self._assessment_to_dict(assessment) for assessment in assessments]
        next_cursor = (
            encode_cursor(assessments[-1].id) if has_more and assessments else None
        )
        return items, next_cursor, has_more

    async def publish_assessment(
        self,
        *,
        assessment_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        bundle = await self.repo.get_assessment_with_class(assessment_id)
        if bundle is None:
            raise NotFoundError("Assessment not found", error_code="ERR-LMS-404")
        assessment, class_room = bundle
        verify_school_boundary(class_room.school_id, auth)

        if assessment.status != "draft":
            raise ConflictError(
                "Assessment can only be published from draft status",
                error_code="ERR-LMS-409",
                details={"current_status": assessment.status},
            )

        assessment.status = "published"
        await self.repo.save_assessment(assessment)

        await self.audit.log_event(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            action_type="ASSESSMENT_PUBLISHED",
            outcome="success",
            target_type="assessment",
            target_id=assessment.id,
            entity_after={"status": "published"},
            ip_address=ip_address,
        )

        return self._assessment_to_dict(assessment)

    async def submit_assessment_result(
        self,
        *,
        assessment_id: uuid.UUID,
        body: AssessmentResultSubmitRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        bundle = await self.repo.get_assessment_with_class(assessment_id)
        if bundle is None:
            raise NotFoundError("Assessment not found", error_code="ERR-LMS-404")
        assessment, class_room = bundle
        verify_school_boundary(class_room.school_id, auth)

        if assessment.status != "published":
            raise ValidationError(
                "Assessment must be published to accept results",
                error_code="ERR-LMS-422",
            )

        existing = await self.repo.get_assessment_result(
            assessment_id=assessment_id,
            student_id=auth.user_id,
        )
        if existing is not None:
            return {
                "id": str(existing.id),
                "assessment_id": str(existing.assessment_id),
                "student_id": str(existing.student_id),
                "score": float(existing.score) if existing.score is not None else None,
                "status": existing.status,
            }

        result_obj = await self.repo.create_assessment_result(
            assessment_id=assessment_id,
            student_id=auth.user_id,
            score=body.score,
            status="submitted",
        )

        await self.audit.log_event(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            action_type="ASSESSMENT_RESULT_SUBMITTED",
            outcome="success",
            target_type="assessment_result",
            target_id=result_obj.id,
            entity_after={
                "assessment_id": str(assessment_id),
                "score": float(body.score) if body.score is not None else None,
            },
            ip_address=ip_address,
        )

        return {
            "id": str(result_obj.id),
            "assessment_id": str(result_obj.assessment_id),
            "student_id": str(result_obj.student_id),
            "score": float(result_obj.score) if result_obj.score is not None else None,
            "status": result_obj.status,
        }

    async def list_results(
        self,
        *,
        student_id: uuid.UUID | None,
        cursor: str | None,
        limit: int,
        auth: AuthContext,
    ) -> tuple[list[dict], str | None, bool]:
        student_ids: set[uuid.UUID] | None

        if auth.role == "STD":
            student_ids = {auth.user_id}
        elif auth.role == "PAR":
            child_ids = await self.repo.list_parent_child_ids(
                parent_id=auth.user_id,
                school_id=auth.school_id,
            )
            if student_id is None:
                student_ids = child_ids if child_ids else None
            else:
                verify_parent_child_ownership(student_id, child_ids)
                student_ids = {student_id}
        else:
            student_ids = {student_id} if student_id is not None else None

        rows, has_more = await self.repo.list_results(
            school_id=auth.school_id,
            student_ids=student_ids,
            cursor=cursor,
            limit=limit,
        )
        items = [
            {
                "assignment_id": str(assignment.id),
                "assignment_title": assignment.title,
                "course_title": course.title,
                "submission_id": str(submission.id),
                "status": submission.status,
                "score": float(grade.score) if grade.score is not None else None,
                "feedback_text": grade.feedback_text,
                "total_points": assignment.total_points,
                "due_at": assignment.due_at.isoformat() if assignment.due_at else None,
            }
            for assignment, submission, grade, course in rows
        ]
        next_cursor = encode_cursor(rows[-1][0].id) if has_more and rows else None
        return items, next_cursor, has_more

    async def create_quiz(
        self,
        *,
        body: QuizCreateRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        school_id = None if auth.role == "CONTENT_MGR" else auth.school_id
        quiz = await self.quiz_repo.create_quiz(
            school_id=school_id,
            created_by=auth.user_id,
            title=body.title,
            description=body.description,
            subject=body.subject,
            level_band=body.level_band,
            difficulty=body.difficulty,
            time_limit_minutes=body.time_limit_minutes,
            max_attempts=body.max_attempts,
            shuffle_questions=body.shuffle_questions,
            status="draft",
        )
        questions = await self.quiz_repo.create_quiz_questions(
            [
                {
                    "quiz_id": quiz.id,
                    "question_type": question.question_type,
                    "question_text": question.question_text,
                    "question_media_path": question.question_media_path,
                    "options": question.options,
                    "correct_answer": question.correct_answer,
                    "points": question.points,
                    "order": question.order if question.order > 0 else index,
                    "explanation": question.explanation,
                }
                for index, question in enumerate(body.questions)
            ]
        )

        await self.audit.log_event(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            action_type="QUIZ_CREATED",
            outcome="success",
            target_type="quiz",
            target_id=quiz.id,
            entity_after={"title": quiz.title, "question_count": len(questions)},
            ip_address=ip_address,
        )

        payload = self._quiz_to_dict(quiz, questions)
        payload["questions"] = [
            self._quiz_question_to_dict(question, include_answer=True)
            for question in questions
        ]
        return payload

    async def list_quizzes(
        self,
        *,
        subject: str | None,
        level_band: str | None,
        status: str | None,
        difficulty: str | None,
        cursor: str | None,
        limit: int,
        auth: AuthContext,
    ) -> tuple[list[dict], str | None, bool]:
        quizzes, has_more = await self.quiz_repo.list_quizzes_for_actor(
            role=auth.role,
            school_id=auth.school_id,
            user_id=auth.user_id,
            subject=subject,
            level_band=level_band,
            status=status,
            difficulty=difficulty,
            cursor=cursor,
            limit=limit,
        )
        counts = await self.quiz_repo.get_question_counts([quiz.id for quiz in quizzes])

        items = []
        for quiz in quizzes:
            question_count, total_points = counts.get(quiz.id, (0, 0))
            items.append(
                {
                    "id": str(quiz.id),
                    "school_id": str(quiz.school_id) if quiz.school_id else None,
                    "created_by": str(quiz.created_by),
                    "title": quiz.title,
                    "description": quiz.description,
                    "subject": quiz.subject,
                    "level_band": quiz.level_band,
                    "difficulty": quiz.difficulty,
                    "time_limit_minutes": quiz.time_limit_minutes,
                    "max_attempts": quiz.max_attempts,
                    "shuffle_questions": quiz.shuffle_questions,
                    "status": quiz.status,
                    "total_points": total_points,
                    "question_count": question_count,
                }
            )

        next_cursor = encode_cursor(quizzes[-1].id) if has_more and quizzes else None
        return items, next_cursor, has_more

    async def get_quiz(
        self,
        *,
        quiz_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict:
        quiz = await self.quiz_repo.get_quiz(quiz_id)
        if quiz is None:
            raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")
        if quiz.school_id is not None and quiz.school_id != auth.school_id:
            raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")
        if auth.role == "STD" and quiz.status != "published":
            raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")

        questions = await self.quiz_repo.list_quiz_questions(quiz_id)
        include_answer = auth.role in ("CONTENT_MGR", "TCH", "ADM")
        payload = self._quiz_to_dict(quiz, questions)
        payload["questions"] = [
            self._quiz_question_to_dict(question, include_answer=include_answer)
            for question in questions
        ]
        return payload

    async def update_quiz(
        self,
        *,
        quiz_id: uuid.UUID,
        body: QuizUpdateRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        quiz = await self.quiz_repo.get_quiz(quiz_id)
        if quiz is None:
            raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")
        if quiz.status != "draft":
            raise ValidationError("Can only edit draft quizzes", error_code="ERR-QUIZ-400")
        if auth.role == "TCH" and quiz.created_by != auth.user_id:
            raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")

        update_data = body.model_dump(exclude_unset=True, exclude={"questions"})
        for field, value in update_data.items():
            setattr(quiz, field, value)
        await self.quiz_repo.save_quiz(quiz)

        if body.questions is not None:
            await self.quiz_repo.delete_quiz_questions(quiz_id)
            await self.quiz_repo.create_quiz_questions(
                [
                    {
                        "quiz_id": quiz.id,
                        "question_type": question.question_type,
                        "question_text": question.question_text,
                        "question_media_path": question.question_media_path,
                        "options": question.options,
                        "correct_answer": question.correct_answer,
                        "points": question.points,
                        "order": question.order if question.order > 0 else index,
                        "explanation": question.explanation,
                    }
                    for index, question in enumerate(body.questions)
                ]
            )

        questions = await self.quiz_repo.list_quiz_questions(quiz_id)

        await self.audit.log_event(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            action_type="QUIZ_UPDATED",
            outcome="success",
            target_type="quiz",
            target_id=quiz.id,
            entity_after={"title": quiz.title},
            ip_address=ip_address,
        )

        payload = self._quiz_to_dict(quiz, questions)
        payload["questions"] = [
            self._quiz_question_to_dict(question, include_answer=True)
            for question in questions
        ]
        return payload

    async def publish_quiz(
        self,
        *,
        quiz_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        quiz = await self.quiz_repo.get_quiz(quiz_id)
        if quiz is None:
            raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")
        if auth.role == "TCH" and quiz.created_by != auth.user_id:
            raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")
        if quiz.status != "draft":
            raise ValidationError("Quiz is not in draft status", error_code="ERR-QUIZ-400")

        question_count = await self.quiz_repo.count_quiz_questions(quiz_id)
        if question_count == 0:
            raise ValidationError(
                "Cannot publish a quiz with no questions",
                error_code="ERR-QUIZ-400",
            )

        quiz.status = "published"
        await self.quiz_repo.save_quiz(quiz)

        await self.audit.log_event(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            action_type="QUIZ_PUBLISHED",
            outcome="success",
            target_type="quiz",
            target_id=quiz.id,
            entity_after={"status": "published"},
            ip_address=ip_address,
        )

        return {"id": str(quiz.id), "status": "published"}

    async def start_quiz_attempt(
        self,
        *,
        quiz_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        quiz = await self.quiz_repo.get_quiz(quiz_id)
        if quiz is None or quiz.status != "published":
            raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")
        if quiz.school_id is not None and quiz.school_id != auth.school_id:
            raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")

        existing_count = await self.quiz_repo.count_student_attempts(
            quiz_id=quiz_id,
            student_id=auth.user_id,
        )
        if existing_count >= quiz.max_attempts:
            raise ValidationError(
                f"Maximum attempts ({quiz.max_attempts}) reached",
                error_code="ERR-QUIZ-429",
            )

        active = await self.quiz_repo.get_active_attempt(
            quiz_id=quiz_id,
            student_id=auth.user_id,
        )
        if active is not None:
            return self._attempt_to_dict(active)

        max_score = await self.quiz_repo.sum_quiz_points(quiz_id)
        attempt = await self.quiz_repo.create_quiz_attempt(
            quiz_id=quiz_id,
            student_id=auth.user_id,
            attempt_no=existing_count + 1,
            started_at=_utc_now(),
            max_score=max_score,
            status="STARTED",
        )

        await self.audit.log_event(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            action_type="QUIZ_ATTEMPT_STARTED",
            outcome="success",
            target_type="quiz_attempt",
            target_id=attempt.id,
            entity_after={"quiz_id": str(quiz_id), "attempt_no": attempt.attempt_no},
            ip_address=ip_address,
        )

        return self._attempt_to_dict(attempt)

    async def respond_to_quiz_question(
        self,
        *,
        attempt_id: uuid.UUID,
        body: QuizRespondRequest,
        auth: AuthContext,
    ) -> dict:
        attempt = await self.quiz_repo.get_quiz_attempt(attempt_id)
        if attempt is None:
            raise NotFoundError("Attempt not found", error_code="ERR-QUIZ-404")
        if attempt.student_id != auth.user_id:
            raise NotFoundError("Attempt not found", error_code="ERR-QUIZ-404")
        if attempt.status != "STARTED":
            raise ValidationError("Attempt already completed", error_code="ERR-QUIZ-400")

        quiz = await self.quiz_repo.get_quiz(attempt.quiz_id)
        if quiz is None:
            raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")

        if quiz.time_limit_minutes and quiz.time_limit_minutes > 0:
            elapsed = (_utc_now() - attempt.started_at).total_seconds()
            if elapsed > quiz.time_limit_minutes * 60:
                attempt.status = "TIMED_OUT"
                attempt.completed_at = _utc_now()
                await self.quiz_repo.save_quiz_attempt(attempt)
                raise ValidationError("Time limit exceeded", error_code="ERR-QUIZ-408")

        question = await self.quiz_repo.get_quiz_question(
            quiz_id=attempt.quiz_id,
            question_id=body.question_id,
        )
        if question is None:
            raise NotFoundError(
                "Question not found in this quiz",
                error_code="ERR-QUIZ-404",
            )

        response = await self.quiz_repo.get_quiz_response(
            attempt_id=attempt_id,
            question_id=body.question_id,
        )
        now = _utc_now()
        if response is not None:
            response.student_answer = body.student_answer
            response.answered_at = now
            response.is_correct = None
            response.points_earned = None
            await self.quiz_repo.save_quiz_response(response)
        else:
            response = await self.quiz_repo.create_quiz_response(
                attempt_id=attempt_id,
                question_id=body.question_id,
                student_answer=body.student_answer,
                answered_at=now,
            )

        return {
            "id": str(response.id),
            "attempt_id": str(attempt_id),
            "question_id": str(body.question_id),
            "answered_at": now.isoformat(),
        }

    async def submit_quiz_attempt(
        self,
        *,
        attempt_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        attempt = await self.quiz_repo.get_quiz_attempt(attempt_id)
        if attempt is None:
            raise NotFoundError("Attempt not found", error_code="ERR-QUIZ-404")
        if attempt.student_id != auth.user_id:
            raise NotFoundError("Attempt not found", error_code="ERR-QUIZ-404")
        if attempt.status != "STARTED":
            raise ValidationError("Attempt already completed", error_code="ERR-QUIZ-400")

        total_score, max_score = await grade_attempt(attempt_id, self.db)
        attempt = await self.quiz_repo.get_quiz_attempt(attempt_id)
        if attempt is None:
            raise NotFoundError("Attempt not found", error_code="ERR-QUIZ-404")

        await self.audit.log_event(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            action_type="QUIZ_ATTEMPT_SUBMITTED",
            outcome="success",
            target_type="quiz_attempt",
            target_id=attempt.id,
            entity_after={
                "score": float(total_score),
                "max_score": max_score,
                "status": "COMPLETED",
            },
            ip_address=ip_address,
        )

        return self._attempt_to_dict(attempt)

    async def get_quiz_attempt_results(
        self,
        *,
        attempt_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict:
        attempt = await self.quiz_repo.get_quiz_attempt(attempt_id)
        if attempt is None:
            raise NotFoundError("Attempt not found", error_code="ERR-QUIZ-404")
        if auth.role == "STD" and attempt.student_id != auth.user_id:
            raise NotFoundError("Attempt not found", error_code="ERR-QUIZ-404")
        if attempt.status == "STARTED":
            raise ValidationError("Attempt not yet submitted", error_code="ERR-QUIZ-400")

        rows = await self.quiz_repo.list_attempt_responses_with_questions(attempt_id)
        responses = [
            {
                "question_id": str(response.question_id),
                "question_type": question.question_type,
                "question_text": question.question_text,
                "student_answer": response.student_answer,
                "correct_answer": question.correct_answer,
                "is_correct": response.is_correct,
                "points_earned": float(response.points_earned)
                if response.points_earned is not None
                else None,
                "points": question.points,
                "explanation": question.explanation,
            }
            for response, question in rows
        ]
        return {
            "attempt": self._attempt_to_dict(attempt),
            "responses": responses,
        }

    async def get_quiz_analytics(
        self,
        *,
        quiz_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict:
        quiz = await self.quiz_repo.get_quiz(quiz_id)
        if quiz is None:
            raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")

        if auth.role == "TCH" and quiz.created_by != auth.user_id:
            if quiz.school_id is not None and quiz.school_id != auth.school_id:
                raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")

        total_attempts, completed, avg_score, max_achieved, min_achieved = (
            await self.quiz_repo.get_attempt_stats(quiz_id)
        )
        max_possible = await self.quiz_repo.sum_quiz_points(quiz_id)
        avg_pct = None
        if avg_score is not None and max_possible > 0:
            avg_pct = round(avg_score / max_possible * 100, 1)

        questions = await self.quiz_repo.list_quiz_questions(quiz_id)
        question_stats = []
        for question in questions:
            total_responses, correct_responses = await self.quiz_repo.get_question_response_stats(
                question.id
            )
            question_stats.append(
                {
                    "question_id": str(question.id),
                    "question_text": question.question_text[:100],
                    "question_type": question.question_type,
                    "total_responses": total_responses,
                    "correct_responses": correct_responses,
                    "accuracy": round(correct_responses / total_responses * 100, 1)
                    if total_responses > 0
                    else None,
                }
            )

        return {
            "quiz_id": str(quiz_id),
            "title": quiz.title,
            "total_attempts": total_attempts,
            "completed_attempts": completed,
            "average_score": round(avg_score, 2) if avg_score is not None else None,
            "max_score_achieved": max_achieved,
            "min_score_achieved": min_achieved,
            "average_percentage": avg_pct,
            "question_stats": question_stats,
        }
