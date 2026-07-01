# Design & Motion Enhancement Plan — Web + Mobile

> Goal: make both apps feel advanced, professional, and high-end without a ground-up
> redesign. Grounded in the actual codebase (June 2026). Plan first — implement after
> you pick the batches. Effort = rough dev time. Impact = perceived-quality lift.

---

## 1. Where things actually stand

**Web (React 18 + Vite + framer-motion + design tokens).** The *foundation is excellent
and largely unused.* You already have:

- `AnimatedPage`, `StaggerContainer`, `StaggerItem` (framer-motion) — **adopted in ~0 of 133 page files.**
- `framer-motion` imported directly in only **2** files; the shell `Layout.tsx` is animated, pages are not.
- Ready but idle: `animations.css` (shimmer skeletons, toast slide, card hover), `glassmorphism.css`,
  `CelebrationOverlay`, per-level themes (`maternelle/primaire/college`), `useReducedMotion`, full token set
  (`tokens.ts` / `generated-tokens.css`) with light/dark/kids/gamification colors.
- Pages are well-architected (react-query, i18n, shared `LoadingState`/`EmptyState`/`ErrorBanner`) but
  visually static — no entrance motion, plain spinners instead of skeletons, flat cards.

**Verdict:** the single biggest win on web is **adoption**, not new effects. You built the engine; it isn't wired to the wheels.

**Mobile (Flutter + Riverpod + Material 3).** Solid themed light/dark (`app_theme.dart`),
token files (colors/radii/spacing/typography), age themes, per-screen RTL. Motion is ad-hoc:
~12 files touch animation (mostly kids/games), **no motion package** (no `flutter_animate`/`shimmer`/`lottie`),
and **default Material page transitions** (no custom `PageTransitionsTheme`). Lists/cards appear instantly.

**Verdict:** mobile needs a small, consistent **motion layer** built once and reused — not scattered one-offs.

---

## 2. Design principles to standardize first (both platforms)

These are cheap, set the ceiling for everything else, and prevent "animation soup":

1. **One motion vocabulary.** Durations: 150ms (micro), 250ms (standard), 400ms (page/overlay).
   Easing: a single "emphasized" curve — web `cubic-bezier(0.16, 1, 0.3, 1)` (already in `AnimatedPage`),
   Flutter `Curves.easeOutCubic`. Reuse everywhere; never hand-pick per component.
2. **Motion is enhancement, never required.** Honor `prefers-reduced-motion` (web hook exists) and
   Flutter `MediaQuery.disableAnimations`. Reduced = instant, no parallax/scale, opacity only.
3. **Depth via tokens, not ad-hoc shadows.** Add a small elevation scale (e.g. `--shadow-sm/md/lg`
   + `--shadow-primary-glow`) and use it consistently. Same for radii and spacing (tokens already exist).
4. **Animate meaning, not decoration.** Entrance for new content, state-change for feedback (save/error),
   continuity for navigation. Skip idle/loop animations outside the kids/gamification context.

---

## 3. Web enhancements (prioritized)

### P0 — Quick wins (adopt what exists) · high impact / low effort

- **Wire `AnimatedPage` into the routed `<Outlet>` once**, with `AnimatePresence mode="wait"` keyed by
  route. Every page then gets a consistent fade/slide entrance for free — no per-page edits. *(S)*
- **Replace spinners with shimmer skeletons** on the main list/table/dashboard loads using the existing
  `.skeleton--shimmer` + `Skeleton.tsx`. Perceived-speed jump. Start with admin users/invitations,
  reports history, content library, billing. *(M)*
- **Stagger list/grid reveals** with `StaggerContainer`/`StaggerItem` on card grids (content library,
  games, dashboards). *(S–M)*
- **Standard micro-interactions:** card `hover` lift + shadow (token-based), button press scale (`active:scale-[.98]`),
  focus-visible rings from one token. Apply via shared classes, not per component. *(M)*
- **Animated number/stat count-up** in `StatCard` (dashboards/reports) — small framer-motion or a tiny hook. *(S)*

### P1 — Polish layer · high impact / medium effort

- **Toast/notification system** using the ready `toast-slide-in/out` keyframes (consistent success/error feedback). *(M)*
- **Dialog/sheet transitions:** scale-fade for `ConfirmDialog`, slide-over for side panels; backdrop blur via `glassmorphism.css`. *(M)*
- **Elevation & glass on key surfaces:** topbar, modals, the notification dropdown — selective glassmorphism (not everywhere). *(M)*
- **Empty/error states with personality:** `EmptyState`/`ErrorBanner` get a small illustration/icon motion + clear CTA. *(M)*
- **Theme/RTL/dark-mode transition:** cross-fade on theme switch and language direction flip instead of hard repaint. *(S)*

### P2 — Bolder / signature moments · medium-high effort

- **Dashboard hero treatment:** gradient/mesh header, animated greeting, live KPI chips with count-up + sparkline (recharts already in). *(L)*
- **Onboarding & auth delight:** multi-step progress with motion, success confetti via `CelebrationOverlay`, animated illustrations. *(L)*
- **Recharts polish:** animated draw-in, custom tooltips, gradient fills, consistent palette from tokens. *(M–L)*
- **Gamification moments:** XP bar fill, level-up burst, streak flame pulse (kids tokens already defined). *(M–L)*
- **Scroll-reveal** for long pages (intersection-based fade/slide) — used sparingly. *(M)*

---

## 4. Mobile enhancements (prioritized)

### P0 — Build the motion layer once · high impact / low–medium effort

- **Custom `PageTransitionsTheme`** in `app_theme.dart` (shared axis / fade-through) so *every* route
  transition upgrades at once — the mobile equivalent of wiring `AnimatedPage`. *(S)*
- **Add `flutter_animate`** (one dependency) for declarative, reduced-motion-aware entrance/stagger,
  OR a small shared `AnimatedEntrance`/`StaggeredList` widget if you'd rather stay dependency-free. *(S)*
- **Shimmer skeletons** for list loads (you have `kids_skeleton_layouts`; generalize it to adult screens
  instead of `CircularProgressIndicator`). *(M)*
- **Micro-interactions:** `InkWell`/scale feedback on cards, `AnimatedSwitcher` on status badges/filters,
  `Hero` on avatar → profile and list-item → detail. *(M)*

### P1 — Polish layer

- **List item entrance stagger** on the main list screens (users, invitations, classes, content, submissions). *(M)*
- **Animated bottom-nav / tab indicator** and selection feedback. *(S–M)*
- **Pull-to-refresh + load-more** with smooth state transitions (some screens already paginate). *(M)*
- **Snackbars/toasts** with consistent slide + iconography matching web. *(S)*

### P2 — Bolder / signature

- **Animated splash → home handoff** (you have `app_splash_screen`; make it transition, not cut). *(M)*
- **Dashboard hero + count-up KPIs**, gradient headers consistent with web. *(L)*
- **Gamification feedback** parity with web (XP/level/streak), `animated_guide` mascot reactions. *(M–L)*
- **Optional Lottie** for celebration/empty states (kids context) — only if asset budget allows. *(M)*

---

## 5. Cross-platform consistency

- Keep **the same motion tokens, naming, and timing** on both sides so the apps feel like one product.
- Mirror **signature moments** (page entrance, skeletons, stat count-up, celebration, theme/RTL transition)
  on web and mobile so a user moving between them recognizes the language.
- Reduced-motion and RTL must be respected by every shared pattern (web hook + Flutter `disableAnimations`;
  RTL already handled — verify motion directions flip, e.g. slide-in side).

---

## 6. Suggested first implementation batch (my recommendation)

Highest perceived-quality lift for the least risk, both platforms, all reduced-motion-safe:

**Web**
1. Wire `AnimatedPage` into the router outlet (one change, every page benefits).
2. Shimmer skeletons on ~5 highest-traffic list/dashboard loads.
3. Shared card-hover + button-press + focus-ring micro-interactions.
4. `StatCard` count-up.

**Mobile**
5. Custom `PageTransitionsTheme` (one change, every route benefits).
6. Shared entrance + staggered-list widget; apply to the main list screens.
7. Generalized shimmer skeletons for list loads.
8. `Hero` avatar/list→detail + `AnimatedSwitcher` on the status badges we just refactored.

All eight are P0, additive, and verifiable (`flutter analyze`, `npm run lint`/`typecheck`, visual check).
Estimated: web ~1 focused pass, mobile ~1 focused pass.

---

## 7. Effort / impact summary

| Tier | Web | Mobile | Impact | Risk |
| ---- | --- | ------ | ------ | ---- |
| P0 adoption / motion layer | AnimatedPage wiring, skeletons, micro-interactions, count-up | PageTransitions, entrance/stagger, skeletons, Hero | Very high | Low |
| P1 polish | toasts, dialogs, glass, state personality, theme transition | list stagger, nav indicator, refresh, snackbars | High | Low–Med |
| P2 signature | dashboard hero, onboarding delight, chart polish, gamification | splash handoff, hero KPIs, gamification, Lottie | High (wow) | Med |

---

_Next step: tell me which batch to implement (the §6 recommendation, or pick/reorder items). I'll
implement, keep everything reduced-motion- and RTL-safe, and verify with analyze/lint + a visual pass._
