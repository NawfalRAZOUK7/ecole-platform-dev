"""Student academic history endpoints — G49.

Routes:
  GET /students/{student_id}/program-history     — append-only event log
  GET /students/{student_id}/academic-timeline   — joined enrollment + program view
  GET /students/{student_id}/current-program     — latest active enrollment program

Authorization:
  - STD: own data only.
  - PAR: their linked children only (via parent_child_links).
  - ADM/DIR/TCH/SUP/SYS: school-scoped (school boundary check).
  Authorization is enforced inside ProgramService._authorize_student_read so
  every endpoint here behaves consistently.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import HTMLResponse

from app.core.database import get_db
from app.core.dependencies import AuthContext, get_current_user
from app.core.response import list_response, success_response
from app.services.program_service import ProgramService
from app.services.transcript_service import TranscriptService

router = APIRouter(prefix="/students", tags=["erp-academic-history"])


@router.get(
    "/{student_id}/program-history",
    summary="Student program history (append-only events, newest first)",
    response_description="List of ProgramAssignmentEvent rows",
)
async def get_program_history(
    student_id: uuid.UUID,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProgramService(db)
    items = await service.get_program_history(student_id=student_id, auth=auth)
    return list_response(items, next_cursor=None, has_more=False)


@router.get(
    "/{student_id}/academic-timeline",
    summary="Student academic timeline (per-period, oldest first)",
    response_description="Enrollment + class + period + program rows",
)
async def get_academic_timeline(
    student_id: uuid.UUID,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProgramService(db)
    items = await service.get_academic_timeline(
        student_id=student_id, auth=auth
    )
    return list_response(items, next_cursor=None, has_more=False)


@router.get(
    "/{student_id}/current-program",
    summary="Student's currently active program (most recent active enrollment)",
    response_description="Current program summary or null",
)
async def get_current_program(
    student_id: uuid.UUID,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProgramService(db)
    item = await service.get_current_program(
        student_id=student_id, auth=auth
    )
    return success_response(item)


@router.get(
    "/{student_id}/transcript",
    summary="Student transcript for an academic year",
    response_description="Live preview or latest snapshot transcript",
)
async def get_student_transcript(
    student_id: uuid.UUID,
    academic_year_id: uuid.UUID = Query(...),
    mode: str = Query(
        "preview",
        description="preview = live render, snapshot = latest frozen snapshot",
    ),
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TranscriptService(db)
    item = await service.get_student_transcript(
        student_id=student_id,
        academic_year_id=academic_year_id,
        mode=mode,
        auth=auth,
    )
    return success_response(item)


@router.get(
    "/{student_id}/transcript/html",
    summary="Student transcript HTML preview for an academic year",
    response_class=HTMLResponse,
)
async def get_student_transcript_html(
    student_id: uuid.UUID,
    academic_year_id: uuid.UUID = Query(...),
    mode: str = Query("preview"),
    lang: str = Query("fr"),
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TranscriptService(db)
    html = await service.render_student_transcript_html(
        student_id=student_id,
        academic_year_id=academic_year_id,
        mode=mode,
        auth=auth,
        lang=lang,
    )
    return HTMLResponse(content=html)


@router.get(
    "/{student_id}/transcript/pdf",
    summary="Student transcript PDF for an academic year",
)
async def get_student_transcript_pdf(
    student_id: uuid.UUID,
    academic_year_id: uuid.UUID = Query(...),
    mode: str = Query("preview"),
    lang: str = Query("fr"),
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TranscriptService(db)
    pdf_bytes = await service.download_student_transcript_pdf(
        student_id=student_id,
        academic_year_id=academic_year_id,
        mode=mode,
        auth=auth,
        lang=lang,
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="transcript-{student_id}-{academic_year_id}.pdf"'
            )
        },
    )
