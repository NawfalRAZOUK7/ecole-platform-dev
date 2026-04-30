"""Program (filière) catalog + program assignment endpoints — G49.

Routes:
  GET    /programs                              — list active programs
  GET    /programs/{program_id}                 — get a single program
  POST   /programs                              — create program (ADM/DIR)
  PATCH  /programs/{program_id}                 — update program (ADM/DIR)
  POST   /enrollments/{enrollment_id}/program   — assign/change program

Permissions:
  PERM-ERP:program:read    — list/get (granted: STD, PAR, TCH, DIR, ADM)
  PERM-ERP:program:manage  — create/update (granted: ADM, DIR)
  PERM-ERP:enrollment:assign — assign program to enrollment (ADM)
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    AuthContext,
    requires_permission,
)
from app.core.permissions import (
    PERM_ERP_ENROLLMENT_ASSIGN,
    PERM_ERP_PROGRAM_MANAGE,
    PERM_ERP_PROGRAM_READ,
)
from app.core.request_utils import get_client_ip
from app.core.response import list_response, success_response
from app.schemas.programs import (
    ProgramAssignRequest,
    ProgramCreateRequest,
    ProgramEquivalenceCreateRequest,
    ProgramUpdateRequest,
    ProgramVersionCreateRequest,
    ProgramVersionUpdateRequest,
)
from app.services.program_service import ProgramService

programs_router = APIRouter(prefix="/programs", tags=["erp-programs"])
enrollment_program_router = APIRouter(
    prefix="/enrollments", tags=["erp-programs"]
)
program_equivalences_router = APIRouter(
    prefix="/program-equivalences", tags=["erp-programs"]
)


# ---------------------------------------------------------------------------
# Catalog — read
# ---------------------------------------------------------------------------
@programs_router.get(
    "",
    summary="List academic programs (filières) for the caller's school",
    response_description="Active programs (or all when active_only=false)",
)
async def list_programs(
    active_only: bool = Query(
        True,
        description="If true (default), only return programs with is_active = true.",
    ),
    auth: AuthContext = Depends(requires_permission(PERM_ERP_PROGRAM_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = ProgramService(db)
    items = await service.list_programs(auth=auth, active_only=active_only)
    return list_response(items, next_cursor=None, has_more=False)


@programs_router.get(
    "/{program_id}",
    summary="Get a single academic program",
    response_description="Program record",
)
async def get_program(
    program_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_ERP_PROGRAM_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = ProgramService(db)
    item = await service.get_program(program_id=program_id, auth=auth)
    return success_response(item)


# ---------------------------------------------------------------------------
# Catalog — write
# ---------------------------------------------------------------------------
@programs_router.post(
    "",
    status_code=201,
    summary="Create an academic program",
    response_description="Program record (idempotent on (school_id, code))",
)
async def create_program(
    body: ProgramCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_ERP_PROGRAM_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    service = ProgramService(db)
    item = await service.create_program(
        code=body.code,
        name=body.name,
        level=body.level,
        description=body.description,
        version_label=body.version_label,
        effective_from=body.effective_from,
        auth=auth,
        ip_address=get_client_ip(request),
    )
    return success_response(item)


# ---------------------------------------------------------------------------
# Program versions (Phase 3.1)
# ---------------------------------------------------------------------------
@programs_router.get(
    "/{program_id}/versions",
    summary="List versions for a program",
    response_description="Versions ordered: active first, newest effective_from first",
)
async def list_program_versions(
    program_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_ERP_PROGRAM_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = ProgramService(db)
    items = await service.list_program_versions(program_id=program_id, auth=auth)
    return list_response(items, next_cursor=None, has_more=False)


@programs_router.post(
    "/{program_id}/versions",
    status_code=201,
    summary="Create a version for a program (idempotent on (program, label))",
    response_description="ProgramVersion record",
)
async def create_program_version(
    program_id: uuid.UUID,
    body: ProgramVersionCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_ERP_PROGRAM_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    service = ProgramService(db)
    item = await service.create_program_version(
        program_id=program_id,
        version_label=body.version_label,
        description=body.description,
        effective_from=body.effective_from,
        is_active=body.is_active,
        auth=auth,
        ip_address=get_client_ip(request),
    )
    return success_response(item)


@programs_router.patch(
    "/{program_id}/versions/{version_id}",
    summary="Update a program version (description, dates, active flag)",
    response_description="Updated ProgramVersion record",
)
async def update_program_version(
    program_id: uuid.UUID,
    version_id: uuid.UUID,
    body: ProgramVersionUpdateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_ERP_PROGRAM_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    # program_id is part of the URL for clarity; the service validates the
    # version's school boundary independently.
    del program_id  # unused — version_id is the lookup key
    service = ProgramService(db)
    item = await service.update_program_version(
        version_id=version_id,
        description=body.description,
        effective_from=body.effective_from,
        retired_at=body.retired_at,
        is_active=body.is_active,
        auth=auth,
        ip_address=get_client_ip(request),
    )
    return success_response(item)


@programs_router.patch(
    "/{program_id}",
    summary="Update an academic program",
    response_description="Updated program record",
)
async def update_program(
    program_id: uuid.UUID,
    body: ProgramUpdateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_ERP_PROGRAM_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    service = ProgramService(db)
    item = await service.update_program(
        program_id=program_id,
        name=body.name,
        level=body.level,
        description=body.description,
        is_active=body.is_active,
        version_label=body.version_label,
        effective_from=body.effective_from,
        auth=auth,
        ip_address=get_client_ip(request),
    )
    return success_response(item)


# ---------------------------------------------------------------------------
# Program assignment to an enrollment
# ---------------------------------------------------------------------------
@enrollment_program_router.post(
    "/{enrollment_id}/program",
    status_code=201,
    summary="Assign or change the program (filière) for an enrollment",
    response_description="ProgramAssignmentEvent record (append-only audit row)",
)
async def assign_program(
    enrollment_id: uuid.UUID,
    body: ProgramAssignRequest,
    request: Request,
    auth: AuthContext = Depends(
        requires_permission(PERM_ERP_ENROLLMENT_ASSIGN)
    ),
    db: AsyncSession = Depends(get_db),
):
    """Assign a program to an enrollment.

    - INITIAL on a programless enrollment → in-place update.
    - Real change → soft-replace (mark previous TRANSFERRED, create new
      active enrollment with the new program).
    - No-op (same program) → 409 ConflictError.

    Always writes one ``ProgramAssignmentEvent`` row in the same transaction.
    """
    service = ProgramService(db)
    event = await service.assign_program_to_enrollment(
        enrollment_id=enrollment_id,
        program_id=body.program_id,
        program_version_id=body.program_version_id,
        reason_code=body.reason_code,
        reason_note=body.reason_note,
        auth=auth,
        ip_address=get_client_ip(request),
    )
    return success_response(event)


# ---------------------------------------------------------------------------
# Program equivalences (Phase 3.2)
# ---------------------------------------------------------------------------
@program_equivalences_router.get(
    "",
    summary="List program equivalences (optionally filtered by a program)",
)
async def list_equivalences(
    program_id: uuid.UUID | None = None,
    auth: AuthContext = Depends(requires_permission(PERM_ERP_PROGRAM_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = ProgramService(db)
    items = await service.list_program_equivalences(
        auth=auth, program_id=program_id
    )
    return list_response(items, next_cursor=None, has_more=False)


@program_equivalences_router.post(
    "",
    status_code=201,
    summary="Declare an equivalence between two programs",
)
async def create_equivalence(
    body: ProgramEquivalenceCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_ERP_PROGRAM_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    service = ProgramService(db)
    item = await service.create_program_equivalence(
        from_program_id=body.from_program_id,
        to_program_id=body.to_program_id,
        kind=body.kind,
        note=body.note,
        ratified_at=body.ratified_at,
        auth=auth,
        ip_address=get_client_ip(request),
    )
    return success_response(item)


@program_equivalences_router.delete(
    "/{equivalence_id}",
    status_code=204,
    summary="Remove a declared program equivalence",
)
async def delete_equivalence(
    equivalence_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_ERP_PROGRAM_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    service = ProgramService(db)
    await service.delete_program_equivalence(
        equivalence_id=equivalence_id,
        auth=auth,
        ip_address=get_client_ip(request),
    )
    return None
