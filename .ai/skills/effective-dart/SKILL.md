---
name: effective-dart
description: "Apply Effective Dart guidelines to write idiomatic, high-quality Dart and Flutter code. Use when writing new Dart code in mobile/, reviewing pull requests for style compliance, refactoring naming conventions, adding doc comments, structuring imports, enforcing type annotations, or running code review checks against Effective Dart standards."
---

# Effective Dart Skill

This skill defines how to write idiomatic, high-quality Dart and Flutter code following Effective Dart guidelines.

---

## 1. Naming Conventions

| Kind | Convention | Example |
|---|---|---|
| Classes, enums, typedefs, type parameters, extensions | `UpperCamelCase` | `MyWidget`, `UserState` |
| Packages, directories, source files | `lowercase_with_underscores` | `user_profile.dart` |
| Import prefixes | `lowercase_with_underscores` | `import '...' as my_prefix;` |
| Variables, parameters, named parameters, functions | `lowerCamelCase` | `userName`, `fetchData()` |

- Capitalize acronyms and abbreviations longer than two letters like words: `HttpRequest`, not `HTTPRequest`.
- Avoid abbreviations unless the abbreviation is more common than the full term.
- Prefer putting the **most descriptive noun last** in names.
- Use terms **consistently** throughout your code.
- Follow mnemonic conventions for type parameters: `E` (element), `K`/`V` (key/value), `T`/`S`/`U` (generic types).
- Prefer a **noun phrase** for non-boolean properties or variables.
- Prefer a **non-imperative verb phrase** for boolean properties or variables; prefer the positive form.

---

## 2. Types and Functions

- Use **class modifiers** (`final`, `sealed`, `interface`, `base`, `mixin`) to control whether a class can be extended or implemented.
- **Type annotate variables** without initializers.
- Type annotate **fields and top-level variables** if the type isn't obvious.
- **Annotate return types** and **parameter types** on function declarations.
- Write **type arguments** on generic invocations that aren't inferred.
- Annotate with `dynamic` instead of letting inference fail.
- Use `Future<void>` as the return type of async members that do not produce values.
- Use **getters/setters** for operations that conceptually access/change properties.
- Use **inclusive start and exclusive end** parameters to accept a range.

```dart
// Prefer: explicit class modifier
final class AppConfig {
  final String apiUrl;
  final int timeout;
  const AppConfig({required this.apiUrl, required this.timeout});
}

// Prefer: sealed for exhaustive pattern matching
sealed class Result<T> {}
class Success<T> extends Result<T> { final T value; Success(this.value); }
class Failure<T> extends Result<T> { final Exception error; Failure(this.error); }
```

---

## 3. Style

```bash
dart format .
```

- Format code with `dart format` — don't manually format.
- Use **curly braces** for all flow control statements.
- Prefer `final` over `var` when variable values won't change; `const` for compile-time constants.
- Prefer lines **80 characters or fewer** — even in Markdown files and comments (readable in split-screen). Exceptions: long URLs or unbreakable identifiers. Rely on the `lines_longer_than_80_chars` lint.

### Multi-line Strings

Prefer triple-quoted multi-line strings (`'''`) over concatenating with `+` and `\n`, especially for large text blocks (SQL, HTML, PEM keys):

```dart
// Avoid
final pem = '-----BEGIN RSA PRIVATE KEY-----\n' +
    base64Encode(fullBytes) +
    '\n-----END RSA PRIVATE KEY-----';

// Prefer
final pem = '''
-----BEGIN RSA PRIVATE KEY-----
${base64Encode(fullBytes)}
-----END RSA PRIVATE KEY-----''';
```

Discovery regexes for refactor candidates: `['"]\s*\+\s*['"]` and `\+\s*['"].*\\n`.

---

## 4. Imports and Files

- Don't import libraries inside the `src` directory of another package.
- Don't allow import paths to reach into or out of `lib`.
- **Prefer relative import paths** within a package; don't use `/lib/` or `../` in import paths.
- Consider writing a **library-level doc comment** for library files.

---

## 5. Structure

- Keep files **focused on a single responsibility**; limit file length.
- Group related functionality together.
- Prefer making fields and top-level variables `final`; constructors `const` when supported.
- **Prefer making declarations private** — only expose what's necessary.

---

## 6. Usage Patterns

```dart
// Adjacent string concatenation (not +)
final greeting = 'Hello, '
    'world!';

// Collection literals
final list = [1, 2, 3];
final map = {'key': 'value'};

// Initializing formals
class Point {
  final double x, y;
  Point(this.x, this.y);
}

// Empty constructor body
class Empty {
  Empty();  // not Empty() {}
}

// rethrow to preserve stack trace
try {
  doSomething();
} catch (e) {
  log(e);
  rethrow;
}
```

- Use `whereType<T>()` to filter a collection by type.
- Initialize fields at their **declaration** when possible.
- Override `hashCode` if you override `==`.
- **Prefer specific exception handling**: `on SomeException catch (e)` instead of broad `catch (e)`.

---

## 7. Documentation

```dart
/// Returns the sum of [a] and [b].
///
/// Throws [ArgumentError] if either value is negative.
int add(int a, int b) { ... }
```

- Use `///` doc comments — not `/* */` — for types and members.
- Start with a **single-sentence summary**, separated into its own paragraph.
- Start boolean variable/property comments with "Whether".
- Use `[identifier]` to refer to in-scope identifiers.
- Put doc comments **before** metadata annotations.
- Document **why** code exists, not just what it does.

---

## 8. Testing Patterns

```dart
import 'package:test/test.dart';

void main() {
  group('CartService', () {
    late CartService cart;

    setUp(() => cart = CartService());

    test('addItem increases item count', () {
      cart.addItem(Product(id: '1', name: 'Widget', price: 9.99));
      expect(cart.items, hasLength(1));
    });
  });
}
```

Widget tests use `testWidgets` and `WidgetTester` with `pumpWidget` / `tap` / `pump` / `find`.

---

## 9. Code Review Workflow

1. **Naming** — verify identifiers follow Section 1 conventions.
2. **Type annotations** — public API parameters, return types, uninitialized variables annotated.
3. **Class modifiers** — `final`, `sealed`, or `interface` used where appropriate.
4. **Documentation** — public members have `///` doc comments with a single-sentence summary.
5. **Style** — `dart format --output=none --set-exit-if-changed .`
6. **Analysis** — `dart analyze` with zero issues.

---

## References

- [Effective Dart](https://dart.dev/effective-dart)

*Sources: [evanca/flutter-ai-rules](https://github.com/evanca/flutter-ai-rules) (MIT), merged with [kevmoo/dash_skills](https://github.com/kevmoo/dash_skills) dart-best-practices (Apache-2.0).*
