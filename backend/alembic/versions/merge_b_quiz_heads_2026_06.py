"""Merge the 6 divergent migration heads into one.

The migration graph had drifted into 6 parallel heads, which makes
``alembic upgrade head`` ambiguous. This empty merge revision unifies them so
later migrations (e.g. add_quiz_source_columns) have a single linear base.

Revision ID: merge_b_quiz_heads_2026_06
Revises: 748989a9f381, add_phase11_security_columns, b8c9d0e1f2a3, d1e2f3a4b5c6, d9e8f7a6b5c4, e9f0a1b2c3d4
Create Date: 2026-06-05 00:00:00.000000
"""

from __future__ import annotations

# revision identifiers, used by Alembic.
revision = "merge_b_quiz_heads_2026_06"
down_revision = (
    "748989a9f381",
    "add_phase11_security_columns",
    "b8c9d0e1f2a3",
    "d1e2f3a4b5c6",
    "d9e8f7a6b5c4",
    "e9f0a1b2c3d4",
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    """No-op: this revision only merges heads."""


def downgrade() -> None:
    """No-op: merge revisions are not reversible in a meaningful way."""
