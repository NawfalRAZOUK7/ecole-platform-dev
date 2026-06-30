# Prompt prêt à coller — Codex (suite + exécution)

> Lis d'abord **`PRODUCT_QUALITY_PASS.md`** (décisions verrouillées D1–D4, matrices §2/§3, corrections par cause, état fait/reste §7–§9). Implémente le « reste », puis exécute et teste. N'invente pas de routes : n'ajoute un module à un client que si l'écran existe déjà ; sinon, signale-le.

## 0. Taxonomie & migrations backend — état à jour (lire avant tout `make migrate`)

> Initiative taxonomie/enums documentée dans **`EDUCATION_TAXONOMY.md`** (source de vérité des décisions) + **`BACKEND_DB_AUDIT.md` §9–§11**. `app/models/taxonomy.py` = SoT code.

- **Fait (chaîne cohérente `617 → 625`, 9 migrations) :** promotion enums natifs (mig 622) ; **A1** `GameDifficulty`→`DifficultyLevel` ; **A2** auto-réparation des agrégats budget (`recompute_budget_rollups`) ; **A3** `RetentionMetric` reclassé ; **B1** `conversations.subject→subject_line`, `writing_attempts.subject→topic` (mig 623) ; **B4** `payment_proofs` supprimée (mig 624) ; **B3** `micro_budgets→school_budgets` (mig 625) ; **`taxonomy.py` réécrit aux valeurs marocaines (MEN)**.
- **⚠️ Brouillon périmé — NE PAS exécuter tel quel :** la migration `20260626` (B2 Phase 1) + ses éditions de modèles ont été écrites **avant** la réécriture marocaine et **codent en dur les anciens niveaux français** (`maternelle/CP/CE1/CE2/CM1/CM2/…`). Elle est en tête de chaîne Alembic : **`make migrate` créerait des enums aux mauvaises valeurs.** Refaire B2 (tâche 13) **avant** de migrer.
- **Non démarré (tâches 13–17) :** **13** B2 enums natifs `subject`/`level_band` (Phase 1 *à refaire* + Phase 2 `resources`/`timetable_slots`/`difficulty_adaptations`/`men_curricula` + `MicroSchool.type`/`type_detail` + remap seed marocain §8) ; **14** soft-delete (mixin + filtrage lecture) ; **15** bascule i18n backend (sérialiseurs → `tr()`, drop colonnes `*_fr/_ar/_en`) ; **16** renommages de champs côté clients web/mobile (B1/B3, enums) ; **17** mobile i18n (340 chaînes).
- **TODO (hors périmètre, volontairement) :** détail niveau→matière collège/lycée ; matières `amazigh` + `quranic` ; niveaux coraniques (hifz) du msid ; UX `MicroSchool.type_detail`.
- **`make migrate` n'est sûr qu'après correction du `626` périmé** (voir tâche 13).

## 1. Nav — finir depuis la matrice (§2, §8)
- **Parité web↔mobile par rôle** : aligner STD et TCH (puis PAR, EDUCATOR) sur les ensembles listés au §8. Ajouter les modules manquants **uniquement** si l'écran/route existe des deux côtés ; lister ceux qui manquent réellement.
- **DIR vs ADM** : retirer de la nav DIR (mobile `shell_screen.dart`) les items ADM-only `/admin/invitations`, `/admin/features`, `/admin/school` ; garder DIR = dashboards/analytics/budgets/reports/conformité. Vérifier la cohérence côté web.
- **`/reports`** : réconcilier web (`ReportsPage`, génération) vs mobile (`compliance_report_screen`) — même route, écrans différents. Choisir une route distincte ou un écran commun.
- Idempotence : conserver les **garde-fous anti-doublon** déjà en place (web `Layout.tsx`, mobile `shell_screen.dart`) et le **gating `/micro-schools` par type** (déjà posé).
- (Optionnel) Externaliser une **matrice de nav partagée** (config unique) pour éviter la dérive future.

## 2. Mobile — défense en profondeur
- Ajouter des **métadonnées de rôle par `GoRoute`** (`mobile/lib/app/router/app_router.dart`) et rediriger vers la route par défaut du rôle si accès non autorisé. Le backend reste le garant réel des données.

## 3. Mobile i18n (~340 chaînes en dur restantes ; 4 écrans déjà externalisés — tâche 17)
- Externaliser les chaînes UI codées en dur vers les ressources de localisation Flutter (ARB / `AppLocalizations`), pour `fr`/`ar`/`en`. Prioriser : timetable, billing, micro-schools, question bank, rubrics, games, profile, auth. Ajouter une vérification (script) qui échoue si une chaîne UI littérale réapparaît dans ces écrans.

## 4. Backend — déjà fait, à valider
- Portée par affectation appliquée : `get_content_item`, `list_class_content`, `list_content_items` (allowlist), `update_content_progress`, `complete_content_item`, `get_content_asset`. **Écrire/lancer les tests de sécurité** : un STD/PAR ne peut pas lire/streamer un `content_item` non affecté à sa classe, **même par appel API direct** (404).
- (Reste) Filtre **niveau** pour la bibliothèque CMS de l'enseignant (TCH ne voit que ses niveaux) — à ajouter dans `list_content_items` (param level∈niveaux du prof).

## 5. i18n — relecture
- Faire **relire l'arabe** des 229 clés ajoutées (`web/scripts/i18n-fill.mjs`) par un locuteur natif. Garde CI : `cd web && npm run i18n:check` (doit rester vert).

## 6. Seed — matrice de personas (§3) — DERNIÈRE étape avant réécriture des tests
Étendre `backend/app/seed.py` (+ `seed_enhanced.py`) pour générer **un compte par ligne** de la matrice §3, toutes relations câblées :
- Formel : STD CP, STD 3e primaire ; TCH (CP+primaire) ; PAR (1 enfant) ; DIR/ADM.
- Informel : STD crèche (micro-groupe), STD msid (micro-groupe) — **vrais comptes** (D1), liés à PAR + EDUCATOR ; PAR informel ; EDUCATOR.
- Plateforme : SUP, CONTENT_MGR.
- Contenu : bibliothèque CMS **par niveau** (CP, primaire, …) + quelques **contenus privés** d'enseignant par classe + **affectations** classe↔contenu, pour que chaque élève voie un sous-ensemble **différent** et démontre la portée D3.
- Mots de passe de démo documentés, données réalistes marocaines (pas de « John Doe »).

## 7. Exécution & vérification (ordre)
```bash
# 0) pré-requis : renseigner .env (POSTGRES_*, REDIS_PASSWORD, MINIO_*, JWT_SECRET…)
cd <repo>
make up                 # démarre postgres/redis/minio/backend/worker/web (infra/docker-compose.dev.yml)
make migrate            # migrations Alembic
make seed               # python -m app.seed + seed_friend_content  (lance le nouveau seed personas)

# Vérifs ciblées
cd web && npm run i18n:check && npm run typecheck && npm run lint && npm run build
cd ../backend && pytest -q tests/security tests/edge   # + nouveaux tests de portée contenu
cd ../mobile && flutter analyze && flutter test
```
- Critères d'acceptation : voir `PRODUCT_QUALITY_PASS.md` §6 (par persona : STD ne voit que sa classe même par appel API ; TCH ne voit que ses niveaux ; PAR que ses enfants ; mêmes modules web/mobile par rôle ; identité visuelle cohérente ; pas de doublon de nav ; permissions masquées hors SUP/ADM ; en/ar alignés).

## 8. Docker
Aucune modif requise (cf. §9). Vérifier seulement `.env`. Pour staging/prod : `make staging-up` / `make prod-up`. Build images : `make build` / `make build-prod`.
