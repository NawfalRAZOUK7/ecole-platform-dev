---
name: slides
description: Create strategic HTML presentations with Chart.js, design tokens, responsive layouts, copywriting formulas, and contextual slide strategies. Use for pitch decks, demo presentations (e.g. DEMO_GUIDE_PARRAIN_INDUSTRIEL), marketing slides, data-driven decks.
argument-hint: "[topic] [slide-count]"
metadata:
  author: claudekit
  version: "1.0.0"
---

> **Vendored note (Ecole Platform):** run `.ai/skills/fetch-skill-assets.sh` once to pull
> the references below from upstream. For the PFE soutenance deck (LaTeX/Beamer), prefer
> the latex-writing skill's Beamer section in `ecole-platform-final-report`; use this skill
> for HTML decks (demos, sponsor presentations).

# Slides

Strategic HTML presentation design with data visualization.

## When to Use

- Marketing presentations and pitch decks
- Data-driven slides with Chart.js
- Strategic slide design with layout patterns
- Copywriting-optimized presentation content

## Subcommands

| Subcommand | Description | Reference |
|------------|-------------|-----------|
| `create` | Create strategic presentation slides | `references/create.md` |

## References (Knowledge Base)

| Topic | File |
|-------|------|
| Layout Patterns | `references/layout-patterns.md` |
| HTML Template | `references/html-template.md` |
| Copywriting Formulas | `references/copywriting-formulas.md` |
| Slide Strategies | `references/slide-strategies.md` |

## Core Requirements (from design-system slide rules)

ALL slides must:
1. Import a single design-tokens CSS file and use `var(--…)` exclusively — no hardcoded hex
2. Use Chart.js for charts (not CSS-only bars):
   ```html
   <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
   ```
3. Include navigation (keyboard arrows, click, progress bar)
4. Center-align content; one idea per slide
5. Alternate emotional beats (Duarte sparkline: "what is" ↔ "what could be") for engagement

## Routing

1. Parse subcommand from arguments (first word)
2. Load corresponding `references/{subcommand}.md`
3. Execute with remaining arguments

---

*Source: [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) slides (MIT).*
