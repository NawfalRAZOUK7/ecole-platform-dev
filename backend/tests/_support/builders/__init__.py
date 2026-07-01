"""Fluent test-data builders.

Usage::

    from tests._support.builders import AuthContextBuilder, SchoolApplicationBuilder
"""

from __future__ import annotations

from tests._support.builders.auth import AuthContextBuilder
from tests._support.builders.onboarding import SchoolApplicationBuilder

__all__ = ["AuthContextBuilder", "SchoolApplicationBuilder"]
