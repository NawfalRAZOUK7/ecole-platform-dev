# 🔗 Stratégie Cross-Platform

## Philosophie

École Platform adopte une stratégie cross-platform basée sur deux principes fondamentaux :

### 1. Priorisation par rôle

| Rôle | Plateforme principale | Justification |
|------|----------------------|---------------|
| **Élève** (STD) | 📱 Mobile | Interaction tactile naturelle, jeux éducatifs, engagement quotidien, notifications push |
| **Parent** (PAR) | 📱 Mobile | Consultation rapide du suivi, notifications en temps réel, paiements |
| **Enseignant** (TCH) | 💻 Web | Saisie de données complexe (notes, contenu), tableaux de bord, multitâche |
| **Admin** (ADM) | 💻 Web | Gestion avancée, audit, configuration, rapports détaillés |
| **Directeur** (DIR) | 💻 Web | Analytics, rapports, vue d'ensemble pédagogique |

### 2. Transparence via Bridge Cards

Quand une fonctionnalité existe sur une plateforme mais pas l'autre, au lieu de la masquer, on **informe l'utilisateur** avec un composant visuel attractif qui explique pourquoi et où trouver la fonctionnalité.

---

## PlatformBridgeCard

### Concept

Le composant `PlatformBridgeCard` est un élément UI réutilisable qui :
- Affiche un **badge de plateforme** ("متوفر على التطبيق" / "متوفر على الويب")
- Montre un **titre** et une **description** contextuels
- Utilise des **couleurs adaptées** : violet pour mobile, bleu pour web
- Supporte le **RTL** (arabe) par défaut

### Implémentation React (Web)

```tsx
// web/src/shared/ui/PlatformBridgeCard.tsx
<PlatformBridgeCard
  targetPlatform="mobile"
  title="تلوين تفاعلي"
  description="هذا النشاط مصمم للأجهزة اللوحية — استخدم التطبيق لتجربة تلوين تفاعلية بلمسة إصبعك."
  icon="🎨"
/>
```

Props :
- `targetPlatform` : `'web'` | `'mobile'` — vers quelle plateforme rediriger
- `title` : titre de la fonctionnalité
- `description` : explication de pourquoi c'est sur l'autre plateforme
- `icon` : (optionnel) emoji ou icône personnalisée

### Implémentation Flutter (Mobile)

```dart
// mobile/lib/shared/widgets/platform_bridge_card.dart
const PlatformBridgeCard(
  targetPlatform: BridgePlatform.web,
  title: 'أدوات الإدارة المتقدمة',
  description: 'التسجيل الجماعي، سجل التدقيق، إدارة الشارات متوفرة على المنصة عبر الحاسوب.',
  icon: Icons.admin_panel_settings_rounded,
  textDirection: TextDirection.rtl,
)
```

Props :
- `targetPlatform` : `BridgePlatform.web` | `BridgePlatform.mobile`
- `title` : titre
- `description` : explication
- `icon` : (optionnel) `IconData` Flutter
- `textDirection` : (optionnel) `TextDirection.rtl` pour forcer le RTL

---

## Cas d'utilisation déployés

### Web → Mobile (fonctionnalité disponible sur mobile)

| Page web | Message | Raison |
|----------|---------|--------|
| Coloring Viewer | "تلوين تفاعلي — استخدم التطبيق لتجربة تلوين تفاعلية بلمسة إصبعك" | Le coloriage tactile est naturel sur tablette |

### Mobile → Web (fonctionnalité disponible sur web)

| Écran mobile | Message | Raison |
|-------------|---------|--------|
| Content Library (Enseignant) | "إنشاء المحتوى والاختبارات — استخدم المنصة على الحاسوب لتجربة أفضل" | Création de contenu complexe = web |
| Admin Dashboard | "أدوات الإدارة المتقدمة — التسجيل الجماعي، سجل التدقيق متوفرة على الحاسوب" | Gestion avancée = web |

---

## Design

### Couleurs

| Plateforme cible | Couleur accent | Variable CSS/Dart |
|-----------------|----------------|-------------------|
| Mobile | `#7C3AED` (violet) | `--color-secondary` / `AppColors.secondary` |
| Web | `#2563EB` (bleu) | `--color-primary` / `AppColors.primary` |

### Rendu visuel

```
┌────────────────────────────────────────────────┐
│  ┌──────┐                                      │
│  │  📱  │  ┌ متوفر على التطبيق ┐               │
│  │      │  │                    │               │
│  └──────┘  │ تلوين تفاعلي       │               │
│            │ هذا النشاط مصمم      │               │
│            │ للأجهزة اللوحية...   │               │
│            └────────────────────┘               │
└────────────────────────────────────────────────┘
```

Le composant utilise `color-mix()` en CSS (web) et `Color.withOpacity()` en Flutter pour créer des nuances subtiles du fond et de la bordure.

---

## Tests

Le composant PlatformBridgeCard est testé sur le web avec 6 tests unitaires :

1. Rendu mobile avec titre, description et icône par défaut (📱)
2. Rendu web avec icône par défaut (💻)
3. Icône personnalisée remplace l'icône par défaut
4. Direction RTL appliquée sur le conteneur
5. Badge plateforme correct pour mobile ("متوفر على التطبيق")
6. Badge plateforme correct pour web ("متوفر على الويب")

---

## Phase E — Parité visuelle web ⇄ mobile (v1.1)

La phase E établit une parité visuelle complète entre web et mobile sur les écrans destinés aux jeunes élèves. Les 10 sous-tâches ont été livrées en mai 2026.

### E1 — Filtrage par âge automatique

Le mapping `level → age_range` (centralisé dans `app/core/level_age_mapping.py` côté backend, et `level_age.dart` côté mobile, `levelAge.ts` côté web) filtre automatiquement les contenus présentés à un élève selon sa tranche d'âge inférée du niveau scolaire.

### E2 — Suivi du record de série

Le champ `student_rewards.longest_streak` (migration G53) conserve le record historique. Affichage dans `LongestStreakBadge` (web) et `LongestStreakWidget` (mobile).

### E4 — Police Cairo sur le web

La police arabe Cairo (déjà utilisée sur mobile) est intégrée au web. Bascule automatique sur la locale `ar` via la classe CSS `.font-arabic` injectée par `i18n.ts`.

### E5 — Système de couleurs kid-friendly sur le web

Réplication du `KidsContentColors` mobile en CSS variables web :

| Token | Web | Mobile |
|-------|-----|--------|
| `--color-kids-primary` | `KidsContentColors.primary` | `#FF6B6B` |
| `--color-kids-accent` | `KidsContentColors.accent` | `#4ECDC4` |
| `--color-kids-warning` | `KidsContentColors.warning` | `#FFE66D` |
| `--color-kids-success` | `KidsContentColors.success` | `#95E1D3` |

### E6 — Squelettes shimmer

Composants `<ShimmerSkeleton />` (web) et `ShimmerSkeleton` widget (mobile) avec animation 1.5s, utilisés sur tous les écrans kid-facing pendant le chargement.

### E7 — Splash branding mobile

Splash natif Android (`android/app/src/main/res/drawable/launch_background.xml`) et iOS (`ios/Runner/Base.lproj/LaunchScreen.storyboard`) avec logo et fond `#FF6B6B`.

### E8 — Design tokens partagés

`design-tokens/tokens.json` est consommé par :
- Web : généré en CSS variables via `style-dictionary` au build
- Mobile : généré en `app_colors.dart` / `app_spacing.dart` au build

Garantit une parité de couleurs, espacements et rayons de bordure entre les deux plateformes.

### E9 — Empty states avec mascotte

Composants `<KidEmptyState />` et `KidEmptyState` widget partagent une mascotte SVG (Sami) et un message localisé. Variantes : `noContent`, `noResults`, `error`, `comingSoon`.

### E10 — Cache hors-ligne du contenu (mobile)

L'application mobile télécharge à la demande les contenus pédagogiques (PDF, vidéos, images) dans un cache local (`flutter_cache_manager`) avec :
- TTL de **7 jours** pour le contenu téléchargé
- TTL de **15 minutes** pour les métadonnées de la bibliothèque
- Indicateur visuel `OfflineAvailableBadge` sur les contenus disponibles hors-ligne
- Purge automatique selon LRU si dépassement du quota (200 MB par défaut)

---

## Sync v2 (v1.1)

L'infrastructure de synchronisation mobile a été enrichie :

- **Indicateur shell** : un `SyncStatusBar` s'affiche en bas de l'app quand des opérations sont en attente
- **États** : `idle`, `syncing`, `paused`, `conflict`, `error`
- **Résolution de conflits** : UI dédiée pour les conflits de modifications concurrentes
- **Reprise automatique** : retry exponentiel sur les échecs réseau, déclenché à la reconnexion
