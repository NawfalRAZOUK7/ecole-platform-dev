"""g48 add max_consecutive_classes timetable constraint type

Revision ID: e9f0a1b2c3d4
Revises: d8e9f0a1b2c3
Create Date: 2026-04-18 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "e9f0a1b2c3d4"
down_revision = "d8e9f0a1b2c3"
branch_labels = None
depends_on = None


_UPGRADE_CONDITION = (
    "constraint_type IN ("
    "'teacher_unavailable',"
    "'room_capacity',"
    "'max_consecutive_classes',"
    "'max_hours_per_day',"
    "'subject_hours_per_week',"
    "'no_consecutive_same_subject'"
    ")"
)

_DOWNGRADE_CONDITION = (
    "constraint_type IN ("
    "'teacher_unavailable',"
    "'room_capacity',"
    "'max_hours_per_day',"
    "'subject_hours_per_week',"
    "'no_consecutive_same_subject'"
    ")"
)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = set(inspector.get_table_names())
    if "timetable_constraints" not in table_names:
        return

    constraints = {
        constraint["name"]
        for constraint in inspector.get_check_constraints("timetable_constraints")
        if constraint["name"]
    }
    if "ck_timetable_constraints_type" in constraints:
        op.drop_constraint(
            "ck_timetable_constraints_type",
            "timetable_constraints",
            type_="check",
        )
    op.create_check_constraint(
        "ck_timetable_constraints_type",
        "timetable_constraints",
        _UPGRADE_CONDITION,
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = set(inspector.get_table_names())
    if "timetable_constraints" not in table_names:
        return

    constraints = {
        constraint["name"]
        for constraint in inspector.get_check_constraints("timetable_constraints")
        if constraint["name"]
    }
    if "ck_timetable_constraints_type" in constraints:
        op.drop_constraint(
            "ck_timetable_constraints_type",
            "timetable_constraints",
            type_="check",
        )
    op.create_check_constraint(
        "ck_timetable_constraints_type",
        "timetable_constraints",
        _DOWNGRADE_CONDITION,
    )
