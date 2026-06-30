---
name: banner-design
description: "Design banners for social media, ads, website heroes, creative assets, and print. Multiple art direction options with AI-generated visuals. Actions: design, create, generate banner. Platforms: Facebook, Twitter/X, LinkedIn, YouTube, Instagram, Google Display, website hero, print. Styles: minimalist, gradient, bold typography, photo-based, illustrated, geometric, retro, glassmorphism, 3D, neon, duotone, editorial, collage."
argument-hint: "[platform] [style] [dimensions]"
license: MIT
metadata:
  author: claudekit
  version: "1.0.0"
---

> **Vendored note (Ecole Platform):** this skill references external claudekit skills
> (`ai-artist`, `ai-multimodal`, `frontend-design`, `chrome-devtools`, `assets-organizing`)
> that are NOT in this repo, and AI image generation needs `GEMINI_API_KEY`. Without them,
> follow the same workflow using available equivalents: design the HTML/CSS banner directly,
> use CSS gradients/shapes or stock images instead of generated visuals, and screenshot via
> Playwright (`web/` has `@playwright/test`) instead of chrome-devtools scripts.
> Run `.ai/skills/fetch-skill-assets.sh` once to pull `references/banner-sizes-and-styles.md`.

# Banner Design - Multi-Format Creative Banner System

Design banners across social, ads, web, and print formats. Generates multiple art direction options per request with AI-powered visual elements. This skill handles banner design only. Does NOT handle video editing, full website design, or print production.

## When to Activate

- User requests banner, cover, or header design
- Social media cover/header creation
- Ad banner or display ad design
- Website hero section visual design
- Event/print banner design
- Creative asset generation for campaigns

## Workflow

### Step 1: Gather Requirements (AskUserQuestion)

1. **Purpose** — social cover, ad banner, website hero, print, or creative asset?
2. **Platform/size** — which platform or custom dimensions?
3. **Content** — headline, subtext, CTA, logo placement?
4. **Brand** — existing brand guidelines? (check `docs/brand-guidelines.md`)
5. **Style preference** — any art direction? (show style options if unsure)
6. **Quantity** — how many options to generate? (default: 3)

### Step 2: Research & Art Direction

1. Activate `ui-ux-pro-max` skill for design intelligence
2. Research design references (e.g. Pinterest) for art direction inspiration
3. Select 2-3 complementary art direction styles from `references/banner-sizes-and-styles.md`

### Step 3: Design & Generate Options

For each art direction option:

1. **Create HTML/CSS banner**
   - Use exact platform dimensions from size reference
   - Apply safe zone rules (critical content in central 70-80%)
   - Max 2 typefaces, single CTA, 4.5:1 contrast ratio
2. **Generate or source visual elements** (AI generation if available, otherwise CSS art / stock imagery)
3. **Compose final banner** — overlay text, CTA, logo on the visual in HTML/CSS

### Step 4: Export Banners to Images

Serve the HTML files locally and screenshot each banner at exact platform dimensions (Playwright or any headless browser). Compress if >5MB.

**Output path convention:**
```
assets/banners/{campaign}/
├── minimalist-1500x500.png
├── gradient-1500x500.png
└── bold-type-1500x500.png
```
Kebab-case filenames: `{style}-{width}x{height}.{ext}`; date prefix for time-sensitive campaigns.

### Step 5: Present Options & Iterate

Present all exported images side-by-side with style name, preview, design rationale, file path & dimensions. Iterate until approved.

## Banner Size Quick Reference

| Platform | Type | Size (px) | Aspect Ratio |
|----------|------|-----------|--------------|
| Facebook | Cover | 820 × 312 | ~2.6:1 |
| Twitter/X | Header | 1500 × 500 | 3:1 |
| LinkedIn | Personal | 1584 × 396 | 4:1 |
| YouTube | Channel art | 2560 × 1440 | 16:9 |
| Instagram | Story | 1080 × 1920 | 9:16 |
| Instagram | Post | 1080 × 1080 | 1:1 |
| Google Ads | Med Rectangle | 300 × 250 | 6:5 |
| Google Ads | Leaderboard | 728 × 90 | 8:1 |
| Website | Hero | 1920 × 600-1080 | ~3:1 |

Full reference: `references/banner-sizes-and-styles.md`

## Art Direction Styles (Top 10)

| Style | Best For | Key Elements |
|-------|----------|--------------|
| Minimalist | SaaS, tech | White space, 1-2 colors, clean type |
| Bold Typography | Announcements | Oversized type as hero element |
| Gradient | Modern brands | Mesh gradients, chromatic blends |
| Photo-Based | Lifestyle, e-com | Full-bleed photo + text overlay |
| Geometric | Tech, fintech | Shapes, grids, abstract patterns |
| Retro/Vintage | F&B, craft | Distressed textures, muted colors |
| Glassmorphism | SaaS, apps | Frosted glass, blur, glow borders |
| Neon/Cyberpunk | Gaming, events | Dark bg, glowing neon accents |
| Editorial | Media, luxury | Grid layouts, pull quotes |
| 3D/Sculptural | Product, tech | Rendered objects, depth, shadows |

Full 22 styles: `references/banner-sizes-and-styles.md`

## Design Rules

- **Safe zones**: critical content in central 70-80% of canvas
- **CTA**: one per banner, bottom-right, min 44px height, action verb
- **Typography**: max 2 fonts, min 16px body, ≥32px headline
- **Text ratio**: under 20% for ads (Meta penalizes heavy text)
- **Print**: 300 DPI, CMYK, 3-5mm bleed
- **Brand**: always inject brand guidelines context

---

*Source: [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) banner-design (MIT). AI-generation commands generalized; upstream "Security" boilerplate dropped.*
