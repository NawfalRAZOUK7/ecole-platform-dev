"""G31b — convert string-backed status/type columns to PostgreSQL enums.

Revision ID: 1c42d3e4f5a6
Revises: 0a31b2c3d4e5
Create Date: 2026-03-29
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "1c42d3e4f5a6"
down_revision: Union[str, None] = "0a31b2c3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

USER_STATUS_ENUM = postgresql.ENUM(
    "active",
    "inactive",
    "suspended",
    name="user_status_enum",
)
MEMBERSHIP_STATUS_ENUM = postgresql.ENUM(
    "active",
    "inactive",
    name="membership_status_enum",
)
ROLE_CODE_ENUM = postgresql.ENUM(
    "ADM",
    "DIR",
    "TCH",
    "PAR",
    "STD",
    "SUP",
    "SYS",
    "CONTENT_MGR",
    name="role_code_enum",
)
RECOVERY_STATUS_ENUM = postgresql.ENUM(
    "pending",
    "verified",
    "reset",
    name="recovery_status_enum",
)
INVOICE_STATUS_ENUM = postgresql.ENUM(
    "pending",
    "paid",
    "failed",
    "canceled",
    name="invoice_status_enum",
)
PAYMENT_STATUS_ENUM = postgresql.ENUM(
    "pending",
    "processing",
    "paid",
    "failed",
    "canceled",
    name="payment_status_enum",
)
ENROLLMENT_STATUS_ENUM = postgresql.ENUM(
    "active",
    "transferred",
    "dropped",
    name="enrollment_status_enum",
)
ATTENDANCE_STATUS_ENUM = postgresql.ENUM(
    "present",
    "absent",
    "excused",
    "late",
    name="attendance_status_enum",
)
NOTIFICATION_CATEGORY_ENUM = postgresql.ENUM(
    "academic",
    "billing",
    "attendance",
    "system",
    "announcement",
    name="notification_category_enum",
)
NOTIFICATION_PRIORITY_ENUM = postgresql.ENUM(
    "low",
    "normal",
    "high",
    "critical",
    name="notification_priority_enum",
)
DELIVERY_CHANNEL_ENUM = postgresql.ENUM(
    "in_app",
    "email",
    "sms",
    "push",
    name="delivery_channel_enum",
)
DELIVERY_STATUS_ENUM = postgresql.ENUM(
    "queued",
    "sent",
    "delivered",
    "failed",
    "clicked",
    "opened",
    "bounced",
    "fallback",
    "suppressed",
    name="delivery_status_enum",
)
CONSENT_STATUS_ENUM = postgresql.ENUM(
    "opted_in",
    "opted_out",
    name="consent_status_enum",
)
DEVICE_PLATFORM_ENUM = postgresql.ENUM(
    "android",
    "ios",
    "web",
    name="device_platform_enum",
)
CONVERSATION_TYPE_ENUM = postgresql.ENUM(
    "DIRECT",
    "GROUP",
    name="conversation_type_enum",
)
PARTICIPANT_ROLE_ENUM = postgresql.ENUM(
    "INITIATOR",
    "PARTICIPANT",
    name="participant_role_enum",
)
ANNOUNCEMENT_STATUS_ENUM = postgresql.ENUM(
    "DRAFT",
    "PUBLISHED",
    "ARCHIVED",
    name="announcement_status_enum",
)
REPORT_JOB_STATUS_ENUM = postgresql.ENUM(
    "pending",
    "generating",
    "ready",
    "failed",
    name="report_job_status_enum",
)
REPORT_TYPE_ENUM = postgresql.ENUM(
    "student_report_card",
    "class_summary",
    "attendance_report",
    "billing_statement",
    "school_analytics",
    name="report_type_enum",
)
DATA_EXPORT_FORMAT_ENUM = postgresql.ENUM(
    "csv",
    "xlsx",
    name="data_export_format_enum",
)
DOCUMENT_CATEGORY_ENUM = postgresql.ENUM(
    "certificate",
    "report_card",
    "medical",
    "identity",
    "transcript",
    "other",
    name="document_category_enum",
)
RESOURCE_TYPE_ENUM = postgresql.ENUM(
    "lesson_plan",
    "worksheet",
    "presentation",
    "exam_template",
    "reference",
    name="resource_type_enum",
)
RESOURCE_VISIBILITY_ENUM = postgresql.ENUM(
    "school",
    "class",
    name="resource_visibility_enum",
)
ASSIGNMENT_TYPE_ENUM = postgresql.ENUM(
    "STANDARD",
    "PRINTABLE_PDF",
    "QUIZ",
    name="assignment_type_enum",
)
SUBMISSION_STATUS_ENUM = postgresql.ENUM(
    "draft",
    "submitted",
    "graded",
    "returned",
    name="submission_status_enum",
)
QUIZ_ATTEMPT_STATUS_ENUM = postgresql.ENUM(
    "STARTED",
    "COMPLETED",
    "TIMED_OUT",
    name="quiz_attempt_status_enum",
)
TIMETABLE_JOB_STATUS_ENUM = postgresql.ENUM(
    "pending",
    "running",
    "completed",
    "failed",
    "applied",
    name="timetable_job_status_enum",
)

ENUM_TYPES = [
    USER_STATUS_ENUM,
    MEMBERSHIP_STATUS_ENUM,
    ROLE_CODE_ENUM,
    RECOVERY_STATUS_ENUM,
    INVOICE_STATUS_ENUM,
    PAYMENT_STATUS_ENUM,
    ENROLLMENT_STATUS_ENUM,
    ATTENDANCE_STATUS_ENUM,
    NOTIFICATION_CATEGORY_ENUM,
    NOTIFICATION_PRIORITY_ENUM,
    DELIVERY_CHANNEL_ENUM,
    DELIVERY_STATUS_ENUM,
    CONSENT_STATUS_ENUM,
    DEVICE_PLATFORM_ENUM,
    CONVERSATION_TYPE_ENUM,
    PARTICIPANT_ROLE_ENUM,
    ANNOUNCEMENT_STATUS_ENUM,
    REPORT_JOB_STATUS_ENUM,
    REPORT_TYPE_ENUM,
    DATA_EXPORT_FORMAT_ENUM,
    DOCUMENT_CATEGORY_ENUM,
    RESOURCE_TYPE_ENUM,
    RESOURCE_VISIBILITY_ENUM,
    ASSIGNMENT_TYPE_ENUM,
    SUBMISSION_STATUS_ENUM,
    QUIZ_ATTEMPT_STATUS_ENUM,
    TIMETABLE_JOB_STATUS_ENUM,
]

COLUMN_CONVERSIONS: list[tuple[str, str, postgresql.ENUM, int]] = [
    ("users", "status", USER_STATUS_ENUM, 20),
    ("memberships", "status", MEMBERSHIP_STATUS_ENUM, 20),
    ("memberships", "role_code", ROLE_CODE_ENUM, 20),
    ("account_recovery_requests", "status", RECOVERY_STATUS_ENUM, 20),
    ("invoices", "status", INVOICE_STATUS_ENUM, 20),
    ("payment_attempts", "status", PAYMENT_STATUS_ENUM, 20),
    ("enrollments", "status", ENROLLMENT_STATUS_ENUM, 20),
    ("attendance_records", "status", ATTENDANCE_STATUS_ENUM, 20),
    ("notifications", "category", NOTIFICATION_CATEGORY_ENUM, 30),
    ("notifications", "priority", NOTIFICATION_PRIORITY_ENUM, 20),
    ("notification_deliveries", "channel", DELIVERY_CHANNEL_ENUM, 20),
    ("notification_deliveries", "status", DELIVERY_STATUS_ENUM, 20),
    ("consent_preferences", "status", CONSENT_STATUS_ENUM, 20),
    ("consent_preferences", "channel", DELIVERY_CHANNEL_ENUM, 20),
    ("device_tokens", "platform", DEVICE_PLATFORM_ENUM, 20),
    ("conversations", "type", CONVERSATION_TYPE_ENUM, 20),
    (
        "conversation_participants",
        "role_in_conversation",
        PARTICIPANT_ROLE_ENUM,
        20,
    ),
    ("announcements", "status", ANNOUNCEMENT_STATUS_ENUM, 20),
    ("report_jobs", "status", REPORT_JOB_STATUS_ENUM, 20),
    ("report_jobs", "type", REPORT_TYPE_ENUM, 50),
    ("report_schedules", "report_type", REPORT_TYPE_ENUM, 50),
    ("data_exports", "format", DATA_EXPORT_FORMAT_ENUM, 10),
    ("documents", "category", DOCUMENT_CATEGORY_ENUM, 40),
    ("resources", "type", RESOURCE_TYPE_ENUM, 40),
    ("resources", "visibility", RESOURCE_VISIBILITY_ENUM, 20),
    ("assignments", "exercise_type", ASSIGNMENT_TYPE_ENUM, 20),
    ("submissions", "status", SUBMISSION_STATUS_ENUM, 20),
    ("quiz_attempts", "status", QUIZ_ATTEMPT_STATUS_ENUM, 20),
    ("timetable_generation_jobs", "status", TIMETABLE_JOB_STATUS_ENUM, 20),
]


def upgrade() -> None:
    bind = op.get_bind()

    for enum_type in ENUM_TYPES:
        enum_type.create(bind, checkfirst=False)

    for table_name, column_name, enum_type, length in COLUMN_CONVERSIONS:
        op.alter_column(
            table_name,
            column_name,
            existing_type=sa.String(length=length),
            type_=enum_type,
            postgresql_using=f"{column_name}::text::{enum_type.name}",
        )


def downgrade() -> None:
    for table_name, column_name, enum_type, length in reversed(COLUMN_CONVERSIONS):
        op.alter_column(
            table_name,
            column_name,
            existing_type=enum_type,
            type_=sa.String(length=length),
            postgresql_using=f"{column_name}::text",
        )

    bind = op.get_bind()
    for enum_type in reversed(ENUM_TYPES):
        enum_type.drop(bind, checkfirst=False)
