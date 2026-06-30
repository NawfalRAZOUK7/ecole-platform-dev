"""Add ``amazigh`` and ``quranic`` to content_subject_enum.

Both were previously documented TODOs in ``ContentSubject`` (amazigh = official
MEN matière since 2011; quranic = msid Quran memorisation). They are now real
enum members, so content/quizzes can use them without the ``other`` escape hatch.

`ALTER TYPE ... ADD VALUE` cannot run inside a transaction block, so the
statements run in an ``autocommit_block``. ``IF NOT EXISTS`` makes it idempotent.
Postgres cannot drop enum values, so ``downgrade`` is a documented no-op.

Revision ID: 20260633_subject_amz_qur
Revises: 20260632_subject_enum_other
Create Date: 2026-07-03
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "20260633_subject_amz_qur"
down_revision: Union[str, None] = "20260632_subject_enum_other"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_NEW_VALUES = ("amazigh", "quranic")


def upgrade() -> None:
    with op.get_context().autocommit_block():
        for value in _NEW_VALUES:
            op.execute(
                f"ALTER TYPE content_subject_enum ADD VALUE IF NOT EXISTS '{value}'"
            )


def downgrade() -> None:
    # Postgres has no DROP VALUE for enums; removing a value would require
    # recreating the type and recasting every column. Intentionally a no-op —
    # leaving the (now-unused) values in place is harmless.
    pass
