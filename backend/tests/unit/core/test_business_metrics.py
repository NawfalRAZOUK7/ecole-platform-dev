"""Unit tests for app/core/business_metrics.py — ensures module-level metrics register."""

from __future__ import annotations

import pytest
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
