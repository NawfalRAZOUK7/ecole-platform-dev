"""Life-skills passport API endpoints."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.permissions import (
    PERM_SKILL_DIMENSION_MANAGE,
    PERM_SKILL_DIMENSION_READ,
    PERM_SKILL_MILESTONE_MANAGE,
    PERM_SKILL_MILESTONE_READ,
    PERM_SKILL_PASSPORT_GENERATE,
    PERM_SKILL_PASSPORT_READ,
    PERM_SKILL_PROGRESS_EVALUATE,
    PERM_SKILL_PROGRESS_READ,
)
from app.core.request_utils import get_client_ip
from app.core.response import list_response, success_response
from app.schemas.skill_passport import (
    SkillDimensionCreateRequest,
    SkillMilestoneCreateRequest,
)
from app.services.skill_passport_service import SkillPassportService

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get(
    "/dimensions",
    summary="List skill dimensions",
    response_description="List of skill dimensions",
)
async def list_skill_dimensions(
    is_active: bool | None = Query(None),
    auth: AuthContext = Depends(requires_permission(PERM_SKILL_DIMENSION_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List active and inactive life-skill dimensions."""
    service = SkillPassportService(db)
    return list_response(await service.list_dimensions(is_active=is_active))


@router.post(
    "/dimensions",
    status_code=201,
    summary="Create skill dimension",
    response_description="Created skill dimension",
)
async def create_skill_dimension(
    body: SkillDimensionCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_SKILL_DIMENSION_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a life-skill dimension."""
    service = SkillPassportService(db)
    return success_response(
        await service.create_dimension(
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "/milestones",
    summary="List skill milestones",
    response_description="List of skill milestones",
)
async def list_skill_milestones(
    dimension_id: uuid.UUID | None = Query(None),
    is_active: bool | None = Query(None),
    auth: AuthContext = Depends(requires_permission(PERM_SKILL_MILESTONE_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List milestones defined for the skill framework."""
    service = SkillPassportService(db)
    return list_response(
        await service.list_milestones(
            dimension_id=dimension_id,
            is_active=is_active,
        )
    )


@router.post(
    "/milestones",
    status_code=201,
    summary="Create skill milestone",
    response_description="Created skill milestone",
)
async def create_skill_milestone(
    body: SkillMilestoneCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_SKILL_MILESTONE_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a life-skill milestone."""
    service = SkillPassportService(db)
    return success_response(
        await service.create_milestone(
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "/progress/student/{student_id}",
    summary="Get student skill progress",
    response_description="Student skill progress detail",
)
async def get_student_skill_progress(
    student_id: uuid.UUID,
    academic_year_id: uuid.UUID = Query(...),
    auth: AuthContext = Depends(requires_permission(PERM_SKILL_PROGRESS_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Return skill progress records for one student."""
    service = SkillPassportService(db)
    return list_response(
        await service.get_student_progress(
            student_id=student_id,
            academic_year_id=academic_year_id,
            auth=auth,
        )
    )


@router.post(
    "/evaluate/{student_id}",
    summary="Evaluate student life skills",
    response_description="Evaluation result",
)
async def evaluate_student_skills(
    student_id: uuid.UUID,
    request: Request,
    academic_year_id: uuid.UUID = Query(...),
    auth: AuthContext = Depends(requires_permission(PERM_SKILL_PROGRESS_EVALUATE)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Evaluate a student's life-skill milestones."""
    service = SkillPassportService(db)
    return success_response(
        await service.evaluate_student(
            student_id=student_id,
            academic_year_id=academic_year_id,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "/passport/{student_id}",
    summary="Get student skill passport",
    response_description="Skill passport detail",
)
async def get_skill_passport(
    student_id: uuid.UUID,
    academic_year_id: uuid.UUID = Query(...),
    auth: AuthContext = Depends(requires_permission(PERM_SKILL_PASSPORT_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Fetch the generated skill passport for a student."""
    service = SkillPassportService(db)
    return success_response(
        await service.get_passport(
            student_id=student_id,
            academic_year_id=academic_year_id,
            auth=auth,
        )
    )


@router.post(
    "/passport/{student_id}/generate",
    summary="Generate student skill passport",
    response_description="Generated skill passport",
)
async def generate_skill_passport(
    student_id: uuid.UUID,
    request: Request,
    academic_year_id: uuid.UUID = Query(...),
    auth: AuthContext = Depends(requires_permission(PERM_SKILL_PASSPORT_GENERATE)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Generate a skill passport for a student."""
    service = SkillPassportService(db)
    return success_response(
        await service.generate_passport(
            student_id=student_id,
            academic_year_id=academic_year_id,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "/passport/{student_id}/download",
    summary="Download student skill passport PDF",
    response_description="PDF bytes",
)
async def download_skill_passport(
    student_id: uuid.UUID,
    academic_year_id: uuid.UUID = Query(...),
    auth: AuthContext = Depends(requires_permission(PERM_SKILL_PASSPORT_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Download the student's skill passport PDF."""
    service = SkillPassportService(db)
    passport = await service.get_passport(
        student_id=student_id,
        academic_year_id=academic_year_id,
        auth=auth,
    )
    pdf_bytes = await service.download_pdf(
        passport_id=uuid.UUID(passport["id"]),
        auth=auth,
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="skill-passport-{student_id}-{academic_year_id}.pdf"'
            )
        },
    )


@router.get(
    "/analytics/class/{class_id}",
    summary="Get class life-skills analytics",
    response_description="Class analytics summary",
)
async def get_skill_class_analytics(
    class_id: uuid.UUID,
    academic_year_id: uuid.UUID = Query(...),
    auth: AuthContext = Depends(requires_permission(PERM_SKILL_PROGRESS_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Return class-level life-skill analytics."""
    service = SkillPassportService(db)
    return success_response(
        await service.class_analytics(
            class_id=class_id,
            academic_year_id=academic_year_id,
            auth=auth,
        )
    )


@router.get(
    "/analytics/school",
    summary="Get school life-skills analytics",
    response_description="School analytics summary",
)
async def get_skill_school_analytics(
    academic_year_id: uuid.UUID = Query(...),
    auth: AuthContext = Depends(requires_permission(PERM_SKILL_PROGRESS_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Return school-level life-skill analytics."""
    service = SkillPassportService(db)
    return success_response(
        await service.school_analytics(
            academic_year_id=academic_year_id,
            auth=auth,
        )
    )


@router.get(
    "/leaderboard/{class_id}",
    summary="Get anonymized class skill leaderboard",
    response_description="Anonymized leaderboard",
)
async def get_skill_leaderboard(
    class_id: uuid.UUID,
    academic_year_id: uuid.UUID = Query(...),
    limit: int = Query(10, ge=1, le=100),
    auth: AuthContext = Depends(requires_permission(PERM_SKILL_PROGRESS_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Return an anonymized skill leaderboard for a class."""
    service = SkillPassportService(db)
    return list_response(
        await service.leaderboard(
            class_id=class_id,
            academic_year_id=academic_year_id,
            auth=auth,
            limit=limit,
        )
    )
