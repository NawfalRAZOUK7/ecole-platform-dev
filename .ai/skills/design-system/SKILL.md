---
name: design-system-tokens
description: Token architecture, component specifications, and slide generation. Three-layer tokens (primitive→semantic→component), CSS variables, spacing/typography scales, component specs, strategic slide creation. Use for design tokens, systematic design, brand-compliant presentations. Complements the project's existing design-tokens/ folder.
argument-hint: "[component or token]"
license: MIT
metadata:
  author: claudekit
  version: "1.0.0"
---

> **Vendored note (Ecole Platform):** named `design-system-tokens` to avoid clashing with the
> Cowork `design:design-system` plugin skill. Run `.ai/skills/fetch-skill-assets.sh` once to
> pull references/, scripts/, data/ and templates/ from upstream. The repo already has a
> `design-tokens/` folder — audit it against the three-layer structure before generating new tokens.

# Design System

Token architecture, component specifications, systematic design, slide generation.

## When to Use

- Design token creation
- Component state definitions
- CSS variable systems
- Spacing/typography scales
- Design-to-code handoff
- Tailwind theme configuration
- Slide/presentation generation

## Token Architecture

Load: `references/token-architecture.md`

### Three-Layer Structure

```
Primitive (raw values)
       ↓
Semantic (purpose aliases)
       ↓
Component (component-specific)
```

**Example:**
```css
/* Primitive */
--color-blue-600: #2563EB;

/* Semantic */
--color-primary: var(--color-blue-600);

/* Component */
--button-bg: var(--color-primary);
```

## Quick Start

```bash
# Generate tokens
node scripts/generate-tokens.cjs --config tokens.json -o tokens.css

# Validate usage (finds hardcoded values)
node scripts/validate-tokens.cjs --dir src/
```

## References

| Topic | File |
|-------|------|
| Token Architecture | `references/token-architecture.md` |
| Primitive Tokens | `references/primitive-tokens.md` |
| Semantic Tokens | `references/semantic-tokens.md` |
| Component Tokens | `references/component-tokens.md` |
| Component Specs | `references/component-specs.md` |
| States & Variants | `references/states-and-variants.md` |
| Tailwind Integration | `references/tailwind-integration.md` |

## Component Spec Pattern

| Property | Default | Hover | Active | Disabled |
|----------|---------|-------|--------|----------|
| Background | primary | primary-dark | primary-darker | muted |
| Text | white | white | white | muted-fg |
| Border | none | none | none | muted-border |
| Shadow | sm | md | none | none |

## Scripts

| Script | Purpose |
|--------|---------|
| `generate-tokens.cjs` | Generate CSS from JSON token config |
| `validate-tokens.cjs` | Check for hardcoded values in code |
| `search-slides.py` | BM25 search + contextual slide recommendations |
| `slide-token-validator.py` | Validate slide HTML for token compliance |
| `fetch-background.py` | Fetch images from Pexels/Unsplash |

## Slide System

Brand-compliant presentations using design tokens + Chart.js + contextual decision system.

### Decision System CSVs (data/)

| File | Purpose |
|------|---------|
| `slide-strategies.csv` | 15 deck structures + emotion arcs + sparkline beats |
| `slide-layouts.csv` | 25 layouts + component variants + animations |
| `slide-layout-logic.csv` | Goal → Layout + break_pattern flag |
| `slide-typography.csv` | Content type → Typography scale |
| `slide-color-logic.csv` | Emotion → Color treatment |
| `slide-backgrounds.csv` | Slide type → Image category |
| `slide-copy.csv` | 25 copywriting formulas (PAS, AIDA, FAB) |
| `slide-charts.csv` | 25 chart types with Chart.js config |

### Contextual Decision Flow

```
1. Parse goal/context
2. Search slide-strategies.csv → strategy + emotion beats
3. Per slide: layout-logic → typography → color-logic → backgrounds → animation
4. Generate HTML with design tokens
5. Validate with slide-token-validator.py
```

### Slide Requirements

ALL slides must: import the design-tokens CSS (single source of truth); use CSS variables exclusively; use Chart.js for charts; include navigation (keyboard, click, progress bar); center content.

### Token Compliance

```css
/* CORRECT */ background: var(--slide-bg); color: var(--color-primary);
/* WRONG   */ background: #0D0D0D; color: #FF6B6B;
```

## Best Practices

1. Never use raw hex in components — always reference tokens
2. Semantic layer enables theme switching (light/dark)
3. Component tokens enable per-component customization
4. Use HSL format for opacity control
5. Document every token's purpose

---

*Source: [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) design-system (MIT).*
