"""Unit tests for app/services/reports/kpi.py — full branch coverage.

AnalyticsRepository is patched at app.services.reports.kpi.AnalyticsRepository
since it's a module-level import.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.reports.kpi import (
    compute_all_kpis,
    compute_kpi_g1_001,
    compute_kpi_g1_002,
    compute_kpi_g1_003,
    compute_kpi_g1_004,
    compute_kpi_g1_005,
    compute_kpi_g1_006,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_db():
    return AsyncMock()


def _mock_repo(**kwargs):
    """Build a mock AnalyticsRepository with specified return values."""
    repo = MagicMock()
    for attr, value in kwargs.items():
        setattr(repo, attr, AsyncMock(return_value=value))
    # Defaults for anything not specified
    for method in [
        "count_active_accounts",
        "count_active_users",
        "count_distinct_audit_users",
        "count_audit_events",
        "count_invitations_created",
        "count_invitations_consumed",
    ]:
        if not hasattr(repo, method) or not isinstance(getattr(repo, method), AsyncMock):
            setattr(repo, method, AsyncMock(return_value=0))
    return repo


_PATCH = "app.services.reports.kpi.AnalyticsRepository"
_SID = uuid.uuid4()


# ---------------------------------------------------------------------------
# compute_kpi_g1_001 — Adoption rate
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_kpi_g1_001_normal():
    repo = _mock_repo(count_active_accounts=100, count_active_users=75)
    with patch(_PATCH, return_value=repo):
        result = await compute_kpi_g1_001(_mock_db(), school_id=_SID)

    assert result["kpi_id"] == "KPI-G1-001"
    assert result["value"] == 75.0
    assert result["numerator"] == 75
    assert result["denominator"] == 100
    assert result["unit"] == "percent"
    repo.count_active_accounts.assert_awaited_once_with(school_id=_SID)
    repo.count_active_users.assert_awaited_once()


@pytest.mark.asyncio
async def test_kpi_g1_001_zero_total_accounts():
    """Division by zero guard: total_accounts == 0 → rate 0.0."""
    repo = _mock_repo(count_active_accounts=0, count_active_users=0)
    with patch(_PATCH, return_value=repo):
        result = await compute_kpi_g1_001(_mock_db(), school_id=_SID)

    assert result["value"] == 0.0


@pytest.mark.asyncio
async def test_kpi_g1_001_custom_period():
    repo = _mock_repo(count_active_accounts=50, count_active_users=30)
    with patch(_PATCH, return_value=repo):
        result = await compute_kpi_g1_001(_mock_db(), school_id=_SID, period_days=30)

    assert result["period"] == "30d"
    assert result["value"] == 60.0


@pytest.mark.asyncio
async def test_kpi_g1_001_full_adoption():
    repo = _mock_repo(count_active_accounts=50, count_active_users=50)
    with patch(_PATCH, return_value=repo):
        result = await compute_kpi_g1_001(_mock_db(), school_id=_SID)

    assert result["value"] == 100.0


# ---------------------------------------------------------------------------
# compute_kpi_g1_002 — Critical journey usage rate
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_kpi_g1_002_normal():
    repo = _mock_repo(count_distinct_audit_users=40, count_active_users=80)
    with patch(_PATCH, return_value=repo):
        result = await compute_kpi_g1_002(_mock_db(), school_id=_SID)

    assert result["kpi_id"] == "KPI-G1-002"
    assert result["value"] == 50.0
    assert result["numerator"] == 40
    assert result["denominator"] == 80
    repo.count_distinct_audit_users.assert_awaited_once()
    repo.count_active_users.assert_awaited_once()


@pytest.mark.asyncio
async def test_kpi_g1_002_zero_active_users():
    """Division by zero guard: active_users == 0 → rate 0.0."""
    repo = _mock_repo(count_distinct_audit_users=0, count_active_users=0)
    with patch(_PATCH, return_value=repo):
        result = await compute_kpi_g1_002(_mock_db(), school_id=_SID)

    assert result["value"] == 0.0


@pytest.mark.asyncio
async def test_kpi_g1_002_custom_period():
    repo = _mock_repo(count_distinct_audit_users=10, count_active_users=20)
    with patch(_PATCH, return_value=repo):
        result = await compute_kpi_g1_002(_mock_db(), school_id=_SID, period_days=14)

    assert result["period"] == "14d"


# ---------------------------------------------------------------------------
# compute_kpi_g1_003 — Auth error rate
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_kpi_g1_003_normal():
    # Two calls to count_audit_events: total, then failed
    call_count = 0

    async def _count(**kwargs):
        nonlocal call_count
        call_count += 1
        return 200 if call_count == 1 else 10

    repo = MagicMock()
    repo.count_audit_events = AsyncMock(side_effect=_count)

    with patch(_PATCH, return_value=repo):
        result = await compute_kpi_g1_003(_mock_db(), school_id=_SID)

    assert result["kpi_id"] == "KPI-G1-003"
    assert result["value"] == 5.0  # 10/200*100
    assert result["numerator"] == 10
    assert result["denominator"] == 200
    assert repo.count_audit_events.await_count == 2


@pytest.mark.asyncio
async def test_kpi_g1_003_zero_total_auth():
    """Division by zero guard."""
    repo = MagicMock()
    repo.count_audit_events = AsyncMock(return_value=0)
    with patch(_PATCH, return_value=repo):
        result = await compute_kpi_g1_003(_mock_db(), school_id=_SID)

    assert result["value"] == 0.0


@pytest.mark.asyncio
async def test_kpi_g1_003_passes_outcomes_to_second_call():
    repo = MagicMock()
    repo.count_audit_events = AsyncMock(return_value=0)
    with patch(_PATCH, return_value=repo):
        await compute_kpi_g1_003(_mock_db(), school_id=_SID)

    # Second call should include outcomes filter
    second_call_kwargs = repo.count_audit_events.call_args_list[1].kwargs
    assert "outcomes" in second_call_kwargs
    assert "denied" in second_call_kwargs["outcomes"]


# ---------------------------------------------------------------------------
# compute_kpi_g1_004 — API latency (static, no DB calls)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_kpi_g1_004_static_response():
    result = await compute_kpi_g1_004(_mock_db(), school_id=_SID)

    assert result["kpi_id"] == "KPI-G1-004"
    assert result["value"] is None
    assert result["data_source"] == "prometheus"
    assert "query" in result


@pytest.mark.asyncio
async def test_kpi_g1_004_custom_period():
    result = await compute_kpi_g1_004(_mock_db(), school_id=_SID, period_days=30)
    assert result["period"] == "30d"


# ---------------------------------------------------------------------------
# compute_kpi_g1_005 — Incident count
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_kpi_g1_005_normal():
    repo = _mock_repo(count_audit_events=5)
    with patch(_PATCH, return_value=repo):
        result = await compute_kpi_g1_005(_mock_db(), school_id=_SID)

    assert result["kpi_id"] == "KPI-G1-005"
    assert result["value"] == 5.0
    assert result["numerator"] == 5
    repo.count_audit_events.assert_awaited_once()
    call_kwargs = repo.count_audit_events.call_args.kwargs
    assert "outcomes" in call_kwargs
    assert "error" in call_kwargs["outcomes"]


@pytest.mark.asyncio
async def test_kpi_g1_005_zero_incidents():
    repo = _mock_repo(count_audit_events=0)
    with patch(_PATCH, return_value=repo):
        result = await compute_kpi_g1_005(_mock_db(), school_id=_SID)

    assert result["value"] == 0.0


@pytest.mark.asyncio
async def test_kpi_g1_005_custom_period():
    repo = _mock_repo(count_audit_events=3)
    with patch(_PATCH, return_value=repo):
        result = await compute_kpi_g1_005(_mock_db(), school_id=_SID, period_days=30)

    assert result["period"] == "30d"


# ---------------------------------------------------------------------------
# compute_kpi_g1_006 — Invitation conversion
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_kpi_g1_006_normal():
    repo = _mock_repo(count_invitations_created=100, count_invitations_consumed=60)
    with patch(_PATCH, return_value=repo):
        result = await compute_kpi_g1_006(_mock_db(), school_id=_SID)

    assert result["kpi_id"] == "KPI-G1-006"
    assert result["value"] == 60.0
    assert result["numerator"] == 60
    assert result["denominator"] == 100
    repo.count_invitations_created.assert_awaited_once()
    call_kwargs = repo.count_invitations_created.call_args.kwargs
    assert call_kwargs["school_id"] == _SID
    assert "from_dt" in call_kwargs
    repo.count_invitations_consumed.assert_awaited_once()


@pytest.mark.asyncio
async def test_kpi_g1_006_zero_created():
    """Division by zero guard: no invitations created → rate 0.0."""
    repo = _mock_repo(count_invitations_created=0, count_invitations_consumed=0)
    with patch(_PATCH, return_value=repo):
        result = await compute_kpi_g1_006(_mock_db(), school_id=_SID)

    assert result["value"] == 0.0


@pytest.mark.asyncio
async def test_kpi_g1_006_full_conversion():
    repo = _mock_repo(count_invitations_created=10, count_invitations_consumed=10)
    with patch(_PATCH, return_value=repo):
        result = await compute_kpi_g1_006(_mock_db(), school_id=_SID)

    assert result["value"] == 100.0


@pytest.mark.asyncio
async def test_kpi_g1_006_custom_period():
    repo = _mock_repo(count_invitations_created=5, count_invitations_consumed=3)
    with patch(_PATCH, return_value=repo):
        result = await compute_kpi_g1_006(_mock_db(), school_id=_SID, period_days=30)

    assert result["period"] == "30d"
    assert result["value"] == 60.0


# ---------------------------------------------------------------------------
# compute_all_kpis — aggregates all 6 KPIs
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_compute_all_kpis_returns_all_six():
    repo = _mock_repo(
        count_active_accounts=100,
        count_active_users=80,
        count_distinct_audit_users=50,
        count_audit_events=5,
        count_invitations_created=10,
        count_invitations_consumed=7,
    )
    # count_audit_events is called twice in g1_003 (total and failed)
    repo.count_audit_events = AsyncMock(side_effect=[100, 2, 5])  # g1_003×2 + g1_005×1

    with patch(_PATCH, return_value=repo):
        results = await compute_all_kpis(_mock_db(), school_id=_SID)

    assert len(results) == 6
    kpi_ids = [r["kpi_id"] for r in results]
    assert "KPI-G1-001" in kpi_ids
    assert "KPI-G1-002" in kpi_ids
    assert "KPI-G1-003" in kpi_ids
    assert "KPI-G1-004" in kpi_ids
    assert "KPI-G1-005" in kpi_ids
    assert "KPI-G1-006" in kpi_ids


@pytest.mark.asyncio
async def test_compute_all_kpis_has_computed_at():
    repo = _mock_repo(
        count_active_accounts=10,
        count_active_users=5,
        count_distinct_audit_users=3,
        count_invitations_created=0,
        count_invitations_consumed=0,
    )
    repo.count_audit_events = AsyncMock(return_value=0)

    with patch(_PATCH, return_value=repo):
        results = await compute_all_kpis(_mock_db(), school_id=_SID)

    for r in results:
        assert "computed_at" in r


@pytest.mark.asyncio
async def test_compute_all_kpis_one_fails_returns_error_entry():
    """If one KPI raises, compute_all_kpis catches and returns error dict."""
    repo = MagicMock()
    repo.count_active_accounts = AsyncMock(side_effect=RuntimeError("DB error"))
    repo.count_active_users = AsyncMock(return_value=0)
    repo.count_distinct_audit_users = AsyncMock(return_value=0)
    repo.count_audit_events = AsyncMock(return_value=0)
    repo.count_invitations_created = AsyncMock(return_value=0)
    repo.count_invitations_consumed = AsyncMock(return_value=0)

    with patch(_PATCH, return_value=repo):
        results = await compute_all_kpis(_mock_db(), school_id=_SID)

    # Still 6 entries (error entry for failed KPI)
    assert len(results) == 6
    # The first one (g1_001) should be an error entry
    error_entries = [r for r in results if r.get("value") is None and "error" in r]
    assert len(error_entries) >= 1
    assert "DB error" in error_entries[0]["error"]


@pytest.mark.asyncio
async def test_compute_all_kpis_error_entry_has_computed_at():
    repo = MagicMock()
    repo.count_active_accounts = AsyncMock(side_effect=ValueError("boom"))
    repo.count_active_users = AsyncMock(return_value=0)
    repo.count_distinct_audit_users = AsyncMock(return_value=0)
    repo.count_audit_events = AsyncMock(return_value=0)
    repo.count_invitations_created = AsyncMock(return_value=0)
    repo.count_invitations_consumed = AsyncMock(return_value=0)

    with patch(_PATCH, return_value=repo):
        results = await compute_all_kpis(_mock_db(), school_id=_SID)

    error_entry = next(r for r in results if "error" in r)
    assert "computed_at" in error_entry


@pytest.mark.asyncio
async def test_compute_all_kpis_custom_period():
    repo = _mock_repo(
        count_active_accounts=50,
        count_active_users=25,
        count_distinct_audit_users=10,
        count_invitations_created=5,
        count_invitations_consumed=2,
    )
    repo.count_audit_events = AsyncMock(return_value=0)

    with patch(_PATCH, return_value=repo):
        results = await compute_all_kpis(_mock_db(), school_id=_SID, period_days=30)

    for r in results:
        if "period" in r:
            assert r["period"] == "30d"


# ---------------------------------------------------------------------------
# Rounding
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_kpi_values_rounded_to_2_decimals():
    repo = _mock_repo(count_active_accounts=3, count_active_users=2)
    with patch(_PATCH, return_value=repo):
        result = await compute_kpi_g1_001(_mock_db(), school_id=_SID)

    # 2/3*100 = 66.666... → rounded to 66.67
    assert result["value"] == round(2 / 3 * 100, 2)
