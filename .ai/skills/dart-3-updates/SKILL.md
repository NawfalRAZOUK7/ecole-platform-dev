---
name: dart-3-updates
description: "Apply modern Dart features (v3.0–v3.10) including patterns, sealed classes, switch expressions, records, if-case syntax, extension types, class modifiers, wildcards, null-aware elements, digit separators, and dot shorthands. Use when writing switch statements, refactoring if-else chains, creating data classes, choosing between records and classes, destructuring values, or modernizing pre-Dart-3 code."
---

# Dart 3 Updates Skill

Apply Dart 3 language features — branches, patterns, pattern types, and records — correctly and idiomatically.

## When to Use

* Writing or refactoring `switch` statements or `if-else` chains.
* Creating new data-holding classes and deciding between sealed classes, records, or plain classes.
* Destructuring values from maps, lists, records, or objects.
* Modernizing pre-Dart-3 code to use patterns, exhaustiveness checks, or switch expressions.

---

## 1. Branches

### if-case

```dart
if (pair case [int x, int y]) {
  print('$x, $y');
}
```

- Variables declared in the pattern are scoped to the matching branch.
- If the pattern does not match, control flows to the `else` branch (if present).

### switch statements

```dart
switch (command) {
  case 'quit':
    quit();
  case 'start' || 'begin': // logical-or pattern
    startGame();
  default:
    print('Unknown command');
}
```

- `break` is **not required** — matched case bodies don't fall through.
- Empty cases fall through; use `break` to prevent it.
- Use logical-or patterns (`case a || b`) to share a body between cases.

### switch expressions

```dart
final color = switch (shape) {
  Circle() => 'red',
  Square() => 'blue',
  _ => 'unknown',
};
```

- Omit `case`; use `=>`; separate with commas; default is `_`.

### Exhaustiveness

```dart
sealed class Shape {}
class Circle extends Shape {}
class Square extends Shape {}

// Dart knows all subtypes — no default needed:
String describe(Shape s) => switch (s) {
  Circle() => 'circle',
  Square() => 'square',
};
```

### Guard clauses

```dart
switch (point) {
  case (int x, int y) when x == y:
    print('Diagonal: $x');
  case (int x, int y):
    print('$x, $y');
}
```

---

## 2. Patterns

```dart
// Variable declaration
var (a, [b, c]) = ('str', [1, 2]);

// Variable assignment (swap)
(b, a) = (a, b);

// for-in loop destructuring
for (final MapEntry(:key, :value) in map.entries) { ... }

// Object pattern
var Foo(:one, :two) = myFoo;

// JSON / nested data validation
if (data case {'user': [String name, int age]}) {
  print('$name, $age');
}
```

- Wildcard `_` ignores parts of a matched value; rest elements (`...`) ignore list tails.
- Case patterns are **refutable**: if no match, execution continues to the next case.

---

## 3. Pattern Types

| Pattern | Syntax | Description |
|---|---|---|
| Logical-or | `p1 \|\| p2` | Matches if any branch matches. All branches must bind the same variables. |
| Logical-and | `p1 && p2` | Both must match. Variable names must not overlap. |
| Relational | `== c`, `< c`, `>= c` | Compares value to a constant. Combine with `&&` for ranges. |
| Cast | `subpattern as Type` | Asserts type, then matches inner pattern. |
| Null-check | `subpattern?` | Matches non-null; binds non-nullable type. |
| Null-assert | `subpattern!` | Matches non-null or throws. |
| Constant | `42`, `'str'`, `const Foo()` | Matches if value equals the constant. |
| Variable | `var name`, `final Type name` | Binds matched value to a new variable. |
| Wildcard | `_`, `Type _` | Matches any value without binding. |
| List | `[p1, p2]` | Matches lists by position; length must match unless `...` used. |
| Map | `{'key': subpattern}` | Matches maps by key. Missing keys throw `StateError`. |
| Record | `(p1, p2)`, `(x: p1, y: p2)` | Matches records by shape. |
| Object | `ClassName(field: p)` | Matches by type and destructures via getters. |

All pattern types can be **nested and combined**.

---

## 4. Records

```dart
// Create
var record = ('first', a: 2, b: true, 'last');

// Access
print(record.$1);   // positional: 'first'
print(record.a);    // named: 2

// Multiple return values
(String name, int age) userInfo(Map<String, dynamic> json) {
  return (json['name'] as String, json['age'] as int);
}
var (name, age) = userInfo(json);
final (:name, :age) = userInfo(json); // named form
```

- Records are **anonymous, immutable, fixed-size** aggregates with structural equality (`==`/`hashCode` auto-defined).

### Records vs. data classes

Use a **record** when: returning multiple values; grouping a few values locally; structural equality with no behavior.

Use a **class** when: the type is reused across files/features; you need methods, encapsulation, inheritance, or `copyWith`; it's part of a public API or long-lived model.

Use `typedef` for record types to improve readability.

---

## 5. Later Dart 3.x Features (3.3–3.10)

### Extension Types — zero-cost wrappers

```dart
// Avoid: allocating a wrapper class for type safety
class Id {
  final int value;
  Id(this.value);
  bool get isValid => value > 0;
}

// Prefer: compiles down to the underlying type at runtime
extension type Id(int value) {
  bool get isValid => value > 0;
}
```

### Class Modifiers (recap)
Prefer `sealed` for closed subtype families (exhaustive switch); `final`/`base`/`interface` to restrict use outside the defining library.

### Digit Separators

```dart
const int oneMillion = 1_000_000;   // not 1000000
```

### Wildcard Variables
Use `_` as a non-binding parameter/variable for intentionally unused values:

```dart
void handleEvent(String _, int status) => print('Status: $status');
```

### Null-Aware Elements

```dart
// Avoid
var names = ['Alice', if (optionalName != null) optionalName, 'Charlie'];
// Prefer
var names = ['Alice', ?optionalName, 'Charlie'];
```

### Dot Shorthands
Omit the type name when inferable: `LogLevel currentLevel = .info;`

## Discovery (refactor candidates)

- Switch statements where every case returns/assigns: `switch\s*\([^)]+\)\s*\{\s*case`
- Manual JSON extraction: `containsKey\(['"][^'"]+['"]\)` and `json\[['"][^'"]+['"]\]\s+is\s+`
- Collection `if` null checks: `if\s*\(\w+\s*!=\s*null\)\s*\w+`
- Long numbers without separators: `\b\d{6,}\b`

## 6. Migration Workflow

1. **Replace if-else chains with switch expressions**

```dart
final label = switch (status) {
  Status.loading => 'Loading...',
  Status.success => 'Done',
  Status.error => 'Error',
};
```

2. **Convert abstract class hierarchies to sealed classes** (enables exhaustive switch)

```dart
sealed class Result {}
final class Success extends Result { const Success(this.data); final String data; }
final class Failure extends Result { const Failure(this.error); final String error; }
```

3. **Use records for multiple return values** instead of wrapper classes.

4. **Validate** — run `dart analyze` after each change.

---

*Sources: [evanca/flutter-ai-rules](https://github.com/evanca/flutter-ai-rules) (MIT), merged with [kevmoo/dash_skills](https://github.com/kevmoo/dash_skills) dart-modern-features (Apache-2.0).*
