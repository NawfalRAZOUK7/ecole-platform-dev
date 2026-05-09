"""Regression tests for CI unit coverage gating."""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def _unit_coverage_step() -> str:
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    start = workflow.index("- name: Run unit tests with coverage")
    end = workflow.index("- name: Upload unit coverage report", start)
    return workflow[start:end]


def test_unit_coverage_gate_keeps_explicit_unit_scope() -> None:
    step = _unit_coverage_step()

    assert "UNIT_COVERAGE_FILES=" in step
    assert "app/core/exceptions.py" in step
    assert "app/core/permissions.py" in step
    assert "app/core/response.py" in step
    assert "app/core/security.py" in step
    assert 'coverage report --include="$UNIT_COVERAGE_FILES" --fail-under=90' in step
    assert 'coverage xml -o coverage-unit.xml --include="$UNIT_COVERAGE_FILES"' in step


def test_unit_coverage_gate_does_not_measure_whole_backend_app() -> None:
    step = _unit_coverage_step()

    assert "coverage report --fail-under=90" not in step
    assert "coverage xml -o coverage-unit.xml\n" not in step
