# Audit accessibilité — thème "kids" (WCAG 2.1 AA)

> Réalisé le 2026-06-05 contre `web/src/shared/ui/kids-theme.css` + `tokens.ts`.
> Ratios calculés selon la formule de contraste WCAG. Seuils : **4.5:1** texte
> normal, **3:1** texte large (≥18px gras ou ≥24px) et composants d'interface.

## 1. Contraste — paires texte / fond

| Paire | Couleurs | Ratio | Seuil | Verdict |
|---|---|---|---|---|
| Texte principal sur fond crème | `#1f1035` / `#fff7ed` | 16.71:1 | 4.5 | ✅ |
| Texte secondaire sur fond crème | `#6d5a8a` / `#fff7ed` | 5.68:1 | 4.5 | ✅ |
| Texte secondaire sur surface | `#6d5a8a` / `#ffffff` | 6.03:1 | 4.5 | ✅ |
| Texte sur fond secondaire | `#1f1035` / `#fef3c7` | 15.93:1 | 4.5 | ✅ |
| Lien primaire sur fond crème | `#7c3aed` / `#fff7ed` | 5.37:1 | 4.5 | ✅ |
| Blanc sur primaire (boutons) | `#ffffff` / `#7c3aed` | 5.70:1 | 4.5 | ✅ |
| Blanc sur sidebar | `#ffffff` / `#5b21b6` | 8.98:1 | 4.5 | ✅ |
| Texte sidebar atténué | `~#c9b8e0` / `#5b21b6` | 4.88:1 | 4.5 | ✅ |

Le cœur de la palette (textes/fonds) **passe AA**.

## 2. Échecs détectés et corrigés

| Élément | Avant | Ratio | Après | Ratio | Statut |
|---|---|---|---|---|---|
| Valeur stat XP (sur blanc) | `#3b82f6` | 3.68:1 | `#2563eb` | 5.17:1 | ✅ corrigé |
| Valeur stat Étoiles | `#f59e0b` | 2.15:1 | `#b45309` | 5.02:1 | ✅ corrigé |
| Valeur stat Série (streak) | `#f97316` | 2.80:1 | `#c2410c` | 5.18:1 | ✅ corrigé |
| CTA primaire (fin du dégradé) | `#a78bfa` | 2.72:1 | `#8b5cf6` | 4.23:1 | ✅ corrigé |
| CTA écriture (dégradé vert) | `#10b981`→`#34d399` | 2.54 / 1.92 | `#047857`→`#059669` | 5.48 / 3.77 | ✅ corrigé |

Les valeurs de stats sont du **texte large** (≥3:1 requis) mais échouaient
même ce seuil ; elles passent désormais le seuil **texte normal** (4.5:1).
Les CTA portent des libellés larges (seuil 3:1) : les deux dégradés respectent
maintenant 3:1 **sur toute la surface du bouton**, y compris la teinte la plus
claire.

**Déjà conforme (pas de changement)** : le bouton CTA secondaire ambre
(`#f59e0b`→`#fcd34d`) utilise déjà du **texte foncé** `#7c2d12` — bon réflexe,
car l'ambre + blanc est un anti-pattern de contraste.

## 3. Cibles tactiles (WCAG 2.5.5)

| Élément | Avant | Après |
|---|---|---|
| `.nav-link` (sidebar kids) | `padding:10px 12px` ≈ 40px de haut | `min-height:44px` + `display:flex; align-items:center` |

Les boutons des tiers `maternelle`/`primaire` sont déjà généreux
(`--kids-btn-padding: 16px 28px`). Le seul point sous 44px était la navigation
latérale, désormais garantie à ≥44px.

## 4. Résiduel / à surveiller

- Vérifier le focus-visible clavier sur fond sombre de la sidebar (anneau de
  focus visible) — non couvert par cet audit de couleur.
- Re-tester après `npm install` + build : confirmer visuellement les nouveaux
  dégradés CTA sur écran réel.

_Audit conduit contre le code réel ; tous les ratios sont reproductibles._
