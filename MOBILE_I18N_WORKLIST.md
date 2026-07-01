# Mobile i18n — remaining worklist

> Status 2026-06-29. A parity **guard** is in place and **8 files are fully wired**
> (guard green at 953 keys ×3). **~134 hardcoded UI strings across ~40 files
> remain** — mechanical, but must be finished where `flutter analyze` can verify
> each edit (Dart `const`-removal + some files need an import / `Consumer`
> conversion, which can't be compiler-checked in the review sandbox).
>
> **Risk split of the remainder:** ~21 files already import the l10n helper
> (low-risk literal swaps) and ~19 files need structural setup (add the import,
> a `final t = AppLocalizations.of(ref);`, and in a few cases convert a
> `StatefulWidget` → `ConsumerStatefulWidget`). Do the structural ones with
> `flutter analyze` open.
>
> **Key conventions already established** (reuse these): `common.cancel|save|edit|
> create|title|subject|description|error`, `quiz.easy|medium|hard`,
> `questionBank.*` (subject/difficulty/type/typeMcq/…/tags/createQuestion/…),
> `auth.email|password|or|signInWithGoogle|signInWithMicrosoft|emailRequired|
> passwordRequired`, `rubrics.create`.

## Done

- **Guard:** `mobile/scripts/i18n_check.mjs` — fails if `fr`/`ar`/`en` key sets in
  `lib/l10n/app_localizations.dart` diverge. Run: `node mobile/scripts/i18n_check.mjs`
  (currently green: 938 keys each). Wire it into `mobile-ci` / pre-commit.
- **Fully wired (pattern reference):**
  - `lib/features/lms/question_bank/generate_quiz_screen.dart` (5 strings)
  - `lib/features/lms/rubrics/rubrics_list_screen.dart` (6 strings)
- **Keys added** (fr/ar/en): `questionBank.subject|difficulty|questionCount|tags`,
  `rubrics.create`, `common.create|title|subject|description`.

## The recipe (apply per string)

1. Ensure the widget is a `Consumer*` with `ref`, the file imports
   `package:ecole_platform/l10n/app_localizations.dart`, and `final t =
   AppLocalizations.of(ref);` is in scope (or use `AppLocalizations.of(ref).t(...)`
   inline — works anywhere `ref` is a member, e.g. in dialog builders).
2. **Reuse** an existing key if the FR value already exists (e.g. `quiz.easy`,
   `common.cancel`, `common.save`). Otherwise add a new key under the screen's
   namespace to **all three** locale maps: `fr` = original, `ar` = real MSA,
   `en` = natural English.
3. Replace the literal: `const Text('…')` → `Text(t.t('ns.key'))`, and
   `labelText: '…'` → `labelText: t.t('ns.key')`. **Remove `const`** from the
   widget (and any parent `const [ … ]` list) that now depends on runtime `t`.
4. Keep ICU-style placeholders intact (use the existing replace helper for counts).
5. Do **not** touch: `debugPrint`/log strings, asset paths, enum codes
   (`value: 'easy'`), API field names, `subject` codes.
6. After each file: `cd mobile && flutter analyze` (0 new errors) and
   `node scripts/i18n_check.mjs` (green).

## Remaining files (by string count)

| Count | File |
|---|---|
| 14 | billing/invoices/invoice_detail_screen.dart |
| 9 | billing/payment_plans_screen.dart |
| 7 | school/settings/school_settings_screen.dart |
| 7 | content/coloring/coloring_screen.dart |
| 6 | lms/teacher/assignment_form_screen.dart |
| 6 | billing/sibling_policy_screen.dart |
| 6 | auth/login_screen.dart |
| 5 | reports/core/report_schedule_manager.dart |
| 5 | billing/late_fee_policy_screen.dart |
| 5 | billing/budgets/budget_request_screen.dart |
| 4 | lms/rubrics/rubric_editor_screen.dart |
| 4 | content/teacher_library/content_card.dart |
| 4 | ai/games/vocabulary_game.dart |
| 4 | ai/games/screens/vocabulary_cards_screen.dart |
| 4 | ai/games/memory_match_game.dart |
| 4 | academic/timetable/timetable_constraints_screen.dart |
| 3 | user/profile/profile_screen.dart |
| 3 | communication/calendar/create_event_screen.dart |
| 2 | reports/financial_health/financial_dashboard_screen.dart |
| 2 | reports/core/reports_generator.dart |
| 2 | lms/teacher/submissions_screen.dart |
| 2 | lms/student/quiz_list_view.dart |
| 2 | lms/rubrics/rubric_grading_screen.dart |
| 2 | lms/question_bank/question_bank_import_screen.dart |
| 2 | content/teacher_library/upload_form.dart |
| 2 | content/student/story_reader_screen.dart |
| 2 | ai/games/screens/sorting_game_screen.dart |
| 2 | ai/games/screens/memory_match_screen.dart |
| 2 | admin/justification_review_screen.dart |
| 2 | admin/feature_toggles_screen.dart |
| 2 | admin/compliance/curriculum_mapping_screen.dart |
| 2 | academic/timetable/timetable_screen.dart |
| 2 | academic/teacher/attendance_screen.dart |
| 2 | academic/attendance/attendance_history_screen.dart |
| 2 | academic/attendance/attendance_analytics_screen.dart |
| 1 | (12 more files with a single string each — see detection command below) |

Re-run detection any time:

```bash
cd mobile && LC_ALL=C grep -rnoE \
 "(child: Text|title: Text|label: Text|Text)\(\s*(const\s+)?'[A-Za-z][^']*'|(labelText|hintText|helperText|tooltip|errorText):\s*'[A-Za-z][^']*'" \
 lib --include='*.dart' | grep -vE "t\.t\(|AppLocalizations|debugPrint"
```
