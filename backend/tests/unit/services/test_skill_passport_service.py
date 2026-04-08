"""Unit tests for life-skills passport services."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio

from app.core.dependencies import AuthContext
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.services import skill_passport_service as skill_module
from app.services.skill_passport_service import SkillPassportService


@pytest_asyncio.fixture(autouse=True)
async def clear_analytics_cache():
    yield


@pytest_asyncio.fixture(autouse=True)
async def override_test_redis():
    yield


@pytest_asyncio.fixture(autouse=True)
async def dispose_app_engine_pool():
    yield


def make_auth(role: str = "ADM") -> AuthContext:
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


def make_dimension() -> SimpleNamespace:
    now = datetime(2026, 4, 4, 12, 0, tzinfo=UTC)
    return SimpleNamespace(
        id=uuid.uuid4(),
        code="autonomy",
        name_fr="Autonomie",
        name_ar="الاستقلالية",
        name_en="Autonomy",
        description_fr="Autonomie au quotidien",
        icon="autonomy-icon",
        display_order=1,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def make_milestone(
    *,
    dimension: SimpleNamespace | None = None,
    level: int = 1,
) -> SimpleNamespace:
    now = datetime(2026, 4, 4, 12, 15, tzinfo=UTC)
    dimension = dimension or make_dimension()
    return SimpleNamespace(
        id=uuid.uuid4(),
        dimension_id=dimension.id,
        dimension=dimension,
        code=f"{dimension.code}_level_{level}",
        name_fr=f"Niveau {level}",
        name_ar=f"المستوى {level}",
        level=level,
        rule_config={
            "metric": "submissions_on_time",
            "threshold": 1,
            "period_days": 30,
        },
        badge_icon="badge-star",
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def make_progress(
    auth: AuthContext,
    *,
    student_id: uuid.UUID | None = None,
    milestone: SimpleNamespace | None = None,
    status: str = "locked",
    current_value: float = 0.0,
) -> SimpleNamespace:
    now = datetime(2026, 4, 4, 12, 30, tzinfo=UTC)
    milestone = milestone or make_milestone()
    return SimpleNamespace(
        id=uuid.uuid4(),
        student_id=student_id or uuid.uuid4(),
        school_id=auth.school_id,
        milestone_id=milestone.id,
        milestone=milestone,
        unlocked_at=now if status == "unlocked" else None,
        current_value=current_value,
        status=status,
        evidence={"metric": "submissions_on_time", "actual_value": 1},
        academic_year_id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
    )


def make_passport(
    auth: AuthContext, *, student_id: uuid.UUID | None = None
) -> SimpleNamespace:
    now = datetime(2026, 4, 4, 12, 45, tzinfo=UTC)
    return SimpleNamespace(
        id=uuid.uuid4(),
        student_id=student_id or uuid.uuid4(),
        school_id=auth.school_id,
        academic_year_id=uuid.uuid4(),
        generated_at=now,
        pdf_url="/generated/skill-passports/test.pdf",
        total_milestones=1,
        unlocked_milestones=1,
        overall_score=100.0,
        created_at=now,
        updated_at=now,
    )


def setup_skill_service(monkeypatch: pytest.MonkeyPatch):
    service = SkillPassportService(AsyncMock())
    service.repo = AsyncMock()
    service.audit = AsyncMock()
    service._dispatcher = SimpleNamespace(dispatch=AsyncMock())

    repo_in_uow = AsyncMock()
    audit = AsyncMock()
    dispatcher = SimpleNamespace(dispatch=AsyncMock())
    uow = FakeUnitOfWork()

    monkeypatch.setattr(skill_module, "UnitOfWork", lambda _db: uow)
    monkeypatch.setattr(
        skill_module, "SkillPassportRepository", lambda _session: repo_in_uow
    )
    monkeypatch.setattr(skill_module, "AuditService", lambda _session: audit)
    monkeypatch.setattr(skill_module, "EventDispatcher", lambda _session: dispatcher)

    return service, repo_in_uow, audit, dispatcher, uow


class TestSkillPassportService:
    @pytest.mark.asyncio
    async def test_create_dimension_rejects_duplicate_code(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth()
        service, *_ = setup_skill_service(monkeypatch)
        service.repo.get_dimension_by_code.return_value = make_dimension()

        with pytest.raises(ConflictError, match="already exists"):
            await service.create_dimension(
                body=skill_module.SkillDimensionCreateRequest(
                    code="autonomy",
                    name_fr="Autonomie",
                    name_ar="الاستقلالية",
                    name_en="Autonomy",
                ),
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_create_dimension_returns_serialized_dimension(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth()
        service, repo_in_uow, audit, dispatcher, uow = setup_skill_service(monkeypatch)
        dimension = make_dimension()
        service.repo.get_dimension_by_code.return_value = None
        repo_in_uow.create_dimension.return_value = dimension

        result = await service.create_dimension(
            body=skill_module.SkillDimensionCreateRequest(
                code="autonomy",
                name_fr="Autonomie",
                name_ar="الاستقلالية",
                name_en="Autonomy",
            ),
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["code"] == "autonomy"
        audit.log_event.assert_awaited_once()
        dispatcher.dispatch.assert_awaited_once()
        assert uow.committed is True

    def test_normalize_metric_config_accepts_alias(self) -> None:
        service = SkillPassportService(AsyncMock())

        metric, threshold, period_days = service._normalize_metric_config(
            {"metric": "modules_without_help", "threshold": 5, "period_days": 30}
        )

        assert metric == "content_items_completed"
        assert threshold == 5.0
        assert period_days == 30

    @pytest.mark.asyncio
    async def test_create_milestone_rejects_unsupported_metric(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth()
        service, *_ = setup_skill_service(monkeypatch)
        dimension = make_dimension()
        service.repo.get_dimension.return_value = dimension
        service.repo.get_milestone_by_code.return_value = None

        with pytest.raises(ValidationError, match="Unsupported skill metric"):
            await service.create_milestone(
                body=skill_module.SkillMilestoneCreateRequest(
                    dimension_id=dimension.id,
                    code="bad_metric",
                    name_fr="Niveau 1",
                    name_ar="المستوى 1",
                    level=1,
                    rule_config={"metric": "unknown_metric", "threshold": 1},
                ),
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_analyze_activity_logs_returns_all_metrics(self) -> None:
        auth = make_auth(role="TCH")
        service = SkillPassportService(AsyncMock())
        service.repo = AsyncMock()
        student = SimpleNamespace(id=uuid.uuid4(), school_id=auth.school_id)
        service.repo.get_user.return_value = student
        service.repo.count_completed_activity_sessions.return_value = 2
        service.repo.count_completed_content_items.return_value = 3
        service.repo.count_submitted_assignments.side_effect = [4, 1]
        service.repo.count_quiz_attempts.return_value = 5
        service.repo.average_quiz_score_percent.return_value = 88.0
        service.repo.count_activity_types_completed.return_value = 2

        metrics = await service.analyze_activity_logs(
            student_id=student.id,
            auth=auth,
            horizon_days=14,
        )

        assert metrics["activity_sessions_completed"] == 2.0
        assert metrics["submissions_on_time"] == 1.0
        assert metrics["average_quiz_score"] == 88.0

    @pytest.mark.asyncio
    async def test_evaluate_student_returns_summary(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth(role="TCH")
        service, _repo_in_uow, audit, _dispatcher, uow = setup_skill_service(
            monkeypatch
        )
        student = SimpleNamespace(id=uuid.uuid4(), school_id=auth.school_id)
        academic_year = SimpleNamespace(id=uuid.uuid4(), school_id=auth.school_id)
        progress = make_progress(
            auth, student_id=student.id, status="unlocked", current_value=100
        )
        service.repo.get_user.return_value = student
        service.repo.get_academic_year.return_value = academic_year
        monkeypatch.setattr(
            service,
            "_evaluate_student_records",
            AsyncMock(
                return_value=([progress], {"submissions_on_time": 1.0}, 1, 1, 100.0)
            ),
        )

        result = await service.evaluate_student(
            student_id=student.id,
            academic_year_id=academic_year.id,
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["overall_score"] == 100.0
        assert result["unlocked_milestones"] == 1
        audit.log_event.assert_awaited_once()
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_get_passport_generates_for_staff_when_missing(self) -> None:
        auth = make_auth(role="TCH")
        service = SkillPassportService(AsyncMock())
        service.repo = AsyncMock()
        student = SimpleNamespace(id=uuid.uuid4(), school_id=auth.school_id)
        academic_year = SimpleNamespace(id=uuid.uuid4(), school_id=auth.school_id)
        service.repo.get_user.return_value = student
        service.repo.get_academic_year.return_value = academic_year
        service.repo.get_passport.return_value = None
        service.generate_passport = AsyncMock(return_value={"id": str(uuid.uuid4())})

        result = await service.get_passport(
            student_id=student.id,
            academic_year_id=academic_year.id,
            auth=auth,
        )

        assert "id" in result
        service.generate_passport.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_passport_rejects_parent_when_not_generated(self) -> None:
        auth = make_auth(role="PAR")
        service = SkillPassportService(AsyncMock())
        service.repo = AsyncMock()
        student = SimpleNamespace(id=uuid.uuid4(), school_id=auth.school_id)
        academic_year = SimpleNamespace(id=uuid.uuid4(), school_id=auth.school_id)
        service.repo.get_user.return_value = student
        service.repo.get_academic_year.return_value = academic_year
        service.repo.is_parent_of_student.return_value = True
        service.repo.get_passport.return_value = None

        with pytest.raises(NotFoundError, match="has not been generated"):
            await service.get_passport(
                student_id=student.id,
                academic_year_id=academic_year.id,
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_class_analytics_returns_zeroes_for_empty_class(self) -> None:
        auth = make_auth(role="TCH")
        service = SkillPassportService(AsyncMock())
        service.repo = AsyncMock()
        school_class = SimpleNamespace(id=uuid.uuid4(), school_id=auth.school_id)
        academic_year = SimpleNamespace(id=uuid.uuid4(), school_id=auth.school_id)
        service.repo.get_class.return_value = school_class
        service.repo.get_academic_year.return_value = academic_year
        service.repo.list_class_student_ids.return_value = []
        service.repo.list_progress.return_value = []
        service.repo.list_passports.return_value = []
        service.repo.list_dimensions.return_value = []
        service.repo.list_milestones.return_value = []

        result = await service.class_analytics(
            class_id=school_class.id,
            academic_year_id=academic_year.id,
            auth=auth,
        )

        assert result["student_count"] == 0
        assert result["average_overall_score"] == 0.0

    @pytest.mark.asyncio
    async def test_school_analytics_counts_unlocked_progress(self) -> None:
        auth = make_auth(role="TCH")
        service = SkillPassportService(AsyncMock())
        service.repo = AsyncMock()
        academic_year = SimpleNamespace(id=uuid.uuid4(), school_id=auth.school_id)
        dimension = make_dimension()
        milestone = make_milestone(dimension=dimension)
        progress = make_progress(
            auth, milestone=milestone, status="unlocked", current_value=100
        )
        service.repo.get_academic_year.return_value = academic_year
        service.repo.list_school_student_ids.return_value = [progress.student_id]
        service.repo.list_progress.return_value = [progress]
        service.repo.list_passports.return_value = [
            make_passport(auth, student_id=progress.student_id)
        ]
        service.repo.list_dimensions.return_value = [dimension]
        service.repo.list_milestones.return_value = [milestone]

        result = await service.school_analytics(
            academic_year_id=academic_year.id,
            auth=auth,
        )

        assert result["student_count"] == 1
        assert result["unlocked_record_count"] == 1
        assert result["average_overall_score"] == 100.0

    @pytest.mark.asyncio
    async def test_leaderboard_orders_students_by_score(self) -> None:
        auth = make_auth(role="TCH")
        service = SkillPassportService(AsyncMock())
        service.repo = AsyncMock()
        school_class = SimpleNamespace(id=uuid.uuid4(), school_id=auth.school_id)
        academic_year = SimpleNamespace(id=uuid.uuid4(), school_id=auth.school_id)
        milestone_one = make_milestone(level=1)
        milestone_two = make_milestone(level=2)
        student_one = uuid.uuid4()
        student_two = uuid.uuid4()
        progress_rows = [
            make_progress(
                auth,
                student_id=student_one,
                milestone=milestone_one,
                status="unlocked",
                current_value=100,
            ),
            make_progress(
                auth,
                student_id=student_one,
                milestone=milestone_two,
                status="unlocked",
                current_value=100,
            ),
            make_progress(
                auth,
                student_id=student_two,
                milestone=milestone_one,
                status="unlocked",
                current_value=100,
            ),
            make_progress(
                auth,
                student_id=student_two,
                milestone=milestone_two,
                status="locked",
                current_value=0,
            ),
        ]
        service.repo.get_class.return_value = school_class
        service.repo.get_academic_year.return_value = academic_year
        service.repo.list_class_student_ids.return_value = [student_one, student_two]
        service.repo.list_milestones.return_value = [milestone_one, milestone_two]
        service.repo.list_progress.return_value = progress_rows

        result = await service.leaderboard(
            class_id=school_class.id,
            academic_year_id=academic_year.id,
            auth=auth,
        )

        assert result[0]["student_id"] == str(student_one)
        assert result[0]["overall_score"] == 100.0
        assert result[1]["overall_score"] == 50.0

    @pytest.mark.asyncio
    async def test_download_pdf_returns_pdf_bytes(self) -> None:
        auth = make_auth(role="TCH")
        service = SkillPassportService(AsyncMock())
        service.repo = AsyncMock()
        passport = make_passport(auth)
        student = SimpleNamespace(id=passport.student_id, school_id=auth.school_id)
        progress = make_progress(
            auth, student_id=passport.student_id, status="unlocked", current_value=100
        )
        service.repo.get_passport_by_id.return_value = passport
        service.repo.get_user.return_value = student
        service.repo.list_progress.return_value = [progress]

        pdf_bytes = await service.download_pdf(passport_id=passport.id, auth=auth)

        assert pdf_bytes.startswith(b"%PDF-1.4")
