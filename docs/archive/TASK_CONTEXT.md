# TASK CONTEXT - Academic Program Management / Student Academic History

Derniere mise a jour: 2026-04-30.

Ce fichier est l'etat courant pour continuer le travail sans relire tout `Conversation_Claude_Cowork.txt`.

## Regle Codex de tracabilite

Lire aussi `CODEX_TRACEABILITY.md`.

A partir de maintenant:

- `TASK_CONTEXT.md` garde l'etat courant, les prochaines etapes et les commandes a lancer.
- `History_claude.md` garde la memoire historique de la conversation Claude.
- `CODEX_TRACEABILITY.md` garde le journal chronologique des actions Codex.

Apres chaque changement important, ajouter une note courte dans `CODEX_TRACEABILITY.md` avec:

- l'action effectuee;
- les fichiers touches;
- la verification faite ou impossible;
- les risques/restes a faire.

## Etat global

Le chantier "Academic Program Management & Student Academic History" a ete implemente en plusieurs phases:

- Phase 1: backend foundation G49.
- Phase 2: web admin, mobile read-only, reporting filters.
- Phase 3: program versions, equivalences, academic snapshots, eligibility rules.
- Follow-up Phase 3: pages admin versions/rules, tests frontend Phase 3, correction `min_attendance_rate` avec `academic_year_id`.

L'arbre Git n'est pas propre:

- 39 fichiers suivis modifies.
- 43 nouveaux fichiers code/tests non suivis.
- fichiers racine non suivis: `Conversation_Claude_Cowork.txt`, `History_claude.md`, `TASK_CONTEXT.md`, `ecole-platform-dev.zip`.
- `git diff --check` ne retourne aucune erreur whitespace.

Important: la phase G49/G50 stable est maintenant verifiee. La prochaine feature active est le transcript (Phase 3.5), dont une premiere tranche backend + point d'entree web JSON a ete demarree le 2026-04-30.

## Git actuel

- Branche: `main`
- HEAD local: `96d98c1 Add technical decisions and engineering justifications document`
- `origin/main`: `e9bafe0 feat(k8s): enhance kubeconfig setup with error handling and validation`
- Derniers commits notables vus:
  - `96d98c1` Add technical decisions and engineering justifications document
  - `e9bafe0` feat(k8s): enhance kubeconfig setup with error handling and validation
  - `2bc6417` Refactor code for improved readability and consistency
  - `a8dc64a` Add Phase 2 TODO checklist...

## Ce qui est code

### Backend

Migrations ajoutees:

- `backend/alembic/versions/9d9968735a7b_g49_program_management_and_history.py`
  - `programs`;
  - nullable `enrollments.program_id`;
  - `program_assignment_events`;
  - indexes;
  - append-only trigger.
- `backend/alembic/versions/cb375ca25f1b_g50a_program_versions.py`
  - `program_versions`;
  - nullable `program_version_id` sur enrollments/events;
  - backfill version `1.0`.
- `backend/alembic/versions/ab873f7d5708_g50b_program_equivalences.py`
  - `program_equivalences`.
- `backend/alembic/versions/72e15d401f00_g50c_academic_snapshots.py`
  - `academic_snapshots` JSONB.
- `backend/alembic/versions/748989a9f381_g50d_eligibility_rules.py`
  - `eligibility_rules`.

Chaine Alembic attendue:

```text
f4e5d6c7b8a9
  -> 9d9968735a7b
  -> cb375ca25f1b
  -> ab873f7d5708
  -> 72e15d401f00
  -> 748989a9f381
```

Modeles/services/endpoints:

- `Program`, `ProgramVersion`, `ProgramEquivalence`, `AcademicSnapshot`, `EligibilityRule`.
- `Enrollment` et `ProgramAssignmentEvent` etendus avec `program_id` / `program_version_id`.
- `ProgramService`: CRUD programs, versions, equivalences, assign program, history/timeline/current, admin enrollments.
- `AcademicSnapshotService`: creation/list/get/delete snapshot.
- `EligibilityService`: rules CRUD et evaluation.
- `ERPService.create_enrollment`: accepte maintenant optional `program_id`.
- Analytics/attendance/gradebook: filtre `program_id`.
- Permissions ajoutees/etendues pour programme/enrollments.
- OpenAPI docs modifies: `backend/openapi.json`, `backend/docs/openapi.json`, `backend/docs/api.html`.

Endpoints importants:

- `GET /programs`
- `GET /programs/{program_id}`
- `POST /programs`
- `PATCH /programs/{program_id}`
- `GET /programs/{program_id}/versions`
- `POST /programs/{program_id}/versions`
- `PATCH /programs/{program_id}/versions/{version_id}`
- `POST /enrollments/{enrollment_id}/program`
- `GET /admin/enrollments`
- `GET /students/{student_id}/program-history`
- `GET /students/{student_id}/academic-timeline`
- `GET /students/{student_id}/current-program`
- `GET /program-equivalences`
- `POST /program-equivalences`
- `DELETE /program-equivalences/{id}`
- `POST /academic-snapshots`
- `GET /academic-snapshots/{id}`
- `DELETE /academic-snapshots/{id}`
- `GET /students/{student_id}/snapshots`
- `GET /eligibility/rules`
- `POST /eligibility/rules`
- `DELETE /eligibility/rules/{rule_id}`
- `GET /students/{student_id}/eligibility`

### Web

Pages/composants ajoutes:

- `ProgramsPage`: CRUD programmes.
- `AssignProgramDialog`: assign/change program + version picker.
- `EnrollmentsPage`: list admin avec filtre "missing program" + bouton assign.
- `StudentAcademicHistoryPage`: current program, timeline, history events, snapshots, eligibility tile.
- `ProgramEquivalencesPage`: CRUD equivalences.
- `ProgramVersionsPage`: CRUD versions par programme.
- `EligibilityRulesPage`: CRUD simple delete-and-recreate rules.
- `EligibilityCheckTile`: run eligibility check.

Routing/navigation:

- routes admin ajoutees dans `web/src/app/routes.ts`, `LazyPages.ts`, `App.tsx`.
- sidebar mise a jour dans `web/src/shared/ui/Layout.tsx`.

Reporting UI:

- filtre programme dans analytics dashboard.
- filtre programme dans attendance analytics.
- filtre programme dans gradebook.

i18n:

- locales EN/FR/AR modifiees.

### Mobile

Ajouts Flutter:

- domain entity `Program`, `ProgramSummary`, `ProgramAssignmentEvent`, `AcademicTimelineEntry`, `CurrentProgram`, `AcademicSnapshotSummary`.
- repository interface + implementation Dio/CacheStore pour historique, snapshots et transcripts PDF.
- mappers DTO.
- providers Riverpod.
- screen read-only academic history.
- carte d'actions transcript avec boutons libelles.
- viewer PDF Flutter in-app pour transcript courant et snapshots.
- section snapshots academiques avec actions ouvrir/partager.
- reusable current program card.
- route `/students/:studentId/academic-history`.
- i18n inline.
- tests repository + widget.

## Points importants de design

- Les changements de programme sont append-only dans `program_assignment_events`.
- Les transferts utilisent soft-replace:
  - ancien enrollment -> `transferred`;
  - nouveau enrollment actif avec nouveau programme/version.
- `POST /enrollments` accepte `program_id` uniquement pour creation initiale.
- Pour modifier un enrollment existant, utiliser `POST /enrollments/{id}/program`.
- Le backfill des anciens enrollments reste manuel via `/admin/enrollments` + filtre `missing_program`.
- Les versions/rules sont considerees comme edition annuelle/manuelle, pas comme workflow frequent.
- `academic_snapshots` existe.
- Phase 3.5 transcript commencee:
  - backend `TranscriptService` ajoute;
  - endpoints JSON ajoutes pour preview live et rendu depuis snapshot;
  - web admin: preview HTML modale ajoutee + telechargement JSON en secours.
- Decision produit/technique actuelle:
  - transcript web en HTML-first;
  - PDF ensuite via la meme base de rendu.
  - mobile: acces transcript depuis l'ecran historique academique;
  - current transcript + snapshot transcript disponibles en PDF;
  - decision retenue: viewer PDF in-app + partage secondaire, au lieu de share-only.

## Etat de verification

Deja observe dans le transcript:

- plusieurs checks AST backend OK;
- Alembic single head OK a plusieurs moments;
- plusieurs `tsc --noEmit` OK;
- eslint cible OK;
- Vitest bloque dans le sandbox a cause du binaire Rollup Linux manquant et npm registry bloque;
- pytest/alembic upgrade non executes faute de Postgres/pip;
- mobile transcript PDF:
  - `flutter analyze lib/features/student/program_history_screen.dart lib/features/student/transcript_pdf_screen.dart lib/features/student/program_history_provider.dart lib/data/repositories_impl/program_repository_impl.dart lib/domain/repositories/program_repository.dart test/unit/program_repository_test.dart test/widget/program_history_screen_test.dart` -> OK;
  - `flutter test test/unit/program_repository_test.dart test/widget/program_history_screen_test.dart` -> OK;
  - `flutter test` complet -> `All tests passed!`

Derniere phase inachevee:

- Apres ajout de `ProgramVersionsPage`, `EligibilityRulesPage`, tests frontend Phase 3, correction `min_attendance_rate`, Claude a commence la verification puis a ete coupe.
- Ne pas considerer cette derniere phase comme CI-green tant que les commandes ci-dessous n'ont pas ete lancees.

## Commandes a lancer maintenant

### Backend

```bash
cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev/backend
alembic heads
alembic upgrade head
pytest tests/unit/services/test_program_service.py
pytest tests/integration/test_program_g49.py
pytest tests/integration/test_program_g50_phase3.py
pytest
```

### Web

```bash
cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev/web
npm run typecheck
npm run lint
npm test -- tests/unit/features/ProgramsPage.test.tsx \
  tests/unit/features/AssignProgramDialog.test.tsx \
  tests/unit/features/EnrollmentsPage.test.tsx \
  tests/unit/features/StudentAcademicHistoryPage.test.tsx \
  tests/unit/features/ProgramEquivalencesPage.test.tsx \
  tests/unit/features/ProgramVersionsPage.test.tsx \
  tests/unit/features/EligibilityRulesPage.test.tsx \
  tests/unit/features/EligibilityCheckTile.test.tsx
npm test
```

### Mobile

```bash
cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev/mobile
flutter pub get
flutter analyze
flutter test test/unit/program_repository_test.dart
flutter test
```

### Git sanity

```bash
cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev
git diff --check
git status --short
```

## Decoupage de commit recommande

1. transcript backend/web
   - backend transcript service, endpoints HTML/PDF, templates report
   - web admin transcript preview/print/PDF

2. mobile transcript access
   - snapshots academiques cote mobile
   - viewer PDF in-app
   - UX revue de `AcademicHistoryScreen`
   - tests mobile associes

3. docs de reprise
   - `TASK_CONTEXT.md`
   - `CODEX_TRACEABILITY.md`
   - `History_claude.md` si modifie dans une autre session

## Etat confirme apres review scope + human pass

- Les docs `TASK_CONTEXT.md` et `CODEX_TRACEABILITY.md` sont coherents avec l'etat G49/G50 vert.
- Surface web admin confirmee:
  - `StudentAcademicHistoryPage` couvre current program, timeline, history, snapshots, eligibility.
- Surface mobile confirmee:
  - ecran et provider programme/historique en lecture seule;
  - pas encore de snapshots/eligibility cote mobile, ce qui reste coherent avec le scope mobile documente.
- Surface backend confirmee:
  - APIs programmes, versions, equivalences, snapshots, eligibility et history sont presentes et raccordees.
- Ecart produit principal restant:
  - transcript riche (PDF/HTML + UX complete) au-dessus des snapshots/historique.

## Prochaine etape recommandee

1. Continuer Phase 3.5 transcript:
   - impression / export PDF maintenant branche a partir du template HTML transcript;
   - prochaine sous-etape: finitions visuelles si besoin, pas nouvelle filiere de rendu.
2. Decision mobile recommandee:
   - exposer d'abord l'acces au PDF transcript sur mobile;
   - ne pas construire une preview transcript HTML complete dans Flutter tant que le besoin produit n'est pas confirme.
2. Verifier manuellement les parcours transcript:
   - `GET /students/{student_id}/transcript?academic_year_id=...&mode=preview`
   - `GET /students/{student_id}/transcript?academic_year_id=...&mode=snapshot`
   - `GET /academic-snapshots/{snapshot_id}/transcript`
   - bouton transcript dans `/students/:studentId/academic-history`
3. Ensuite seulement, etendre au mobile si la feature transcript doit y exister.
4. Decider quoi committer:
   - inclure code + tests;
   - probablement ne pas committer `Conversation_Claude_Cowork.txt`;
   - probablement ne pas committer `ecole-platform-dev.zip` sauf raison explicite;
   - garder ou non ces deux docs selon votre workflow.

## Prochaine feature: Transcript service (Phase 3.5)

Recommandation: faire le transcript service comme phase separee, apres validation des changements actuels.

Prompt recommande pour une prochaine session:

```text
You are working in /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev on the Ecole Platform ERP/LMS.

Goal: build Phase 3.5 Transcript Service on top of the already implemented academic_snapshots/programs/program_versions/program_equivalences system.

Before coding:
- Inspect existing backend services, models, schemas, PDF/export patterns, i18n conventions, and tests.
- Do not rewrite the existing academic program work.
- Preserve school_id tenant scoping and role/ABAC behavior.
- Treat AcademicSnapshot as the immutable source for transcript rendering when a snapshot is provided.
- Live recomputation is allowed only for preview mode and must be clearly marked as non-frozen.

Deliverables:
1. Backend TranscriptService that can render a student/year transcript from:
   - an AcademicSnapshot id; or
   - student_id + academic_year_id preview.
2. Transcript data schema with:
   - student identity summary;
   - school summary;
   - academic year;
   - enrollments/classes/periods;
   - program + program version;
   - resolved program equivalences when relevant;
   - grade summary;
   - attendance summary;
   - snapshot metadata if frozen.
3. API endpoints:
   - GET /academic-snapshots/{snapshot_id}/transcript
   - GET /students/{student_id}/transcript?academic_year_id=...&mode=preview|snapshot
4. Output format:
   - start with JSON/HTML if PDF infrastructure is unclear;
   - add PDF only if the repo already has a safe PDF/export pattern.
5. Tests:
   - service unit tests;
   - integration tests for auth, tenant isolation, snapshot mode, preview mode, missing data, and equivalence rendering.
6. Web:
   - add transcript action on StudentAcademicHistoryPage snapshots;
   - allow opening/downloading transcript result.

Constraints:
- No destructive migration.
- Do not create a new source of truth.
- Use existing response envelope helpers.
- Keep transcript rendering deterministic for snapshot mode.
- If PDF is added, verify Arabic/RTL and French labels do not break layout.

At the end, report:
- files changed;
- commands run;
- commands that could not run;
- remaining product decisions.
```

## Fichiers modifies non commites

### Fichiers suivis modifies

```text
backend/app/api/v1/admin.py
backend/app/api/v1/analytics.py
backend/app/api/v1/attendance_analytics.py
backend/app/api/v1/enrollments.py
backend/app/api/v1/gradebook.py
backend/app/api/v1/router.py
backend/app/core/permissions.py
backend/app/models/__init__.py
backend/app/models/erp.py
backend/app/repositories/analytics.py
backend/app/repositories/attendance_analytics.py
backend/app/schemas/erp.py
backend/app/services/attendance_analytics.py
backend/app/services/dashboard_analytics.py
backend/app/services/erp.py
backend/app/services/gradebook.py
backend/docs/api.html
backend/docs/openapi.json
backend/openapi.json
mobile/lib/app/providers.dart
mobile/lib/app/router.dart
mobile/lib/data/dto/mappers.dart
mobile/lib/l10n/app_localizations.dart
web/src/app/App.tsx
web/src/app/LazyPages.ts
web/src/app/routes.ts
web/src/features/analytics/AnalyticsDashboardPage.tsx
web/src/features/analytics/analytics.service.ts
web/src/features/attendance/AttendanceAnalyticsPage.tsx
web/src/features/attendance/attendance.service.ts
web/src/features/attendance/useAttendance.ts
web/src/features/gradebook/GradebookPage.tsx
web/src/features/gradebook/gradebook.service.ts
web/src/features/gradebook/useGradebook.ts
web/src/features/student/student.service.ts
web/src/shared/i18n/locales/ar.json
web/src/shared/i18n/locales/en.json
web/src/shared/i18n/locales/fr.json
web/src/shared/ui/Layout.tsx
```

### Nouveaux fichiers code/tests non suivis

```text
backend/alembic/versions/72e15d401f00_g50c_academic_snapshots.py
backend/alembic/versions/748989a9f381_g50d_eligibility_rules.py
backend/alembic/versions/9d9968735a7b_g49_program_management_and_history.py
backend/alembic/versions/ab873f7d5708_g50b_program_equivalences.py
backend/alembic/versions/cb375ca25f1b_g50a_program_versions.py
backend/app/api/v1/eligibility.py
backend/app/api/v1/programs.py
backend/app/api/v1/snapshots.py
backend/app/api/v1/student_academic.py
backend/app/schemas/programs.py
backend/app/services/academic_snapshot_service.py
backend/app/services/eligibility_service.py
backend/app/services/program_service.py
backend/tests/integration/test_program_g49.py
backend/tests/integration/test_program_g50_phase3.py
backend/tests/unit/services/test_program_service.py
mobile/lib/data/repositories_impl/program_repository_impl.dart
mobile/lib/domain/entities/program.dart
mobile/lib/domain/repositories/program_repository.dart
mobile/lib/features/student/program_history_provider.dart
mobile/lib/features/student/program_history_screen.dart
mobile/lib/features/student/widgets/current_program_card.dart
mobile/test/unit/program_repository_test.dart
web/src/features/admin/AssignProgramDialog.tsx
web/src/features/admin/EligibilityCheckTile.tsx
web/src/features/admin/EligibilityRulesPage.tsx
web/src/features/admin/EnrollmentsPage.tsx
web/src/features/admin/ProgramEquivalencesPage.tsx
web/src/features/admin/ProgramVersionsPage.tsx
web/src/features/admin/ProgramsPage.tsx
web/src/features/admin/StudentAcademicHistoryPage.tsx
web/src/features/admin/enrollments.service.ts
web/src/features/admin/programs.service.ts
web/src/features/admin/useEnrollments.ts
web/src/features/admin/usePrograms.ts
web/tests/unit/features/AssignProgramDialog.test.tsx
web/tests/unit/features/EligibilityCheckTile.test.tsx
web/tests/unit/features/EligibilityRulesPage.test.tsx
web/tests/unit/features/EnrollmentsPage.test.tsx
web/tests/unit/features/ProgramEquivalencesPage.test.tsx
web/tests/unit/features/ProgramVersionsPage.test.tsx
web/tests/unit/features/ProgramsPage.test.tsx
web/tests/unit/features/StudentAcademicHistoryPage.test.tsx
```

### Autres fichiers non suivis

```text
Conversation_Claude_Cowork.txt
History_claude.md
TASK_CONTEXT.md
ecole-platform-dev.zip
```

## Risques a garder en tete

- La derniere phase web n'a pas ete terminee par un rapport final de verification.
- Les tests frontend Phase 3 ont ete crees mais pas executes.
- Les migrations doivent etre testees sur PostgreSQL reel.
- Les fichiers OpenAPI generes doivent etre verifies pour coherence.
- Le rendu transcript n'existe pas encore.
- Les snapshots sont utiles surtout quand le Transcript service sera construit.
- `ecole-platform-dev.zip` est non suivi et peut etre un artefact local a exclure du commit.
