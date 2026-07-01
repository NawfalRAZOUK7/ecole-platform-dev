# Ecole Platform — Audit & Plan de correction (Micro-École, 2FA/SMS/TOTP/QR, UI/UX par Rôle & Âge)

> Audit basé sur la lecture du code réel (`ecole-platform-dev/`) le 2026-06-05.
> Source de vérité : le code. Chaque constat ci-dessous cite le fichier concerné.
> Légende statut : ✅ complet · 🟡 partiel · 🔴 manquant / cassé

---

## 0. Tableau de synthèse

| Domaine | Backend | Web | Mobile | Verdict | Priorité |
|---|---|---|---|---|---|
| Micro-École (modèle + API) | ✅ | 🟡 | 🟡 | Domaine complet côté API, UI plate (listes) | P2 |
| 2FA TOTP | ✅ | ✅ | 🟡 | Web OK, mobile sans vrai QR | P1 |
| QR Code (provisioning) | — | 🔴 | 🔴 | Web = fuite secret vers Google + endpoint déprécié ; Mobile = pas de QR | **P0** |
| SMS 2FA (Twilio) | ✅ | 🔴 | 🔴 | Backend complet, **aucune UI** | P1 |
| Codes de secours (backup) | ✅ | 🟡 | 🟡 | Affichés 1 fois, pas de copie / pas de garde "j'ai sauvegardé" | P2 |
| Cohérence UI par rôle | ✅ | 🟡 | 🔴 | **EDUCATOR absent du redirect web et du mobile** | **P0** |
| Thème par Âge & Niveau | — | ✅ | 🔴 | Web seulement (STD, via DOB), rien en mobile | P2 |
| Accessibilité (WCAG AA) | — | 🟡 | 🟡 | Palette kids à auditer (contraste / cibles tactiles) | P2 |

**Les deux P0 à traiter en premier :** (1) le QR code 2FA, et (2) le rôle EDUCATOR non câblé dans les frontends. Ce sont aussi les deux points les plus exposés en soutenance.

---

## 1. Micro-École

### État réel
- **Modèle complet** : `backend/app/models/micro_school.py` — `MicroSchool → MicroGroup → MicroEnrollment`, plus `MicroPayment` (weekly/monthly, MAD/EUR/USD), `MicroProgressLog` (note + `photo_url` + `milestone_tag`), `MicroResource` (activity_sheet/song/game/lesson_plan, arabe par défaut).
- **Service / API / events / tests** : `services/school/micro_school_service.py` (Micro{School,Group,Payment,Progress}Service), `api/v1/school/micro_school.py`, `domain/events/micro_school.py`, tests unit + integration + edge + **RBAC sécurité**.
- **Propriétaire = EDUCATOR** (`educator_id` FK), pas une école formelle. Les enfants ne sont **pas** des comptes `User`/`STD` : juste `child_name` + `date_of_birth` + `parent_id` dans `MicroEnrollment`.
- **Web** : `features/school/micro-schools/ui/` → `MicroSchoolListPage`, `MicroSchoolDetailPage`, `MicroSchoolEnrollPage`.
- **Mobile** : `features/school/micro_schools/` → list / detail / enroll + provider.

### Problèmes
1. L'UI est une suite de **listes plates** — elle ne valorise pas la richesse du modèle (photos de progression, jalons, paiements hebdo).
2. Le `MicroProgressLog` (note + photo + jalon, daté) est **le contenu le plus émotionnellement fort** pour des parents de garderie/kuttab, et il est noyé dans une page de détail.

### Suggestions
- **Transformer le journal de progression en "fil d'activité" (feed) parent** sur mobile : timeline chronologique, photo en grand, tag de jalon en pastille (« A appris la lettre ج », « Première comptine »). C'est démo-friendly et différenciant.
- **Tableau de bord éducateur** : une vue unique (1 personne / 1 cohorte) avec : présents du jour, paiements en retard (`MicroPaymentStatus.OVERDUE`), bouton « + Ajouter une observation ».
- **Carte enfant** réutilisable (avatar/initiale, âge calculé depuis `date_of_birth`, statut d'inscription) au lieu de lignes de tableau.
- Réutiliser les `MicroResource` (chansons, jeux, fiches) comme **bibliothèque filtrable par âge et langue** (le modèle a déjà `age_group` + `language`).

---

## 2. 2FA — TOTP

### État réel
- **Backend complet** : `core/totp.py` (génération secret, URI de provisioning, vérif code, **10 codes de secours** hashés bcrypt). Endpoints `auth/auth.py` : `/2fa/setup`, `/2fa/verify-setup`, `/2fa/disable`, et public `/2fa/verify` (flux temp-token quand login renvoie `requires_2fa`).
- **Web** : `features/user/profile/ui/TwoFactorPage.tsx` (247 lignes) — flux idle → setup → verify → done → disable, i18n complet.
- **Mobile** : `features/user/profile/two_factor_setup_screen.dart` (448 lignes) — même flux.

### Problèmes
1. **Mobile n'affiche pas de vrai QR** : `two_factor_setup_screen.dart` lignes 200-216 = un *placeholder* (`Icons.qr_code_2` + l'URI de provisioning en texte à copier). L'utilisateur doit **saisir le secret à la main** → friction forte sur l'usage premier de la 2FA.
2. **Reset par rechargement** : côté web, `handleDisable` et l'étape « done » appellent `window.location.reload()` → rechargement complet, à la place d'une invalidation d'état/requête.
3. **Codes de secours** : téléchargement présent, mais pas de bouton **Copier** ni de garde « j'ai sauvegardé mes codes » avant de continuer (c'est là que les gens les perdent).

### Suggestions
- Voir §4 (QR) pour le rendu QR — c'est la correction centrale, web + mobile.
- Remplacer `window.location.reload()` par un reset d'état local + invalidation de la query d'auth (TanStack Query : `queryClient.invalidateQueries(['auth','me'])`).
- Écran codes de secours : ajouter **Copier**, **Télécharger**, **Imprimer**, + checkbox « J'ai sauvegardé ces codes » qui débloque le bouton Continuer. Proposer **Régénérer les codes** dans les paramètres.

---

## 3. SMS 2FA (Twilio)

### État réel
- **Backend complet** : `services/auth/sms_2fa.py` (`Sms2FAService`, OTP 6 chiffres via `secrets`, Twilio), endpoints `api/v1/auth/sms_2fa.py` (`/setup`, `/verify-setup`, `/disable`).
- **Web** : 🔴 **aucune UI** (`grep` SMS dans `features/user` + `features/auth` = vide).
- **Mobile** : 🔴 **aucune UI**.

### Problème
Fonctionnalité **backend-only** : impossible pour un utilisateur d'activer le SMS 2FA depuis l'app. Soit on l'expose, soit on l'assume comme « API-only / hors périmètre UI » dans le rapport (ne pas la présenter comme une feature utilisateur si l'UI n'existe pas).

### Suggestions
- **Unifier la 2FA dans une seule page « Sécurité »** avec un choix de méthode : `App d'authentification (TOTP)` ou `SMS`. Réutiliser le même squelette d'états (setup → verify → done).
- Champ téléphone + bouton « Envoyer le code », saisie OTP, renvoi avec compte à rebours (anti-spam, cohérent avec le rate-limit backend).
- Indiquer clairement le **fallback** : si TOTP indisponible → SMS ou code de secours. Bon point sécurité pour la soutenance.

---

## 4. QR Code — correction P0 (web + mobile)

### Le problème (confirmé dans le code)
- **Web** (`TwoFactorPage.tsx`) génère le QR via
  `https://chart.googleapis.com/chart?cht=qr&chs=200x200&chl=<provisioning_uri>`.
  - 🔴 **Fuite de sécurité** : l'URI de provisioning **contient le secret TOTP partagé**. On l'envoie à un tiers (Google). C'est exactement ce que la 2FA est censée protéger.
  - 🔴 **Fiabilité** : l'endpoint QR de Google Image Charts est **déprécié / arrêté** → l'`<img>` peut être cassé.
  - Aucune lib QR dans `web/package.json`.
- **Mobile** : pas de QR du tout (placeholder), pas de package QR dans `pubspec.yaml`.

### La correction : générer le QR **localement** (rien ne sort de l'appareil)

**Web** — `qrcode.react` :
```bash
cd web && npm i qrcode.react
```
```tsx
import { QRCodeSVG } from 'qrcode.react';
// remplace la balise <img src="https://chart.googleapis.com/...">
<QRCodeSVG value={provisioningUri} size={200} includeMargin level="M" />
```

**Mobile** — `qr_flutter` :
```yaml
# pubspec.yaml
dependencies:
  qr_flutter: ^4.1.0
```
```dart
import 'package:qr_flutter/qr_flutter.dart';
// remplace le placeholder Icons.qr_code_2
QrImageView(
  data: provisioningUri,
  version: QrVersions.auto,
  size: 200,
  backgroundColor: Colors.white,
);
```
> Gain : suppression de la fuite du secret **et** rendu fiable hors-ligne, sur les deux plateformes. Petit diff, fort impact sur le chapitre sécurité.

---

## 5. Cohérence UI par Rôle — correction P0

### Rôles backend (`models/iam.py` `RoleCode`)
`ADM` (admin école), `DIR` (directeur), `TCH` (enseignant), **`EDUCATOR` (micro-école / éducation informelle)**, `PAR` (parent), `STD` (élève), `SUP` (super-admin), `SYS`, `CONTENT_MGR`.

### Le problème (confirmé)
- **Web** : `app/roleRedirects.ts` mappe `PAR, STD, TCH, ADM, DIR, SUP, CONTENT_MGR` → **`EDUCATOR` est absent**. Or `App.tsx` fait `ROLE_REDIRECT[user?.role] || '/profile'` : un éducateur qui se connecte **atterrit sur `/profile`**, sans accueil ni navigation dédiée.
- `EDUCATOR` n'apparaît que dans le type TS (`shared/types/models.ts`), **nulle part dans le routing ni les gardes** `ProtectedRoute`.
- Les pages micro-école (`features/school/micro-schools`) ne sont pas explicitement réservées au rôle EDUCATOR.
- **Mobile** : `EDUCATOR` **n'apparaît nulle part** (`app/`, `features/school/` = vide). Les écrans micro-école existent mais le rôle n'est pas câblé.

→ Incohérence nette : **le backend a un rôle EDUCATOR de première classe + tout le domaine micro-école, mais les frontends ne lui donnent ni accueil, ni redirection, ni navigation.**

### Suggestions
1. **Web — ajouter EDUCATOR au redirect** :
   ```ts
   // app/roleRedirects.ts
   EDUCATOR: '/micro-schools',
   ```
2. **Web — garder les routes micro-école** :
   ```tsx
   <ProtectedRoute roles={['EDUCATOR', 'ADM', 'DIR']}> ... </ProtectedRoute>
   ```
3. **Navigation par rôle** : définir un `NAV_BY_ROLE` explicite pour que chaque rôle ait son set d'items (l'éducateur voit Micro-Écoles / Groupes / Paiements / Ressources ; pas Bulletins, Emplois du temps, etc.).
4. **Mobile** : ajouter EDUCATOR au routeur (`app/router/app_router.dart`) avec un onglet d'accueil = liste des micro-écoles, symétrique au web.
5. **Test de cohérence** : un petit test « chaque `RoleCode` a une entrée de redirection » empêche la régression (le trou EDUCATOR aurait été attrapé).

---

## 6. Thème par Âge & Niveau

### État réel
- **Web** : `shared/hooks/useAgeTheme.ts` calcule un *tier* depuis la `date_of_birth` → `maternelle (≤5)`, `primaire (6-9)`, `college (10+)`, posé en `data-age-tier` sur `<html>`. CSS dédié : `shared/styles/themes/{maternelle,primaire,college}.css` (tailles de police, rayons, icônes, mascotte). Appliqué pour le rôle **STD**.
- **Mobile** : 🔴 aucun équivalent de thème par âge trouvé.

### Problèmes / Suggestions
- **Parité mobile manquante** : porter `useAgeTheme` en Flutter (un `AgeTier` dérivé de la DOB qui sélectionne un `ThemeData` / des tokens — tailles, rayons, densité). Sans ça, l'argument « UI adaptée à l'âge » ne tient que sur le web.
- **Distinguer Âge vs Niveau** : aujourd'hui le tier vient de l'**âge** (DOB). Pour le scolaire marocain, prévoir aussi un axe **niveau** (maternelle / primaire / collège) issu de la classe inscrite, car âge ≠ niveau (redoublement, avance). Idéalement : `tier = niveau ?? ageTier(DOB)`.
- **Micro-École** : les enfants (2-6 ans) ne sont pas des `User`, donc n'ont pas de thème — mais les vues **éducateur/parent** de micro-école peuvent adopter le style `maternelle` par défaut (cohérence visuelle avec l'âge réel de la cohorte).
- **Fallback** : `useAgeTheme` retombe sur `primaire` si DOB absente — OK, mais le documenter.

---

## 7. Transverse — Accessibilité & cohérence

- **Contraste** : auditer la palette kids (primary `#7c3aed` violet sur fond crème `#fff7ed`) en WCAG AA — c'est précisément sur les UI petits-enfants que contraste élevé et **grandes cibles tactiles** comptent le plus.
- **Cibles tactiles** : viser ≥ 44×44 px (déjà partiellement couvert par `--kids-btn-padding`), à vérifier sur les icônes de navigation.
- **RTL / arabe** : le domaine micro-école est arabe-first (`المجموعة`, ressources `ar`). Vérifier RTL bout-en-bout + chiffres arabes là où pertinent (dates, montants MAD).
- **Système partagé** : bonne base (`EmptyState`, `Skeleton`, `OfflineIndicator`, `ConfirmDialog`, `ErrorBanner`, tokens web↔mobile en miroir). À valoriser tel quel dans le rapport.

---

## 8. Plan d'action priorisé

| # | Action | Fichiers | Effort | Priorité |
|---|---|---|---|---|
| 1 | QR local web (`qrcode.react`) — supprime la fuite du secret | `TwoFactorPage.tsx`, `web/package.json` | 30 min | **P0** |
| 2 | QR local mobile (`qr_flutter`) — remplace le placeholder | `two_factor_setup_screen.dart`, `pubspec.yaml` | 45 min | **P0** |
| 3 | Câbler EDUCATOR : redirect + gardes + nav (web) | `roleRedirects.ts`, `App.tsx` | 1 h | **P0** |
| 4 | Câbler EDUCATOR (mobile) | `app_router.dart` | 1 h 30 | P1 |
| 5 | UI SMS 2FA dans une page « Sécurité » unifiée | nouveau, web + mobile | 3 h | P1 |
| 6 | Codes de secours : copier + garde « sauvegardé » + régénérer | `TwoFactorPage.tsx`, screen mobile | 1 h | P2 |
| 7 | Remplacer `window.location.reload()` par invalidation de query | `TwoFactorPage.tsx` | 20 min | P2 |
| 8 | Feed de progression Micro-École (mobile) | `micro_school_detail_screen.dart` | 3 h | P2 |
| 9 | Thème par âge en mobile (parité web) | nouveau hook/thème Flutter | 2 h | P2 |
| 10 | Axe Niveau (en plus de l'âge) + test « chaque rôle a un redirect » | `useAgeTheme.ts`, test | 1 h 30 | P2 |
| 11 | Audit accessibilité WCAG AA palette kids | thèmes CSS | 1 h | P2 |

> Si tu ne fais que 3 choses : **#1, #2, #3** — ce sont les corrections à fort impact (sécurité + cohérence) et les plus visibles en démo/soutenance.

---

---

## 9. Journal d'implémentation (2026-06-05)

Corrections appliquées dans cette session :

**P0 — QR Code 2FA (web + mobile)** ✅
- Web : `TwoFactorPage.tsx` rend désormais `<QRCodeSVG>` localement (dép. `qrcode.react` ajoutée à `web/package.json`). Le secret TOTP ne quitte plus le navigateur — fin de la fuite vers `chart.googleapis.com`.
- Mobile : `two_factor_setup_screen.dart` rend un vrai `QrImageView` (dép. `qr_flutter` ajoutée à `pubspec.yaml`), capture du `provisioningUri` ajoutée ; le placeholder n'est plus qu'un fallback.

**P0 — Rôle EDUCATOR (web)** ✅
- `roleRedirects.ts` : `EDUCATOR → /micro-schools`.
- `App.tsx` : `EDUCATOR` ajouté aux 3 gardes `ProtectedRoute` des routes micro-écoles.
- `Layout.tsx` : item de nav micro-écoles visible pour `EDUCATOR`.

**P1 — Rôle EDUCATOR (mobile)** ✅
- `app_router.dart` : redirection `EDUCATOR → /micro-schools`.
- `shell_screen.dart` : micro-écoles + notifications + profil visibles pour `EDUCATOR`, avec un set d'onglets primaires dédié.

**P1 — UI SMS 2FA (web + mobile)** ✅
- Web : `SmsTwoFactorCard.tsx` (flux téléphone → OTP → vérif / désactivation), branché dans `TwoFactorPage`, hooks + API (`/auth/sms-2fa/*`), i18n fr/en/ar.
- Mobile : méthodes SMS ajoutées au `AuthRepository` (+ impl + fake), `SmsTwoFactorCard` ajouté à l'écran 2FA.

**P2 — Thème par Âge & Niveau (mobile)** ✅
- Nouveau `shared/ui/age_theme.dart` : `AgeTier`, résolution niveau→DOB→primaire, `applyAgeTier` (échelle typo, rayons, tailles de boutons, densité), widget `AgeThemedView`.
- `student_home_screen.dart` : `studentAgeTierProvider` (lit le profil) + wrap de l'écran dans `AgeThemedView`.

**P2 — Feed de progression Micro-École (mobile)** ✅
- Les `progress-logs` (note + photo + jalon + date) étaient récupérés puis jetés (agrégat factice `100%`). Ajout de l'entité `MicroProgressLogEntry`, parsing réel dans le repo, et refonte de `_ProgressTab` en **fil d'activité** (photo, puce de jalon, note, nom de l'enfant résolu via les inscriptions).

**P2 — Codes de secours + reload (web)** ✅
- `TwoFactorPage` : bouton **Copier**, case « j'ai enregistré mes codes » qui débloque Fermer.
- Ajout de `refreshUser()` à `AuthContext` ; tous les `window.location.reload()` des écrans 2FA (TOTP + SMS) remplacés par un rafraîchissement d'état propre.

**Étapes humaines requises** (filesystems séparés — à exécuter sur la machine) :
```bash
cd web && npm install        # installe qrcode.react
cd ../mobile && flutter pub get   # installe qr_flutter
```
Puis `flutter analyze` / build web pour valider la compilation.

**P2 — Axe Niveau côté web** ✅
- `useAgeTheme(dateOfBirth, niveau?)` : `niveauToTier` ajoute la résolution par `class_level` (niveau d'abord, puis DOB, puis primaire) — parité avec le mobile. Les 3 appelants (`Layout`, `StudentHomePage`, `WritingWorkspacePage`) passent désormais `class_level`.

**P2 — Audit WCAG AA palette kids** ✅
- Voir `docs/WCAG_AUDIT_KIDS.md`. Cœur de palette conforme ; 5 combinaisons en échec corrigées (valeurs stats XP/Étoiles/Série, dégradés CTA primaire + écriture) ; cible tactile `.nav-link` portée à ≥44px.

**Tous les items P0/P1/P2 de cet audit sont traités.** Restent seulement, hors périmètre : focus-visible clavier (audit séparé) et validation visuelle post-build.

---

_Audit généré le 2026-06-05 contre `ecole-platform-dev/`. Tous les constats sont traçables aux fichiers cités._
