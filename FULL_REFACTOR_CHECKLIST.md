# Full Refactor Checklist — Ecole Platform

> Unified tracking for OOP Refactor + Feature Enhancements.
> Mark items [x] as you complete each prompt. Review & commit after each section.

---

## PART 1: OOP REFACTOR (Prompts OOP-A1 through OOP-F1)

---

### Phase OOP-A: Foundation Layer

#### OOP-A1: Value Objects
- [x] Created backend/app/domain/ directory
- [x] Created backend/app/domain/value_objects/ directory
- [x] Created backend/app/domain/events/ directory
- [x] Created backend/app/domain/protocols/ directory
- [x] Created __init__.py files in all domain directories
- [x] Created MoroccanGrade (grade.py) — validates 0-20, has mention property
- [x] Created Money (money.py) — validates non-negative, MAD currency
- [x] Created UserId + SchoolId (typed_id.py)
- [x] Created RoleSet (role_set.py) — validates 8 roles
- [ ] **Review & commit myself**

#### OOP-A2: UnitOfWork (Core Services)
- [x] Created backend/app/core/unit_of_work.py
- [x] Updated auth.py — register() uses UoW
- [x] Updated auth.py — login() uses UoW
- [x] Updated billing.py — create_invoice uses UoW
- [x] Updated billing.py — process_payment uses UoW
- [x] Updated erp.py — create_enrollment uses UoW
- [x] Updated erp.py — batch_attendance uses UoW
- [x] Verified no direct db.commit() in updated methods
- [ ] **Review & commit myself**

#### OOP-A3: UnitOfWork (All Services)
- [x] Updated admin.py with UoW
- [x] Updated ai.py with UoW
- [x] Updated audit.py with UoW
- [x] Updated calendar.py with UoW
- [x] Updated cms.py with UoW
- [x] Updated communication.py with UoW
- [x] Updated data_export.py with UoW
- [x] Updated email_digest.py with UoW
- [x] Updated feature.py with UoW
- [x] Updated gdpr.py with UoW
- [x] Updated lms.py with UoW
- [x] Updated notification_hub.py with UoW
- [x] Updated overdue_reminders.py with UoW
- [x] Updated payment_retry.py with UoW
- [x] Updated profile.py with UoW
- [x] Reviewed progress.py (read-only, no DB transaction writes)
- [x] Updated push_config.py with UoW
- [x] Updated quiz_grading.py with UoW
- [x] Reviewed realtime.py (no DB transaction writes)
- [x] Updated reminders.py with UoW
- [x] Updated reports.py with UoW
- [x] Updated resource_library.py with UoW
- [x] Updated rsvp.py with UoW
- [x] Updated student_documents.py with UoW
- [x] Zero db.commit() calls remain in services (only uow.commit)
- [ ] **Review & commit myself**

---

### Phase OOP-B: Profile System

#### OOP-B1: Profile Models + Migration
- [x] Added AdminProfile model to iam.py
- [x] Added ContentManagerProfile model to iam.py
- [x] Updated models/__init__.py with new exports
- [x] Created Alembic migration g26_oop_profiles
- [x] Migration creates admin_profiles table
- [x] Migration creates content_manager_profiles table
- [x] Migration adds correct indexes
- [ ] **Review & commit myself**

#### OOP-B2: ProfileLoader
- [x] Created repositories/profile_loader.py
- [x] Created services/profile_loader.py
- [x] Updated auth.py to use ProfileLoader on register
- [x] Updated auth.py to use ProfileLoader on /me
- [x] Updated profile.py to use ProfileLoader
- [x] Updated repositories/__init__.py
- [ ] **Review & commit myself**

---

### Phase OOP-C: Domain Events

#### OOP-C1: Event Classes
- [x] Created domain/events/base.py (DomainEvent)
- [x] Created domain/events/lms.py (5 events)
- [x] Created domain/events/calendar.py (4 events)
- [x] Created domain/events/billing.py (3 events)
- [x] Created domain/events/documents.py (3 events)
- [x] Created domain/events/auth.py (3 events)
- [x] Updated domain/events/__init__.py with all exports
- [ ] **Review & commit myself**

#### OOP-C2: Delivery Strategies
- [x] Created services/delivery/ directory
- [x] Created delivery/base.py (DeliveryStrategy ABC)
- [x] Created delivery/push.py (PushDeliveryStrategy)
- [x] Created delivery/email_delivery.py (EmailDeliveryStrategy)
- [x] Created delivery/sms_delivery.py (SMSDeliveryStrategy)
- [x] Created delivery/in_app.py (InAppDeliveryStrategy)
- [x] Created services/event_dispatcher.py
- [x] Registered all events in EVENT_HANDLERS
- [ ] **Review & commit myself**

#### OOP-C3: Wire Events into Services
- [x] lms.py emits GradePublished
- [x] lms.py emits AssignmentCreated
- [x] lms.py emits QuizCompleted
- [x] lms.py emits SubmissionReceived
- [x] calendar.py emits EventCreated
- [x] calendar.py emits EventUpdated
- [x] billing.py emits InvoiceGenerated
- [x] billing.py emits PaymentReceived/Failed
- [x] student_documents.py emits DocumentExpiring
- [x] resource_library.py emits ResourceShared
- [x] auth.py emits UserRegistered
- [x] Existing notification calls kept as fallback (marked TODO)
- [ ] **Review & commit myself**

---

### Phase OOP-D: Evaluatable Protocol

#### OOP-D1: Protocols + Strategies
- [x] Created domain/protocols/evaluatable.py
- [x] Created domain/protocols/grading.py
- [x] QuizAutoGradeStrategy implemented
- [x] ManualGradeStrategy implemented
- [x] QuizRepository satisfies Evaluatable
- [x] Assignment repo methods satisfy Evaluatable
- [x] Assessment repo methods satisfy Evaluatable
- [ ] **Review & commit myself**

#### OOP-D2: StudentWork Service
- [x] Created services/student_work.py
- [x] Created schemas/student_work.py
- [x] Added GET /student-work endpoint
- [x] Added GET /student-work/class/{class_id} endpoint
- [x] Registered in router.py
- [x] Added permissions
- [ ] **Review & commit myself**

---

### Phase OOP-E: LMS Split

#### OOP-E1: Split lms.py
- [x] Created services/lms/ directory
- [x] Created lms/course_service.py
- [x] Created lms/assignment_service.py
- [x] Created lms/quiz_service.py
- [x] Created lms/content_service.py
- [x] Created lms/progress_service.py
- [x] Created lms/_helpers.py (shared functions)
- [x] Created lms/__init__.py (re-exports)
- [x] Updated courses.py router
- [x] Updated assignments.py router
- [x] Updated submissions.py router
- [x] Updated quizzes.py router
- [x] Updated content.py router
- [x] Updated content_library.py router
- [x] Updated results.py router
- [x] Updated progress.py router
- [x] Updated assessments.py router
- [x] Updated activities.py router
- [x] Deleted original services/lms.py
- [x] Each sub-service under 500 lines
- [ ] **Review & commit myself**

---

### Phase OOP-F: OOP Validation

#### OOP-F1: Full Validation
- [x] Zero db.commit() in services (only uow.commit)
- [x] All value objects validate correctly
- [x] Both new profile tables exist in migration
- [x] ProfileLoader works for 5 role types
- [x] All domain event files exist
- [x] EventDispatcher has all events registered
- [x] 5+ services emit events
- [x] All 3 repos satisfy Evaluatable protocol
- [x] StudentWorkService combines all types
- [x] /student-work endpoint registered
- [x] LMS split into 5 sub-services
- [x] All router imports resolve
- [x] All import health checks pass
- [ ] **Review & commit myself**

---

## PART 2: FEATURE ENHANCEMENTS (Prompts ENH-A1 through ENH-E1)

---

### Phase ENH-A: IAM Enhancements

#### ENH-A1: Admin Impersonation + Login History + Session Limits
- [x] Added LoginHistory model to iam.py
- [x] Added impersonator_id column to Session model
- [x] Updated models/__init__.py with LoginHistory export
- [x] Created migration G27a: login_history + Session.impersonator_id
- [x] Created repositories/login_history.py (create_login_record, list_user_login_history, get_device_fingerprints)
- [x] Updated repositories/auth.py (count_active_sessions, get_oldest_active_session)
- [x] Updated services/auth.py — login creates LoginHistory, checks concurrent sessions
- [x] Added impersonate() method to auth service
- [x] Added stop_impersonation() method to auth service
- [x] Added NewDeviceLogin event to domain/events/auth.py
- [x] Registered NewDeviceLogin in EventDispatcher
- [x] Added PERM_ADM_IMPERSONATE + PERM_IAM_LOGIN_HISTORY_READ to permissions.py
- [x] Assigned permissions to roles (ADM, DIR, SUP)
- [x] Added GET /auth/login-history endpoint
- [x] Added POST /admin/impersonate/{user_id} endpoint
- [x] Added POST /admin/stop-impersonation endpoint
- [x] Added GET /admin/users/{user_id}/login-history endpoint
- [x] Registered endpoints in router.py
- [x] Added MAX_SESSIONS_PER_USER = 5 to config.py
- [ ] **Review & commit myself**

---

### Phase ENH-B: LMS Enhancements

#### ENH-B1: Rubric Engine — Models + Migration
- [x] Added Rubric, RubricCriterion, RubricLevel, RubricScore models to lms.py
- [x] Added rubric_id FK to Assignment model
- [x] Updated models/__init__.py with new exports
- [x] Created migration G28a: rubrics + criteria + levels + scores tables + Assignment.rubric_id
- [x] Created schemas/rubric.py (all request/response schemas)
- [ ] **Review & commit myself**

#### ENH-B2: Rubric Engine — Service + Router
- [x] Created repositories/rubric.py (CRUD for rubrics, criteria, levels, scores)
- [x] Created services/rubric.py — RubricService
- [x] Added PERM_LMS_RUBRIC_CREATE, PERM_LMS_RUBRIC_READ to permissions.py
- [x] Assigned to roles (TCH, ADM)
- [x] Created api/v1/rubrics.py — all endpoints
- [x] Registered in router.py
- [x] Updated AssignmentService to support rubric-based grading
- [ ] **Review & commit myself**

#### ENH-B3: Weighted Gradebook + GPA
- [x] Added GradeCategory, StudentPeriodAverage models to lms.py
- [x] Added grade_category_id FK to Assignment model
- [x] Created migration G28b: grade_categories + student_period_averages + Assignment.grade_category_id
- [x] Created schemas/gradebook.py
- [x] Created repositories/gradebook.py (CRUD categories, student grades, class averages, transcripts)
- [x] Created services/gradebook.py — GradebookService with MoroccanGrade mentions
- [x] Added PERM_LMS_GRADEBOOK_MANAGE, PERM_LMS_GRADEBOOK_READ to permissions.py
- [x] Assigned to roles (TCH manage, PAR/STD/ADM/DIR read)
- [x] Created api/v1/gradebook.py — all endpoints
- [x] Registered in router.py
- [x] Validated weights sum to 1.0 (with 0.01 tolerance)
- [ ] **Review & commit myself**

#### ENH-B4: Question Bank + Late Submission Penalties
- [x] Added QuestionBankItem model to lms.py
- [x] Created migration G28c: question_bank_items table
- [x] Created schemas/question_bank.py
- [x] Created repositories/question_bank.py
- [x] Created services/question_bank.py — QuestionBankService
- [x] Added PERM_LMS_QUESTION_BANK_MANAGE, PERM_LMS_QUESTION_BANK_READ to permissions.py
- [x] Created api/v1/question_bank.py — all endpoints
- [x] Registered in router.py
- [x] Added grace_period_hours, late_penalty_per_day, max_late_days, allow_late to Assignment
- [x] Added original_score, late_penalty, late_days, penalty_overridden to Grade
- [x] Created migration G28d: Assignment + Grade column additions
- [x] Updated AssignmentService.grade_submission() with late penalty calculation
- [x] Added override_late_penalty() method to AssignmentService
- [x] Added POST /submissions/{id}/override-penalty endpoint
- [ ] **Review & commit myself**

---

### Phase ENH-C: Billing & ERP Enhancements

#### ENH-C1: Sibling Discounts + Late Fees + Payment Plans
- [x] Added SiblingDiscountPolicy, LateFeePolicy, PaymentPlan, Installment models to billing.py
- [x] Updated models/__init__.py
- [x] Created migration G27b: sibling_discount_policies + late_fee_policies + payment_plans + installments
- [x] Created schemas/billing_enhancements.py
- [x] Created repositories/billing_enhancements.py (CRUD policies, plans, installments, get_siblings)
- [x] Updated services/billing.py — generate_invoices() detects siblings, applies discounts
- [x] Added apply_late_fees() method for background processing
- [x] Created services/payment_plan.py — PaymentPlanService
- [x] Added new permissions to permissions.py
- [x] Added endpoints to billing router
- [x] Registered in router.py
- [ ] **Review & commit myself**

#### ENH-C2: Attendance Analytics + Alerts
- [x] Added AttendanceAlert model to erp.py
- [x] Updated models/__init__.py
- [x] Created migration G29a: attendance_alerts table
- [x] Created schemas/attendance_analytics.py
- [x] Created repositories/attendance_analytics.py (compute rates, trends, alerts)
- [x] Created services/attendance_analytics.py — AttendanceAnalyticsService
- [x] Added AttendanceThresholdExceeded domain event
- [x] Registered in EventDispatcher (push + email)
- [x] Added PERM_ERP_ATTENDANCE_ANALYTICS_READ, PERM_ERP_ATTENDANCE_ALERT_MANAGE to permissions.py
- [x] Created api/v1/attendance_analytics.py — all endpoints
- [x] Registered in router.py
- [x] Added ATTENDANCE_WARNING_THRESHOLD + ATTENDANCE_CRITICAL_THRESHOLD to config.py
- [ ] **Review & commit myself**

#### ENH-C3: Timetable Auto-Generation
- [x] Added TimetableConstraint, TimetableGenerationJob models to erp.py
- [x] Updated models/__init__.py
- [x] Created migration G29b: timetable_constraints + timetable_generation_jobs
- [x] Created schemas/timetable_generation.py
- [x] Created repositories/timetable_generation.py
- [x] Created services/timetable_generator.py — greedy backtracking algorithm
- [x] Algorithm handles 20 classes x 10 teachers within 30 seconds
- [x] preview() shows slots without committing, apply() creates real rows
- [x] Added PERM_ERP_TIMETABLE_GENERATE, PERM_ERP_TIMETABLE_CONSTRAINT_MANAGE to permissions.py
- [x] Created api/v1/timetable_generation.py — all endpoints
- [x] Registered in router.py
- [ ] **Review & commit myself**

---

### Phase ENH-D: Communication & Docs Enhancements

#### ENH-D1: Message Attachments + Search + Document Versioning
- [x] Added attachment_id FK to Message model in com.py
- [x] Updated send_message in communication.py to accept attachment_id
- [x] Validated attachment belongs to sender
- [x] Created migration G30a: Message.attachment_id + GIN index on messages.body
- [x] Added search_messages() to messaging repository (PostgreSQL full-text search)
- [x] Added search_messages() to communication service
- [x] Added GET /messages/search endpoint
- [x] Added DocumentVersion model to documents.py
- [x] Created migration G30b: document_versions table
- [x] Updated student_documents.py upload logic (detect existing, create version)
- [x] Added list_versions(), restore_version(), get_version() to student_documents service
- [x] Added GET /documents/{id}/versions endpoint
- [x] Added POST /documents/{id}/versions/{n}/restore endpoint
- [x] Added GET /documents/{id}/versions/{n} endpoint
- [x] Updated models/__init__.py and repositories
- [ ] **Review & commit myself**

#### ENH-D2: Report Scheduling + AI Provider Abstraction
- [x] Added ReportSchedule model to reporting.py
- [x] Created migration G30c: report_schedules table
- [x] Created schemas/report_schedule.py
- [x] Created repositories/report_schedule.py
- [x] Created services/report_scheduler.py — ReportSchedulerService
- [x] Added PERM_RPT_SCHEDULE_MANAGE to permissions.py
- [x] Created report schedule endpoints
- [x] Added process_due_schedules() background task trigger
- [x] Created services/ai/ directory
- [x] Moved ai.py to services/ai/ai_service.py
- [x] Created services/ai/__init__.py (re-exports)
- [x] Created services/ai/provider_base.py (AIProvider Protocol)
- [x] Created services/ai/mock_provider.py — MockProvider with realistic responses
- [x] Created services/ai/claude_provider.py — ClaudeProvider (ready, not active)
- [x] Created services/ai/provider_factory.py — create_ai_provider(settings)
- [x] Added AI_PROVIDER, AI_API_KEY, AI_MODEL to config.py (defaults: mock)
- [x] Updated ai_service.py to use provider factory
- [x] Updated routers that use AIService
- [ ] **Review & commit myself**

---

### Phase ENH-E: Enhancement Validation

#### ENH-E1: Full Enhancement Validation
- [x] IAM: impersonator_id on Session, LoginHistory exists, MAX_SESSIONS_PER_USER in config
- [x] Rubric: 4 models exist, rubric_id on Assignment, /rubrics endpoints registered
- [x] Gradebook: 2 models exist, grade_category_id on Assignment, /gradebook endpoints registered
- [x] Question Bank: model exists, /question-bank endpoints registered, generate-quiz works
- [x] Late Penalties: Assignment has grace/penalty fields, Grade has original_score/late_penalty
- [x] Sibling Discounts: SiblingDiscountPolicy exists, generate_invoices applies discounts
- [x] Late Fees: LateFeePolicy exists, apply_late_fees() method exists
- [x] Payment Plans: PaymentPlan + Installment exist, /payment-plans endpoints registered
- [x] Attendance Analytics: AttendanceAlert exists, /analytics/attendance endpoints registered
- [x] Timetable Generation: 2 models exist, algorithm runs within 30s
- [x] Message Attachments: attachment_id on Message, /messages/search works
- [x] Document Versioning: DocumentVersion exists, /versions endpoints registered
- [x] Report Scheduling: ReportSchedule exists, /schedules endpoints registered
- [x] AI Provider: services/ai/ exists, MockProvider realistic, ClaudeProvider ready
- [x] All new permissions registered with correct role assignments
- [x] All migrations (G27a-G30c) exist and are valid
- [x] All new endpoints registered in router.py
- [x] All import health checks pass
- [ ] **Review & commit myself**

---

## Progress Summary

| Part | Phase | Prompts | Status |
|------|-------|---------|--------|
| OOP | A — Foundation | OOP-A1, A2, A3 | Not started |
| OOP | B — Profiles | OOP-B1, B2 | Not started |
| OOP | C — Events | OOP-C1, C2, C3 | Not started |
| OOP | D — Evaluatable | OOP-D1, D2 | Not started |
| OOP | E — LMS Split | OOP-E1 | Not started |
| OOP | F — OOP Validation | OOP-F1 | Not started |
| ENH | A — IAM | ENH-A1 | Complete |
| ENH | B — LMS | ENH-B1, B2, B3, B4 | Not started |
| ENH | C — Billing/ERP | ENH-C1, C2, C3 | Not started |
| ENH | D — Comms/Docs | ENH-D1, D2 | Not started |
| ENH | E — Validation | ENH-E1 | Not started |

**Total: 23 prompts, ~120+ files to create/modify, 8 migrations (G26-G30c)**
