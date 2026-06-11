"""Unit tests for app/core/business_metrics.py — ensures module-level metrics register."""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

import app.core.business_metrics as bm


def test_active_students_is_gauge():
    assert isinstance(bm.active_students, Gauge)


def test_assignment_submissions_is_counter():
    assert isinstance(bm.assignment_submissions, Counter)


def test_grade_distribution_is_histogram():
    assert isinstance(bm.grade_distribution, Histogram)


def test_attendance_rate_is_gauge():
    assert isinstance(bm.attendance_rate, Gauge)


def test_billing_collection_is_counter():
    assert isinstance(bm.billing_collection, Counter)


def test_billing_revenue_is_counter():
    assert isinstance(bm.billing_revenue, Counter)


def test_timetable_generation_is_histogram():
    assert isinstance(bm.timetable_generation, Histogram)


# ---------------------------------------------------------------------------
# Naming + labelling contract (dashboards/alerts depend on these)
# ---------------------------------------------------------------------------
_ALL_METRICS = {
    "active_students": "ecole_active_students",
    "assignment_submissions": "ecole_assignment_submissions",
    "grade_distribution": "ecole_grade_value",
    "attendance_rate": "ecole_attendance_rate",
    "billing_collection": "ecole_billing_payments",
    "billing_revenue": "ecole_billing_revenue_mad",
    "timetable_generation": "ecole_timetable_generation_seconds",
}


def test_metric_names_are_prefixed_with_ecole():
    for attr, expected_prefix in _ALL_METRICS.items():
        metric = getattr(bm, attr)
        assert metric._name.startswith("ecole_"), f"{attr} not ecole-prefixed"
        assert metric._name.startswith(expected_prefix), (
            f"{attr} name {metric._name!r} != expected {expected_prefix!r}"
        )


def test_every_metric_is_labelled_by_school_id():
    # Tenant attribution: every business metric must carry the school_id label.
    for attr in _ALL_METRICS:
        metric = getattr(bm, attr)
        assert "school_id" in metric._labelnames, f"{attr} missing school_id label"


def test_metric_names_are_unique():
    names = [getattr(bm, attr)._name for attr in _ALL_METRICS]
    assert len(names) == len(set(names))
