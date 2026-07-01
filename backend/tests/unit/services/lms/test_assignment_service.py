"""Unit tests for LMS assignment service."""

from __future__ import annotations

import io
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.core.dependencies import AuthContext
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.schemas.lms import AssignmentCreateRequest, SubmissionCreateRequest
from app.services.lms.assignment_service import AssignmentService
from app.services.lms import assignment_service as assignment_module


def utc_datetime(
    year: int,
    month: int,
    day: int,
    hour: int = 0,
    minute: int = 0,
) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


def make_auth(role: str = "TCH") -> AuthContext:
    return AuthContext(
        user_id=uuid.uuid4(),
        role=role,
        school_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        permissions=set(),
    )


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.session = AsyncMock()
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def commit(self) -> None:
        self.committed = True


def setup_service(monkeypatch: pytest.MonkeyPatch):
    service = AssignmentService(AsyncMock())
    service.repo = AsyncMock()
    service._dispatch_assignment_created = AsyncMock()
    service._dispatch_submission_received = AsyncMock()

    repo_in_uow = AsyncMock()
    audit = AsyncMock()
    uow = FakeUnitOfWork()

    monkeypatch.setattr(assignment_module, "UnitOfWork", lambda _db: uow)
    monkeypatch.setattr(
        assignment_module, "LMSRepository", lambda _session: repo_in_uow
    )
    monkeypatch.setattr(assignment_module, "AuditService", lambda _session: audit)

    return service, repo_in_uow, audit, uow


def make_course(auth: AuthContext, *, teacher_id: uuid.UUID | None = None):
    return SimpleNamespace(
        id=uuid.uuid4(),
        school_id=auth.school_id,
        class_id=uuid.uuid4(),
        teacher_id=teacher_id or auth.user_id,
        title="Math 6A",
    )


def make_assignment(
    course, *, exercise_type: str = "STANDARD", pdf_path: str | None = None
):
    return SimpleNamespace(
        id=uuid.uuid4(),
        course_id=course.id,
        teacher_id=course.teacher_id,
        title="Fractions",
        description="Exercises",
        due_at=utc_datetime(2026, 4, 1, 8),
        total_points=20,
        exercise_type=exercise_type,
        quiz_id=None,
        exercise_pdf_path=pdf_path,
    )


def make_submission(assignment, auth: AuthContext, *, status: str = "draft"):
    return SimpleNamespace(
        id=uuid.uuid4(),
        assignment_id=assignment.id,
        student_id=auth.user_id,
        status=status,
        submitted_at=None,
    )


class TestCreateAssignment:
    @pytest.mark.asyncio
    async def test_valid_create_assignment(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth()
        service, repo_in_uow, audit, uow = setup_service(monkeypatch)
        course = make_course(auth)
        assignment = make_assignment(course)
        service.repo.get_course.return_value = course
        repo_in_uow.create_assignment.return_value = assignment

        result = await service.create_assignment(
            body=AssignmentCreateRequest(
                course_id=course.id,
                title="Fractions",
                description="Exercises",
                due_at=utc_datetime(2026, 4, 1, 8),
                total_points=20,
                grace_period_hours=2,
                late_penalty_per_day=2.0,
                max_late_days=3,
                allow_late=True,
                exercise_type="STANDARD",
            ),
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["id"] == str(assignment.id)
        repo_in_uow.create_assignment.assert_awaited_once()
        audit.log_event.assert_awaited_once()
        assert uow.committed is True
        service._dispatch_assignment_created.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_course_not_found(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth()
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        service.repo.get_course.return_value = None

        with pytest.raises(NotFoundError, match="Course not found"):
            await service.create_assignment(
                body=AssignmentCreateRequest(
                    course_id=uuid.uuid4(),
                    title="Fractions",
                ),
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_wrong_teacher_cannot_create_assignment(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        auth = make_auth()
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        service.repo.get_course.return_value = make_course(
            auth, teacher_id=uuid.uuid4()
        )

        with pytest.raises(AuthorizationError, match="your own courses"):
            await service.create_assignment(
                body=AssignmentCreateRequest(
                    course_id=uuid.uuid4(),
                    title="Fractions",
                ),
                auth=auth,
                ip_address=None,
            )


class TestListAssignments:
    @pytest.mark.asyncio
    async def test_list_assignments_returns_items_and_cursor(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        auth = make_auth()
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        assignment = make_assignment(make_course(auth))
        service.repo.list_assignments.return_value = ([assignment], True)

        items, next_cursor, has_more = await service.list_assignments(
            course_id=None,
            filters=[],
            sort=[],
            search=None,
            cursor=None,
            limit=10,
            auth=auth,
        )

        assert items[0]["id"] == str(assignment.id)
        assert next_cursor is not None
        assert has_more is True

    @pytest.mark.asyncio
    async def test_list_assignments_validates_course_when_given(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        auth = make_auth()
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        service.repo.get_course.return_value = None

        with pytest.raises(NotFoundError, match="Course not found"):
            await service.list_assignments(
                course_id=uuid.uuid4(),
                filters=[],
                sort=[],
                search=None,
                cursor=None,
                limit=10,
                auth=auth,
            )


class TestUploadExercisePdf:
    @pytest.mark.asyncio
    async def test_upload_raises_when_assignment_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        auth = make_auth()
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        service.repo.get_assignment_with_course.return_value = None

        with pytest.raises(NotFoundError, match="Assignment not found"):
            await service.upload_exercise_pdf(
                assignment_id=uuid.uuid4(),
                file=io.BytesIO(b"%PDF"),
                filename="exercise.pdf",
                mime_type="application/pdf",
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_upload_requires_assignment_owner(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        auth = make_auth()
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        course = make_course(auth, teacher_id=uuid.uuid4())
        assignment = make_assignment(course, exercise_type="PRINTABLE_PDF")
        service.repo.get_assignment_with_course.return_value = (assignment, course)

        with pytest.raises(AuthorizationError, match="your own assignments"):
            await service.upload_exercise_pdf(
                assignment_id=assignment.id,
                file=io.BytesIO(b"%PDF"),
                filename="exercise.pdf",
                mime_type="application/pdf",
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_valid_pdf_upload(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth()
        service, repo_in_uow, audit, uow = setup_service(monkeypatch)
        course = make_course(auth)
        assignment = make_assignment(course, exercise_type="PRINTABLE_PDF")
        service.repo.get_assignment_with_course.return_value = (assignment, course)
        save_mock = AsyncMock(return_value=("exercises/file.pdf", "abc123", 1024))
        monkeypatch.setattr(assignment_module.storage, "save", save_mock)
        monkeypatch.setattr(assignment_module.storage, "delete", AsyncMock())

        result = await service.upload_exercise_pdf(
            assignment_id=assignment.id,
            file=io.BytesIO(b"%PDF"),
            filename="exercise.pdf",
            mime_type="application/pdf",
            auth=auth,
            ip_address=None,
        )

        assert result["exercise_pdf_path"] == "exercises/file.pdf"
        repo_in_uow.save_assignment.assert_awaited_once_with(assignment)
        audit.log_event.assert_awaited_once()
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_upload_replaces_existing_pdf(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth()
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        course = make_course(auth)
        assignment = make_assignment(
            course,
            exercise_type="PRINTABLE_PDF",
            pdf_path="old/path.pdf",
        )
        delete_mock = AsyncMock()
        monkeypatch.setattr(assignment_module.storage, "delete", delete_mock)
        monkeypatch.setattr(
            assignment_module.storage,
            "save",
            AsyncMock(return_value=("new/path.pdf", "abc123", 1024)),
        )
        service.repo.get_assignment_with_course.return_value = (assignment, course)

        await service.upload_exercise_pdf(
            assignment_id=assignment.id,
            file=io.BytesIO(b"%PDF"),
            filename="exercise.pdf",
            mime_type="application/pdf",
            auth=auth,
            ip_address=None,
        )

        delete_mock.assert_awaited_once_with("old/path.pdf")

    @pytest.mark.asyncio
    async def test_upload_rejects_non_printable_assignments(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        auth = make_auth()
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        course = make_course(auth)
        assignment = make_assignment(course, exercise_type="STANDARD")
        service.repo.get_assignment_with_course.return_value = (assignment, course)

        with pytest.raises(ValidationError, match="PRINTABLE_PDF"):
            await service.upload_exercise_pdf(
                assignment_id=assignment.id,
                file=io.BytesIO(b"%PDF"),
                filename="exercise.pdf",
                mime_type="application/pdf",
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_upload_rejects_non_pdf_files(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth()
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        course = make_course(auth)
        assignment = make_assignment(course, exercise_type="PRINTABLE_PDF")
        service.repo.get_assignment_with_course.return_value = (assignment, course)

        with pytest.raises(ValidationError, match="Only PDF files"):
            await service.upload_exercise_pdf(
                assignment_id=assignment.id,
                file=io.BytesIO(b"not pdf"),
                filename="exercise.txt",
                mime_type="text/plain",
                auth=auth,
                ip_address=None,
            )


class TestCreateSubmission:
    @pytest.mark.asyncio
    async def test_assignment_must_exist_to_create_submission(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth(role="STD")
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        service.repo.get_assignment_with_course.return_value = None

        with pytest.raises(NotFoundError, match="Assignment not found"):
            await service.create_submission(
                body=SubmissionCreateRequest(assignment_id=uuid.uuid4()),
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_existing_active_submission_is_returned(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        auth = make_auth(role="STD")
        service, repo_in_uow, audit, _uow = setup_service(monkeypatch)
        course = make_course(auth)
        assignment = make_assignment(course)
        existing = make_submission(assignment, auth, status="submitted")
        service.repo.get_assignment_with_course.return_value = (assignment, course)
        service.repo.find_active_submission.return_value = existing

        result = await service.create_submission(
            body=SubmissionCreateRequest(assignment_id=assignment.id),
            auth=auth,
            ip_address=None,
        )

        assert result["id"] == str(existing.id)
        repo_in_uow.create_submission.assert_not_awaited()
        audit.log_event.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_printable_pdf_submission_starts_as_draft(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        auth = make_auth(role="STD")
        service, repo_in_uow, audit, uow = setup_service(monkeypatch)
        course = make_course(auth)
        assignment = make_assignment(course, exercise_type="PRINTABLE_PDF")
        submission = make_submission(assignment, auth, status="draft")
        service.repo.get_assignment_with_course.return_value = (assignment, course)
        service.repo.find_active_submission.return_value = None
        repo_in_uow.create_submission.return_value = submission

        result = await service.create_submission(
            body=SubmissionCreateRequest(assignment_id=assignment.id),
            auth=auth,
            ip_address=None,
        )

        assert result["status"] == "draft"
        repo_in_uow.create_submission.assert_awaited_once()
        audit.log_event.assert_awaited_once()
        service._dispatch_submission_received.assert_not_awaited()
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_standard_submission_is_immediately_submitted(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth(role="STD")
        service, repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        course = make_course(auth)
        assignment = make_assignment(course, exercise_type="STANDARD")
        submission = make_submission(assignment, auth, status="submitted")
        service.repo.get_assignment_with_course.return_value = (assignment, course)
        service.repo.find_active_submission.return_value = None
        repo_in_uow.create_submission.return_value = submission

        result = await service.create_submission(
            body=SubmissionCreateRequest(assignment_id=assignment.id),
            auth=auth,
            ip_address=None,
        )

        assert result["status"] == "submitted"
        service._dispatch_submission_received.assert_awaited_once()


class TestUploadSubmissionFile:
    @pytest.mark.asyncio
    async def test_only_submission_owner_can_upload(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        auth = make_auth(role="STD")
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        course = make_course(auth)
        assignment = make_assignment(course, exercise_type="PRINTABLE_PDF")
        submission = SimpleNamespace(
            id=uuid.uuid4(),
            assignment_id=assignment.id,
            student_id=uuid.uuid4(),
            status="draft",
        )
        service.repo.get_submission_with_context.return_value = (
            submission,
            assignment,
            course,
        )

        with pytest.raises(NotFoundError, match="Submission not found"):
            await service.upload_submission_file(
                submission_id=submission.id,
                file=io.BytesIO(b"image"),
                filename="scan.jpg",
                mime_type="image/jpeg",
                file_type_hint="SOLUTION_SCAN",
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_cannot_upload_to_graded_submission(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        auth = make_auth(role="STD")
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        course = make_course(auth)
        assignment = make_assignment(course, exercise_type="PRINTABLE_PDF")
        submission = make_submission(assignment, auth, status="graded")
        service.repo.get_submission_with_context.return_value = (
            submission,
            assignment,
            course,
        )

        with pytest.raises(ValidationError, match="graded or returned"):
            await service.upload_submission_file(
                submission_id=submission.id,
                file=io.BytesIO(b"image"),
                filename="scan.jpg",
                mime_type="image/jpeg",
                file_type_hint="SOLUTION_SCAN",
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_upload_rejects_when_max_files_reached(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        auth = make_auth(role="STD")
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        course = make_course(auth)
        assignment = make_assignment(course, exercise_type="PRINTABLE_PDF")
        submission = make_submission(assignment, auth)
        service.repo.get_submission_with_context.return_value = (
            submission,
            assignment,
            course,
        )
        service.repo.count_submission_files.return_value = (
            assignment_module.MAX_FILES_PER_SUBMISSION
        )

        with pytest.raises(ValidationError, match="Maximum of"):
            await service.upload_submission_file(
                submission_id=submission.id,
                file=io.BytesIO(b"image"),
                filename="scan.jpg",
                mime_type="image/jpeg",
                file_type_hint="SOLUTION_SCAN",
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_upload_rejects_invalid_file_hint(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        auth = make_auth(role="STD")
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        course = make_course(auth)
        assignment = make_assignment(course, exercise_type="PRINTABLE_PDF")
        submission = make_submission(assignment, auth)
        service.repo.get_submission_with_context.return_value = (
            submission,
            assignment,
            course,
        )
        service.repo.count_submission_files.return_value = 0

        with pytest.raises(ValidationError, match="file_type_hint must be one of"):
            await service.upload_submission_file(
                submission_id=submission.id,
                file=io.BytesIO(b"image"),
                filename="scan.jpg",
                mime_type="image/jpeg",
                file_type_hint="INVALID",
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_valid_file_upload(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth(role="STD")
        service, repo_in_uow, audit, uow = setup_service(monkeypatch)
        course = make_course(auth)
        assignment = make_assignment(course, exercise_type="PRINTABLE_PDF")
        submission = make_submission(assignment, auth)
        submission_file = SimpleNamespace(
            id=uuid.uuid4(),
            submission_id=submission.id,
            file_path="submissions/scan.jpg",
            checksum="abc123",
            mime_type="image/jpeg",
            file_size=2048,
            file_type_hint="SOLUTION_SCAN",
        )
        validate_mock = Mock()
        monkeypatch.setattr(assignment_module, "validate_mime_type", validate_mock)
        monkeypatch.setattr(
            assignment_module.storage,
            "save",
            AsyncMock(return_value=("submissions/scan.jpg", "abc123", 2048)),
        )
        service.repo.get_submission_with_context.return_value = (
            submission,
            assignment,
            course,
        )
        service.repo.count_submission_files.return_value = 0
        repo_in_uow.create_submission_file.return_value = submission_file

        result = await service.upload_submission_file(
            submission_id=submission.id,
            file=io.BytesIO(b"image"),
            filename="scan.jpg",
            mime_type="image/jpeg",
            file_type_hint="SOLUTION_SCAN",
            auth=auth,
            ip_address=None,
        )

        assert result["file_path"] == "submissions/scan.jpg"
        validate_mock.assert_called_once_with("image/jpeg")
        repo_in_uow.create_submission_file.assert_awaited_once()
        audit.log_event.assert_awaited_once()
        assert uow.committed is True


class TestFinalizeSubmission:
    @pytest.mark.asyncio
    async def test_finalize_requires_existing_submission(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        auth = make_auth(role="STD")
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        service.repo.get_submission_with_context.return_value = None

        with pytest.raises(NotFoundError, match="Submission not found"):
            await service.finalize_submission(
                submission_id=uuid.uuid4(),
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_only_owner_can_finalize_submission(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        auth = make_auth(role="STD")
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        course = make_course(auth)
        assignment = make_assignment(course, exercise_type="PRINTABLE_PDF")
        submission = SimpleNamespace(
            id=uuid.uuid4(),
            assignment_id=assignment.id,
            student_id=uuid.uuid4(),
            status="draft",
            submitted_at=None,
        )
        service.repo.get_submission_with_context.return_value = (
            submission,
            assignment,
            course,
        )

        with pytest.raises(NotFoundError, match="Submission not found"):
            await service.finalize_submission(
                submission_id=submission.id,
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_only_draft_submission_can_be_finalized(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        auth = make_auth(role="STD")
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        course = make_course(auth)
        assignment = make_assignment(course, exercise_type="PRINTABLE_PDF")
        submission = make_submission(assignment, auth, status="submitted")
        service.repo.get_submission_with_context.return_value = (
            submission,
            assignment,
            course,
        )

        with pytest.raises(ValidationError, match="Only draft submissions"):
            await service.finalize_submission(
                submission_id=submission.id,
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_printable_pdf_requires_uploaded_file(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        auth = make_auth(role="STD")
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        course = make_course(auth)
        assignment = make_assignment(course, exercise_type="PRINTABLE_PDF")
        submission = make_submission(assignment, auth, status="draft")
        service.repo.get_submission_with_context.return_value = (
            submission,
            assignment,
            course,
        )
        service.repo.count_submission_files.return_value = 0

        with pytest.raises(
            ValidationError, match="require at least one uploaded solution file"
        ):
            await service.finalize_submission(
                submission_id=submission.id,
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_valid_finalize_submission(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth(role="STD")
        service, repo_in_uow, audit, uow = setup_service(monkeypatch)
        course = make_course(auth)
        assignment = make_assignment(course, exercise_type="PRINTABLE_PDF")
        submission = make_submission(assignment, auth, status="draft")
        fixed_now = utc_datetime(2026, 3, 30, 12)
        monkeypatch.setattr(assignment_module, "_utc_now", lambda: fixed_now)
        service.repo.get_submission_with_context.return_value = (
            submission,
            assignment,
            course,
        )
        service.repo.count_submission_files.return_value = 1

        result = await service.finalize_submission(
            submission_id=submission.id,
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["status"] == "submitted"
        assert submission.status == "submitted"
        assert submission.submitted_at == fixed_now
        repo_in_uow.save_submission.assert_awaited_once_with(submission)
        audit.log_event.assert_awaited_once()
        service._dispatch_submission_received.assert_awaited_once()
        assert uow.committed is True
