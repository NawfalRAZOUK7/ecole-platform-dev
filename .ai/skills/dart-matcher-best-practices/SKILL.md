---
name: dart-matcher-best-practices
description: |-
  Best practices for using `expect` and `package:matcher`.
  Focuses on readable assertions, proper matcher selection, and avoiding
  common pitfalls. Use when writing or reviewing assertions in mobile/test.
license: Apache-2.0
---

# Dart Matcher Best Practices

## When to use this skill

- Writing assertions using `expect` and `package:matcher`.
- Migrating legacy manual checks to cleaner matchers.
- Debugging confusing test failures.

## Discovery

Search for suboptimal patterns:

- Length checks that should use `hasLength`: regex `expect\([^,]+.length,\s*`
- Boolean checks with specific matchers available: regex `expect\([^,]+.isEmpty,\s*(true|equals\(true\))`, same for `isNotEmpty` and `.contains(...)`
- Manual map lookups instead of `containsPair`: regex `expect\([^,]+\[.*\],\s*`

## Core Matchers

### 1. Collections

- **`hasLength(n)`**: prefer `expect(list, hasLength(n))` over `expect(list.length, n)` — better error messages (shows actual list content).
- **`isEmpty` / `isNotEmpty`**: prefer `expect(list, isEmpty)` over `expect(list.isEmpty, true)`.
- **`contains(item)`**: prefer over `expect(list.contains(item), true)`.
- **`unorderedEquals(items)`**: verify contents regardless of order.
- **`containsPair(key, value)`**: prefer over `expect(map[key], value)` or `containsKey` checks.

### 2. Type Checks

- **`isA<T>()`**: prefer for inline assertions; allows chaining constraints via `.having()`.
- **`TypeMatcher<T>`**: prefer when defining top-level reusable matchers; use `const`: `const isMyType = TypeMatcher<MyType>();`

### 3. Object Properties (`having`)

```dart
expect(person, isA<Person>()
    .having((p) => p.name, 'name', 'Alice')
    .having((p) => p.age, 'age', greaterThan(18)));
```

Use meaningful parameter names in the closure (`(e) => e.message`, not `p0`). Provides detailed failure messages indicating exactly which property failed.

### 4. Async Assertions

- **`completion(matcher)`**: wait for a future and check its value. Prefer `await expectLater(future, completion(equals(42)))`.
- **`throwsA(matcher)`**: `await expectLater(future, throwsA(isA<StateError>()))`; synchronous throwing functions are fine with plain `expect(() => fn(), throwsA(...))`.

### 5. Using `expectLater`

```dart
// GOOD: waits for future to complete before checking side effects
await expectLater(future, completion(equals(42)));
expect(sideEffectState, equals('done'));

// BAD: side effect check might run before future completes
expect(future, completion(equals(42)));
expect(sideEffectState, equals('done')); // Race condition!
```

## Principles

1. **Readable failures**: choose matchers that produce clear error messages.
2. **Avoid manual logic**: no `if` statements or `for` loops for assertions; let matchers handle it.
3. **Specific matchers**: use the most specific matcher available.

## Related Skills

- **dart-test-fundamentals** — structuring tests, lifecycles, configuration.
- **flutter-mocktail** — mocking and verification.

---

*Source: [kevmoo/dash_skills](https://github.com/kevmoo/dash_skills) (Apache-2.0).*
