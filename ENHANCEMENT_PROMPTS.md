# Enhancement Prompts — Ecole Platform

> Execute AFTER OOP refactor (OOP-A through OOP-F).
> Each prompt is self-contained. Run one at a time.
> Reference: ENHANCEMENT_ARCHITECTURE.md

---

## Pre-Requisite

The AI agent MUST have already executed META_PROMPT_OOP_1_CONTEXT.md and read ENHANCEMENT_ARCHITECTURE.md before running these prompts.

---

## Phase ENH-A: IAM Enhancements

### Prompt ENH-A1: Admin Impersonation + Login History + Session Limits

```
CONTEXT: You are working on Ecole Platform. Read ENHANCEMENT_ARCHITECTURE.md sections A1, A2, A3.

TASK: Implement all three IAM enhancements in one batch.

STEPS:
1. Add LoginHistory model to backend/app/models/iam.py (exact spec from ENHANCEMENT_ARCHITECTURE.md A2).
2. Add impersonator_id column to Session model in iam.py.
3. Update backend/app/models/__init__.py — add LoginHistory export.
4. Create Alembic migration G27a: login_history table + Session.impersonator_id column.
5. Create backend/app/repositories/login_history.py:
   - create_login_record(...)
   - list_user_login_history(user_id, limit, cursor)
   - get_device_fingerprints(user_id, days=30)
6. Update backend/app/repositories/auth.py:
   - count_active_sessions(user_id, school_id)
   - get_oldest_active_session(user_id, school_id)
7. Update backend/app/services/auth.py:
   - In login(): create LoginHistory record, check for new device, emit NewDeviceLogin event.
   - In login(): check concurrent session limit, revoke oldest if exceeded.
   - Add impersonate() method (creates shadow session with impersonator_id).
   - Add stop_impersonation() method.
8. Add NewDeviceLogin domain event to backend/app/domain/events/auth.py.
9. Register NewDeviceLogin in EventDispatcher (email delivery).
10. Add PERM_ADM_IMPERSONATE and PERM_IAM_LOGIN_HISTORY_READ to backend/app/core/permissions.py.
11. Assign permissions to roles (ADM, DIR, SUP get impersonate; all get login_history_read for self).
12. Add endpoints to backend/app/api/v1/auth.py:
    - GET /auth/login-history
13. Add endpoints to backend/app/api/v1/admin.py:
    - POST /admin/impersonate/{user_id}
    - POST /admin/stop-impersonation
    - GET /admin/users/{user_id}/login-history
14. Register new endpoints in router.py.
15. Add MAX_SESSIONS_PER_USER = 5 to backend/app/core/config.py.

RULES:
- Use UnitOfWork for all write operations.
- All new code follows 3-tier pattern (Router → Service → Repository).
- Do NOT run any git command.
```

---

## Phase ENH-B: LMS Enhancements

### Prompt ENH-B1: Rubric Engine — Models + Migration

```
CONTEXT: Read ENHANCEMENT_ARCHITECTURE.md section B1 (Rubric Engine).

TASK: Create rubric models and migration.

STEPS:
1. Add Rubric, RubricCriterion, RubricLevel, RubricScore models to backend/app/models/lms.py.
2. Add rubric_id FK to Assignment model.
3. Update models/__init__.py with new exports.
4. Create Alembic migration G28a: rubrics, rubric_criteria, rubric_levels, rubric_scores tables + Assignment.rubric_id column.
5. Create backend/app/schemas/rubric.py:
   - RubricCreateRequest, CriterionInput, LevelInput
   - RubricResponse, CriterionResponse, LevelResponse
   - RubricScoreInput, RubricScoreResponse, RubricResultsResponse

RULES:
- Follow existing model patterns (TimestampMixin, UUID PK, proper indexes).
- Do NOT run any git command.
```

### Prompt ENH-B2: Rubric Engine — Service + Router

```
CONTEXT: ENH-B1 created rubric models. Read ENHANCEMENT_ARCHITECTURE.md B1.

TASK: Create RubricService and endpoints.

STEPS:
1. Create backend/app/repositories/rubric.py:
   - get_rubric(), create_rubric(), list_rubrics()
   - create_criterion(), create_level()
   - create_rubric_score(), list_rubric_scores()
2. Create backend/app/services/rubric.py — RubricService with all methods from ENHANCEMENT_ARCHITECTURE.md B1.
3. Add PERM_LMS_RUBRIC_CREATE, PERM_LMS_RUBRIC_READ to permissions.py.
4. Assign to roles (TCH, ADM).
5. Create backend/app/api/v1/rubrics.py — all endpoints from B1.
6. Register in router.py.
7. Update assignment grading in AssignmentService to support rubric-based grading.

RULES:
- Use UnitOfWork for writes. Use MoroccanGrade value object for score calculations.
- Do NOT run any git command.
```

### Prompt ENH-B3: Weighted Gradebook + GPA

```
CONTEXT: Read ENHANCEMENT_ARCHITECTURE.md B2 (Weighted Gradebook).

TASK: Create grade categories, weighted averages, and gradebook service.

STEPS:
1. Add GradeCategory, StudentPeriodAverage models to lms.py.
2. Add grade_category_id FK to Assignment model.
3. Create migration G28b: grade_categories, student_period_averages tables + Assignment.grade_category_id.
4. Create backend/app/schemas/gradebook.py — all request/response schemas.
5. Create backend/app/repositories/gradebook.py:
   - CRUD for grade categories
   - get_student_grades_by_category()
   - save_student_period_average()
   - get_class_averages(), get_student_transcript()
6. Create backend/app/services/gradebook.py — GradebookService with all methods from B2.
   - Use MoroccanGrade value object for mention calculation.
7. Add PERM_LMS_GRADEBOOK_MANAGE, PERM_LMS_GRADEBOOK_READ to permissions.py.
8. Assign to roles (TCH manage, PAR/STD/ADM/DIR read).
9. Create backend/app/api/v1/gradebook.py — all endpoints.
10. Register in router.py.

RULES:
- Weighted average formula: sum(category_avg × weight) for each category.
- Validate weights sum to 1.0 (with 0.01 tolerance for rounding).
- Use UnitOfWork, MoroccanGrade value object.
- Do NOT run any git command.
```

### Prompt ENH-B4: Question Bank + Late Submission Penalties

```
CONTEXT: Read ENHANCEMENT_ARCHITECTURE.md B3 (Question Bank) and B4 (Late Penalties).

TASK: Implement question bank and late submission penalties.

STEPS — Question Bank:
1. Add QuestionBankItem model to lms.py.
2. Create migration G28c: question_bank_items table.
3. Create backend/app/schemas/question_bank.py.
4. Create backend/app/repositories/question_bank.py.
5. Create backend/app/services/question_bank.py — QuestionBankService.
6. Add PERM_LMS_QUESTION_BANK_MANAGE, PERM_LMS_QUESTION_BANK_READ to permissions.py.
7. Create backend/app/api/v1/question_bank.py — all endpoints.
8. Register in router.py.

STEPS — Late Penalties:
9. Add grace_period_hours, late_penalty_per_day, max_late_days, allow_late to Assignment model.
10. Add original_score, late_penalty, late_days, penalty_overridden to Grade model.
11. Create migration G28d: Assignment + Grade column additions.
12. Update AssignmentService.grade_submission() to calculate late penalties as described in B4.
13. Add override_late_penalty() method to AssignmentService.
14. Add POST /submissions/{id}/override-penalty endpoint.

RULES:
- Question bank generate_quiz_from_bank uses random.sample() for selection.
- Late penalty: max(0, score - penalty) — never negative.
- Do NOT run any git command.
```

---

## Phase ENH-C: Billing & ERP Enhancements

### Prompt ENH-C1: Sibling Discounts + Late Fees + Payment Plans

```
CONTEXT: Read ENHANCEMENT_ARCHITECTURE.md C1, C2.

TASK: Implement sibling discount logic, late fee policies, and payment plans.

STEPS:
1. Add SiblingDiscountPolicy, LateFeePolicy, PaymentPlan, Installment models to billing.py.
2. Update models/__init__.py.
3. Create migration G27b: sibling_discount_policies, late_fee_policies, payment_plans, installments tables.
4. Create backend/app/schemas/billing_enhancements.py — all new schemas.
5. Create backend/app/repositories/billing_enhancements.py:
   - CRUD for policies
   - CRUD for payment plans and installments
   - get_siblings_by_parent()
6. Update backend/app/services/billing.py:
   - In generate_invoices(): detect siblings, apply tiered discounts from SiblingDiscountPolicy.
   - Add apply_late_fees() method for background processing.
7. Create backend/app/services/payment_plan.py — PaymentPlanService.
8. Add new permissions to permissions.py.
9. Add endpoints to billing.py router or create new router file.
10. Register in router.py.

RULES:
- Sibling discount stacks with manual fee_assignment discount.
- Late fees: compute based on policy (fixed/percent × frequency × days_late), cap at max_fee.
- Payment plan splits into equal installments.
- Use UnitOfWork, Money value object.
- Do NOT run any git command.
```

### Prompt ENH-C2: Attendance Analytics + Alerts

```
CONTEXT: Read ENHANCEMENT_ARCHITECTURE.md C3.

TASK: Implement attendance analytics with configurable thresholds.

STEPS:
1. Add AttendanceAlert model to erp.py.
2. Update models/__init__.py.
3. Create migration G29a: attendance_alerts table.
4. Create backend/app/schemas/attendance_analytics.py.
5. Create backend/app/repositories/attendance_analytics.py:
   - compute_student_absence_count()
   - compute_class_absence_rates()
   - get_absence_trends()
   - create_attendance_alert()
   - list_alerts()
6. Create backend/app/services/attendance_analytics.py — AttendanceAnalyticsService.
7. Add AttendanceThresholdExceeded domain event.
8. Register in EventDispatcher (push + email).
9. Add PERM_ERP_ATTENDANCE_ANALYTICS_READ, PERM_ERP_ATTENDANCE_ALERT_MANAGE to permissions.py.
10. Create backend/app/api/v1/attendance_analytics.py — all endpoints.
11. Register in router.py.
12. Add ATTENDANCE_WARNING_THRESHOLD and ATTENDANCE_CRITICAL_THRESHOLD to config.py.

RULES:
- Absence rate = absent_count / total_sessions (exclude excused).
- Alert is created only once per student per period per threshold level.
- Use UnitOfWork. Emit domain events for notifications.
- Do NOT run any git command.
```

### Prompt ENH-C3: Timetable Auto-Generation

```
CONTEXT: Read ENHANCEMENT_ARCHITECTURE.md C4.

TASK: Implement timetable constraint system and greedy generation algorithm.

STEPS:
1. Add TimetableConstraint, TimetableGenerationJob models to erp.py.
2. Update models/__init__.py.
3. Create migration G29b: timetable_constraints, timetable_generation_jobs tables.
4. Create backend/app/schemas/timetable_generation.py.
5. Create backend/app/repositories/timetable_generation.py.
6. Create backend/app/services/timetable_generator.py — TimetableGeneratorService:
   - set_constraints(), list_constraints()
   - generate() — the core algorithm:
     a. Load all constraints, classes, teachers, rooms.
     b. Build list of (class, subject, hours_per_week) requirements.
     c. Define available timeslots (e.g., Mon-Fri, 08:00-17:00, 1-hour blocks).
     d. Greedy assignment with backtracking:
        - For each requirement, try each available slot.
        - Check constraints: teacher not double-booked, room not full, teacher available, no consecutive same subject.
        - If valid, assign. If no valid slot, backtrack.
     e. Score solution: count unassigned requirements (conflicts).
     f. Store candidate TimetableSlots in job result.
   - get_job_status(), preview_generated(), apply_generated()
7. Add PERM_ERP_TIMETABLE_GENERATE, PERM_ERP_TIMETABLE_CONSTRAINT_MANAGE to permissions.py.
8. Create backend/app/api/v1/timetable_generation.py — all endpoints.
9. Register in router.py.

RULES:
- Algorithm must handle at least 20 classes × 10 teachers within 30 seconds.
- preview shows slots WITHOUT committing. apply() creates real TimetableSlot rows.
- Job runs synchronously for v1 (can be made async later with Celery).
- Use UnitOfWork for writes.
- Do NOT run any git command.
```

---

## Phase ENH-D: Communication & Docs Enhancements

### Prompt ENH-D1: Message Attachments + Search + Document Versioning

```
CONTEXT: Read ENHANCEMENT_ARCHITECTURE.md D1, D2.

TASK: Add message attachments, message search, and document versioning.

STEPS — Message Attachments:
1. Add attachment_id FK to Message model in com.py.
2. Update send_message in communication.py to accept attachment_id.
3. Validate attachment belongs to sender (document.uploader_id == user_id).

STEPS — Message Search:
4. Create migration G30a: Message.attachment_id + GIN index on messages.body.
5. Add search_messages() to messaging repository.
6. Add search_messages() to communication service.
7. Add GET /messages/search endpoint.

STEPS — Document Versioning:
8. Add DocumentVersion model to documents.py.
9. Create migration G30b: document_versions table.
10. Update student_documents.py upload logic:
    - When uploading, check if document with same category + linked_student exists.
    - If yes: create DocumentVersion from current state, then update document.
    - If no: normal upload.
11. Add list_versions(), restore_version(), get_version() to student_documents service.
12. Add endpoints: GET /documents/{id}/versions, POST /documents/{id}/versions/{n}/restore, GET /documents/{id}/versions/{n}.
13. Update models/__init__.py and repositories.

RULES:
- Message search uses PostgreSQL full-text search (to_tsvector + ts_query).
- Document version restore copies the old version's file to become the current.
- Use UnitOfWork for all writes.
- Do NOT run any git command.
```

### Prompt ENH-D2: Report Scheduling + AI Provider Abstraction

```
CONTEXT: Read ENHANCEMENT_ARCHITECTURE.md D3, D4.

TASK: Add report scheduling and AI provider abstraction.

STEPS — Report Scheduling:
1. Add ReportSchedule model to reporting.py.
2. Create migration G30c: report_schedules table.
3. Create backend/app/schemas/report_schedule.py.
4. Create backend/app/repositories/report_schedule.py.
5. Create backend/app/services/report_scheduler.py — ReportSchedulerService.
6. Add PERM_RPT_SCHEDULE_MANAGE to permissions.py.
7. Create endpoints in reports.py router or new file.
8. Add process_due_schedules() as a background task trigger (called by core/tasks.py).

STEPS — AI Provider Abstraction:
9. Create backend/app/services/ai/ directory.
10. Move existing ai.py content to backend/app/services/ai/ai_service.py.
11. Create backend/app/services/ai/__init__.py — re-export AIService.
12. Create backend/app/services/ai/provider_base.py — AIProvider Protocol.
13. Create backend/app/services/ai/mock_provider.py — MockProvider:
    - complete(): returns template responses based on keywords (fr/ar/en).
    - analyze_writing(): returns grammar/structure feedback based on text analysis.
    - generate_recommendations(): returns grade-range-based recommendations.
    - compute_kpi_insights(): returns threshold-based insights.
    MockProvider should return realistic, helpful responses (not just "mock response").
14. Create backend/app/services/ai/claude_provider.py — ClaudeProvider:
    - Full implementation using anthropic SDK.
    - All methods call self._client.messages.create().
    - Wrap in try/except, fallback to MockProvider on API error.
    - Add comment: # Activate by setting AI_PROVIDER=claude and AI_API_KEY in .env
15. Create backend/app/services/ai/provider_factory.py — create_ai_provider(settings).
16. Add AI_PROVIDER, AI_API_KEY, AI_MODEL to config.py (defaults: mock, empty, empty).
17. Update ai_service.py to use self._provider = create_ai_provider(settings).
18. Update routers that use AIService.

RULES:
- MockProvider MUST return useful, realistic responses (not empty strings).
- ClaudeProvider should import anthropic conditionally (try/except ImportError).
- Report scheduler uses existing report generation logic, adds email delivery.
- Use UnitOfWork for writes.
- Do NOT run any git command.
```

---

## Phase ENH-E: Final Validation

### Prompt ENH-E1: Enhancement Validation

```
CONTEXT: All enhancement prompts (A1-D2) have been executed.

TASK: Validate all 15 enhancements.

CHECKS:
1. IAM: impersonator_id on Session model, LoginHistory model exists, login creates history records, MAX_SESSIONS_PER_USER in config.
2. Rubric: Rubric + RubricCriterion + RubricLevel + RubricScore models exist, rubric_id on Assignment, /rubrics endpoints work.
3. Gradebook: GradeCategory + StudentPeriodAverage models exist, grade_category_id on Assignment, /gradebook endpoints work.
4. Question Bank: QuestionBankItem model exists, /question-bank endpoints work, generate-quiz creates quiz.
5. Late Penalties: Assignment has grace_period_hours + late_penalty_per_day, Grade has original_score + late_penalty.
6. Sibling Discounts: SiblingDiscountPolicy model exists, generate_invoices applies tiered discounts.
7. Late Fees: LateFeePolicy model exists, apply_late_fees() method works.
8. Payment Plans: PaymentPlan + Installment models exist, /payment-plans endpoints work.
9. Attendance Analytics: AttendanceAlert model exists, /analytics/attendance endpoints work, threshold alerts created.
10. Timetable Generation: TimetableConstraint + TimetableGenerationJob models exist, generate algorithm runs.
11. Message Attachments: attachment_id on Message, search endpoint works.
12. Document Versioning: DocumentVersion model exists, /versions endpoints work.
13. Report Scheduling: ReportSchedule model exists, /schedules endpoints work.
14. AI Provider: services/ai/ directory exists, MockProvider returns useful responses, ClaudeProvider ready.
15. All new permissions registered in permissions.py with correct role assignments.
16. All 4 migrations (G27-G30) exist and are valid.
17. All new endpoints registered in router.py.
18. All import health checks pass.

OUTPUT: PASS/FAIL table for each check.

RULES:
- Do NOT fix issues — just report them.
- Do NOT run any git command.
```

---

## Summary

| Phase | Prompt | Features | New Files (approx) |
|-------|--------|----------|-------------------|
| ENH-A1 | IAM | Impersonation + Login History + Session Limits | ~8 |
| ENH-B1 | LMS Models | Rubric models + migration | ~4 |
| ENH-B2 | LMS Rubric | RubricService + router | ~5 |
| ENH-B3 | LMS Gradebook | GradebookService + weighted averages | ~5 |
| ENH-B4 | LMS Quiz+Late | Question Bank + Late Penalties | ~7 |
| ENH-C1 | Billing | Siblings + Late Fees + Payment Plans | ~6 |
| ENH-C2 | Attendance | Analytics + threshold alerts | ~5 |
| ENH-C3 | Timetable | Auto-generation algorithm | ~5 |
| ENH-D1 | Comms/Docs | Attachments + Search + Versioning | ~5 |
| ENH-D2 | Reports/AI | Scheduling + Provider abstraction | ~10 |
| ENH-E1 | Validation | Full check | 0 |
