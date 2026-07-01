# Prompt for Claude Code

Copy everything in the fenced block below into Claude Code, run from the repo root
(`ecole-platform-dev/`).

```
You are finishing a backend + web + mobile monorepo. A prior pass (in another tool)
already implemented and VERIFIED a lot of the backend and web; the remaining work is
mostly Flutter (Dart) that needs a compiler, plus running every test suite to green.

FIRST, read these planning docs in the repo root and treat them as the source of truth:
- CLAUDE_CODE_HANDOFF_MOBILE.md   (the remaining mobile work, task by task, with API endpoints)
- MOBILE_I18N_WORKLIST.md         (the ~134-string i18n tail: recipe + per-file list)
- FEATURE_REVIEW.md               (add/dedup/merge/remove findings; some marked DONE)
- FRONTEND_REVIEW_WEB_VS_MOBILE.md(web/mobile parity gaps)
- PROJECT_COMPLETION_CHECKLIST.md (overall status, P0..P3)

GROUND RULES
- Work in small steps; after each change run the relevant verify gate and fix before moving on.
- Keep these guards GREEN at all times:
    node web/scripts/i18n-check.mjs
    node scripts/check-taxonomy-sync.mjs
    node mobile/scripts/i18n_check.mjs
- Commit messages must be CLEAN: conventional-commit style, NO "Claude", NO "Generated with",
  NO "Co-Authored-By", no AI attribution of any kind. (Check `git config commit.template` and
  ~/.gitmessage are clean too.)
- If a `.git/index.lock` error appears, run `rm -f .git/index.lock` and retry.

STEP 0 — Environment + repo hygiene
- Ensure Python 3.11+ (the code uses datetime.UTC), Node, and the Flutter SDK are available.
- Untrack stray build artifacts and keep them ignored (.gitignore already updated):
    git rm --cached backend/.coverage-unit.json web/playwright-report/index.html web/test-results/.last-run.json

STEP 1 — Backend: migrate, seed, test (fix failures)
- cd backend && make migrate   # applies the chain incl. new 20260633_subject_amazigh_quranic
                               # (adds enum values amazigh, quranic via autocommit_block)
- make seed
- pytest                       # unit + integration + security + contract
  Fix any real failures. Note: a prior pass already fixed 8 unit test files
  (permissions counts, attendance batched rollup, ai topic, conversation subject_line,
  sms logger, budget recompute) — keep those.
- Confirm: amazigh/quranic are valid subjects; collège/lycée subjects validate per level
  (philosophy valid @lycée, rejected @collège; economics/accounting lycée-only).

STEP 2 — Web: typecheck, lint, guards, build, tests (fix failures)
- cd web && npm ci
- npm run typecheck && npm run lint
- npm run i18n:check && npm run taxonomy:check
- npm run build            # confirms the rollup/vite bundle (couldn't run in the prior sandbox)
- npm test && npm run test:e2e
- npm run knip             # remove dead code it surfaces (it was unrunnable before)
  Verify the route redirects work: /results→/grades, /admin/settings→/admin/school,
  /justification→/attendance/justify, /analytics→/admin/analytics.

STEP 3 — Mobile: do CLAUDE_CODE_HANDOFF_MOBILE.md, Tasks A–E, in order
- Task A: route reconciliation (/results→/grades with redirect; /reports→generation,
  compliance stays /compliance/reports; confirm /admin/school + /admin/features).
- Task B: `git rm` the 3 dead game files (memory_match_game, sorting_game, vocabulary_game);
  then wire the remaining ~134 hardcoded strings per MOBILE_I18N_WORKLIST.md (real MSA Arabic,
  add every new key to fr/ar/en, keep the guard green).
- Task C: replace free-text subject/level inputs with lib/shared/taxonomy/taxonomy.g.dart
  (Taxonomy.subjects / levelBands / subjectTitles / subjectOther).
- Task D: build the 8 missing screens from the endpoint table (login-history, sessions,
  AI activities, teacher courses, teacher assessments, admin audit, analytics, budget analytics).
  Add GoRoute + _routeRoles + nav + i18n for each. Prioritize DIR oversight + account security.
- Task E (optional): generate mobile permissions.g.dart from backend permissions and gate
  write affordances by permission.
- After each: `cd mobile && flutter analyze` (0 new errors), `flutter test`,
  `node mobile/scripts/i18n_check.mjs` (green).

STEP 4 — Commit + finish
- Stage in logical commits (migrations; models/api; services; tests; web; mobile; docs),
  clean messages, no AI attribution. The current branch is feat/onboarding-quizgen-docker-tests
  (46 commits ahead of main) — push it and open a PR to main.
- Final report: what was fixed, suites' pass/fail, anything still red and why.

Be thorough: the goal is all three suites green, all guards green, the mobile parity gaps
closed, and a clean set of commits ready to merge.
```
