# Global Mega-Prompts — Ecole Platform

> **3 prompts to rule them all.**
> Give ONE prompt to Codex or Claude Code → it runs autonomously until done.
> Each prompt covers ALL 25 execution steps (T-01→T-13 + CI-01→CI-12).
>
> **Workflow**: Run Prompt 1 → Run Prompt 2 → Run Prompt 3
> **Constraint**: Do NOT stop until the prompt is fully complete.

---

## PROMPT 1 of 3: GLOBAL ANALYZE

```
═══════════════════════════════════════════════════════════════
GLOBAL PROMPT 1/3 — ANALYZE & UNDERSTAND THE ENTIRE CODEBASE
═══════════════════════════════════════════════════════════════

YOU ARE: An autonomous AI agent (Codex or Claude Code) tasked with deeply analyzing the Ecole Platform codebase before any modifications. This is a K-12 EdTech SaaS for Moroccan schools (FastAPI backend, React web, Flutter mobile).

YOUR GOAL: Read, map, and understand every file that will be touched by the 25 execution prompts. Produce a single output file ANALYSIS_REPORT.md that confirms understanding of each area and identifies any risks or blockers.

DO NOT modify any files. READ ONLY. DO NOT stop until every section is complete.

═══════════════════════════════════════════════════════════════
SECTION A: PROJECT STRUCTURE MAPPING
═══════════════════════════════════════════════════════════════

1. List ALL files in these directories (recursive):
   - backend/app/models/
   - backend/app/core/
   - backend/app/services/ (including lms/ subdirectory)
   - backend/app/api/v1/
   - backend/app/repositories/
   - backend/app/domain/
   - backend/tests/
   - .github/workflows/
   - infra/

2. For each directory, count: total files, total lines of code.

3. Read and record the content of:
   - backend/requirements.txt
   - backend/requirements-dev.txt
   - backend/pyproject.toml (or pytest.ini)
   - Makefile (first 150 lines)
   - .env.example
   - .github/workflows/ci.yml

═══════════════════════════════════════════════════════════════
SECTION B: DOMAIN MODEL ANALYSIS
═══════════════════════════════════════════════════════════════

Read COMPLETELY each model file. For each, extract and record:

4. backend/app/models/iam.py:
   - All classes (User, Membership, Session, InvitationCode, ParentChildLink, etc.)
   - All enums (UserStatus, RoleCode, etc.)
   - All @validates decorators (name + field + validation logic)
   - All @property methods (name + return type + logic)
   - All __repr__ methods (what they include/exclude)
   - Mixins used (SchoolScopedMixin, TimestampMixin, etc.)

5. Repeat step 4 for EACH of:
   - backend/app/models/school.py
   - backend/app/models/lms.py
   - backend/app/models/erp.py
   - backend/app/models/billing.py
   - backend/app/models/com.py
   - backend/app/models/documents.py
   - backend/app/models/calendar.py
   - backend/app/models/reporting.py
   - backend/app/models/audit.py

6. backend/app/core/database.py:
   - Record Base class, all mixins (TimestampMixin, SchoolScopedMixin, NullableSchoolScopedMixin, SoftDeleteMixin)
   - Record each mixin's fields, properties, and methods
   - Record engine and session setup (async engine, sessionmaker)

═══════════════════════════════════════════════════════════════
SECTION C: PERMISSIONS & SECURITY ANALYSIS
═══════════════════════════════════════════════════════════════

7. backend/app/core/permissions.py (READ ALL ~622 lines):
   - Count total PERM_* constants
   - Record PLATFORM_ROLES set
   - Record ROLE_HIERARCHY dict (exact structure)
   - Record get_effective_permissions() logic (circular detection)
   - Record role_has_permission() logic
   - For EACH of 8 roles (SYS, SUP, ADM, DIR, TCH, PAR, STD, CONTENT_MGR):
     → Count direct permissions
     → Count inherited permissions (via hierarchy)
     → Count total effective permissions
   - Create a PERMISSION MATRIX: at least 20 key permissions × 8 roles → True/False

8. backend/app/core/abac.py (READ ALL):
   - Record apply_owner_scope() — parameters, role-based filtering logic
   - Record validate_parent_child_access() — what it checks, exceptions
   - Record validate_teacher_class_access() — what it checks
   - Record validate_student_teacher_access() — what it checks

═══════════════════════════════════════════════════════════════
SECTION D: SERVICE LAYER ANALYSIS
═══════════════════════════════════════════════════════════════

For EACH service file, read completely and record:
- Class name
- Constructor dependencies (db, repos, etc.)
- ALL public methods: name, parameters, return type, key logic, exceptions raised
- Repository methods called (what to mock in tests)
- Events dispatched

9.  backend/app/services/lms/grading_service.py (~178 lines)
10. backend/app/services/lms/assignment_service.py (~393 lines)
11. backend/app/services/lms/quiz_service.py
12. backend/app/services/lms/_helpers.py (~438 lines) — especially calculate_late_penalty()
13. backend/app/services/lms/_serializers.py (~182 lines)
14. backend/app/services/billing.py
15. backend/app/services/payment_plan.py
16. backend/app/services/auth.py
17. backend/app/services/attendance_analytics.py
18. backend/app/services/communication.py
19. backend/app/services/school.py
20. backend/app/services/timetable_generator.py
21. backend/app/services/gradebook.py
22. backend/app/services/report_scheduler.py (or reports.py)

═══════════════════════════════════════════════════════════════
SECTION E: DOMAIN VALUE OBJECTS ANALYSIS
═══════════════════════════════════════════════════════════════

23. Read ALL files in backend/app/domain/value_objects/:
    - grade.py → MoroccanGrade: constructor, value, mention, validation, operators
    - money.py → Money: constructor, currency, validation, arithmetic
    - typed_id.py → UserId, SchoolId: creation, validation, equality, hash
    - role_set.py → RoleSet: constructor, has_role, membership, iteration

24. Read ALL files in backend/app/domain/events/:
    - Record all domain event classes and their fields

25. Read ALL files in backend/app/domain/protocols/:
    - Record all protocol/interface definitions

═══════════════════════════════════════════════════════════════
SECTION F: API ENDPOINTS ANALYSIS
═══════════════════════════════════════════════════════════════

26. For each API file in backend/app/api/v1/, record:
    - Route prefix
    - All endpoints: method + path + permission required + response model
    Focus especially on:
    - schools.py, gradebook.py, rubrics.py, billing.py, payments.py
    - attendance_analytics.py, timetable_generation.py, messaging.py
    - question_bank.py, assignments.py, submissions.py

═══════════════════════════════════════════════════════════════
SECTION G: EXISTING TESTS ANALYSIS
═══════════════════════════════════════════════════════════════

27. backend/tests/conftest.py — READ ALL:
    - Record every fixture: name, scope, what it provides
    - Note backward compatibility requirements

28. List all existing test files in backend/tests/:
    - For each: count tests, identify what they cover
    - Identify which areas have NO tests

29. Run (if possible): cd backend && pytest --co -q 2>&1 | tail -5
    - Record total test count

═══════════════════════════════════════════════════════════════
SECTION H: INFRASTRUCTURE ANALYSIS
═══════════════════════════════════════════════════════════════

30. Read completely:
    - .github/workflows/ci.yml → all 10 stages, triggers, services, needs
    - infra/docker-compose.dev.yml → all services, resources, networks
    - infra/docker-compose.staging.yml → differences from dev
    - infra/docker-compose.prod.yml → secrets, scaling, resources
    - infra/docker-compose.monitoring.yml → Prometheus, Grafana, Loki, Alertmanager
    - backend/Dockerfile → stages, healthcheck, non-root user
    - web/Dockerfile → stages
    - infra/nginx/nginx-prod.conf → rate limiting, TLS, security headers
    - infra/prometheus/prometheus.yml → scrape targets
    - infra/prometheus/alert_rules.yml → existing alerts
    - infra/loki/loki-config.yml → retention, ingestion config
    - infra/loki/promtail-config.yml → scrape config
    - infra/scripts/deploy.sh → deployment logic
    - infra/scripts/healthcheck.sh → health check logic
    - infra/postgres/init.sql → roles, extensions
    - infra/redis/redis.conf → memory, persistence

═══════════════════════════════════════════════════════════════
SECTION I: REFERENCE DOCUMENTS
═══════════════════════════════════════════════════════════════

31. Read these project documents:
    - TESTING_ARCHITECTURE.md → test strategy reference
    - CICD_INFRASTRUCTURE.md → CI/CD enhancement specs
    - EXECUTION_PROMPTS.md → all 25 prompts to execute
    - EXECUTION_CHECKLIST.md → checklist to track progress
    - FINAL_VERIFICATION_REPORT.md → 28/28 checks passing
    - DEPLOYMENT.md → current deployment guide

═══════════════════════════════════════════════════════════════
SECTION J: OUTPUT — ANALYSIS_REPORT.md
═══════════════════════════════════════════════════════════════

Create file: ANALYSIS_REPORT.md

Structure:
1. **Project Stats**: total files, total LOC, model count, service count, endpoint count, test count
2. **Model Map**: table of all models with their mixins, validators, properties
3. **Permission Matrix**: 20+ permissions × 8 roles → True/False grid
4. **Service Map**: table of all services with methods, dependencies, and test coverage status
5. **API Map**: table of all endpoints with method, path, auth requirement
6. **Existing Test Inventory**: what's covered, what's missing
7. **Infrastructure Map**: current CI stages, Docker services, monitoring components
8. **Risk Assessment**: any potential blockers for the 25 execution prompts:
   - Missing imports or circular dependencies?
   - Files that don't match expected structure?
   - Deprecated APIs or version conflicts?
   - Any model that doesn't have expected validators/properties?
9. **Factory Requirements**: for each model, list required fields with types (used by T-01)
10. **Readiness Confirmation**: "READY TO EXECUTE" or "BLOCKERS FOUND: [list]"

DO NOT STOP until ANALYSIS_REPORT.md is complete and written to disk.
═══════════════════════════════════════════════════════════════
```

---

## PROMPT 2 of 3: GLOBAL EXECUTE

```
═══════════════════════════════════════════════════════════════
GLOBAL PROMPT 2/3 — EXECUTE ALL 25 PROMPTS SEQUENTIALLY
═══════════════════════════════════════════════════════════════

YOU ARE: An autonomous AI agent (Codex or Claude Code) tasked with executing ALL 25 implementation prompts for the Ecole Platform. This is a K-12 EdTech SaaS for Moroccan schools (FastAPI, SQLAlchemy 2.0, PostgreSQL, Redis).

YOUR GOAL: Execute every prompt from T-01 to CI-12, in order. After each prompt, run its VERIFY checks. If a check fails, fix the issue before moving to the next prompt.

DO NOT stop until ALL 25 prompts are complete.

ENVIRONMENT:
- If CODEX_ENV is set (or you are Codex): git add -A && git commit after each prompt with the specified COMMIT_MSG.
- Otherwise (Claude Code): skip all git commands, print "SKIP GIT" instead.

REFERENCE FILES (read these FIRST before starting):
- EXECUTION_PROMPTS.md — contains the detailed instructions for each prompt
- EXECUTION_CHECKLIST.md — track progress by checking off items
- TESTING_ARCHITECTURE.md — test patterns and examples
- CICD_INFRASTRUCTURE.md — CI/CD specs and configurations
- ANALYSIS_REPORT.md — codebase analysis from Prompt 1 (if exists)

RULES:
- Do NOT delete existing files unless explicitly told to.
- Do NOT break existing tests — all changes are additive.
- Do NOT modify .env or any file containing real secrets.
- Preserve existing imports and code — extend, don't replace.
- Use realistic Moroccan data: Faker("fr_FR"), +212 phones, Africa/Casablanca, MAD, 0-20 scale.
- If a step fails: log the error, attempt to fix, continue. Never stop.
- After each prompt's VERIFY phase: update EXECUTION_CHECKLIST.md by marking completed items.

═══════════════════════════════════════════════════════════════
BEGIN EXECUTION — PART 1: TESTING (T-01 → T-13)
═══════════════════════════════════════════════════════════════

PROMPT T-01: TEST INFRASTRUCTURE SETUP
──────────────────────────────────────

Read EXECUTION_PROMPTS.md section "T-01" and execute ALL steps:

EXECUTE:
1. Create backend/requirements-test.txt extending requirements-dev.txt:
   -r requirements-dev.txt
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

2. Run: cd backend && pip install -r requirements-test.txt

3. Create directories with __init__.py:
   backend/tests/{factories,unit,unit/domain,unit/models,unit/core,unit/services,integration,integration/api,integration/db,security,edge,performance,contract}

4. Create backend/tests/factories/base.py:
   AsyncSQLAlchemyFactory with async create() and create_batch() classmethods.
   The create() method takes a session, builds the object, adds to session, flushes, refreshes, returns.

5. Create backend/tests/factories/iam.py:
   Read backend/app/models/iam.py to get exact field names and types.
   UserFactory: all required fields with Faker("fr_FR") data, +212 phones.
   MembershipFactory: user SubFactory, role_code="STD".
   SessionFactory, InvitationCodeFactory, ParentChildLinkFactory.

6. Create backend/tests/factories/school.py:
   Read backend/app/models/school.py for exact fields.
   SchoolFactory: name, code, city="Casablanca", preferences with Africa/Casablanca timezone.

7. Create backend/tests/factories/lms.py:
   Read backend/app/models/lms.py for exact fields.
   CourseFactory, AssignmentFactory (total_points=20, due_at future, allow_late=True, late_penalty_per_day=2.0), SubmissionFactory, GradeFactory.

8. Create backend/tests/factories/erp.py:
   Read backend/app/models/erp.py. AcademicYearFactory, ClassFactory, EnrollmentFactory, AttendanceSessionFactory, AttendanceRecordFactory.

9. Create backend/tests/factories/billing.py:
   Read backend/app/models/billing.py. InvoiceFactory (MAD currency, 500.00), InvoiceItemFactory, PaymentAttemptFactory, FeeStructureFactory, PaymentPlanFactory, InstallmentFactory.

10. Create backend/tests/factories/com.py:
    Read backend/app/models/com.py. NotificationFactory, ConversationFactory, MessageFactory.

11. Create backend/tests/factories/documents.py:
    Read backend/app/models/documents.py. DocumentFactory, ResourceFactory.

12. Create backend/tests/factories/calendar.py:
    Read backend/app/models/calendar.py. EventFactory, EventRSVPFactory.

13. Update backend/tests/conftest.py — ADD new fixtures WITHOUT removing existing ones:
    - postgres_url (testcontainer, scope=session)
    - engine (create_async_engine, scope=session)
    - db_session (per-test with rollback)
    - admin_auth, teacher_auth, student_auth, parent_auth, sup_auth (mock AuthContext)

14. Update pyproject.toml: pytest markers, coverage config (branch=true, fail_under=90).

15. Append to Makefile: test-unit, test-integration, test-security, test-full, test-perf targets.

VERIFY T-01:
- python -c "from tests.factories.iam import UserFactory; from tests.factories.school import SchoolFactory; print('OK')"
- find backend/tests -type d | sort (verify structure)
- pytest tests/ -x -q --timeout=60 (existing tests still pass)
- grep "fail_under" pyproject.toml (or backend/pyproject.toml)
- grep "test-unit" Makefile

GIT T-01: "test(infra): add test infrastructure — factories, conftest, directory structure, pytest config"

──────────────────────────────────────
PROMPT T-02: DOMAIN VALUE OBJECT TESTS
──────────────────────────────────────

Read EXECUTION_PROMPTS.md section "T-02" and execute ALL steps:

EXECUTE:
1. Read backend/app/domain/value_objects/grade.py — understand MoroccanGrade exactly.
2. Read backend/app/domain/value_objects/money.py — understand Money exactly.
3. Read backend/app/domain/value_objects/typed_id.py — understand typed IDs exactly.
4. Read backend/app/domain/value_objects/role_set.py — understand RoleSet exactly.

5. Create backend/tests/unit/domain/test_grade.py (~15 tests):
   Match the ACTUAL class name, constructor, properties from step 1.
   Test: valid scores (0, 10, 15.75, 20), invalid (-1, 21, 100), all 5 mentions at boundaries.
   Use @pytest.mark.parametrize for boundary/mention pairs.

6. Create backend/tests/unit/domain/test_money.py (~12 tests):
   Match ACTUAL class from step 2.
   Test: valid MAD/EUR/USD, zero, negative error, decimal precision, large amounts.

7. Create backend/tests/unit/domain/test_typed_id.py (~8 tests):
   Match ACTUAL classes from step 3.
   Test: valid UUID, string UUID, invalid input, equality, hash consistency.

8. Create backend/tests/unit/domain/test_role_set.py (~10 tests):
   Match ACTUAL class from step 4.
   Test: single role, multiple, invalid code, has_role, empty set, all 8 valid roles.

VERIFY T-02:
- pytest tests/unit/domain/ -v --tb=short (all ~45 tests pass)

GIT T-02: "test(domain): add value object unit tests — MoroccanGrade, Money, TypedId, RoleSet"

──────────────────────────────────────
PROMPT T-03: MODEL VALIDATOR + PROPERTY TESTS
──────────────────────────────────────

Read EXECUTION_PROMPTS.md section "T-03" and execute ALL steps.

EXECUTE:
1. Read ALL model files → extract every @validates and every @property.
2. Create backend/tests/unit/models/test_validators.py (~30 tests):
   For each validator found: test valid, boundary, and invalid inputs.
   Match ACTUAL validator method names and signatures.
3. Create backend/tests/unit/models/test_helper_properties.py (~25 tests):
   For each property found: test both truthy and falsy states.
   Use freezegun for time-dependent properties (is_expired, is_overdue, is_past).
4. Create backend/tests/unit/models/test_repr.py (~10 tests):
   Verify __repr__ includes identifiers, excludes sensitive data.

VERIFY T-03:
- pytest tests/unit/models/ -v --tb=short (all ~60 tests pass)

GIT T-03: "test(models): add validator + property unit tests for all models"

──────────────────────────────────────
PROMPT T-04: PERMISSION + ABAC UNIT TESTS
──────────────────────────────────────

Read EXECUTION_PROMPTS.md section "T-04" and execute ALL steps.

EXECUTE:
1. Read backend/app/core/permissions.py completely.
2. Read backend/app/core/abac.py completely.
3. Create backend/tests/unit/core/test_permissions.py (~25 tests):
   - get_effective_permissions for all 8 roles
   - Hierarchy inheritance: DIR⊃TCH, ADM⊃DIR, SUP⊃ADM, SYS⊃SUP
   - STD and PAR independent branches
   - Parametrized role_has_permission matrix
   - PLATFORM_ROLES constant check
4. Create backend/tests/unit/core/test_abac.py (~15 tests):
   - apply_owner_scope for each role type
   - validate_parent_child_access (active, inactive, missing)
   - validate_teacher_class_access
   - validate_student_teacher_access

VERIFY T-04:
- pytest tests/unit/core/ -v --tb=short (all ~40 tests pass)

GIT T-04: "test(core): add permission hierarchy + ABAC unit tests"

──────────────────────────────────────
PROMPT T-05: LMS SERVICE UNIT TESTS
──────────────────────────────────────

Read EXECUTION_PROMPTS.md section "T-05" and execute ALL steps.

EXECUTE:
1. Read grading_service.py, assignment_service.py, quiz_service.py, _helpers.py, _serializers.py completely.
2. Read the corresponding repository files to understand method signatures to mock.
3. Create backend/tests/unit/services/test_grading_service.py (~25 tests): grade_submission (valid, invalid score, not found, wrong teacher, rubric, late penalty, update), override_late_penalty, calculate_late_penalty (grace, days, max exceeded, floor at 0).
4. Create backend/tests/unit/services/test_assignment_service.py (~20 tests): create, upload PDF, create submission, finalize, upload file, max files.
5. Create backend/tests/unit/services/test_quiz_service.py (~20 tests): create, start attempt, submit (auto-grade, time limit), generate from bank.
All repos mocked with AsyncMock.

VERIFY T-05:
- pytest tests/unit/services/test_grading_service.py tests/unit/services/test_assignment_service.py tests/unit/services/test_quiz_service.py -v --tb=short (all ~65 pass)

GIT T-05: "test(lms): add LMS service unit tests — grading, assignment, quiz"

──────────────────────────────────────
PROMPT T-06: BILLING + AUTH + ATTENDANCE TESTS
──────────────────────────────────────

Read EXECUTION_PROMPTS.md section "T-06" and execute ALL steps.

EXECUTE:
1. Read billing.py, payment_plan.py, auth.py, attendance_analytics.py completely.
2. Create test_billing_service.py (~25): invoices, sibling discounts, late fees, payment plans, MAD currency.
3. Create test_auth_service.py (~20): login, impersonation, session limits, device detection, token refresh.
4. Create test_attendance_service.py (~15): thresholds, rates, trends.

VERIFY T-06:
- pytest tests/unit/services/test_billing_service.py tests/unit/services/test_auth_service.py tests/unit/services/test_attendance_service.py -v --tb=short (all ~60 pass)

GIT T-06: "test(services): add billing, auth, attendance service unit tests"

──────────────────────────────────────
PROMPT T-07: COMMUNICATION + SCHOOL + OTHER TESTS
──────────────────────────────────────

Read EXECUTION_PROMPTS.md section "T-07" and execute ALL steps.

EXECUTE:
1. Read communication.py, school.py, timetable_generator.py, gradebook.py, reports.py completely.
2. Create test_communication_service.py (~15): STD/PAR ABAC, messaging.
3. Create test_school_service.py (~10): CRUD, soft delete, subscription.
4. Create test_timetable_service.py (~15): constraints, preview, apply.
5. Create test_gradebook_service.py (~15): weighted averages, mentions, transcript.
6. Create test_report_service.py (~10): scheduling, format validation.

VERIFY T-07:
- pytest tests/unit/ --co -q (total ~210+ tests)

GIT T-07: "test(services): add communication, school, timetable, gradebook, report unit tests"

──────────────────────────────────────
PROMPT T-08: API INTEGRATION TESTS
──────────────────────────────────────

Read EXECUTION_PROMPTS.md section "T-08" and execute ALL steps.

EXECUTE:
1. Read all API endpoint files to map routes × auth × status codes.
2. Create test_schools_api.py (~20), test_gradebook_api.py (~15), test_rubrics_api.py (~15), test_billing_api.py (~15), test_attendance_analytics_api.py (~10), test_timetable_api.py (~10).
Each test: factory seed → httpx request → assert status + body.

VERIFY T-08:
- pytest tests/integration/api/ -v --tb=short (all ~80 pass, no 500s)

GIT T-08: "test(api): add API integration tests for 6 endpoint groups"

──────────────────────────────────────
PROMPT T-09: DB REPOSITORY INTEGRATION TESTS
──────────────────────────────────────

Read EXECUTION_PROMPTS.md section "T-09" and execute ALL steps.

EXECUTE:
1. Create test_school_repo.py (~15), test_lms_repo.py (~15), test_billing_repo.py (~10).
Real testcontainer DB — test CRUD, pagination, FK constraints, soft delete.

VERIFY T-09:
- pytest tests/integration/db/ -v --tb=short (all ~40 pass)

GIT T-09: "test(db): add repository integration tests — school, LMS, billing"

──────────────────────────────────────
PROMPT T-10: RBAC + ABAC SECURITY MATRIX
──────────────────────────────────────

Read EXECUTION_PROMPTS.md section "T-10" and execute ALL steps.

EXECUTE:
1. Create test_rbac_matrix.py (~80): 7 endpoint groups × 8 roles + no-token.
2. Create test_abac_parent_child.py (~15), test_abac_student_teacher.py (~15), test_abac_teacher_class.py (~10), test_permission_escalation.py (~10).

VERIFY T-10:
- pytest tests/security/ -v --tb=short (all ~120 pass, no 500s)

GIT T-10: "test(security): add RBAC matrix + ABAC security tests"

──────────────────────────────────────
PROMPT T-11: EDGE CASE + BOUNDARY TESTS
──────────────────────────────────────

Read EXECUTION_PROMPTS.md section "T-11" and execute ALL steps.

EXECUTE:
1. Create test_boundary_values.py (~30): numeric, string, Unicode Arabic/French, pagination.
2. Create test_time_dependent.py (~25): freezegun, Africa/Casablanca timezone, DST.
3. Create test_error_paths.py (~25): not found, duplicates, invalid transitions.

VERIFY T-11:
- pytest tests/edge/ -v --tb=short (all ~80 pass)

GIT T-11: "test(edge): add boundary, time-dependent, and error path tests"

──────────────────────────────────────
PROMPT T-12: PERFORMANCE + CONTRACT TESTS
──────────────────────────────────────

Read EXECUTION_PROMPTS.md section "T-12" and execute ALL steps.

EXECUTE:
1. Create test_benchmarks.py (~20): permission <1ms, grade <0.1ms.
2. Create test_load_patterns.py (~10): concurrent ops, batch.
3. Create test_api_contracts.py (~15): response schemas.
4. Create test_migration_contracts.py (~5): upgrade/downgrade, linear chain.

VERIFY T-12:
- pytest tests/performance/ tests/contract/ -v --tb=short (all ~50 pass)

GIT T-12: "test(perf+contract): add performance benchmarks and API contract tests"

──────────────────────────────────────
PROMPT T-13: COVERAGE GAP FILL
──────────────────────────────────────

EXECUTE:
1. Run: cd backend && pytest --cov=app --cov-branch --cov-report=term-missing
2. Identify ALL files below 90% line / 85% branch.
3. Write targeted tests for each gap.
4. Re-run coverage until targets met.

VERIFY T-13:
- pytest --cov=app --cov-branch | grep TOTAL → ≥90% line, ≥85% branch
- pytest --co -q | tail -3 → ~1,200+ tests
- pytest -x -q → all pass

GIT T-13: "test(coverage): fill gaps to 90%+ line, 85%+ branch coverage"

═══════════════════════════════════════════════════════════════
BEGIN EXECUTION — PART 2: CI/CD & INFRASTRUCTURE (CI-01 → CI-12)
═══════════════════════════════════════════════════════════════

PROMPT CI-01: PRE-COMMIT HOOKS
──────────────────────────────────────

Read EXECUTION_PROMPTS.md section "CI-01" and execute ALL steps.

EXECUTE:
1. Create .pre-commit-config.yaml (ruff v0.8.0, detect-secrets v1.5.0, conventional-pre-commit v3.6.0, alembic-heads local hook, pre-commit-hooks v4.6.0).
2. Generate .secrets.baseline via detect-secrets scan.
3. Add hooks-install Makefile target.

VERIFY: YAML valid, baseline valid JSON, Makefile target exists.
GIT: "ci(hooks): add pre-commit hooks — ruff, detect-secrets, conventional commits"

──────────────────────────────────────
PROMPT CI-02: CI PIPELINE HARDENING
──────────────────────────────────────

Read EXECUTION_PROMPTS.md section "CI-02" and execute ALL steps.

EXECUTE:
1. Add matrix strategy to unit-tests + integration-tests (Python 3.12/3.13 × PG 15/16/17).
2. Add pip/npm caching to all jobs.
3. Add security-trivy, security-pip-audit, security-bandit jobs.
4. Add migration-safety job (conditional on alembic/ changes).
5. Add migration head check to lint job.
6. Add [tool.bandit] to pyproject.toml.

VERIFY: YAML valid, TOML valid, correct job dependencies.
GIT: "ci(pipeline): add matrix testing, security scanning, migration safety"

──────────────────────────────────────
PROMPT CI-03: DOCKER BUILD OPTIMIZATION
──────────────────────────────────────

Read EXECUTION_PROMPTS.md section "CI-03" and execute ALL steps.

EXECUTE: Rewrite backend/Dockerfile with BuildKit, cache mounts, test stage, non-root prod.
VERIFY: grep "^FROM" shows 4 stages.
GIT: "build(docker): optimize Dockerfile with BuildKit caching"

──────────────────────────────────────
PROMPT CI-04: CONTAINER REGISTRY
──────────────────────────────────────

Read EXECUTION_PROMPTS.md section "CI-04" and execute ALL steps.

EXECUTE: Add publish-images job + SBOM + cleanup-images.yml.
VERIFY: Both YAML files valid.
GIT: "ci(registry): add ghcr.io publishing with SHA tags and SBOM"

──────────────────────────────────────
PROMPT CI-05: PGBOUNCER
──────────────────────────────────────

Read EXECUTION_PROMPTS.md section "CI-05" and execute ALL steps.

EXECUTE: Add pgbouncer to prod+staging, update DATABASE_URL, add statement_cache_size=0.
VERIFY: compose validates, cache setting present.
GIT: "infra(db): add PgBouncer transaction-level connection pooling"

──────────────────────────────────────
PROMPT CI-06: READ REPLICA
──────────────────────────────────────

Read EXECUTION_PROMPTS.md section "CI-06" and execute ALL steps.

EXECUTE: Add replicator role, replica service, create db_routing.py, add config.
VERIFY: compose validates, routing importable.
GIT: "infra(db): add PostgreSQL read replica with SQLAlchemy routing"

──────────────────────────────────────
PROMPT CI-07: AUTOMATED BACKUPS
──────────────────────────────────────

Read EXECUTION_PROMPTS.md section "CI-07" and execute ALL steps.

EXECUTE: Create backup-s3.sh, restore-drill.sh, Makefile targets, .env.example update.
VERIFY: shellcheck/bash -n passes, scripts executable.
GIT: "infra(backup): add automated S3 backups with weekly restore drill"

──────────────────────────────────────
PROMPT CI-08: OPENTELEMETRY APM
──────────────────────────────────────

Read EXECUTION_PROMPTS.md section "CI-08" and execute ALL steps.

EXECUTE: Add OTel packages, create telemetry.py, tempo.yml, Tempo service, Grafana datasource.
VERIFY: pip install OK, telemetry importable, compose validates.
GIT: "feat(observability): add OpenTelemetry tracing with Grafana Tempo"

──────────────────────────────────────
PROMPT CI-09: BUSINESS METRICS + LOG ALERTING
──────────────────────────────────────

Read EXECUTION_PROMPTS.md section "CI-09" and execute ALL steps.

EXECUTE: Create business_metrics.py, dashboard JSON, Loki ruler config, alert rules.
VERIFY: Metrics importable, JSON valid, YAML valid.
GIT: "feat(monitoring): add education business metrics + Loki log alerting"

──────────────────────────────────────
PROMPT CI-10: SECURITY HARDENING
──────────────────────────────────────

Read EXECUTION_PROMPTS.md section "CI-10" and execute ALL steps.

EXECUTE: Create rotate-secrets.sh, update nginx WAF, create dependabot.yml + automerge.yml.
VERIFY: shellcheck OK, YAML valid, nginx rules present.
GIT: "security: add secret rotation, WAF rules, Dependabot"

──────────────────────────────────────
PROMPT CI-11: BLUE-GREEN DEPLOYMENT
──────────────────────────────────────

Read EXECUTION_PROMPTS.md section "CI-11" and execute ALL steps.

EXECUTE: Create blue/green compose files, blue-green-deploy.sh, upstream.conf, update nginx.
VERIFY: Both compose validate, script passes shellcheck.
GIT: "infra(deploy): add blue-green deployment with instant rollback"

──────────────────────────────────────
PROMPT CI-12: DEV ONBOARDING + DOCS
──────────────────────────────────────

Read EXECUTION_PROMPTS.md section "CI-12" and execute ALL steps.

EXECUTE: Create seed_demo.py, Makefile targets (dev-init, dev-reset), docs.yml, docs targets.
VERIFY: seed_demo importable, targets exist, YAML valid.
GIT: "feat(dx): add dev-init, demo seed data, API docs generation"

═══════════════════════════════════════════════════════════════
FINAL STEP: Update EXECUTION_CHECKLIST.md
═══════════════════════════════════════════════════════════════

Mark ALL items as checked [x] in EXECUTION_CHECKLIST.md.
Print: "ALL 25 PROMPTS EXECUTED SUCCESSFULLY"

DO NOT STOP UNTIL THIS LINE IS PRINTED.
═══════════════════════════════════════════════════════════════
```

---

## PROMPT 3 of 3: GLOBAL VERIFY

```
═══════════════════════════════════════════════════════════════
GLOBAL PROMPT 3/3 — VERIFY EVERYTHING WORKS
═══════════════════════════════════════════════════════════════

YOU ARE: An autonomous AI agent tasked with verifying ALL work done by Prompt 2. You will run a comprehensive verification suite and produce a VERIFICATION_FINAL.md report.

DO NOT modify source code (only fix test issues if tests fail due to minor bugs). DO NOT stop until the full report is written.

═══════════════════════════════════════════════════════════════
SECTION 1: TEST SUITE VERIFICATION
═══════════════════════════════════════════════════════════════

1.1 — Install dependencies:
  cd backend && pip install -r requirements-test.txt

1.2 — Run ALL unit tests:
  cd backend && pytest tests/unit/ -v --tb=short --timeout=30 2>&1
  Record: total tests, passed, failed, errors, time.

1.3 — Run ALL integration tests:
  cd backend && pytest tests/integration/ -v --tb=short --timeout=120 2>&1
  Record: total, passed, failed, errors, time.

1.4 — Run ALL security tests:
  cd backend && pytest tests/security/ -v --tb=short --timeout=60 2>&1
  Record: total, passed, failed, errors, time.

1.5 — Run ALL edge case tests:
  cd backend && pytest tests/edge/ -v --tb=short --timeout=30 2>&1
  Record: total, passed, failed, errors, time.

1.6 — Run ALL performance tests:
  cd backend && pytest tests/performance/ -v --tb=short --timeout=300 2>&1
  Record: total, passed, failed, time.

1.7 — Run ALL contract tests:
  cd backend && pytest tests/contract/ -v --tb=short --timeout=30 2>&1
  Record: total, passed, failed, time.

1.8 — Run existing tests (backward compatibility):
  cd backend && pytest tests/ --ignore=tests/unit --ignore=tests/integration --ignore=tests/security --ignore=tests/edge --ignore=tests/performance --ignore=tests/contract -v --tb=short --timeout=120 2>&1
  Record: total, passed, failed. ALL MUST PASS (no regressions).

1.9 — Full coverage run:
  cd backend && pytest --cov=app --cov-branch --cov-report=term-missing --cov-report=html 2>&1
  Record: line coverage %, branch coverage %, fail_under result.

1.10 — Total test count:
  cd backend && pytest --co -q 2>&1 | tail -3
  Record: total collected tests.

IF ANY TESTS FAIL:
  - Analyze the failure
  - If it's a minor test bug (wrong assertion, import error): fix the test file
  - If it's a real code bug: document it in the report as "CODE BUG FOUND"
  - Re-run the failing tests after fixes
  - Continue to next section

═══════════════════════════════════════════════════════════════
SECTION 2: FACTORY VERIFICATION
═══════════════════════════════════════════════════════════════

2.1 — Import check for ALL factories:
  cd backend && python -c "
  from tests.factories.base import AsyncSQLAlchemyFactory
  from tests.factories.iam import UserFactory, MembershipFactory, SessionFactory, InvitationCodeFactory, ParentChildLinkFactory
  from tests.factories.school import SchoolFactory
  from tests.factories.lms import CourseFactory, AssignmentFactory, SubmissionFactory, GradeFactory
  from tests.factories.erp import AcademicYearFactory, ClassFactory, EnrollmentFactory, AttendanceSessionFactory, AttendanceRecordFactory
  from tests.factories.billing import InvoiceFactory, InvoiceItemFactory, PaymentAttemptFactory, FeeStructureFactory, PaymentPlanFactory, InstallmentFactory
  from tests.factories.com import NotificationFactory, ConversationFactory, MessageFactory
  from tests.factories.documents import DocumentFactory, ResourceFactory
  from tests.factories.calendar import EventFactory, EventRSVPFactory
  print('ALL 25+ FACTORIES IMPORTED OK')
  "

2.2 — Build check (can factories create objects without DB):
  cd backend && python -c "
  from tests.factories.iam import UserFactory
  from tests.factories.school import SchoolFactory
  user = UserFactory.build()
  school = SchoolFactory.build()
  assert user.email, 'User email missing'
  assert school.name, 'School name missing'
  assert '+212' in (user.phone or ''), 'Phone should have +212 prefix'
  print(f'User: {user.email}, Phone: {user.phone}')
  print(f'School: {school.name}, City: {school.city}')
  print('FACTORY BUILD CHECK OK')
  "

═══════════════════════════════════════════════════════════════
SECTION 3: INFRASTRUCTURE FILE VERIFICATION
═══════════════════════════════════════════════════════════════

3.1 — Validate ALL YAML files:
  python -c "
  import yaml, glob, sys
  errors = []
  for f in glob.glob('.github/**/*.yml', recursive=True) + glob.glob('infra/**/*.yml', recursive=True) + glob.glob('infra/**/*.yaml', recursive=True):
      try:
          yaml.safe_load(open(f))
      except Exception as e:
          errors.append(f'{f}: {e}')
  if errors:
      print('YAML ERRORS:'); [print(f'  {e}') for e in errors]; sys.exit(1)
  print(f'ALL {len(glob.glob(\".github/**/*.yml\", recursive=True) + glob.glob(\"infra/**/*.yml\", recursive=True))} YAML FILES VALID')
  "

3.2 — Validate Docker Compose files:
  docker compose -f infra/docker-compose.dev.yml config > /dev/null 2>&1 && echo "dev OK" || echo "dev FAIL"
  docker compose -f infra/docker-compose.staging.yml config > /dev/null 2>&1 && echo "staging OK" || echo "staging FAIL"
  docker compose -f infra/docker-compose.prod.yml config > /dev/null 2>&1 && echo "prod OK" || echo "prod FAIL"
  docker compose -f infra/docker-compose.monitoring.yml config > /dev/null 2>&1 && echo "monitoring OK" || echo "monitoring FAIL"

3.3 — Validate shell scripts:
  for script in infra/scripts/*.sh; do
    bash -n "$script" && echo "$script OK" || echo "$script FAIL"
  done

3.4 — Check new files exist:
  Files that MUST exist after Prompt 2:
  - .pre-commit-config.yaml
  - .secrets.baseline
  - .github/dependabot.yml
  - .github/workflows/dependabot-automerge.yml
  - .github/workflows/cleanup-images.yml (or cleanup in docs.yml)
  - backend/app/core/telemetry.py
  - backend/app/core/db_routing.py
  - backend/app/core/business_metrics.py
  - backend/app/scripts/seed_demo.py
  - infra/scripts/backup-s3.sh
  - infra/scripts/restore-drill.sh
  - infra/scripts/rotate-secrets.sh
  - infra/scripts/blue-green-deploy.sh
  - infra/docker-compose.blue.yml
  - infra/docker-compose.green.yml
  - infra/nginx/upstream.conf
  - infra/tempo/tempo.yml
  - infra/loki/rules/ecole-alerts.yml
  - infra/grafana/dashboards/business-education.json

  For each: ls -la <file> && echo "EXISTS" || echo "MISSING"

═══════════════════════════════════════════════════════════════
SECTION 4: IMPORT VERIFICATION
═══════════════════════════════════════════════════════════════

4.1 — Verify new modules import without errors:
  cd backend && python -c "
  from app.core.telemetry import setup_telemetry
  from app.core.db_routing import get_read_db, get_write_db
  from app.core.business_metrics import active_students, grade_distribution, billing_collection
  print('ALL NEW CORE MODULES IMPORT OK')
  "

4.2 — Verify existing app still starts (import check):
  cd backend && python -c "
  from app.main import app
  print(f'FastAPI app loaded: {len(app.routes)} routes')
  print('APP IMPORT OK')
  "

═══════════════════════════════════════════════════════════════
SECTION 5: CONFIGURATION VERIFICATION
═══════════════════════════════════════════════════════════════

5.1 — pyproject.toml:
  - [tool.pytest.ini_options] has asyncio_mode, markers, addopts
  - [tool.coverage.run] has branch=true, source=["app"]
  - [tool.coverage.report] has fail_under=90
  - [tool.bandit] has exclude_dirs, skips

5.2 — Makefile targets (verify ALL exist):
  grep -c "test-unit\|test-integration\|test-security\|test-full\|test-perf\|hooks-install\|dev-init\|dev-reset\|seed-demo\|docs\|docs-schema\|backup\|restore-drill\|rotate-\|deploy-blue-green\|deploy-rollback\|deploy-status" Makefile

5.3 — .env.example has new variables:
  grep "DATABASE_REPLICA_URL\|ENABLE_TRACING\|OTEL_EXPORTER_ENDPOINT\|S3_BUCKET" .env.example

═══════════════════════════════════════════════════════════════
SECTION 6: CHECKLIST RECONCILIATION
═══════════════════════════════════════════════════════════════

6.1 — Read EXECUTION_CHECKLIST.md
6.2 — For each unchecked item, verify if it was actually completed
6.3 — Update EXECUTION_CHECKLIST.md: mark verified items as [x]

═══════════════════════════════════════════════════════════════
SECTION 7: OUTPUT — VERIFICATION_FINAL.md
═══════════════════════════════════════════════════════════════

Create file: VERIFICATION_FINAL.md

Structure:
1. **Test Results Summary**:
   | Category | Tests | Passed | Failed | Time |
   Unit, Integration, Security, Edge, Performance, Contract, Existing (regression)

2. **Coverage Report**:
   | Metric | Value | Target | Status |
   Line coverage, Branch coverage, fail_under gate

3. **Factory Status**: all 25+ factories — PASS/FAIL

4. **Infrastructure Status**:
   | File | Status |
   All YAML, Compose, shell scripts, new files

5. **Import Status**: all new modules — PASS/FAIL

6. **Configuration Status**: pyproject.toml, Makefile targets, .env.example — PASS/FAIL

7. **Checklist Status**: X/Y items completed

8. **Issues Found** (if any):
   - Test failures and fixes applied
   - Missing files
   - Code bugs discovered

9. **Final Verdict**:
   - ✅ ALL GREEN: "All 25 prompts verified. Platform is production-ready."
   - ⚠️ PARTIAL: "X issues found. See Issues section."
   - ❌ BLOCKED: "Critical failures. See Issues section."

DO NOT STOP until VERIFICATION_FINAL.md is written to disk.
═══════════════════════════════════════════════════════════════
```

---

## How to Use These 3 Prompts

| Step | Prompt | Runner | Duration | Output |
|------|--------|--------|----------|--------|
| 1 | **GLOBAL ANALYZE** | Codex or Claude Code | ~30 min | `ANALYSIS_REPORT.md` |
| 2 | **GLOBAL EXECUTE** | Codex or Claude Code | ~8 hours | All 25 prompts completed, code written |
| 3 | **GLOBAL VERIFY** | Codex or Claude Code | ~30 min | `VERIFICATION_FINAL.md` |

**Total**: ~9 hours autonomous execution.
**Result**: ~1,200 tests at 90%+ coverage + full CI/CD + infrastructure hardening.
