"""Edge and validation tests for life-skills passport models and schemas."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from pydantic import ValidationError as PydanticValidationError

from app.core.dependencies import AuthContext
from app.core.exceptions import NotFoundError, ValidationError
from app.schemas.skill_passport import (
    SkillDimensionCreateRequest,
    SkillMilestoneCreateRequest,
)
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


class TestSkillModelValidation:
    def test_skill_dimension_code_rejects_blank_value(self) -> None:
        from app.models.skill_passport import SkillDimension

        dimension = SkillDimension()

        with pytest.raises(ValueError, match="code is required"):
            dimension.validate_code("code", "   ")

    def test_skill_milestone_code_rejects_blank_value(self) -> None:
        from app.models.skill_passport import SkillMilestone

        milestone = SkillMilestone()

        with pytest.raises(ValueError, match="code is required"):
            milestone.validate_code("code", "   ")

    def test_skill_passport_blank_pdf_url_normalizes_to_none(self) -> None:
        from app.models.skill_passport import SkillPassport

        passport = SkillPassport()

        assert passport.validate_pdf_url("pdf_url", "   ") is None


class TestSkillSchemaValidation:
    def test_dimension_request_rejects_negative_display_order(self) -> None:
        with pytest.raises(PydanticValidationError):
            SkillDimensionCreateRequest(
                code="autonomy",
                name_fr="Autonomie",
                name_ar="الاستقلالية",
                name_en="Autonomy",
                display_order=-1,
            )

    def test_milestone_request_rejects_invalid_level(self) -> None:
        with pytest.raises(PydanticValidationError):
            SkillMilestoneCreateRequest(
                dimension_id="10000000-0000-4000-8000-000000000001",
                code="autonomy_level_7",
                name_fr="Niveau 7",
                name_ar="المستوى 7",
                level=7,
            )


class TestSkillServiceEdges:
    def test_normalize_metric_config_rejects_unknown_metric(self) -> None:
        service = SkillPassportService(AsyncMock())

        with pytest.raises(ValidationError, match="Unsupported skill metric"):
            service._normalize_metric_config({"metric": "unknown", "threshold": 1})

    def test_normalize_metric_config_rejects_non_positive_threshold(self) -> None:
        service = SkillPassportService(AsyncMock())

        with pytest.raises(ValidationError, match="threshold must be greater than zero"):
            service._normalize_metric_config({"metric": "quiz_attempts", "threshold": 0})

    def test_normalize_metric_config_rejects_non_positive_period_days(self) -> None:
        service = SkillPassportService(AsyncMock())

        with pytest.raises(ValidationError, match="period_days must be greater than zero"):
            service._normalize_metric_config(
                {"metric": "quiz_attempts", "threshold": 1, "period_days": 0}
            )

    def test_build_minimal_pdf_emits_pdf_header(self) -> None:
        service = SkillPassportService(AsyncMock())

        payload = service._build_minimal_pdf(["Life Skills Passport", "Overall score: 100"])

        assert payload.startswith(b"%PDF-1.4")

    @pytest.mark.asyncio
    async def test_parent_missing_passport_raises_not_found(self) -> None:
        import uuid

        auth = AuthContext(
            user_id=uuid.UUID("10000000-0000-4000-8000-000000000100"),
            role="PAR",
            school_id=uuid.UUID("10000000-0000-4000-8000-000000000001"),
            session_id=uuid.UUID("10000000-0000-4000-8000-000000000200"),
            permissions=set(),
        )
        service = SkillPassportService(AsyncMock())
        service.repo = AsyncMock()
        student = type(
            "StudentStub",
            (),
            {
                "id": uuid.UUID("10000000-0000-4000-8000-000000000300"),
                "school_id": auth.school_id,
            },
        )()
        academic_year = type(
            "YearStub",
            (),
            {
                "id": uuid.UUID("10000000-0000-4000-8000-000000000400"),
                "school_id": auth.school_id,
            },
        )()
        service.repo.get_user.return_value = student
        service.repo.get_academic_year.return_value = academic_year
        service.repo.is_parent_of_student.return_value = True
        service.repo.get_passport.return_value = None

        with pytest.raises(NotFoundError):
            await service.get_passport(
                student_id=student.id,
                academic_year_id=academic_year.id,
                auth=auth,
            )
