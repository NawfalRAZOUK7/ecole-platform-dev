# Design Phase 2 — Brand & Signature Surfaces (traceability)

> Continuation of `DESIGN_ENHANCEMENT_PLAN.md`. Order chosen: **brand-first**
> (logo is a dependency for splash/nav/login). Everything reduced-motion- and
> RTL-safe, reuses existing tokens. Web verified with `tsc` + `eslint`; mobile
> with brace/paren balance + user-run `flutter analyze`.

## Decisions (locked)
- **Order:** brand-first → logo → web splash → mobile splash → nav (web) → nav (mobile) → login (web) → finish migrations → P2.
- **Logo:** designer's choice — a creative, distinctive mark with a ring motif (ties into the "landing effect").
- **"Landing effect":** a **brand intro / splash animation** (logo + animated ring reveal, a few hundred ms), not a marketing page.
- **Images:** no text-to-image model available; logo is authored as **vector SVG** and exported to **PNG** (ImageMagick/Pillow). Superior for a logo (scalable, editable).

## Status

| # | Item | Surface | Status |
| - | ---- | ------- | ------ |
| 23 | Logo / icon (SVG + PNG + favicon) | both | ✅ |
| 24 | Brand intro animation (BrandSplash) | web | ✅ |
| 25 | Brand intro animation (app_splash_screen) | mobile | ✅ |
| 26 | Nav item redesign + effects | web | ✅ |
| 27 | Nav item redesign + effects | mobile | ✅ |
| 28 | Login page redesign (branded split) | web | ✅ |
| 29 | Snackbar migration (30 sites) + skeletons (13 web pages) | both | ✅ |
| 30 | P2: dashboard hero, onboarding celebration, chart polish | both | ✅ |
| 31 | Verify — web tsc+eslint clean; mobile balanced (run `flutter analyze`) | both | ✅ |

## Delivered assets
- `web/public/brand/`: `ecole-icon.svg`, `ecole-icon-{1024,512,192,180,32}.png`, `ecole-logo-horizontal.svg`, `ecole-logo-onlight.png`, `ecole-logo-ondark.png`
- `web/public/`: `favicon.svg` (new mark), `icon-192.png`, `icon-512.png`, `apple-touch-icon.png`
- `mobile/assets/brand/`: `ecole-icon.svg`, `ecole-icon-512.png`, `ecole-logo-horizontal.svg`

## Notes / left intentionally
- 48 complex mobile snackbars (custom color/action/duration) kept as-is; only the simple `SnackBar(content: Text(...))` form was migrated to `AppSnackBar`.
- Detail/editor pages keep the spinner (a list skeleton doesn't fit those); skeletons applied to list/dashboard pages.
- Chart gradient/animation pattern demonstrated on QuizAnalytics; replicable across the other ~9 recharts pages.
- `mobile/assets/brand/` not yet registered in `pubspec.yaml` (splash uses a CustomPainter, so no asset dependency needed; register only if you reference the PNGs directly).

## Brand tokens (existing, reused)
- Primary `#2563eb`, secondary `#8b5cf6`, accent `#f59e0b`, success `#10b981`.
- Shadow scale `--shadow-sm..xl` + `--shadow-glow-primary`; radii + spacing tokens; light/dark/kids themes.
- Motion: easeOutCubic `cubic-bezier(0.16,1,0.3,1)`; durations 150/250/400ms (web) and `AppMotion` (mobile).

## Notes
- Asset output dir: `web/public/brand/` (web) + `mobile/assets/brand/` (mobile), plus favicon in `web/public/`.
- Migrations (#29) are low-risk cleanup folded in after the visual work.
