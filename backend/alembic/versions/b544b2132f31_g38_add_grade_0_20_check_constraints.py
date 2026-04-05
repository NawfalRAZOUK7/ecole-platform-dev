"""g38 add grade 0-20 CHECK constraints.

Revision ID: b544b2132f31
Revises: 0d4e5f6a7b8c
Create Date: 2026-04-05 19:43:56.222637
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b544b2132f31"
down_revision: Union[str, None] = "0d4e5f6a7b8c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_grades_score_range",
        "grades",
        "score >= 0 AND score <= 20",
    )
    op.create_check_constraint(
        "ck_assessment_results_score_range",
        "assessment_results",
        "score IS NULL OR (score >= 0 AND score <= 20)",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_assessment_results_score_range",
        "assessment_results",
        type_="check",
    )
    op.drop_constraint(
        "ck_grades_score_range",
        "grades",
        type_="check",
    )
