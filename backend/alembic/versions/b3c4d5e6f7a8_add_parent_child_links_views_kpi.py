"""G8: Phase 1A — parent_child_links table, views, mv_kpi_daily.

Revision ID: b3c4d5e6f7a8
Revises: a2f8b3c4d5e6
Create Date: 2026-03-15 22:00:00.000000

Reference: Phase 1A — Database Views, Parent-Child Links & Migration Hardening

Creates:
  - parent_child_links table (explicit parent-child relationships)
  - vw_user_permissions view (users + memberships + role permissions)
  - vw_active_sessions view (active sessions with user info)
  - vw_assignment_results view (assignments + submissions + grades summary)
  - vw_invoice_balance view (invoices + payments aggregated balance)
  - mv_kpi_daily materialized view (pre-computed KPI-G1-001 through G1-006)

Seeds parent_child_links for existing parent/student pairs.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b3c4d5e6f7a8"
down_revision: str = "a2f8b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. parent_child_links table ──────────────────────────────────────
    op.create_table(
        "parent_child_links",
        sa.Column("id", sa.Uuid(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("parent_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("child_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, default="active"),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("linked_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("parent_user_id", "child_user_id", "school_id", name="uq_parent_child_links_parent_child_school"),
    )
    op.create_index("idx_parent_child_links_parent", "parent_child_links", ["parent_user_id", "school_id"])
    op.create_index("idx_parent_child_links_child", "parent_child_links", ["child_user_id"])

    # ── 2. Seed parent_child_links for existing seed data ────────────────
    # Link PARENT_1 (Hassan Alaoui) -> STUDENT_1 (Yassine Alaoui)
    # Link PARENT_2 (Khadija Idrissi) -> STUDENT_2 (Salma Idrissi)
    # Link PARENT_1 -> STUDENT_3 (Omar Benali) — second child
    op.execute(sa.text("""
        INSERT INTO parent_child_links (id, parent_user_id, child_user_id, school_id, status, linked_at, linked_by, created_at)
        SELECT
            gen_random_uuid(),
            p.id,
            s.id,
            p.school_id,
            'active',
            now(),
            (SELECT id FROM users WHERE email = 'admin@ecole-benani.ma' LIMIT 1),
            now()
        FROM users p
        CROSS JOIN users s
        WHERE (p.email, s.email) IN (
            ('parent.alaoui@gmail.com', 'yassine.alaoui@ecole-benani.ma'),
            ('parent.alaoui@gmail.com', 'omar.benali@ecole-benani.ma'),
            ('parent.idrissi@gmail.com', 'salma.idrissi@ecole-benani.ma')
        )
        AND p.school_id = s.school_id
        ON CONFLICT DO NOTHING
    """))

    # ── 3. vw_user_permissions view ──────────────────────────────────────
    # Joins users + memberships to show effective permissions per user
    op.execute(sa.text("""
        CREATE OR REPLACE VIEW vw_user_permissions AS
        SELECT
            u.id AS user_id,
            u.email,
            u.full_name,
            u.status AS user_status,
            u.school_id,
            m.role_code,
            m.status AS membership_status,
            m.created_at AS membership_since
        FROM users u
        INNER JOIN memberships m ON m.user_id = u.id
        WHERE m.status = 'active'
          AND u.status = 'active'
    """))

    # ── 4. vw_active_sessions view ───────────────────────────────────────
    # Active sessions (not revoked) with user info and device context
    op.execute(sa.text("""
        CREATE OR REPLACE VIEW vw_active_sessions AS
        SELECT
            s.id AS session_id,
            s.user_id,
            u.email,
            u.full_name,
            u.school_id,
            m.role_code,
            s.source,
            s.correlation_id,
            s.created_at AS session_started_at,
            EXTRACT(EPOCH FROM (now() - s.created_at)) / 3600.0 AS hours_active
        FROM sessions s
        INNER JOIN users u ON u.id = s.user_id
        LEFT JOIN memberships m ON m.user_id = u.id AND m.status = 'active'
        WHERE s.revoke_at IS NULL
    """))

    # ── 5. vw_assignment_results view ────────────────────────────────────
    # Assignments + submissions + grades summary per student
    op.execute(sa.text("""
        CREATE OR REPLACE VIEW vw_assignment_results AS
        SELECT
            a.id AS assignment_id,
            a.title AS assignment_title,
            a.total_points,
            a.due_at,
            c.id AS course_id,
            c.title AS course_title,
            c.school_id,
            sub.student_id,
            u.full_name AS student_name,
            sub.id AS submission_id,
            sub.status AS submission_status,
            sub.submitted_at,
            g.score,
            g.feedback_text,
            g.published_at AS grade_published_at,
            CASE
                WHEN a.total_points > 0 AND g.score IS NOT NULL
                THEN ROUND((g.score / a.total_points) * 100, 2)
                ELSE NULL
            END AS score_percent
        FROM assignments a
        INNER JOIN courses c ON c.id = a.course_id
        LEFT JOIN submissions sub ON sub.assignment_id = a.id
        LEFT JOIN users u ON u.id = sub.student_id
        LEFT JOIN grades g ON g.submission_id = sub.id
    """))

    # ── 6. vw_invoice_balance view ───────────────────────────────────────
    # Invoices + payment_attempts aggregated balance per parent
    op.execute(sa.text("""
        CREATE OR REPLACE VIEW vw_invoice_balance AS
        SELECT
            inv.id AS invoice_id,
            inv.school_id,
            inv.parent_id,
            u.full_name AS parent_name,
            inv.status AS invoice_status,
            inv.total_amount,
            inv.currency,
            inv.issued_date,
            inv.due_date,
            COALESCE(pay.paid_amount, 0) AS paid_amount,
            inv.total_amount - COALESCE(pay.paid_amount, 0) AS balance_due,
            COALESCE(pay.attempt_count, 0) AS payment_attempts,
            pay.last_attempt_at
        FROM invoices inv
        INNER JOIN users u ON u.id = inv.parent_id
        LEFT JOIN LATERAL (
            SELECT
                COUNT(*) AS attempt_count,
                SUM(CASE WHEN pa.status = 'paid' THEN inv.total_amount ELSE 0 END) AS paid_amount,
                MAX(pa.created_at) AS last_attempt_at
            FROM payment_attempts pa
            WHERE pa.invoice_id = inv.id
        ) pay ON true
    """))

    # ── 7. mv_kpi_daily materialized view ────────────────────────────────
    # Pre-computed KPI-G1-001 through G1-006, refreshed daily
    op.execute(sa.text("""
        CREATE MATERIALIZED VIEW mv_kpi_daily AS
        WITH
        -- KPI-G1-001: Adoption activation (active 7d / total)
        kpi_001 AS (
            SELECT
                u.school_id,
                'KPI-G1-001' AS kpi_id,
                'Adoption activation pilote' AS kpi_name,
                COUNT(DISTINCT u.id) AS denominator,
                COUNT(DISTINCT s.user_id) AS numerator,
                CASE
                    WHEN COUNT(DISTINCT u.id) > 0
                    THEN ROUND(COUNT(DISTINCT s.user_id)::numeric / COUNT(DISTINCT u.id) * 100, 2)
                    ELSE 0
                END AS value,
                'percent' AS unit
            FROM users u
            LEFT JOIN sessions s
                ON s.user_id = u.id
                AND s.created_at >= (now() - interval '7 days')
                AND s.school_id = u.school_id
            WHERE u.status = 'active'
            GROUP BY u.school_id
        ),
        -- KPI-G1-002: Critical journey usage
        kpi_002 AS (
            SELECT
                al.school_id,
                'KPI-G1-002' AS kpi_id,
                'Usage parcours critiques' AS kpi_name,
                (SELECT COUNT(DISTINCT s2.user_id)
                 FROM sessions s2
                 WHERE s2.school_id = al.school_id
                   AND s2.created_at >= (now() - interval '7 days')
                ) AS denominator,
                COUNT(DISTINCT al.actor_id) AS numerator,
                CASE
                    WHEN (SELECT COUNT(DISTINCT s2.user_id)
                          FROM sessions s2
                          WHERE s2.school_id = al.school_id
                            AND s2.created_at >= (now() - interval '7 days')) > 0
                    THEN ROUND(
                        COUNT(DISTINCT al.actor_id)::numeric /
                        (SELECT COUNT(DISTINCT s2.user_id)
                         FROM sessions s2
                         WHERE s2.school_id = al.school_id
                           AND s2.created_at >= (now() - interval '7 days')) * 100, 2)
                    ELSE 0
                END AS value,
                'percent' AS unit
            FROM audit_logs al
            WHERE al.created_at >= (now() - interval '7 days')
              AND al.action_type IN (
                  'CONTENT_PROGRESS_UPDATED', 'NOTIFICATION_READ',
                  'RESULT_VIEWED', 'PAYMENT_INITIATED',
                  'SUBMISSION_CREATED', 'ASSESSMENT_RESULT_SUBMITTED'
              )
              AND al.outcome = 'success'
            GROUP BY al.school_id
        ),
        -- KPI-G1-003: Auth error rate
        kpi_003 AS (
            SELECT
                al.school_id,
                'KPI-G1-003' AS kpi_id,
                'Taux erreurs auth' AS kpi_name,
                COUNT(*) AS denominator,
                COUNT(*) FILTER (WHERE al.outcome IN ('denied', 'error')) AS numerator,
                CASE
                    WHEN COUNT(*) > 0
                    THEN ROUND(
                        COUNT(*) FILTER (WHERE al.outcome IN ('denied', 'error'))::numeric / COUNT(*) * 100, 2)
                    ELSE 0
                END AS value,
                'percent' AS unit
            FROM audit_logs al
            WHERE al.created_at >= (now() - interval '7 days')
              AND al.action_type IN (
                  'AUTH_LOGIN', 'AUTH_REFRESH', 'AUTH_LOGOUT',
                  'AUTH_LOGIN_FAILED', 'AUTH_REFRESH_FAILED'
              )
            GROUP BY al.school_id
        ),
        -- KPI-G1-005: Support incidents (error audit events)
        kpi_005 AS (
            SELECT
                al.school_id,
                'KPI-G1-005' AS kpi_id,
                'Taux incidents support' AS kpi_name,
                0 AS denominator,
                COUNT(*) AS numerator,
                COUNT(*)::numeric AS value,
                'incidents/week' AS unit
            FROM audit_logs al
            WHERE al.created_at >= (now() - interval '7 days')
              AND al.outcome = 'error'
            GROUP BY al.school_id
        ),
        -- KPI-G1-006: Invitation conversion
        kpi_006 AS (
            SELECT
                ic.school_id,
                'KPI-G1-006' AS kpi_id,
                'Conversion rattachement' AS kpi_name,
                COUNT(*) AS denominator,
                COUNT(*) FILTER (WHERE ic.consumed_at IS NOT NULL) AS numerator,
                CASE
                    WHEN COUNT(*) > 0
                    THEN ROUND(
                        COUNT(*) FILTER (WHERE ic.consumed_at IS NOT NULL)::numeric / COUNT(*) * 100, 2)
                    ELSE 0
                END AS value,
                'percent' AS unit
            FROM invitation_codes ic
            WHERE ic.created_at >= (now() - interval '7 days')
            GROUP BY ic.school_id
        )
        -- Union all KPIs
        SELECT school_id, kpi_id, kpi_name, numerator, denominator, value, unit, now() AS computed_at
        FROM kpi_001
        UNION ALL
        SELECT school_id, kpi_id, kpi_name, numerator, denominator, value, unit, now() AS computed_at
        FROM kpi_002
        UNION ALL
        SELECT school_id, kpi_id, kpi_name, numerator, denominator, value, unit, now() AS computed_at
        FROM kpi_003
        UNION ALL
        SELECT school_id, kpi_id, kpi_name, numerator, denominator, value, unit, now() AS computed_at
        FROM kpi_005
        UNION ALL
        SELECT school_id, kpi_id, kpi_name, numerator, denominator, value, unit, now() AS computed_at
        FROM kpi_006
    """))

    # Create unique index on mv_kpi_daily for REFRESH CONCURRENTLY
    op.execute(sa.text(
        "CREATE UNIQUE INDEX idx_mv_kpi_daily_school_kpi ON mv_kpi_daily (school_id, kpi_id)"
    ))


def downgrade() -> None:
    # Drop materialized view
    op.execute(sa.text("DROP MATERIALIZED VIEW IF EXISTS mv_kpi_daily"))

    # Drop views
    op.execute(sa.text("DROP VIEW IF EXISTS vw_invoice_balance"))
    op.execute(sa.text("DROP VIEW IF EXISTS vw_assignment_results"))
    op.execute(sa.text("DROP VIEW IF EXISTS vw_active_sessions"))
    op.execute(sa.text("DROP VIEW IF EXISTS vw_user_permissions"))

    # Drop parent_child_links table
    op.drop_table("parent_child_links")
