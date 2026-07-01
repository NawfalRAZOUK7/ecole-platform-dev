---
name: design
description: "Comprehensive design skill: brand identity, design tokens, UI styling, logo generation (55 styles, Gemini AI), corporate identity program (50 deliverables, CIP mockups), HTML presentations (Chart.js), banner design (22 styles, social/ads/web/print), icon design (15 styles, SVG), social photos (HTML→screenshot, multi-platform). Actions: design logo, create CIP, generate mockups, build slides, design banner, generate icon, create social photos, brand identity, design system."
argument-hint: "[design-type] [context]"
license: MIT
metadata:
  author: claudekit
  version: "2.1.0"
---

> **Vendored note (Ecole Platform):** AI generation (logo/CIP/icon) requires
> `GEMINI_API_KEY` + `pip install google-genai pillow`. Run
> `.ai/skills/fetch-skill-assets.sh` once to pull references/, scripts/ and data/ CSVs.
> Upstream invokes scripts from `~/.claude/skills/design/` — here they live in
> `.ai/skills/design/`, so adjust paths accordingly. Without an API key, the
> references (styles, color psychology, prompt engineering, sizes) are still
> directly usable for manual/SVG design work.

# Design

Unified design skill: brand, tokens, UI, logo, CIP, slides, banners, social photos, icons.

## When to Use

- Brand identity, voice, assets
- Design system tokens and specs
- UI styling with shadcn/ui + Tailwind
- Logo design and AI generation
- Corporate identity program (CIP) deliverables
- Presentations and pitch decks
- Banner design for social media, ads, web, print
- Social photos for Instagram, Facebook, LinkedIn, Twitter, Pinterest, TikTok

## Sub-skill Routing

| Task | Sub-skill | Details |
|------|-----------|---------|
| Brand identity, voice, assets | `brand` | `.ai/skills/brand` |
| Tokens, specs, CSS vars | `design-system-tokens` | `.ai/skills/design-system` |
| shadcn/ui, Tailwind, code | `ui-styling` | `.ai/skills/ui-styling` |
| Logo creation, AI generation | Logo (built-in) | `references/logo-design.md` |
| CIP mockups, deliverables | CIP (built-in) | `references/cip-design.md` |
| Presentations, pitch decks | Slides (built-in) | `references/slides.md` |
| Banners, covers, headers | Banner (built-in) | `references/banner-sizes-and-styles.md` |
| Social media images/photos | Social Photos (built-in) | `references/social-photos-design.md` |
| SVG icons, icon sets | Icon (built-in) | `references/icon-design.md` |

## Logo Design (Built-in)

55+ styles, 30 color palettes, 25 industry guides.

```bash
# Generate design brief
python3 scripts/logo/search.py "tech startup modern" --design-brief -p "BrandName"

# Search styles/colors/industries
python3 scripts/logo/search.py "minimalist clean" --domain style
python3 scripts/logo/search.py "tech professional" --domain color
python3 scripts/logo/search.py "education e-learning" --domain industry

# Generate with AI (white background always)
python3 scripts/logo/generate.py --brand "EcolePlatform" --style minimalist --industry education
```

## CIP Design (Built-in)

50+ deliverables, 20 styles, 20 industries.

```bash
# Brief + search
python3 scripts/cip/search.py "education platform" --cip-brief -b "BrandName"
python3 scripts/cip/search.py "business card letterhead" --domain deliverable

# Generate mockups (with logo recommended)
python3 scripts/cip/generate.py --brand "EcolePlatform" --logo /path/to/logo.png --deliverable "business card" --industry "education"
python3 scripts/cip/generate.py --brand "EcolePlatform" --logo logo.png --industry "education" --set

# Render HTML presentation of results
python3 scripts/cip/render-html.py --brand "EcolePlatform" --industry "education" --images /path/to/cip-output
```

Models: `flash` (default), `pro` (4K text fidelity).

## Slides (Built-in)

Strategic HTML presentations with Chart.js, design tokens, copywriting formulas.
Load `references/slides-create.md` for the workflow; see also the standalone `slides` skill.

| Topic | File |
|-------|------|
| Creation Guide | `references/slides-create.md` |
| Layout Patterns | `references/slides-layout-patterns.md` |
| HTML Template | `references/slides-html-template.md` |
| Copywriting | `references/slides-copywriting-formulas.md` |
| Strategies | `references/slides-strategies.md` |

## Banner Design (Built-in)

22 art direction styles. See the standalone `banner-design` skill and `references/banner-sizes-and-styles.md`.

## Icon Design (Built-in)

15 styles, 12 categories. Gemini generates SVG as text output (no image API needed).

```bash
python3 scripts/icon/generate.py --prompt "settings gear" --style outlined
python3 scripts/icon/generate.py --prompt "shopping cart" --style filled --color "#6366F1"
python3 scripts/icon/generate.py --prompt "cloud upload" --batch 4 --output-dir ./icons
python3 scripts/icon/generate.py --prompt "user profile" --sizes "16,24,32,48" --output-dir ./icons
```

Top styles: outlined (UI/web), filled (mobile nav), duotone (marketing), rounded (friendly), sharp (tech/enterprise), flat (Material), gradient (SaaS).

## Social Photos (Built-in)

Multi-platform social image design: HTML/CSS → screenshot export.
Load `references/social-photos-design.md` for sizes, templates, best practices.

| Platform | Size (px) | Platform | Size (px) |
|----------|-----------|----------|-----------|
| IG Post | 1080×1080 | FB Post | 1200×630 |
| IG Story | 1080×1920 | X Post | 1200×675 |
| IG Carousel | 1080×1350 | LinkedIn | 1200×627 |
| YT Thumb | 1280×720 | Pinterest | 1000×1500 |

Workflow: analyze prompt → ideate 3-5 concepts (AskUserQuestion) → design HTML per idea × size → screenshot at exact px (2x deviceScaleFactor, Playwright) → visually verify → report.

## Workflows

### Complete Brand Package
1. **Logo** → `scripts/logo/generate.py` → variants
2. **CIP** → `scripts/cip/generate.py --logo ...` → deliverable mockups
3. **Presentation** → `references/slides-create.md` → pitch deck

### New Design System
1. **Brand** (brand skill) → colors, typography, voice
2. **Tokens** (design-system-tokens skill) → semantic token layers
3. **Implement** (ui-styling skill) → Tailwind/shadcn or existing CSS tokens

## References

All under `references/`: design-routing, logo-design, logo-style-guide, logo-color-psychology, logo-prompt-engineering, cip-design, cip-deliverable-guide, cip-style-guide, cip-prompt-engineering, slides-create, slides-layout-patterns, slides-html-template, slides-copywriting-formulas, slides-strategies, banner-sizes-and-styles, social-photos-design, icon-design.

## Setup

```bash
export GEMINI_API_KEY="your-key"  # https://aistudio.google.com/apikey
pip install google-genai pillow
```

---

*Source: [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) design v2.1.0 (MIT).*
