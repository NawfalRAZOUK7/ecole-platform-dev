# Feature Review — Backend / Web / Mobile (enhancements: add · dedup · merge · remove)

> Generated 2026-06-29 from a code-level pass. Each item has evidence and a
> recommendation. Grouped by action type, ordered by leverage within each group.
> Items marked **DONE ✅** were fixed in this session.

---

## REMOVE — dead code / duplication to delete

1. **Mobile: 3 orphaned game files (dead code).** `ai/games/memory_match_game.dart`
   (`MemoryMatchGame`), `ai/games/sorting_game.dart` (`SortingGame`), and
   `ai/games/vocabulary_game.dart` (`VocabularyGame`) have **0 references** — the
   router uses the newer `ai/games/screens/` versions (`MemoryMatchScreen`,
   `SortingGameScreen`, `VocabularyCardsScreen`). Confirmed dead (imported 0×).
   **Delete on your machine** (the review sandbox can't `rm` on the mount):
   `git rm mobile/lib/features/ai/games/{memory_match_game,sorting_game,vocabulary_game}.dart`
   then `flutter analyze`. This also removes ~12 hardcoded i18n strings from the
   worklist — they were in dead files.

2. **Web: `/admin/settings` duplicated `/admin/school`** (both rendered
   `SchoolSettingsPage`). **DONE ✅** — `/admin/settings` now redirects to
   `/admin/school`; nav points to the canonical path.

3. **Web: `ParentJustificationPage` mounted at two paths** — **DONE ✅**
   `/justification` now redirects to `/attendance/justify` (both were PAR-only,
   same page). Typecheck green.

4. **Web: `AnalyticsDashboardPage` mounted at two paths** — **DONE ✅**
   `/analytics` now redirects to `/admin/analytics` (both were ADM/DIR, same page).
   Typecheck green. *(The `CmsQuizBuilderPage` pair `/cms/quizzes` +
   `/cms/quizzes/:id/edit` is intentional create-vs-edit — left as-is.)*

5. **Dead-code sweep (run on your machine — native tooling can't run in review
   sandbox):** `cd web && npm run knip` (unused files/exports — knip is already
   configured) and `cd mobile && flutter analyze` (unused elements). Both surface
   more removals safely.

---

## MERGE — converge parallel structures

6. **Backend: micro/macro convergence (highest-leverage, biggest).** The informal
   world is a *second copy* of the formal one: `micro_schools`↔`schools`,
   `micro_groups`↔`classes`, `micro_enrollments`↔`enrollments`,
   `micro_resources`↔`content_items`, `micro_payments`↔`invoices`. Every shared
   feature is built and tested twice and they drift (this is what produced the
   class-vs-age content-scoping inconsistency). `PRODUCT_ROADMAP.md` already lays
   out the phased merge — now that the PFE is done, it's worth starting **Phase 1
   (content + scoping spine):** fold `micro_resources` into `content_items` with a
   `_user_group_ids` resolver that treats a `Class` or a `micro_group` uniformly.
   Keep genuinely-different bits separate (observational vs graded progress,
   no academic periods, flat fees). Do **not** big-bang it.

7. **Backend: split the two oversized modules** (maintainability, not behavior).
   `app/seed.py` is **9,215 lines** and `app/services/auth/auth.py` is **2,410**.
   Seed was deliberately consolidated, so leave it unless it bites; but `auth.py`
   is a single service mixing login, OAuth, 2FA, passkey and session logic —
   splitting into `auth/{login,oauth,twofa,passkey,session}.py` would make it far
   easier to navigate and test.

---

## ADD — missing features worth building

8. **Backend: collège/lycée niveau→matière detail — DONE ✅.** Filled
   `CYCLE_SUBJECTS` (college=14, lycee=15) **and** the validation map
   `MATIERES_BY_LEVEL` for the 6 secondary level bands (1AC–3AC → collège,
   TC/1BAC/2BAC → lycée), plus the `LEVELS_BY_CYCLE` mapping. Verified: per-level
   validation now enforces correctly (philosophy valid @lycée, rejected @collège;
   economics/accounting lycée-only; svt/technology @collège; music rejected at
   secondary). Compiles; taxonomy unit tests pass; taxonomy.json + mobile
   `taxonomy.g.dart` regenerated; drift check green.
   *Minor follow-up:* `CYCLE_SUBJECTS` (taxonomy.py) and `MATIERES_BY_LEVEL`
   (curriculum.py) are two parallel subject-per-level lists (pre-existing pattern,
   kept consistent) — one could derive from the other later to remove the duplication.

9. **Mobile: the screen gaps** from `FRONTEND_REVIEW_WEB_VS_MOBILE.md` —
   account security (`login-history`, `sessions`), AI `activities` (students),
   teacher `courses`/`assessments`, DIR oversight (`audit`, `analytics`,
   `budgets/analytics`). These are role-facing features web has and mobile lacks.

10. **Mobile: a permissions source of truth** (parallel to the taxonomy SoT added
    this session). Mobile gates by role only; web has `shared/permissions.ts`.
    Generate a `permissions.g.dart` from the backend catalog and gate the few
    write affordances (e.g. game-config) by permission, like web does.

---

## Cross-cutting / smaller polish

- **Web nav label:** `nav.results` now points to `/grades` (route renamed this
  session). The label key still reads "Résultats/Results" which is fine for grades;
  rename the key to `nav.grades` only if you want the vocabulary fully consistent.
- **Wire mobile screens to the generated `Taxonomy`** (`taxonomy.g.dart`, added this
  session) so subject/level inputs draw from the backend set instead of free text.
- **Mobile i18n tail** (~134 strings) — see `MOBILE_I18N_WORKLIST.md`.

---

## Suggested order

1. Quick removals (#1 mobile dead games, #3/#4 web route dedups) — small, safe.
2. Run knip + flutter analyze (#5) and clear what they surface.
3. Backend collège/lycée subjects (#8) — closes the taxonomy.
4. Mobile screen gaps + taxonomy/permissions wiring (#9, #10) — in Claude Code.
5. Plan micro/macro Phase 1 (#6) as a dedicated, staged effort — the big one.
