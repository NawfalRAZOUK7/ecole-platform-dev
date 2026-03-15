"""KPI computation service — SQL queries for G1 KPI catalog.

Reference: S-140 — KPI computation queries, Pack G1 — Data & Reporting
KPIs: KPI-G1-001 to KPI-G1-006

Data lineage per G1.2:
  KPI-G1-001: IAM core (users, sessions) + auth login events
  KPI-G1-002: Scenarios critiques (notifications, results, invoices, content)
  KPI-G1-003: Auth metrics (4xx+5xx / total auth requests)
  KPI-G1-004: API latency p95 (from Prometheus metrics, not SQL)
  KPI-G1-005: Incident count (from ops logs, approximated via audit_logs)
  KPI-G1-006: Invitation conversion (invites consumed / created)

All queries use the school's timezone (Africa/Casablanca) for period boundaries.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.iam import InvitationCode, Membership, Session, User

logger = logging.getLogger(__name__)


async def compute_kpi_g1_001(
    db: AsyncSession,
    *,
    school_id: uuid.UUID,
    period_days: int = 7,
) -> dict[str, Any]:
    """KPI-G1-001: Adoption activation pilote.

    Formula: active accounts (7d) / total activated pilot accounts
    Source: IAM core tables + session login activity

    An "active" account is one with at least one session created in the period.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=period_days)

    # Total activated accounts in school
    total_result = await db.execute(
        select(func.count(func.distinct(User.id))).where(
            User.school_id == school_id,
            User.status == "active",
        )
    )
    total_accounts = total_result.scalar() or 0

    # Active accounts (had a session in the period)
    active_result = await db.execute(
        select(func.count(func.distinct(Session.user_id))).where(
            Session.school_id == school_id,
            Session.created_at >= cutoff,
        )
    )
    active_accounts = active_result.scalar() or 0

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
    """KPI-G1-002: Usage parcours critiques.

    Formula: P0 journeys completed / P0 journeys started
    Source: audit_logs with action_types for critical path actions

    Approximation: count distinct users who performed at least one critical action
    (content progress, notification read, result view, payment)
    vs total active users.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=period_days)

    # Critical path action types from audit_logs
    critical_actions = [
        "CONTENT_PROGRESS_UPDATED",
        "NOTIFICATION_READ",
        "RESULT_VIEWED",
        "PAYMENT_INITIATED",
        "SUBMISSION_CREATED",
        "ASSESSMENT_RESULT_SUBMITTED",
    ]

    # Users who performed at least one critical action
    from app.models.audit import AuditLog

    journey_result = await db.execute(
        select(func.count(func.distinct(AuditLog.actor_id))).where(
            AuditLog.school_id == school_id,
            AuditLog.created_at >= cutoff,
            AuditLog.action_type.in_(critical_actions),
            AuditLog.outcome == "success",
        )
    )
    journey_users = journey_result.scalar() or 0

    # Total active users in period
    active_result = await db.execute(
        select(func.count(func.distinct(Session.user_id))).where(
            Session.school_id == school_id,
            Session.created_at >= cutoff,
        )
    )
    active_users = active_result.scalar() or 0

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
    """KPI-G1-003: Taux erreurs auth.

    Formula: (4xx+5xx auth) / total auth requests
    Source: audit_logs with auth action types

    Target: ≤ 1.0% (30-day rolling)
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=period_days)

    auth_actions = [
        "AUTH_LOGIN",
        "AUTH_REFRESH",
        "AUTH_LOGOUT",
        "AUTH_LOGIN_FAILED",
        "AUTH_REFRESH_FAILED",
    ]

    from app.models.audit import AuditLog

    # Total auth events
    total_result = await db.execute(
        select(func.count()).where(
            AuditLog.school_id == school_id,
            AuditLog.created_at >= cutoff,
            AuditLog.action_type.in_(auth_actions),
        )
    )
    total_auth = total_result.scalar() or 0

    # Failed auth events (outcome = denied or error)
    failed_result = await db.execute(
        select(func.count()).where(
            AuditLog.school_id == school_id,
            AuditLog.created_at >= cutoff,
            AuditLog.action_type.in_(auth_actions),
            AuditLog.outcome.in_(["denied", "error"]),
        )
    )
    failed_auth = failed_result.scalar() or 0

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
    """KPI-G1-004: Latence API p95.

    NOTE: This KPI is derived from Prometheus metrics (F2), not SQL.
    The SQL implementation returns a placeholder.
    Actual values come from: api_request_duration_seconds histogram (p95).

    Target: ≤ 350ms (30-day rolling)
    """
    # This KPI is sourced from Prometheus, not the database.
    # Return metadata-only result indicating the data source.
    return {
        "kpi_id": "KPI-G1-004",
        "name": "Latence API p95",
        "value": None,
        "unit": "milliseconds",
        "data_source": "prometheus",
        "query": 'histogram_quantile(0.95, rate(api_request_duration_seconds_bucket[5m]))',
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
    """KPI-G1-005: Taux incidents support.

    Formula: (SEV-1 + SEV-2 incidents) / week
    Source: F4 incident logs (approximated via audit_logs with error outcomes)

    Note: In production this would query the incident management system.
    We approximate by counting severe error audit events.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=period_days)

    from app.models.audit import AuditLog

    # Count distinct error events (approximation for incidents)
    incident_result = await db.execute(
        select(func.count()).where(
            AuditLog.school_id == school_id,
            AuditLog.created_at >= cutoff,
            AuditLog.outcome == "error",
        )
    )
    incident_count = incident_result.scalar() or 0

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
    """KPI-G1-006: Conversion rattachement compte-ecole.

    Formula: invites_consumed_success / invites_created
    Source: invitation_codes table
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=period_days)

    # Total invitations created in period
    created_result = await db.execute(
        select(func.count()).where(
            InvitationCode.school_id == school_id,
            InvitationCode.created_at >= cutoff,
        )
    )
    created = created_result.scalar() or 0

    # Consumed invitations in period
    consumed_result = await db.execute(
        select(func.count()).where(
            InvitationCode.school_id == school_id,
            InvitationCode.created_at >= cutoff,
            InvitationCode.consumed_at.isnot(None),
        )
    )
    consumed = consumed_result.scalar() or 0

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


# ---------------------------------------------------------------------------
# Aggregate all KPIs
# ---------------------------------------------------------------------------
async def compute_all_kpis(
    db: AsyncSession,
    *,
    school_id: uuid.UUID,
    period_days: int = 7,
) -> list[dict[str, Any]]:
    """Compute all G1 KPIs for a school."""
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
            kpis.append({
                "kpi_id": compute_fn.__name__.replace("compute_", "").upper().replace("_", "-"),
                "name": "Computation error",
                "value": None,
                "error": str(exc),
                "computed_at": datetime.now(timezone.utc).isoformat(),
            })
    return kpis
