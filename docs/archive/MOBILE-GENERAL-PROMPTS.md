# Ecole Platform — Mobile (Flutter) General Prompts

> Generated: 2026-04-10
> Meta-prompts for Mobile Phases M0 → M4
> Reference files: `docs/MOBILE-TODOS.md`, `docs/MOBILE-PROMPTS.md`
> Architecture: Flutter 3.5+ / Dart 3.5 / Riverpod / go_router / Dio / SQLite

---

## 1. ANALYZE-MOBILE — Pre-Development Baseline

```
ROLE: Senior Flutter architect
PROJECT: ecole-platform-dev/mobile/

Run these checks to establish a mobile baseline:

1. PROJECT STRUCTURE
   find lib -name "*.dart" | wc -l
   find lib -type d | sort
   Report: total Dart files, feature modules, directory tree

2. LOC COUNT
   find lib -name "*.dart" -exec cat {} + | wc -l
   Report: total lines of code

3. ROUTE COUNT
   grep -c "GoRoute\|ShellRoute" lib/app/router.dart

4. PROVIDER COUNT
   grep -c "Provider\|StateNotifier\|AsyncNotifier" lib/app/providers.dart
   grep -rn "Provider" lib/features/ --include="*.dart" | wc -l

5. DEPENDENCY CHECK
   flutter pub outdated
   flutter analyze 2>&1 | tail -10

6. TEST COUNT
   find test -name "*_test.dart" 2>/dev/null | wc -l
   find integration_test -name "*.dart" 2>/dev/null | wc -l

7. i18n KEY COUNT
   grep -c "'" lib/l10n/app_localizations.dart | head -1
   or: grep -cE "^\s+'[a-z]" lib/l10n/app_localizations.dart

8. NATIVE PLATFORM CHECK
   ls -la android/app/build.gradle 2>/dev/null || echo "No Android config"
   ls -la ios/Runner.xcodeproj 2>/dev/null || echo "No iOS config"

9. OFFLINE INFRASTRUCTURE
   ls lib/data/local_store/
   grep -rn "OfflineQueue\|CacheStore\|ConnectivityService" lib/ --include="*.dart" | wc -l

10. BACKEND ALIGNMENT
    Count repository implementations:
    ls lib/data/repositories_impl/*.dart | wc -l
    Compare against web service count:
    ls ../web/src/features/*/*.service.ts 2>/dev/null | wc -l

Output: Markdown table with baseline numbers to compare against after each phase.
```

---

## 2. EXECUTE-ALL-MOBILE — Run All 25 Prompts

```
ROLE: Senior Flutter developer.
PROJECT: ecole-platform-dev/mobile/
REFERENCE: Read docs/MOBILE-PROMPTS.md in its entirety first.

Execute ALL 25 prompts in strict order:
  MOB-P0-1 through MOB-P0-5 (Foundation)
  MOB-P1-1 through MOB-P1-5 (Critical + Innovation×2)
  MOB-P2-1 through MOB-P2-5 (Innovation×4 + Billing)
  MOB-P3-1 through MOB-P3-7 (Supporting + Polish)
  MOB-P4-1 through MOB-P4-3 (Testing + Verification)

FOR EACH PROMPT:
1. Read CONTEXT section
2. Execute TASK completely
3. Run VERIFY — fix any failures before proceeding
4. Execute GIT (Codex only)

IMPORTANT RULES:
- Never skip a verify step
- If `flutter analyze` reports issues, fix them before the next prompt
- If a test fails, fix the test or the code before proceeding
- Keep imports clean — run `dart fix --apply` if needed

FINAL OUTPUT: Summary table showing PASS/FAIL for each of the 25 prompts.
```

---

## 3. EXECUTE-PHASE — Individual Phase Executors

### Execute Phase M0 (Foundation)
```
PROJECT: ecole-platform-dev/mobile/
Read docs/MOBILE-PROMPTS.md. Execute MOB-P0-1 through MOB-P0-5 in order.

MOB-P0-1: Flutter native platform setup (android/, ios/)
MOB-P0-2: Design system tokens (colors, spacing, typography, radii, themes)
MOB-P0-3: Shared widget library (10+ reusable widgets)
MOB-P0-4: Dark mode + i18n expansion
MOB-P0-5: Test infrastructure (helpers, mocks, factories, first smoke test)

After all 5:
  flutter analyze           # 0 issues
  flutter test              # smoke test passes
  flutter build apk --debug # builds successfully

This phase has NO backend dependencies — it's purely Flutter project setup.
```

### Execute Phase M1 (Critical + Innovation×2)
```
PROJECT: ecole-platform-dev/mobile/
Read docs/MOBILE-PROMPTS.md. Execute MOB-P1-1 through MOB-P1-5 in order.
Prerequisite: Phase M0 complete (design tokens, shared widgets, test infra exist).

MOB-P1-1: Attendance enhancement (history, analytics, offline cache)
MOB-P1-2: Gradebook module (grade grid, detail, transcript)
MOB-P1-3: Invoices enhancement (detail screen, payment proof upload)
MOB-P1-4: Micro-budgets (list, detail, requests)
MOB-P1-5: Micro-schools (list, detail, enrollment)

After all 5:
  flutter analyze
  flutter test
  # Verify new routes registered in router.dart
  grep -c "GoRoute" lib/app/router.dart   # should increase by ~15
```

### Execute Phase M2 (Innovation×4 + Billing)
```
PROJECT: ecole-platform-dev/mobile/
Read docs/MOBILE-PROMPTS.md. Execute MOB-P2-1 through MOB-P2-5 in order.
Prerequisite: Phases M0–M1 complete.

MOB-P2-1: Skills passport (radar chart, passport, evaluation, analytics)
MOB-P2-2: MEN compliance (dashboard, curriculum mapping, reports)
MOB-P2-3: Offline sync enhancement (10 sync endpoints, conflict resolution)
MOB-P2-4: Financial health (multi-chart dashboard, snapshots, export)
MOB-P2-5: Billing enhancements (sibling policy, late fees, payment plans)

After all 5:
  flutter analyze
  flutter test
  grep -c "GoRoute" lib/app/router.dart   # should increase by ~15 more
```

### Execute Phase M3 (Supporting + Polish)
```
PROJECT: ecole-platform-dev/mobile/
Read docs/MOBILE-PROMPTS.md. Execute MOB-P3-1 through MOB-P3-7 in order.
Prerequisite: Phases M0–M2 complete.

MOB-P3-1: Question bank (bank, import, quiz generation)
MOB-P3-2: Rubrics (list, editor, grading)
MOB-P3-3: Timetable generation (constraints, generate, preview)
MOB-P3-4: Recovery flow (forgot/reset password)
MOB-P3-5: Remaining small features (GDPR, feature toggles, school settings, etc.)
MOB-P3-6: Component splitting (5 oversized files → smaller widgets)
MOB-P3-7: Accessibility audit (Semantics, touch targets, textScaleFactor)

After all 7:
  flutter analyze
  flutter test
  # Check no file exceeds 600 lines:
  find lib -name "*.dart" -exec wc -l {} + | sort -rn | head -10
```

### Execute Phase M4 (Testing + Verification)
```
PROJECT: ecole-platform-dev/mobile/
Read docs/MOBILE-PROMPTS.md. Execute MOB-P4-1 through MOB-P4-3 in order.
Prerequisite: Phases M0–M3 complete (all features implemented).

MOB-P4-1: Unit tests — domain & data (50 tests target)
MOB-P4-2: Widget tests — shared + feature screens (50 tests target)
MOB-P4-3: Integration tests + final verification

After all 3:
  flutter analyze                               # 0 issues
  flutter test                                  # all pass (100+ tests)
  flutter build apk --release                   # Android release build
  flutter build ios --release --no-codesign     # iOS release build
```

---

## 4. VERIFY-ALL-MOBILE — Full Verification

```
PROJECT: ecole-platform-dev/mobile/

=== STATIC ANALYSIS ===
flutter analyze                          # 0 issues
dart format --set-exit-if-changed lib/   # properly formatted

=== TESTS ===
flutter test                             # all pass
flutter test --coverage                  # coverage report generated
find test -name "*_test.dart" | wc -l    # target: >= 30 unit + widget
find integration_test -name "*.dart" | wc -l  # target: >= 4

=== BUILDS ===
flutter build apk --release              # successful Android build
flutter build ios --release --no-codesign # successful iOS build

=== STRUCTURE ===
find lib -name "*.dart" | wc -l          # target: >= 200
find lib -name "*.dart" -exec cat {} + | wc -l  # target: >= 40,000 LOC
ls -d lib/features/*/ | wc -l            # target: >= 25 feature modules
grep -c "GoRoute" lib/app/router.dart    # target: >= 55 routes

=== DESIGN SYSTEM ===
ls lib/shared/ui/tokens/                 # colors.dart, spacing.dart, typography.dart, radii.dart
ls lib/shared/ui/app_theme.dart          # light theme
ls lib/shared/ui/app_theme_dark.dart     # dark theme

=== SHARED WIDGETS ===
grep -c "class App" lib/shared/widgets/widgets.dart  # target: >= 10 exports

=== OFFLINE ===
ls lib/data/local_store/                 # multiple store files
grep -c "syncEndpoint\|SyncEndpoint" lib/data/local_store/offline_queue.dart  # target: >= 10

=== i18n ===
grep -cE "^\s+'[a-z]" lib/l10n/app_localizations.dart  # target: >= 1500 keys
grep -c "Directionality\|TextDirection" lib/ -r          # RTL support present

=== ACCESSIBILITY ===
grep -rn "Semantics" lib/ --include="*.dart" | wc -l     # target: >= 50
grep -rn "excludeSemantics" lib/ --include="*.dart" | wc -l  # decorative images handled

=== DARK MODE ===
grep -rn "Theme.of(context)" lib/ --include="*.dart" | wc -l  # target: >= 100
# No hardcoded colors:
grep -rn "Color(0x\|Colors\." lib/features/ --include="*.dart" | wc -l  # target: 0

=== BACKEND ALIGNMENT ===
ls lib/data/repositories_impl/*.dart | wc -l  # target: >= 20 repo implementations
ls lib/domain/repositories/*.dart | wc -l     # target: >= 20 repo interfaces

Output: verification table with PASS/FAIL for each section.
```

---

## 5. PROGRESS-CHECK-MOBILE

```
PROJECT: ecole-platform-dev/mobile/
Check which mobile prompts (MOB-P0-1 through MOB-P4-3) are complete.

For each prompt, check if OUTPUT files exist and VERIFY commands pass:

Phase M0 — Foundation:
  MOB-P0-1: ls android/app/build.gradle ios/Runner.xcodeproj
  MOB-P0-2: ls lib/shared/ui/tokens/colors.dart lib/shared/ui/app_theme.dart
  MOB-P0-3: ls lib/shared/widgets/widgets.dart
  MOB-P0-4: grep "themeProvider" lib/app/providers.dart
  MOB-P0-5: ls test/helpers/pump_app.dart test/app_test.dart

Phase M1 — Critical + Innovation:
  MOB-P1-1: ls lib/features/attendance/attendance_history_screen.dart
  MOB-P1-2: ls lib/features/gradebook/gradebook_screen.dart
  MOB-P1-3: ls lib/features/invoices/invoice_detail_screen.dart
  MOB-P1-4: ls lib/features/budgets/budget_list_screen.dart
  MOB-P1-5: ls lib/features/micro-schools/micro_school_list_screen.dart

Phase M2 — Innovation + Billing:
  MOB-P2-1: ls lib/features/skills/skills_overview_screen.dart
  MOB-P2-2: ls lib/features/compliance/compliance_dashboard_screen.dart
  MOB-P2-3: ls lib/features/sync/sync_status_screen.dart
  MOB-P2-4: ls lib/features/financial-health/financial_dashboard_screen.dart
  MOB-P2-5: ls lib/features/billing/sibling_policy_screen.dart

Phase M3 — Supporting + Polish:
  MOB-P3-1: ls lib/features/question-bank/question_bank_screen.dart
  MOB-P3-2: ls lib/features/rubrics/rubrics_list_screen.dart
  MOB-P3-3: ls lib/features/timetable/timetable_constraints_screen.dart
  MOB-P3-4: ls lib/features/auth/forgot_password_screen.dart
  MOB-P3-5: ls lib/features/settings/gdpr_screen.dart
  MOB-P3-6: check no file > 600 lines in features/
  MOB-P3-7: grep -c "Semantics" lib/ -r

Phase M4 — Testing:
  MOB-P4-1: find test -name "*_test.dart" | wc -l  # >= 15
  MOB-P4-2: find test -name "*_test.dart" | wc -l  # >= 30
  MOB-P4-3: flutter analyze && flutter test && flutter build apk --release

| Prompt | Description | Status |
|--------|-------------|--------|
| MOB-P0-1 | Native platform setup | DONE/TODO |
| MOB-P0-2 | Design system tokens | DONE/TODO |
| ... | ... | ... |

State: "X of 25 prompts complete. Next: MOB-P{x}-{y}"
```

---

## 6. FIX-FAILURES-MOBILE

```
PROJECT: ecole-platform-dev/mobile/

After running a prompt, if VERIFY fails:

1. Run `flutter analyze` and fix all issues
2. Run `flutter test` — for each failing test:
   a. Read the test file and the file under test
   b. Determine if the test or the code is wrong
   c. Fix and re-run
3. Run `dart fix --apply` for quick lint fixes
4. If a build fails:
   a. Check `flutter doctor -v` for environment issues
   b. Check pubspec.yaml for dependency conflicts
   c. Run `flutter pub get` to refresh dependencies
5. Re-run the full VERIFY for the current prompt
6. Only proceed to the next prompt when all checks pass
```

---

## 7. DIFF-REPORT-MOBILE

```
PROJECT: ecole-platform-dev/mobile/

Generate a before/after comparison for the mobile project.

BEFORE (current baseline):
  Files: find lib -name "*.dart" | wc -l
  LOC: find lib -name "*.dart" -exec cat {} + | wc -l
  Routes: grep -c "GoRoute" lib/app/router.dart
  Features: ls -d lib/features/*/ | wc -l
  Tests: find test -name "*_test.dart" | wc -l
  Providers: grep -c "Provider" lib/app/providers.dart
  i18n keys: grep -cE "^\s+'[a-z]" lib/l10n/app_localizations.dart

AFTER (target):
  Files: ~220+
  LOC: ~45,000+
  Routes: 55+
  Features: 25+
  Tests: 100+
  Providers: 40+
  i18n keys: 2000+

Present as a comparison table with delta column.
```

---

## 8. SINGLE-PROMPT-MOBILE

```
Execute a single mobile prompt by ID.

Usage: Replace {PROMPT_ID} with the target (e.g., MOB-P1-3)

1. Read docs/MOBILE-PROMPTS.md
2. Find prompt {PROMPT_ID}
3. Read its CONTEXT section
4. Check prerequisites — verify prior prompts are complete
5. Execute TASK
6. Run VERIFY
7. Fix any failures
8. Execute GIT (Codex only)

Output: "{PROMPT_ID} — PASS" or "{PROMPT_ID} — FAIL: {reason}"
```

---

## 9. ESTIMATE-MOBILE

```
PROJECT: ecole-platform-dev/mobile/
Estimate effort for remaining mobile prompts.

For each incomplete prompt (from PROGRESS-CHECK), estimate:
- Files to create/modify
- Approximate LOC
- Dependencies on other prompts
- Risk level (low/medium/high)
- Estimated time with AI tool (Codex/Claude/Cursor)

Output table:
| Prompt | Files | LOC | Dependencies | Risk | Est. Time |
|--------|-------|-----|--------------|------|-----------|

Total estimated time for all remaining prompts.
```

---

## 10. ROLLBACK-MOBILE

```
If a prompt causes regressions:

1. git log --oneline -10   # find the commit before the problem
2. git diff HEAD~1         # review what changed
3. git revert HEAD         # revert last commit (safe)

If multiple commits need reverting:
  git revert HEAD~{n}..HEAD --no-commit
  flutter analyze
  flutter test
  git commit -m "revert: rollback MOB-P{x}-{y} due to {reason}"

Never use git reset --hard in shared branches.
```

---

## 11. WEB-MOBILE-PARITY-CHECK

```
PROJECT: ecole-platform-dev/
Compare web and mobile feature coverage to ensure parity.

For each web feature module (ls web/src/features/):
1. Check if corresponding mobile feature exists (ls mobile/lib/features/)
2. Compare screens: web pages vs mobile screens
3. Compare API coverage: web service methods vs mobile repository methods
4. Check i18n key coverage

Output:
| Feature | Web Screens | Mobile Screens | Web API Calls | Mobile API Calls | Parity |
|---------|-------------|----------------|---------------|------------------|--------|
| attendance | 3 | 3 | 8 | 8 | ✅ |
| budgets | 3 | 3 | 14 | 14 | ✅ |
| ... | ... | ... | ... | ... | ... |

List any parity gaps at the end with recommended fixes.
```

---

## Summary

| # | Prompt | Purpose |
|---|--------|---------|
| 1 | ANALYZE-MOBILE | Baseline audit before development |
| 2 | EXECUTE-ALL-MOBILE | Run all 25 prompts sequentially |
| 3 | EXECUTE-PHASE (×5) | Run one phase at a time (M0–M4) |
| 4 | VERIFY-ALL-MOBILE | Full verification after all phases |
| 5 | PROGRESS-CHECK-MOBILE | Check which prompts are done |
| 6 | FIX-FAILURES-MOBILE | Debug and fix failing verifications |
| 7 | DIFF-REPORT-MOBILE | Before/after comparison |
| 8 | SINGLE-PROMPT-MOBILE | Execute one prompt by ID |
| 9 | ESTIMATE-MOBILE | Effort estimation for remaining work |
| 10 | ROLLBACK-MOBILE | Safe revert strategy |
| 11 | WEB-MOBILE-PARITY-CHECK | Cross-platform feature parity audit |
