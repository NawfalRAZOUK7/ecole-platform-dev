# Ecole Platform — Web Frontend TODO Checklist

> Generated: 2026-04-06
> Architecture: React 18 + Vite 6 + TypeScript 5.6 + TanStack React Query v5 + React Router v6
> Backend API surface: 54 router files, ~339 endpoint functions
> Frontend coverage: 23 feature modules, ~58 pages, 2 unit tests, 5 E2E tests

---

## Phase 0 — Infrastructure & Shared Foundation

> Goal: Build the reusable foundation that every subsequent phase depends on.

### P0-1: Form Library Integration
- [ ] Install `react-hook-form` + `@hookform/resolvers` + `zod`
- [ ] Create `web/src/shared/ui/FormField.tsx` — reusable wrapper (label, input, error message, i18n)
- [ ] Create `web/src/shared/ui/FormSelect.tsx` — select/dropdown with zod validation
- [ ] Create `web/src/shared/ui/FormTextarea.tsx` — textarea variant
- [ ] Create `web/src/shared/ui/FormCheckbox.tsx` — checkbox with label
- [ ] Create `web/src/shared/ui/FormDatePicker.tsx` — date input with Africa/Casablanca default
- [ ] Create `web/src/shared/validation/schemas.ts` — common zod schemas (email, phone, grade 0-20, MAD currency, moroccan-date)
- [ ] Refactor `RegisterPage.tsx` (494 lines) to use react-hook-form as proof of migration
- [ ] Refactor `ProfilePage.tsx` (499 lines) to use react-hook-form

### P0-2: Shared Component Library
- [ ] Create `web/src/shared/ui/DataTable.tsx` — sortable, paginated table (columns config, loading skeleton, empty state)
- [ ] Create `web/src/shared/ui/Pagination.tsx` — page controls with page size selector
- [ ] Create `web/src/shared/ui/ConfirmDialog.tsx` — modal confirmation (title, message, confirm/cancel, danger variant)
- [ ] Create `web/src/shared/ui/Skeleton.tsx` — content skeleton loader (line, card, table-row variants)
- [ ] Create `web/src/shared/ui/Badge.tsx` — status badge (success, warning, error, info, neutral)
- [ ] Create `web/src/shared/ui/Tabs.tsx` — accessible tab navigation
- [ ] Create `web/src/shared/ui/Breadcrumb.tsx` — route-aware breadcrumb
- [ ] Create `web/src/shared/ui/SearchInput.tsx` — debounced search with clear button
- [ ] Create `web/src/shared/ui/DateRangePicker.tsx` — date range selection
- [ ] Create `web/src/shared/ui/StatCard.tsx` — dashboard metric card (value, label, trend, icon)
- [ ] Export all from `web/src/shared/ui/index.ts` barrel file

### P0-3: Error Handling & Boundaries
- [ ] Create `web/src/shared/ui/ErrorBoundary.tsx` — React Error Boundary with fallback UI and retry
- [ ] Wrap each route's lazy-loaded page with `ErrorBoundary` in `App.tsx`
- [ ] Create `web/src/shared/ui/OfflineIndicator.tsx` — banner when `navigator.onLine` is false
- [ ] Create `web/src/shared/hooks/useNetworkStatus.ts` — online/offline hook
- [ ] Create `web/src/shared/ui/RetryButton.tsx` — retry failed queries
- [ ] Add global `QueryClient` error handler with toast notification
- [ ] Add `<Suspense fallback={<Skeleton />}>` to all lazy route boundaries in `App.tsx`

### P0-4: Accessibility Foundation
- [ ] Add `aria-label`, `aria-describedby`, `role` attributes to all shared UI components
- [ ] Add keyboard navigation to `DataTable` (arrow keys, Enter to select row)
- [ ] Add keyboard navigation to `Tabs` (arrow keys to switch, Enter/Space to activate)
- [ ] Add focus trap to `ConfirmDialog`
- [ ] Add skip-to-content link in `Layout.tsx`
- [ ] Add `aria-live="polite"` region for toast notifications
- [ ] Add `prefers-reduced-motion` media query respect in all transitions
- [ ] Audit and fix color contrast ratios (WCAG AA minimum 4.5:1)

### P0-5: Dark Mode
- [ ] Add `data-theme="dark"` toggle mechanism in `Layout.tsx`
- [ ] Define dark mode CSS variables in `styles.css` (all 13 existing variables need dark variants)
- [ ] Create `web/src/shared/hooks/useTheme.ts` — theme toggle hook with system preference detection
- [ ] Add theme toggle button to sidebar in `Layout.tsx`
- [ ] Update all hardcoded colors in `styles.css` (2,426 lines) to use CSS variables
- [ ] Test RTL + dark mode combination for Arabic locale

### P0-6: TypeScript Strict Improvements
- [ ] Create `web/src/shared/types/api.ts` — generic API response types (`PaginatedResponse<T>`, `ApiError`, `ApiSuccess<T>`)
- [ ] Create `web/src/shared/types/models.ts` — shared domain types (User, School, Class, Student, etc.)
- [ ] Create `web/src/shared/types/forms.ts` — form state types
- [ ] Create `web/src/shared/types/routes.ts` — typed route params
- [ ] Add type-safe route constants in `web/src/app/routes.ts`

---

## Phase 1 — Complete Partial Features + First Innovation Features

> Goal: Finish the most critical broken/partial features + build the 2 most-used innovation features.

### P1-1: Attendance Module (Currently: STUB — 22 lines total)
- [ ] Create `web/src/features/attendance/attendance.types.ts` — AttendanceRecord, JustificationStatus, BulkAttendancePayload
- [ ] Expand `attendance.service.ts` — add `markAttendance()`, `bulkMark()`, `getClassAttendance()`, `getStudentHistory()`
- [ ] Expand `useAttendance.ts` — add mutations for marking, bulk operations, justification approval
- [ ] Create `AttendancePage.tsx` — teacher view: class selector, date picker, student list with present/absent/late toggles
- [ ] Create `AttendanceHistoryPage.tsx` — student/parent view: calendar heatmap, stats summary
- [ ] Create `AttendanceBulkPage.tsx` — bulk mark by class with CSV import option
- [ ] Create `AttendanceAnalyticsPage.tsx` — charts: trends, absenteeism rates, alerts (connects to `/analytics/attendance/*`)
- [ ] Wire routes in `App.tsx`: `/attendance`, `/attendance/history`, `/attendance/bulk`, `/attendance/analytics`

### P1-2: Gradebook & Grades (Currently: NO frontend)
- [ ] Create `web/src/features/gradebook/` directory
- [ ] Create `gradebook.service.ts` — connects to `/gradebook/*` (5 endpoints)
- [ ] Create `useGradebook.ts` — queries + mutations for gradebook CRUD
- [ ] Create `GradebookPage.tsx` — teacher view: spreadsheet-like grade entry grid (students x assignments), weighted columns, 0-20 scale
- [ ] Create `GradeDetailPage.tsx` — single student grade breakdown with Recharts visualization
- [ ] Create `gradebook.types.ts` — GradebookEntry, WeightedColumn, GradeScale (0-20 Moroccan)
- [ ] Wire routes: `/gradebook`, `/gradebook/:studentId`

### P1-3: Invoices Enhancement (Currently: 70 lines, basic list only)
- [ ] Expand `invoices.service.ts` — add `downloadPdf()`, `markAsPaid()`, `uploadPaymentProof()`
- [ ] Expand `useInvoices.ts` — add payment proof mutation, PDF download
- [ ] Rewrite `InvoicesPage.tsx` — use DataTable, add filters (status, date range, amount), download button
- [ ] Create `InvoiceDetailPage.tsx` — full invoice view with line items, payment history, proof upload via FileUpload component
- [ ] Wire routes: `/invoices/:id`

### P1-4: Innovation — Micro-Budgets (Backend: 14 endpoints, Frontend: 0)
- [ ] Create `web/src/features/budgets/` directory
- [ ] Create `budgets.types.ts` — Budget, Allocation, BudgetRequest, Transaction
- [ ] Create `budgets.service.ts` — connects to `/budgets/*` (14 endpoints: envelopes, allocations, requests, transactions, analytics)
- [ ] Create `useBudgets.ts` — queries for list/detail, mutations for create/approve/reject
- [ ] Create `BudgetListPage.tsx` — list of class micro-budget envelopes with status badges
- [ ] Create `BudgetDetailPage.tsx` — single budget: allocations breakdown, transaction history, Recharts pie chart
- [ ] Create `BudgetRequestPage.tsx` — submit/approve/reject allocation requests
- [ ] Create `BudgetAnalyticsPage.tsx` — spending trends, remaining balance charts
- [ ] Wire routes: `/budgets`, `/budgets/:id`, `/budgets/requests`, `/budgets/analytics`
- [ ] Add sidebar nav entry for ADM, DIR roles

### P1-5: Innovation — Micro-Schools (Backend: 14 endpoints, Frontend: 0)
- [ ] Create `web/src/features/micro-schools/` directory
- [ ] Create `micro-schools.types.ts` — MicroSchool, MicroEnrollment, MicroResource, MicroProgress
- [ ] Create `micro-schools.service.ts` — connects to `/micro/*` (14 endpoints: CRUD, enrollments, payments, resources, progress)
- [ ] Create `useMicroSchools.ts` — queries + mutations
- [ ] Create `MicroSchoolListPage.tsx` — list/grid of micro-schools with filter by status
- [ ] Create `MicroSchoolDetailPage.tsx` — school info, enrolled students, resources, progress overview
- [ ] Create `MicroSchoolEnrollPage.tsx` — enrollment form with payment integration
- [ ] Create `MicroSchoolProgressPage.tsx` — student progress within micro-school, Recharts charts
- [ ] Wire routes: `/micro-schools`, `/micro-schools/:id`, `/micro-schools/:id/enroll`, `/micro-schools/:id/progress`
- [ ] Add sidebar nav entry for ADM, DIR, PAR roles

---

## Phase 2 — Remaining Partial Features + Next Innovation Features

> Goal: Complete all remaining partial features and add 2 more innovation modules.

### P2-1: Activities Enhancement (Currently: 69-line basic page)
- [ ] Expand `activities.service.ts` — add session management, bulk operations
- [ ] Create `ActivityDetailPage.tsx` — single activity: sessions list, student participation, grading
- [ ] Create `ActivityCalendarView.tsx` — calendar visualization of activity sessions
- [ ] Add activity type filters and search to `ActivitiesPage.tsx`
- [ ] Wire routes: `/activities/:id`

### P2-2: Content Management Enhancement (Currently: 103-line basic page)
- [ ] Expand `content.service.ts` — add progress tracking, content ordering, publish/draft toggle
- [ ] Create `ContentDetailPage.tsx` — single content item: view, progress bar, student analytics
- [ ] Create `ContentPlayerPage.tsx` — content consumption view (video player, document viewer, quiz embed)
- [ ] Add content type tabs (video, document, quiz, link) to `ContentPage.tsx`
- [ ] Wire routes: `/content/:id`, `/content/:id/play`

### P2-3: Feed Enhancement (Currently: 95-line basic page)
- [ ] Expand `feed.service.ts` — add WebSocket real-time updates, mark-as-read
- [ ] Create `web/src/features/feed/FeedItem.tsx` — individual feed entry (announcement, grade, attendance, etc.)
- [ ] Add real-time badge count in sidebar navigation
- [ ] Add infinite scroll / load more to `FeedPage.tsx`
- [ ] Add feed filters (type, date, read/unread)

### P2-4: Innovation — Skills Passport (Backend: 12 endpoints, Frontend: 0)
- [ ] Create `web/src/features/skills/` directory
- [ ] Create `skills.types.ts` — SkillDimension, Milestone, SkillEvaluation, SkillPassport
- [ ] Create `skills.service.ts` — connects to `/skills/*` (12 endpoints: dimensions, milestones, evaluations, passports, analytics)
- [ ] Create `useSkills.ts` — queries + mutations
- [ ] Create `SkillsOverviewPage.tsx` — radar chart of student skill dimensions (Recharts)
- [ ] Create `SkillPassportPage.tsx` — printable/exportable student skill passport
- [ ] Create `SkillEvaluationPage.tsx` — teacher evaluation form per student per dimension
- [ ] Create `SkillAnalyticsPage.tsx` — class-wide skill analytics, comparison charts
- [ ] Wire routes: `/skills`, `/skills/passport/:studentId`, `/skills/evaluate`, `/skills/analytics`
- [ ] Add sidebar nav entry for TCH, DIR, PAR, STD roles

### P2-5: Innovation — MEN Compliance (Backend: 12 endpoints, Frontend: 0)
- [ ] Create `web/src/features/compliance/` directory
- [ ] Create `compliance.types.ts` — CurriculumMapping, ComplianceReport, ComplianceDashboard
- [ ] Create `compliance.service.ts` — connects to `/compliance/*` (12 endpoints: mappings, dashboards, reports)
- [ ] Create `useCompliance.ts` — queries + mutations
- [ ] Create `ComplianceDashboardPage.tsx` — MEN compliance overview with gauge charts, gap analysis
- [ ] Create `CurriculumMappingPage.tsx` — map courses to MEN curriculum standards
- [ ] Create `ComplianceReportPage.tsx` — generate and export MEN compliance reports
- [ ] Wire routes: `/compliance`, `/compliance/mapping`, `/compliance/reports`
- [ ] Add sidebar nav entry for ADM, DIR roles

---

## Phase 3 — Final Innovation Features + Dark Mode + Accessibility

> Goal: Complete all innovation features and add full polish.

### P3-1: Innovation — Offline Sync (Backend: 10 endpoints, Frontend: 0)
- [ ] Create `web/src/features/sync/` directory
- [ ] Create `sync.types.ts` — SyncDevice, SyncQueue, SyncConflict, SyncCheckpoint
- [ ] Create `sync.service.ts` — connects to `/sync/*` (10 endpoints: device registration, queue push/pull, conflicts, checkpoints)
- [ ] Create `useSync.ts` — queries + mutations + background sync logic
- [ ] Create `SyncStatusPage.tsx` — device list, sync status, last checkpoint, conflict count
- [ ] Create `SyncConflictsPage.tsx` — list conflicts with resolution UI (keep local / keep remote / merge)
- [ ] Create `SyncSettingsPage.tsx` — configure sync interval, data scope, device management
- [ ] Integrate Service Worker for offline queue management
- [ ] Wire routes: `/sync`, `/sync/conflicts`, `/sync/settings`
- [ ] Add sync status indicator in `Layout.tsx` header

### P3-2: Innovation — Financial Health (Backend: 12 endpoints, Frontend: 0)
- [ ] Create `web/src/features/financial-health/` directory
- [ ] Create `financial-health.types.ts` — RetentionMetric, CashflowData, CostPerStudent, Snapshot
- [ ] Create `financial-health.service.ts` — connects to `/financial-health/*` (12 endpoints: retention, cashflow, cost-per-student, snapshots, exports)
- [ ] Create `useFinancialHealth.ts` — queries
- [ ] Create `FinancialDashboardPage.tsx` — multi-chart dashboard: retention trend, cashflow waterfall, cost-per-student comparison
- [ ] Create `FinancialSnapshotsPage.tsx` — historical snapshots list with export
- [ ] Create `FinancialExportPage.tsx` — generate PDF/Excel financial reports
- [ ] Wire routes: `/financial-health`, `/financial-health/snapshots`, `/financial-health/export`
- [ ] Add sidebar nav entry for ADM, SYS roles

### P3-3: Component Splitting (Large Files)
- [ ] Split `QuizBuilderPage.tsx` (711 lines) into: `QuizBuilderForm`, `QuestionEditor`, `QuestionList`, `QuizPreview`
- [ ] Split `DocumentsPage.tsx` (646 lines) into: `DocumentList`, `DocumentUpload`, `DocumentViewer`, `DocumentFilters`
- [ ] Split `CalendarPage.tsx` (539 lines) + `shared.tsx` (610 lines) into: `CalendarGrid`, `EventForm`, `EventDetail`, `CalendarFilters`
- [ ] Split `ContentLibraryPage.tsx` (534 lines) into: `LibraryGrid`, `ContentCard`, `ContentFilters`, `ContentUploadModal`
- [ ] Split `ProfilePage.tsx` (499 lines) into: `ProfileInfo`, `ProfileForm`, `AvatarUpload`, `SecuritySettings`
- [ ] Split `RegisterPage.tsx` (494 lines) into: `RegisterSteps`, `PersonalInfoStep`, `SchoolInfoStep`, `VerificationStep`
- [ ] Split `TimetablePage.tsx` (470 lines) into: `TimetableGrid`, `SlotEditor`, `TimetableFilters`

### P3-4: Dark Mode Implementation
- [ ] Define all dark CSS variables in `styles.css` under `[data-theme="dark"]`
- [ ] Update `Layout.tsx` to include theme toggle in header
- [ ] Replace all hardcoded color values in `styles.css` with CSS variable references
- [ ] Test all 23 feature pages in dark mode
- [ ] Test RTL (Arabic) + dark mode combination
- [ ] Store theme preference in `localStorage`

### P3-5: Full Accessibility Audit
- [ ] Add ARIA labels to all 23 feature page list views
- [ ] Add ARIA labels to all form inputs across all pages
- [ ] Add keyboard navigation to sidebar menu in `Layout.tsx`
- [ ] Add focus management on route changes
- [ ] Add `alt` text to all images and icons
- [ ] Add screen reader announcements for async operations (loading, success, error)
- [ ] Test with screen reader (axe-core automated + manual VoiceOver/NVDA)

---

## Phase 4 — Testing & Verification

> Goal: Comprehensive test coverage and final verification.

### P4-1: Unit Test Infrastructure
- [ ] Create `web/tests/utils/render.tsx` — custom render with providers (QueryClient, Router, AuthContext, i18n)
- [ ] Create `web/tests/utils/mocks.ts` — MSW handlers for all API endpoints
- [ ] Install `msw` for API mocking in tests
- [ ] Create `web/tests/utils/factories.ts` — test data factories for all domain models

### P4-2: Shared Component Tests
- [ ] Test `DataTable` — renders columns, sorts, paginates, handles empty state
- [ ] Test `FormField` — validation, error display, i18n labels
- [ ] Test `ConfirmDialog` — open/close, confirm/cancel callbacks, keyboard trap
- [ ] Test `ErrorBoundary` — catches errors, shows fallback, retry works
- [ ] Test `Skeleton` — renders all variants
- [ ] Test `Pagination` — page change, size change, boundary conditions
- [ ] Test `SearchInput` — debounce, clear, submit

### P4-3: Feature Page Tests (Critical Paths)
- [ ] Test `AttendancePage` — load students, mark present/absent, submit
- [ ] Test `GradebookPage` — load grid, enter grades (0-20 validation), save
- [ ] Test `InvoiceDetailPage` — load invoice, upload payment proof
- [ ] Test `BudgetListPage` — load budgets, filter, navigate to detail
- [ ] Test `MicroSchoolListPage` — load schools, filter, navigate to detail
- [ ] Test `SkillsOverviewPage` — load dimensions, render radar chart
- [ ] Test `ComplianceDashboardPage` — load metrics, render gauges
- [ ] Test `FinancialDashboardPage` — load data, render charts
- [ ] Test auth flow — login, 2FA, token refresh, logout

### P4-4: E2E Test Expansion
- [ ] Add E2E: Teacher marks attendance for a class
- [ ] Add E2E: Teacher enters grades in gradebook
- [ ] Add E2E: Parent views invoice and uploads payment proof
- [ ] Add E2E: Admin creates micro-budget and approves request
- [ ] Add E2E: Director views compliance dashboard
- [ ] Add E2E: Student views skill passport
- [ ] Add E2E: Dark mode toggle persists across navigation
- [ ] Add E2E: Language switch (FR → AR) applies RTL correctly

### P4-5: Final Verification
- [ ] Run `tsc --noEmit` — zero TypeScript errors
- [ ] Run `eslint .` — zero lint errors
- [ ] Run `vitest run --coverage` — minimum 70% coverage on shared/ and services/
- [ ] Run `playwright test` — all E2E tests pass
- [ ] Run `vite build` — production build succeeds with no warnings
- [ ] Verify all 23+ feature routes render without errors
- [ ] Verify all 6 innovation feature pages connect to backend APIs correctly
- [ ] Verify dark mode on all pages
- [ ] Verify RTL (Arabic) on all pages
- [ ] Verify responsive layout at 768px breakpoint on all pages
- [ ] Lighthouse audit: Performance > 80, Accessibility > 90, Best Practices > 90

---

## Summary Statistics

| Phase | Tasks | New Files | Scope |
|-------|-------|-----------|-------|
| P0 — Infrastructure | 6 groups, ~48 items | ~25 new components | Foundation |
| P1 — Critical + Innovation×2 | 5 groups, ~45 items | ~30 new files | Attendance, Gradebook, Invoices, Budgets, Micro-Schools |
| P2 — Partial + Innovation×2 | 5 groups, ~40 items | ~25 new files | Activities, Content, Feed, Skills, Compliance |
| P3 — Final Innovation + Polish | 5 groups, ~45 items | ~20 new files | Sync, Financial Health, Split, Dark Mode, A11y |
| P4 — Testing & Verification | 5 groups, ~40 items | ~15 test files | Unit, Component, Feature, E2E, Verification |
| **Total** | **26 groups, ~218 items** | **~115 new files** | **Full frontend completion** |
