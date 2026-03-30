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
- [x] **ANALYZE** — Read grading_service, assignment_service, quiz_service, _helpers
  - [x] Listed every method with happy/error paths
- [x] **EXECUTE** — Create tests
  - [x] Created `test_grading_service.py` (~25 tests)
  - [x] Created `test_assignment_service.py` (~20 tests)
  - [x] Created `test_quiz_service.py` (~20 tests)
- [x] **VERIFY** — ~65 tests pass, no real DB calls
- [x] **GIT** — Committed (Codex only)

---

### T-06: Billing + Auth + Attendance Service Tests (~60 tests)
- [x] **ANALYZE** — Read billing, payment_plan, attendance_analytics, auth services
  - [x] Listed methods and edge cases
- [x] **EXECUTE** — Create tests
  - [x] Created `test_billing_service.py` (~25 tests: invoices, sibling discounts, late fees)
  - [x] Created `test_auth_service.py` (~20 tests: login, impersonation, tokens)
  - [x] Created `test_attendance_service.py` (~15 tests: thresholds, rates, trends)
- [x] **VERIFY** — ~60 tests pass, no DB connections
  - [x] Total unit tests so far: ~165+
- [x] **GIT** — Committed (Codex only)

---

### T-07: Communication + School + Other Service Tests (~50 tests)
- [x] **ANALYZE** — Read communication, school, timetable, gradebook, reports services
- [x] **EXECUTE** — Create tests
  - [x] Created `test_communication_service.py` (~15 tests)
  - [x] Created `test_school_service.py` (~10 tests)
  - [x] Created `test_timetable_service.py` (~15 tests)
  - [x] Created `test_gradebook_service.py` (~15 tests)
  - [x] Created `test_report_service.py` (~10 tests)
- [x] **VERIFY** — ~50 tests pass
  - [x] Total unit tests: ~210+
- [x] **GIT** — Committed (Codex only)

---

### T-08: API Integration Tests (~80 tests)
- [x] **ANALYZE** — Read all API endpoint files, map routes × auth × status codes
- [x] **EXECUTE** — Create tests
  - [x] Created `test_schools_api.py` (~20 tests)
  - [x] Created `test_gradebook_api.py` (~15 tests)
  - [x] Created `test_rubrics_api.py` (~15 tests)
  - [x] Created `test_billing_api.py` (~15 tests)
  - [x] Created `test_attendance_analytics_api.py` (~10 tests)
  - [x] Created `test_timetable_api.py` (~10 tests)
- [x] **VERIFY** — ~80 tests pass against testcontainer DB
  - [x] No 500 status codes in happy paths
- [x] **GIT** — Committed (Codex only)

---

### T-09: Database Repository Integration Tests (~40 tests)
- [x] **ANALYZE** — Read school, LMS, billing repositories
- [x] **EXECUTE** — Create tests
  - [x] Created `test_school_repo.py` (~15 tests)
  - [x] Created `test_lms_repo.py` (~15 tests)
  - [x] Created `test_billing_repo.py` (~10 tests)
- [x] **VERIFY** — ~40 tests pass, real SQL executed
- [x] **GIT** — Committed (Codex only)

---

### T-10: RBAC + ABAC Security Matrix (~120 tests)
- [x] **ANALYZE** — Map full endpoint × role matrix
- [x] **EXECUTE** — Create tests
  - [x] Created `test_rbac_matrix.py` (~80 tests: 7 groups × 8 roles)
  - [x] Created `test_abac_parent_child.py` (~15 tests)
  - [x] Created `test_abac_student_teacher.py` (~15 tests)
  - [x] Created `test_abac_teacher_class.py` (~10 tests)
  - [x] Created `test_permission_escalation.py` (~10 tests)
- [x] **VERIFY** — ~120 tests pass, no 500s
- [x] **GIT** — Committed (Codex only)

---

### T-11: Edge Case + Boundary + Time Tests (~80 tests)
- [x] **ANALYZE** — Review all validators/services for untested edge cases
- [x] **EXECUTE** — Create tests
  - [x] Created `test_boundary_values.py` (~30 tests: numeric, string, Unicode, pagination)
  - [x] Created `test_time_dependent.py` (~25 tests: freezegun, timezone, DST)
  - [x] Created `test_error_paths.py` (~25 tests: not found, duplicates, state transitions)
- [x] **VERIFY** — ~80 tests pass
- [x] **GIT** — Committed (Codex only)

---

### T-12: Performance + Contract Tests (~50 tests)
- [x] **ANALYZE** — Understand benchmark targets and contract schemas
- [x] **EXECUTE** — Create tests
  - [x] Created `test_benchmarks.py` (~20 tests: permission <1ms, grade <0.1ms)
  - [x] Created `test_load_patterns.py` (~10 tests: concurrent ops, batch)
  - [x] Created `test_api_contracts.py` (~15 tests: response schemas)
  - [x] Created `test_migration_contracts.py` (~5 tests: upgrade/downgrade)
- [x] **VERIFY** — ~50 tests pass
- [x] **GIT** — Committed (Codex only)

---

### T-13: Coverage Gap Analysis + Fill to 90%
- [x] **ANALYZE** — Run coverage, identify files below 90% line / 85% branch
- [x] **EXECUTE** — Write targeted tests for uncovered paths
  - [x] Filled coverage gaps in services
  - [x] Filled coverage gaps in core
  - [x] Filled coverage gaps in models
  - [x] Filled coverage gaps in repositories
- [x] **VERIFY** — Coverage targets met
  - [x] Line coverage ≥ 90%
  - [x] Branch coverage ≥ 85%
  - [x] Total tests: ~1,200+
  - [x] All tests pass
- [x] **GIT** — Committed (Codex only)

---

## PART 2: CI/CD & INFRASTRUCTURE (CI-01 → CI-12)

### CI-01: Pre-commit Hooks
- [x] **ANALYZE** — Read Makefile, ruff config, existing hooks
- [x] **EXECUTE**
  - [x] Created `.pre-commit-config.yaml` (ruff, detect-secrets, conventional commits, alembic heads, pre-commit-hooks)
  - [x] Generated `.secrets.baseline`
  - [x] Added `hooks-install` Makefile target
- [x] **VERIFY** — YAML valid, baseline valid, target exists
- [x] **GIT** — Committed (Codex only)

---

### CI-02: CI Pipeline Hardening
- [x] **ANALYZE** — Read ci.yml, understand current 10-stage pipeline
- [x] **EXECUTE**
  - [x] Added matrix strategy (Python 3.12/3.13 × PostgreSQL 15/16/17)
  - [x] Added pip/npm dependency caching
  - [x] Added Trivy container scanning job
  - [x] Added pip-audit job
  - [x] Added Bandit static analysis job
  - [x] Added migration safety job (forward/downgrade/re-forward)
  - [x] Added migration head conflict check
  - [x] Added [tool.bandit] to pyproject.toml
- [x] **VERIFY** — YAML valid, correct job dependencies, TOML valid
- [x] **GIT** — Committed (Codex only)

---

### CI-03: Docker Build Optimization
- [x] **ANALYZE** — Read backend/Dockerfile
- [x] **EXECUTE**
  - [x] Rewrote Dockerfile with BuildKit syntax
  - [x] Added cache mounts for pip
  - [x] Added test stage (ruff lint+format check)
  - [x] Production: non-root user, 4 workers, healthcheck
- [x] **VERIFY** — All stages defined, syntax valid
- [x] **GIT** — Committed (Codex only)

---

### CI-04: Container Registry + Versioned Tags
- [x] **ANALYZE** — Read ci.yml for publish placement
- [x] **EXECUTE**
  - [x] Added publish-images job (ghcr.io, SHA tags)
  - [x] Added SBOM generation
  - [x] Created cleanup-images.yml (weekly)
- [x] **VERIFY** — YAML valid, correct gating on main push
- [x] **GIT** — Committed (Codex only)

---

### CI-05: PgBouncer Connection Pooling
- [x] **ANALYZE** — Read docker-compose.prod.yml, database.py
- [x] **EXECUTE**
  - [x] Added pgbouncer service to prod + staging compose
  - [x] Updated DATABASE_URL to pgbouncer:6432
  - [x] Added statement_cache_size=0 to connect_args
- [x] **VERIFY** — Compose validates, cache setting present
- [x] **GIT** — Committed (Codex only)

---

### CI-06: Read Replica + DB Routing
- [x] **ANALYZE** — Read postgres config, init.sql, database.py, config.py
- [x] **EXECUTE**
  - [x] Added replicator role to init.sql
  - [x] Added postgres-replica service
  - [x] Created db_routing.py (get_read_db, get_write_db)
  - [x] Added DATABASE_REPLICA_URL to config + .env.example
- [x] **VERIFY** — Compose validates, routing importable, env documented
- [x] **GIT** — Committed (Codex only)

---

### CI-07: Automated Backups + S3
- [x] **ANALYZE** — Read existing backup scripts
- [x] **EXECUTE**
  - [x] Created backup-s3.sh (pg_dump + gzip + S3 upload)
  - [x] Created restore-drill.sh (download + restore + validate)
  - [x] Made scripts executable
  - [x] Added Makefile targets + .env.example + DEPLOYMENT.md cron docs
- [x] **VERIFY** — shellcheck passes, scripts executable, S3_BUCKET documented
- [x] **GIT** — Committed (Codex only)

---

### CI-08: OpenTelemetry APM
- [x] **ANALYZE** — Read requirements, config, main.py, monitoring compose
- [x] **EXECUTE**
  - [x] Added OTel packages to requirements.txt
  - [x] Created telemetry.py (setup_telemetry)
  - [x] Added ENABLE_TRACING + OTEL_EXPORTER_ENDPOINT to config
  - [x] Integrated in main.py (guarded)
  - [x] Created tempo.yml + added Tempo service
  - [x] Added Tempo datasource to Grafana
- [x] **VERIFY** — pip install OK, telemetry importable, compose validates
- [x] **GIT** — Committed (Codex only)

---

### CI-09: Business Metrics + Log Alerting
- [x] **ANALYZE** — Read metrics.py, service files, loki config, dashboards
- [x] **EXECUTE**
  - [x] Created business_metrics.py (7 education metrics)
  - [x] Added metric calls to service methods
  - [x] Created business-education.json dashboard (7 panels)
  - [x] Added Loki ruler config
  - [x] Created ecole-alerts.yml (5 alert rules)
- [x] **VERIFY** — Metrics importable, JSON valid, YAML valid
- [x] **GIT** — Committed (Codex only)

---

### CI-10: Security Hardening
- [x] **ANALYZE** — Read nginx-prod.conf, scripts, .github/
- [x] **EXECUTE**
  - [x] Created rotate-secrets.sh (jwt, db, redis, all)
  - [x] Updated nginx with WAF rules + per-user rate limiting
  - [x] Created dependabot.yml (4 ecosystems)
  - [x] Created dependabot-automerge.yml
  - [x] Added Makefile rotate targets
- [x] **VERIFY** — shellcheck OK, YAML valid, nginx rules present
- [x] **GIT** — Committed (Codex only)

---

### CI-11: Blue-Green Deployment
- [x] **ANALYZE** — Read prod compose, nginx, deploy scripts
- [x] **EXECUTE**
  - [x] Created docker-compose.blue.yml
  - [x] Created docker-compose.green.yml
  - [x] Created blue-green-deploy.sh
  - [x] Created upstream.conf
  - [x] Updated nginx-prod.conf include
  - [x] Added Makefile deploy targets
- [x] **VERIFY** — Both compose files validate, script passes shellcheck
- [x] **GIT** — Committed (Codex only)

---

### CI-12: Developer Onboarding + Documentation
- [x] **ANALYZE** — Read Makefile, .env.example, main.py
- [x] **EXECUTE**
  - [x] Created seed_demo.py (Lycée Mohammed V, users, courses, billing)
  - [x] Added Makefile targets: dev-init, dev-reset, seed-demo
  - [x] Created docs.yml (Redoc → GitHub Pages)
  - [x] Added Makefile targets: docs, docs-schema
- [x] **VERIFY** — seed_demo importable, targets exist, YAML valid
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
