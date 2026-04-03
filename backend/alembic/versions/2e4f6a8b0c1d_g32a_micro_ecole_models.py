"""G32a — micro-school models and EDUCATOR role support.

Revision ID: 2e4f6a8b0c1d
Revises: 1c42d3e4f5a6
Create Date: 2026-04-03
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "2e4f6a8b0c1d"
down_revision: Union[str, None] = "1c42d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

MICRO_SCHOOL_STATUS_ENUM = postgresql.ENUM(
    "active",
    "suspended",
    "closed",
    name="micro_school_status_enum",
    create_type=False,
)
MICRO_ENROLLMENT_STATUS_ENUM = postgresql.ENUM(
    "active",
    "withdrawn",
    name="micro_enrollment_status_enum",
    create_type=False,
)
MICRO_PAYMENT_PERIOD_TYPE_ENUM = postgresql.ENUM(
    "weekly",
    "monthly",
    name="micro_payment_period_type_enum",
    create_type=False,
)
MICRO_PAYMENT_STATUS_ENUM = postgresql.ENUM(
    "pending",
    "paid",
    "overdue",
    name="micro_payment_status_enum",
    create_type=False,
)
MICRO_RESOURCE_TYPE_ENUM = postgresql.ENUM(
    "activity_sheet",
    "song",
    "game",
    "lesson_plan",
    name="micro_resource_type_enum",
    create_type=False,
)


def _drop_role_views() -> None:
    op.execute(sa.text("DROP VIEW IF EXISTS vw_active_sessions"))
    op.execute(sa.text("DROP VIEW IF EXISTS vw_user_permissions"))


def _create_role_views() -> None:
    op.execute(
        sa.text(
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
    )
    op.execute(
        sa.text(
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
    )


def _remove_educator_role_value() -> None:
    old_enum = postgresql.ENUM(
        "ADM",
        "DIR",
        "TCH",
        "PAR",
        "STD",
        "SUP",
        "SYS",
        "CONTENT_MGR",
        name="role_code_enum_old",
    )
    restored_enum = postgresql.ENUM(
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

    op.execute(sa.text("DELETE FROM memberships WHERE role_code = 'EDUCATOR'"))
    _drop_role_views()
    op.execute(sa.text("ALTER TYPE role_code_enum RENAME TO role_code_enum_old"))
    restored_enum.create(op.get_bind(), checkfirst=False)
    op.execute(
        sa.text(
            """
            ALTER TABLE memberships
            ALTER COLUMN role_code TYPE role_code_enum
            USING role_code::text::role_code_enum
            """
        )
    )
    old_enum.drop(op.get_bind(), checkfirst=False)
    _create_role_views()


def upgrade() -> None:
    bind = op.get_bind()

    _drop_role_views()
    op.execute(sa.text("ALTER TYPE role_code_enum ADD VALUE IF NOT EXISTS 'EDUCATOR'"))
    _create_role_views()

    MICRO_SCHOOL_STATUS_ENUM.create(bind, checkfirst=True)
    MICRO_ENROLLMENT_STATUS_ENUM.create(bind, checkfirst=True)
    MICRO_PAYMENT_PERIOD_TYPE_ENUM.create(bind, checkfirst=True)
    MICRO_PAYMENT_STATUS_ENUM.create(bind, checkfirst=True)
    MICRO_RESOURCE_TYPE_ENUM.create(bind, checkfirst=True)

    op.create_table(
        "micro_schools",
        sa.Column("educator_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("neighborhood", sa.String(length=200), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column(
            "max_capacity",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("20"),
        ),
        sa.Column(
            "status",
            MICRO_SCHOOL_STATUS_ENUM,
            nullable=False,
            server_default=sa.text("'active'"),
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("max_capacity > 0", name="ck_micro_schools_max_capacity"),
        sa.ForeignKeyConstraint(["educator_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_micro_schools_educator",
        "micro_schools",
        ["educator_id"],
        unique=False,
    )
    op.create_index(
        "idx_micro_schools_city_status",
        "micro_schools",
        ["city", "status"],
        unique=False,
    )

    op.create_table(
        "micro_groups",
        sa.Column("micro_school_id", sa.Uuid(), nullable=False),
        sa.Column(
            "name",
            sa.String(length=100),
            nullable=False,
            server_default=sa.text("'المجموعة'"),
        ),
        sa.Column(
            "age_range_min",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("2"),
        ),
        sa.Column(
            "age_range_max",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("6"),
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "age_range_min >= 2 AND age_range_min <= 6",
            name="ck_micro_groups_age_range_min",
        ),
        sa.CheckConstraint(
            "age_range_max >= 2 AND age_range_max <= 6",
            name="ck_micro_groups_age_range_max",
        ),
        sa.CheckConstraint(
            "age_range_max >= age_range_min",
            name="ck_micro_groups_age_range_order",
        ),
        sa.ForeignKeyConstraint(
            ["micro_school_id"],
            ["micro_schools.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_micro_groups_school",
        "micro_groups",
        ["micro_school_id"],
        unique=False,
    )

    op.create_table(
        "micro_enrollments",
        sa.Column("micro_group_id", sa.Uuid(), nullable=False),
        sa.Column("child_name", sa.String(length=200), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("enrolled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            MICRO_ENROLLMENT_STATUS_ENUM,
            nullable=False,
            server_default=sa.text("'active'"),
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["micro_group_id"],
            ["micro_groups.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["parent_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_micro_enrollments_group_status",
        "micro_enrollments",
        ["micro_group_id", "status"],
        unique=False,
    )
    op.create_index(
        "idx_micro_enrollments_parent_status",
        "micro_enrollments",
        ["parent_id", "status"],
        unique=False,
    )

    op.create_table(
        "micro_payments",
        sa.Column("micro_school_id", sa.Uuid(), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=False),
        sa.Column("child_enrollment_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
            server_default=sa.text("'MAD'"),
        ),
        sa.Column(
            "period_type",
            MICRO_PAYMENT_PERIOD_TYPE_ENUM,
            nullable=False,
            server_default=sa.text("'monthly'"),
        ),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            MICRO_PAYMENT_STATUS_ENUM,
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("amount > 0", name="ck_micro_payments_amount"),
        sa.CheckConstraint(
            "period_end >= period_start",
            name="ck_micro_payments_period_window",
        ),
        sa.ForeignKeyConstraint(
            ["micro_school_id"],
            ["micro_schools.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["parent_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["child_enrollment_id"],
            ["micro_enrollments.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_micro_payments_school_status",
        "micro_payments",
        ["micro_school_id", "status"],
        unique=False,
    )
    op.create_index(
        "idx_micro_payments_parent_period",
        "micro_payments",
        ["parent_id", "period_start"],
        unique=False,
    )

    op.create_table(
        "micro_resources",
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("resource_type", MICRO_RESOURCE_TYPE_ENUM, nullable=False),
        sa.Column("age_group", sa.String(length=20), nullable=False),
        sa.Column(
            "language",
            sa.String(length=5),
            nullable=False,
            server_default=sa.text("'ar'"),
        ),
        sa.Column("file_url", sa.String(length=500), nullable=True),
        sa.Column(
            "is_premium",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_micro_resources_type_language_age",
        "micro_resources",
        ["resource_type", "language", "age_group"],
        unique=False,
    )

    op.create_table(
        "micro_progress_logs",
        sa.Column("micro_enrollment_id", sa.Uuid(), nullable=False),
        sa.Column("educator_id", sa.Uuid(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("photo_url", sa.String(length=500), nullable=True),
        sa.Column("milestone_tag", sa.String(length=50), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["micro_enrollment_id"],
            ["micro_enrollments.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["educator_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_micro_progress_logs_enrollment_date",
        "micro_progress_logs",
        ["micro_enrollment_id", "date"],
        unique=False,
    )
    op.create_index(
        "idx_micro_progress_logs_educator_date",
        "micro_progress_logs",
        ["educator_id", "date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "idx_micro_progress_logs_educator_date",
        table_name="micro_progress_logs",
    )
    op.drop_index(
        "idx_micro_progress_logs_enrollment_date",
        table_name="micro_progress_logs",
    )
    op.drop_table("micro_progress_logs")

    op.drop_index(
        "idx_micro_resources_type_language_age",
        table_name="micro_resources",
    )
    op.drop_table("micro_resources")

    op.drop_index("idx_micro_payments_parent_period", table_name="micro_payments")
    op.drop_index("idx_micro_payments_school_status", table_name="micro_payments")
    op.drop_table("micro_payments")

    op.drop_index(
        "idx_micro_enrollments_parent_status",
        table_name="micro_enrollments",
    )
    op.drop_index(
        "idx_micro_enrollments_group_status",
        table_name="micro_enrollments",
    )
    op.drop_table("micro_enrollments")

    op.drop_index("idx_micro_groups_school", table_name="micro_groups")
    op.drop_table("micro_groups")

    op.drop_index("idx_micro_schools_city_status", table_name="micro_schools")
    op.drop_index("idx_micro_schools_educator", table_name="micro_schools")
    op.drop_table("micro_schools")

    bind = op.get_bind()
    MICRO_RESOURCE_TYPE_ENUM.drop(bind, checkfirst=True)
    MICRO_PAYMENT_STATUS_ENUM.drop(bind, checkfirst=True)
    MICRO_PAYMENT_PERIOD_TYPE_ENUM.drop(bind, checkfirst=True)
    MICRO_ENROLLMENT_STATUS_ENUM.drop(bind, checkfirst=True)
    MICRO_SCHOOL_STATUS_ENUM.drop(bind, checkfirst=True)

    _remove_educator_role_value()
