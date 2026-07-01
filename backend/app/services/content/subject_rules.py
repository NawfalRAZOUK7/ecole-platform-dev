"""Service-layer matière (subject) validation.

Because ``subject`` is a free ``String`` (to allow custom matières), the request
schemas can only do shape checks. This is the authoritative rule, run in the
service layer where the DB + school are available:

  * official matière (``curriculum``)  → allowed; if a level is given it must be
    taught at that level;
  * **custom** matière → allowed **only** for school-scoped content and only if
    it's a *registered, active* ``CustomSubject`` for that school;
  * platform content (``school_id is None``) → official matières only.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.models.curriculum import (
    is_official_subject,
    is_subject_valid_for_level,
    matieres_for_level,
)
from app.models.taxonomy import CONTENT_SUBJECTS, ContentSubject

_OTHER = ContentSubject.OTHER.value


async def validate_subject(
    db: AsyncSession,
    *,
    school_id: uuid.UUID | None,
    subject: str | None,
    level_band: str | None = None,
    subject_other: str | None = None,
) -> None:
    """Raise ``ValidationError`` if ``subject`` is not valid for the school/level.

    ``subject`` is a closed enum (``content_subject_enum``) that includes
    ``other``. A school-specific matière uses ``subject = 'other'`` + a free-text
    ``subject_other`` name. Platform content (``school_id is None``) may not use
    ``other``.
    """
    if not subject:
        return

    if subject == _OTHER:
        if school_id is None:
            raise ValidationError(
                "platform content cannot use a custom ('other') matière",
                error_code="ERR-CMS-422",
            )
        if not (subject_other and subject_other.strip()):
            raise ValidationError(
                "subject 'other' requires 'subject_other' (the matière name)",
                error_code="ERR-CMS-422",
            )
        return

    if subject not in CONTENT_SUBJECTS:
        raise ValidationError(
            f"'{subject}' is not a valid matière (use 'other' + subject_other "
            "for a school-specific one)",
            error_code="ERR-CMS-422",
        )

    # Official matière: if a level is given it must be taught at that level.
    if (
        is_official_subject(subject)
        and level_band
        and not is_subject_valid_for_level(subject, level_band)
    ):
        allowed = ", ".join(matieres_for_level(level_band)) or "(none)"
        raise ValidationError(
            f"subject '{subject}' is not taught at level '{level_band}'. "
            f"Allowed matières: {allowed}",
            error_code="ERR-CMS-422",
        )
