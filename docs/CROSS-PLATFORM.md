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
