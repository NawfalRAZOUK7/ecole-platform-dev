---
name: nothing-design
description: This skill should be used when the user explicitly says "Nothing style", "Nothing design", "/nothing-design", or directly asks to use/apply the Nothing design system. NEVER trigger automatically for generic UI or design tasks.
version: 3.0.0
allowed-tools: [Read, Write, Edit, Glob, Grep]
---

# Nothing-Inspired UI/UX Design System

A senior product designer's toolkit trained in Swiss typography, industrial design (Braun, Teenage Engineering), and modern interface craft. Monochromatic, typographically driven, information-dense without clutter. Dark and light mode with equal rigor.

**Before starting any design work, declare which Google Fonts are required and how to load them** (see `references/tokens.md` Section 1). Never assume fonts are already available.

---

## 1. DESIGN PHILOSOPHY

- **Subtract, don't add.** Every element must earn its pixel. Default to removal.
- **Structure is ornament.** Expose the grid, the data, the hierarchy itself.
- **Monochrome is the canvas.** Color is an event, not a default — except when encoding data status (see Section 3).
- **Type does the heavy lifting.** Scale, weight, and spacing create hierarchy — not color, not icons, not borders.
- **Both modes are first-class.** Dark mode: OLED black. Light mode: warm off-white. Ask the user which mode to start with.
- **Industrial warmth.** Technical and precise, but never cold.

---

## 2. CRAFT RULES — HOW TO COMPOSE

### 2.1 Visual Hierarchy: The Three-Layer Rule

Every screen has exactly **three layers of importance.**

| Layer | What | How |
|-------|------|-----|
| **Primary** | The ONE thing the user sees first. A number, a headline, a state. | Doto or Space Grotesk at display size. `--text-display`. 48–96px breathing room. |
| **Secondary** | Supporting context. Labels, descriptions, related data. | Space Grotesk at body/subheading. `--text-primary`. Grouped tight (8–16px) to the primary. |
| **Tertiary** | Metadata, navigation, system info. | Space Mono at caption/label. `--text-secondary` or `--text-disabled`. ALL CAPS. Pushed to edges. |

**The test:** squint at the screen. Can you still tell what's most important? If two things compete, one needs to shrink, fade, or move.

### 2.2 Font Discipline

Per screen, use maximum: **2 font families** (Space Grotesk + Space Mono; Doto only for hero moments), **3 font sizes**, **2 font weights**.

| Decision | Size | Weight | Color |
|----------|:---:|:---:|:---:|
| Heading vs. body | Yes | No | No |
| Label vs. value | No | No | Yes |
| Active vs. inactive nav | No | No | Yes |
| Hero number vs. unit | Yes | No | No |
| Section title vs. content | Yes | Optional | No |

**Rule of thumb:** if reaching for a new font-size, it's probably a spacing problem. Add distance instead.

### 2.3 Spacing as Meaning

```
Tight (4–8px)   = "These belong together" (icon + label, number + unit)
Medium (16px)    = "Same group, different items" (list items, form fields)
Wide (32–48px)   = "New group starts here" (section breaks)
Vast (64–96px)   = "This is a new context" (hero to content, major divisions)
```

**If a divider line is needed, the spacing is probably wrong.**

### 2.4 Container Strategy (prefer top)

1. **Spacing alone** → 2. single divider line → 3. subtle border outline → 4. surface card.
Use the lightest tool that works. Never box the most important element.

### 2.5 Color as Hierarchy

Max 4 gray levels per screen: `--text-display` (100%, hero, one per screen), `--text-primary` (90%), `--text-secondary` (60%), `--text-disabled` (40%).

**Red (#D71921) is not part of the hierarchy.** It's an interrupt. If nothing is urgent, no red on the screen. Data status colors are exempt when encoding data values — apply color to the **value itself**, not labels or row backgrounds.

### 2.6 Consistency vs. Variance

**Be consistent in:** font families, label treatment (Space Mono ALL CAPS), spacing rhythm, color roles, component shapes, alignment.

**Break the pattern in exactly ONE place per screen.** This single break IS the design.

### 2.7 Compositional Balance

**Asymmetry > symmetry.** Favor large-left/small-right, top-heavy, or edge-anchored compositions. Balance heavy elements with more empty space, not more heavy elements.

### 2.8 The Nothing Vibe

1. Confidence through emptiness. 2. Precision in the small things. 3. Data as beauty (`36GB/s` in Space Mono at 48px IS the visual). 4. Mechanical honesty (a toggle = physical switch). 5. One moment of surprise. 6. Percussive, not fluid (click not swoosh).

### 2.9 Visual Variety in Data-Dense Screens

When 3+ data sections appear on one screen, vary the visual form:

| Form | Best for | Weight |
|------|----------|--------|
| Hero number (large Doto/Space Mono) | Single key metric | Heavy — use once |
| Segmented progress bar | Progress toward goal | Medium |
| Concentric rings / arcs | Multiple related percentages | Medium |
| Inline compact bar | Secondary metrics in rows | Light |
| Number-only with status color | Values without proportion | Lightest |
| Sparkline | Trends over time | Medium |
| Stat row (label + value) | Simple data points | Light |

---

## 3. ANTI-PATTERNS — WHAT TO NEVER DO

- No gradients in UI chrome; no shadows; no blur. Flat surfaces, border separation.
- No skeleton loading screens — use `[LOADING...]` text or segmented spinner.
- No toast popups — inline status text: `[SAVED]`, `[ERROR: ...]`
- No sad-face illustrations, mascots, or multi-paragraph empty states.
- No zebra striping in tables; no filled/multi-color icons or emoji as UI.
- No parallax, scroll-jacking, or gratuitous animation; no spring/bounce easing.
- No border-radius > 16px on cards. Buttons are pill (999px) or technical (4–8px).
- Data visualization: differentiate with **opacity** (100%/60%/30%) or **pattern** before introducing color.

---

## 4. WORKFLOW

1. **Declare fonts** — tell the user which Google Fonts to load (`references/tokens.md`)
2. **Ask mode** — dark or light? Neither is default.
3. **Sketch hierarchy** — identify the 3 layers before writing any code
4. **Compose** — apply craft rules (Sections 2.1–2.9)
5. **Check tokens** — `references/tokens.md` for exact values
6. **Build components** — `references/components.md` for patterns
7. **Adapt to platform** — `references/platform-mapping.md` (HTML/CSS, React/Tailwind, SwiftUI)

---

*Source: [dominikmartn/nothing-design-skill](https://github.com/dominikmartn/nothing-design-skill) v3.0.0 (MIT). Fetch references/tokens.md, components.md, platform-mapping.md from upstream if missing locally.*
