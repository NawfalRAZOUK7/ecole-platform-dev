# Part 2 Enhancement Notes

This document summarizes the completed Part 2 enhancement work for the Ecole Platform backend.

It covers:
- what was implemented across enhancement prompts `ENH-A1` through `ENH-E1`;
- the main model, service, router, migration, and worker changes;
- implementation decisions that were taken during execution but were not stated clearly in the prompts or checklist;
- the final validation result and the remaining known drift.

## Status

Part 2 is complete through:
- `ENH-A1` IAM: impersonation, login history, session limits
- `ENH-B1` LMS rubric models + `G28a`
- `ENH-B2` LMS rubric service + router
- `ENH-B3` LMS weighted gradebook + GPA
- `ENH-B4` LMS question bank + late penalties
- `ENH-C1` Billing sibling discounts + late fees + payment plans
- `ENH-C2` ERP attendance analytics + alerts
- `ENH-C3` ERP timetable auto-generation
- `ENH-D1` Comms/Docs attachments + search + versioning
- `ENH-D2` Reports scheduling + AI provider abstraction
- `ENH-E1` enhancement validation

## What Was Implemented

### 1. IAM Enhancements (`ENH-A1`)

Implemented:
- `LoginHistory` model in [iam.py](/Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev/backend/app/models/iam.py)
- `impersonator_id` on `Session`
- `backend/app/repositories/login_history.py`
- `G27a` migration for IAM enhancements
- login history recording in `AuthService`
- concurrent session limiting using `settings.max_sessions_per_user`
- impersonation start/stop flows in auth/admin APIs
- `NewDeviceLogin` domain event and dispatcher wiring

Added endpoints:
- `GET /auth/login-history`
- `POST /admin/impersonate/{user_id}`
- `POST /admin/stop-impersonation`
- `GET /admin/users/{user_id}/login-history`

### 2. LMS Rubric Engine (`ENH-B1`, `ENH-B2`)

Implemented models:
- `Rubric`
- `RubricCriterion`
- `RubricLevel`
- `RubricScore`
- `Assignment.rubric_id`

Implemented:
- `backend/app/repositories/rubric.py`
- `backend/app/services/rubric.py`
- `backend/app/api/v1/rubrics.py`
- rubric grading endpoints for submissions
- `G28a` migration

Added routes:
- `POST /rubrics`
- `GET /rubrics`
- `GET /rubrics/{rubric_id}`
- `POST /rubrics/{rubric_id}/duplicate`
- `POST /submissions/{submission_id}/grade-rubric`
- `GET /submissions/{submission_id}/rubric-results`

### 3. Weighted Gradebook (`ENH-B3`)

Implemented models:
- `GradeCategory`
- `StudentPeriodAverage`
- `Assignment.grade_category_id`

Implemented:
- `backend/app/repositories/gradebook.py`
- `backend/app/services/gradebook.py`
- `backend/app/api/v1/gradebook.py`
- weighted category aggregation and GPA/transcript support
- `G28b` migration

Added routes:
- `GET /gradebook/categories/{class_id}/{period_id}`
- `POST /gradebook/categories`
- `POST /gradebook/compute/{class_id}/{period_id}`
- `GET /gradebook/{class_id}/{period_id}`
- `GET /gradebook/transcript/{student_id}`

### 4. Question Bank + Late Penalties (`ENH-B4`)

Implemented:
- `QuestionBankItem` model
- `Assignment` late-policy fields:
  - `grace_period_hours`
  - `late_penalty_per_day`
  - `max_late_days`
  - `allow_late`
- `Grade` late-penalty fields:
  - `original_score`
  - `late_penalty`
  - `late_days`
  - `penalty_overridden`

Implemented:
- `backend/app/repositories/question_bank.py`
- `backend/app/services/question_bank.py`
- question bank quiz generation/import routes
- late-penalty calculation helpers in LMS shared helpers
- late-penalty override endpoint
- `G28c` and `G28d` migrations

Added routes:
- `GET /question-bank`
- `POST /question-bank`
- `POST /question-bank/generate-quiz`
- `POST /question-bank/import/{quiz_id}`
- `GET /question-bank/stats`
- `POST /submissions/{submission_id}/override-penalty`

### 5. Billing Enhancements (`ENH-C1`)

Implemented models:
- `SiblingDiscountPolicy`
- `LateFeePolicy`
- `PaymentPlan`
- `Installment`

Implemented:
- `backend/app/repositories/billing_enhancements.py`
- payment plan service
- sibling discount logic in invoice generation
- late fee application logic
- `G27b` migration

Added routes:
- `GET /billing/sibling-policy`
- `PUT /billing/sibling-policy`
- `GET /billing/late-fee-policy`
- `PUT /billing/late-fee-policy`
- `POST /billing/payment-plans`
- `GET /billing/payment-plans`
- `GET /billing/payment-plans/{plan_id}`

### 6. Attendance Analytics + Alerts (`ENH-C2`)

Implemented:
- `AttendanceAlert` model
- `AttendanceThresholdExceeded` domain event
- `backend/app/repositories/attendance_analytics.py`
- `backend/app/services/attendance_analytics.py`
- attendance rate, trends, class/student analytics
- threshold-check endpoint and alert persistence
- `G29a` migration

Added routes:
- `GET /analytics/attendance`
- `GET /analytics/attendance/class/{class_id}`
- `GET /analytics/attendance/student/{student_id}`
- `GET /analytics/attendance/trends/{class_id}`
- `GET /analytics/attendance/alerts`
- `POST /analytics/attendance/check-thresholds`

### 7. Timetable Generation (`ENH-C3`)

Implemented models:
- `TimetableConstraint`
- `TimetableGenerationJob`

Implemented:
- `backend/app/repositories/timetable_generation.py`
- `backend/app/services/timetable_generator.py`
- synchronous preview/apply generation flow
- constraint replacement/listing
- generation job persistence
- `G29b` migration

Added routes:
- `POST /timetable/constraints`
- `GET /timetable/constraints`
- `POST /timetable/generate`
- `GET /timetable/generate/{job_id}`
- `GET /timetable/generate/{job_id}/preview`
- `POST /timetable/generate/{job_id}/apply`

### 8. Messaging + Documents (`ENH-D1`)

Implemented:
- `Message.attachment_id`
- `DocumentVersion` model
- search support in messaging
- document version history and restore
- `G30a` and `G30b` migrations

Updated:
- `backend/app/repositories/messaging.py`
- `backend/app/repositories/documents.py`
- `backend/app/services/communication.py`
- `backend/app/services/student_documents.py`
- `backend/app/services/file_storage.py`

Added routes:
- `GET /messages/search`
- `GET /documents/{document_id}/versions`
- `GET /documents/{document_id}/versions/{version_number}`
- `POST /documents/{document_id}/versions/{version_number}/restore`

### 9. Report Scheduling + AI Provider Abstraction (`ENH-D2`)

Implemented models and scheduling stack:
- `ReportSchedule` model in [reporting.py](/Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev/backend/app/models/reporting.py)
- `backend/app/schemas/report_schedule.py`
- `backend/app/repositories/report_schedule.py`
- `backend/app/services/report_scheduler.py`
- `task_process_due_report_schedules` in [tasks.py](/Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev/backend/app/core/tasks.py)
- `G30c` migration

Added routes:
- `POST /reports/schedules`
- `GET /reports/schedules`
- `PUT /reports/schedules/{schedule_id}`
- `DELETE /reports/schedules/{schedule_id}`
- `POST /reports/schedules/{schedule_id}/run`

Implemented AI package split:
- removed legacy `backend/app/services/ai.py`
- created `backend/app/services/ai/`
- created:
  - `__init__.py`
  - `ai_service.py`
  - `provider_base.py`
  - `mock_provider.py`
  - `claude_provider.py`
  - `provider_factory.py`

Updated config:
- `ai_provider`
- `ai_api_key`
- `ai_model`

### 10. Final Validation (`ENH-E1`)

Validation outcome:
- `ENH-E1` initially surfaced one failing check for permission-role drift
- that drift was fixed afterward in [permissions.py](/Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev/backend/app/core/permissions.py)
- the enhancement validation now passes all 18 checks

## Decisions Taken During Implementation

These are the main execution decisions that were not clearly spelled out in the prompts or checklist.

### 1. Existing response shapes were preserved where the prompt did not require changing them

This affected multiple areas:
- message responses were not expanded to return `attachment_id`, even though attachments are now accepted and stored;
- gradebook support was added without rewriting old assignment response shapes;
- existing endpoint envelopes were preserved unless a prompt explicitly required a different response model.

Reason:
- the meta prompt explicitly said not to change existing response shapes.

### 2. Gradebook support was added without retrofitting all assignment payloads

`Assignment.grade_category_id` exists at the model/service layer and gradebook logic uses it, but the prompt did not require a broad assignment API contract rewrite.

Reason:
- avoids breaking existing assignment clients while still enabling the new gradebook flow.

### 3. Late penalties were applied to rubric grading too

Late-penalty logic was not limited to standard manual grading. It was also applied in rubric-based grading paths.

Reason:
- otherwise `/submissions/{id}/grade-rubric` would have bypassed the penalty rules introduced by `ENH-B4`.

### 4. Optional late-policy fields were exposed on assignment creation

Although `ENH-B4` mainly described model/service behavior, optional late-policy creation fields were added so the feature is usable through the API.

Reason:
- adding backend logic without any creation-time input would make the feature incomplete in practice.

### 5. Sibling discounts stack with manual discounts but are capped at 100%

Billing logic allows sibling discount percentage to stack with pre-existing manual assignment discounts, but the effective total discount is capped.

Reason:
- keeps feature behavior additive without allowing invalid over-discounting.

### 6. Late fees are incremental, not blindly appended

Late fee application was implemented as a delta calculation against existing late-fee invoice lines rather than always inserting new duplicate fee lines.

Reason:
- allows `apply_late_fees()` to be rerun safely.

### 7. Attendance analytics config followed the project’s lowercase settings style

The prompt/architecture examples use uppercase env-style names, but implementation added lowercase settings fields:
- `attendance_warning_threshold`
- `attendance_critical_threshold`
- `ai_provider`
- `ai_api_key`
- `ai_model`

Reason:
- [config.py](/Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev/backend/app/core/config.py) already uses lowercase field names throughout.

### 8. `preview_generated()` for timetable generation stayed read-only

Timetable preview reads from the stored job payload and does not create `TimetableSlot` rows. `apply_generated()` performs the actual replacement of the academic year’s slots and marks the job as applied.

Reason:
- keeps the preview/apply contract clean and prevents accidental writes during preview.

### 9. Document restore creates a new current file, not just a pointer flip

Restoring a document version performs a physical file copy into the current document record instead of only repointing metadata.

Reason:
- keeps version history intact and prevents destructive coupling between current and historical storage references.

### 10. Storage cleanup counts version references and shared previews

Document storage cleanup was updated to consider both `Document` and `DocumentVersion` references, plus shared thumbnail usage.

Reason:
- avoids deleting versioned assets or shared previews too early.

### 11. Report scheduling reuses existing report generation instead of building a second pipeline

`ReportSchedulerService` calls the existing `ReportsService` request/generation flow rather than creating a separate rendering implementation.

Reason:
- reduces duplication and ensures scheduled reports behave like manual report jobs.

### 12. Scheduled report email delivery reuses the existing notification email template

Scheduled report emails use `notification_alert.html` with the report download link.

Reason:
- the prompt required email delivery, but did not require a new template;
- reusing the existing template kept the implementation smaller and consistent.

### 13. `end_of_period` schedules behave as one-shot triggers after execution

If an `end_of_period` schedule runs successfully for a period that has already ended, `next_run_at` is cleared rather than reusing the same past timestamp.

Reason:
- prevents the worker from reprocessing the same schedule indefinitely.

### 14. The AI package split kept the existing `from app.services.ai import AIService` import path stable

The old module file was removed and replaced with a package whose `__init__.py` re-exports `AIService`.

Reason:
- avoids router churn and keeps the public service import unchanged.

### 15. `MockProvider` was implemented as a realistic local provider, not a placeholder stub

`MockProvider` now returns:
- language-aware completion text;
- structured writing feedback;
- recommendation items with reason codes;
- KPI insight text.

Reason:
- the prompt explicitly required useful responses, not empty strings or `"mock response"`.

### 16. `ClaudeProvider` is fully wired but intentionally inactive by default

`ClaudeProvider`:
- conditionally imports `anthropic`;
- creates an async client only if the dependency and API key are available;
- falls back to `MockProvider` on API/setup/runtime failure.

Reason:
- satisfies the prompt requirement to be ready-to-use without making the local environment depend on active Claude credentials.

### 17. The architecture mentions `openai_provider.py`, but it was not implemented in Part 2

The architecture document’s AI section shows an `openai_provider.py` example, but the execution prompt for `ENH-D2` required only:
- `provider_base.py`
- `mock_provider.py`
- `claude_provider.py`
- `provider_factory.py`

Decision:
- only the prompt-required providers were implemented.

### 18. Dependency declarations were not changed

No requirements file update was made before Part 2.

Reason:
- the earlier import-health issue was caused by using the wrong interpreter;
- backend dependencies already existed in `backend/.venv` and `backend/requirements.txt`.

### 19. `/auth/login-history` now uses authenticated self-access instead of RBAC gating

After tightening `PERM_IAM_LOGIN_HISTORY_READ` to match the architecture summary (`ADM`, `DIR`, `SUP`), the self-service route in [auth.py](/Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev/backend/app/api/v1/auth.py) was switched to `get_current_user`.

Reason:
- the architecture summary says login-history access is admin/director/support plus self;
- keeping RBAC on the self route would have forced broader role grants than the architecture intended.

## Validation Result from `ENH-E1`

### Passed

Passed checks:
- IAM enhancements
- rubric engine
- gradebook
- question bank
- late penalties
- sibling discounts
- late fees
- payment plans
- attendance analytics
- timetable generation
- message attachments
- document versioning
- report scheduling
- AI provider abstraction
- migrations `G27a` through `G30c`
- endpoint registration in main router
- import health

### Post-Validation Permission Alignment

After `ENH-E1`, the permission-role drift was corrected so that the enhancement permission map matches the summary in [ENHANCEMENT_ARCHITECTURE.md](/Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev/ENHANCEMENT_ARCHITECTURE.md).

That cleanup included:
- narrowing `PERM_IAM_LOGIN_HISTORY_READ` to `ADM`, `DIR`, `SUP`
- adding missing LMS enhancement grants to `ADM`, `DIR`, `TCH`, and `CONTENT_MGR` where required
- removing extra `DIR`, `PAR`, `STD`, and `SYS` grants where the architecture did not include them
- preserving self-service login-history access through the auth route instead of broader RBAC role grants

## Environment Notes

- Use the backend virtual environment for verification:

```bash
cd backend && .venv/bin/python ...
```

- Full backend Python compile verification passed with:

```bash
cd backend && .venv/bin/python -m py_compile $(find app -name '*.py' -print)
```

- Router import smoke checks still emit non-blocking `fontconfig` cache warnings in this local environment. They did not prevent validation.

## Suggested Next Follow-Up

Part 2 is now technically closed. The next useful follow-up would be optional regression testing around:
- login-history self access versus admin target access;
- LMS enhancement permissions for `DIR`, `TCH`, and `CONTENT_MGR`;
- billing policy access after removing the extra `DIR` grants.
