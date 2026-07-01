# Analyse Design — Cohérence Web ↔ Mobile, Types d'école, Rôles, Âge & Niveau, UX

> Analyse basée sur la lecture du code réel (`ecole-platform-dev/`) le 2026-06-05.
> Sources : `web/src/shared/ui/tokens.ts`, `web/src/app/styles.css`,
> `web/src/shared/ui/kids-theme.css`, `web/src/shared/styles/themes/*`,
> `mobile/lib/shared/ui/tokens/*`, `mobile/lib/shared/ui/app_theme*.dart`,
> `Layout.tsx`, `shell_screen.dart`. Chaque constat cite un fichier.

---

## 1. Cohérence Web ↔ Mobile

### Fondations communes (bonne cohérence)
- **Police identique** : les deux utilisent **Cairo** (`app_theme.dart` `fontFamily: 'Cairo'` ; `styles.css` commente explicitement « matches mobile AppTypography with Cairo »). Échelle typo alignée (heading1 700/28, body 400/16…).
- **Échelle d'espacement identique** : `4 / 8 / 12 / 16 / 24 / 32 / 48` (`AppSpacing` ↔ `tokens.ts spacing`).
- **Rayons identiques** : `4 / 8 / 12 / 16 / 999` (`AppRadii` ↔ `tokens.ts radii`).
- **Mode sombre aligné** : `bg #0f172a`, `surface #1e293b`, `text #f1f5f9`, `border #334155` sur les deux.
- **Architecture symétrique** : 12 features de chaque côté (academic, admin, ai, auth, billing, communication, content, lms, reports, school, sync, user).
- **Bibliothèque de composants jumelle** : `EmptyState/Skeleton/StatCard/OfflineIndicator/ConfirmDialog` (web) ↔ `AppEmptyState/AppStatCard/…` (mobile).

### Divergences de couleurs (à corriger pour la cohérence)

| Token | Web (`tokens.ts`) | Mobile (`colors.dart`) | Écart |
|---|---|---|---|
| secondary | `#8b5cf6` | `#7C3AED` | violet différent |
| primaryLight | `#60a5fa` | `#93C5FD` | nuance différente |
| primaryDark | `#1d4ed8` | `#1E40AF` | nuance différente |
| success | `#10b981` (emerald) | `#4CAF50` (Material) | **vert différent** |
| warning | `#f59e0b` (amber) | `#FF9800` (Material) | **orange différent** |
| info | `#0ea5e9` | `#2196F3` (Material) | **bleu différent** |
| text | `#111827` | `#1F2937` | mobile plus clair |
| bg / surface | bg `#f9fafb`, surface `#ffffff` | background `#ffffff`, surface `#f9fafb` | **inversés** |

> Constat : `primary` (`#2563eb`) coïncide, mais les couleurs **sémantiques**
> (success/warning/info) suivent Material sur mobile et Tailwind sur web. Même
> intention, exécution divergente → un badge « succès » n'a pas la même teinte
> sur les deux plateformes. `bg`/`surface` sont littéralement inversés.

### Écarts structurels de thème

| Élément | Web | Mobile |
|---|---|---|
| Thème enfant (couleurs) | **Oui** — `data-theme='kids'` (violet/crème) appliqué au rôle STD (`Layout.tsx:292`) | **Non** — pas de thème couleur enfant sur le shell STD ; seulement `KidsContentColors` pour le lecteur d'histoire / mascotte Sami |
| Couleurs par matière | **Absentes** | **Présentes** — `subjectColors` (10 matières, clair + sombre) |
| Glassmorphism | `glassmorphism.css` (cartes givrées) | partiel (`BackdropFilter` sur quelques écrans) |
| Adaptation par âge | couleurs **+** tailles (kids + age tiers) | tailles seulement (`age_theme.dart`, ajout récent) |

---

## 2. Types d'école : formel / semi-formel / informel

**Réalité du code : il n'existe que DEUX catégories, pas trois.**

| Catégorie | Existe ? | Implémentation | Rôle propriétaire |
|---|---|---|---|
| **Formel** (école enregistrée) | ✅ | « school tenant » + domaine académique/LMS complet | ADM, DIR, TCH, PAR, STD |
| **Informel** (micro-école) | ✅ | `micro_school.py` — cohortes de quartier, arabe-first, paiements hebdo | EDUCATOR |
| **Semi-formel** | ❌ **inexistant** | aucun `school_type`/enum « semi-formal » dans le code | — |

> Important : **« semi-formel » n'existe nulle part dans le code** (recherche
> exhaustive : aucun enum, champ ou écran). Si le concept doit exister (ex.
> écoles privées non homologuées, soutien scolaire), il reste **à concevoir**.

**Traitement design actuel** : la micro-école (informel) **n'a pas d'identité
visuelle distincte** — elle réutilise le thème par défaut, seuls les écrans
diffèrent. Or sa population est préscolaire (2-6 ans) et arabe-first. **Reco** :
lui donner une identité plus chaleureuse/simple (réutiliser le style
`maternelle` + RTL renforcé), pour la différencier visuellement du formel.

---

## 3. Rôles : STD / TCH / PAR / ADM / DIR / CMS / EDUCATOR / SUP

**Rôles définis** (`models/iam.py RoleCode`) : `ADM, DIR, TCH, EDUCATOR, PAR,
STD, SUP, CONTENT_MGR (CMS)`, + `SYS`.

### Différenciation visuelle actuelle

| Mécanisme | Web | Mobile |
|---|---|---|
| Thème couleur par rôle | **binaire** : STD → thème « kids » ; tous les autres → light/dark standard | **aucun** : thème global unique pour tous |
| Navigation par rôle | ✅ `NAV_BY_ROLE` (items filtrés) | ✅ `shell_screen.dart` (onglets filtrés) |
| Page d'accueil par rôle | ✅ `ROLE_REDIRECT` | ✅ `_roleRedirects` |

### Redirections d'accueil (après correctifs récents)

| Rôle | Web | Mobile |
|---|---|---|
| PAR | `/feed` | `/family` |
| STD | `/student/home` | `/student/home` |
| TCH | `/teacher` | `/teacher/classes` |
| EDUCATOR | `/micro-schools` | `/micro-schools` |
| ADM / DIR | `/admin` | `/admin/dashboard` |
| SUP | `/notifications` | `/notifications` |
| CMS (CONTENT_MGR) | `/cms` | — (pas d'accueil mobile) |

> Constats :
> - La différenciation des rôles passe **par la navigation et la page
>   d'accueil**, **pas** par la couleur (sauf STD). Un TCH, un PAR et un ADM
>   voient strictement la même palette.
> - **ADM et DIR sont quasi identiques** (même accueil, même nav) — distinction
>   à clarifier (ou assumer).
> - **CMS** n'a pas de redirection mobile ; **SUP** n'a pas de nav mobile riche.
> - **Reco** : ajouter un **accent de rôle subtil** (puce/couleur d'en-tête par
>   rôle) pour l'orientation, sans fragmenter la palette globale.

---

## 4. Âge & Niveau (rôle STD)

| Aspect | Web | Mobile |
|---|---|---|
| Source du tier | `class_level` (niveau) puis `date_of_birth` (`useAgeTheme`, après ajout de l'axe niveau) | idem (`age_theme.dart resolveAgeTier`) |
| Tiers | maternelle (≤5 / PS·MS·GS), primaire (6-9 / CP·CE·CM), college (10+) | identiques |
| Ce qui change | **couleurs + tailles + mascotte** (`data-age-tier` + thème kids) | **tailles seulement** (typo, rayons, densité, boutons) |
| Portée | Layout + pages élève | écran d'accueil élève uniquement |

> Cohérence : la **logique de résolution** est désormais alignée (niveau→DOB→
> primaire). L'**effet visuel** ne l'est pas : web change la palette ET les
> tailles ; mobile ne change que les tailles, et seulement sur un écran.
> **Reco** : porter un mini-thème couleur enfant en Flutter et l'appliquer à
> tous les écrans élève (parité avec `data-theme='kids'`).

---

## 5. UX — points forts et frictions

### Points forts
- État hors-ligne explicite (`OfflineIndicator` web ; bandeau sync + compteur dans le shell mobile).
- États vides / squelettes de chargement systématiques des deux côtés.
- i18n complet **ar / fr / en** + RTL ; domaine micro-école arabe-first.
- Adaptation à l'âge (rare et différenciant).
- 2FA TOTP+SMS complet, QR local, feed de progression micro-école (corrigés récemment).

### Frictions
1. **L'élève ne peut pas utiliser le mode sombre sur web** : `data-theme='kids'` écrase `theme` (`Layout.tsx:292`). À régler (variante sombre du thème kids).
2. **Identité de rôle faible** : hors STD, aucune différenciation visuelle entre TCH/PAR/ADM/DIR/CMS.
3. **Couleurs par matière mobile-only** : un même cours n'a pas la même couleur sur web et mobile (web n'a pas de `subjectColors`).
4. **Palette de gamification divergente** : XP = bleu côté web vs barre verte (`xpBar #4CAF50`) côté mobile ; level badge `#7c3aed` (web) vs `#7C4DFF` (mobile).
5. **ADM ≈ DIR** : redondance fonctionnelle non résolue.

---

## 6. Recommandations priorisées

| # | Action | Impact | Effort |
|---|---|---|---|
| 1 | **Source de vérité unique des tokens** : aligner success/warning/info + dé-inverser bg/surface entre web et mobile (générer les deux depuis un même fichier) | Cohérence de marque | Moyen |
| 2 | **Porter le thème couleur « kids » en Flutter** et l'appliquer à tous les écrans STD (parité web) | Forte (cœur de cible) | Moyen |
| 3 | **Ajouter `subjectColors` au web** (reprendre la map mobile) | Reconnaissance des matières | Faible |
| 4 | **Identité visuelle micro-école** (informel) : style maternelle + RTL renforcé | Différenciation produit | Moyen |
| 5 | **Variante sombre du thème kids** pour débloquer le mode sombre élève | Confort / accessibilité | Faible |
| 6 | **Unifier la palette de gamification** (XP/level/streak) web↔mobile | Cohérence ludique | Faible |
| 7 | **Accent de rôle subtil** (en-tête coloré par rôle) pour TCH/PAR/ADM/DIR/CMS | Orientation utilisateur | Faible |
| 8 | **Clarifier ADM vs DIR** (permissions/nav distinctes) ou les fusionner | Clarté | Faible |
| 9 | Si pertinent : **concevoir le type « semi-formel »** (inexistant aujourd'hui) | Couverture marché | Élevé |

---

## 7. Réponses directes aux questions

- **Cohérence web/mobile ?** Forte sur les fondations (police Cairo, espacements, rayons, dark mode, architecture, composants) ; **divergente sur les couleurs sémantiques** (success/warning/info Material vs Tailwind), `bg`/`surface` inversés, et sur le thème enfant (couleurs côté web seulement).
- **Formel / semi-formel / informel ?** Seulement **formel** (école) et **informel** (micro-école) existent. **« Semi-formel » n'existe pas** dans le code. L'informel n'a pas d'identité visuelle propre aujourd'hui.
- **Rôles (STD/TCH/PAR/ADM/DIR/CMS…) ?** Différenciés par **navigation + accueil**, pas par couleur — **sauf STD** (thème kids sur web). ADM≈DIR. CMS/SUP incomplets sur mobile.
- **Âge & niveau (STD) ?** Logique alignée (niveau→âge→primaire) ; **web change couleurs+tailles, mobile seulement tailles** et sur un seul écran.
- **UX ?** Solide (offline, états vides, i18n/RTL, adaptation âge) ; frictions principales : élève sans mode sombre sur web, identité de rôle faible, couleurs matière/gamification non synchronisées.

_Analyse conduite contre le code réel ; constats traçables aux fichiers cités._
