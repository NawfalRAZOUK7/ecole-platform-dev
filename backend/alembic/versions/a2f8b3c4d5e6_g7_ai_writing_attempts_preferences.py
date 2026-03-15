"""G7: AI — writing_attempts + ai_preferences tables.

Revision ID: a2f8b3c4d5e6
Revises: 9f7257bc8dd1
Create Date: 2026-03-15 18:00:00.000000

Reference: S-143 (Writing assistance), S-144 (AI opt-out), Pack G3
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a2f8b3c4d5e6"
down_revision: str = "9f7257bc8dd1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # writing_attempts
    op.create_table(
        "writing_attempts",
        sa.Column("id", sa.Uuid(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("student_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("subject", sa.String(200), nullable=True),
        sa.Column("input_text", sa.Text(), nullable=False),
        sa.Column("input_word_count", sa.Integer(), nullable=False, default=0),
        sa.Column("status", sa.String(20), nullable=False, default="completed"),
        sa.Column("suggestion", sa.Text(), nullable=True),
        sa.Column("hints", postgresql.JSONB(), nullable=True),
        sa.Column("prompt_id", sa.String(50), nullable=True),
        sa.Column("prompt_version", sa.Integer(), nullable=True),
        sa.Column("warnings", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_writing_attempts_student", "writing_attempts", ["student_id"])
    op.create_index("idx_writing_attempts_school", "writing_attempts", ["school_id"])

    # ai_preferences
    op.create_table(
        "ai_preferences",
        sa.Column("id", sa.Uuid(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("opt_out", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "target_user_id", name="uq_ai_preferences_user_target"),
    )
    op.create_index("idx_ai_preferences_target", "ai_preferences", ["target_user_id"])
    op.create_index("idx_ai_preferences_school", "ai_preferences", ["school_id"])


def downgrade() -> None:
    op.drop_table("ai_preferences")
    op.drop_table("writing_attempts")
