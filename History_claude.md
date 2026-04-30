# History Claude - Academic Program Management and Student Academic History

Source principale: `Conversation_Claude_Cowork.txt`.
Sources de verification ajoutees: `git log`, `git status`, `git diff --name-status`, `git diff --stat`, `git diff --check`.

Derniere lecture locale:

- Branche: `main`
- HEAD local: `96d98c1 Add technical decisions and engineering justifications document`
- `origin/main`: `e9bafe0 feat(k8s): enhance kubeconfig setup with error handling and validation`
- Etat: gros travail non commite sur backend, web et mobile.

## 1. Contexte initial

Le besoin initial etait de concevoir puis integrer un systeme de:

- suivi du programme/filiere academique d'un eleve;
- historique des changements de programme;
- tracabilite academique inter-annees;
- evolution de curriculum/programme;
- API, web et mobile pour consommer ces donnees.

Regle imposee au debut: ne pas coder immediatement. Claude devait d'abord proposer une architecture, attendre l'approbation, puis implementer.

Etat technique identifie au debut:

- Backend FastAPI + SQLAlchemy async + PostgreSQL + Alembic.
- Multi-tenant via `school_id` / `SchoolScopedMixin`.
- Backbone existant: `AcademicYear`, `Period`, `Class`, `Enrollment`.
- `Enrollment` etait deja le meilleur support temporel pour dire "dans quelle classe/periode etait cet eleve".
- Il n'existait pas encore de vraie entite `Program` / filiere.

## 2. Design propose avant implementation

Claude a propose une approche hybride:

- Level 2 complet: solution minimale production-safe.
- Plus un petit shim Level 3: `version_label` / `effective_from` pour preparer l'evolution des programmes.

Decisions importantes:

- `Enrollment` reste la source de verite de l'affectation programme par periode/annee.
- Un event log append-only conserve la trace des changements.
- Pas de reecriture destructrice de l'historique.
- Les anciens enrollments gardent `program_id = NULL`; aucun backfill automatique depuis du texte libre.
- Les transferts utilisent le pattern "soft-replace": ancien enrollment marque transfere, nouveau enrollment actif cree avec le nouveau programme.
- Les events doivent etre ecrits dans la meme transaction que l'enrollment.
- Les nouvelles tables et colonnes sont additives.

Phase 1 recommandee:

- migration Alembic;
- modeles SQLAlchemy;
- schemas Pydantic;
- service layer;
- endpoints programmes + history/timeline/current program;
- tests unitaires et integration;
- UI de backfill "needs assignment" plus tard.

Phase 2 recommandee:

- web admin Programs CRUD;
- web admin Academic History;
- mobile read-only;
- filtres reporting par programme.

Phase 3 recommandee seulement si besoin reel:

- table `program_versions`;
- equivalences de programmes;
- snapshots academiques;
- rules engine d'eligibilite.

## 3. Phase 1 - Backend G49

Apres approbation utilisateur, Claude a implemente la base backend.

Ajouts principaux:

- migration `9d9968735a7b_g49_program_management_and_history.py`;
- table `programs`;
- `program_id` nullable sur `enrollments`;
- table append-only `program_assignment_events`;
- trigger PostgreSQL pour empecher UPDATE/DELETE sur l'event log;
- modeles `Program`, `ProgramAssignmentEvent`, `ProgramAssignmentReason`;
- schemas `backend/app/schemas/programs.py`;
- service `backend/app/services/program_service.py`;
- endpoints:
  - `GET/POST/PATCH /programs`;
  - `POST /enrollments/{enrollment_id}/program`;
  - `GET /students/{id}/program-history`;
  - `GET /students/{id}/academic-timeline`;
  - `GET /students/{id}/current-program`;
- permissions `PERM_ERP_PROGRAM_READ` et `PERM_ERP_PROGRAM_MANAGE`;
- tests backend G49.

Blocage/erreur corrigee:

- Claude a detecte une collision d'ID Alembic avec une migration existante `0a1b2c3d4e5f`.
- La migration G49 a ete renommee/revisionnee en `9d9968735a7b`.

Verification declaree dans le transcript:

- parse statique Python OK;
- un seul Alembic head apres correction;
- parity migration/modeles verifiee;
- imports/routers verifies.

Non execute dans le sandbox:

- `alembic upgrade head`;
- tests pytest complets, faute de Postgres/pip dans l'environnement.

## 4. Phase 2.1 - Web admin Programs CRUD

Claude a cree l'UI admin pour gerer les programmes.

Ajouts:

- `web/src/features/admin/programs.service.ts`;
- `web/src/features/admin/usePrograms.ts`;
- `web/src/features/admin/ProgramsPage.tsx`;
- `web/src/features/admin/AssignProgramDialog.tsx`;
- route `/admin/programs`;
- entree sidebar;
- i18n EN/FR/AR;
- tests:
  - `ProgramsPage.test.tsx`;
  - `AssignProgramDialog.test.tsx`.

Verification declaree:

- `tsc --noEmit` OK;
- eslint sur fichiers touches OK;
- Vitest non executable dans le sandbox a cause du binaire natif Rollup Linux manquant et d'un npm registry bloque.

## 5. Phase 2.2 - Admin Enrollments page

L'utilisateur a choisi l'option "b": construire une page dediee `EnrollmentsPage`.

Backend:

- Nouveau endpoint admin `GET /admin/enrollments`.
- Ajout de `ProgramService.list_enrollments_for_admin`.
- Filtres: class, period, status, `missing_program`.
- Pagination cursor.
- Permission `PERM_ERP_ENROLLMENT_READ` accordee a ADM/DIR.

Frontend:

- `web/src/features/admin/enrollments.service.ts`;
- `web/src/features/admin/useEnrollments.ts`;
- `web/src/features/admin/EnrollmentsPage.tsx`;
- route `/admin/enrollments`;
- entree sidebar;
- i18n EN/FR/AR;
- tests `EnrollmentsPage.test.tsx`.

Resultat fonctionnel:

- Admins peuvent voir les enrollments sans programme.
- Ils peuvent ouvrir `AssignProgramDialog` depuis la ligne d'enrollment actif.
- Le backfill manuel "needs program assignment" est maintenant possible.

## 6. Phase 2.3 - Web Student Academic History

Claude a recommande et implemente la vue web academic history.

Ajouts:

- `web/src/features/admin/StudentAcademicHistoryPage.tsx`;
- route `/students/:studentId/academic-history`;
- lien depuis `EnrollmentsPage` sur le nom de l'eleve;
- i18n `student.academicHistory.*`;
- test `StudentAcademicHistoryPage.test.tsx`.

Fonctionnalites:

- carte programme courant;
- timeline academique groupee par annee;
- event log append-only des changements de programme;
- route accessible ADM/DIR/TCH/PAR/STD, avec enforcement backend ABAC.

## 7. Phase 2.3 Mobile - Flutter read-only

L'utilisateur a accepte de continuer meme si Claude ne pouvait pas executer Flutter.

Ajouts mobile:

- `mobile/lib/domain/entities/program.dart`;
- `mobile/lib/domain/repositories/program_repository.dart`;
- `mobile/lib/data/repositories_impl/program_repository_impl.dart`;
- mappers dans `mobile/lib/data/dto/mappers.dart`;
- provider repository dans `mobile/lib/app/providers.dart`;
- route dans `mobile/lib/app/router.dart`;
- `mobile/lib/features/student/program_history_provider.dart`;
- `mobile/lib/features/student/program_history_screen.dart`;
- `mobile/lib/features/student/widgets/current_program_card.dart`;
- i18n inline dans `mobile/lib/l10n/app_localizations.dart`;
- test `mobile/test/unit/program_repository_test.dart`.

Fonctionnalites:

- lecture du current program;
- timeline academique;
- history events;
- cache 10 minutes sur timeline/history;
- current-program sans cache volontaire.

Blocages:

- Pas de `flutter` CLI dans le sandbox.
- Pas de `flutter analyze`, `flutter test`, `dart format`.
- Claude a tente un heuristic de brace-balance Dart, mais l'a abandonne car faux positifs sur fichiers existants valides.

## 8. Phase 2.4 et 2.5 - Reporting integration

L'utilisateur a demande de continuer avec Phase 2.4 puis 2.5.

Backend:

- `/analytics/attendance` accepte `program_id`.
- `/analytics/grades` accepte `program_id`.
- `/analytics/attendance/alerts` accepte `program_id`.
- `/gradebook/{class}/{period}` accepte `program_id`.
- Filtres implementes via `EXISTS` sur enrollments quand pertinent.
- Cache keys analytics mises a jour avec `program_id`.

Frontend:

- dropdown "All programs" dans `AnalyticsDashboardPage`;
- dropdown programme dans `AttendanceAnalyticsPage`;
- dropdown programme dans `GradebookPage`;
- services/hooks mis a jour.

Tests:

- nouveaux tests smoke/filtres ajoutes dans `test_program_g49.py`.

Verification declaree:

- AST backend OK;
- `tsc --noEmit` OK;
- eslint OK.

## 9. Follow-up Phase 1 - POST /enrollments avec program_id

L'utilisateur a demande le petit follow-up: permettre une creation d'enrollment avec `program_id` dans le meme POST.

Changements:

- `EnrollmentCreateRequest.program_id`;
- `ERPService.create_enrollment(..., program_id=...)`;
- validation du programme: meme ecole + actif;
- persistence `program_id` sur la nouvelle ligne;
- ecriture d'un `ProgramAssignmentEvent` INITIAL dans la meme transaction;
- `EnrollmentResponse.program_id`;
- type web `EnrollmentPayload.program_id?` et `EnrollmentRecord.program_id`.

Note de design:

- Le chemin idempotent existant retourne l'enrollment deja present sans ecrire d'event si le second POST ajoute seulement `program_id`. Pour ajouter un programme a un enrollment existant, utiliser `POST /enrollments/{id}/program`.

## 10. Phase 3 - Toutes les pieces avancees

Malgre la recommandation initiale d'attendre un besoin reel, l'utilisateur a demande "All phase 3". Claude a alors implemente une version backend complete et une UI ciblee.

### 10.1 Program versions - G50a

Migration:

- `cb375ca25f1b_g50a_program_versions.py`;
- down revision: `9d9968735a7b`;
- cree `program_versions`;
- backfill une version `1.0` par programme existant;
- ajoute `program_version_id` sur `enrollments` et `program_assignment_events`.

Backend:

- modele `ProgramVersion`;
- schemas version;
- endpoints:
  - `GET /programs/{program_id}/versions`;
  - `POST /programs/{program_id}/versions`;
  - `PATCH /programs/{program_id}/versions/{version_id}`;
- `assign_program_to_enrollment` accepte et valide `program_version_id`.

Frontend:

- version picker dans `AssignProgramDialog`;
- page admin `ProgramVersionsPage`;
- route `/admin/programs/:programId/versions`;
- lien "manage versions" depuis `ProgramsPage`.

### 10.2 Program equivalences - G50b

Migration:

- `ab873f7d5708_g50b_program_equivalences.py`;
- down revision: `cb375ca25f1b`.

Backend:

- modele `ProgramEquivalence`;
- enum kind: `EQUIVALENT`, `SUPERSEDES`, `PARTIAL`;
- service CRUD;
- resolver BFS `equivalent_program_ids()`;
- endpoints:
  - `GET /program-equivalences`;
  - `POST /program-equivalences`;
  - `DELETE /program-equivalences/{id}`.

Frontend:

- `ProgramEquivalencesPage`;
- route `/admin/program-equivalences`;
- sidebar admin.

### 10.3 Academic snapshots - G50c

Migration:

- `72e15d401f00_g50c_academic_snapshots.py`;
- down revision: `ab873f7d5708`.

Backend:

- modele `AcademicSnapshot`;
- service `AcademicSnapshotService`;
- blob JSONB avec enrollments, events, grade summary, attendance summary, schema_version;
- endpoints:
  - `POST /academic-snapshots`;
  - `GET /academic-snapshots/{id}`;
  - `DELETE /academic-snapshots/{id}`;
  - `GET /students/{id}/snapshots`.

Frontend:

- section snapshots ajoutee dans `StudentAcademicHistoryPage`;
- bouton "Take snapshot now" pour l'annee la plus recente de la timeline.

Important:

- Le moteur de transcript PDF/HTML n'est pas encore construit. Les snapshots sont seulement le substrat.

### 10.4 Eligibility rules - G50d

Migration:

- `748989a9f381_g50d_eligibility_rules.py`;
- down revision: `72e15d401f00`;
- head final attendu: `748989a9f381`.

Backend:

- modele `EligibilityRule`;
- service `EligibilityService`;
- conditions connues:
  - `has_completed_program`;
  - `min_attendance_rate`;
  - `min_grade_average`;
- endpoints:
  - `GET /eligibility/rules`;
  - `POST /eligibility/rules`;
  - `DELETE /eligibility/rules/{rule_id}`;
  - `GET /students/{student_id}/eligibility?kind=...&target_program_id=...`.

Frontend:

- `EligibilityCheckTile`;
- tile embarquee dans `StudentAcademicHistoryPage`;
- page admin `EligibilityRulesPage`;
- route `/admin/eligibility-rules`;
- sidebar admin.

## 11. Gaps identifies et triage

Claude a liste des gaps apres Phase 3:

- Pas de page web complete pour gerer les versions.
- Pas de page web complete pour gerer les eligibility rules.
- Pas de mobile Phase 3.
- Pas de transcript service PDF/HTML.
- `min_attendance_rate` ignorait `academic_year_id`.
- Pas de cache pour equivalence transitivity.
- Pas de tests frontend Phase 3.

Decision utilisateur:

- Faire maintenant:
  - correction `min_attendance_rate` pour respecter `academic_year_id`;
  - tests frontend Phase 3;
  - pages admin versions/rules.
- Mode operationnel recommande:
  - versions et rules en edition annuelle/manuelle, pas workflow frequent complexe.
- Transcript service:
  - recommande comme Phase 3.5 separee, car c'est un livrable reel mais plus lourd.

Changements deja faits apres cette decision:

- `EligibilityService._evaluate()` filtre maintenant `min_attendance_rate` via la fenetre `AcademicYear.date_start/date_end`.
- Test backend year-scoped ajoute dans `test_program_g50_phase3.py`.
- `ProgramVersionsPage` creee et routee.
- `EligibilityRulesPage` creee et routee.
- Tests frontend Phase 3 crees:
  - `ProgramEquivalencesPage.test.tsx`;
  - `ProgramVersionsPage.test.tsx`;
  - `EligibilityRulesPage.test.tsx`;
  - `EligibilityCheckTile.test.tsx`.

Le transcript s'arrete pendant la verification de cette derniere phase. Il faut donc relancer toutes les validations localement.

## 12. Derniere demande non traitee dans le transcript

Derniere demande utilisateur a Claude avant la coupure:

- creer a la racine un fichier Markdown avec un prompt detaille pour "Build #4 / Transcript service";
- creer a la racine un fichier Markdown qui decrit tout ce qui a ete code dans la conversation et toutes les commandes de tests a lancer.

Claude n'a pas pu le faire a cause de la limite d'usage.

Dans la presente session, les fichiers demandes maintenant sont:

- `History_claude.md`: ce fichier, memoire du projet.
- `TASK_CONTEXT.md`: etat actuel + prochaines etapes.

## 13. Verification et limites connues

Ce qui a ete possible dans le sandbox selon le transcript:

- plusieurs passes AST Python;
- checks Alembic head;
- `tsc --noEmit`;
- eslint cible;
- `git diff --check` local: aucune sortie, donc pas d'erreur whitespace detectee.

Ce qui n'a pas ete execute ou reste a reexecuter:

- migrations sur vrai PostgreSQL;
- pytest backend;
- vitest web;
- flutter analyze;
- flutter test;
- verification fonctionnelle UI dans navigateur;
- revue de `backend/openapi.json` / `backend/docs/openapi.json` generes;
- decision sur `ecole-platform-dev.zip`, actuellement non suivi.
