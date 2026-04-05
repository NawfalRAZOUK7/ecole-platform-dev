"""g39 add remaining FK indexes.

Revision ID: c9d5e3f7a1b4
Revises: b544b2132f31
Create Date: 2026-04-05
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c9d5e3f7a1b4"
down_revision: Union[str, None] = "b544b2132f31"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_INDEXES: list[tuple[str, str, str]] = [
    ("ix_absence_justifications_school_id", "absence_justifications", "school_id"),
    ("idx_activity_sessions_activity_id", "activity_sessions", "activity_id"),
    ("idx_attendance_records_student_id", "attendance_records", "student_id"),
    ("ix_attendance_sessions_school_id", "attendance_sessions", "school_id"),
    ("ix_classes_school_id", "classes", "school_id"),
    ("idx_content_progress_content_item_id", "content_progress", "content_item_id"),
    ("idx_courses_class_id", "courses", "class_id"),
    ("idx_device_tokens_user_id", "device_tokens", "user_id"),
    ("idx_enrollments_period_id", "enrollments", "period_id"),
    ("idx_enrollments_student_id", "enrollments", "student_id"),
    (
        "idx_event_reminder_preferences_user_id",
        "event_reminder_preferences",
        "user_id",
    ),
    ("idx_events_class_id", "events", "class_id"),
    ("idx_events_created_by", "events", "created_by"),
    ("idx_fee_structures_academic_year_id", "fee_structures", "academic_year_id"),
    ("idx_grade_categories_period_id", "grade_categories", "period_id"),
    ("idx_invoices_period_id", "invoices", "period_id"),
    ("ix_justification_reviews_school_id", "justification_reviews", "school_id"),
    ("ix_memberships_school_id", "memberships", "school_id"),
    (
        "idx_notification_deliveries_notification_id",
        "notification_deliveries",
        "notification_id",
    ),
    ("idx_notifications_parent_id", "notifications", "parent_id"),
    ("ix_parent_child_links_school_id", "parent_child_links", "school_id"),
    ("idx_parent_feed_items_parent_id", "parent_feed_items", "parent_id"),
    ("idx_periods_academic_year_id", "periods", "academic_year_id"),
    ("idx_report_jobs_requester_id", "report_jobs", "requester_id"),
    ("idx_report_schedules_created_by", "report_schedules", "created_by"),
    ("idx_rubrics_teacher_id", "rubrics", "teacher_id"),
    (
        "idx_student_period_averages_period_id",
        "student_period_averages",
        "period_id",
    ),
    ("idx_submissions_student_id", "submissions", "student_id"),
    ("idx_teacher_assignments_class_id", "teacher_assignments", "class_id"),
    ("idx_teacher_assignments_period_id", "teacher_assignments", "period_id"),
    ("idx_teacher_assignments_teacher_id", "teacher_assignments", "teacher_id"),
    (
        "idx_timetable_constraints_academic_year_id",
        "timetable_constraints",
        "academic_year_id",
    ),
    (
        "idx_timetable_generation_jobs_academic_year_id",
        "timetable_generation_jobs",
        "academic_year_id",
    ),
    ("idx_timetable_slots_academic_year_id", "timetable_slots", "academic_year_id"),
]


def upgrade() -> None:
    for index_name, table_name, column_name in _INDEXES:
        op.execute(
            f'CREATE INDEX IF NOT EXISTS "{index_name}" '
            f'ON "{table_name}" ("{column_name}")'
        )


def downgrade() -> None:
    for index_name, _table_name, _column_name in reversed(_INDEXES):
        op.execute(f'DROP INDEX IF EXISTS "{index_name}"')
