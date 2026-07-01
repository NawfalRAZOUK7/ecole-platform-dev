---
name: dart-test-coverage
description: |-
  Understand and improve test coverage in a Dart package.
  Helps run coverage, interpret results, and identify missed lines.
  Use when asked to check or improve coverage in mobile/ (the project
  tracks coverage via Codecov — see PLAN_AUGMENT_COVERAGE_TESTS.md).
---

# Dart Test Coverage

Guidelines for running and interpreting test coverage in Dart/Flutter packages.

## When to use this skill
- When asked to "check test coverage" or "improve coverage".
- When you need to identify which parts of a library are untested.

## Workflow
1. Ensure tests pass: `dart test` (or `flutter test` for the mobile app).
2. Collect coverage:
   ```bash
   # Pure Dart
   dart test --coverage=.dart_tool/coverage
   # Flutter (produces coverage/lcov.info)
   flutter test --coverage
   ```
3. Interpret the results.
4. Add tests to cover missed lines.

> [!TIP]
> For complex conditional logic, pass `--branch-coverage` to `dart test`.

## Interpreting Results

### Flutter (lcov)
```bash
# Summary (requires lcov)
lcov --summary coverage/lcov.info
# Per-file detail
lcov --list coverage/lcov.info
# HTML report
genhtml coverage/lcov.info -o coverage/html
```

### Pure Dart (package:coverage)
```bash
dart run coverage:format_coverage --in=.dart_tool/coverage --out=stdout --pretty-print --report-on=lib
```
Outputs file content with hit counts on the left (`0|` = missed line).

## Best Practices for Reporting Results
1. **State the high-level percentage first** for immediate context.
2. **Identify specific files and missed lines** clearly.
3. **Translate line numbers to code**: don't just say "lines 3-6 are missed" — name the untested functions or blocks.
4. **Propose concrete fixes**: provide example test code that covers the missed lines.
5. **Use tables for multi-file summaries**: File | Coverage % | Missed Lines.

## Constraints
- ALWAYS verify that tests pass before collecting coverage.
- DO NOT commit `.dart_tool/coverage` or regenerate `coverage/` artifacts unnecessarily.
- Focus coverage improvements on `lib/` files, not `test/` or generated files (`*.g.dart`, `*.freezed.dart`).

---

*Source: [kevmoo/dash_skills](https://github.com/kevmoo/dash_skills) (Apache-2.0); upstream helper script replaced with lcov/format_coverage commands, Flutter notes added.*
