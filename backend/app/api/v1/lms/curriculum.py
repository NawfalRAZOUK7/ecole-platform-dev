"""Curriculum endpoints — official Cycle → Niveau → Matière → Topics tree.

Read-only. The structure is the backend source of truth
(``app/models/curriculum.py``), so the frontend derives the official curriculum
from here instead of hardcoding it. Scope: PRIVATE sector, préscolaire + primaire.

  GET /curriculum                                  — full tree
  GET /curriculum/cycles                           — cycles + their niveaux
  GET /curriculum/levels/{level}/matieres          — matières at a niveau
  GET /curriculum/levels/{level}/matieres/{subject}/topics — topics (sujets)
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, get_current_user
from app.core.response import success_response
from app.models import curriculum as cur
from app.models.custom_subject import CustomSubject
from app.models.erp import Class

router = APIRouter(prefix="/curriculum", tags=["Curriculum"])


@router.get("", summary="Full curriculum tree (cycle → level → matière → topics)")
async def get_curriculum(_: AuthContext = Depends(get_current_user)):
    return success_response({"sector": cur.SchoolSector.PRIVATE.value, "cycles": cur.curriculum_tree()})


@router.get("/cycles", summary="Cycles and their niveaux")
async def get_cycles(_: AuthContext = Depends(get_current_user)):
    return success_response(
        [
            {"cycle": cycle, "levels": list(levels)}
            for cycle, levels in cur.LEVELS_BY_CYCLE.items()
        ]
    )


@router.get("/levels/{level}/matieres", summary="Matières offered at a niveau")
async def get_level_matieres(level: str, _: AuthContext = Depends(get_current_user)):
    if cur.cycle_for_level(level) is None:
        raise HTTPException(status_code=404, detail=f"Unknown or out-of-scope level '{level}'")
    return success_response(
        {
            "level": level,
            "cycle": cur.cycle_for_level(level),
            "matieres": [
                {"subject": s, "topics": list(cur.topics_for(level, s))}
                for s in cur.matieres_for_level(level)
            ],
        }
    )


@router.get(
    "/class/{class_id}/matieres",
    summary="Matières for a class (official for its niveau + the school's custom)",
)
async def get_class_matieres(
    class_id: uuid.UUID,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Class → matières: official matières for the class's niveau, plus the
    school's active custom matières scoped to that niveau/cycle (or global)."""
    cls = (
        await db.execute(
            select(Class).where(
                Class.id == class_id, Class.school_id == auth.school_id
            )
        )
    ).scalar_one_or_none()
    if cls is None:
        raise HTTPException(status_code=404, detail="Class not found")

    level = cls.level_band
    matieres: list[dict] = []
    if level and cur.cycle_for_level(level) is not None:
        matieres = [
            {
                "subject": s,
                "title": cur.SUBJECT_TITLES.get(s, {}),
                "topics": list(cur.topics_for(level, s)),
                "official": True,
            }
            for s in cur.matieres_for_level(level)
        ]

    customs = (
        (
            await db.execute(
                select(CustomSubject).where(
                    CustomSubject.school_id == auth.school_id,
                    CustomSubject.is_active.is_(True),
                )
            )
        )
        .scalars()
        .all()
    )
    matieres += [
        {"subject": c.code, "title": c.titles(), "topics": [], "official": False}
        for c in customs
        if c.level_band in (None, level) and c.cycle in (None, cls.cycle)
    ]

    return success_response(
        {
            "class_id": str(class_id),
            "level_band": level,
            "cycle": cls.cycle,
            "matieres": matieres,
        }
    )


@router.get(
    "/levels/{level}/matieres/{subject}/topics",
    summary="Topics (sujets) for a matière at a niveau",
)
async def get_topics(level: str, subject: str, _: AuthContext = Depends(get_current_user)):
    if not cur.is_subject_valid_for_level(subject, level):
        raise HTTPException(
            status_code=404,
            detail=f"Matière '{subject}' is not offered at level '{level}'",
        )
    return success_response(
        {"level": level, "subject": subject, "topics": list(cur.topics_for(level, subject))}
    )
