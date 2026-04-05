"""Shared helpers for split LMS services."""

from __future__ import annotations

import logging
import math
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import AuthContext, verify_school_boundary
from app.core.exceptions import NotFoundError, ValidationError
from app.core.permissions import STD, TCH
from app.core.storage import storage
from app.domain.events.lms import (
    AssignmentCreated,
    GradePublished,
    QuizCompleted,
    SubmissionReceived,
)
from app.models.lms import (
    Assignment,
    Course,
    Grade,
    QuizAttempt,
    Submission,
)
from app.repositories.lms import LMSRepository
from app.repositories.quiz import QuizRepository
from app.services.event_dispatcher import EventDispatcher
from app.services.lms._serializers import LMSSerializerMixin
from app.services.realtime import publish_grade_published

MAX_FILES_PER_SUBMISSION = 5
logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def calculate_late_penalty(
    *,
    assignment: Assignment,
    submission: Submission,
    original_score: float,
) -> dict[str, float | int]:
    """Apply assignment late rules to a raw score and return penalty metadata."""

    penalty = 0.0
    late_days = 0
    adjusted_score = float(original_score)

    if submission.submitted_at is None or assignment.due_at is None:
        return {
            "original_score": float(original_score),
            "adjusted_score": adjusted_score,
            "late_penalty": penalty,
            "late_days": late_days,
        }

    late_delta = submission.submitted_at - assignment.due_at
    grace = timedelta(hours=assignment.grace_period_hours or 0)
    if late_delta <= grace:
        return {
            "original_score": float(original_score),
            "adjusted_score": adjusted_score,
            "late_penalty": penalty,
            "late_days": late_days,
        }

    if not assignment.allow_late:
        raise ValidationError(
            "Late submissions are not allowed for this assignment",
            error_code="ERR-LMS-422",
        )

    late_days = math.ceil((late_delta - grace).total_seconds() / 86400)
    if assignment.max_late_days is not None and late_days > assignment.max_late_days:
        raise ValidationError(
            "Submission exceeded the maximum allowed late days",
            error_code="ERR-LMS-422",
            details={
                "late_days": late_days,
                "max_late_days": assignment.max_late_days,
            },
        )

    penalty = round(late_days * float(assignment.late_penalty_per_day or 0.0), 2)
    adjusted_score = round(max(0.0, float(original_score) - penalty), 2)
    return {
        "original_score": round(float(original_score), 2),
        "adjusted_score": adjusted_score,
        "late_penalty": penalty,
        "late_days": late_days,
    }


class LMSServiceBase(LMSSerializerMixin):
    """Shared LMS service dependencies. Serialization via LMSSerializerMixin."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = LMSRepository(db)
        self.quiz_repo = QuizRepository(db)
        self._dispatcher = EventDispatcher(db)

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

        if auth.role == TCH and course.teacher_id != auth.user_id:
            raise NotFoundError("Assignment not found", error_code="ERR-LMS-404")
        if auth.role == STD:
            enrolled = await self.repo.student_is_enrolled_in_class(
                student_id=auth.user_id,
                class_id=course.class_id,
            )
            if not enrolled:
                raise NotFoundError("Assignment not found", error_code="ERR-LMS-404")

        abs_path = await storage.read(assignment.exercise_pdf_path)
        return str(abs_path), "application/pdf", f"exercise_{assignment_id}.pdf"

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

        if auth.role == STD and submission.student_id != auth.user_id:
            raise NotFoundError("File not found", error_code="ERR-UPLOAD-404")
        if auth.role == TCH and course.teacher_id != auth.user_id:
            raise NotFoundError("File not found", error_code="ERR-UPLOAD-404")

        abs_path = await storage.read(submission_file.file_path)
        return (
            str(abs_path),
            submission_file.mime_type or "application/octet-stream",
            abs_path.name,
        )

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

        if auth.role == TCH and course.teacher_id != auth.user_id:
            raise NotFoundError("Submission not found", error_code="ERR-LMS-404")

        files = await self.repo.list_submission_files(submission_id)
        return {
            "submission_id": str(submission_id),
            "assignment_id": str(submission.assignment_id),
            "student_id": str(submission.student_id),
            "status": submission.status,
            "exercise_type": assignment.exercise_type,
            "files": [
                {
                    "id": str(file.id),
                    "file_path": file.file_path,
                    "mime_type": file.mime_type,
                    "file_size": file.file_size,
                    "file_type_hint": file.file_type_hint,
                    "checksum": file.checksum,
                    "is_previewable": (
                        (file.mime_type or "").startswith("image/")
                        or file.mime_type == "application/pdf"
                    ),
                    "download_url": f"/api/v1/submissions/{submission_id}/files/{file.id}",
                }
                for file in files
            ],
        }

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

    async def get_quiz_attempt_results(
        self,
        *,
        attempt_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict:
        attempt = await self.quiz_repo.get_quiz_attempt(attempt_id)
        if attempt is None:
            raise NotFoundError("Attempt not found", error_code="ERR-QUIZ-404")
        if auth.role == STD and attempt.student_id != auth.user_id:
            raise NotFoundError("Attempt not found", error_code="ERR-QUIZ-404")
        if attempt.status == "STARTED":
            raise ValidationError("Attempt not yet submitted", error_code="ERR-QUIZ-400")

        rows = await self.quiz_repo.list_attempt_responses_with_questions(attempt_id)
        return {
            "attempt": self._attempt_to_dict(attempt),
            "responses": [
                {
                    "question_id": str(response.question_id),
                    "question_type": question.question_type,
                    "question_text": question.question_text,
                    "student_answer": response.student_answer,
                    "correct_answer": question.correct_answer,
                    "is_correct": response.is_correct,
                    "points_earned": (
                        float(response.points_earned)
                        if response.points_earned is not None
                        else None
                    ),
                    "points": question.points,
                    "explanation": question.explanation,
                }
                for response, question in rows
            ],
        }

    async def _dispatch_assignment_created(
        self,
        *,
        assignment: Assignment,
        course: Course,
        actor_id: uuid.UUID,
    ) -> None:
        try:
            await self._dispatcher.dispatch(
                AssignmentCreated(
                    school_id=course.school_id,
                    actor_id=actor_id,
                    assignment_id=assignment.id,
                    course_title=course.title,
                    due_at=assignment.due_at.isoformat() if assignment.due_at else "",
                    class_id=course.class_id,
                )
            )
        except Exception:
            logger.exception("Failed to dispatch AssignmentCreated for %s", assignment.id)

    async def _dispatch_submission_received(
        self,
        *,
        submission: Submission,
        assignment: Assignment,
        course: Course,
        actor_id: uuid.UUID,
    ) -> None:
        try:
            student = await self.repo.get_user(actor_id)
            await self._dispatcher.dispatch(
                SubmissionReceived(
                    school_id=course.school_id,
                    actor_id=actor_id,
                    submission_id=submission.id,
                    student_name=student.full_name if student is not None else str(actor_id),
                    assignment_title=assignment.title,
                    teacher_id=course.teacher_id,
                )
            )
        except Exception:
            logger.exception("Failed to dispatch SubmissionReceived for %s", submission.id)

    async def _send_grade_published_fallback_email(
        self,
        *,
        grade: Grade,
        submission: Submission,
        assignment: Assignment,
        score: float,
        feedback_text: str | None,
    ) -> None:
        try:
            from app.core.tasks import enqueue_email

            student = await self.repo.get_user(submission.student_id)
            if student is None or not student.email:
                return

            student_name = getattr(student, "first_name", None) or getattr(
                student,
                "full_name",
                None,
            )
            await enqueue_email(
                to=student.email,
                template_name="grade_published",
                lang="fr",
                student_name=student_name or student.email,
                assignment_title=assignment.title,
                score=score,
                total_points=float(assignment.total_points),
                feedback=feedback_text,
            )
        except Exception:
            logger.warning(
                "Failed to execute GradePublished fallback email for %s",
                grade.id,
                exc_info=True,
            )

    async def _dispatch_grade_published(
        self,
        *,
        grade: Grade,
        submission: Submission,
        assignment: Assignment,
        course: Course,
        actor_id: uuid.UUID,
        score: float,
        feedback_text: str | None,
    ) -> None:
        await publish_grade_published(
            student_id=submission.student_id,
            grade_id=grade.id,
            submission_id=submission.id,
            score=score,
            assignment_title=assignment.title,
        )

        try:
            teacher = await self.repo.get_user(actor_id)
            await self._dispatcher.dispatch(
                GradePublished(
                    school_id=course.school_id,
                    actor_id=actor_id,
                    student_id=submission.student_id,
                    course_title=course.title,
                    score=score,
                    teacher_name=teacher.full_name if teacher is not None else str(actor_id),
                )
            )
        except Exception:
            logger.exception("Failed to dispatch GradePublished for %s", grade.id)
            await self._send_grade_published_fallback_email(
                grade=grade,
                submission=submission,
                assignment=assignment,
                score=score,
                feedback_text=feedback_text,
            )

    async def _dispatch_quiz_completed(
        self,
        *,
        attempt: QuizAttempt,
        actor_id: uuid.UUID,
        school_id: uuid.UUID,
        total_score: float,
        max_score: float | int,
    ) -> None:
        try:
            quiz = await self.quiz_repo.get_quiz(attempt.quiz_id)
            await self._dispatcher.dispatch(
                QuizCompleted(
                    school_id=school_id,
                    actor_id=actor_id,
                    student_id=attempt.student_id,
                    quiz_title=quiz.title if quiz is not None else str(attempt.quiz_id),
                    score_percent=(
                        round((float(total_score) / float(max_score)) * 100, 2)
                        if max_score
                        else 0.0
                    ),
                )
            )
        except Exception:
            logger.exception("Failed to dispatch QuizCompleted for %s", attempt.id)
