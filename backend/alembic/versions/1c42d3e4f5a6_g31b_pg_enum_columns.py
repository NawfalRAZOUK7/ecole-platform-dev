"""G31b — convert string-backed status/type columns to PostgreSQL enums.

Revision ID: 1c42d3e4f5a6
Revises: 0a31b2c3d4e5
Create Date: 2026-03-29
"""

from __future__ import annotations

import re
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "1c42d3e4f5a6"
down_revision: Union[str, None] = "0a31b2c3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

USER_STATUS_ENUM = postgresql.ENUM(
    "active",
    "inactive",
    "suspended",
    name="user_status_enum",
)
MEMBERSHIP_STATUS_ENUM = postgresql.ENUM(
    "active",
    "inactive",
    name="membership_status_enum",
)
ROLE_CODE_ENUM = postgresql.ENUM(
    "ADM",
    "DIR",
    "TCH",
    "PAR",
    "STD",
    "SUP",
    "SYS",
    "CONTENT_MGR",
    name="role_code_enum",
)
RECOVERY_STATUS_ENUM = postgresql.ENUM(
    "pending",
    "verified",
    "reset",
    name="recovery_status_enum",
)
INVOICE_STATUS_ENUM = postgresql.ENUM(
    "pending",
    "paid",
    "failed",
    "canceled",
    name="invoice_status_enum",
)
PAYMENT_STATUS_ENUM = postgresql.ENUM(
    "pending",
    "processing",
    "paid",
    "failed",
    "canceled",
    name="payment_status_enum",
)
ENROLLMENT_STATUS_ENUM = postgresql.ENUM(
    "active",
    "transferred",
    "dropped",
    name="enrollment_status_enum",
)
ATTENDANCE_STATUS_ENUM = postgresql.ENUM(
    "present",
    "absent",
    "excused",
    "late",
    name="attendance_status_enum",
)
NOTIFICATION_CATEGORY_ENUM = postgresql.ENUM(
    "academic",
    "billing",
    "attendance",
    "system",
    "announcement",
    name="notification_category_enum",
)
NOTIFICATION_PRIORITY_ENUM = postgresql.ENUM(
    "low",
    "normal",
    "high",
    "critical",
    name="notification_priority_enum",
)
DELIVERY_CHANNEL_ENUM = postgresql.ENUM(
    "in_app",
    "email",
    "sms",
    "push",
    name="delivery_channel_enum",
)
DELIVERY_STATUS_ENUM = postgresql.ENUM(
    "queued",
    "sent",
    "delivered",
    "failed",
    "clicked",
    "opened",
    "bounced",
    "fallback",
    "suppressed",
    name="delivery_status_enum",
)
CONSENT_STATUS_ENUM = postgresql.ENUM(
    "opted_in",
    "opted_out",
    name="consent_status_enum",
)
DEVICE_PLATFORM_ENUM = postgresql.ENUM(
    "android",
    "ios",
    "web",
    name="device_platform_enum",
)
CONVERSATION_TYPE_ENUM = postgresql.ENUM(
    "DIRECT",
    "GROUP",
    name="conversation_type_enum",
)
PARTICIPANT_ROLE_ENUM = postgresql.ENUM(
    "INITIATOR",
    "PARTICIPANT",
    name="participant_role_enum",
)
ANNOUNCEMENT_STATUS_ENUM = postgresql.ENUM(
    "DRAFT",
    "PUBLISHED",
    "ARCHIVED",
    name="announcement_status_enum",
)
REPORT_JOB_STATUS_ENUM = postgresql.ENUM(
    "pending",
    "generating",
    "ready",
    "failed",
    name="report_job_status_enum",
)
REPORT_TYPE_ENUM = postgresql.ENUM(
    "student_report_card",
    "class_summary",
    "attendance_report",
    "billing_statement",
    "school_analytics",
    name="report_type_enum",
)
DATA_EXPORT_FORMAT_ENUM = postgresql.ENUM(
    "csv",
    "xlsx",
    name="data_export_format_enum",
)
DOCUMENT_CATEGORY_ENUM = postgresql.ENUM(
    "certificate",
    "report_card",
    "medical",
    "identity",
    "transcript",
    "other",
    name="document_category_enum",
)
RESOURCE_TYPE_ENUM = postgresql.ENUM(
    "lesson_plan",
    "worksheet",
    "presentation",
    "exam_template",
    "reference",
    name="resource_type_enum",
)
RESOURCE_VISIBILITY_ENUM = postgresql.ENUM(
    "school",
    "class",
    name="resource_visibility_enum",
)
ASSIGNMENT_TYPE_ENUM = postgresql.ENUM(
    "STANDARD",
    "PRINTABLE_PDF",
    "QUIZ",
    name="assignment_type_enum",
)
SUBMISSION_STATUS_ENUM = postgresql.ENUM(
    "draft",
    "submitted",
    "graded",
    "returned",
    name="submission_status_enum",
)
QUIZ_ATTEMPT_STATUS_ENUM = postgresql.ENUM(
    "STARTED",
    "COMPLETED",
    "TIMED_OUT",
    name="quiz_attempt_status_enum",
)
TIMETABLE_JOB_STATUS_ENUM = postgresql.ENUM(
    "pending",
    "running",
    "completed",
    "failed",
    "applied",
    name="timetable_job_status_enum",
)

ENUM_TYPES = [
    USER_STATUS_ENUM,
    MEMBERSHIP_STATUS_ENUM,
    ROLE_CODE_ENUM,
    RECOVERY_STATUS_ENUM,
    INVOICE_STATUS_ENUM,
    PAYMENT_STATUS_ENUM,
    ENROLLMENT_STATUS_ENUM,
    ATTENDANCE_STATUS_ENUM,
    NOTIFICATION_CATEGORY_ENUM,
    NOTIFICATION_PRIORITY_ENUM,
    DELIVERY_CHANNEL_ENUM,
    DELIVERY_STATUS_ENUM,
    CONSENT_STATUS_ENUM,
    DEVICE_PLATFORM_ENUM,
    CONVERSATION_TYPE_ENUM,
    PARTICIPANT_ROLE_ENUM,
    ANNOUNCEMENT_STATUS_ENUM,
    REPORT_JOB_STATUS_ENUM,
    REPORT_TYPE_ENUM,
    DATA_EXPORT_FORMAT_ENUM,
    DOCUMENT_CATEGORY_ENUM,
    RESOURCE_TYPE_ENUM,
    RESOURCE_VISIBILITY_ENUM,
    ASSIGNMENT_TYPE_ENUM,
    SUBMISSION_STATUS_ENUM,
    QUIZ_ATTEMPT_STATUS_ENUM,
    TIMETABLE_JOB_STATUS_ENUM,
]

COLUMN_CONVERSIONS: list[tuple[str, str, postgresql.ENUM, int]] = [
    ("users", "status", USER_STATUS_ENUM, 20),
    ("memberships", "status", MEMBERSHIP_STATUS_ENUM, 20),
    ("memberships", "role_code", ROLE_CODE_ENUM, 20),
    ("account_recovery_requests", "status", RECOVERY_STATUS_ENUM, 20),
    ("invoices", "status", INVOICE_STATUS_ENUM, 20),
    ("payment_attempts", "status", PAYMENT_STATUS_ENUM, 20),
    ("enrollments", "status", ENROLLMENT_STATUS_ENUM, 20),
    ("attendance_records", "status", ATTENDANCE_STATUS_ENUM, 20),
    ("notifications", "category", NOTIFICATION_CATEGORY_ENUM, 30),
    ("notifications", "priority", NOTIFICATION_PRIORITY_ENUM, 20),
    ("notification_deliveries", "channel", DELIVERY_CHANNEL_ENUM, 20),
    ("notification_deliveries", "status", DELIVERY_STATUS_ENUM, 20),
    ("consent_preferences", "status", CONSENT_STATUS_ENUM, 20),
    ("consent_preferences", "channel", DELIVERY_CHANNEL_ENUM, 20),
    ("device_tokens", "platform", DEVICE_PLATFORM_ENUM, 20),
    ("conversations", "type", CONVERSATION_TYPE_ENUM, 20),
    (
        "conversation_participants",
        "role_in_conversation",
        PARTICIPANT_ROLE_ENUM,
        20,
    ),
    ("announcements", "status", ANNOUNCEMENT_STATUS_ENUM, 20),
    ("report_jobs", "status", REPORT_JOB_STATUS_ENUM, 20),
    ("report_jobs", "type", REPORT_TYPE_ENUM, 50),
    ("report_schedules", "report_type", REPORT_TYPE_ENUM, 50),
    ("data_exports", "format", DATA_EXPORT_FORMAT_ENUM, 10),
    ("documents", "category", DOCUMENT_CATEGORY_ENUM, 40),
    ("resources", "type", RESOURCE_TYPE_ENUM, 40),
    ("resources", "visibility", RESOURCE_VISIBILITY_ENUM, 20),
    ("assignments", "exercise_type", ASSIGNMENT_TYPE_ENUM, 20),
    ("submissions", "status", SUBMISSION_STATUS_ENUM, 20),
    ("quiz_attempts", "status", QUIZ_ATTEMPT_STATUS_ENUM, 20),
    ("timetable_generation_jobs", "status", TIMETABLE_JOB_STATUS_ENUM, 20),
]

STATUS_PARTIAL_INDEXES = [
    (
        "uq_memberships_user_school_role_active",
        "memberships",
        ["user_id", "school_id", "role_code"],
        True,
        "status = 'active'",
        "status = 'active'::membership_status_enum",
    ),
    (
        "uq_enrollments_school_student_period_active",
        "enrollments",
        ["school_id", "student_id", "period_id"],
        True,
        "status = 'active'",
        "status = 'active'::enrollment_status_enum",
    ),
    (
        "uq_submissions_assignment_student_active",
        "submissions",
        ["assignment_id", "student_id"],
        True,
        "status IN ('draft', 'submitted')",
        "status IN ('draft'::submission_status_enum, 'submitted'::submission_status_enum)",
    ),
]

DEFAULT_LITERAL_RE = re.compile(r"'((?:[^']|'')*)'")


MV_KPI_DAILY_SQL = sa.text(
    """
    CREATE MATERIALIZED VIEW mv_kpi_daily AS
    WITH
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
    """
)


VW_USER_PERMISSIONS_SQL = sa.text(
    """
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
    """
)

VW_ACTIVE_SESSIONS_SQL = sa.text(
    """
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
    """
)

VW_ASSIGNMENT_RESULTS_SQL = sa.text(
    """
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
    """
)

VW_INVOICE_BALANCE_SQL = sa.text(
    """
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
    """
)


def _drop_dependent_views() -> None:
    op.execute(sa.text("DROP MATERIALIZED VIEW IF EXISTS mv_kpi_daily"))
    op.execute(sa.text("DROP VIEW IF EXISTS vw_invoice_balance"))
    op.execute(sa.text("DROP VIEW IF EXISTS vw_assignment_results"))
    op.execute(sa.text("DROP VIEW IF EXISTS vw_active_sessions"))
    op.execute(sa.text("DROP VIEW IF EXISTS vw_user_permissions"))


def _create_dependent_views() -> None:
    op.execute(VW_USER_PERMISSIONS_SQL)
    op.execute(VW_ACTIVE_SESSIONS_SQL)
    op.execute(VW_ASSIGNMENT_RESULTS_SQL)
    op.execute(VW_INVOICE_BALANCE_SQL)
    op.execute(MV_KPI_DAILY_SQL)
    op.execute(
        sa.text(
            "CREATE UNIQUE INDEX idx_mv_kpi_daily_school_kpi ON mv_kpi_daily (school_id, kpi_id)"
        )
    )


def _drop_status_partial_indexes() -> None:
    for index_name, table_name, _, _, _, _ in STATUS_PARTIAL_INDEXES:
        op.drop_index(index_name, table_name=table_name)


def _create_status_partial_indexes(*, use_enum_predicates: bool) -> None:
    for index_name, table_name, columns, unique, string_predicate, enum_predicate in STATUS_PARTIAL_INDEXES:
        op.create_index(
            index_name,
            table_name,
            columns,
            unique=unique,
            postgresql_where=sa.text(
                enum_predicate if use_enum_predicates else string_predicate
            ),
        )


def _load_string_defaults(
    bind, conversions: list[tuple[str, str, postgresql.ENUM, int]]
) -> dict[tuple[str, str], str]:
    defaults: dict[tuple[str, str], str] = {}
    for table_name, column_name, _, _ in conversions:
        default_expr = bind.execute(
            sa.text(
                """
                SELECT column_default
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = :table_name
                  AND column_name = :column_name
                """
            ),
            {"table_name": table_name, "column_name": column_name},
        ).scalar_one_or_none()
        if not default_expr:
            continue
        match = DEFAULT_LITERAL_RE.search(default_expr)
        if not match:
            continue
        defaults[(table_name, column_name)] = match.group(1).replace("''", "'")
        op.execute(
            sa.text(
                f'ALTER TABLE "{table_name}" ALTER COLUMN "{column_name}" DROP DEFAULT'
            )
        )
    return defaults


def _restore_defaults(
    defaults: dict[tuple[str, str], str],
    *,
    use_enum_casts: bool,
) -> None:
    enum_lookup = {
        (table_name, column_name): enum_type.name
        for table_name, column_name, enum_type, _ in COLUMN_CONVERSIONS
    }
    for (table_name, column_name), default_value in defaults.items():
        escaped = default_value.replace("'", "''")
        if use_enum_casts:
            default_sql = f"'{escaped}'::{enum_lookup[(table_name, column_name)]}"
        else:
            default_sql = f"'{escaped}'"
        op.execute(
            sa.text(
                f'ALTER TABLE "{table_name}" ALTER COLUMN "{column_name}" SET DEFAULT {default_sql}'
            )
        )


def upgrade() -> None:
    bind = op.get_bind()
    _drop_dependent_views()
    _drop_status_partial_indexes()
    defaults = _load_string_defaults(bind, COLUMN_CONVERSIONS)

    for enum_type in ENUM_TYPES:
        enum_type.create(bind, checkfirst=False)

    for table_name, column_name, enum_type, length in COLUMN_CONVERSIONS:
        op.alter_column(
            table_name,
            column_name,
            existing_type=sa.String(length=length),
            type_=enum_type,
            postgresql_using=f"{column_name}::text::{enum_type.name}",
        )

    _restore_defaults(defaults, use_enum_casts=True)
    _create_dependent_views()
    _create_status_partial_indexes(use_enum_predicates=True)


def downgrade() -> None:
    _drop_dependent_views()
    _drop_status_partial_indexes()
    bind = op.get_bind()
    defaults = _load_string_defaults(bind, COLUMN_CONVERSIONS)

    for table_name, column_name, enum_type, length in reversed(COLUMN_CONVERSIONS):
        op.alter_column(
            table_name,
            column_name,
            existing_type=enum_type,
            type_=sa.String(length=length),
            postgresql_using=f"{column_name}::text",
        )

    _restore_defaults(defaults, use_enum_casts=False)
    for enum_type in reversed(ENUM_TYPES):
        enum_type.drop(bind, checkfirst=False)

    _create_dependent_views()
    _create_status_partial_indexes(use_enum_predicates=False)
