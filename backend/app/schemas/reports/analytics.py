"""Phase 14 analytics schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ComparisonMetric(BaseModel):
    current: float = 0
    previous: float | None = None
    change_percent: float | None = None
    trend: str = "flat"


class OverviewMetric(BaseModel):
    key: str
    label: str
    value: ComparisonMetric


class TrendPoint(BaseModel):
    label: str
    value: float
    extra: dict[str, Any] = Field(default_factory=dict)


class HistogramBucket(BaseModel):
    label: str
    count: int


class FeatureAdoptionMetric(BaseModel):
    feature: str
    users: int
    adoption_rate: float
