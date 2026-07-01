# Part 3 Model & Role Notes

This document summarizes the completed Part 3 model and role enhancement work for the Ecole Platform backend.

It covers:
- what was implemented across model/role prompts `MR-A1` through `MR-F1`;
- the main model, core, repository, service, router, and migration changes;
- implementation decisions that were taken during execution but were not stated clearly in the prompts or checklist;
- validation outcomes and environment notes that matter before any later prompts or review.

## Status

Part 3 is complete through:
- `MR-A1` School model + school/soft-delete mixins
- `MR-B1` helper properties
- `MR-B2` model `__repr__`
- `MR-B3` validators
- `MR-C1` PostgreSQL enum columns
- `MR-D1` permission expansion + role hierarchy
- `MR-E1` ABAC validation
- `MR-E2` hardcoded role removal
- `MR-F1` full validation

## What Was Implemented

### 1. School Model + Shared Mixins (`MR-A1`)

Implemented:
- `backend/app/models/school.py`
- `backend/app/repositories/school.py`
- `backend/app/services/school.py`
- `backend/app/schemas/school.py`
- `backend/app/api/v1/schools.py`
- router registration in `backend/app/api/v1/router.py`
- `G31a` migration in `backend/alembic/versions/0a31b2c3d4e5_g31a_school_model_mixins.py`

Core mixin work:
- added `SchoolScopedMixin` in `backend/app/core/database.py`
- added `NullableSchoolScopedMixin` in `backend/app/core/database.py`
- added `SoftDeleteMixin` in `backend/app/core/database.py`
- replaced per-model `school_id` declarations across the model layer with mixin inheritance
- removed duplicated `deleted_at` declarations from soft-deleted models

Validation outcome:
- no remaining manual `school_id` declarations
- no remaining manual `deleted_at` declarations
- school CRUD stack and `/schools` routes resolve correctly

### 2. Helper Properties (`MR-B1`)

Added or finalized pure helper properties on live models, including:
- `User.is_active`
- `User.has_2fa`
- `User.is_email_verified`
- `Session.is_expired`
- `Session.is_impersonated`
- `Session.is_revoked`
- `Invoice.is_overdue`
- `Invoice.is_paid`
- `Assignment.is_past_due`
- `Submission.is_graded`
- `ReportJob.is_complete`
- `ReportJob.is_expired`

This work was applied in the actual model modules:
- `backend/app/models/iam.py`
- `backend/app/models/billing.py`
- `backend/app/models/lms.py`
- `backend/app/models/erp.py`
- `backend/app/models/com.py`
- `backend/app/models/reporting.py`
- `backend/app/models/documents.py`
- `backend/app/models/calendar.py`

### 3. Model `__repr__` Standardization (`MR-B2`)

Standardized model `__repr__` coverage across the mapped model layer:
- added `_short_id()` helpers where needed
- ensured mapped models expose a short, review-friendly identifier
- kept sensitive fields out of string representations

This affected model modules including:
- `backend/app/models/iam.py`
- `backend/app/models/lms.py`
- `backend/app/models/erp.py`
- `backend/app/models/billing.py`
- `backend/app/models/com.py`
- `backend/app/models/documents.py`
- `backend/app/models/calendar.py`
- `backend/app/models/reporting.py`
- `backend/app/models/audit.py`

### 4. Validation Rules and Normalization (`MR-B3`)

Added or aligned validators and normalization logic for real schema fields, including:
- email normalization and validation
- grade score bounds
- invoice total non-negative validation
- currency normalization
- phone normalization
- selected status validators on live enum-backed fields

This work landed in:
- `backend/app/models/iam.py`
- `backend/app/models/billing.py`
- `backend/app/models/lms.py`
- `backend/app/models/erp.py`
- `backend/app/models/documents.py`
- `backend/app/models/reporting.py`

### 5. PostgreSQL Enum Migration (`MR-C1`)

Converted string status/type columns to explicit PostgreSQL enum-backed columns.

Implemented:
- enum-backed model updates in:
  - `backend/app/models/iam.py`
  - `backend/app/models/billing.py`
  - `backend/app/models/lms.py`
  - `backend/app/models/erp.py`
  - `backend/app/models/com.py`
  - `backend/app/models/documents.py`
  - `backend/app/models/reporting.py`
- `G31b` migration in `backend/alembic/versions/1c42d3e4f5a6_g31b_pg_enum_columns.py`

Validation outcome:
- enum migration compiles
- `PgEnum(..., create_type=False)` usage is in place
- repository-wide incompatible string-literal audit was clean

### 6. Permission Expansion + Role Hierarchy (`MR-D1`)

Updated `backend/app/core/permissions.py` to support:
- expanded billing authority for `DIR`
- explicit platform-role handling for `SUP`, `SYS`, and `CONTENT_MGR`
- `PLATFORM_ROLES`
- `ROLE_HIERARCHY`
- `get_effective_permissions()`
- inherited permission checks via `role_has_permission()`

Validation outcome:
- `DIR` inherits `TCH`
- `ADM` inherits `DIR + TCH`
- `SUP` inherits the admin chain
- duplicate direct grants that became redundant under inheritance were removed

### 7. ABAC + Relationship-Based Access (`MR-E1`)

Implemented or finalized:
- `backend/app/core/abac.py`
- `apply_owner_scope()`
- `validate_parent_child_access()`
- `validate_teacher_class_access()`
- `validate_student_teacher_access()`
- `requires_any_permission()` in `backend/app/core/dependencies.py`

Integrated ABAC into live consumers including:
- messaging access control
- parent billing visibility
- student-teacher direct conversation checks

Validation outcome:
- parent access checks use live parent-child relationships
- student messaging is limited to direct conversations
- student-teacher checks enforce shared-class relationship

### 8. Hardcoded Role Removal (`MR-E2`)

Removed remaining quoted role checks and quoted role literals from:
- `backend/app/services/`
- `backend/app/api/v1/`

This was done by normalizing logic to:
- permission helpers
- role constants
- existing ABAC validators

The goal was cleanup without broadening access semantics.

### 9. Final Validation (`MR-F1`)

Completed full validation for:
- school mixins
- soft delete mixin
- helper properties
- model `__repr__`
- validators
- enum columns
- school CRUD/router stack
- permission expansion
- role hierarchy
- ABAC
- hardcoded role cleanup
- import health

Final outcome:
- all MR-F1 checks passed
- no additional backend code changes were needed during the final validation prompt itself

## Decisions Taken During Implementation

These are the main execution decisions that were not clearly spelled out in the prompts or checklist.

### 1. `NullableSchoolScopedMixin` was introduced for platform-wide content models

The prompt focused on `SchoolScopedMixin`, but the live codebase includes content-like records that intentionally allow `school_id = NULL`.

To avoid breaking platform-level content manager behavior, `NullableSchoolScopedMixin` was added and used for:
- `ContentItem`
- `Activity`
- `Quiz`

Without this, the MR-A1 mixin rollout would have forced content that is meant to remain platform-wide into school-only storage.

### 2. `PERM_ADM_SCHOOL_MANAGE` was assigned to both `ADM` and `SUP`

The architecture language and route expectations implied both roles needed real school-management authority.

This was applied so `PATCH /schools/{id}` remains valid for both `ADM` and `SUP`, instead of narrowing management to one platform role only.

### 3. Helper-property behavior followed the live schema where the prompt drifted

Several prompt examples referenced fields that do not exist in the current models. The implementation used the real schema instead of inventing columns.

Examples:
- `Invoice.is_overdue` uses the real pending-state logic, not a nonexistent `"sent"` state
- `Assignment.is_past_due` uses `due_at`
- `Submission.is_graded` uses submission status because there is no `graded_at`
- `Quiz.is_active` maps to `status == "published"` and respects optional future scheduling fields if added later
- `InvitationCode.is_fully_used` falls back to the existing one-time-use model because there are no usage counters
- `Session.is_expired` returns `False` unless an `expires_at` field is actually present
- `AttendanceAlert.is_resolved` returns `False` unless a `resolved_at` field exists

### 4. `Event.is_all_day` did not need to be added

The prompt implied additional event helpers were needed, but `Event.is_all_day` already existed as a mapped boolean.

Only the missing helper behavior, such as `Event.is_past`, was added where necessary.

### 5. `__repr__` work used real model fields and intentionally avoided secrets

The prompt required every model to have a concise `__repr__`, but some prompt examples referenced fields that do not exist in the live schema.

The implementation therefore used real fields such as:
- `Course.title` instead of nonexistent `name`
- `Assignment.exercise_type` instead of generic `type`
- derived `Quiz` publish state from `status`

Sensitive values were intentionally excluded:
- no raw tokens
- no hashes
- no passwords
- no large content payloads
- no secret JSON blobs

### 6. Validator work mapped to actual column names, not prompt placeholders

Examples:
- `Invoice.total` in the prompt maps to live `total_amount`
- `Assignment.max_score` in the prompt maps to live `total_points`
- `SiblingDiscountPolicy.discount_percent` in the prompt maps to the real tiered percentage fields

I also added validators for live status fields like `Enrollment.status` and `ReportJob.status` while working through the MR-B3 scope.

### 7. Enum migration preserved live value sets instead of prompt examples

The enum conversion was based on the current production-oriented schema, not on drifted names from the prompt examples.

Important examples:
- `PaymentAttempt.status` uses the existing live values
- `Assignment` converts the real `exercise_type` column through `assignment_type_enum`
- `PaymentAttempt.method` was not migrated because that column does not exist
- `TimetableJobStatus` was added as a real enum for timetable generation jobs
- compatibility aliases were added for prompt-oriented names like `AssignmentType` and `PaymentStatus`

### 8. Role hierarchy cleanup removed redundant direct grants

After inheritance was introduced, some role-permission entries were redundant and would have made the hierarchy harder to reason about.

Those duplicates were removed intentionally.

Examples noted during implementation:
- `ADM` direct entries like dashboard/report-export grants that were already inherited
- `SUP` direct entries that were already available through the inherited admin chain

### 9. ABAC uses the live relationship schema, not a legacy `verified=True` pattern

Parent-child validation uses:
- `ParentChildLink.parent_user_id`
- `ParentChildLink.child_user_id`
- `status == "active"`

This matches the live codebase. The prompt’s example fields did not.

### 10. Some modules were audited and intentionally left unchanged

During MR-E1, I reviewed:
- LMS access paths
- ERP access paths
- report access paths
- student document access paths
- progress access paths

Where the live logic already enforced appropriate ownership or relationship constraints, I left those modules unchanged rather than forcing redundant edits.

### 11. Hardcoded-role cleanup preserved behavior instead of rewriting everything into broader permission checks

For MR-E2, the goal was not to redesign authorization from scratch.

Where a branch already had the right semantic shape:
- permission-based branches stayed permission-based
- scope checks were normalized to constants
- ABAC checks stayed relationship-based

This avoided accidental privilege broadening under the new hierarchy.

### 12. MR-F1 validation had two important interpretation rules

First:
- enum classes themselves are not “models” for `__repr__` validation
- only mapped SQLAlchemy models were counted

Second:
- the school-scoped index check was interpreted as “existing school-aware composite indexes remain correct”
- not “every composite index on every school-scoped table must include `school_id`”

That distinction matters because several valid cross-entity or workflow indexes do not need `school_id` in their key.

### 13. The `DeviceToken` `__repr__` concern was a false positive during validation

The validation heuristic initially flagged `DeviceToken` only because the class name contains the word `token`.

Manual inspection confirmed the actual `__repr__` does not expose the device token value.

## Validation and Environment Notes

Use the backend virtual environment for verification:

```bash
cd backend && .venv/bin/python ...
```

Key verification outcomes during Part 3:
- `py_compile` passed across the backend app
- model/core import health passed in the backend venv
- role hierarchy runtime checks passed
- hardcoded quoted-role scans in `services/` and `api/v1/` returned clean
- MR-F1 completed with all checks passing

Known environment caveats observed during Part 3:
- router import smoke checks can emit non-blocking `fontconfig` cache warnings in this workspace
- direct live Postgres distinct-value verification for enum migration could not be completed locally because the configured `ecole` DB credentials failed in this environment

That DB credential issue did not block the Python-level enum migration and metadata validation.

## Files and Areas Most Affected

Primary core files:
- `backend/app/core/database.py`
- `backend/app/core/permissions.py`
- `backend/app/core/abac.py`
- `backend/app/core/dependencies.py`

Primary model files:
- `backend/app/models/school.py`
- `backend/app/models/iam.py`
- `backend/app/models/lms.py`
- `backend/app/models/erp.py`
- `backend/app/models/billing.py`
- `backend/app/models/com.py`
- `backend/app/models/documents.py`
- `backend/app/models/calendar.py`
- `backend/app/models/reporting.py`
- `backend/app/models/audit.py`
- `backend/app/models/ai.py`
- `backend/app/models/feature.py`

Primary CRUD stack additions:
- `backend/app/repositories/school.py`
- `backend/app/services/school.py`
- `backend/app/schemas/school.py`
- `backend/app/api/v1/schools.py`

Primary migrations:
- `backend/alembic/versions/0a31b2c3d4e5_g31a_school_model_mixins.py`
- `backend/alembic/versions/1c42d3e4f5a6_g31b_pg_enum_columns.py`

## Final State

Part 3 is complete.

The checklist and progress summary now reflect:
- `MR-A1` complete
- `MR-B1/B2/B3` complete
- `MR-C1` complete
- `MR-D1` complete
- `MR-E1/E2` complete
- `MR-F1` complete

At the end of Part 3, all 30 prompts across Parts 1, 2, and 3 are complete.
