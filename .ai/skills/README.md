# Skills — ecole-platform-dev

Agent-agnostic skills for developing the platform (Flutter mobile, React web, Python backend).
Canonical location: `.ai/skills/`. Claude Code auto-discovers them via the `.claude/skills`
symlink; other agents should read this directory directly — each skill is a folder with a
`SKILL.md` (YAML frontmatter: `name`, `description`) plus optional `references/`.

## Flutter / Dart (mobile/)

| Skill | Purpose |
| ----- | ------- |
| [flutter-riverpod](flutter-riverpod/SKILL.md) | Riverpod state management: providers, Ref, families, autoDispose, side effects, testing |
| [flutter-app-architecture](flutter-app-architecture/SKILL.md) | Layered MVVM: views, view models, repositories, services, DI, unidirectional flow |
| [flutter-testing](flutter-testing/SKILL.md) | Unit + widget tests that catch real regressions; Riverpod overrides |
| [flutter-mocktail](flutter-mocktail/SKILL.md) | Mocking: mock vs fake, stubbing, fallback values, verification |
| [flutter-errors](flutter-errors/SKILL.md) | Common runtime/layout error fixes (RenderFlex overflow, unbounded constraints…) |
| [flutter-code-review](flutter-code-review/SKILL.md) | Structured PR review checklist for Flutter/Dart |
| [effective-dart](effective-dart/SKILL.md) | Effective Dart style: naming, types, docs, structure |
| [dart-3-updates](dart-3-updates/SKILL.md) | Dart 3 features: patterns, sealed classes, switch expressions, records |
| [dart-test-fundamentals](dart-test-fundamentals/SKILL.md) | package:test structure, lifecycle, dart_test.yaml |
| [dart-test-coverage](dart-test-coverage/SKILL.md) | Running and interpreting coverage (lcov / format_coverage) |
| [dart-matcher-best-practices](dart-matcher-best-practices/SKILL.md) | Readable assertions with package:matcher |

## UI / Design (web/ and mobile/)

| Skill | Purpose |
| ----- | ------- |
| [ui-ux-pro-max](ui-ux-pro-max/SKILL.md) | Design intelligence: 50+ styles, palettes, font pairings, 99 UX rules, priority checklists, searchable DB |
| [design](design/SKILL.md) | Unified design router: logo (AI), CIP mockups, slides, banners, icons, social photos (needs GEMINI_API_KEY for generation) |
| [design-system](design-system/SKILL.md) | Three-layer token architecture (primitive→semantic→component), token scripts, slide decision system |
| [brand](brand/SKILL.md) | Brand voice, visual identity, messaging, asset validation, brand→tokens sync |
| [ui-styling](ui-styling/SKILL.md) | Accessible UI patterns: shadcn/Tailwind setup (if adopted), a11y checklist, responsive design, tokens |
| [slides](slides/SKILL.md) | Strategic HTML presentations with Chart.js + design tokens |
| [banner-design](banner-design/SKILL.md) | Multi-format banner design (22 styles, social/ads/web/print sizes) |
| [nothing-design](nothing-design/SKILL.md) | Nothing-inspired design system (explicit trigger only): tokens, components, platform mapping incl. Flutter |

## Diagrams (docs/)

| Skill | Purpose |
| ----- | ------- |
| [plantuml-diagrams](plantuml-diagrams/SKILL.md) | UML/architecture diagrams from code, Kroki rendering loop |
| [mermaid-diagrams](mermaid-diagrams/SKILL.md) | Markdown-embedded diagrams (GitHub renders natively) |
| [drawio-diagrams](drawio-diagrams/SKILL.md) | Freeform/pixel-controlled .drawio XML diagrams + shape reference |

## Bootstrap

The design-suite skills are vendored as SKILL.md only; their references/scripts/data/fonts
come from upstream. The bootstrap also installs additional verbatim skills chosen by the
user: flutter-ai-rules extras (patrol-e2e-testing, flutter-pre-caching,
architecture-feature-first, flutterfire-configure, the 13 firebase-* skills, and
bloc/provider/flutter-change-notifier/mockito — **competing patterns**: the project standard
stays Riverpod + mocktail; use those only when explicitly working with that pattern) and
dash_skills micro-skills (dart-doc-validation, dart-long-lines, dart-multiline-strings,
dart-package-maintenance). dart-best-practices and dart-modern-features were **merged** into
effective-dart and dart-3-updates instead of installed as duplicates. Run once on your machine:

```bash
bash .ai/skills/fetch-skill-assets.sh
```

## Provenance

Sources: [evanca/flutter-ai-rules](https://github.com/evanca/flutter-ai-rules) (MIT) — riverpod/mocktail selection matches pubspec.yaml;
[kevmoo/dash_skills](https://github.com/kevmoo/dash_skills) (Apache-2.0) — overlapping skills (dart-best-practices, dart-modern-features) skipped in favor of effective-dart / dart-3-updates;
[nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) (ui-styling, trimmed);
[dominikmartn/nothing-design-skill](https://github.com/dominikmartn/nothing-design-skill);
[Agents365-ai/365-skills](https://github.com/Agents365-ai/365-skills) (plantuml, mermaid).
