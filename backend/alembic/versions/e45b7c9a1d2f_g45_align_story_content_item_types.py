"""g45 align story content item types

Revision ID: e45b7c9a1d2f
Revises: d4c8f1a7e2b3
Create Date: 2026-04-14 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql.compiler import IdentifierPreparer


# revision identifiers, used by Alembic.
revision = "e45b7c9a1d2f"
down_revision = "d4c8f1a7e2b3"
branch_labels = None
depends_on = None


def _get_content_type_enum_name(bind) -> str | None:
    row = bind.execute(
        sa.text(
            """
            SELECT data_type, udt_name
            FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = 'content_items'
              AND column_name = 'content_type'
            """
        )
    ).mappings().one_or_none()
    if row is None or row["data_type"] != "USER-DEFINED":
        return None
    return str(row["udt_name"])


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"]: column for column in inspector.get_columns("content_items")}

    if "target_age_min" in columns and isinstance(
        columns["target_age_min"]["type"], sa.SmallInteger
    ):
        op.alter_column(
            "content_items",
            "target_age_min",
            existing_type=sa.SmallInteger(),
            type_=sa.Integer(),
            existing_nullable=True,
        )

    if "target_age_max" in columns and isinstance(
        columns["target_age_max"]["type"], sa.SmallInteger
    ):
        op.alter_column(
            "content_items",
            "target_age_max",
            existing_type=sa.SmallInteger(),
            type_=sa.Integer(),
            existing_nullable=True,
        )

    enum_name = _get_content_type_enum_name(bind)
    if enum_name is None:
        return

    existing_values = bind.execute(
        sa.text(
            """
            SELECT enumlabel
            FROM pg_type t
            JOIN pg_enum e ON e.enumtypid = t.oid
            WHERE t.typname = :enum_name
            ORDER BY e.enumsortorder
            """
        ),
        {"enum_name": enum_name},
    ).scalars().all()

    preparer = IdentifierPreparer(bind.dialect)
    quoted_enum_name = preparer.quote(enum_name)
    for value in ("story", "coloring_book"):
        if value not in existing_values:
            op.execute(
                sa.text(
                    f"ALTER TYPE {quoted_enum_name} ADD VALUE IF NOT EXISTS '{value}'"
                )
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"]: column for column in inspector.get_columns("content_items")}

    if "target_age_max" in columns and isinstance(
        columns["target_age_max"]["type"], sa.Integer
    ):
        op.alter_column(
            "content_items",
            "target_age_max",
            existing_type=sa.Integer(),
            type_=sa.SmallInteger(),
            existing_nullable=True,
        )

    if "target_age_min" in columns and isinstance(
        columns["target_age_min"]["type"], sa.Integer
    ):
        op.alter_column(
            "content_items",
            "target_age_min",
            existing_type=sa.Integer(),
            type_=sa.SmallInteger(),
            existing_nullable=True,
        )

