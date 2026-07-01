"""Custom (non-official) matières — the open tail of the subject taxonomy.

Official matières live in **code** (``curriculum.SUBJECT_TITLES`` /
``ContentSubject``). This table holds the matières a school's privileged role
adds that are NOT in the official MEN list — e.g. "Chant", "Théâtre", "Échecs".
A school may add as many as it wants.

``code`` is a slug (unique per school) actually stored in a content/quiz
``subject`` column; ``title`` is the human name the user typed. Because custom
codes are open, the ``subject`` columns are validated ``String`` (not a native
enum) — see migration ``20260628_custom_subjects``.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import (
    Base,
    SchoolScopedMixin,
    TimestampMixin,
    TranslatableMixin,
)


class CustomSubject(TimestampMixin, SchoolScopedMixin, TranslatableMixin, Base):
    """A school-defined matière. Scoped to one school; optionally to a cycle/level.

    Trilingual like the official matières: ``title`` is the canonical/fallback
    name (typically French) and ``translations`` (from ``TranslatableMixin``)
    holds per-locale overrides, shape ``{"title": {"fr": ..., "ar": ..., "en": ...}}``.
    Read localized names with :meth:`titles` / ``tr("title", locale)``.
    """

    __tablename__ = "custom_subjects"

    # Slug stored in content.subject (e.g. "chant"). Unique per school.
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    # Canonical/fallback display name (e.g. "Chant"). Localized via translations.
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    # Optional scope — null means "available at any niveau of this school".
    cycle: Mapped[str | None] = mapped_column(String(20), nullable=True)
    level_band: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint("school_id", "code", name="uq_custom_subjects_school_code"),
    )

    def titles(self, default_locale: str = "fr") -> dict[str, str]:
        """Resolved {fr, ar, en} display names.

        A per-locale ``translations['title']`` entry wins; otherwise falls back to
        the canonical ``title`` (so a partially-translated row still renders).
        """
        return {
            loc: (self.tr("title", loc, default_locale) or self.title)
            for loc in ("fr", "ar", "en")
        }
