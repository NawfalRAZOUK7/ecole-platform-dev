# Passe qualité produit — décisions verrouillées + brief d'implémentation (pour Codex)

> Objectif : corriger les **patterns partagés** (seed, accès, design, nav, i18n), pas un onglet à la fois.
> Principe directeur : **la nav cachée n'est pas de la sécurité** — toute portée d'accès est imposée au **backend** ; l'UI ne fait que refléter. Une **matrice unique** alimente web + mobile + seed.

---

## 1. Décisions verrouillées

**D1 — Élèves informels = vrais comptes.**
Chaque apprenant informel (crèche, msid, kouttab) a un **compte de connexion**, rattaché à un **micro-groupe** (et non une classe formelle), avec relations **parent** + **éducateur**. Modèle unifié avec le formel : même écran « élève », mêmes règles d'accès et de design ; seule l'inscription diffère (classe formelle vs micro-groupe informel).

**D2 — Design : 3 identités par CONTEXTE d'école.**
1. **Plateforme** : `SUP`, `CONTENT_MGR` (CMS).
2. **École formelle** : tous ses rôles (`DIR`, `ADM`, `TCH`, `PAR`, `STD`) partagent une identité.
3. **École informelle / micro-école** : tous ses rôles (`EDUCATOR`, `PAR`, `STD`, `DIR/ADM` informel) partagent une autre identité.
L'**âge** de l'élève = **accent uniquement** (taille de police, icônes ludiques), jamais un thème séparé. **Web et mobile partagent les mêmes tokens** (un seul contrat de design). → Supprimer l'override `role === 'STD' → kids` ; piloter par `school_type`/`design_mode` + contexte plateforme.

**D3 — Accès au contenu (3 filtres, imposés backend).**
1. **Filtre niveau** : un enseignant ne voit, dans la bibliothèque CMS publique, **que les niveaux qu'il enseigne**.
2. **Sélection enseignant** : il choisit/approuve quel contenu public **afficher à quelle classe** (table d'affectation classe↔contenu).
3. **Vue élève/parent** : ne voient **que** le contenu affecté à **leur** classe + le contenu **privé** publié par l'enseignant pour cette classe.
Lecture/stream/progression d'un `content_item` doit vérifier **l'affectation** (inscription/relation), pas seulement `school_id` + âge.

**D4 — Parité web/mobile.**
Pour un rôle donné, web et mobile exposent **les mêmes modules**, dérivés de la matrice unique. Exceptions = **techniques uniquement** (authoring CMS lourd reste web). La présentation tactile peut différer, mais **aucun module retiré**.

---

## 2. Source de vérité unique — matrice d'accès

Créer un fichier de config partagé (idéalement généré/partagé entre web, mobile et tests) :

`rôle × type_école × plateforme → { modules visibles, route par défaut, permission backend requise, portée relationnelle, identité design, compte de démo }`

Rôles : `SUP, CONTENT_MGR, ADM, DIR, TCH, EDUCATOR, PAR, STD`.
Types : `platform, formal, informal`.
Pour chaque cellule, renseigner la **portée relationnelle** (ce que l'utilisateur a le droit de voir) :
- `STD formel` → uniquement SA classe (contenu affecté, ses notes, son assiduité).
- `STD informel` → uniquement SON micro-groupe.
- `PAR` → uniquement ses enfants liés (`parent_child_links` / `micro_enrollments`).
- `TCH` → ses classes affectées + contenu CMS de ses niveaux.
- `EDUCATOR` → son/ses micro-groupe(s).
- `DIR/ADM` → son établissement (cloisonné `school_id`).
- `SUP` → supervision plateforme ; `CONTENT_MGR` → CMS par niveau.

→ Web (`Layout.tsx`/`App.tsx`), mobile (`shell_screen.dart`/`app_router.dart`) et seed lisent CETTE matrice. Plus de listes de nav divergentes codées en dur.

---

## 3. Matrice de personas de démo (seed)

> **Codes de niveau — taxonomie marocaine (voir `EDUCATION_TAXONOMY.md`).** Les codes français ci-dessous sont **remplacés** par les codes officiels MEN et sont **à remapper** (tâche 13, remap seed) : `CP→1AEP`, `CE1→2AEP`, `CE2/« 3e primaire »→3AEP`, `CM1→4AEP`, `CM2→6AEP` ; préscolaire/**Crèche → `rawd`** (niveaux `PS/MS/GS`) ; **Msid → `MicroSchool.type = msid`** (matière `quranic` = TODO). Rappel des 4 axes : *cycle* (stage) ≠ *niveau* (grade) ≠ *matière* (subject) ≠ *type de prestataire informel* (`MicroSchoolType`).

Un compte par ligne, avec toutes les relations câblées, pour démontrer **formel vs informel × rôle × niveau × accès × contenu** :

| École | Rôle | Niveau / groupe | Relations | À démontrer |
|---|---|---|---|---|
| Formelle | STD | CP | classe CP, parent, prof CP | voit seulement contenu affecté CP |
| Formelle | STD | 3e primaire | classe, parent, prof | contenu d'un autre niveau |
| Informelle | STD | Crèche (micro-groupe) | parent, éducateur | écran élève informel + design informel |
| Informelle | STD | Msid (micro-groupe) | parent, éducateur | apprenant informel plus âgé |
| Formelle | TCH | CP + primaire | classes affectées | ne voit que CMS CP/primaire ; affecte à sa classe |
| Informelle | EDUCATOR | micro-groupe | apprenants liés | gestion micro-groupe |
| Formelle | PAR | — | 1 enfant formel | ne voit que son enfant |
| Informelle | PAR | — | 1 enfant informel | ne voit que son enfant informel |
| Formelle | DIR/ADM | — | établissement | pilotage cloisonné |
| Plateforme | SUP | — | — | supervision |
| Plateforme | CONTENT_MGR | — | — | CMS par niveau |

Contenu seedé : bibliothèque CMS **par niveau** (CP, primaire, …) + quelques **contenus privés** d'enseignant par classe + **affectations** classe↔contenu, pour que chaque élève de démo voie un sous-ensemble **différent**.

---

## 4. Corrections par CAUSE (pas par symptôme) — avec ancrages Codex

1. **Backend — autorisation contenu (priorité 1).**
   - `content_service.get_content_item` / stream / progress : ajouter le contrôle d'**affectation** (classe/micro-groupe de l'utilisateur), pas seulement `school_id`+publié. (`app/services/lms/_helpers.py:213`)
   - `/content-items` : scoper par affectation de classe, pas tout le contenu école+âge. (`app/api/v1/lms/content.py:52`, `content_service.py:46`, `repositories/lms.py:489`)
   - `list_class_content` : valider inscription/relation enseignant↔classe avant de renvoyer. (`content_service.py:696`, `repositories/lms.py:761`)
   - Mobile `student_content_screen.dart:54` doit appeler l'endpoint scopé classe.

2. **Web — état actif de nav (bug « Soumissions sélectionne Mes classes »).**
   - Cause : route parente `/teacher` + `NavLink` sans `end`. Activer le **matching exact** pour les routes parentes. (`Layout.tsx:126`, `:558`)

3. **Web — doublon bibliothèque enseignant.**
   - Retirer l'entrée générique `/content` pour `TCH` (garder `/teacher/content-library`) ET restreindre la route `/content` côté `App.tsx:934`. → dédoublonner **depuis la matrice** pour couvrir tous les cas similaires.

4. **Profil — permissions brutes exposées.**
   - Masquer la liste des permissions sauf `SUP`/admin (mode debug). (`web ProfileInfo.tsx:28`, `mobile profile_screen.dart:254`)

5. **Design — résolveur unique.**
   - Supprimer l'override `STD→kids`. Piloter par contexte (plateforme / formel / informel) + accent d'âge. Aligner `web designContext.ts:38` et `mobile design_context.dart` + `shell_screen.dart:521` sur **le même contrat de tokens**.

6. **Mobile — gardes de rôle + parité.**
   - Ajouter des **métadonnées de rôle** par route (`app_router.dart`) et dériver la nav de la matrice (corrige `CONTENT_MGR` absent, `SUP` mal redirigé, divergences TCH/STD/DIR).

7. **i18n.**
   - Compléter `en`/`ar` (229 clés manquantes vs `fr`) + **garde CI** qui échoue si une langue manque une clé de `fr`. Localiser les ~340 chaînes en dur restantes du mobile. (`web i18n/index.ts:65`)

---

## 5. Ordre d'exécution

1. Figer la **matrice d'accès** + la **matrice de personas** (sections 2 et 3) — source de vérité.
2. **Backend** : portée par affectation/relation (contenu d'abord), gardes de route mobile.
3. **Web + mobile** : dériver nav/routes de la matrice → supprime doublons + divergences + bug d'état actif.
4. **Design** : résolveur unique (3 identités + accent d'âge), tokens partagés web/mobile.
5. **Seed** : générer tous les personas + contenu CMS par niveau + affectations.
6. **Profil** : masquer permissions.
7. **i18n** : compléter + garde CI.

---

## 6. Critères d'acceptation (à tester par persona)

- Élève CP ne voit **aucun** contenu non affecté à sa classe (ni d'un autre niveau, ni d'une autre classe), vérifié **même via appel API direct** (pas seulement nav cachée).
- Enseignant CP+primaire ne voit dans le CMS **que** CP/primaire.
- Parent ne voit **que** ses enfants liés (formel et informel).
- Même rôle → **mêmes modules** sur web et mobile.
- Un compte d'une école formelle a la **même identité visuelle** sur web et mobile ; un compte informel a l'identité informelle ; SUP/CMS la plateforme.
- Aucune entrée de nav dupliquée pour aucun rôle.
- `SUP` (et rôles non-admin) ne voient pas la liste brute des permissions.
- `en`/`ar` : zéro clé manquante ; la garde CI échoue si on en retire une.

---

## 7. Avancement implémentation (passe Cowork) — fait vs reste

**Déjà appliqué (à exécuter/tester par Codex) :**
- Web nav : `NavLink end` (état actif exact) + `/content` retiré pour TCH (nav + route `App.tsx`). (`Layout.tsx`)
- Profil : permissions brutes masquées sauf `SUP`/`ADM` (web `ProfileInfo.tsx` + mobile `profile_screen.dart`).
- Design : résolveur unique web (`designContext.ts` : `isPlatform`, `ageAccent`, suppression override `STD→kids`) + attributs DOM (`Layout.tsx`) ; mobile (`shell_screen.dart`) — l'élève hérite du thème école + accent d'âge.
- Backend scoping (cœur, anti-IDOR) :
  - `LMSServiceBase._user_class_ids(auth)` + `_content_assigned_to_user(...)` (compose `DocumentsRepository` + `find_class_content_assignment`).
  - `get_content_item` : STD/PAR → 404 si le contenu n'est pas affecté à une de leurs classes. (`_helpers.py`)
  - `list_class_content` : TCH/STD/PAR → 404 si la classe demandée n'est pas une des leurs. (`content_service.py`)

**Reste backend (à faire par Codex, nécessite requêtes repo + tests) :**
- `list_content_items` (bibliothèque générique) : pour STD/PAR, filtrer **au niveau requête** sur les `content_item_id` affectés à leurs classes (ajouter un param d'allowlist au repo `list_content_items` pour préserver la pagination ; ne pas post-filtrer). Pour TCH : filtrer la bibliothèque CMS sur **les niveaux enseignés** (filtre `level_band` ∈ niveaux du prof).
- `stream` / `progress` / `complete` d'un `content_item` : appliquer la même garde d'affectation que `get_content_item` (réutiliser `_content_assigned_to_user`).
- Mobile : `student_content_screen.dart` doit appeler l'endpoint **scopé classe** plutôt que `/content-items`.
- Tests de sécurité : un STD/PAR ne peut pas lire un `content_item` non affecté **même par appel API direct avec un id valide** (404).

**Nav — appliqué (passe Cowork) :**
- Garde-fou **anti-doublon par route et par rôle** sur les DEUX clients : web (`Layout.tsx` `visibleItems`) et mobile (`shell_screen.dart` `visibleItems`) — corrige le pattern, pas un onglet.
- Mobile : `SUP` et `CONTENT_MGR` redirigés vers `/profile` (SUP n'a pas la lecture des notifications ; CMS web-only) — `app_router.dart` `_roleRedirects` + `shell_screen.dart` `_primaryRoutesByRole`.

**Nav — reste (Codex) :**
- Mobile : ajouter des **métadonnées de rôle par `GoRoute`** (défense en profondeur ; aujourd'hui routes auth-guardées seulement, la sécurité réelle est au backend).
- Web : nettoyer les rôles `STD` morts dans `NAV_ITEMS` (les élèves utilisent `KIDS_NAV_ITEMS`), pour que les listes de rôles soient honnêtes.
- Parité fine web/mobile par rôle à partir de la matrice §2 (ajouter les modules manquants là où l'écran existe).

**i18n web — FAIT (passe Cowork) :**
- 229 clés manquantes `en` + `ar` traduites (EN + arabe MSA) via `web/scripts/i18n-fill.mjs` (exécuté : en=2433, ar=2453, garde verte). Arabe à faire relire par un natif.
- Garde CI `web/scripts/i18n-check.mjs` + `npm run i18n:check` (tolère les catégories de pluriel ICU `_zero/_two/_few/_many`).
- Backend list_content_items/stream/progress/complete/asset : portée par affectation appliquée (cf. ci-dessus). Le client mobile `/content-items` reçoit désormais des données déjà scopées côté serveur (pas de changement client requis pour la sécurité).

**Reste majeur (données / traduction / Flutter — nécessite exécution, donc Codex) :**
- Mobile i18n : ~340 chaînes en dur restantes à externaliser vers les ARB/locales Flutter (gros volume Flutter).
- Mobile : métadonnées de rôle par `GoRoute` (défense en profondeur ; backend déjà garant).
- Web : nettoyage cosmétique des rôles `STD` morts dans `NAV_ITEMS` (volontairement non fait — risque de retirer un accès voulu ; le garde-fou anti-doublon neutralise déjà l'effet).

---

## 8. Revue de nav par rôle — décisions + état

**Appliqué (passe Cowork) :**
- `/reports` = fonction staff → retiré de STD/PAR (web nav + route, mobile nav) ; staff = TCH/ADM/DIR.
- `/micro-schools` → **gaté par type d'école** (informel, ou SUP supervision) sur web et mobile — un parent d'école formelle ne le voit plus.
- Garde-fou anti-doublon par route et par rôle (web + mobile) ; redirections SUP/CONTENT_MGR → /profile.

**À implémenter par Codex (depuis la matrice §2, nécessite app lancée pour vérifier l'existence des écrans par route) :**
- **Parité web↔mobile par rôle** (D4). Cibles :
  - STD : accueil, contenu, quiz, jeux, écriture, passeport (skills), résultats, progression, récompenses, calendrier, annonces, notifications, profil.
  - TCH : classes, cours, devoirs, soumissions, assiduité, évaluations, quiz, contenu, rubrics, banque de questions, progression de classe + messagerie/calendrier/annonces/notifications/profil.
  - PAR : famille, résultats, progression enfant, messagerie, calendrier, annonces, fil, factures, contenu (scopé), notifications, profil.
  - EDUCATOR (informel) : micro-école(s), contenu, messagerie, calendrier, progression du groupe, notifications, profil.
- **DIR vs ADM** : DIR = tableaux de bord, analytics, budgets, rapports, conformité (oversight). ADM = utilisateurs, invitations, frais, fonctionnalités, paramètres (opérationnel). Retirer de la nav DIR (mobile) les items ADM-only : `/admin/invitations`, `/admin/features`, `/admin/school`.
- Cohérence `/reports` : web pointe `ReportsPage` (génération), mobile pointe `compliance_report_screen` — **même route, écrans différents** : à réconcilier (route distincte ou écran commun).
- Consolider `/results` (notes) vs `/progress` (compétences/avancement) — noms et périmètres clairs, pas de chevauchement.

## 9. Revue Docker — conclusion

Aucune modification Docker requise pour le seed : `infra/docker-compose.dev.yml` fournit déjà `postgres`/`redis`/`minio`/`worker`, le `backend` a `DATABASE_URL`/`REDIS_URL`/`UPLOAD_DIR` et le volume `../backend/uploads:/app/uploads`. Le seed s'exécute via `make seed` (`migrate` + `python -m app.seed` + `scripts.seed_friend_content`). Vérifier seulement que `.env` (POSTGRES_*, REDIS_PASSWORD, MINIO_*) est renseigné avant `make up && make seed`.
- **Seed** (§3) : générer la matrice de personas + contenu CMS par niveau + affectations. Gros volume dans `seed.py`/`seed_enhanced.py`, à valider en lançant le seed.
- **i18n** (§6 corrections) : compléter ~229 clés `en`/`ar` (vraie traduction, pas un repli FR) + script de **garde CI** qui échoue si une langue perd une clé de `fr` ; localiser les ~340 chaînes en dur restantes du mobile.
