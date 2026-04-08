"""Performance benchmarks for critical permission, ABAC, and grading operations."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from app.core.abac import apply_owner_scope
from app.core.dependencies import AuthContext
from app.core.permissions import (
    ADM,
    CONTENT_MGR,
    DIR,
    PAR,
    PERM_ADM_SCHOOL_MANAGE,
    PERM_BIL_PAYMENT_PLAN_READ,
    PERM_CMS_CONTENT_MANAGE,
    PERM_LMS_SUBMISSION_GRADE,
    PERM_PROF_CHILD_READ,
    STD,
    SUP,
    SYS,
    TCH,
    get_effective_permissions,
    role_has_permission,
)
from app.domain.value_objects.grade import MoroccanGrade
from app.models.billing import Invoice
from app.models.lms import Assignment, Submission
from app.services.lms._helpers import calculate_late_penalty


def make_auth(role: str) -> AuthContext:
    return AuthContext(
        user_id=uuid.uuid4(),
        role=role,
        school_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        permissions=set(),
    )


def make_assignment_and_submission(
    *, late_days: int = 0
) -> tuple[Assignment, SimpleNamespace]:
    due_at = datetime(2026, 3, 29, 8, 0, tzinfo=timezone.utc)
    assignment = Assignment(
        due_at=due_at,
        grace_period_hours=0,
        allow_late=True,
        max_late_days=5,
        late_penalty_per_day=2.0,
        total_points=20,
    )
    submission = SimpleNamespace(
        submitted_at=due_at if late_days == 0 else due_at + timedelta(days=late_days)
    )
    return assignment, submission


@pytest.mark.performance
class TestPermissionBenchmarks:
    @pytest.mark.parametrize(
        "role_code",
        [ADM, DIR, TCH, PAR, STD, SUP, SYS, CONTENT_MGR],
    )
    def test_get_effective_permissions_under_one_millisecond(
        self,
        benchmark,
        role_code: str,
    ) -> None:
        result = benchmark(get_effective_permissions, role_code)

        assert result
        assert benchmark.stats["mean"] < 0.001

    @pytest.mark.parametrize(
        ("role_code", "permission", "expected"),
        [
            (ADM, PERM_ADM_SCHOOL_MANAGE, True),
            (TCH, PERM_LMS_SUBMISSION_GRADE, True),
            (PAR, PERM_BIL_PAYMENT_PLAN_READ, True),
            (STD, PERM_PROF_CHILD_READ, False),
            (CONTENT_MGR, PERM_CMS_CONTENT_MANAGE, True),
        ],
    )
    def test_role_has_permission_under_half_millisecond(
        self,
        benchmark,
        role_code: str,
        permission: str,
        expected: bool,
    ) -> None:
        result = benchmark(role_has_permission, role_code, permission)

        assert result is expected
        assert benchmark.stats["mean"] < 0.0005

    @pytest.mark.parametrize(
        ("raw_score", "expected"),
        [
            (0.0, 0.0),
            (10.25, 10.25),
            (19.995, 20.0),
        ],
    )
    def test_grade_creation_under_tenth_millisecond(
        self,
        benchmark,
        raw_score: float,
        expected: float,
    ) -> None:
        result = benchmark(MoroccanGrade.from_float, raw_score)

        assert float(result.value) == expected
        assert benchmark.stats["mean"] < 0.0001

    @pytest.mark.parametrize(
        ("role_code", "query_factory", "expected_fragment"),
        [
            (ADM, lambda _auth: select(Invoice), "SELECT"),
            (TCH, lambda _auth: select(Assignment), "teacher_id"),
            (PAR, lambda _auth: select(Invoice), "parent_id"),
            (STD, lambda _auth: select(Submission), "student_id"),
        ],
    )
    def test_apply_owner_scope_under_one_millisecond(
        self,
        benchmark,
        role_code: str,
        query_factory,
        expected_fragment: str,
    ) -> None:
        auth = make_auth(role_code)
        result = benchmark(lambda: apply_owner_scope(query_factory(auth), auth=auth))

        assert expected_fragment in str(result)
        assert benchmark.stats["mean"] < 0.001

    @pytest.mark.parametrize("late_days", [0, 1, 3])
    def test_calculate_late_penalty_under_half_millisecond(
        self,
        benchmark,
        late_days: int,
    ) -> None:
        assignment, submission = make_assignment_and_submission(late_days=late_days)
        result = benchmark(
            calculate_late_penalty,
            assignment=assignment,
            submission=submission,
            original_score=18.0,
        )

        assert result["late_days"] == late_days
        assert benchmark.stats["mean"] < 0.0005
