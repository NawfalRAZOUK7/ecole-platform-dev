# Plan d'augmentation de la couverture des tests — Ecole Platform

> **Statut** : plan de travail prêt à être délégué à un agent IA externe (Claude Code, Codex, etc.).
> **Cible** : ≥ **97,9 %** de couverture lignes + branches sur l'ensemble du dépôt, sans modifier le code applicatif.
> **Périmètre** : backend Python (pytest), web (Vitest + Playwright), mobile (Flutter), system-tests (cross-stack).
> **Date** : 2026-05-28
> **Auteur du plan** : agent d'analyse (Cowork). À appliquer par un autre agent IA.

---

## 0. Cadre et règles du jeu

### 0.1 Règles non négociables (héritées de `PROMPTS_COUVERTURE_TESTS.md`)

- Ne **pas modifier** le code applicatif (`backend/app/`, `web/src/`, `mobile/lib/`, `infra/`).
- Ne **pas modifier** les modèles SQLAlchemy, schémas Pydantic, migrations Alembic, configurations runtime.
- Ne **pas** baisser un seuil (`fail_under`, `coverageThreshold`, etc.) pour faire passer la CI.
- Ne **pas** ajouter d'exclusions artificielles : pas de `# pragma: no cover`, pas d'ajout dans `omit`, pas de suppression de fichier mesuré.
- Ne **pas** supprimer / affaiblir un test existant.
- Ne **pas** commiter ni stager : **aucun `git add`, aucun `git commit`, aucun `git push`**. L'agent applique uniquement des modifications sur le disque, l'utilisateur reviewe et commit lui-même.
- Toute couverture revendiquée doit être **reproductible** par une commande shell unique.

### 0.2 Conventions du projet à respecter

- Tests classés par intention :
  - `backend/tests/unit/` (mocké, rapide, `--timeout=10`)
  - `backend/tests/integration/` (DB réelle, `--timeout=30`)
  - `backend/tests/contract/` (OpenAPI ↔ implémentation)
  - `backend/tests/edge/` (cas limites)
  - `backend/tests/security/` (RBAC / ABAC)
  - `backend/tests/performance/` (benchmarks)
- Réutiliser systématiquement :
  - les factories `backend/tests/factories/*`
  - les fixtures `backend/tests/_support/fixtures/*`
  - le `backend/tests/conftest.py` (auth contexts, sessions DB, redis fake)
- Markers `pytest` autorisés : `slow`, `security`, `performance`, `unit`, `integration` (déjà déclarés dans `pytest.ini`).
- Pour le web : tests Vitest dans `web/tests/unit/`, contracts dans `web/tests/contract/`, e2e dans `web/e2e/`.
- Pour le mobile : tests `mobile/test/` et `mobile/integration_test/`.

### 0.3 Constat de départ (baseline actuelle observable)

À partir de `backend/coverage.xml` (timestamp `1774616660169`) :

| Aire | Lignes couvertes / total | Couverture |
|---|---|---|
| **Global backend** | 7 569 / 11 170 | **67,76 %** |
| `app/` (racine) | 25 / 331 | 7,55 % |
| `app/services/` | 462 / 1 326 | 34,84 % |
| `app/api/` | 1 757 / 3 755 | 46,79 % |
| `app/core/` | 969 / 1 376 | 70,42 % |
| `app/models/` | 833 / 833 | 100,00 % |
| `app/schemas/` | 861 / 861 | 100,00 % |

> ⚠️ **Coverage.xml est obsolète** : il référence `app/api/v1/quizzes.py` mais le code a été restructuré en `app/api/v1/lms/quizzes.py` et `app/services/auth.py` est devenu `app/services/auth/auth.py`. **La toute première action de la Phase 0 est de régénérer une baseline fraîche.**

Top fichiers backend les plus déficitaires (lignes non couvertes) selon coverage.xml :

- `app/seed.py` (306 L, 0 %) — *omis dans `tool.coverage.report.omit` mais présent dans `coverage.run.source` ; à confirmer après refresh.*
- `app/api/v1/quizzes.py` / `lms/quizzes.py` (264 L, 14,8 %)
- `app/core/tasks.py` (226 L, 29,2 %)
- `app/api/v1/timetable.py` (239 L, 16,3 %)
- `app/api/v1/billing.py` (215 L, 14,9 %)
- `app/services/progress.py` / `academic/progress.py` (213 L, 12,2 %)
- `app/api/v1/submissions.py` (214 L, 46,7 %)
- `app/api/v1/messaging.py` (209 L, 16,8 %)
- `app/services/ai.py` (161 L, 28,0 %)
- `app/api/v1/cms.py` (156 L, 19,2 %)
- `app/api/v1/announcements.py` / `content_library.py` (136 L, 19,8 %)
- `app/api/v1/admin.py` (289 L, 51,2 %)
- `app/api/v1/assignments.py` (118 L, 51,7 %)
- `app/services/auth.py` / `auth/auth.py` (482 L, 45,0 %)
- `app/core/feature_flags.py` (86 L, 31,4 %)
- `app/core/idempotency.py` (43 L, 37,2 %)
- `app/core/rate_limit.py` (69 L, 47,8 %)
- `app/core/totp.py` (38 L, 0,0 %)
- `app/services/sms.py` (50 L, 0,0 %)
- `app/services/overdue_reminders.py` (45 L, 0,0 %)
- `app/services/payment_retry.py` (58 L, 0,0 %)
- `app/services/kpi.py` (64 L, 25,0 %)
- `app/services/quiz_grading.py` (66 L, 24,2 %)

### 0.4 Outils et commandes connues

- Backend complet avec couverture branches : `make test-full`
  → `cd backend && .venv/bin/python -m pytest --cov=app --cov-branch --cov-report=html --cov-report=term-missing`
- Backend par suite : `make test-unit`, `make test-integration`, `make test-security`, `make test-perf`
- Backend dockerisé : `make test-cov`
- Runner CI-like : `scripts/run-backend-test-suite.sh <unit|integration|security|contract|edge|performance|full>`
- Web Vitest : `cd web && npm run test:coverage`
- Web contract : `cd web && npm run test:contract`
- Web e2e : `cd web && npm run test:e2e`
- Mobile Flutter : `cd mobile && flutter test --coverage`
- System-tests : `system-tests/run_tests.sh`

---

## 1. Architecture du plan

Le plan est découpé en **8 phases**. Chaque phase est cumulative : on ne passe à la suivante que si la précédente est **verte localement**.

| Phase | Cible | Effort estimé | Livrable |
|---|---|---|---|
| 0 — Baseline & inventaire | Régénérer un coverage frais et un inventaire des gaps | 0,5 j | `artifacts/coverage-baseline/` + `docs/testing/baseline.md` |
| 1 — Quick wins core/utils | `app/core/*` → ≥ 95 % | 0,5 j | tests unitaires dans `tests/unit/core/` |
| 2 — Services à 0 % | `services/sms`, `overdue_reminders`, `payment_retry`, `totp` → ≥ 95 % | 0,5 j | tests unitaires dans `tests/unit/services/` |
| 3 — Services métier sous-couverts | `auth`, `progress`, `ai`, `kpi`, `quiz_grading` → ≥ 90 % | 1,5 j | tests unitaires + integration |
| 4 — API v1 sous-couverts | `quizzes`, `billing`, `timetable`, `messaging`, `cms`, `announcements`, `content_library`, `submissions`, `admin` → ≥ 95 % | 2 j | tests integration + contract |
| 5 — Workers, tasks, repositories | `app/workers/*`, `app/core/tasks.py`, `app/repositories/*` → ≥ 95 % | 1 j | tests unitaires + integration |
| 6 — Frontend Vitest + Playwright | `web/src/` → ≥ 95 % | 1 j | tests dans `web/tests/unit`, `web/tests/contract`, `web/e2e` |
| 7 — Mobile Flutter | `mobile/lib/` → ≥ 95 % | 1 j | tests dans `mobile/test/` et `mobile/integration_test/` |
| 8 — Verrouillage & validation finale | Global ≥ 97,9 % + relever `fail_under` | 0,5 j | rapport final + tableau de preuve |

> ✅ Chaque phase se termine par un **bloc validation** : commande à lancer + assertion sur le delta de couverture + checklist.

---

## 2. Phase 0 — Baseline reproductible

### 2.1 Pourquoi

Le `coverage.xml` actuel est désynchronisé du code. Sans baseline fraîche on optimise dans le vide.

### 2.2 Substeps

- **0.A — Geler l'environnement**
  - [ ] Vérifier que `backend/.venv/` existe (`python -V` ≥ 3.12).
  - [ ] `cd backend && .venv/bin/pip install -r requirements-test.txt`.
  - [ ] Vérifier que Postgres + Redis du Docker compose sont up (`make status` ou `docker compose ps`).
  - [ ] Charger les seeds : `make seed` (préalable obligatoire pour `tests/integration`).

- **0.B — Régénérer la baseline backend**
  - [ ] Vider les anciens artefacts : `rm -rf backend/htmlcov backend/htmlcov-* backend/coverage.xml backend/.coverage.pytest`.
  - [ ] Lancer la suite complète : `cd backend && .venv/bin/python -m pytest --cov=app --cov-branch --cov-report=xml:coverage.xml --cov-report=html:htmlcov --cov-report=term-missing -q | tee ../artifacts/coverage-baseline/backend.log`.
  - [ ] Vérifier 0 test en `failed`. Si des tests sont en `skipped`, lister la raison.

- **0.C — Régénérer la baseline web**
  - [ ] `cd web && npm ci`.
  - [ ] `npm run test:coverage -- --reporter=verbose | tee ../artifacts/coverage-baseline/web.log`.
  - [ ] Sauvegarder `web/coverage/coverage-final.json` dans `artifacts/coverage-baseline/web/`.

- **0.D — Régénérer la baseline mobile**
  - [ ] `cd mobile && flutter pub get`.
  - [ ] `flutter test --coverage | tee ../artifacts/coverage-baseline/mobile.log`.
  - [ ] Vérifier la présence de `mobile/coverage/lcov.info` et l'archiver.

- **0.E — Construire l'inventaire des gaps**
  - [ ] Écrire `docs/testing/baseline.md` avec :
    - tableau « top 30 fichiers les moins couverts » backend, web, mobile.
    - pour chaque fichier : nombre de lignes manquantes + ranges (ex. `lines 41-58, 72, 88-110`).
    - hypothèses sur la **raison du gap** (route admin oubliée, branche d'erreur, retry/backoff, code de fallback…).
  - [ ] Marquer les fichiers déjà à 100 % comme **« interdits »** (ne pas y toucher).

### 2.3 Validation Phase 0

- [ ] `backend/coverage.xml` daté du jour et `line-rate` connu.
- [ ] Logs des 3 baselines archivés sous `artifacts/coverage-baseline/`.
- [ ] `docs/testing/baseline.md` créé et listant ≥ 30 fichiers backend, ≥ 10 web, ≥ 10 mobile.

### 2.4 Prompt à coller (Phase 0)

```text
Tu travailles dans /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev.

Mission : produire une baseline de couverture fraîche et reproductible pour backend, web et mobile, et un inventaire des gaps. NE MODIFIE AUCUN FICHIER applicatif. N'utilise jamais `git add` ni `git commit`.

Étapes :
1. Vérifie l'environnement : `cd backend && .venv/bin/python -V`, `pip install -r requirements-test.txt`, services Docker postgres/redis up, seeds chargés via `make seed`.
2. Nettoie : `rm -rf backend/htmlcov backend/htmlcov-* backend/coverage.xml backend/.coverage.pytest`.
3. Lance la suite backend complète :
   `cd backend && .venv/bin/python -m pytest --cov=app --cov-branch --cov-report=xml:coverage.xml --cov-report=html:htmlcov --cov-report=term-missing -q`
   Archive le stdout dans `artifacts/coverage-baseline/backend.log`.
4. Lance le web :
   `cd web && npm ci && npm run test:coverage -- --reporter=verbose`
   Archive dans `artifacts/coverage-baseline/web.log` et copie `web/coverage/coverage-final.json`.
5. Lance le mobile :
   `cd mobile && flutter pub get && flutter test --coverage`
   Archive `mobile/coverage/lcov.info`.
6. Génère `docs/testing/baseline.md` avec, pour backend/web/mobile :
   - top 30 (backend) / 10 (web/mobile) fichiers les moins couverts ;
   - colonnes : chemin, lignes valides, lignes manquantes, % ligne, % branche, plages de lignes non couvertes, hypothèse de gap.
   - tableau récap : couverture globale par aire (`app/api`, `app/services`, `app/core`, `app/workers`, `app/repositories`).

Contraintes :
- Ne modifie aucun fichier en dehors de `docs/testing/baseline.md` et `artifacts/coverage-baseline/`.
- Si une commande échoue, documente la cause exacte (env, dépendance manquante, test cassé) et ARRÊTE-TOI. Ne contourne pas.
- Aucun commit, aucun stage git.

Livrables : 3 logs + 3 artefacts de coverage + `baseline.md`. Termine par un résumé en 10 lignes max.
```

---

## 3. Phase 1 — Quick wins sur `app/core/*`

### 3.1 Pourquoi

`app/core/` contient des utilitaires purs (idempotency, rate_limit, feature_flags, totp, tasks). Coût/bénéfice imbattable : petits fichiers, peu de dépendances, gros gain en %.

### 3.2 Cibles et substeps

Pour **chaque** fichier ci-dessous, créer un test unitaire dédié dans `backend/tests/unit/core/test_<module>.py`.

- **1.A — `app/core/totp.py` (0 % → 100 %)**
  - [ ] Test génération / vérification d'un secret TOTP avec horloge mockée (`freezegun` ou `monkeypatch` sur `time.time`).
  - [ ] Test code invalide, code expiré (fenêtre ±1).
  - [ ] Test format QR / URI otpauth.
  - [ ] Test entropie / longueur du secret.

- **1.B — `app/core/idempotency.py` (37 % → 100 %)**
  - [ ] Test première écriture : clé absente → stockage + retour.
  - [ ] Test deuxième écriture même clé : retour identique sans ré-exécution du handler.
  - [ ] Test expiration TTL (fakeredis).
  - [ ] Test collision : même clé, payload différent → erreur 409 ou hash mismatch.
  - [ ] Test concurrence : 2 appels simultanés (asyncio.gather) → un seul handler exécuté.

- **1.C — `app/core/rate_limit.py` (48 % → 100 %)**
  - [ ] Test sous-quota → 200, headers `X-RateLimit-*` corrects.
  - [ ] Test dépassement → 429 + `Retry-After`.
  - [ ] Test reset après TTL.
  - [ ] Test segmentation par user/IP/route.
  - [ ] Test mode `fail_open` quand Redis indisponible.

- **1.D — `app/core/feature_flags.py` (31 % → 100 %)**
  - [ ] Test flag présent / absent.
  - [ ] Test override par rôle, par école (`school_id`), par utilisateur.
  - [ ] Test rollout pourcentage (mock hash).
  - [ ] Test fallback si store inaccessible.
  - [ ] Test invalidation cache (`refresh()`).

- **1.E — `app/core/tasks.py` (29 % → 95 %)**
  - [ ] Test enqueue (arq) avec fake Redis.
  - [ ] Test retry / max_tries (mock du worker).
  - [ ] Test cron jobs : déclenchement à l'heure (`monkeypatch` `datetime`).
  - [ ] Test dedup par task_id.
  - [ ] Test gestion d'erreur : exception métier vs erreur réseau.

### 3.3 Validation Phase 1

- [ ] `pytest tests/unit/core --cov=app.core --cov-branch --cov-report=term-missing` → ≥ 95 % global sur `app/core/`.
- [ ] Aucun nouveau test marqué `slow`.
- [ ] Aucun test en `xfail` introduit pour cacher un manque.

### 3.4 Prompt à coller (Phase 1)

```text
Tu travailles dans /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev.

Mission : amener `app/core/*` à ≥ 95 % de couverture branche en ajoutant uniquement des tests unitaires. NE TOUCHE PAS au code applicatif. Pas de `git add`/`git commit`.

Cibles (dans cet ordre) :
1. app/core/totp.py
2. app/core/idempotency.py
3. app/core/rate_limit.py
4. app/core/feature_flags.py
5. app/core/tasks.py

Méthode pour chacun :
A. Lis le module et liste les fonctions/branches non couvertes via `pytest --cov=app.<module> --cov-report=term-missing`.
B. Crée `backend/tests/unit/core/test_<module>.py` (un fichier par module). Réutilise `tests/conftest.py` et `tests/_support/fixtures/*`.
C. Couvre :
   - chemins heureux (≥ 1 assert significatif par fonction publique) ;
   - branches d'erreur (exceptions, valeurs invalides) ;
   - cas limites (TTL=0, quotas atteints, fenêtre TOTP ±1, flag manquant) ;
   - mode dégradé (Redis down) avec `fakeredis` ou monkeypatch.
D. Utilise des fakes/mocks (pas de DB, pas de Redis réel).
E. Pas d'assertions creuses (`assert result is not None` sans contexte). Chaque test doit avoir au moins une assertion sur la valeur/le comportement.

Validation :
- `cd backend && .venv/bin/python -m pytest tests/unit/core --cov=app.core --cov-branch --cov-report=term-missing` doit afficher ≥ 95 % sur `app/core`.
- Aucun test précédent ne doit casser : relance `pytest tests/unit -q`.
- Mets à jour `docs/testing/baseline.md` avec la nouvelle couverture `app/core`.

Si un module exige une dépendance réelle (DB/Redis), documente-le dans `docs/testing/baseline.md` et reporte-le en Phase 5. Ne baisse jamais un seuil. Ne commite pas.
```

---

## 4. Phase 2 — Services à 0 % de couverture

### 4.1 Pourquoi

Quatre services sont totalement non testés : `sms`, `overdue_reminders`, `payment_retry`, `totp` (déjà traité en 1.A). Ils contiennent surtout du I/O externe ; testables proprement avec mocks.

### 4.2 Cibles et substeps

- **2.A — `app/services/sms.py`**
  - [ ] Mock du client SMS (Twilio/MessageBird) via `monkeypatch`.
  - [ ] Test envoi simple → payload attendu + statut.
  - [ ] Test format numéro invalide → exception métier.
  - [ ] Test backoff / retry sur erreur réseau (mocker `tenacity`).
  - [ ] Test idempotency (même `message_id` → pas de doublon).
  - [ ] Test localisation FR/AR.

- **2.B — `app/services/overdue_reminders.py`**
  - [ ] Fixture DB en mémoire ou repository fake (Protocol) avec 3 factures : à jour, en retard 7j, en retard 30j.
  - [ ] Test sélection des candidats (filtre `due_date < now - threshold`).
  - [ ] Test génération du contenu (FR/AR), variables interpolées.
  - [ ] Test envoi groupé : ≤ N par run.
  - [ ] Test no-op si flag désactivé.
  - [ ] Test dry-run.

- **2.C — `app/services/payment_retry.py`**
  - [ ] Test premier retry : `attempts=1` → schedule à +1h.
  - [ ] Test escalade : `attempts=N` → schedule à backoff exponentiel jusqu'à plafond.
  - [ ] Test abandon : `attempts > max` → marquage `failed_final`.
  - [ ] Test succès intermédiaire : provider 200 → marquage `paid` + arrêt retries.
  - [ ] Test webhook reentrant idempotent.

- **2.D — `app/services/quiz_grading.py` (24 % → 95 %)**
  - [ ] Test grading QCM simple (toutes les options possibles).
  - [ ] Test grading texte libre avec barème.
  - [ ] Test partial credit (multi-réponses).
  - [ ] Test pondération par question.
  - [ ] Test réponse absente / vide / hors plage.
  - [ ] Test cas tricheur (durée > limite) si géré.

- **2.E — `app/services/kpi.py` (25 % → 95 %)**
  - [ ] Test agrégations par école / niveau / classe.
  - [ ] Test fenêtres temporelles (7j, 30j, YTD).
  - [ ] Test division par zéro / dataset vide.
  - [ ] Test cache (Redis fake).
  - [ ] Test serialization (Pydantic schema).

### 4.3 Validation Phase 2

- [ ] `pytest tests/unit/services --cov=app.services --cov-branch --cov-report=term-missing` → progression visible sur ces 5 fichiers.
- [ ] Chaque nouveau test fait ≤ 200 ms (`pytest --durations=10`).

### 4.4 Prompt à coller (Phase 2)

```text
Mission : couvrir les services backend à 0 % ou très bas en tests unitaires (pas d'I/O réel). NE MODIFIE PAS le code applicatif. Pas de git.

Cibles :
- app/services/sms.py
- app/services/overdue_reminders.py
- app/services/payment_retry.py
- app/services/quiz_grading.py
- app/services/kpi.py

Pour chacun :
1. Lis le module + ses dépendances (repository, settings, clients externes).
2. Crée `backend/tests/unit/services/test_<module>.py`.
3. Mocke toutes les I/O : Twilio/SMS provider, HTTP, DB session, Redis.
   - Utilise `unittest.mock.AsyncMock` pour les coroutines.
   - Pour la DB, préfère un Protocol fake (repository swap) plutôt qu'un sqlite en mémoire si le service accepte un repository injecté.
4. Couvre obligatoirement :
   - tous les chemins heureux ;
   - toutes les branches d'erreur (assert que l'exception attendue est levée et que rien d'autre n'a été appelé) ;
   - les cas limites (datasets vides, division par zéro, retries au plafond).
5. Vérifie chaque appel mocké : `mock.assert_called_with(...)`.
6. Mets à jour `docs/testing/baseline.md` (delta de couverture pour ces 5 fichiers).

Validation :
- `pytest tests/unit/services -q` ne casse pas l'existant.
- `pytest --cov=app.services.sms --cov=app.services.overdue_reminders --cov=app.services.payment_retry --cov=app.services.quiz_grading --cov=app.services.kpi --cov-branch --cov-report=term-missing` ≥ 95 % sur ces 5.

Pas de commit. Pas de `# pragma: no cover`. Pas d'ajout dans `omit`.
```

---

## 5. Phase 3 — Services métier sous-couverts

### 5.1 Pourquoi

`auth`, `progress`, `ai` portent l'essentiel de la logique. Ils sont entre 12 % et 45 %. Ce sont les fichiers les plus rentables après les API.

### 5.2 Cibles et substeps

- **3.A — `app/services/auth/auth.py` (45 % → 90 %)**
  - [ ] Tests unitaires (fakes) :
    - [ ] login OK / mauvais password / utilisateur inactif / verrouillé.
    - [ ] refresh token : valide, expiré, révoqué, scope incorrect.
    - [ ] rotation JWT (vérifier `kid`, `iat`, `exp`).
    - [ ] reset password : token valide, expiré, déjà utilisé.
    - [ ] 2FA : challenge créé, verify OK/KO, fallback SMS.
    - [ ] OAuth callback : state OK/KO, code échangé, user créé/lié.
    - [ ] WebAuthn enrolment / login (challenge mocké).
  - [ ] Tests integration (`tests/integration/services/test_auth_flow.py`) :
    - [ ] cycle complet login → me → refresh → logout via TestClient.
    - [ ] account lockout après N tentatives.

- **3.B — `app/services/academic/progress.py` (12 % → 90 %)**
  - [ ] Tests unitaires :
    - [ ] calcul moyenne pondérée (coefficients matières).
    - [ ] arrondi (demi-points, dixièmes selon config école).
    - [ ] bulletin trimestriel : structure JSON, ordre matières, mentions.
    - [ ] historique : agrégation sur N trimestres.
    - [ ] passerelle skill-passport (mock du service voisin).
  - [ ] Tests intégration :
    - [ ] insertion notes via factory → recalcul progress idempotent.

- **3.C — `app/services/ai.py` (28 % → 90 %)**
  - [ ] Tests unitaires :
    - [ ] sélection provider (OpenAI / Anthropic / local) selon flag.
    - [ ] formatting du prompt (system + user + contexte cours).
    - [ ] parsing réponse JSON, gestion fallback texte.
    - [ ] gestion quota / 429 / timeout.
    - [ ] redaction PII avant envoi.
    - [ ] retry exponentiel.

### 5.3 Validation Phase 3

- [ ] `pytest tests/unit/services tests/integration/services --cov=app.services.auth --cov=app.services.academic.progress --cov=app.services.ai --cov-branch --cov-report=term-missing` ≥ 90 %.
- [ ] Suite intégration toujours < 60 s sur machine dev.

### 5.4 Prompt à coller (Phase 3)

```text
Mission : porter `app/services/auth/auth.py`, `app/services/academic/progress.py` et `app/services/ai.py` à ≥ 90 % de couverture branche, via unit + integration. Pas de modif code applicatif. Pas de git.

Workflow par module :
1. Identifie les fonctions non couvertes : `pytest --cov=app.services.<mod> --cov-report=term-missing`.
2. Pour chaque fonction :
   a. Si elle est pure ou facilement isolable → test unitaire dans `tests/unit/services/<area>/test_<mod>.py`.
   b. Sinon → test intégration dans `tests/integration/services/test_<mod>_flow.py` avec TestClient + factories.
3. Mocks autorisés :
   - clients HTTP externes (OpenAI, Anthropic, provider OAuth, WebAuthn) via `respx` ou `httpx_mock`.
   - horloge via `freezegun`.
   - Redis via `fakeredis`.
4. Mocks INTERDITS :
   - mocker la session SQLAlchemy quand un test d'intégration peut tourner avec la DB Docker.
   - mocker la fonction sous test (anti-pattern).
5. Réutilise les factories `tests/factories/iam.py`, `lms.py`, etc.
6. Pour `auth.py`, ajoute aussi un test de **non-régression sécurité** : login d'un utilisateur d'une autre école → 403/404 (selon contrat actuel — ne change pas le comportement, vérifie-le).

Validation :
- Coverage cible ≥ 90 % sur les 3 modules.
- `pytest -q` global vert.
- `docs/testing/baseline.md` mis à jour.
```

---

## 6. Phase 4 — API v1 sous-couvertes

### 6.1 Pourquoi

Le plus gros volume non couvert (`app/api/v1/*`) est ici. Chaque route a une signature OpenAPI ; tester via TestClient couvre la route + la dépendance + la sérialisation + le repository.

### 6.2 Cibles (par ordre de gain)

Pour chaque module : créer un fichier `backend/tests/integration/api/test_<module>.py`.

- **4.A — `app/api/v1/lms/quizzes.py`** (264 L, 14,8 %)
- **4.B — `app/api/v1/billing.py` (sous-arborescence)** (215 L, 14,9 %)
- **4.C — `app/api/v1/timetable.py`** (239 L, 16,3 %)
- **4.D — `app/api/v1/communication/messaging.py`** (209 L, 16,8 %)
- **4.E — `app/api/v1/content/cms.py`** (156 L, 19,2 %)
- **4.F — `app/api/v1/communication/announcements.py`** (136 L, 19,8 %)
- **4.G — `app/api/v1/content/content_library.py`** (136 L, 19,8 %)
- **4.H — `app/api/v1/lms/submissions.py`** (214 L, 46,7 %)
- **4.I — `app/api/v1/admin/admin.py`** (289 L, 51,2 %)
- **4.J — `app/api/v1/ai/ai.py`** (87 L, 29,9 %)
- **4.K — `app/api/v1/gdpr.py`** (94 L, 29,8 %)

### 6.3 Substeps par module

- [ ] Lister les routes exposées : `grep -nE "@(router|app)\.(get|post|put|patch|delete)" app/api/v1/<file>`.
- [ ] Pour **chaque route**, tester au moins :
  - [ ] **succès** (200/201/204) avec corps minimal valide.
  - [ ] **succès** (200/201) avec corps complet (tous champs optionnels remplis).
  - [ ] **404** sur ressource inexistante.
  - [ ] **403** par rôle (admin/teacher/parent/student) selon RBAC.
  - [ ] **403/404** cross-tenant (ressource d'une autre école).
  - [ ] **422** validation (champ requis manquant, type incorrect, longueur excessive).
  - [ ] **409 / 412** conflit / précondition si la route le prévoit.
  - [ ] **idempotency-key** si la route est `POST` mutante.
  - [ ] **pagination** : page 1, page hors-limites, `limit` invalide.
  - [ ] **filtres / tri** si supportés (au moins 1 cas par filtre).
- [ ] Asserter sur :
  - [ ] code HTTP exact ;
  - [ ] **enveloppe de réponse** (utiliser `tests/_support/matchers` ou comparer à un snapshot Pydantic) ;
  - [ ] **side-effects DB** vérifiés via session (`select(...)`).

### 6.4 Tests contract (OpenAPI)

- [ ] Étendre `tests/contract/test_api_contracts.py` :
  - [ ] charger `openapi.json` ;
  - [ ] pour chaque route ajoutée en 4.A-K, vérifier que la response réelle satisfait le schéma déclaré (utiliser `openapi-schema-validator` ou `jsonschema`).
  - [ ] s'assurer qu'aucune route n'apparaît dans le code sans être déclarée dans `openapi.json`, et inversement.

### 6.5 Validation Phase 4

- [ ] `pytest tests/integration/api tests/contract --cov=app.api --cov-branch --cov-report=term-missing` ≥ 95 % sur `app/api`.
- [ ] **Aucune** route OpenAPI sans test.
- [ ] Le rapport `pytest --collect-only -q tests/integration/api | wc -l` ≥ 200 (indicateur volume).

### 6.6 Prompt à coller (Phase 4)

```text
Mission : couvrir les modules `app/api/v1/*` listés dans `docs/testing/PLAN_AUGMENT_COVERAGE_TESTS.md` §6.2 jusqu'à ≥ 95 % de couverture branche, exclusivement via tests d'intégration (`tests/integration/api/`) + contract (`tests/contract/`).
NE MODIFIE PAS le code de `app/api/`, `app/services/`, `app/repositories/`, `app/models/`. Pas de git.

Pour chaque module dans l'ordre 4.A → 4.K :

1. Recense les routes : `grep -nE "@(router|app)\.(get|post|put|patch|delete)" app/api/v1/<path>`.
2. Pour chaque route, crée un test dans `tests/integration/api/test_<module>.py` qui couvre OBLIGATOIREMENT :
   - 1 succès minimal + 1 succès complet
   - 404 ressource manquante
   - 403 par rôle (admin, teacher, parent, student) selon ce qui s'applique
   - 403/404 cross-school (tenant isolation)
   - 422 validation (au moins 2 cas)
   - 409/412 si applicable (idempotency, optimistic locking)
   - pagination + filtres si exposés
3. Utilise :
   - le TestClient/Async client défini dans `tests/conftest.py`
   - les factories `tests/factories/*`
   - les matchers de `tests/_support/matchers`
4. Asserte sur (a) le status HTTP, (b) la forme de la réponse, (c) les side-effects DB via `AsyncSession`.
5. Pour les routes mutantes POST/PUT/PATCH/DELETE, ajoute un test d'idempotency si la route déclare `Idempotency-Key`.
6. Étends `tests/contract/test_api_contracts.py` : valide les réponses réelles contre `backend/openapi.json` (jsonschema/openapi-schema-validator). Si une route n'a pas de schéma OpenAPI, NE LA SUPPRIME PAS — log un échec de contrat.

Validation après chaque module :
- `pytest tests/integration/api/test_<module>.py --cov=app.api.v1.<module> --cov-branch --cov-report=term-missing` ≥ 95 %.
- Aucune route OpenAPI sans test (générer la liste via un script si nécessaire).

Si une fonctionnalité paraît bugguée : NE LA CORRIGE PAS. Écris un test `pytest.mark.xfail(strict=True, reason="bug suspecté: ...")` et reporte dans `docs/testing/anomalies.md`.

Pas de commit, pas de stage git.
```

---

## 7. Phase 5 — Workers, tasks, repositories

### 7.1 Pourquoi

`app/core/tasks.py` (29 %), `app/workers/*` et `app/repositories/*` constituent le reste de la dette backend. Ce sont des couches techniques avec peu de logique métier mais beaucoup de chemins d'erreur (réseau, DB, file d'attente).

### 7.2 Substeps

- **5.A — Workers**
  - [ ] Tester chaque worker arq : `process_*`, gestion `retry`, `job_failed`.
  - [ ] Mocker la Redis arq via `fakeredis`.
  - [ ] Asserter side-effects (envoi mail, notification, MAJ DB).

- **5.B — Repositories**
  - [ ] Pour chaque repository : `tests/unit/repositories/test_<name>.py` avec sqlite-async ou DB de test ; assertions sur `get`, `list`, `create`, `update`, `delete`, filtres, scopes (school_id).
  - [ ] Cas erreur : not found, integrity error, optimistic lock.

- **5.C — `app/core/tasks.py`** (compléter Phase 1.E si nécessaire)
  - [ ] Test cron schedule resolver.
  - [ ] Test priorisation et timeouts.

### 7.3 Validation Phase 5

- [ ] `pytest tests/unit/repositories tests/integration/repositories --cov=app.repositories --cov-branch --cov-report=term-missing` ≥ 95 %.
- [ ] `pytest --cov=app.workers --cov-branch` ≥ 95 %.

### 7.4 Prompt à coller (Phase 5)

```text
Mission : couvrir `app/workers/`, `app/repositories/`, et terminer `app/core/tasks.py`. Tests unitaires (fakeredis, sqlite-async) + intégration au besoin. Pas de modif code applicatif. Pas de git.

Étapes :
1. Liste les workers et repositories :
   - `find app/workers -name '*.py'`
   - `find app/repositories -name '*.py'`
2. Pour chaque worker :
   - Crée `tests/unit/workers/test_<worker>.py`.
   - Mocke arq via `fakeredis` + import du callable.
   - Couvre : succès, retry, échec définitif, dedup.
3. Pour chaque repository :
   - Crée `tests/unit/repositories/test_<repo>.py`.
   - Couvre CRUD + filtres + scope tenant (`school_id`).
   - Pour les requêtes complexes (joins, agrégats), préfère `tests/integration/repositories/`.
4. Complète `tests/unit/core/test_tasks.py` avec les branches restantes (cron resolver, timeouts).

Validation :
- `pytest tests/unit/repositories tests/unit/workers --cov=app.repositories --cov=app.workers --cov-branch --cov-report=term-missing` ≥ 95 %.
- Mets à jour `docs/testing/baseline.md`.

Pas de commit.
```

---

## 8. Phase 6 — Frontend (Vitest + Playwright)

### 8.1 Pourquoi

`web/src/` est le second gros bloc. Couvrir composants, hooks, stores, contrats API et parcours utilisateurs critiques.

### 8.2 Substeps

- **6.A — Vitest unit (`web/tests/unit/`)**
  - [ ] Pour chaque module dans `web/src/lib/`, `web/src/hooks/`, `web/src/utils/`, créer un test unitaire (Vitest).
  - [ ] Pour chaque composant React, tester :
    - [ ] rendu avec props par défaut ;
    - [ ] handlers (`onClick`, `onChange`) via `@testing-library/react` ;
    - [ ] états (loading, error, empty, success) ;
    - [ ] a11y minimal : `role`, `aria-*`, focus.
  - [ ] Pour chaque store/contexte, tester actions + sélecteurs.

- **6.B — Vitest contract (`web/tests/contract/`)**
  - [ ] Pour chaque client API généré, ajouter test : réponse mock conforme au schéma → parsing OK ; réponse divergente → erreur typée.
  - [ ] Lancer `npm run test:contract` en mode strict.

- **6.C — Playwright e2e (`web/e2e/`)**
  - [ ] Parcours critiques :
    - [ ] login / logout / refresh token.
    - [ ] enrolment d'un élève (admin).
    - [ ] consultation bulletin (parent).
    - [ ] dépôt devoir (élève).
    - [ ] correction devoir (prof).
    - [ ] paiement facture (parent).
    - [ ] messagerie : envoi + lecture.
  - [ ] Vérifier les a11y de chaque page critique via `@axe-core/playwright`.

### 8.3 Validation Phase 6

- [ ] `cd web && npm run test:coverage` ≥ 95 % lignes et branches.
- [ ] `cd web && npm run test:contract` 0 échec.
- [ ] `cd web && npm run test:e2e` vert.

### 8.4 Prompt à coller (Phase 6)

```text
Mission : porter `web/src/` à ≥ 95 % de couverture lignes et branches via Vitest (unit + contract) + Playwright e2e. NE MODIFIE PAS le code applicatif (`web/src/`). Pas de git.

Étapes :
1. Lance `cd web && npm run test:coverage` et capture le rapport `web/coverage/`.
2. Liste les fichiers `web/src/` < 95 % et trie par poids (lignes manquantes).
3. Par lot de 10 fichiers :
   a. Pour les utilitaires/hooks/stores : crée un test Vitest dans `web/tests/unit/<chemin-miroir>.test.ts`.
   b. Pour les composants : utilise `@testing-library/react`, teste rendu + interactions + états + a11y minimal.
   c. Pour les clients API : crée un test contract dans `web/tests/contract/`.
4. Ajoute les parcours e2e dans `web/e2e/` listés dans `docs/testing/PLAN_AUGMENT_COVERAGE_TESTS.md` §8.2.6C.
5. Pour chaque nouveau test, exécute uniquement le fichier ajouté pour vérifier l'absence de flakiness.

Règles :
- Pas de snapshot opaque sans assertion sémantique.
- Pas de `it.skip` / `test.skip`.
- Pas de mock de la librairie sous test.
- Réutilise les mocks `web/tests/utils/`.

Validation :
- `npm run test:coverage` ≥ 95 %.
- `npm run test:contract` strict OK.
- `npm run test:e2e` vert (headless).
- Mets à jour `docs/testing/baseline.md` (delta web).

Pas de commit.
```

---

## 9. Phase 7 — Mobile (Flutter)

### 9.1 Pourquoi

`mobile/lib/` est un client significatif (auth, sync offline, push, biométrie). Toute la logique non-UI peut être unit-testée ; les écrans critiques en widget/integration test.

### 9.2 Substeps

- **7.A — Dart unit (`mobile/test/`)**
  - [ ] Pour chaque service Dart (`auth_service`, `sync_service`, `notifications_service`, `biometric_service`) : test des cas succès + erreurs réseau + retries.
  - [ ] Pour chaque repository : test mapping JSON ↔ modèle + persistance sqflite (in-memory).
  - [ ] Pour chaque provider Riverpod : test états (`AsyncValue.data`, `error`, `loading`).

- **7.B — Widget tests**
  - [ ] Pour chaque écran critique (login, dashboard, bulletin, messagerie) : widget test rendant l'écran avec un provider mocké.
  - [ ] Asserter présence des éléments clés + interactions (tap, scroll).

- **7.C — Integration tests (`mobile/integration_test/`)**
  - [ ] Parcours login → dashboard.
  - [ ] Mode offline : déconnexion réseau → cache local affiché → reconnexion → sync.
  - [ ] Push notifications (mock du token).

### 9.3 Validation Phase 7

- [ ] `cd mobile && flutter test --coverage` → `mobile/coverage/lcov.info` ≥ 95 % lignes.
- [ ] `flutter test integration_test/` vert sur émulateur.

### 9.4 Prompt à coller (Phase 7)

```text
Mission : porter `mobile/lib/` à ≥ 95 % de couverture lignes via tests Flutter (unit, widget, integration). NE MODIFIE PAS `mobile/lib/`. Pas de git.

Étapes :
1. Lance `cd mobile && flutter test --coverage` et parse `coverage/lcov.info`.
2. Liste les fichiers < 95 % triés par lignes manquantes.
3. Pour les services et providers : crée `mobile/test/<chemin>_test.dart` avec `mocktail` et `riverpod_test`.
4. Pour les écrans : `mobile/test/screens/<screen>_widget_test.dart`.
5. Pour les parcours : `mobile/integration_test/<flow>_test.dart`.
6. Mocks Firebase / secure_storage / sqflite via packages dédiés (`fake_async`, `sqflite_common_ffi`).

Règles :
- Pas de `skip:` sur les tests.
- Pas d'`expect(true)` ni d'assertion vide.
- Couvre les états `loading`/`error`/`data` de chaque provider.

Validation :
- `flutter test --coverage` ≥ 95 % global.
- `lcov --summary mobile/coverage/lcov.info` archivé sous `artifacts/coverage-baseline/mobile.log`.
- `docs/testing/baseline.md` mis à jour.

Pas de commit.
```

---

## 10. Phase 8 — Verrouillage et validation finale

### 10.1 Substeps

- **8.A — Recalcul global**
  - [ ] Backend : `make test-full` (commande `pytest --cov=app --cov-branch --cov-report=html --cov-report=term-missing --cov-report=xml`).
  - [ ] Web : `npm run test:coverage`.
  - [ ] Mobile : `flutter test --coverage`.
  - [ ] Système : `system-tests/run_tests.sh` (au moins smoke).

- **8.B — Mise à jour des seuils (sans baisse)**
  - [ ] `backend/pyproject.toml` → `[tool.coverage.report] fail_under = 97.9` (uniquement si ≥ atteint).
  - [ ] `scripts/run-backend-test-suite.sh` → exporter `COV_FAIL_UNDER=97.9` dans la CI (laisser default à 0 pour dev local).
  - [ ] `web/vite.config.ts` / `vitest.config.ts` → `coverage.thresholds.lines = 95` (et branches/statements/functions).
  - [ ] CI : vérifier que la matrice GitHub Actions consomme ces seuils.

- **8.C — Tableau de preuve**
  - [ ] Créer `docs/testing/COVERAGE_REPORT_FINAL.md` :
    - couverture par aire (avant / après / delta) ;
    - tableau « modules à 100 % » ;
    - tableau « modules restants à risque » (si on a dû s'arrêter avant 97,9 %) ;
    - commandes utilisées et hash de l'env (`pip freeze`, `npm ls`, `flutter --version`).
  - [ ] Ajouter une checklist auto-portante listant les commandes pour rejouer la validation.

- **8.D — Sanity checks**
  - [ ] Aucun `# pragma: no cover` ajouté.
  - [ ] `omit` dans `pyproject.toml` inchangé.
  - [ ] Aucun seuil baissé.
  - [ ] Aucun test supprimé.
  - [ ] Aucun test sans assertion (`grep -nE 'def test_[^(]*\(.*\):\s*pass'`).

### 10.2 Prompt à coller (Phase 8)

```text
Mission : verrouiller la couverture à ≥ 97,9 % global et produire le rapport final. Pas de modif code applicatif. Pas de git.

Étapes :
1. Recalcule la couverture des trois stacks (backend, web, mobile) avec les commandes du §10.1.8A.
2. Vérifie que le global atteint ≥ 97,9 % LIGNES + BRANCHES sur chaque stack. Si non, ARRÊTE-TOI et liste les modules restants à risque dans `docs/testing/COVERAGE_REPORT_FINAL.md`. Ne rentre pas dans le code applicatif.
3. Si le seuil est atteint :
   - relève `fail_under` dans `backend/pyproject.toml` à 97.9 (pas plus haut).
   - relève les seuils Vitest dans `web/vitest.config.ts` à 95 / 95 / 95 / 95.
   - dans `scripts/run-backend-test-suite.sh`, documente `COV_FAIL_UNDER=97.9` dans la doc CI (sans changer la valeur par défaut locale).
4. Génère `docs/testing/COVERAGE_REPORT_FINAL.md` :
   - tableau avant/après par aire ;
   - liste des fichiers à 100 % ;
   - commandes de validation reproductibles ;
   - hash env (`pip freeze`, `npm ls --depth=0`, `flutter --version`).
5. Effectue les sanity checks du §10.1.8D et reporte-les dans le rapport.

Pas de commit. Pas de stage git. Pas de baisse de seuil. Pas de pragma. Pas d'ajout dans omit.
```

---

## 11. Synthèse — Checklist maître

Une seule case par phase. À cocher à la fin de chaque phase, en l'attachant au rapport `docs/testing/baseline.md`.

- [ ] Phase 0 — Baseline reproductible générée.
- [ ] Phase 1 — `app/core/*` ≥ 95 %.
- [ ] Phase 2 — Services à 0 % couverts ≥ 95 %.
- [ ] Phase 3 — `auth`, `progress`, `ai`, `kpi`, `quiz_grading` ≥ 90 %.
- [ ] Phase 4 — `app/api/v1/*` ≥ 95 % + contracts OpenAPI verts.
- [ ] Phase 5 — workers + repositories + `core/tasks` ≥ 95 %.
- [ ] Phase 6 — `web/` ≥ 95 % unit/contract + e2e critiques verts.
- [ ] Phase 7 — `mobile/` ≥ 95 % unit/widget/integration.
- [ ] Phase 8 — Global ≥ 97,9 %, rapport final publié, sanity checks OK.

---

## 12. Annexes

### 12.1 Anti-patterns à refuser

- Tests sans assertion (`pass`, `assert True`).
- Tests qui ne font qu'importer un module.
- Mocks de la fonction sous test.
- `pytest.mark.skip` sans justification écrite (utiliser `pytest.mark.xfail(strict=True)` avec raison).
- Snapshots opaques sans matcher sémantique.
- Tests qui se basent sur l'ordre de tests précédents.
- Tests qui dépendent de l'heure réelle (utiliser `freezegun`).

### 12.2 Outils recommandés

- **Backend** : `pytest-asyncio`, `pytest-cov`, `pytest-mock`, `respx`, `httpx`, `fakeredis`, `freezegun`, `polyfactory` (ou continuer avec les factories maison), `dirty-equals` pour les assertions partielles.
- **Web** : `vitest`, `@testing-library/react`, `msw` pour les mocks API, `@axe-core/playwright`, `@playwright/test`.
- **Mobile** : `mocktail`, `riverpod_test`, `sqflite_common_ffi`, `fake_async`, `network_image_mock`.

### 12.3 Garde-fous pour l'agent IA exécutant

À rappeler dans chaque prompt envoyé :

1. Ne modifie pas `app/`, `web/src/`, `mobile/lib/`, `infra/`, `alembic/`.
2. Ne baisse aucun seuil.
3. Ne supprime aucun test existant.
4. Aucun `git add`, `git commit`, `git push`, `git stash`.
5. Tout résultat doit être reproductible par une commande unique listée dans le rapport.
6. Si un test révèle un bug, écrire un `xfail(strict=True)` documenté et reporter dans `docs/testing/anomalies.md`. Ne pas corriger le bug.
7. Pas de mock de la fonction sous test, pas de pragma, pas d'ajout dans `omit`.

### 12.4 Prompt « kickoff » consolidé

Si tu veux relancer toute la séquence d'un coup :

```text
Tu es chargé d'augmenter la couverture des tests du dépôt Ecole Platform à ≥ 97,9 % SANS modifier le code applicatif (backend/app, web/src, mobile/lib, infra). Tu suis EXACTEMENT le plan `docs/testing/PLAN_AUGMENT_COVERAGE_TESTS.md`, phase par phase, de la Phase 0 à la Phase 8.

Règles absolues :
- Aucun `git add`, `git commit`, `git push`, `git stash`.
- Aucune baisse de seuil, aucune `# pragma: no cover`, aucun ajout dans `omit`.
- Aucune suppression / affaiblissement de test existant.
- À la fin de chaque phase, mets à jour `docs/testing/baseline.md` avec la couverture mesurée.
- Si une phase échoue à atteindre sa cible, ARRÊTE-TOI, documente précisément (modules, lignes, raison) dans `docs/testing/anomalies.md`, et attends instruction.

Commence par la Phase 0.
```

---

*Fin du plan.*
