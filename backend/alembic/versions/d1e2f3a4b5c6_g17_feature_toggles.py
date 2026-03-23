"""G17: Feature toggles table (Phase 11E)

Revision ID: d1e2f3a4b5c6
Revises: c0d1e2f3a4b5
Create Date: 2026-03-23

New tables:
  - feature_toggles: feature flag configuration with school/role scoping

Indexes:
  - ix_feature_toggles_feature_key (unique via column constraint)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "d1e2f3a4b5c6"
down_revision = "c0d1e2f3a4b5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "feature_toggles",
        sa.Column("id", sa.Uuid(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("feature_key", sa.String(100), nullable=False),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "enabled_globally",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "enabled_school_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "enabled_role_codes",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Unique index on feature_key
    op.create_index(
        "ix_feature_toggles_feature_key",
        "feature_toggles",
        ["feature_key"],
        unique=True,
    )

    # ── Pre-create 6 default feature toggles ──────────────────────────
    op.execute(
        """
        INSERT INTO feature_toggles (id, feature_key, display_name, description, enabled_globally, enabled_school_ids, enabled_role_codes)
        VALUES
            (gen_random_uuid(), 'content_library', 'Content Library', 'Platform-wide content library (CMS) for reusable learning resources', false, '[]'::jsonb, '[]'::jsonb),
            (gen_random_uuid(), 'quiz_engine', 'Quiz Engine', 'Interactive quiz creation and attempt engine', false, '[]'::jsonb, '[]'::jsonb),
            (gen_random_uuid(), 'pdf_exercises', 'PDF Exercises', 'PDF exercise generation and submission workflow', false, '[]'::jsonb, '[]'::jsonb),
            (gen_random_uuid(), 'messaging', 'Messaging', 'Parent-teacher direct and group messaging', false, '[]'::jsonb, '[]'::jsonb),
            (gen_random_uuid(), 'announcements', 'Announcements', 'School-wide announcement publish and targeting', false, '[]'::jsonb, '[]'::jsonb),
            (gen_random_uuid(), 'timetable', 'Timetable', 'Weekly timetable management with exceptions', false, '[]'::jsonb, '[]'::jsonb);
        """
    )


def downgrade() -> None:
    op.drop_index("ix_feature_toggles_feature_key", table_name="feature_toggles")
    op.drop_table("feature_toggles")
