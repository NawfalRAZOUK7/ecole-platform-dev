# Frontend Review — Web (React/TS) vs Mobile (Flutter)

> Generated 2026-06-29 from a code-level comparison of `web/src` and `mobile/lib`
> (routers, feature folders, design tokens, i18n, role guards). Focus: parity and
> concrete enhancements — not the backend-drift items, which `WEB_MOBILE_ALIGNMENT.md`
> already closed (R1–R6).

## Verdict

Parity is **good at the domain level, uneven at the screen level.** Both clients
share the same 13 feature domains (`academic, admin, ai, auth, billing, communication,
content, lms, onboarding, reports, school, sync, user`), a **shared design-token
source of truth**, per-route **role guards**, and the same API contract. The split is
deliberate and mostly healthy: **web is the full management + authoring client; mobile
is a lighter consumption client** that uniquely adds native mini-games and offline sync.
The gaps worth acting on are a cluster of mobile screens (admin/oversight, account
security, a couple of teacher/student views) and one real quality debt (mobile i18n).

## Strengths already in place (don't rebuild)

- **Design tokens are a single source of truth.** `design-tokens/tokens.json` →
  `scripts/generate-design-tokens.mjs` emits web (`tokens.ts` + `generated-tokens.css`)
  **and** mobile (`mobile/lib/shared/ui/tokens/colors.dart`). Colors can't drift.
- **Both clients gate routes by role.** Web: `ProtectedRoute` with `roles={…}` /
  `permissions={…}` (119 explicit gates of 241 routes). Mobile: `_routeRoles` +
  redirect in `app_router.dart` covering **92 of 99** routes. (The older docs saying
  "mobile is auth-only" are stale.)
- **Web has shared SoT modules** `shared/taxonomy.ts` and `shared/permissions.ts`
  mirroring the backend enums/catalog.
- **Code quality is high on both.** Web: `tsc` + eslint green, 0 `TODO`/`console`/`any`,
  plus `knip` (dead code) and dependency-cruiser architecture checks. Mobile: clean
  layered architecture, `flutter_lints`, only 1 TODO.

## Parity gaps (mobile is missing screens that exist on web)

Several "web-only" paths actually have a mobile equivalent under a different name
(`/attendance`↔`/teacher/attendance`, `/games`↔`/student/games`, `/submissions`↔
`/teacher/submissions`, `/student/content/:id/color`↔`/coloring`). The list below is
the **genuine** missing screens after removing those.

### Acceptable web-only (technical exceptions — document, don't port)

Heavy authoring / bulk management belongs on web (matches the D4 decision):

- CMS authoring — `/cms/*` (upload, review, quiz builder, analytics).
- Teacher game authoring — `/teacher/games`, `/teacher/games/new`, `/teacher/games/:id`.
- Bulk admin — `/admin/batch-register`, `/admin/generate-invoices`,
  `/admin/fee-structures`, `/admin/fee-assignments`.
- Program management — `/admin/programs` (+versions), `/admin/program-equivalences`,
  `/admin/eligibility-rules`.
- `/calendar/holidays` editor, `/financial-health/export`.

### Worth closing on mobile (role-facing features, D4 implies parity)

| Screen (web) | Role | Why it matters on mobile |
|---|---|---|
| `/profile/login-history`, `/profile/sessions` | all | Account security; users expect these on the phone (2FA already partly there). |
| `/activities`, `/activities/:id` | STD | AI activities — students are the heaviest mobile users. |
| `/teacher/courses`, `/teacher/assessments` | TCH | Core teacher views, read at minimum. |
| `/admin/audit`, `/admin/analytics`, `/budgets/analytics` | DIR | DIR is an **oversight** role — analytics/audit on mobile is the point of the role. |
| `/admin/enrollments`, `/admin/family-links` | ADM | Operational screens with no mobile equivalent. |
| `/students/:id/rewards`, `/admin/badges` | STD/ADM | Badges/rewards gallery (mobile has `/rewards`+`/leaderboard` but not the detail). |
| `/documents/:id/preview`, `/documents/:id/versions` | staff | Document detail/versioning. |

### Mobile-only (web could adopt or intentionally keep different)

- **Native mini-games** — `/games/letter-puzzle|memory|sorting|vocabulary`. Mobile
  ships real native games; web uses a single generic player (`/student/games/:id/play`).
  This is a mobile **strength**; just decide whether web should match or stay generic.
- Offline/`/sync/conflicts`, `/submissions/upload`, `/admin/dashboard` (vs web
  `/admin` + `/admin/analytics`).

## Cross-cutting enhancements (prioritized)

1. **(P1) Mobile i18n sweep + CI guard — STARTED.** Guard added
   (`mobile/scripts/i18n_check.mjs`, green at 938 keys ×3) and 2 files fully wired as
   the reference pattern (`generate_quiz_screen.dart`, `rubrics_list_screen.dart`),
   including the worst "English in a FR/AR UI" offenders. **166 strings across ~48
   files remain** (more than the first ~111 estimate — the colon-form `labelText:`/
   `hintText:` strings weren't counted). Mechanical, but each needs `flutter analyze`
   to verify. Full per-file worklist + recipe: `MOBILE_I18N_WORKLIST.md`.

2. **(P1) Web i18n completion — DONE ✅.** All 157 missing keys filled in EN + MSA AR;
   `node scripts/i18n-check.mjs` is green.

3. **(P2) Reconcile divergent route vocabulary across clients.** Same concept, different
   names/screens: `/reports` (web = report generation, mobile = compliance report),
   `/results` vs `/progress` (grades vs skills — overlap), `/admin/settings` (web) vs
   `/admin/school` + `/admin/features` (mobile), `/gradebook/student/:id` vs
   `/gradebook/transcript/:id`, class-scoped vs global `/leaderboard`. Pick one
   vocabulary and apply it to both.

4. **(P2) Extend the shared-SoT pattern to taxonomy & permissions — TAXONOMY DONE ✅.**
   Added a backend-derived single source: `design-tokens/taxonomy.json` (dumped from
   the taxonomy enums) + `scripts/generate-taxonomy.mjs` → `mobile/lib/shared/taxonomy/
   taxonomy.g.dart` (mobile now has a typed taxonomy, was free-text) +
   `scripts/check-taxonomy-sync.mjs` drift guard (`npm run taxonomy:check`). The guard
   immediately caught a real bug: web offered `amazigh`/`quranic` subjects the backend
   rejects (422) — now removed; check is green, web typecheck green. *Follow-up:* a
   parallel permissions SoT for mobile (role-only today) and wiring the mobile screens
   to consume `Taxonomy.subjects`/`levelBands` (needs `flutter analyze`).

5. **(P3) Permission-level gating on mobile.** Mobile guards by **role**; web also guards
   by **permission** (e.g. `GAME_CONFIG_MANAGE`). Adopting permission checks on mobile
   keeps the two affordance models identical (low risk — backend is the real boundary).

6. **(P3) Close the highest-value mobile screen gaps** from the table above, starting
   with account security (`login-history`, `sessions`) and the DIR oversight views.

## Bottom line

Nothing here blocks the demo or the PFE — the architecture, theming, role guards, and
API contract are consistent across both clients. The one item I'd treat as "should fix
before calling the frontend done" is the **mobile i18n sweep (111 strings + guard)**;
everything else is parity polish you can sequence after the P0/P1 items in
`PROJECT_COMPLETION_CHECKLIST.md`.
