"""Level-age mapping endpoints — G46.

GET  /levels         — List all level-age mappings (ordered by display_order)
PUT  /levels/{code}  — Update a mapping (admin/director/supervisor/system only)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, get_current_user, requires_role
from app.core.permissions import ADM, DIR, SUP, SYS
from app.core.response import success_response
from app.models.levels import LevelAgeMapping
from app.schemas.lms.levels import LevelAgeMappingResponse, LevelAgeMappingUpdateRequest

router = APIRouter(prefix="/levels", tags=["Levels"])


def _serialize(mapping: LevelAgeMapping) -> LevelAgeMappingResponse:
    return LevelAgeMappingResponse(
        id=str(mapping.id),
        level_code=mapping.level_code,
        label_fr=mapping.label_fr,
        label_ar=mapping.label_ar,
        label_en=mapping.label_en,
        default_age_min=mapping.default_age_min,
        default_age_max=mapping.default_age_max,
        display_order=mapping.display_order,
        school_id=str(mapping.school_id) if mapping.school_id else None,
    )


@router.get("", summary="List level-age mappings")
async def list_level_age_mappings(
    school_id: uuid.UUID | None = Query(
        None,
        description="If provided, merge school-specific overrides with platform defaults.",
    ),
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return all level-age mappings ordered by display_order.

    If school_id is provided, school-specific overrides take precedence over
    the platform defaults for that level_code.
    """
    # Fetch platform defaults
    stmt = (
        select(LevelAgeMapping)
        .where(LevelAgeMapping.school_id.is_(None))
        .order_by(LevelAgeMapping.display_order)
    )
    result = await db.execute(stmt)
    platform_rows = list(result.scalars().all())

    if school_id is None:
        items = [_serialize(row) for row in platform_rows]
        return success_response(items)

    # Fetch school overrides
    stmt_school = select(LevelAgeMapping).where(LevelAgeMapping.school_id == school_id)
    result_school = await db.execute(stmt_school)
    school_rows = {row.level_code: row for row in result_school.scalars().all()}

    # Merge: school override wins over platform default
    merged = []
    for platform_row in platform_rows:
        effective = school_rows.get(platform_row.level_code, platform_row)
        merged.append(_serialize(effective))

    return success_response(merged)


@router.put("/{level_code}", summary="Update a level-age mapping")
async def update_level_age_mapping(
    level_code: str,
    body: LevelAgeMappingUpdateRequest,
    school_id: uuid.UUID | None = Query(
        None,
        description="If provided, creates/updates a school-specific override.",
    ),
    auth: AuthContext = Depends(requires_role(ADM, DIR, SUP, SYS)),
    db: AsyncSession = Depends(get_db),
):
    """Update (or create) a level-age mapping.

    Without school_id: updates the platform default (SUP/SYS only).
    With school_id: creates/updates a school override (ADM/DIR for their school).
    """
    if school_id is None:
        # Platform-wide update — require SUP or SYS
        if auth.role not in (SUP, SYS):
            raise HTTPException(
                status_code=403,
                detail="Only platform admins (SUP/SYS) can update platform-wide level mappings.",
            )
        stmt = select(LevelAgeMapping).where(
            LevelAgeMapping.level_code == level_code,
            LevelAgeMapping.school_id.is_(None),
        )
    else:
        stmt = select(LevelAgeMapping).where(
            LevelAgeMapping.level_code == level_code,
            LevelAgeMapping.school_id == school_id,
        )

    result = await db.execute(stmt)
    mapping = result.scalar_one_or_none()

    if mapping is None:
        if school_id is None:
            raise HTTPException(
                status_code=404, detail=f"Level '{level_code}' not found."
            )
        # Create a school override by copying the platform default first
        default_stmt = select(LevelAgeMapping).where(
            LevelAgeMapping.level_code == level_code,
            LevelAgeMapping.school_id.is_(None),
        )
        default_result = await db.execute(default_stmt)
        default = default_result.scalar_one_or_none()
        if default is None:
            raise HTTPException(
                status_code=404, detail=f"Level '{level_code}' not found."
            )
        mapping = LevelAgeMapping(
            level_code=level_code,
            label_fr=default.label_fr,
            label_ar=default.label_ar,
            label_en=default.label_en,
            default_age_min=default.default_age_min,
            default_age_max=default.default_age_max,
            display_order=default.display_order,
            school_id=school_id,
        )
        db.add(mapping)

    if body.label_fr is not None:
        mapping.label_fr = body.label_fr
    if body.label_ar is not None:
        mapping.label_ar = body.label_ar
    if body.label_en is not None:
        mapping.label_en = body.label_en
    if body.default_age_min is not None:
        mapping.default_age_min = body.default_age_min
    if body.default_age_max is not None:
        mapping.default_age_max = body.default_age_max

    mapping.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(mapping)
    return success_response(_serialize(mapping))
