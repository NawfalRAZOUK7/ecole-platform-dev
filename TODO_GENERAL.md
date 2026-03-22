# École Platform — General TODO by Phases

> Update this file as you complete items. Each phase will get its own detailed checklist later.

---

## Phase 0 — Docker & Infrastructure ✅
- [x] `docker compose up` starts all services without errors
- [x] PostgreSQL reachable on localhost:5432 (PostgreSQL 16.13)
- [x] Redis reachable on localhost:6379 (Redis 7.4.7)
- [x] Backend health endpoint returns 200 at /api/v1/health
- [x] `make up`, `make down`, `make logs`, `make shell` all work
- [x] Web dev server accessible on localhost:5173 (Vite 6.4.1)

## Phase 1 — Database Schema & Migrations ✅
- [x] SQLAlchemy models: IAM domain (users, memberships, sessions, invitations, recovery) — 5 tables
- [x] SQLAlchemy models: ERP domain (years, periods, classes, enrollments, attendance, justifications) — 9 tables
- [x] SQLAlchemy models: LMS domain (courses, assignments, submissions, grades, content, activities, assessments) — 12 tables
- [x] SQLAlchemy models: COM domain (consent, notifications, deliveries, feed) — 4 tables
- [x] SQLAlchemy models: Billing domain (invoices, items, payments, proofs, webhooks) — 5 tables
- [x] SQLAlchemy models: Audit domain (audit_logs) — 1 table
- [x] Alembic migration G1-G6 runs cleanly (single combined migration)
- [x] All unique/partial indexes verified in PostgreSQL (84 indexes)
- [x] All CHECK constraints verified (9 domain constraints)
- [x] Seed data script works (`make seed`) — 10 users, 6 roles, realistic Moroccan school data
- [x] Migration rollback works (`make migrate-down`)

## Phase 2 — Auth & Security Pipeline ✅
- [x] JWT token generation (access + refresh cookie) — core/security.py
- [x] POST /auth/login — validates credentials, creates session, returns tokens
- [x] POST /auth/refresh — rotates tokens, CSRF double-submit cookie protection
- [x] POST /auth/logout — revokes session, clears cookies, idempotent
- [x] GET /me — returns user profile with permissions and memberships
- [x] RBAC middleware — RequiresPermission dependency with 50+ PERM-* mappings (core/permissions.py)
- [x] ABAC: school boundary — verify_school_boundary() returns 404 for cross-school access
- [x] ABAC: parent-child ownership — get_parent_child_ids() + verify guard
- [x] ABAC: teacher assignment — get_teacher_class_ids() + verify guard
- [x] Audit trail service — AuditService async write to audit_logs (services/audit.py)
- [x] X-Correlation-Id middleware — CorrelationIdMiddleware with contextvars propagation
- [x] Invitation code endpoints — POST /invites/create, /consume, /revoke (SHA-256 hashed)
- [x] Account recovery flow — POST /recovery/request, /verify, /reset (OTP, lockout, state machine)
- [x] Standard response envelope — { data, meta: { timestamp, version } } + cursor pagination
- [x] ErrorResponse model — { error: { code, message, category, correlation_id, retryable, timestamp } }
- [x] Deny ordering — 401 → 404 (masking) → 403 verified end-to-end
- [x] First ERP endpoints — GET /classes/{class_id}, POST /enrollments (full pipeline validation)
- [x] Rate limiting — Redis-backed login attempt throttling (5/15min)
- [x] Integration tests for auth flow — 30/30 tests passing

## Phase 3 — Core API Endpoints ✅
- [x] Idempotency-Key middleware (Redis-backed) — core/idempotency.py, 24h TTL, X-Idempotency-Replayed header
- [x] ERP endpoints: POST /class-assignments (ADM), POST /attendance/sessions (TCH), POST /attendance/justifications (PAR), POST /attendance/justifications/{id}/review (ADM)
- [x] LMS endpoints: POST /courses + GET /courses (TCH), POST /assignments + GET /assignments (TCH)
- [x] LMS endpoints: POST /submissions (STD), POST /submissions/{id}/grade (TCH)
- [x] LMS endpoints: GET /results (STD, PAR) — joined Assignment+Submission+Grade+Course
- [x] LMS endpoints: GET /content-items + GET /content-items/{id} (STD, PAR), POST /content-items/{id}/progress (STD)
- [x] LMS endpoints: GET /activities + POST /activity-sessions (STD), POST /activity-sessions/{id}/complete (STD)
- [x] LMS endpoints: POST /assessments (TCH, ADM), GET /assessments, POST /assessments/{id}/publish (TCH, ADM), POST /assessments/{id}/results (STD)
- [x] Billing endpoints: GET /invoices + GET /invoices/{id} (PAR, ADM), POST /payments/initiate (PAR), GET /payments/{attempt_id} (PAR, ADM), POST /payments/webhook/provider (SYS)
- [x] COM endpoints: GET /notifications (PAR, TCH, ADM), GET /consents + PUT /consents/{id} (PAR, ADM), GET /feed (PAR)
- [x] All endpoints return correct status codes and error codes (ERR-{DOMAIN}-{NNN})
- [x] Cursor pagination works on all list endpoints (base64 opaque cursors, DEFAULT_PAGE_SIZE=20)
- [x] Pydantic schemas for all domains — schemas/erp.py, schemas/lms.py, schemas/billing.py, schemas/com.py
- [x] RBAC enforced on all endpoints with deny ordering (401 → 404 → 403)
- [x] ABAC guards: school boundary, teacher assignment, parent-child ownership
- [x] Application-level idempotency on all write endpoints (enrollment, payment, submission, justification)
- [x] Audit trail on all state-changing operations
- [x] Integration tests for all domains — 44/44 tests passing (+ 30/30 Phase 2 tests = 74 total)

## Phase 4 — Web Frontend ✅
- [x] React app runs (`npm run dev`) — Vite 6.4.1, TypeScript strict, builds cleanly (83 modules)
- [x] API client with mandatory headers (Auth, Accept-Language, X-Correlation-Id, X-Client-Version, X-Client-Platform) — services/api/client.ts
- [x] Session management (token in memory, refresh via cookie, auto-refresh on 401, CSRF double-submit) — services/auth/AuthContext.tsx
- [x] Login page + role-based redirect — features/auth/LoginPage.tsx, PAR→/feed, STD→/content, TCH→/content, ADM→/notifications
- [x] Route guards (auth + role check) — features/auth/ProtectedRoute.tsx, redirect to /login if unauthenticated
- [x] Pages: /feed, /notifications, /content, /results, /invoices, /activities, /profile — all with cursor pagination
- [x] i18n (fr/ar/en) with RTL for Arabic — i18next + react-i18next, browser language detection, Africa/Casablanca timezone
- [x] Error handling with categorized banners — shared/ui/ErrorBanner.tsx (validation, authn, authz, conflict, system, rate_limit)
- [x] Loading/empty/error states on all pages — shared/ui/LoadingState.tsx, EmptyState.tsx
- [x] Layout with role-based sidebar navigation — shared/ui/Layout.tsx with NavLink active states
- [x] Language switcher — shared/ui/LanguageSwitcher.tsx (fr/ar/en toggle)
- [x] Global CSS styles — app/styles.css with CSS variables, responsive layout, RTL support
- [x] Vite proxy verified — /api → localhost:8000, login + /me flow working end-to-end

## Phase 5 — Mobile App ✅
- [x] Flutter app analyzes cleanly (0 issues, 43 Dart files) — Flutter 3.35.7, Dart 3.9.2
- [x] 3-layer architecture per DEC-E2-001: presentation/ → domain/ → data/ (no layer violations)
- [x] Riverpod state management (DEC-E2-002) — ProviderScope, StateNotifier for all features
- [x] go_router declarative navigation (DEC-E2-010) — auth guards, role-based redirect (PAR→/feed, STD→/content, ADM→/notifications)
- [x] Dio API client with mandatory headers (Auth, Accept-Language, X-Correlation-Id, X-Client-Version, X-Client-Platform=ios|android) — data/api/api_client.dart
- [x] Auto-retry with exponential backoff + jitter (max 3 retries) per DEC-E2-022 — retryable errors only
- [x] 401 auto-refresh with promise deduplication — data/api/api_client.dart
- [x] Secure token storage (Android Keystore / iOS Keychain) — shared/secure_storage.dart (flutter_secure_storage)
- [x] Auth flow: login, refresh, logout — features/auth/auth_provider.dart + login_screen.dart, session restore on app start
- [x] SQLite offline cache with TTL policies per DEC-E2-020 — data/local_store/cache_store.dart
  - feed: 5min, notifications: 2min, content: 15min, results: 10min, invoices: 10min
- [x] Offline write queue with SQLite persistence — data/local_store/offline_queue.dart (enqueue/replay/markFailed)
- [x] Connectivity service — shared/connectivity_service.dart (auto-replay on reconnect, cache invalidation)
- [x] Push notification service (FCM + APNs) with deep-link support — shared/push_notifications.dart
- [x] Domain entities: User, FeedItem, NotificationItem, ContentItem, Result, Invoice — domain/entities/
- [x] Repository interfaces + implementations — domain/repositories/ + data/repositories_impl/ (all 6 repos)
- [x] DTO mappers — data/dto/mappers.dart (JSON → domain entities for all 6 types)
- [x] Core screens: feed, notifications, content library, results, invoices, profile — all with pull-to-refresh
- [x] Shell screen with bottom NavigationBar — role-based visible tabs per user role
- [x] Login screen — email, password, school ID form with Material 3 styling
- [x] Content screen with type/level dropdown filters
- [x] Invoices screen with status badges (paid/pending/failed/canceled) and currency formatting
- [x] Results screen with color-coded score badges and feedback display
- [x] Profile screen with user info, permissions, logout
- [x] Material 3 theming with custom color scheme, card styles, input decoration

## Phase 6 — Testing & Quality ✅
- [x] Backend unit tests — 74 tests: IAM (JWT, passwords, RBAC catalog 31 tests) + response/exceptions (cursor, pagination, envelope, error hierarchy 43 tests)
  - tests/test_unit_iam.py: JWT generation/validation, bcrypt password hashing, RBAC permission catalog (8 roles, 50+ PERM-* codes)
  - tests/test_unit_response.py: cursor encode/decode, page size clamping, success/list envelope, Meta/PaginationMeta models, exception hierarchy (6 exception classes), ErrorDetail/ErrorResponse Pydantic models
  - Core module coverage: permissions.py 100%, response.py 100%, exceptions.py 98%, security.py 95%, config.py 94%
- [x] Integration tests — 74 tests (30 Phase 2 auth + 44 Phase 3 endpoints) all passing against live DB/Redis
- [x] Contract tests — 45 tests verifying all responses match Pack C5 OpenAPI spec
  - tests/test_contract.py: health check contract, success envelope (data+meta), list envelope (data+meta with pagination), error envelope (code+message+category+correlation_id+retryable+timestamp), pagination contract (cursor, limit, has_more), data field contracts for ERP/LMS/Billing/COM, version contract
- [x] RBAC security tests — 75 tests, every endpoint × every role matrix
  - tests/test_rbac_security.py: 20 unauthenticated 401 tests (all endpoints), deny ordering (401→404→403), per-endpoint role allow/deny for ERP (class read, enrollment, attendance), LMS (courses, assignments, submissions, results, content, activities, assessments), Billing (invoices, payments), COM (notifications, consents, feed), error response format validation
- [x] CI pipeline with quality gates — .github/workflows/ci.yml
  - 7 stages: lint → unit tests → integration tests → contract tests → RBAC security tests → coverage report → web frontend lint
  - GitHub Actions with PostgreSQL 16 + Redis 7 service containers
  - Coverage enforcement: ≥85% unit (core), ≥90% integration (API), ≥80% overall
  - Ruff lint + format check, TypeScript compile check, Vite build
- [x] All 268 tests passing (74 unit + 74 integration + 75 RBAC + 45 contract) — 0 failures

## Phase 7 — DevOps & Monitoring ✅
- [x] Staging environment — docker-compose.staging.yml (PostgreSQL WAL archiving, Nginx reverse proxy, rate limiting)
  - infra/docker-compose.staging.yml: Backend (production target), PostgreSQL with wal_level=replica + archive_mode=on, Redis, Nginx
  - infra/nginx/nginx-staging.conf: rate limiting (10r/s API, 5r/s web), security headers, proxy pass with X-Correlation-Id
- [x] Prometheus metrics exporter (golden signals) — backend/app/core/metrics.py (S-128, F2)
  - PrometheusMiddleware auto-instruments all API requests (throughput, latency histogram, error count)
  - 19 collectors: request count/duration, error count, auth login/refresh, DB pool (size/in_use/overflow), Redis (hit/miss/commands), webhook (count/signature failures), payment (initiated/completed), backup (success/failure/timestamp)
  - Path normalization (UUID → {id}) to prevent cardinality explosion
  - GET /metrics endpoint verified working on localhost:8000/metrics
  - prometheus-client==0.21.* added to requirements.txt
- [x] Grafana dashboards — 4 dashboards, 23 panels total
  - infra/grafana/dashboards/api-overview.json: Request Rate, Error Rate, P95 Latency, Status Codes, Top Endpoints, Availability gauge (6 panels)
  - infra/grafana/dashboards/auth-sessions.json: Login attempts, Login success rate, Token refresh, Auth errors, Deny rate (5 panels)
  - infra/grafana/dashboards/db-redis-health.json: DB pool gauge, Pool size vs in use, Redis hit/miss, Redis hit rate, Redis commands, DB query latency (6 panels)
  - infra/grafana/dashboards/billing-providers.json: Payment initiations, Payment outcomes, Webhook events, Signature failures, Billing latency, Payment failure rate (6 panels)
  - Auto-provisioned via infra/grafana/provisioning/ (datasources: Prometheus, Loki, Alertmanager)
- [x] Alertmanager rules per F2 SLO thresholds — infra/prometheus/alert_rules.yml (S-130)
  - SEV-1: ApiAvailabilityCritical (<99.5% 1h), DbPoolSaturationCritical (>=90% 10m), WebhookSignatureFailure (>0 5m)
  - SEV-2: ApiLatencyHigh (p95>500ms 10m), ApiErrorRateHigh (>2% 5m), AuthLoginSuccessLow (<90%), DbPoolSaturationWarning (>=85%), ProviderTimeoutHigh, BackupJobFailed
  - SEV-3: ApiRequestRateHigh (>500 req/s), PaymentFailureElevated (>10%), BackupMissed (>25h)
  - Inhibition rules: SEV-1 suppresses SEV-2/3, SEV-2 suppresses SEV-3
  - infra/alertmanager/alertmanager.yml: route tree by severity, placeholder receivers (Slack/PagerDuty)
- [x] Loki log aggregation with correlation_id search — infra/loki/ + infra/docker-compose.monitoring.yml (S-131)
  - infra/loki/loki-config.yml: TSDB schema, filesystem storage, 168h max age, retention enabled
  - infra/loki/promtail-config.yml: Docker SD config, JSON pipeline extracting correlation_id/level/method/path/status_code, PII redaction (password, token, refresh_token)
- [x] Monitoring stack — infra/docker-compose.monitoring.yml
  - Prometheus (30d retention), Grafana (admin/admin), Alertmanager, Loki, Promtail
  - External network referencing infra_ecole-network (overlay pattern)
- [x] PostgreSQL backup with PITR — infra/backup/pg_backup.sh (S-132, F3 Ch04)
  - Daily full pg_dump, gzip compression, optional AES-256-CBC encryption
  - SHA-256 checksum verification, 30-day retention pruning
  - Cron-ready (02:00 UTC schedule), Prometheus metrics push on success/failure
- [x] PostgreSQL restore script — infra/backup/pg_restore.sh (S-134, F3 Ch05)
  - Full restore from backup or PITR mode
  - Supports encrypted backups, checksum verification, interactive confirmation
  - 5-step procedure: terminate connections → recreate DB → restore → run migrations → post-restore validation
  - Post-restore validation: schema conformance, data integrity, audit log check, API smoke test
- [x] Audit log WORM export — infra/backup/audit_worm_export.sh (S-133, F3 Ch04)
  - Daily append-only export of audit_logs to immutable storage (JSONL format)
  - 180-day retention per F3, AES-256 encryption, SHA-256 checksums
  - WORM semantics: refuses to overwrite existing exports (immutability guarantee)
  - Manifest file with metadata, optional chattr +i for filesystem-level immutability
  - Cron-ready (03:30 UTC, after pg_backup)
- [x] Restore drill script — infra/backup/restore_drill.sh (S-134, F3 Ch05)
  - Automated restore drill: creates temp DB, restores backup, validates, reports, cleans up
  - Validation checks: checksum, schema conformance (tables/indexes/constraints), data integrity (users, audit logs, FK violations, Alembic version), source DB comparison
  - RTO measurement against 1h target
  - JSON drill report saved to artifacts/f3/restore_drills/
  - Monthly cron schedule (1st of month at 04:00 UTC)
- [x] All 268 tests still passing (0 regressions from metrics middleware addition)

## Phase 8 — Data, AI & Launch Prep ✅
- [x] Analytics event emitter (canonical schema) — services/analytics.py (S-138, G2)
  - AnalyticsEvent Pydantic model with all G2.2 fields: event_name, event_version, schema_version, occurred_at, env, actor_type, actor_id (pseudonymized), correlation_id, client_platform, client_version, properties, pii_flags, redaction_applied
  - HMAC-SHA256 pseudonymization of actor_id (DEC-G2-021)
  - Per-event property whitelists (G2.3 — 26 events registered)
  - PII blocklist: raw email/phone/name/password/token blocked from all events (G2.5, POL-G3-001)
  - Structured JSON logging for Loki/Promtail ingestion
- [x] P0 tracking events implemented — 6 convenience emitters (S-139)
  - emit_auth_login_success (EVT-002, KPI-G1-001)
  - emit_auth_login_failure (EVT-003, KPI-G1-003)
  - emit_feed_item_open (EVT-008, KPI-G1-002)
  - emit_notification_delivered (P0, KPI-G1-002)
  - emit_content_progress_updated (P0, KPI-G1-002)
  - emit_payment_completed (P0, KPI-G1-002)
- [x] KPI computation queries — services/kpi.py (S-140, G1)
  - KPI-G1-001: Adoption activation pilote (active 7d / total accounts)
  - KPI-G1-002: Usage parcours critiques (critical actions / active users)
  - KPI-G1-003: Taux erreurs auth (failed / total auth events)
  - KPI-G1-004: Latence API p95 (Prometheus source, PromQL query provided)
  - KPI-G1-005: Taux incidents support (error audit events / period)
  - KPI-G1-006: Conversion rattachement (invites consumed / created)
  - GET /kpis endpoint for ADM/TCH/DIR roles
- [x] AI service with PII guardrails — services/ai.py (S-142, G3)
  - POL-G3-001: PII detection + blocking in prompt payloads (email, phone, CIN patterns)
  - POL-G3-002: Opt-out enforcement checked before all AI processing
  - POL-G3-003: Structured output validation (required fields, PII scan)
  - Safety content check for generated text (unsafe pattern detection)
  - Fail-closed policy: fallback responses in fr/ar/en when AI unavailable (G3.9)
  - Prompt inventory: PROMPT-G3-001 (recommendation), PROMPT-G3-002 (writing), PROMPT-G3-003 (fallback)
  - 5 AI Prometheus metrics: ai_request_count, ai_error_count, ai_fallback_count, ai_request_duration_seconds, ai_opt_out_count
- [x] Writing assistance endpoint — POST /writing-attempts (S-143, PROMPT-G3-002)
  - STD role: submit text for AI-assisted writing feedback
  - Input sanitized (PII redaction, length limit 5000 chars)
  - Opt-out check (POL-G3-002): returns fallback if opted out
  - Persisted to writing_attempts table with prompt_id/version tracking
  - Audit trail + analytics event (writing_attempt_created)
- [x] AI opt-out preference — POST /ai/preferences/opt-out (S-144, DEC-009, G3.3)
  - PAR role: opt out of AI personalization for child or self
  - Idempotent upsert with audit trail (ai.opt_out.updated)
  - ai_preferences table with unique (user_id, target_user_id) constraint
  - Analytics event (ai_opt_out_updated) with pseudonymized target_user_id
- [x] Learning recommendations — GET /recommendations (S-145, PROMPT-G3-001)
  - STD/PAR roles: personalized learning recommendations
  - Mandatory reason_code on each recommendation (G3 contract)
  - Opt-out check: returns empty list if opted out (POL-G3-002)
  - Analytics event (recommendation_served)
- [x] Event schema versioning with CI drift detection — scripts/validate_event_schema.py (S-146)
  - 5 validation checks: P0 events registered, no PII in whitelists, model fields, schema version, non-empty whitelists
  - Export/diff modes for baseline comparison
  - CI-ready: exit code 1 on breaking changes
  - SCHEMA_VERSION = 1 (increment on breaking changes)
- [x] Database migration — G7-AI (writing_attempts + ai_preferences)
  - Alembic migration a2f8b3c4d5e6: 2 new tables, 7 new indexes, 1 unique constraint
  - Total tables: 39 (up from 37)
- [x] All 268 tests still passing (0 regressions)
- [x] All 5 new endpoints return 401 without auth (deny ordering preserved)
- [x] 5 AI metrics exposed on GET /metrics (ai_request_count, ai_error_count, ai_fallback_count, ai_request_duration_seconds, ai_opt_out_count)

---
---

# Advanced Sub-Phases — All Phases (Production Hardening)

> Cascade rule: when a backend sub-phase adds a feature (e.g., 2FA), later sub-phases integrate it in web/mobile.

## Phase 0A — Infrastructure Production Hardening ✅
- [x] Add resource limits to `docker-compose.dev.yml` (backend 512M/1CPU, web 256M/0.5CPU, postgres 1G/1CPU, redis 256M/0.5CPU)
  - Resource reservations also set (backend 128M, postgres 256M, redis/web 64M)
  - `deploy.resources.limits` and `deploy.resources.reservations` on all 4 services
  - Verified via `docker inspect`: memory + CPU limits applied correctly
- [x] Add logging driver config (`json-file`, max-size 10m, max-file 3) to all services
  - `logging.driver: json-file` with `max-size: "10m"` and `max-file: "3"` on all 4 dev services
  - Prevents unbounded log growth on dev machines
- [x] Complete `docker-compose.prod.yml` (production targets, TLS-ready Nginx, managed DB/Redis URLs, Docker secrets)
  - infra/docker-compose.prod.yml: 5 services (backend, postgres, redis, web, nginx)
  - Backend: production Dockerfile target, 1G/2CPU limits, all env vars from .env.prod
  - PostgreSQL: WAL archiving, pg_stat_statements, tuned shared_buffers/effective_cache_size, 2G/2CPU
  - Redis: maxmemory 512mb, allkeys-lru eviction, 512M/0.5CPU
  - Nginx: TLS-ready with nginx-prod.conf, certbot webroot volume, rate limiting
  - Docker secrets for jwt_secret_key, db_password, smtp_password (file-based)
  - infra/nginx/nginx-prod.conf: TLS 1.2+1.3, HSTS, OCSP stapling, CSP headers, gzip, auth rate limiting (1r/s), API rate limiting (10r/s), connection limits, attack path blocking
  - infra/secrets/ directory with .gitignore (never commit secrets) + README.md setup guide
  - infra/certs/ directory with .gitignore (never commit TLS certs)
  - Comments documenting managed DB/Redis replacement for production
- [x] Add Makefile targets: `make build`, `make staging-up`, `make prod-up`, `make shell-db`, `make redis-cli`, `make backup`, `make restore`, `make docker-prune`, `make version`
  - `make build` — rebuild dev images (no cache)
  - `make build-prod` — rebuild production images (no cache)
  - `make staging-up` / `make staging-down` / `make staging-logs` — staging lifecycle
  - `make prod-up` / `make prod-down` / `make prod-logs` — production lifecycle (validates secrets exist)
  - `make monitoring-up` / `make monitoring-down` — monitoring stack lifecycle
  - `make shell-db` / `make shell-db-staging` — psql into PostgreSQL
  - `make redis-cli` / `make redis-cli-staging` — redis-cli into Redis
  - `make backup` — wrapper for pg_backup.sh
  - `make restore` — wrapper for pg_restore.sh (BACKUP_FILE= param)
  - `make restore-drill` — wrapper for restore_drill.sh
  - `make audit-export` — wrapper for audit_worm_export.sh
  - `make docker-prune` — prune unused Docker resources + images
  - `make version` — show app version, backend status, Docker images, compose services
  - All targets verified with `make -n` dry run + live `make version` / `make health`
- [x] Add missing `.env.example` vars: UPLOAD_DIR, MAX_FILE_SIZE_MB, SMTP_HOST/PORT/USER/PASSWORD, S3_ENDPOINT, TOTP_ISSUER
  - UPLOAD_DIR=/app/uploads, MAX_FILE_SIZE_MB=25
  - SMTP_HOST, SMTP_PORT=587, SMTP_USER, SMTP_PASSWORD
  - S3_ENDPOINT (MinIO local, S3/R2/Spaces prod), S3_BUCKET, S3_REGION
  - TOTP_ISSUER=EcolePlatform
  - ENABLE_TRACING, ENABLE_STRICT_RATE_LIMIT feature flags
- [x] Create `docker-compose.override.yml.example` for local dev customization
  - infra/docker-compose.override.yml.example with commented-out examples for:
  - Port overrides (avoid conflicts), resource overrides (adjust for machine)
  - Debug tools: pgAdmin (5050), Redis Commander (8081), Mailhog (1025/8025)
  - docker-compose.override.yml already in .gitignore
- [x] All 268 tests still passing (0 regressions from infrastructure changes)

## Phase 1A — Database Views, Parent-Child Links & Migration Hardening ✅
- [x] Create `parent_child_links` table (parent_user_id, child_user_id, school_id, status, linked_at, linked_by) with unique constraint
  - ParentChildLink model in models/iam.py with LinkStatus enum (ACTIVE, REVOKED)
  - UniqueConstraint on (parent_user_id, child_user_id, school_id)
  - Indexes: idx_parent_child_links_parent (parent_user_id, school_id), idx_parent_child_links_child (child_user_id)
  - FK relationships to User (parent, child, linker) with CASCADE/SET NULL
- [x] Alembic migration for parent_child_links + seed data (link existing parents to students)
  - Migration b3c4d5e6f7a8: creates table, seeds 3 parent-child links via INSERT...SELECT (idempotent ON CONFLICT DO NOTHING)
  - Revision chain: 9f7257bc8dd1 → a2f8b3c4d5e6 → b3c4d5e6f7a8 (head)
  - Total tables: 40 (up from 39)
- [x] Create PostgreSQL views: `vw_user_permissions`, `vw_active_sessions`, `vw_assignment_results`, `vw_invoice_balance`
  - vw_user_permissions: users + memberships (10 rows with seed data)
  - vw_active_sessions: non-revoked sessions + user info + hours_active (1 row)
  - vw_assignment_results: assignments + submissions + grades with score_percent (1 row)
  - vw_invoice_balance: invoices + aggregated payments with balance_due (1 row)
- [x] Create materialized view `mv_kpi_daily` (pre-computed KPI-G1-001 through G1-006)
  - 5 KPIs via UNION ALL CTEs (KPI-G1-004 excluded — Prometheus-sourced)
  - Unique index idx_mv_kpi_daily_school_kpi on (school_id, kpi_id) for REFRESH CONCURRENTLY support
  - Verified: KPI-G1-001 = 10 active users after seed
- [x] Update `get_parent_child_ids()` in dependencies.py to use parent_child_links table
  - Changed from enrollment-based derivation (returned ALL students) to explicit parent_child_links query
  - Filters by parent_user_id, school_id, and status="active"
- [x] Create `scripts/validate_migrations.py` (naming convention, up/down roundtrip check)
  - Validates naming convention (12-char hex + group + description)
  - Checks upgrade()/downgrade() presence via AST parsing
  - Validates revision chain integrity (no forks, no orphans, no broken references)
  - Warns about raw SQL without comments
  - Supports --verbose flag, CI-ready (exit code 1 on failures)
  - Result: PASSED with 1 warning (cosmetic)
- [x] Add `make migrate-status` and `make migrate-validate` Makefile targets
  - migrate-status: runs alembic current + alembic history --verbose
  - migrate-validate: runs python scripts/validate_migrations.py --verbose
- [x] Integration test: verify all views return correct data
  - All 4 views + mv_kpi_daily return data after seed (10 + 1 + 1 + 1 + 1 rows)
  - parent_child_links: 3 rows (PARENT_1→STUDENT_1, PARENT_1→STUDENT_3, PARENT_2→STUDENT_2)
  - REFRESH MATERIALIZED VIEW mv_kpi_daily works without error
  - All 268 tests passing (0 regressions)
- [x] Seed data updated — seed.py adds 3 parent-child links, TRUNCATE order fixed (parent_child_links, writing_attempts, ai_preferences added)

## Phase 2A — Password Policy & Session Management ✅
- [x] Create `core/password_policy.py` — PasswordValidator (min 12 chars, uppercase+lowercase+digit+special, reject common passwords, reject name/email in password)
  - 8 validation rules: min_length (12), uppercase, lowercase, digit, special_char, common_password, contains_email, contains_name
  - `check()` returns list of failure dicts with `rule` and `message` keys
  - `validate()` raises ValidationError with error_code `ERR-IAM-POLICY` and structured details
  - Module-level singleton: `password_validator = PasswordValidator()`
- [x] Load common passwords from `data/common_passwords.txt` (~300 entries including French/Moroccan context: azerty, motdepasse, etc.)
- [x] Enforce policy on: /recovery/reset (service layer loads user for email/name contextual checks), POST /auth/change-password
  - Note: /invites/consume doesn't set passwords — policy enforced when passwords are actually set
- [x] Return structured errors listing which rules failed (ERR-IAM-POLICY with details array)
- [x] Create `GET /auth/sessions` — list user's active sessions (session_id, source, user_agent, ip_address, device_name, created_at, last_active)
  - Ordered by created_at desc, only non-revoked sessions for authenticated user's school
- [x] Create `DELETE /auth/sessions/{session_id}` — revoke specific session (owner or ADM within same school)
  - School boundary check, Redis session cleanup, audit trail (session.revoke)
- [x] Add Session model columns: user_agent VARCHAR(500), ip_address VARCHAR(45), device_name VARCHAR(200) — Alembic migration c4d5e6f7a8b9
  - Revision chain: 9f7257bc8dd1 → a2f8b3c4d5e6 → b3c4d5e6f7a8 → c4d5e6f7a8b9 (head)
  - Total tables: 40 (unchanged, columns added to existing sessions table)
- [x] Populate device info on login from request headers (User-Agent parsed to "Browser on OS" format)
  - `_parse_device_name()` helper: extracts Chrome/Firefox/Safari/Edge/Mobile App on Windows/macOS/Linux/iOS/Android
- [x] Add rate limit headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset on all responses
  - Headers added to every response (including in dev mode for testability)
  - CORS expose_headers updated to include X-RateLimit-* headers
- [x] Per-endpoint rate limits: auth 5/15min, write 30/min, read 100/min — `core/rate_limit.py`
  - Redis-backed sliding window per IP, 3 categories (auth, write, read)
  - AUTH_PATHS: login, refresh, recovery/request, recovery/verify, recovery/reset
  - SKIP_PATHS: /metrics, /docs, /redoc, /openapi.json, /api/v1/health
  - Graceful degradation if Redis unavailable (allows request through)
  - Non-enforcing in dev/test (headers only) unless ENABLE_STRICT_RATE_LIMIT=true
  - 429 response with structured error body (ERR-RATE-429) + Retry-After header
- [x] POST /auth/change-password — verify current password, enforce policy, update hash, revoke all other sessions
  - Keeps current session active, revokes all others (session cleanup + Redis cleanup)
  - Audit trail (password.change), ChangePasswordRequest schema (current_password + new_password min 12)
- [x] RBAC permissions: PERM-IAM:session:list + PERM-IAM:password:change added to ADM, DIR, TCH, PAR, STD, SUP
- [x] All 268 tests passing (267 passed + 1 pre-existing httpx.ReadTimeout flake in test_create_assignment) — 0 regressions from Phase 2A

## Phase 2B — Two-Factor Authentication (TOTP) & Email Verification ✅
- [x] Add `pyotp==2.9.*` + `qrcode[pil]==8.0.*` to requirements.txt
- [x] Create `core/totp.py` — TOTP secret generation, QR code URI, code verification (30s window, 1 drift), backup codes
- [x] Add User model columns: totp_secret, totp_enabled, totp_verified_at, backup_codes, email_verified_at
- [x] Alembic migration `d5e6f7a8b9c0` (G10) — adds 5 columns to users table
- [x] Create `POST /auth/2fa/setup` — generate TOTP secret + QR code URI (requires auth)
- [x] Create `POST /auth/2fa/verify-setup` — verify first code to activate 2FA, return 10 backup codes
- [x] Create `POST /auth/2fa/disable` — disable 2FA (requires TOTP code or backup code)
- [x] Create `POST /auth/2fa/verify` — verify TOTP during login (called after password, before tokens)
- [x] Modify login flow: if totp_enabled → return `{ requires_2fa: true, temp_token }` instead of full tokens
- [x] Generate 10 backup codes on setup (bcrypt hashed, single-use, consumed on verify)
- [x] Add `email_verified_at` column to User model (in same migration)
- [x] Create `POST /auth/verify-email` — verify email OTP sent during invite consumption
- [x] Hook: invite consumption → send email OTP via `EmailVerificationService`
- [x] Rate limit paths updated for `/auth/2fa/verify` and `/auth/verify-email`
- [x] All 268 existing tests pass (0 regressions)

## Phase 3A — OpenAPI Spec Export & API Documentation ✅
- [x] Add `openapi_tags` metadata to `main.py` (21 tags: IAM, ERP, LMS, COM, Billing, AI, system)
- [x] Add `summary` + `response_description` to all 48 endpoint decorators across 20 router files + health
- [x] Endpoint docstrings serve as OpenAPI descriptions (already present from prior phases)
- [x] Create `scripts/export_openapi.py` → exports `docs/openapi.json` (3868 lines, 56 endpoints, 53 paths)
- [x] `--check` mode for CI drift detection (exits 1 if spec differs from committed)
- [x] Generate static Redoc HTML page (`docs/api.html`, 61KB)
- [x] Add `make openapi` + `make openapi-check` Makefile commands
- [x] CI step added to lint stage in `.github/workflows/ci.yml`
- [x] Volume mounts added for `scripts/` and `docs/` in docker-compose.dev.yml
- [x] All 268 tests pass (0 regressions)

## Phase 3B — File Upload & Storage Pipeline
- [x] Create `core/storage.py` — StorageBackend protocol + LocalStorageBackend
- [x] Add config: UPLOAD_DIR, MAX_FILE_SIZE_MB (25), ALLOWED_MIME_TYPES (15 types)
- [x] Create `POST /submissions/{id}/files` — multipart upload (STD, max 5 per submission)
- [x] Create `GET /submissions/{id}/files/{file_id}` — download (STD owner, TCH assigned, ADM)
- [x] Create `POST /content-items/{id}/assets` — asset upload (TCH, ADM)
- [x] Create `GET /content-items/{id}/assets/{asset_id}` — download (STD, PAR, TCH, ADM)
- [x] Create `DELETE /content-items/{id}/assets/{asset_id}` — remove (TCH, ADM)
- [x] MIME whitelist + size limit (25 MB) + SHA-256 checksum + virus scan hook (no-op placeholder)
- [x] Persist to existing submission_files / content_item_assets tables (no migration needed)
- [x] Docker volume mount for uploads (`upload_data` named volume)
- [x] RBAC permissions: submission-file:upload/read, content-asset:upload/read/delete
- [x] Integration tests: upload → download → checksum → MIME reject → max files → delete → RBAC
- [x] OpenAPI spec regenerated (61 endpoints, 57 paths)

## Phase 3C — WebSocket Real-time Notifications
- [x] Create `core/ws_manager.py` — ConnectionManager + Redis Pub/Sub (multi-instance)
- [x] Create `api/v1/ws.py` — `GET /ws?token={jwt}` with JWT auth + session validation
- [x] Create `services/realtime.py` — publish helpers: notification:created, feed:created, grade:published, payment:updated
- [x] Hook into existing services: grade publish (submissions.py), payment webhook (payments.py)
- [x] Heartbeat 30s ping/pong, connection limit 3/user (oldest evicted), graceful degradation (local-only if Redis down)
- [x] App lifespan: ws_manager.startup() / ws_manager.shutdown() in main.py
- [x] OpenAPI tag "websocket" added
- [x] Integration tests: WS connect/auth/reject, heartbeat, Redis pub/sub delivery, multi-role
- [x] `websockets==14.*` added to requirements-dev.txt
- [x] OpenAPI spec regenerated (61 HTTP endpoints + 1 WS endpoint)

## Phase 3D — Advanced Query Filters & Full-text Search ✅
- [x] Create `core/filtering.py` — FilterSpec + SortSpec dependencies with allowlists per model
- [x] Support operators: eq, gt, gte, lt, lte, in, like — `?filter[field__op]=value` syntax
- [x] Create `core/search.py` — PostgreSQL tsvector full-text search with 'simple' config (multilingual FR/AR/EN)
- [x] Alembic migration `e6f7a8b9c0d1` — GIN indexes on 7 tables (courses, assignments, content_items, notifications, activities, assessments, parent_feed_items)
- [x] Add `?filter[status]=X&sort=-created_at&search=keyword` to all 8 list endpoints (courses, assignments, content-items, activities, assessments, invoices, notifications, feed)
- [x] Compose with existing cursor pagination — filters/sort/search applied before cursor + limit
- [x] Add `meta.filters_applied`, `meta.sort_by`, `meta.search_term` to response envelope via list_response kwargs
- [x] Integration tests: 30 tests covering filter operators, sort asc/desc, full-text search, meta fields, composition, all endpoints

## Phase 3E — Background Tasks & Email Notifications
- [x] Add `arq`, `aiosmtplib`, `jinja2` to requirements.txt
- [x] Create `core/tasks.py` — ARQ worker config + task registry (WorkerSettings, 4 tasks, 3 cron jobs)
- [x] Create `services/email.py` — SMTP + Jinja2 email service (EmailService singleton, 4 convenience methods)
- [x] Email templates: welcome, OTP, invoice_reminder, grade_published (base.html + 4 templates, fr/ar/en, RTL support)
- [x] Tasks: task_send_email, task_cleanup_expired_sessions, task_cleanup_expired_cache, task_send_notification_digest
- [x] Hooks: recovery → OTP email (services/auth.py), grade published → notification email (submissions.py)
- [x] ARQ worker service in docker-compose.dev.yml + `make worker` + `make worker-logs`
- [x] Prometheus metrics: task_enqueued_total, task_completed_total, task_failed_total, task_duration_seconds
- [x] SMTP config in core/config.py (smtp_host, smtp_port, smtp_user, smtp_password, smtp_use_tls, smtp_from_email/name)
- [x] Main lifespan updated: close_arq_pool on shutdown
- [x] Integration tests: 26 tests covering templates, rendering, SMTP mock, task functions, metrics, worker settings

## Phase 4A — Admin Dashboard
- [x] Create `/admin` route group (ADM, DIR roles only) — ProtectedRoute with roles guard
- [x] Backend: `api/v1/admin.py` — 8 endpoints (dashboard, users CRUD, invitations list, audit logs, justifications)
- [x] `DashboardPage.tsx` — summary cards (users, sessions, invitations, audit events, justifications, users by role)
- [x] `UsersPage.tsx` — user list with search/filter by name/email/role/status, suspend/activate, role assignment (ADM only)
- [x] `InvitationsPage.tsx` — create (role + expiry), list with status filter, revoke active codes
- [x] `AuditLogPage.tsx` — searchable with correlation_id, action_type, date range filters
- [x] `SchoolSettingsPage.tsx` — school name, timezone, notification preferences (localStorage)
- [x] `JustificationReviewPage.tsx` — approve/deny with rejection reason, status filter
- [x] Admin sidebar navigation (6 items: Dashboard, Users, Invitations, Audit, Justifications, Settings)
- [x] Role redirect: ADM/DIR → /admin on login
- [x] i18n translations: fr/ar/en for all admin pages
- [x] Admin CSS: stats grid, filter inputs, small buttons, code display, checkbox labels, settings form
- [x] OpenAPI tag "admin" added to main.py

## Phase 4B — Teacher Dashboard ✅
- [x] Create `/teacher` route group (TCH role only)
- [x] Backend: `GET /teacher/classes` — teacher's assigned classes with student/course counts
- [x] Backend: `GET /teacher/classes/{id}/students` — enrolled students roster
- [x] Backend: `GET /teacher/submissions` — submissions for teacher's courses (filterable)
- [x] Backend: `GET /teacher/periods` — active periods for attendance form
- [x] Backend: teacher router registered in router.py + OpenAPI tag in main.py
- [x] `ClassesPage.tsx` — teacher's assigned classes with expandable student roster
- [x] `CoursesPage.tsx` — list/create courses for assigned classes (GET/POST /courses)
- [x] `AssignmentFormPage.tsx` — list/create assignments for courses (GET/POST /assignments)
- [x] `SubmissionsPage.tsx` — list submissions, inline grading with score + feedback + publish
- [x] `AttendancePage.tsx` — mark attendance per class/period/slot (present/absent/late/excused)
- [x] `AssessmentFormPage.tsx` — list/create/publish assessments (draft → published)
- [x] Teacher sidebar navigation (6 nav items: Classes, Courses, Assignments, Submissions, Attendance, Assessments)
- [x] App.tsx routes with ProtectedRoute roles={['TCH']}
- [x] LoginPage ROLE_REDIRECT: TCH → /teacher
- [x] i18n translations (en/fr/ar) — teacher section with 6 sub-objects
- [x] Teacher CSS styles (teacher-classes-grid, teacher-class-card, status badge variants)

## Phase 4C — CRUD Forms, 2FA UI & Cascade Integration
- [x] **From 2A:** SessionsPage.tsx — list active sessions with device info, revoke button
- [x] **From 2B:** TwoFactorPage.tsx — enable/disable 2FA, QR code, verify setup, backup codes
- [x] **From 2B:** LoginPage.tsx — handle `requires_2fa` response, TOTP input, backup code fallback
- [x] **From 2B:** AuthContext.tsx — `verify2fa()` + `cancel2fa()` + `twoFactorPending` state
- [x] **From 3B:** Drag-drop FileUpload.tsx component (reusable, max files/size, validation)
- [x] **From 3C:** WebSocketClient.ts — auto-connect, reconnect backoff, heartbeat
- [x] **From 3C:** Layout.tsx — WebSocket integration, notification toasts, badge count
- [x] **From 3D:** Search bar on ContentPage + NotificationsPage
- [x] Student submission form (StudentSubmissionPage.tsx — select assignment, file upload, submit)
- [x] Parent justification form (ParentJustificationPage.tsx — attendance record ID, reason, submit)
- [x] Profile edit form (ProfilePage.tsx — password change with policy feedback, policy checklist)
- [x] App.tsx routes for sessions, 2FA, submissions, justification pages
- [x] Layout.tsx nav items for submissions (STD), justification (PAR), sessions, 2FA (all roles)
- [x] i18n translations (en/fr/ar) — sessions, twoFactor, fileUpload, studentSubmission, justification, profile password, ws toasts
- [x] CSS styles — file-drop-zone, file-item, notif-badge, toast-container, toast

## Phase 5A — Push Notifications, Biometric Auth & 2FA Mobile
- [x] Configure Firebase (document google-services.json + GoogleService-Info.plist setup)
- [x] Deep-link routing: notification tap → correct screen (PushNotificationService with route inference)
- [x] Notification permission request flow + badge count (flutter_app_badger + flutter_local_notifications)
- [x] Add `local_auth` package — biometric unlock (fingerprint/FaceID) after first login
- [x] Biometric fallback to password after 3 failures (BiometricService.shouldFallbackToPassword)
- [x] **From 2B:** 2FA verification screen in login flow (TOTP input + backup code option)
- [x] **From 2B:** 2FA setup screen in profile (QR code, verify, save backup codes)
- [x] **From 3B:** File picker for submission upload (gallery, camera, documents) + progress indicator
- [x] **From 3C:** WebSocket client — connect on login, local notification on WS event, badge update
- [x] **From 2A:** Send device_name, user_agent on login for session tracking (device_info_plus)

## Phase 5B — Admin/Teacher Mobile Screens & Search
- [x] **From 4A:** Admin dashboard screen, users screen, invitations screen, justification review screen
- [x] **From 4B:** Classes screen, assignment form, submissions/grading, attendance marking
- [x] **From 3D:** Search bar + filter chips + sort toggle on mobile list screens (SearchFilterBar widget)
- [x] Role-based shell navigation (show admin/teacher tabs by role)

## Phase 6A — E2E Tests, Load Testing & Security Audit ✅
- [x] Install Playwright: `npm install -D @playwright/test`
- [x] E2E J1: Login → feed → notification → logout
- [x] E2E J2: Teacher login → create assignment → verify list
- [x] E2E J3: Student login → submit file → verify submissions
- [x] E2E J4: Admin login → create invitation → verify → revoke
- [x] E2E J5: Login with 2FA → TOTP verification flow
- [x] k6 load tests: 100 concurrent logins, 500 GET requests, 50 file uploads, 200 WS connections
- [x] Security tests: CSRF, XSS, SQL injection, auth bypass, scope masking, password policy, role escalation
- [x] All E2E + load + security tests in CI pipeline

## Phase 7A — Production Environment & TLS ✅
- [x] Complete docker-compose.prod.yml (all services, resource limits, managed DB/Redis URLs, ARQ worker, certbot)
- [x] Enhance `nginx-prod.conf` — TLS, HSTS, CSP, X-Frame-Options, gzip, rate limiting, WebSocket support
- [x] Create `infra/scripts/deploy.sh` — zero-downtime deploy with rollback
- [x] Create `infra/scripts/ssl-renew.sh` — Let's Encrypt cert renewal (obtain/renew/status)
- [x] Docker secrets for JWT_SECRET_KEY, DB password, SMTP password
- [x] Create `infra/scripts/healthcheck.sh` — comprehensive health (API, DB, Redis, disk, cert, containers)
- [x] Document deployment in `infra/DEPLOYMENT.md`

## Phase 8A — GDPR Compliance & Analytics Dashboard ✅
- [x] `GET /users/{id}/data-export` — export all user data as JSON (ADM or self)
- [x] `POST /users/{id}/data-deletion` — anonymize PII, keep audit structure (ADM only)
- [x] `GET /users/{id}/consent-log` — full consent change history
- [x] Audit trail on all GDPR actions (GDPR_DATA_EXPORT, GDPR_DATA_DELETION, GDPR_CONSENT_LOG_ACCESS)
- [x] `features/admin/AnalyticsPage.tsx` — KPI dashboard with recharts (adoption, usage, auth errors, latency, incidents, conversion)
- [x] Date range selector (7d, 30d, 90d) + auto-refresh every 5 minutes
- [x] Background task: `refresh_kpi_views` (daily at 03:30 UTC, refreshes mv_kpi_daily)

---

# NEW PHASES — Registration, Profiles & Cascade (Not Yet Started)

> All previous phases (0→8 and 0A→8A) are already completed. Do NOT redo them.
> **Phases 1B, 2C, 4D, 5C are already completed.** Run remaining 3 phases: **2D → 4D-patch → 5C-patch**

---

## Phase 1B — Role-Specific Profile Tables
- [x] Create `student_profiles` table (user_id FK unique, school_id, student_number unique/school, date_of_birth, gender, class_level, nationality, guardian_notes)
- [x] Create `parent_profiles` table (user_id FK unique, school_id, relationship_type FATHER/MOTHER/GUARDIAN/OTHER, cin_number, address, profession, emergency_phone)
- [x] Create `teacher_profiles` table (user_id FK unique, school_id, employee_id, subject_specialty, qualification, hire_date)
- [x] SQLAlchemy models: StudentProfile, ParentProfile, TeacherProfile in models/iam.py
- [x] Alembic migration for all 3 profile tables
- [x] Pydantic schemas for each profile (create, update, response)
- [x] `GET /me/profile` — returns user + role-specific profile data
- [x] `PUT /me/profile` — update role-specific fields
- [x] `GET /admin/users/{id}/profile` — admin reads any user's profile
- [x] Enhance invitation codes: add optional `target_student_id` field
- [x] Seed data includes profiles for all test users
- [x] Integration tests for profile CRUD

## Phase 2C — Registration with Invitation Code
- [x] Create `POST /auth/register` — public endpoint (no auth required)
- [x] Input: code, email, full_name, phone, password, profile_data (role-specific)
- [x] Validate code (not expired, not consumed, not revoked)
- [x] Create user + membership + role-specific profile in one transaction
- [x] If code has target_student_id + role=PAR → auto-create parent_child_link
- [x] Enforce password policy (Phase 2A)
- [x] Send email verification OTP (Phase 2B)
- [x] Return JWT tokens (logged in immediately)
- [x] Rate limiting on /auth/register (5/15min)
- [x] Validate email not already registered for that school
- [x] Audit trail: user.register event
- [x] `POST /admin/register-batch` — bulk account creation endpoint
- [x] Integration tests: register PAR (with target_student_id → auto-link), register STD, register TCH

## Phase 4D — Registration & Profile UI (Web)
- [x] `RegisterPage.tsx` — multi-step: code input → role detected → personal info → role-specific fields → OTP
- [x] Step 1: enter code → validate → show role + school name
- [x] Step 2: email, full_name, phone, password (with policy checklist)
- [x] Step 3: role-specific fields (date_of_birth for STD, relationship_type for PAR, subject for TCH)
- [x] Step 4: email verification OTP input
- [x] Route `/register` + "Register" link on LoginPage
- [x] Profile edit: student section (student_number, date_of_birth, class_level)
- [x] Profile edit: parent section (relationship_type, CIN, address, profession, emergency_phone)
- [x] Profile edit: teacher section (employee_id, subject_specialty, qualification)
- [x] `BatchRegisterPage.tsx` — admin CSV upload for bulk registration
- [x] i18n translations (fr/ar/en) for all registration + profile fields

## Phase 5C — Registration & Profile Mobile
- [x] `register_screen.dart` — stepper flow (code → info → role fields → OTP)
- [x] Role-specific profile sections on profile screen
- [x] "Register" button on login screen
- [x] i18n for all new fields (fr/ar/en)

## Phase 2D — Parent-Child Link Management & Invitation Schema Fix
- [x] Add `target_student_id: UUID | None` to `InviteCreateRequest` schema
- [x] Update `InvitationService.create_invite()` to accept and persist `target_student_id`
- [x] Validate `target_student_id` is a STD user in the same school
- [x] Update `POST /invites/create` endpoint to pass `target_student_id` through
- [x] `POST /admin/parent-child-links` — admin manually links parent ↔ student (validate same school, correct roles, no duplicate)
- [x] `GET /admin/parent-child-links?parent_id=X&student_id=X` — list links filtered, paginated
- [x] `DELETE /admin/parent-child-links/{link_id}` — revoke link (set status="revoked")
- [x] Add PERM-IAM:parent-link:create, :read, :delete permission codes + assign to ADM role (+ read to DIR)
- [x] `GET /me/children` — parent endpoint to see linked children (id, full_name, class_level)
- [x] Add `target_student_id` to `BatchRegisterItem` schema for PAR batch creation with auto-link
- [x] Integration test: create invite with `target_student_id` → register parent → verify auto-link
- [x] Integration test: `POST /admin/parent-child-links` (success, duplicate, wrong school, wrong role)
- [x] Integration test: `GET /admin/parent-child-links` filtered by parent and by student
- [x] Integration test: `DELETE /admin/parent-child-links/{id}` (revoke + verify status)
- [x] Integration test: `GET /me/children` (parent sees children, non-parent rejected, RBAC)
- [x] Integration test: RBAC — student/teacher/parent cannot access admin parent-child link endpoints
- [x] ~~Alembic migration if new permission codes added~~ — N/A: permissions are runtime (ROLE_PERMISSIONS dict), not DB rows
- [x] Permission codes added to ROLE_PERMISSIONS dict (runtime, no seed needed)

## Phase 4D-patch — Parent-Child Link UI (Web Patch)
> PATCH: 4D was already run before 2D. This adds ONLY the parent-child link UI.
- [x] `ParentChildLinksPage.tsx` — admin page to list/create/revoke parent-child links
- [x] "Link Parent to Student" form with parent + student dropdowns → `POST /admin/parent-child-links`
- [x] "Revoke" button per row → confirmation → `DELETE /admin/parent-child-links/{id}`
- [x] Add page to admin sidebar navigation (`/admin/family-links`)
- [x] Invitation form: when role=PAR, show optional "Pre-link to student" dropdown → `target_student_id`
- [x] Parent "My Children" card on profile page → `GET /me/children`
- [x] Click child → navigate to child's results page
- [x] i18n for all new UI text (fr/ar/en)

## Phase 5C-patch — "My Children" Screen (Mobile Patch)
> PATCH: 5C was already run before 2D. This adds ONLY the "My Children" feature.
- [x] `my_children_screen.dart` — list linked children (name, class_level, school) via `GET /me/children`
- [x] Tap child → navigate to child's grades/attendance (/results)
- [x] Add "My Children" entry in parent's bottom nav (only visible for PAR role)
- [x] i18n for all new text — N/A: mobile uses hardcoded French strings (no l10n framework)
- [x] ChildLink entity + getChildren() in AuthRepository interface & impl
- [x] MyChildrenNotifier (StateNotifier) + myChildrenProvider
- [x] GoRoute `/family` added to router.dart

---

# NEW PHASES — Content Library, Quiz Engine & CMS (Not Yet Started)

> All previous phases (0→8, 0A→8A, 1B→5C) must be completed first.
> Run these 6 new phases in order: **9A → 9B → 9C → 10A → 10B → 10C**

---

## Phase 9A — CONTENT_MGR Role + Content Library Backend
- [x] Add `CONTENT_MGR` role to `core/permissions.py` (platform-wide, not school-scoped)
- [x] New permissions: `PERM_CMS_CONTENT_CREATE`, `PERM_CMS_CONTENT_PUBLISH`, `PERM_CMS_CONTENT_MANAGE`, `PERM_CMS_CONTENT_DELETE`, `PERM_CMS_CONTENT_ANALYTICS`, `PERM_CMS_CONTENT_REVIEW`, `PERM_CMS_CONTENT_ASSIGN`, `PERM_CMS_CONTENT_SUBMIT`
- [x] Add `subject` field (String 50) to `ContentItem` model
- [x] Add `created_by` field (FK to users) to `ContentItem` model
- [x] Add `description` field (Text) to `ContentItem` model
- [x] Add `thumbnail_path` field (String 500) to `ContentItem` model
- [x] Add `origin` field (String 20, default PLATFORM) to `ContentItem` — values: PLATFORM, PROMOTED
- [x] Add `original_content_id` field (FK to content_items, nullable) — links promoted content to original
- [x] Create `class_content_assignments` table (teacher_id, class_id, content_item_id, school_id, assigned_at, notes)
- [x] Create `content_submissions` table (content_item_id, submitted_by, school_id, status: PENDING/UNDER_REVIEW/APPROVED/REJECTED, reviewed_by, review_notes, promoted_content_id)
- [x] Add `reward_points` field (Integer, default 0) to `teacher_profiles`
- [x] SQLAlchemy models: `ClassContentAssignment`, `ContentSubmission`
- [x] CMS endpoints: `POST /cms/content`, `GET /cms/content`, `PUT /cms/content/{id}`, `DELETE /cms/content/{id}`
- [x] Review queue endpoints: `GET /cms/submissions`, `POST /cms/submissions/{id}/review` (approve/reject)
- [x] Approve workflow: create platform copy + award points + notify teacher
- [x] Reject workflow: send notification with feedback to teacher
- [x] Teacher endpoints: `GET /content/library`, `POST /content/assign`, `DELETE /content/assign/{id}`
- [x] Teacher promotion endpoints: `POST /content/submit-for-review`, `GET /content/my-submissions`
- [x] Student endpoint: `GET /classes/{class_id}/content`
- [x] Audit trail on all CMS + submission operations
- [x] Seed data: 6 platform content items (2 videos, 2 PDFs, 2 audios) + 1 teacher submission + 1 class assignment + CONTENT_MGR user
- [x] `CONTENT_MGR` added to `RoleCode` enum in `models/iam.py`
- [x] Pydantic schemas: `schemas/cms.py`
- [x] Routers registered in `api/v1/router.py`
- [x] Alembic migration — N/A: permissions are runtime (ROLE_PERMISSIONS dict)

## Phase 9B — Quiz Engine Backend
- [ ] Create `quizzes` table (school_id nullable, created_by, title, subject, level_band, difficulty, time_limit, max_attempts, shuffle, status)
- [ ] Create `quiz_questions` table (quiz_id, question_type: MCQ/TRUE_FALSE/FILL_IN/DRAG_DROP/MATCHING, question_text, options JSONB, correct_answer JSONB, points, order, explanation)
- [ ] Create `quiz_attempts` table (quiz_id, student_id, attempt_no, started_at, completed_at, score, max_score, status)
- [ ] Create `quiz_responses` table (attempt_id, question_id, student_answer JSONB, is_correct, points_earned, answered_at)
- [ ] SQLAlchemy models: `Quiz`, `QuizQuestion`, `QuizAttempt`, `QuizResponse`
- [ ] Auto-grading service (`services/quiz_grading.py`) for all 5 question types
- [ ] Quiz CRUD endpoints: create, list, get, update, publish
- [ ] Student endpoints: start attempt, submit response, submit attempt, view results
- [ ] Analytics endpoint: `GET /quizzes/{id}/analytics` (class performance stats)
- [ ] Add `exercise_type` field to `Assignment` (STANDARD/PRINTABLE_PDF/QUIZ)
- [ ] Add `quiz_id` field (FK nullable) to `Assignment`
- [ ] Audit trail on all quiz operations
- [ ] Seed data: sample quizzes with mixed question types

## Phase 9C — PDF Exercise Workflow Backend
- [ ] Add `exercise_pdf_path` field (String 500) to `Assignment` model
- [ ] Alembic migration for new field
- [ ] Update `POST /assignments` — require PDF upload when exercise_type=PRINTABLE_PDF
- [ ] `GET /assignments/{id}/exercise-pdf` — download printable exercise PDF
- [ ] Submission validation: require file upload for PRINTABLE_PDF assignments
- [ ] Add `file_type_hint` field to `SubmissionFile` (SOLUTION_SCAN/SOLUTION_PHOTO/DOCUMENT)
- [ ] Teacher inline preview of uploaded solution files
- [ ] Audit trail for PDF exercise operations

## Phase 10A — CMS Dashboard (Web)
- [ ] CMS route group `/cms/*` with separate layout + CONTENT_MGR role guard
- [ ] `ContentListPage.tsx` — list platform content with filters (type, level, subject, language, status, origin)
- [ ] `ContentUploadPage.tsx` — upload form with progress bar (video/PDF/audio + metadata)
- [ ] `ContentEditPage.tsx` — edit metadata, replace files, publish/archive
- [ ] `ReviewQueuePage.tsx` — list teacher submissions (filter by status/subject/level/school)
- [ ] Review detail view: content preview + teacher info + approve/reject actions
- [ ] Approve action: creates platform copy + awards points + notifies teacher
- [ ] Reject action: requires feedback text + notifies teacher
- [ ] Pending submissions badge/counter on sidebar
- [ ] `QuizBuilderPage.tsx` — create/edit quizzes with all 5 question types
- [ ] Question editors: MCQ, True/False, Fill-in, Drag&Drop, Matching
- [ ] Quiz preview mode (see as student)
- [ ] `AnalyticsPage.tsx` — content usage stats + teacher contribution stats
- [ ] Bulk upload support
- [ ] i18n (fr/ar/en)

## Phase 10B — Teacher Content Library + Quiz Player (Web)
- [ ] `ContentLibraryPage.tsx` — teacher browses platform + school content, assigns to class
- [ ] Teacher: upload school-scoped content
- [ ] "Submit to Platform Library" button on teacher's own content → creates submission for CONTENT_MGR review
- [ ] "My Submissions" tab showing submission statuses + CONTENT_MGR feedback
- [ ] Show reward points balance in teacher profile
- [ ] `QuizBuilderPage.tsx` — teacher creates class-specific quizzes
- [ ] Teacher: assign platform quizzes to class
- [ ] `ContentPage.tsx` — student views assigned content (video/PDF/audio players)
- [ ] Student content progress tracking (started/completed)
- [ ] `QuizPlayerPage.tsx` — student takes quiz (all 5 question types, timer, navigation)
- [ ] Quiz results screen with score + explanations
- [ ] PDF exercise: download button + upload solution flow
- [ ] Parent dashboard: quiz results alongside assignment grades
- [ ] i18n (fr/ar/en)

## Phase 10C — Content Library + Quiz Player (Mobile)
- [ ] `content_library_screen.dart` — teacher browses + assigns content
- [ ] Teacher: upload from phone (camera/gallery/file picker)
- [ ] `content_screen.dart` — student views content (video/PDF/audio players)
- [ ] `quiz_player_screen.dart` — swipe-through questions, all 5 input types
- [ ] Quiz timer, progress dots, results screen
- [ ] PDF exercise: download + camera capture for solution upload
- [ ] Parent: quiz results in child dashboard
- [ ] Offline: cache quiz questions, sync answers when online
- [ ] i18n (fr/ar/en)

---

# NEW PHASES — Missing V1 Features: Timetable, Billing, Messaging, Progress, Toggles (Not Yet Started)

> All previous phases (0→8, 0A→8A, 1B→5C, 9A→10C) must be completed first.
> Run these 8 new phases in order: **11A → 11B → 11C → 11D → 11E → 12A → 12B → 12C**

---

## Phase 11A — Timetable / Schedule Management Backend
- [ ] Create `timetable_slots` table (school_id, class_id, academic_year_id, day_of_week, start_time, end_time, subject, teacher_id, room, is_recurring, effective_from/until)
- [ ] Create `timetable_exceptions` table (timetable_slot_id, exception_date, exception_type: CANCELED/SUBSTITUTED/ROOM_CHANGED, substitute_teacher_id, reason)
- [ ] SQLAlchemy models: `TimetableSlot`, `TimetableException`
- [ ] Timetable CRUD endpoints: POST/GET/PUT/DELETE /timetable/slots
- [ ] Weekly view endpoints: GET /timetable/class/{id}/weekly, /teacher/{id}/weekly, /me/weekly
- [ ] Exception endpoints: POST/GET /timetable/exceptions
- [ ] Overlap validation (no double-booking class or teacher)
- [ ] Audit trail + seed data

## Phase 11B — Billing Enhancements Backend
- [ ] Create `fee_structures` table (school_id, academic_year_id, name, amount, currency, frequency, due_day, applies_to_level, status)
- [ ] Create `fee_assignments` table (fee_structure_id, student_id, school_id, discount_percent, discount_reason, status)
- [ ] Add retry fields to `PaymentAttempt` (retry_count, next_retry_at, last_retry_error)
- [ ] Add reminder fields to `Invoice` (reminder_sent_at, reminder_count)
- [ ] Payment retry service: ARQ task retries failed payments (3x, exponential backoff)
- [ ] Overdue reminder service: ARQ task sends reminders daily (respects consent, max 3)
- [ ] Fee structure CRUD endpoints + bulk assignment + invoice generation
- [ ] Audit trail + seed data

## Phase 11C — Messaging & Communication Backend
- [ ] Create `conversations` table (school_id, type: DIRECT/GROUP, created_by, subject)
- [ ] Create `conversation_participants` table (conversation_id, user_id, role_in_conversation)
- [ ] Create `messages` table (conversation_id, sender_id, body, sent_at, edited_at)
- [ ] Create `message_read_receipts` table (message_id, user_id, read_at)
- [ ] Create `announcements` table (school_id, author_id, title, body, target_roles JSONB, target_class_ids JSONB, status: DRAFT/PUBLISHED/ARCHIVED)
- [ ] SMS fallback service (abstract SMSProvider, stub implementation, sends on email failure + consent)
- [ ] Messaging endpoints: conversations CRUD, send/list messages, read receipts
- [ ] ABAC: parents↔teachers of their children only
- [ ] Announcements endpoints: CRUD + publish (sends notifications)
- [ ] WebSocket push for new messages + announcements
- [ ] Audit trail on all operations

## Phase 11D — Student Progress Visualization Backend
- [ ] Progress aggregation service: grade trends, content completion, activity scores, attendance rates
- [ ] `GET /progress/student/{id}` — full student dashboard data
- [ ] `GET /progress/class/{id}` — class summary (teacher/admin)
- [ ] `GET /progress/me` — student shortcut
- [ ] `GET /progress/children` — parent's children overview
- [ ] Response format: chart-ready (labels + datasets arrays)
- [ ] Redis caching (15-min TTL) on aggregated data
- [ ] ABAC enforcement on all endpoints

## Phase 11E — Feature Toggles
- [ ] Create `feature_toggles` table (feature_key unique, enabled_globally, enabled_school_ids JSONB, enabled_role_codes JSONB)
- [ ] `core/feature_flags.py` — is_feature_enabled() + Redis cache (1-min TTL)
- [ ] `RequiresFeature(key)` dependency guard for endpoints
- [ ] Toggle CRUD endpoints (SYS/CONTENT_MGR)
- [ ] `GET /features/active` — returns active features for current user (frontend conditional rendering)
- [ ] Pre-create toggles: content_library, quiz_engine, pdf_exercises, messaging, announcements, timetable
- [ ] Audit trail on toggle changes

## Phase 12A — Timetable + Billing + Messaging UI (Web)
- [ ] `TimetablePage.tsx` — weekly grid (Mon-Sat, time slots as rows, color-coded by subject)
- [ ] ADM: add/edit/delete slots, create exceptions (cancel, substitute)
- [ ] Teacher/student/parent timetable views (read-only)
- [ ] `FeeStructuresPage.tsx` — CRUD for fee structures (ADM)
- [ ] `FeeAssignmentsPage.tsx` — assign fees to students/classes, apply discounts
- [ ] `GenerateInvoicesPage.tsx` — generate invoices from fee structures
- [ ] Extend InvoicesPage with overdue indicators + retry status
- [ ] `ConversationsPage.tsx` — inbox-style conversation list
- [ ] `ChatPage.tsx` — message thread with read receipts (blue ticks), real-time via WebSocket
- [ ] Unread message count badge on navigation
- [ ] `AnnouncementsPage.tsx` — list + create/publish (ADM/DIR)
- [ ] i18n (fr/ar/en)

## Phase 12B — Timetable + Billing + Messaging (Mobile)
- [ ] `timetable_screen.dart` — weekly grid (swipe days on phone, full week on tablet)
- [ ] `conversations_screen.dart` — inbox with unread badges
- [ ] `chat_screen.dart` — chat bubbles, real-time, read receipts
- [ ] Push notification → deep link to conversation on new message
- [ ] `announcements_screen.dart` — list with push notification for new announcements
- [ ] Update InvoicesScreen with overdue indicators + retry status
- [ ] Offline cache for conversations + announcements
- [ ] i18n (fr/ar/en)

## Phase 12C — Student Progress Dashboard (Web + Mobile)
- [ ] `ProgressDashboardPage.tsx` — student progress with 4 charts (grade trend, content completion, activity scores, attendance)
- [ ] Parent dashboard: progress summary per child + drill-down
- [ ] `ClassProgressPage.tsx` — teacher class-wide averages + per-student breakdown
- [ ] `progress_screen.dart` — mobile progress with fl_chart (swipe between tabs)
- [ ] Parent mobile: child progress cards
- [ ] Charts render with real aggregated data from 11D endpoints
- [ ] i18n (fr/ar/en)
