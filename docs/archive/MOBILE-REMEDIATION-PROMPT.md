# Mobile Remediation — Fix 6 Verification Failures

> Run after all 25 mobile prompts are complete.
> Fixes: dart format, test count, shared widgets export, offline check, accessibility, hardcoded colors.

---

### MOB-REM-1 — Dart Format + Shared Widgets Export Fix

```
CONTEXT
-------
Project: ecole-platform-dev/mobile
Two quick fixes:
1. dart format --set-exit-if-changed lib/ found 72 files with inconsistent formatting.
2. lib/shared/widgets/widgets.dart barrel file is missing the export for search_filter_bar.dart.

TASK
----

=== FIX 1: Format all Dart files ===
dart format lib/
dart format test/
dart format integration_test/

=== FIX 2: Complete widgets barrel export ===
File: lib/shared/widgets/widgets.dart

Add the missing export:
  export 'search_filter_bar.dart';

Ensure the barrel file exports ALL widget files in the directory.
List all .dart files in lib/shared/widgets/ (excluding widgets.dart itself)
and verify each has a corresponding export line.

VERIFY
------
dart format --set-exit-if-changed lib/     # exit 0 (no changes needed)
dart format --set-exit-if-changed test/     # exit 0
flutter analyze                             # 0 issues
grep -c "export" lib/shared/widgets/widgets.dart  # >= 10

GIT (Codex only)
---
git add -A
git commit -m "style(mobile): dart format + complete shared widgets barrel export"
```

---

### MOB-REM-2 — Eliminate Hardcoded Colors (278 → 0)

```
CONTEXT
-------
Project: ecole-platform-dev/mobile
278 hardcoded color references found in lib/features/:
  - 263 are Colors.xxx (Material palette: Colors.red, Colors.grey, Colors.green, etc.)
  - 20 are Color(0x...) (custom hex in timetable_screen.dart and progress_screen.dart)
  - Spread across 44 files in 18 feature modules

The design system tokens exist at lib/shared/ui/tokens/colors.dart (AppColors).
Both light theme (app_theme.dart) and dark theme (app_theme_dark.dart) exist.
All colors should come from Theme.of(context) or AppColors constants.

TASK
----

Step 1: Extend AppColors if needed
File: lib/shared/ui/tokens/colors.dart

Review the 278 usages and add any missing semantic colors to AppColors.
Common patterns to map:
  Colors.red / Colors.red.shade700     → AppColors.error / theme.colorScheme.error
  Colors.green / Colors.green.shade600 → AppColors.success / a new AppColors.success
  Colors.orange                        → AppColors.warning / a new AppColors.warning
  Colors.blue                          → theme.colorScheme.primary
  Colors.grey / Colors.grey.shade300   → theme.colorScheme.outline / surfaceVariant
  Colors.white                         → theme.colorScheme.surface / onPrimary
  Colors.black87                       → theme.colorScheme.onSurface
  Color(0x...) subject colors          → AppColors.subjectColors map
  Color(0x...) chart colors            → AppColors.chartPalette list

Add to AppColors:
  static const Color success = Color(0xFF4CAF50);
  static const Color warning = Color(0xFFFF9800);
  static const Color info = Color(0xFF2196F3);
  static const List<Color> chartPalette = [ ... 8 colors ... ];
  static const Map<String, Color> subjectColors = { ... };

Make sure app_theme.dart and app_theme_dark.dart both define appropriate values
for these semantic colors (light vs dark variants).

Step 2: Replace hardcoded colors in all 44 feature files

For EACH file in lib/features/ that contains Colors.xxx or Color(0x...):

Replace patterns:
  Colors.red[shade]       → Theme.of(context).colorScheme.error
  Colors.green[shade]     → AppColors.success  (or a theme extension)
  Colors.orange[shade]    → AppColors.warning
  Colors.blue[shade]      → Theme.of(context).colorScheme.primary
  Colors.grey[shade]      → Theme.of(context).colorScheme.outline (for borders)
                          → Theme.of(context).colorScheme.surfaceContainerHighest (for backgrounds)
  Colors.grey.shade100-300→ Theme.of(context).colorScheme.surfaceContainerLow
  Colors.white            → Theme.of(context).colorScheme.surface
  Colors.black / black87  → Theme.of(context).colorScheme.onSurface
  Color(0x...)            → AppColors.chartPalette[n] or AppColors.subjectColors[key]
  Colors.transparent      → Colors.transparent (OK, this one can stay)

For each widget method that uses colors, accept a BuildContext or get theme at top:
  final theme = Theme.of(context);
  final colors = theme.colorScheme;
Then replace inline Colors.xxx with colors.xxx throughout.

High-priority files (most usages):
  - student/student_content_screen.dart (17 usages)
  - admin/justification_review_screen.dart (15 usages)
  - teacher/content_card.dart (13 usages)
  - documents/documents_widgets.dart (11 usages)
  - timetable/timetable_screen.dart (12 hex colors)
  - progress/progress_screen.dart (8 hex colors)

CONSTRAINTS
-----------
- Colors.transparent is OK to keep — it has no dark mode variant
- Do NOT change colors in test files — only lib/features/
- Every replaced color must work in BOTH light and dark mode
- Import AppColors where needed: import 'package:ecole_platform/shared/ui/tokens/colors.dart';
- Do NOT change the visual appearance in light mode — map to equivalent semantic colors

VERIFY
------
flutter analyze                                           # 0 issues
grep -rn "Color(0x\|Colors\." lib/features/ --include="*.dart" | grep -v "Colors.transparent" | wc -l
# Target: 0 (excluding Colors.transparent)
flutter test                                              # all pass

# Visual check: build and verify no white-on-white or invisible text
flutter build apk --debug

GIT (Codex only)
---
git add lib/shared/ui/ lib/features/
git commit -m "refactor(mobile): replace 278 hardcoded colors with theme tokens — dark mode safe"
```

---

### MOB-REM-3 — Accessibility Audit (17 → 50+ Semantics)

```
CONTEXT
-------
Project: ecole-platform-dev/mobile
Current state: 17 Semantics() usages, all in lib/shared/widgets/.
30 feature modules have ZERO accessibility markup.
Target: >= 50 Semantics usages across the app.

TASK
----

Step 1: Add Semantics to ALL interactive elements in feature screens

For each feature screen file in lib/features/:

a) Wrap custom tap targets (GestureDetector, InkWell) in Semantics:
   Semantics(
     button: true,
     label: '<descriptive action>',
     child: GestureDetector(...)
   )

b) Wrap data display cards/tiles with Semantics:
   Semantics(
     label: '<what this card shows>',
     child: Card(...)
   )

c) Mark decorative images with excludeFromSemantics or excludeSemantics:
   Image.asset('...', semanticLabel: null, excludeFromSemantics: true)
   OR
   Semantics(excludeSemantics: true, child: Icon(Icons.decorative))

d) Add semantic labels to charts (fl_chart):
   Semantics(
     label: 'Bar chart showing attendance for the last 7 days',
     child: BarChart(...)
   )

Step 2: Priority screens to annotate (cover these first for maximum impact)

These are high-traffic screens that need Semantics most:
  1. features/attendance/ — mark/unmark buttons, status badges, date picker
  2. features/gradebook/ — grade cells, student rows, transcript items
  3. features/invoices/ — payment status, action buttons, amount displays
  4. features/budgets/ — request buttons, allocation cards, status indicators
  5. features/admin/ — user management actions, approval/reject buttons
  6. features/teacher/ — class cards, student list, grade entry
  7. features/student/ — content cards, quiz start buttons, progress indicators
  8. features/auth/ — login form, register form, password fields
  9. features/calendar/ — event cards, date selection, add event button
  10. features/messages/ — message bubbles, send button, conversation list
  11. features/skills/ — radar chart, passport items, skill badges
  12. features/compliance/ — report cards, mapping items, alert badges
  13. features/profile/ — info fields, edit buttons, avatar
  14. features/notifications/ — notification cards, dismiss actions

Step 3: Ensure minimum touch target sizes

For any tappable widget smaller than 48x48dp, wrap in:
  SizedBox(
    width: 48,
    height: 48,
    child: <tappable widget>,
  )

Or use Material:
  Material(
    child: InkWell(
      customBorder: const CircleBorder(),
      child: Padding(
        padding: const EdgeInsets.all(8),
        child: Icon(...),
      ),
    ),
  )

Step 4: Add textScaleFactor support

In screens with fixed-size containers holding text, use:
  MediaQuery.textScalerOf(context) instead of hardcoded sizes.
  Ensure text doesn't overflow when system font size is set to "Large" or "Extra Large".

For key screens (login, attendance, gradebook), verify with:
  MediaQuery(
    data: MediaQuery.of(context).copyWith(textScaler: const TextScaler.linear(1.5)),
    child: <screen>,
  )

CONSTRAINTS
-----------
- Add Semantics to at least 3-4 elements per feature screen
- Do NOT wrap every single widget — focus on interactive and informative elements
- Keep label strings translatable — use AppLocalizations where keys exist
- Do NOT change visual appearance or layout

VERIFY
------
flutter analyze                                                    # 0 issues
grep -rn "Semantics" lib/ --include="*.dart" | wc -l              # target: >= 50
grep -rn "excludeSemantics\|excludeFromSemantics" lib/ --include="*.dart" | wc -l  # > 0
flutter test                                                       # all pass

GIT (Codex only)
---
git add lib/features/ lib/shared/
git commit -m "a11y(mobile): add Semantics to 30+ feature screens — 50+ annotations"
```

---

### MOB-REM-4 — Add Missing Tests (13 → 30+ unit/widget, 3 → 4+ integration)

```
CONTEXT
-------
Project: ecole-platform-dev/mobile
Current tests:
  Unit (test/unit/): 6 files — api_client, dto_mappers, entities_coverage, entities, local_store, repositories
  Widget (test/widget/): 5 files — attendance_screens, budget_screens, gradebook_screens, shared_widgets, skills_screens
  Integration (integration_test/): 1 test file + 2 helpers
  App-level: 2 files — app_test, app_flows_vm_test

Need: >= 30 test files total, >= 4 integration test files.

TASK
----

=== NEW UNIT TESTS (add 8 files) ===

File: test/unit/connectivity_service_test.dart
  - Test online/offline detection
  - Test auto-sync trigger on reconnect
  - Test push/pull change flow
  - Mock: ConnectivityPlus, SyncRepository

File: test/unit/cache_store_test.dart
  - Test cache write/read/expire
  - Test cache invalidation
  - Test max-age expiry

File: test/unit/auth_repository_test.dart
  - Test login success/failure
  - Test token refresh
  - Test biometric auth flow
  - Mock: ApiClient, SecureStorage

File: test/unit/budget_repository_test.dart
  - Test list budgets, allocations
  - Test create/approve request flow
  - Mock: ApiClient

File: test/unit/notification_repository_test.dart
  - Test list, mark read, unread count
  - Mock: ApiClient

File: test/unit/invoice_repository_test.dart
  - Test list invoices, get detail
  - Test payment proof upload
  - Mock: ApiClient

File: test/unit/compliance_repository_test.dart
  - Test list curricula, mappings, reports
  - Mock: ApiClient

File: test/unit/offline_queue_test.dart
  - Test enqueue/dequeue operations
  - Test retry logic with backoff
  - Test idempotency key handling
  - Mock: SQLite database

=== NEW WIDGET TESTS (add 9 files) ===

File: test/widget/invoice_screens_test.dart
  - Test invoice list renders
  - Test invoice detail renders amounts in MAD
  - Test payment proof upload button

File: test/widget/micro_school_screens_test.dart
  - Test micro-school list renders
  - Test detail screen with enrollment button

File: test/widget/compliance_screens_test.dart
  - Test compliance dashboard renders
  - Test curriculum mapping list

File: test/widget/financial_health_screens_test.dart
  - Test financial dashboard chart rendering
  - Test snapshot list

File: test/widget/timetable_screens_test.dart
  - Test timetable grid renders
  - Test weekly view

File: test/widget/question_bank_screens_test.dart
  - Test question bank list
  - Test quiz generation form

File: test/widget/auth_screens_test.dart
  - Test login form renders
  - Test forgot password screen

File: test/widget/messages_screens_test.dart
  - Test conversation list renders
  - Test message bubble rendering

File: test/widget/dark_mode_test.dart
  - Test 5 key screens render correctly in dark mode
  - Verify no white-on-white text
  - Use pumpApp with dark theme

=== NEW INTEGRATION TEST (add 1 file) ===

File: integration_test/offline_sync_test.dart
  - Test: queue action while offline → reconnect → sync completes
  - Use fake_app_environment.dart for setup
  - Mock network connectivity toggle

CONSTRAINTS
-----------
- Use mocktail for mocking (add to dev_dependencies if not present: mocktail: ^1.0.4)
- Use the existing test/helpers/pump_app.dart helper for widget tests
- Each test file must have at least 3 test cases
- Follow existing test patterns from test/unit/api_client_test.dart and test/widget/attendance_screens_test.dart
- All tests must pass: flutter test

VERIFY
------
flutter test                                              # all pass
find test -name "*_test.dart" | wc -l                    # >= 30
find integration_test -name "*_test.dart" | wc -l        # >= 2
flutter test --coverage                                   # generates coverage report

GIT (Codex only)
---
git add test/ integration_test/ pubspec.yaml
git commit -m "test(mobile): add 18 test files — 30+ unit/widget tests, 2 integration tests"
```

---

### MOB-REM-5 — Final Verification Pass

```
CONTEXT
-------
After MOB-REM-1 through MOB-REM-4, re-run VERIFY-ALL-MOBILE from docs/MOBILE-GENERAL-PROMPTS.md.

TASK
----
Run every check from VERIFY-ALL-MOBILE (section 4 in docs/MOBILE-GENERAL-PROMPTS.md).

Expected results after remediation:

| Section | Target |
|---|---|
| Static Analysis | dart format: 0 changes. flutter analyze: 0 issues |
| Tests | >= 30 test files. >= 2 integration tests. All pass |
| Builds | APK + iOS both pass |
| Structure | >= 226 files, >= 42K LOC, >= 30 features, >= 79 routes |
| Design System | All token files + both themes present |
| Shared Widgets | >= 10 exports in widgets.dart |
| Offline | Queue + stores functional (pushChanges/pullChanges pattern) |
| i18n | >= 1605 keys, RTL present |
| Accessibility | >= 50 Semantics, excludeSemantics present |
| Dark Mode | 0 hardcoded colors in features/ (excluding Colors.transparent) |
| Backend Alignment | >= 23 repo implementations + interfaces |

If any check still fails, fix it inline and re-run until all PASS.

VERIFY
------
All sections PASS.

GIT (Codex only)
---
git add -A
git commit -m "verify(mobile): all VERIFY-ALL-MOBILE checks pass after remediation"
```

---

## Execution Order

| # | Prompt | Effort | What it fixes |
|---|--------|--------|---------------|
| 1 | MOB-REM-1 | Small | dart format (72 files) + widgets barrel export |
| 2 | MOB-REM-2 | Large | 278 hardcoded colors → theme tokens |
| 3 | MOB-REM-3 | Medium | Accessibility 17 → 50+ Semantics |
| 4 | MOB-REM-4 | Large | Tests 13 → 30+ files |
| 5 | MOB-REM-5 | Small | Final verification gate |

Total: 5 prompts. Execute in order.
