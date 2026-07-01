---
name: ui-ux-pro-max
description: "UI/UX design intelligence for web and mobile. Includes 50+ styles, 161 color palettes, 57 font pairings, 161 product types, 99 UX guidelines, and 25 chart types across 10 stacks (React, Next.js, Vue, Svelte, SwiftUI, React Native, Flutter, Tailwind, shadcn/ui, and HTML/CSS). Actions: plan, build, create, design, implement, review, fix, improve, optimize, enhance, refactor, and check UI/UX code. Projects: website, landing page, dashboard, admin panel, e-commerce, SaaS, portfolio, blog, and mobile app. Elements: button, modal, navbar, sidebar, card, table, form, and chart. Styles: glassmorphism, claymorphism, minimalism, brutalism, neumorphism, bento grid, dark mode, responsive, skeuomorphism, and flat design. Topics: color systems, accessibility, animation, layout, typography, font pairing, spacing, interaction states, shadow, and gradient."
---

> **Vendored note (Ecole Platform):** the searchable database (CSV data + `scripts/search.py`)
> is pulled by `.ai/skills/fetch-skill-assets.sh` (upstream keeps it under repo root `cli/`;
> the script maps it into this skill folder). This project's stacks are **React (web/) and
> Flutter (mobile/)** — substitute those wherever the examples below say React Native, and use
> `--stack flutter` / `--domain react` accordingly.

# UI/UX Pro Max - Design Intelligence

Comprehensive design guide for web and mobile applications. Contains 50+ styles, 161 color palettes, 57 font pairings, 161 product types with reasoning rules, 99 UX guidelines, and 25 chart types across 10 technology stacks. Searchable database with priority-based recommendations.

## When to Apply

Use when the task involves **UI structure, visual design decisions, interaction patterns, or user experience quality control**.

**Must use:** designing new pages (landing, dashboard, admin, SaaS, mobile app); creating/refactoring UI components; choosing color schemes, typography, spacing, or layout systems; reviewing UI code for UX/accessibility/visual consistency; navigation, animations, responsive behavior; product-level design decisions.

**Recommended:** UI looks "not professional enough" but the reason is unclear; usability feedback; pre-launch UI polish; cross-platform alignment; design systems.

**Skip:** pure backend logic, API/database design, non-UI performance, infra/DevOps.

**Decision criterion:** if the task changes how a feature **looks, feels, moves, or is interacted with**, use this skill.

## Rule Categories by Priority

| Priority | Category | Impact | Domain | Key Checks (Must Have) | Anti-Patterns (Avoid) |
|----------|----------|--------|--------|------------------------|------------------------|
| 1 | Accessibility | CRITICAL | `ux` | Contrast 4.5:1, alt text, keyboard nav, aria-labels | Removing focus rings, icon-only buttons without labels |
| 2 | Touch & Interaction | CRITICAL | `ux` | Min size 44×44px, 8px+ spacing, loading feedback | Hover-only reliance, instant state changes (0ms) |
| 3 | Performance | HIGH | `ux` | WebP/AVIF, lazy loading, reserve space (CLS < 0.1) | Layout thrashing, cumulative layout shift |
| 4 | Style Selection | HIGH | `style`, `product` | Match product type, consistency, SVG icons (no emoji) | Mixing flat & skeuomorphic randomly, emoji as icons |
| 5 | Layout & Responsive | HIGH | `ux` | Mobile-first breakpoints, viewport meta, no horizontal scroll | Fixed px container widths, disabling zoom |
| 6 | Typography & Color | MEDIUM | `typography`, `color` | Base 16px, line-height 1.5, semantic color tokens | Body text < 12px, gray-on-gray, raw hex in components |
| 7 | Animation | MEDIUM | `ux` | 150–300ms, motion conveys meaning, spatial continuity | Decorative-only animation, animating width/height, no reduced-motion |
| 8 | Forms & Feedback | MEDIUM | `ux` | Visible labels, error near field, helper text, progressive disclosure | Placeholder-only labels, errors only at top |
| 9 | Navigation Patterns | HIGH | `ux` | Predictable back, bottom nav ≤5, deep linking | Overloaded nav, broken back behavior |
| 10 | Charts & Data | LOW | `chart` | Legends, tooltips, accessible colors | Color alone conveying meaning |

## Quick Reference (condensed)

### 1. Accessibility (CRITICAL)
contrast 4.5:1 (3:1 large text) · visible focus rings (2–4px) · alt text · aria-labels / accessibilityLabel for icon-only controls · tab order = visual order · label[for] on form fields · skip links · sequential heading hierarchy · never color-only meaning · support Dynamic Type / text scaling · respect prefers-reduced-motion · meaningful screen-reader labels and reading order · cancel/back escape routes in modals and multi-step flows · keyboard alternatives for drag-and-drop.

### 2. Touch & Interaction (CRITICAL)
44×44pt (Apple) / 48×48dp (Material) minimum targets, extend hit area if visual is smaller · ≥8px gap between targets · tap (not hover) for primary interactions · disable buttons during async + spinner · errors near the problem · cursor-pointer on clickables (web) · `touch-action: manipulation` · platform-standard gestures, never block system gestures · press feedback (ripple/highlight) within ~100ms · haptics for confirmations (sparingly) · always a visible-control alternative to gestures · keep targets out of notch/gesture-bar zones · swipe affordances visible · drag threshold against accidental drags.

### 3. Performance (HIGH)
WebP/AVIF + srcset + lazy-load non-critical · declare width/height or aspect-ratio (CLS) · font-display: swap, preload only critical fonts · inline critical CSS · route/feature code-splitting · async/defer third-party scripts · batch DOM reads/writes · reserve space for async content · `loading="lazy"` below fold · virtualize 50+ item lists · ~16ms/frame budget · skeletons (not blocking spinners) for >1s ops · input latency <100ms · tap feedback <100ms · debounce/throttle scroll/resize/input · offline states + degraded modes for slow networks.

### 4. Style Selection (HIGH)
match style to product type (`--design-system`) · one style across all pages · SVG icons (Heroicons/Lucide), never emoji · palette from product/industry (`--domain color`) · shadows/blur/radius aligned with the chosen style · respect platform idioms (HIG vs Material) · distinct hover/pressed/disabled states · consistent elevation scale · design light/dark together · one icon language (stroke width, radius) · prefer native/system controls · blur signals background dismissal, not decoration · ONE primary CTA per screen.

### 5. Layout & Responsive (HIGH)
viewport meta, never disable zoom · mobile-first, systematic breakpoints (375/768/1024/1440) · ≥16px body on mobile (avoids iOS auto-zoom) · 35–60 chars/line mobile, 60–75 desktop · no horizontal scroll · 4pt/8dp spacing scale · consistent desktop max-width · layered z-index scale (0/10/20/40/100/1000) · fixed bars reserve padding for content · avoid nested scroll regions · `min-h-dvh` over `100vh` · landscape support · core content first on mobile · hierarchy via size/spacing/contrast, not color alone.

### 6. Typography & Color (MEDIUM)
line-height 1.5–1.75 body · 65–75 chars/line · matched font pairings · consistent type scale (12/14/16/18/24/32) · platform type systems (Dynamic Type, Material roles) · weight hierarchy (600–700 headings, 400 body, 500 labels) · semantic color tokens — no raw hex in components · dark mode = desaturated/lighter tones, not inversion; test contrast separately · AA 4.5:1 pairs · functional colors get icon/text too · prefer wrapping over truncation · default letter-spacing for body · tabular figures for data columns · intentional whitespace grouping.

### 7. Animation (MEDIUM)
150–300ms micro, ≤400ms transitions · transform/opacity only · skeleton beyond 300ms loading · animate 1-2 key elements max · ease-out enter / ease-in exit · every animation expresses cause-effect · smooth state transitions, no snapping · spatial continuity between screens (shared elements, directional slides) · subtle parallax only + reduced-motion respect · spring/physics curves feel natural · exits ~60–70% of enter duration · stagger lists 30–50ms/item · interruptible, never input-blocking · crossfade content swaps · 0.95–1.05 scale press feedback · gestures track the finger in real time · direction expresses hierarchy (enter from below = deeper) · global duration/easing tokens · no CLS from animation · modals animate from their trigger · forward = left/up, back = right/down.

### 8. Forms & Feedback (MEDIUM)
visible label per input · error below its field · loading → success/error on submit · mark required fields · helpful empty states · toasts auto-dismiss 3-5s without stealing focus (aria-live="polite") · confirm destructive actions, offer undo · persistent helper text · disabled = 0.38–0.5 opacity + semantics · progressive disclosure · validate on blur (not keystroke) · semantic input types for correct mobile keyboard · password show/hide · autocomplete/textContentType for autofill · step indicator + back nav in multi-step flows · autosave long forms · confirm dismissing unsaved sheets · errors state cause + fix · group related fields · read-only ≠ disabled visually · focus first invalid field after submit · error summary with anchors for multiple errors (WCAG) · ≥44px input height on mobile · destructive actions in danger color, spatially separated · role="alert"/aria-live for errors · 4.5:1 contrast on state colors · timeout feedback with retry.

### 9. Navigation Patterns (HIGH)
bottom nav max 5 items with labels · drawer for secondary nav · predictable back with preserved scroll/state · deep links for all key screens · iOS bottom tab bar / Android top app bar idioms · icon + label, never icon-only nav · highlight current location · separate primary vs secondary nav · clear modal dismiss affordance · reachable search with suggestions · breadcrumbs for 3+ levels (web) · restore state on back · support system gesture nav (swipe-back, predictive back) · sparing nav badges · overflow menu over cramming · bottom nav = top-level only · sidebar on ≥1024px · never silently reset the back stack · same nav placement on every page · don't mix tab+sidebar+bottom-nav at one level · modals are not primary navigation · move focus to main content after route change (WCAG) · core nav reachable from deep pages · destructive actions separated from normal nav · explain unavailable destinations.

### 10. Charts & Data (LOW)
chart type matches data (trend→line, comparison→bar, proportion→pie ≤5 categories) · accessible palettes, no red/green-only · table alternative for screen readers · patterns/textures supplement color · visible legend near chart, clickable to toggle series · tooltips on hover/tap with exact values, keyboard-reachable · labeled axes with units, readable ticks · responsive simplification on small screens · meaningful empty/error states with retry · skeleton while loading · respect reduced-motion · aggregate 1000+ points with drill-down (keep back-path) · locale-aware number/date formatting · ≥44pt interactive elements · ≥3:1 data-vs-background contrast · direct labels for small datasets · sortable tables with aria-sort · low-contrast gridlines · trends over decoration · text summary of the chart's key insight · clear time granularity labels · CSV/image export for data-heavy products.

## How to Use This Skill

| Scenario | Trigger Examples | Start From |
|----------|-----------------|------------|
| **New project / page** | "Build a landing page", "Build a dashboard" | Step 1 → Step 2 (design system) |
| **New component** | "Create a pricing card", "Add a modal" | Step 3 (domain search: style, ux) |
| **Choose style / color / font** | "What style fits an education app?" | Step 2 (design system) |
| **Review existing UI** | "Review this page for UX issues" | Quick Reference checklist above |
| **Fix a UI bug** | "Button hover is broken", "Layout shifts on load" | Quick Reference → relevant section |
| **Improve / optimize** | "Improve mobile experience" | Step 3 (domain search: ux, react) |
| **Dark mode** | "Add dark mode support" | Step 3 (domain: style "dark mode") |
| **Charts / data viz** | "Add an analytics dashboard chart" | Step 3 (domain: chart) |
| **Stack best practices** | "React performance tips", "Flutter lists" | Step 4 (stack search) |

### Step 1: Analyze User Requirements
Extract: product type (education platform → productivity/tool hybrid), target audience (students, teachers, admins), style keywords, stack (React web / Flutter mobile).

### Step 2: Generate Design System (REQUIRED)

```bash
python3 .ai/skills/ui-ux-pro-max/scripts/search.py "<product_type> <industry> <keywords>" --design-system [-p "Project Name"]
```

Searches domains in parallel (product, style, color, landing, typography), applies reasoning rules, returns a complete design system (pattern, style, colors, typography, effects, anti-patterns).

**Persist for cross-session retrieval** with `--persist` (creates `design-system/MASTER.md` + `design-system/pages/` overrides; page files override Master):

```bash
python3 .ai/skills/ui-ux-pro-max/scripts/search.py "<query>" --design-system --persist -p "Ecole Platform" --page "dashboard"
```

### Step 3: Supplement with Domain Searches

```bash
python3 .ai/skills/ui-ux-pro-max/scripts/search.py "<keyword>" --domain <domain> [-n <max_results>]
```

| Domain | Use For | Example Keywords |
|--------|---------|------------------|
| `product` | Product type recommendations | SaaS, e-commerce, education, healthcare |
| `style` | UI styles, colors, effects | glassmorphism, minimalism, dark mode, brutalism |
| `typography` | Font pairings, Google Fonts | elegant, playful, professional, modern |
| `color` | Color palettes by product type | saas, education, fintech |
| `landing` | Page structure, CTA strategies | hero, testimonial, pricing, social-proof |
| `chart` | Chart types, library recommendations | trend, comparison, timeline, funnel |
| `ux` | Best practices, anti-patterns | animation, accessibility, z-index, loading |
| `google-fonts` | Individual font lookup | sans serif, monospace, variable font |
| `react` | React/Next.js performance | waterfall, bundle, suspense, memo, rerender |
| `web` | App interface guidelines (iOS/Android) | accessibilityLabel, touch targets, safe areas |
| `prompt` | AI prompts, CSS keywords | (style name) |

### Step 4: Stack Guidelines

```bash
python3 .ai/skills/ui-ux-pro-max/scripts/search.py "<keyword>" --stack flutter   # mobile/
python3 .ai/skills/ui-ux-pro-max/scripts/search.py "<keyword>" --domain react    # web/
```

## Tips

- Multi-dimensional keywords: `"education platform clean content-first"` not just `"app"`.
- `--design-system` first, then `--domain` deep-dives.
- Output formats: default ASCII box, or `-f markdown` for docs.

| Problem | What to Do |
|---------|------------|
| Can't decide style/color | Re-run `--design-system` with different keywords |
| Dark mode contrast issues | §6: color-dark-mode + color-accessible-pairs |
| Animations feel unnatural | §7: spring-physics + easing + exit-faster-than-enter |
| Poor form UX | §8: inline-validation + error-clarity + focus-management |
| Confusing navigation | §9: nav-hierarchy + bottom-nav-limit + back-behavior |
| Layout breaks on small screens | §5: mobile-first + breakpoint-consistency |
| Performance/jank | §3: virtualize-lists + main-thread-budget + debounce-throttle |

## Common Rules for Professional UI (App)

**Icons & visual elements:** no emoji as structural icons (vector icons only: Lucide, @expo/vector-icons, Flutter Icons) · vector-only assets · press states never shift layout bounds · official brand logos with correct usage · icon sizes as tokens (sm/md/lg) · consistent stroke width (1.5px or 2px) · one filled-vs-outline style per hierarchy level · ≥44×44pt touch areas (hitSlop if smaller) · baseline-aligned icons with consistent padding · WCAG contrast for icons.

**Interaction:** pressed feedback within 80-150ms · micro-interactions 150-300ms with native easing · screen-reader focus order matches visual · disabled semantics + reduced emphasis · ≥44pt/48dp tap areas · one primary gesture per region · semantic native controls (`Button`, `Pressable`) over generic containers.

**Light/dark contrast:** surfaces clearly separated · body text ≥4.5:1 in BOTH themes, secondary ≥3:1 · borders visible in both themes · interaction-state parity across themes · token-driven theming, no per-screen hex · modal scrim 40-60% black.

**Layout & spacing:** respect safe areas for fixed bars · clearance for status/nav bars and gesture indicator · consistent content width per device class · 4/8dp rhythm · readable text measure on tablets · vertical rhythm tiers (16/24/32/48) · adaptive gutters by breakpoint · scroll insets so content isn't hidden behind fixed bars.

## Pre-Delivery Checklist (App UI)

**Visual:** no emoji icons; one icon family; correct brand assets; pressed states don't jitter; semantic theme tokens everywhere.
**Interaction:** pressed feedback on everything tappable; ≥44pt/48dp targets; 150-300ms timing; clear disabled states; SR focus order; no gesture conflicts.
**Light/Dark:** ≥4.5:1 primary and ≥3:1 secondary text in both modes; visible dividers and states in both; scrim 40-60%; both themes actually tested.
**Layout:** safe areas respected; scroll content not hidden behind bars; verified small phone/large phone/tablet, portrait+landscape; adaptive gutters; 4/8dp rhythm; readable long-form measure.
**Accessibility:** labels on meaningful images/icons; labeled form fields with hints and clear errors; color never the only indicator; reduced motion + dynamic type don't break layout; roles/states announced correctly.

---

*Source: [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) (MIT). Quick Reference rule lists condensed from itemized form to compact prose (all rules retained); upstream React-Native-only project notes generalized to this repo's React + Flutter stacks.*
