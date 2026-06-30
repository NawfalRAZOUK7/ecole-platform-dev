# Education Taxonomy — Decisions & Spec (Morocco)

> Single source of truth for the categorical vocabularies of the platform, aligned
> to the **Moroccan national education system (MEN)**. Code lives in
> `backend/app/models/taxonomy.py`; this doc records the **decisions, rationale,
> mappings, and TODOs** for traceability. Read together with `BACKEND_DB_AUDIT.md`
> (§10 naming, §11 follow-ups).

---

## 0. Status at a glance

| Area | State |
|------|-------|
| Core enum policy (closed→enum, free-text only for user input) | **Decided** |
| `taxonomy.py` rewritten to Moroccan taxonomy | **Done** (compiles) |
| difficulty / language / currency / cycle → native enums | **Done** (migration 622) |
| `taxonomy.py` itself rewritten to the Moroccan values | **Done** (code SoT) |
| subject / level_band **Phase 1** → native enums (content_items, quizzes, question_bank_items, classes) | **Done** — migration `20260626` rewritten to Moroccan values + defensive remap (task 13) |
| subject **Phase 2** → native enums (resources, difficulty_adaptations) | **Done** — migration `20260627` (task 13). `timetable_slots` deferred to its own activity redesign; `men_curricula` keeps its own MEN vocabulary |
| `MicroSchool.type` (+ optional free-text `type_detail`) | **Done** — migration `20260627` (task 13) |
| Moroccan codes propagated to migrations + seeds + runtime code + tests | **Done** (task 13) |
| Collège / lycée niveau→matière detail | **TODO** |
| Amazigh, Quranic subjects; msid Quranic levels | **TODO** |

---

## 1. Core principle — enums vs free text

**Closed, finite vocabularies are native PostgreSQL enums** (`PgEnum(..., values_callable=enum_values)`), never free strings. **Free text is allowed only where the value is genuinely open user input.**

**Closed → native enum:**

| Field(s) | Enum |
|----------|------|
| `difficulty` (game_configs, activities, quizzes, question_bank_items) | `difficulty_enum` |
| `language` (content_items, quizzes, micro_resources, school_applications) | `language_enum` |
| `currency` (9 financial tables) | `currency_enum` |
| `cycle` (classes) | `school_cycle_enum` |
| `subject` (content_items, quizzes, question_bank_items, resources, timetable_slots, difficulty_adaptations, men_curricula) | `content_subject_enum` |
| `level_band` (content_items, quizzes, question_bank_items, classes) | `content_level_band_enum` |
| `MicroSchool.type` | `micro_school_type_enum` |

**Free text (stays `String`) — legitimate open input:**

| Field | Why free text |
|-------|---------------|
| `writing_attempts.topic` | The essay topic a student writes about — open prose (renamed from `subject` in B1). |
| `conversations.subject_line` | A message-thread subject line typed by a user (renamed from `subject` in B1). |
| `MicroSchool.type_detail` *(to add)* | When `type = general`, the educator specifies *exactly* what kind of informal school it is — free text. Optional; only meaningful for `general`. |
| titles, names, descriptions, notes, addresses, etc. | Always open prose. |

Rule of thumb: **if the platform defines the allowed values, it's an enum; if the user defines the value, it's free text.**

---

## 2. The four axes (never conflate)

1. **Stage / cycle** — `SchoolCycle`: the broad education stage.
2. **Niveau (level)** — `ContentLevelBand`: the grade inside a stage.
3. **Matière (subject)** — `ContentSubject`: what is taught.
4. **Provider type** — `MicroSchoolType`: who runs an *informal* school and how.

A *rawd* = stage `prescolaire` **+** provider `rawd`. A *msid* ≈ stage préscolaire/primaire **+** provider `msid` **+** subject `quranic` (TODO). Mixing any two axes into one column is the mistake that produced `micro_budget` (see audit §10).

---

## 3. `SchoolCycle` — stage (formal classes)

`prescolaire`, `primaire`, `college` *(TODO detail)*, `lycee` *(TODO detail)*.

Renames the previous `maternelle` → `prescolaire`; the previous `informel` cycle is **dropped** — informal education is modeled by `MicroSchool` + `MicroSchoolType`, not as a class cycle.

---

## 4. `MicroSchoolType` — provider type (informal = micro-school)

"Informal school" **=** `MicroSchool` (educator-run, not institution-run). Types:

| Value | Meaning |
|-------|---------|
| `rawd` | Secular informal **kindergarten** (préscolaire), ages ~3–5; early literacy/numeracy/play. روض |
| `msid` | Traditional **Quranic** school, faqih-run; Quran memorisation + basic Arabic + Islamic ed. مسيد / kuttab |
| `non_formel` | **2e-chance / dropout reintegration**, ages ~9–22; remedial + vocational bridge. |
| `general` | Any other informal micro-school (soutien scolaire, alternative centre, …). |

**Decision (free-text exception):** `general` is intentionally vague, so `MicroSchool` gets an optional free-text **`type_detail`** for the educator to state exactly what it is. Enum for the closed set + free text for the open tail.

---

## 5. `ContentLevelBand` — niveau (Moroccan official codes)

**Détaillé (in scope now):**
- Préscolaire / rawd: `PS`, `MS`, `GS`
- Primaire (6 ans): `1AEP`, `2AEP`, `3AEP`, `4AEP`, `5AEP`, `6AEP`

**Codes kept so existing data validates, detail = TODO:**
- Collège: `1AC`, `2AC`, `3AC`
- Lycée: `TC`, `1BAC`, `2BAC`

**TODO:** msid Quranic memorisation stages (hifz levels).

The previous **French** codes (`CP…CM2`, `6eme…Terminale`, generic `maternelle/primaire/college/lycee`) are **replaced**; existing data is migrated via the map in §8.

---

## 6. `ContentSubject` — matière (Moroccan-official)

**In scope:** `arabic`, `french`, `english`, `math`, `activite_scientifique`, `svt`, `physique_chimie`, `histoire_geo`, `civic`, `philosophy`, `islamic`, `art`, `music`, `sport`, `informatique`, `technology`, `economics`, `accounting`, plus early-literacy helpers `arabic_letters`, `literacy`, `vocabulary`, and the teacher tag `pedagogy`.

**Removed (not needed):** `german`, `spanish`.

**TODO (add later):** `amazigh` (official since 2011), `quranic` (msid). Also the redundant split forms `physics`/`chemistry`/`biology`/`history`/`geography` are **dropped** in favour of MEN's combined `physique_chimie` / `svt` / `histoire_geo`.

---

## 7. Niveau → matière mapping (`CYCLE_SUBJECTS`)

Defined for **préscolaire** and **primaire** (collège/lycée = empty, TODO):

- **Préscolaire / rawd:** arabic, french, math, activite_scientifique, islamic, art, music, sport, arabic_letters, literacy, vocabulary.
- **Primaire:** arabic, french, english, math, activite_scientifique, islamic, histoire_geo, civic, art, music, sport, informatique, arabic_letters, literacy, vocabulary.

Used by validators / UI so a level only offers the matières that actually exist at that stage.

---

## 8. French → Moroccan migration mappings (seed + data migration)

**Levels:** `maternelle→GS` · `CP→1AEP`, `CE1→2AEP`, `CE2→3AEP`, `CM1→4AEP`, `CM2→6AEP` · `6eme→1AC`, `5eme→2AC`, `4eme→3AC`, `3eme→3AC` · `2nde→TC`, `1ere→1BAC`, `Terminale→2BAC` · generic `primaire→1AEP`, `college→1AC`, `lycee→TC`.

**Subjects:** `science→activite_scientifique` · `physics→physique_chimie`, `chemistry→physique_chimie` · `biology→svt` · `history→histoire_geo`, `geography→histoire_geo` · display-names `Français→french`, `Mathématiques→math`, `Sciences→activite_scientifique` · MEN `Sciences de la vie et de la terre→svt`, `Physique-Chimie→physique_chimie`, `Francais→french`.

**Cycle:** `maternelle→prescolaire`; `informel` classes → folded into `MicroSchool.type`.

> These mappings are awaiting final sign-off before the data propagation runs.

---

## 9. Work completed (this initiative)

- **Native-enum promotion** (migration 622): difficulty/language/currency/cycle → enums; superseded CHECKs dropped; `vw_invoice_balance` rebuilt.
- **A1** GameDifficulty consolidated → `DifficultyLevel`. **A2** budget cached-aggregate self-heal (`recompute_budget_rollups`). **A3** `RetentionMetric` relabelled (enrollment metric).
- **B1** `conversations.subject→subject_line`, `writing_attempts.subject→topic` (migration 623) — *free-text fields, kept String*. (Seed leftover in `seed_extensions.py` WritingAttempt still to fix.)
- **B4** `payment_proofs` dropped (migration 624).
- **B3** `micro_budgets→school_budgets` / `MicroBudget→SchoolBudget` (migration 625).
- **taxonomy.py** rewritten to the Moroccan taxonomy above (code SoT).

- **B2 / task 13 — DONE.** `subject` / `level_band` promoted to native **Moroccan** enums: Phase 1 (`20260626`, rewritten from the stale French draft to Moroccan values + a defensive French→Moroccan remap so it is safe on either fresh or already-seeded DBs) on content_items / quizzes / question_bank_items / classes; Phase 2 (`20260627`) on resources + difficulty_adaptations. Added **`MicroSchool.type`** (`micro_school_type_enum`) + free-text **`type_detail`**. Moroccan codes propagated across all seeds, the `repositories/lms.py` class-label parser (tokenised, French + Moroccan → Moroccan), `mock_provider`, `import_story_assets`, and ~18 test files. **Excluded:** `timetable_slots` (its own activity redesign) and `men_curricula` (own MEN vocabulary).

> **Coherent migration chain: `617 → 627`** (single Alembic head `20260627`). Statically validated (py_compile/compileall, enum↔taxonomy parity, parser unit cases, zero invalid enum values). Run `make migrate && make seed` + `pytest` to execute.

---

## 10. Propagation — status (task 13 DONE)

1. ✅ Migration value-lists set to Moroccan (`20260626` rewritten from the stale French draft; `20260627` added).
2. ✅ `MicroSchool.type` (`micro_school_type_enum`) + optional free-text `type_detail` (`20260627`).
3. ✅ **B2 Phase 2**: `resources.subject`, `difficulty_adaptations.subject` → `content_subject_enum`. **`timetable_slots`** moved to its own activity redesign (a slot = activity + 0..N matières or free-text title); **`men_curricula`** kept on its own official MEN vocabulary.
4. ✅ Models updated (`MicroSchool.type`/`type_detail`; `resources` + `difficulty_adaptations` `subject` → `PgEnum`).
5. ✅ Seeds + runtime code (`repositories/lms.py` parser, `mock_provider`, `import_story_assets`) + ~18 test files remapped to Moroccan; `seed_extensions.py` WritingAttempt `subject→topic` fixed.
6. ✅ Statically validated (py_compile/compileall, parity, single head `20260627`, parser tests). Run `make migrate && make seed` + `pytest` to execute on a DB.

**Deferred to their own sub-tasks:** `timetable_slots` activity-model redesign; the language architecture (decision: *status quo + translations*, lands in task 15).

**Open TODOs (unchanged):** collège/lycée niveau→matière detail; `amazigh` + `quranic` subjects; msid Quranic (hifz) levels; `MicroSchool.type_detail` UX.

---

## 11. Curriculum structure — Cycle → Niveau → Matière → Topics (backend SoT)

**Decision:** the official curriculum is modeled **in backend code** (not seed) as a
hierarchy, and enforced + served from there. Source of truth:
`backend/app/models/curriculum.py`.

**Terminology (kept strictly distinct):** `cycle` (stage) → `niveau`/`level`
(grade) → `matière` **= subject** (code field `subject`) → `sujet` = **`topic`**
(chapter inside a matière). The code never uses "subject" to mean a topic.

**Scope (decided with the product owner):** **PRIVATE / "formal" sector**,
**préscolaire + primaire** only. Depth = "structure now + representative topics"
(Option 1): the cycle→niveau→matière skeleton is complete & official; topic lists
are a sensible starter, expandable toward the full MEN programme.

**Modeled now:**
- Cycles: `prescolaire` (PS, MS, GS), `primaire` (1AEP–6AEP).
- Matières per niveau (private/trilingue): **French from préscolaire**; **English
  from 3AEP**; préscolaire + 1er cycle (1–2AEP) = arabic/french/math/activité
  scientifique/islamic/arts/sport + early-literacy; 2e cycle (3–6AEP) adds
  english, histoire-géo (الاجتماعيات), civic, informatique.
- Representative topics for core matières (math 1AEP–6AEP, plus arabic/french/
  science/histoire-géo samples).

**Enforced & exposed (backend layers, not just DB/seed):**
- `is_subject_valid_for_level()` + `ensure…` cross-field rule wired into the
  Pydantic schemas `CmsContentCreate/Update` and `QuizCreate/Update` — a content/
  quiz subject must be a matière taught at its niveau (out-of-scope levels are not
  over-constrained). Verified: `english@1AEP` rejected, `english@3AEP` ok,
  `french@PS` ok, `philosophy@6AEP` rejected.
- Read-only API `GET /curriculum`, `/curriculum/cycles`,
  `/curriculum/levels/{level}/matieres`, `/.../matieres/{subject}/topics`
  (`app/api/v1/lms/curriculum.py`) so the **frontend derives the official
  structure from the backend**.

**Sources (official MEN + sector practice):**
- Primaire = 6 yrs in 2 sub-cycles; French taught from 1AEP in public since
  2017/2018; social studies from the 2e cycle (3AEP).
  [Réforme / écoles pionnières (École branchée)](https://ecolebranchee.com/maroc-reforme-ecole-publique-pedagogies-structurees/) ·
  [Système éducatif au Maroc (Wikipédia)](https://fr.wikipedia.org/wiki/Syst%C3%A8me_%C3%A9ducatif_au_Maroc) ·
  [Nuffic — Morocco primary/secondary](https://www.nuffic.nl/en/education-systems/morocco/primary-and-secondary-education)
- Préscolaire 6 learning domains: [Cadre curriculaire préscolaire (MEN 2018, OMEP)](https://omepworld.org/wp-content/uploads/2025/05/MAR_MEN_2018_prescolaire-document-de-reference-et-d-orientation-pedagogique.pdf)
- Private/trilingue: French from préscolaire, English from primary (Cambridge):
  [École Trilingue Internationale (Globeducate)](https://www.globeducate.com/our-schools/morocco/ecole-trilingue-internationale) ·
  [Les Quatre Temps — trilingue dès la petite section](https://lesquatretemps.ac.ma/ecole-trilingue/)

**TODO (next versions):** public-sector mapping; collège/lycée; full official
topic lists (Option 2); amazigh + quranic matières; msid Quranic levels;
content `topic` field + per-class matière assignment UI.

### 11.1 Official titles + custom matières

- **Official titles**: every official matière now carries its MEN name in
  `curriculum.SUBJECT_TITLES` (AR/FR/EN), surfaced in the `/curriculum` tree and
  API (`subject_title()`).
- **Custom matières** (decided): a school's ADM/DIR can add **non-official**
  matières (e.g. "Chant", "Théâtre"), as many as they want. Model
  `CustomSubject` (`custom_subjects` table, per-school, slug `code` + user
  `title`), API `GET/POST/DELETE /custom-subjects` (writes role-gated).
- **Consequence (migration `20260628`)**: the 5 `content_subject_enum` columns
  (content_items, quizzes, question_bank_items, resources, difficulty_adaptations)
  were converted **enum → validated String** and the enum type dropped, so a
  custom slug can be stored in `subject`. Official matières are still the code
  SoT; validity = **official (curriculum) ∪ a school's custom rows**. Pydantic
  enforces the curriculum rule for *official* subjects only (custom bypass);
  **TODO**: a service-layer check that rejects a `subject` that is neither
  official nor a registered custom matière for the school (prevents typos).
- This is the concrete payoff of the "backend-governed, less-Alembic" direction:
  adding an official matière/level/topic is now a pure code edit; only true
  schema changes (the new table, the enum→String) needed a migration.
