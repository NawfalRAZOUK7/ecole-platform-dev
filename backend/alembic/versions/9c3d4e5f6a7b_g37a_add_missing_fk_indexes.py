"""G37a - add missing FK indexes for innovation feature tables.

Revision ID: 9c3d4e5f6a7b
Revises: 8b2c3d4e5f6a
Create Date: 2026-04-05
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9c3d4e5f6a7b"
down_revision: Union[str, None] = "8b2c3d4e5f6a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (index_name, table, column)
_INDEXES: list[tuple[str, str, str]] = [
    # micro_school
    ("idx_micro_groups_micro_school_id", "micro_groups", "micro_school_id"),
    ("idx_micro_payments_micro_school_id", "micro_payments", "micro_school_id"),
    ("idx_micro_payments_parent_id", "micro_payments", "parent_id"),
    ("idx_micro_payments_child_enrollment_id", "micro_payments", "child_enrollment_id"),
    ("idx_micro_progress_logs_micro_enrollment_id", "micro_progress_logs", "micro_enrollment_id"),
    ("idx_micro_progress_logs_educator_id", "micro_progress_logs", "educator_id"),
    # sync_queue
    ("idx_sync_queue_device_id", "sync_queue", "device_id"),
    ("idx_sync_conflicts_queue_item_id", "sync_conflicts", "queue_item_id"),
    ("idx_sync_conflicts_resolved_by", "sync_conflicts", "resolved_by"),
    ("idx_sync_checkpoints_device_id", "sync_checkpoints", "device_id"),
    # budget
    ("idx_micro_budgets_academic_year_id", "micro_budgets", "academic_year_id"),
    ("idx_budget_allocations_budget_id", "budget_allocations", "budget_id"),
    ("idx_budget_allocations_class_id", "budget_allocations", "class_id"),
    ("idx_budget_allocations_teacher_id", "budget_allocations", "teacher_id"),
    ("idx_budget_allocations_allocated_by", "budget_allocations", "allocated_by"),
    ("idx_budget_requests_reviewed_by", "budget_requests", "reviewed_by"),
    ("idx_budget_transactions_allocation_id", "budget_transactions", "allocation_id"),
    ("idx_budget_transactions_request_id", "budget_transactions", "request_id"),
    ("idx_budget_transactions_recorded_by", "budget_transactions", "recorded_by"),
    # financial_health
    ("idx_cost_per_student_academic_year_id", "cost_per_student", "academic_year_id"),
    # men_compliance
    ("idx_men_objectives_curriculum_id", "men_objectives", "curriculum_id"),
    ("idx_curriculum_mappings_objective_id", "curriculum_mappings", "objective_id"),
    ("idx_curriculum_mappings_course_id", "curriculum_mappings", "course_id"),
    ("idx_curriculum_mappings_content_item_id", "curriculum_mappings", "content_item_id"),
    ("idx_curriculum_mappings_mapped_by", "curriculum_mappings", "mapped_by"),
    ("idx_compliance_reports_curriculum_id", "compliance_reports", "curriculum_id"),
    ("idx_compliance_reports_generated_by_fk", "compliance_reports", "generated_by"),
    ("idx_compliance_reports_academic_year_id", "compliance_reports", "academic_year_id"),
    # skill_passport
    ("idx_skill_milestones_dimension_id", "skill_milestones", "dimension_id"),
    ("idx_skill_progress_student_id", "skill_progress", "student_id"),
    ("idx_skill_progress_milestone_id", "skill_progress", "milestone_id"),
    ("idx_skill_progress_academic_year_id", "skill_progress", "academic_year_id"),
    ("idx_skill_passports_student_id", "skill_passports", "student_id"),
    ("idx_skill_passports_academic_year_id", "skill_passports", "academic_year_id"),
]


def upgrade() -> None:
    for index_name, table, column in _INDEXES:
        op.create_index(index_name, table, [column], unique=False)


def downgrade() -> None:
    for index_name, table, _column in reversed(_INDEXES):
        op.drop_index(index_name, table_name=table)
