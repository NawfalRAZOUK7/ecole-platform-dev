"""Edge and validation tests for MEN compliance models, schemas, and services."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from pydantic import ValidationError as PydanticValidationError

from app.core.dependencies import AuthContext
from app.core.exceptions import NotFoundError, ValidationError
from app.schemas.men_compliance import (
    CurriculumMappingCreateRequest,
    MenCurriculumCreateRequest,
)
from app.services.compliance_service import ComplianceService


@pytest_asyncio.fixture(autouse=True)
async def clear_analytics_cache():
    yield


@pytest_asyncio.fixture(autouse=True)
async def override_test_redis():
    yield


@pytest_asyncio.fixture(autouse=True)
async def dispose_app_engine_pool():
    yield


class TestComplianceModelValidation:
    def test_curriculum_required_text_rejects_blank_value(self) -> None:
        from app.models.men_compliance import MenCurriculum

        curriculum = MenCurriculum()

        with pytest.raises(ValueError, match="level is required"):
            curriculum.validate_required_text("level", "   ")

    def test_objective_code_rejects_blank_value(self) -> None:
        from app.models.men_compliance import MenObjective

        objective = MenObjective()

        with pytest.raises(ValueError, match="code is required"):
            objective.validate_code("code", "   ")


class TestComplianceSchemaValidation:
    def test_curriculum_request_rejects_invalid_academic_year(self) -> None:
        with pytest.raises(PydanticValidationError):
            MenCurriculumCreateRequest(
                level="college",
                grade="3eme",
                subject="mathematics",
                academic_year="2026",
            )

    def test_mapping_request_rejects_invalid_coverage_percent(self) -> None:
        with pytest.raises(PydanticValidationError):
            CurriculumMappingCreateRequest(
                objective_id="10000000-0000-4000-8000-000000000001",
                course_id="10000000-0000-4000-8000-000000000002",
                coverage_percent=101,
            )


class TestComplianceServiceEdges:
    def test_build_minimal_pdf_emits_pdf_header(self) -> None:
        service = ComplianceService(AsyncMock())

        payload = service._build_minimal_pdf(["MEN Compliance Report", "Compliance: 100%"])

        assert payload.startswith(b"%PDF-1.4")

    @pytest.mark.asyncio
    async def test_create_mapping_without_target_raises_validation_error(self) -> None:
        service = ComplianceService(AsyncMock())
        service.repo = AsyncMock()
        service.repo.get_objective.return_value = type(
            "ObjectiveStub",
            (),
            {
                "id": uuid.uuid4(),
                "curriculum_id": uuid.uuid4(),
                "curriculum": None,
            },
        )()
        auth = AuthContext(
            user_id=uuid.uuid4(),
            role="TCH",
            school_id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            permissions=set(),
        )

        with pytest.raises(ValidationError, match="requires a course_id or content_item_id"):
            await service.create_mapping(
                body=CurriculumMappingCreateRequest(objective_id=uuid.uuid4()),
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_get_dashboard_with_no_curricula_returns_zero_percent(self) -> None:
        auth = AuthContext(
            user_id=uuid.uuid4(),
            role="DIR",
            school_id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            permissions=set(),
        )
        service = ComplianceService(AsyncMock())
        service.repo = AsyncMock()
        service.repo.list_curricula.return_value = []
        service._ensure_academic_year_or_404 = AsyncMock()

        result = await service.get_dashboard(auth=auth, academic_year_id=uuid.uuid4())

        assert result["curriculum_count"] == 0
        assert result["overall_compliance_percent"] == 0.0

    @pytest.mark.asyncio
    async def test_download_pdf_missing_report_raises_not_found(self) -> None:
        auth = AuthContext(
            user_id=uuid.uuid4(),
            role="DIR",
            school_id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            permissions=set(),
        )
        service = ComplianceService(AsyncMock())
        service.repo = AsyncMock()
        service.repo.get_report.return_value = None

        with pytest.raises(NotFoundError):
            await service.download_pdf(report_id=uuid.uuid4(), auth=auth)

    @pytest.mark.asyncio
    async def test_seed_reference_curricula_rejects_teacher_role(self) -> None:
        auth = AuthContext(
            user_id=uuid.uuid4(),
            role="TCH",
            school_id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            permissions=set(),
        )
        service = ComplianceService(AsyncMock())

        with pytest.raises(ValidationError, match="Only SUP and SYS"):
            await service.seed_reference_curricula(auth=auth)
