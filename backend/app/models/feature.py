"""Feature toggle model — Phase 11E.

Reference: Phase 11E — Feature Toggles for gradual rollout.
Table: feature_toggles — stores feature flags with school/role scoping.
"""

from __future__ import annotations

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin


class FeatureToggle(TimestampMixin, Base):
    """Feature toggle for gradual feature rollout.

    Scoping logic (evaluated in order):
    1. If enabled_globally is True → feature is ON for everyone.
    2. If school_id is in enabled_school_ids → ON for that school.
    3. If role_code is in enabled_role_codes → ON for that role.
    4. Otherwise → OFF.

    enabled_school_ids: JSON array of UUID strings, e.g. ["00000000-..."]
    enabled_role_codes: JSON array of role code strings, e.g. ["ADM", "TCH"]
    """

    __tablename__ = "feature_toggles"

    feature_key: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled_globally: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    enabled_school_ids: Mapped[list | None] = mapped_column(
        JSONB, nullable=True, server_default="[]"
    )
    enabled_role_codes: Mapped[list | None] = mapped_column(
        JSONB, nullable=True, server_default="[]"
    )
