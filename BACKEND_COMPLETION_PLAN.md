# Backend Completion — Plan, Decisions & Traceability

> Honest status + the ordered remaining-backend work (excl. seed & tests), with
> the decisions I'm making on your behalf. Companion to `BACKEND_DB_AUDIT.md`
> and `EDUCATION_TAXONOMY.md`. Updated as work lands.

## 0. Honest status

The backend is **mature, not half-built**: core (29 files), api (82), models
(28), repositories (39), services (99), schemas (44), domain (23), workers (2);
data-driven RBAC catalog; idempotency; layered architecture; **332**
permission-gated endpoints. My work has been *targeted* features + audits, not a
line-by-line completion of every service/repository. **No migration has been
executed yet** — migrations 622→628 are code-only. So: *not* "all backend done".

## 1. Ordered execution plan (my recommendation)

| # | Item | Why this order | Validatable here? |
|---|------|----------------|-------------------|
| #29 | Service-layer subject validation (official ∪ custom) | Finishes the just-shipped custom-matières feature; pure code | ✅ static |
| #30 | Strict-role RBAC cleanup + DIR/ADM/SUP/SYS matrix | Your explicit concern; pure code + this doc | ✅ static |
| #31 | Taxonomy storage policy (decision + doc) | Light; clarifies #29/#33; mostly this doc | ✅ |
| #33 | CustomSubject title → AR/FR/EN | Small; completes custom-matières (trilingual) | ⚠ migration |
| #32 | Class↔matière + content `topic` wiring | Bigger; the end-to-end cycle→level→class→matière→topic model | ⚠ migration |
| #28 | Run `make migrate && make seed` (617→628) | Needs your machine; do after each migration-adding step | ❌ your machine |
| #34 | Maturity audit (async/observability/perf/API) | Review + fixes; do last | partial |

## 2. Decision — DIR vs ADM vs SUP vs SYS (real-school logic)

The catalog already separates them (ADM 29 perms, DIR 70, SUP 9, SYS 8; none a
subset of another). The fix is to align the *split* with how a real school works
and to stop endpoints from lumping roles.

- **SYS** — non-human system/automation account (cron, integrations, scheduled
  jobs, snapshots, retention, health). No school-data management.
- **SUP** — platform super-admin / operator. Cross-school supervision, platform
  config, **impersonation (support)**, CMS oversight. *Not* a school role.
- **CONTENT_MGR** — platform-wide official CMS library manager. Not school-scoped.
- **DIR** *(Directeur — institutional head)* — **oversight** (all dashboards,
  analytics, reports, compliance, audit *read*) **+ strategic approvals**
  (budgets, high-level justifications/sign-offs) **+ institutional voice**
  (announcements). **NOT** day-to-day ops, **NOT** impersonation.
- **ADM** *(Administration / secrétariat — operations)* — users, invitations,
  enrollments, fees/billing config, school settings, feature toggles, document
  management, attendance admin. The operational engine.
- **TCH / EDUCATOR / PAR / STD** — unchanged.

**Concrete RBAC changes (#30):**
1. Remove `PERM-ADM:impersonation:create` from **DIR** → **SUP** only.
2. Keep operational `*:manage` (user, invitation, fee, school settings,
   features) **ADM-only** (verify none leaked to DIR).
3. DIR keeps: all `*:read`/dashboard/analytics/report/compliance/audit-read,
   `announcement:manage`, `invitation:read` (oversight), budget approvals.
4. Convert the **~14** `requires_role(...)` endpoints that lump roles to
   `requires_permission(PERM-...)` so the catalog (not the endpoint) governs.
   Endpoints needing a role union keep it only where a permission truly can't
   express it (document each exception).

## 3. Decision — taxonomy storage policy

- **Closed + stable** vocabularies → **native PG enum**: `difficulty`,
  `language`, `currency`, `cycle`, `level_band`. (Levels are official-only — no
  custom levels — so `level_band` stays an enum.)
- **Open / extensible** vocabularies → **validated `String`** (code = source of
  truth, app-layer validation): **`subject`** (official ∪ per-school custom).
- Rule of thumb: *if the platform owns the full closed list and it rarely
  changes → enum; if users can extend it → validated String.*

## 4. Progress log

- **#30 — RBAC de-inheritance (DONE, static-verified).** Replaced the linear
  `ROLE_HIERARCHY` (SYS→SUP→ADM→DIR→TCH) — which made **ADM ⊇ DIR** — with
  **explicit composition bundles** in `app/core/permissions.py`:
  `_STAFF_BASE`, `_ADMIN_BASE` (shared admin reads), `_DIR_OVERSIGHT`,
  `_ADM_OPS`, `_SUP_PLATFORM`, `_SYS_AUTOMATION`. `ROLE_HIERARCHY` is now `{}`.
  - **DIR (oversight)** = `_STAFF_BASE | _ADMIN_BASE | _DIR_OVERSIGHT` — dashboards/
    analytics/reports/compliance + audit-read, announcements, budget **approve**.
  - **ADM (operations)** = `_STAFF_BASE | _ADMIN_BASE | _ADM_OPS` — user/fee/
    settings/timetable/budget-execution/document management.
  - **Siblings:** neither a superset (verified `not DIR⊆ADM and not ADM⊆DIR`).
  - **SUP** = full school capability + platform (impersonation, platform stats,
    grants). **Impersonation is SUP-only** (removed from DIR).
  - **SYS** = narrow automation (auth baseline + jobs); **no more god-mode**
    (previously inherited everything). Effective sizes: SYS 13, SUP 178, ADM 161,
    DIR 118, TCH 85.
  - Tests rewritten (`tests/unit/core/test_permissions.py`) for the composition
    model; all 27 matrix assertions + structural checks verified statically.
  - ⚠ **Validate on a real run:** confirm scheduled tasks/workers running as
    **SYS** don't need perms beyond `_SYS_AUTOMATION` (it lost god-mode). Add any
    genuinely-needed job perm to that bundle if a worker breaks.
- **#33 — CustomSubject trilingual titles (DONE, static-verified).** `CustomSubject`
  now uses `TranslatableMixin` (JSONB `translations`), matching the official
  `SUBJECT_TITLES {ar,fr,en}`. `title` stays the canonical/fallback (FR); a
  `titles()` helper resolves `{fr,ar,en}` (per-locale override → fallback to
  `title`). API accepts optional `title_ar`/`title_en` and returns resolved
  `titles`. Migration `20260629_custom_subject_i18n` adds the column (additive,
  nullable — no data migration). Single Alembic head now `20260629`. py_compile +
  fallback-logic verified.
- **#32 — class↔matière + content `topic` (sujet) (DONE, static-verified).**
  Completed the cycle→niveau→class→matière→sujet chain:
  - Added **`topic`** (sujet) free-text column to `content_items` + `quizzes`
    (open user input; suggestions from `curriculum.topics_for`). Migration
    `20260630_content_quiz_topic`. Wired through CMS create/serialize/promote +
    `CmsContent*` schemas.
  - New **`GET /curriculum/class/{class_id}/matieres`** — derives a class's
    matières from its `level_band` (official `matieres_for_level` + localized
    `SUBJECT_TITLES`) **plus** the school's active `CustomSubject`s scoped to that
    niveau/cycle. (Class↔matière is derived, not a redundant table.)
  - `Class` already has cycle+level; `ClassContentAssignment` already wires
    content↔class. Single Alembic head now `20260630`. py_compile clean.

- ⚠ **P0 BLOCKER for #28 (found during #32):** migration **`20260626`** still
  converts `*.subject` to `content_subject_enum`, but the models + the
  custom-matières feature + §3 declare `subject` a **validated `String`** (so
  schools can add non-official matières). As written, `make migrate` would make
  `subject` an enum that **rejects custom matières**. **Fix (per §3):** `20260626`
  should convert **only `level_band`** columns to the enum and, for `subject`,
  just **drop the legacy CHECK** (validation stays in `subject_rules`). Also
  reconcile `EDUCATION_TAXONOMY.md` §0/§1 (which still lists `subject` as an
  enum). *Awaiting your confirm that subject = validated String (not enum).*

- **P0 RESOLVED (your call: enum + `other` escape hatch).** `subject` is the
  native `content_subject_enum` **including `other`**; a school-specific matière
  uses `subject = 'other'` + a free-text **`subject_other`** name (same pattern as
  `MicroSchool.type` / `type_detail`). Changes: added `OTHER` to `ContentSubject`
  (taxonomy + migration 626 snapshot, parity verified); reverted the 3 `subject`
  columns (content_items/quizzes/question_bank_items) back to `PgEnum`; added
  `subject_other` columns (migration `20260631`); rewrote `subject_rules` (enum
  membership; `other`→require `subject_other`, platform content may not use
  `other`); wired `subject_other` through CMS schema/service. The `CustomSubject`
  registry now serves as the per-school **suggestion list** of `other` names
  (trilingual via #33), not a content-validation source. Single head `20260631`.
  *TODO:* wire `subject_other` into quiz + question-bank create paths (CMS done);
  reconcile `EDUCATION_TAXONOMY.md` §0/§1/§6 wording (subject = enum incl `other`).
- **Backend follow-ups (DONE).** `MicroSchool.type_detail` already existed
  (migration 627). `subject_other` now wired into **quiz** and **question-bank**
  create paths too (schema field + `validate_subject(subject_other=...)` + repo
  kwargs), matching CMS. `MicroSchoolType` enum already in place.
- **Seed consolidation (DONE).** Merged the 6 seed files
  (`seed.py` + `seed_enhanced` + `seed_extensions` + `seed_demo_scenarios` +
  `seed_onboarding` + orphaned `seed_audit`) into a **single `app/seed.py`**
  (~9,130 lines): concatenated the satellite function libraries, dropped the
  cross-seed imports, kept one copy of the identical shared ID constants/helpers,
  preserved `main()`'s call order, kept the `__main__` guard last, and deleted the
  5 now-dead files. Updated to all our changes (verified in-merge): no
  `PaymentProof` (B4), no `MicroBudget` (B3→SchoolBudget), `conversations` uses
  `subject_line` + `WritingAttempt` uses `topic` (B1), timetable subjects coded.
  Enum-column seed values already valid (Moroccan/canonical); the remaining
  display-name/generic values live in `String` columns (`timetable_slots`,
  `school_applications`) so they don't break the enum casts. `compileall app/`
  passes; single head `20260631`.
  - ⚠ **Final gate:** `make seed` against a real DB (#28) — a 9k-line merge is
    statically verified (compile + symbol resolution + call-graph) but only a real
    run confirms FK ordering/relationships end-to-end. Backup of the 6 originals
    is at `/tmp/seedbak/` (sandbox-only).
- Remaining: **#28** (run chain 617→631 + `make seed` on your DB) → **#34**
  (maturity audit). Backend feature work is otherwise complete (tests untouched
  per your instruction).

## Migration/seed run log (your DB) — 2026-06-16

- **`make migrate`: GREEN.** Full chain `617 → 632` applied. Two run-time fixes
  were needed and made along the way:
  - *622* — stale lowercase `game_configs.difficulty` default `'easy'` failed the
    enum recast → `_restore_defaults` now coerces defaults to the enum member
    case-insensitively (`'easy' → 'EASY'`).
  - Three revision IDs exceeded Alembic's `version_num VARCHAR(32)` → shortened
    (`20260623_rename_subjects`, `20260626_subj_level_enums`,
    `20260627_subj_p2_micro_type`) + down_revision links updated.
  - *632* recreates `content_subject_enum` (incl. `other`) that the 628 pivot had
    dropped, and recasts the 5 subject columns back to the enum.
- **`make seed`: fixed the last pre-Moroccan literals.** Migrations remapped the
  *data*, but `seed_level_content()` / `seed_class_content_assignments()` /
  `_seed_content_review_workflow()` still emitted **old French level codes**
  (`maternelle/CP/CE1…Terminale`) and **3 invalid subjects** (`science`,
  `geography`, `history`) into the `content_*` enum columns. Remap applied
  (approved): levels → official MEN codes, FK-critical bands matched to the
  already-seeded classes (`1AEP↔CLASS_CP`, `3AEP↔CLASS_CE2`, `6AEP↔CLASS_CM2`,
  `1AC↔CLASS_6A`, `3AC↔CLASS_3EME`, `2BAC↔CLASS_TERM`); `science →
  activite_scientifique | physique_chimie | svt` (by item), `geography/history →
  histoire_geo`. Also fixed `else "CE2" → "3AEP"` and a JSON `approved_subjects`
  entry. Full-file scan confirms **no remaining French level/subject literals on
  any enum column** (the only `level_band="primaire|lycee"` left are on
  `SchoolApplication`, a `String(50)` field — safe). `py_compile` green.

### Seed run #2 — two more list-driven French level values

The first seed pass got much further (past micro-schools + demo coverage) then
failed on `content_items.level_band = "CP"` in `seed_demo_coverage_data`. Cause:
the value reached the `level_band ==` filter via a **loop variable from a data
list**, so the line-based scan had missed it. Robust fix:
- `seed_demo_coverage_data.age_students[i][2]` (also the éval-title label) →
  Moroccan codes (`1AEP/3AEP/6AEP/3AC/2BAC`), matching the classes + the
  `level_band` query at the same function.
- `_seed_reference_tables.levels` (the `LevelAgeMapping` **level catalogue**) →
  `level_code` now Moroccan (`GS/1AEP/3AEP/6AEP/1AC/3AC/2BAC`); `label_fr` keeps
  the French equivalent for display. Coherence fix (column is `String`, was not
  breaking).
- Re-audited **every** `level_band ==` / `subject ==` query filter (4 total) and
  every content insert: all now resolve to valid enum values. The 30 French
  tokens still in the file are all `class_level` / `applies_to_level` /
  `Resource.level` / `tags` / invoice-description / JSON `snapshot_data` —
  `String`/JSON human labels, intentionally left. `py_compile` green.

### ✅ Seed run #3 — GREEN

`make migrate && make seed` complete end-to-end. Single-file `app/seed.py` runs
clean: schools, IAM, ERP, LMS, MEN curricula, micro-schools, demo coverage,
content review, personas, + friend-content import (4 stories, 33 coloring pages,
10 audio, 5 PDFs, 2 videos, 6 mascots). Reports: `seed-report.md` +
`seed-friend-report.md`. **#28 done.** Backend feature work + migrations + seed
all validated on a real DB. Remaining: **#34 maturity audit** (optional) and the
product-quality client items (nav parity, mobile i18n, Arabic review) — then the
test rewrite you've deferred.

### ✅ Dynamic smoke-test — GREEN (2026-06-16)

`scripts/smoke_test_scoping.sh` against the live stack: **12/12 pass.**
- D3 list scoping: CP student 5 items vs Terminale 5 *different* items (class-scoped).
- D3 hard boundary: CP direct GET of a Terminale-only item → 404.
- Strict roles: DIR → 403 on `user:manage`, ADM → 200 (DIR≠ADM proven live).
- Impersonation: DIR → 403 (SUP-only).
Backend (RBAC, scoping, seed, Moroccan taxonomy) validated end-to-end, not just compiled.
