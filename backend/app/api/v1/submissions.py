"""Submission API endpoints: create, grade, file upload, file download.

Reference:
  S-053 — POST /submissions (STD) — Submit work for an assignment
  S-054 — POST /submissions/{id}/grade (TCH) — Grade a submission
  Phase 3B — POST /submissions/{id}/files — Upload submission file
  Phase 3B — GET /submissions/{id}/files/{file_id} — Download submission file
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    AuthContext,
    requires_permission,
    verify_school_boundary,
)
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.core.response import success_response
from app.core.storage import storage, validate_mime_type
from app.models.lms import Assignment, Course, Grade, Submission, SubmissionFile
from app.schemas.lms import GradeRequest, SubmissionCreateRequest
from app.services.audit import AuditService
from app.services.realtime import publish_grade_published

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
@router.post(
    "",
    status_code=201,
    summary="Submit student work",
    response_description="Submission record",
)
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
        return success_response(
            {
                "id": str(existing.id),
                "assignment_id": str(existing.assignment_id),
                "student_id": str(existing.student_id),
                "status": existing.status,
                "submitted_at": existing.submitted_at.isoformat()
                if existing.submitted_at
                else None,
            }
        )

    # 4. Create submission
    # PRINTABLE_PDF assignments start as draft so student can upload solution files first
    now = datetime.now(timezone.utc)
    is_pdf_exercise = assignment.exercise_type == "PRINTABLE_PDF"
    initial_status = "draft" if is_pdf_exercise else "submitted"

    submission = Submission(
        assignment_id=body.assignment_id,
        student_id=auth.user_id,
        status=initial_status,
        submitted_at=None if is_pdf_exercise else now,
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
            "status": initial_status,
        },
        ip_address=_get_client_ip(request),
    )

    return success_response(
        {
            "id": str(submission.id),
            "assignment_id": str(submission.assignment_id),
            "student_id": str(submission.student_id),
            "status": submission.status,
            "submitted_at": submission.submitted_at.isoformat()
            if submission.submitted_at
            else None,
        }
    )


# ---------------------------------------------------------------------------
# S-054: POST /submissions/{id}/grade — Grade a submission (TCH)
# ---------------------------------------------------------------------------
@router.post(
    "/{submission_id}/grade",
    status_code=201,
    summary="Grade a submission",
    response_description="Updated submission with grade",
)
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

    # 7. Real-time push (Phase 3C) — notify student when grade is published
    if body.publish:
        await publish_grade_published(
            student_id=submission.student_id,
            grade_id=grade.id,
            submission_id=submission_id,
            score=float(body.score),
            assignment_title=assignment.title,
        )

        # 8. Enqueue grade notification email (Phase 3E)
        try:
            from app.core.tasks import enqueue_email
            from app.models.iam import User

            student_result = await db.execute(
                select(User).where(User.id == submission.student_id)
            )
            student = student_result.scalar_one_or_none()
            if student and student.email:
                await enqueue_email(
                    to=student.email,
                    template_name="grade_published",
                    lang="fr",
                    student_name=student.first_name or student.email,
                    assignment_title=assignment.title,
                    score=float(body.score),
                    total_points=float(assignment.total_points),
                    feedback=body.feedback_text,
                )
        except Exception:
            pass  # Fire-and-forget — never block grading

    return success_response(
        {
            "id": str(grade.id),
            "submission_id": str(grade.submission_id),
            "teacher_id": str(grade.teacher_id),
            "score": float(grade.score),
            "feedback_text": grade.feedback_text,
            "published_at": grade.published_at.isoformat()
            if grade.published_at
            else None,
        }
    )


# ---------------------------------------------------------------------------
# Phase 3B: POST /submissions/{id}/files — Upload submission file (STD)
# ---------------------------------------------------------------------------
MAX_FILES_PER_SUBMISSION = 5


@router.post(
    "/{submission_id}/files",
    status_code=201,
    summary="Upload a submission file",
    response_description="Uploaded file metadata",
)
async def upload_submission_file(
    submission_id: uuid.UUID,
    file: UploadFile,
    request: Request,
    file_type_hint: str | None = Form(None),
    auth: AuthContext = Depends(requires_permission("PERM-LMS:submission-file:upload")),
    db: AsyncSession = Depends(get_db),
):
    """Upload a file to a submission.

    Validates:
    1. Submission exists and belongs to the student
    2. Submission is in draft/submitted status
    3. Max 5 files per submission
    4. MIME type whitelist + file size limit
    5. Computes SHA-256 checksum on write
    """
    audit = AuditService(db)

    # 1. Validate submission
    sub_result = await db.execute(
        select(Submission).where(Submission.id == submission_id)
    )
    submission = sub_result.scalar_one_or_none()
    if submission is None:
        raise NotFoundError("Submission not found", error_code="ERR-LMS-404")

    # Must be the student's own submission
    if submission.student_id != auth.user_id:
        raise NotFoundError("Submission not found", error_code="ERR-LMS-404")

    # School boundary via assignment → course
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

    # 2. Submission must be active
    if submission.status not in ("draft", "submitted"):
        raise ValidationError(
            "Cannot upload files to a graded or returned submission",
            error_code="ERR-LMS-422",
        )

    # 3. Max files check
    count_result = await db.execute(
        select(func.count()).where(SubmissionFile.submission_id == submission_id)
    )
    current_count = count_result.scalar() or 0
    if current_count >= MAX_FILES_PER_SUBMISSION:
        raise ValidationError(
            f"Maximum of {MAX_FILES_PER_SUBMISSION} files per submission",
            error_code="ERR-UPLOAD-422",
        )

    # 4. Validate file_type_hint if provided
    valid_hints = {"SOLUTION_SCAN", "SOLUTION_PHOTO", "DOCUMENT"}
    if file_type_hint and file_type_hint not in valid_hints:
        raise ValidationError(
            f"file_type_hint must be one of: {', '.join(sorted(valid_hints))}",
            error_code="ERR-LMS-422",
        )

    # 5. MIME validation
    mime = file.content_type or "application/octet-stream"
    validate_mime_type(mime)

    # 6. Save file via storage backend
    relative_path, checksum, file_size = await storage.save(
        file.file,
        file.filename or "upload",
        subdirectory=f"submissions/{submission_id}",
    )

    # 7. Persist to submission_files table
    sf = SubmissionFile(
        submission_id=submission_id,
        file_path=relative_path,
        checksum=checksum,
        mime_type=mime,
        file_size=file_size,
        file_type_hint=file_type_hint,
    )
    db.add(sf)
    await db.flush()

    # 8. Audit
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="SUBMISSION_FILE_UPLOADED",
        outcome="success",
        target_type="submission_file",
        target_id=sf.id,
        entity_after={
            "submission_id": str(submission_id),
            "file_path": relative_path,
            "mime_type": mime,
            "file_size": file_size,
            "checksum": checksum,
            "file_type_hint": file_type_hint,
        },
        ip_address=_get_client_ip(request),
    )

    return success_response(
        {
            "id": str(sf.id),
            "submission_id": str(sf.submission_id),
            "file_path": sf.file_path,
            "checksum": sf.checksum,
            "mime_type": sf.mime_type,
            "file_size": sf.file_size,
            "file_type_hint": sf.file_type_hint,
        }
    )


# ---------------------------------------------------------------------------
# Phase 3B: GET /submissions/{id}/files/{file_id} — Download file
# ---------------------------------------------------------------------------
@router.get(
    "/{submission_id}/files/{file_id}",
    summary="Download a submission file",
    response_description="File binary content",
)
async def download_submission_file(
    submission_id: uuid.UUID,
    file_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission("PERM-LMS:submission-file:read")),
    db: AsyncSession = Depends(get_db),
):
    """Download a submission file.

    Access: student who owns the submission, teacher assigned to the course, or admin.
    """
    # 1. Validate submission file exists
    sf_result = await db.execute(
        select(SubmissionFile).where(
            SubmissionFile.id == file_id,
            SubmissionFile.submission_id == submission_id,
        )
    )
    sf = sf_result.scalar_one_or_none()
    if sf is None:
        raise NotFoundError("File not found", error_code="ERR-UPLOAD-404")

    # 2. Validate submission + school boundary
    sub_result = await db.execute(
        select(Submission).where(Submission.id == submission_id)
    )
    submission = sub_result.scalar_one_or_none()
    if submission is None:
        raise NotFoundError("Submission not found", error_code="ERR-LMS-404")

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

    # 3. ABAC: student owns submission, or teacher owns course, or ADM
    if auth.role == "STD" and submission.student_id != auth.user_id:
        raise NotFoundError("File not found", error_code="ERR-UPLOAD-404")
    if auth.role == "TCH" and course.teacher_id != auth.user_id:
        raise NotFoundError("File not found", error_code="ERR-UPLOAD-404")

    # 4. Serve file
    abs_path = await storage.read(sf.file_path)
    return FileResponse(
        path=str(abs_path),
        media_type=sf.mime_type or "application/octet-stream",
        filename=abs_path.name,
    )


# ---------------------------------------------------------------------------
# Phase 9C: POST /submissions/{id}/submit — Finalize a draft submission (STD)
# ---------------------------------------------------------------------------
@router.post(
    "/{submission_id}/submit",
    summary="Finalize and submit a draft submission",
    response_description="Updated submission",
)
async def finalize_submission(
    submission_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-LMS:submission:create")),
    db: AsyncSession = Depends(get_db),
):
    """Finalize a draft submission (transition draft → submitted).

    For PRINTABLE_PDF assignments, validates that at least one file has been uploaded.
    """
    audit = AuditService(db)

    # 1. Load submission
    sub_result = await db.execute(
        select(Submission).where(Submission.id == submission_id)
    )
    submission = sub_result.scalar_one_or_none()
    if submission is None:
        raise NotFoundError("Submission not found", error_code="ERR-LMS-404")

    if submission.student_id != auth.user_id:
        raise NotFoundError("Submission not found", error_code="ERR-LMS-404")

    if submission.status != "draft":
        raise ValidationError(
            "Only draft submissions can be finalized",
            error_code="ERR-LMS-422",
        )

    # 2. Load assignment to check exercise_type
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

    # 3. PRINTABLE_PDF: require at least one uploaded file
    if assignment.exercise_type == "PRINTABLE_PDF":
        file_count_result = await db.execute(
            select(func.count()).where(SubmissionFile.submission_id == submission_id)
        )
        file_count = file_count_result.scalar() or 0
        if file_count == 0:
            raise ValidationError(
                "PRINTABLE_PDF submissions require at least one uploaded solution file",
                error_code="ERR-LMS-422",
            )

    # 4. Transition to submitted
    now = datetime.now(timezone.utc)
    submission.status = "submitted"
    submission.submitted_at = now
    await db.flush()

    # 5. Audit
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
        ip_address=_get_client_ip(request),
    )

    return success_response(
        {
            "id": str(submission.id),
            "assignment_id": str(submission.assignment_id),
            "student_id": str(submission.student_id),
            "status": submission.status,
            "submitted_at": submission.submitted_at.isoformat(),
        }
    )


# ---------------------------------------------------------------------------
# Phase 9C: GET /submissions/{id}/preview — Teacher inline preview of files
# ---------------------------------------------------------------------------
@router.get(
    "/{submission_id}/preview",
    summary="Preview submission files (teacher)",
    response_description="List of files with preview metadata",
)
async def preview_submission_files(
    submission_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission("PERM-LMS:submission:grade")),
    db: AsyncSession = Depends(get_db),
):
    """Teacher inline preview: list submission files with metadata for rendering.

    Returns file list with mime_type, file_type_hint, and download URL path
    so the frontend can render inline previews for images/PDFs.
    """
    # 1. Load submission
    sub_result = await db.execute(
        select(Submission).where(Submission.id == submission_id)
    )
    submission = sub_result.scalar_one_or_none()
    if submission is None:
        raise NotFoundError("Submission not found", error_code="ERR-LMS-404")

    # 2. Verify teacher owns the course
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

    if auth.role == "TCH" and course.teacher_id != auth.user_id:
        raise NotFoundError("Submission not found", error_code="ERR-LMS-404")

    # 3. Load files
    files_result = await db.execute(
        select(SubmissionFile).where(SubmissionFile.submission_id == submission_id)
    )
    files = list(files_result.scalars().all())

    items = []
    for f in files:
        is_previewable = (f.mime_type or "").startswith(
            "image/"
        ) or f.mime_type == "application/pdf"
        items.append(
            {
                "id": str(f.id),
                "file_path": f.file_path,
                "mime_type": f.mime_type,
                "file_size": f.file_size,
                "file_type_hint": f.file_type_hint,
                "checksum": f.checksum,
                "is_previewable": is_previewable,
                "download_url": f"/api/v1/submissions/{submission_id}/files/{f.id}",
            }
        )

    return success_response(
        {
            "submission_id": str(submission_id),
            "assignment_id": str(submission.assignment_id),
            "student_id": str(submission.student_id),
            "status": submission.status,
            "exercise_type": assignment.exercise_type,
            "files": items,
        }
    )
