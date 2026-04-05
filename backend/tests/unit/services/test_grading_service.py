"""Unit tests for LMS grading service."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.dependencies import AuthContext
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.schemas.lms import GradeRequest
from app.services.lms._helpers import calculate_late_penalty
from app.services.lms.grading_service import GradingService
from app.services.lms import grading_service as grading_module


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


def make_bundle(
    *,
    auth: AuthContext,
    teacher_id: uuid.UUID | None = None,
    school_id: uuid.UUID | None = None,
    total_points: int = 20,
    rubric_id: uuid.UUID | None = None,
    submission_status: str = "submitted",
):
    course = SimpleNamespace(
        id=uuid.uuid4(),
        school_id=school_id or auth.school_id,
        teacher_id=teacher_id or auth.user_id,
        title="Math 6A",
        class_id=uuid.uuid4(),
    )
    assignment = SimpleNamespace(
        id=uuid.uuid4(),
        course_id=course.id,
        teacher_id=course.teacher_id,
        title="Fractions",
        due_at=utc_datetime(2026, 3, 30, 8),
        total_points=total_points,
        grace_period_hours=0,
        late_penalty_per_day=2.0,
        max_late_days=3,
        allow_late=True,
        rubric_id=rubric_id,
        exercise_type="STANDARD",
    )
    submission = SimpleNamespace(
        id=uuid.uuid4(),
        assignment_id=assignment.id,
        student_id=uuid.uuid4(),
        status=submission_status,
        submitted_at=utc_datetime(2026, 3, 31, 8),
    )
    return submission, assignment, course


def setup_service(monkeypatch: pytest.MonkeyPatch):
    service = GradingService(AsyncMock())
    service.repo = AsyncMock()
    service._dispatch_grade_published = AsyncMock()

    repo_in_uow = AsyncMock()
    audit = AsyncMock()
    uow = FakeUnitOfWork()

    monkeypatch.setattr(grading_module, "UnitOfWork", lambda _db: uow)
    monkeypatch.setattr(grading_module, "LMSRepository", lambda _session: repo_in_uow)
    monkeypatch.setattr(grading_module, "AuditService", lambda _session: audit)

    return service, repo_in_uow, audit, uow


class TestGradeSubmission:
    @pytest.mark.asyncio
    async def test_valid_grade_creates_record(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth()
        service, repo_in_uow, audit, uow = setup_service(monkeypatch)
        submission, assignment, course = make_bundle(auth=auth)
        created_grade = SimpleNamespace(
            id=uuid.uuid4(),
            submission_id=submission.id,
            teacher_id=auth.user_id,
            score=18.0,
            original_score=20.0,
            late_penalty=2.0,
            late_days=1,
            penalty_overridden=False,
            feedback_text="Bien",
            published_at=None,
        )
        service.repo.get_submission_with_context.return_value = (
            submission,
            assignment,
            course,
        )
        repo_in_uow.get_grade_for_submission.return_value = None
        repo_in_uow.create_grade.return_value = created_grade
        monkeypatch.setattr(
            grading_module,
            "calculate_late_penalty",
            lambda **_: {
                "original_score": 20.0,
                "adjusted_score": 18.0,
                "late_penalty": 2.0,
                "late_days": 1,
            },
        )

        result = await service.grade_submission(
            submission_id=submission.id,
            body=GradeRequest(score=20, feedback_text="Bien", publish=False),
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["id"] == str(created_grade.id)
        assert result["score"] == 18.0
        repo_in_uow.create_grade.assert_awaited_once()
        repo_in_uow.save_submission.assert_awaited_once_with(submission)
        audit.log_event.assert_awaited_once()
        assert submission.status == "graded"
        assert uow.committed is True
        service._dispatch_grade_published.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_existing_grade_is_updated(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth()
        service, repo_in_uow, _audit, uow = setup_service(monkeypatch)
        submission, assignment, course = make_bundle(auth=auth, submission_status="graded")
        existing_grade = SimpleNamespace(
            id=uuid.uuid4(),
            submission_id=submission.id,
            teacher_id=auth.user_id,
            score=10.0,
            original_score=10.0,
            late_penalty=0.0,
            late_days=0,
            penalty_overridden=True,
            feedback_text=None,
            published_at=None,
        )
        service.repo.get_submission_with_context.return_value = (
            submission,
            assignment,
            course,
        )
        repo_in_uow.get_grade_for_submission.return_value = existing_grade
        monkeypatch.setattr(
            grading_module,
            "calculate_late_penalty",
            lambda **_: {
                "original_score": 19.0,
                "adjusted_score": 17.0,
                "late_penalty": 2.0,
                "late_days": 1,
            },
        )
        fixed_now = utc_datetime(2026, 3, 30, 12)
        monkeypatch.setattr(grading_module, "_utc_now", lambda: fixed_now)

        result = await service.grade_submission(
            submission_id=submission.id,
            body=GradeRequest(score=19, feedback_text="Updated", publish=True),
            auth=auth,
            ip_address=None,
        )

        assert result["score"] == 17.0
        assert existing_grade.original_score == 19.0
        assert existing_grade.late_penalty == 2.0
        assert existing_grade.penalty_overridden is False
        assert existing_grade.published_at == fixed_now
        repo_in_uow.create_grade.assert_not_awaited()
        repo_in_uow.save_grade.assert_awaited_once_with(existing_grade)
        assert uow.committed is True
        service._dispatch_grade_published.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_submission_not_found(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth()
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        service.repo.get_submission_with_context.return_value = None

        with pytest.raises(NotFoundError, match="Submission not found"):
            await service.grade_submission(
                submission_id=uuid.uuid4(),
                body=GradeRequest(score=15),
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_wrong_teacher_cannot_grade(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth()
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        service.repo.get_submission_with_context.return_value = make_bundle(
            auth=auth,
            teacher_id=uuid.uuid4(),
        )

        with pytest.raises(AuthorizationError, match="your own courses"):
            await service.grade_submission(
                submission_id=uuid.uuid4(),
                body=GradeRequest(score=15),
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_rubric_assignments_require_other_endpoint(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth()
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        service.repo.get_submission_with_context.return_value = make_bundle(
            auth=auth,
            rubric_id=uuid.uuid4(),
        )

        with pytest.raises(ValidationError, match="rubric grading"):
            await service.grade_submission(
                submission_id=uuid.uuid4(),
                body=GradeRequest(score=15),
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_only_submitted_or_graded_status_can_be_graded(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth()
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        service.repo.get_submission_with_context.return_value = make_bundle(
            auth=auth,
            submission_status="draft",
        )

        with pytest.raises(ValidationError, match="submitted or graded"):
            await service.grade_submission(
                submission_id=uuid.uuid4(),
                body=GradeRequest(score=15),
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_score_cannot_exceed_assignment_total(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth()
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        service.repo.get_submission_with_context.return_value = make_bundle(
            auth=auth,
            total_points=20,
        )

        with pytest.raises(ValidationError, match="cannot exceed total points"):
            await service.grade_submission(
                submission_id=uuid.uuid4(),
                body=GradeRequest(score=25),
                auth=auth,
                ip_address=None,
            )


class TestOverrideLatePenalty:
    @pytest.mark.asyncio
    async def test_submission_not_found(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth()
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        service.repo.get_submission_with_context.return_value = None

        with pytest.raises(NotFoundError, match="Submission not found"):
            await service.override_late_penalty(
                submission_id=uuid.uuid4(),
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_wrong_teacher_cannot_override_penalty(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth()
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        service.repo.get_submission_with_context.return_value = make_bundle(
            auth=auth,
            teacher_id=uuid.uuid4(),
        )

        with pytest.raises(AuthorizationError, match="own courses"):
            await service.override_late_penalty(
                submission_id=uuid.uuid4(),
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_grade_not_found(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth()
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        service.repo.get_submission_with_context.return_value = make_bundle(auth=auth)
        service.repo.get_grade_for_submission.return_value = None

        with pytest.raises(NotFoundError, match="Grade not found"):
            await service.override_late_penalty(
                submission_id=uuid.uuid4(),
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_grade_without_penalty_cannot_be_overridden(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth()
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        grade = SimpleNamespace(
            id=uuid.uuid4(),
            submission_id=uuid.uuid4(),
            original_score=None,
            late_penalty=0.0,
            late_days=0,
            penalty_overridden=False,
            score=17.0,
            teacher_id=auth.user_id,
            feedback_text=None,
            published_at=None,
        )
        service.repo.get_submission_with_context.return_value = make_bundle(auth=auth)
        service.repo.get_grade_for_submission.return_value = grade

        with pytest.raises(ValidationError, match="does not have a late penalty"):
            await service.override_late_penalty(
                submission_id=grade.submission_id,
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_already_overridden_grade_returns_without_write(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth()
        service, repo_in_uow, audit, _uow = setup_service(monkeypatch)
        grade = SimpleNamespace(
            id=uuid.uuid4(),
            submission_id=uuid.uuid4(),
            original_score=18.0,
            late_penalty=2.0,
            late_days=1,
            penalty_overridden=True,
            score=18.0,
            teacher_id=auth.user_id,
            feedback_text=None,
            published_at=None,
        )
        service.repo.get_submission_with_context.return_value = make_bundle(auth=auth)
        service.repo.get_grade_for_submission.return_value = grade

        result = await service.override_late_penalty(
            submission_id=grade.submission_id,
            auth=auth,
            ip_address=None,
        )

        assert result["score"] == 18.0
        repo_in_uow.save_grade.assert_not_awaited()
        audit.log_event.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_valid_override_restores_original_score(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth()
        service, repo_in_uow, audit, uow = setup_service(monkeypatch)
        grade = SimpleNamespace(
            id=uuid.uuid4(),
            submission_id=uuid.uuid4(),
            original_score=19.5,
            late_penalty=2.5,
            late_days=2,
            penalty_overridden=False,
            score=17.0,
            teacher_id=auth.user_id,
            feedback_text="Good",
            published_at=None,
        )
        service.repo.get_submission_with_context.return_value = make_bundle(auth=auth)
        service.repo.get_grade_for_submission.return_value = grade

        result = await service.override_late_penalty(
            submission_id=grade.submission_id,
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["score"] == 19.5
        assert grade.score == 19.5
        assert grade.penalty_overridden is True
        repo_in_uow.save_grade.assert_awaited_once_with(grade)
        audit.log_event.assert_awaited_once()
        assert uow.committed is True


class TestCalculateLatePenalty:
    def test_returns_original_score_when_submission_has_no_timestamp(self):
        assignment = SimpleNamespace(
            due_at=utc_datetime(2026, 3, 30, 8),
            grace_period_hours=0,
            allow_late=True,
            max_late_days=3,
            late_penalty_per_day=2.0,
        )
        submission = SimpleNamespace(submitted_at=None)

        result = calculate_late_penalty(
            assignment=assignment,
            submission=submission,
            original_score=18.0,
        )

        assert result == {
            "original_score": 18.0,
            "adjusted_score": 18.0,
            "late_penalty": 0.0,
            "late_days": 0,
        }

    def test_within_grace_period_has_no_penalty(self):
        assignment = SimpleNamespace(
            due_at=utc_datetime(2026, 3, 30, 8),
            grace_period_hours=4,
            allow_late=True,
            max_late_days=3,
            late_penalty_per_day=2.0,
        )
        submission = SimpleNamespace(submitted_at=utc_datetime(2026, 3, 30, 11))

        result = calculate_late_penalty(
            assignment=assignment,
            submission=submission,
            original_score=16.0,
        )

        assert result["late_penalty"] == 0.0
        assert result["adjusted_score"] == 16.0

    def test_late_submissions_not_allowed_raise_validation_error(self):
        assignment = SimpleNamespace(
            due_at=utc_datetime(2026, 3, 30, 8),
            grace_period_hours=0,
            allow_late=False,
            max_late_days=3,
            late_penalty_per_day=2.0,
        )
        submission = SimpleNamespace(submitted_at=utc_datetime(2026, 3, 31, 8))

        with pytest.raises(ValidationError, match="Late submissions are not allowed"):
            calculate_late_penalty(
                assignment=assignment,
                submission=submission,
                original_score=16.0,
            )

    def test_submission_exceeding_max_late_days_raises(self):
        assignment = SimpleNamespace(
            due_at=utc_datetime(2026, 3, 30, 8),
            grace_period_hours=0,
            allow_late=True,
            max_late_days=1,
            late_penalty_per_day=2.0,
        )
        submission = SimpleNamespace(submitted_at=utc_datetime(2026, 4, 2, 8))

        with pytest.raises(ValidationError, match="maximum allowed late days") as exc_info:
            calculate_late_penalty(
                assignment=assignment,
                submission=submission,
                original_score=16.0,
            )

        assert exc_info.value.details == {"late_days": 3, "max_late_days": 1}

    def test_late_days_round_up_partial_days(self):
        assignment = SimpleNamespace(
            due_at=utc_datetime(2026, 3, 30, 8),
            grace_period_hours=0,
            allow_late=True,
            max_late_days=3,
            late_penalty_per_day=1.5,
        )
        submission = SimpleNamespace(
            submitted_at=utc_datetime(2026, 3, 31, 20),
        )

        result = calculate_late_penalty(
            assignment=assignment,
            submission=submission,
            original_score=18.0,
        )

        assert result["late_days"] == 2
        assert result["late_penalty"] == 3.0
        assert result["adjusted_score"] == 15.0

    def test_penalty_never_drops_score_below_zero(self):
        assignment = SimpleNamespace(
            due_at=utc_datetime(2026, 3, 30, 8),
            grace_period_hours=0,
            allow_late=True,
            max_late_days=5,
            late_penalty_per_day=10.0,
        )
        submission = SimpleNamespace(submitted_at=utc_datetime(2026, 4, 1, 8))

        result = calculate_late_penalty(
            assignment=assignment,
            submission=submission,
            original_score=5.0,
        )

        assert result["late_days"] == 2
        assert result["late_penalty"] == 20.0
        assert result["adjusted_score"] == 0.0
