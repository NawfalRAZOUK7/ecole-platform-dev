# Ecole Platform — Mobile (Flutter) Detailed Prompts

> Generated: 2026-04-10
> Usage: Copy-paste into Codex, Claude Code, or any AI tool.
> Architecture: Flutter 3.5+ / Dart 3.5 / Riverpod / go_router / Dio / SQLite
> 28 prompts following: CONTEXT → TASK → CONSTRAINTS → OUTPUT → VERIFY → GIT

---

## PHASE M0 — Flutter Project Bootstrap & Shared Foundation

---

### MOB-P0-1 — Flutter Native Platform Setup

```
CONTEXT
-------
Project: ecole-platform-dev/mobile/ (Flutter, Dart 3.5)
Current state: lib/ has 110 Dart files but NO android/ or ios/ native directories.
The project was created as lib-only — needs native platform scaffolding to build.
pubspec.yaml: name ecole_platform, uses Firebase, local_auth, sqflite, etc.

TASK
----
1. In the mobile/ directory, generate native platforms:
   cd mobile
   flutter create --platforms=android,ios --org com.ecole --project-name ecole_platform .

   Note: This will NOT overwrite existing lib/ files — it only creates android/ and ios/.

2. Configure Android (mobile/android/app/build.gradle.kts or build.gradle):
   - minSdk = 23 (Android 6.0+, required by flutter_secure_storage + local_auth)
   - targetSdk = 34
   - applicationId = "com.ecole.platform"
   - versionCode = 1, versionName = "0.1.0"
   - Add multidex support: multiDexEnabled = true
   - Add internet permission to AndroidManifest.xml (if not present)

3. Configure iOS (mobile/ios/Runner/Info.plist):
   - Deployment target: iOS 15.0 (in Podfile: platform :ios, '15.0')
   - Bundle identifier: com.ecole.platform
   - Add privacy keys for camera, photo library, biometrics:
     NSCameraUsageDescription, NSPhotoLibraryUsageDescription,
     NSFaceIDUsageDescription, NSLocalNetworkUsageDescription

4. Add Firebase placeholder configs:
   - Create empty mobile/android/app/google-services.json with placeholder content
   - Create empty mobile/ios/Runner/GoogleService-Info.plist with placeholder
   - These will be replaced with real configs at deployment time

5. Add to mobile/.gitignore:
   build/
   android/.gradle/
   android/app/build/
   ios/Pods/
   ios/.symlinks/
   *.iml
   .dart_tool/

6. Run: cd mobile && flutter pub get
   Verify all dependencies resolve.

CONSTRAINTS
-----------
- Do NOT modify any existing Dart files in lib/
- Do NOT remove any existing files
- If flutter create fails because some files exist, only create the missing directories manually

VERIFY
------
cd mobile
flutter pub get                     # All deps resolve
flutter analyze                     # Zero errors (warnings ok for now)
flutter build apk --debug          # Android debug build succeeds
# iOS build: flutter build ios --debug --no-codesign (only on macOS)

GIT (Codex only)
---
git add mobile/android/ mobile/ios/ mobile/.gitignore mobile/pubspec.lock
git commit -m "feat(mobile): initialize Android and iOS native platforms"
```

---

### MOB-P0-2 — Design System & UI Tokens

```
CONTEXT
-------
Project: ecole-platform-dev/mobile/
Current theme: inline ThemeData in main.dart (lines 187-211) with hardcoded Color(0xFF2563EB)
shared/ui/tokens/ directory exists but is empty
Web CSS variables: --color-primary (#2563EB), --color-bg (#FFFFFF), --color-surface (#F9FAFB),
  --color-border (#E5E7EB), --color-text (#1F2937), --color-text-secondary (#6B7280), etc.

TASK
----
1. Create mobile/lib/shared/ui/tokens/colors.dart:
   class AppColors {
     // Light theme colors (matching web CSS variables)
     static const primary = Color(0xFF2563EB);
     static const primaryLight = Color(0xFF93C5FD);
     static const primaryDark = Color(0xFF1E40AF);
     static const secondary = Color(0xFF7C3AED);
     static const accent = Color(0xFFF59E0B);
     static const success = Color(0xFF10B981);
     static const warning = Color(0xFFF59E0B);
     static const error = Color(0xFFEF4444);
     static const info = Color(0xFF3B82F6);
     static const background = Color(0xFFFFFFFF);
     static const surface = Color(0xFFF9FAFB);
     static const border = Color(0xFFE5E7EB);
     static const text = Color(0xFF1F2937);
     static const textSecondary = Color(0xFF6B7280);

     // Dark theme colors (matching web dark mode)
     static const darkPrimary = Color(0xFF6B8AFF);
     static const darkBackground = Color(0xFF0F172A);
     static const darkSurface = Color(0xFF1E293B);
     static const darkBorder = Color(0xFF334155);
     static const darkText = Color(0xFFF1F5F9);
     static const darkTextSecondary = Color(0xFF94A3B8);
   }

2. Create mobile/lib/shared/ui/tokens/spacing.dart:
   class AppSpacing {
     static const double xs = 4;
     static const double sm = 8;
     static const double md = 12;
     static const double base = 16;
     static const double lg = 24;
     static const double xl = 32;
     static const double xxl = 48;
   }

3. Create mobile/lib/shared/ui/tokens/typography.dart:
   class AppTypography {
     static const heading1 = TextStyle(fontSize: 28, fontWeight: FontWeight.bold, fontFamily: 'Inter');
     static const heading2 = TextStyle(fontSize: 24, fontWeight: FontWeight.bold, fontFamily: 'Inter');
     static const heading3 = TextStyle(fontSize: 20, fontWeight: FontWeight.w600, fontFamily: 'Inter');
     static const heading4 = TextStyle(fontSize: 18, fontWeight: FontWeight.w600, fontFamily: 'Inter');
     static const body = TextStyle(fontSize: 16, fontWeight: FontWeight.normal, fontFamily: 'Inter');
     static const bodySmall = TextStyle(fontSize: 14, fontWeight: FontWeight.normal, fontFamily: 'Inter');
     static const caption = TextStyle(fontSize: 12, fontWeight: FontWeight.normal, fontFamily: 'Inter');
     static const label = TextStyle(fontSize: 14, fontWeight: FontWeight.w500, fontFamily: 'Inter');
   }

4. Create mobile/lib/shared/ui/tokens/radii.dart:
   class AppRadii {
     static const double sm = 4;
     static const double md = 8;
     static const double lg = 12;
     static const double xl = 16;
     static const double full = 999;
   }

5. Create mobile/lib/shared/ui/app_theme.dart:
   ThemeData appLightTheme = ThemeData(
     colorSchemeSeed: AppColors.primary,
     useMaterial3: true,
     fontFamily: 'Inter',
     scaffoldBackgroundColor: AppColors.background,
     appBarTheme: ...,
     cardTheme: ...,
     inputDecorationTheme: ...,
     // Use all token values
   );

6. Create mobile/lib/shared/ui/app_theme_dark.dart:
   ThemeData appDarkTheme = ThemeData(
     brightness: Brightness.dark,
     colorSchemeSeed: AppColors.darkPrimary,
     useMaterial3: true,
     fontFamily: 'Inter',
     scaffoldBackgroundColor: AppColors.darkBackground,
     // Use all dark token values
   );

7. Add themeProvider to mobile/lib/app/providers.dart:
   final themeModeProvider = StateProvider<ThemeMode>((ref) => ThemeMode.system);

8. Update mobile/lib/main.dart to use themes:
   Replace inline ThemeData with: theme: appLightTheme, darkTheme: appDarkTheme,
   themeMode: ref.watch(themeModeProvider)

CONSTRAINTS
-----------
- Colors MUST match web CSS variables exactly for brand consistency
- Do NOT change any functional behavior
- All hardcoded colors in main.dart must be replaced with token references

VERIFY
------
cd mobile
flutter analyze
flutter build apk --debug

GIT (Codex only)
---
git add mobile/lib/shared/ui/ mobile/lib/main.dart mobile/lib/app/providers.dart
git commit -m "feat(mobile): add design system tokens, light/dark themes matching web CSS variables"
```

---

### MOB-P0-3 — Shared Widget Library

```
CONTEXT
-------
Project: ecole-platform-dev/mobile/
Current shared widgets: only search_filter_bar.dart (167 lines)
Web has: DataTable, Badge, StatCard, ConfirmDialog, Skeleton, EmptyState, ErrorBoundary, FormField, etc.
Mobile needs equivalents for Flutter.

TASK
----
Create these files in mobile/lib/shared/widgets/:

1. app_data_table.dart (~120 lines):
   - Generic AppDataTable<T> widget
   - Props: columns (List<AppColumn<T>>), rows (List<T>), isLoading, emptyMessage, onRowTap
   - AppColumn<T>: {String header, Widget Function(T) cellBuilder, double? width, bool sortable}
   - Loading state: show AppSkeleton rows
   - Empty state: show AppEmptyState
   - Uses DataTable or custom ListView.builder with header

2. app_badge.dart (~40 lines):
   - Props: String label, AppBadgeVariant variant (success/warning/error/info/neutral)
   - Small colored Container with Text, borderRadius, appropriate color per variant

3. app_stat_card.dart (~60 lines):
   - Props: String label, String value, IconData? icon, TrendDirection? trend, double? trendValue
   - Card with large value text, small label, optional trend arrow (up green, down red)

4. app_confirm_dialog.dart (~80 lines):
   - Static method: show(context, {title, message, confirmLabel, cancelLabel, variant, onConfirm})
   - Uses AlertDialog with customized actions
   - Danger variant: red confirm button
   - Returns Future<bool>

5. app_skeleton.dart (~50 lines):
   - Props: SkeletonVariant (line/card/tableRow/circle), width, height, count
   - Shimmer animation effect using AnimatedContainer or shimmer package
   - CSS-animation-like pulse effect

6. app_empty_state.dart (~40 lines):
   - Props: IconData icon, String title, String? subtitle, Widget? action
   - Centered column with icon, title, subtitle, optional action button

7. app_error_widget.dart (~40 lines):
   - Props: String message, VoidCallback? onRetry
   - Error icon, message text, retry button

8. app_form_field.dart (~80 lines):
   - Props: TextEditingController controller, String label, String? hint,
     String? Function(String?)? validator, TextInputType? keyboardType, bool obscure
   - Uses TextFormField with InputDecoration from theme
   - Error display below field

9. app_date_picker.dart (~50 lines):
   - Props: DateTime? value, ValueChanged<DateTime> onChanged, String label
   - Taps to show DatePicker with Africa/Casablanca locale defaults

10. app_currency_text.dart (~25 lines):
    - Props: double amount, String currency (default "MAD")
    - Formats using intl: NumberFormat.currency(locale: 'fr_MA', symbol: 'MAD')

11. Create barrel file: mobile/lib/shared/widgets/widgets.dart — export all.

CONSTRAINTS
-----------
- Use Material 3 widgets (Material Design 3 is enabled in theme)
- All text must go through AppLocalizations.of(ref).t() or accept String params
- Colors from Theme.of(context) — do NOT hardcode any Color()
- Support RTL via Directionality (Flutter handles this automatically with correct locales)

VERIFY
------
cd mobile
flutter analyze
flutter build apk --debug

GIT (Codex only)
---
git add mobile/lib/shared/widgets/
git commit -m "feat(mobile): add shared widget library — DataTable, Badge, StatCard, Skeleton, FormField, etc."
```

---

### MOB-P0-4 — i18n Expansion & RTL

```
CONTEXT
-------
Current i18n: lib/l10n/app_localizations.dart (1,179 lines) — Map-based, covers ~200 keys for Phase 10C only
Missing: translations for 19 existing features, all new features, Arabic RTL support
Web has: ~2260 t() calls across 35 namespaces in 3 locales

TASK
----
1. Expand lib/l10n/app_localizations.dart:
   Add ALL missing translation keys for existing 19 features. Group by feature namespace:
   - auth.*, admin.*, teacher.*, attendance.*, feed.*, calendar.*, documents.*,
     notifications.*, messages.*, profile.*, invoices.*, progress.*, reports.*,
     analytics.*, content.*, results.*, timetable.*, submissions.*, family.*

2. Add placeholder namespaces for new features (will be filled as features are built):
   - gradebook.*, budgets.*, microSchools.*, skills.*, compliance.*, sync.*,
     financialHealth.*, billing.*, questionBank.*, rubrics.*, gdpr.*, settings.*

3. Add RTL support:
   - Update MaterialApp in main.dart to include locale and localizationsDelegates
   - Add Directionality widget that reads localeProvider
   - When locale == 'ar', app should render RTL

4. Ensure AppLocalizations.of(ref).t(key) returns the key itself if translation not found
   (graceful fallback instead of crash)

CONSTRAINTS
-----------
- Keep the Map-based approach (no flutter_localizations package required)
- French must be the default fallback locale
- Target: ~800+ keys per locale (will grow as features are added)

VERIFY
------
cd mobile
flutter analyze
flutter build apk --debug

GIT (Codex only)
---
git add mobile/lib/l10n/ mobile/lib/main.dart
git commit -m "feat(mobile): expand i18n to all features with Arabic RTL support"
```

---

### MOB-P0-5 — Test Infrastructure

```
CONTEXT
-------
Current: ZERO tests. No test/ directory exists.
13 repository interfaces, 13 repository implementations, 16 domain entities, 8 local stores

TASK
----
1. Add to pubspec.yaml dev_dependencies: mocktail: ^1.0.4

2. Create mobile/test/ directory structure:
   test/
     helpers/
       pump_app.dart     — pumpApp() wrapper with ProviderScope + MaterialApp + theme + i18n
       mock_repositories.dart  — Mock classes for all 13+ repositories
       factories.dart    — factory functions for all domain entities
     unit/
       (tests go here later)
     widget/
       (tests go here later)

3. pump_app.dart:
   Widget wrapper that provides: ProviderScope with overrides for mock repos,
   MaterialApp with theme, GoRouter with test routes.

4. mock_repositories.dart:
   Using mocktail: class MockAuthRepository extends Mock implements AuthRepository {}
   One mock per repository interface.

5. factories.dart:
   Factory functions: createUser(), createFeedItem(), createInvoice(), createCalendarEvent(), etc.
   Each returns a fully populated entity with sensible defaults.

6. Create test/app_test.dart — smoke test:
   testWidgets('App starts without crash', (tester) async {
     await tester.pumpWidget(const ProviderScope(child: EcolePlatformApp()));
     expect(find.byType(MaterialApp), findsOneWidget);
   });

VERIFY
------
cd mobile
flutter pub get
flutter test    # Should pass the 1 smoke test

GIT (Codex only)
---
git add mobile/test/ mobile/pubspec.yaml mobile/pubspec.lock
git commit -m "feat(mobile): add test infrastructure — pump helpers, mock repos, entity factories"
```

---

## PHASE M1 — Critical Features + First Innovation

---

### MOB-P1-1 — Gradebook Module (New)

```
CONTEXT
-------
No gradebook feature exists in mobile. Backend: 5+ endpoints (prefix /gradebook).
Web has: GradebookPage (grade grid), GradeDetailPage (student view), transcript.
Mobile pattern: Entity → Repository interface → Repository impl → Provider → Screen

TASK
----
1. Create lib/domain/entities/gradebook.dart:
   - GradebookGrid: classId, className, columns (List<GradebookColumn>), entries (List<GradebookEntry>)
   - GradebookColumn: assessmentId, title, weight, maxScore (20), date, type
   - GradebookEntry: studentId, studentName, grades (Map<String, double?>), weightedAverage
   - BulkGradeUpdate: classId, grades (List<{studentId, assessmentId, value}>)
   - WeightedSummary: classId, periodId, averages (List<{studentId, avg}>)

2. Create lib/domain/repositories/gradebook_repository.dart:
   abstract interface with: getClassGradebook, getStudentGrades, updateGrades,
   getWeightedSummary, exportGrades, getCategories, computeGrades, getTranscript

3. Create lib/data/repositories_impl/gradebook_repository_impl.dart:
   Implements all methods, calls ApiClient, caches with CacheStore

4. Add provider to lib/app/providers.dart: gradebookRepositoryProvider

5. Create lib/features/gradebook/gradebook_provider.dart:
   - gradebookProvider(classId) — AsyncNotifier for grade grid data
   - gradeUpdateProvider — mutation for saving grades

6. Create lib/features/gradebook/gradebook_screen.dart (~300 lines):
   - Teacher view: horizontal scrollable DataTable (students × assessments)
   - Each cell: TextFormField with 0-20 validation
   - Color coding: >= 10 green, < 10 red
   - Save button, export button (CSV/PDF)

7. Create lib/features/gradebook/grade_detail_screen.dart (~200 lines):
   - Student/parent view: bar chart (fl_chart BarChart), grade list, stats

8. Create lib/features/gradebook/transcript_screen.dart (~150 lines):
   - Full transcript: all periods, all subjects, weighted averages

9. Add routes to router.dart:
   GoRoute(path: '/gradebook', builder: ... GradebookScreen)
   GoRoute(path: '/gradebook/student/:id', builder: ... GradeDetailScreen)
   GoRoute(path: '/gradebook/transcript/:id', builder: ... TranscriptScreen)

10. Add i18n keys under gradebook.*

CONSTRAINTS
-----------
- Grade validation: 0-20 (Moroccan scale), step 0.5
- Use fl_chart for charts (already in pubspec.yaml)
- Follow existing clean architecture pattern exactly

VERIFY
------
cd mobile && flutter analyze && flutter build apk --debug

GIT (Codex only)
---
git add mobile/lib/domain/entities/gradebook.dart mobile/lib/domain/repositories/gradebook_repository.dart mobile/lib/data/repositories_impl/gradebook_repository_impl.dart mobile/lib/features/gradebook/ mobile/lib/app/providers.dart mobile/lib/app/router.dart mobile/lib/l10n/
git commit -m "feat(mobile): build gradebook module — grade grid, student detail, transcript with 0-20 scale"
```

---

### MOB-P1-2 — Attendance Enhancement

```
CONTEXT
-------
Current: teacher/attendance_screen.dart exists (basic marking). No history, no analytics.
Backend: 8 attendance + attendance_analytics endpoints.

TASK
----
1. Create lib/domain/entities/attendance.dart (types)
2. Create lib/domain/repositories/attendance_repository.dart (interface)
3. Create lib/data/repositories_impl/attendance_repository_impl.dart (all 8 endpoints)
4. Create lib/data/local_store/attendance_store.dart (offline cache)
5. Create lib/features/attendance/attendance_provider.dart
6. Create lib/features/attendance/attendance_history_screen.dart — calendar heatmap, stats
7. Create lib/features/attendance/attendance_analytics_screen.dart — fl_chart line chart, alerts list
8. Add routes: /attendance/history, /attendance/analytics
9. Add i18n keys

VERIFY: cd mobile && flutter analyze && flutter build apk --debug

GIT (Codex only)
---
git add mobile/lib/domain/ mobile/lib/data/ mobile/lib/features/attendance/ mobile/lib/app/
git commit -m "feat(mobile): build attendance module — history heatmap, analytics charts, offline cache"
```

---

### MOB-P1-3 — Innovation: Micro-Budgets

```
CONTEXT
-------
No budgets feature in mobile. Backend: 14 endpoints (prefix /budgets).

TASK
----
1. Full clean architecture: entity, repo interface, repo impl (14 endpoints), provider
2. budget_list_screen.dart — ListView of budget envelopes with AppBadge status
3. budget_detail_screen.dart — tabs: allocations, transactions, requests. fl_chart PieChart
4. budget_request_screen.dart — form to submit/approve/reject requests
5. Routes: /budgets, /budgets/:id, /budgets/requests
6. All amounts in MAD using AppCurrencyText
7. Add nav entry for ADM, DIR in ShellScreen
8. Add i18n keys

VERIFY: cd mobile && flutter analyze && flutter build apk --debug

GIT (Codex only)
---
git add mobile/lib/domain/ mobile/lib/data/ mobile/lib/features/budgets/ mobile/lib/app/ mobile/lib/l10n/
git commit -m "feat(mobile): build micro-budgets module — envelopes, allocations, requests with MAD currency"
```

---

### MOB-P1-4 — Innovation: Micro-Schools

```
CONTEXT
-------
No micro-schools feature in mobile. Backend: 14 endpoints (prefix /micro/).

TASK
----
1. Full clean architecture: entity, repo interface, repo impl (14 endpoints), provider
2. micro_school_list_screen.dart — card grid with capacity bar
3. micro_school_detail_screen.dart — tabs: students, resources, payments, progress
4. micro_school_enroll_screen.dart — enrollment form
5. Routes: /micro-schools, /micro-schools/:id, /micro-schools/:id/enroll
6. Add nav for ADM, DIR, PAR
7. Add i18n keys

VERIFY: cd mobile && flutter analyze && flutter build apk --debug

GIT (Codex only)
---
git add mobile/lib/domain/ mobile/lib/data/ mobile/lib/features/micro-schools/ mobile/lib/app/ mobile/lib/l10n/
git commit -m "feat(mobile): build micro-schools module — CRUD, enrollments, resources, progress"
```

---

### MOB-P1-5 — Invoices Enhancement

```
CONTEXT
-------
Current: invoices_screen.dart (343 lines), basic list only. No detail, no payment proof.

TASK
----
1. Expand invoice_repository_impl — payment proof upload, PDF download, payment creation
2. Create invoice_detail_screen.dart — line items, payment history, file_picker for proof upload
3. Route: /invoices/:id
4. Add i18n keys

VERIFY: cd mobile && flutter analyze && flutter build apk --debug

GIT (Codex only)
---
git add mobile/lib/features/invoices/ mobile/lib/data/ mobile/lib/app/ mobile/lib/l10n/
git commit -m "feat(mobile): enhance invoices — detail page, payment proof upload, MAD formatting"
```

---

## PHASE M2 — More Innovation + Feature Enhancement

---

### MOB-P2-1 — Innovation: Skills Passport

```
Full module: entity, repo (12 endpoints), impl, provider.
Screens: skills_overview (fl_chart RadarChart), skill_passport (exportable via share_plus),
  skill_evaluation (teacher form), skill_analytics (class comparison).
Routes: /skills, /skills/passport/:id, /skills/evaluate, /skills/analytics
```

### MOB-P2-2 — Innovation: MEN Compliance

```
Full module: entity, repo (12 endpoints), impl, provider.
Screens: compliance_dashboard (gauge charts), curriculum_mapping, compliance_report.
Routes: /compliance, /compliance/mapping, /compliance/reports
```

### MOB-P2-3 — Innovation: Sync Enhancement

```
Expand existing OfflineQueue + ConnectivityService for all 10 sync endpoints.
New screens: sync_status, sync_conflicts. Sync indicator in ShellScreen app bar.
Routes: /sync, /sync/conflicts
```

### MOB-P2-4 — Innovation: Financial Health

```
Full module: entity, repo (12 endpoints), impl, provider.
Screens: financial_dashboard (multi-chart), financial_snapshots, financial_export.
Routes: /financial-health, /financial-health/snapshots
All amounts in MAD.
```

### MOB-P2-5 — Billing Enhancements

```
Expand invoice repository — sibling policy, late fee policy, payment plans.
Screens: sibling_policy, late_fee_policy, payment_plans, payment_plan_detail.
Routes: /billing/sibling-policy, /billing/late-fees, /billing/payment-plans
```

---

## PHASE M3 — Supporting Features + Polish

---

### MOB-P3-1 — Question Bank

```
Full module: entity, repo (5 endpoints), impl, provider.
Screens: question_bank, import, generate_quiz.
Routes: /question-bank, /question-bank/import, /question-bank/generate
```

### MOB-P3-2 — Rubrics

```
Full module: entity, repo (6 endpoints), impl, provider.
Screens: rubrics_list, rubric_editor, rubric_grading.
Routes: /rubrics, /rubrics/:id/edit, /rubrics/:id/grade
```

### MOB-P3-3 — Timetable Generation

```
Expand timetable — constraints, generation, preview, apply.
Screens: timetable_constraints, timetable_generate.
Routes: /timetable/constraints, /timetable/generate
```

### MOB-P3-4 — Recovery Flow + Remaining Small Features

```
Auth: forgot_password_screen, reset_password_screen. Routes: /forgot-password, /reset-password
GDPR: gdpr_screen → /settings/privacy
Feature Toggles: feature_toggles_screen → /admin/features
School Settings: school_settings_screen → /admin/school
Report Scheduling: expand reports with schedule CRUD
```

### MOB-P3-5 — Component Splitting

```
Split files > 500 lines:
  documents_screen.dart (1,679 lines) → DocumentList, DocumentUpload, DocumentPreview, DocumentFilters
  quiz_player_screen.dart (1,194 lines) → QuizQuestion, QuizTimer, QuizResults, QuizProgress
  content_library_screen.dart (931 lines) → LibraryGrid, ContentCard, UploadForm, ContentFilters
  analytics_summary_screen.dart (876 lines) → AnalyticsCards, charts sub-widgets
  reports_screen.dart (827 lines) → ReportList, ReportGenerator, ScheduleManager
  register_screen.dart (715 lines) → RegisterSteps, PersonalInfoStep, SchoolInfoStep
No functional changes — extract-and-compose only.
```

### MOB-P3-6 — Accessibility

```
Add Semantics widgets to all custom widgets.
Ensure minimum 48x48 touch targets.
Test with TalkBack/VoiceOver.
Add textScaleFactor support.
```

---

## PHASE M4 — Testing & Verification

---

### MOB-P4-1 — Unit Tests

```
Test all repository implementations (mock Dio responses with mocktail).
Test all domain entities (fromJson, toJson, equality).
Test CacheStore, OfflineQueue, local stores.
Test ApiClient retry, refresh, error parsing.
Target: ~50 unit tests.
```

### MOB-P4-2 — Widget Tests

```
Test shared widgets: AppDataTable, AppBadge, AppStatCard, AppConfirmDialog, AppSkeleton.
Test feature screens: attendance, gradebook, budgets, skills (key screens).
Use pump_app.dart helper with mock repositories.
Target: ~50 widget tests.
```

### MOB-P4-3 — Integration Tests

```
Create integration_test/:
  Full flow: login → feed → notifications → logout
  Teacher: mark attendance → parent views history
  Dark mode toggle persistence
  Language switch → RTL layout
```

### MOB-P4-4 — Final Verification Gate

```
cd mobile
flutter analyze                              # 0 issues
flutter test                                  # all pass
flutter build apk --release                   # Android release build
flutter build ios --release --no-codesign     # iOS release build (macOS only)

Feature audit: verify these directories exist with >= 3 files:
  lib/features/gradebook/
  lib/features/budgets/
  lib/features/micro-schools/
  lib/features/skills/
  lib/features/compliance/
  lib/features/sync/
  lib/features/financial-health/

Quality: flutter analyze → 0 issues
Tests: flutter test → all pass, coverage > 50%
Dark mode: works on all screens
RTL: Arabic layout correct
Offline: graceful degradation with no crashes
```

---

## Summary

| Prompt | Phase | Scope | Est. Files |
|--------|-------|-------|-----------|
| MOB-P0-1 | Foundation | Native platform setup | 50+ (generated) |
| MOB-P0-2 | Foundation | Design system tokens | 6 |
| MOB-P0-3 | Foundation | Shared widget library | 12 |
| MOB-P0-4 | Foundation | i18n expansion + RTL | 2 (major edits) |
| MOB-P0-5 | Foundation | Test infrastructure | 5 |
| MOB-P1-1 | Critical | Gradebook | 8 |
| MOB-P1-2 | Critical | Attendance | 7 |
| MOB-P1-3 | Innovation | Micro-Budgets | 7 |
| MOB-P1-4 | Innovation | Micro-Schools | 7 |
| MOB-P1-5 | Critical | Invoices | 3 |
| MOB-P2-1 | Innovation | Skills Passport | 7 |
| MOB-P2-2 | Innovation | MEN Compliance | 6 |
| MOB-P2-3 | Innovation | Sync Enhancement | 5 |
| MOB-P2-4 | Innovation | Financial Health | 6 |
| MOB-P2-5 | Enhancement | Billing | 5 |
| MOB-P3-1 | Supporting | Question Bank | 5 |
| MOB-P3-2 | Supporting | Rubrics | 5 |
| MOB-P3-3 | Supporting | Timetable Gen | 3 |
| MOB-P3-4 | Supporting | Recovery + Small | 8 |
| MOB-P3-5 | Refactor | Component splitting | ~20 |
| MOB-P3-6 | Polish | Accessibility | 0 (edits) |
| MOB-P4-1 | Testing | Unit tests | ~15 |
| MOB-P4-2 | Testing | Widget tests | ~15 |
| MOB-P4-3 | Testing | Integration tests | ~5 |
| MOB-P4-4 | Verification | Final gate | 0 |
| **Total** | **25 prompts** | | **~210 files** |
