"""Regression tests for CI unit coverage gating."""

from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[4]
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"


@pytest.fixture()
def _skip_if_no_ci_workflow() -> None:
    if not CI_WORKFLOW.exists():
        pytest.skip("CI workflow not available in this environment")


def _unit_coverage_step() -> str:
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    start = workflow.index("- name: Run unit tests with coverage")
    end = workflow.index("- name: Upload unit coverage report", start)
    return workflow[start:end]


def test_unit_coverage_gate_keeps_explicit_unit_scope(
    _skip_if_no_ci_workflow: None,
) -> None:
    step = _unit_coverage_step()

    # CI uses pytest-cov with scoped app coverage
    assert "pytest tests/unit/" in step
    assert "--cov=app" in step
    assert "--cov-branch" in step
    assert "--cov-report=xml" in step
    assert "--cov-report=term" in step


def test_unit_coverage_gate_does_not_measure_whole_backend_app(
    _skip_if_no_ci_workflow: None,
) -> None:
    step = _unit_coverage_step()

    # Ensure coverage is scoped to the app package, not the entire backend dir
    assert "--cov=app" in step
