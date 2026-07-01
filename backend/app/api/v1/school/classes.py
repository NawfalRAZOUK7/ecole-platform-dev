"""Class API endpoint: GET /classes/{class_id}.

Reference: S-045 — First ERP endpoint validating the full security pipeline.
Pipeline: AuthN -> RBAC (PERM-ERP:class:read) -> ABAC (school boundary + teacher assignment)
Roles: ADM (all classes in school), TCH (only assigned classes)
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.response import ApiResponse, success_response
from app.schemas.academic.erp import ClassResponse
from app.services.academic.erp import ERPService

router = APIRouter(prefix="/classes", tags=["erp-classes"])


@router.get(
    "/{class_id}",
    response_model=ApiResponse[ClassResponse],
    summary="Get class details",
    response_description="Class with capacity, level, academic year",
)
async def get_class(
    class_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission("PERM-ERP:class:read")),
    db: AsyncSession = Depends(get_db),
):
    """Get class details by ID.

    Full security pipeline:
    1. AuthN — verified by get_current_user (via requires_permission)
    2. RBAC — requires PERM-ERP:class:read
    3. ABAC — school boundary (404 for other school's classes)
    4. ABAC — teacher assignment (TCH only sees assigned classes)
    """
    service = ERPService(db)
    result = await service.get_class(
        class_id=class_id,
        auth=auth,
    )
    return success_response(result)
