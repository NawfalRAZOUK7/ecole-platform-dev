# CODEX TRACEABILITY

Derniere mise a jour: 2026-04-29.

Objectif: garder une trace courte, exploitable et chronologique de ce que Codex fait dans ce repo apres la reprise du travail depuis `Conversation_Claude_Cowork.txt`.

Ce fichier complete:

- `History_claude.md`: memoire historique de ce que Claude a fait.
- `TASK_CONTEXT.md`: etat courant + prochaines etapes.

## Regle de suivi

Apres chaque action importante, ajouter une note ici.

Une action importante inclut:

- creation ou modification de fichiers;
- lancement de commandes de verification;
- resultat d'un test, lint, build ou migration;
- decision technique;
- blocage ou limite d'environnement;
- changement de prochaine etape.

Format recommande:

```text
## YYYY-MM-DD - Courte description

- Action:
- Fichiers:
- Verification:
- Notes / risques:
```

## Etat initial Codex

Codex a repris le projet avec:

- `Conversation_Claude_Cowork.txt` comme transcript source;
- `History_claude.md` rempli comme memoire chronologique;
- `TASK_CONTEXT.md` rempli comme etat courant du projet;
- gros arbre de travail non commite sur backend, web et mobile;
- verification complete encore a faire localement: backend pytest/alembic, web vitest, mobile flutter.

## 2026-04-29 - Creation du journal Codex

- Action: creation de `CODEX_TRACEABILITY.md` pour servir de journal de suivi Codex.
- Fichiers:
  - `CODEX_TRACEABILITY.md`
- Verification: fichier cree via patch, pas encore de commande de test necessaire.
- Notes / risques:
  - Ce fichier doit etre maintenu a jour apres chaque changement important.
  - Il ne remplace pas `TASK_CONTEXT.md`; il garde le fil chronologique des actions Codex.

## 2026-04-29 - Liaison avec TASK_CONTEXT

- Action: `TASK_CONTEXT.md` doit maintenant pointer vers ce journal et rappeler la regle de suivi.
- Fichiers:
  - `TASK_CONTEXT.md`
  - `CODEX_TRACEABILITY.md`
- Verification: confirme par lecture rapide de `CODEX_TRACEABILITY.md`, lecture du debut de `TASK_CONTEXT.md`, `wc -l`, et `git status --short CODEX_TRACEABILITY.md TASK_CONTEXT.md`.
- Notes / risques:
  - Si une future session Codex reprend le travail, elle doit lire `TASK_CONTEXT.md` puis ajouter ses notes ici.

## 2026-04-29 - Verification documentaire initiale

- Action: verification rapide que le journal Codex existe et que `TASK_CONTEXT.md` reference la nouvelle regle de tracabilite.
- Fichiers:
  - `CODEX_TRACEABILITY.md`
  - `TASK_CONTEXT.md`
- Verification:
  - `wc -l CODEX_TRACEABILITY.md TASK_CONTEXT.md`
  - `sed -n '1,90p' CODEX_TRACEABILITY.md`
  - `sed -n '1,45p' TASK_CONTEXT.md`
  - `git status --short CODEX_TRACEABILITY.md TASK_CONTEXT.md`
- Notes / risques:
  - Les deux fichiers sont non suivis (`??`) dans Git, car ils font partie de la documentation locale nouvelle.
  - Aucun test applicatif n'est necessaire pour cette modification documentaire.

## 2026-04-29 - Demarrage verification selon TASK_CONTEXT

- Action: lecture de `TASK_CONTEXT.md`, lecture du journal Codex, et creation d'une todo dynamique dans le chat pour executer les checks dans l'ordre: backend, web, mobile, git sanity.
- Fichiers:
  - `TASK_CONTEXT.md`
  - `CODEX_TRACEABILITY.md`
- Verification:
  - `sed -n '1,220p' TASK_CONTEXT.md`
  - `tail -n 80 CODEX_TRACEABILITY.md`
  - `git status --short`
- Notes / risques:
  - L'arbre reste tres modifie/non suivi.
  - La prochaine action est la verification backend: `alembic heads`, `alembic upgrade head`, puis pytest.

## 2026-04-29 - Backend Alembic et test unitaire ProgramService

- Action: verification Alembic puis correction des tests unitaires `ProgramService` apres drift Phase 3.
- Fichiers:
  - `backend/tests/unit/services/test_program_service.py`
- Verification:
  - `alembic heads` global indisponible (`command not found`), puis `.venv/bin/alembic heads` OK: head `748989a9f381`.
  - `.venv/bin/alembic upgrade head` a echoue dans le sandbox avec `PermissionError: Operation not permitted`, puis a reussi avec execution autorisee hors sandbox.
  - `.venv/bin/python -m pytest tests/unit/services/test_program_service.py` a d'abord echoue:
    - mocks d'enrollment sans `program_version_id`;
    - fake `session.add()` asynchrone alors que SQLAlchemy `add()` est synchrone.
  - Corrections appliquees puis relance: `8 passed in 0.42s`.
- Notes / risques:
  - Le service etait correct; les doubles de test etaient obsoletes apres ajout de `program_version_id`.
  - Les tests integration backend restent a lancer.

## 2026-04-29 - Backend integration et pytest complet

- Action: execution des tests backend cibles puis correction des erreurs detectees dans le run complet.
- Fichiers:
  - `backend/app/services/program_service.py`
  - `backend/tests/unit/services/test_program_service.py`
  - `backend/tests/unit/core/test_permissions.py`
  - `backend/tests/integration/api/test_financial_health_api.py`
  - `backend/tests/test_phase_b_shared_review.py`
- Verification:
  - `.venv/bin/python -m pytest tests/integration/test_program_g49.py`:
    - sandbox bloque Docker;
    - relance autorisee hors sandbox: `22 passed, 1 skipped`.
  - `.venv/bin/python -m pytest tests/integration/test_program_g50_phase3.py`:
    - premier run: 1 failure sur `test_program_versions_crud`;
    - correction: `create_program()` cree maintenant une `ProgramVersion` initiale;
    - relance: `6 passed`.
  - regression G49 apres correction: `22 passed, 1 skipped`.
  - premier `.venv/bin/python -m pytest` complet:
    - `7 failed`, `21 errors`;
    - failures de permissions dues aux nouvelles permissions;
    - errors fixture `financial_health` avec `due_date < issued_date`;
    - errors `shared_review` avec login sans `school_id` puis loop scope.
  - Corrections:
    - compteurs `tests/unit/core/test_permissions.py` mis a jour;
    - `financial_health` paid invoice due_date remise apres issued_date;
    - `shared_review` login inclut `school_id` et fixtures async en `loop_scope="function"`.
  - Tests cibles apres correction:
    - `tests/unit/core/test_permissions.py`: `38 passed`;
    - `tests/integration/api/test_financial_health_api.py`: `13 passed`;
    - `tests/test_phase_b_shared_review.py`: `8 passed`.
  - Rerun complet final: `1658 passed, 1 skipped in 629.73s`.
- Notes / risques:
  - Les tests integration backend necessitent Docker/testcontainers et ont ete lances hors sandbox.
  - Les corrections `financial_health` et `shared_review` etaient hors feature academique mais necessaires pour rendre le backend complet vert.
  - Prochaine etape: web `npm run typecheck`, `npm run lint`, tests cibles, puis `npm test`.

## 2026-04-29 - Web verification complete

- Action: finalisation de la verification web avec correction des tests G49/G50 et relance de la suite complete.
- Fichiers:
  - `web/src/features/admin/usePrograms.ts`
  - `web/src/features/admin/AssignProgramDialog.tsx`
  - `web/tests/unit/features/AssignProgramDialog.test.tsx`
  - `web/tests/unit/features/EnrollmentsPage.test.tsx`
  - `web/tests/unit/features/StudentAcademicHistoryPage.test.tsx`
  - `web/tests/unit/features/EligibilityCheckTile.test.tsx`
- Verification:
  - `npm run typecheck`: OK.
  - `npm run lint`: OK.
  - lot cible G49/G50:
    - `npm test -- tests/unit/features/ProgramsPage.test.tsx tests/unit/features/AssignProgramDialog.test.tsx tests/unit/features/EnrollmentsPage.test.tsx tests/unit/features/StudentAcademicHistoryPage.test.tsx tests/unit/features/ProgramEquivalencesPage.test.tsx tests/unit/features/ProgramVersionsPage.test.tsx tests/unit/features/EligibilityRulesPage.test.tsx tests/unit/features/EligibilityCheckTile.test.tsx`
    - resultat final: `8 passed`, `20 passed`.
  - suite complete web:
    - `npm test`
    - resultat final: `35 passed`, `116 passed`.
- Notes / risques:
  - `useProgramsQuery(true, open)` evite les fetch MSW inutiles quand le dialog est ferme.
  - `AssignProgramDialog.test.tsx` a ete rendu deterministe via mock direct des hooks, car la combinaison React Query/MSW/jsdom autour de `<dialog>` laissait Vitest suspendu.
  - `EnrollmentsPage.test.tsx` mocke maintenant `AssignProgramDialog` pour verifier l'ouverture sans dependre du rendu complet du modal.
  - La suite complete web a affiche quelques messages MSW non-bloquants lies a `GET /api/v1/programs?active_only=1`, mais le run final est vert.

## 2026-04-29 - Mobile verification et corrections de harnais

- Action: verification Flutter, correction du nouveau test programme, puis correction de deux harnais de test mobiles pour rendre la suite complete verte.
- Fichiers:
  - `mobile/test/unit/program_repository_test.dart`
  - `mobile/test/unit/repositories_test.dart`
  - `mobile/integration_test/helpers/fake_app_environment.dart`
  - `mobile/test/app_test.dart`
- Verification:
  - `flutter --version`: OK apres acces au cache Flutter hors sandbox.
  - `flutter pub get`: OK.
  - `flutter analyze`: pas d'erreur bloquante, mais gros volume d'infos stylistiques historiques dans le repo.
  - `flutter analyze test/unit/program_repository_test.dart`: `No issues found!`
  - `flutter test test/unit/program_repository_test.dart`: OK.
  - premier `flutter test` complet:
    - echec `test/unit/repositories_test.dart` sur une cle de cache `content:first:::` non alignee avec le test;
    - echec des `app_flows` puis `app_test.dart` car `apiClientProvider` lisait `dotenv` non initialise dans les harnais de test.
  - corrections:
    - test repository aligne sur la vraie cle de cache de `ContentRepositoryImpl`;
    - `FakeAppEnvironment` override maintenant `apiClientProvider` avec un `ApiClient` de test local;
    - `app_test.dart` override aussi `apiClientProvider` avec un `ApiClient` de test local.
  - rechecks cibles:
    - `flutter test test/unit/repositories_test.dart`: OK.
    - `flutter test test/app_flows_vm_test.dart`: OK.
    - `flutter test test/app_test.dart`: OK.
  - rerun final suite complete:
    - `flutter test`
    - resultat final: `All tests passed!`
- Notes / risques:
  - Le bruit `flutter analyze` restant est preexistant et principalement compose de `require_trailing_commas` / `prefer_const_constructors`.
  - Les corrections apportees ici portent sur le harnais de test et la stabilite de verification, pas sur le comportement produit.

## 2026-04-29 - Sanity git final

- Action: verification finale de l'arbre de travail apres backend/web/mobile verts.
- Fichiers:
  - arbre global du repo
- Verification:
  - `git diff --check`: OK.
  - `git status --short`: arbre toujours tres modifie et non committe, sans corruption de patch.
- Notes / risques:
  - L'arbre contient beaucoup de changements utilisateur/historiques hors perimetre de cette session; rien n'a ete revert.
  - Les fichiers documentaires `CODEX_TRACEABILITY.md`, `TASK_CONTEXT.md`, `History_claude.md` restent non suivis.

## 2026-04-30 - Review de scope G49/G50 et demarrage Phase 3.5 transcript

- Action:
  - relecture de `TASK_CONTEXT.md` et `CODEX_TRACEABILITY.md`;
  - human pass des surfaces G49/G50 web/mobile/backend;
  - confirmation que l'etat "green" documente correspond bien au scope implemente;
  - lancement de la tranche suivante: transcript Phase 3.5.
- Fichiers:
  - `TASK_CONTEXT.md`
  - `CODEX_TRACEABILITY.md`
  - `backend/app/services/transcript_service.py`
  - `backend/app/api/v1/student_academic.py`
  - `backend/app/api/v1/snapshots.py`
  - `backend/app/schemas/programs.py`
  - `backend/tests/integration/test_program_g50_phase3.py`
  - `web/src/features/admin/programs.service.ts`
  - `web/src/features/admin/usePrograms.ts`
  - `web/src/features/admin/StudentAcademicHistoryPage.tsx`
- Verification:
  - review code/doc des surfaces:
    - backend programmes/historique/snapshots/eligibility;
    - web admin `StudentAcademicHistoryPage`;
    - mobile `program_history_screen.dart` et provider associe.
  - backend:
    - `cd backend && .venv/bin/python -m pytest tests/integration/test_program_g50_phase3.py -q` -> `8 passed`
    - `cd backend && .venv/bin/python -m pytest tests/integration/test_program_g49.py tests/integration/test_program_g50_phase3.py -q` -> `30 passed, 1 skipped`
  - web:
    - `cd web && npm run typecheck` -> OK
    - `cd web && npm run lint` -> OK
- Notes / risques:
  - La tranche transcript livree ici est volontairement JSON-first:
    - `GET /students/{student_id}/transcript?academic_year_id=...&mode=preview|snapshot`
    - `GET /academic-snapshots/{snapshot_id}/transcript`
  - Le web expose pour l'instant un telechargement JSON depuis la liste des snapshots; il manque encore une vraie UX de preview.
  - Le rendu transcript HTML/PDF n'est pas encore implemente; prochaine etape recommandee dans `TASK_CONTEXT.md`.

## 2026-04-30 - Transcript web HTML-first

- Action:
  - decision technique prise et implemente: transcript HTML-first, pas PDF-first;
  - ajout de previews HTML backend + modale web de preview transcript;
  - conservation du telechargement JSON comme secours.
- Fichiers:
  - `backend/app/services/transcript_service.py`
  - `backend/app/templates/reports/transcript.html`
  - `backend/app/api/v1/student_academic.py`
  - `backend/app/api/v1/snapshots.py`
  - `backend/tests/integration/test_program_g50_phase3.py`
  - `web/src/features/admin/programs.service.ts`
  - `web/src/features/admin/usePrograms.ts`
  - `web/src/features/admin/StudentAcademicHistoryPage.tsx`
  - `web/tests/unit/features/StudentAcademicHistoryPage.test.tsx`
- Verification:
  - `cd backend && .venv/bin/python -m pytest tests/integration/test_program_g50_phase3.py -q` -> `8 passed`
  - `cd web && npm run typecheck` -> OK
  - `cd web && npm run lint` -> OK
  - `cd web && npm test -- tests/unit/features/StudentAcademicHistoryPage.test.tsx` -> `4 passed`
- Notes / risques:
  - Le preview HTML s'appuie sur la meme base Jinja/reports que les rendus imprimables, ce qui prepare une conversion PDF propre plus tard.
  - La prochaine etape logique est d'ajouter impression/PDF a partir de ce meme template, sans changer le contrat transcript.

## 2026-04-30 - Polish impression transcript + recommandation mobile

- Action:
  - amelioration du rendu transcript pour impression;
  - ajout d'une action `Print` explicite dans la modale de preview web;
  - ajout / validation du PDF transcript sur la meme base HTML;
  - decision documentee pour le mobile.
- Fichiers:
  - `backend/app/templates/reports/base.html`
  - `backend/app/templates/reports/transcript.html`
  - `backend/app/services/transcript_service.py`
  - `backend/app/api/v1/student_academic.py`
  - `backend/app/api/v1/snapshots.py`
  - `backend/tests/integration/test_program_g50_phase3.py`
  - `web/src/features/admin/StudentAcademicHistoryPage.tsx`
  - `web/tests/unit/features/StudentAcademicHistoryPage.test.tsx`
- Verification:
  - `cd backend && .venv/bin/python -m pytest tests/integration/test_program_g50_phase3.py -q` -> `8 passed`
  - `cd web && npm run typecheck` -> OK
  - `cd web && npm run lint` -> OK
  - `cd web && npm test -- tests/unit/features/StudentAcademicHistoryPage.test.tsx` -> `4 passed`
- Notes / risques:
  - Recommandation mobile: commencer par acces PDF uniquement, pas preview transcript complet.
  - Raison: le transcript est deja stabilise en web/admin et le PDF couvre le besoin mobile principal sans dupliquer une surface HTML complexe dans Flutter.

## 2026-04-30 - Mobile transcript PDF access only

- Action:
  - ajout d'un acces mobile PDF-only depuis l'ecran `AcademicHistoryScreen`;
  - reutilisation directe de l'endpoint backend existant `/students/{student_id}/transcript/pdf`;
  - partage systeme du PDF telecharge au lieu d'un viewer Flutter dedie.
- Fichiers:
  - `mobile/lib/domain/repositories/program_repository.dart`
  - `mobile/lib/data/repositories_impl/program_repository_impl.dart`
  - `mobile/lib/features/student/program_history_screen.dart`
  - `mobile/lib/l10n/app_localizations.dart`
  - `mobile/test/unit/program_repository_test.dart`
  - `TASK_CONTEXT.md`
- Verification:
  - verification code locale des patterns existants (`ApiClient.download`, `share_plus`, repositories PDF mobiles);
  - `cd mobile && flutter test test/unit/program_repository_test.dart` -> `All tests passed!`
  - `cd mobile && flutter analyze lib/features/student/program_history_screen.dart lib/data/repositories_impl/program_repository_impl.dart lib/domain/repositories/program_repository.dart test/unit/program_repository_test.dart` -> `No issues found!`
  - `git diff --check` -> OK
- Notes / risques:
  - cette tranche couvre uniquement le transcript courant via `academic_year_id`;
  - aucun preview in-app ni acces snapshot mobile n'est ajoute dans cette passe.

## 2026-04-30 - Mobile transcript snapshots + viewer in-app

- Action:
  - ajout des snapshots academiques au repository/provider mobile;
  - ajout de l'acces PDF snapshot via `/academic-snapshots/{snapshot_id}/transcript/pdf`;
  - changement de decision UX: viewer PDF Flutter in-app retenu pour les transcripts, avec partage conserve en action secondaire;
  - remplacement du simple bouton AppBar par une carte d'actions libellee sur `AcademicHistoryScreen`;
  - ajout d'une section snapshots avec actions `ouvrir` / `partager`.
- Fichiers:
  - `mobile/lib/domain/entities/program.dart`
  - `mobile/lib/data/dto/mappers.dart`
  - `mobile/lib/domain/repositories/program_repository.dart`
  - `mobile/lib/data/repositories_impl/program_repository_impl.dart`
  - `mobile/lib/features/student/program_history_provider.dart`
  - `mobile/lib/features/student/program_history_screen.dart`
  - `mobile/lib/features/student/transcript_pdf_screen.dart`
  - `mobile/lib/l10n/app_localizations.dart`
  - `mobile/test/helpers/mock_repositories.dart`
  - `mobile/test/unit/program_repository_test.dart`
  - `mobile/test/widget/program_history_screen_test.dart`
  - `TASK_CONTEXT.md`
- Verification:
  - `cd mobile && flutter analyze lib/features/student/program_history_screen.dart lib/features/student/transcript_pdf_screen.dart lib/features/student/program_history_provider.dart lib/data/repositories_impl/program_repository_impl.dart lib/domain/repositories/program_repository.dart test/unit/program_repository_test.dart test/widget/program_history_screen_test.dart` -> `No issues found!`
  - `cd mobile && flutter test test/unit/program_repository_test.dart test/widget/program_history_screen_test.dart` -> `All tests passed!`
  - `cd mobile && flutter test` -> `All tests passed!`
  - `git diff --check` -> OK
- Notes / risques:
  - le viewer transcript repose sur `pdf_render`, deja present dans l'app;
  - la navigation vers le viewer est locale (pas de deep link dedie);
  - le scope reste limite aux transcripts PDF, sans preview HTML mobile.
