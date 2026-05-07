"""g46 level age mappings

Revision ID: f6e5d4c3b2a1
Revises: e45b7c9a1d2f
Create Date: 2026-04-17 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f6e5d4c3b2a1"
down_revision = "e45b7c9a1d2f"
branch_labels = None
depends_on = None


DEFAULT_MAPPINGS = [
    ("maternelle", "Maternelle", "ما قبل المدرسة", "Preschool", 3, 5, 0),
    ("cp", "Cours Préparatoire", "السنة الأولى ابتدائي", "1st Grade", 5, 6, 1),
    ("ce1", "Cours Élémentaire 1", "السنة الثانية ابتدائي", "2nd Grade", 6, 7, 2),
    ("ce2", "Cours Élémentaire 2", "السنة الثالثة ابتدائي", "3rd Grade", 7, 8, 3),
    ("cm1", "Cours Moyen 1", "السنة الرابعة ابتدائي", "4th Grade", 8, 9, 4),
    ("cm2", "Cours Moyen 2", "السنة الخامسة ابتدائي", "5th Grade", 9, 10, 5),
    ("6eme", "6ème", "السادسة إعدادي", "6th Grade", 10, 11, 6),
    ("5eme", "5ème", "الخامسة إعدادي", "7th Grade", 11, 12, 7),
    ("4eme", "4ème", "الرابعة إعدادي", "8th Grade", 12, 13, 8),
    ("3eme", "3ème", "الثالثة إعدادي", "9th Grade", 13, 14, 9),
    ("2nde", "Seconde", "الثانية ثانوي", "10th Grade", 14, 15, 10),
    ("1ere", "Première", "الأولى ثانوي", "11th Grade", 15, 16, 11),
    ("terminale", "Terminale", "الجذع المشترك", "12th Grade", 16, 17, 12),
]


def upgrade() -> None:
    op.create_table(
        "level_age_mappings",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("level_code", sa.String(50), nullable=False),
        sa.Column("label_fr", sa.String(100), nullable=False),
        sa.Column("label_ar", sa.String(100), nullable=True),
        sa.Column("label_en", sa.String(100), nullable=True),
        sa.Column("default_age_min", sa.SmallInteger(), nullable=False),
        sa.Column("default_age_max", sa.SmallInteger(), nullable=False),
        sa.Column("display_order", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column(
            "school_id",
            sa.UUID(),
            sa.ForeignKey("schools.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        # Unique constraint supporting NULL school_id (platform defaults)
        sa.UniqueConstraint(
            "level_code",
            "school_id",
            name="uq_level_age_mappings_code_school",
        ),
    )
    op.create_index(
        "ix_level_age_mappings_school_id",
        "level_age_mappings",
        ["school_id"],
    )
    op.create_index(
        "ix_level_age_mappings_display_order",
        "level_age_mappings",
        ["display_order"],
    )

    # Seed default platform-wide mappings (school_id = NULL)
    bind = op.get_bind()
    for level_code, label_fr, label_ar, label_en, age_min, age_max, order in DEFAULT_MAPPINGS:
        bind.execute(
            sa.text(
                """
                INSERT INTO level_age_mappings
                  (level_code, label_fr, label_ar, label_en,
                   default_age_min, default_age_max, display_order)
                VALUES
                  (:level_code, :label_fr, :label_ar, :label_en,
                   :age_min, :age_max, :order)
                ON CONFLICT DO NOTHING
                """
            ),
            {
                "level_code": level_code,
                "label_fr": label_fr,
                "label_ar": label_ar,
                "label_en": label_en,
                "age_min": age_min,
                "age_max": age_max,
                "order": order,
            },
        )


def downgrade() -> None:
    op.drop_index("ix_level_age_mappings_display_order", table_name="level_age_mappings")
    op.drop_index("ix_level_age_mappings_school_id", table_name="level_age_mappings")
    op.drop_table("level_age_mappings")
