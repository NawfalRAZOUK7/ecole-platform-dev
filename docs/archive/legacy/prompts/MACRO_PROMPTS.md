# Macro Prompts — Ecole Platform

> **3 global prompts** that orchestrate ALL 25 execution prompts.
> Run them in order: **MACRO-1** → **MACRO-2** → **MACRO-3**.
> Each macro runs autonomously — do NOT stop until complete.
> Reference files: `EXECUTION_PROMPTS.md`, `EXECUTION_CHECKLIST.md`, `TESTING_ARCHITECTURE.md`, `CICD_INFRASTRUCTURE.md`.

---

## MACRO-1: ANALYZE & UNDERSTAND

```
═══════════════════════════════════════════════════════════════
MACRO PROMPT 1/3: ANALYZE & UNDERSTAND THE ENTIRE CODEBASE
═══════════════════════════════════════════════════════════════

OBJECTIVE:
Read, map, and deeply understand the entire Ecole Platform codebase
before writing any code. Build a complete mental model of:
- Every model, validator, property, and mixin
- Every service method, its parameters, return types, and error paths
- Every API endpoint, its auth requirements, and expected status codes
- Every permission, role hierarchy relationship, and ABAC rule
- Every infrastructure file, CI pipeline stage, and deployment config

DO NOT write any code. DO NOT create any files. DO NOT modify anything.
This prompt is READ-ONLY.

────────────────────────────────────────────────────────────────

STEP 1 — ARCHITECTURE DOCUMENTS (read fully):

Read these reference documents that define what needs to be built:
  - EXECUTION_PROMPTS.md (the 25 detailed prompts you will execute in MACRO-2)
  - EXECUTION_CHECKLIST.md (track what to deliver)
  - TESTING_ARCHITECTURE.md (test strategy: pyramid, categories, patterns)
  - CICD_INFRASTRUCTURE.md (CI/CD + infra enhancement specs)
  - FINAL_VERIFICATION_REPORT.md (28/28 checks — understand what was built)
  - MODEL_ROLE_ARCHITECTURE.md (M1-M6 model enhancements, R1-R8 role fixes)

────────────────────────────────────────────────────────────────

STEP 2 — DATABASE & MODELS (read fully):

  backend/app/core/database.py
    → Map: Base, TimestampMixin, SchoolScopedMixin, NullableSchoolScopedMixin, SoftDeleteMixin
    → Note: is_deleted property, soft_delete(), restore()
    → Note: async engine setup, session factory

  backend/app/models/iam.py
    → Map ALL: User, Membership, UserSession, InvitationCode, ParentChildLink,
      StudentProfile, TeacherProfile, LoginHistory, PasswordHistory
    → List EVERY @validates method (email, phone, etc.)
    → List EVERY @property (is_active, has_2fa, is_email_verified, etc.)
    → List EVERY __repr__
    → Note ALL enums (UserStatus, RoleCode, etc.)

  backend/app/models/school.py
    → Map: School, SchoolStatus, all fields, preferences JSONB structure
    → List properties: is_active, is_subscription_valid

  backend/app/models/lms.py
    → Map ALL: Course, Assignment, Submission, Grade, GradeCategory,
      ContentItem, Assessment, Activity, ActivitySession,
      Quiz, QuizQuestion, QuizAttempt
    → List EVERY @validates, @property, __repr__
    → Note enums and relationships

  backend/app/models/erp.py
    → Map ALL: AcademicYear, Class, Enrollment, TeacherAssignment,
      AttendanceSession, AttendanceRecord, TimetableSlot
    → List EVERY @validates, @property

  backend/app/models/billing.py
    → Map ALL: Invoice, InvoiceItem, PaymentAttempt, FeeStructure,
      PaymentPlan, Installment, SiblingDiscount
    → List EVERY @validates, @property (is_overdue, is_paid, etc.)

  backend/app/models/com.py
    → Map: Notification, Conversation, Message, Announcement
    → Note SoftDeleteMixin on Notification, Conversation.is_group

  backend/app/models/documents.py
    → Map: Document, Resource, DocumentVersion
    → Note SoftDeleteMixin usage

  backend/app/models/calendar.py
    → Map: Event, EventRSVP
    → Note SoftDeleteMixin, is_past, is_all_day

  backend/app/models/reporting.py
    → Map: ReportJob, ReportSchedule
    → Note is_complete, is_expired

  backend/app/models/audit.py
    → Map: AuditLog, __repr__

────────────────────────────────────────────────────────────────

STEP 3 — DOMAIN LAYER (read fully):

  backend/app/domain/value_objects/grade.py → MoroccanGrade (constructor, value, mention)
  backend/app/domain/value_objects/money.py → Money (constructor, currency, arithmetic)
  backend/app/domain/value_objects/typed_id.py → UserId, SchoolId, etc.
  backend/app/domain/value_objects/role_set.py → RoleSet (has_role, iteration)
  backend/app/domain/events/ → all event classes (base, auth, billing, lms, erp, calendar, documents)
  backend/app/domain/protocols/ → evaluatable.py, grading.py

────────────────────────────────────────────────────────────────

STEP 4 — CORE INFRASTRUCTURE (read fully):

  backend/app/core/permissions.py (ALL 622+ lines)
    → Map: all 166 PERM_* constants
    → Map: PLATFORM_ROLES = {SUP, SYS, CONTENT_MGR}
    → Map: ROLE_HIERARCHY (SYS→SUP→ADM→DIR→TCH)
    → Map: get_effective_permissions() — recursive resolution with circular detection
    → Map: role_has_permission()
    → BUILD A MATRIX: for each of 8 roles, count direct + inherited permissions

  backend/app/core/abac.py (ALL)
    → Map: apply_owner_scope() — which roles bypass, which get filtered
    → Map: validate_parent_child_access() — checks ParentChildLink.status=="active"
    → Map: validate_teacher_class_access() — checks TeacherAssignment
    → Map: validate_student_teacher_access() — Enrollment × TeacherAssignment

  backend/app/core/security.py → token creation, verification, password hashing
  backend/app/core/config.py → all settings and environment variables
  backend/app/core/exceptions.py → all custom exception classes
  backend/app/core/response.py → standard response envelope format
  backend/app/core/middleware.py → correlation_id, timing, error handling
  backend/app/core/dependencies.py → FastAPI dependency injection (get_db, get_auth)
  backend/app/core/rate_limit.py → rate limiting logic
  backend/app/core/unit_of_work.py → UoW pattern
  backend/app/core/metrics.py → existing Prometheus metrics

────────────────────────────────────────────────────────────────

STEP 5 — SERVICES (read fully — every file):

  LMS Services:
    backend/app/services/lms/_helpers.py → LMSServiceBase, calculate_late_penalty(), MAX_FILES_PER_SUBMISSION
    backend/app/services/lms/_serializers.py → LMSSerializerMixin, all _*_to_dict methods
    backend/app/services/lms/grading_service.py → grade_submission(), override_late_penalty()
    backend/app/services/lms/assignment_service.py → create/list/upload/submit/finalize
    backend/app/services/lms/quiz_service.py → create/start_attempt/submit/generate_from_bank
    backend/app/services/lms/course_service.py → CRUD
    backend/app/services/lms/content_service.py → content management
    backend/app/services/lms/progress_service.py → progress tracking
    backend/app/services/lms/__init__.py → LMSService facade

  Core Services:
    backend/app/services/auth.py → login, impersonate, stop_impersonation, token_refresh, session mgmt
    backend/app/services/billing.py → generate_invoices, apply_late_fees, sibling discounts
    backend/app/services/payment_plan.py → create plan, record payment
    backend/app/services/school.py → CRUD, subscription
    backend/app/services/communication.py → conversations, messages, ABAC for STD/PAR
    backend/app/services/attendance_analytics.py → thresholds, rates, trends
    backend/app/services/timetable_generator.py → constraints, backtracking, preview, apply
    backend/app/services/gradebook.py → weighted averages, mentions, transcript
    backend/app/services/report_scheduler.py → schedule processing
    backend/app/services/rubric.py → rubric management
    backend/app/services/question_bank.py → question bank
    backend/app/services/analytics.py → analytics
    backend/app/services/audit.py → audit logging
    backend/app/services/event_dispatcher.py → domain events

────────────────────────────────────────────────────────────────

STEP 6 — REPOSITORIES (read method signatures — first 50 lines each):

  backend/app/repositories/base.py → BaseRepository CRUD pattern
  backend/app/repositories/auth.py
  backend/app/repositories/school.py
  backend/app/repositories/lms.py
  backend/app/repositories/quiz.py
  backend/app/repositories/billing.py
  backend/app/repositories/billing_enhancements.py
  backend/app/repositories/attendance_analytics.py
  backend/app/repositories/gradebook.py
  backend/app/repositories/messaging.py
  backend/app/repositories/notifications.py

────────────────────────────────────────────────────────────────

STEP 7 — API ENDPOINTS (read fully — map route × method × auth × permissions):

  backend/app/api/v1/router.py → all route registrations
  backend/app/api/v1/schools.py
  backend/app/api/v1/auth.py
  backend/app/api/v1/gradebook.py
  backend/app/api/v1/rubrics.py
  backend/app/api/v1/question_bank.py
  backend/app/api/v1/billing.py
  backend/app/api/v1/payments.py
  backend/app/api/v1/attendance.py
  backend/app/api/v1/attendance_analytics.py
  backend/app/api/v1/timetable.py
  backend/app/api/v1/timetable_generation.py
  backend/app/api/v1/messaging.py
  backend/app/api/v1/assignments.py
  backend/app/api/v1/submissions.py
  backend/app/api/v1/assessments.py
  backend/app/api/v1/quizzes.py
  backend/app/api/v1/courses.py
  backend/app/api/v1/classes.py
  backend/app/api/v1/enrollments.py

  For EACH endpoint, note:
  - HTTP method + path
  - Required role/permission
  - Request body schema
  - Response schema
  - Error status codes

────────────────────────────────────────────────────────────────

STEP 8 — EXISTING TESTS (read fully):

  backend/tests/conftest.py → existing fixtures, DB setup, auth helpers
  backend/tests/test_auth.py → existing auth tests
  backend/tests/test_rbac_security.py → existing RBAC matrix
  backend/tests/test_security_audit.py → existing security tests
  backend/tests/test_contract.py → existing contract tests
  backend/tests/test_unit_response.py → existing unit tests
  backend/tests/test_unit_iam.py → existing IAM unit tests
  All backend/tests/test_phase*.py → existing integration tests

  Count existing tests. Note coverage gaps.

────────────────────────────────────────────────────────────────

STEP 9 — INFRASTRUCTURE (read fully):

  .github/workflows/ci.yml → current 10-stage pipeline, all jobs
  infra/docker-compose.dev.yml → dev services
  infra/docker-compose.staging.yml → staging services
  infra/docker-compose.prod.yml → prod services, secrets, resources
  infra/docker-compose.monitoring.yml → Prometheus, Grafana, Loki, Promtail
  infra/nginx/nginx-prod.conf → TLS, rate limiting, security headers
  infra/prometheus/prometheus.yml + alert_rules.yml
  infra/loki/loki-config.yml + promtail-config.yml
  infra/alertmanager/alertmanager.yml
  infra/grafana/provisioning/datasources/datasources.yml
  infra/grafana/dashboards/*.json
  infra/postgres/init.sql
  infra/redis/redis.conf
  infra/scripts/deploy.sh + healthcheck.sh + ssl-renew.sh
  infra/backup/*.sh
  backend/Dockerfile + web/Dockerfile
  Makefile (all targets)
  .env.example
  backend/requirements.txt + requirements-dev.txt
  backend/pytest.ini or pyproject.toml

────────────────────────────────────────────────────────────────

STEP 10 — BUILD THE MAP:

After reading everything, produce these summary outputs (print to console):

OUTPUT 1 — MODEL MAP:
  For each model file: list models, validators count, properties count, mixins used
  Format: "iam.py: User(5v, 4p), Membership(1v, 1p), Session(0v, 3p) [SchoolScopedMixin]"

OUTPUT 2 — PERMISSION MATRIX:
  For each of 8 roles: count of direct permissions, inherited permissions, total
  Format: "SYS: 10 direct + 155 inherited = 165 total"

OUTPUT 3 — SERVICE METHOD MAP:
  For each service: list public methods with parameter count
  Format: "grading_service: grade_submission(4), override_late_penalty(3)"

OUTPUT 4 — ENDPOINT MAP:
  For each API router: count endpoints, list methods
  Format: "schools.py: 5 endpoints (POST, GET list, GET detail, PATCH, DELETE)"

OUTPUT 5 — TEST GAP ANALYSIS:
  Current test count, current coverage, files with 0% test coverage

OUTPUT 6 — INFRA STATUS:
  CI stages count, Docker services count, monitoring components, security features

PRINT ALL 6 OUTPUTS.
Then print: "MACRO-1 COMPLETE — Ready for MACRO-2 (Execute)"

════════════════════════════════════════════════════════════════
DO NOT WRITE ANY CODE. DO NOT CREATE ANY FILES. READ ONLY.
════════════════════════════════════════════════════════════════
```

---

## MACRO-2: EXECUTE ALL PROMPTS

```
═══════════════════════════════════════════════════════════════
MACRO PROMPT 2/3: EXECUTE ALL 25 PROMPTS SEQUENTIALLY
═══════════════════════════════════════════════════════════════

OBJECTIVE:
Execute the EXECUTE phase of ALL 25 prompts from EXECUTION_PROMPTS.md,
in order (T-01 → T-13, then CI-01 → CI-12).
Do NOT stop between prompts. Run continuously until all 25 are complete.

IMPORTANT RULES:
- Read EXECUTION_PROMPTS.md FIRST — it contains the full details for each prompt.
- You have already analyzed the codebase in MACRO-1. Do NOT re-read files
  unless you need to check a specific signature or field name.
- If a step fails, log the error, attempt a fix, and continue to the next step.
- If a fix is not possible, log "BLOCKED: <reason>" and continue.
- Do NOT stop execution for any reason until all 25 prompts are done.
- Do NOT run any git commands (user handles git himself).
- After EACH prompt's execute phase, print:
    "✓ [T-XX/CI-XX] DONE — [brief summary]"

ENVIRONMENT:
- Project root contains: backend/, web/, infra/, .github/, Makefile
- Python 3.12, Node 20, Docker available
- pip install uses --break-system-packages flag
- All new files go in their correct locations per EXECUTION_PROMPTS.md

────────────────────────────────────────────────────────────────

EXECUTION ORDER:

── PART 1: TESTING ────────────────────────────────────────────

PROMPT T-01: TEST INFRASTRUCTURE
  Read EXECUTION_PROMPTS.md → section "T-01"
  Execute ALL 14 steps:
    1. Create requirements-test.txt → install
    2. Create 12 directories with __init__.py
    3. Create factories/base.py (AsyncSQLAlchemyFactory)
    4. Create factories/iam.py (User, Membership, Session, InvitationCode, ParentChildLink)
    5. Create factories/school.py (School)
    6. Create factories/lms.py (Course, Assignment, Submission, Grade, Quiz)
    7. Create factories/erp.py (AcademicYear, Class, Enrollment, Attendance)
    8. Create factories/billing.py (Invoice, Payment, FeeStructure, Plan, Installment)
    9. Create factories/com.py (Notification, Conversation, Message)
    10. Create factories/documents.py (Document, Resource)
    11. Create factories/calendar.py (Event, RSVP)
    12. Update conftest.py (testcontainer + auth fixtures — DO NOT break existing)
    13. Update pyproject.toml (markers, coverage branch=true, fail_under=90)
    14. Add Makefile targets (test-unit, test-integration, test-security, test-full, test-perf)
  Print: "✓ [T-01] DONE — infrastructure: 9 factory files, conftest, config, Makefile targets"

PROMPT T-02: DOMAIN VALUE OBJECT TESTS
  Read EXECUTION_PROMPTS.md → section "T-02"
  Create 4 test files in backend/tests/unit/domain/:
    - test_grade.py (~15 tests: MoroccanGrade boundaries, mentions, parametrized)
    - test_money.py (~12 tests: MAD, EUR, USD, negative, decimal)
    - test_typed_id.py (~8 tests: UUID, validation, equality, hash)
    - test_role_set.py (~10 tests: membership, iteration, invalid codes)
  IMPORTANT: Match the REAL value object APIs found in the actual code.
  If a value object doesn't exist or has different methods, adapt tests accordingly.
  Print: "✓ [T-02] DONE — ~45 domain value object tests"

PROMPT T-03: MODEL VALIDATOR + PROPERTY TESTS
  Read EXECUTION_PROMPTS.md → section "T-03"
  Create 3 test files in backend/tests/unit/models/:
    - test_validators.py (~30 tests)
    - test_helper_properties.py (~25 tests, use freezegun for time)
    - test_repr.py (~10 tests)
  IMPORTANT: Only test validators and properties that ACTUALLY EXIST in the models.
  Print: "✓ [T-03] DONE — ~60 model validator + property tests"

PROMPT T-04: PERMISSION + ABAC TESTS
  Read EXECUTION_PROMPTS.md → section "T-04"
  Create 2 test files in backend/tests/unit/core/:
    - test_permissions.py (~25 tests: hierarchy, effective perms, parametrized matrix)
    - test_abac.py (~15 tests: owner scope, parent-child, teacher-class, student-teacher)
  Print: "✓ [T-04] DONE — ~40 permission + ABAC tests"

PROMPT T-05: LMS SERVICE TESTS
  Read EXECUTION_PROMPTS.md → section "T-05"
  Create 3 test files in backend/tests/unit/services/:
    - test_grading_service.py (~25 tests)
    - test_assignment_service.py (~20 tests)
    - test_quiz_service.py (~20 tests)
  All repos mocked with AsyncMock. Match REAL method signatures.
  Print: "✓ [T-05] DONE — ~65 LMS service tests"

PROMPT T-06: BILLING + AUTH + ATTENDANCE TESTS
  Read EXECUTION_PROMPTS.md → section "T-06"
  Create 3 test files:
    - test_billing_service.py (~25 tests)
    - test_auth_service.py (~20 tests)
    - test_attendance_service.py (~15 tests)
  Print: "✓ [T-06] DONE — ~60 billing + auth + attendance tests"

PROMPT T-07: COMMUNICATION + SCHOOL + OTHER TESTS
  Read EXECUTION_PROMPTS.md → section "T-07"
  Create 5 test files:
    - test_communication_service.py (~15 tests)
    - test_school_service.py (~10 tests)
    - test_timetable_service.py (~15 tests)
    - test_gradebook_service.py (~15 tests)
    - test_report_service.py (~10 tests)
  Print: "✓ [T-07] DONE — ~50 remaining service tests"

PROMPT T-08: API INTEGRATION TESTS
  Read EXECUTION_PROMPTS.md → section "T-08"
  Create 6 test files in backend/tests/integration/api/:
    - test_schools_api.py (~20 tests)
    - test_gradebook_api.py (~15 tests)
    - test_rubrics_api.py (~15 tests)
    - test_billing_api.py (~15 tests)
    - test_attendance_analytics_api.py (~10 tests)
    - test_timetable_api.py (~10 tests)
  Use testcontainer DB + factories. Real HTTP requests via httpx.AsyncClient.
  Print: "✓ [T-08] DONE — ~80 API integration tests"

PROMPT T-09: DB REPOSITORY TESTS
  Read EXECUTION_PROMPTS.md → section "T-09"
  Create 3 test files in backend/tests/integration/db/:
    - test_school_repo.py (~15 tests)
    - test_lms_repo.py (~15 tests)
    - test_billing_repo.py (~10 tests)
  Print: "✓ [T-09] DONE — ~40 repository integration tests"

PROMPT T-10: RBAC + ABAC SECURITY MATRIX
  Read EXECUTION_PROMPTS.md → section "T-10"
  Create 5 test files in backend/tests/security/:
    - test_rbac_matrix.py (~80 parametrized tests)
    - test_abac_parent_child.py (~15 tests)
    - test_abac_student_teacher.py (~15 tests)
    - test_abac_teacher_class.py (~10 tests)
    - test_permission_escalation.py (~10 tests)
  Print: "✓ [T-10] DONE — ~120 security tests"

PROMPT T-11: EDGE CASE TESTS
  Read EXECUTION_PROMPTS.md → section "T-11"
  Create 3 test files in backend/tests/edge/:
    - test_boundary_values.py (~30 tests)
    - test_time_dependent.py (~25 tests with freezegun)
    - test_error_paths.py (~25 tests)
  Print: "✓ [T-11] DONE — ~80 edge case tests"

PROMPT T-12: PERFORMANCE + CONTRACT TESTS
  Read EXECUTION_PROMPTS.md → section "T-12"
  Create 4 test files:
    - performance/test_benchmarks.py (~20 tests)
    - performance/test_load_patterns.py (~10 tests)
    - contract/test_api_contracts.py (~15 tests)
    - contract/test_migration_contracts.py (~5 tests)
  Print: "✓ [T-12] DONE — ~50 performance + contract tests"

PROMPT T-13: COVERAGE GAP FILL
  Read EXECUTION_PROMPTS.md → section "T-13"
  1. Run: cd backend && pytest --cov=app --cov-branch --cov-report=term-missing
  2. Identify files below 90% line / 85% branch
  3. Write targeted tests for uncovered paths
  4. Re-run coverage until targets met
  Print: "✓ [T-13] DONE — coverage gaps filled, [X]% line, [X]% branch"

── PART 2: CI/CD & INFRASTRUCTURE ─────────────────────────────

PROMPT CI-01: PRE-COMMIT HOOKS
  Read EXECUTION_PROMPTS.md → section "CI-01"
  Create .pre-commit-config.yaml, .secrets.baseline, Makefile target
  Print: "✓ [CI-01] DONE — pre-commit hooks configured"

PROMPT CI-02: CI PIPELINE HARDENING
  Read EXECUTION_PROMPTS.md → section "CI-02"
  Update .github/workflows/ci.yml: matrix, caching, security jobs, migration safety
  Add [tool.bandit] to pyproject.toml
  Print: "✓ [CI-02] DONE — CI pipeline hardened with matrix + security + migration safety"

PROMPT CI-03: DOCKER BUILD OPTIMIZATION
  Read EXECUTION_PROMPTS.md → section "CI-03"
  Rewrite backend/Dockerfile with BuildKit, cache mounts, multi-stage
  Print: "✓ [CI-03] DONE — Dockerfile optimized"

PROMPT CI-04: CONTAINER REGISTRY
  Read EXECUTION_PROMPTS.md → section "CI-04"
  Add publish-images job to ci.yml, create cleanup-images.yml
  Print: "✓ [CI-04] DONE — ghcr.io publishing + SBOM + cleanup"

PROMPT CI-05: PGBOUNCER
  Read EXECUTION_PROMPTS.md → section "CI-05"
  Add pgbouncer to prod/staging compose, update DATABASE_URL, add statement_cache_size=0
  Print: "✓ [CI-05] DONE — PgBouncer connection pooling"

PROMPT CI-06: READ REPLICA
  Read EXECUTION_PROMPTS.md → section "CI-06"
  Add replica to compose, create db_routing.py, add config
  Print: "✓ [CI-06] DONE — read replica + SQLAlchemy routing"

PROMPT CI-07: AUTOMATED BACKUPS
  Read EXECUTION_PROMPTS.md → section "CI-07"
  Create backup-s3.sh, restore-drill.sh, Makefile targets
  Print: "✓ [CI-07] DONE — S3 backups + restore drill"

PROMPT CI-08: OPENTELEMETRY APM
  Read EXECUTION_PROMPTS.md → section "CI-08"
  Add OTel deps, create telemetry.py, Tempo config, Grafana datasource
  Print: "✓ [CI-08] DONE — OpenTelemetry + Tempo tracing"

PROMPT CI-09: BUSINESS METRICS + LOG ALERTING
  Read EXECUTION_PROMPTS.md → section "CI-09"
  Create business_metrics.py, Grafana dashboard, Loki alert rules
  Print: "✓ [CI-09] DONE — education metrics + log alerts"

PROMPT CI-10: SECURITY HARDENING
  Read EXECUTION_PROMPTS.md → section "CI-10"
  Create rotate-secrets.sh, update nginx WAF, create dependabot.yml + automerge
  Print: "✓ [CI-10] DONE — secret rotation + WAF + Dependabot"

PROMPT CI-11: BLUE-GREEN DEPLOYMENT
  Read EXECUTION_PROMPTS.md → section "CI-11"
  Create blue/green compose files, deploy script, nginx upstream
  Print: "✓ [CI-11] DONE — blue-green deployment"

PROMPT CI-12: DEVELOPER ONBOARDING
  Read EXECUTION_PROMPTS.md → section "CI-12"
  Create seed_demo.py, dev-init/dev-reset targets, docs workflow
  Print: "✓ [CI-12] DONE — dev onboarding + API docs"

────────────────────────────────────────────────────────────────

FINAL OUTPUT:
Print a summary table:
  | # | Prompt | Status | Files Created | Tests Added |
  |---|--------|--------|--------------|-------------|
  | 1 | T-01   | ✓/✗    | ...          | ...         |
  ...
  | 25| CI-12  | ✓/✗    | ...          | ...         |

Print: "MACRO-2 COMPLETE — Ready for MACRO-3 (Verify)"

════════════════════════════════════════════════════════════════
DO NOT STOP UNTIL ALL 25 PROMPTS ARE EXECUTED.
IF A STEP FAILS, LOG IT AND CONTINUE.
════════════════════════════════════════════════════════════════
```

---

## MACRO-3: VERIFY EVERYTHING

```
═══════════════════════════════════════════════════════════════
MACRO PROMPT 3/3: VERIFY ALL WORK + FINAL VALIDATION
═══════════════════════════════════════════════════════════════

OBJECTIVE:
Run the VERIFY phase of ALL 25 prompts, then perform a comprehensive
final validation of the entire project. Fix any issues found.
At the end, produce a final status report.

IMPORTANT RULES:
- If a verification check fails, ATTEMPT TO FIX the issue immediately.
- After fixing, re-run the check to confirm it passes.
- If a fix is not possible, log "FAILED: <reason>" and continue.
- Do NOT stop until all checks are complete.
- Do NOT run any git commands (user handles git himself).

────────────────────────────────────────────────────────────────

PHASE A — TEST VERIFICATION (T-01 → T-13)
────────────────────────────────────────────────────────────────

CHECK T-01: Infrastructure
  1. cd backend && python -c "
     from tests.factories.base import AsyncSQLAlchemyFactory
     from tests.factories.iam import UserFactory, MembershipFactory
     from tests.factories.school import SchoolFactory
     from tests.factories.lms import CourseFactory, AssignmentFactory
     from tests.factories.erp import ClassFactory, EnrollmentFactory
     from tests.factories.billing import InvoiceFactory
     from tests.factories.com import NotificationFactory
     from tests.factories.documents import DocumentFactory
     from tests.factories.calendar import EventFactory
     print('ALL FACTORIES OK')
     "
  2. find backend/tests -type d | sort → verify all 12 directories exist
  3. grep "fail_under" backend/pyproject.toml → must show 90
  4. grep "test-unit\|test-integration\|test-security\|test-full\|test-perf" Makefile → all 5

  → Print: "T-01: [PASS/FAIL] — [details]"

CHECK T-02: Domain Tests
  cd backend && pytest tests/unit/domain/ -v --tb=short -q
  → Expect: ~45 tests pass
  → Print: "T-02: [PASS/FAIL] — [X] tests, [Y] passed, [Z] failed"

CHECK T-03: Model Tests
  cd backend && pytest tests/unit/models/ -v --tb=short -q
  → Expect: ~60 tests pass
  → Print: "T-03: [PASS/FAIL] — [X] tests, [Y] passed, [Z] failed"

CHECK T-04: Permission + ABAC Tests
  cd backend && pytest tests/unit/core/ -v --tb=short -q
  → Expect: ~40 tests pass
  → Print: "T-04: [PASS/FAIL] — [X] tests, [Y] passed, [Z] failed"

CHECK T-05: LMS Service Tests
  cd backend && pytest tests/unit/services/test_grading_service.py tests/unit/services/test_assignment_service.py tests/unit/services/test_quiz_service.py -v --tb=short -q
  → Expect: ~65 tests pass
  → Print: "T-05: [PASS/FAIL] — [X] tests"

CHECK T-06: Billing + Auth + Attendance Tests
  cd backend && pytest tests/unit/services/test_billing_service.py tests/unit/services/test_auth_service.py tests/unit/services/test_attendance_service.py -v --tb=short -q
  → Expect: ~60 tests pass
  → Print: "T-06: [PASS/FAIL] — [X] tests"

CHECK T-07: Remaining Service Tests
  cd backend && pytest tests/unit/services/test_communication_service.py tests/unit/services/test_school_service.py tests/unit/services/test_timetable_service.py tests/unit/services/test_gradebook_service.py tests/unit/services/test_report_service.py -v --tb=short -q
  → Expect: ~50 tests pass
  → Print: "T-07: [PASS/FAIL] — [X] tests"

CHECK T-08: API Integration Tests
  cd backend && pytest tests/integration/api/ -v --tb=short -q
  → Expect: ~80 tests pass (may require testcontainer — if unavailable, check imports only)
  → Print: "T-08: [PASS/FAIL] — [X] tests"

CHECK T-09: DB Repository Tests
  cd backend && pytest tests/integration/db/ -v --tb=short -q
  → Expect: ~40 tests
  → Print: "T-09: [PASS/FAIL] — [X] tests"

CHECK T-10: Security Tests
  cd backend && pytest tests/security/ -v --tb=short -q
  → Expect: ~120 tests
  → Print: "T-10: [PASS/FAIL] — [X] tests"

CHECK T-11: Edge Case Tests
  cd backend && pytest tests/edge/ -v --tb=short -q
  → Expect: ~80 tests
  → Print: "T-11: [PASS/FAIL] — [X] tests"

CHECK T-12: Performance + Contract Tests
  cd backend && pytest tests/performance/ tests/contract/ -v --tb=short -q
  → Expect: ~50 tests
  → Print: "T-12: [PASS/FAIL] — [X] tests"

CHECK T-13: Coverage
  cd backend && pytest --cov=app --cov-branch --cov-report=term-missing -q 2>&1 | grep TOTAL
  → Expect: ≥90% line, ≥85% branch
  → Print: "T-13: [PASS/FAIL] — [X]% line, [Y]% branch"

────────────────────────────────────────────────────────────────

PHASE B — CI/CD & INFRA VERIFICATION (CI-01 → CI-12)
────────────────────────────────────────────────────────────────

CHECK CI-01: Pre-commit
  1. python -c "import yaml; yaml.safe_load(open('.pre-commit-config.yaml'))" → valid
  2. python -c "import json; json.load(open('.secrets.baseline'))" → valid
  3. grep "hooks-install" Makefile → exists
  → Print: "CI-01: [PASS/FAIL]"

CHECK CI-02: CI Pipeline
  1. python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))" → valid
  2. grep "matrix" .github/workflows/ci.yml → exists
  3. grep "trivy\|pip-audit\|bandit" .github/workflows/ci.yml → all 3 found
  4. grep "migration-safety" .github/workflows/ci.yml → exists
  → Print: "CI-02: [PASS/FAIL]"

CHECK CI-03: Dockerfile
  1. head -1 backend/Dockerfile → must start with "# syntax="
  2. grep "^FROM" backend/Dockerfile → must show base, test, development, production
  3. grep "mount=type=cache" backend/Dockerfile → BuildKit cache mount exists
  → Print: "CI-03: [PASS/FAIL]"

CHECK CI-04: Container Registry
  1. grep "publish-images" .github/workflows/ci.yml → exists
  2. grep "ghcr.io" .github/workflows/ci.yml → exists
  3. test -f .github/workflows/cleanup-images.yml → exists
  → Print: "CI-04: [PASS/FAIL]"

CHECK CI-05: PgBouncer
  1. grep "pgbouncer" infra/docker-compose.prod.yml → exists
  2. grep "statement_cache_size" backend/app/core/database.py → exists
  3. docker compose -f infra/docker-compose.prod.yml config > /dev/null 2>&1 || echo "WARN: docker compose not available"
  → Print: "CI-05: [PASS/FAIL]"

CHECK CI-06: Read Replica
  1. test -f backend/app/core/db_routing.py → exists
  2. python -c "from app.core.db_routing import get_read_db, get_write_db" (from backend dir)
  3. grep "postgres-replica" infra/docker-compose.prod.yml → exists
  4. grep "DATABASE_REPLICA_URL" .env.example → exists
  → Print: "CI-06: [PASS/FAIL]"

CHECK CI-07: Backups
  1. test -x infra/scripts/backup-s3.sh → executable
  2. test -x infra/scripts/restore-drill.sh → executable
  3. bash -n infra/scripts/backup-s3.sh → syntax OK
  4. bash -n infra/scripts/restore-drill.sh → syntax OK
  5. grep "S3_BUCKET" .env.example → exists
  → Print: "CI-07: [PASS/FAIL]"

CHECK CI-08: OpenTelemetry
  1. test -f backend/app/core/telemetry.py → exists
  2. grep "opentelemetry" backend/requirements.txt → exists
  3. test -f infra/tempo/tempo.yml → exists
  4. grep "tempo" infra/docker-compose.monitoring.yml → exists
  5. grep "ENABLE_TRACING" .env.example → exists
  → Print: "CI-08: [PASS/FAIL]"

CHECK CI-09: Business Metrics
  1. test -f backend/app/core/business_metrics.py → exists
  2. python -c "from app.core.business_metrics import active_students, grade_distribution" (from backend)
  3. test -f infra/grafana/dashboards/business-education.json → exists
  4. python -c "import json; json.load(open('infra/grafana/dashboards/business-education.json'))" → valid
  5. test -f infra/loki/rules/ecole-alerts.yml → exists
  → Print: "CI-09: [PASS/FAIL]"

CHECK CI-10: Security
  1. test -x infra/scripts/rotate-secrets.sh → executable
  2. bash -n infra/scripts/rotate-secrets.sh → syntax OK
  3. test -f .github/dependabot.yml → exists
  4. test -f .github/workflows/dependabot-automerge.yml → exists
  5. grep "limit_req_zone.*jwt_sub\|sql.*injection\|WAF\|union.*select" infra/nginx/nginx-prod.conf → WAF rules present
  → Print: "CI-10: [PASS/FAIL]"

CHECK CI-11: Blue-Green
  1. test -f infra/docker-compose.blue.yml → exists
  2. test -f infra/docker-compose.green.yml → exists
  3. test -x infra/scripts/blue-green-deploy.sh → executable
  4. test -f infra/nginx/upstream.conf → exists
  5. grep "backend_active" infra/nginx/upstream.conf → exists
  → Print: "CI-11: [PASS/FAIL]"

CHECK CI-12: Developer Onboarding
  1. test -f backend/app/scripts/seed_demo.py → exists
  2. grep "dev-init\|dev-reset\|seed-demo" Makefile → all 3 exist
  3. test -f .github/workflows/docs.yml → exists
  4. grep "docs\b\|docs-schema" Makefile → both exist
  → Print: "CI-12: [PASS/FAIL]"

────────────────────────────────────────────────────────────────

PHASE C — GLOBAL VALIDATION
────────────────────────────────────────────────────────────────

GLOBAL-1: All existing tests still pass
  cd backend && pytest tests/ -x -q --timeout=120 2>&1 | tail -10
  → No failures from pre-existing tests

GLOBAL-2: No broken imports
  cd backend && python -c "
  import importlib, pkgutil
  failures = []
  for importer, modname, ispkg in pkgutil.walk_packages(['app'], prefix='app.'):
      try:
          importlib.import_module(modname)
      except Exception as e:
          failures.append(f'{modname}: {e}')
  if failures:
      print('IMPORT FAILURES:')
      for f in failures: print(f'  {f}')
  else:
      print('ALL IMPORTS OK')
  "

GLOBAL-3: No syntax errors in infrastructure files
  python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"
  python -c "import yaml; yaml.safe_load(open('infra/docker-compose.prod.yml'))" 2>/dev/null || echo "WARN: needs docker compose"
  bash -n infra/scripts/*.sh 2>&1

GLOBAL-4: Final test count
  cd backend && pytest --co -q 2>&1 | tail -3
  → Should show ~1,200+ tests collected

GLOBAL-5: Final coverage
  cd backend && pytest --cov=app --cov-branch --cov-report=term 2>&1 | grep "^TOTAL"
  → Line ≥90%, Branch ≥85%

────────────────────────────────────────────────────────────────

PHASE D — FIX FAILURES
────────────────────────────────────────────────────────────────

For each FAILED check from Phases A, B, C:
  1. Identify root cause
  2. Apply fix
  3. Re-run the specific check
  4. Print: "FIX [CHECK-ID]: [what was wrong] → [what was fixed] → [PASS/STILL FAILING]"

Repeat until all fixable issues are resolved.

────────────────────────────────────────────────────────────────

PHASE E — FINAL REPORT
────────────────────────────────────────────────────────────────

Print this exact format:

═══════════════════════════════════════════════════════════════
           ECOLE PLATFORM — FINAL VERIFICATION REPORT
═══════════════════════════════════════════════════════════════

TESTING:
  Total tests:        [number]
  Tests passing:      [number]
  Tests failing:      [number]
  Line coverage:      [X]%
  Branch coverage:    [X]%
  Target met:         [YES/NO]

  T-01 Infrastructure:  [PASS/FAIL]
  T-02 Domain tests:    [PASS/FAIL] ([X] tests)
  T-03 Model tests:     [PASS/FAIL] ([X] tests)
  T-04 Permission tests:[PASS/FAIL] ([X] tests)
  T-05 LMS tests:       [PASS/FAIL] ([X] tests)
  T-06 Billing/Auth:    [PASS/FAIL] ([X] tests)
  T-07 Other services:  [PASS/FAIL] ([X] tests)
  T-08 API integration: [PASS/FAIL] ([X] tests)
  T-09 DB repos:        [PASS/FAIL] ([X] tests)
  T-10 Security matrix: [PASS/FAIL] ([X] tests)
  T-11 Edge cases:      [PASS/FAIL] ([X] tests)
  T-12 Perf/Contract:   [PASS/FAIL] ([X] tests)
  T-13 Coverage fill:   [PASS/FAIL]

CI/CD & INFRASTRUCTURE:
  CI-01 Pre-commit:     [PASS/FAIL]
  CI-02 Pipeline:       [PASS/FAIL]
  CI-03 Dockerfile:     [PASS/FAIL]
  CI-04 Registry:       [PASS/FAIL]
  CI-05 PgBouncer:      [PASS/FAIL]
  CI-06 Read replica:   [PASS/FAIL]
  CI-07 Backups:        [PASS/FAIL]
  CI-08 APM:            [PASS/FAIL]
  CI-09 Metrics:        [PASS/FAIL]
  CI-10 Security:       [PASS/FAIL]
  CI-11 Blue-green:     [PASS/FAIL]
  CI-12 Onboarding:     [PASS/FAIL]

GLOBAL:
  Existing tests:     [PASS/FAIL]
  Import check:       [PASS/FAIL]
  Infra syntax:       [PASS/FAIL]

ISSUES REMAINING: [count]
  [list any unresolved issues]

═══════════════════════════════════════════════════════════════
MACRO-3 COMPLETE — ALL VERIFICATION DONE
═══════════════════════════════════════════════════════════════

════════════════════════════════════════════════════════════════
DO NOT STOP UNTIL THE FINAL REPORT IS PRINTED.
FIX EVERY FAILURE YOU CAN BEFORE REPORTING.
════════════════════════════════════════════════════════════════
```

---

## Usage Instructions

| Step | Prompt | What It Does | When to Run |
|------|--------|-------------|-------------|
| 1 | **MACRO-1** | Reads entire codebase, builds mental model, outputs maps | First — before any code |
| 2 | **MACRO-2** | Executes all 25 prompts (T-01→T-13 + CI-01→CI-12) | After MACRO-1 completes |
| 3 | **MACRO-3** | Verifies everything, fixes failures, prints final report | After MACRO-2 completes |

**For Codex**: Run MACRO-1, then MACRO-2, then MACRO-3. Codex will not stop within each macro.
**For Claude Code**: Same order, same behavior. Git commands are skipped automatically.

**Expected output after all 3 macros**:
- ~770 new tests (total ~1,200+)
- 90%+ line coverage, 85%+ branch coverage
- Hardened CI pipeline (matrix + security + migration safety)
- Full infra upgrades (PgBouncer, replica, backups, APM, blue-green, WAF)
- Developer onboarding (one-command setup + auto-docs)
