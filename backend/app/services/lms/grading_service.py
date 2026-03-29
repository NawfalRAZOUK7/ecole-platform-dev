"""Grading and late-penalty management LMS service."""

from __future__ import annotations

import uuid

from app.core.dependencies import AuthContext, verify_school_boundary
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.core.unit_of_work import UnitOfWork
from app.repositories.lms import LMSRepository
from app.schemas.lms import GradeRequest
from app.services.audit import AuditService
from app.services.lms._helpers import (
    LMSServiceBase,
    calculate_late_penalty,
    _utc_now,
)


class GradingService(LMSServiceBase):
    """Handles grading submissions and late-penalty overrides."""

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
