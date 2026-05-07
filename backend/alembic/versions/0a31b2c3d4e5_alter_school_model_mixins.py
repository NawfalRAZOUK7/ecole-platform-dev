"""G31a — School model and school_id foreign keys.

Revision ID: 0a31b2c3d4e5
Revises: f28394a5b6c7
Create Date: 2026-03-29
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0a31b2c3d4e5"
down_revision: Union[str, None] = "f28394a5b6c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES_WITH_SCHOOL_ID: list[str] = [
    "users",
    "memberships",
    "sessions",
    "login_history",
    "invitation_codes",
    "account_recovery_requests",
    "parent_child_links",
    "student_profiles",
    "parent_profiles",
    "teacher_profiles",
    "admin_profiles",
    "content_manager_profiles",
    "academic_years",
    "periods",
    "classes",
    "enrollments",
    "teacher_assignments",
    "attendance_sessions",
    "attendance_records",
    "absence_justifications",
    "justification_reviews",
    "attendance_alerts",
    "timetable_constraints",
    "timetable_generation_jobs",
    "timetable_slots",
    "timetable_exceptions",
    "courses",
    "grade_categories",
    "rubrics",
    "student_period_averages",
    "content_items",
    "activities",
    "class_content_assignments",
    "content_submissions",
    "quizzes",
    "question_bank_items",
    "invoices",
    "payment_attempts",
    "provider_webhook_events",
    "fee_structures",
    "fee_assignments",
    "sibling_discount_policies",
    "late_fee_policies",
    "payment_plans",
    "consent_preferences",
    "notifications",
    "notification_preferences",
    "device_tokens",
    "notification_deliveries",
    "parent_feed_items",
    "conversations",
    "announcements",
    "documents",
    "resources",
    "student_document_requirements",
    "events",
    "event_reminder_preferences",
    "report_schedules",
    "report_jobs",
    "data_exports",
    "audit_logs",
    "writing_attempts",
    "ai_preferences",
]


def _seed_schools_sql() -> str:
    selects = "\nUNION\n".join(
        f"SELECT DISTINCT school_id FROM {table_name} WHERE school_id IS NOT NULL"
        for table_name in TABLES_WITH_SCHOOL_ID
    )
    return f"""
WITH existing_school_ids AS (
    {selects}
),
ranked_school_ids AS (
    SELECT school_id, ROW_NUMBER() OVER (ORDER BY school_id) AS seq
    FROM existing_school_ids
)
INSERT INTO schools (
    id,
    name,
    code,
    status,
    timezone,
    default_language,
    grading_scale,
    settings,
    created_at,
    updated_at
)
SELECT
    school_id,
    'School ' || seq,
    'SCH-' || LPAD(seq::text, 4, '0'),
    'active',
    'Africa/Casablanca',
    'fr',
    'moroccan_20',
    '{{}}'::jsonb,
    NOW(),
    NOW()
FROM ranked_school_ids
ON CONFLICT (id) DO NOTHING
"""


def upgrade() -> None:
    op.create_table(
        "schools",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("name_ar", sa.String(length=255), nullable=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("massar_code", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("region", sa.String(length=100), nullable=True),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("website", sa.String(length=500), nullable=True),
        sa.Column("logo_path", sa.String(length=500), nullable=True),
        sa.Column("max_students", sa.Integer(), nullable=True),
        sa.Column("max_teachers", sa.Integer(), nullable=True),
        sa.Column("subscription_plan", sa.String(length=50), nullable=True),
        sa.Column("subscription_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("timezone", sa.String(length=50), nullable=False),
        sa.Column("default_language", sa.String(length=5), nullable=False),
        sa.Column("grading_scale", sa.String(length=20), nullable=False),
        sa.Column(
            "settings",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        sa.UniqueConstraint("massar_code"),
    )

    op.execute(sa.text(_seed_schools_sql()))

    for table_name in TABLES_WITH_SCHOOL_ID:
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.create_foreign_key(
                f"fk_{table_name}_school_id_schools",
                "schools",
                ["school_id"],
                ["id"],
                ondelete="CASCADE",
            )


def downgrade() -> None:
    for table_name in reversed(TABLES_WITH_SCHOOL_ID):
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.drop_constraint(
                f"fk_{table_name}_school_id_schools",
                type_="foreignkey",
            )

    op.drop_table("schools")
