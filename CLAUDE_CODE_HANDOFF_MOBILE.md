# Claude Code handoff — remaining mobile (Flutter) work

> Everything here is **Dart that needs a compiler in the loop** — run it in Claude
> Code (Flutter SDK available), not the review sandbox. Each task ends with a
> verify gate. The backend + web sides of all of this are already done & verified.

## Verify gates (run after each task)
```bash
cd mobile && flutter analyze            # 0 new errors
cd mobile && flutter test               # 69 test files
node mobile/scripts/i18n_check.mjs      # fr/ar/en key parity (currently green, 953 keys)
```

## Conventions (match existing code)
- Screens are `ConsumerStatefulWidget` / `ConsumerWidget` in `lib/features/<domain>/`.
- API: `final api = ref.read(apiClientProvider); final res = await api.get('/path');`
  (see `lib/features/user/profile/gdpr_screen.dart`).
- i18n: `final t = AppLocalizations.of(ref); Text(t.t('ns.key'))`; add every new key to
  **all three** locale maps in `lib/l10n/app_localizations.dart` (fr/ar/en) — the guard
  enforces parity. Real MSA Arabic, not a French copy.
- Routes: add a `GoRoute` in `lib/app/router/app_router.dart` **and** an entry in the
  `_routeRoles` map (role guard); add nav in `lib/presentation/shell_screen.dart`.

---

## Task A — Route reconciliation (match the web decisions already shipped)
1. **`/results` → `/grades`.** Rename the GoRoute path + its `_routeRoles` key + the
   nav item + any `context.go('/results')`. Add a redirect GoRoute `/results` →
   `/grades` for old links. (Leave any API path strings alone.)
2. **`/reports` → report generation.** Point `/reports` at the report-generation
   screen (`reports/core/reports_generator.dart`); the compliance report stays at the
   existing `/compliance/reports`. Update nav so staff see generation under `/reports`.
3. **Admin settings** already use `/admin/school` + `/admin/features` on mobile — just
   confirm no stray `/admin/settings` references remain.

**Verify:** flutter analyze + tap through STD (grades), staff (reports), ADM (admin).

---

## Task B — i18n tail + dead-code delete
1. **Delete the 3 dead game files** (confirmed 0 refs, superseded by `screens/`):
   `git rm mobile/lib/features/ai/games/{memory_match_game,sorting_game,vocabulary_game}.dart`
2. **Wire the remaining ~134 hardcoded strings** per `MOBILE_I18N_WORKLIST.md`
   (recipe + per-file list there). 8 files are already done as the reference pattern.
   ~19 files need an import / `Consumer` conversion first (flagged in the worklist).

**Verify:** flutter analyze + `node mobile/scripts/i18n_check.mjs` green.

---

## Task C — Wire screens to the generated Taxonomy
`lib/shared/taxonomy/taxonomy.g.dart` (generated from the backend) now exists. Replace
free-text subject/level inputs with it:
- Subject dropdowns → `Taxonomy.subjects` (label via `Taxonomy.subjectTitles[code]?[locale]`).
- Level pickers → `Taxonomy.levelBands`.
- "Other" subject → `Taxonomy.subjectOther` + a free-text field (mirrors backend
  `subject_other`). Files: `content/teacher_library/upload_form.dart`,
  `lms/question_bank/*`, `lms/teacher/assignment_form_screen.dart`.

Regenerate any time the backend enums change: `node scripts/generate-taxonomy.mjs`.

**Verify:** flutter analyze; creating content/quiz with a real subject succeeds.

---

## Task D — Build the missing screens (parity with web)
Mirror the web pages' API calls. Endpoints (confirmed from the web API layer):

| Screen | Role | Endpoint(s) | Web reference |
|---|---|---|---|
| Login history | all | `GET /auth/login-history` | `user/profile/.../login-history` |
| Active sessions | all | `GET /auth/sessions` (+ revoke) | `ProfileSessionsPage` |
| AI activities | STD | `GET /activities`, `GET /activities/sessions` | `ai/activities` |
| Teacher courses | TCH | `GET /courses` | `lms/teacher CoursesPage` |
| Teacher assessments | TCH | `GET /assessments` | `lms/teacher AssessmentsPage` |
| Admin audit log | DIR | `GET /admin/audit-logs` | `admin AuditPage` |
| Analytics dashboard | DIR/ADM | `GET /analytics/overview\|attendance\|billing\|engagement\|grades` | `reports AnalyticsDashboardPage` |
| Budget analytics | DIR | `GET /budgets/analytics` | `billing/budgets` |

For each: create the screen, add the `GoRoute` + `_routeRoles` entry + nav, add i18n
keys (fr/ar/en). Keep them read-first (lists/dashboards); reuse existing list/empty/error
widgets (`shared/widgets/app_error_widget.dart`, etc.). DIR analytics/audit are the
point of the oversight role — prioritize those + account security.

**Verify:** flutter analyze + flutter test; each screen loads against a seeded backend.

---

## Task E — (optional) Mobile permissions source of truth
Parallel to the taxonomy SoT: add `scripts/generate-permissions.mjs` that dumps the
backend permission catalog (`backend/app/core/permissions.py`) to
`mobile/lib/shared/auth/permissions.g.dart`, then gate the few write affordances
(e.g. game-config authoring) by permission instead of role — matching web's
`shared/permissions.ts` + `ProtectedRoute permissions={...}`.

---

## Done / verified already (context — don't redo)
- Backend: oauth expiry, reports stubs, `amazigh`/`quranic` (+ migration 20260633),
  collège/lycée subjects, taxonomy SoT + drift guard. All compile + unit tests pass.
- Web: 157 i18n keys, `/results→/grades`, `/admin/settings`+`/justification`+`/analytics`
  dedup redirects, taxonomy in sync. Typecheck green.
- Mobile: i18n guard + 8 files wired + generated `taxonomy.g.dart`.
