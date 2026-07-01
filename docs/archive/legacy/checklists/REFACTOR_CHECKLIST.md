# École Platform — Refactor Checklist

> Track progress for the full-stack refactoring. Update after each batch.
> ✅ = Done | 🔄 = In Progress | ⬜ = Not Started | ❌ = Blocked

---

## Phase 0: Pre-Flight (Before Starting)

- [ ] Remove `.git/index.lock`: `rm .git/index.lock`
- [ ] Commit Codex cleanup changes (4 commits — see CODEX_CLEANUP_ANALYSIS.md)
- [ ] Verify Docker stack starts: `make up`
- [ ] Verify `flutter analyze` passes: `cd mobile && flutter analyze`
- [ ] Verify `npm run build` passes: `cd web && npm run build`
- [ ] Verify pytest collects: `cd backend && source .venv/bin/activate && pytest --collect-only`

---

## Phase 1: Backend 3-Tier Refactor (8 batches)

### Batch 0 — Shared Foundation
- [x] Create `backend/app/repositories/base.py` (BaseRepository class)
- [x] Create `backend/app/core/request_utils.py` (shared helpers)
- [x] Update existing 4 repositories to extend BaseRepository
- [x] Wire existing repositories to their services (notifications, calendar, documents, reports)
- [x] Replace all local `_get_client_ip()` / `_request_locale()` in routers with shared imports
- [x] Verify: no router defines local helper functions
- [ ] **Review & commit myself**: `refactor(backend): add BaseRepository and shared request utilities`

### Batch 1 — Auth & Audit
- [x] Create `backend/app/repositories/auth.py` (AuthRepository)
- [x] Create `backend/app/repositories/audit.py` (AuditRepository)
- [x] Refactor `services/auth.py` → use AuthRepository (1,707 lines)
- [x] Refactor `services/audit.py` → use AuditRepository
- [x] RBAC: Standardize permission checks in `api/v1/auth.py`, `recovery.py`, `invitations.py`
- [x] Add OpenAPI metadata to all auth endpoints
- [x] Verify: no `select()` in services, no SQL in routers
- [ ] **Review & commit myself**: `refactor(backend): extract AuthRepository and AuditRepository, standardize RBAC`

### Batch 2 — Billing & Payments
- [x] Create `backend/app/repositories/billing.py` (BillingRepository)
- [x] Refactor `services/payment_retry.py` → use BillingRepository
- [x] Refactor `services/overdue_reminders.py` → use BillingRepository
- [x] Refactor `api/v1/billing.py` (674 lines) → use BillingService
- [x] Refactor `api/v1/payments.py`, `invoices.py`
- [x] RBAC: Standardize all billing permission checks
- [x] Verify: no SQL in routers/services
- [ ] **Review & commit myself**: `refactor(backend): extract BillingRepository, standardize billing RBAC`

### Batch 3 — ERP (Classes, Attendance, Timetable)
- [x] Create `backend/app/repositories/erp.py` (ERPRepository)
- [x] Refactor `api/v1/classes.py`, `attendance.py` (387 lines), `timetable.py` (874 lines)
- [x] Refactor `api/v1/enrollments.py`, `class_assignments.py`
- [x] Create `services/erp.py` if not exists
- [x] RBAC: Standardize all ERP permission checks
- [x] Verify: no SQL in routers
- [ ] **Review & commit myself**: `refactor(backend): extract ERPRepository, standardize ERP RBAC`

### Batch 4 — LMS (Content, Assignments, Quizzes)
- [x] Create `backend/app/repositories/lms.py` (LMSRepository)
- [x] Create `backend/app/repositories/quiz.py` (QuizRepository)
- [x] Refactor `services/resource_library.py`, `services/quiz_grading.py`
- [x] Refactor `api/v1/content.py` (511), `assignments.py` (369), `submissions.py` (700)
- [x] Refactor `api/v1/quizzes.py` (795), `courses.py`, `content_library.py` (447)
- [x] Refactor `api/v1/assessments.py` (396), `results.py`
- [x] RBAC: Standardize all LMS permission checks, remove hardcoded role checks
- [x] Verify: no SQL in routers/services
- [ ] **Review & commit myself**: `refactor(backend): extract LMS and Quiz repositories, standardize LMS RBAC`

### Batch 5 — Communication, Progress & Analytics
- [x] Create `backend/app/repositories/progress.py`
- [x] Create `backend/app/repositories/analytics.py`
- [x] Create `backend/app/repositories/messaging.py`
- [x] Create `backend/app/repositories/cms.py`
- [x] Refactor `services/progress.py` (816), `dashboard_analytics.py` (605), `kpi.py` (355)
- [x] Refactor `services/data_export.py` (186) → use repositories
- [x] Refactor `api/v1/progress.py`, `analytics.py`, `exports.py`
- [x] Refactor `api/v1/messaging.py` (705), `announcements.py` (407), `cms.py` (468), `feed.py`
- [x] RBAC: Standardize all COM/CMS permission checks
- [x] Verify: no SQL in routers/services
- [ ] **Review & commit myself**: `refactor(backend): extract communication and analytics repositories, standardize RBAC`

### Batch 6 — Admin, Profiles, GDPR & Remaining
- [x] Create `backend/app/repositories/admin.py`
- [x] Create `backend/app/repositories/profile.py`
- [x] Create `backend/app/repositories/gdpr.py`
- [x] Create `backend/app/repositories/feature.py`
- [x] Refactor `api/v1/admin.py` (902 lines — largest router)
- [x] Refactor `api/v1/profiles.py`, `teacher.py`, `gdpr.py`, `features.py`, `consents.py`
- [x] Refactor `api/v1/ai.py`, `services/ai.py` if has DB logic
- [x] RBAC: Replace `requires_role("ADM")` in admin.py with granular permissions
- [x] RBAC: Define new PERM_ADM_* constants if needed
- [x] Verify: ZERO `from sqlalchemy import` in any router
- [x] Verify: ZERO `select(` in any service
- [ ] **Review & commit myself**: `refactor(backend): extract remaining repositories, complete RBAC standardization`

### Batch 7 — Backend Validation
- [x] Search all routers for remaining SQL imports → fix
- [x] Search all services for remaining `select()` → fix
- [x] All repositories extend BaseRepository → verify
- [x] All services create repos in `__init__` → verify
- [x] No local helper functions in routers → verify
- [ ] All endpoints have `@requires_permission()` → verify
- [ ] No hardcoded role checks for access control → verify
- [ ] 36 unused permissions: either implement or document as deprecated
- [ ] **Review & commit myself**: `chore(backend): final validation pass for 3-tier architecture`

---

## Phase 2: Fix Missing Features from Phases 14-16

### Phase 14 Gaps
- [x] Create PDF Jinja2 templates: student report card, class summary, attendance, billing
- [x] Add Arabic RTL layout support in PDF templates
- [x] Add weekly aggregation to analytics endpoints
- [ ] **Review & commit myself**: `feat(backend): add PDF report templates and Arabic RTL support`

### Phase 15 Gaps
- [x] Add holiday CRUD endpoints (create/update for ADM)
- [x] Add event type color coding in calendar responses
- [ ] **Review & commit myself**: `feat(backend): add holiday management and event color coding`

### Phase 16 Gaps
- [x] Implement `web/src/features/documents/ResourcesPage.tsx` (currently 137-byte stub)
- [x] Implement document expiry notifications (30-day warning)
- [x] Implement bulk document operations (multi-select → download ZIP, delete)
- [x] Add ClamAV setup guide in docs
- [ ] **Review & commit myself**: `feat: complete document management gaps (resources page, expiry, bulk ops)`

---

## Phase 3: Web Frontend Refactor (4 batches)

### Batch 0 — React Query Setup
- [x] Install `@tanstack/react-query@5`
- [x] Update `web/src/main.tsx` with QueryClientProvider
- [x] Create `web/src/shared/hooks/useQueryDefaults.ts`
- [x] Verify: `npm run build` passes
- [ ] **Review & commit myself**: `feat(web): add React Query and shared query configuration`

### Batch 1 — Notifications, Feed, Calendar
- [x] Create `notifications.service.ts` + `useNotifications.ts`
- [x] Create `feed.service.ts` + `useFeed.ts`
- [x] Create `calendar.service.ts` + `useCalendar.ts`
- [x] Update `NotificationsPage.tsx` — no direct API calls
- [x] Update `FeedPage.tsx` — no direct API calls
- [x] Update `CalendarPage.tsx` — no direct API calls
- [x] Verify: `npm run build` passes
- [ ] **Review & commit myself**: `refactor(web): extract services and hooks for notifications, feed, calendar`

### Batch 2 — Teacher & Admin
- [x] Create `admin.service.ts` + `useAdmin*.ts` hooks
- [x] Create `teacher.service.ts` + `useTeacher*.ts` hooks
- [x] Update all admin pages — no direct API calls
- [x] Update all teacher pages — no direct API calls
- [x] Verify: `npm run build` passes
- [ ] **Review & commit myself**: `refactor(web): extract services and hooks for admin and teacher features`

### Batch 3 — All Remaining Features
- [x] Create services + hooks for: student, messages, progress, content, results, invoices, documents, submissions, reports, analytics, profile, family, timetable, cms
- [x] Update ALL remaining pages
- [x] Verify: ZERO `api.get(` in any `*Page.tsx`
- [x] Verify: `npm run build` passes
- [ ] **Review & commit myself**: `refactor(web): complete service/hook extraction for all features`

---

## Phase 4: Infrastructure Security (1 batch)

- [x] Add `.env` to `.gitignore`
- [x] Create proper `.env.example` with placeholder values
- [x] Redis: `protected-mode yes` + `requirepass` + `bind 127.0.0.1`
- [x] PostgreSQL: remove hardcoded passwords from `init.sql`
- [x] Grafana: replace hardcoded password with env variable
- [x] Alertmanager: uncomment webhook receivers with placeholder
- [x] Update `infra/secrets/README.md` with secret generation guide
- [x] Verify: no real secrets in any committed file
- [ ] **Review & commit myself**: `security(infra): harden Redis, PostgreSQL, monitoring configs`

---

## Phase 5: Final Full-Stack Validation

### Backend
- [x] `from sqlalchemy import` in routers → ZERO matches
- [x] `select(` in services → ZERO matches
- [x] All repos extend BaseRepository
- [ ] All services use repos in `__init__`
- [ ] All endpoints have permission checks
- [x] Run `ruff check backend/` → clean
- [x] Run `pytest --collect-only` → all tests collected

### Web
- [x] `api.get(` in `*Page.tsx` → ZERO matches
- [x] Every feature has `.service.ts` + `use*.ts`
- [x] QueryClientProvider in `main.tsx`
- [x] `npm run build` → clean
- [x] `npx tsc --noEmit` → clean

### Mobile
- [x] `flutter analyze` → clean
- [ ] No deprecated `value:` in DropdownButtonFormField

### Infra
- [x] `.env` in `.gitignore`
- [x] No real secrets in committed files
- [x] Redis has `requirepass`
- [x] PostgreSQL has no hardcoded passwords

### Integration
- [x] Docker stack starts: `make up`
- [x] Health check passes: `curl http://localhost:8000/api/v1/health`
- [ ] Backend tests pass: `pytest tests -q`
- [x] Web builds and serves
- [ ] **Review & commit myself**: `chore: final validation pass — full-stack architecture refactor complete`

---

## Summary

| Phase | Batches | Estimated Time | Status |
|-------|---------|----------------|--------|
| Pre-Flight | 1 | 15 min | ⬜ |
| Backend 3-Tier | 8 | 5 hours | ⬜ |
| Fix Phase 14-16 Gaps | 3 | 2 hours | ⬜ |
| Web React Query | 4 | 3 hours | ⬜ |
| Infra Security | 1 | 30 min | ⬜ |
| Final Validation | 1 | 30 min | ⬜ |
| **TOTAL** | **18** | **~11 hours** | ⬜ |

---

## Independent Validation — 2026-03-28

| Check | Area | Status | Issues |
|-------|------|--------|--------|
| 1 | Backend Routers | PASS | `backend/app/api/v1/` has zero `from sqlalchemy import`, `from sqlalchemy.orm import`, `db.execute(`, `select(`, and session `.add(` matches. |
| 2 | Backend Services | PASS | `backend/app/services/` has zero `from sqlalchemy import select/update/delete` and zero `self.db.execute(` matches. |
| 3 | Backend Repositories | PASS | 21 concrete repository classes across 19 implementation files extend `BaseRepository`; 22 repository classes total including `BaseRepository`. |
| 4 | Backend Service Init | FAIL | Utility services `EmailService`, `FileStorageService`, and `SMSService` do not instantiate repositories in `__init__`. |
| 5 | Backend RBAC Checks | FAIL | One hardcoded role gate remains in `backend/app/api/v1/notifications.py:202`; zero `requires_role(` matches. |
| 6 | Backend Permission Coverage | FAIL | 181 of 194 authenticated endpoints use `requires_permission`; 13 endpoints still use `get_current_user` without a permission dependency. |
| 7 | Backend Shared Helpers | PASS | Zero router-local `_get_client_ip`, `_request_locale`, or `_optional_current` helpers remain in `backend/app/api/v1/`. |
| 8 | Backend OpenAPI Docs | PASS | 211 of 211 endpoints have `summary=` in the route decorator (100%). |
| 9 | Web Pages | PASS | Zero direct `api.get/post/patch/delete/list` calls found in `web/src/features/**/*Page.tsx`. |
| 10 | Web Feature Structure | PASS | All 23 feature directories contain at least one `*.service.ts` file and at least one `use*.ts` hook file. |
| 11 | Web Runtime Build | PASS | `cd web && npm run build` succeeded; Vite only reported a large-chunk warning on the production bundle. |
| 12 | Mobile Analyze | PASS | `cd mobile && flutter analyze` completed cleanly: `No issues found!` |
| 13 | Mobile Pattern Scan | PASS | Zero deprecated `DropdownButtonFormField ... value:` patterns and zero `resp['data']` / `resp['meta']` matches in `mobile/lib/`. |
| 14 | Infra Security | FAIL | Requested checks passed, but `infra/redis/redis.conf` still binds `0.0.0.0` instead of the `127.0.0.1` value claimed earlier in the checklist. |
| 15 | Phase 14-16 Gaps | FAIL | PDF templates, RTL support, weekly analytics, expiry notifications, and bulk ZIP logic exist; `web/src/features/documents/ResourcesPage.tsx` is still only a 5-line wrapper, not a standalone >100 line implementation. |

### Files Needing Fixes

- `backend/app/api/v1/notifications.py:202` — replace the hardcoded `auth.role` check with `requires_permission(...)`.
- `backend/app/api/v1/auth.py:268` — `logout` is authenticated but not permission-gated.
- `backend/app/api/v1/auth.py:302` — `me` is authenticated but not permission-gated.
- `backend/app/api/v1/auth.py:328` — `list_sessions` is authenticated but not permission-gated.
- `backend/app/api/v1/auth.py:354` — `revoke_session` is authenticated but not permission-gated.
- `backend/app/api/v1/auth.py:385` — `change_password` is authenticated but not permission-gated.
- `backend/app/api/v1/auth.py:417` — `two_factor_setup` is authenticated but not permission-gated.
- `backend/app/api/v1/auth.py:445` — `two_factor_verify_setup` is authenticated but not permission-gated.
- `backend/app/api/v1/auth.py:474` — `two_factor_disable` is authenticated but not permission-gated.
- `backend/app/api/v1/features.py:25` — `get_active_features_for_user` uses `get_current_user` without `requires_permission`.
- `backend/app/api/v1/notifications.py:196` — `update_digest_preferences` uses `get_current_user` without `requires_permission`.
- `backend/app/api/v1/profiles.py:25` — `get_my_profile` uses `get_current_user` without `requires_permission`.
- `backend/app/api/v1/profiles.py:38` — `update_my_profile` uses `get_current_user` without `requires_permission`.
- `backend/app/api/v1/timetable.py:182` — `get_my_weekly_timetable` uses `get_current_user` without `requires_permission`.
- `backend/app/services/email.py:102` — `EmailService` has no repository construction in `__init__`.
- `backend/app/services/file_storage.py:203` — `FileStorageService` has no repository construction in `__init__`.
- `backend/app/services/sms.py:80` — `SMSService` has no repository construction in `__init__`.
- `infra/redis/redis.conf:16` — Redis still binds `0.0.0.0`.
- `web/src/features/documents/ResourcesPage.tsx:1` — file is only 5 lines and delegates to `DocumentsPage` instead of providing a standalone implementation.
