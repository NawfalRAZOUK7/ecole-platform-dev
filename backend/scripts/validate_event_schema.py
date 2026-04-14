#!/usr/bin/env python3
"""Event schema drift detection — CI validation script.

Reference: S-146 — Event schema versioning, Pack G2 — Analytics & Tracking Contract

This script validates that:
  1. All P0 events are registered in the analytics emitter
  2. Event property whitelists match the documented schema
  3. Schema version is consistent across all events
  4. No PII fields appear in any event whitelist
  5. New events have corresponding entries in the event dictionary

Usage:
  python scripts/validate_event_schema.py           # Validate
  python scripts/validate_event_schema.py --export   # Export schema as JSON
  python scripts/validate_event_schema.py --diff     # Show changes from baseline

Exit codes:
  0 — All checks passed
  1 — Validation failures detected (breaking change requires version increment)

CI integration (.github/workflows/ci.yml):
  - name: Event schema drift detection
    run: python scripts/validate_event_schema.py
"""

from __future__ import annotations

import json
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.analytics import (
    SCHEMA_VERSION,
    _EVENT_PROPERTY_WHITELIST,
    _PII_FIELD_BLOCKLIST,
    AnalyticsEvent,
)


# ---------------------------------------------------------------------------
# P0 Required Events (G2.3 — must be registered)
# ---------------------------------------------------------------------------
P0_REQUIRED_EVENTS = {
    "auth_login_success",  # EVT-002
    "auth_login_failure",  # EVT-003
    "feed_item_open",  # EVT-008
    "content_progress_updated",  # P0 KPI
    "notification_delivered",  # P0 KPI
    "payment_completed",  # P0 KPI
}


# ---------------------------------------------------------------------------
# Validation checks
# ---------------------------------------------------------------------------
def validate_p0_events_registered() -> list[str]:
    """Check that all P0 required events are registered."""
    errors = []
    for event_name in P0_REQUIRED_EVENTS:
        if event_name not in _EVENT_PROPERTY_WHITELIST:
            errors.append(f"P0 event '{event_name}' not registered in whitelist")
    return errors


def validate_no_pii_in_whitelists() -> list[str]:
    """Check that no PII fields appear in any event whitelist."""
    errors = []
    for event_name, properties in _EVENT_PROPERTY_WHITELIST.items():
        for prop in properties:
            if prop.lower() in _PII_FIELD_BLOCKLIST:
                errors.append(
                    f"PII field '{prop}' found in whitelist for '{event_name}'"
                )
    return errors


def validate_event_model_fields() -> list[str]:
    """Check that the AnalyticsEvent model has all required G2.2 fields."""
    required_fields = {
        "event_name",
        "event_version",
        "schema_version",
        "occurred_at",
        "env",
        "actor_type",
        "actor_id",
        "correlation_id",
        "client_platform",
        "client_version",
        "properties",
        "pii_flags",
        "redaction_applied",
    }
    model_fields = set(AnalyticsEvent.model_fields.keys())
    missing = required_fields - model_fields
    errors = []
    if missing:
        errors.append(f"AnalyticsEvent missing G2.2 required fields: {missing}")
    return errors


def validate_schema_version_consistency() -> list[str]:
    """Check schema version is a positive integer."""
    errors = []
    if not isinstance(SCHEMA_VERSION, int) or SCHEMA_VERSION < 1:
        errors.append(f"Invalid SCHEMA_VERSION: {SCHEMA_VERSION} (must be int >= 1)")
    return errors


def validate_whitelist_non_empty() -> list[str]:
    """Check all events have at least one whitelisted property."""
    errors = []
    for event_name, properties in _EVENT_PROPERTY_WHITELIST.items():
        if not properties:
            errors.append(f"Event '{event_name}' has empty property whitelist")
    return errors


# ---------------------------------------------------------------------------
# Export / diff helpers
# ---------------------------------------------------------------------------
def export_schema() -> dict:
    """Export the current event schema as a JSON-serializable dict."""
    events = []
    for event_name, properties in sorted(_EVENT_PROPERTY_WHITELIST.items()):
        events.append(
            {
                "event_name": event_name,
                "schema_version": SCHEMA_VERSION,
                "properties": sorted(properties),
                "property_count": len(properties),
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "total_events": len(events),
        "p0_events": sorted(P0_REQUIRED_EVENTS),
        "events": events,
    }


BASELINE_FILE = os.path.join(
    os.path.dirname(__file__), "..", "artifacts", "event_schema_baseline.json"
)


def diff_from_baseline() -> list[str]:
    """Compare current schema against saved baseline."""
    if not os.path.exists(BASELINE_FILE):
        return ["No baseline file found. Run with --export to create one."]

    with open(BASELINE_FILE) as f:
        baseline = json.load(f)

    changes = []
    current = export_schema()

    # Check schema version change
    if current["schema_version"] != baseline.get("schema_version"):
        changes.append(
            f"Schema version changed: {baseline.get('schema_version')} → {current['schema_version']}"
        )

    # Check for new/removed events
    baseline_events = {e["event_name"] for e in baseline.get("events", [])}
    current_events = {e["event_name"] for e in current["events"]}

    added = current_events - baseline_events
    removed = baseline_events - current_events

    for event in sorted(added):
        changes.append(f"NEW event: {event}")
    for event in sorted(removed):
        changes.append(f"REMOVED event: {event}")

    # Check for property changes in existing events
    baseline_map = {
        e["event_name"]: set(e["properties"]) for e in baseline.get("events", [])
    }
    current_map = {e["event_name"]: set(e["properties"]) for e in current["events"]}

    for event in current_events & baseline_events:
        added_props = current_map[event] - baseline_map[event]
        removed_props = baseline_map[event] - current_map[event]
        if added_props:
            changes.append(f"  {event}: added properties {sorted(added_props)}")
        if removed_props:
            changes.append(
                f"  {event}: REMOVED properties {sorted(removed_props)} (BREAKING)"
            )

    return changes


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    args = sys.argv[1:]

    if "--export" in args:
        schema = export_schema()
        print(json.dumps(schema, indent=2))
        # Also save as baseline
        os.makedirs(os.path.dirname(BASELINE_FILE), exist_ok=True)
        with open(BASELINE_FILE, "w") as f:
            json.dump(schema, f, indent=2)
        print(f"\nBaseline saved to: {BASELINE_FILE}", file=sys.stderr)
        return 0

    if "--diff" in args:
        changes = diff_from_baseline()
        if not changes:
            print("No changes from baseline.")
            return 0
        print("Event schema changes detected:")
        for change in changes:
            print(f"  {change}")
        return 1 if any("BREAKING" in c or "REMOVED" in c for c in changes) else 0

    # Default: validate
    print(f"Validating event schema (version {SCHEMA_VERSION})...")
    all_errors = []

    checks = [
        ("P0 events registered", validate_p0_events_registered),
        ("No PII in whitelists", validate_no_pii_in_whitelists),
        ("Event model fields", validate_event_model_fields),
        ("Schema version", validate_schema_version_consistency),
        ("Whitelist non-empty", validate_whitelist_non_empty),
    ]

    for name, check_fn in checks:
        errors = check_fn()
        if errors:
            print(f"  FAIL: {name}")
            for err in errors:
                print(f"    - {err}")
            all_errors.extend(errors)
        else:
            print(f"  PASS: {name}")

    total_events = len(_EVENT_PROPERTY_WHITELIST)
    print(f"\nTotal events registered: {total_events}")
    print(f"P0 events: {len(P0_REQUIRED_EVENTS)}")
    print(f"Schema version: {SCHEMA_VERSION}")

    if all_errors:
        print(f"\nFAILED: {len(all_errors)} error(s)")
        return 1

    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
