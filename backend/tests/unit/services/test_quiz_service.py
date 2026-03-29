"""Unit tests for LMS quiz service."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.dependencies import AuthContext
from app.core.exceptions import NotFoundError, ValidationError
from app.schemas.quiz import QuizCreateRequest, QuizQuestionInput, QuizRespondRequest
from app.services.lms.quiz_service import QuizService
from app.services.lms import quiz_service as quiz_module


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
    service = QuizService(AsyncMock())
    service.quiz_repo = AsyncMock()
    service._dispatch_quiz_completed = AsyncMock()

    quiz_repo_in_uow = AsyncMock()
    audit = AsyncMock()
    uow = FakeUnitOfWork()

    monkeypatch.setattr(quiz_module, "UnitOfWork", lambda _db: uow)
    monkeypatch.setattr(quiz_module, "QuizRepository", lambda _session: quiz_repo_in_uow)
    monkeypatch.setattr(quiz_module, "AuditService", lambda _session: audit)

    return service, quiz_repo_in_uow, audit, uow


def make_quiz(auth: AuthContext, *, status: str = "draft", school_id=None, max_attempts: int = 2):
    return SimpleNamespace(
        id=uuid.uuid4(),
        school_id=auth.school_id if school_id is None else school_id,
        created_by=auth.user_id,
        title="Quiz Fractions",
        description="Revise fractions",
        subject="math",
        level_band="6eme",
        difficulty="MEDIUM",
        time_limit_minutes=15,
        max_attempts=max_attempts,
        shuffle_questions=False,
        status=status,
    )


def make_question(quiz_id: uuid.UUID, *, order: int = 0, points: int = 2):
    return SimpleNamespace(
        id=uuid.uuid4(),
        quiz_id=quiz_id,
        question_type="MCQ",
        question_text="2/4 equals?",
        question_media_path=None,
        options=[{"id": "a", "text": "1/2"}],
        correct_answer=["a"],
        points=points,
        order=order,
        explanation="2/4 simplifies to 1/2",
    )


def make_attempt(quiz, auth: AuthContext, *, status: str = "STARTED", attempt_no: int = 1):
    return SimpleNamespace(
        id=uuid.uuid4(),
        quiz_id=quiz.id,
        student_id=auth.user_id,
        attempt_no=attempt_no,
        started_at=utc_datetime(2026, 3, 30, 10),
        completed_at=None,
        score=None,
        max_score=10,
        status=status,
    )


class TestCreateQuiz:
    @pytest.mark.asyncio
    async def test_teacher_created_quiz_is_school_scoped(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth("TCH")
        service, quiz_repo_in_uow, audit, uow = setup_service(monkeypatch)
        quiz = make_quiz(auth, status="draft")
        questions = [make_question(quiz.id)]
        quiz_repo_in_uow.create_quiz.return_value = quiz
        quiz_repo_in_uow.create_quiz_questions.return_value = questions

        result = await service.create_quiz(
            body=QuizCreateRequest(
                title="Quiz Fractions",
                subject="math",
                questions=[
                    QuizQuestionInput(
                        question_type="MCQ",
                        question_text="2/4 equals?",
                        options=[{"id": "a", "text": "1/2"}],
                        correct_answer=["a"],
                        points=2,
                        order=0,
                    )
                ],
            ),
            auth=auth,
            ip_address=None,
        )

        assert result["school_id"] == str(auth.school_id)
        assert result["question_count"] == 1
        assert result["questions"][0]["correct_answer"] == ["a"]
        quiz_repo_in_uow.create_quiz.assert_awaited_once()
        audit.log_event.assert_awaited_once()
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_content_manager_creates_platform_quiz(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth("CONTENT_MGR")
        service, quiz_repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        quiz = make_quiz(auth, status="draft")
        quiz.school_id = None
        quiz_repo_in_uow.create_quiz.return_value = quiz
        quiz_repo_in_uow.create_quiz_questions.return_value = []

        result = await service.create_quiz(
            body=QuizCreateRequest(title="Platform quiz"),
            auth=auth,
            ip_address=None,
        )

        assert result["school_id"] is None


class TestPublishQuiz:
    @pytest.mark.asyncio
    async def test_publish_requires_draft_status(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth("TCH")
        service, _quiz_repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        quiz = make_quiz(auth, status="published")
        service.quiz_repo.get_quiz.return_value = quiz

        with pytest.raises(ValidationError, match="not in draft status"):
            await service.publish_quiz(
                quiz_id=quiz.id,
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_publish_requires_questions(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth("TCH")
        service, _quiz_repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        quiz = make_quiz(auth, status="draft")
        service.quiz_repo.get_quiz.return_value = quiz
        service.quiz_repo.count_quiz_questions.return_value = 0

        with pytest.raises(ValidationError, match="no questions"):
            await service.publish_quiz(
                quiz_id=quiz.id,
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_publish_success(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth("TCH")
        service, quiz_repo_in_uow, audit, uow = setup_service(monkeypatch)
        quiz = make_quiz(auth, status="draft")
        service.quiz_repo.get_quiz.return_value = quiz
        service.quiz_repo.count_quiz_questions.return_value = 3

        result = await service.publish_quiz(
            quiz_id=quiz.id,
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result == {"id": str(quiz.id), "status": "published"}
        assert quiz.status == "published"
        quiz_repo_in_uow.save_quiz.assert_awaited_once_with(quiz)
        audit.log_event.assert_awaited_once()
        assert uow.committed is True


class TestStartQuizAttempt:
    @pytest.mark.asyncio
    async def test_start_attempt_hides_quiz_from_other_school_students(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth("STD")
        service, _quiz_repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        quiz = make_quiz(auth, status="published", school_id=uuid.uuid4())
        service.quiz_repo.get_quiz.return_value = quiz

        with pytest.raises(NotFoundError, match="Quiz not found"):
            await service.start_quiz_attempt(
                quiz_id=quiz.id,
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_start_attempt_requires_published_quiz(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth("STD")
        service, _quiz_repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        service.quiz_repo.get_quiz.return_value = None

        with pytest.raises(NotFoundError, match="Quiz not found"):
            await service.start_quiz_attempt(
                quiz_id=uuid.uuid4(),
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_start_attempt_rejects_when_max_attempts_reached(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth("STD")
        service, _quiz_repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        quiz = make_quiz(auth, status="published", max_attempts=1)
        service.quiz_repo.get_quiz.return_value = quiz
        service.quiz_repo.count_student_attempts.return_value = 1

        with pytest.raises(ValidationError, match="Maximum attempts"):
            await service.start_quiz_attempt(
                quiz_id=quiz.id,
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_start_attempt_returns_existing_active_attempt(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth("STD")
        service, _quiz_repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        quiz = make_quiz(auth, status="published")
        active_attempt = make_attempt(quiz, auth)
        service.quiz_repo.get_quiz.return_value = quiz
        service.quiz_repo.count_student_attempts.return_value = 0
        service.quiz_repo.get_active_attempt.return_value = active_attempt

        result = await service.start_quiz_attempt(
            quiz_id=quiz.id,
            auth=auth,
            ip_address=None,
        )

        assert result["id"] == str(active_attempt.id)

    @pytest.mark.asyncio
    async def test_start_attempt_creates_new_attempt(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth("STD")
        service, quiz_repo_in_uow, audit, uow = setup_service(monkeypatch)
        quiz = make_quiz(auth, status="published", max_attempts=3)
        attempt = make_attempt(quiz, auth, attempt_no=2)
        fixed_now = utc_datetime(2026, 3, 30, 10)
        monkeypatch.setattr(quiz_module, "_utc_now", lambda: fixed_now)
        service.quiz_repo.get_quiz.return_value = quiz
        service.quiz_repo.count_student_attempts.return_value = 1
        service.quiz_repo.get_active_attempt.return_value = None
        quiz_repo_in_uow.sum_quiz_points.return_value = 12
        quiz_repo_in_uow.create_quiz_attempt.return_value = attempt

        result = await service.start_quiz_attempt(
            quiz_id=quiz.id,
            auth=auth,
            ip_address=None,
        )

        assert result["attempt_no"] == 2
        quiz_repo_in_uow.create_quiz_attempt.assert_awaited_once()
        audit.log_event.assert_awaited_once()
        assert uow.committed is True


class TestRespondToQuizQuestion:
    @pytest.mark.asyncio
    async def test_attempt_must_exist_and_belong_to_student(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth("STD")
        service, _quiz_repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        service.quiz_repo.get_quiz_attempt.return_value = None

        with pytest.raises(NotFoundError, match="Attempt not found"):
            await service.respond_to_quiz_question(
                attempt_id=uuid.uuid4(),
                body=QuizRespondRequest(question_id=uuid.uuid4(), student_answer="a"),
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_completed_attempt_cannot_accept_more_answers(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth("STD")
        service, _quiz_repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        quiz = make_quiz(auth, status="published")
        attempt = make_attempt(quiz, auth, status="COMPLETED")
        service.quiz_repo.get_quiz_attempt.return_value = attempt

        with pytest.raises(ValidationError, match="already completed"):
            await service.respond_to_quiz_question(
                attempt_id=attempt.id,
                body=QuizRespondRequest(question_id=uuid.uuid4(), student_answer="a"),
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_time_limit_exceeded_marks_attempt_timed_out(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth("STD")
        service, quiz_repo_in_uow, _audit, uow = setup_service(monkeypatch)
        quiz = make_quiz(auth, status="published")
        quiz.time_limit_minutes = 10
        attempt = make_attempt(quiz, auth, status="STARTED")
        attempt.started_at = utc_datetime(2026, 3, 30, 9)
        monkeypatch.setattr(quiz_module, "_utc_now", lambda: utc_datetime(2026, 3, 30, 10, 0))
        service.quiz_repo.get_quiz_attempt.return_value = attempt
        service.quiz_repo.get_quiz.return_value = quiz

        with pytest.raises(ValidationError, match="Time limit exceeded"):
            await service.respond_to_quiz_question(
                attempt_id=attempt.id,
                body=QuizRespondRequest(question_id=uuid.uuid4(), student_answer="a"),
                auth=auth,
            )

        assert attempt.status == "TIMED_OUT"
        quiz_repo_in_uow.save_quiz_attempt.assert_awaited_once_with(attempt)
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_question_must_belong_to_quiz(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth("STD")
        service, _quiz_repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        quiz = make_quiz(auth, status="published")
        attempt = make_attempt(quiz, auth, status="STARTED")
        service.quiz_repo.get_quiz_attempt.return_value = attempt
        service.quiz_repo.get_quiz.return_value = quiz
        service.quiz_repo.get_quiz_question.return_value = None
        monkeypatch.setattr(quiz_module, "_utc_now", lambda: utc_datetime(2026, 3, 30, 10))

        with pytest.raises(NotFoundError, match="Question not found"):
            await service.respond_to_quiz_question(
                attempt_id=attempt.id,
                body=QuizRespondRequest(question_id=uuid.uuid4(), student_answer="a"),
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_existing_response_is_updated(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth("STD")
        service, quiz_repo_in_uow, _audit, uow = setup_service(monkeypatch)
        quiz = make_quiz(auth, status="published")
        attempt = make_attempt(quiz, auth, status="STARTED")
        question = make_question(quiz.id)
        response = SimpleNamespace(
            id=uuid.uuid4(),
            attempt_id=attempt.id,
            question_id=question.id,
            student_answer="b",
            answered_at=None,
            is_correct=True,
            points_earned=2.0,
        )
        fixed_now = utc_datetime(2026, 3, 30, 10)
        monkeypatch.setattr(quiz_module, "_utc_now", lambda: fixed_now)
        service.quiz_repo.get_quiz_attempt.return_value = attempt
        service.quiz_repo.get_quiz.return_value = quiz
        service.quiz_repo.get_quiz_question.return_value = question
        service.quiz_repo.get_quiz_response.return_value = response

        result = await service.respond_to_quiz_question(
            attempt_id=attempt.id,
            body=QuizRespondRequest(question_id=question.id, student_answer="a"),
            auth=auth,
        )

        assert result["id"] == str(response.id)
        assert response.student_answer == "a"
        assert response.is_correct is None
        quiz_repo_in_uow.save_quiz_response.assert_awaited_once_with(response)
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_new_response_is_created(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth("STD")
        service, quiz_repo_in_uow, _audit, uow = setup_service(monkeypatch)
        quiz = make_quiz(auth, status="published")
        attempt = make_attempt(quiz, auth, status="STARTED")
        question = make_question(quiz.id)
        created = SimpleNamespace(
            id=uuid.uuid4(),
            attempt_id=attempt.id,
            question_id=question.id,
        )
        fixed_now = utc_datetime(2026, 3, 30, 10)
        monkeypatch.setattr(quiz_module, "_utc_now", lambda: fixed_now)
        service.quiz_repo.get_quiz_attempt.return_value = attempt
        service.quiz_repo.get_quiz.return_value = quiz
        service.quiz_repo.get_quiz_question.return_value = question
        service.quiz_repo.get_quiz_response.return_value = None
        quiz_repo_in_uow.create_quiz_response.return_value = created

        result = await service.respond_to_quiz_question(
            attempt_id=attempt.id,
            body=QuizRespondRequest(question_id=question.id, student_answer="a"),
            auth=auth,
        )

        assert result["id"] == str(created.id)
        quiz_repo_in_uow.create_quiz_response.assert_awaited_once()
        assert uow.committed is True


class TestSubmitQuizAttempt:
    @pytest.mark.asyncio
    async def test_attempt_must_exist(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth("STD")
        service, _quiz_repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        service.quiz_repo.get_quiz_attempt.return_value = None

        with pytest.raises(NotFoundError, match="Attempt not found"):
            await service.submit_quiz_attempt(
                attempt_id=uuid.uuid4(),
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_completed_attempt_cannot_be_submitted_again(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth("STD")
        service, _quiz_repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        attempt = make_attempt(make_quiz(auth, status="published"), auth, status="COMPLETED")
        service.quiz_repo.get_quiz_attempt.return_value = attempt

        with pytest.raises(ValidationError, match="already completed"):
            await service.submit_quiz_attempt(
                attempt_id=attempt.id,
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_submit_attempt_auto_grades_and_dispatches(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth("STD")
        service, quiz_repo_in_uow, audit, uow = setup_service(monkeypatch)
        attempt = make_attempt(make_quiz(auth, status="published"), auth, status="STARTED")
        completed_attempt = make_attempt(make_quiz(auth, status="published"), auth, status="COMPLETED")
        completed_attempt.id = attempt.id
        completed_attempt.quiz_id = attempt.quiz_id
        completed_attempt.score = 8.0
        completed_attempt.max_score = 10
        service.quiz_repo.get_quiz_attempt.side_effect = [attempt]
        quiz_repo_in_uow.get_quiz_attempt.return_value = completed_attempt
        grade_attempt_mock = AsyncMock(return_value=(8.0, 10))
        monkeypatch.setattr(quiz_module, "grade_attempt", grade_attempt_mock)

        result = await service.submit_quiz_attempt(
            attempt_id=attempt.id,
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["score"] == 8.0
        grade_attempt_mock.assert_awaited_once()
        audit.log_event.assert_awaited_once()
        service._dispatch_quiz_completed.assert_awaited_once()
        assert uow.committed is True


class TestQuizAnalytics:
    @pytest.mark.asyncio
    async def test_analytics_computes_average_percentage(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth("TCH")
        service, _quiz_repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        quiz = make_quiz(auth, status="published")
        question = make_question(quiz.id, points=4)
        service.quiz_repo.get_quiz.return_value = quiz
        service.quiz_repo.get_attempt_stats.return_value = (3, 2, 3.0, 4.0, 2.0)
        service.quiz_repo.sum_quiz_points.return_value = 4
        service.quiz_repo.list_quiz_questions.return_value = [question]
        service.quiz_repo.get_question_response_stats.return_value = (2, 1)

        result = await service.get_quiz_analytics(
            quiz_id=quiz.id,
            auth=auth,
        )

        assert result["average_percentage"] == 75.0
        assert result["question_stats"][0]["accuracy"] == 50.0
