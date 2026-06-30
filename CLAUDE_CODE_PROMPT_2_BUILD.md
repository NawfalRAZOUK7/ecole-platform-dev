# Prompt 2 — build the not-started work + ship

Run AFTER Prompt 1 (backend green + i18n tail done + work committed). Paste the fenced block
into Claude Code from the repo root (`ecole-platform-dev/`).

```
Continue this backend+web+mobile monorepo. The backend and web are green and prior work is
committed. Your job: build the missing mobile screens (Task D), optionally add a mobile
permissions source-of-truth (Task E), then commit, push, and open the PR (STEP 4).

GROUND RULES
- Small steps; after each screen run the gate and fix before moving on.
- Keep guards GREEN: node web/scripts/i18n-check.mjs · node scripts/check-taxonomy-sync.mjs ·
  node mobile/scripts/i18n_check.mjs
- Commit messages CLEAN: conventional-commit style, NO "Claude"/"Generated with"/
  "Co-Authored-By"/any AI attribution.
- If `.git/index.lock` errors appear, `rm -f .git/index.lock` and retry.

MOBILE CONVENTIONS (match existing code)
- Screens: `ConsumerStatefulWidget`/`ConsumerWidget` in lib/features/<domain>/.
- API: `final api = ref.read(apiClientProvider); final res = await api.get('/path');`
  (see lib/features/user/profile/gdpr_screen.dart).
- i18n: `final t = AppLocalizations.of(ref); Text(t.t('ns.key'))`; add every new key to ALL THREE
  locale maps (fr/ar/en) in lib/l10n/app_localizations.dart — real MSA Arabic, not a FR copy.
- Routing: add a GoRoute in lib/app/router/app_router.dart AND an entry in the `_routeRoles`
  map (role guard); add nav in lib/presentation/shell_screen.dart.
- Reuse existing list/empty/error/skeleton widgets (shared/widgets/...). Keep screens read-first
  (lists/dashboards).

TASK D — build the 8 missing screens (mirror the web pages; endpoints confirmed)
| Screen              | Role     | Endpoint(s)                                                              |
|---------------------|----------|--------------------------------------------------------------------------|
| Login history       | all      | GET /auth/login-history                                                  |
| Active sessions     | all      | GET /auth/sessions  (+ revoke)                                           |
| AI activities       | STD      | GET /activities, GET /activities/sessions                                |
| Teacher courses     | TCH      | GET /courses                                                             |
| Teacher assessments | TCH      | GET /assessments                                                         |
| Admin audit log     | DIR      | GET /admin/audit-logs                                                     |
| Analytics dashboard | DIR/ADM  | GET /analytics/overview|attendance|billing|engagement|grades             |
| Budget analytics    | DIR      | GET /budgets/analytics                                                    |
- Prioritize DIR oversight (audit, analytics, budget analytics) + account security
  (login-history, sessions) — those are the point of the roles.
- For each: build the screen, add GoRoute + _routeRoles + nav + i18n keys (fr/ar/en).
- After each: `cd mobile && flutter analyze` (0 new errors) + `flutter test` +
  `node scripts/i18n_check.mjs` (green). Commit per screen or in small batches.

TASK E — (optional) mobile permissions source of truth
- Add scripts/generate-permissions.mjs that dumps the backend permission catalog
  (backend/app/core/permissions.py) to mobile/lib/shared/auth/permissions.g.dart, then gate the
  few write affordances (e.g. game-config authoring) by permission instead of role — matching
  web's shared/permissions.ts + ProtectedRoute permissions={...}. Add a parity/check note.

STEP 4 — ship
- Final verify: backend pytest green · web (typecheck, lint, build, test, e2e) green ·
  mobile (analyze, test) green · all 3 guards green.
- Make sure everything is committed in logical commits, clean messages, no attribution.
- The branch is feat/onboarding-quizgen-docker-tests (ahead of main). Push it and open a PR to main.
- Final report: screens built, suites' pass/fail, anything still red and why.
```
