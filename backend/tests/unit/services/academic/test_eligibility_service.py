"""Unit tests for EligibilityService.

Tests rule evaluation logic, condition type handling, and response shapes
with mocked database sessions.
"""

from __future__ import annotations

import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.lms.eligibility_service import EligibilityService, KNOWN_CONDITION_TYPES
from app.core.exceptions import NotFoundError
from app.models.erp import EligibilityRule


def _uuid(n: int) -> uuid.UUID:
    return uuid.UUID(f"50000000-0000-4000-8000-{n:012d}")


@pytest.fixture
def mock_db() -> MagicMock:
    """Return a mocked AsyncSession."""
    return MagicMock()


@pytest.fixture
def service(mock_db: MagicMock) -> EligibilityService:
    return EligibilityService(db=mock_db)


@pytest.fixture
def sample_rule() -> EligibilityRule:
    rule = MagicMock(spec=EligibilityRule)
    rule.id = _uuid(1)
    rule.school_id = _uuid(10)
    rule.kind = "enrollment"
    rule.target_program_id = _uuid(20)
    rule.condition_type = "has_completed_program"
    rule.condition_params = {"program_id": str(_uuid(30))}
    rule.message_key = "needs_prerequisite"
    rule.is_active = True
    rule.created_at = MagicMock()
    rule.created_at.isoformat.return_value = "2024-01-01T00:00:00"
    rule.updated_at = None
    return rule


# ---------------------------------------------------------------------------
# Known condition types catalog
# ---------------------------------------------------------------------------
class TestKnownConditionTypes:
    """Ensure the service advertises the expected rule catalog."""

    def test_catalog_contains_expected_types(self) -> None:
        assert "has_completed_program" in KNOWN_CONDITION_TYPES
        assert "min_attendance_rate" in KNOWN_CONDITION_TYPES
        assert "min_grade_average" in KNOWN_CONDITION_TYPES
        assert len(KNOWN_CONDITION_TYPES) == 3


# ---------------------------------------------------------------------------
# _to_response
# ---------------------------------------------------------------------------
class TestToResponse:
    """Tests for the internal _to_response helper."""

    def test_response_shape(
        self, service: EligibilityService, sample_rule: EligibilityRule
    ) -> None:
        resp = service._to_response(sample_rule)
        assert resp["id"] == str(sample_rule.id)
        assert resp["school_id"] == str(sample_rule.school_id)
        assert resp["kind"] == sample_rule.kind
        assert resp["condition_type"] == sample_rule.condition_type
        assert resp["condition_params"] == sample_rule.condition_params
        assert resp["message_key"] == sample_rule.message_key
        assert resp["is_active"] is True
        assert resp["created_at"] == "2024-01-01T00:00:00"
        assert resp["updated_at"] is None


# ---------------------------------------------------------------------------
# _evaluate — has_completed_program
# ---------------------------------------------------------------------------
class TestEvaluateHasCompletedProgram:
    """Tests for the has_completed_program condition evaluator."""

    @pytest.mark.asyncio
    async def test_passes_when_enrollment_exists(
        self, service: EligibilityService, sample_rule: EligibilityRule
    ) -> None:
        mock_result = MagicMock()
        mock_result.first.return_value = ("enrollment-id",)
        service.db.execute = AsyncMock(return_value=mock_result)

        passed, detail = await service._evaluate(
            student_id=_uuid(5),
            rule=sample_rule,
        )
        assert passed is True
        assert detail is None

    @pytest.mark.asyncio
    async def test_fails_when_no_enrollment(
        self, service: EligibilityService, sample_rule: EligibilityRule
    ) -> None:
        mock_result = MagicMock()
        mock_result.first.return_value = None
        service.db.execute = AsyncMock(return_value=mock_result)

        passed, detail = await service._evaluate(
            student_id=_uuid(5),
            rule=sample_rule,
        )
        assert passed is False
        assert detail is None

    @pytest.mark.asyncio
    async def test_fails_when_program_id_missing(
        self, service: EligibilityService, sample_rule: EligibilityRule
    ) -> None:
        sample_rule.condition_params = {}
        passed, detail = await service._evaluate(
            student_id=_uuid(5),
            rule=sample_rule,
        )
        assert passed is False
        assert detail == "missing program_id"


# ---------------------------------------------------------------------------
# _evaluate — min_attendance_rate
# ---------------------------------------------------------------------------
class TestEvaluateMinAttendanceRate:
    """Tests for the min_attendance_rate condition evaluator."""

    @pytest.fixture
    def attendance_rule(self, sample_rule: EligibilityRule) -> EligibilityRule:
        sample_rule.condition_type = "min_attendance_rate"
        sample_rule.condition_params = {
            "min_rate": 0.8,
            "academic_year_id": str(_uuid(40)),
        }
        return sample_rule

    @pytest.mark.asyncio
    async def test_passes_when_rate_above_threshold(
        self, service: EligibilityService, attendance_rule: EligibilityRule
    ) -> None:
        # Mock academic year lookup
        ay_result = MagicMock()
        ay_result.first.return_value = MagicMock(
            date_start=date(2024, 1, 1), date_end=date(2024, 12, 31)
        )

        # Mock attendance count
        count_result = MagicMock()
        count_result.first.return_value = MagicMock(total=100, present=90)

        service.db.execute = AsyncMock(side_effect=[ay_result, count_result])

        passed, detail = await service._evaluate(
            student_id=_uuid(5),
            rule=attendance_rule,
        )
        assert passed is True
        assert "rate=0.90" in detail
        assert "required >= 0.80" in detail

    @pytest.mark.asyncio
    async def test_fails_when_rate_below_threshold(
        self, service: EligibilityService, attendance_rule: EligibilityRule
    ) -> None:
        ay_result = MagicMock()
        ay_result.first.return_value = MagicMock(
            date_start=date(2024, 1, 1), date_end=date(2024, 12, 31)
        )

        count_result = MagicMock()
        count_result.first.return_value = MagicMock(total=100, present=70)

        service.db.execute = AsyncMock(side_effect=[ay_result, count_result])

        passed, detail = await service._evaluate(
            student_id=_uuid(5),
            rule=attendance_rule,
        )
        assert passed is False
        assert "rate=0.70" in detail

    @pytest.mark.asyncio
    async def test_fails_when_no_academic_year_found(
        self, service: EligibilityService, attendance_rule: EligibilityRule
    ) -> None:
        ay_result = MagicMock()
        ay_result.first.return_value = None
        service.db.execute = AsyncMock(return_value=ay_result)

        passed, detail = await service._evaluate(
            student_id=_uuid(5),
            rule=attendance_rule,
        )
        assert passed is False
        assert "academic_year not found" in detail

    @pytest.mark.asyncio
    async def test_zero_total_sessions_returns_zero_rate(
        self, service: EligibilityService, attendance_rule: EligibilityRule
    ) -> None:
        ay_result = MagicMock()
        ay_result.first.return_value = MagicMock(
            date_start=date(2024, 1, 1), date_end=date(2024, 12, 31)
        )

        count_result = MagicMock()
        count_result.first.return_value = MagicMock(total=0, present=0)

        service.db.execute = AsyncMock(side_effect=[ay_result, count_result])

        passed, detail = await service._evaluate(
            student_id=_uuid(5),
            rule=attendance_rule,
        )
        assert passed is False
        assert "rate=0.00" in detail


# ---------------------------------------------------------------------------
# _evaluate — min_grade_average
# ---------------------------------------------------------------------------
class TestEvaluateMinGradeAverage:
    """Tests for the min_grade_average condition evaluator."""

    @pytest.fixture
    def grade_rule(self, sample_rule: EligibilityRule) -> EligibilityRule:
        sample_rule.condition_type = "min_grade_average"
        sample_rule.condition_params = {"min_average": 12.0}
        return sample_rule

    @pytest.mark.asyncio
    async def test_passes_when_average_above_threshold(
        self, service: EligibilityService, grade_rule: EligibilityRule
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = 15.5
        service.db.execute = AsyncMock(return_value=mock_result)

        passed, detail = await service._evaluate(
            student_id=_uuid(5),
            rule=grade_rule,
        )
        assert passed is True
        assert "avg=15.50" in detail

    @pytest.mark.asyncio
    async def test_fails_when_average_below_threshold(
        self, service: EligibilityService, grade_rule: EligibilityRule
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = 10.0
        service.db.execute = AsyncMock(return_value=mock_result)

        passed, detail = await service._evaluate(
            student_id=_uuid(5),
            rule=grade_rule,
        )
        assert passed is False
        assert "avg=10.00" in detail

    @pytest.mark.asyncio
    async def test_fails_when_no_grades(
        self, service: EligibilityService, grade_rule: EligibilityRule
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        service.db.execute = AsyncMock(return_value=mock_result)

        passed, detail = await service._evaluate(
            student_id=_uuid(5),
            rule=grade_rule,
        )
        assert passed is False
        assert detail == "no grades"


# ---------------------------------------------------------------------------
# _evaluate — unknown condition
# ---------------------------------------------------------------------------
class TestEvaluateUnknownCondition:
    """Tests for unrecognised condition types."""

    @pytest.mark.asyncio
    async def test_returns_false_for_unknown(
        self, service: EligibilityService, sample_rule: EligibilityRule
    ) -> None:
        sample_rule.condition_type = "totally_made_up"
        passed, detail = await service._evaluate(
            student_id=_uuid(5),
            rule=sample_rule,
        )
        assert passed is False
        assert "unknown condition_type" in detail


# ---------------------------------------------------------------------------
# check_eligibility — integration of evaluator
# ---------------------------------------------------------------------------
class TestCheckEligibility:
    """Tests for the top-level check_eligibility method."""

    @pytest.mark.asyncio
    async def test_eligible_when_all_rules_pass(
        self, service: EligibilityService, sample_rule: EligibilityRule
    ) -> None:
        auth = MagicMock()
        auth.school_id = sample_rule.school_id

        # Mock student lookup
        student_result = MagicMock()
        student_result.scalar_one_or_none.return_value = MagicMock(
            school_id=sample_rule.school_id
        )

        # Mock program lookup
        program_result = MagicMock()
        program_result.scalar_one_or_none.return_value = MagicMock(
            school_id=sample_rule.school_id
        )

        # Mock rules lookup
        rules_result = MagicMock()
        rules_result.scalars.return_value.all.return_value = [sample_rule]

        # Mock evaluation
        eval_result = MagicMock()
        eval_result.first.return_value = ("enrollment-id",)

        service.db.execute = AsyncMock(
            side_effect=[
                student_result,
                program_result,
                rules_result,
                eval_result,
            ]
        )

        result = await service.check_eligibility(
            student_id=_uuid(5),
            target_program_id=sample_rule.target_program_id,
            kind="enrollment",
            auth=auth,
        )
        assert result["eligible"] is True
        assert len(result["rules"]) == 1
        assert result["rules"][0]["passed"] is True

    @pytest.mark.asyncio
    async def test_ineligible_when_any_rule_fails(
        self, service: EligibilityService, sample_rule: EligibilityRule
    ) -> None:
        auth = MagicMock()
        auth.school_id = sample_rule.school_id

        student_result = MagicMock()
        student_result.scalar_one_or_none.return_value = MagicMock(
            school_id=sample_rule.school_id
        )

        program_result = MagicMock()
        program_result.scalar_one_or_none.return_value = MagicMock(
            school_id=sample_rule.school_id
        )

        rules_result = MagicMock()
        rules_result.scalars.return_value.all.return_value = [sample_rule]

        eval_result = MagicMock()
        eval_result.first.return_value = None

        service.db.execute = AsyncMock(
            side_effect=[
                student_result,
                program_result,
                rules_result,
                eval_result,
            ]
        )

        result = await service.check_eligibility(
            student_id=_uuid(5),
            target_program_id=sample_rule.target_program_id,
            kind="enrollment",
            auth=auth,
        )
        assert result["eligible"] is False
        assert result["rules"][0]["passed"] is False

    @pytest.mark.asyncio
    async def test_student_not_found_raises(
        self, service: EligibilityService, sample_rule: EligibilityRule
    ) -> None:
        auth = MagicMock()
        auth.school_id = sample_rule.school_id

        student_result = MagicMock()
        student_result.scalar_one_or_none.return_value = None
        service.db.execute = AsyncMock(return_value=student_result)

        with pytest.raises(NotFoundError, match="Student not found"):
            await service.check_eligibility(
                student_id=_uuid(5),
                target_program_id=sample_rule.target_program_id,
                kind="enrollment",
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_program_not_found_raises(
        self, service: EligibilityService, sample_rule: EligibilityRule
    ) -> None:
        auth = MagicMock()
        auth.school_id = sample_rule.school_id

        student_result = MagicMock()
        student_result.scalar_one_or_none.return_value = MagicMock(
            school_id=sample_rule.school_id
        )

        program_result = MagicMock()
        program_result.scalar_one_or_none.return_value = None

        service.db.execute = AsyncMock(side_effect=[student_result, program_result])

        with pytest.raises(NotFoundError, match="Program not found"):
            await service.check_eligibility(
                student_id=_uuid(5),
                target_program_id=sample_rule.target_program_id,
                kind="enrollment",
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_evaluator_error_gracefully_handled(
        self, service: EligibilityService, sample_rule: EligibilityRule
    ) -> None:
        auth = MagicMock()
        auth.school_id = sample_rule.school_id

        student_result = MagicMock()
        student_result.scalar_one_or_none.return_value = MagicMock(
            school_id=sample_rule.school_id
        )

        program_result = MagicMock()
        program_result.scalar_one_or_none.return_value = MagicMock(
            school_id=sample_rule.school_id
        )

        rules_result = MagicMock()
        rules_result.scalars.return_value.all.return_value = [sample_rule]

        service.db.execute = AsyncMock(
            side_effect=[
                student_result,
                program_result,
                rules_result,
                Exception("DB connection lost"),
            ]
        )

        result = await service.check_eligibility(
            student_id=_uuid(5),
            target_program_id=sample_rule.target_program_id,
            kind="enrollment",
            auth=auth,
        )
        assert result["eligible"] is False
        assert "evaluator error" in result["rules"][0]["detail"]
