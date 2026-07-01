# Handoff — Cowork session → Claude Code (VS Code)

> Continuation of `PRODUCT_QUALITY_PASS.md` + `CODEX_RUN_PROMPT.md`.
> Ran **code-only** in a sandbox **without Flutter / Docker / a database**.
> Validation that needs `flutter` or `make seed` must run in VS Code (see §2).

---

## 1. What changed (code, statically checked — not executed)

### Nav + role guards (web + mobile)
- GoRoute **role-metadata** guard + DIR/ADM split + `/reports` consistency were already done (Codex) — verified.
- **EDUCATOR parity**: added to `/content`, `/messages`, `/calendar`, `/announcements` on **both** clients (mobile `app_router.dart` `_routeRoles` + `shell_screen.dart`; web `Layout.tsx`). Enriched EDUCATOR primary routes; added a `/compliance` nav entry (DIR/ADM).
- **`/student/games` hub**: mobile had a complete but **unwired** `MiniGamesScreen` — added the `/student/games` route, role metadata, and a `shell.games` nav entry (fr/ar/en). Now at parity with web.
- **`/results` vs `/progress`**: mobile relabeled to match web's clearer wording — `shell.progress` → "My Progress" and a new `shell.parentProgress` ("Children's Progress") for `/parent/progress` (was colliding on one label).

### Seed + CMS content audit (`backend/app/seed.py`)
- Persona matrix was already seeded (SUP, CONTENT_MGR, informal STD via Codex, formal STD at every level, teacher links, `seed_class_content_assignments`).
- **D3 gap fixed**: no content was tagged `CP`/`CE2`/`3eme`, and CM2/Terminale had **zero** published content → demo students saw empty libraries. Audited every `ContentItem`; re-leveled the orphaned Arabic-alphabet item (`primaire`→`CP`); added a level-appropriate library so **every** demo class has content:
  - Per-level published platform items now: CP=3, CE2=3, CM2=3, 6eme=5, 3eme=3, Terminale=3 (mix of math/french/arabic/science/physics/philosophy, fr + ar).
  - The existing assignment loop auto-attaches them, so Amina(CP), Karim(CE2), Leila(CM2), Mehdi(3eme), Sara(Terminale) each see a **distinct** library.
  - ⚠️ **These French level codes (`CP`/`CE2`/`CM2`/`6eme`/`3eme`/`Terminale`) are now superseded** by the Moroccan taxonomy and are **pending remap** to `1AEP…6AEP` / `1AC…3AC` / `TC` per `EDUCATION_TAXONOMY.md` §8 (master task 13 — seed Moroccan remap).

### Tests (written, not run — no DB here)
- `backend/tests/security/abac/test_abac_content_scope.py` — 10 ABAC tests: STD/PAR can't read/stream/progress/complete an unassigned `content_item` by valid id (404); list returns only assigned ids; teacher library filtered to taught level bands. Uses the existing `tests/security/conftest.py` fixtures (`client`, `student_token`, `teacher_token`, `parent_token`, `_security_session`).
- `backend/tests/unit/repositories/test_level_band_parser.py` — DB-free unit tests for `_level_bands_from_class_label` (validated: `6eme-A`→{6eme}, `CP-A`→{CP}, etc.).

### Content taxonomy — enum instead of free strings (`subject` / `level_band`)

> **⚠️ Superseded by the taxonomy/enum initiative (passes 4–5) — see `EDUCATION_TAXONOMY.md` + `BACKEND_DB_AUDIT.md` §9–§11.** This section describes the *original* String+CHECK approach (migration 617). It has since evolved: the enums were re-homed from `lms.py` into a single SoT module **`app/models/taxonomy.py`**, the closed sets were **promoted to native PG enums** (difficulty/language/currency/cycle = migration 622), and `taxonomy.py` was **rewritten to the Moroccan national system (MEN)** — `1AEP…6AEP`, `PS/MS/GS`, `physique_chimie`/`svt`/`histoire_geo`, `MicroSchoolType`, etc. The `subject`/`level_band` native-enum promotion (B2) is **not yet done** (master task 13) — a drafted migration `20260626` is stale (hardcodes the old French level bands). The French codes below are therefore **pending remap to Moroccan codes** per `EDUCATION_TAXONOMY.md` §8.

- `ContentItem.subject` / `level_band` (shared with `Quiz`) were free `String(50)` while the project uses enums elsewhere (`RoleCode`, `*_status_enum`). Added canonical Python enums **`ContentLevelBand`** + **`ContentSubject`** *(originally in `app/models/lms.py`; now in `app/models/taxonomy.py`)*.
- Enforced at **API layer**: `field_validator`s in `app/schemas/content/cms.py` (`CmsContentCreate/UpdateRequest`) reject non-canonical `subject`/`level_band` (422).
- Enforced at **DB layer**: migration `alembic/versions/20260617_content_taxonomy_check.py` adds CHECK constraints on `content_items` (`NOT VALID` → existing rows untouched, new writes enforced; `VALIDATE CONSTRAINT` later once data is clean — the seed already is).
- *(Original rationale, now superseded by native enums):* kept the columns `String` so seeds/imports and the shared `Quiz` write the same vocabulary via a CHECK. **Validate with `make migrate`** — but note `make migrate` is **not safe until the stale `20260626` is fixed** (task 13).

### Mobile i18n
- Scanner / CI guard: `mobile/scripts/i18n_scan.mjs` → `make mobile-i18n-scan` / `make mobile-i18n-check`.
- **Use the project's own skills** in `.ai/skills/` for the remaining Dart work: `effective-dart` (style), `flutter-riverpod` (`ConsumerWidget`/`ref` for the `t` accessor), `flutter-testing` + `flutter-mocktail` (widget/provider tests), `flutter-code-review` (PR checklist).
- **4 screens fully externalized** as the proven pattern (enforced count 357→340): `timetable_generate_screen`, `forgot_password_screen`, `reset_password_screen`, `register_screen` (the last needed the import + `t` added — template for `StatelessWidget`/no-`ref` cases).

### Static checks that PASSED in-sandbox
- `python3 -m py_compile` on `seed.py` + both test files — OK.
- `web` `npm run i18n:check` — green (en=2433, ar=2453, aligned).
- Mobile `app_localizations.dart` **fr/ar/en at perfect parity: 740 / 740 / 740**, zero diffs.
- Brace/paren balance OK on every edited Dart file.

---

## 2. Validate on your machine (could NOT run here)

```bash
cd <repo>
cd mobile && flutter analyze && flutter test && dart format .
make up && make migrate && make seed                 # needs .env
cd web && npm run i18n:check && npm run typecheck && npm run lint && npm run build
cd ../backend && pytest -q tests/security/abac/test_abac_content_scope.py \
                          tests/unit/repositories/test_level_band_parser.py
```
`flutter analyze` may ask for trailing commas on edited maps → `dart format` fixes it.

---

## 3. Remaining mobile i18n — 340 strings, ratchet the guard

`make mobile-i18n-scan` lists every remaining string by file/line. Biggest: `two_factor_setup_screen` (47), `profile_screen` (32), `register_steps` (26), `invoice_detail_screen` (25), `question_bank_screen` (23), `login_screen` (21).

Pattern (see the 4 cleared screens):
1. `import 'package:ecole_platform/l10n/app_localizations.dart';`
2. In build: `final t = AppLocalizations.of(ref);` (needs a `WidgetRef` — `ConsumerWidget`/`ConsumerState`; convert plain `StatelessWidget`/`StatefulWidget`, as done in `register_screen`).
3. Replace literal → `t.t('area.key')`; drop `const` on that widget; keep `border: const OutlineInputBorder()`.
4. Add the key to all three blocks (`fr`/`ar`/`en`) — keep the 740/740/740 parity.
5. `flutter analyze` per screen; tighten `ENFORCED_DIRS` in `i18n_scan.mjs` as each area clears.

**Real bug, not just untranslated:** some screens hardcode **Arabic** literals (e.g. `"مسح الكل"`, `"حذف"`) — they never switch language. Treat as defects.

## 4. Other follow-ups
- **Arabic review**: all AR keys (web 229 + mobile additions) need a native-speaker pass.
- **`/results` vs `/progress`** labels: I aligned wording, but confirm live that each screen's content matches its new label (Results = report card; My Progress = grades/content/activities/attendance dashboard; Passport = skills).
- **Asset *read* endpoint**: `get_content_asset` (read) has the STD/PAR assignment guard — the new tests cover get/stream/progress/complete; add an explicit asset-read 404 case if you seed assets.
