"""G37b - add missing FK indexes for legacy tables.

Revision ID: 0d4e5f6a7b8c
Revises: 9c3d4e5f6a7b
Create Date: 2026-04-05
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0d4e5f6a7b8c"
down_revision: Union[str, None] = "9c3d4e5f6a7b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (index_name, table, column)
_INDEXES: list[tuple[str, str, str]] = [
    # erp.py
    ("idx_classes_academic_year_id", "classes", "academic_year_id"),
    ("idx_enrollments_class_id", "enrollments", "class_id"),
    ("idx_attendance_sessions_class_id", "attendance_sessions", "class_id"),
    ("idx_attendance_sessions_period_id", "attendance_sessions", "period_id"),
    ("idx_attendance_sessions_teacher_id", "attendance_sessions", "teacher_id"),
    ("idx_absence_justifications_attendance_record_id", "absence_justifications", "attendance_record_id"),
    ("idx_absence_justifications_parent_id", "absence_justifications", "parent_id"),
    ("idx_justification_reviews_justification_id", "justification_reviews", "justification_id"),
    ("idx_justification_reviews_reviewer_id", "justification_reviews", "reviewer_id"),
    ("idx_attendance_alerts_period_id", "attendance_alerts", "period_id"),
    ("idx_timetable_exceptions_timetable_slot_id", "timetable_exceptions", "timetable_slot_id"),
    ("idx_timetable_exceptions_substitute_teacher_id", "timetable_exceptions", "substitute_teacher_id"),
    # iam.py
    ("idx_sessions_user_id", "sessions", "user_id"),
    ("idx_invitation_codes_issuer_user_id", "invitation_codes", "issuer_user_id"),
    ("idx_invitation_codes_consumed_by", "invitation_codes", "consumed_by"),
    ("idx_invitation_codes_target_student_id", "invitation_codes", "target_student_id"),
    ("idx_account_recovery_requests_school_id", "account_recovery_requests", "school_id"),
    ("idx_parent_child_links_linked_by", "parent_child_links", "linked_by"),
    # lms.py
    ("idx_courses_teacher_id", "courses", "teacher_id"),
    ("idx_grade_categories_school_id", "grade_categories", "school_id"),
    ("idx_assignments_teacher_id", "assignments", "teacher_id"),
    ("idx_submission_files_submission_id", "submission_files", "submission_id"),
    ("idx_rubric_scores_criterion_id", "rubric_scores", "criterion_id"),
    ("idx_rubric_scores_level_id", "rubric_scores", "level_id"),
    ("idx_grades_submission_id", "grades", "submission_id"),
    ("idx_grades_teacher_id", "grades", "teacher_id"),
    ("idx_student_period_averages_student_id", "student_period_averages", "student_id"),
    ("idx_student_period_averages_school_id", "student_period_averages", "school_id"),
    ("idx_assessments_teacher_id", "assessments", "teacher_id"),
    ("idx_assessment_results_student_id", "assessment_results", "student_id"),
    ("idx_content_items_original_content_id", "content_items", "original_content_id"),
    ("idx_content_items_school_id", "content_items", "school_id"),
    ("idx_content_item_assets_content_item_id", "content_item_assets", "content_item_id"),
    ("idx_class_content_assignments_content_item_id", "class_content_assignments", "content_item_id"),
    ("idx_content_submissions_content_item_id", "content_submissions", "content_item_id"),
    ("idx_content_submissions_reviewed_by", "content_submissions", "reviewed_by"),
    ("idx_content_submissions_promoted_content_id", "content_submissions", "promoted_content_id"),
    ("idx_quiz_responses_question_id", "quiz_responses", "question_id"),
    # billing.py
    ("idx_invoices_fee_structure_id", "invoices", "fee_structure_id"),
    ("idx_invoice_items_invoice_id", "invoice_items", "invoice_id"),
    ("idx_payment_attempts_parent_id", "payment_attempts", "parent_id"),
    ("idx_payment_attempts_school_id", "payment_attempts", "school_id"),
    ("idx_payment_proofs_payment_attempt_id", "payment_proofs", "payment_attempt_id"),
    ("idx_provider_webhook_events_payment_attempt_id", "provider_webhook_events", "payment_attempt_id"),
    ("idx_fee_assignments_fee_structure_id", "fee_assignments", "fee_structure_id"),
    # com.py
    ("idx_parent_feed_items_student_id", "parent_feed_items", "student_id"),
    # documents.py
    ("idx_documents_uploader_id", "documents", "uploader_id"),
    ("idx_document_versions_uploader_id", "document_versions", "uploader_id"),
    ("idx_resources_uploader_id", "resources", "uploader_id"),
    ("idx_resources_file_id", "resources", "file_id"),
]


def upgrade() -> None:
    for index_name, table, column in _INDEXES:
        op.create_index(index_name, table, [column], unique=False)


def downgrade() -> None:
    for index_name, table, _column in reversed(_INDEXES):
        op.drop_index(index_name, table_name=table)
