"""Custom matières endpoints — school-defined (non-official) subjects.

Official matières come from code (`/curriculum`). These let a school's admin add
their own (e.g. "Chant", "Théâtre", "Échecs") — as many as they want. The slug
`code` is what gets stored in a content/quiz `subject`; `title` is the display
name the user typed.

  GET    /custom-subjects            — list this school's active custom matières
  POST   /custom-subjects            — add one (ADM/DIR)
  DELETE /custom-subjects/{id}       — deactivate one (ADM/DIR)
"""

from __future__ import annotations

import re
import unicodedata
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, get_current_user, requires_role
from app.core.permissions import ADM
from app.core.response import success_response
from app.models.curriculum import is_official_subject
from app.models.custom_subject import CustomSubject

router = APIRouter(prefix="/custom-subjects", tags=["Curriculum"])


class CustomSubjectCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)  # canonical/fallback (FR)
    title_ar: str | None = Field(None, max_length=120)  # optional Arabic name
    title_en: str | None = Field(None, max_length=120)  # optional English name
    code: str | None = Field(None, max_length=50)  # optional explicit slug
    cycle: str | None = Field(None, max_length=20)
    level_band: str | None = Field(None, max_length=50)


def _slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower()
    return value[:50] or "matiere"


def _serialize(cs: CustomSubject) -> dict:
    return {
        "id": str(cs.id),
        "code": cs.code,
        "title": cs.title,  # canonical/fallback (back-compat)
        "titles": cs.titles(),  # resolved {fr, ar, en}
        "cycle": cs.cycle,
        "level_band": cs.level_band,
        "is_active": cs.is_active,
        "official": False,
    }


@router.get("", summary="List this school's custom matières")
async def list_custom_subjects(
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (
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
    return success_response([_serialize(r) for r in rows])


@router.post("", status_code=201, summary="Add a custom matière (ADM/DIR)")
async def create_custom_subject(
    body: CustomSubjectCreateRequest,
    auth: AuthContext = Depends(requires_role(ADM)),
    db: AsyncSession = Depends(get_db),
):
    code = _slugify(body.code or body.title)
    if is_official_subject(code):
        raise HTTPException(
            status_code=409,
            detail=f"'{code}' is an official matière; pick a different name.",
        )
    exists = (
        await db.execute(
            select(CustomSubject.id).where(
                CustomSubject.school_id == auth.school_id,
                CustomSubject.code == code,
            )
        )
    ).scalar_one_or_none()
    if exists is not None:
        raise HTTPException(status_code=409, detail=f"Custom matière '{code}' already exists.")

    # Trilingual title: canonical FR + optional AR/EN overrides in translations.
    title_map: dict[str, str] = {"fr": body.title.strip()}
    if body.title_ar and body.title_ar.strip():
        title_map["ar"] = body.title_ar.strip()
    if body.title_en and body.title_en.strip():
        title_map["en"] = body.title_en.strip()

    cs = CustomSubject(
        school_id=auth.school_id,
        code=code,
        title=body.title.strip(),
        translations={"title": title_map},
        cycle=body.cycle,
        level_band=body.level_band,
        created_by=auth.user_id,
        is_active=True,
    )
    db.add(cs)
    await db.commit()
    await db.refresh(cs)
    return success_response(_serialize(cs))


@router.delete("/{subject_id}", summary="Deactivate a custom matière (ADM/DIR)")
async def deactivate_custom_subject(
    subject_id: uuid.UUID,
    auth: AuthContext = Depends(requires_role(ADM)),
    db: AsyncSession = Depends(get_db),
):
    cs = (
        await db.execute(
            select(CustomSubject).where(
                CustomSubject.id == subject_id,
                CustomSubject.school_id == auth.school_id,
            )
        )
    ).scalar_one_or_none()
    if cs is None:
        raise HTTPException(status_code=404, detail="Custom matière not found")
    cs.is_active = False
    await db.commit()
    return success_response({"id": str(subject_id), "is_active": False})
