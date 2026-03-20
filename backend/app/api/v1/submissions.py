"""Submission API endpoint: POST /submissions, POST /submissions/{id}/grade.

Reference:
  S-053 — POST /submissions (STD) — Submit work for an assignment
  S-054 — POST /submissions/{id}/grade (TCH) — Grade a submission
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission, verify_school_boundary
from app.core.exceptions import AuthorizationError, ConflictError, NotFoundError, ValidationError
from app.core.response import success_response
from app.models.lms import Assignment, Course, Grade, Submission
from app.schemas.lms import GradeRequest, SubmissionCreateRequest
from app.services.audit import AuditService

router = APIRouter(prefix="/submissions", tags=["lms-submissions"])


def _get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


# ---------------------------------------------------------------------------
# S-053: POST /submissions — Submit work (STD)
# ---------------------------------------------------------------------------
@router.post("", status_code=201, summary="Submit student work", response_description="Submission record")
async def create_submission(
    body: SubmissionCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-LMS:submission:create")),
    db: AsyncSession = Depends(get_db),
):
    """Create a submission for an assignment.

    Validates:
    1. Assignment exists
    2. Course is in the same school
    3. INV-LMS-SUBMISSION: one active submission per student per assignment (idempotent)
    """
    audit = AuditService(db)

    # 1. Validate assignment exists
    assignment_result = await db.execute(
        select(Assignment).where(Assignment.id == body.assignment_id)
    )
    assignment = assignment_result.scalar_one_or_none()
    if assignment is None:
        raise NotFoundError("Assignment not found", error_code="ERR-LMS-404")

    # 2. Verify course school boundary
    course_result = await db.execute(
        select(Course).where(Course.id == assignment.course_id)
    )
    course = course_result.scalar_one_or_none()
    if course is None:
        raise NotFoundError("Course not found", error_code="ERR-LMS-404")
    verify_school_boundary(course.school_id, auth)

    # 3. Check for existing active submission (idempotent)
    existing_result = await db.execute(
        select(Submission).where(
            Submission.assignment_id == body.assignment_id,
            Submission.student_id == auth.user_id,
            Submission.status.in_(["draft", "submitted"]),
        )
    )
    existing = existing_result.scalar_one_or_none()
    if existing is not None:
        return success_response({
            "id": str(existing.id),
            "assignment_id": str(existing.assignment_id),
            "student_id": str(existing.student_id),
            "status": existing.status,
            "submitted_at": existing.submitted_at.isoformat() if existing.submitted_at else None,
        })

    # 4. Create submission (status=submitted immediately)
    now = datetime.now(timezone.utc)
    submission = Submission(
        assignment_id=body.assignment_id,
        student_id=auth.user_id,
        status="submitted",
        submitted_at=now,
    )
    db.add(submission)
    await db.flush()

    # 5. Audit
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="SUBMISSION_CREATED",
        outcome="success",
        target_type="submission",
        target_id=submission.id,
        entity_after={
            "assignment_id": str(body.assignment_id),
            "status": "submitted",
        },
        ip_address=_get_client_ip(request),
    )

    return success_response({
        "id": str(submission.id),
        "assignment_id": str(submission.assignment_id),
        "student_id": str(submission.student_id),
        "status": submission.status,
        "submitted_at": submission.submitted_at.isoformat() if submission.submitted_at else None,
    })


# ---------------------------------------------------------------------------
# S-054: POST /submissions/{id}/grade — Grade a submission (TCH)
# ---------------------------------------------------------------------------
@router.post("/{submission_id}/grade", status_code=201, summary="Grade a submission", response_description="Updated submission with grade")
async def grade_submission(
    submission_id: uuid.UUID,
    body: GradeRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-LMS:submission:grade")),
    db: AsyncSession = Depends(get_db),
):
    """Grade a student submission.

    Validates:
    1. Submission exists
    2. Assignment is in teacher's course (teacher owns the course)
    3. Submission must be in 'submitted' status
    4. Score <= assignment total_points
    5. Creates grade, updates submission status to 'graded'
    """
    audit = AuditService(db)

    # 1. Validate submission exists
    sub_result = await db.execute(
        select(Submission).where(Submission.id == submission_id)
    )
    submission = sub_result.scalar_one_or_none()
    if submission is None:
        raise NotFoundError("Submission not found", error_code="ERR-LMS-404")

    # 2. Validate assignment + course + school boundary
    assignment_result = await db.execute(
        select(Assignment).where(Assignment.id == submission.assignment_id)
    )
    assignment = assignment_result.scalar_one_or_none()
    if assignment is None:
        raise NotFoundError("Assignment not found", error_code="ERR-LMS-404")

    course_result = await db.execute(
        select(Course).where(Course.id == assignment.course_id)
    )
    course = course_result.scalar_one_or_none()
    if course is None:
        raise NotFoundError("Course not found", error_code="ERR-LMS-404")
    verify_school_boundary(course.school_id, auth)

    # Teacher must own the course
    if course.teacher_id != auth.user_id:
        raise AuthorizationError(
            "You can only grade submissions for your own courses",
            error_code="ERR-AUTHZ-001",
        )

    # 3. Submission must be submitted
    if submission.status not in ("submitted", "graded"):
        raise ValidationError(
            "Submission must be in submitted or graded status to be graded",
            error_code="ERR-LMS-422",
        )

    # 4. Score validation
    if assignment.total_points > 0 and body.score > assignment.total_points:
        raise ValidationError(
            f"Score cannot exceed total points ({assignment.total_points})",
            error_code="ERR-LMS-422",
        )

    # 5. Check for existing grade (update if exists)
    existing_grade_result = await db.execute(
        select(Grade).where(Grade.submission_id == submission_id)
    )
    existing_grade = existing_grade_result.scalar_one_or_none()

    now = datetime.now(timezone.utc) if body.publish else None

    if existing_grade is not None:
        # Update existing grade
        existing_grade.score = body.score
        existing_grade.feedback_text = body.feedback_text
        if body.publish:
            existing_grade.published_at = now
        await db.flush()
        grade = existing_grade
    else:
        # Create new grade
        grade = Grade(
            submission_id=submission_id,
            teacher_id=auth.user_id,
            score=body.score,
            feedback_text=body.feedback_text,
            published_at=now,
        )
        db.add(grade)
        await db.flush()

    # Update submission status
    submission.status = "graded"
    await db.flush()

    # 6. Audit
    await audit.log_event(
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
        ip_address=_get_client_ip(request),
    )

    return success_response({
        "id": str(grade.id),
        "submission_id": str(grade.submission_id),
        "teacher_id": str(grade.teacher_id),
        "score": float(grade.score),
        "feedback_text": grade.feedback_text,
        "published_at": grade.published_at.isoformat() if grade.published_at else None,
    })
