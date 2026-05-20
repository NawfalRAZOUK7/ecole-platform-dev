# École Platform — Claude Prompts (One Per Phase)

> Each prompt is self-contained. Copy-paste it into a new session.
> After finishing a phase, close the session and open a new one for the next phase.

---

## Phase 0 — Docker & Infrastructure

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder, NOT ecole-platform-dev)
**Why parent?** Phase 0 only touches ecole-platform-dev/ but future phases need access to ecole-platform-jira/ and ecole-platform-report/ for specs.

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
This is a monorepo with FastAPI backend, React web, and Flutter mobile.
The skeleton is already set up.

I need you to implement Phase 0 from ecole-platform-dev/DEV_PHASES.md.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md for the full plan
- Read ecole-platform-dev/backend/app/core/ for existing config, database, security stubs
- Read ecole-platform-dev/infra/ for Docker Compose setup
- The documentation repo (ecole-platform-report/) is a sibling folder with full specs
- The Jira planning (ecole-platform-jira/) is also a sibling with stories and acceptance criteria
- Reference files to read for specs:
  - ecole-platform-jira/sprint-1.md (Sprint 1 stories with acceptance criteria)
  - ecole-platform-jira/sprint-2.md (Sprint 2 stories with acceptance criteria)
  - ecole-platform-jira/epics.md (Epic definitions with scope and DoD)
  - ecole-platform-jira/backlog.md (Full backlog with priorities)

PHASE 0 — Docker & Infra:
- Verify docker compose starts all services (postgres, redis, backend, web)
- Fix any issues with Dockerfiles, compose file, or configs
- Ensure `make up` → `make health` works end-to-end
- Test all Makefile commands work correctly
- Verify PostgreSQL is reachable on localhost:5432
- Verify Redis is reachable on localhost:6379

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command. You can run git status or git diff.
- After finishing, suggest the exact git add + git commit commands I should run manually in my terminal.
- After each completed step, update ecole-platform-dev/TODO_GENERAL.md to mark items as done.
- Do Phase 0 ONLY. When done, stop and wait — I will tell you when to start the next phase.
```

---

## Phase 1 — Database Schema & Migrations

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)
**Why parent?** Needs to read ecole-platform-jira/sprint-1.md for table specs and ecole-platform-report/ for Pack C4 data model.

```yaml
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
This is a monorepo with FastAPI backend, React web, and Flutter mobile.
Phase 0 (Docker & Infra) is done. I need you to implement Phase 1.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md for the full plan (Phase 1 section)
- Read ecole-platform-dev/backend/app/core/database.py for the existing SQLAlchemy Base
- Read ecole-platform-dev/backend/alembic/env.py for migration config
- Read ecole-platform-jira/sprint-1.md for Sprint 1 stories with acceptance criteria (table definitions, indexes, invariants)
- Read ecole-platform-jira/epics.md for EP-02 scope and definition of done
- Read ecole-platform-report/ for Pack C4 data model specs if you need more detail on any table

PHASE 1 — Database Schema & Migrations:
- Create SQLAlchemy 2.0 models (Mapped[] style, UUID PKs) for all 6 domains:
  - IAM: users, memberships, sessions, invitation_codes, account_recovery_requests
  - ERP: academic_years, periods, classes, enrollments, teacher_assignments, attendance_sessions, attendance_records, absence_justifications, justification_reviews
  - LMS: courses, assignments, submissions, submission_files, grades, assessments, assessment_results, content_items, content_item_assets, content_progress, activities, activity_sessions
  - COM: consent_preferences, notifications, notification_deliveries, parent_feed_items
  - Billing: invoices, invoice_items, payment_attempts, payment_proofs, provider_webhook_events
  - Audit: audit_logs
- One model file per domain: backend/app/models/iam.py, erp.py, lms.py, com.py, billing.py, audit.py
- Import all in backend/app/models/__init__.py
- Generate Alembic migrations in strict order: G1-IAM → G2-ERP → G3-LMS → G4-COM → G5-Billing → G6-Audit
- All unique/partial/composite indexes from sprint-1.md acceptance criteria
- All CHECK constraints and invariants (INV-IAM-*, INV-ERP-*, INV-LMS-*, etc.)
- Create seed data script at backend/app/seed.py
- Verify: `make migrate` runs cleanly, tables visible in PostgreSQL

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command. You can run git status or git diff.
- After finishing, suggest the exact git add + git commit commands I should run manually in my terminal.
- After each completed step, update ecole-platform-dev/TODO_GENERAL.md to mark items as done.
- Do Phase 1 ONLY. When done, stop and wait — I will tell you when to start the next phase.
```

---

## Phase 2 — Auth & Security Pipeline

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)
**Why parent?** Needs ecole-platform-jira/sprint-2.md for auth stories and ecole-platform-report/ for Pack C6 RBAC model.

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
This is a monorepo with FastAPI backend, React web, and Flutter mobile.
Phase 0 (Docker) and Phase 1 (Database) are done. I need you to implement Phase 2.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md for the full plan (Phase 2 section)
- Read ecole-platform-dev/TODO_GENERAL.md to see what's already done
- Read ecole-platform-dev/backend/app/models/ for the existing SQLAlchemy models
- Read ecole-platform-dev/backend/app/core/ for config, database, security stubs
- Read ecole-platform-jira/sprint-2.md for Sprint 2 stories with acceptance criteria
- Read ecole-platform-jira/epics.md for EP-03 (Auth & RBAC) scope and DoD
- Read ecole-platform-report/ for Pack C6 RBAC model and Pack D6 security enforcement if needed

PHASE 2 — Auth & Security Pipeline:
- JWT token generation/validation (access 30min + refresh 7d HttpOnly cookie) in core/security.py
- Auth endpoints: POST /auth/login, POST /auth/refresh, POST /auth/logout, GET /me
- RBAC permission middleware (@requires_permission decorator) with 50+ PERM-* mappings from C6
- ABAC guards: school boundary (cross-school → 404 masking), parent-child ownership, teacher assignment
- Audit trail service (async write to audit_logs, log all denies + sensitive allows)
- X-Correlation-Id middleware (generate/propagate/return)
- Invitation code endpoints: POST /invites/create (ADM), /consume (auth), /revoke (ADM)
- Account recovery flow: POST /recovery/request, /verify (OTP), /reset
- Standard response envelope { data, meta } with cursor pagination helper
- ErrorResponse model (error_code, category, correlation_id, retryable)
- Deny ordering enforcement: 401 → 404 (scope masking) → 403
- Write integration tests for the complete auth flow

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command. You can run git status or git diff.
- After finishing, suggest the exact git add + git commit commands I should run manually in my terminal.
- After each completed step, update ecole-platform-dev/TODO_GENERAL.md to mark items as done.
- Follow router → service → repository layer pattern per Pack D2.
- Use SQLAlchemy 2.0 async with Mapped[] type annotations.
- Do Phase 2 ONLY. When done, stop and wait — I will tell you when to start the next phase.
```

---

## Phase 3 — Core API Endpoints

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)
**Why parent?** Needs ecole-platform-jira/sprint-3.md and backlog.md for endpoint specs.

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
Phases 0-2 (Docker, Database, Auth) are done. I need you to implement Phase 3.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md for the full plan (Phase 3 section)
- Read ecole-platform-dev/TODO_GENERAL.md to see what's already done
- Read ecole-platform-dev/backend/app/ for existing models, auth, middleware
- Read ecole-platform-jira/sprint-3.md for Sprint 3 stories
- Read ecole-platform-jira/backlog.md for all EP-04 stories (Core API Endpoints)
- Read ecole-platform-report/ for Pack C5 API contract if needed

PHASE 3 — Core API Endpoints:
- Idempotency-Key middleware (Redis-backed key→response cache)
- ERP endpoints: GET /classes/{id}, POST /enrollments, POST /class-assignments, POST /attendance/sessions, POST /attendance/justifications, POST /justifications/{id}/review
- LMS endpoints: POST /courses, POST /assignments, POST /submissions, POST /submissions/{id}/grade, GET /results, GET /content-items, POST /content-items/{id}/progress, GET /activities, POST /activity-sessions, POST /activity-sessions/{id}/complete, assessment CRUD
- Billing endpoints: GET /invoices, POST /payments/initiate, GET /payments/{id}, POST /payments/webhook/provider
- COM endpoints: GET /notifications, PUT /consents/{id}, GET /feed
- All endpoints use standard response envelope, cursor pagination, RBAC checks
- Pydantic schemas for all request/response models in backend/app/schemas/
- Error codes follow ERR-{DOMAIN}-{NNN} pattern

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command. You can run git status or git diff.
- After finishing, suggest the exact git add + git commit commands I should run manually in my terminal.
- After each completed step, update ecole-platform-dev/TODO_GENERAL.md to mark items as done.
- Do Phase 3 ONLY. When done, stop and wait.
```

---

## Phase 4 — Web Frontend

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)
**Why parent?** Needs ecole-platform-jira/ for EP-05 stories and ecole-platform-report/ for Pack E1 web architecture.

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
Phases 0-3 (Docker, Database, Auth, API) are done. I need you to implement Phase 4.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md for the full plan (Phase 4 section)
- Read ecole-platform-dev/TODO_GENERAL.md to see what's already done
- Read ecole-platform-dev/web/ for the existing Vite + React skeleton
- Read ecole-platform-jira/backlog.md for all EP-05 stories (Web Frontend)
- Read ecole-platform-report/ for Pack E1 (web architecture), Pack E5 (design system) if needed

PHASE 4 — Web Frontend:
- Run npm install to set up dependencies
- Create unified API client in src/services/api/ with mandatory headers (Authorization, Accept-Language, X-Correlation-Id, X-Client-Version, X-Client-Platform=web)
- Session management: access token in memory, refresh via HttpOnly cookie, auto-refresh on 401, CSRF double-submit
- Login page (/login) with email, password, school selector
- Route guards (ProtectedRoute) with auth + role check, redirect to /login
- Feature pages: /feed, /notifications, /content-items, /results, /invoices, /activities, /me
- i18n with fr (default), ar, en — RTL layout for Arabic, Africa/Casablanca timezone
- Error handling with categorized banners (validation, authn, authz, conflict, system)
- Loading/empty/error states on all data pages

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command. You can run git status or git diff.
- After finishing, suggest the exact git add + git commit commands I should run manually in my terminal.
- After each completed step, update ecole-platform-dev/TODO_GENERAL.md to mark items as done.
- Do Phase 4 ONLY. When done, stop and wait.
```

---

## Phase 5 — Mobile App

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)
**Why parent?** Needs ecole-platform-jira/ for EP-06 stories and ecole-platform-report/ for Pack E2 mobile architecture.

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
Phases 0-4 are done. I need you to implement Phase 5.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md for the full plan (Phase 5 section)
- Read ecole-platform-dev/TODO_GENERAL.md to see what's already done
- Read ecole-platform-dev/mobile/ for the existing Flutter skeleton
- Read ecole-platform-jira/backlog.md for all EP-06 stories (Mobile App)
- Read ecole-platform-report/ for Pack E2 (mobile architecture) if needed

PHASE 5 — Mobile App (Flutter):
- flutter pub get to install dependencies
- API client with offline write queue (dio + SQLite persistence, replay on reconnect)
- Secure token storage (flutter_secure_storage for refresh token)
- Auth flow: login, refresh, logout screens with go_router navigation
- SQLite offline cache with TTL per E2: feed 5min, notifications 2min, content 15min, results 10min, invoices 10min
- Push notifications via FCM + APNs with deep-link to target screen
- Core screens: feed, notifications, content library, results, invoices
- Riverpod state management, 3-layer separation (presentation/domain/data)

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command. You can run git status or git diff.
- After finishing, suggest the exact git add + git commit commands I should run manually in my terminal.
- After each completed step, update ecole-platform-dev/TODO_GENERAL.md to mark items as done.
- Do Phase 5 ONLY. When done, stop and wait.
```

---

## Phase 6 — Testing & Quality

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
Phases 0-5 are done. I need you to implement Phase 6.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md for the full plan (Phase 6 section)
- Read ecole-platform-dev/TODO_GENERAL.md to see what's already done
- Read ecole-platform-jira/backlog.md for all EP-08 stories (Testing & Quality)
- Read ecole-platform-report/ for Pack D7 (testing strategy), Pack E6 (client testing) if needed

PHASE 6 — Testing & Quality:
- Backend unit tests for IAM, ERP, LMS, Billing services (pytest + pytest-asyncio)
- Integration tests for all P0 API endpoints (full DB, auth flow)
- Contract tests verifying endpoints against Pack C5 OpenAPI spec
- RBAC security tests: every endpoint × every role, deny ordering verification
- Frontend E2E tests for critical journeys J1-J4
- CI pipeline (GitHub Actions): lint → unit → integration → contract → security
- Coverage enforcement: ≥80% overall, ≥90% API, ≥85% business logic

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command. You can run git status or git diff.
- After finishing, suggest the exact git add + git commit commands I should run manually in my terminal.
- After each completed step, update ecole-platform-dev/TODO_GENERAL.md to mark items as done.
- Do Phase 6 ONLY. When done, stop and wait.
```

---

## Phase 7 — DevOps & Monitoring

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
Phases 0-6 are done. I need you to implement Phase 7.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md for the full plan (Phase 7 section)
- Read ecole-platform-dev/TODO_GENERAL.md to see what's already done
- Read ecole-platform-jira/backlog.md for all EP-09 stories (DevOps & Infrastructure)
- Read ecole-platform-report/ for Pack F1-F5 (deployment, monitoring, backup, incidents, runbooks) if needed

PHASE 7 — DevOps & Monitoring:
- Staging environment configuration
- Prometheus metrics exporter (golden signals: request count, error rate, latency, DB pool, Redis hit)
- Grafana dashboards for API performance, DB health, auth, billing
- Alertmanager rules per F2 SLO thresholds
- Loki log aggregation with correlation_id search
- PostgreSQL backup config (daily full + continuous WAL, PITR)
- Audit log WORM export
- Restore runbook and drill procedure

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command. You can run git status or git diff.
- After finishing, suggest the exact git add + git commit commands I should run manually in my terminal.
- After each completed step, update ecole-platform-dev/TODO_GENERAL.md to mark items as done.
- Do Phase 7 ONLY. When done, stop and wait.
```

---

## Phase 8 — Data, AI & Launch Prep

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
Phases 0-7 are done. I need you to implement Phase 8.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md for the full plan (Phase 8 section)
- Read ecole-platform-dev/TODO_GENERAL.md to see what's already done
- Read ecole-platform-jira/backlog.md for all EP-10 stories (Data, Reporting & AI)
- Read ecole-platform-report/ for Pack G1 (KPIs), G2 (analytics tracking), G3 (AI governance) if needed

PHASE 8 — Data, AI & Launch Prep:
- Analytics event emitter with canonical schema per G2 (snake_case, pseudonymized actor_id, correlation_id)
- P0 tracking events: auth_login_success, feed_item_open, notification_delivered, content_progress_updated, payment_completed
- KPI computation queries for KPI-G1-001 to KPI-G1-006
- AI request endpoint with guardrails: PII blocking (POL-G3-001), opt-out enforcement (POL-G3-002), output validation (POL-G3-003)
- Writing assistance endpoint (POST /writing-attempts)
- AI opt-out preference (POST /ai/preferences/opt-out)
- Learning recommendations endpoint (GET /recommendations)
- Event schema versioning with CI drift detection

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command. You can run git status or git diff.
- After finishing, suggest the exact git add + git commit commands I should run manually in my terminal.
- After each completed step, update ecole-platform-dev/TODO_GENERAL.md to mark items as done.
- Do Phase 8 ONLY. When done, stop and wait.
```

---

## Summary Table

| Phase | Tool | Open Folder | Focus |
|-------|------|-------------|-------|
| 0 | Claude Code | `Ecole-Platform/` (parent) | Docker, infra, make commands |
| 1 | Claude Code | `Ecole-Platform/` (parent) | SQLAlchemy models, Alembic migrations |
| 2 | Claude Code | `Ecole-Platform/` (parent) | JWT auth, RBAC, ABAC, audit |
| 3 | Claude Code | `Ecole-Platform/` (parent) | All P0 API endpoints |
| 4 | Claude Code | `Ecole-Platform/` (parent) | React web app |
| 5 | Claude Code | `Ecole-Platform/` (parent) | Flutter mobile app |
| 6 | Claude Code | `Ecole-Platform/` (parent) | Tests, CI, coverage |
| 7 | Claude Code | `Ecole-Platform/` (parent) | Monitoring, backup, stage |
| 8 | Claude Code | `Ecole-Platform/` (parent) | Analytics, AI, launch |

**All phases use Claude Code** (not Cowork) because they involve running commands, testing, and iterating on code.

**All phases open the parent `Ecole-Platform/` folder** because every phase needs access to:

- `ecole-platform-dev/` (the code)
- `ecole-platform-jira/` (the specs and stories)
- `ecole-platform-report/` (the full documentation)

---

---

# Advanced Sub-Phase Prompts — All Phases (Production Hardening)

> All 8 original phases are done. These sub-phases harden each phase in order (0→8),
> with cascade integration (backend changes → web + mobile).
> Same rules: one sub-phase per session, Claude Code, parent folder, no commits.

---

## Phase 0A — Infrastructure Production Hardening

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
All 8 original phases are done. I need you to implement Phase 0A — Infrastructure Production Hardening.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "Phase 0A" in the Advanced Sub-Phases section)
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "Phase 0A" checklist)
- Read ecole-platform-dev/infra/docker-compose.dev.yml for current dev config
- Read ecole-platform-dev/infra/docker-compose.prod.yml for current prod placeholder
- Read ecole-platform-dev/Makefile for existing targets
- Read ecole-platform-dev/.env.example for current vars

PHASE 0A:
- Add resource limits to docker-compose.dev.yml (backend 512M/1CPU, web 256M/0.5CPU, postgres 1G, redis 256M)
- Add logging driver (json-file, max-size 10m, max-file 3) to all services
- Complete docker-compose.prod.yml: production targets, TLS-ready Nginx, managed DB/Redis URL placeholders, Docker secrets
- Add Makefile targets: build, staging-up, prod-up, shell-db, redis-cli, backup, restore, docker-prune, version
- Add missing .env.example vars: UPLOAD_DIR, MAX_FILE_SIZE_MB, SMTP_HOST/PORT/USER/PASSWORD, S3_ENDPOINT, TOTP_ISSUER
- Create docker-compose.override.yml.example for local customization

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command. You can run git status or git diff.
- After finishing, suggest the exact git add + git commit commands I should run manually.
- After each completed step, update ecole-platform-dev/TODO_GENERAL.md to mark items as done.
- Do Phase 0A ONLY. When done, stop and wait.
```

---

## Phase 1A — Database Views, Parent-Child Links & Migration Hardening

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
All 8 original phases + Phase 0A are done. I need you to implement Phase 1A.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "Phase 1A")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "Phase 1A" checklist)
- Read ecole-platform-dev/backend/app/models/__init__.py for current model imports
- Read ecole-platform-dev/backend/app/models/iam.py for User/Membership models
- Read ecole-platform-dev/backend/app/core/dependencies.py for get_parent_child_ids() (currently derives from enrollments)
- Read ecole-platform-dev/backend/app/services/kpi.py for KPI queries

PHASE 1A:
- Create parent_child_links table (parent_user_id, child_user_id, school_id, status, linked_at, linked_by) with Alembic migration + seed data
- Create PostgreSQL views: vw_user_permissions, vw_active_sessions, vw_assignment_results, vw_invoice_balance
- Create materialized view mv_kpi_daily for pre-computed KPI-G1-001 through G1-006
- Update get_parent_child_ids() in dependencies.py to use parent_child_links table
- Create scripts/validate_migrations.py (naming convention, roundtrip check)
- Add make migrate-status target

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- After finishing, suggest the exact git add + git commit commands.
- Update TODO_GENERAL.md after each step.
- Do Phase 1A ONLY. When done, stop and wait.
```

---

## Phase 2A — Password Policy & Session Management

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
All 8 original phases + 0A + 1A are done. I need you to implement Phase 2A.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "Phase 2A")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "Phase 2A" checklist)
- Read ecole-platform-dev/backend/app/core/security.py for current password hashing
- Read ecole-platform-dev/backend/app/api/v1/auth.py for login/recovery endpoints
- Read ecole-platform-dev/backend/app/models/iam.py for Session model
- Read ecole-platform-dev/backend/app/core/dependencies.py for auth pipeline

PHASE 2A:
- Create core/password_policy.py: min 12 chars, uppercase+lowercase+digit+special, reject common passwords (load from data/common_passwords.txt), reject name/email in password, return structured error listing failed rules
- Enforce on: /invites/consume, /recovery/reset, profile password change
- Create GET /auth/sessions (list active sessions with device info)
- Create DELETE /auth/sessions/{session_id} (revoke, self or ADM)
- Add Session model columns: user_agent, ip_address, device_name (Alembic migration)
- Populate device info on login from request headers
- Add rate limit headers (X-RateLimit-Limit/Remaining/Reset) to all responses
- Per-endpoint rate limits: auth 5/15min, write 30/min, read 100/min

NOTE: Phase 4C will add session management UI, Phase 5A will send device info from mobile.

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- After finishing, suggest the exact git add + git commit commands.
- Update TODO_GENERAL.md after each step.
- Do Phase 2A ONLY. When done, stop and wait.
```

---

## Phase 2B — Two-Factor Authentication (TOTP) & Email Verification

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
All 8 original phases + 0A + 1A + 2A are done. I need you to implement Phase 2B.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "Phase 2B")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "Phase 2B" checklist)
- Read ecole-platform-dev/backend/app/core/security.py for JWT/password functions
- Read ecole-platform-dev/backend/app/api/v1/auth.py for login flow
- Read ecole-platform-dev/backend/app/api/v1/invitations.py for invite consumption
- Read ecole-platform-dev/backend/app/models/iam.py for User model

PHASE 2B:
- Add pyotp + qrcode[pil] to requirements.txt
- Create core/totp.py: TOTP secret generation, QR code URI, code verification (30s window, 1 drift)
- Add User model columns: totp_secret, totp_enabled, totp_verified_at, backup_codes, email_verified_at (Alembic migration)
- Create endpoints: POST /auth/2fa/setup, /2fa/verify-setup, /2fa/disable, /2fa/verify
- Modify login flow: if totp_enabled → return { requires_2fa: true, temp_token } → client calls /2fa/verify with TOTP code → get real tokens
- Generate 10 backup codes on 2FA setup (bcrypt hashed, single-use)
- Create POST /auth/verify-email: verify OTP sent during invite consumption
- Hook: invite consumption → send email OTP → must verify before active

NOTE: Phase 4C will add 2FA setup UI + login TOTP screen, Phase 5A will add mobile 2FA.

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- After finishing, suggest the exact git add + git commit commands.
- Update TODO_GENERAL.md after each step.
- Do Phase 2B ONLY. When done, stop and wait.
```

---

## Phase 3A — OpenAPI Spec Export & API Documentation

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
All 8 original phases + 0A + 1A + 2A + 2B are done. I need you to implement Phase 3A.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "Phase 3A")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "Phase 3A" checklist)
- Read ecole-platform-dev/backend/app/main.py for FastAPI app config
- Read ecole-platform-dev/backend/app/api/v1/ for all router files
- Read ecole-platform-report/ for Pack C5 API contract if needed

PHASE 3A:
- Add openapi_tags metadata to main.py (group by domain)
- Add summary + description to every router decorator (all 22+ routers)
- Add response examples to key endpoints
- Create scripts/export_openapi.py → docs/openapi.json
- CI drift detection + static Redoc page + make openapi

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- After finishing, suggest the exact git add + git commit commands.
- Update TODO_GENERAL.md after each step.
- Do Phase 3A ONLY. When done, stop and wait.
```

---

## Phase 3B — File Upload & Storage Pipeline

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
Previous phases + 3A done. I need you to implement Phase 3B.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "Phase 3B")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "Phase 3B" checklist)
- Read ecole-platform-dev/backend/app/models/lms.py for SubmissionFile and ContentItemAsset models (tables already exist)
- Read ecole-platform-dev/backend/app/api/v1/submissions.py and content.py
- Read ecole-platform-dev/backend/app/core/dependencies.py for RBAC/ABAC guards

PHASE 3B:
- Create core/storage.py: StorageBackend protocol + LocalStorageBackend
- Config: UPLOAD_DIR, MAX_FILE_SIZE_MB (25), ALLOWED_MIME_TYPES
- Upload/download/delete endpoints for submissions and content-items
- SHA-256 checksum, MIME whitelist, size limit (413), virus scan hook
- Persist to EXISTING tables (no new migration for these)
- Docker volume mount + integration tests

NOTE: Phase 4C will add drag-drop UI, Phase 5A will add mobile file picker.

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- Suggest git commands after finishing. Update TODO_GENERAL.md.
- Do Phase 3B ONLY.
```

---

## Phase 3C — WebSocket Real-time Notifications

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
Previous phases + 3B done. I need you to implement Phase 3C.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "Phase 3C")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "Phase 3C" checklist)
- Read ecole-platform-dev/backend/app/api/v1/notifications.py and feed.py
- Read ecole-platform-dev/backend/app/core/security.py for JWT validation
- Read ecole-platform-dev/backend/app/core/redis.py for Redis client

PHASE 3C:
- ConnectionManager + Redis Pub/Sub, GET /ws with JWT auth
- services/realtime.py: publish on notification/feed/grade/payment events
- Hook into existing services, heartbeat 30s, max 3 WS/user
- Integration test

NOTE: Phase 4C will add WebSocket client in React, Phase 5A in Flutter.

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- Suggest git commands. Update TODO_GENERAL.md. Phase 3C ONLY.
```

---

## Phase 3D — Advanced Query Filters & Full-text Search

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
Previous phases + 3C done. I need you to implement Phase 3D.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "Phase 3D")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "Phase 3D" checklist)
- Read ecole-platform-dev/backend/app/core/response.py for cursor pagination
- Read ecole-platform-dev/backend/app/api/v1/courses.py, content.py, notifications.py, activities.py

PHASE 3D:
- core/filtering.py: FilterParams + SortParams dependencies
- core/search.py: PostgreSQL tsvector full-text search
- GIN indexes via Alembic migration
- ?filter[status]=X&sort=-created_at&search=keyword on all list endpoints
- Compose with cursor pagination, meta.filters_applied + meta.sort_by

NOTE: Phase 4C will add search bar + filter dropdowns, Phase 5B on mobile.

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- Suggest git commands. Update TODO_GENERAL.md. Phase 3D ONLY.
```

---

## Phase 3E — Background Tasks & Email Notifications

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```yaml
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
Previous phases + 3D done. I need you to implement Phase 3E.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "Phase 3E")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "Phase 3E" checklist)
- Read ecole-platform-dev/backend/app/services/ for services to hook into
- Read ecole-platform-dev/backend/app/core/redis.py and metrics.py
- Read ecole-platform-dev/infra/docker-compose.dev.yml

PHASE 3E:
- arq in requirements.txt, core/tasks.py ARQ worker config
- services/email.py: SMTP + Jinja2 templates (fr/ar/en)
- Templates: welcome, OTP, invoice_reminder, grade_published
- Tasks: send_email, cleanup_expired_sessions, cleanup_expired_cache, send_notification_digest
- Hooks: recovery → OTP email, grade → notification email
- ARQ worker in docker-compose + make worker + Prometheus metrics

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- Suggest git commands. Update TODO_GENERAL.md. Phase 3E ONLY.
```

---

## Phase 4A — Admin Dashboard

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
Previous phases + 3E done. I need you to implement Phase 4A — Admin Dashboard.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "Phase 4A")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "Phase 4A" checklist)
- Read ecole-platform-dev/web/src/app/App.tsx for existing routes
- Read ecole-platform-dev/web/src/features/ for existing feature structure
- Read ecole-platform-dev/web/src/services/api/client.ts for API client
- Read ecole-platform-dev/web/src/services/auth/AuthContext.tsx for auth context

PHASE 4A:
- Create /admin route group (ADM, DIR roles only)
- DashboardPage.tsx: summary cards (users, sessions, invitations, audit events)
- UsersPage.tsx: user list with search/filter, suspend/activate, role assignment
- InvitationsPage.tsx: create, list, revoke invitation codes
- AuditLogPage.tsx: searchable with correlation_id filter, date range
- SchoolSettingsPage.tsx: school name, timezone, notification prefs
- JustificationReviewPage.tsx: approve/deny absence justifications
- Admin sidebar navigation + role guard

NOTE: Phase 5B will create corresponding mobile admin screens.

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- Suggest git commands. Update TODO_GENERAL.md. Phase 4A ONLY.
```

---

## Phase 4B — Teacher Dashboard

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
Previous phases + 4A done. I need you to implement Phase 4B — Teacher Dashboard.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "Phase 4B")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "Phase 4B" checklist)
- Read ecole-platform-dev/web/src/app/App.tsx for routes
- Read ecole-platform-dev/web/src/features/admin/ for admin pattern to follow
- Read ecole-platform-dev/backend/app/api/v1/ for teacher-relevant endpoints (assignments, submissions, attendance, assessments, courses)

PHASE 4B:
- Create /teacher route group (TCH role only)
- ClassesPage.tsx: assigned classes with student roster
- AssignmentFormPage.tsx: create/edit with file upload (from Phase 3B)
- SubmissionsPage.tsx: list, download, inline grading (score + feedback)
- AttendancePage.tsx: mark attendance per class session
- AssessmentFormPage.tsx: create/edit/publish
- CoursesPage.tsx: manage courses, upload content
- Teacher sidebar navigation

NOTE: Phase 5B will create corresponding mobile teacher screens.

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- Suggest git commands. Update TODO_GENERAL.md. Phase 4B ONLY.
```

---

## Phase 4C — CRUD Forms, 2FA UI & Cascade Integration

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
Previous phases + 4B done. I need you to implement Phase 4C — cascade integration.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "Phase 4C")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "Phase 4C" checklist)
- Read ecole-platform-dev/web/src/features/auth/LoginPage.tsx for login flow
- Read ecole-platform-dev/web/src/features/profile/ProfilePage.tsx for profile
- Read ecole-platform-dev/web/src/services/ for API client and auth context

PHASE 4C — This integrates all backend improvements into the web frontend:
- FROM 2A: SessionsPage.tsx (list sessions, device info, revoke button)
- FROM 2B: TwoFactorPage.tsx (enable/disable 2FA, QR code, verify, backup codes)
- FROM 2B: Update LoginPage.tsx to handle requires_2fa response + TOTP input
- FROM 3B: Drag-drop file upload on submission + teacher content pages
- FROM 3C: WebSocketClient.ts (auto-connect, notification toasts, badge count)
- FROM 3D: Search bar + filter dropdowns + sort toggle on list pages
- Student submission form, parent justification form
- Profile edit form with password change (policy feedback from 2A)

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- Suggest git commands. Update TODO_GENERAL.md. Phase 4C ONLY.
```

---

## Phase 5A — Push Notifications, Biometric Auth & 2FA Mobile

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
Previous phases + 4C done. I need you to implement Phase 5A.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "Phase 5A")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "Phase 5A" checklist)
- Read ecole-platform-dev/mobile/lib/main.dart for app structure
- Read ecole-platform-dev/mobile/lib/features/auth/ for login flow
- Read ecole-platform-dev/mobile/lib/shared/ for push_notifications.dart, secure_storage.dart
- Read ecole-platform-dev/mobile/pubspec.yaml for current dependencies

PHASE 5A:
- Firebase push: document config setup, deep-link routing, permission flow, badge count
- Biometric auth: add local_auth, fingerprint/FaceID unlock, fallback to password
- FROM 2B: 2FA verification screen in login flow + 2FA setup in profile
- FROM 3B: File picker (gallery, camera, documents) for submission upload + progress
- FROM 3C: WebSocket client with reconnection + local notifications on WS event
- FROM 2A: Send device_name, user_agent on login for session tracking

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- Suggest git commands. Update TODO_GENERAL.md. Phase 5A ONLY.
```

---

## Phase 5B — Admin/Teacher Mobile Screens & Search

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
Previous phases + 5A done. I need you to implement Phase 5B.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "Phase 5B")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "Phase 5B" checklist)
- Read ecole-platform-dev/mobile/lib/features/ for existing screens
- Read ecole-platform-dev/web/src/features/admin/ and teacher/ for web versions to match

PHASE 5B:
- FROM 4A: Admin mobile screens (dashboard, users, invitations, justification review)
- FROM 4B: Teacher mobile screens (classes, assignment form, submissions/grading, attendance)
- FROM 3D: Search bar + filter chips + sort toggle on mobile list screens
- Update shell navigation: role-based tabs for admin/teacher

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- Suggest git commands. Update TODO_GENERAL.md. Phase 5B ONLY.
```

---

## Phase 6A — E2E Tests, Load Testing & Security Audit

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
Previous phases + 5B done. I need you to implement Phase 6A.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "Phase 6A")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "Phase 6A" checklist)
- Read ecole-platform-dev/.github/workflows/ci.yml for existing CI pipeline
- Read ecole-platform-dev/backend/tests/ for existing test structure
- Read ecole-platform-dev/web/ for frontend to E2E test

PHASE 6A:
- Playwright E2E: J1 login→feed→logout, J2 teacher assignment, J3 student submission, J4 admin invitation, J5 2FA login
- k6 load tests: 100 logins, 500 GETs, 50 uploads, 200 WS connections (per F2 SLO)
- Security tests: CSRF, XSS, SQL injection, auth bypass, scope masking
- All tests in CI pipeline

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- Suggest git commands. Update TODO_GENERAL.md. Phase 6A ONLY.
```

---

## Phase 7A — Production Environment & TLS

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
Previous phases + 6A done. I need you to implement Phase 7A.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "Phase 7A")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "Phase 7A" checklist)
- Read ecole-platform-dev/infra/ for existing Docker/Nginx/monitoring configs
- Read ecole-platform-dev/infra/docker-compose.prod.yml (enhanced in 0A)

PHASE 7A:
- Complete docker-compose.prod.yml (all services, managed URLs, secrets)
- nginx-prod.conf: TLS, HSTS, CSP, X-Frame-Options, gzip, rate limiting
- deploy.sh: zero-downtime deploy with rollback
- ssl-renew.sh: Let's Encrypt cert renewal
- Docker secrets for sensitive vars
- healthcheck.sh: API + DB + Redis + disk + cert
- DEPLOYMENT.md documentation

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- Suggest git commands. Update TODO_GENERAL.md. Phase 7A ONLY.
```

---

## Phase 8A — GDPR Compliance & Analytics Dashboard

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
Previous phases + 7A done. I need you to implement Phase 8A.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "Phase 8A")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "Phase 8A" checklist)
- Read ecole-platform-dev/backend/app/services/kpi.py for existing KPI queries
- Read ecole-platform-dev/backend/app/services/analytics.py for event system
- Read ecole-platform-dev/web/src/features/admin/ for admin pages

PHASE 8A:
- GDPR endpoints: GET /users/{id}/data-export, POST /users/{id}/data-deletion (anonymize), GET /users/{id}/consent-log
- Audit trail on all GDPR actions
- AnalyticsPage.tsx: KPI dashboard with recharts (adoption, usage, auth errors, latency)
- Date range selector (7d, 30d, 90d) + auto-refresh
- Background task: refresh_kpi_views daily (refresh mv_kpi_daily from Phase 1A)

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- Suggest git commands. Update TODO_GENERAL.md. Phase 8A ONLY.
```

---

## Advanced Sub-Phase Summary Table

| Sub-Phase | Tool | Open Folder | Focus | Cascades To |
|-----------|------|-------------|-------|-------------|
| 0A | Claude Code | `Ecole-Platform/` | Docker prod, Makefile, env vars | — |
| 1A | Claude Code | `Ecole-Platform/` | DB views, parent-child, migrations | 2A |
| 2A | Claude Code | `Ecole-Platform/` | Password policy, sessions, rate limits | 4C, 5A |
| 2B | Claude Code | `Ecole-Platform/` | 2FA/TOTP, email verification, backup codes | 4C, 5A |
| 3A | Claude Code | `Ecole-Platform/` | OpenAPI spec, Redoc, CI drift | — |
| 3B | Claude Code | `Ecole-Platform/` | File upload/download, S3-ready storage | 4C, 5A |
| 3C | Claude Code | `Ecole-Platform/` | WebSocket, Redis Pub/Sub, real-time | 4C, 5A |
| 3D | Claude Code | `Ecole-Platform/` | Filters, sorting, full-text search | 4C, 5B |
| 3E | Claude Code | `Ecole-Platform/` | ARQ worker, email, background tasks | — |
| 4A | Claude Code | `Ecole-Platform/` | Admin dashboard (users, invites, audit) | 5B |
| 4B | Claude Code | `Ecole-Platform/` | Teacher dashboard (assignments, grading) | 5B |
| 4C | Claude Code | `Ecole-Platform/` | CRUD forms + cascade (2FA, WS, files, search) | — |
| 5A | Claude Code | `Ecole-Platform/` | Push, biometric, 2FA mobile, WS client | — |
| 5B | Claude Code | `Ecole-Platform/` | Admin/teacher mobile, search/filter | — |
| 6A | Claude Code | `Ecole-Platform/` | Playwright E2E, k6 load, security audit | — |
| 7A | Claude Code | `Ecole-Platform/` | Production TLS, deploy, secrets, health | — |
| 8A | Claude Code | `Ecole-Platform/` | GDPR, analytics dashboard, KPI refresh | — |

---

---

# NEW PHASES — Registration, Profiles & Cascade (Not Yet Started)

> These phases were added after analyzing the report specs vs code gaps.
> They cover: role-specific profile tables, self-registration with invitation code, and the web/mobile UI cascade.
>
> **All previous phases (0→8 and 0A→8A) are already completed.** Do NOT rerun them.
>
> **Phases 1B, 2C, 4D, 5C are already completed.** Run remaining 3 phases: `2D → 4D-patch → 5C-patch`
>
> - 2D adds backend parent-child link management (schema fix + admin endpoints + parent endpoint)
> - 4D-patch and 5C-patch add the link management UI to the already-completed web and mobile code

---

## Phase 1B — Role-Specific Profile Tables

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
All phases 0→8 and all advanced sub-phases 0A→8A are already completed and working.
I need you to implement Phase 1B (a NEW phase that adds role-specific profile tables on top of the existing code).

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "NEW PHASES" section → "Phase 1B")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "NEW PHASES" section → "Phase 1B" checklist)
- Read ecole-platform-dev/backend/app/models/iam.py for existing User, Membership, ParentChildLink, InvitationCode models (from Phase 1A)
- Read ecole-platform-dev/backend/app/schemas/ for existing Pydantic schemas
- Read ecole-platform-dev/backend/app/api/v1/ for existing endpoints (auth, invites, users, etc.)
- Read ecole-platform-dev/backend/app/services/ for existing service layer
- The codebase already has: Docker infra (Phase 0/0A), full DB schema with 40+ tables (Phase 1/1A), auth with JWT+2FA+TOTP (Phase 2/2A/2B), file upload, WebSocket, search, ARQ workers (Phase 3A-3E), admin+teacher web dashboards (Phase 4A-4C), mobile app (Phase 5A-5B), E2E tests (Phase 6A), deploy scripts (Phase 7A), GDPR+analytics (Phase 8A)

PHASE 1B — Role-Specific Profile Tables:
- Create student_profiles table: user_id (FK unique), school_id, student_number (unique per school), date_of_birth, gender (optional), class_level, nationality, guardian_notes
- Create parent_profiles table: user_id (FK unique), school_id, relationship_type (FATHER/MOTHER/GUARDIAN/OTHER), cin_number (optional), address (optional), profession (optional), emergency_phone
- Create teacher_profiles table: user_id (FK unique), school_id, employee_id (optional), subject_specialty, qualification, hire_date
- Create SQLAlchemy models: StudentProfile, ParentProfile, TeacherProfile in models/iam.py
- Create Pydantic schemas (create, update, response) for each profile
- Create endpoints: GET /me/profile (returns role-specific data), PUT /me/profile (updates role-specific fields), GET /admin/users/{id}/profile (ADM only)
- Add optional target_student_id field to InvitationCode model (so admin can pre-link parent codes to a student)
- Update seed data to populate profiles for all test users
- All 3 Alembic migrations must follow the G1-IAM naming convention

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- Suggest git commands. Update TODO_GENERAL.md. Phase 1B ONLY.
```

---

## Phase 2C — Registration with Invitation Code

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
All phases 0→8 and all advanced sub-phases 0A→8A are already completed and working.
Phase 1B (role-specific profile tables) is also completed.
I need you to implement Phase 2C (a NEW phase that adds self-registration with invitation code on top of the existing code).

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "NEW PHASES" section → "Phase 2C")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "NEW PHASES" section → "Phase 2C" checklist)
- Read ecole-platform-dev/backend/app/models/iam.py for User, Membership, InvitationCode, ParentChildLink, StudentProfile, ParentProfile, TeacherProfile (StudentProfile/ParentProfile/TeacherProfile were added in Phase 1B)
- Read ecole-platform-dev/backend/app/api/v1/auth.py for existing auth endpoints (login, token refresh, 2FA from Phase 2/2A/2B)
- Read ecole-platform-dev/backend/app/api/v1/invites.py for existing invite endpoints (code generation, consumption)
- Read ecole-platform-dev/backend/app/services/auth.py for password policy (from Phase 2A)
- Read ecole-platform-dev/backend/app/services/otp.py for email verification OTP (from Phase 2B)
- Read ecole-platform-dev/backend/app/core/rate_limit.py for rate limiting
- Currently there is NO public registration endpoint — users can only be created by admins. This phase adds POST /auth/register

PHASE 2C — Registration with Invitation Code:
- Create POST /auth/register — public endpoint (no auth required):
  - Input: code, email, full_name, phone (optional), password, profile_data (role-specific)
  - Validates code (not expired, not consumed, not revoked)
  - Creates user with password (enforce password policy from Phase 2A)
  - Creates membership (role from code's role_target, school from code's school_id)
  - Creates role-specific profile (StudentProfile, ParentProfile, or TeacherProfile from Phase 1B)
  - If code has target_student_id and role=PAR → creates parent_child_link automatically
  - Marks code as consumed
  - Sends email verification OTP (from Phase 2B)
  - Returns JWT tokens (user is logged in immediately)
  - All in one DB transaction (rollback on any failure)
- Add rate limiting: 5 registrations per 15 min per IP
- Validate email uniqueness per school
- Add audit trail: user.register event
- Create POST /admin/register-batch — admin bulk-creates accounts from CSV (name, email, role, class → generates codes or creates accounts directly)
- Update the login flow docs/comments to note the new "Register with code" option

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- Suggest git commands. Update TODO_GENERAL.md. Phase 2C ONLY.
```

---

## Phase 2D — Parent-Child Link Management & Invitation Schema Fix

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
All phases 0→8 and all advanced sub-phases 0A→8A are already completed and working.
Phases 1B (profile tables) and 2C (registration endpoint) are also completed.
I need you to implement Phase 2D — parent-child link management and fixing the invitation schema gap.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "NEW PHASES" section → "Phase 2D")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "NEW PHASES" section → "Phase 2D" checklist)
- Read ecole-platform-dev/backend/app/models/iam.py for InvitationCode model (has target_student_id column) and ParentChildLink model
- Read ecole-platform-dev/backend/app/schemas/auth.py for InviteCreateRequest (currently missing target_student_id)
- Read ecole-platform-dev/backend/app/services/auth.py for InvitationService.create_invite() and AuthService.register() (register already handles auto-link at lines ~397-408)
- Read ecole-platform-dev/backend/app/api/v1/invitations.py for POST /invites/create endpoint
- Read ecole-platform-dev/backend/app/api/v1/admin.py for existing admin endpoints (batch register, invitation list)
- Read ecole-platform-dev/backend/app/core/permissions.py for ROLE_PERMISSIONS and existing PERM codes
- Read ecole-platform-dev/backend/app/core/dependencies.py for get_parent_child_ids() and verify_parent_child_ownership() ABAC guards

PHASE 2D — Parent-Child Link Management (backend-only, extends Phase 2C):

1. FIX INVITATION SCHEMA GAP:
   - Add `target_student_id: UUID | None = None` to InviteCreateRequest schema
   - Update InvitationService.create_invite() to accept target_student_id parameter
   - Validate: if target_student_id provided, verify the user exists, has STD role, and belongs to the same school
   - Update POST /invites/create handler to pass target_student_id through
   - The auto-link in AuthService.register() already works — this just lets admins set the field via API

2. ADMIN PARENT-CHILD LINK ENDPOINTS (add to admin.py or new family.py router):
   - POST /admin/parent-child-links — body: {parent_user_id, child_user_id}
     - Validate: both users exist in admin's school, parent has PAR membership, student has STD membership
     - Check no active duplicate link exists (same parent + child + school)
     - Create ParentChildLink with status="active", linked_by=admin user_id
     - Return the created link
   - GET /admin/parent-child-links?parent_id=X&student_id=X&page=1&size=20
     - Filter by parent_user_id, child_user_id, or both (all optional)
     - Scope to admin's school_id (ABAC)
     - Return paginated list with parent name, child name, status, linked_at, linked_by
   - DELETE /admin/parent-child-links/{link_id}
     - Soft-revoke: set status="revoked" (do NOT hard delete)
     - Verify the link belongs to admin's school
     - Return success message

3. ADD PERMISSION CODES:
   - PERM-IAM:parent-link:create, PERM-IAM:parent-link:read, PERM-IAM:parent-link:delete
   - Assign all 3 to ADM role in ROLE_PERMISSIONS
   - Assign PERM-IAM:parent-link:read to DIR role (read-only oversight)
   - Add to seed.py if permission seeding exists

4. PARENT SELF-SERVICE ENDPOINT:
   - GET /me/children — returns list of linked children for the authenticated parent
   - Each child: {user_id, full_name, class_level, school_name, linked_at}
   - Requires PAR role (use requires_role("PAR") or similar guard)
   - Returns empty list (not 404) if no links

5. BATCH REGISTER UPDATE:
   - Add optional target_student_id to BatchRegisterItem schema
   - When batch-creating PAR users with target_student_id, auto-create ParentChildLink after user creation
   - Validate target_student_id same as in step 1

6. INTEGRATION TESTS (in backend/tests/test_phase2d_family.py):
   - Test create invite with target_student_id → register parent → GET /me/children shows the child
   - Test POST /admin/parent-child-links (success → 201)
   - Test POST /admin/parent-child-links duplicate → 409
   - Test POST /admin/parent-child-links wrong school → 404
   - Test POST /admin/parent-child-links wrong role (link two students) → 422
   - Test GET /admin/parent-child-links?parent_id=X returns correct links
   - Test GET /admin/parent-child-links?student_id=X returns correct links
   - Test DELETE /admin/parent-child-links/{id} → verify status="revoked"
   - Test GET /me/children with 0, 1, 2 linked children
   - Test GET /me/children as non-PAR role → 403
   - Test ABAC: after revoking link, parent can no longer access child's grades

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- Suggest git commands. Update TODO_GENERAL.md. Phase 2D ONLY.
```

---

## Phase 4D — Registration & Profile UI (Web)

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
All phases 0→8 and all advanced sub-phases 0A→8A are already completed and working.
Phases 1B (profile tables), 2C (registration endpoint), and 2D (parent-child link management + invitation schema fix) are also completed.
I need you to implement Phase 4D — this EXTENDS the existing web app (from Phase 4A/4B/4C) to add registration, profile UI, and parent-child link management.
Do NOT rewrite existing pages. ADD new pages and EXTEND existing ones.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "NEW PHASES" section → "Phase 4D")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "NEW PHASES" section → "Phase 4D" checklist)
- Read ecole-platform-dev/web/src/features/auth/ for existing LoginPage, auth hooks (from Phase 4C — you will ADD a RegisterPage here and ADD a "Register" link to LoginPage)
- Read ecole-platform-dev/web/src/features/profile/ or web/src/features/admin/ for existing profile pages (from Phase 4C — you will EXTEND ProfilePage with role-specific fields)
- Read ecole-platform-dev/web/src/lib/api.ts for API client
- Read ecole-platform-dev/web/src/i18n/ for existing translations structure (ADD new keys, don't replace)
- Read ecole-platform-dev/backend/app/api/v1/auth.py for POST /auth/register contract (from Phase 2C)
- Read ecole-platform-dev/backend/app/schemas/ for registration + profile schemas (from Phase 1B + 2C)
- Read ecole-platform-dev/backend/app/api/v1/admin.py for parent-child link endpoints (from Phase 2D)

PHASE 4D — Registration & Profile UI + Parent-Child Links (EXTENDS existing web code from 4C, cascading from 1B + 2C + 2D):
- Create RegisterPage.tsx with multi-step flow:
  - Step 1: Enter invitation code → API validates → shows role + school name
  - Step 2: Enter email, full_name, phone, password (with real-time password policy feedback from 2A rules)
  - Step 3: Role-specific fields (date_of_birth for STD, relationship_type for PAR, subject_specialty for TCH)
  - Step 4: Email verification OTP input (from 2B)
  - Route: /register
- Extend ProfilePage with role-specific edit forms:
  - Student: student_number (read-only), date_of_birth, class_level
  - Parent: relationship_type, CIN, address, profession, emergency_phone
  - Teacher: employee_id (read-only), subject_specialty, qualification
- Create BatchRegisterPage.tsx for admin:
  - CSV upload form for bulk account creation
  - Preview table before submission, progress indicator during creation
- Add "Register" link on LoginPage.tsx (alongside login form)
- Admin Parent-Child Link Management (cascading from Phase 2D):
  - ParentChildLinksPage.tsx in admin section — list all links for the school, filter by parent/student
  - "Link Parent to Student" form: select parent (dropdown/search), select student (dropdown/search), submit
  - "Revoke Link" button with confirmation dialog
  - When creating an invitation for PAR role, show optional "Pre-link to student" dropdown
- Parent "My Children" section on parent profile/dashboard:
  - List linked children with name, class, school
  - Navigate to child's grades/attendance from here
- i18n translations for all new fields (fr/ar/en)

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- Suggest git commands. Update TODO_GENERAL.md. Phase 4D ONLY.
```

---

## Phase 5C — Registration & Profile Mobile

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
All phases 0→8 and all advanced sub-phases 0A→8A are already completed and working.
Phases 1B (profile tables), 2C (registration endpoint), 2D (parent-child link management), and 4D (web registration + profile + link UI) are also completed.
I need you to implement Phase 5C — this EXTENDS the existing mobile app (from Phase 5A/5B) to add registration, profile screens, and parent "My Children" feature.
Do NOT rewrite existing screens. ADD new screens and EXTEND existing ones.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "NEW PHASES" section → "Phase 5C")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "NEW PHASES" section → "Phase 5C" checklist)
- Read ecole-platform-dev/mobile/lib/features/auth/ for existing login screen, auth providers (from Phase 5A — you will ADD a register_screen.dart here and ADD a "Register" button to the login screen)
- Read ecole-platform-dev/mobile/lib/features/profile/ for existing profile screens (from Phase 5A/5B — you will EXTEND with role-specific sections)
- Read ecole-platform-dev/mobile/lib/core/ for API client, routing, theme
- Read ecole-platform-dev/mobile/lib/l10n/ for existing i18n setup (ADD new keys, don't replace)
- Read ecole-platform-dev/web/src/features/auth/RegisterPage.tsx to match the web registration flow (from Phase 4D — mobile should mirror the same steps)

PHASE 5C — Registration & Profile & My Children Mobile (EXTENDS existing mobile code from 5A/5B, cascading from 1B + 2C + 2D):
- Create register_screen.dart with stepper flow matching web:
  - Step 1: Enter code → validate → show role + school
  - Step 2: Email, full_name, phone, password (with policy feedback)
  - Step 3: Role-specific fields
  - Step 4: OTP verification
  - Keyboard-friendly, auto-focus, validation on each step
- Enhance profile screen with role-specific sections:
  - Student: date_of_birth (date picker), class_level
  - Parent: relationship_type (dropdown), CIN, emergency_phone
  - Teacher: subject_specialty, qualification
- Add "Register" button on login screen
- Parent "My Children" screen (cascading from Phase 2D):
  - my_children_screen.dart — list linked children with name, class_level, school
  - Tap child → navigate to child's grades/attendance
  - Add "My Children" entry in parent's bottom nav or drawer menu
- i18n for all new fields (fr/ar/en)

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- Suggest git commands. Update TODO_GENERAL.md. Phase 5C ONLY.
```

---

---

## Phase 4D-patch — Parent-Child Link UI (Web Patch)

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
All phases 0→8 and all advanced sub-phases 0A→8A are already completed and working.
Phases 1B (profile tables), 2C (registration endpoint), 4D (web registration + profile UI), and 5C (mobile registration + profile) are also completed.
Phase 2D (parent-child link management backend) is also completed — it added:
- target_student_id field to InviteCreateRequest schema
- POST/GET/DELETE /admin/parent-child-links endpoints
- GET /me/children endpoint for parents
- New PERM-IAM:parent-link:* permission codes

I need you to implement Phase 4D-patch — this is a PATCH to add parent-child link UI to the EXISTING web app.
4D was run BEFORE 2D existed, so the web app is missing the link management UI.
Do NOT rewrite existing pages. ADD new components and EXTEND existing pages.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "Phase 4D-patch")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "Phase 4D-patch" checklist)
- Read ecole-platform-dev/backend/app/api/v1/admin.py for parent-child link endpoints (POST/GET/DELETE /admin/parent-child-links)
- Read ecole-platform-dev/backend/app/api/v1/auth.py or family.py for GET /me/children endpoint
- Read ecole-platform-dev/backend/app/schemas/ for link request/response schemas
- Read ecole-platform-dev/web/src/features/admin/ for existing admin pages (you will ADD ParentChildLinksPage here)
- Read ecole-platform-dev/web/src/features/auth/ or features/profile/ for existing parent profile/dashboard (you will ADD "My Children" section)
- Read ecole-platform-dev/web/src/lib/api.ts for API client patterns
- Read ecole-platform-dev/web/src/i18n/ for existing translations

PHASE 4D-patch — Parent-Child Link UI (PATCH — adds ONLY link management features):
- Create ParentChildLinksPage.tsx in admin section:
  - List all parent-child links for the school (table with parent name, child name, status, linked_at)
  - Search/filter by parent name/email or student name/email
  - "Link Parent to Student" button → modal with parent dropdown (search users with PAR role) + student dropdown (search users with STD role) → POST /admin/parent-child-links
  - "Revoke" button per row → confirmation dialog → DELETE /admin/parent-child-links/{id}
  - Add navigation entry in admin sidebar
- Enhance invitation creation form:
  - When admin creates an invite with role=PAR, show optional "Pre-link to student" dropdown
  - Selected student sends target_student_id to POST /invites/create
- Add "My Children" section for parents:
  - On parent's dashboard or profile page, add a "My Children" card
  - Calls GET /me/children → shows list of linked children (name, class_level)
  - Click child → navigate to child's grades/attendance page
  - Show empty state "No children linked yet" if list is empty
- i18n translations for all new UI text (fr/ar/en)

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- Suggest git commands. Update TODO_GENERAL.md. Phase 4D-patch ONLY.
```

---

## Phase 5C-patch — "My Children" Screen (Mobile Patch)

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
All phases 0→8 and all advanced sub-phases 0A→8A are already completed and working.
Phases 1B, 2C, 4D, 5C, 2D, and 4D-patch are all completed.
Phase 2D added GET /me/children endpoint for parents.
Phase 4D-patch added the web version of "My Children".

I need you to implement Phase 5C-patch — this is a PATCH to add the "My Children" screen to the EXISTING mobile app.
5C was run BEFORE 2D existed, so the mobile app is missing the "My Children" feature.
Do NOT rewrite existing screens. ADD new screens and EXTEND navigation.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "Phase 5C-patch")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "Phase 5C-patch" checklist)
- Read ecole-platform-dev/backend/app/api/v1/auth.py or family.py for GET /me/children endpoint
- Read ecole-platform-dev/mobile/lib/features/ for existing feature folders
- Read ecole-platform-dev/mobile/lib/core/ for API client, routing, theme
- Read ecole-platform-dev/mobile/lib/l10n/ for existing i18n setup
- Read ecole-platform-dev/web/src/features/ to match the "My Children" section from 4D-patch (mobile should mirror the same data)

PHASE 5C-patch — "My Children" Mobile Screen (PATCH — adds ONLY the My Children feature):
- Create my_children_screen.dart (in features/family/ or features/profile/):
  - Calls GET /me/children
  - List linked children with name, class_level, school name
  - Tap child → navigate to child's grades/attendance screen
  - Empty state: "No children linked yet. Contact your school admin."
- Add "My Children" entry in parent's bottom navigation bar or drawer menu
  - Only visible when authenticated user has role = PAR
  - Use appropriate icon (e.g., people/family icon)
- Create Riverpod provider for children data (AsyncNotifier pattern matching existing code)
- i18n for all new text (fr/ar/en)

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- Suggest git commands. Update TODO_GENERAL.md. Phase 5C-patch ONLY.
```

---

## New Phases Summary Table

| Sub-Phase | Tool | Open Folder | Focus | Status |
|-----------|------|-------------|-------|--------|
| **1B** ✅ | Claude Code | `Ecole-Platform/` | Role-specific profile tables | Done |
| **2C** ✅ | Claude Code | `Ecole-Platform/` | Registration with invitation code | Done |
| **4D** ✅ | Claude Code | `Ecole-Platform/` | Registration + profile UI (web) | Done |
| **5C** ✅ | Claude Code | `Ecole-Platform/` | Registration + profile (mobile) | Done |
| **2D** | Claude Code | `Ecole-Platform/` | Parent-child link management + schema fix | **Run next** |
| **4D-patch** | Claude Code | `Ecole-Platform/` | Parent-child link UI (web patch) | After 2D |
| **5C-patch** | Claude Code | `Ecole-Platform/` | "My Children" screen (mobile patch) | After 4D-patch |

**Already completed:** 1B, 2C, 4D, 5C
**Remaining run order:** `2D → 4D-patch → 5C-patch`

---

---

# NEW PHASES — Content Library, Quiz Engine & CMS (Not Yet Started)

> These phases were added after analyzing the gap for: content management, PDF exercises, dynamic quizzes, and media library.
>
> **All previous phases (0→8, 0A→8A, 1B→5C) must be completed first.**
>
> **Run these 6 new phases in order:** `9A → 9B → 9C → 10A → 10B → 10C`
>
> - 9A, 9B, 9C are backend (new CONTENT_MGR role + content library + quiz engine + PDF exercises)
> - 10A is a separate CMS web dashboard for CONTENT_MGR
> - 10B **extends** the existing web app (teacher library + student quiz player)
> - 10C **extends** the existing mobile app (same features on mobile)

---

## Phase 9A — CONTENT_MGR Role + Content Library Backend

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```sql
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
All phases 0→8, all advanced sub-phases 0A→8A, and new phases 1B→5C are already completed and working.
I need you to implement Phase 9A (a NEW phase that adds a platform-wide CONTENT_MGR role and content library system).

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "Content Library, Quiz Engine & CMS" section → "Phase 9A")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "Content Library, Quiz Engine & CMS" section → "Phase 9A" checklist)
- Read ecole-platform-dev/backend/app/core/permissions.py for existing roles (ADM, DIR, TCH, PAR, STD, SUP, SYS) and permission matrix
- Read ecole-platform-dev/backend/app/models/lms.py for existing ContentItem, ContentItemAsset, Activity models (note: ContentItem already has nullable school_id, content_type, level_band, language)
- Read ecole-platform-dev/backend/app/models/erp.py for Class model (needed for class_content_assignments FK)
- Read ecole-platform-dev/backend/app/api/v1/content.py for existing content endpoints
- Read ecole-platform-dev/backend/app/core/storage.py for file upload system (Phase 3B)

PHASE 9A — CONTENT_MGR Role + Content Library + Teacher Promotion System:
- Add CONTENT_MGR role to permissions.py — platform-wide (NOT school-scoped), with PERM_CONTENT_CREATE, PERM_CONTENT_PUBLISH, PERM_CONTENT_MANAGE, PERM_CONTENT_DELETE, PERM_CONTENT_ANALYTICS, PERM_CONTENT_REVIEW
- Add fields to ContentItem: subject (String 50), created_by (FK users), description (Text), thumbnail_path (String 500), origin (String 20, default PLATFORM — values: PLATFORM/PROMOTED), original_content_id (FK to content_items nullable — links promoted content back to teacher's original)
- Create class_content_assignments table: id, teacher_id (FK), class_id (FK), content_item_id (FK), school_id, assigned_at, notes — unique(class_id, content_item_id)
- Create content_submissions table (teacher→platform promotion): id, content_item_id (FK), submitted_by (FK), school_id, status (PENDING/UNDER_REVIEW/APPROVED/REJECTED), reviewed_by (FK nullable), reviewed_at, review_notes (Text), promoted_content_id (FK nullable — the platform copy after approval)
- Add reward_points field (Integer, default 0) to teacher_profiles table (from Phase 1B)
- CMS endpoints (CONTENT_MGR only): POST/GET/PUT/DELETE /cms/content — manage platform-wide content (school_id=NULL)
- Review queue endpoints: GET /cms/submissions (list teacher submissions, filter by status/subject/level/school), POST /cms/submissions/{id}/review (approve or reject with notes)
- Approve workflow: create platform copy of content (school_id=NULL, origin=PROMOTED, original_content_id=source), award reward_points to teacher, send notification to teacher
- Reject workflow: update status, send notification with review_notes feedback to teacher
- Teacher endpoints: GET /content/library (browse platform + school content), POST /content/assign (assign to class), DELETE /content/assign/{id}, POST /content/submit-for-review (submit own content for platform promotion), GET /content/my-submissions (track submission status)
- Student endpoint: GET /classes/{id}/content (see assigned content)
- Audit trail on all CMS + submission operations
- Seed data: platform content (videos, PDFs, audios) + sample teacher submission

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- Suggest git commands. Update TODO_GENERAL.md. Phase 9A ONLY.
```

---

## Phase 9B — Quiz Engine Backend

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
All phases 0→8, 0A→8A, 1B→5C, and 9A are already completed and working.
I need you to implement Phase 9B (a NEW phase that adds a full quiz engine with 5 question types and auto-grading).

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "Phase 9B")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "Phase 9B" checklist)
- Read ecole-platform-dev/backend/app/models/lms.py for existing models (Course, Assignment, Activity, ContentItem + new CONTENT_MGR changes from 9A)
- Read ecole-platform-dev/backend/app/core/permissions.py for CONTENT_MGR role (from 9A)
- Read ecole-platform-dev/backend/app/api/v1/ for existing LMS endpoints
- Read ecole-platform-dev/backend/app/services/ for existing service layer

PHASE 9B — Quiz Engine:
- Create 4 new tables: quizzes (school_id nullable, created_by, title, subject, level_band, difficulty, time_limit_minutes, max_attempts, shuffle_questions, status), quiz_questions (question_type: MCQ/TRUE_FALSE/FILL_IN/DRAG_DROP/MATCHING, options JSONB, correct_answer JSONB, points, order, explanation), quiz_attempts (student_id, attempt_no, score, max_score, status: STARTED/COMPLETED/TIMED_OUT), quiz_responses (student_answer JSONB, is_correct, points_earned)
- Auto-grading service (services/quiz_grading.py): grade all 5 types automatically by comparing student_answer to correct_answer
- Quiz CRUD endpoints (CONTENT_MGR for platform / TCH for school-scoped)
- Student endpoints: start attempt (check max_attempts), submit response per question, submit attempt → auto-grade, view results with explanations
- Analytics: GET /quizzes/{id}/analytics — class performance stats
- Add exercise_type field to Assignment (STANDARD/PRINTABLE_PDF/QUIZ) + quiz_id FK
- Audit trail + seed data

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- Suggest git commands. Update TODO_GENERAL.md. Phase 9B ONLY.
```

---

## Phase 9C — PDF Exercise Workflow Backend

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
All phases 0→8, 0A→8A, 1B→5C, 9A, and 9B are already completed and working.
I need you to implement Phase 9C (a NEW phase that adds PDF exercise workflow: teacher uploads exercise PDF → student prints → solves → uploads scan/photo back).

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "Phase 9C")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "Phase 9C" checklist)
- Read ecole-platform-dev/backend/app/models/lms.py for Assignment model (which now has exercise_type from 9B), Submission, SubmissionFile models
- Read ecole-platform-dev/backend/app/api/v1/assignments.py for existing assignment endpoints
- Read ecole-platform-dev/backend/app/api/v1/submissions.py for existing submission + file upload endpoints
- Read ecole-platform-dev/backend/app/core/storage.py for file upload system

PHASE 9C — PDF Exercise Workflow:
- Add exercise_pdf_path field (String 500) to Assignment model
- Update POST /assignments: when exercise_type=PRINTABLE_PDF, require exercise PDF upload
- GET /assignments/{id}/exercise-pdf — download the printable exercise PDF (students in class)
- Update submission validation: require at least one file upload for PRINTABLE_PDF assignments
- Add file_type_hint field to SubmissionFile (SOLUTION_SCAN/SOLUTION_PHOTO/DOCUMENT)
- Teacher inline preview of uploaded solutions
- Audit trail

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- Suggest git commands. Update TODO_GENERAL.md. Phase 9C ONLY.
```

---

## Phase 10A — CMS Dashboard (Web)

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
All phases 0→8, 0A→8A, 1B→5C, and 9A→9C are already completed and working.
I need you to implement Phase 10A (a NEW separate CMS web dashboard at /cms for the CONTENT_MGR role).
This is a NEW route group — do NOT modify existing admin/teacher/student pages.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "Phase 10A")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "Phase 10A" checklist)
- Read ecole-platform-dev/web/src/ for existing app structure, routing, auth hooks, i18n
- Read ecole-platform-dev/backend/app/api/v1/content.py for CMS content endpoints (from 9A)
- Read ecole-platform-dev/backend/app/api/v1/quizzes.py for quiz CRUD endpoints (from 9B)
- Read ecole-platform-dev/backend/app/schemas/ for content + quiz schemas
- Read ecole-platform-dev/web/src/lib/api.ts for API client

PHASE 10A — CMS Dashboard:
- New route group /cms/* with separate layout (sidebar: Content, Review Queue, Quizzes, Analytics)
- CONTENT_MGR role guard on all CMS routes (403 for other roles)
- ContentListPage.tsx — list platform content with filters (type, level, subject, language, status, origin: PLATFORM/PROMOTED)
- ContentUploadPage.tsx — upload form: title, description, content_type (VIDEO/PDF/AUDIO/INTERACTIVE), level_band, subject, language, thumbnail, main file with progress bar
- ContentEditPage.tsx — edit metadata, replace files, publish/archive
- ReviewQueuePage.tsx — list teacher content submissions (filter by status: PENDING/UNDER_REVIEW/APPROVED/REJECTED, by subject, level, school)
  - Each card: content preview (thumbnail, title), teacher name, school, submission date
  - Detail view: full content preview (play video, view PDF, listen audio), teacher info
  - Actions: "Approve" (creates platform copy, awards points, notifies teacher), "Reject" (requires feedback text, notifies teacher), "Mark Under Review"
  - Badge/counter on sidebar showing PENDING count
- QuizBuilderPage.tsx — create/edit quizzes with editors for all 5 question types (MCQ, T/F, Fill-in, Drag&Drop, Matching), question reorder, preview mode
- AnalyticsPage.tsx — content usage stats across schools + teacher contribution stats (top contributors, approval rates)
- Bulk upload support
- i18n (fr/ar/en)

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- Suggest git commands. Update TODO_GENERAL.md. Phase 10A ONLY.
```

---

## Phase 10B — Teacher Content Library + Quiz Player (Web)

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
All phases 0→8, 0A→8A, 1B→5C, 9A→9C, and 10A are already completed and working.
I need you to implement Phase 10B — this EXTENDS the existing web app (from Phase 4A/4B/4C/4D) to add content library, quiz player, and PDF exercise features.
Do NOT rewrite existing pages. ADD new pages and EXTEND existing ones.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "Phase 10B")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "Phase 10B" checklist)
- Read ecole-platform-dev/web/src/features/teacher/ for existing teacher dashboard pages (from 4B/4C)
- Read ecole-platform-dev/web/src/features/student/ for existing student pages
- Read ecole-platform-dev/web/src/features/parent/ for existing parent pages
- Read ecole-platform-dev/backend/app/api/v1/content.py for GET /content/library, POST /content/assign endpoints (from 9A)
- Read ecole-platform-dev/backend/app/api/v1/quizzes.py for quiz endpoints (from 9B)
- Read ecole-platform-dev/backend/app/api/v1/assignments.py for PDF exercise endpoints (from 9C)

PHASE 10B — Teacher Library + Quiz Player (EXTENDS existing web code):
- Teacher: ContentLibraryPage.tsx — browse platform + school content, filter, assign to class, upload school-scoped content
- Teacher: "Submit to Platform Library" button on own content → POST /content/submit-for-review → submits for CONTENT_MGR review
- Teacher: "My Submissions" tab showing submission statuses (PENDING/UNDER_REVIEW/APPROVED/REJECTED) + feedback from CONTENT_MGR
- Teacher: show reward_points balance in profile section
- Teacher: QuizBuilderPage.tsx — create class-specific quizzes, assign platform quizzes
- Student: ContentPage.tsx — view assigned content (HTML5 video/audio player, PDF embed), progress tracking
- Student: QuizPlayerPage.tsx — take quizzes with all 5 question types (radio for MCQ, toggle for T/F, text for Fill-in, drag zones, matching lines), timer, navigation, results with explanations
- Student: PDF exercise download + upload solution flow in assignment view
- Parent: extend dashboard to show quiz results alongside grades
- i18n (fr/ar/en)

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- Suggest git commands. Update TODO_GENERAL.md. Phase 10B ONLY.
```

---

## Phase 10C — Content Library + Quiz Player (Mobile)

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
All phases 0→8, 0A→8A, 1B→5C, 9A→9C, 10A, and 10B are already completed and working.
I need you to implement Phase 10C — this EXTENDS the existing mobile app (from Phase 5A/5B/5C) to add content library, quiz player, and PDF exercise features.
Do NOT rewrite existing screens. ADD new screens and EXTEND existing ones.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "Phase 10C")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "Phase 10C" checklist)
- Read ecole-platform-dev/mobile/lib/features/ for existing teacher/student/parent screens (from 5A/5B/5C)
- Read ecole-platform-dev/mobile/lib/core/ for API client, routing, theme
- Read ecole-platform-dev/mobile/lib/l10n/ for existing i18n setup
- Read ecole-platform-dev/web/src/features/teacher/ContentLibraryPage.tsx to match web UX (from 10B)
- Read ecole-platform-dev/web/src/features/student/QuizPlayerPage.tsx to match web quiz flow (from 10B)

PHASE 10C — Content Library + Quiz Player Mobile (EXTENDS existing mobile code):
- Teacher: content_library_screen.dart — browse + assign content, upload from phone (camera/gallery/file picker)
- Student: content_screen.dart — view assigned content (video/PDF/audio players)
- Student: quiz_player_screen.dart — swipe-through questions, tap/drag answers, all 5 types, timer, results
- Student: PDF exercise download + camera capture for solution upload
- Parent: quiz results in child dashboard
- Offline: cache quiz questions for offline attempt, sync answers when online
- i18n (fr/ar/en)

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- Suggest git commands. Update TODO_GENERAL.md. Phase 10C ONLY.
```

---

## Content & Quiz Phases Summary Table

| Sub-Phase | Tool | Open Folder | Focus | Cascades To |
|-----------|------|-------------|-------|-------------|
| __9A__ | Claude Code | `Ecole-Platform/` | CONTENT_MGR role + content library backend | 9B, 10A, 10B, 10C |
| __9B__ | Claude Code | `Ecole-Platform/` | Quiz engine (5 question types, auto-grading) | 10A, 10B, 10C |
| __9C__ | Claude Code | `Ecole-Platform/` | PDF exercise workflow backend | 10B, 10C |
| __10A__ | Claude Code | `Ecole-Platform/` | CMS dashboard for CONTENT_MGR (web) | — |
| __10B__ | Claude Code | `Ecole-Platform/` | Teacher content library + student quiz player (web) | — |
| __10C__ | Claude Code | `Ecole-Platform/` | Content library + quiz player (mobile) | — |

---

---

# NEW PHASES — Missing V1 Features: Timetable, Billing, Messaging, Progress, Toggles (Not Yet Started)

> These phases cover V1 (P0/P1) features from the reports that were not previously planned.
>
> **All previous phases (0→8, 0A→8A, 1B→5C, 9A→10C) must be completed first.**
>
> **Run these 8 new phases in order:** `11A → 11B → 11C → 11D → 11E → 12A → 12B → 12C`

---

## Phase 11A — Timetable / Schedule Management Backend

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
All phases 0→8, 0A→8A, 1B→5C, and 9A→10C are already completed and working.
I need you to implement Phase 11A (a NEW phase that adds timetable/schedule management).

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "Missing V1 Features" section → "Phase 11A")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "Missing V1 Features" section → "Phase 11A" checklist)
- Read ecole-platform-dev/backend/app/models/erp.py for existing Class, AcademicYear, TeacherAssignment models
- Read ecole-platform-dev/backend/app/core/permissions.py for role permissions
- Read ecole-platform-dev/backend/app/api/v1/ for existing ERP endpoints

PHASE 11A — Timetable:
- Create timetable_slots table: school_id, class_id (FK), academic_year_id (FK), day_of_week (0-6), start_time, end_time, subject, teacher_id (FK), room, is_recurring, effective_from/until
- Create timetable_exceptions table: timetable_slot_id (FK), exception_date, exception_type (CANCELED/SUBSTITUTED/ROOM_CHANGED), substitute_teacher_id, reason
- CRUD endpoints for slots + weekly view endpoints (by class, teacher, current user)
- Exception endpoints (cancel, substitute)
- Validation: no overlapping slots for same class or teacher at same time
- Audit trail + seed data

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- Suggest git commands. Update TODO_GENERAL.md. Phase 11A ONLY.
```

---

## Phase 11B — Billing Enhancements Backend

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
All phases 0→8, 0A→8A, 1B→5C, 9A→10C, and 11A are already completed and working.
I need you to implement Phase 11B (a NEW phase that adds fee structures, payment retry, and overdue reminders).

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "Phase 11B")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "Phase 11B" checklist)
- Read ecole-platform-dev/backend/app/models/billing.py for existing Invoice, PaymentAttempt, InvoiceItem models
- Read ecole-platform-dev/backend/app/api/v1/payments.py for existing billing endpoints
- Read ecole-platform-dev/backend/app/services/email.py for email notification templates
- Read ecole-platform-dev/backend/app/core/tasks.py or similar for ARQ background task setup

PHASE 11B — Billing Enhancements:
- Create fee_structures table: school_id, academic_year_id, name, amount, currency (MAD), frequency (MONTHLY/TRIMESTRIAL/ANNUAL/ONE_TIME), due_day, applies_to_level, status
- Create fee_assignments table: fee_structure_id (FK), student_id (FK), discount_percent, discount_reason, status (ACTIVE/EXEMPTED)
- Add retry fields to PaymentAttempt: retry_count, next_retry_at, last_retry_error
- Add reminder fields to Invoice: reminder_sent_at, reminder_count
- Payment retry service: ARQ task, 3 retries with exponential backoff (1h, 6h, 24h)
- Overdue reminder service: ARQ task daily at 09:00, emails parents for invoices overdue >7 days (max 3 reminders, respects consent)
- Fee CRUD + bulk assignment + invoice generation from fee structures
- Audit trail + seed data

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- Suggest git commands. Update TODO_GENERAL.md. Phase 11B ONLY.
```

---

## Phase 11C — Messaging & Communication Backend

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
All phases 0→8, 0A→8A, 1B→5C, 9A→10C, 11A, and 11B are already completed and working.
I need you to implement Phase 11C (a NEW phase that adds parent-teacher messaging, SMS fallback, and announcements).

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "Phase 11C")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "Phase 11C" checklist)
- Read ecole-platform-dev/backend/app/models/com.py for existing Notification, ConsentPreference, ParentFeedItem models
- Read ecole-platform-dev/backend/app/models/iam.py for ParentChildLink model (for ABAC validation)
- Read ecole-platform-dev/backend/app/api/v1/ws.py for existing WebSocket setup
- Read ecole-platform-dev/backend/app/services/email.py for existing email service
- Read ecole-platform-dev/backend/app/core/ws_manager.py for WebSocket manager

PHASE 11C — Messaging & Communication:
- Create conversations table: school_id, type (DIRECT/GROUP), created_by, subject
- Create conversation_participants table: conversation_id (FK), user_id (FK), role_in_conversation
- Create messages table: conversation_id (FK), sender_id (FK), body, sent_at, edited_at
- Create message_read_receipts table: message_id (FK), user_id (FK), read_at
- Create announcements table: school_id, author_id, title, body, target_roles (JSONB), target_class_ids (JSONB), status (DRAFT/PUBLISHED/ARCHIVED)
- SMS fallback service: abstract SMSProvider protocol + stub, triggers on email failure + SMS consent
- Messaging endpoints: conversation CRUD, send/list messages, read receipts
- ABAC: parents can only message teachers of their children's classes
- Announcement endpoints: CRUD + publish (sends notifications to targeted roles/classes)
- WebSocket push for new messages + announcements
- Audit trail

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- Suggest git commands. Update TODO_GENERAL.md. Phase 11C ONLY.
```

---

## Phase 11D — Student Progress Visualization Backend

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
All phases 0→8, 0A→8A, 1B→5C, 9A→10C, and 11A→11C are already completed and working.
I need you to implement Phase 11D (a NEW phase that adds progress data aggregation endpoints for charts).

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "Phase 11D")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "Phase 11D" checklist)
- Read ecole-platform-dev/backend/app/models/lms.py for Grade, Submission, ContentProgress, ActivitySession models
- Read ecole-platform-dev/backend/app/models/erp.py for AttendanceRecord, Enrollment models
- Read ecole-platform-dev/backend/app/models/iam.py for ParentChildLink model
- Read ecole-platform-dev/backend/app/core/filtering.py for existing filter patterns

PHASE 11D — Student Progress:
- Create services/progress.py: aggregation functions for grade trends (monthly avg), content completion (done/total), activity scores (over time), attendance rates (present/absent/justified %)
- Class-wide summary for teachers
- Parent multi-child overview
- Endpoints: GET /progress/student/{id}, /progress/class/{id}, /progress/me, /progress/children
- Response format: chart-ready (labels array + datasets array for recharts/fl_chart)
- Redis cache with 15-min TTL
- ABAC: school boundary, parent-child, teacher-class guards

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- Suggest git commands. Update TODO_GENERAL.md. Phase 11D ONLY.
```

---

## Phase 11E — Feature Toggles

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
All phases 0→8, 0A→8A, 1B→5C, 9A→10C, and 11A→11D are already completed and working.
I need you to implement Phase 11E (a NEW phase that adds a feature toggle system for gradual rollout).

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "Phase 11E")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "Phase 11E" checklist)
- Read ecole-platform-dev/backend/app/core/ for existing middleware, dependencies patterns
- Read ecole-platform-dev/backend/app/core/rate_limit.py as reference for Redis-cached dependency injection

PHASE 11E — Feature Toggles:
- Create feature_toggles table: feature_key (unique), enabled_globally (bool), enabled_school_ids (JSONB), enabled_role_codes (JSONB)
- core/feature_flags.py: is_feature_enabled(key, school_id, role_code), Redis cache 1-min TTL
- RequiresFeature(key) dependency guard for endpoints
- CRUD endpoints for toggle management (SYS/CONTENT_MGR)
- GET /features/active — returns active features for current user (frontend reads this)
- Pre-create toggles: content_library, quiz_engine, pdf_exercises, messaging, announcements, timetable
- Audit trail

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- Suggest git commands. Update TODO_GENERAL.md. Phase 11E ONLY.
```

---

## Phase 12A — Timetable + Billing + Messaging UI (Web)

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
All phases 0→8, 0A→8A, 1B→5C, 9A→10C, and 11A→11E are already completed and working.
I need you to implement Phase 12A — this EXTENDS the existing web app to add timetable, billing management, messaging, and announcements.
Do NOT rewrite existing pages. ADD new pages and EXTEND existing ones.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "Phase 12A")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "Phase 12A" checklist)
- Read ecole-platform-dev/web/src/features/ for existing page structure
- Read ecole-platform-dev/backend/app/api/v1/ for timetable (11A), billing (11B), messaging (11C) endpoints
- Read ecole-platform-dev/web/src/services/ws/ for existing WebSocket client (needed for real-time messaging)

PHASE 12A — Timetable + Billing + Messaging (Web):
- TimetablePage.tsx: weekly grid (Mon-Sat), color-coded by subject, ADM can add/edit/delete, teacher/student/parent read-only
- FeeStructuresPage.tsx + FeeAssignmentsPage.tsx + GenerateInvoicesPage.tsx (ADM billing management)
- Extend InvoicesPage with overdue indicators + retry status
- ConversationsPage.tsx (inbox) + ChatPage.tsx (message thread with read receipts via WebSocket)
- Unread message count badge on navigation
- AnnouncementsPage.tsx (list + create/publish for ADM/DIR)
- i18n (fr/ar/en)

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- Suggest git commands. Update TODO_GENERAL.md. Phase 12A ONLY.
```

---

## Phase 12B — Timetable + Billing + Messaging (Mobile)

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
All phases 0→8, 0A→8A, 1B→5C, 9A→10C, 11A→11E, and 12A are already completed and working.
I need you to implement Phase 12B — this EXTENDS the existing mobile app to add timetable, messaging, and announcements.
Do NOT rewrite existing screens. ADD new screens and EXTEND existing ones.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "Phase 12B")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "Phase 12B" checklist)
- Read ecole-platform-dev/mobile/lib/features/ for existing screen structure
- Read ecole-platform-dev/web/src/features/timetable/ and web/src/features/messages/ to match web UX
- Read ecole-platform-dev/mobile/lib/shared/ for push notification + WebSocket setup

PHASE 12B — Timetable + Messaging + Announcements (Mobile):
- timetable_screen.dart: weekly grid (swipe days on phone, full week on tablet), color-coded
- conversations_screen.dart: inbox with unread badges
- chat_screen.dart: chat bubbles, real-time WebSocket, read receipts
- Push notification → deep link to conversation on new message
- announcements_screen.dart: list + push for new announcements
- Update InvoicesScreen with overdue indicators + retry status
- Offline cache for conversations + announcements
- i18n (fr/ar/en)

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- Suggest git commands. Update TODO_GENERAL.md. Phase 12B ONLY.
```

---

## Phase 12C — Student Progress Dashboard (Web + Mobile)

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
All phases 0→8, 0A→8A, 1B→5C, 9A→10C, 11A→11E, 12A, and 12B are already completed and working.
I need you to implement Phase 12C — this adds progress visualization dashboards on BOTH web and mobile.
Do NOT rewrite existing pages/screens. ADD new pages/screens and EXTEND existing ones.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES.md (scroll to "Phase 12C")
- Read ecole-platform-dev/TODO_GENERAL.md (scroll to "Phase 12C" checklist)
- Read ecole-platform-dev/backend/app/api/v1/ for progress endpoints (from 11D): GET /progress/student/{id}, /progress/class/{id}, /progress/me, /progress/children
- Read ecole-platform-dev/web/src/features/ for existing page structure (recharts already available)
- Read ecole-platform-dev/mobile/lib/features/ for existing screen structure

PHASE 12C — Progress Dashboards (Web + Mobile):
- Web: ProgressDashboardPage.tsx — student progress with 4 charts (grade trend line, content completion pie, activity scores bar, attendance donut) using recharts
- Web: extend parent dashboard with per-child progress cards + drill-down
- Web: ClassProgressPage.tsx — teacher class-wide averages + per-student sparklines
- Mobile: progress_screen.dart — same charts using fl_chart, swipe between tabs
- Mobile: parent child progress cards
- All charts render with real data from 11D endpoints
- i18n (fr/ar/en)

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command.
- Suggest git commands. Update TODO_GENERAL.md. Phase 12C ONLY.
```

---

## Missing V1 Features — Phases Summary Table

| Sub-Phase | Tool | Open Folder | Focus | Cascades To |
|-----------|------|-------------|-------|-------------|
| **11A** | Claude Code | `Ecole-Platform/` | Timetable / schedule management backend | 12A, 12B |
| **11B** | Claude Code | `Ecole-Platform/` | Billing enhancements (fee structures, retry, reminders) | 12A, 12B |
| **11C** | Claude Code | `Ecole-Platform/` | Messaging + SMS fallback + announcements backend | 12A, 12B |
| **11D** | Claude Code | `Ecole-Platform/` | Student progress visualization backend | 12C |
| **11E** | Claude Code | `Ecole-Platform/` | Feature toggles system | — |
| **12A** | Claude Code | `Ecole-Platform/` | Timetable + billing + messaging UI (web) | — |
| **12B** | Claude Code | `Ecole-Platform/` | Timetable + messaging + announcements (mobile) | — |
| **12C** | Claude Code | `Ecole-Platform/` | Student progress dashboard (web + mobile) | — |
