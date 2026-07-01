---
name: dart-test-fundamentals
description: |-
  Core concepts and best practices for `package:test`.
  Covers `test`, `group`, lifecycle methods (`setUp`, `tearDown`), and
  configuration (`dart_test.yaml`). Use when writing or restructuring
  Dart test files in mobile/test.
license: Apache-2.0
---

# Dart Test Fundamentals

## When to use this skill

- Writing new test files.
- Structuring test suites with `group`.
- Configuring test execution via `dart_test.yaml`.
- Understanding test lifecycle methods.

## Discovery

To find candidates for improving test structure:

### `try-finally` Cleanup
Search for tests that use `try-finally` for cleanup instead of `addTearDown`:
- **Regex**: `\bfinally\s*\{` (check if used for resource cleanup inside a test).

## Core Concepts

### 1. Test Structure (`test` and `group`)

- **`test`**: the fundamental unit of testing.
- **`group`**: organizes tests into logical blocks.
  - Groups can be nested; descriptions are concatenated.
  - Helps scope `setUp` and `tearDown` calls.
  - **Naming**: use `PascalCase` for groups that correspond to a class name (e.g., `group('MyClient', ...)`).
  - **Avoid single groups**: don't wrap all tests in a file with one `group` if it's the only one.
  - **NOTE**: do NOT remove groups when cleaning up existing code you didn't create unless explicitly asked — it causes diff churn.

- **Naming tests**:
  - Avoid redundant "test" prefixes; use `group` instead.
  - Include the expected behavior or outcome (e.g., `'throws StateError'`, `'adds API key to URL'`).
  - Descriptions should read well when concatenated with their group name.

- **Named parameters placement**: place `testOn`, `timeout`, `skip` immediately after the description string, before the callback:
  ```dart
  test('description', testOn: 'vm', () {
    // assertions
  });
  ```

### 2. Lifecycle Methods

- **`setUp`**: runs *before* every `test` in the current group (and nested groups).
- **`tearDown`**: runs *after* every `test` in the current group.
- **`setUpAll`** / **`tearDownAll`**: run *once* before/after all tests in the group.

Best practice: use `setUp` for resetting state to ensure test isolation; avoid sharing mutable state between tests without resetting it.

### 3. Cleaning Up Resources

Use `addTearDown` instead of `try-finally` for resources created within the test body:

```dart
test('can create and delete a file', () {
  final file = File('temp.txt');
  // Register teardown immediately after resource creation
  addTearDown(() {
    if (file.existsSync()) file.deleteSync();
  });

  file.writeAsStringSync('hello');
  expect(file.readAsStringSync(), 'hello');
});
```

### 4. Configuration (`dart_test.yaml`)

```yaml
platforms:
  - vm
  - chrome

tags:
  integration:
    timeout: 2x

timeouts:
  2x # Double the default timeout
```

Tag usage in code: `@Tags(['integration'])` at the top of the file.
Running tags: `dart test --tags integration`.

### 5. File Naming
- Test files **must** end in `_test.dart`.
- Place tests in the `test/` directory.

## Common commands

- `dart test` (or `flutter test` in the mobile app): run all tests.
- `dart test test/path/to/file_test.dart`: run a specific file.
- `dart test --name "substring"`: run tests matching a description.

## Related Skills

- **dart-matcher-best-practices** — assertions with `package:matcher` (`expect`).
- **flutter-testing** — widget tests and Riverpod test patterns.
- **dart-test-coverage** — running and interpreting coverage.

---

*Source: [kevmoo/dash_skills](https://github.com/kevmoo/dash_skills) (Apache-2.0).*
