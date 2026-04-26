# Ecole Platform — Web Phase 2 TODO Checklist

> Generated: 2026-04-06
> Prerequisite: All 26 Phase 1 prompts (WEB-P0-1 → WEB-P4-5) completed and green
> Scope: Bundle optimization, remaining endpoint coverage, CI/CD, integration tests
> Backend surface: 311 endpoints total, ~141 uncovered by frontend

---

## Phase 5 — Bundle Optimization & Performance

> Goal: Fix the 1.5MB bundle, add code splitting, improve build performance.

### P5-1: Route-Based Code Splitting
- [ ] Convert ALL page imports in `App.tsx` to `React.lazy()` with dynamic imports
- [ ] Group lazy imports by feature for better chunk splitting
- [ ] Add `<Suspense fallback={<Skeleton variant="card" count={3} />}>` around each lazy route group
- [ ] Configure Vite `manualChunks` in `vite.config.ts` to split: vendor (react, react-dom, react-router), query (tanstack), charts (recharts), i18n, features
- [ ] Verify: `npm run build` → no single chunk > 300KB
- [ ] Add bundle analyzer: `npm install -D rollup-plugin-visualizer`

### P5-2: Performance Optimizations
- [ ] Add `React.memo()` to all shared components that receive stable props (Badge, StatCard, Breadcrumb)
- [ ] Add `useMemo`/`useCallback` to expensive computations in large pages (GradebookPage, AnalyticsDashboardPage)
- [ ] Add `staleTime: 5 * 60 * 1000` (5 min) to React Query defaults for read-heavy queries
- [ ] Add `prefetchQuery` on hover for navigation links to feature pages
- [ ] Verify: Lighthouse Performance score > 80

### P5-3: Image & Asset Optimization
- [ ] Configure Vite to inline small SVGs (< 4KB) as data URIs
- [ ] Add `loading="lazy"` to all `<img>` tags in feature pages
- [ ] Compress locale JSON files (remove whitespace in production builds)
- [ ] Move large locale files to dynamic imports (load only active language)

---

## Phase 6 — Remaining Endpoint Coverage (Tier 1 — Critical)

> Goal: Cover the most-used uncovered backend endpoints.

### P6-1: Auth Service Completion
- [ ] Add to `auth.service.ts`: `login()`, `refresh()`, `logout()`, `getMe()`, `getLoginHistory()`
- [ ] Note: `AuthContext.tsx` likely already handles login/refresh/logout via direct fetch — reconcile to use the service pattern consistently
- [ ] Add `LoginHistoryPage.tsx` under profile or admin feature (DataTable of login sessions with IP, device, timestamp)
- [ ] Wire route: `/profile/login-history`

### P6-2: API Path Reconciliation (Contract Mismatches)
- [ ] **micro-schools**: Frontend uses `/micro-schools`, backend uses `/micro/schools` — fix frontend service to match backend
- [ ] **micro-schools**: Add missing endpoints: groups CRUD, enrollment POST/GET, payment POST/GET/analytics, resource POST/GET, progress-logs POST/GET
- [ ] **skills**: Add missing endpoints: `GET /skills/progress/student/{id}`, `POST /skills/evaluate/{id}`, `GET/POST /skills/passport/{id}`, `GET /skills/passport/{id}/download`, `GET /skills/leaderboard/{class_id}`
- [ ] **gradebook**: Add missing endpoints: `POST /gradebook/categories`, `GET /gradebook/categories/{classId}/{periodId}`, `POST /gradebook/compute/{classId}/{periodId}`, `GET /gradebook/transcript/{studentId}`, `GET /gradebook/{classId}/{periodId}`
- [ ] **sync**: Add missing endpoints: `POST /sync/push`, `POST /sync/pull`
- [ ] **financial-health**: Add missing: `GET /financial-health/export/csv`, `GET /financial-health/export/pdf`

### P6-3: Billing Enhancements (7 Uncovered Endpoints)
- [ ] Add to `billing.service.ts`: `getSiblingPolicy()`, `updateSiblingPolicy()`, `getLateFeePolicy()`, `updateLateFeePolicy()`, `createPaymentPlan()`, `listPaymentPlans()`, `getPaymentPlan(id)`
- [ ] Create `SiblingPolicyPage.tsx` — edit sibling discount rules
- [ ] Create `LateFeePolicyPage.tsx` — edit late fee rules
- [ ] Create `PaymentPlansPage.tsx` — list/create payment plans, DataTable with status
- [ ] Create `PaymentPlanDetailPage.tsx` — view plan, installments, payment schedule
- [ ] Wire routes: `/billing/sibling-policy`, `/billing/late-fees`, `/billing/payment-plans`, `/billing/payment-plans/:id`

### P6-4: Documents Module Completion (24 Endpoints — Largest Gap)
- [ ] Expand `documents.service.ts` to cover ALL 24 endpoints: upload, versions, download, preview, bulk download/delete, student documents, checklist, resources CRUD, resource download/rate
- [ ] Create `DocumentVersionsPage.tsx` — version history with restore capability
- [ ] Create `DocumentPreviewPage.tsx` — inline preview (PDF viewer, image, text)
- [ ] Create `StudentDocumentsPage.tsx` — manage student-specific documents + checklist
- [ ] Create `ResourceRatingComponent.tsx` — star rating for resources
- [ ] Add bulk operations to `DocumentsPage.tsx`: bulk download, bulk delete with ConfirmDialog
- [ ] Wire routes: `/documents/:id/versions`, `/documents/:id/preview`, `/students/:id/documents`

### P6-5: Events & Calendar Completion (15 Endpoints)
- [ ] Expand `calendar.service.ts` to cover ALL 15 event endpoints: CRUD events, holidays CRUD, RSVP create/get/list, reminder preferences, calendar options, iCal feed
- [ ] Create `HolidayManagerPage.tsx` — CRUD for school holidays (ADM/DIR only)
- [ ] Create `EventDetailPage.tsx` — single event view with RSVP button and attendee list
- [ ] Create `EventRSVPPage.tsx` — RSVP form with calendar integration
- [ ] Add iCal feed export button to `CalendarPage.tsx`
- [ ] Add reminder preferences UI in calendar settings
- [ ] Wire routes: `/calendar/holidays`, `/events/:id`, `/events/:id/rsvp`

---

## Phase 7 — Remaining Endpoint Coverage (Tier 2 — Supporting)

> Goal: Cover secondary backend modules that support core features.

### P7-1: Quiz Engine Completion (10 Endpoints)
- [ ] The CMS already has `QuizBuilderPage.tsx` and the student has `QuizPlayerPage.tsx`, but the API calls may not be fully wired
- [ ] Verify and add to appropriate services: quiz CRUD, publish, start attempt, respond, submit, get results, analytics
- [ ] Create `QuizAnalyticsPage.tsx` — quiz-level analytics: completion rate, average score, question difficulty
- [ ] Create `QuizResultsPage.tsx` — individual attempt results with correct/incorrect breakdown
- [ ] Wire routes: `/quizzes/:id/analytics`, `/quizzes/attempts/:id/results`

### P7-2: Question Bank (5 Endpoints)
- [ ] Create `web/src/features/question-bank/` directory
- [ ] Create `question-bank.service.ts`: CRUD, import from quiz, generate quiz, stats
- [ ] Create `useQuestionBank.ts`
- [ ] Create `QuestionBankPage.tsx` — DataTable of reusable questions with filters (subject, type, difficulty)
- [ ] Create `QuestionBankImportPage.tsx` — import questions from existing quiz
- [ ] Create `GenerateQuizPage.tsx` — auto-generate quiz from bank with criteria selection
- [ ] Wire routes: `/question-bank`, `/question-bank/import`, `/question-bank/generate`

### P7-3: Rubrics (6 Endpoints)
- [ ] Create `web/src/features/rubrics/` directory (or add to existing teacher feature)
- [ ] Create `rubrics.service.ts`: CRUD, duplicate, grade with rubric, get rubric results
- [ ] Create `RubricsListPage.tsx` — list/create/duplicate rubrics
- [ ] Create `RubricEditorPage.tsx` — create/edit rubric with criteria rows and level columns
- [ ] Create `RubricGradingPage.tsx` — grade a submission using a rubric
- [ ] Wire routes: `/rubrics`, `/rubrics/:id/edit`, `/submissions/:id/grade-rubric`

### P7-4: Timetable Generation (6 Endpoints)
- [ ] Expand `timetable.service.ts`: constraints CRUD, generate job, preview, apply
- [ ] Create `TimetableConstraintsPage.tsx` — define scheduling constraints (teacher availability, room limits)
- [ ] Create `TimetableGeneratePage.tsx` — trigger generation, show job progress, preview result
- [ ] Add "Apply" button to accept generated timetable
- [ ] Wire routes: `/timetable/constraints`, `/timetable/generate`

### P7-5: Recovery Flow (3 Endpoints)
- [ ] Create `web/src/features/recovery/` directory
- [ ] Create `recovery.service.ts`: request, verify, reset
- [ ] Create `ForgotPasswordPage.tsx` — email input → request reset
- [ ] Create `ResetPasswordPage.tsx` — token verification + new password form
- [ ] Wire routes: `/forgot-password`, `/reset-password`

### P7-6: Remaining Small Modules
- [ ] **GDPR** (3 endpoints): Create `GDPRPage.tsx` — data export request, data deletion request, consent log viewer. Wire: `/settings/privacy`
- [ ] **Exports** (2 endpoints): Add export buttons to existing pages (CSV/XLSX download utility in DataTable)
- [ ] **Feature Toggles** (4 endpoints): Create `FeatureTogglesPage.tsx` — admin toggle management UI. Wire: `/admin/features`
- [ ] **Consents** (1 endpoint): Add consent update to existing notification preferences page
- [ ] **Schools** (3 endpoints): Create `SchoolSettingsPage.tsx` — view/edit school info (ADM only). Wire: `/admin/school`
- [ ] **Profiles** (4 endpoints): Wire missing endpoints into existing `ProfilePage.tsx` (admin view, children view)
- [ ] **Content Library** (6 endpoints): Wire into existing CMS/teacher pages — library browse, assign, review queue
- [ ] **Invitations** (1 endpoint): Add consume invite flow to registration page

---

## Phase 8 — CI/CD Pipeline

> Goal: Automated quality gates on every push.

### P8-1: GitHub Actions — Lint & Type Check
- [ ] Create `.github/workflows/web-ci.yml`
- [ ] Trigger: push to `main`, `develop`, all PRs targeting `main`
- [ ] Job 1: Install deps → `npx tsc --noEmit` → `npm run lint`
- [ ] Cache `node_modules` with `actions/cache`
- [ ] Fail PR if any error

### P8-2: GitHub Actions — Unit Tests
- [ ] Add Job 2 to `web-ci.yml`: `npm run test -- --reporter=junit --outputFile=test-results.xml`
- [ ] Upload test results as artifact
- [ ] Add coverage reporting: `npm run test:coverage`
- [ ] Upload coverage to Codecov or as artifact
- [ ] Set minimum coverage threshold: 60% (warning), 50% (fail)

### P8-3: GitHub Actions — Build & Bundle Analysis
- [ ] Add Job 3: `npm run build`
- [ ] Add bundle size check: fail if any chunk > 500KB
- [ ] Add build artifact upload (for deployment preview)
- [ ] Add Lighthouse CI for performance/accessibility scoring

### P8-4: GitHub Actions — E2E Tests
- [ ] Add Job 4 (optional, runs on `main` only): start backend + frontend in docker-compose → run Playwright
- [ ] Upload Playwright report as artifact
- [ ] Create `docker-compose.ci.yml` for test environment

### P8-5: Pre-Commit Hooks
- [ ] Install `husky` + `lint-staged`
- [ ] Pre-commit: `lint-staged` runs ESLint + Prettier on staged files
- [ ] Pre-push: `npx tsc --noEmit` (type check entire project)
- [ ] Create `.lintstagedrc.json`

---

## Phase 9 — Integration Tests & Contract Tests

> Goal: Verify frontend actually works with the real backend.

### P9-1: API Contract Tests
- [ ] Install `@apidevtools/swagger-parser` or use OpenAPI spec from backend
- [ ] Create `tests/contract/` directory
- [ ] For each frontend service file, verify that every API path exists in the backend OpenAPI spec
- [ ] Verify request/response shapes match between frontend types and backend Pydantic schemas
- [ ] Automate: run as part of CI

### P9-2: Docker-Compose Dev Environment
- [ ] Create `docker-compose.dev.yml`: PostgreSQL + Redis + backend + frontend (hot reload)
- [ ] Create `scripts/seed-dev.sh`: seed database with test data for all features
- [ ] Create `scripts/reset-dev.sh`: drop and recreate database
- [ ] Ensure all 6 innovation features have seed data

### P9-3: Integration E2E Tests
- [ ] Create `web/e2e/integration/` directory
- [ ] Tests run against real backend (docker-compose):
  - [ ] Full registration → login → 2FA → access protected page
  - [ ] Teacher creates quiz → student takes quiz → teacher sees results
  - [ ] Admin creates budget → teacher submits request → admin approves
  - [ ] Parent views child's attendance, grades, and skill passport
  - [ ] Director views compliance dashboard with real data
  - [ ] Complete invoice → payment → proof upload → verification flow

### P9-4: Visual Regression Tests
- [ ] Install `@playwright/test` visual comparison
- [ ] Capture baseline screenshots for all pages in: light mode, dark mode, French, Arabic (RTL)
- [ ] Add to CI: compare against baselines, fail on unexpected pixel differences
- [ ] Create `scripts/update-baselines.sh` for intentional UI changes

### P9-5: Load & Performance Tests
- [ ] Add Lighthouse CI to measure: Performance, Accessibility, Best Practices, SEO
- [ ] Target scores: Performance > 80, Accessibility > 90, Best Practices > 90
- [ ] Test largest pages with simulated data: 500 students in gradebook, 1000 attendance records
- [ ] Add Web Vitals monitoring: LCP < 2.5s, FID < 100ms, CLS < 0.1

---

## Phase 10 — Final Verification Gate

> Goal: Everything green, production-ready.

### P10-1: Full Verification
- [ ] `npx tsc --noEmit` — 0 errors
- [ ] `npm run lint` — 0 errors, 0 warnings
- [ ] `npm run test` — all unit tests pass
- [ ] `npm run test:e2e` — all E2E tests pass
- [ ] `npm run build` — no chunk > 300KB (post code-splitting)
- [ ] All 311 backend endpoints have corresponding frontend API calls
- [ ] All feature pages render in: light mode, dark mode, FR, AR (RTL), EN
- [ ] All feature pages are keyboard-navigable
- [ ] Lighthouse: Performance > 80, Accessibility > 90
- [ ] CI pipeline runs green on GitHub Actions
- [ ] Docker-compose dev environment starts and seeds correctly

---

## Summary Statistics

| Phase | Tasks | Focus |
|-------|-------|-------|
| P5 — Bundle & Performance | 3 groups, ~18 items | Code splitting, memo, lazy loading |
| P6 — Endpoint Coverage Tier 1 | 5 groups, ~40 items | Auth, billing, documents, events, contract fixes |
| P7 — Endpoint Coverage Tier 2 | 6 groups, ~35 items | Quizzes, question bank, rubrics, timetable gen, recovery, misc |
| P8 — CI/CD | 5 groups, ~20 items | GitHub Actions, Husky, Codecov |
| P9 — Integration Tests | 5 groups, ~25 items | Contract, docker, integration E2E, visual regression, perf |
| P10 — Final Gate | 1 group, ~11 items | Full verification |
| **Total** | **25 groups, ~149 items** | **Production-ready** |
