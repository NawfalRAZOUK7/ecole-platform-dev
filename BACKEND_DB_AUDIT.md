# Backend & Database Audit — École Platform

> Scope: `backend/` (SQLAlchemy models, Alembic, schemas, services) + a UI/UX section for web & mobile.
> Status: **audit only — no code changed for these items.** Implementation is gated on your selection (next step).
> Constraint: this pass ran without a DB/Flutter, so every migration below is marked with risk + a "validate in VS Code" note.

---

## 0. Executive summary

The backend is **already mature and well-architected** — a clean layered design (models → repositories → services → schemas → api), ~8,900 lines of models across cohesive domain files, and strong DB discipline: **40+ native PostgreSQL enums, 126 CHECK constraints, 366 indexes, 222 foreign keys, 51 unique constraints.** This is not a codebase that needs a rewrite.

The high-value work is **targeted consistency**: a small set of categorical columns are still free strings while every comparable field is an enum, and the **level/grade concept is modelled three different ways at once** (a reference table, free-string columns, and runtime string-parsing of class codes). Fixing those removes real data-integrity risk and simplifies the teacher-scoping logic.

Findings are ranked **P0 (correctness/data-integrity) → P1 (consistency/maintainability) → P2 (polish)**. Each has evidence, impact, a recommended fix, effort, and whether it's breaking.

---

## 1. P0 — correctness & data integrity

### 1.1 `difficulty` stores two vocabularies for the same concept *(bug)*
- **Evidence:** seed contains both `EASY/MEDIUM/HARD` and `easy/medium/hard`; columns: `models/games.py:47` (`default="easy"`), `models/lms.py:929`, `:1090`, `:1285` (required, no default).
- **Impact:** any filter/group-by on difficulty silently splits the same level into two buckets; adaptive-difficulty logic and analytics are wrong. Defaults disagree across tables.
- **Fix:** `DifficultyLevel(str, Enum)` = {`easy, medium, hard`} (or upper — pick one); normalize existing rows; native PG enum `difficulty_enum` (closed set) + consistent default. Validate in Pydantic.
- **Effort:** S. **Breaking:** data normalization required (one `UPDATE lower(difficulty)`), column type swap.

### 1.2 `Class` has no level/cycle column — level is parsed from code strings *(fragility)*
- **Evidence:** `models/erp.py:153` `Class` has only `code` + `name`; the teacher CMS scope derives levels by string-parsing the code (`repositories/lms.py:_level_bands_from_class_label`). A canonical reference table **already exists** (`models/levels.py` `LevelAgeMapping.level_code`) but **nothing FKs to it**.
- **Impact:** teacher content scoping breaks for any class code that doesn't match the parser's heuristics (e.g. `Groupe-1`, `Section A`, bilingual labels). Level is unqueryable; reporting can't group by level reliably.
- **Fix:** add `Class.level_band` (the `ContentLevelBand` enum) **and** `Class.cycle` (`maternelle/primaire/college/lycee`); backfill from existing codes via the parser once; replace the runtime parser with a direct column read in scoping. Optionally FK `Class.level_code → level_age_mappings.level_code` (make it `UNIQUE` first).
- **Effort:** M. **Breaking:** additive columns + a one-time backfill; parser stays only as a backfill helper.

### 1.3 Taxonomy enums only applied to `content_items`, not `quizzes` / question bank
- **Evidence:** I constrained `content_items.subject/level_band` last round; `models/lms.py:810,816` (`Quiz`), `:1088,1089` (quiz question), `:1283` (`QuestionBankItem.subject`) are still free `String`.
- **Impact:** the "shared curriculum taxonomy" is only half-enforced; quiz library filtering can drift from content filtering.
- **Fix:** reuse `ContentLevelBand`/`ContentSubject`; add the same Pydantic validators + CHECK constraints to `quizzes` (and question-bank where appropriate).
- **Effort:** S. **Breaking:** additive CHECKs (`NOT VALID`), no data change if values are already canonical.

---

## 2. P1 — consistency & maintainability

### 2.1 Inconsistent bilingual/i18n storage across the schema
- **Evidence:** `*_fr/_ar/_en` columns are duplicated on 6+ models with **inconsistent nullability**: `calendar.py:62` (`title_fr` required, others nullable), `men_compliance.py:95-96` (`_fr` **and** `_ar` required), `games.py:44` (all nullable), plus `rewards.py`, `levels.py`. No shared contract.
- **Impact:** every translatable entity reinvents the pattern; adding a 4th language means schema changes everywhere; queries can't generically "give me the label in locale X".
- **Fix (pick one):**
  - **A — `translations` JSONB column** + a `TranslatableMixin` helper (`name = {"fr": ..., "ar": ..., "en": ...}`), with a small accessor `tr(field, locale)`. Lowest friction, flexible, one migration per table.
  - **B — central `translations` table** (`entity_type, entity_id, field, locale, value`, unique on the 4-tuple). Most normalized, best for CMS-managed copy, but heavier joins.
  - Recommend **A** for app-owned labels; consider **B** only if non-devs will translate content at scale.
- **Effort:** M–L. **Breaking:** yes (column moves + data migration + read-path updates in web/mobile/serializers).

### 2.2 `level` free-strings scattered, not referencing the canonical table
- **Evidence:** independent `level` `String` columns: `documents.py:166`, `erp.py:777`, `lms.py:1284`, `men_compliance.py:35`; seed values are inconsistent (`"6"`, `"6eme"`, `"informal-creche"`, `"5eme"`).
- **Impact:** same concept, many spellings; impossible to join "all content for level X" across domains.
- **Fix:** standardize on `ContentLevelBand` (+ informal variants) and reference `level_age_mappings.level_code`; normalize seed values.
- **Effort:** M. **Breaking:** data normalization + CHECK/FK.

### 2.3 `language` should be an enum
- **Evidence:** `language` free `String`; data only `fr`/`ar` though `en` is supported app-wide.
- **Fix:** `Language(str, Enum)` = {`fr, ar, en`}; native PG enum `language_enum`; default `fr`.
- **Effort:** S. **Breaking:** type swap (values already valid).

### 2.4 `currency` should be constrained
- **Evidence:** 9 `currency` `String` columns, all `MAD` in data (billing/budget/micro-payments).
- **Impact:** a typo (`Mad`, `MAD ` ) corrupts money math/reporting.
- **Fix:** ISO-4217 CHECK or `Currency` enum (at least `{MAD, EUR, USD}`); `server_default='MAD'`.
- **Effort:** S. **Breaking:** additive CHECK + default.

### 2.5 `LevelAgeMapping` is a reference table that nothing references
- **Evidence:** `models/levels.py` defines levels with labels + age ranges, but no FK points at it; age tiers are recomputed elsewhere.
- **Fix:** add `UNIQUE(level_code, school_id)`, treat it as the canonical level dimension, and FK content/quiz/class level columns to it (or keep the enum as the code and use this table for labels/age — pick one source of truth).
- **Effort:** M. **Breaking:** constraints + FKs.

---

## 3. P2 — polish

- **Soft-delete inconsistency:** some models carry `deleted_at`, others hard-delete. Decide a policy and apply a `SoftDeleteMixin` where audit/GDPR matters (billing, submissions, content).
- **Overloaded column names** (`type`, `subject`, `code`) across domains are fine functionally but hurt grep-ability; document the per-table meaning in model docstrings.
- **`mime_type`** free string is acceptable (open set) — it's already validated in the service layer; optionally add an allowlist CHECK.
- **Index hygiene:** with 366 indexes, run `pg_stat_user_indexes` after load to drop unused ones and confirm every FK used in filters has a covering index.
- **Enum naming** is already consistent (`*_enum`) — keep new ones on that convention (`difficulty_enum`, `language_enum`, `currency_enum`, `class_level_band_enum`).

---

## 4. Proposed target state (breaking changes allowed)

A single **taxonomy module** (`app/models/taxonomy.py`) owning the closed vocabularies: `ContentLevelBand`, `ContentSubject`, `DifficultyLevel`, `Language`, `Currency`, `SchoolCycle`. Native PG enums for the closed ones (`difficulty`, `language`, `currency`, `cycle`); CHECK constraints for the open-ish ones (`subject`, `level_band`) that are written as raw strings and shared across tables.

`Class` becomes the source of truth for level: `level_band` (enum) + `cycle` (enum) + optional FK to `level_age_mappings`. `_level_bands_from_class_label` is demoted to a one-time backfill utility. Translatable copy moves to a `TranslatableMixin` (JSONB) so a new language is config, not a migration.

---

## 5. Migration & rollout plan (phased)

1. **Phase A (additive, safe):** new enums + new nullable columns (`Class.level_band/cycle`, taxonomy on quizzes) + `NOT VALID` CHECKs. Ship, no behavior change.
2. **Phase B (backfill):** data scripts — normalize `difficulty` case, backfill `Class.level_band` from codes, normalize `level`/`language`/`currency`. Then `VALIDATE CONSTRAINT`.
3. **Phase C (cutover):** switch scoping/reporting to read the new columns; update web/mobile serializers; update seed + tests.
4. **Phase D (cleanup, breaking):** drop/replace legacy free-string columns, migrate i18n columns → `translations`. Reseed.

Each phase is independently shippable; only D requires the coordinated web/mobile/test update + reseed.

---

## 6. UI/UX audit — web + mobile

**Design system / tokens.** The project already has a 3-layer token system (`design-tokens/`, `.ai/skills/design-system`). Last round removed the `STD→kids` theme override and moved to a context-driven resolver (platform / formal / informal + age accent). **Recommendation:** finish a single shared token contract consumed by *both* web (`shared/ui/designContext.ts`) and mobile (`shared/ui/design_context.dart`) from one source — today they're parallel implementations that can drift.

**Accessibility.** 340 hardcoded mobile strings remain (`make mobile-i18n-scan`); some are **hardcoded Arabic** that never switches language. Web needs an ARIA pass. Both need focus-visible states and adequate contrast on the role-accent colors.

**RTL.** Arabic is right-to-left. Verify both clients flip layout/direction (not just translate text) — icons, chevrons, progress bars, padding. This is the single biggest correctness gap for the Arabic experience.

**Consistency.** Unify nav groups web↔mobile, notification/message badges, empty states per role (a student with no assigned content should see a friendly empty state, not a blank list), loading skeletons, and a shared icon set.

**Quick wins (safe, no runtime needed):** role-aware empty states, consistent button hierarchy, the remaining i18n externalization, and `Semantics`/`aria-label` coverage. **Deeper (needs preview):** RTL verification, contrast tuning, motion/transition polish.

---

## 7. Prioritized roadmap

| Pri | Item | Effort | Breaking |
|----|------|--------|----------|
| P0 | 1.1 `difficulty` enum + normalize | S | data norm |
| P0 | 1.2 `Class.level_band`/`cycle` + retire string parsing | M | additive+backfill |
| P0 | 1.3 taxonomy on quizzes/question-bank | S | additive |
| P1 | 2.3 `language` enum · 2.4 `currency` constraint | S | low |
| P1 | 2.2 normalize `level` → canonical | M | data norm |
| P1 | 2.1 unified i18n storage | M–L | yes |
| P1 | 2.5 `LevelAgeMapping` as canonical dimension | M | constraints/FK |
| P2 | soft-delete policy · index audit · docstrings | S–M | no |
| UX | shared token contract · RTL · empty states · a11y · finish i18n | M | per-item |

---

## 8. Next step

Tell me which of these to implement and I'll do them in dependency order (P0 → P1), additive phases first, each with its Alembic migration + seed + test updates, then the breaking cutover where you've approved it.

---

## 9. Implementation progress (this pass)

**Done — backend P0 + P1-quick (code, statically validated; migrations need `make migrate` to run):**

- **Taxonomy module** `app/models/taxonomy.py` — single source of truth: `ContentLevelBand`, `ContentSubject` (re-homed from `lms.py`, re-exported for back-compat), `DifficultyLevel`, `Language`, `Currency`, `SchoolCycle` + value tuples.
- **P0.1 difficulty** — fixed the `EASY`/`easy` bug: migration `20260618_taxonomy_constraints` normalizes case (`upper`) across `game_configs/activities/quizzes/question_bank_items` + CHECK constraints; model default `easy`→`EASY`; seed normalized to uppercase.
- **P0.2 Class.level_band + cycle** — added the canonical columns (`models/erp.py`), migration `20260619_class_level_band` (additive + CHECK), seed populates them, and `repositories/lms.py:list_teacher_level_bands` now **reads the column** and only falls back to code-parsing for legacy rows.
- **P0.3 quiz taxonomy** — extended the subject/level_band CHECKs to `quizzes` + `question_bank_items` (same `20260618` migration).
- **P1 language + currency** — migration `20260620_currency_language` adds CHECK constraints (`fr/ar/en`; `MAD/EUR/USD`) across all owning tables (4 language, 9 currency).
- Migration chain: `616 → 617 → 618 → 619 → 620` (linear). All `py_compile` clean. All CHECKs `NOT VALID` (existing rows safe; `VALIDATE CONSTRAINT` once data confirmed clean — the seed already is).

**Done — P1 unified i18n storage (2.1), phase A+B:**

- `TranslatableMixin` (`app/core/database.py`) — one JSONB `translations` column + `tr(field, locale)` accessor (validated fallback: requested locale → `fr` → any).
- Migration `20260621_i18n_translations` adds `translations` + **backfills** it from the legacy `*_fr/_ar/_en` columns across all 9 bilingual tables (events, moroccan_holidays, game_configs, level_age_mappings, men_objectives, reward_badges, skill_dimensions, skill_milestones, schools).
- Exemplar wired end-to-end on `RewardBadge` (mixin applied) + `RewardBadgeResponse` exposes `translations`. **Dual-read**: legacy columns retained, nothing breaks.
- *Remaining (phase C/D, breaking):* apply the mixin + switch serializers to `tr(...)` on the other 8 models, then drop the legacy columns + update web/mobile reads. Tracked.

**Done — P1 level normalization (2.2), decision + safe fix:**

- The `level` columns are **distinct concepts sharing a name**, so a blanket constraint is wrong: `question_bank_items.level` is *redundant* with the new `level_band` (→ consolidate); `programs.level` holds program-types (`informal-creche`, `senior`) (→ rename to `program_type` / use `SchoolCycle`); `resources.level` is `String(120)` free text (→ review); `student_rewards.level` / `skill_milestones.level` are gamification integers (leave). Fixed the one concrete inconsistency: fee `applies_to_level="6"` → `"6eme"`.
- *Remaining (breaking cutover):* the per-concept consolidation/renames above + FK to `level_age_mappings`. Tracked.

**Done — pass 3:**

- **Difficulty reconciliation** (completes P0.1): the codebase had *three* live conventions — quizzes `EASY|MEDIUM|HARD`, question-bank `easy|medium|hard`, games `GameDifficulty` (lowercase) + a model validator that force-lowercased writes. All reconciled to canonical **UPPERCASE**: `GameDifficulty` values, the `@validates` + `_normalize_difficulty` service, and seed. Input schemas (`QuizCreate/Update`, `QuestionBankCreate`) now use a tolerant `normalize_difficulty` validator (accept any case → store uppercase) so existing **lowercase web/mobile clients don't break**.
- **i18n cutover (phase mixin):** `TranslatableMixin` applied to all 9 bilingual models (Event, MoroccanHoliday, GameConfig, LevelAgeMapping, MenObjective, RewardBadge, SkillDimension, SkillMilestone, School) — additive, columns already added/backfilled by `20260621`.
- **P2 index audit:** `backend/scripts/db_index_audit.sql` (unused indexes, FKs missing a covering index, duplicate indexes) — run against a loaded DB.

**Done — pass 4 (native PG enum promotion, completes Queued #1):**

- Migration `20260622_promote_native_enums` promotes the four closed sets from String+CHECK to native PG enums (precedent: `1c42d3e4f5a6`): `difficulty_enum` (game_configs, activities, quizzes, question_bank_items), `language_enum` (content_items, quizzes, micro_resources, school_applications), `currency_enum` (invoices, fee_structures, micro_budgets *(renamed `school_budgets` later in migration 625, B3)*, budget_allocations, budget_requests, cashflow_forecasts, cost_per_student, financial_snapshots, micro_payments), `school_cycle_enum` (classes.cycle) — **18 columns**.
- The redundant per-table CHECKs from 618/619/620 are dropped (the enum now enforces the domain) and re-created `NOT VALID` on downgrade. `classes.level_band` + the quiz `subject`/`level_band` CHECKs are intentionally left as String+CHECK (shared, open-ish).
- `vw_invoice_balance` (the only view selecting a converted column, `invoices.currency`) is dropped + recreated around the conversion with its exact `1c42d3e4f5a6` definition. Plain b-tree indexes on converted columns are auto-rebuilt by `ALTER TYPE`; no partial-index predicates reference these columns.
- Models updated to `PgEnum(..., name="*_enum", create_type=False, values_callable=_enum_values)` matching the project's 40+ other enum columns (games, lms, erp, billing, budget, micro_school, financial_health, onboarding). `taxonomy.py` remains the single source of truth (migration enum values verified equal to the taxonomy).
- Statically validated: `py_compile` clean on all touched files + the migration; enum values ↔ taxonomy parity; all 18 superseded CHECKs accounted for; **Alembic head `20260622`, chain `617→622` linear — *as of pass 4*** (pass 5 extends the coherent chain to `617→625`; see below). (DB-less sandbox — run `make migrate` to execute.)

**Done — pass 5 (Moroccan `taxonomy.py` rewrite + follow-ups A1–A3, B1, B3, B4):**

> Taxonomy decisions, the four-axis model, French→Moroccan migration maps, and remaining TODOs are documented in **`EDUCATION_TAXONOMY.md`** (the taxonomy single-source-of-truth doc); `app/models/taxonomy.py` is the code SoT.

- **Taxonomy rewritten to the Moroccan national system (MEN)** *(code SoT done; the data/migration/seed propagation is task 13 below)*. `SchoolCycle` = `prescolaire`/`primaire`/`college`/`lycee` (previous `maternelle` → `prescolaire`; the `informel` cycle **dropped** — informal education is modeled by `MicroSchool` + `MicroSchoolType`, not a class cycle). `ContentLevelBand` = `PS`/`MS`/`GS`, `1AEP`…`6AEP` (detailed), plus `1AC`/`2AC`/`3AC`, `TC`/`1BAC`/`2BAC` (codes kept so data validates). `ContentSubject` = Moroccan-official combined forms (`physique_chimie`, `svt`, `histoire_geo`, …; dropped `german`/`spanish` and the redundant `physics`/`chemistry`/`biology`/`history`/`geography` split forms). New `MicroSchoolType` = `rawd`/`msid`/`non_formel`/`general`. **Collège/lycée niveau→matière detail, `amazigh` + `quranic` subjects, and msid Quranic (hifz) levels are intentionally left TODO** (see EDUCATION_TAXONOMY.md §5–§7, §10).
- **A1 — `GameDifficulty` consolidated** onto `taxonomy.DifficultyLevel` (duplicate enum deleted; `games.py` + `game_service.py` validators point at `DifficultyLevel`). Verified no `class GameDifficulty` remains.
- **A2 — Budget cached-aggregate self-heal**: `budget_service.recompute_budget_rollups(...)` recomputes `allocated_amount`/`remaining_amount` (from allocations) and `spent`/`remaining` (from the `budget_transactions` ledger), wired into `approve_request` + `record_transaction` (idempotent), plus a public repair method. *Validate with the budget test suite — money logic, not runnable in a DB-less sandbox.*
- **A3 — `RetentionMetric` relabelled** as an *enrollment* metric (no `currency`); docstring corrected. Physical move to an analytics module deferred.
- **B1 — Non-curriculum `subject` overloads renamed** (migration `20260623_rename_subject_overloads`): `conversations.subject` → `subject_line`, `writing_attempts.subject` → `topic`. *These stay `String` (genuine open user input — message subject line / essay topic).* The other 8 `subject` columns are genuine curriculum and keep the name. *(Client field renames are task 16; a `seed_extensions.py` WritingAttempt `subject=` leftover remains — folded into task 13's seed remap.)*
- **B4 — `payment_proofs` dropped** (migration `20260624_drop_payment_proofs`): table + `PaymentProof` model + relationship + seed removed (was seeded but had no repo/service/API). Downgrade recreates the original schema.
- **B3 — `micro_budgets` → `school_budgets`** / `MicroBudget` → `SchoolBudget` (migration `20260625_rename_school_budgets`), per §10.2 — table + model + repo + service + reports + seed renamed (a *formal-school* budget; the `micro_` prefix was the misuse).
- **EDUCATION_TAXONOMY.md** authored — the decision doc capturing the enum-vs-free-text rule, the four axes, the niveau→matière mapping, the French→Moroccan data maps (§8), and the pending propagation (§10).
- **Migration chain `617 → 625`** for passes 1–5 (9 migrations); **task 13 extends it to `617 → 627`** (below). All `py_compile` clean; statically validated (DB-less sandbox).

**✅ Task 13 (B2) — DONE: `subject`/`level_band` promoted to native Moroccan enums.**

The stale French-valued `20260626` draft was **rewritten to the Moroccan vocabulary** + a defensive French→Moroccan remap (safe on a fresh *or* already-seeded DB); **`20260627`** added for Phase 2 + `MicroSchool.type`:
- *Phase 1* (`20260626`): `content_subject_enum`/`content_level_band_enum` on `content_items`, `quizzes`, `question_bank_items`, `classes.level_band`.
- *Phase 2* (`20260627`): `resources.subject`, `difficulty_adaptations.subject` → `content_subject_enum`. **Excluded:** `timetable_slots` (own activity redesign) and `men_curricula` (own official MEN vocabulary).
- `MicroSchool.type` (`micro_school_type_enum`: rawd/msid/non_formel/general) + free-text `type_detail` (user-input exception, only for `general`).
- Moroccan codes propagated across all seeds, the `repositories/lms.py` class-label parser (tokenised; French + Moroccan → Moroccan; track suffixes like `2BAC-PC` no longer collide with `cp`), `mock_provider`, `import_story_assets`, and ~18 test files; `seed_extensions.py` WritingAttempt `subject` → `topic` fixed.
- Validated: compileall clean; enum↔taxonomy parity; **single Alembic head `20260627`**; parser unit cases pass; **zero invalid level_band/subject on enum columns**. Run `make migrate && make seed` + `pytest` to execute on a DB.

**Queued — NOT started, in recommended order (master tasks 14–17):**

- **14 — Soft-delete policy** — add `SoftDeleteMixin` + **query filtering** (read paths must exclude soft-deleted, not just add a column) to the **audit set** (e.g. ContentItem) **+ financial set** (e.g. Invoice/Submission).
- **15 — i18n cutover (backend)** — switch the other 8 bilingual models' serializers to `tr(...)`, then drop the legacy `*_fr/_ar/_en` columns; per-concept `level` consolidation/renames. *(Language decision: status quo + translations.)*
- **16 — Client field renames (web + mobile)** — propagate B1 (`subject_line`/`topic`), B3 (`school_budgets`), the difficulty-uppercase selectors, and the new Moroccan `subject`/`level_band` enum values to both clients.
- **17 — Mobile i18n** — externalize the remaining **340** hardcoded strings (also fix screens hardcoding Arabic literals — real defects, not just untranslated).

**Deferred to their own sub-tasks:** `timetable_slots` activity-model redesign (slot = `activity_type` + 0..N matières or free-text title + assignment target); Moroccanising residual free-text level references (`fee.applies_to_level`, `programs.level`, `level_age_mappings` codes). *(Possible B1 leftover to verify: communication/Conversation `subject` vs `subject_line` in tests.)*

**Open TODOs (deliberately out of scope):** collège/lycée niveau→matière detail; `amazigh` + `quranic` subjects; msid Quranic (hifz) levels; `MicroSchool.type_detail` UX.

**Validate in VS Code:** `make migrate` (now `617→627`) → `make seed` → `pytest -q tests/security tests/unit/repositories/test_level_band_parser.py`.

---

## 10. Naming conventions — `micro` / `macro` and ERP alignment

**Core rule: a name prefix should name a *thing* (a domain, tenant, or entity), never a *size adjective*.** This is the same trap as the overloaded `subject` column — a prefix that means different things in different places, or that encodes scale, is unsearchable and ages badly.

1. **`micro_*` is reserved for the informal micro-school sector** — `MicroSchool`, `MicroGroup`, `MicroEnrollment`, `MicroPayment`, `MicroResource`, `MicroProgressLog`, and the `Micro*` enums. Here "micro" = *micro-école*, a real sector/tenant noun. **Correct usage — keep.**
2. **`MicroBudget`/`micro_budgets` is the misuse** — it is a *formal-school* budget (`SchoolScopedMixin`, "School budget envelope for a given academic year"). "micro" there means "small envelope" and collides with the sector meaning. → rename **`school_budgets`** (see §11).
3. **Do not introduce `macro_*`.** In ERP "macro" drifts toward "org-wide/consolidated," but a size adjective as a prefix is unsearchable. A layer above a single school (network / franchise / group) must be named by the **entity**: `Organization`, `SchoolGroup`, `Network`, or `Tenant` — never `macro_*`.
4. **Where neither is needed** — scale is already carried by the relationship hierarchy and by document nouns:
   - Aggregate / analytics rows → name by *what's measured* (`FinancialSnapshot`, `RetentionMetric`, `CashflowForecast`), not by scale.
   - Granular / line items → name by the *entity* (`InvoiceItem`, `BudgetTransaction`, `Installment`), not "micro".
5. **ERP alignment** — lean on the two standard ERP axes: the **entity hierarchy** (Organization → School → Class → Student) and **document types** (Invoice, Payment, Budget, Allocation, Request, Transaction/Ledger). Qualify by **sector/tenant type** when there is a real distinction (`formal` school vs `micro`-school) — never by size.

**One-line convention to adopt:** *informal sector → `micro_*`; formal sector → unprefixed or `school_*`; aggregates → named by metric; future super-tenant → `organization_*` / `school_group_*`, never `macro_*`.*

---

## 11. Agreed follow-ups (pass 5 — decided with owner)

Sequenced **safe → breaking**. Each breaking item needs an Alembic migration + schema/API + web/mobile updates + reseed, validated with `make migrate && make seed`. **Status legend:** ✅ done · ⏳ not started (master task #).

**A. Safe / non-breaking (done first):**

- ✅ **A1 — Consolidate `GameDifficulty`** onto `taxonomy.DifficultyLevel`: duplicate enum deleted in `games.py`; `validate_difficulty` points at `DifficultyLevel`. *(Done — see §9 pass 5.)*
- ✅ **A2 — Guard budget cached-aggregate drift:** `SchoolBudget.allocated_amount/remaining_amount` and `BudgetAllocation.spent/remaining` are denormalized sums of `BudgetTransaction`. Recompute-on-write self-heal (`recompute_budget_rollups`) funnels mutations through one path so they cannot diverge. *The one real correctness risk in the financial domain.* *(Done — validate with budget tests.)*
- ✅ **A3 — Relabel `RetentionMetric`:** an *enrollment* metric (student counts, no `currency`); docstring corrected. Physical move to an analytics module deferred. *(Done.)*

**B. Breaking (migration + clients):**

- ✅ **B1 — Rename the two non-curriculum `subject` columns** (the only true overloads; the other 8 `subject` columns are genuine curriculum and stay): `conversations.subject` → `subject_line`; `writing_attempts.subject` → `topic`. *(Done — migration `20260623`. Client field names = task 16; a `seed_extensions.py` WritingAttempt `subject=` leftover folds into task 13's seed remap.)*
- ✅ **B2 — Promote `subject` / `level_band` to native Moroccan enums (master task 13) — DONE.**
  - *Phase 1* (`20260626`, rewritten from the stale French draft to Moroccan values + a defensive French→Moroccan remap): `content_items`, `quizzes`, `question_bank_items`, `classes.level_band` → `content_subject_enum` / `content_level_band_enum`.
  - *Phase 2* (`20260627`): `resources.subject`, `difficulty_adaptations.subject` → `content_subject_enum`. **`timetable_slots`** deferred to its own activity redesign; **`men_curricula`** kept on its own official MEN vocabulary (not forced onto `ContentSubject`, per decision).
  - Added **`MicroSchool.type`** (`micro_school_type_enum`) + free-text **`type_detail`** (user-input exception, only for `general`). Moroccan codes propagated to all seeds, the `repositories/lms.py` parser, `mock_provider`, `import_story_assets`, and ~18 test files. Validated; single head `20260627`.
- ✅ **B3 — Rename `micro_budgets` → `school_budgets`** (and `MicroBudget` → `SchoolBudget`), per §10.2 — table + model + repo + service + reports + seed. *(Done — migration `20260625`.)*
- ✅ **B4 — Resolve `PaymentProof`:** dropped the table + model + seed (was seeded but had no repo/service/API). *(Done — migration `20260624`. Re-introduce when a payment-verification flow is wired.)*

**Other not-started follow-ups (master tasks 14–17):**

- ⏳ **14 — Soft-delete policy:** `SoftDeleteMixin` + read-path query filtering on the **audit set** (e.g. ContentItem) **+ financial set** (e.g. Invoice/Submission).
- ⏳ **15 — i18n cutover (backend):** switch the other 8 bilingual models' serializers to `tr(...)`, drop the legacy `*_fr/_ar/_en` columns; per-concept `level` consolidation/renames.
- ⏳ **16 — Client field renames (web + mobile):** propagate B1/B3 renames, difficulty-uppercase, and the new `subject`/`level_band` enum values to both clients.
- ⏳ **17 — Mobile i18n:** externalize the remaining 340 hardcoded strings (incl. screens hardcoding Arabic literals).

**Not doing (considered, left as-is):** `currency` repeated on 9 tables (correct by design — every amount self-describes); `MicroPayment` vs `Invoice` duplication (intentional — two tenancy models). Revisit only if a shared payment abstraction is needed.
