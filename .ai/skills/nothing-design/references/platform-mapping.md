# Nothing Design System — Platform Mapping

## 1. HTML / CSS / WEB (React/Vite — web/)

Load fonts via Google Fonts `<link>` or `@import`. Use CSS custom properties, `rem` for type, `px` for spacing/borders. Dark/light via `prefers-color-scheme` or class toggle.

```css
:root {
  --black: #000000;
  --surface: #111111;
  --surface-raised: #1A1A1A;
  --border: #222222;
  --border-visible: #333333;
  --text-disabled: #666666;
  --text-secondary: #999999;
  --text-primary: #E8E8E8;
  --text-display: #FFFFFF;
  --accent: #D71921;
  --accent-subtle: rgba(215,25,33,0.15);
  --success: #4A9E5C;
  --warning: #D4A843;
  --interactive: #5B9BF6;
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;
  --space-2xl: 48px;
  --space-3xl: 64px;
  --space-4xl: 96px;
}
```

---

## 2. FLUTTER (mobile/)

Bundle `.ttf` files under `assets/fonts/` and declare in `pubspec.yaml`. Map tokens to a `ThemeExtension` or constants class:

```dart
abstract final class NdColors {
  static const black = Color(0xFF000000);
  static const surface = Color(0xFF111111);
  static const surfaceRaised = Color(0xFF1A1A1A);
  static const border = Color(0xFF222222);
  static const borderVisible = Color(0xFF333333);
  static const textDisabled = Color(0xFF666666);
  static const textSecondary = Color(0xFF999999);
  static const textPrimary = Color(0xFFE8E8E8);
  static const textDisplay = Color(0xFFFFFFFF);
  static const accent = Color(0xFFD71921);
  static const success = Color(0xFF4A9E5C);
  static const warning = Color(0xFFD4A843);
  static const interactive = Color(0xFF5B9BF6);
}
```

Light mode values in tokens.md Dark/Light table. Use `ThemeMode.system` with both `ThemeData` variants.

---

## 3. SWIFTUI / iOS

Register fonts in Info.plist, bundle `.ttf` files. Use `@Environment(\.colorScheme)` for mode switching. Derive a `Color`/`Font` extension from the token tables (`.custom("Doto"/"SpaceGrotesk-Regular"/"SpaceMono-Regular", size:)`).

---

*Source: [dominikmartn/nothing-design-skill](https://github.com/dominikmartn/nothing-design-skill) (MIT); Flutter mapping added for Ecole Platform, Paper-tool section dropped.*
