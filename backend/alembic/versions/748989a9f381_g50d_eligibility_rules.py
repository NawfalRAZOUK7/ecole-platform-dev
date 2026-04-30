"""g50d eligibility_rules (Phase 3.4).

Declarative rules for "can student X be promoted/admitted to program Y?".

Per the original design we deliberately keep this *simple* — a small
table where each row is one rule:

    (kind, target_program_id, condition_type, condition_params, message_key)

Built-in condition_types live in the service evaluator; admins compose
rules by referencing them. We do NOT introduce a DSL — when the rule
catalog grows past ~10 condition_types the right move is to revisit.

Revision ID: 748989a9f381
Revises: 72e15d401f00
Create Date: 2026-04-28 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "748989a9f381"
down_revision = "72e15d401f00"
branch_labels = None
depends_on = None


RULE_KINDS = ("PROMOTION", "ADMISSION", "TRANSFER")


def upgrade() -> None:
    op.create_table(
        "eligibility_rules",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "school_id",
            sa.UUID(),
            sa.ForeignKey("schools.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column(
            "target_program_id",
            sa.UUID(),
            sa.ForeignKey("programs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("condition_type", sa.String(40), nullable=False),
        sa.Column(
            "condition_params",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("message_key", sa.String(100), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "kind IN (" + ", ".join(f"'{k}'" for k in RULE_KINDS) + ")",
            name="ck_eligibility_rules_kind",
        ),
    )
    op.create_index(
        "idx_eligibility_rules_school_kind_target",
        "eligibility_rules",
        ["school_id", "kind", "target_program_id"],
    )
    op.create_index(
        "idx_eligibility_rules_active",
        "eligibility_rules",
        ["school_id", "is_active"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_eligibility_rules_active",
        table_name="eligibility_rules",
    )
    op.drop_index(
        "idx_eligibility_rules_school_kind_target",
        table_name="eligibility_rules",
    )
    op.drop_table("eligibility_rules")
