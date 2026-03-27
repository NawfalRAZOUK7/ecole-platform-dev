"""KPI computation service."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.analytics import AnalyticsRepository

logger = logging.getLogger(__name__)


async def compute_kpi_g1_001(
    db: AsyncSession,
    *,
    school_id: uuid.UUID,
    period_days: int = 7,
) -> dict[str, Any]:
    repo = AnalyticsRepository(db)
    cutoff = datetime.now(timezone.utc) - timedelta(days=period_days)
    total_accounts = await repo.count_active_accounts(school_id=school_id)
    active_accounts = await repo.count_active_users(
        school_id=school_id,
        from_dt=cutoff,
        to_dt=datetime.now(timezone.utc),
    )
    rate = (active_accounts / total_accounts * 100) if total_accounts > 0 else 0.0
    return {
        "kpi_id": "KPI-G1-001",
        "name": "Adoption activation pilote",
        "value": round(rate, 2),
        "unit": "percent",
        "numerator": active_accounts,
        "denominator": total_accounts,
        "period": f"{period_days}d",
        "threshold": "DEC-G1-020",
    }


async def compute_kpi_g1_002(
    db: AsyncSession,
    *,
    school_id: uuid.UUID,
    period_days: int = 7,
) -> dict[str, Any]:
    repo = AnalyticsRepository(db)
    cutoff = datetime.now(timezone.utc) - timedelta(days=period_days)
    critical_actions = [
        "CONTENT_PROGRESS_UPDATED",
        "NOTIFICATION_READ",
        "RESULT_VIEWED",
        "PAYMENT_INITIATED",
        "SUBMISSION_CREATED",
        "ASSESSMENT_RESULT_SUBMITTED",
    ]
    journey_users = await repo.count_distinct_audit_users(
        school_id=school_id,
        from_dt=cutoff,
        to_dt=datetime.now(timezone.utc),
        action_types=critical_actions,
        outcome="success",
    )
    active_users = await repo.count_active_users(
        school_id=school_id,
        from_dt=cutoff,
        to_dt=datetime.now(timezone.utc),
    )
    rate = (journey_users / active_users * 100) if active_users > 0 else 0.0
    return {
        "kpi_id": "KPI-G1-002",
        "name": "Usage parcours critiques",
        "value": round(rate, 2),
        "unit": "percent",
        "numerator": journey_users,
        "denominator": active_users,
        "period": f"{period_days}d",
        "threshold": "DEC-G1-020",
    }


async def compute_kpi_g1_003(
    db: AsyncSession,
    *,
    school_id: uuid.UUID,
    period_days: int = 1,
) -> dict[str, Any]:
    repo = AnalyticsRepository(db)
    cutoff = datetime.now(timezone.utc) - timedelta(days=period_days)
    auth_actions = [
        "AUTH_LOGIN",
        "AUTH_REFRESH",
        "AUTH_LOGOUT",
        "AUTH_LOGIN_FAILED",
        "AUTH_REFRESH_FAILED",
    ]
    total_auth = await repo.count_audit_events(
        school_id=school_id,
        from_dt=cutoff,
        action_types=auth_actions,
    )
    failed_auth = await repo.count_audit_events(
        school_id=school_id,
        from_dt=cutoff,
        action_types=auth_actions,
        outcomes=["denied", "error"],
    )
    rate = (failed_auth / total_auth * 100) if total_auth > 0 else 0.0
    return {
        "kpi_id": "KPI-G1-003",
        "name": "Taux erreurs auth",
        "value": round(rate, 2),
        "unit": "percent",
        "numerator": failed_auth,
        "denominator": total_auth,
        "period": f"{period_days}d",
        "threshold": "<=1.0% (30d)",
    }


async def compute_kpi_g1_004(
    db: AsyncSession,
    *,
    school_id: uuid.UUID,
    period_days: int = 1,
) -> dict[str, Any]:
    return {
        "kpi_id": "KPI-G1-004",
        "name": "Latence API p95",
        "value": None,
        "unit": "milliseconds",
        "data_source": "prometheus",
        "query": "histogram_quantile(0.95, rate(api_request_duration_seconds_bucket[5m]))",
        "period": f"{period_days}d",
        "threshold": "<=350ms (30d)",
        "note": "Query Prometheus /api/v1/query for live value",
    }


async def compute_kpi_g1_005(
    db: AsyncSession,
    *,
    school_id: uuid.UUID,
    period_days: int = 7,
) -> dict[str, Any]:
    repo = AnalyticsRepository(db)
    cutoff = datetime.now(timezone.utc) - timedelta(days=period_days)
    incident_count = await repo.count_audit_events(
        school_id=school_id,
        from_dt=cutoff,
        outcomes=["error"],
    )
    return {
        "kpi_id": "KPI-G1-005",
        "name": "Taux incidents support",
        "value": float(incident_count),
        "unit": "incidents/week",
        "numerator": incident_count,
        "period": f"{period_days}d",
        "threshold": "DEC-G1-021",
        "note": "Approximated from audit error events. Production uses incident management.",
    }


async def compute_kpi_g1_006(
    db: AsyncSession,
    *,
    school_id: uuid.UUID,
    period_days: int = 7,
) -> dict[str, Any]:
    repo = AnalyticsRepository(db)
    cutoff = datetime.now(timezone.utc) - timedelta(days=period_days)
    created = await repo.count_invitations_created(school_id=school_id, from_dt=cutoff)
    consumed = await repo.count_invitations_consumed(school_id=school_id, from_dt=cutoff)
    rate = (consumed / created * 100) if created > 0 else 0.0
    return {
        "kpi_id": "KPI-G1-006",
        "name": "Conversion rattachement compte-ecole",
        "value": round(rate, 2),
        "unit": "percent",
        "numerator": consumed,
        "denominator": created,
        "period": f"{period_days}d",
        "threshold": "DEC-G1-020",
    }


async def compute_all_kpis(
    db: AsyncSession,
    *,
    school_id: uuid.UUID,
    period_days: int = 7,
) -> list[dict[str, Any]]:
    kpis = []
    for compute_fn in [
        compute_kpi_g1_001,
        compute_kpi_g1_002,
        compute_kpi_g1_003,
        compute_kpi_g1_004,
        compute_kpi_g1_005,
        compute_kpi_g1_006,
    ]:
        try:
            result = await compute_fn(db, school_id=school_id, period_days=period_days)
            result["computed_at"] = datetime.now(timezone.utc).isoformat()
            kpis.append(result)
        except Exception as exc:
            logger.warning("KPI computation failed for %s: %s", compute_fn.__name__, exc)
            kpis.append(
                {
                    "kpi_id": compute_fn.__name__.replace("compute_", "")
                    .upper()
                    .replace("_", "-"),
                    "name": "Computation error",
                    "value": None,
                    "error": str(exc),
                    "computed_at": datetime.now(timezone.utc).isoformat(),
                }
            )
    return kpis
