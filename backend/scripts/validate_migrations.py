#!/usr/bin/env python3
"""Migration validation script — naming convention + integrity checks.

Reference: Phase 1A — Migration Hardening

This script validates that:
  1. Migration filenames follow the naming convention: {hash}_{group}_{description}.py
  2. Every migration has both upgrade() and downgrade() functions
  3. Migration revision chain is linear (no orphans, no forks)
  4. Raw SQL in migrations has explanatory comments

Usage:
  python scripts/validate_migrations.py           # Validate all
  python scripts/validate_migrations.py --verbose  # Show details

Exit codes:
  0 — All checks passed
  1 — Validation failures detected

CI integration (.github/workflows/ci.yml):
  - name: Migration validation
    run: python scripts/validate_migrations.py
"""

from __future__ import annotations

import ast
import os
import re
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

VERSIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "alembic", "versions")

# Expected filename pattern: {12-char-hex}_{group}_{description}.py
# Examples:
#   9f7257bc8dd1_g1_g6_initial_schema_iam_erp_lms_com_.py
#   a2f8b3c4d5e6_g7_ai_writing_attempts_preferences.py
#   b3c4d5e6f7a8_g8_parent_child_links_views_kpi.py
FILENAME_PATTERN = re.compile(r"^[0-9a-f]{12}_[a-z0-9][a-z0-9_]+\.py$")

# Known migration groups
VALID_GROUPS = {"g1", "g2", "g3", "g4", "g5", "g6", "g7", "g8", "g9", "g10"}


# ---------------------------------------------------------------------------
# Validation checks
# ---------------------------------------------------------------------------
def get_migration_files() -> list[str]:
    """Get all migration .py files (excluding __pycache__)."""
    if not os.path.isdir(VERSIONS_DIR):
        return []
    return sorted(
        f
        for f in os.listdir(VERSIONS_DIR)
        if f.endswith(".py") and not f.startswith("__")
    )


def validate_naming_convention(files: list[str]) -> list[str]:
    """Check that migration filenames follow the naming convention."""
    errors = []
    for filename in files:
        if not FILENAME_PATTERN.match(filename):
            errors.append(
                f"Naming: '{filename}' does not match pattern "
                "{{12-char-hex}}_{{group}}_{{description}}.py"
            )
    return errors


def validate_upgrade_downgrade(files: list[str]) -> list[str]:
    """Check that each migration has both upgrade() and downgrade() functions."""
    errors = []
    for filename in files:
        filepath = os.path.join(VERSIONS_DIR, filename)
        with open(filepath, "r") as f:
            source = f.read()

        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            errors.append(f"Syntax error in '{filename}': {e}")
            continue

        function_names = {
            node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
        }

        if "upgrade" not in function_names:
            errors.append(f"Missing upgrade() function in '{filename}'")
        if "downgrade" not in function_names:
            errors.append(f"Missing downgrade() function in '{filename}'")

    return errors


def validate_revision_chain(files: list[str]) -> list[str]:
    """Check that the revision chain is linear with no orphans or forks."""
    errors = []
    revisions = {}  # revision -> (down_revision, filename)

    for filename in files:
        filepath = os.path.join(VERSIONS_DIR, filename)
        with open(filepath, "r") as f:
            source = f.read()

        # Extract revision and down_revision
        rev_match = re.search(r'revision:\s*str\s*=\s*["\']([^"\']+)["\']', source)
        down_match = re.search(
            r'down_revision:\s*str\s*=\s*["\']([^"\']+)["\']', source
        )
        if not rev_match:
            errors.append(f"Cannot find 'revision' in '{filename}'")
            continue

        revision = rev_match.group(1)
        down_revision = down_match.group(1) if down_match else None

        if revision in revisions:
            errors.append(
                f"Duplicate revision '{revision}' in '{filename}' "
                f"and '{revisions[revision][1]}'"
            )

        revisions[revision] = (down_revision, filename)

    # Check chain integrity
    all_revisions = set(revisions.keys())
    all_down_revisions = {dr for dr, _ in revisions.values() if dr is not None}

    # Find head(s) — revisions not referenced as down_revision by any other
    heads = all_revisions - all_down_revisions
    if len(heads) > 1:
        errors.append(f"Multiple head revisions detected (fork): {heads}")
    elif len(heads) == 0 and len(revisions) > 0:
        errors.append("No head revision found (circular chain?)")

    # Find roots — migrations with down_revision = None
    roots = [rev for rev, (dr, _) in revisions.items() if dr is None]
    if len(roots) > 1:
        errors.append(f"Multiple root revisions detected: {roots}")
    elif len(roots) == 0 and len(revisions) > 0:
        errors.append("No root revision found (no migration with down_revision = None)")

    # Check for broken references
    for revision, (down_revision, filename) in revisions.items():
        if down_revision is not None and down_revision not in all_revisions:
            errors.append(
                f"Broken chain: '{filename}' references down_revision "
                f"'{down_revision}' which does not exist"
            )

    return errors


def validate_raw_sql_comments(files: list[str]) -> list[str]:
    """Check that raw SQL (op.execute) in migrations has comments nearby."""
    warnings = []
    for filename in files:
        filepath = os.path.join(VERSIONS_DIR, filename)
        with open(filepath, "r") as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            stripped = line.strip()
            if "op.execute(" in stripped:
                # Check if there's a comment within 3 lines above
                has_comment = False
                for j in range(max(0, i - 3), i + 1):
                    if "#" in lines[j] or '"""' in lines[j] or "'''" in lines[j]:
                        has_comment = True
                        break
                if not has_comment:
                    warnings.append(
                        f"Raw SQL at {filename}:{i+1} — consider adding a comment "
                        "explaining the purpose"
                    )

    return warnings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    verbose = "--verbose" in sys.argv

    files = get_migration_files()
    if not files:
        print("No migration files found.")
        return 0

    print(f"Validating {len(files)} migration file(s)...")

    all_errors = []
    all_warnings = []

    checks = [
        ("Naming convention", validate_naming_convention),
        ("upgrade/downgrade functions", validate_upgrade_downgrade),
        ("Revision chain integrity", validate_revision_chain),
    ]

    for name, check_fn in checks:
        errors = check_fn(files)
        if errors:
            print(f"  FAIL: {name}")
            for err in errors:
                print(f"    - {err}")
            all_errors.extend(errors)
        else:
            print(f"  PASS: {name}")

    # Raw SQL comments (warnings only, not failures)
    warnings = validate_raw_sql_comments(files)
    if warnings:
        print(f"  WARN: Raw SQL comments ({len(warnings)} warning(s))")
        if verbose:
            for w in warnings:
                print(f"    - {w}")
        all_warnings.extend(warnings)
    else:
        print("  PASS: Raw SQL comments")

    # Summary
    print(f"\nMigration files: {len(files)}")

    if verbose:
        print("\nRevision chain:")
        for filename in files:
            filepath = os.path.join(VERSIONS_DIR, filename)
            with open(filepath, "r") as f:
                source = f.read()
            rev_match = re.search(r'revision:\s*str\s*=\s*["\']([^"\']+)["\']', source)
            down_match = re.search(
                r'down_revision:\s*str\s*=\s*["\']([^"\']+)["\']', source
            )
            rev = rev_match.group(1) if rev_match else "?"
            down = down_match.group(1) if down_match else "None"
            print(f"  {down} -> {rev}  ({filename})")

    if all_errors:
        print(f"\nFAILED: {len(all_errors)} error(s)")
        return 1

    if all_warnings:
        print(f"\nPASSED with {len(all_warnings)} warning(s)")
    else:
        print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
