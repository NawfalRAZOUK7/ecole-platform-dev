# Ecole Platform — Mobile (Flutter) TODO Checklist

> Generated: 2026-04-10
> Architecture: Flutter 3.5+ / Dart 3.5 / Riverpod / go_router / Dio / SQLite
> Current state: 110 Dart files, 27,199 LOC, 19 feature modules, 38 routes, 0 tests
> Target: Full parity with web frontend (all features, dark mode, a11y, tests)

---

## Phase M0 — Flutter Project Bootstrap & Shared Foundation

> Goal: Initialize native platforms, create shared widgets, design system, and test infra.

### M0-1: Flutter Native Platform Setup
- [ ] Run `flutter create --platforms=android,ios .` in mobile/ to generate android/ and ios/ directories
- [ ] Configure Android: set `minSdkVersion 23`, `targetSdkVersion 34`, `applicationId: com.ecole.platform`
- [ ] Configure iOS: set deployment target iOS 15+, bundle ID `com.ecole.platform`
- [ ] Add Firebase config files: `google-services.json` (Android), `GoogleService-Info.plist` (iOS)
- [ ] Verify: `flutter run` on Android emulator and iOS simulator
- [ ] Add `.gitignore` entries for build artifacts

### M0-2: Design System & UI Tokens
- [ ] Create `lib/shared/ui/tokens/colors.dart` — app color palette matching web CSS variables (light + dark)
- [ ] Create `lib/shared/ui/tokens/spacing.dart` — consistent spacing scale (4, 8, 12, 16, 24, 32, 48)
- [ ] Create `lib/shared/ui/tokens/typography.dart` — text styles (heading1-4, body, caption, label)
- [ ] Create `lib/shared/ui/tokens/radii.dart` — border radius constants (sm: 4, md: 8, lg: 12, xl: 16)
- [ ] Create `lib/shared/ui/app_theme.dart` — ThemeData for light mode using tokens
- [ ] Create `lib/shared/ui/app_theme_dark.dart` — ThemeData for dark mode using tokens
- [ ] Refactor `main.dart` to use `app_theme.dart` instead of inline ThemeData

### M0-3: Shared Widget Library
- [ ] Create `lib/shared/widgets/app_data_table.dart` — sortable, paginated table (columns config, loading skeleton)
- [ ] Create `lib/shared/widgets/app_badge.dart` — status badge (success, warning, error, info, neutral)
- [ ] Create `lib/shared/widgets/app_stat_card.dart` — metric card (value, label, trend icon)
- [ ] Create `lib/shared/widgets/app_confirm_dialog.dart` — confirmation dialog (title, message, confirm/cancel, danger variant)
- [ ] Create `lib/shared/widgets/app_skeleton.dart` — shimmer loading placeholder (line, card, table-row)
- [ ] Create `lib/shared/widgets/app_empty_state.dart` — empty state with icon, title, subtitle, action button
- [ ] Create `lib/shared/widgets/app_error_widget.dart` — error state with retry button
- [ ] Create `lib/shared/widgets/app_form_field.dart` — text field with label, validation, error message
- [ ] Create `lib/shared/widgets/app_date_picker.dart` — date picker with Africa/Casablanca default
- [ ] Create `lib/shared/widgets/app_currency_text.dart` — formatted MAD currency display
- [ ] Export all from `lib/shared/widgets/widgets.dart` barrel file

### M0-4: Dark Mode Support
- [ ] Add `themeProvider` StateProvider to app providers (light/dark/system)
- [ ] Update `main.dart` MaterialApp: `theme: appLightTheme`, `darkTheme: appDarkTheme`, `themeMode: themeProvider`
- [ ] Add theme toggle to profile/settings screen
- [ ] Store preference in secure storage
- [ ] Audit all 19 existing screens for hardcoded colors — replace with `Theme.of(context)` references

### M0-5: i18n Expansion
- [ ] Current: Map-based i18n in `app_localizations.dart` (1,179 lines) — covers Phase 10C screens only
- [ ] Add missing translations for ALL existing 19 feature screens
- [ ] Add translations for all new features to be built (budgets, micro-schools, skills, etc.)
- [ ] Add Arabic (ar) RTL support: set `Directionality` based on locale
- [ ] Total target: ~2000+ translation keys across 3 locales (fr, ar, en)

### M0-6: Test Infrastructure
- [ ] Create `mobile/test/` directory
- [ ] Create `test/helpers/pump_app.dart` — test helper that wraps widgets with ProviderScope, MaterialApp, theme, i18n
- [ ] Create `test/helpers/mock_repositories.dart` — mock implementations for all 13 repositories
- [ ] Create `test/helpers/factories.dart` — test data factories for all domain entities
- [ ] Add `mockito` and `mocktail` to dev_dependencies
- [ ] Create first smoke test: `test/app_test.dart` — app launches without crash

---

## Phase M1 — Complete Partial Features + First Innovation

> Goal: Enhance existing features to full parity with web, build first 2 innovation modules.

### M1-1: Attendance Enhancement
- [ ] Current mobile: Teacher has `attendance_screen.dart` in teacher/ — basic marking only
- [ ] Create `lib/domain/entities/attendance.dart` — AttendanceRecord, BulkPayload, AttendanceTrend, Alert
- [ ] Create `lib/domain/repositories/attendance_repository.dart` — abstract interface
- [ ] Create `lib/data/repositories_impl/attendance_repository_impl.dart` — all 8 endpoints
- [ ] Create `lib/data/local_store/attendance_store.dart` — SQLite offline cache for attendance records
- [ ] Create `lib/features/attendance/attendance_provider.dart` — Riverpod state
- [ ] Create `lib/features/attendance/attendance_history_screen.dart` — student/parent view: calendar heatmap
- [ ] Create `lib/features/attendance/attendance_analytics_screen.dart` — director view: trends charts (fl_chart)
- [ ] Add routes: `/attendance/history`, `/attendance/analytics`

### M1-2: Gradebook Module (New)
- [ ] Create `lib/domain/entities/gradebook.dart` — GradebookGrid, GradebookEntry, GradebookColumn, WeightedSummary
- [ ] Create `lib/domain/repositories/gradebook_repository.dart`
- [ ] Create `lib/data/repositories_impl/gradebook_repository_impl.dart` — all 5+ endpoints
- [ ] Create `lib/features/gradebook/gradebook_provider.dart`
- [ ] Create `lib/features/gradebook/gradebook_screen.dart` — teacher: scrollable grade grid (students × assignments, 0-20 scale)
- [ ] Create `lib/features/gradebook/grade_detail_screen.dart` — student/parent: grade breakdown with fl_chart
- [ ] Create `lib/features/gradebook/transcript_screen.dart` — full student transcript
- [ ] Add providers to `app/providers.dart`
- [ ] Add routes: `/gradebook`, `/gradebook/student/:id`, `/gradebook/transcript/:id`

### M1-3: Invoices Enhancement
- [ ] Current: `invoices_screen.dart` (343 lines) — basic list
- [ ] Expand `invoice_repository_impl.dart` — add payment proof upload, PDF download, payment creation
- [ ] Create `lib/features/invoices/invoice_detail_screen.dart` — full invoice with line items, payment history, proof upload
- [ ] Add route: `/invoices/:id`

### M1-4: Innovation — Micro-Budgets
- [ ] Create `lib/domain/entities/budget.dart`
- [ ] Create `lib/domain/repositories/budget_repository.dart`
- [ ] Create `lib/data/repositories_impl/budget_repository_impl.dart` — all 14 endpoints
- [ ] Create `lib/features/budgets/budget_provider.dart`
- [ ] Create `lib/features/budgets/budget_list_screen.dart` — list with status badges
- [ ] Create `lib/features/budgets/budget_detail_screen.dart` — allocations, transactions, pie chart
- [ ] Create `lib/features/budgets/budget_request_screen.dart` — submit/approve/reject requests
- [ ] Add routes: `/budgets`, `/budgets/:id`, `/budgets/requests`
- [ ] Add nav entry for ADM, DIR

### M1-5: Innovation — Micro-Schools
- [ ] Create `lib/domain/entities/micro_school.dart`
- [ ] Create `lib/domain/repositories/micro_school_repository.dart`
- [ ] Create `lib/data/repositories_impl/micro_school_repository_impl.dart` — all 14 endpoints
- [ ] Create `lib/features/micro-schools/micro_school_provider.dart`
- [ ] Create `lib/features/micro-schools/micro_school_list_screen.dart` — card grid
- [ ] Create `lib/features/micro-schools/micro_school_detail_screen.dart` — tabs: students, resources, progress
- [ ] Create `lib/features/micro-schools/micro_school_enroll_screen.dart`
- [ ] Add routes: `/micro-schools`, `/micro-schools/:id`, `/micro-schools/:id/enroll`

---

## Phase M2 — More Innovation + Feature Enhancement

### M2-1: Innovation — Skills Passport
- [ ] Full module: entity, repo interface, repo impl (12 endpoints), provider
- [ ] `skills_overview_screen.dart` — radar chart (fl_chart RadarChart)
- [ ] `skill_passport_screen.dart` — printable/exportable passport (share_plus for PDF export)
- [ ] `skill_evaluation_screen.dart` — teacher evaluation form
- [ ] `skill_analytics_screen.dart` — class-wide analytics
- [ ] Routes: `/skills`, `/skills/passport/:id`, `/skills/evaluate`, `/skills/analytics`

### M2-2: Innovation — MEN Compliance
- [ ] Full module: entity, repo, impl (12 endpoints), provider
- [ ] `compliance_dashboard_screen.dart` — gauge charts, gap analysis
- [ ] `curriculum_mapping_screen.dart` — map courses to MEN standards
- [ ] `compliance_report_screen.dart` — generate/export reports
- [ ] Routes: `/compliance`, `/compliance/mapping`, `/compliance/reports`

### M2-3: Innovation — Offline Sync Enhancement
- [ ] Current mobile has basic OfflineQueue + ConnectivityService
- [ ] Expand `lib/data/local_store/offline_queue.dart` to handle all 10 sync endpoints
- [ ] Create `lib/features/sync/sync_provider.dart`
- [ ] Create `lib/features/sync/sync_status_screen.dart` — device list, sync indicator
- [ ] Create `lib/features/sync/sync_conflicts_screen.dart` — conflict resolution UI
- [ ] Add sync status indicator in `ShellScreen` app bar
- [ ] Routes: `/sync`, `/sync/conflicts`

### M2-4: Innovation — Financial Health
- [ ] Full module: entity, repo, impl (12 endpoints), provider
- [ ] `financial_dashboard_screen.dart` — multi-chart: retention, cashflow, cost-per-student
- [ ] `financial_snapshots_screen.dart` — historical snapshots
- [ ] `financial_export_screen.dart` — PDF/CSV export
- [ ] Routes: `/financial-health`, `/financial-health/snapshots`

### M2-5: Billing Enhancements
- [ ] Expand invoice_repository — add sibling policy, late fee policy, payment plans
- [ ] Create `lib/features/billing/sibling_policy_screen.dart`
- [ ] Create `lib/features/billing/late_fee_policy_screen.dart`
- [ ] Create `lib/features/billing/payment_plans_screen.dart`
- [ ] Routes: `/billing/sibling-policy`, `/billing/late-fees`, `/billing/payment-plans`

---

## Phase M3 — Supporting Features + Polish

### M3-1: Question Bank
- [ ] Full module: entity, repo, impl (5 endpoints), provider
- [ ] `question_bank_screen.dart`, `import_screen.dart`, `generate_quiz_screen.dart`
- [ ] Routes: `/question-bank`, `/question-bank/import`, `/question-bank/generate`

### M3-2: Rubrics
- [ ] Full module: entity, repo, impl (6 endpoints), provider
- [ ] `rubrics_list_screen.dart`, `rubric_editor_screen.dart`, `rubric_grading_screen.dart`
- [ ] Routes: `/rubrics`, `/rubrics/:id/edit`, `/rubrics/:id/grade`

### M3-3: Timetable Generation
- [ ] Expand timetable feature — add constraints, generation, preview, apply
- [ ] `timetable_constraints_screen.dart`, `timetable_generate_screen.dart`
- [ ] Routes: `/timetable/constraints`, `/timetable/generate`

### M3-4: Recovery Flow
- [ ] Create `lib/features/auth/forgot_password_screen.dart`
- [ ] Create `lib/features/auth/reset_password_screen.dart`
- [ ] Routes: `/forgot-password`, `/reset-password`

### M3-5: Remaining Small Features
- [ ] GDPR: `gdpr_screen.dart` (data export/deletion request) → `/settings/privacy`
- [ ] Feature Toggles: `feature_toggles_screen.dart` → `/admin/features`
- [ ] School Settings: `school_settings_screen.dart` → `/admin/school`
- [ ] Report Scheduling: expand reports feature with schedule CRUD
- [ ] Submission files: expand submissions feature with file upload/preview

### M3-6: Component Splitting (Large Files)
- [ ] Split `documents_screen.dart` (1,679 lines) → DocumentList, DocumentUpload, DocumentPreview, DocumentFilters
- [ ] Split `quiz_player_screen.dart` (1,194 lines) → QuizQuestion, QuizTimer, QuizResults, QuizProgress
- [ ] Split `content_library_screen.dart` (931 lines) → LibraryGrid, ContentCard, UploadForm, ContentFilters
- [ ] Split `analytics_summary_screen.dart` (876 lines) → AnalyticsCards, AttendanceChart, GradesChart, BillingChart
- [ ] Split `reports_screen.dart` (827 lines) → ReportList, ReportGenerator, ScheduleManager

### M3-7: Accessibility
- [ ] Add `Semantics` widgets to all custom widgets
- [ ] Add `excludeSemantics` to decorative images
- [ ] Test with TalkBack (Android) and VoiceOver (iOS)
- [ ] Ensure minimum touch target size 48×48
- [ ] Add `textScaleFactor` support for large text

---

## Phase M4 — Testing & Verification

### M4-1: Unit Tests — Domain & Data
- [ ] Test all 13+ repository implementations (mock Dio responses)
- [ ] Test all domain entities (serialization, validation)
- [ ] Test CacheStore, OfflineQueue, each local store
- [ ] Test ApiClient (retry logic, 401 refresh, error parsing)
- [ ] Target: ~50 unit tests

### M4-2: Widget Tests — Shared Components
- [ ] Test AppDataTable, AppBadge, AppStatCard, AppConfirmDialog, AppSkeleton
- [ ] Test AppFormField validation, error display
- [ ] Test search_filter_bar debounce, clear
- [ ] Target: ~20 widget tests

### M4-3: Widget Tests — Feature Screens
- [ ] Test AttendanceScreen — load students, toggle status, submit
- [ ] Test GradebookScreen — load grid, enter grades (0-20)
- [ ] Test BudgetListScreen — load budgets, navigate to detail
- [ ] Test SkillsOverviewScreen — load dimensions, render radar chart
- [ ] Test feed, notifications, invoices, documents screens
- [ ] Target: ~30 widget tests

### M4-4: Integration Tests
- [ ] Create `integration_test/` directory
- [ ] Test: login → navigate to feed → view notification → logout
- [ ] Test: teacher marks attendance → parent views history
- [ ] Test: dark mode toggle persistence
- [ ] Test: language switch → RTL layout

### M4-5: Final Verification
- [ ] `flutter analyze` — 0 issues
- [ ] `flutter test` — all tests pass
- [ ] `flutter build apk --release` — successful Android build
- [ ] `flutter build ios --release --no-codesign` — successful iOS build
- [ ] Verify all routes render without error
- [ ] Verify dark mode on all screens
- [ ] Verify RTL (Arabic) on all screens
- [ ] Verify offline mode (airplane mode) graceful degradation

---

## Summary

| Phase | Tasks | New Files | Scope |
|-------|-------|-----------|-------|
| M0 — Foundation | 6 groups, ~45 items | ~20 files | Bootstrap, design system, widgets, dark mode, i18n, tests |
| M1 — Critical + Innovation×2 | 5 groups, ~40 items | ~30 files | Attendance, Gradebook, Invoices, Budgets, Micro-Schools |
| M2 — Innovation×4 + Billing | 5 groups, ~35 items | ~25 files | Skills, Compliance, Sync, Financial Health, Billing |
| M3 — Supporting + Polish | 7 groups, ~35 items | ~20 files | QuestionBank, Rubrics, TimetableGen, Recovery, Small, Split, A11y |
| M4 — Testing | 5 groups, ~25 items | ~15 files | Unit, Widget, Feature, Integration, Verification |
| **Total** | **28 groups, ~180 items** | **~110 new files** | **Full parity with web** |
