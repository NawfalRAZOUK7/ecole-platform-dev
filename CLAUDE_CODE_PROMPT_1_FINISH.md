# Prompt 1 — finish the partially-done work

Paste the fenced block into Claude Code, run from the repo root (`ecole-platform-dev/`).

```
Continue an in-progress finishing pass on this backend+web+mobile monorepo. A prior run
already got WEB fully green and made many backend/mobile fixes, but it stopped mid-way
(rate limit) WITHOUT committing. Your job: protect that work, then finish two things —
(1) the backend full test suite to green, and (2) the mobile i18n tail.

GROUND RULES
- Small steps; after each change run the relevant gate and fix before moving on.
- Keep these guards GREEN at all times:
    node web/scripts/i18n-check.mjs
    node scripts/check-taxonomy-sync.mjs
    node mobile/scripts/i18n_check.mjs
- Commit messages CLEAN: conventional-commit style, NO "Claude"/"Generated with"/
  "Co-Authored-By"/any AI attribution. (Check `git config commit.template` and ~/.gitmessage.)
- If `.git/index.lock` errors appear, `rm -f .git/index.lock` and retry.

STEP 0 — Protect the work FIRST (nothing is committed; ~475 changes in the worktree)
- Review `git status`, then stage in logical commits and commit everything currently in the
  worktree (migrations; backend models/api/services; backend tests; web src/tests; mobile lib;
  generated taxonomy; docs). Do NOT push yet. This is so the prior run's verified work can't be lost.

STEP 1 — Backend: run the FULL suite to green
- The prior run confirmed: `migrate`/`seed` targets are in the ROOT Makefile; host has no global
  pytest (use `backend/.venv/bin/pytest`); the suite needs Postgres + Redis, so run it with real
  localhost service access (not sandboxed) and export the DB/Redis env it expects
  (from `backend/.env`: DATABASE_URL, TEST_DATABASE_URL, REDIS_URL — creds ecole/ecole).
- Ensure services up: `make migrate && make seed` (idempotent), then run the full suite:
    cd backend && <export DB/REDIS env> && .venv/bin/pytest
- The full suite is slow; iterate with `-x` or focused subsets to find the next real failure, fix,
  then do ONE final full run to confirm green.
- IMPORTANT — stale-test pattern: several failures are tests still assuming the OLD RBAC. Realign
  the TEST to the strict-role permission model (do NOT loosen the backend): announcement-create →
  DIR, audit-read → DIR, impersonation → SUP, etc. The prior run already fixed difficulty-enum,
  content-detail-404 (assign content to a class in the fixture), announcement→DIR, audit→DIR,
  impersonation→SUP — keep those and continue the same way for any remaining ones.
- Goal: `pytest` exits 0 (or a short, explicitly-justified skip list). Commit the test fixes.

STEP 2 — Mobile i18n tail (the prior run skipped this — the green guard only checks key parity,
NOT whether literals are wired)
- Detect what's still hardcoded:
    cd mobile && LC_ALL=C grep -rnoE \
     "(child: Text|title: Text|label: Text|Text)\(\s*(const\s+)?'[A-Za-z][^']*'|(labelText|hintText|helperText|tooltip|errorText):\s*'[A-Za-z][^']*'" \
     lib --include='*.dart' | grep -vE "t\.t\(|AppLocalizations|debugPrint"
- Wire each per MOBILE_I18N_WORKLIST.md: reuse existing keys where the FR value already exists;
  else add a new key to ALL THREE locale maps in lib/l10n/app_localizations.dart (fr original,
  ar = real MSA Arabic, en = natural English). Replace literals with `t.t('ns.key')` /
  `labelText: t.t(...)`; remove `const` from the widget AND any parent `const [...]` it breaks;
  ensure `final t = AppLocalizations.of(ref);` is in scope (or use `AppLocalizations.of(ref).t(...)`
  inline). ~19 files need an import / Consumer conversion first — the worklist flags them.
- After each file: `flutter analyze` (0 new errors) + `node scripts/i18n_check.mjs` (green).
  Commit in small batches.

FINISH
- Confirm: backend pytest green; flutter analyze + flutter test green; all 3 guards green;
  web still green (npm run typecheck && npm test). Commit any stragglers. Do NOT push yet
  (Prompt 2 builds the new screens, then pushes + opens the PR).
- Report: backend pass/fail count, how many i18n strings wired, anything still red and why.
```
