# Claude Code prompt — Mobile i18n sweep + nav-naming polish (verified)

> Run this **in Claude Code, inside `ecole-platform-dev/`** (Flutter SDK available).
> Goal: externalize the remaining hardcoded French UI strings in `mobile/lib` to the
> existing Map-based localization (`lib/l10n/app_localizations.dart`, locales `fr`/`ar`/`en`),
> then **verify** with `flutter analyze` and an fr/ar/en parity check. Also do the small
> nav-naming reconciliation. **No backend changes. No new dependencies.**

---

## Context (already true — do NOT redo)
- Web i18n is complete (fr/en/ar 2451 keys synced, `npm run i18n:check` guard) — leave web alone.
- Web RTL works (`applyDirection` on init + `LanguageSwitcher`). Mobile RTL works per-screen
  (`Directionality` + `TextDirection.rtl` when `t.locale == 'ar'`).
- Mobile nav, DIR/ADM split, SUP/CONTENT_MGR redirects, per-route role sets — already done.
- Mobile i18n mechanism = **Map-based**: `const Map<String,Map<String,String>> _translations`
  in `lib/l10n/app_localizations.dart` with `'fr'`, `'ar'`, `'en'` sub-maps; usage
  `final t = AppLocalizations.of(context); Text(t['namespace.key']!)`.

## Scope — ~112 hardcoded FR strings across 33 files
Top files (counts approximate, re-scan to confirm):
`user/profile/two_factor_setup_screen.dart` (17), `user/profile/profile_screen.dart` (11),
`auth/register_steps.dart` (9), `content/teacher_library/content_card.dart` (7),
`content/student/student_content_screen.dart` (7), `academic/teacher/attendance_screen.dart` (6),
`admin/invitations_screen.dart` (5), `lms/student/quiz_inputs.dart` (4),
`user/profile/change_password_screen.dart` (3), `lms/teacher/assignment_form_screen.dart` (3),
`lms/student/quiz_play_view.dart` (3), `ai/games/mini_games_screen.dart` (3),
`admin/users_screen.dart` (3), `academic/teacher/classes_screen.dart` (3),
plus ~19 files with 1–2 each (auth/login, family/my_children, billing/*, content/*, reports/*, …).

Re-scan command (heuristic):
```
grep -rnE "(Text\(|labelText:|hintText:|tooltip:|helperText:|content:\s*(const\s+)?Text\()\s*'[^']*([éèàêûôîçÉÈÀ]|\b(le|la|les|une|un|des|aucun|votre|sélection|enregistr|réessay|chargement|erreur|succès|annul|envoy|ajout|modifier|supprimer|rechercher)\b)" mobile/lib --include=*.dart | grep -vE "//|debugPrint|print\(|throw |assert\(|app_localizations.dart"
```

## Rules (apply per string)
1. **Reuse an existing key** if the FR value already exists in `_translations['fr']`
   (e.g. `'Mot de passe oublié ?'` → `auth.forgotPassword` already exists). Many strings
   are unkeyed *literals* even though the key exists — just wire them.
2. Else **add a new key** under the screen's namespace (e.g. `twoFactor.*`, `profile.*`,
   `register.*`, `users.*`, `invitations.*`) to **all three** locale maps:
   - `fr` = the original string,
   - `ar` = real **MSA Arabic** (not a FR copy),
   - `en` = natural English.
3. Replace the literal: `const Text('…')` → `Text(t['ns.key']!)`. **Remove `const`** on any
   widget (and its parents) that now depends on the runtime `t`. Add
   `final t = AppLocalizations.of(context);` at the top of the relevant `build`/builder if missing,
   and `import 'package:ecole_platform/l10n/app_localizations.dart';`.
4. Interpolations: use placeholder keys already in the pattern (e.g. `'{n} questions'`,
   `'{name}'`) and the existing replace helper; don't concatenate translated fragments.
5. Don't touch: debug/log strings, asset paths, enum codes, API field names, `subject` codes.

## Verify (must pass before done)
1. `cd mobile && flutter analyze` → **0 new errors** (warnings pre-existing are OK; no new).
2. **Parity check** — fr/ar/en key sets identical. Quick script:
   ```bash
   cd mobile && dart run - <<'DART'
   import 'dart:io';
   void main(){ /* parse app_localizations.dart maps, assert fr.keys == ar.keys == en.keys */ }
   DART
   ```
   or a grep/awk that extracts the `'key':` per locale block and diffs the three sets; fail if any locale is missing a key.
3. Re-run the scan command above → only acceptable residue (logs/asset/enum), no user-facing FR literals left.
4. Report a short table: strings externalized per file, new keys added, any string intentionally left.

## Also (nav-naming polish — small, low risk; flag if uncertain)
- **`/reports` divergence:** web routes `/reports` → `ReportsPage` (generation); mobile `/reports`
  → `compliance_report_screen`. Reconcile: either (a) rename the mobile route to `/compliance`
  (it already has `shell.compliance`) and keep `/reports` for the generator on both, or
  (b) point both `/reports` at the report-generator screen and move compliance under `/compliance`.
  Pick (a) unless the running app shows otherwise; update nav labels accordingly.
- **`/results` vs `/progress`:** keep distinct — `/results` = grades/marks, `/progress` =
  competencies/advancement. Ensure labels/keys are unambiguous (`shell.results` vs `shell.progress`)
  and no role sees both pointing at the same screen.
- Optional: wrap any still-LTR-only screen that renders user text in `Directionality` like the
  existing pattern (`t.locale == 'ar' ? TextDirection.rtl : TextDirection.ltr`).

## Caveats
- **Arabic needs a native-speaker review pass** (same caveat as the web i18n-fill).
- Keep keys **stable** (don't rename existing keys) so the web/mobile/test expectations hold.
