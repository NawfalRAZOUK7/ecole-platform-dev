"""G24 — Phase 15 calendar and events.

Revision ID: 4e5f6a7b8c9d
Revises: 3d4e5f6a7b8c
Create Date: 2026-03-27
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4e5f6a7b8c9d"
down_revision: Union[str, None] = "3d4e5f6a7b8c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _holiday_rows() -> list[dict[str, object]]:
    return [
        {
            "id": uuid.uuid4(),
            "code": "new_year",
            "holiday_date": date(2026, 1, 1),
            "name_fr": "Nouvel An",
            "name_ar": "رأس السنة الميلادية",
            "name_en": "New Year's Day",
        },
        {
            "id": uuid.uuid4(),
            "code": "amazigh_new_year",
            "holiday_date": date(2026, 1, 14),
            "name_fr": "Nouvel An amazigh",
            "name_ar": "رأس السنة الأمازيغية",
            "name_en": "Amazigh New Year",
        },
        {
            "id": uuid.uuid4(),
            "code": "eid_al_fitr",
            "holiday_date": date(2026, 3, 20),
            "name_fr": "Aïd al-Fitr",
            "name_ar": "عيد الفطر",
            "name_en": "Eid al-Fitr",
        },
        {
            "id": uuid.uuid4(),
            "code": "labour_day",
            "holiday_date": date(2026, 5, 1),
            "name_fr": "Fête du Travail",
            "name_ar": "عيد العمال",
            "name_en": "Labour Day",
        },
        {
            "id": uuid.uuid4(),
            "code": "eid_al_adha",
            "holiday_date": date(2026, 5, 27),
            "name_fr": "Aïd al-Adha",
            "name_ar": "عيد الأضحى",
            "name_en": "Eid al-Adha",
        },
        {
            "id": uuid.uuid4(),
            "code": "throne_day",
            "holiday_date": date(2026, 7, 30),
            "name_fr": "Fête du Trône",
            "name_ar": "عيد العرش",
            "name_en": "Throne Day",
        },
        {
            "id": uuid.uuid4(),
            "code": "mawlid",
            "holiday_date": date(2026, 8, 26),
            "name_fr": "Mawlid",
            "name_ar": "المولد النبوي",
            "name_en": "Mawlid",
        },
        {
            "id": uuid.uuid4(),
            "code": "green_march",
            "holiday_date": date(2026, 11, 6),
            "name_fr": "Marche Verte",
            "name_ar": "المسيرة الخضراء",
            "name_en": "Green March",
        },
        {
            "id": uuid.uuid4(),
            "code": "independence_day",
            "holiday_date": date(2026, 11, 18),
            "name_fr": "Fête de l'Indépendance",
            "name_ar": "عيد الاستقلال",
            "name_en": "Independence Day",
        },
        {
            "id": uuid.uuid4(),
            "code": "new_year",
            "holiday_date": date(2027, 1, 1),
            "name_fr": "Nouvel An",
            "name_ar": "رأس السنة الميلادية",
            "name_en": "New Year's Day",
        },
        {
            "id": uuid.uuid4(),
            "code": "amazigh_new_year",
            "holiday_date": date(2027, 1, 14),
            "name_fr": "Nouvel An amazigh",
            "name_ar": "رأس السنة الأمازيغية",
            "name_en": "Amazigh New Year",
        },
        {
            "id": uuid.uuid4(),
            "code": "eid_al_fitr",
            "holiday_date": date(2027, 3, 9),
            "name_fr": "Aïd al-Fitr",
            "name_ar": "عيد الفطر",
            "name_en": "Eid al-Fitr",
        },
        {
            "id": uuid.uuid4(),
            "code": "labour_day",
            "holiday_date": date(2027, 5, 1),
            "name_fr": "Fête du Travail",
            "name_ar": "عيد العمال",
            "name_en": "Labour Day",
        },
        {
            "id": uuid.uuid4(),
            "code": "eid_al_adha",
            "holiday_date": date(2027, 5, 17),
            "name_fr": "Aïd al-Adha",
            "name_ar": "عيد الأضحى",
            "name_en": "Eid al-Adha",
        },
        {
            "id": uuid.uuid4(),
            "code": "throne_day",
            "holiday_date": date(2027, 7, 30),
            "name_fr": "Fête du Trône",
            "name_ar": "عيد العرش",
            "name_en": "Throne Day",
        },
        {
            "id": uuid.uuid4(),
            "code": "mawlid",
            "holiday_date": date(2027, 8, 15),
            "name_fr": "Mawlid",
            "name_ar": "المولد النبوي",
            "name_en": "Mawlid",
        },
        {
            "id": uuid.uuid4(),
            "code": "green_march",
            "holiday_date": date(2027, 11, 6),
            "name_fr": "Marche Verte",
            "name_ar": "المسيرة الخضراء",
            "name_en": "Green March",
        },
        {
            "id": uuid.uuid4(),
            "code": "independence_day",
            "holiday_date": date(2027, 11, 18),
            "name_fr": "Fête de l'Indépendance",
            "name_ar": "عيد الاستقلال",
            "name_en": "Independence Day",
        },
        {
            "id": uuid.uuid4(),
            "code": "new_year",
            "holiday_date": date(2028, 1, 1),
            "name_fr": "Nouvel An",
            "name_ar": "رأس السنة الميلادية",
            "name_en": "New Year's Day",
        },
        {
            "id": uuid.uuid4(),
            "code": "amazigh_new_year",
            "holiday_date": date(2028, 1, 14),
            "name_fr": "Nouvel An amazigh",
            "name_ar": "رأس السنة الأمازيغية",
            "name_en": "Amazigh New Year",
        },
        {
            "id": uuid.uuid4(),
            "code": "eid_al_fitr",
            "holiday_date": date(2028, 2, 26),
            "name_fr": "Aïd al-Fitr",
            "name_ar": "عيد الفطر",
            "name_en": "Eid al-Fitr",
        },
        {
            "id": uuid.uuid4(),
            "code": "labour_day",
            "holiday_date": date(2028, 5, 1),
            "name_fr": "Fête du Travail",
            "name_ar": "عيد العمال",
            "name_en": "Labour Day",
        },
        {
            "id": uuid.uuid4(),
            "code": "eid_al_adha",
            "holiday_date": date(2028, 5, 5),
            "name_fr": "Aïd al-Adha",
            "name_ar": "عيد الأضحى",
            "name_en": "Eid al-Adha",
        },
        {
            "id": uuid.uuid4(),
            "code": "throne_day",
            "holiday_date": date(2028, 7, 30),
            "name_fr": "Fête du Trône",
            "name_ar": "عيد العرش",
            "name_en": "Throne Day",
        },
        {
            "id": uuid.uuid4(),
            "code": "mawlid",
            "holiday_date": date(2028, 8, 3),
            "name_fr": "Mawlid",
            "name_ar": "المولد النبوي",
            "name_en": "Mawlid",
        },
        {
            "id": uuid.uuid4(),
            "code": "green_march",
            "holiday_date": date(2028, 11, 6),
            "name_fr": "Marche Verte",
            "name_ar": "المسيرة الخضراء",
            "name_en": "Green March",
        },
        {
            "id": uuid.uuid4(),
            "code": "independence_day",
            "holiday_date": date(2028, 11, 18),
            "name_fr": "Fête de l'Indépendance",
            "name_ar": "عيد الاستقلال",
            "name_en": "Independence Day",
        },
    ]


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("title_fr", sa.String(length=255), nullable=False),
        sa.Column("title_ar", sa.String(length=255), nullable=True),
        sa.Column("title_en", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("type", sa.String(length=30), nullable=False),
        sa.Column("visibility", sa.String(length=30), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("rsvp_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recurrence_rule", sa.JSON(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("class_id", sa.Uuid(), nullable=True),
        sa.Column("role_codes", sa.JSON(), nullable=True),
        sa.Column("is_all_day", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("end_at >= start_at", name="ck_events_end_after_start"),
        sa.CheckConstraint("capacity IS NULL OR capacity > 0", name="ck_events_capacity_positive"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_events_school_start", "events", ["school_id", "start_at"], unique=False)
    op.create_index(
        "idx_events_school_type_start",
        "events",
        ["school_id", "type", "start_at"],
        unique=False,
    )
    op.create_index(
        "idx_events_school_class_start",
        "events",
        ["school_id", "class_id", "start_at"],
        unique=False,
    )
    op.create_index(
        "idx_events_school_visibility_start",
        "events",
        ["school_id", "visibility", "start_at"],
        unique=False,
    )

    op.create_table(
        "event_rsvps",
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", "user_id", name="uq_event_rsvps_event_user"),
    )
    op.create_index(
        "idx_event_rsvps_event_status",
        "event_rsvps",
        ["event_id", "status"],
        unique=False,
    )
    op.create_index(
        "idx_event_rsvps_user_responded",
        "event_rsvps",
        ["user_id", "responded_at"],
        unique=False,
    )

    op.create_table(
        "event_reminders",
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("remind_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("sent", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("occurrence_start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "event_id",
            "remind_at",
            "channel",
            name="uq_event_reminders_event_remind_channel",
        ),
    )
    op.create_index(
        "idx_event_reminders_due_sent",
        "event_reminders",
        ["sent", "remind_at"],
        unique=False,
    )

    op.create_table(
        "event_reminder_preferences",
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=30), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "school_id",
            "user_id",
            "event_type",
            name="uq_event_reminder_prefs_school_user_type",
        ),
    )

    op.create_table(
        "moroccan_holidays",
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("holiday_date", sa.Date(), nullable=False),
        sa.Column("name_fr", sa.String(length=255), nullable=False),
        sa.Column("name_ar", sa.String(length=255), nullable=True),
        sa.Column("name_en", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_all_day", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", "holiday_date", name="uq_moroccan_holidays_code_date"),
    )
    op.create_index(
        "idx_moroccan_holidays_date",
        "moroccan_holidays",
        ["holiday_date"],
        unique=False,
    )

    holidays_table = sa.table(
        "moroccan_holidays",
        sa.column("id", sa.Uuid()),
        sa.column("code", sa.String()),
        sa.column("holiday_date", sa.Date()),
        sa.column("name_fr", sa.String()),
        sa.column("name_ar", sa.String()),
        sa.column("name_en", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("is_all_day", sa.Boolean()),
    )
    op.bulk_insert(
        holidays_table,
        [
            {
                **row,
                "description": None,
                "is_all_day": True,
            }
            for row in _holiday_rows()
        ],
    )

    op.alter_column("events", "is_all_day", server_default=None)
    op.alter_column("event_reminders", "sent", server_default=None)
    op.alter_column("event_reminder_preferences", "enabled", server_default=None)
    op.alter_column("moroccan_holidays", "is_all_day", server_default=None)


def downgrade() -> None:
    op.drop_index("idx_moroccan_holidays_date", table_name="moroccan_holidays")
    op.drop_table("moroccan_holidays")

    op.drop_table("event_reminder_preferences")

    op.drop_index("idx_event_reminders_due_sent", table_name="event_reminders")
    op.drop_table("event_reminders")

    op.drop_index("idx_event_rsvps_user_responded", table_name="event_rsvps")
    op.drop_index("idx_event_rsvps_event_status", table_name="event_rsvps")
    op.drop_table("event_rsvps")

    op.drop_index("idx_events_school_visibility_start", table_name="events")
    op.drop_index("idx_events_school_class_start", table_name="events")
    op.drop_index("idx_events_school_type_start", table_name="events")
    op.drop_index("idx_events_school_start", table_name="events")
    op.drop_table("events")
