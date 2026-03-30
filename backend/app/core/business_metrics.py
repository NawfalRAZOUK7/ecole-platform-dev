"""Education-specific Prometheus metrics."""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

from app.core.metrics import REGISTRY

active_students = Gauge(
    "ecole_active_students_total",
    "Currently active students",
    ["school_id"],
    registry=REGISTRY,
)

assignment_submissions = Counter(
    "ecole_assignment_submissions_total",
    "Total assignment submissions",
    ["school_id", "status"],
    registry=REGISTRY,
)

grade_distribution = Histogram(
    "ecole_grade_value",
    "Grade distribution on the Moroccan 0-20 scale",
    ["school_id", "subject"],
    buckets=(0, 4, 8, 10, 12, 14, 16, 18, 20),
    registry=REGISTRY,
)

attendance_rate = Gauge(
    "ecole_attendance_rate",
    "Attendance rate by school",
    ["school_id"],
    registry=REGISTRY,
)

billing_collection = Counter(
    "ecole_billing_payments_total",
    "Billing payment events",
    ["school_id", "status"],
    registry=REGISTRY,
)

billing_revenue = Counter(
    "ecole_billing_revenue_mad",
    "Collected revenue in MAD",
    ["school_id", "plan"],
    registry=REGISTRY,
)

timetable_generation = Histogram(
    "ecole_timetable_generation_seconds",
    "Timetable generation duration in seconds",
    ["school_id"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
    registry=REGISTRY,
)
