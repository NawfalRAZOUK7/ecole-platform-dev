# Execution Checklist — Ecole Platform

> Track progress across all 25 execution prompts.
> Check off each phase as it completes. Mark sub-tasks within each prompt.
> Reference: `EXECUTION_PROMPTS.md` for full prompt details.

---

## PART 1: TESTING (T-01 → T-13)

### T-01: Test Infrastructure Setup
- [x] **ANALYZE** — Read conftest, models, database.py, requirements-dev
  - [x] Understood existing fixtures and backward compatibility needs
  - [x] Listed all models that need factories
- [x] **EXECUTE** — Create infrastructure
  - [x] Created `requirements-test.txt` with all new dependencies
  - [x] Installed test dependencies successfully
  - [x] Created directory structure (12 directories with `__init__.py`)
  - [x] Created `factories/base.py` (AsyncSQLAlchemyFactory)
  - [x] Created `factories/iam.py` (User, Membership, Session, InvitationCode, ParentChildLink)
  - [x] Created `factories/school.py` (School)
  - [x] Created `factories/lms.py` (Course, Assignment, Submission, Grade, Quiz)
  - [x] Created `factories/erp.py` (AcademicYear, Class, Enrollment, Attendance)
  - [x] Created `factories/billing.py` (Invoice, Payment, FeeStructure, Plan)
  - [x] Created `factories/com.py` (Notification, Conversation, Message)
  - [x] Created `factories/documents.py` (Document, Resource)
  - [x] Created `factories/calendar.py` (Event, RSVP)
  - [x] Updated `conftest.py` (testcontainer, engine, db_session, auth fixtures)
  - [x] Updated `pyproject.toml` (pytest markers, coverage config, fail_under=90)
  - [x] Added Makefile targets (test-unit, test-integration, test-security, test-full, test-perf)
- [x] **VERIFY** — All checks pass
  - [x] All factories importable
  - [x] Directory structure complete
  - [x] Existing tests still pass
  - [x] pyproject.toml has fail_under=90
  - [x] Makefile has all 5 targets
- [x] **GIT** — Committed (Codex only)

---

### T-02: Domain Value Object Unit Tests (~45 tests)
- [x] **ANALYZE** — Read grade.py, money.py, typed_id.py, role_set.py
  - [x] Listed all public methods/properties per value object
- [x] **EXECUTE** — Create tests
  - [x] Created `test_grade.py` (~15 tests: boundaries, mentions, parametrized)
  - [x] Created `test_money.py` (~12 tests: MAD/EUR/USD, negative, decimal)
  - [x] Created `test_typed_id.py` (~8 tests: UUID creation, validation, equality)
  - [x] Created `test_role_set.py` (~10 tests: membership, iteration, invalid codes)
- [x] **VERIFY** — ~45 tests pass
  - [x] All domain tests pass
  - [x] No import errors
  - [x] Existing tests unaffected
- [x] **GIT** — Committed (Codex only)

---

### T-03: Model Validator + Property Tests (~60 tests)
- [x] **ANALYZE** — Read all model files for @validates and @property
  - [x] Complete list of validators and properties per model
- [x] **EXECUTE** — Create tests
  - [x] Created `test_validators.py` (~30 tests: email, phone, score, total, currency)
  - [x] Created `test_helper_properties.py` (~25 tests: is_active, is_expired, is_overdue, etc.)
  - [x] Created `test_repr.py` (~10 tests: no sensitive data leaks)
- [x] **VERIFY** — ~60 tests pass
  - [x] All model tests pass
  - [x] No test isolation issues
  - [x] Existing tests unaffected
- [x] **GIT** — Committed (Codex only)

---

### T-04: Permission + ABAC Unit Tests (~40 tests)
- [x] **ANALYZE** — Read permissions.py (622 lines), abac.py
  - [x] Created permission matrix (20+ permissions × 8 roles)
- [x] **EXECUTE** — Create tests
  - [x] Created `test_permissions.py` (~25 tests: hierarchy, effective perms, role_has_permission)
  - [x] Created `test_abac.py` (~15 tests: owner scope, parent-child, teacher-class, student-teacher)
- [x] **VERIFY** — ~40 tests pass
  - [x] Permission count sanity check per role
  - [x] All core tests pass
- [x] **GIT** — Committed (Codex only)

---

### T-05: LMS Service Unit Tests (~65 tests)
- [ ] **ANALYZE** — Read grading_service, assignment_service, quiz_service, _helpers
  - [ ] Listed every method with happy/error paths
- [ ] **EXECUTE** — Create tests
  - [ ] Created `test_grading_service.py` (~25 tests)
  - [ ] Created `test_assignment_service.py` (~20 tests)
  - [ ] Created `test_quiz_service.py` (~20 tests)
- [ ] **VERIFY** — ~65 tests pass, no real DB calls
- [ ] **GIT** — Committed (Codex only)

---

### T-06: Billing + Auth + Attendance Service Tests (~60 tests)
- [ ] **ANALYZE** — Read billing, payment_plan, attendance_analytics, auth services
  - [ ] Listed methods and edge cases
- [ ] **EXECUTE** — Create tests
  - [ ] Created `test_billing_service.py` (~25 tests: invoices, sibling discounts, late fees)
  - [ ] Created `test_auth_service.py` (~20 tests: login, impersonation, tokens)
  - [ ] Created `test_attendance_service.py` (~15 tests: thresholds, rates, trends)
- [ ] **VERIFY** — ~60 tests pass, no DB connections
  - [ ] Total unit tests so far: ~165+
- [ ] **GIT** — Committed (Codex only)

---

### T-07: Communication + School + Other Service Tests (~50 tests)
- [ ] **ANALYZE** — Read communication, school, timetable, gradebook, reports services
- [ ] **EXECUTE** — Create tests
  - [ ] Created `test_communication_service.py` (~15 tests)
  - [ ] Created `test_school_service.py` (~10 tests)
  - [ ] Created `test_timetable_service.py` (~15 tests)
  - [ ] Created `test_gradebook_service.py` (~15 tests)
  - [ ] Created `test_report_service.py` (~10 tests)
- [ ] **VERIFY** — ~50 tests pass
  - [ ] Total unit tests: ~210+
- [ ] **GIT** — Committed (Codex only)

---

### T-08: API Integration Tests (~80 tests)
- [ ] **ANALYZE** — Read all API endpoint files, map routes × auth × status codes
- [ ] **EXECUTE** — Create tests
  - [ ] Created `test_schools_api.py` (~20 tests)
  - [ ] Created `test_gradebook_api.py` (~15 tests)
  - [ ] Created `test_rubrics_api.py` (~15 tests)
  - [ ] Created `test_billing_api.py` (~15 tests)
  - [ ] Created `test_attendance_analytics_api.py` (~10 tests)
  - [ ] Created `test_timetable_api.py` (~10 tests)
- [ ] **VERIFY** — ~80 tests pass against testcontainer DB
  - [ ] No 500 status codes in happy paths
- [ ] **GIT** — Committed (Codex only)

---

### T-09: Database Repository Integration Tests (~40 tests)
- [ ] **ANALYZE** — Read school, LMS, billing repositories
- [ ] **EXECUTE** — Create tests
  - [ ] Created `test_school_repo.py` (~15 tests)
  - [ ] Created `test_lms_repo.py` (~15 tests)
  - [ ] Created `test_billing_repo.py` (~10 tests)
- [ ] **VERIFY** — ~40 tests pass, real SQL executed
- [ ] **GIT** — Committed (Codex only)

---

### T-10: RBAC + ABAC Security Matrix (~120 tests)
- [ ] **ANALYZE** — Map full endpoint × role matrix
- [ ] **EXECUTE** — Create tests
  - [ ] Created `test_rbac_matrix.py` (~80 tests: 7 groups × 8 roles)
  - [ ] Created `test_abac_parent_child.py` (~15 tests)
  - [ ] Created `test_abac_student_teacher.py` (~15 tests)
  - [ ] Created `test_abac_teacher_class.py` (~10 tests)
  - [ ] Created `test_permission_escalation.py` (~10 tests)
- [ ] **VERIFY** — ~120 tests pass, no 500s
- [ ] **GIT** — Committed (Codex only)

---

### T-11: Edge Case + Boundary + Time Tests (~80 tests)
- [ ] **ANALYZE** — Review all validators/services for untested edge cases
- [ ] **EXECUTE** — Create tests
  - [ ] Created `test_boundary_values.py` (~30 tests: numeric, string, Unicode, pagination)
  - [ ] Created `test_time_dependent.py` (~25 tests: freezegun, timezone, DST)
  - [ ] Created `test_error_paths.py` (~25 tests: not found, duplicates, state transitions)
- [ ] **VERIFY** — ~80 tests pass
- [ ] **GIT** — Committed (Codex only)

---

### T-12: Performance + Contract Tests (~50 tests)
- [ ] **ANALYZE** — Understand benchmark targets and contract schemas
- [ ] **EXECUTE** — Create tests
  - [ ] Created `test_benchmarks.py` (~20 tests: permission <1ms, grade <0.1ms)
  - [ ] Created `test_load_patterns.py` (~10 tests: concurrent ops, batch)
  - [ ] Created `test_api_contracts.py` (~15 tests: response schemas)
  - [ ] Created `test_migration_contracts.py` (~5 tests: upgrade/downgrade)
- [ ] **VERIFY** — ~50 tests pass
- [ ] **GIT** — Committed (Codex only)

---

### T-13: Coverage Gap Analysis + Fill to 90%
- [ ] **ANALYZE** — Run coverage, identify files below 90% line / 85% branch
- [ ] **EXECUTE** — Write targeted tests for uncovered paths
  - [ ] Filled coverage gaps in services
  - [ ] Filled coverage gaps in core
  - [ ] Filled coverage gaps in models
  - [ ] Filled coverage gaps in repositories
- [ ] **VERIFY** — Coverage targets met
  - [ ] Line coverage ≥ 90%
  - [ ] Branch coverage ≥ 85%
  - [ ] Total tests: ~1,200+
  - [ ] All tests pass
- [ ] **GIT** — Committed (Codex only)

---

## PART 2: CI/CD & INFRASTRUCTURE (CI-01 → CI-12)

### CI-01: Pre-commit Hooks
- [ ] **ANALYZE** — Read Makefile, ruff config, existing hooks
- [ ] **EXECUTE**
  - [ ] Created `.pre-commit-config.yaml` (ruff, detect-secrets, conventional commits, alembic heads, pre-commit-hooks)
  - [ ] Generated `.secrets.baseline`
  - [ ] Added `hooks-install` Makefile target
- [ ] **VERIFY** — YAML valid, baseline valid, target exists
- [ ] **GIT** — Committed (Codex only)

---

### CI-02: CI Pipeline Hardening
- [ ] **ANALYZE** — Read ci.yml, understand current 10-stage pipeline
- [ ] **EXECUTE**
  - [ ] Added matrix strategy (Python 3.12/3.13 × PostgreSQL 15/16/17)
  - [ ] Added pip/npm dependency caching
  - [ ] Added Trivy container scanning job
  - [ ] Added pip-audit job
  - [ ] Added Bandit static analysis job
  - [ ] Added migration safety job (forward/downgrade/re-forward)
  - [ ] Added migration head conflict check
  - [ ] Added [tool.bandit] to pyproject.toml
- [ ] **VERIFY** — YAML valid, correct job dependencies, TOML valid
- [ ] **GIT** — Committed (Codex only)

---

### CI-03: Docker Build Optimization
- [ ] **ANALYZE** — Read backend/Dockerfile
- [ ] **EXECUTE**
  - [ ] Rewrote Dockerfile with BuildKit syntax
  - [ ] Added cache mounts for pip
  - [ ] Added test stage (ruff lint+format check)
  - [ ] Production: non-root user, 4 workers, healthcheck
- [ ] **VERIFY** — All stages defined, syntax valid
- [ ] **GIT** — Committed (Codex only)

---

### CI-04: Container Registry + Versioned Tags
- [ ] **ANALYZE** — Read ci.yml for publish placement
- [ ] **EXECUTE**
  - [ ] Added publish-images job (ghcr.io, SHA tags)
  - [ ] Added SBOM generation
  - [ ] Created cleanup-images.yml (weekly)
- [ ] **VERIFY** — YAML valid, correct gating on main push
- [ ] **GIT** — Committed (Codex only)

---

### CI-05: PgBouncer Connection Pooling
- [ ] **ANALYZE** — Read docker-compose.prod.yml, database.py
- [ ] **EXECUTE**
  - [ ] Added pgbouncer service to prod + staging compose
  - [ ] Updated DATABASE_URL to pgbouncer:6432
  - [ ] Added statement_cache_size=0 to connect_args
- [ ] **VERIFY** — Compose validates, cache setting present
- [ ] **GIT** — Committed (Codex only)

---

### CI-06: Read Replica + DB Routing
- [ ] **ANALYZE** — Read postgres config, init.sql, database.py, config.py
- [ ] **EXECUTE**
  - [ ] Added replicator role to init.sql
  - [ ] Added postgres-replica service
  - [ ] Created db_routing.py (get_read_db, get_write_db)
  - [ ] Added DATABASE_REPLICA_URL to config + .env.example
- [ ] **VERIFY** — Compose validates, routing importable, env documented
- [ ] **GIT** — Committed (Codex only)

---

### CI-07: Automated Backups + S3
- [ ] **ANALYZE** — Read existing backup scripts
- [ ] **EXECUTE**
  - [ ] Created backup-s3.sh (pg_dump + gzip + S3 upload)
  - [ ] Created restore-drill.sh (download + restore + validate)
  - [ ] Made scripts executable
  - [ ] Added Makefile targets + .env.example + DEPLOYMENT.md cron docs
- [ ] **VERIFY** — shellcheck passes, scripts executable, S3_BUCKET documented
- [ ] **GIT** — Committed (Codex only)

---

### CI-08: OpenTelemetry APM
- [ ] **ANALYZE** — Read requirements, config, main.py, monitoring compose
- [ ] **EXECUTE**
  - [ ] Added OTel packages to requirements.txt
  - [ ] Created telemetry.py (setup_telemetry)
  - [ ] Added ENABLE_TRACING + OTEL_EXPORTER_ENDPOINT to config
  - [ ] Integrated in main.py (guarded)
  - [ ] Created tempo.yml + added Tempo service
  - [ ] Added Tempo datasource to Grafana
- [ ] **VERIFY** — pip install OK, telemetry importable, compose validates
- [ ] **GIT** — Committed (Codex only)

---

### CI-09: Business Metrics + Log Alerting
- [ ] **ANALYZE** — Read metrics.py, service files, loki config, dashboards
- [ ] **EXECUTE**
  - [ ] Created business_metrics.py (7 education metrics)
  - [ ] Added metric calls to service methods
  - [ ] Created business-education.json dashboard (7 panels)
  - [ ] Added Loki ruler config
  - [ ] Created ecole-alerts.yml (5 alert rules)
- [ ] **VERIFY** — Metrics importable, JSON valid, YAML valid
- [ ] **GIT** — Committed (Codex only)

---

### CI-10: Security Hardening
- [ ] **ANALYZE** — Read nginx-prod.conf, scripts, .github/
- [ ] **EXECUTE**
  - [ ] Created rotate-secrets.sh (jwt, db, redis, all)
  - [ ] Updated nginx with WAF rules + per-user rate limiting
  - [ ] Created dependabot.yml (4 ecosystems)
  - [ ] Created dependabot-automerge.yml
  - [ ] Added Makefile rotate targets
- [ ] **VERIFY** — shellcheck OK, YAML valid, nginx rules present
- [ ] **GIT** — Committed (Codex only)

---

### CI-11: Blue-Green Deployment
- [ ] **ANALYZE** — Read prod compose, nginx, deploy scripts
- [ ] **EXECUTE**
  - [ ] Created docker-compose.blue.yml
  - [ ] Created docker-compose.green.yml
  - [ ] Created blue-green-deploy.sh
  - [ ] Created upstream.conf
  - [ ] Updated nginx-prod.conf include
  - [ ] Added Makefile deploy targets
- [ ] **VERIFY** — Both compose files validate, script passes shellcheck
- [ ] **GIT** — Committed (Codex only)

---

### CI-12: Developer Onboarding + Documentation
- [ ] **ANALYZE** — Read Makefile, .env.example, main.py
- [ ] **EXECUTE**
  - [ ] Created seed_demo.py (Lycée Mohammed V, users, courses, billing)
  - [ ] Added Makefile targets: dev-init, dev-reset, seed-demo
  - [ ] Created docs.yml (Redoc → GitHub Pages)
  - [ ] Added Makefile targets: docs, docs-schema
- [ ] **VERIFY** — seed_demo importable, targets exist, YAML valid
- [ ] **GIT** — Committed (Codex only)

---

## Final Validation

- [ ] All 25 prompts completed
- [ ] All tests pass: `cd backend && pytest -x -q`
- [ ] Coverage ≥ 90% line, ≥ 85% branch
- [ ] CI pipeline YAML valid
- [ ] All Docker Compose files validate
- [ ] All shell scripts pass shellcheck/bash -n
- [ ] No broken imports across the project
- [ ] Total test count: ~1,200+
