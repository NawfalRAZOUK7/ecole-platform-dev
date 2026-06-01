# Baseline de couverture — 2026-05-28 (mis à jour 2026-06-01)

> Généré automatiquement. Ne pas modifier manuellement.
> Artefacts : `artifacts/coverage-baseline/`

---

## Résumé exécutif

| Aire | Statut | Couverture globale | Tests exécutés |
|------|--------|-------------------|----------------|
| **Backend** | ⚠ Partiel (unit only) | **40.3 % ligne (global) / 94 % app/core / 100 % 5 services cibles** | Tests unitaires + edge uniquement |
| **Web** | ✅ Tests débloqués | **En cours (forks CI mode)** | 165 fichiers de tests, contract ✅ |
| **Mobile** | ⚠ Delta Phase 6 | **32.5 % ligne** (+2.5 pp) | 253 tests passés |

---

## Phase 3 — Services backend 0 % → 100 % (2026-05-29)

**Cibles** : 5 services à 0 % ou très bas couverts à **100 % branche**  
**Résultat** : 295 stmts, 0 manquants, 58 branches, 0 partielles → **100 %**  
**Tests ajoutés** : 124 tests (568 passés au total dans `tests/unit/services`)

### Delta de couverture

| Module | Avant | Après | Tests |
|--------|-------|-------|-------|
| `app/services/communication/sms.py` | 38 % | **100 %** | `test_sms.py` (31 tests) |
| `app/services/communication/overdue_reminders.py` | 0 % | **100 %** | `test_overdue_reminders.py` (14 tests) |
| `app/services/billing/payment_retry.py` | 0 % | **100 %** | `test_payment_retry.py` (22 tests) |
| `app/services/lms/quiz_grading.py` | 16 % | **100 %** | `test_quiz_grading.py` (37 tests) |
| `app/services/reports/kpi.py` | 26 % | **100 %** | `test_kpi.py` (20 tests) |

### Stratégie de mock

- **sms.py** : injection de provider via `SMSService(provider=mock)`, rate-limit via état global `_daily_counts` réinitialisé entre tests. Aucun I/O réel.
- **overdue_reminders.py** : toutes les imports lazies patchées (`async_session`, `UnitOfWork`, `BillingRepository`, `enqueue_email`, `AuditService`). Fake context-manager pour la session.
- **payment_retry.py** : même stratégie. Branches testées : premier retry, retry intermédiaire, échec final (avec/sans parent), backoff hors-liste, exception swallowed, `schedule_retry_for_failed_payment` avec et sans `_uow_depth`.
- **quiz_grading.py** : 5 graders purs testés directement + `grade_attempt()` via `FakeQuizRepository`. Deux chemins UoW testés (depth=1 et depth=0).
- **kpi.py** : `AnalyticsRepository` patché au niveau module (`app.services.reports.kpi.AnalyticsRepository`). Division par zéro testée pour chaque KPI. `compute_all_kpis` testé avec succès et avec exception (error entry).

### Validation Phase 3

```bash
cd backend && .venv/bin/python -m pytest tests/unit/services -q
# 568 passed

.venv/bin/python -m pytest tests/unit/services/test_sms.py \
  tests/unit/services/test_overdue_reminders.py \
  tests/unit/services/test_payment_retry.py \
  tests/unit/services/test_quiz_grading.py \
  tests/unit/services/test_kpi.py \
  --cov=app.services.communication.sms \
  --cov=app.services.communication.overdue_reminders \
  --cov=app.services.billing.payment_retry \
  --cov=app.services.lms.quiz_grading \
  --cov=app.services.reports.kpi \
  --cov-branch --cov-report=term-missing
# TOTAL 295 stmts, Miss 0, Branch 58, BrPart 0 → 100 %
```

---

## Phase 2 — Couverture app/core (2026-05-29)

**Objectif** : ≥ 95 % branche sur `app/core/*`  
**Résultat** : **94 %** (2163 stmts, 105 manquants, 372 branches, 14 partielles)

### Modules portés à ≥ 95 % (cibles primaires)

| Module | Avant | Après | Tests |
|--------|-------|-------|-------|
| `app/core/totp.py` | 0 % | **100 %** | `test_totp.py` (35 tests) |
| `app/core/idempotency.py` | 20 % | **98 %** | `test_idempotency.py` (17 tests) |
| `app/core/rate_limit.py` | 18 % | **100 %** | `test_rate_limit.py` (35 tests) |
| `app/core/feature_flags.py` | 25 % | **100 %** | `test_feature_flags.py` (38 tests) |
| `app/core/tasks.py` | 12 % | **98 %** | `test_tasks.py` (48 tests) |

### Modules supplémentaires couverts

| Module | Avant | Après |
|--------|-------|-------|
| `app/core/password_policy.py` | 0 % | 100 % |
| `app/core/security_headers.py` | 0 % | 100 % |
| `app/core/business_metrics.py` | 0 % | 100 % |
| `app/core/search.py` | 22 % | 100 % |
| `app/core/unit_of_work.py` | 32 % | 100 % |
| `app/core/middleware.py` | 46 % | 100 % |
| `app/core/security.py` | 63 % | 100 % |
| `app/core/filtering.py` | 23 % | 100 % |
| `app/core/request_utils.py` | 0 % | 100 % |
| `app/core/ws_manager.py` | 16 % | 99 % |
| `app/core/telemetry.py` | 0 % | 100 % |
| `app/core/db_routing.py` | 0 % | 100 % |
| `app/core/metrics.py` | 69 % | 100 % |
| `app/core/redis.py` | 61 % | 100 % |

### Modules hors-cible non couverts (Phase 5)

Les modules suivants nécessitent une infrastructure réelle (DB async, FastAPI DI) et sont différés en Phase 5 :

| Module | Couverture | Raison du blocage |
|--------|-----------|-------------------|
| `app/core/database.py` | 69 % | Création d'engine SQLAlchemy réel requis |
| `app/core/dependencies.py` | 34 % | FastAPI Depends() + JWT + sessions DB réelles |
| `app/core/downloads.py` | 54 % | Backend de stockage (S3/local) requis |
| `app/core/storage.py` | 86 % | Edge cases S3/MinIO |

**Bug découvert** : `task_cleanup_expired_sessions` utilise `Session.revoked_at` (inexistant) — le modèle définit `Session.revoke_at`. L'exception est catchée silencieusement. Documenté dans les tests.

### Commande de validation

```bash
cd backend && .venv/bin/python -m pytest tests/unit/core \
  --cov=app.core --cov-branch --cov-report=term-missing
```

Résultat : **TOTAL 2163 stmts, Miss 105, Branch 372, BrPart 14, Cover 94 %**  
(1368 tests unitaires passés, 1 skippé)

---

## Blocages et causes exactes

### Backend — Sentry SDK incompatible

**Commande** : `cd backend && .venv/bin/python -m pytest --cov=app --cov-branch --cov-report=xml:coverage.xml --cov-report=html:htmlcov --cov-report=term-missing -q`

**Erreur** :
```
TypeError: Unknown option 'enable_logs'
  app/main.py:35  →  sentry_sdk.init(enable_logs=True, ...)
```

**Cause** : `app/main.py` utilise l'option `enable_logs=True` ajoutée dans sentry-sdk ≥ 2.26.
`requirements.txt` épingle `sentry-sdk[fastapi]==2.25.*` (installé : 2.25.1).
Les suites `tests/integration`, `tests/contract` et `tests/security` importent `app.main`,
ce qui déclenche l'erreur à la phase de collection. Seules les suites `tests/unit` et
`tests/edge` — qui n'importent pas `app.main` directement — ont pu tourner.

**Impact** : couverture backend limitée à ~40 % (unit/edge). Les routes HTTP, la sécurité
RBAC et les tests de contrat sont exclus.

---

### Web — NODE_ENV=production bloque l'installation des devDependencies

**Commande** : `cd web && npm ci && npm run test:coverage -- --reporter=verbose`

**Erreur** :
```
sh: vitest: command not found
```

**Cause** : `NODE_ENV=production` est défini dans le shell courant. `npm ci` en mode
production ignore les `devDependencies`, donc `vitest` et `@vitest/coverage-v8` ne sont
pas installés. Aucun test n'a pu tourner ; aucun artefact de couverture n'est disponible.

**Fix requis** : démarrer la session avec `NODE_ENV=test` ou `NODE_ENV=development`,
ou passer `--include=dev` à `npm ci`. Ne pas modifier la source.

---

## Backend — Couverture (tests unitaires + edge uniquement)

> Python 3.14.2 · pytest · sentry-sdk 2.25.1 (incompatible avec `enable_logs`)
> Coverage total : **40.3 %** (29 982 lignes déclarées, 17 889 manquantes)

### Récapitulatif par aire

| Aire | Lignes valides | Lignes manquantes | % ligne |
|------|---------------|-------------------|---------|
| `app/api` | 3 581 | 1 693 | **52.7 %** |
| `app/repositories` | 4 489 | 3 278 | **27.0 %** |
| `app/core` | 2 163 | 1 302 | **39.8 %** |
| `app/services` | 12 711 | 10 247 | **19.4 %** |
| `app/workers` | 140 | 122 | **12.9 %** |
| _autres (seeds, schemas…)_ | 6 898 | 1 247 | **81.9 %** |
| **TOTAL** | **29 982** | **17 889** | **40.3 %** |

> `app/api` bénéficie de la couverture directe des tests unitaires des routes.
> `app/services` est le plus grand gap absolu (10 247 lignes) : les services métier
> ne sont exercés que via les intégrations, qui n'ont pas tourné.

### Top 30 fichiers les moins couverts

| Chemin (`app/`) | Lignes val. | Manquantes | % ligne | % branche | Plages non couvertes (extrait) | Hypothèse de gap |
|-----------------|-------------|-----------|---------|-----------|-------------------------------|-----------------|
| `seed_enhanced.py` | 478 | 478 | 0.0 % | 0.0 % | 17, 19-21, 23-24, 27, 41, 60 | Script de seed — hors périmètre test |
| `seed_extensions.py` | 106 | 106 | 0.0 % | 0.0 % | 6, 8-9, 11-12, 14-15, 24, 32 | Script de seed — hors périmètre test |
| `core/db_routing.py` | 19 | 19 | 0.0 % | 100.0 % | 3, 5, 7, 9, 11, 18-19, 24, 29 | Routing multi-tenant — nécessite intégration |
| `core/telemetry.py` | 24 | 24 | 0.0 % | 0.0 % | 3-12, 14, 16, 19, 23-24 | Init OpenTelemetry — jamais importé en unit |
| `core/totp.py` | 38 | 38 | 0.0 % | 0.0 % | 10, 12-13, 15-16, 22-27, 33, 39 | TOTP 2FA — dépend de `app.main` (bloqué) |
| `domain/protocols/__init__.py` | 3 | 3 | 0.0 % | 100.0 % | 3-4, 10 | Protocoles abstraits — non instanciés |
| `domain/protocols/evaluatable.py` | 13 | 13 | 0.0 % | 100.0 % | 3, 5-6, 9-10, 13, 21, 23 | Protocole abstrait — non instancié |
| `domain/protocols/grading.py` | 81 | 81 | 0.0 % | 0.0 % | 3, 5-7, 9, 12, 15, 18, 21-24 | Protocole de notation — non instancié |
| `schemas/reports/analytics.py` | 23 | 23 | 0.0 % | 100.0 % | 3, 5, 7, 10-14, 17-20, 23-26 | Schémas de rapport — sans tests unitaires |
| `services/billing/payment_retry.py` | 71 | 71 | 0.0 % | 0.0 % | 13, 15-16, 18, 21-22, 25, 30-33 | Retry paiement — aucun test dédié |
| `services/communication/overdue_reminders.py` | 42 | 42 | 0.0 % | 0.0 % | 14, 16-17, 19, 21-23, 26, 31-35 | Rappels retard — worker async, non testé |
| `services/platform/suspicious_activity.py` | 38 | 38 | 0.0 % | 0.0 % | 6-7, 9-10, 12, 15, 18-24, 26 | Détection fraude — aucun test |
| `services/auth/auth.py` | 720 | 638 | 11.4 % | 0.0 % | 86-92, 99-108, 111, 114-133 | Auth OAuth/webauthn — nécessite intégration |
| `services/lms/quiz_service.py` | 195 | 172 | 11.8 % | 0.0 % | 33-37, 50, 66, 76, 78-79, 83 | Logique quiz — pas de mock complet |
| `services/billing/budget_service.py` | 369 | 325 | 11.9 % | 0.0 % | 49, 56-59, 62, 77, 99, 121 | Service budget — logique financière complexe |
| `services/lms/program_service.py` | 354 | 312 | 11.9 % | 0.0 % | 54, 58, 68-70, 76, 99, 116-118 | Gestion programmes — flux multi-étapes |
| `core/tasks.py` | 386 | 337 | 12.7 % | 6.2 % | 58, 72-73, 75-77, 83-86, 88-95 | Tâches Arq/async — besoin fixtures worker |
| `services/ai/mock_provider.py` | 79 | 69 | 12.7 % | 0.0 % | 14-22, 25-27, 32-34, 39-40, 45 | Provider IA mock — testé via vrai provider |
| `workers/post_upload.py` | 140 | 122 | 12.9 % | 0.0 % | 51, 53-54, 56-58, 63, 65-67 | Worker upload — dépend de MinIO et S3 |
| `services/academic/erp.py` | 334 | 290 | 13.2 % | 0.0 % | 57-59, 68, 79, 97, 106, 118 | Service ERP — intégration Odoo/externe |
| `services/reports/reports.py` | 547 | 475 | 13.2 % | 0.0 % | 65, 69-78, 82-86, 90-96 | Rapports PDF/Excel — génération lourde |
| `services/school/micro_school_service.py` | 501 | 435 | 13.2 % | 0.0 % | 60, 65-68, 71, 74, 81-84 | Gestion école — 500+ lignes, flux CRUD |
| `services/billing/billing.py` | 448 | 388 | 13.4 % | 0.0 % | 67-71, 74, 92, 106, 129, 142 | Paiement Stripe — intégration nécessaire |
| `services/academic/gradebook.py` | 234 | 202 | 13.7 % | 0.0 % | 37-39, 42-43, 50-54, 67, 83-86 | Carnet de notes — calculs complexes |
| `services/academic/skill_passport_service.py` | 442 | 376 | 14.9 % | 0.0 % | 77, 82-85, 88-89, 95-96 | Passeport compétences — non priorisé |
| `services/communication/event_dispatcher.py` | 213 | 181 | 15.0 % | 0.0 % | 128-132, 135-143, 145-156 | Dispatcher événements — flux async |
| `services/academic/progress.py` | 203 | 171 | 15.8 % | 0.0 % | 29-30, 34-47, 54, 62-75 | Progression élève — dépend de BDD |
| `services/academic/timetable_generator.py` | 441 | 371 | 15.9 % | 0.0 % | 77-83, 88, 102, 122, 130-154 | Génération EDT — algorithme complexe |
| `services/content/cms.py` | 189 | 159 | 15.9 % | 0.0 % | 36-38, 41, 66, 95-116 | CMS contenu — flux upload/asset |
| `services/admin/service.py` | 181 | 152 | 16.0 % | 0.0 % | 23-28, 35-37, 40-42, 69, 77 | Service admin — RBAC multi-rôle |

---

## Web — BLOQUÉ

Aucune donnée de couverture disponible.

**Cause** : `NODE_ENV=production` → `npm ci` ignore devDependencies → `vitest` absent.

**Fix** : lancer `NODE_ENV=test npm ci && npm run test:coverage -- --reporter=verbose`.

---

## Mobile — Couverture (suite complète)

> Flutter 3.35.7 · Dart 3.9.2 · 242 tests passés (0 échecs)
> Coverage total : **30.0 %** (22 730 lignes, 15 903 manquantes)

### Top 10 fichiers les moins couverts

| Chemin (`lib/`) | Lignes val. | Manquantes | % ligne | % branche | Plages non couvertes (extrait) | Hypothèse de gap |
|-----------------|-------------|-----------|---------|-----------|-------------------------------|-----------------|
| `core/network/ws_client.dart` | 93 | 93 | 0.0 % | 100.0 % | 30, 32, 34, 36, 38, 40, 42 | Client WebSocket — nécessite serveur live |
| `data/repositories_impl/ai/rewards_repository.dart` | 22 | 22 | 0.0 % | 100.0 % | 8, 10, 12-13, 16, 18-19, 22 | Repo récompenses IA — non mocké |
| `shared/services/tts_service.dart` | 65 | 65 | 0.0 % | 100.0 % | 9, 61, 64-66, 68, 71-78 | Service TTS — dépend de plugin natif |
| `shared/ui/tokens/radii.dart` | 1 | 1 | 0.0 % | 100.0 % | 2 | Token UI const — importé mais non instancié |
| `shared/ui/tokens/spacing.dart` | 1 | 1 | 0.0 % | 100.0 % | 2 | Token UI const — importé mais non instancié |
| `shared/ui/tokens/typography.dart` | 1 | 1 | 0.0 % | 100.0 % | 4 | Token UI const — importé mais non instancié |
| `shared/widgets/app_date_picker.dart` | 24 | 24 | 0.0 % | 100.0 % | 9, 16, 18, 20, 22, 24 | Widget date — pas de test widget dédié |
| `features/academic/student/transcript_pdf_screen.dart` | 25 | 25 | 0.0 % | 100.0 % | 15, 21-22, 25-27, 30-31, 35 | Écran PDF — rendu natif non testable |
| `features/auth/register_steps.dart` | 139 | 139 | 0.0 % | 100.0 % | 4-5, 7-8, 11-12, 16-17, 29 | Inscription multi-étapes — pas de test widget |
| `features/auth/reset_password_screen.dart` | 45 | 45 | 0.0 % | 100.0 % | 11, 16, 18, 27, 29-30, 33 | Reset MDP — pas de test widget |

---

## Phase 6 — Mobile (delta 2026-06-01)

**Objectif** : `mobile/lib/` → ≥ 95 % lignes.  
**Résultat** : **32.5 %** (7 379 / 22 730 lignes) — delta **+2.5 pp** par rapport à 30.0 %.  
**Tests ajoutés** : 11 fichiers, 110+ tests.

### Nouveaux tests créés

| Fichier test | Cible source | Lignes couvertes |
|---|---|---|
| `test/unit/rewards_repository_test.dart` | `data/repositories_impl/ai/rewards_repository.dart` | 22 → ~95% |
| `test/unit/tts_service_test.dart` | `shared/services/tts_service.dart` | 65 → ~85% |
| `test/unit/ws_client_test.dart` | `core/network/ws_client.dart` | 93 → ~40% |
| `test/unit/reporting_repository_test.dart` | `data/repositories_impl/reports/reporting_repository_impl.dart` | 164 → ~70% |
| `test/unit/gradebook_repository_test.dart` | `data/repositories_impl/academic/gradebook_repository_impl.dart` | 108 → ~80% |
| `test/unit/micro_school_repository_test.dart` | `data/repositories_impl/school/micro_school_repository_impl.dart` | 111 → ~65% |
| `test/unit/rubric_repository_test.dart` | `data/repositories_impl/lms/rubric_repository_impl.dart` | 88 → ~85% |
| `test/unit/invoice_repository_test.dart` | `data/repositories_impl/billing/invoice_repository_impl.dart` | 71 → ~60% |
| `test/unit/quiz_repository_test.dart` | `data/repositories_impl/lms/quiz_repository_impl.dart` | 68 → ~75% |
| `test/unit/ui_tokens_test.dart` | `shared/ui/tokens/radii|spacing|typography.dart` | 3 → 100% |
| `test/widget/reset_password_screen_test.dart` | `features/auth/reset_password_screen.dart` | 45 → ~80% |
| `test/widget/app_date_picker_test.dart` | `shared/widgets/app_date_picker.dart` | 24 → ~90% |

### Blocage principal vers 95%

Le principal frein est la masse de code UI non couverte (~14 000 lignes) :
- **200+ fichiers d'écrans Flutter** (0–5% chacun, 100–500 lignes)
- Chaque écran nécessite un test widget dédié avec providers mockés
- Stratégie recommandée : prioriser les 30 fichiers avec > 100 lignes manquantes

### Fichiers prioritaires restants (> 100 lignes manquantes)

| Fichier | Manquantes | % actuel |
|---|---|---|
| `features/content/student/student_content_screen.dart` | 542 | 0.2% |
| `features/academic/teacher/class_progress_screen.dart` | 370 | 0.3% |
| `features/content/documents/documents_actions.dart` | 298 | 0.0% |
| `features/lms/submissions/submission_upload_screen.dart` | 275 | 0.0% |
| `features/content/student/story_reader_screen.dart` | 252 | 0.8% |
| `features/communication/calendar/create_event_screen.dart` | 247 | 0.0% |
| `features/lms/quizzes/quiz_analytics_screen.dart` | 242 | 0.0% |
| `features/reports/analytics/analytics_summary_screen.dart` | 238 | 0.4% |
| `features/ai/games/game_provider.dart` | 230 | 0.0% |
| `features/lms/teacher/submissions_screen.dart` | 223 | 0.9% |

---

## Artefacts générés

| Artefact | Chemin | Statut |
|----------|--------|--------|
| Log backend | `artifacts/coverage-baseline/backend.log` | ✅ |
| Coverage XML backend | `backend/coverage.xml` | ✅ |
| Coverage HTML backend | `backend/htmlcov/` | ✅ |
| Log web | `artifacts/coverage-baseline/web.log` | ✅ (tests débloqués 2026-06-01) |
| Coverage web JSON | — | ⏳ (en cours, forks mode) |
| Log mobile (Phase 6) | `artifacts/coverage-baseline/mobile.log` | ✅ |
| LCOV mobile | `artifacts/coverage-baseline/mobile-lcov.info` | ✅ |

---

## Prochaines actions recommandées

1. **Backend** : mettre à jour `sentry-sdk` vers `>=2.26` dans `requirements.txt` pour débloquer les 3 suites manquantes (intégration, contrat, sécurité) et obtenir une couverture réelle.
2. **Web** : s'assurer que `NODE_ENV` n'est pas `production` lors des sessions de CI/test locaux.
3. **Priorités couverture backend** : `services/auth/auth.py` (720 lignes, 11 %), `services/reports/reports.py` (547 lignes, 13 %), `services/billing/billing.py` (448 lignes, 13 %) — fort impact, gap structurel.
4. **Priorités couverture mobile** : `core/network/ws_client.dart` (WebSocket), `features/auth/register_steps.dart` (inscription), `features/auth/reset_password_screen.dart` (reset) — flux utilisateur critiques sans aucun test.
