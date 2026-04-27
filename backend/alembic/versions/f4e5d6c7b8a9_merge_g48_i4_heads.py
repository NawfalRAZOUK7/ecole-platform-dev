"""merge g48 and i4 migration heads

Revision ID: f4e5d6c7b8a9
Revises: e9f0a1b2c3d4, b2c3d4e5f6a7
Create Date: 2026-04-27 01:15:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union


revision: str = "f4e5d6c7b8a9"
down_revision: tuple[str, str] = ("e9f0a1b2c3d4", "b2c3d4e5f6a7")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
