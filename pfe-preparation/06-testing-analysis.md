# Step 6 — Testing Analysis

> Extracted from implemented test code in `backend/tests/`, `web/e2e/`, `web/playwright.config.ts`, and `.github/workflows/ci.yml`.

---

## 1. Test Suite Inventory

| Category | Directory | Files | LOC | Test Functions |
|---|---|---|---|---|
| Unit Tests | `tests/unit/` | 24 | ~11,668 | ~450 |
| Unit Tests (legacy) | `tests/test_unit_*.py` | 2 | ~484 | ~30 |
| Integration Tests | `tests/integration/` | 22 | ~6,038 | ~200 |
| Integration Tests (legacy) | `tests/test_phase*.py`, `test_auth.py` | 14 | ~5,200 | ~180 |
| Security Tests | `tests/security/` | 12 | ~2,935 | ~130 |
| Security Tests (legacy) | `test_rbac_security.py`, `test_security_audit.py` | 2 | ~1,149 | ~60 |
| Edge / Boundary Tests | `tests/edge/` | 9 | ~2,141 | ~80 |
| Contract Tests | `tests/contract/` | 2 | ~268 | ~25 |
| Performance Tests | `tests/performance/` | 2 | ~265 | ~15 |
| Test Factories | `tests/factories/` | 17 | ~1,808 | — |
| E2E Tests (Playwright) | `web/e2e/` | 17 | ~4,170 | ~60 |
| **Total** | | **119 files** | **~33,759** (backend) + **~4,170** (E2E) | **~1,339** |

Total: **119 backend test files**, **17 E2E spec files**, **~37,929 LOC** of test code, **~1,339 backend test functions**.

---

## 2. Test Architecture & Organization

### 2.1 Directory Structure

The test suite is organized in two layers. The modern structured layout uses `tests/unit/`, `tests/integration/`, `tests/security/`, `tests/edge/`, `tests/contract/`, and `tests/performance/` subdirectories. A legacy layer at `tests/test_*.py` contains phase-specific test files that were written during initial development and run as integration tests in CI.

Both layers coexist — CI runs both modern and legacy suites. The legacy files test specific features (auth, WebSocket, uploads, filters, background tasks, notifications, reports, calendar, documents) while the structured directories organize by test type.

### 2.2 Test Frameworks & Tools

**Backend (Python)**:
- `pytest` as the core test runner with async support via `pytest-asyncio`
- `httpx.AsyncClient` for HTTP-level integration testing (both against live servers and ASGI transport)
- `testcontainers` (PostgresContainer) for disposable database instances in integration tests
- `unittest.mock.AsyncMock` for service-layer mocking in unit tests
- `factory_boy` with async SQLAlchemy factories for test data generation
- `Faker` (French locale `fr_FR`) for realistic Moroccan test data
- `pytest-benchmark` for performance benchmarks
- `coverage.py` for code coverage measurement
- `ruff` for lint-as-test in Docker build stage

**Frontend (TypeScript)**:
- Playwright for browser-based E2E testing
- Chromium-only in CI (`npx playwright install --with-deps chromium`)
- Mock API layer (`mockApi.ts`) for session simulation

**Load Testing**:
- k6 (Grafana) with 4 scenarios: login flows, GET requests, file uploads, WebSocket connections

---

## 3. Test Fixture Architecture

### 3.1 Root conftest.py — Shared Fixtures

The root `conftest.py` (374 lines) provides the foundation for all integration-style tests:

**Seed-based Authentication**: Fixtures `admin_token`, `teacher_token`, `student_token`, `parent_token` each call `_login_with_seed_retry()` which authenticates against the live API using pre-seeded accounts. If login fails (401), it automatically re-seeds the database via Docker exec or direct `python -m app.seed`, then retries. This makes tests resilient to database state drift.

**AuthContext Fixtures**: `admin_auth`, `teacher_auth`, `student_auth`, `parent_auth`, `sup_auth` create mock `AuthContext` objects for unit tests without needing a live server — each receives the correct role permissions via `get_permissions_for_role()`.

**Disposable Database**: The `postgres_url` fixture uses `testcontainers.PostgresContainer("postgres:16-alpine")` to spin up a fresh PostgreSQL instance per test session. The `engine` fixture creates all tables via `Base.metadata.create_all`, and `db_session` wraps each test in a rollback-only transaction — ensuring test isolation without database teardown overhead.

**Redis Hygiene**: Two autouse fixtures manage Redis state. `clear_analytics_cache` cleans known key patterns (analytics, rate limits, login attempts, notification counts, idempotency keys) before and after each test. `override_test_redis` monkeypatches 7 modules to use the authenticated test Redis instance. Both fixtures skip for unit tests via path detection (`"unit" in path.parts`).

**PostgreSQL Enum Bootstrapping**: `_create_postgres_enum_types()` introspects all SQLAlchemy models and creates PostgreSQL enum types before `Base.metadata.create_all` — necessary because models use `create_type=False` for explicit control.

### 3.2 Integration conftest.py — Full Context Setup

The `tests/integration/conftest.py` (291 lines) extends the root with:

**ASGI Transport**: Instead of hitting a live server, integration tests use `httpx.ASGITransport(app=app)` — the FastAPI application runs in-process. The `get_db` dependency is overridden with the test session factory, providing full database isolation per test.

**api_context Fixture**: Creates a complete school ecosystem via factories — school, academic year, period, class, and 7 actors (admin, teacher, parent, student, 2 peer students, content manager). Each actor gets a real JWT via `create_access_token()`. Parent-child links and enrollments are established. Teacher assignment is created. This single fixture provides all relationships needed for RBAC, ABAC, and cross-role tests.

**Level-Age Mapping Seed**: An autouse fixture (`seed_level_mappings`) inserts the 13 Moroccan education levels (maternelle through terminale) with trilingual labels — required because integration tests use `create_all` instead of Alembic migrations which carry this seed data.

### 3.3 Test Factory System

17 factory modules in `tests/factories/` (1,808 LOC) implement async SQLAlchemy factories via `factory_boy`. The base class `AsyncSQLAlchemyFactory` handles async session management. Domain-specific factories include:

- **IAM**: `UserFactory`, `MembershipFactory`, `SessionFactory`, `ParentChildLinkFactory`, `InvitationCodeFactory` — Moroccan phone format (`+2126...`), French Faker locale
- **ERP**: `AcademicYearFactory`, `ClassFactory`, `EnrollmentFactory`, `PeriodFactory`
- **LMS**: Assignment, course, submission factories
- **Billing**: Invoice, fee structure, budget, financial health factories
- **Games/Rewards**: Game configuration, reward factories
- **School**: SchoolFactory with Casablanca defaults
- **Specialized**: Compliance, micro-school, skill passport, sync queue, calendar, documents factories

---

## 4. Unit Test Analysis

### 4.1 Service Layer Tests

16 unit test files in `tests/unit/services/` test service-layer logic with mocked dependencies:

- `test_auth_service.py`: Tests login flow, rate limiting, device fingerprinting, session management, impersonation. Uses `FakeRedis` and `FakePipeline` classes that simulate Redis behavior (incr, expire, get, setex, pipeline execute) without a live Redis instance. Tests `AsyncMock` UnitOfWork, verifying that service methods correctly call commit/rollback.

- `test_billing_service.py`: Fee structure creation, invoice generation, sibling discount computation, payment lifecycle.

- `test_grading_service.py`: Late penalty calculations, Moroccan 0-20 grade normalization, penalty overrides.

- `test_communication_service.py`: ABAC validation per role pair, message sending, conversation types.

- `test_budget_service.py`, `test_financial_health_service.py`, `test_compliance_service.py`: Financial module tests.

- `test_timetable_service.py`, `test_attendance_service.py`: ERP scheduling and attendance logic.

- `test_quiz_service.py`, `test_assignment_service.py`, `test_gradebook_service.py`: LMS assessment and grading workflows.

- `test_skill_passport_service.py`, `test_micro_school_service.py`, `test_sync_service.py`: Specialized domain tests.

### 4.2 Domain Value Object Tests

5 test files in `tests/unit/domain/`:

- `test_money.py`: Validates the Money value object — MAD/EUR/USD currencies, negative amount rejection, decimal precision preservation, `from_float` quantization to 2 decimals, arithmetic operations (add/subtract same currency), currency mismatch detection.

- `test_grade.py`: MoroccanGrade value object — 0-20 scale boundaries, `from_float` conversion, `average()` computation, empty list error handling.

- `test_typed_id.py`: Typed UUID wrappers for domain safety.

- `test_role_set.py`: Role set operations and permission membership.

- `test_value_object_additional.py`: Extended value object edge cases.

### 4.3 Core Module Tests

4 test files in `tests/unit/core/`:

- `test_abac.py`: ABAC scope application — owner scope filtering, role-based query scoping.
- `test_permissions.py`: Permission matrix validation — each role has exactly the expected set of permissions.
- `test_jwt_rotation.py`: JWT token creation and validation with key rotation scenarios.
- `test_exceptions_additional.py`: Exception hierarchy and error code mapping.

### 4.4 Model Tests

4 test files in `tests/unit/models/`:

- `test_validators.py`: Pydantic model validators — field constraints, type coercion, validation errors.
- `test_repr.py`: Model `__repr__` methods for debugging.
- `test_helper_properties.py`: Computed properties on SQLAlchemy models.
- `test_additional_repr.py`: Extended model representation tests.

---

## 5. Integration Test Analysis

### 5.1 API Integration Tests

12 test files in `tests/integration/api/` test full request→response cycles through the ASGI application:

- `test_billing_api.py`: Fee structure CRUD, invoice generation, payment initiation, webhook processing.
- `test_gradebook_api.py`: Gradebook retrieval per class and period, role-based view differences.
- `test_timetable_api.py`: Timetable management, conflict detection, role-adaptive views.
- `test_schools_api.py`: School management CRUD with RBAC.
- `test_rubrics_api.py`: Grading rubric creation and assignment.
- `test_budgets_api.py`: Budget planning and tracking API.
- `test_financial_health_api.py`: Financial health score computation API.
- `test_compliance_api.py`: MEN compliance reporting API.
- `test_skill_passport_api.py`: Skill passport creation and progression.
- `test_micro_school_api.py`: Micro-school management.
- `test_sync_api.py`: Offline sync queue API.
- `test_readiness.py`: Health and readiness endpoint verification.
- `test_attendance_analytics_api.py`: Attendance analytics endpoints.

### 5.2 Database Repository Tests

3 test files in `tests/integration/db/` test repository-layer database operations:

- `test_billing_repo.py`: Invoice queries, payment record persistence.
- `test_lms_repo.py`: Course and submission data access patterns.
- `test_school_repo.py`: School lookup and listing.

### 5.3 Domain-Specific Integration Tests

6 standalone test files in `tests/integration/`:

- `test_rewards.py` (400 lines): XP award pipeline, level progression, streak tracking, leaderboard computation.
- `test_games.py` (146 lines): Game configuration CRUD, completion→reward bridge, difficulty validation.
- `test_story_content.py` (270 lines): Story content management, age-appropriate filtering.
- `test_difficulty_adapter.py`: Adaptive difficulty algorithm testing.
- `test_content_age_filter.py`: Content filtering by student age and grade level.
- `test_level_age_mapping.py`: Moroccan education level to age range mapping.

### 5.4 Phase-Specific Integration Tests

14 legacy integration files test feature milestones:

- `test_auth.py` (551 lines): Full authentication journey — login, token refresh, logout, session listing, profile, 2FA setup/verify/disable, email verification, password change.
- `test_phase3.py`: ERP endpoints — classes, enrollments, teacher assignments, attendance, courses, assignments, submissions, results, content, activities, assessments, invoices, payments, notifications, consents, feed, admin dashboard, AI endpoints.
- `test_phase3b_uploads.py`: File upload via multipart form, size limits, MIME type validation.
- `test_phase3c_websocket.py`: WebSocket connection, authentication, real-time event delivery.
- `test_phase3d_filters.py`: Cursor-based pagination, sorting, filtering across endpoints.
- `test_phase3e_tasks.py`: ARQ background task enqueue and execution.
- `test_phase13_notifications.py`: Notification delivery, preference management, batch notifications.
- `test_phase14_reports_analytics.py`: Report generation, analytics aggregation.
- `test_phase15_calendar_events.py`: Calendar event CRUD, recurring events.
- `test_phase16_document_management.py`: Document upload, versioning, deduplication.
- `test_phase1b_profiles.py`: User profile management.
- `test_phase2c_register.py`: User registration flow.
- `test_phase2d_family.py`: Parent-child link management.
- `test_phase_b_shared_review.py`: Shared review functionality.

---

## 6. Security Test Analysis

### 6.1 RBAC Matrix Tests

The `tests/security/` directory (12 files, 2,935 LOC) systematically validates role-based access control:

**test_rbac_matrix.py**: Implements a data-driven RBAC test matrix. Each test case defines an endpoint and the expected HTTP status per role (SYS, SUP, ADM, DIR, TCH, PAR, STD, CONTENT_MGR). The matrix covers schools, gradebook, rubrics, question bank, payment plans, attendance analytics, budgets, financial health, compliance, timetables, and micro-school endpoints. Example: gradebook allows all roles (200) except CONTENT_MGR (403); schools allow SUP/ADM/DIR (200) but deny TCH/PAR/STD/CONTENT_MGR (403).

**test_permission_escalation.py**: Tests specific privilege escalation attempts: student cannot list schools (403), parent cannot impersonate users (403), teacher cannot update school settings (403), content manager cannot update school settings (403), student cannot create fee structures (403).

**test_abac_parent_child.py**, **test_abac_student_teacher.py**, **test_abac_teacher_class.py**: Test attribute-based access control at the relationship level — parent can only access their linked children's data, students can only access their class teacher's data, teachers can only access their assigned classes.

**Module-specific RBAC**: `test_budget_rbac.py`, `test_compliance_rbac.py`, `test_finhealth_rbac.py`, `test_micro_school_rbac.py`, `test_skill_passport_rbac.py`, `test_sync_rbac.py` — each tests role-specific access control for its respective module.

### 6.2 Legacy Security Suites

**test_rbac_security.py** (716 lines): Comprehensive endpoint × role matrix organized in 3 test classes:
1. `TestUnauthenticated`: 19 parameterized endpoints verify 401 without token
2. `TestDenyOrdering`: Validates the deny chain 401 → 404 → 403 (unauthenticated before not-found before forbidden)
3. Role-specific test classes for admin, teacher, parent, and student access patterns

**test_security_audit.py** (433 lines): Penetration-style tests:
1. `TestAuthBypass`: 16 protected endpoints return 401 without token
2. SQL injection payloads in login (`' OR 1=1 --`, `admin' --`)
3. XSS payload in headers and query parameters
4. Cross-school data isolation (school_id scope masking)
5. Password policy enforcement (length, complexity)
6. Token reuse after logout
7. Rate limit verification on auth endpoints

---

## 7. Edge & Boundary Tests

9 test files in `tests/edge/` (2,141 LOC) test boundary conditions and error paths:

**test_boundary_values.py**: Moroccan grade boundaries (0, 20, 0.01, 19.99), invoice numeric limits (0 to 999,999.99), currency normalization (lowercase → uppercase), cursor pagination edge cases (invalid base64, empty cursor, max page size), Unicode in school names and user data, empty string handling.

**test_error_paths.py**: Tests error recovery — malformed JSON requests, missing required fields, invalid UUID formats, expired tokens, database constraint violations.

**test_time_dependent.py**: Time-sensitive logic — late submission penalty calculations at exact deadline boundary, academic year transitions, session expiry edge cases.

**test_budget_edge.py**, **test_finhealth_edge.py**: Financial calculation edge cases — zero budget, negative adjustments, extreme decimal precision, sibling discount with single child.

**test_compliance_edge.py**: MEN compliance edge cases — incomplete data, missing required fields.

**test_skill_passport_edge.py**: Skill progression edge cases — level boundaries, XP overflow.

**test_micro_school_edge.py**: Micro-school capacity limits, concurrent enrollment.

**test_sync_edge.py**: Offline sync conflict resolution, queue ordering.

---

## 8. Contract Tests

2 test files in `tests/contract/` (268 LOC) validate API contracts:

**test_api_contracts.py**: Verifies response envelopes conform to the standard schema:
- Success envelope: `{ data: {...}, meta: { timestamp, version } }`
- List envelope: `{ data: [], meta: { next_cursor, has_more, timestamp, version } }`
- Error envelope: `{ error: { code, message, category, correlation_id, retryable, timestamp } }`
- Health endpoint contract (status, version, timestamp fields, ISO 8601 format)
- Cursor-based pagination contract (DEFAULT_PAGE_SIZE=20, cursor presence)

**test_migration_contracts.py**: Validates Alembic migration chain integrity:
- Every migration defines both `upgrade()` and `downgrade()` functions
- All revision IDs are unique
- Single migration head exists (no branches)
- All `down_revision` references point to known parent revisions

---

## 9. Performance Tests

2 test files in `tests/performance/` (265 LOC) using `pytest-benchmark`:

**test_benchmarks.py**: Benchmarks critical hot-path operations:
- `get_effective_permissions()` for all 8 roles must complete under 1ms
- `role_has_permission()` lookup for specific permission strings under 1ms
- `apply_owner_scope()` ABAC filter under 1ms
- `MoroccanGrade.from_float()` conversion under 1ms
- `calculate_late_penalty()` computation under 1ms
- Invoice total amount validation under 1ms

**test_load_patterns.py**: Load pattern simulation for capacity planning.

---

## 10. E2E Tests (Playwright)

### 10.1 Configuration

`playwright.config.ts` configures: Chromium-only execution, sequential tests (workers: 1, fullyParallel: false), 30-second timeout, trace on first retry, screenshot on failure only, CI-specific GitHub reporter. In local development, auto-starts Vite dev server.

### 10.2 User Journey Specs

15 spec files in `web/e2e/` covering complete user journeys:

**Critical Journeys (J1-J5)**:
- `j1-parent-feed-notify-logout.spec.ts`: Parent login → feed view → notifications → logout. Verifies unauthenticated redirect to login.
- `j2-teacher-assignment.spec.ts`: Teacher creates assignment workflow.
- `j3-student-submission.spec.ts`: Student submits work.
- `j4-admin-invitation.spec.ts`: Admin creates invitation codes.
- `j5-two-factor-auth.spec.ts` (127 lines): Full 2FA setup and verification flow.

**Feature Flows**:
- `attendance-flow.spec.ts`: Attendance marking and justification workflow.
- `gradebook-flow.spec.ts`: Gradebook viewing and grade entry.
- `invoice-payment.spec.ts`: Invoice viewing and payment initiation.
- `budget-flow.spec.ts`: Budget planning interface.
- `rewards.spec.ts` (185 lines): Rewards display, star/XP visualization, leaderboard.
- `games-management.spec.ts`: Game configuration CRUD.
- `cms-story-content.spec.ts`: Content management.
- `admin-badges.spec.ts`: Badge management.

**UI/UX Tests**:
- `dark-mode.spec.ts`: Dark mode toggle and persistence.
- `language-switch.spec.ts`: Trilingual (Arabic/French/English) switching.

### 10.3 Test Infrastructure

`helpers.ts`: Shared login/logout functions and page title assertions.
`mockApi.ts` (238 lines): API mock layer using Playwright's `page.route()` to intercept API calls. Simulates session state for different roles (parent, teacher, student, admin) without requiring a live backend.

---

## 11. Load Testing (k6)

4 k6 JavaScript scenarios referenced by CI but implemented outside the Python test directory:

- `scenario1_logins.js`: Login flow stress test — concurrent authentication attempts
- `scenario2_get_requests.js`: Read-heavy endpoint performance (feed, notifications, content)
- `scenario3_file_uploads.js`: File upload throughput under load
- `scenario4_websocket.js`: WebSocket connection scaling and message throughput

k6 runs in CI after integration tests pass, validating that the application meets performance requirements under load.

---

## 12. CI Integration & Coverage

### 12.1 Test Execution in CI

The CI pipeline (`ci.yml`) executes tests in a strict dependency chain:

1. **Unit tests**: 6-matrix (Python 3.12/3.13 × PostgreSQL 15/16/17). Coverage enforced at **95% minimum** for core modules (`exceptions.py`, `permissions.py`, `response.py`, `security.py`)
2. **Integration tests**: Same 6-matrix, real PostgreSQL + Redis services, Alembic migrations + seed data, live Uvicorn server
3. **Contract tests**: API contract verification against live server
4. **Security tests**: RBAC enforcement matrix
5. **Security audit tests**: Penetration-style security verification
6. **E2E tests**: Playwright with Chromium, full frontend + backend stack
7. **Load tests**: k6 with 4 scenarios

### 12.2 Coverage Strategy

Coverage is collected across all test phases using `coverage.py` with `--parallel-mode`. Each job uploads `.coverage*` artifacts. The final `coverage-report` job combines all coverage data into a unified report. This cross-phase aggregation means a line exercised in integration tests counts toward coverage even if unit tests don't reach it.

The 95% coverage threshold is applied only to critical security modules — the modules that handle authentication, authorization, error responses, and cryptographic operations.

### 12.3 Migration Safety in CI

The `migration-safety` job implements a 3-step verification when Alembic files change:
1. `alembic upgrade head` — forward migration succeeds
2. `alembic downgrade base` — all migrations are reversible
3. `alembic upgrade head` — re-apply confirms idempotency

This runs against a dedicated PostgreSQL service and only triggers when `backend/alembic/**` files change (detected via `dorny/paths-filter`).

---

## 13. Test Patterns & Techniques

### 13.1 Parameterized RBAC Testing

Security tests use `pytest.mark.parametrize` with endpoint × role matrices. The `ENDPOINT_CASES` pattern defines a list of tuples: `(name, path, params, {role: expected_status})`. A single test function iterates all roles for each endpoint, asserting the correct HTTP status. This ensures every new endpoint gets tested across all 8 roles.

### 13.2 Rollback-Transaction Isolation

The `db_session` fixture wraps each test in a database transaction that is always rolled back — never committed. This provides complete test isolation without database cleanup overhead. Each test sees a fresh database state because the outer transaction is rolled back after the test completes.

### 13.3 Auto-Seed with Retry

The `_login_with_seed_retry` pattern in conftest handles the "cold database" problem. If login returns 401, it assumes the seed data is missing and re-runs the seed script (via Docker exec or direct invocation). This makes tests self-healing when run against a freshly initialized database.

### 13.4 Factory Pattern with French Locale

Factories use `Faker("fr_FR")` for realistic test data matching the Moroccan context (French names, phone numbers in `+212` format). Each factory produces valid domain objects with correct relationships, avoiding the "magic strings" anti-pattern.

### 13.5 Benchmark-as-Test

Performance tests use `pytest-benchmark` to enforce timing contracts. If `get_effective_permissions()` takes more than 1ms, the test fails. This prevents performance regressions from being merged — the hot-path operations that run on every request must stay under their timing budget.

---

## 14. Test Quality Metrics

| Metric | Value |
|---|---|
| Total backend test files | 119 |
| Total backend test LOC | ~33,759 |
| Total test functions | ~1,339 |
| E2E spec files | 17 |
| E2E LOC | ~4,170 |
| Factory modules | 17 (1,808 LOC) |
| CI test matrix | 6 combinations (2 Python × 3 PostgreSQL) |
| Unit coverage threshold | 95% on core modules |
| Roles tested in RBAC matrix | 8 (ADM, DIR, TCH, PAR, STD, SUP, SYS, CONTENT_MGR) |
| User journey E2E specs | 5 critical journeys + 10 feature flows |
| k6 load scenarios | 4 |
| Test-to-source ratio | ~33,759 test LOC / ~21,350 service LOC ≈ 1.58:1 |
