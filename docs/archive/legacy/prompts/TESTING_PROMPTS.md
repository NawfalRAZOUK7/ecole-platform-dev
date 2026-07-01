# Testing Prompts — Ecole Platform

> Execute to build the full professional test suite.
> Each prompt is self-contained. Run one at a time.
> Reference: TESTING_ARCHITECTURE.md

---

## Phase T-A: Test Infrastructure

### Prompt T-A1: Infrastructure Setup

```yaml
CONTEXT: Read TESTING_ARCHITECTURE.md sections "Test Infrastructure" and "Directory Structure".

TASK: Set up the test infrastructure: conftest, factories, configuration, directory structure.

STEPS:
1. Install new test dependencies — add to backend/requirements-test.txt (create if not exists):
   pytest-factoryboy==2.7.*
   testcontainers[postgres]==4.*
   pytest-xdist==3.5.*
   pytest-timeout==2.3.*
   pytest-mock==3.14.*
   respx==0.21.*
   freezegun==1.4.*
   hypothesis==6.100.*
   faker==24.*
   pytest-benchmark==4.0.*

2. Create the directory structure:
   backend/tests/factories/
   backend/tests/unit/
   backend/tests/unit/domain/
   backend/tests/unit/models/
   backend/tests/unit/core/
   backend/tests/unit/services/
   backend/tests/integration/
   backend/tests/integration/api/
   backend/tests/integration/db/
   backend/tests/security/
   backend/tests/edge/
   backend/tests/performance/
   backend/tests/contract/
   Add __init__.py to each directory.

3. Create backend/tests/factories/base.py:
   - AsyncSQLAlchemyFactory base class for factory_boy with async session support
   - Helper: create() classmethod that accepts a session and commits

4. Create backend/tests/factories/iam.py:
   - UserFactory (email, full_name, phone with +212, password_hash placeholder, status, school_id)
   - MembershipFactory (user SubFactory, role_code, status)
   - SessionFactory (user_id, token, expires_at, impersonator_id=None)
   - InvitationCodeFactory (code, role_code, school_id, max_uses, current_uses)
   - ParentChildLinkFactory (parent_user_id, child_user_id, status="active")
   - Use Faker("fr_FR") for Moroccan-appropriate data

5. Create backend/tests/factories/school.py:
   - SchoolFactory (name, code, city="Casablanca", timezone="Africa/Casablanca", default_language="fr", grading_scale="moroccan_20")

6. Create backend/tests/factories/lms.py:
   - CourseFactory, AssignmentFactory, SubmissionFactory, GradeFactory
   - QuizFactory, QuizQuestionFactory, QuizAttemptFactory

7. Create backend/tests/factories/erp.py:
   - AcademicYearFactory, ClassFactory, EnrollmentFactory
   - AttendanceSessionFactory, AttendanceRecordFactory

8. Create backend/tests/factories/billing.py:
   - InvoiceFactory, InvoiceItemFactory, PaymentAttemptFactory
   - FeeStructureFactory, PaymentPlanFactory, InstallmentFactory

9. Create backend/tests/factories/com.py:
   - NotificationFactory, ConversationFactory, MessageFactory

10. Create backend/tests/factories/documents.py:
    - DocumentFactory, ResourceFactory

11. Create backend/tests/factories/calendar.py:
    - EventFactory, EventRSVPFactory

12. Update backend/tests/conftest.py (or create new root conftest):
    - Add testcontainer PostgreSQL fixture (scope="session")
    - Add async engine fixture
    - Add db_session fixture with per-test rollback
    - Add AuthContext mock fixtures for each role (admin_auth, teacher_auth, student_auth, parent_auth)
    - Keep existing fixtures for backward compatibility

13. Update pyproject.toml with pytest configuration:
    - asyncio_mode = "auto"
    - markers: slow, security, performance, unit, integration
    - coverage: branch=true, source=["app"], fail_under=90

14. Add Makefile targets: test-unit, test-integration, test-security, test-full, test-perf

RULES:
- Do NOT run any git command.
- Do NOT break existing tests — new infrastructure is additive.
- Factories must use realistic Moroccan data (Faker fr_FR).
- All factory create() methods must be async-compatible.
```

---

## Phase T-B: Unit Tests — Domain, Models, Core

### Prompt T-B1: Domain Value Object Tests

```jl
CONTEXT: Read TESTING_ARCHITECTURE.md section "Category 1: Unit Tests — 1A".

TASK: Create comprehensive unit tests for all domain value objects.

STEPS:
1. Create backend/tests/unit/domain/test_grade.py:
   - Test MoroccanGrade(0) through MoroccanGrade(20) — valid
   - Test MoroccanGrade(-1), MoroccanGrade(21), MoroccanGrade(100) — ValueError
   - Test decimal grades (15.5, 10.25)
   - Test all 5 mention brackets: Très Bien (>=16), Bien (>=14), Assez Bien (>=12), Passable (>=10), Insuffisant (<10)
   - Test boundary values exactly at thresholds (10.0, 12.0, 14.0, 16.0)
   - Test equality and comparison operators if implemented
   ~15 tests

2. Create backend/tests/unit/domain/test_money.py:
   - Test Money(100, "MAD") — valid
   - Test Money(-1, "MAD") — ValueError for negative
   - Test Money(0, "MAD") — valid edge case
   - Test currency validation (MAD valid, XXX invalid)
   - Test arithmetic if implemented (add, subtract)
   ~12 tests

3. Create backend/tests/unit/domain/test_typed_id.py:
   - Test UserId creation with valid UUID
   - Test SchoolId creation with valid UUID
   - Test invalid inputs
   ~8 tests

4. Create backend/tests/unit/domain/test_role_set.py:
   - Test RoleSet with valid roles (ADM, DIR, TCH, etc.)
   - Test RoleSet with invalid role codes — ValueError
   - Test membership checks (has_role, is_admin, etc.)
   ~10 tests

RULES:
- Pure unit tests — no DB, no async, no mocking needed.
- Use pytest.mark.parametrize for boundary value tests.
- Do NOT run any git command.
```

### Prompt T-B2: Model Validator + Property Tests

```yaml
CONTEXT: Read TESTING_ARCHITECTURE.md sections "1C" and "M3 Helper Properties".

TASK: Test all SQLAlchemy validators and helper properties on models.

STEPS:
1. Create backend/tests/unit/models/test_validators.py:
   - TestUserValidators: email (lowercase, strip, @ required), phone (+prefix, normalize)
   - TestGradeValidators: score (0-20), late_penalty (>=0)
   - TestInvoiceValidators: total (>=0), currency (MAD/EUR/USD)
   - TestAssignmentValidators: max_score (>0 if exists as total_points), late_penalty_per_day (0-100)
   - TestGradeCategoryValidators: weight (0-1)
   - TestResourceRatingValidators: rating (1-5)
   - TestInstallmentValidators: amount (>0)
   - TestSiblingDiscountValidators: discount_percent (0-100)
   Each validator: test valid values, boundary values, and invalid values that should raise ValueError.
   ~60 tests

2. Create backend/tests/unit/models/test_helper_properties.py:
   - Test User.is_active with active/inactive/suspended statuses
   - Test User.has_2fa with and without totp_secret
   - Test User.is_email_verified with and without email_verified_at
   - Test Session.is_expired with future/past expires_at (use freezegun)
   - Test Session.is_impersonated with/without impersonator_id
   - Test Session.is_revoked with/without revoked_at
   - Test Invoice.is_overdue with sent+past_due, sent+future_due, paid
   - Test Invoice.is_paid with paid/sent/draft statuses
   - Test Assignment.is_past_due with past/future due dates
   - Test Submission.is_graded with/without graded_at
   - Test Enrollment.is_active with active/withdrawn statuses
   - Test SoftDeleteMixin.is_deleted with/without deleted_at
   - Test School.is_active (active + not deleted)
   - Test School.is_subscription_valid (expired, valid, no expiry)
   ~40 tests

3. Create backend/tests/unit/models/test_repr.py:
   - Test User.__repr__ contains id[:8] and email, NOT password_hash
   - Test School.__repr__ contains name and status
   - Test Invoice.__repr__ does not contain sensitive data
   - Spot-check 5-10 models for correct repr format
   ~15 tests

RULES:
- For time-dependent properties, use freezegun.
- Model instances can be created without DB — just set attributes manually.
- Do NOT run any git command.
```

### Prompt T-B3: Permission + ABAC Unit Tests

```yaml
CONTEXT: Read TESTING_ARCHITECTURE.md sections "1D" and "Category 3".

TASK: Test role hierarchy, effective permissions, and ABAC helper functions.

STEPS:
1. Create backend/tests/unit/core/test_permissions.py:
   - Test get_effective_permissions for each role (8 roles)
   - Test hierarchy inheritance: DIR gets all TCH perms
   - Test hierarchy inheritance: ADM gets all DIR+TCH perms
   - Test hierarchy inheritance: SUP gets all ADM+DIR+TCH perms
   - Test STD does NOT inherit from TCH
   - Test PAR does NOT inherit from any hierarchy
   - Test CONTENT_MGR is not in hierarchy (lateral)
   - Test specific permission checks with role_has_permission()
   - Test PLATFORM_ROLES constant contains SUP, SYS, CONTENT_MGR
   - Test circular hierarchy detection (ValueError)
   ~25 tests

2. Create backend/tests/unit/core/test_abac.py:
   - Test apply_owner_scope with ADM role → no filter applied
   - Test apply_owner_scope with TCH role → teacher_field filter
   - Test apply_owner_scope with PAR role → parent_field filter
   - Test apply_owner_scope with STD role → student_field filter
   - Test apply_owner_scope with custom admin_roles
   - Test apply_owner_scope with None fields → falls back to owner_field
   ~15 tests

3. Create backend/tests/unit/core/test_role_hierarchy.py:
   - Parametrized test: for each (role, permission, expected_bool) tuple
   - Cover: TCH direct perms, DIR inherited perms, ADM inherited, SUP inherited
   - Cover: STD cannot access TCH perms, PAR cannot access TCH perms
   - Cover: new permissions from R1 (DIR billing), R5 (SUP cross-school)
   ~30 tests using @pytest.mark.parametrize

RULES:
- No DB needed for permission tests (pure function).
- ABAC apply_owner_scope tests can use mock Select objects.
- Do NOT run any git command.
```

---

## Phase T-C: Unit Tests — Services

### Prompt T-C1: LMS Service Unit Tests

```yaml
CONTEXT: Read TESTING_ARCHITECTURE.md "1B Service Unit Tests".

TASK: Create unit tests for LMS services (grading, assignment, quiz) with mocked repositories.

STEPS:
1. Create backend/tests/unit/services/test_grading_service.py (~25 tests):
   - Mock: LMSRepository, AuditService, EventDispatcher
   - Test grade_submission: valid score → grade created
   - Test grade_submission: score exceeds total_points → ValidationError
   - Test grade_submission: submission not found → NotFoundError
   - Test grade_submission: wrong teacher → AuthorizationError
   - Test grade_submission: rubric assignment → ValidationError (use rubric endpoint)
   - Test grade_submission: late penalty applied correctly
   - Test grade_submission: update existing grade
   - Test grade_submission: publish triggers event dispatch
   - Test override_late_penalty: restores original score
   - Test override_late_penalty: no penalty → ValidationError
   - Test override_late_penalty: already overridden → returns current
   - Test calculate_late_penalty: all scenarios from TESTING_ARCHITECTURE.md

2. Create backend/tests/unit/services/test_assignment_service.py (~20 tests):
   - Test create_assignment: valid → assignment dict returned
   - Test create_assignment: course not found → NotFoundError
   - Test create_assignment: not course teacher → AuthorizationError
   - Test upload_exercise_pdf: valid PDF → saved
   - Test upload_exercise_pdf: non-PDF → ValidationError
   - Test upload_exercise_pdf: not PRINTABLE_PDF type → ValidationError
   - Test create_submission: new → created with correct status
   - Test create_submission: existing → returns existing
   - Test finalize_submission: draft → submitted
   - Test finalize_submission: already submitted → ValidationError
   - Test upload_submission_file: max files exceeded → ValidationError

3. Create backend/tests/unit/services/test_quiz_service.py (~20 tests):
   - Test create_quiz: valid → created
   - Test start_attempt: first attempt → created
   - Test start_attempt: max attempts exceeded → ValidationError
   - Test start_attempt: quiz not published → ValidationError
   - Test submit_attempt: auto-grading calculates score
   - Test submit_attempt: time limit exceeded
   - Test generate_quiz_from_bank: correct question selection

RULES:
- Use unittest.mock.AsyncMock for all repository methods.
- Use MagicMock for model instances returned by repos.
- Each test must be isolated — no shared state between tests.
- Do NOT run any git command.
```

### Prompt T-C2: Billing + Auth Service Unit Tests

```yaml
CONTEXT: Read TESTING_ARCHITECTURE.md "1B Service Unit Tests".

TASK: Create unit tests for billing, attendance, and auth services.

STEPS:
1. Create backend/tests/unit/services/test_billing_service.py (~25 tests):
   - Test generate_invoices: standard invoice created
   - Test generate_invoices: sibling discount applied (2nd child gets X%)
   - Test generate_invoices: sibling discount not applied for single child
   - Test apply_late_fees: overdue invoice → fee added
   - Test apply_late_fees: paid invoice → no fee
   - Test apply_late_fees: already has max fees → capped
   - Test create_payment_plan: valid installments created
   - Test create_payment_plan: total matches invoice amount
   - Test record_installment_payment: marks paid, checks plan completion
   - Test validate currency is MAD

2. Create backend/tests/unit/services/test_attendance_service.py (~15 tests):
   - Test check_thresholds_and_alert: below warning → no alert
   - Test check_thresholds_and_alert: at warning → warning alert created
   - Test check_thresholds_and_alert: at critical → critical alert + event dispatched
   - Test compute_attendance_rate: various scenarios
   - Test attendance_trends: correct period grouping

3. Create backend/tests/unit/services/test_auth_service.py (~20 tests):
   - Test login: valid credentials → tokens + LoginHistory created
   - Test login: invalid password → LoginHistory with failure
   - Test login: new device → is_new_device=True + event dispatched
   - Test login: session limit reached → oldest revoked
   - Test impersonate: admin → shadow session created
   - Test impersonate: non-admin → AuthorizationError
   - Test impersonate: same school only
   - Test stop_impersonation: revokes shadow session
   - Test token_refresh: valid → new tokens
   - Test token_refresh: expired → error

RULES:
- Mock all DB interactions.
- Use freezegun for date-dependent billing logic.
- Do NOT run any git command.
```

### Prompt T-C3: Communication + School + Other Service Tests

```yaml
CONTEXT: Read TESTING_ARCHITECTURE.md.

TASK: Create unit tests for remaining services.

STEPS:
1. Create backend/tests/unit/services/test_communication_service.py (~15 tests):
   - Test create_conversation: STD → validates student-teacher relationship
   - Test create_conversation: STD → rejects GROUP type
   - Test create_conversation: STD → rejects unrelated teacher (ABAC)
   - Test create_conversation: PAR → validates parent-child link
   - Test create_conversation: TCH → allowed freely
   - Test send_message: valid → message created
   - Test search_messages: returns filtered results

2. Create backend/tests/unit/services/test_school_service.py (~10 tests):
   - Test create_school: valid → created with defaults (Africa/Casablanca, fr, moroccan_20)
   - Test create_school: duplicate code → error
   - Test update_school: subscription fields updated
   - Test deactivate_school: soft delete applied
   - Test get_school: SUP sees any, ADM sees own only

3. Create backend/tests/unit/services/test_timetable_service.py (~15 tests):
   - Test constraint validation: no overlaps
   - Test preview: returns slots without committing
   - Test apply: creates real timetable rows
   - Test generation: respects teacher availability constraints
   - Test generation: handles 20 classes within time limit

4. Create backend/tests/unit/services/test_gradebook_service.py (~15 tests):
   - Test weighted_average: weights sum to 1.0
   - Test weighted_average: handles missing grades
   - Test moroccan_mention: correct mention for each bracket
   - Test class_averages: correct aggregation
   - Test transcript: all periods included

5. Create backend/tests/unit/services/test_report_service.py (~10 tests):
   - Test process_due_schedules: triggers report generation
   - Test report format validation
   - Test schedule creation with cron expression

RULES:
- Mock all DB interactions.
- Do NOT run any git command.
```

---

## Phase T-D: Integration Tests

### Prompt T-D1: API Integration Tests

```yaml
CONTEXT: Read TESTING_ARCHITECTURE.md "Category 2: Integration Tests".

TASK: Create API integration tests for all new endpoints.

STEPS:
1. Create backend/tests/integration/api/test_schools_api.py (~20 tests):
   - POST /schools: SUP creates → 201
   - POST /schools: ADM creates → 403
   - POST /schools: duplicate code → 409
   - GET /schools: SUP sees all
   - GET /schools: ADM sees own school only
   - GET /schools/{id}: valid → 200
   - PATCH /schools/{id}: update name → 200
   - DELETE /schools/{id}: soft delete → 204

2. Create backend/tests/integration/api/test_gradebook_api.py (~15 tests)
3. Create backend/tests/integration/api/test_rubrics_api.py (~15 tests)
4. Create backend/tests/integration/api/test_billing_enhancements_api.py (~15 tests)
5. Create backend/tests/integration/api/test_attendance_analytics_api.py (~10 tests)
6. Create backend/tests/integration/api/test_timetable_api.py (~10 tests)

Each test file follows the pattern:
- Create test data using factories
- Make HTTP request with appropriate auth token
- Assert status code, response schema, and data correctness

RULES:
- Use the testcontainer DB from conftest.
- Use factories to create test data.
- Test both happy path and error paths.
- Do NOT run any git command.
```

### Prompt T-D2: Database Repository Integration Tests

```yaml
CONTEXT: Read TESTING_ARCHITECTURE.md.

TASK: Create repository integration tests against real PostgreSQL.

STEPS:
1. Create backend/tests/integration/db/test_school_repo.py (~15 tests):
   - Test CRUD operations
   - Test pagination with cursor
   - Test soft delete + restore
   - Test unique constraint on code

2. Create backend/tests/integration/db/test_lms_repo.py (~15 tests):
   - Test assignment creation with FK constraints
   - Test grade creation with submission FK
   - Test pagination with filters
   - Test SchoolScopedMixin filtering

3. Create backend/tests/integration/db/test_billing_repo.py (~10 tests):
   - Test invoice with items
   - Test sibling query (get_siblings)
   - Test payment plan with installments

RULES:
- Use real async session from testcontainer.
- Test FK constraints, unique constraints, cascade deletes.
- Do NOT run any git command.
```

---

## Phase T-E: Security Tests

### Prompt T-E1: RBAC + ABAC Security Matrix

```yaml
CONTEXT: Read TESTING_ARCHITECTURE.md "Category 3: Security Tests".

TASK: Create comprehensive RBAC matrix and ABAC validation tests.

STEPS:
1. Create backend/tests/security/test_rbac_matrix.py (~80 tests):
   - For each NEW endpoint group (schools, gradebook, rubrics, question-bank, payment-plans, attendance-analytics, timetable-generation):
   - Test each endpoint × each role (8 roles)
   - Expected: 401 (no token), 403 (wrong role), 200/201 (correct role)
   - Use @pytest.mark.parametrize for the matrix

2. Create backend/tests/security/test_abac_parent_child.py (~15 tests):
   - PAR with valid link → 200
   - PAR without link → 403
   - PAR with inactive link → 403
   - Test across: grades, attendance, billing, notifications, documents

3. Create backend/tests/security/test_abac_student_teacher.py (~15 tests):
   - STD messages teacher of enrolled class → 200
   - STD messages unrelated teacher → 403
   - STD creates group conversation → 400

4. Create backend/tests/security/test_abac_teacher_class.py (~10 tests):
   - TCH grades own course → 200
   - TCH grades other teacher's course → 403

5. Create backend/tests/security/test_permission_escalation.py (~10 tests):
   - STD cannot access ADM endpoints
   - PAR cannot impersonate
   - TCH cannot manage school
   - Test each critical permission boundary

RULES:
- Each test must be explicit about expected status code.
- Use deny ordering convention: 401 → 403 → 404.
- Do NOT run any git command.
```

---

## Phase T-F: Edge Case + Performance + Contract Tests

### Prompt T-F1: Edge Case + Boundary Tests

```yaml
CONTEXT: Read TESTING_ARCHITECTURE.md "Category 4: Edge Case Tests".

TASK: Create edge case, boundary value, and time-dependent tests.

STEPS:
1. Create backend/tests/edge/test_boundary_values.py (~30 tests):
   - Grade score exactly 0, exactly 20, 0.01, 19.99
   - Invoice total 0, large number (999999.99)
   - Discount percent 0, 100
   - Empty strings for email, phone, name
   - Max-length strings (255, 500 chars)
   - Unicode names (Arabic: "أحمد", French: "François")
   - Pagination: limit=0, limit=1000, cursor=invalid

2. Create backend/tests/edge/test_time_dependent.py (~25 tests):
   - Use @freeze_time for all tests
   - Session expiration at exact boundary
   - Assignment due date at midnight Africa/Casablanca
   - Invoice due date + grace period
   - Subscription expiration
   - Academic year transitions
   - Late penalty calculation at day boundaries

3. Create backend/tests/edge/test_error_paths.py (~25 tests):
   - Not found: every entity type (user, course, assignment, invoice, etc.)
   - Duplicate creation: invitation code, school code, enrollment
   - Invalid state transitions: grading a draft submission
   - Cascade effects: deleting a course with assignments
   - Empty results: listing with no matching records

RULES:
- Use freezegun for all time tests.
- Use pytest.raises for expected exceptions.
- Do NOT run any git command.
```

### Prompt T-F2: Performance + Contract Tests

```yaml
CONTEXT: Read TESTING_ARCHITECTURE.md sections 5 and 6.

TASK: Create performance benchmarks and API contract tests.

STEPS:
1. Create backend/tests/performance/test_benchmarks.py (~20 tests):
   - Benchmark get_effective_permissions for all roles (target: <1ms)
   - Benchmark apply_owner_scope query building (target: <1ms)
   - Benchmark MoroccanGrade creation (target: <0.1ms)
   - Benchmark role_has_permission (target: <0.5ms)
   - Benchmark calculate_late_penalty (target: <0.5ms)
   Mark all with @pytest.mark.performance

2. Create backend/tests/performance/test_load_patterns.py (~10 tests):
   - 100 concurrent permission checks
   - Batch grade creation (40 at once)
   - Paginate 1000 records
   Mark all with @pytest.mark.slow

3. Create backend/tests/contract/test_api_contracts.py (~15 tests):
   - Validate response envelopes match schema for each endpoint
   - Validate error responses have correct format
   - Validate pagination response has cursor + has_more

4. Create backend/tests/contract/test_migration_contracts.py (~5 tests):
   - All migration files have both upgrade() and downgrade()
   - No duplicate revision IDs
   - Enum values in migrations match Python enum classes

RULES:
- Use pytest-benchmark for benchmark tests.
- Mark slow tests with @pytest.mark.slow.
- Do NOT run any git command.
```

---

## Phase T-G: Coverage Gap Fill + Validation

### Prompt T-G1: Coverage Analysis + Gap Fill

```yaml
CONTEXT: All previous test phases (T-A through T-F) are complete.

TASK: Run coverage analysis, identify remaining gaps, and write tests to reach 90%+.

STEPS:
1. Run: pytest --cov=app --cov-branch --cov-report=html --cov-report=term-missing
2. Analyze coverage report — identify files below 90%.
3. For each under-covered file, write targeted tests:
   - Focus on untested branches (if/else paths)
   - Focus on error handlers and edge cases
   - Focus on any untested service methods
4. Re-run coverage until app/ reaches 90%+ line coverage and 85%+ branch coverage.
5. Generate final coverage report.

RULES:
- Only write tests for real gaps — no padding with trivial tests.
- Focus on branch coverage (the harder metric).
- Do NOT run any git command.
- Report final coverage numbers in a summary table.
```
