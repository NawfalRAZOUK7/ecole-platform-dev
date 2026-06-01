# Test Anomalies — Phase 4 API Coverage

> Tests that reveal suspected bugs in the application code.  
> Per convention: **NE PAS corriger le code applicatif** — marquer `xfail(strict=True)` et lister ici.  
> Date de détection: 2026-05-29  
> Branche: feat/new-modifications

---

## ANO-001 — `Grade.student_id` AttributeError in GDPR data export

| Champ | Valeur |
|---|---|
| **Sévérité** | Medium |
| **Module affecté** | `app/repositories/user_gdpr.py:89` |
| **Route affectée** | `GET /users/{user_id}/data-export` |
| **Test xfail** | `tests/integration/api/user/test_gdpr_api.py::TestDataExport::test_user_can_export_own_data` |
| **Reproduire** | `pytest tests/integration/api/user/test_gdpr_api.py::TestDataExport::test_user_can_export_own_data -v` |

### Symptôme

```
AttributeError: type object 'Grade' has no attribute 'student_id'
  File "app/repositories/user_gdpr.py", line 89, in list_grades
      .where(Grade.student_id == student_id)
```

### Cause probable

Dans `app/repositories/user_gdpr.py`, la méthode `list_grades` utilise `Grade.student_id`
comme attribut de colonne SQLAlchemy. Cependant, le modèle `Grade` (défini dans
`app/models/lms.py`) n'expose pas `student_id` directement — il est accessible via
la relation `submission.student_id` ou une jointure vers `Submission`.

### Impact

- Export GDPR des données d'un étudiant retourne 500 au lieu de 200.
- Les tests `test_user_can_export_own_data` et `test_admin_can_export_any_user_data`
  sont marqués `xfail(strict=True)` pour maintenir la visibilité du bug sans bloquer la CI.

### Recommandation (sans modifier app)

Corriger `app/repositories/user_gdpr.py:89` pour joindre la table `submissions` et
filtrer via `Submission.student_id == student_id` avant de sélectionner les grades,
ou utiliser `Grade.submission.has(Submission.student_id == student_id)`.

---

---

## INFRA-001 — Deadlock `TRUNCATE ALL` lors du teardown d'`isolated_legacy_api_db`

| Champ | Valeur |
|---|---|
| **Sévérité** | Infrastructure (non-bloquant en CI propre) |
| **Fixture affectée** | `tests/integration/api/conftest.py::isolated_legacy_api_db` |
| **Symptôme** | `asyncpg.exceptions.DeadlockDetectedError` lors du TRUNCATE ALL TABLES en teardown |
| **Trigger** | Connexions inactives du pool SQLAlchemy tenues ouvertes par le client ASGI pendant la teardown |

### Cause

`isolated_legacy_api_db` exécute `TRUNCATE TABLE ... CASCADE` (toutes les tables en une seule
requête) à la fois en setup ET en teardown. PostgreSQL doit acquérir `AccessExclusiveLock` sur
chaque table simultanément. Si des connexions du pool de l'app (test ASGI) ont encore des
verrous partiels, un deadlock se produit.

### Impact

- Sur une DB partagée avec des connexions actives (machine dev), les tests successive se bloquent.
- En CI avec une DB isolée et fraîche (Docker éphémère, `--forked`, ou DB per-worker), ce problème
  n'apparaît pas.
- **Le premier batch de tests** (DB propre, avant le premier teardown) **s'est exécuté correctement** :
  3 passed, 1 xfailed (ANO-001).

### Résolution (sans toucher au code applicatif)

Option recommandée pour CI : utiliser une DB dédiée per-session pytest (`DATABASE_URL=...test_db_$RANDOM`).

Mitigation implémentée : ajout de `ON CONFLICT DO NOTHING` dans `seed_level_mappings`
(`tests/integration/conftest.py:135`) pour que la fixture de seed ignore les doublons après
un teardown incomplet.

---

## Résumé des anomalies

| ID | Module | Severité | Test xfail | Statut |
|---|---|---|---|---|
| ANO-001 | `user_gdpr.py:89` | Medium | `test_gdpr_api.py::TestDataExport::test_user_can_export_own_data` | Ouvert |

---

## Note méthodologique

Tous les tests marqués `xfail(strict=True)` dans ce projet signifient:
- La fonctionnalité est implémentée (la route existe et est routée)
- Mais un comportement incorrect a été observé (bug applicatif confirmé)
- Le test va **échouer** en production jusqu'à ce que le bug soit corrigé
- Si le bug est corrigé sans mettre à jour le marqueur, le test devient `XPASS` (fail inattendu)

Pour lister tous les xfails:
```bash
pytest tests/integration/api/ tests/contract/ -v --no-header 2>&1 | grep xfail
```
