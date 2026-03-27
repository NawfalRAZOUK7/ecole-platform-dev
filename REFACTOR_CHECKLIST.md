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
- [ ] Create `backend/app/repositories/erp.py` (ERPRepository)
- [ ] Refactor `api/v1/classes.py`, `attendance.py` (387 lines), `timetable.py` (874 lines)
- [ ] Refactor `api/v1/enrollments.py`, `class_assignments.py`
- [ ] Create `services/erp.py` if not exists
- [ ] RBAC: Standardize all ERP permission checks
- [ ] Verify: no SQL in routers
- [ ] **Review & commit myself**: `refactor(backend): extract ERPRepository, standardize ERP RBAC`

### Batch 4 — LMS (Content, Assignments, Quizzes)
- [ ] Create `backend/app/repositories/lms.py` (LMSRepository)
- [ ] Create `backend/app/repositories/quiz.py` (QuizRepository)
- [ ] Refactor `services/resource_library.py`, `services/quiz_grading.py`
- [ ] Refactor `api/v1/content.py` (511), `assignments.py` (369), `submissions.py` (700)
- [ ] Refactor `api/v1/quizzes.py` (795), `courses.py`, `content_library.py` (447)
- [ ] Refactor `api/v1/assessments.py` (396), `results.py`
- [ ] RBAC: Standardize all LMS permission checks, remove hardcoded role checks
- [ ] Verify: no SQL in routers/services
- [ ] **Review & commit myself**: `refactor(backend): extract LMS and Quiz repositories, standardize LMS RBAC`

### Batch 5 — Communication, Progress & Analytics
- [ ] Create `backend/app/repositories/progress.py`
- [ ] Create `backend/app/repositories/analytics.py`
- [ ] Create `backend/app/repositories/messaging.py`
- [ ] Create `backend/app/repositories/cms.py`
- [ ] Refactor `services/progress.py` (816), `dashboard_analytics.py` (605), `kpi.py` (355)
- [ ] Refactor `services/data_export.py` (186) → use repositories
- [ ] Refactor `api/v1/progress.py`, `analytics.py`, `exports.py`
- [ ] Refactor `api/v1/messaging.py` (705), `announcements.py` (407), `cms.py` (468), `feed.py`
- [ ] RBAC: Standardize all COM/CMS permission checks
- [ ] Verify: no SQL in routers/services
- [ ] **Review & commit myself**: `refactor(backend): extract communication and analytics repositories, standardize RBAC`

### Batch 6 — Admin, Profiles, GDPR & Remaining
- [ ] Create `backend/app/repositories/admin.py`
- [ ] Create `backend/app/repositories/profile.py`
- [ ] Create `backend/app/repositories/gdpr.py`
- [ ] Create `backend/app/repositories/feature.py`
- [ ] Refactor `api/v1/admin.py` (902 lines — largest router)
- [ ] Refactor `api/v1/profiles.py`, `teacher.py`, `gdpr.py`, `features.py`, `consents.py`
- [ ] Refactor `api/v1/ai.py`, `services/ai.py` if has DB logic
- [ ] RBAC: Replace `requires_role("ADM")` in admin.py with granular permissions
- [ ] RBAC: Define new PERM_ADM_* constants if needed
- [ ] Verify: ZERO `from sqlalchemy import` in any router
- [ ] Verify: ZERO `select(` in any service
- [ ] **Review & commit myself**: `refactor(backend): extract remaining repositories, complete RBAC standardization`

### Batch 7 — Backend Validation
- [ ] Search all routers for remaining SQL imports → fix
- [ ] Search all services for remaining `select()` → fix
- [ ] All repositories extend BaseRepository → verify
- [ ] All services create repos in `__init__` → verify
- [ ] No local helper functions in routers → verify
- [ ] All endpoints have `@requires_permission()` → verify
- [ ] No hardcoded role checks for access control → verify
- [ ] 36 unused permissions: either implement or document as deprecated
- [ ] **Review & commit myself**: `chore(backend): final validation pass for 3-tier architecture`

---

## Phase 2: Fix Missing Features from Phases 14-16

### Phase 14 Gaps
- [ ] Create PDF Jinja2 templates: student report card, class summary, attendance, billing
- [ ] Add Arabic RTL layout support in PDF templates
- [ ] Add weekly aggregation to analytics endpoints
- [ ] **Review & commit myself**: `feat(backend): add PDF report templates and Arabic RTL support`

### Phase 15 Gaps
- [ ] Add holiday CRUD endpoints (create/update for ADM)
- [ ] Add event type color coding in calendar responses
- [ ] **Review & commit myself**: `feat(backend): add holiday management and event color coding`

### Phase 16 Gaps
- [ ] Implement `web/src/features/documents/ResourcesPage.tsx` (currently 137-byte stub)
- [ ] Implement document expiry notifications (30-day warning)
- [ ] Implement bulk document operations (multi-select → download ZIP, delete)
- [ ] Add ClamAV setup guide in docs
- [ ] **Review & commit myself**: `feat: complete document management gaps (resources page, expiry, bulk ops)`

---

## Phase 3: Web Frontend Refactor (4 batches)

### Batch 0 — React Query Setup
- [ ] Install `@tanstack/react-query@5`
- [ ] Update `web/src/main.tsx` with QueryClientProvider
- [ ] Create `web/src/shared/hooks/useQueryDefaults.ts`
- [ ] Verify: `npm run build` passes
- [ ] **Review & commit myself**: `feat(web): add React Query and shared query configuration`

### Batch 1 — Notifications, Feed, Calendar
- [ ] Create `notifications.service.ts` + `useNotifications.ts`
- [ ] Create `feed.service.ts` + `useFeed.ts`
- [ ] Create `calendar.service.ts` + `useCalendar.ts`
- [ ] Update `NotificationsPage.tsx` — no direct API calls
- [ ] Update `FeedPage.tsx` — no direct API calls
- [ ] Update `CalendarPage.tsx` — no direct API calls
- [ ] Verify: `npm run build` passes
- [ ] **Review & commit myself**: `refactor(web): extract services and hooks for notifications, feed, calendar`

### Batch 2 — Teacher & Admin
- [ ] Create `admin.service.ts` + `useAdmin*.ts` hooks
- [ ] Create `teacher.service.ts` + `useTeacher*.ts` hooks
- [ ] Update all admin pages — no direct API calls
- [ ] Update all teacher pages — no direct API calls
- [ ] Verify: `npm run build` passes
- [ ] **Review & commit myself**: `refactor(web): extract services and hooks for admin and teacher features`

### Batch 3 — All Remaining Features
- [ ] Create services + hooks for: student, messages, progress, content, results, invoices, documents, submissions, reports, analytics, profile, family, timetable, cms
- [ ] Update ALL remaining pages
- [ ] Verify: ZERO `api.get(` in any `*Page.tsx`
- [ ] Verify: `npm run build` passes
- [ ] **Review & commit myself**: `refactor(web): complete service/hook extraction for all features`

---

## Phase 4: Infrastructure Security (1 batch)

- [ ] Add `.env` to `.gitignore`
- [ ] Create proper `.env.example` with placeholder values
- [ ] Redis: `protected-mode yes` + `requirepass` + `bind 127.0.0.1`
- [ ] PostgreSQL: remove hardcoded passwords from `init.sql`
- [ ] Grafana: replace hardcoded password with env variable
- [ ] Alertmanager: uncomment webhook receivers with placeholder
- [ ] Update `infra/secrets/README.md` with secret generation guide
- [ ] Verify: no real secrets in any committed file
- [ ] **Review & commit myself**: `security(infra): harden Redis, PostgreSQL, monitoring configs`

---

## Phase 5: Final Full-Stack Validation

### Backend
- [ ] `from sqlalchemy import` in routers → ZERO matches
- [ ] `select(` in services → ZERO matches
- [ ] All repos extend BaseRepository
- [ ] All services use repos in `__init__`
- [ ] All endpoints have permission checks
- [ ] Run `ruff check backend/` → clean
- [ ] Run `pytest --collect-only` → all tests collected

### Web
- [ ] `api.get(` in `*Page.tsx` → ZERO matches
- [ ] Every feature has `.service.ts` + `use*.ts`
- [ ] QueryClientProvider in `main.tsx`
- [ ] `npm run build` → clean
- [ ] `npx tsc --noEmit` → clean

### Mobile
- [ ] `flutter analyze` → clean
- [ ] No deprecated `value:` in DropdownButtonFormField

### Infra
- [ ] `.env` in `.gitignore`
- [ ] No real secrets in committed files
- [ ] Redis has `requirepass`
- [ ] PostgreSQL has no hardcoded passwords

### Integration
- [ ] Docker stack starts: `make up`
- [ ] Health check passes: `curl http://localhost:8000/api/v1/health`
- [ ] Backend tests pass: `pytest tests -q`
- [ ] Web builds and serves
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
