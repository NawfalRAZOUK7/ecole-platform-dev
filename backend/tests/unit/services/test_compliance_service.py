"""Unit tests for MEN compliance services."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio

from app.core.dependencies import AuthContext
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
import app.services.admin.compliance as compliance_module
from app.services.admin.compliance import ComplianceService


@pytest_asyncio.fixture(autouse=True)
async def clear_analytics_cache():
    yield


@pytest_asyncio.fixture(autouse=True)
async def override_test_redis():
    yield


@pytest_asyncio.fixture(autouse=True)
async def dispose_app_engine_pool():
    yield


def make_auth(role: str = "SUP") -> AuthContext:
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


def make_curriculum(subject: str = "mathematics") -> SimpleNamespace:
    now = datetime(2026, 4, 4, 14, 0, tzinfo=UTC)
    return SimpleNamespace(
        id=uuid.uuid4(),
        level="college",
        grade="3eme",
        subject=subject,
        academic_year="2025-2026",
        version="1.0",
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def make_objective(
    *,
    curriculum: SimpleNamespace | None = None,
    code: str = "MATH-3C-01",
) -> SimpleNamespace:
    now = datetime(2026, 4, 4, 14, 10, tzinfo=UTC)
    curriculum = curriculum or make_curriculum()
    return SimpleNamespace(
        id=uuid.uuid4(),
        curriculum_id=curriculum.id,
        curriculum=curriculum,
        code=code,
        title_fr="Calculer une aire",
        title_ar="حساب مساحة",
        description_fr="Objectif MEN",
        trimester=1,
        unit_number=1,
        is_mandatory=True,
        hours_recommended=2.0,
        display_order=1,
        created_at=now,
        updated_at=now,
    )


def make_mapping(
    auth: AuthContext,
    *,
    objective: SimpleNamespace | None = None,
    course_id: uuid.UUID | None = None,
) -> SimpleNamespace:
    now = datetime(2026, 4, 4, 14, 20, tzinfo=UTC)
    objective = objective or make_objective()
    return SimpleNamespace(
        id=uuid.uuid4(),
        school_id=auth.school_id,
        objective_id=objective.id,
        objective=objective,
        course_id=course_id or uuid.uuid4(),
        content_item_id=None,
        mapped_by=auth.user_id,
        mapped_at=now,
        coverage_percent=100,
        notes="Couverture complète",
        created_at=now,
        updated_at=now,
    )


def make_report(
    auth: AuthContext,
    *,
    curriculum: SimpleNamespace | None = None,
    compliance_percent: float = 50.0,
) -> SimpleNamespace:
    now = datetime(2026, 4, 4, 14, 30, tzinfo=UTC)
    curriculum = curriculum or make_curriculum()
    return SimpleNamespace(
        id=uuid.uuid4(),
        school_id=auth.school_id,
        curriculum_id=curriculum.id,
        curriculum=curriculum,
        generated_at=now,
        generated_by=auth.user_id,
        total_objectives=4,
        mapped_objectives=2,
        compliance_percent=compliance_percent,
        unmapped_objectives=["MATH-3C-03", "MATH-3C-04"],
        pdf_url="/generated/compliance-reports/test.pdf",
        academic_year_id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
    )


def setup_service(monkeypatch: pytest.MonkeyPatch):
    service = ComplianceService(AsyncMock())
    service.repo = AsyncMock()
    service.audit = AsyncMock()
    service._dispatcher = SimpleNamespace(dispatch=AsyncMock())

    repo_in_uow = AsyncMock()
    audit = AsyncMock()
    dispatcher = SimpleNamespace(dispatch=AsyncMock())
    uow = FakeUnitOfWork()

    monkeypatch.setattr(compliance_module, "UnitOfWork", lambda _db: uow)
    monkeypatch.setattr(
        compliance_module, "ComplianceRepository", lambda _session: repo_in_uow
    )
    monkeypatch.setattr(compliance_module, "AuditService", lambda _session: audit)
    monkeypatch.setattr(
        compliance_module, "EventDispatcher", lambda _session: dispatcher
    )

    return service, repo_in_uow, audit, dispatcher, uow


class TestComplianceService:
    @pytest.mark.asyncio
    async def test_create_curriculum_rejects_duplicate_scope(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth()
        service, *_ = setup_service(monkeypatch)
        service.repo.get_curriculum_by_scope.return_value = make_curriculum()

        with pytest.raises(ConflictError, match="already exists"):
            await service.create_curriculum(
                body=compliance_module.MenCurriculumCreateRequest(
                    level="college",
                    grade="3eme",
                    subject="mathematics",
                    academic_year="2025-2026",
                ),
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_create_curriculum_returns_serialized_payload(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth()
        service, repo_in_uow, audit, dispatcher, uow = setup_service(monkeypatch)
        curriculum = make_curriculum()
        service.repo.get_curriculum_by_scope.return_value = None
        repo_in_uow.create_curriculum.return_value = curriculum

        result = await service.create_curriculum(
            body=compliance_module.MenCurriculumCreateRequest(
                level="college",
                grade="3eme",
                subject="mathematics",
                academic_year="2025-2026",
            ),
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["subject"] == "mathematics"
        audit.log_event.assert_awaited_once()
        dispatcher.dispatch.assert_awaited_once()
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_create_objective_rejects_duplicate_code(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth()
        service, *_ = setup_service(monkeypatch)
        curriculum = make_curriculum()
        objective = make_objective(curriculum=curriculum)
        service.repo.get_curriculum.return_value = curriculum
        service.repo.get_objective_by_code.return_value = objective

        with pytest.raises(ConflictError, match="already exists"):
            await service.create_objective(
                curriculum_id=curriculum.id,
                body=compliance_module.MenObjectiveCreateRequest(
                    code=objective.code,
                    title_fr="Objectif",
                    title_ar="الهدف",
                    trimester=1,
                    unit_number=1,
                    display_order=1,
                ),
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_create_mapping_requires_target(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth(role="TCH")
        service, *_ = setup_service(monkeypatch)
        service.repo.get_objective.return_value = make_objective()

        with pytest.raises(
            ValidationError, match="requires a course_id or content_item_id"
        ):
            await service.create_mapping(
                body=compliance_module.CurriculumMappingCreateRequest(
                    objective_id=uuid.uuid4(),
                ),
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_create_mapping_rejects_duplicate(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth(role="TCH")
        service, *_ = setup_service(monkeypatch)
        objective = make_objective()
        service.repo.get_objective.return_value = objective
        service.repo.find_mapping.return_value = make_mapping(auth, objective=objective)
        monkeypatch.setattr(service, "_ensure_course_or_404", AsyncMock())

        with pytest.raises(ConflictError, match="already exists"):
            await service.create_mapping(
                body=compliance_module.CurriculumMappingCreateRequest(
                    objective_id=objective.id,
                    course_id=uuid.uuid4(),
                ),
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_get_dashboard_aggregates_curriculum_snapshots(self) -> None:
        auth = make_auth(role="DIR")
        service = ComplianceService(AsyncMock())
        service.repo = AsyncMock()
        curriculum_one = make_curriculum("math")
        curriculum_two = make_curriculum("arabic")
        service.repo.list_curricula.return_value = [curriculum_one, curriculum_two]
        service._ensure_academic_year_or_404 = AsyncMock()
        service._calculate_snapshot = AsyncMock(
            side_effect=[
                (
                    curriculum_one,
                    [make_objective(curriculum=curriculum_one) for _ in range(4)],
                    [],
                    ["MATH-3C-03"],
                    75.0,
                ),
                (
                    curriculum_two,
                    [
                        make_objective(curriculum=curriculum_two, code=f"ARAB-3C-0{i}")
                        for i in range(1, 3)
                    ],
                    [],
                    [],
                    100.0,
                ),
            ]
        )

        result = await service.get_dashboard(
            auth=auth,
            academic_year_id=uuid.uuid4(),
        )

        assert result["curriculum_count"] == 2
        assert result["mapped_objectives"] == 5
        assert result["overall_compliance_percent"] == 83.33

    @pytest.mark.asyncio
    async def test_generate_report_returns_serialized_report(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth(role="DIR")
        service, repo_in_uow, audit, dispatcher, uow = setup_service(monkeypatch)
        curriculum = make_curriculum()
        report = make_report(auth, curriculum=curriculum, compliance_percent=50.0)
        service._ensure_academic_year_or_404 = AsyncMock()
        monkeypatch.setattr(
            service,
            "_calculate_snapshot",
            AsyncMock(
                return_value=(
                    curriculum,
                    [make_objective(curriculum=curriculum) for _ in range(4)],
                    [],
                    ["MATH-3C-03", "MATH-3C-04"],
                    50.0,
                )
            ),
        )

        async def create_report_side_effect(created):
            created.id = report.id
            created.created_at = report.created_at
            created.updated_at = report.updated_at
            return created

        repo_in_uow.create_report.side_effect = create_report_side_effect
        repo_in_uow.save_report.side_effect = lambda created: created
        repo_in_uow.get_report.return_value = report

        result = await service.generate_report(
            body=compliance_module.ComplianceReportGenerateRequest(
                curriculum_id=curriculum.id,
                academic_year_id=uuid.uuid4(),
            ),
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["compliance_percent"] == 50.0
        audit.log_event.assert_awaited_once()
        dispatcher.dispatch.assert_awaited_once()
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_list_reports_serializes_reports(self) -> None:
        auth = make_auth(role="DIR")
        service = ComplianceService(AsyncMock())
        service.repo = AsyncMock()
        report = make_report(auth)
        service.repo.list_reports.return_value = [report]

        result = await service.list_reports(auth=auth)

        assert len(result) == 1
        assert result[0]["pdf_url"].endswith(".pdf")

    @pytest.mark.asyncio
    async def test_get_report_raises_when_missing(self) -> None:
        auth = make_auth(role="DIR")
        service = ComplianceService(AsyncMock())
        service.repo = AsyncMock()
        service.repo.get_report.return_value = None

        with pytest.raises(NotFoundError):
            await service.get_report(report_id=uuid.uuid4(), auth=auth)

    @pytest.mark.asyncio
    async def test_download_pdf_emits_pdf_header(self) -> None:
        auth = make_auth(role="DIR")
        service = ComplianceService(AsyncMock())
        service.repo = AsyncMock()
        service.repo.get_report.return_value = make_report(auth)

        payload = await service.download_pdf(report_id=uuid.uuid4(), auth=auth)

        assert payload.startswith(b"%PDF-1.4")

    @pytest.mark.asyncio
    async def test_seed_reference_curricula_counts_new_records(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth()
        service, repo_in_uow, audit, dispatcher, uow = setup_service(monkeypatch)
        curriculum = make_curriculum()
        monkeypatch.setattr(
            compliance_module,
            "DEFAULT_CURRICULA",
            [
                {
                    "level": "college",
                    "grade": "3eme",
                    "subject": "science",
                    "academic_year": "2025-2026",
                    "version": "1.0",
                    "objectives": [
                        {
                            "code": "SCI-3C-01",
                            "title_fr": "Objectif 1",
                            "title_ar": "الهدف 1",
                            "description_fr": "Desc",
                            "trimester": 1,
                            "unit_number": 1,
                            "is_mandatory": True,
                            "hours_recommended": 2.0,
                            "display_order": 1,
                        },
                        {
                            "code": "SCI-3C-02",
                            "title_fr": "Objectif 2",
                            "title_ar": "الهدف 2",
                            "description_fr": "Desc",
                            "trimester": 1,
                            "unit_number": 1,
                            "is_mandatory": True,
                            "hours_recommended": 2.0,
                            "display_order": 2,
                        },
                    ],
                }
            ],
        )
        repo_in_uow.get_curriculum_by_scope.return_value = None
        repo_in_uow.create_curriculum.return_value = curriculum
        repo_in_uow.get_objective_by_code.side_effect = [None, None]

        result = await service.seed_reference_curricula(auth=auth)

        assert result == {"curricula_created": 1, "objectives_created": 2}
        audit.log_event.assert_awaited_once()
        dispatcher.dispatch.assert_awaited_once()
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_seed_reference_curricula_rejects_non_platform_role(self) -> None:
        service = ComplianceService(AsyncMock())

        with pytest.raises(ValidationError, match="Only SUP and SYS"):
            await service.seed_reference_curricula(auth=make_auth(role="TCH"))
