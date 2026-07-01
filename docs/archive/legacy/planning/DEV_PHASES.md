# École Platform — Development Phases Guide

> This file is your roadmap for building the platform step by step.
> Each phase has a clear goal, the subfolder you work in, and what "done" looks like.
> Open a new Claude Code / Cowork session per phase, focused on the relevant subfolder.

---

## Recommended Approach

**Start with:** `backend/` + `infra/` (they go together — you can't test the backend without Docker running the DB)

**Why not web/ or mobile/ first?** The frontend has nothing to talk to yet. You need working API endpoints before building pages. The correct order is: infra → backend → web → mobile.

**Session strategy:** One session = one phase (or sub-phase if it's big). Give Claude the prompt at the bottom of each phase, and it will know exactly what to do.

---

## Phase 0 — Docker & Infrastructure *(~1 day)*
**Subfolder:** `infra/` + root files
**Goal:** `make up` starts PostgreSQL, Redis, and backend — all healthy.

### What to do:
1. Copy `.env.example` → `.env` (already done if you ran setup)
2. Verify `docker compose -f infra/docker-compose.dev.yml up -d` works
3. Verify PostgreSQL is reachable: `psql -h localhost -U ecole -d ecole_platform`
4. Verify Redis is reachable: `redis-cli ping`
5. Verify backend health: `curl http://localhost:8000/api/v1/health`
6. Test all Makefile commands: `make up`, `make down`, `make logs`, `make shell`

### Done when:
- [ ] All 4 services start (postgres, redis, backend, web)
- [ ] Health checks pass
- [ ] `make` commands all work
- [ ] No errors in `make logs`

---

## Phase 1 — Database Schema & Migrations *(~2-3 days)*
**Subfolder:** `backend/` (models + alembic)
**Goal:** All 6 domain tables exist in PostgreSQL with correct indexes and constraints.

### What to do:
1. Create SQLAlchemy models for each domain (IAM → ERP → LMS → COM → Billing → Audit)
2. Generate Alembic migrations per domain group (G1 through G6)
3. Run `make migrate` — all tables created
4. Verify indexes and constraints in PostgreSQL
5. Create seed data script for dev environment

### Migration order (strict):
```
G1-IAM (users, memberships, sessions, invitations, recovery)
  ↓
G2-ERP (academic_years, periods, classes, enrollments, attendance, justifications)
  ↓
G3-LMS (courses, assignments, submissions, grades, content, activities, assessments)
  ↓
G4-COM (consent_preferences, notifications, deliveries, parent_feed_items)
  ↓
G5-Billing (invoices, items, payment_attempts, proofs, webhook_events)
  ↓
G6-Audit (audit_logs)
```

### Key files to create/modify:
- `backend/app/models/` — One file per domain (iam.py, erp.py, lms.py, com.py, billing.py, audit.py)
- `backend/app/models/__init__.py` — Import all models
- `backend/alembic/versions/` — Generated migration files

### Done when:
- [ ] `make migrate` runs cleanly (alembic upgrade head)
- [ ] All P0 tables visible in PostgreSQL
- [ ] Unique/partial indexes from Pack C4 are present
- [ ] `make migrate-down` rolls back without errors
- [ ] Seed script populates test data

---

## Phase 2 — Auth & Security Pipeline *(~3-4 days)*
**Subfolder:** `backend/` (core/security, api/v1/auth, services/auth)
**Goal:** Complete JWT auth flow + RBAC + ABAC + audit trail.

### What to do:
1. JWT token generation/validation (access + refresh cookie)
2. Auth endpoints: POST /auth/login, /auth/refresh, /auth/logout, GET /me
3. RBAC middleware with 50+ permission mappings from Pack C6
4. ABAC guards: school boundary, parent-child, teacher assignment
5. Audit trail service (log all denies + sensitive allows)
6. X-Correlation-Id middleware
7. Invitation code endpoints (create/consume/revoke)
8. Account recovery flow (request/verify/reset)
9. Error response model + deny ordering (401→404→403)

### Key files to create/modify:
- `backend/app/core/security.py` — JWT + password hashing
- `backend/app/api/v1/auth.py` — Auth endpoints
- `backend/app/services/auth.py` — Auth business logic
- `backend/app/core/middleware.py` — Correlation ID, RBAC
- `backend/app/core/permissions.py` — Permission catalog
- `backend/app/services/audit.py` — Audit trail
- `backend/app/core/exceptions.py` — Domain exceptions + ErrorResponse

### Done when:
- [ ] Login returns JWT + sets refresh cookie
- [ ] Refresh rotates tokens with CSRF protection
- [ ] /me returns user profile with permissions
- [ ] RBAC blocks unauthorized roles (403)
- [ ] School boundary returns 404 (not 403) for cross-tenant
- [ ] Audit logs capture all denies
- [ ] Integration tests pass for auth flow

---

## Phase 3 — Core API Endpoints *(~4-5 days)*
**Subfolder:** `backend/` (api/v1/, services/, schemas/)
**Goal:** All P0 CRUD endpoints for ERP, LMS, Billing, COM domains.

### What to do:
1. Standard response envelope ({ data, meta } with cursor pagination)
2. Idempotency-Key middleware (Redis-backed)
3. ERP endpoints: classes, enrollments, attendance, justifications
4. LMS endpoints: courses, assignments, submissions, grading, results, content, activities, assessments
5. Billing endpoints: invoices, payment initiation, webhook handler
6. COM endpoints: notifications, consent, feed
7. Pydantic schemas for all request/response models

### Done when:
- [ ] All 41+ P0 endpoints respond correctly
- [ ] Cursor pagination works on all list endpoints
- [ ] Idempotency-Key prevents duplicates
- [ ] Error codes follow ERR-{DOMAIN}-{NNN} pattern
- [ ] Integration tests cover happy + unhappy paths

---

## Phase 4 — Web Frontend *(~5-7 days)*
**Subfolder:** `web/`
**Goal:** React app with auth, routing, all P0 pages, i18n/RTL.

### What to do:
1. `npm install` (install dependencies)
2. API client service with mandatory headers
3. Session management (token in memory, refresh via cookie)
4. Login page + route guards
5. Feature pages: /feed, /notifications, /content-items, /results, /invoices, /activities
6. Profile page (/me)
7. i18n (fr/ar/en) with RTL for Arabic
8. Error handling with categorized banners

### Done when:
- [ ] Login → role-appropriate dashboard works
- [ ] All P0 routes render with loading/empty/error states
- [ ] Arabic RTL layout works
- [ ] API client sends all mandatory headers

---

## Phase 5 — Mobile App *(~5-7 days)*
**Subfolder:** `mobile/`
**Goal:** Flutter app with auth, offline cache, push notifications, core screens.

### What to do:
1. `flutter pub get`
2. API client with offline write queue
3. Secure token storage (keychain/keystore)
4. Auth flow (login/refresh/logout)
5. SQLite offline cache with TTL policies
6. Push notifications (FCM + APNs)
7. Core screens: feed, notifications, content, results, invoices

### Done when:
- [ ] App runs on iOS + Android
- [ ] Offline cache serves data when network unavailable
- [ ] Push notifications navigate to correct screen

---

## Phase 6 — Testing & Quality *(~3-4 days)*
**Subfolder:** `backend/tests/` + `web/` + CI
**Goal:** ≥80% coverage, contract tests, security tests, E2E critical journeys.

### What to do:
1. Backend unit tests (IAM, ERP, LMS, Billing services)
2. Integration tests (full API flows with DB)
3. Contract tests (verify against C5 OpenAPI spec)
4. RBAC security tests (every endpoint × every role)
5. Frontend E2E (J1-J4 critical journeys)
6. CI pipeline with quality gates
7. Coverage enforcement

---

## Phase 7 — DevOps & Monitoring *(~2-3 days)*
**Subfolder:** `infra/`
**Goal:** Stage environment, monitoring stack, backup/DR.

---

## Phase 8 — Data, AI & Launch Prep *(~2-3 days)*
**Subfolder:** `backend/` (analytics + AI endpoints)
**Goal:** Event tracking, KPI dashboard, AI guardrails, pilot readiness.

---

## Summary: What Subfolder to Open Per Phase

| Phase | Primary Subfolder | Secondary |
|-------|-------------------|-----------|
| 0 | `infra/` | root (Makefile, .env) |
| 1 | `backend/` (models, alembic) | `infra/postgres/` |
| 2 | `backend/` (core, api, services) | — |
| 3 | `backend/` (api, services, schemas) | — |
| 4 | `web/` | — |
| 5 | `mobile/` | — |
| 6 | `backend/tests/` + `web/` | CI config |
| 7 | `infra/` | — |
| 8 | `backend/` | — |

---

## Recommended Session Strategy

**Phase 0+1+2 = one big Claude Code session** (they're tightly coupled — Docker, DB, Auth)
Open Claude Code pointed at `ecole-platform-dev/` root so it can access both `backend/` and `infra/`.

**Phase 3 = dedicated backend session** (focused on API endpoints)

**Phase 4 = dedicated web session** (open `web/` subfolder)

**Phase 5 = dedicated mobile session** (open `mobile/` subfolder)

**Phase 6+ = back to root** (cross-cutting concerns)

---
---

# Advanced Sub-Phases — All Phases (Production Hardening)

> All 8 original phases are complete. These advanced sub-phases harden each phase
> in order (0→1→2→...→8), adding production-critical features, closing gaps,
> and cascading improvements across dependent layers (e.g., auth changes → web + mobile).
>
> **Cascade rule:** When a backend sub-phase adds a feature (e.g., 2FA in Phase 2A),
> later sub-phases (4C, 5A) must integrate the corresponding frontend/mobile support.

---

## Phase 0A — Infrastructure Production Hardening *(~0.5 day)*
**Subfolder:** `infra/` + root files
**Goal:** Complete docker-compose.prod.yml, add missing Makefile targets, harden dev config.

### What to do:
1. Add resource limits to `docker-compose.dev.yml` (backend 512M/1CPU, web 256M/0.5CPU, postgres 1G, redis 256M)
2. Add logging driver config (`json-file` with max-size 10m, max-file 3) to all services
3. Complete `docker-compose.prod.yml`: production targets for all services, TLS-ready Nginx, managed DB/Redis URL placeholders, secret references (Docker secrets or env file)
4. Add Makefile targets: `make build` (rebuild images), `make staging-up` / `make prod-up`, `make shell-db` (psql), `make redis-cli`, `make backup` / `make restore` (wrappers for backup scripts), `make docker-prune`, `make version`
5. Add missing `.env.example` vars: `UPLOAD_DIR`, `MAX_FILE_SIZE_MB`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `S3_ENDPOINT` (placeholder), `TOTP_ISSUER`
6. Create `docker-compose.override.yml.example` for local dev customization

### Done when:
- [ ] `docker-compose.prod.yml` defines all services with resource limits, secrets, and TLS-ready nginx
- [ ] All new Makefile commands work (`make build`, `make staging-up`, `make shell-db`, `make backup`, etc.)
- [ ] `.env.example` documents all vars for Phases 0-8+ features
- [ ] Logging driver configured on all dev services

---

## Phase 1A — Database Views, Parent-Child Links & Migration Hardening *(~1 day)*
**Subfolder:** `backend/` (models, alembic)
**Goal:** Add materialized views for complex queries, create explicit parent_child_links table, harden migration workflow.

### What to do:
1. Create `parent_child_links` table via Alembic migration (parent_user_id, child_user_id, school_id, status, linked_at, linked_by) with unique constraint on (parent, child, school)
2. Create PostgreSQL views via migration:
   - `vw_user_permissions` — users + memberships + role permissions joined
   - `vw_active_sessions` — active sessions with user info + device context
   - `vw_assignment_results` — assignments + submissions + grades summary per student
   - `vw_invoice_balance` — invoices + payment_attempts aggregated balance
3. Create materialized view `mv_kpi_daily` — pre-computed KPI-G1-001 through G1-006 (refresh daily via background task)
4. Update `backend/app/models/__init__.py` to import `ParentChildLink` model
5. Add migration naming convention enforcement: `{number}_{group}_{description}.py` (e.g., `003_g8_parent_child_links.py`)
6. Create `scripts/validate_migrations.py` — checks naming, up/down roundtrip, no raw SQL without comments
7. Update `get_parent_child_ids()` in `dependencies.py` to use `parent_child_links` table instead of enrollment-based derivation
8. Add `make migrate-status` target (show pending migrations)

### Done when:
- [ ] `parent_child_links` table exists with proper constraints and seed data
- [ ] All 4 views queryable in PostgreSQL (`SELECT * FROM vw_user_permissions LIMIT 1`)
- [ ] `mv_kpi_daily` materialized view refreshes without error
- [ ] `get_parent_child_ids()` uses `parent_child_links` table
- [ ] Migration naming convention enforced by validation script
- [ ] `make migrate-status` shows current migration state

---

## Phase 2A — Password Policy & Session Management *(~1 day)*
**Subfolder:** `backend/` (core/, api/v1/, services/)
**Goal:** Enforce strong password policy, add session listing/revocation endpoints, add rate limit headers.

### What to do:
1. Create `core/password_policy.py` — `PasswordValidator` class:
   - Min 12 chars (up from 8)
   - At least 1 uppercase, 1 lowercase, 1 digit, 1 special char
   - Reject common patterns (123456, qwerty, password, etc.) — load from `data/common_passwords.txt`
   - Reject passwords containing user's name or email
   - Return structured errors (which rules failed)
2. Enforce password policy on: `/auth/login` (new accounts via invite), `/recovery/reset`, `/invites/consume`
3. Create `GET /auth/sessions` — list user's active sessions (device, IP, last_active, created_at)
4. Create `DELETE /auth/sessions/{session_id}` — revoke a specific session (user can revoke own, ADM can revoke any in school)
5. Add device fingerprint to Session model: `user_agent`, `ip_address`, `device_name` (parsed from User-Agent)
6. Add Alembic migration for Session table new columns (user_agent, ip_address, device_name)
7. Add rate limit headers to all responses: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
8. Extend rate limiting: per-endpoint categories (auth: 5/15min, write: 30/min, read: 100/min)

### Cascade to later phases:
- **Phase 4C** must add session management UI (list sessions, revoke button)
- **Phase 5A** must store device info on mobile login

### Done when:
- [ ] Password "abc123" rejected with clear error message listing failed rules
- [ ] Password "Str0ng!P@ssw0rd2025" accepted
- [ ] `GET /auth/sessions` returns list of active sessions with device info
- [ ] `DELETE /auth/sessions/{id}` revokes session and invalidates token
- [ ] Rate limit headers present on all API responses
- [ ] Integration tests for password validation + session management

---

## Phase 2B — Two-Factor Authentication (TOTP) & Email Verification *(~1-2 days)*
**Subfolder:** `backend/` (core/, api/v1/, services/, models/)
**Goal:** Optional TOTP-based 2FA per user, email verification on invite consumption, backup codes.

### What to do:
1. Add `pyotp` + `qrcode` to requirements.txt
2. Create `core/totp.py` — TOTP secret generation, QR code URI, code verification (30s window, 1 drift)
3. Add to User model: `totp_secret` (encrypted), `totp_enabled`, `totp_verified_at`, `backup_codes` (hashed array)
4. Alembic migration for User table new columns
5. Create endpoints:
   - `POST /auth/2fa/setup` — generate TOTP secret + QR code URI (requires auth)
   - `POST /auth/2fa/verify-setup` — verify first TOTP code to activate 2FA + return backup codes
   - `POST /auth/2fa/disable` — disable 2FA (requires current TOTP code or backup code)
   - `POST /auth/2fa/verify` — verify TOTP code during login flow (called after password check)
6. Modify login flow: if user has `totp_enabled=True`, return `{ requires_2fa: true, temp_token: "..." }` instead of full tokens. Client must call `/auth/2fa/verify` with temp_token + TOTP code to get real tokens.
7. Generate 10 backup codes on 2FA setup (bcrypt hashed, single-use)
8. Create `POST /auth/verify-email` — verify email via OTP sent during invite consumption
9. Add `email_verified_at` column to User model
10. Hook: on invite consumption → send email OTP → user must verify before account is fully active

### Cascade to later phases:
- **Phase 4C** must add 2FA setup page (QR code display, code input, backup codes download)
- **Phase 5A** must add 2FA verification screen in mobile login flow

### Done when:
- [ ] `POST /auth/2fa/setup` returns QR code URI and provisioning secret
- [ ] `POST /auth/2fa/verify-setup` activates 2FA after valid code
- [ ] Login with 2FA enabled returns `requires_2fa: true` instead of tokens
- [ ] `POST /auth/2fa/verify` with valid TOTP code returns full tokens
- [ ] Backup codes work as TOTP fallback (single-use, consumed on verify)
- [ ] Email verification OTP sent on invite consumption
- [ ] Integration tests for full 2FA flow + backup code flow

---

## Phase 3A — OpenAPI Spec Export & API Documentation *(~0.5 day)*
**Subfolder:** `backend/`
**Goal:** Auto-export a versioned OpenAPI 3.1 JSON spec, add endpoint descriptions, generate a static Redoc HTML page.

### What to do:
1. Add `openapi_tags` metadata to `main.py` grouping endpoints by domain (IAM, ERP, LMS, COM, Billing, AI)
2. Add `summary`, `description`, and `response_description` to every router decorator
3. Create `scripts/export_openapi.py` — dumps `app.openapi()` to `docs/openapi.json`
4. Pin the spec version to match `app.version` from config
5. Add a CI step in `.github/workflows/ci.yml` that exports the spec and fails if it drifts from the committed version
6. Generate a static Redoc HTML page (`docs/api.html`)
7. Add Makefile command: `make openapi`

### Done when:
- [ ] `make openapi` exports `docs/openapi.json` matching the running API
- [ ] CI fails if committed spec differs from generated spec
- [ ] Static Redoc page renders all endpoints with descriptions
- [ ] Every endpoint has a meaningful summary and at least one response example

---

## Phase 3B — File Upload & Storage Pipeline *(~1-2 days)*
**Subfolder:** `backend/` (api/v1/, services/, core/)
**Goal:** Upload/download endpoints for submission_files and content_item_assets, with local storage (S3-compatible interface).

### What to do:
1. Create `core/storage.py` — abstract `StorageBackend` protocol with `upload`, `download`, `delete`, `presigned_url`
2. Implement `LocalStorageBackend` (saves to configurable `UPLOAD_DIR`)
3. Add config vars: `UPLOAD_DIR`, `MAX_FILE_SIZE_MB` (25), `ALLOWED_MIME_TYPES`
4. Create upload/download/delete endpoints for submissions and content-items
5. File validation: MIME whitelist, size limit (413), SHA-256 checksum, virus scan placeholder
6. Persist metadata in existing `submission_files` / `content_item_assets` tables
7. Docker volume mount for uploads

### Cascade to later phases:
- **Phase 4C** must add file upload UI (drag-drop for submissions, asset upload for teachers)
- **Phase 5A** must add file picker / camera capture for mobile uploads

### Done when:
- [ ] POST multipart upload works, GET download returns correct file
- [ ] SHA-256 checksum verified on round-trip
- [ ] MIME + size validation enforced
- [ ] RBAC: STD own files only, TCH assigned class files, ADM all
- [ ] Integration tests for full upload/download/delete cycle

---

## Phase 3C — WebSocket Real-time Notifications *(~1-2 days)*
**Subfolder:** `backend/` (api/v1/, core/, services/)
**Goal:** WebSocket endpoint for real-time push, replacing polling for connected clients.

### What to do:
1. Create `core/ws_manager.py` — ConnectionManager with Redis Pub/Sub
2. Create `api/v1/ws.py` — `GET /ws` with JWT auth
3. Create `services/realtime.py` — publish events on notification/feed/grade/payment changes
4. Hook into existing services
5. Heartbeat 30s, connection limit 3 per user, graceful degradation

### Cascade to later phases:
- **Phase 4C** must add WebSocket client in React (auto-connect, fallback to polling)
- **Phase 5A** must add WebSocket client in Flutter (background reconnection)

### Done when:
- [ ] WebSocket connects with JWT, rejects without auth
- [ ] Notification creation pushes real-time event to connected user
- [ ] Redis Pub/Sub works across multiple backend instances
- [ ] Integration test: create notification → WS client receives it

---

## Phase 3D — Advanced Query Filters & Full-text Search *(~1 day)*
**Subfolder:** `backend/` (api/v1/, core/)
**Goal:** Filtering, sorting, and full-text search on all list endpoints.

### What to do:
1. Create `core/filtering.py` — generic FilterParams + SortParams dependencies
2. Create `core/search.py` — PostgreSQL tsvector full-text search
3. Add GIN indexes via Alembic migration
4. Add `?filter[status]=X&sort=-created_at&search=keyword` to all list endpoints
5. Compose with existing cursor pagination

### Cascade to later phases:
- **Phase 4C** must add search bar + filter dropdowns on list pages
- **Phase 5B** must add search/filter UI on mobile list screens

### Done when:
- [ ] `GET /courses?filter[status]=published&sort=-created_at` works
- [ ] `GET /content-items?search=mathematiques` returns full-text matches
- [ ] Filters compose with cursor pagination
- [ ] Integration tests for filter + sort + search combinations

---

## Phase 3E — Background Tasks & Email Notifications *(~1-2 days)*
**Subfolder:** `backend/` (services/, core/, infra/)
**Goal:** ARQ task queue for email dispatch, scheduled cleanup, notification digests.

### What to do:
1. Add `arq` to requirements.txt
2. Create `core/tasks.py` — ARQ worker settings + task registry
3. Create `services/email.py` — SMTP + Jinja2 templates (fr/ar/en)
4. Email templates: welcome, OTP, invoice reminder, grade published
5. Background tasks: send_email, cleanup_expired_sessions, cleanup_expired_cache, send_notification_digest
6. Hook into recovery → OTP email, grade published → notification email
7. Add ARQ worker to `docker-compose.dev.yml`
8. Prometheus metrics for task tracking

### Done when:
- [ ] ARQ worker processes tasks from Redis queue
- [ ] Emails send via SMTP with correct locale template
- [ ] Account recovery enqueues OTP email end-to-end
- [ ] Session cleanup removes expired sessions
- [ ] Prometheus metrics track task throughput/failures

---

## Phase 4A — Admin Dashboard *(~2-3 days)*
**Subfolder:** `web/` (features/admin/)
**Goal:** Full admin dashboard with user management, invitation codes, audit log viewer, school configuration.

### What to do:
1. Create `/admin` route group (ADM, DIR roles only)
2. Create `features/admin/DashboardPage.tsx` — summary cards (total users, active sessions, pending invitations, recent audit events)
3. Create `features/admin/UsersPage.tsx` — user list with search/filter, suspend/activate actions, role assignment
4. Create `features/admin/InvitationsPage.tsx` — issue new invitation codes, view active/consumed/revoked codes, revoke action
5. Create `features/admin/AuditLogPage.tsx` — searchable audit log viewer with correlation_id filter, date range, event type filter
6. Create `features/admin/SchoolSettingsPage.tsx` — school name, timezone, notification preferences
7. Create `features/admin/JustificationReviewPage.tsx` — list pending absence justifications, approve/deny with reason
8. Add admin sidebar navigation with appropriate icons
9. Add role guard: only ADM/DIR can access `/admin/*` routes

### Done when:
- [ ] `/admin` dashboard renders with summary cards
- [ ] User management: list, search, suspend, activate, assign roles
- [ ] Invitation codes: create, list, revoke
- [ ] Audit log viewer: search by correlation_id, filter by date/event type
- [ ] Absence justification review: approve/deny workflow

---

## Phase 4B — Teacher Dashboard *(~2-3 days)*
**Subfolder:** `web/` (features/teacher/)
**Goal:** Teacher-specific pages for class management, assignment creation, submission grading, attendance marking.

### What to do:
1. Create `/teacher` route group (TCH role only)
2. Create `features/teacher/ClassesPage.tsx` — list teacher's assigned classes with student roster
3. Create `features/teacher/AssignmentFormPage.tsx` — create/edit assignment (title, description, due date, points, attached files via Phase 3B upload)
4. Create `features/teacher/SubmissionsPage.tsx` — list submissions for an assignment, download files, inline grading form (score + feedback)
5. Create `features/teacher/AttendancePage.tsx` — mark attendance per class session (present/absent/late checkboxes per student)
6. Create `features/teacher/AssessmentFormPage.tsx` — create/edit/publish assessments
7. Create `features/teacher/CoursesPage.tsx` — create/manage courses, upload content items (via Phase 3B)
8. Add teacher sidebar navigation

### Done when:
- [ ] Teacher can create assignments with file attachments
- [ ] Teacher can view/download/grade submissions inline
- [ ] Teacher can mark attendance for a class session
- [ ] Teacher can create/publish assessments
- [ ] Teacher can upload course content items

---

## Phase 4C — CRUD Forms, 2FA UI & Cascade Integration *(~2 days)*
**Subfolder:** `web/` (features/, services/)
**Goal:** Integrate all backend improvements from Phases 2A, 2B, 3B, 3C, 3D into the web frontend.

### What to do (cascading from earlier phases):
1. **From 2A — Session Management UI:**
   - Create `features/profile/SessionsPage.tsx` — list active sessions with device info, revoke button
   - Show "current session" indicator
2. **From 2B — 2FA Setup UI:**
   - Create `features/profile/TwoFactorPage.tsx` — enable/disable 2FA, show QR code, verify setup code, download backup codes
   - Modify `LoginPage.tsx` — handle `requires_2fa` response, show TOTP code input, backup code fallback
3. **From 3B — File Upload UI:**
   - Add drag-drop file upload to submission page (student submits files)
   - Add file upload to teacher's content/assignment creation
   - Show file list with download/delete actions
4. **From 3C — WebSocket Client:**
   - Create `services/ws/WebSocketClient.ts` — auto-connect on login, reconnect with backoff, parse events
   - Show real-time notification toast when WS event received
   - Update notification badge count in real-time
5. **From 3D — Search & Filters:**
   - Add search bar component to content, courses, notifications pages
   - Add filter dropdowns (status, date range) on list pages
   - Add sort toggle (newest/oldest) on list pages
6. **Student CRUD forms:**
   - Submission upload form (select assignment, drag-drop files, submit)
   - Parent justification form (select child, date, reason, submit)
7. **Profile edit form:**
   - Edit name, phone, language preference
   - Change password (with password policy feedback)

### Done when:
- [ ] Session management: list sessions, revoke works
- [ ] 2FA: setup with QR code, verify, backup codes, login with TOTP
- [ ] File upload: drag-drop works for submissions and content
- [ ] WebSocket: real-time notification toasts appear
- [ ] Search/filter: search bar and filters work on list pages
- [ ] Profile: edit form saves, password change enforces policy

---

## Phase 5A — Push Notifications, Biometric Auth & 2FA Mobile *(~2 days)*
**Subfolder:** `mobile/` (features/, shared/, data/)
**Goal:** Complete Firebase push notifications, add biometric unlock, integrate 2FA from Phase 2B.

### What to do:
1. **Push notifications:**
   - Add Firebase configuration files (google-services.json, GoogleService-Info.plist) — document setup steps
   - Implement deep-link routing: notification tap → navigate to correct screen (feed, results, invoices)
   - Notification permission request flow on first launch
   - Badge count update
2. **Biometric authentication:**
   - Add `local_auth` package to pubspec.yaml
   - Create `features/auth/biometric_service.dart` — check availability, authenticate with fingerprint/FaceID
   - After first successful login, offer "Enable biometric unlock"
   - On app resume: if biometric enabled, show biometric prompt instead of full login
   - Fallback to password if biometric fails 3 times
3. **2FA integration (cascade from 2B):**
   - Add 2FA verification screen in login flow (TOTP code input after password)
   - Add backup code input option
   - Add 2FA setup screen in profile (show QR code, verify code, save backup codes)
4. **File upload (cascade from 3B):**
   - Add file picker for submission upload (gallery, camera, documents)
   - Show upload progress indicator
   - Preview uploaded files before submit
5. **WebSocket client (cascade from 3C):**
   - Create `data/api/ws_client.dart` — connect on login, reconnect on network restore
   - Show local notification on WS event when app is in foreground
   - Update badge count via WS events
6. **Device info on login (cascade from 2A):**
   - Send `device_name`, `user_agent`, `ip_address` on login request for session tracking

### Done when:
- [ ] Push notification tap navigates to correct screen
- [ ] Biometric unlock works on app resume (fingerprint/FaceID)
- [ ] 2FA verification screen shows during login when required
- [ ] File picker allows submission upload with progress indicator
- [ ] WebSocket receives real-time events, shows local notifications
- [ ] Device info sent on login for session management

---

## Phase 5B — Admin/Teacher Mobile Screens & Search *(~1-2 days)*
**Subfolder:** `mobile/` (features/)
**Goal:** Add admin and teacher screens to mobile app, integrate search/filter from Phase 3D.

### What to do:
1. **Admin screens (cascade from 4A):**
   - `features/admin/admin_dashboard_screen.dart` — summary cards
   - `features/admin/users_screen.dart` — user list with search, suspend/activate
   - `features/admin/invitations_screen.dart` — issue/revoke invitation codes
   - `features/admin/justification_review_screen.dart` — approve/deny justifications
2. **Teacher screens (cascade from 4B):**
   - `features/teacher/classes_screen.dart` — assigned classes with roster
   - `features/teacher/assignment_form_screen.dart` — create assignment with file upload
   - `features/teacher/submissions_screen.dart` — view/grade submissions
   - `features/teacher/attendance_screen.dart` — mark attendance per class
3. **Search & filter (cascade from 3D):**
   - Add search bar widget to content, courses, notifications screens
   - Add filter chips (status, date) on list screens
   - Add sort toggle
4. Update shell navigation: show admin/teacher tabs based on role

### Done when:
- [ ] Admin can manage users and invitations on mobile
- [ ] Teacher can create assignments and grade submissions on mobile
- [ ] Teacher can mark attendance on mobile
- [ ] Search and filter work on mobile list screens
- [ ] Role-based navigation shows correct tabs

---

## Phase 6A — E2E Tests, Load Testing & Security Audit *(~2 days)*
**Subfolder:** `backend/tests/` + `web/` + `infra/`
**Goal:** Playwright E2E tests for critical web journeys, k6 load tests, security audit tests.

### What to do:
1. **Playwright E2E tests (web):**
   - Install Playwright: `npm install -D @playwright/test`
   - J1: Login → navigate to feed → open notification → logout
   - J2: Teacher login → create assignment → verify in list
   - J3: Student login → submit file → verify in submissions
   - J4: Admin login → create invitation → verify in list → revoke
   - J5: Login with 2FA → verify TOTP flow (cascade from 2B)
   - Configure in CI pipeline (headless Chrome)
2. **k6 load tests:**
   - Install k6 scripts in `tests/load/`
   - Scenario 1: 100 concurrent logins (verify <500ms p95)
   - Scenario 2: 500 concurrent GET requests on list endpoints (verify <200ms p95)
   - Scenario 3: 50 concurrent file uploads (verify <2s p95)
   - Scenario 4: WebSocket connection storm (200 concurrent, verify stable)
   - Thresholds per F2 SLO targets
3. **Security audit tests:**
   - CSRF: verify double-submit cookie prevents cross-origin requests
   - XSS: verify React auto-escaping on user-generated content
   - SQL injection: parameterized queries verification (SQLAlchemy is safe, but test)
   - Auth bypass: verify 401 on all protected endpoints without token
   - Scope masking: verify 404 (not 403) for cross-school access
   - Password policy: verify weak passwords rejected

### Done when:
- [ ] Playwright E2E tests pass for all 5 journeys in CI
- [ ] k6 load test results meet SLO thresholds (p95 latency, error rate)
- [ ] Security audit tests pass (CSRF, XSS, SQL injection, auth bypass)
- [ ] CI pipeline includes E2E + load test stages

---

## Phase 7A — Production Environment & TLS *(~1 day)*
**Subfolder:** `infra/`
**Goal:** Production-ready deployment with TLS, secret management, health monitoring.

### What to do:
1. Complete `docker-compose.prod.yml`:
   - Backend: production target, 4 workers, resource limits
   - PostgreSQL: managed DB URL (placeholder), connection pool tuning (max_connections=100)
   - Redis: managed Redis URL (placeholder), maxmemory policy
   - Nginx: TLS termination with Let's Encrypt cert paths, HTTP→HTTPS redirect, security headers (HSTS, CSP, X-Frame-Options)
   - ARQ worker: production config
2. Create `infra/nginx/nginx-prod.conf` — TLS config, rate limiting, gzip compression, static file caching
3. Create `infra/scripts/deploy.sh` — deployment script (pull images, migrate, restart services, health check, rollback on failure)
4. Create `infra/scripts/ssl-renew.sh` — Let's Encrypt cert renewal (certbot)
5. Add Docker secrets support for sensitive env vars (JWT_SECRET_KEY, DB password, SMTP password)
6. Create `infra/scripts/healthcheck.sh` — comprehensive health check (API, DB, Redis, disk space, cert expiry)
7. Document deployment procedure in `infra/DEPLOYMENT.md`

### Done when:
- [ ] `docker-compose.prod.yml` starts all services with production config
- [ ] Nginx serves HTTPS with TLS certificate
- [ ] `deploy.sh` performs zero-downtime deployment with rollback
- [ ] Health check script validates all services
- [ ] Docker secrets protect sensitive env vars

---

## Phase 8A — GDPR Compliance & Analytics Dashboard *(~1-2 days)*
**Subfolder:** `backend/` (api/v1/, services/) + `web/` (features/admin/)
**Goal:** GDPR data export/deletion endpoints, admin analytics dashboard with KPI visualization.

### What to do:
1. **GDPR endpoints:**
   - `GET /users/{id}/data-export` — export all user data as JSON (profile, sessions, audit logs, submissions, grades, payments) — ADM or self
   - `POST /users/{id}/data-deletion` — anonymize user data (replace PII with hashes, keep audit structure) — ADM only, with confirmation
   - `GET /users/{id}/consent-log` — full consent change history
   - Audit trail on all GDPR actions
2. **Analytics admin dashboard (web):**
   - Create `features/admin/AnalyticsPage.tsx` — KPI dashboard
   - Cards: KPI-G1-001 (adoption rate), KPI-G1-002 (usage), KPI-G1-003 (auth error rate)
   - Charts: daily active users trend, login success rate trend, API latency p95 trend
   - Use recharts library for visualization
   - Date range selector (last 7d, 30d, 90d)
   - Auto-refresh every 5 minutes
3. **Materialized view refresh (cascade from 1A):**
   - Add background task `refresh_kpi_views` in ARQ worker (daily at 03:00)
   - `GET /kpis` endpoint reads from `mv_kpi_daily` for fast response

### Done when:
- [ ] `GET /users/{id}/data-export` returns complete user data JSON
- [ ] `POST /users/{id}/data-deletion` anonymizes PII, keeps audit structure
- [ ] Analytics dashboard shows KPI cards and trend charts
- [ ] KPI materialized view refreshes daily via background task
- [ ] Audit trail records all GDPR actions

---

## Master Summary: All Advanced Sub-Phases

| Sub-Phase | Focus | Effort | Cascades To |
|-----------|-------|--------|-------------|
| **0A** | Docker prod, Makefile, env vars | ~0.5 day | — |
| **1A** | DB views, parent-child links, migration hardening | ~1 day | 2A (parent-child) |
| **2A** | Password policy, session management, rate limit headers | ~1 day | 4C, 5A |
| **2B** | 2FA/TOTP, email verification, backup codes | ~1-2 days | 4C, 5A |
| **3A** | OpenAPI spec export, Redoc, CI drift detection | ~0.5 day | — |
| **3B** | File upload/download, S3-ready storage | ~1-2 days | 4C, 5A |
| **3C** | WebSocket real-time, Redis Pub/Sub | ~1-2 days | 4C, 5A |
| **3D** | Filters, sorting, PostgreSQL full-text search | ~1 day | 4C, 5B |
| **3E** | ARQ worker, email templates, background tasks | ~1-2 days | — |
| **4A** | Admin dashboard (users, invites, audit, settings) | ~2-3 days | 5B |
| **4B** | Teacher dashboard (assignments, grading, attendance) | ~2-3 days | 5B |
| **4C** | CRUD forms + cascade integration (2FA, WS, files, search) | ~2 days | — |
| **5A** | Push notifications, biometric auth, 2FA mobile, WS client | ~2 days | — |
| **5B** | Admin/teacher mobile screens, search/filter | ~1-2 days | — |
| **6A** | Playwright E2E, k6 load tests, security audit | ~2 days | — |
| **7A** | Production TLS, deploy script, secrets, health checks | ~1 day | — |
| **8A** | GDPR compliance, analytics dashboard, KPI refresh | ~1-2 days | — |

---
---

# NEW PHASES — Registration, Profiles & Cascade (Not Yet Started)

> These phases were added after analyzing the report specs vs code gaps.
> They cover: role-specific profile tables, self-registration with invitation code, and the web/mobile UI cascade.
>
> **All previous phases (0→8 and 0A→8A) are already completed.** Do NOT redo them.
>
> **Phases 1B, 2C, 4D, 5C are already completed.** Run remaining 3 phases: `2D → 4D-patch → 5C-patch`
> - 2D adds backend parent-child link management (schema fix + admin endpoints + parent endpoint)
> - 4D-patch and 5C-patch add the link management UI to the already-completed web and mobile code

---

## Phase 1B — Role-Specific Profile Tables *(~1 day)*
**Subfolder:** `backend/` (models, alembic, schemas, api)
**Goal:** Create profile extension tables for students, parents, and teachers with role-specific fields. Update registration and profile endpoints to read/write these fields.

### What to do:
1. Create `student_profiles` table via Alembic migration:
   - `user_id` (FK to users, unique), `school_id`, `student_number` (unique per school), `date_of_birth`, `gender` (optional), `class_level`, `nationality`, `guardian_notes` (text, optional)
2. Create `parent_profiles` table:
   - `user_id` (FK to users, unique), `school_id`, `relationship_type` (FATHER, MOTHER, GUARDIAN, OTHER), `cin_number` (optional, Moroccan national ID), `address` (optional), `profession` (optional), `emergency_phone` (optional)
3. Create `teacher_profiles` table:
   - `user_id` (FK to users, unique), `school_id`, `employee_id` (optional), `subject_specialty` (optional), `qualification` (optional), `hire_date` (optional)
4. Create SQLAlchemy models: `StudentProfile`, `ParentProfile`, `TeacherProfile` in `models/iam.py`
5. Create Pydantic schemas for each profile (create, update, response)
6. Create/extend endpoints:
   - `GET /me/profile` — returns role-specific profile data alongside user data
   - `PUT /me/profile` — update role-specific fields
   - `GET /admin/users/{id}/profile` — admin reads any user's profile (ADM only)
7. Update seed data to populate profiles for test users
8. Enhance invitation codes: add optional `target_student_id` field so admin can pre-link parent codes to a specific student

### Cascade to later phases:
- **Phase 2C** registration endpoint will populate profile on account creation
- **Phase 4D** will add profile edit forms per role on web
- **Phase 5C** will add profile screens on mobile

### Done when:
- [ ] All 3 profile tables exist with correct constraints
- [ ] `GET /me/profile` returns role-specific data
- [ ] `PUT /me/profile` updates role-specific fields
- [ ] Invitation codes support optional `target_student_id`
- [ ] Seed data includes profiles for all test users
- [ ] Integration tests for profile CRUD

---

## Phase 2C — Registration with Invitation Code *(~1-2 days)*
**Subfolder:** `backend/` (api/v1/, services/, core/)
**Goal:** Self-registration endpoint where a new user creates an account using an invitation code (code + email + name + password → account + membership + profile + parent-child link).

### What to do:
1. Create `POST /auth/register` — public endpoint (no auth required):
   - Input: `code`, `email`, `full_name`, `phone` (optional), `password`, `profile_data` (role-specific fields from Phase 1B)
   - Validates code (not expired, not consumed, not revoked)
   - Creates user with password (enforces password policy from Phase 2A)
   - Creates membership (role from code's `role_target`, school from code's `school_id`)
   - Creates role-specific profile (StudentProfile, ParentProfile, or TeacherProfile)
   - If code has `target_student_id` and role=PAR → creates `parent_child_link` automatically
   - Marks code as consumed
   - Sends email verification OTP (from Phase 2B)
   - Returns JWT tokens (user is logged in immediately)
2. Add rate limiting on `/auth/register` (auth category: 5/15min to prevent spam)
3. Add validation: email must not already exist for that school
4. Add audit trail: `user.register` event with correlation_id
5. Update login page flow: show "Register with code" option alongside "Login"
6. Create admin helper: `POST /admin/register-batch` — admin creates multiple accounts at once (CSV upload: name, email, role, class → generates invitation codes or directly creates accounts)

### Cascade to later phases:
- **Phase 4D** must add registration form on web (code + personal info + role-specific fields)
- **Phase 5C** must add registration screen on mobile

### Done when:
- [ ] `POST /auth/register` creates user + membership + profile from code
- [ ] Parent registration with `target_student_id` auto-creates parent_child_link
- [ ] Password policy enforced on registration
- [ ] Email verification OTP sent
- [ ] Rate limiting prevents registration spam
- [ ] Existing users cannot register again for same school+role
- [ ] Integration tests for full registration flow (PAR, STD, TCH scenarios)

---

## Phase 4D — Registration & Profile UI (Web) *(~1-2 days)*
**Subfolder:** `web/` (features/auth/, features/profile/)
**Goal:** Registration page and role-specific profile edit forms on web.

### What to do (cascading from 1B + 2C):
1. **Registration page:**
   - Create `features/auth/RegisterPage.tsx` — code input → role detected → show role-specific fields
   - Step 1: Enter invitation code → API validates → shows role + school name
   - Step 2: Enter email, full_name, phone, password (with policy feedback)
   - Step 3: Role-specific fields (date_of_birth for STD, relationship_type for PAR, subject for TCH)
   - Step 4: Email verification OTP input
   - Route: `/register`
2. **Profile edit forms (extend ProfilePage from 4C):**
   - Student section: student_number (read-only), date_of_birth, class_level
   - Parent section: relationship_type, CIN, address, profession, emergency_phone
   - Teacher section: employee_id (read-only), subject_specialty, qualification
3. **Admin batch registration:**
   - Create `features/admin/BatchRegisterPage.tsx` — CSV upload form for bulk account creation
   - Show preview table before submission, progress indicator during creation
4. Add "Register" link on LoginPage.tsx (alongside login form)
5. i18n translations for registration + profile fields (fr/ar/en)

### Done when:
- [ ] Registration page works end-to-end (code → personal info → role fields → OTP → logged in)
- [ ] Profile page shows and edits role-specific fields
- [ ] Admin can batch-register users via CSV upload
- [ ] All text translated (fr/ar/en)

---

## Phase 5C — Registration & Profile Mobile *(~1 day)*
**Subfolder:** `mobile/` (features/auth/, features/profile/)
**Goal:** Registration screen and role-specific profile screens on mobile.

### What to do (cascading from 1B + 2C):
1. **Registration screen:**
   - `features/auth/register_screen.dart` — stepper flow matching web (code → info → role fields → OTP)
   - Keyboard-friendly, auto-focus, validation on each step
2. **Profile screen enhancement:**
   - Add role-specific sections to existing profile screen
   - Student: date_of_birth (date picker), class_level
   - Parent: relationship_type (dropdown), CIN, emergency_phone
   - Teacher: subject_specialty, qualification
3. Add "Register" button on login screen
4. i18n for all new fields (fr/ar/en)

### Done when:
- [ ] Mobile registration flow works end-to-end
- [ ] Profile screen shows/edits role-specific data
- [ ] All text translated (fr/ar/en)

---

## Phase 2D — Parent-Child Link Management & Invitation Schema Fix *(~1-1.5 days)*

> **Depends on:** Phase 2C (registration + invitation codes)
> **Cascades to:** Phase 4D (web UI), Phase 5C (mobile UI)

### What to do

**1. Fix InviteCreateRequest schema gap:**
- Add optional `target_student_id: UUID | None` field to `InviteCreateRequest` in `backend/app/schemas/auth.py`
- Update `InvitationService.create_invite()` in `backend/app/services/auth.py` to accept and persist `target_student_id`
- Validate that `target_student_id` belongs to a STD user in the same school
- Update `POST /invites/create` endpoint in `backend/app/api/v1/invitations.py` to pass the field through

**2. Parent-child link management endpoints (admin):**
- `POST /admin/parent-child-links` — admin manually links a parent to a student (validates both exist in same school, parent has PAR role, student has STD role, no duplicate link)
- `GET /admin/parent-child-links?parent_id=X` or `?student_id=X` — list links filtered by parent or student, paginated
- `DELETE /admin/parent-child-links/{link_id}` — revoke a link (soft-delete: set status="revoked")
- Add these to `backend/app/api/v1/admin.py` with PERM-IAM:parent-link:* permissions

**3. Parent self-service endpoint:**
- `GET /me/children` — parent sees their linked children (id, full_name, class_level, school_name)
- Returns empty list if no links exist
- Add to `backend/app/api/v1/auth.py` or a new `backend/app/api/v1/family.py` router

**4. Batch registration schema update:**
- Add optional `target_student_id` to `BatchRegisterItem` in admin schemas
- When batch-creating PAR users with `target_student_id`, auto-create parent_child_link

**5. Integration tests:**
- Test invitation creation with `target_student_id` → register parent → verify auto-link created
- Test `POST /admin/parent-child-links` (success, duplicate, wrong school, wrong role)
- Test `GET /admin/parent-child-links` filtered by parent and student
- Test `DELETE /admin/parent-child-links/{id}` (revoke)
- Test `GET /me/children` (parent with 0, 1, 2 children)
- Test ABAC: parent can only access linked children's data

**6. Alembic migration:**
- No new tables needed (parent_child_links already exists)
- If any new permission codes added (PERM-IAM:parent-link:create, :read, :delete), add to seed

### Cascade
- Phase 4D must add: admin parent-child link management UI (link/unlink parents to students, list links), "My Children" section on parent profile page
- Phase 5C must add: "My Children" screen for parent role, admin link management if admin mobile features exist

### Done when
- `POST /invites/create` accepts optional `target_student_id` and the auto-link works end-to-end
- Admin can manually link/unlink parents and students via API
- Parents can see their linked children via `GET /me/children`
- Batch registration supports `target_student_id` for PAR users
- All integration tests pass
- ABAC guards confirmed working with the links

> **V2+ deferred:** Parent-initiated link requests (parent requests to link → admin approves). For V1, only admins can create links.

---

---

## Phase 4D-patch — Parent-Child Link UI (Web Patch) *(~0.5-1 day)*

> **Depends on:** Phase 2D (parent-child link endpoints) + Phase 4D already completed
> **This is a PATCH phase** — 4D was already run before 2D existed. This adds ONLY the parent-child link UI features that 2D introduced.

### What to do (ADD to existing 4D code — do NOT rewrite):
1. **Admin Parent-Child Link Management page:**
   - Create `features/admin/ParentChildLinksPage.tsx` — list all parent-child links for the school
   - Filter by parent name/email or student name/email (search input)
   - "Link Parent to Student" button → modal/form with parent dropdown + student dropdown → calls `POST /admin/parent-child-links`
   - "Revoke" button per row → confirmation dialog → calls `DELETE /admin/parent-child-links/{id}`
   - Add navigation entry in admin sidebar
2. **Invitation creation enhancement:**
   - On the existing invitation creation form (or wherever admin creates invites), when role=PAR is selected, show optional "Pre-link to student" dropdown → passes `target_student_id` to `POST /invites/create`
3. **Parent "My Children" section:**
   - On parent's dashboard or profile page, add "My Children" card/section
   - Calls `GET /me/children` → displays list of linked children (name, class_level)
   - Click child → navigate to child's grades/attendance page
4. i18n for all new UI text (fr/ar/en)

### Done when:
- [ ] Admin can list, create, and revoke parent-child links from the web UI
- [ ] Invitation form shows "Pre-link to student" when role=PAR
- [ ] Parent sees "My Children" on their dashboard
- [ ] All text translated (fr/ar/en)

---

## Phase 5C-patch — "My Children" Screen (Mobile Patch) *(~0.5 day)*

> **Depends on:** Phase 2D (parent-child link endpoints) + Phase 5C already completed
> **This is a PATCH phase** — 5C was already run before 2D existed. This adds ONLY the "My Children" feature for parents on mobile.

### What to do (ADD to existing 5C code — do NOT rewrite):
1. **Parent "My Children" screen:**
   - Create `features/family/my_children_screen.dart` — calls `GET /me/children`
   - List linked children with name, class_level, school
   - Tap child → navigate to child's grades/attendance
2. **Navigation entry:**
   - Add "My Children" entry in parent's bottom navigation or drawer menu
   - Only visible when user role = PAR
3. i18n for all new text (fr/ar/en)

### Done when:
- [ ] Parent sees "My Children" in navigation
- [ ] Tapping a child navigates to their grades/attendance
- [ ] All text translated (fr/ar/en)

---

## Updated Master Summary

| Sub-Phase | Focus | Effort | Cascades To |
|-----------|-------|--------|-------------|
| **1B** ✅ | Role-specific profile tables (student, parent, teacher) | ~1 day | 2C, 4D, 5C |
| **2C** ✅ | Registration with invitation code + auto-linking | ~1-2 days | 2D, 4D, 5C |
| **4D** ✅ | Registration page + profile edit UI (web) | ~1-2 days | 4D-patch |
| **5C** ✅ | Registration screen + profile (mobile) | ~1 day | 5C-patch |
| **2D** | Parent-child link management + invitation schema fix | ~1-1.5 days | 4D-patch, 5C-patch |
| **4D-patch** | Parent-child link UI — web patch | ~0.5-1 day | — |
| **5C-patch** | "My Children" screen — mobile patch | ~0.5 day | — |

**Already completed:** 1B, 2C, 4D, 5C
**Remaining effort:** ~2-3 days
**Run order for remaining:** `2D → 4D-patch → 5C-patch`

> **V2+ deferred:** Parent-initiated link requests (parent requests to link → admin approves). For V1, only admins can create links.

---
---

# NEW PHASES — Content Library, Quiz Engine & CMS (Not Yet Started)

> These phases were added after analyzing the gap between report specs and code for:
> content management across schools, PDF exercise workflows, dynamic interactive exercises, and media library.
>
> **All previous phases (0→8, 0A→8A, 1B→5C) must be completed first.**
>
> **Run these 6 new phases in order:** `9A → 9B → 9C → 10A → 10B → 10C`
> - 9A, 9B, 9C are backend (new role + content library + quiz engine + PDF exercises)
> - 10A is the CMS web dashboard for the new CONTENT_MGR role
> - 10B extends the existing web app (teacher library + student quiz player)
> - 10C extends the existing mobile app (same features on mobile)

---

## Phase 9A — CONTENT_MGR Role + Content Library Backend *(~2-3 days)*
**Subfolder:** `backend/` (core/permissions, models/lms, alembic, schemas, api/v1)
**Goal:** Create a new platform-wide CONTENT_MGR role that can upload educational content (videos, PDFs, audios) visible to all schools. Add a content assignment mechanism so teachers can pick from the library and share with their class. Add a teacher content promotion system where teachers submit their content for review, and CONTENT_MGR can approve it to become part of the platform library.

### What to do:
1. Add `CONTENT_MGR` role to `core/permissions.py`:
   - NOT school-scoped — this role operates at platform level (like SYS)
   - New permissions: `PERM_CONTENT_CREATE`, `PERM_CONTENT_PUBLISH`, `PERM_CONTENT_MANAGE`, `PERM_CONTENT_DELETE`, `PERM_CONTENT_ANALYTICS`, `PERM_CONTENT_REVIEW`
   - Update the role→permission matrix
2. Add `subject` field (String(50), nullable) to `ContentItem` model (math, french, science, arabic, history, geography, etc.)
3. Add `created_by` field (FK to users, nullable) to `ContentItem` — tracks who uploaded
4. Add `description` field (Text, nullable) to `ContentItem` — rich description
5. Add `thumbnail_path` field (String(500), nullable) to `ContentItem` — preview image
6. Add `origin` field (String(20), default "PLATFORM") to `ContentItem` — values: PLATFORM (uploaded by CONTENT_MGR), PROMOTED (originally teacher content, promoted to library)
7. Add `original_content_id` field (FK to content_items, nullable) to `ContentItem` — when origin=PROMOTED, points to the original teacher's content item
8. Create `class_content_assignments` table via Alembic migration:
   - `id` (UUID PK), `teacher_id` (FK to users), `class_id` (FK to classes), `content_item_id` (FK to content_items), `school_id` (FK), `assigned_at` (datetime), `notes` (text, optional teacher note)
   - Unique constraint: (class_id, content_item_id) — no duplicate assignments
9. Create `content_submissions` table via Alembic migration (teacher → platform promotion system):
   - `id` (UUID PK), `content_item_id` (FK to content_items — the original school-scoped content), `submitted_by` (FK to users — the teacher), `school_id` (FK), `status` (PENDING/UNDER_REVIEW/APPROVED/REJECTED), `submitted_at` (datetime), `reviewed_by` (FK to users nullable — the CONTENT_MGR who reviewed), `reviewed_at` (datetime nullable), `review_notes` (Text nullable — feedback from CONTENT_MGR), `promoted_content_id` (FK to content_items nullable — the platform copy after approval)
10. Add `reward_points` field (Integer, default 0) to `teacher_profiles` table (from Phase 1B) — teachers earn points when their content is promoted
11. Create SQLAlchemy models: `ClassContentAssignment`, `ContentSubmission` in `models/lms.py`
12. Create Pydantic schemas for content library + submission operations
13. Create/extend endpoints:
    - `POST /cms/content` — CONTENT_MGR creates platform-wide content (school_id=NULL) with metadata + file upload
    - `GET /cms/content` — CONTENT_MGR lists all platform content (filter by type/level/subject/status)
    - `PUT /cms/content/{id}` — CONTENT_MGR updates metadata
    - `DELETE /cms/content/{id}` — CONTENT_MGR soft-deletes (archive)
    - `GET /cms/submissions` — CONTENT_MGR sees review queue (all teacher submissions, filter by status)
    - `POST /cms/submissions/{id}/review` — CONTENT_MGR approves or rejects a submission (with notes)
    - When approved: system creates a copy of the content as platform-wide (school_id=NULL, origin=PROMOTED, original_content_id=source), awards points to teacher, sends notification
    - When rejected: sends notification with feedback to teacher
    - `GET /content/library` — Teachers browse content: platform-wide (school_id=NULL) + their school's content, filter by content_type, level_band, subject, language
    - `POST /content/assign` — Teacher assigns content to their class (creates ClassContentAssignment)
    - `DELETE /content/assign/{id}` — Teacher unassigns content from class
    - `POST /content/submit-for-review` — Teacher submits their school-scoped content for platform promotion (creates ContentSubmission with status=PENDING)
    - `GET /content/my-submissions` — Teacher sees status of their submitted content
    - `GET /classes/{id}/content` — Students see content assigned to their class
14. Add audit trail for all CMS + submission operations
15. Seed data: sample platform-wide content items (2 videos, 2 PDFs, 2 audios) + 1 sample teacher submission

### Cascade to later phases:
- **Phase 9B** quiz engine will also use CONTENT_MGR for platform-wide quizzes
- **Phase 10A** will build the CMS web dashboard + review queue UI
- **Phase 10B** will build the teacher library UI + "Submit to library" button + student content pages
- **Phase 10C** will build mobile equivalents

### Done when:
- [ ] CONTENT_MGR role exists with correct permissions (including PERM_CONTENT_REVIEW)
- [ ] ContentItem has subject, created_by, description, thumbnail_path, origin, original_content_id fields
- [ ] class_content_assignments table exists
- [ ] content_submissions table exists with full status workflow
- [ ] reward_points field added to teacher_profiles
- [ ] CMS endpoints work (create, list, update, archive platform content)
- [ ] Review queue: CONTENT_MGR can list/approve/reject teacher submissions
- [ ] Approved content creates platform copy + awards points + sends notification
- [ ] Rejected content sends notification with feedback
- [ ] Teacher can submit content for review and track submission status
- [ ] Teacher can browse content library and assign to class
- [ ] Students can see content assigned to their class
- [ ] Audit trail on all operations
- [ ] Seed data includes sample platform content + teacher submission

---

## Phase 9B — Quiz Engine Backend *(~2-3 days)*
**Subfolder:** `backend/` (models/lms, alembic, schemas, api/v1, services)
**Goal:** Full quiz/exercise engine with 5 question types (MCQ, True/False, Fill-in, Drag&Drop, Matching), auto-grading, and attempt tracking.

### What to do:
1. Create `quizzes` table via Alembic migration:
   - `id` (UUID PK), `school_id` (FK nullable — NULL=platform-wide by CONTENT_MGR, non-NULL=school-scoped by teacher), `created_by` (FK to users), `title` (String 300), `description` (Text nullable), `subject` (String 50 nullable), `level_band` (String 50 nullable), `difficulty` (String 20 nullable: EASY/MEDIUM/HARD), `time_limit_minutes` (Integer nullable — 0=no limit), `max_attempts` (Integer default 1), `shuffle_questions` (Boolean default false), `status` (DRAFT/PUBLISHED/ARCHIVED), timestamps
2. Create `quiz_questions` table:
   - `id` (UUID PK), `quiz_id` (FK to quizzes), `question_type` (enum: MCQ, TRUE_FALSE, FILL_IN, DRAG_DROP, MATCHING), `question_text` (Text), `question_media_path` (String 500 nullable — image/audio for the question), `options` (JSONB — structure depends on type), `correct_answer` (JSONB — structure depends on type), `points` (Integer default 1), `order` (Integer), `explanation` (Text nullable — shown after answering)
   - MCQ options format: `[{"id": "a", "text": "Option A"}, ...]`, correct_answer: `["a"]` (supports multi-select)
   - TRUE_FALSE: options auto-generated, correct_answer: `true` or `false`
   - FILL_IN: correct_answer: `["answer1", "answer2"]` (accepted alternatives)
   - DRAG_DROP: options: `{"items": [...], "zones": [...]}`, correct_answer: `{"item_id": "zone_id", ...}`
   - MATCHING: options: `{"left": [...], "right": [...]}`, correct_answer: `{"left_id": "right_id", ...}`
3. Create `quiz_attempts` table:
   - `id` (UUID PK), `quiz_id` (FK), `student_id` (FK to users), `attempt_no` (Integer), `started_at` (datetime), `completed_at` (datetime nullable), `score` (Numeric nullable), `max_score` (Integer), `status` (STARTED/COMPLETED/TIMED_OUT), timestamps
   - Unique constraint: (quiz_id, student_id, attempt_no)
4. Create `quiz_responses` table:
   - `id` (UUID PK), `attempt_id` (FK to quiz_attempts), `question_id` (FK to quiz_questions), `student_answer` (JSONB), `is_correct` (Boolean nullable), `points_earned` (Numeric nullable), `answered_at` (datetime)
5. Create SQLAlchemy models in `models/lms.py`: `Quiz`, `QuizQuestion`, `QuizAttempt`, `QuizResponse`
6. Create auto-grading service `services/quiz_grading.py`:
   - MCQ: exact match of selected options → auto-grade
   - TRUE_FALSE: exact match → auto-grade
   - FILL_IN: case-insensitive match against accepted answers → auto-grade
   - DRAG_DROP: exact zone mapping match → auto-grade
   - MATCHING: exact pair match → auto-grade
   - Calculate total score, update attempt status
7. Create endpoints:
   - `POST /quizzes` — CONTENT_MGR (platform) or TCH (school-scoped) creates quiz
   - `GET /quizzes` — list quizzes (filter by school/level/subject/status)
   - `GET /quizzes/{id}` — quiz details with questions (hide answers for students)
   - `PUT /quizzes/{id}` — update quiz (only if DRAFT)
   - `POST /quizzes/{id}/publish` — publish quiz
   - `POST /quizzes/{id}/start` — student starts attempt (checks max_attempts)
   - `POST /attempts/{id}/respond` — student submits answer for one question
   - `POST /attempts/{id}/submit` — student finishes attempt → triggers auto-grading
   - `GET /attempts/{id}/results` — student sees graded results with explanations
   - `GET /quizzes/{id}/analytics` — teacher/CONTENT_MGR sees class performance stats
8. Add `quiz_id` field (FK nullable) to `Assignment` model — when assignment is linked to a quiz, the quiz IS the exercise
9. Add `exercise_type` field to `Assignment` model: STANDARD (current behavior), PRINTABLE_PDF (Phase 9C), QUIZ (linked to quiz_id)
10. Audit trail on all quiz operations
11. Seed data: 2 sample quizzes (1 platform-wide, 1 school-scoped) with mixed question types

### Cascade to later phases:
- **Phase 9C** will add the PRINTABLE_PDF exercise type
- **Phase 10A** CMS dashboard will include quiz builder for CONTENT_MGR
- **Phase 10B** will build teacher quiz builder + student quiz player on web
- **Phase 10C** will build mobile quiz player

### Done when:
- [ ] All 4 quiz tables exist with correct constraints
- [ ] All 5 question types supported with correct JSON schema
- [ ] Auto-grading works for all 5 types
- [ ] Quiz CRUD endpoints work (create, list, update, publish)
- [ ] Student can start attempt, answer questions, submit → auto-graded
- [ ] Assignment model supports exercise_type + quiz_id link
- [ ] Analytics endpoint returns class performance stats
- [ ] Seed data includes sample quizzes

---

## Phase 9C — PDF Exercise Workflow Backend *(~1 day)*
**Subfolder:** `backend/` (models/lms, alembic, schemas, api/v1)
**Goal:** Support printable PDF exercises: teacher uploads exercise PDF → student downloads/prints → solves on paper → uploads photo/scan back → teacher grades.

### What to do:
1. Add `exercise_pdf_path` field (String 500, nullable) to `Assignment` model — stores the downloadable exercise PDF
2. Alembic migration for new field
3. Update `POST /assignments` — when `exercise_type = PRINTABLE_PDF`, require exercise_pdf upload
4. Create endpoint: `GET /assignments/{id}/exercise-pdf` — download the printable exercise PDF (available to students in the class)
5. Update submission validation: when `exercise_type = PRINTABLE_PDF`, at least one file upload is required (the scanned/photographed solution)
6. Add `file_type_hint` field to `SubmissionFile`: SOLUTION_SCAN, SOLUTION_PHOTO, DOCUMENT (helps frontend display correctly)
7. Update `GET /submissions/{id}` for teachers: include inline preview URLs for uploaded images/PDFs
8. Add audit trail for PDF exercise operations

### Cascade to later phases:
- **Phase 10B** will add PDF download + upload UI on web
- **Phase 10C** will add camera capture + upload on mobile

### Done when:
- [ ] Assignment supports `exercise_type = PRINTABLE_PDF` with attached PDF
- [ ] Students can download exercise PDF
- [ ] Students must upload solution file(s) for PDF exercises
- [ ] Teacher can preview uploaded solutions inline
- [ ] Audit trail on operations

---

## Phase 10A — CMS Dashboard (Web) *(~3-4 days)*
**Subfolder:** `web/` (features/cms/)
**Goal:** Separate CMS web dashboard at `/cms` route for CONTENT_MGR to manage platform-wide content, quizzes, and review teacher content submissions.

### What to do (cascading from 9A + 9B):
1. **CMS layout and routing:**
   - New route group: `/cms/*` with its own layout (sidebar: Content, Quizzes, Review Queue, Analytics, Settings)
   - CONTENT_MGR role check on all CMS routes (redirect to 403 if not CONTENT_MGR)
   - Login uses the same auth system but routes to `/cms` for CONTENT_MGR users
2. **Content management pages:**
   - `features/cms/ContentListPage.tsx` — list all platform content with filters (type, level, subject, language, status, origin: PLATFORM/PROMOTED), search, pagination
   - `features/cms/ContentUploadPage.tsx` — upload form: title, description, content_type (VIDEO/PDF/AUDIO/INTERACTIVE), level_band (dropdown), subject (dropdown), language, thumbnail upload, main file upload with progress bar
   - `features/cms/ContentEditPage.tsx` — edit metadata, replace files, change status (publish/archive)
   - Video upload: show file size warning for large files, accept mp4/webm
   - Audio upload: accept mp3/wav/ogg
   - PDF upload: accept pdf
3. **Review Queue (teacher content promotion):**
   - `features/cms/ReviewQueuePage.tsx` — list all teacher submissions (filter by status: PENDING/UNDER_REVIEW/APPROVED/REJECTED, by subject, by level, by school)
   - Each submission card shows: content preview (thumbnail, title, description), teacher name, school name, submission date
   - Click to open detail view: full content preview (play video, view PDF, listen audio), teacher info, school context
   - Action buttons: "Approve" (creates platform copy, awards points, notifies teacher), "Reject" (with required feedback text field, notifies teacher), "Mark Under Review" (intermediate status)
   - Badge/counter on sidebar showing number of PENDING submissions
4. **Quiz builder:**
   - `features/cms/QuizBuilderPage.tsx` — create/edit quizzes
   - Question editor: add questions with type selector (MCQ, True/False, Fill-in, Drag&Drop, Matching)
   - MCQ editor: add/remove options, mark correct answer(s), add explanation
   - Drag&Drop editor: define items and drop zones, set correct mapping
   - Matching editor: define left/right columns, set correct pairs
   - Preview mode: see quiz as student would see it
   - Reorder questions via drag handle
5. **Analytics page:**
   - `features/cms/AnalyticsPage.tsx` — which schools/classes use platform content, most popular content, quiz performance stats
   - Teacher contribution stats: top contributing teachers, approval rates
6. **Bulk upload:**
   - Upload multiple content items at once (ZIP or folder)
7. i18n (fr/ar/en)

### Done when:
- [ ] CMS dashboard accessible at `/cms` for CONTENT_MGR only
- [ ] Content CRUD works (list, upload, edit, archive)
- [ ] Review Queue shows teacher submissions with approve/reject workflow
- [ ] Approved content creates platform copy + awards points + sends notification
- [ ] Rejected content sends feedback notification to teacher
- [ ] Pending submissions badge on sidebar
- [ ] Quiz builder creates quizzes with all 5 question types
- [ ] Analytics page shows usage stats + teacher contribution stats
- [ ] All text translated (fr/ar/en)

---

## Phase 10B — Teacher Content Library + Quiz Player (Web) *(~2-3 days)*
**Subfolder:** `web/` (features/teacher/, features/student/, features/parent/)
**Goal:** Extend existing web app: teachers browse/assign content and create quizzes, students view content and take quizzes, parents see results.

### What to do (cascading from 9A + 9B + 9C, extends existing 4C code):
1. **Teacher: Content Library page:**
   - `features/teacher/ContentLibraryPage.tsx` — browse platform content (school_id=NULL) + own school content
   - Filter by: content_type, level_band, subject, language
   - "Assign to class" button → select class → confirm
   - "My Assignments" tab showing content assigned to each class
   - Teacher can also upload school-scoped content (same form as CMS but school-scoped)
   - "Submit to Platform Library" button on teacher's own content → submits for CONTENT_MGR review
   - "My Submissions" tab showing status of submitted content (PENDING/UNDER_REVIEW/APPROVED/REJECTED) with feedback from CONTENT_MGR
   - Show reward points balance in teacher profile
2. **Teacher: Quiz Builder (class-scoped):**
   - `features/teacher/QuizBuilderPage.tsx` — create class-specific quizzes (same UI as CMS but scoped to teacher's school)
   - Can also assign platform quizzes to class
3. **Student: My Content page:**
   - `features/student/ContentPage.tsx` — list content assigned to student's class, grouped by subject
   - Video player (HTML5 `<video>`), PDF viewer (embed/iframe), audio player
   - Track progress (mark as started/completed)
4. **Student: Quiz Player:**
   - `features/student/QuizPlayerPage.tsx` — take a quiz
   - Renders all 5 question types with appropriate UI (radio buttons for MCQ, toggle for T/F, text input for Fill-in, drag-drop zones, matching lines)
   - Timer display (if time-limited), progress bar, navigation between questions
   - Submit → see results with correct answers + explanations
5. **Student: PDF Exercise flow:**
   - In assignment view: "Download Exercise" button for PRINTABLE_PDF assignments
   - "Upload Solution" button → file picker (accept images + PDF)
6. **Parent: Results page extension:**
   - Extend existing parent dashboard to show quiz results alongside assignment grades
7. i18n (fr/ar/en)

### Done when:
- [ ] Teacher can browse content library and assign to class
- [ ] Teacher can create class-scoped quizzes
- [ ] Student sees assigned content (video/PDF/audio player)
- [ ] Student can take quizzes with all 5 question types
- [ ] PDF exercise download + solution upload works
- [ ] Parent sees quiz results
- [ ] All text translated (fr/ar/en)

---

## Phase 10C — Content Library + Quiz Player (Mobile) *(~2 days)*
**Subfolder:** `mobile/` (features/teacher/, features/student/, features/parent/)
**Goal:** Extend existing mobile app: mirrors web features for content library, quiz player, and PDF exercises.

### What to do (cascading from 9A + 9B + 9C, extends existing 5B code):
1. **Teacher: Content Library screen:**
   - `features/teacher/content_library_screen.dart` — browse + assign content to class
   - Filter chips (type, level, subject)
   - Upload school-scoped content from phone (camera/gallery for images, file picker for PDFs)
2. **Student: Content screen:**
   - `features/student/content_screen.dart` — list assigned content by subject
   - In-app video player, PDF viewer, audio player
   - Track progress
3. **Student: Quiz Player:**
   - `features/student/quiz_player_screen.dart` — swipe-through questions, tap/drag answers
   - MCQ: tap option cards, True/False: toggle switch, Fill-in: text field, Drag&Drop: long-press + drag, Matching: tap pairs
   - Timer, progress dots, submit button
   - Results screen with score + explanations
4. **Student: PDF Exercise flow:**
   - Download exercise PDF (open in external PDF viewer or in-app)
   - "Upload Solution" — camera capture (take photo of solved exercise) or pick from gallery
   - Preview before upload
5. **Parent: Quiz results in child dashboard**
6. **Offline support:**
   - Cache quiz questions for offline attempt, sync answers when online
   - Download content for offline viewing (optional, mark as downloadable)
7. i18n (fr/ar/en)

### Done when:
- [ ] Teacher can browse + assign content on mobile
- [ ] Student sees content (video/PDF/audio) on mobile
- [ ] Quiz player works with all 5 question types on mobile
- [ ] Camera capture + upload for PDF exercise solutions
- [ ] Offline quiz support works
- [ ] Parent sees quiz results
- [ ] All text translated (fr/ar/en)

---

## Content & Quiz Phases Summary

| Sub-Phase | Focus | Effort | Cascades To |
|-----------|-------|--------|-------------|
| **9A** | CONTENT_MGR role + content library backend | ~2 days | 9B, 10A, 10B, 10C |
| **9B** | Quiz engine backend (5 question types, auto-grading) | ~2-3 days | 10A, 10B, 10C |
| **9C** | PDF exercise workflow backend | ~1 day | 10B, 10C |
| **10A** | CMS dashboard for CONTENT_MGR (web) | ~2-3 days | — |
| **10B** | Teacher content library + student quiz player (web) | ~2-3 days | — |
| **10C** | Content library + quiz player (mobile) | ~2 days | — |

**Total estimated effort (9A-10C):** ~11-14 days
**Run order:** `9A → 9B → 9C → 10A → 10B → 10C`

---
---

# NEW PHASES — Missing V1 Features: Timetable, Billing, Messaging, Progress, Toggles (Not Yet Started)

> These phases cover V1 (P0/P1) features found in the reports that were not previously planned.
>
> **All previous phases (0→8, 0A→8A, 1B→5C, 9A→10C) must be completed first.**
>
> **Run these 8 new phases in order:** `11A → 11B → 11C → 11D → 11E → 12A → 12B → 12C`
> - 11A-11E are backend (timetable, billing, messaging, progress, feature toggles)
> - 12A-12C extend the existing web and mobile apps

---

## Phase 11A — Timetable / Schedule Management Backend *(~2-3 days)*
**Subfolder:** `backend/` (models/erp, alembic, schemas, api/v1)
**Goal:** Class timetable management — define weekly schedules with time slots, subjects, teachers, and rooms. Support viewing schedules by class, teacher, or student.

### What to do:
1. Create `timetable_slots` table via Alembic migration:
   - `id` (UUID PK), `school_id` (FK), `class_id` (FK to classes), `academic_year_id` (FK), `day_of_week` (Integer 0-6, Monday=0), `start_time` (Time), `end_time` (Time), `subject` (String 50), `teacher_id` (FK to users, nullable), `room` (String 50, nullable), `is_recurring` (Boolean default true), `effective_from` (Date), `effective_until` (Date nullable)
   - Unique constraint: (class_id, day_of_week, start_time, academic_year_id) — no overlapping slots
   - Check constraint: end_time > start_time
2. Create `timetable_exceptions` table (for holidays, canceled classes, substitutions):
   - `id` (UUID PK), `timetable_slot_id` (FK), `exception_date` (Date), `exception_type` (CANCELED/SUBSTITUTED/ROOM_CHANGED), `substitute_teacher_id` (FK nullable), `new_room` (String 50 nullable), `reason` (Text nullable), `created_by` (FK to users)
3. Create SQLAlchemy models: `TimetableSlot`, `TimetableException` in `models/erp.py`
4. Create Pydantic schemas for timetable operations
5. Create endpoints:
   - `POST /timetable/slots` — ADM creates timetable slot for a class (bulk create supported)
   - `GET /timetable/slots` — list slots (filter by class_id, teacher_id, day_of_week, date range)
   - `PUT /timetable/slots/{id}` — ADM updates a slot
   - `DELETE /timetable/slots/{id}` — ADM removes a slot
   - `GET /timetable/class/{class_id}/weekly` — full weekly view for a class (Mon-Fri/Sat grid)
   - `GET /timetable/teacher/{teacher_id}/weekly` — teacher's weekly schedule across classes
   - `GET /timetable/me/weekly` — current user's schedule (student sees their class, teacher sees their classes)
   - `POST /timetable/exceptions` — ADM creates exception (cancellation, substitution)
   - `GET /timetable/exceptions` — list exceptions for a date range
6. Validation: no overlapping slots for same class, no double-booking teacher at same time
7. Audit trail on all timetable operations
8. Seed data: sample weekly timetable for test classes

### Cascade to later phases:
- **Phase 12A** will build timetable view on web
- **Phase 12B** will build timetable view on mobile

### Done when:
- [ ] timetable_slots and timetable_exceptions tables exist
- [ ] Weekly schedule CRUD works (create, read, update, delete)
- [ ] No overlapping slots validation
- [ ] Class/teacher/student weekly view endpoints work
- [ ] Exception handling (cancel, substitute) works
- [ ] Audit trail on all operations

---

## Phase 11B — Billing Enhancements Backend *(~2 days)*
**Subfolder:** `backend/` (models/billing, alembic, schemas, api/v1, services)
**Goal:** Add fee structures per school, payment retry logic, and overdue invoice handling with automatic reminders.

### What to do:
1. Create `fee_structures` table via Alembic migration:
   - `id` (UUID PK), `school_id` (FK), `academic_year_id` (FK), `name` (String 200, e.g. "Frais de scolarité 1ère année"), `amount` (Numeric), `currency` (String 3, default "MAD"), `frequency` (MONTHLY/TRIMESTRIAL/ANNUAL/ONE_TIME), `due_day` (Integer 1-28, day of month), `applies_to_level` (String 50 nullable — filter by class level), `status` (ACTIVE/ARCHIVED), timestamps
2. Create `fee_assignments` table:
   - `id` (UUID PK), `fee_structure_id` (FK), `student_id` (FK to users), `school_id` (FK), `discount_percent` (Numeric nullable), `discount_reason` (Text nullable), `status` (ACTIVE/EXEMPTED/ARCHIVED)
   - Unique: (fee_structure_id, student_id)
3. Add `retry_count` (Integer default 0), `next_retry_at` (DateTime nullable), `last_retry_error` (Text nullable) to `PaymentAttempt` model
4. Add `reminder_sent_at` (DateTime nullable), `reminder_count` (Integer default 0) to `Invoice` model
5. Create payment retry service `services/payment_retry.py`:
   - Retry failed payments up to 3 times with exponential backoff (1h, 6h, 24h)
   - ARQ background task: `retry_failed_payments` runs every hour
   - On final failure: mark invoice as OVERDUE, notify parent
6. Create overdue reminder service:
   - ARQ background task: `send_overdue_reminders` runs daily at 09:00
   - Sends email reminder to parent for invoices overdue > 7 days (respects consent preferences)
   - Increments reminder_count, max 3 reminders
7. Create endpoints:
   - `POST /billing/fee-structures` — ADM creates fee structure
   - `GET /billing/fee-structures` — list fee structures (filter by school, year, level)
   - `PUT /billing/fee-structures/{id}` — ADM updates
   - `POST /billing/fee-assignments` — ADM assigns fee to student (with optional discount)
   - `POST /billing/fee-assignments/bulk` — ADM bulk-assigns fee to all students in a class/level
   - `GET /billing/fee-assignments` — list assignments (filter by student, fee, status)
   - `POST /billing/generate-invoices` — ADM generates invoices from fee structures for a period
8. Audit trail on all billing operations
9. Seed data: sample fee structures + assignments

### Cascade to later phases:
- **Phase 12A** will add billing management UI on web
- **Phase 12B** will update mobile invoice screen

### Done when:
- [ ] Fee structures and assignments tables exist
- [ ] Fee CRUD + bulk assignment works
- [ ] Invoice generation from fee structures works
- [ ] Payment retry logic runs via ARQ (3 retries, exponential backoff)
- [ ] Overdue reminders sent automatically (respects consent)
- [ ] Audit trail on all operations

---

## Phase 11C — Messaging & Communication Backend *(~2-3 days)*
**Subfolder:** `backend/` (models/com, alembic, schemas, api/v1, services)
**Goal:** Parent-teacher direct messaging with read receipts, SMS notification fallback, and admin announcement broadcast system.

### What to do:
1. Create `conversations` table:
   - `id` (UUID PK), `school_id` (FK), `type` (DIRECT/GROUP), `created_by` (FK to users), `subject` (String 300 nullable), timestamps
2. Create `conversation_participants` table:
   - `id` (UUID PK), `conversation_id` (FK), `user_id` (FK to users), `role_in_conversation` (INITIATOR/PARTICIPANT), `joined_at` (DateTime), `muted` (Boolean default false)
   - Unique: (conversation_id, user_id)
3. Create `messages` table:
   - `id` (UUID PK), `conversation_id` (FK), `sender_id` (FK to users), `body` (Text), `sent_at` (DateTime), `edited_at` (DateTime nullable)
   - Index on (conversation_id, sent_at DESC)
4. Create `message_read_receipts` table:
   - `id` (UUID PK), `message_id` (FK), `user_id` (FK to users), `read_at` (DateTime)
   - Unique: (message_id, user_id)
5. Create `announcements` table:
   - `id` (UUID PK), `school_id` (FK), `author_id` (FK to users), `title` (String 300), `body` (Text), `target_roles` (JSONB array — e.g. ["PAR", "STD"]), `target_class_ids` (JSONB array nullable — specific classes, NULL=all), `published_at` (DateTime nullable), `status` (DRAFT/PUBLISHED/ARCHIVED), timestamps
6. Create SQLAlchemy models in `models/com.py`
7. SMS integration service `services/sms.py`:
   - Abstract SMSProvider protocol (like StorageBackend)
   - Stub implementation for dev (logs to console)
   - When email delivery fails AND user has SMS consent → send SMS fallback
   - Rate limit: max 5 SMS/day per user
8. Create endpoints:
   - `POST /messages/conversations` — start conversation (PAR↔TCH within same school, validated by parent-child + teacher-class links)
   - `GET /messages/conversations` — list user's conversations
   - `GET /messages/conversations/{id}/messages` — list messages (cursor pagination)
   - `POST /messages/conversations/{id}/messages` — send message
   - `POST /messages/{id}/read` — mark as read (creates receipt)
   - `GET /messages/conversations/{id}/read-status` — read receipts for conversation
   - `POST /announcements` — ADM/DIR creates announcement
   - `GET /announcements` — list announcements (filter by role, class)
   - `POST /announcements/{id}/publish` — publish announcement (sends notifications)
9. WebSocket integration: push new messages and announcements in real-time
10. Audit trail on all messaging operations
11. ABAC: parents can only message teachers of their children's classes, teachers can only message parents of their students

### Cascade to later phases:
- **Phase 12A** will build messaging + announcements UI on web
- **Phase 12B** will build messaging + announcements on mobile

### Done when:
- [ ] Conversations, messages, read receipts tables exist
- [ ] Announcements table exists
- [ ] Parent-teacher messaging works with ABAC validation
- [ ] Read receipts tracked
- [ ] SMS fallback service implemented (stub provider)
- [ ] Announcements CRUD + publish + notification
- [ ] Real-time push via WebSocket
- [ ] Audit trail on all operations

---

## Phase 11D — Student Progress Visualization Backend *(~1-2 days)*
**Subfolder:** `backend/` (api/v1, services)
**Goal:** API endpoints that aggregate student progress data for visualization — grade trends, content completion rates, activity scores over time, attendance rates.

### What to do:
1. Create `services/progress.py` — aggregation service:
   - `get_student_grade_trend(student_id, period)` — average grades per month/week
   - `get_student_content_progress(student_id)` — content items completed vs total assigned
   - `get_student_activity_scores(student_id)` — activity session scores over time
   - `get_student_attendance_rate(student_id, period)` — present/absent/justified percentages
   - `get_class_progress_summary(class_id)` — class-wide averages for teacher view
   - `get_child_progress(parent_id)` — parent view of all linked children's progress
2. Create endpoints:
   - `GET /progress/student/{id}` — full student dashboard data (STD sees own, PAR sees child, TCH sees class student, ADM sees any)
   - `GET /progress/class/{id}` — class summary (TCH, ADM)
   - `GET /progress/me` — current user's progress (STD shortcut)
   - `GET /progress/children` — parent's children progress overview (PAR)
3. Response format: structured for chart rendering (labels array + datasets array, compatible with recharts/Chart.js)
4. Caching: Redis cache with 15-minute TTL on aggregated data
5. ABAC: enforce school boundary, parent-child, teacher-class guards

### Cascade to later phases:
- **Phase 12C** will build progress visualization charts on web + mobile

### Done when:
- [ ] Progress aggregation service works (grades, content, activities, attendance)
- [ ] Student/class/parent progress endpoints return chart-ready data
- [ ] Redis caching with 15-min TTL
- [ ] ABAC enforced on all endpoints

---

## Phase 11E — Feature Toggles *(~1 day)*
**Subfolder:** `backend/` (core, models, api/v1)
**Goal:** Simple feature toggle system — enable/disable features per school or globally. Used for gradual rollout and A/B testing.

### What to do:
1. Create `feature_toggles` table:
   - `id` (UUID PK), `feature_key` (String 100, unique), `description` (Text nullable), `enabled_globally` (Boolean default false), `enabled_school_ids` (JSONB array, default []), `enabled_role_codes` (JSONB array, default []), `created_by` (FK nullable), timestamps
2. Create SQLAlchemy model `FeatureToggle` in `models/audit.py` (or new `models/system.py`)
3. Create `core/feature_flags.py`:
   - `is_feature_enabled(feature_key, school_id=None, role_code=None)` — checks global + school + role
   - Redis cache for toggle values (1-minute TTL)
   - Dependency injection: `RequiresFeature(feature_key)` guard for endpoints
4. Create endpoints:
   - `POST /admin/feature-toggles` — SYS/CONTENT_MGR creates toggle
   - `GET /admin/feature-toggles` — list all toggles
   - `PUT /admin/feature-toggles/{id}` — update toggle (enable/disable per school/role)
   - `GET /features/active` — current user's active features (for frontend to conditionally render)
5. Pre-create toggles for new features: `content_library`, `quiz_engine`, `pdf_exercises`, `messaging`, `announcements`, `timetable`
6. Audit trail on toggle changes

### Done when:
- [ ] feature_toggles table exists
- [ ] Toggle check works (global + school + role)
- [ ] Redis-cached lookups
- [ ] RequiresFeature guard dependency
- [ ] CRUD endpoints for toggle management
- [ ] Frontend endpoint returns active features for current user

---

## Phase 12A — Timetable + Billing + Messaging UI (Web) *(~3-4 days)*
**Subfolder:** `web/` (features/timetable, features/billing, features/messages, features/announcements)
**Goal:** Extend existing web app with timetable view, billing management, parent-teacher messaging, and announcements.

### What to do (cascading from 11A + 11B + 11C, extends existing web code):
1. **Timetable pages:**
   - `features/timetable/TimetablePage.tsx` — weekly grid view (Mon-Sat, time slots as rows)
   - Color-coded by subject, shows teacher name + room
   - ADM: add/edit/delete slots (inline or modal form)
   - Teacher view: their schedule across all classes
   - Student/parent view: class schedule (read-only)
   - Exception handling: cancel class, add substitution
2. **Billing management (ADM):**
   - `features/billing/FeeStructuresPage.tsx` — CRUD for fee structures
   - `features/billing/FeeAssignmentsPage.tsx` — assign fees to students/classes, apply discounts
   - `features/billing/GenerateInvoicesPage.tsx` — generate invoices from fee structures for a period
   - Extend existing InvoicesPage with overdue indicators + retry status
3. **Messaging:**
   - `features/messages/ConversationsPage.tsx` — list conversations (inbox-style)
   - `features/messages/ChatPage.tsx` — conversation thread with message bubbles, read receipts (blue ticks), real-time via WebSocket
   - "New Message" button → select teacher (for parents) or parent (for teachers) → start conversation
   - Unread count badge on navigation
4. **Announcements:**
   - `features/announcements/AnnouncementsPage.tsx` — list announcements (all users)
   - `features/announcements/AnnouncementFormPage.tsx` — ADM/DIR creates announcement (target roles, classes, publish)
5. i18n (fr/ar/en)

### Done when:
- [ ] Timetable weekly grid works for ADM/teacher/student/parent views
- [ ] Fee structure CRUD + invoice generation works
- [ ] Messaging with real-time chat + read receipts works
- [ ] Announcements CRUD + publish works
- [ ] All text translated (fr/ar/en)

---

## Phase 12B — Timetable + Billing + Messaging (Mobile) *(~2-3 days)*
**Subfolder:** `mobile/` (features/timetable, features/messages, features/announcements)
**Goal:** Extend existing mobile app with timetable, messaging, and announcements.

### What to do (cascading from 11A + 11B + 11C, extends existing mobile code):
1. **Timetable:**
   - `features/timetable/timetable_screen.dart` — weekly grid (swipe between days on phone, full week on tablet)
   - Color-coded slots, tap for details
   - Teacher/student/parent views
2. **Messaging:**
   - `features/messages/conversations_screen.dart` — inbox list with unread badges
   - `features/messages/chat_screen.dart` — chat bubbles, real-time via WebSocket, read receipts
   - Push notification for new messages → deep link to conversation
3. **Announcements:**
   - `features/announcements/announcements_screen.dart` — list with badge for unread
   - Push notification for new announcements
4. **Billing updates:**
   - Update InvoicesScreen with overdue indicators
   - Payment retry status display
5. Offline: cache conversations + announcements for offline reading
6. i18n (fr/ar/en)

### Done when:
- [ ] Timetable view works on mobile (day/week view)
- [ ] Chat messaging with real-time + push notifications
- [ ] Announcements list with push notifications
- [ ] Invoice overdue indicators
- [ ] Offline cache for conversations + announcements
- [ ] All text translated (fr/ar/en)

---

## Phase 12C — Student Progress Dashboard (Web + Mobile) *(~2 days)*
**Subfolder:** `web/` + `mobile/`
**Goal:** Visual progress dashboards for students, parents, and teachers using charts (recharts on web, fl_chart on mobile).

### What to do (cascading from 11D):
1. **Web — Student Progress:**
   - `features/progress/ProgressDashboardPage.tsx` — student sees their own progress
   - Grade trend chart (line chart, monthly average)
   - Content completion pie chart (completed vs remaining)
   - Activity scores bar chart (by activity type)
   - Attendance rate donut chart (present/absent/justified)
   - Uses recharts library (already available)
2. **Web — Parent Progress:**
   - Extend parent dashboard: each child has a progress summary card
   - Click to see full progress dashboard for that child
3. **Web — Teacher Class Progress:**
   - `features/teacher/ClassProgressPage.tsx` — class-wide averages + per-student breakdown
   - Sortable table with mini sparklines per student
4. **Mobile — Student Progress:**
   - `features/progress/progress_screen.dart` — same charts using fl_chart package
   - Swipe between grade/content/activity/attendance tabs
5. **Mobile — Parent Progress:**
   - Progress summary cards in child dashboard
6. i18n (fr/ar/en)

### Done when:
- [ ] Student progress dashboard with 4 chart types (web + mobile)
- [ ] Parent can view each child's progress
- [ ] Teacher sees class-wide progress + per-student breakdown
- [ ] Charts render correctly with real data
- [ ] All text translated (fr/ar/en)

---

## Missing V1 Features — Phases Summary

| Sub-Phase | Focus | Effort | Cascades To |
|-----------|-------|--------|-------------|
| **11A** | Timetable / schedule management backend | ~2-3 days | 12A, 12B |
| **11B** | Billing enhancements (fee structures, retry, reminders) | ~2 days | 12A, 12B |
| **11C** | Messaging + SMS fallback + announcements backend | ~2-3 days | 12A, 12B |
| **11D** | Student progress visualization backend | ~1-2 days | 12C |
| **11E** | Feature toggles system | ~1 day | — |
| **12A** | Timetable + billing + messaging UI (web) | ~3-4 days | — |
| **12B** | Timetable + messaging + announcements (mobile) | ~2-3 days | — |
| **12C** | Student progress dashboard (web + mobile) | ~2 days | — |

**Total estimated effort (11A-12C):** ~15-20 days
**Run order:** `11A → 11B → 11C → 11D → 11E → 12A → 12B → 12C`
