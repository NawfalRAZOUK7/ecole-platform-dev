"""Level-age mapping models — G46.

Maps academic level codes (cp, ce1, etc.) to default age ranges.
Platform defaults have school_id=NULL; school overrides have school_id set.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class LevelAgeMapping(Base):
    """Mapping from academic level code to a default age range.

    school_id=NULL rows are platform defaults.
    school_id=<uuid> rows are school-specific overrides.
    """

    __tablename__ = "level_age_mappings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    level_code: Mapped[str] = mapped_column(String(50), nullable=False)
    label_fr: Mapped[str] = mapped_column(String(100), nullable=False)
    label_ar: Mapped[str | None] = mapped_column(String(100), nullable=True)
    label_en: Mapped[str | None] = mapped_column(String(100), nullable=True)
    default_age_min: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    default_age_max: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    display_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    school_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
        nullable=True,
    )

    __table_args__ = (
        # Unique level_code per school. For school-specific rows (school_id IS NOT NULL),
        # the regular constraint handles it. For platform defaults (school_id IS NULL),
        # a partial unique index prevents duplicate platform defaults.
        UniqueConstraint(
            "level_code",
            "school_id",
            name="uq_level_age_mappings_code_school",
        ),
        # Partial unique index: only one platform default per level_code (school_id IS NULL)
        Index(
            "uq_level_age_mappings_code_platform",
            "level_code",
            unique=True,
            postgresql_where="school_id IS NULL",
        ),
        Index("ix_level_age_mappings_school_id", "school_id"),
        Index("ix_level_age_mappings_display_order", "display_order"),
    )

    def __repr__(self) -> str:
        return (
            f"<LevelAgeMapping level_code={self.level_code!r} "
            f"ages={self.default_age_min}-{self.default_age_max} "
            f"school_id={str(self.school_id)[:8] if self.school_id else 'platform'}>"
        )
