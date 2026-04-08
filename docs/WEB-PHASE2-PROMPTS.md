# Ecole Platform — Web Phase 2 Detailed Prompts

> Generated: 2026-04-06
> Prerequisite: Phase 1 (WEB-P0-1 → WEB-P4-5) all green
> 18 prompts covering: bundle optimization, endpoint coverage, CI/CD, integration tests

---

## PHASE 5 — Bundle Optimization & Performance

---

### WEB-P5-1 — Route-Based Code Splitting

```
CONTEXT
-------
Project: ecole-platform-dev/web (React 18 + Vite 6 + TypeScript 5.6)
App.tsx (495+ lines) has 60+ routes. ALL page imports are static (import ... from).
Vite build produces a single chunk: index-*.js at 1.5MB (316KB gzip).
No manual chunk splitting configured in vite.config.ts.
React.lazy and Suspense are available in React 18.

TASK
----
1. Install bundle analyzer:
   cd web && npm install -D rollup-plugin-visualizer

2. Update web/vite.config.ts (NOT vitest.config.ts):
   - Import visualizer from rollup-plugin-visualizer
   - Add plugins: [react(), visualizer({ open: false, filename: 'dist/bundle-stats.html' })]
   - Add build.rollupOptions.output.manualChunks:
     vendor: ['react', 'react-dom', 'react-router-dom']
     query: ['@tanstack/react-query']
     charts: ['recharts']
     i18n: ['i18next', 'react-i18next', 'i18next-browser-languagedetector']
   - Everything else auto-splits by dynamic import boundaries

3. Rewrite ALL page imports in web/src/app/App.tsx to use React.lazy():
   Replace every:
     import { SomePage } from '@/features/some/SomePage';
   With:
     const SomePage = lazy(() => import('@/features/some/SomePage'));

   This must cover ALL ~60 page components. Keep non-page imports (ProtectedRoute, Layout, AuthProvider, etc.) as static imports.

4. Wrap route groups with <Suspense> in App.tsx:
   Each major <Route> group (auth routes, admin routes, teacher routes, student routes, etc.) should be wrapped with:
   <Suspense fallback={<LoadingState />}>
   Use the existing LoadingState or Skeleton component as fallback.

5. Create web/src/app/LazyPages.ts barrel file:
   Export all lazy page constants from one file so App.tsx is cleaner.

CONSTRAINTS
-----------
- Do NOT change any route paths or guards
- Do NOT change any component logic
- Every page must have a default export (React.lazy requires it)
  - Check: if any page uses named export, add `export default` or adjust the lazy import to use .then()
- Keep Suspense boundaries at the route group level (not individual routes) for better UX
- The ErrorBoundary from P0-3 should wrap each Suspense

VERIFY
------
cd web
npx tsc --noEmit
npm run lint
npm run build
# Check chunk sizes:
ls -la dist/assets/*.js | awk '{printf "%s\t%.1f KB\n", $9, $5/1024}'
# Verify NO single chunk > 300KB:
ls -la dist/assets/*.js | awk '$5 > 307200 {print "FAIL: " $9 " is " $5/1024 " KB"}'
# Should have multiple chunks (at least 5)
ls dist/assets/*.js | wc -l
npm run test
npm run test:e2e

GIT (Codex only)
---
git add web/vite.config.ts web/src/app/App.tsx web/src/app/LazyPages.ts web/package.json web/package-lock.json
git commit -m "perf(web): add route-based code splitting — lazy load all pages, manual vendor chunks"
```

---

### WEB-P5-2 — Performance Optimizations

```
CONTEXT
-------
Project: ecole-platform-dev/web
Code splitting from WEB-P5-1 is in place.
React Query is configured with defaults in App.tsx or QueryClient setup.
Large pages: GradebookPage (415 lines), AnalyticsDashboardPage (424 lines), several pages > 250 lines.

TASK
----
1. Update QueryClient defaults in web/src/app/App.tsx (or wherever QueryClient is created):
   defaultOptions: {
     queries: {
       staleTime: 5 * 60 * 1000,   // 5 minutes
       gcTime: 10 * 60 * 1000,      // 10 minutes (formerly cacheTime)
       retry: 2,
       refetchOnWindowFocus: false,  // reduce unnecessary refetches
     },
     mutations: {
       retry: 0,
     },
   }

2. Add React.memo to these shared components (only if they don't already use it):
   - Badge.tsx
   - StatCard.tsx
   - Breadcrumb.tsx
   - Skeleton.tsx
   - EmptyState.tsx

3. In GradebookPage.tsx: wrap the grade grid rendering in useMemo (depends on gradebook data).

4. In AnalyticsDashboardPage.tsx: wrap chart data transformations in useMemo.

5. Add prefetch on hover to sidebar navigation links in Layout.tsx:
   - Import useQueryClient from @tanstack/react-query
   - On <Link onMouseEnter>, prefetch the target page's primary query
   - Only for the 5 most-used routes (dashboard, attendance, gradebook, invoices, notifications)

6. Add loading="lazy" to ALL <img> tags across the entire codebase.

CONSTRAINTS
-----------
- Do NOT over-memoize: only memoize components with expensive renders or stable parent props
- Do NOT add React.memo to components that receive children or frequently-changing props
- staleTime applies globally — individual queries can override if needed

VERIFY
------
cd web
npx tsc --noEmit
npm run lint
npm run build
npm run test

GIT (Codex only)
---
git add web/src/
git commit -m "perf(web): optimize React Query defaults, memoize shared components, add prefetch on hover"
```

---

### WEB-P5-3 — Dynamic i18n Loading

```
CONTEXT
-------
Locale files: web/src/shared/i18n/locales/en.json (43KB), fr.json (46KB), ar.json (54KB)
All three are statically imported in web/src/shared/i18n/index.ts.
This adds ~143KB to the initial bundle even though only one language is active.

TASK
----
1. Refactor web/src/shared/i18n/index.ts to use dynamic import:
   - Load only the default locale (fr) synchronously or at init
   - Load other locales on demand when the user switches language
   - Use i18next-http-backend or a custom loadPath with dynamic import():
     import(`./locales/${lang}.json`)
   - Fallback: if dynamic import fails, use the default locale

2. Update LanguageSwitcher.tsx:
   - Show a brief loading state when switching to a new language (first load only)
   - After first load, the language is cached in memory

3. Verify all 3 languages still work correctly after the change.

CONSTRAINTS
-----------
- French (fr) must always be available immediately (it's the default)
- Do NOT use i18next-http-backend if it requires a server — use dynamic import() instead
- Do NOT break the existing translation() calls in any component

VERIFY
------
cd web
npx tsc --noEmit
npm run lint
npm run build
# Verify locale files are separate chunks:
ls dist/assets/ | grep -i locale
npm run test

GIT (Codex only)
---
git add web/src/shared/i18n/ web/src/shared/ui/LanguageSwitcher.tsx
git commit -m "perf(web): dynamic i18n loading — load only active locale, lazy-load others on switch"
```

---

## PHASE 6 — Endpoint Coverage Tier 1

---

### WEB-P6-1 — API Path Reconciliation & Service Completion

```
CONTEXT
-------
Analysis found these frontend/backend path mismatches:
1. micro-schools: Frontend uses /micro-schools, backend uses /micro/schools and /micro/groups etc.
2. Several services are missing endpoints that exist in the backend.

Backend endpoints per module (from router prefix analysis):
  micro_school.py (prefix /micro): 14 endpoints covering schools, groups, enrollments, payments, resources, progress-logs
  skills.py (prefix /skills): 12 endpoints — 6 uncovered (progress, evaluate, passport generate/download, leaderboard)
  gradebook.py (prefix /gradebook): 5 endpoints — 5 uncovered (categories, compute, transcript, period-scoped get)
  sync.py (prefix /sync): 10 endpoints — 2 uncovered (push, pull)
  financial_health.py (prefix /financial-health): 12 endpoints — 2 uncovered (export/csv, export/pdf)
  attendance.py (prefix /attendance): 3 endpoints — 2 uncovered (justifications POST, review)

TASK
----
1. Fix web/src/features/micro-schools/micro-schools.service.ts:
   - Change ALL paths from /micro-schools to /micro/schools
   - Add missing endpoints:
     createGroup(schoolId, payload): POST /micro/groups
     getGroups(schoolId): GET /micro/schools/{id}/groups
     createEnrollment(payload): POST /micro/enrollments
     listEnrollments(params): GET /micro/enrollments
     createPayment(payload): POST /micro/payments
     listPayments(params): GET /micro/payments
     getPaymentAnalytics(): GET /micro/payments/analytics
     createResource(payload): POST /micro/resources
     listResources(params): GET /micro/resources
     createProgressLog(payload): POST /micro/progress-logs
     listProgressLogs(params): GET /micro/progress-logs

2. Fix web/src/features/skills/skills.service.ts — add:
     getStudentProgress(studentId): GET /skills/progress/student/{id}
     evaluateStudent(studentId, payload): POST /skills/evaluate/{id}
     getPassport(studentId): GET /skills/passport/{id}
     generatePassport(studentId): POST /skills/passport/{id}/generate
     downloadPassport(studentId): GET /skills/passport/{id}/download
     getLeaderboard(classId): GET /skills/leaderboard/{id}

3. Fix web/src/features/gradebook/gradebook.service.ts — add:
     createCategory(payload): POST /gradebook/categories
     getCategories(classId, periodId): GET /gradebook/categories/{classId}/{periodId}
     computeGrades(classId, periodId): POST /gradebook/compute/{classId}/{periodId}
     getTranscript(studentId): GET /gradebook/transcript/{studentId}
     getPeriodGradebook(classId, periodId): GET /gradebook/{classId}/{periodId}

4. Fix web/src/features/sync/sync.service.ts — add:
     pushQueue(payload): POST /sync/push
     pullQueue(params): POST /sync/pull

5. Fix web/src/features/financial-health/financial-health.service.ts — add:
     exportCsv(params): GET /financial-health/export/csv
     exportPdf(params): GET /financial-health/export/pdf

6. Fix web/src/features/attendance/attendance.service.ts — add:
     submitJustificationDirect(payload): POST /attendance/justifications
     reviewJustification(justificationId, payload): POST /attendance/justifications/{id}/review

7. Update all corresponding hook files (useMicroSchools.ts, useSkills.ts, useGradebook.ts, useSync.ts, useFinancialHealth.ts, useAttendance.ts) to expose the new service methods as queries/mutations.

8. Update types files to add any missing type definitions for the new endpoints.

CONSTRAINTS
-----------
- Fix paths to match backend EXACTLY (use the router prefix from backend/app/api/v1/*.py)
- All new service methods must be typed with proper request/response types
- All new hooks must follow the existing pattern (useQuery for GET, useMutation for POST/PUT/DELETE)
- Do NOT change any page component yet — this prompt only fixes services and hooks

VERIFY
------
cd web
npx tsc --noEmit
npm run lint
npm run build
# Count total API calls across all services:
grep -rn "api\.\(get\|post\|put\|patch\|delete\|list\)(" src/features/ --include="*.service.ts" | wc -l
# Should be significantly higher than before

GIT (Codex only)
---
git add web/src/features/
git commit -m "fix(web): reconcile API paths with backend, add 30+ missing service endpoints"
```

---

### WEB-P6-2 — Billing Enhancements

```
CONTEXT
-------
Backend billing.py (14 endpoints, prefix /billing):
  7 uncovered: sibling-policy GET/PUT, late-fee-policy GET/PUT, payment-plans POST/GET/GET:id
Current frontend: web/src/features/billing/ has FeeStructuresPage.tsx, FeeAssignmentsPage.tsx

TASK
----
1. Add to billing.service.ts:
   getSiblingPolicy(): GET /billing/sibling-policy
   updateSiblingPolicy(payload): PUT /billing/sibling-policy
   getLateFeePolicy(): GET /billing/late-fee-policy
   updateLateFeePolicy(payload): PUT /billing/late-fee-policy
   createPaymentPlan(payload): POST /billing/payment-plans
   listPaymentPlans(params): GET /billing/payment-plans
   getPaymentPlan(planId): GET /billing/payment-plans/{id}

2. Add types: SiblingPolicy, LateFeePolicy, PaymentPlan, PaymentPlanInstallment

3. Add hooks: useSiblingPolicy(), useUpdateSiblingPolicy(), useLateFeePolicy(), useUpdateLateFeePolicy(), usePaymentPlans(), useCreatePaymentPlan(), usePaymentPlan(id)

4. Create SiblingPolicyPage.tsx (~150 lines):
   - Display current policy: discount percentages per additional sibling
   - Edit form: react-hook-form + zod (percentage 0-100)
   - Guards: ADM only

5. Create LateFeePolicyPage.tsx (~150 lines):
   - Display current policy: grace period days, fee percentage, max fee cap
   - Edit form with validation
   - Guards: ADM only

6. Create PaymentPlansPage.tsx (~200 lines):
   - DataTable: plan name, student, total amount (MAD), installments count, status (Badge)
   - Create new plan button → form modal
   - Guards: ADM, DIR, PAR

7. Create PaymentPlanDetailPage.tsx (~180 lines):
   - Plan header: student, total, start date, status
   - Installments DataTable: due date, amount, status, payment date
   - Progress bar: paid vs remaining

8. Wire routes: /billing/sibling-policy, /billing/late-fees, /billing/payment-plans, /billing/payment-plans/:id
9. Add sidebar links under Billing section for ADM role
10. Add i18n keys under "billing" namespace

CONSTRAINTS
-----------
- All amounts in MAD with Intl.NumberFormat('fr-MA', { style: 'currency', currency: 'MAD' })
- Use existing shared components (DataTable, FormField, Badge, ConfirmDialog)

VERIFY
------
cd web
npx tsc --noEmit && npm run lint && npm run build
ls src/features/billing/*.tsx | wc -l  # Should be >= 6

GIT (Codex only)
---
git add web/src/features/billing/ web/src/app/App.tsx web/src/shared/ui/Layout.tsx web/src/shared/i18n/locales/
git commit -m "feat(web): add billing sibling policy, late fee policy, and payment plans UI"
```

---

### WEB-P6-3 — Documents Module Completion

```
CONTEXT
-------
Backend documents.py has 24 endpoints (largest module). Frontend currently covers ~14 via DocumentsPage.tsx (234 lines) + DocumentList, DocumentUpload, DocumentViewer, DocumentFilters sub-components.
Missing: version history, preview, bulk operations, student documents, resource rating.

TASK
----
1. Expand documents.service.ts to add ALL missing endpoints:
   getVersions(docId): GET /documents/{id}/versions
   getVersion(docId, versionNum): GET /documents/{id}/versions/{num}
   restoreVersion(docId, versionNum): POST /documents/{id}/versions/{num}/restore
   downloadDocument(docId): GET /documents/{id}/download
   previewDocument(docId): GET /documents/{id}/preview
   bulkDownload(docIds): POST /documents/bulk-download
   getBulkDownloadStatus(): GET /documents/bulk-download
   bulkDelete(docIds): POST /documents/bulk-delete
   uploadStudentDocument(studentId, payload): POST /students/{id}/documents
   getStudentDocuments(studentId): GET /students/{id}/documents
   getStudentChecklist(studentId): GET /students/{id}/documents/checklist
   rateResource(resourceId, rating): POST /resources/{id}/rate
   getResourceRating(resourceId): GET /resources/{id}/rating
   downloadResource(resourceId): GET /resources/{id}/download

2. Create DocumentVersionsPage.tsx (~180 lines):
   - DataTable: version number, date, author, size, actions (preview, restore)
   - Restore with ConfirmDialog: "Restore version X? Current version will be kept in history."

3. Create DocumentPreviewPage.tsx (~120 lines):
   - Detect file type and render: PDF in <iframe>, images in <img>, text in <pre>
   - Download button, version history link

4. Create StudentDocumentsPage.tsx (~200 lines):
   - Student selector (for admin/teacher) or auto-select current student
   - Checklist view: required documents with status (uploaded/missing/expired)
   - Upload form per checklist item
   - Guards: ADM, DIR, TCH, PAR, STD

5. Add bulk operations to DocumentsPage.tsx:
   - Checkbox selection on DataTable rows
   - "Bulk Download" and "Bulk Delete" buttons (only visible when rows selected)
   - Bulk delete with ConfirmDialog

6. Add resource rating component: star rating (1-5) with hover preview

7. Wire routes: /documents/:id/versions, /documents/:id/preview, /students/:id/documents
8. Add i18n keys

VERIFY
------
cd web
npx tsc --noEmit && npm run lint && npm run build

GIT (Codex only)
---
git add web/src/features/documents/ web/src/app/App.tsx web/src/shared/i18n/locales/
git commit -m "feat(web): complete documents module — versions, preview, bulk ops, student docs, ratings"
```

---

### WEB-P6-4 — Events & Calendar Completion

```
CONTEXT
-------
Backend events.py (15 endpoints, prefix /events and /calendar):
  Events CRUD, holidays CRUD, RSVP, reminder preferences, calendar options, iCal feed
Current frontend: CalendarPage.tsx (split into sub-components), calendar.service.ts covers ~6 endpoints

TASK
----
1. Expand calendar.service.ts with ALL missing event/calendar endpoints:
   getHolidays(): GET /calendar/holidays
   createHoliday(payload): POST /calendar/holidays
   updateHoliday(id, payload): PUT /calendar/holidays/{id}
   deleteHoliday(id): DELETE /calendar/holidays/{id}
   getEvent(eventId): GET /events/{id}
   createEvent(payload): POST /events
   updateEvent(id, payload): PUT /events/{id}
   deleteEvent(id): DELETE /events/{id}
   submitRSVP(eventId, payload): POST /events/{id}/rsvp
   getMyRSVP(eventId): GET /events/{id}/rsvp
   getEventRSVPs(eventId): GET /events/{id}/rsvps
   updateReminderPreferences(payload): POST /events/reminder-preferences
   getICalFeed(): GET /calendar/ical

2. Create HolidayManagerPage.tsx (~180 lines):
   - DataTable: holiday name, start date, end date, type (national/school), actions
   - Create/edit form modal with date range picker
   - Delete with ConfirmDialog
   - Guards: ADM, DIR

3. Create EventDetailPage.tsx (~200 lines):
   - Event info: title, description, date/time, location, organizer
   - RSVP section: Yes/No/Maybe buttons, attendee count and list
   - Delete/edit buttons for organizer
   - Reminder preferences toggle

4. Add iCal export button to CalendarPage.tsx

5. Wire routes: /calendar/holidays, /events/:id
6. Add sidebar link for holiday management
7. Add i18n keys

VERIFY
------
cd web
npx tsc --noEmit && npm run lint && npm run build

GIT (Codex only)
---
git add web/src/features/calendar/ web/src/app/App.tsx web/src/shared/ui/Layout.tsx web/src/shared/i18n/locales/
git commit -m "feat(web): complete calendar module — holidays CRUD, event detail, RSVP, iCal export"
```

---

### WEB-P6-5 — Auth Service Completion & Recovery Flow

```
CONTEXT
-------
Backend auth.py (14 endpoints), recovery.py (3 endpoints)
AuthContext.tsx handles login/refresh/logout via direct fetch, but auth.service.ts only has register + verify-email
No forgot-password or reset-password UI exists

TASK
----
1. Add to auth.service.ts:
   login(email, password): POST /auth/login
   refresh(): POST /auth/refresh
   logout(): POST /auth/logout (or DELETE)
   getMe(): GET /auth/me
   getLoginHistory(): GET /auth/login-history
   requestRecovery(email): POST /recovery/request
   verifyRecovery(token, code): POST /recovery/verify
   resetPassword(token, newPassword): POST /recovery/reset

2. Create LoginHistoryPage.tsx (~120 lines):
   - DataTable: date, IP address, device/browser, location (if available), status
   - Place under profile feature
   - Guards: all authenticated users

3. Create ForgotPasswordPage.tsx (~100 lines):
   - Email input form (react-hook-form + zod email validation)
   - Submit → show "Check your email" message
   - Link back to login

4. Create ResetPasswordPage.tsx (~120 lines):
   - Token from URL params
   - New password + confirm password form
   - Password strength indicator
   - Submit → redirect to login on success

5. Wire routes: /profile/login-history, /forgot-password, /reset-password
6. Add "Forgot password?" link on LoginPage.tsx
7. Add i18n keys

VERIFY
------
cd web
npx tsc --noEmit && npm run lint && npm run build

GIT (Codex only)
---
git add web/src/features/auth/ web/src/features/profile/ web/src/app/App.tsx web/src/shared/i18n/locales/
git commit -m "feat(web): complete auth service, add password recovery flow and login history"
```

---

## PHASE 7 — Endpoint Coverage Tier 2

---

### WEB-P7-1 — Question Bank Module

```
CONTEXT
-------
Backend question_bank.py (5 endpoints, prefix /question-bank):
  POST /question-bank — create question
  GET /question-bank — list questions
  POST /question-bank/import/{quiz_id} — import from quiz
  POST /question-bank/generate-quiz — auto-generate quiz
  GET /question-bank/stats — bank statistics
No frontend exists for this module.

TASK
----
1. Create web/src/features/question-bank/ with: types, service (5 endpoints), hooks
2. QuestionBankPage.tsx (~200 lines): DataTable with filters (subject, type, difficulty), create button
3. QuestionBankImportPage.tsx (~120 lines): select quiz, preview questions, import
4. GenerateQuizPage.tsx (~150 lines): criteria form (subject, difficulty, count), preview generated quiz, save
5. Wire routes: /question-bank, /question-bank/import, /question-bank/generate
6. Add sidebar link for TCH, CONTENT_MGR
7. Add i18n keys

VERIFY
------
cd web && npx tsc --noEmit && npm run lint && npm run build

GIT (Codex only)
---
git add web/src/features/question-bank/ web/src/app/App.tsx web/src/shared/ui/Layout.tsx web/src/shared/i18n/locales/
git commit -m "feat(web): build question bank module — CRUD, quiz import, auto-generation"
```

---

### WEB-P7-2 — Rubrics Module

```
CONTEXT
-------
Backend rubrics.py (6 endpoints, prefix /rubrics): CRUD, duplicate, grade-rubric, rubric-results
No frontend rubrics feature exists (teacher already has some assessment pages)

TASK
----
1. Create web/src/features/rubrics/ with: types, service (6 endpoints), hooks
2. RubricsListPage.tsx (~150 lines): DataTable of rubrics, duplicate button, create button
3. RubricEditorPage.tsx (~250 lines): criteria rows × level columns grid editor, save/preview
4. RubricGradingPage.tsx (~200 lines): select levels per criteria per student, auto-calculate score
5. Wire routes: /rubrics, /rubrics/:id/edit, /rubrics/:id/grade
6. Add sidebar link for TCH
7. Add i18n keys

VERIFY
------
cd web && npx tsc --noEmit && npm run lint && npm run build

GIT (Codex only)
---
git add web/src/features/rubrics/ web/src/app/App.tsx web/src/shared/ui/Layout.tsx web/src/shared/i18n/locales/
git commit -m "feat(web): build rubrics module — editor, grading, criteria grid"
```

---

### WEB-P7-3 — Timetable Generation

```
CONTEXT
-------
Backend timetable_generation.py (6 endpoints, prefix /timetable):
  POST /timetable/constraints, GET /timetable/constraints
  POST /timetable/generate, GET /timetable/generate/{job_id}
  GET /timetable/generate/{job_id}/preview, POST /timetable/generate/{job_id}/apply
Timetable feature exists but only covers viewing, not generation.

TASK
----
1. Expand timetable.service.ts with all 6 generation endpoints
2. Create TimetableConstraintsPage.tsx (~180 lines): form to define constraints (teacher availability, room capacity, consecutive class limits)
3. Create TimetableGeneratePage.tsx (~200 lines): trigger generation button, progress indicator (polling job status), preview generated timetable in grid, "Apply" button with ConfirmDialog
4. Wire routes: /timetable/constraints, /timetable/generate
5. Add i18n keys

VERIFY
------
cd web && npx tsc --noEmit && npm run lint && npm run build

GIT (Codex only)
---
git add web/src/features/timetable/ web/src/app/App.tsx web/src/shared/i18n/locales/
git commit -m "feat(web): add timetable generation — constraints editor, auto-generate, preview, apply"
```

---

### WEB-P7-4 — Remaining Small Modules

```
CONTEXT
-------
Several backend modules need small frontend additions:
  gdpr.py (3 endpoints, prefix /users): data export, deletion, consent log
  exports.py (2 endpoints, prefix /export): CSV, XLSX export
  features.py (4 endpoints, prefix /features): feature toggle management
  consents.py (1 endpoint): update consent
  schools.py (3 endpoints): school CRUD
  content_library.py (6 endpoints): library browse, assign, review
  invitations.py (1 uncovered): consume invite
  profiles.py (4 endpoints): profile views

TASK
----
1. GDPR: Create GDPRPage.tsx (~150 lines) — 3 sections: request data export, request data deletion (with ConfirmDialog), view consent log. Route: /settings/privacy

2. Feature Toggles: Create FeatureTogglesPage.tsx (~120 lines) — DataTable of toggles with on/off switch, edit modal. Route: /admin/features. Guards: SYS, ADM

3. School Settings: Create SchoolSettingsPage.tsx (~150 lines) — view/edit school info form (name, address, city, phone). Route: /admin/school. Guards: ADM

4. Exports utility: Add export dropdown component to DataTable.tsx — CSV and XLSX options that call /export/csv and /export/xlsx with current table data context

5. Content Library: Wire the 6 content_library.py endpoints into the existing CMS feature (cms.service.ts). Add library browse tab to CMS pages if not present.

6. Profiles: Expand profile.service.ts to add admin user profile view (GET /admin/users/{id}/profile) and children list (GET /me/children). Wire into ProfilePage.tsx.

7. Consents: Add consent update call (PUT /consents/{id}) to notification preferences page.

8. Invitations: Add consume invite flow — if URL has ?invite=TOKEN, call POST /invites/consume on register page.

9. Add i18n keys for all new pages.

CONSTRAINTS
-----------
- Each new page should be < 200 lines
- Use existing shared components
- Wire new routes in App.tsx with appropriate guards

VERIFY
------
cd web
npx tsc --noEmit && npm run lint && npm run build

GIT (Codex only)
---
git add web/src/features/ web/src/app/App.tsx web/src/shared/
git commit -m "feat(web): add GDPR, feature toggles, school settings, exports, and remaining small modules"
```

---

### WEB-P7-5 — Quiz Engine Wiring & Analytics

```
CONTEXT
-------
Backend quizzes.py (10 endpoints). CMS has QuizBuilderPage, student has QuizPlayerPage.
But the services may not be fully wired to all 10 endpoints.

TASK
----
1. Verify and complete quiz-related service calls:
   In cms.service.ts or a new quizzes.service.ts:
     createQuiz, listQuizzes, getQuiz, updateQuiz, publishQuiz
     startAttempt, respondToQuestion, submitAttempt, getResults, getAnalytics

2. Create QuizAnalyticsPage.tsx (~180 lines):
   - Quiz stats: completion rate, average score, question difficulty breakdown
   - Recharts: score distribution histogram, question-by-question bar chart
   - Route: /quizzes/:id/analytics, Guard: TCH

3. Create QuizResultsPage.tsx (~150 lines):
   - Individual attempt: question-by-question results with correct/incorrect indicators
   - Score summary, time taken
   - Route: /quizzes/attempts/:id/results

4. Wire routes and add i18n keys.

VERIFY
------
cd web && npx tsc --noEmit && npm run lint && npm run build

GIT (Codex only)
---
git add web/src/features/
git commit -m "feat(web): complete quiz engine wiring — analytics, results, full API coverage"
```

---

## PHASE 8 — CI/CD Pipeline

---

### WEB-P8-1 — GitHub Actions CI Pipeline

```
CONTEXT
-------
Project: ecole-platform-dev (monorepo with backend/ and web/ directories)
No .github/workflows/ directory exists for frontend CI.
Package manager: npm
Node version: 18+ (use 20 LTS in CI)

TASK
----
1. Create .github/workflows/web-ci.yml:

name: Web CI
on:
  push:
    branches: [main, develop]
    paths: ['web/**']
  pull_request:
    branches: [main]
    paths: ['web/**']

jobs:
  lint-and-typecheck:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: web
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20 }
      - uses: actions/cache@v4
        with:
          path: web/node_modules
          key: node-modules-${{ hashFiles('web/package-lock.json') }}
      - run: npm ci
      - run: npx tsc --noEmit
      - run: npm run lint

  unit-tests:
    runs-on: ubuntu-latest
    needs: lint-and-typecheck
    defaults:
      run:
        working-directory: web
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20 }
      - uses: actions/cache@v4
        with:
          path: web/node_modules
          key: node-modules-${{ hashFiles('web/package-lock.json') }}
      - run: npm ci
      - run: npm run test -- --reporter=default --reporter=junit --outputFile=test-results.xml
      - run: npm run test:coverage
      - uses: actions/upload-artifact@v4
        with:
          name: test-results
          path: web/test-results.xml
      - uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: web/coverage/

  build:
    runs-on: ubuntu-latest
    needs: lint-and-typecheck
    defaults:
      run:
        working-directory: web
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20 }
      - uses: actions/cache@v4
        with:
          path: web/node_modules
          key: node-modules-${{ hashFiles('web/package-lock.json') }}
      - run: npm ci
      - run: npm run build
      - name: Check bundle sizes
        run: |
          MAX_SIZE=307200  # 300KB
          for f in dist/assets/*.js; do
            size=$(stat -c%s "$f")
            if [ "$size" -gt "$MAX_SIZE" ]; then
              echo "WARNING: $(basename $f) is $(($size/1024))KB (limit 300KB)"
            fi
          done
      - uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: web/dist/

2. Create .github/workflows/web-e2e.yml (runs only on main):
   - Similar setup but starts dev server + runs Playwright
   - Uses npx playwright install --with-deps
   - Uploads Playwright HTML report as artifact

CONSTRAINTS
-----------
- Use actions/cache for node_modules
- Build job runs in parallel with tests (both depend on lint)
- E2E only runs on push to main (not on PRs — too slow)

VERIFY
------
# Validate YAML syntax:
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/web-ci.yml'))"
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/web-e2e.yml'))"

GIT (Codex only)
---
git add .github/workflows/
git commit -m "ci(web): add GitHub Actions — lint, typecheck, unit tests, build, E2E"
```

---

### WEB-P8-2 — Pre-Commit Hooks

```
CONTEXT
-------
No pre-commit hooks exist. Developers can push code with lint errors or type errors.

TASK
----
1. cd web && npm install -D husky lint-staged prettier
2. npx husky init
3. Create web/.husky/pre-commit:
   cd web && npx lint-staged

4. Create web/.lintstagedrc.json:
   {
     "*.{ts,tsx}": ["eslint --fix", "prettier --write"],
     "*.{json,md,css}": ["prettier --write"]
   }

5. Create web/.prettierrc:
   {
     "singleQuote": true,
     "trailingComma": "all",
     "printWidth": 100,
     "tabWidth": 2,
     "semi": true
   }

6. Add to package.json scripts:
   "prepare": "husky"
   "format": "prettier --write src/"
   "format:check": "prettier --check src/"

CONSTRAINTS
-----------
- Do NOT run prettier on ALL files immediately (would create a massive diff)
- Only format staged files via lint-staged
- Pre-commit hook must be fast (< 10 seconds)

VERIFY
------
cd web
echo "test" > /tmp/test-hook.ts
git add /tmp/test-hook.ts 2>/dev/null || true
npx tsc --noEmit
npm run lint

GIT (Codex only)
---
git add web/.husky/ web/.lintstagedrc.json web/.prettierrc web/package.json web/package-lock.json
git commit -m "ci(web): add Husky pre-commit hooks with lint-staged and Prettier"
```

---

## PHASE 9 — Integration Tests

---

### WEB-P9-1 — API Contract Tests

```
CONTEXT
-------
Backend has an OpenAPI spec (auto-generated by FastAPI at /docs or /openapi.json).
Frontend has 30 service files with API calls.
No contract validation exists — frontend could call paths that don't exist on the backend.

TASK
----
1. Create web/tests/contract/api-contract.test.ts:
   - Read the backend OpenAPI spec (from backend/openapi.json or generate it)
   - For each frontend service file, extract all API paths
   - Verify each path exists in the OpenAPI spec
   - Verify HTTP methods match
   - Report any mismatches

2. Add a script to generate the OpenAPI spec:
   Create scripts/generate-openapi.sh:
   cd backend && python -c "
   from app.main import app
   import json
   spec = app.openapi()
   with open('openapi.json', 'w') as f:
       json.dump(spec, f, indent=2)
   "

3. Add npm script: "test:contract": "vitest run tests/contract/"

VERIFY
------
cd web && npm run test:contract

GIT (Codex only)
---
git add web/tests/contract/ scripts/generate-openapi.sh web/package.json
git commit -m "test(web): add API contract tests — verify frontend paths match backend OpenAPI spec"
```

---

### WEB-P9-2 — Docker-Compose Dev Environment

```
CONTEXT
-------
Backend needs: PostgreSQL, Redis
Frontend needs: backend API running
No docker-compose for full-stack development exists.

TASK
----
1. Create docker-compose.dev.yml at project root:
   services:
     postgres:
       image: postgres:16-alpine
       environment:
         POSTGRES_DB: ecole_dev
         POSTGRES_USER: ecole
         POSTGRES_PASSWORD: ecole_dev_password
       ports: ["5432:5432"]
       volumes: [postgres_data:/var/lib/postgresql/data]

     redis:
       image: redis:7-alpine
       ports: ["6379:6379"]

     backend:
       build: ./backend
       ports: ["8000:8000"]
       environment:
         DATABASE_URL: postgresql+asyncpg://ecole:ecole_dev_password@postgres:5432/ecole_dev
         REDIS_URL: redis://redis:6379/0
       depends_on: [postgres, redis]
       volumes: [./backend:/app]
       command: uvicorn app.main:app --host 0.0.0.0 --reload

     web:
       build: ./web
       ports: ["5173:5173"]
       depends_on: [backend]
       volumes: [./web/src:/app/src]
       command: npm run dev -- --host 0.0.0.0

   volumes:
     postgres_data:

2. Create web/Dockerfile.dev:
   FROM node:20-alpine
   WORKDIR /app
   COPY package*.json ./
   RUN npm ci
   COPY . .
   EXPOSE 5173
   CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

3. Create scripts/seed-dev.sh:
   Script to seed the database with test data for all features.
   Use alembic upgrade head + seed script.

4. Create scripts/reset-dev.sh:
   docker-compose -f docker-compose.dev.yml down -v
   docker-compose -f docker-compose.dev.yml up -d

VERIFY
------
# Validate docker-compose syntax:
docker-compose -f docker-compose.dev.yml config

GIT (Codex only)
---
git add docker-compose.dev.yml web/Dockerfile.dev scripts/
git commit -m "infra: add docker-compose dev environment with PostgreSQL, Redis, backend, frontend"
```

---

### WEB-P9-3 — Final Phase 2 Verification Gate

```
CONTEXT
-------
All Phase 2 prompts (P5-P9) are complete. Final verification.

TASK
----
Run ALL checks:

1. npx tsc --noEmit — 0 errors
2. npm run lint — 0 errors
3. npm run test — all pass
4. npm run test:e2e — all pass
5. npm run build — success, check chunk sizes
6. npm run test:contract — all paths match backend

7. Endpoint coverage audit:
   Count total API calls in frontend services:
   grep -rn "api\.\(get\|post\|put\|patch\|delete\|list\)(" src/features/ --include="*.service.ts" | wc -l
   Target: >= 250 (covering most of 311 backend endpoints)

8. Bundle size check:
   ls -la dist/assets/*.js | awk '{printf "%s %.1fKB\n", $9, $5/1024}'
   No chunk > 300KB

9. Feature directory count:
   ls -d src/features/*/ | wc -l
   Target: >= 28

10. GitHub Actions workflow exists:
    ls .github/workflows/web-ci.yml

OUTPUT: Summary table same format as Phase 1 final gate.

GIT (Codex only)
---
git add -A
git commit -m "chore(web): Phase 2 final verification gate — all checks green"
```

---

## Summary

| Prompt | Phase | Scope | Est. New Files |
|--------|-------|-------|---------------|
| WEB-P5-1 | Performance | Code splitting | 2 |
| WEB-P5-2 | Performance | React Query + memo | 0 (edits) |
| WEB-P5-3 | Performance | Dynamic i18n | 0 (edits) |
| WEB-P6-1 | Coverage | API path reconciliation | 0 (edits) |
| WEB-P6-2 | Coverage | Billing enhancements | 5 |
| WEB-P6-3 | Coverage | Documents completion | 4 |
| WEB-P6-4 | Coverage | Events & calendar | 3 |
| WEB-P6-5 | Coverage | Auth + recovery | 4 |
| WEB-P7-1 | Coverage | Question bank | 6 |
| WEB-P7-2 | Coverage | Rubrics | 6 |
| WEB-P7-3 | Coverage | Timetable generation | 3 |
| WEB-P7-4 | Coverage | Small modules | 4 |
| WEB-P7-5 | Coverage | Quiz engine | 3 |
| WEB-P8-1 | CI/CD | GitHub Actions | 2 |
| WEB-P8-2 | CI/CD | Pre-commit hooks | 3 |
| WEB-P9-1 | Integration | Contract tests | 2 |
| WEB-P9-2 | Integration | Docker-compose | 3 |
| WEB-P9-3 | Verification | Final gate | 0 |
| **Total** | **18 prompts** | | **~50 files** |
