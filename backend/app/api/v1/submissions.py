"""Submission endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Form, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.permissions import (
    PERM_LMS_SUBMISSION_CREATE,
    PERM_LMS_SUBMISSION_FILE_READ,
    PERM_LMS_SUBMISSION_FILE_UPLOAD,
    PERM_LMS_SUBMISSION_GRADE,
)
from app.core.request_utils import get_client_ip
from app.core.response import success_response
from app.schemas.lms import GradeRequest, SubmissionCreateRequest
from app.services.lms import AssignmentService, GradingService

router = APIRouter(prefix="/submissions", tags=["lms-submissions"])


@router.post(
    "",
    status_code=201,
    summary="Submit student work",
    response_description="Submission record",
)
async def create_submission(
    body: SubmissionCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_LMS_SUBMISSION_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    service = AssignmentService(db)
    return success_response(
        await service.create_submission(
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.post(
    "/{submission_id}/grade",
    status_code=201,
    summary="Grade a submission",
    response_description="Updated submission with grade",
)
async def grade_submission(
    submission_id: uuid.UUID,
    body: GradeRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_LMS_SUBMISSION_GRADE)),
    db: AsyncSession = Depends(get_db),
):
    service = GradingService(db)
    return success_response(
        await service.grade_submission(
            submission_id=submission_id,
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.post(
    "/{submission_id}/override-penalty",
    summary="Override a late submission penalty",
    response_description="Updated grade without penalty deduction",
)
async def override_late_penalty(
    submission_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_LMS_SUBMISSION_GRADE)),
    db: AsyncSession = Depends(get_db),
):
    service = GradingService(db)
    return success_response(
        await service.override_late_penalty(
            submission_id=submission_id,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.post(
    "/{submission_id}/files",
    status_code=201,
    summary="Upload a submission file",
    response_description="Uploaded file metadata",
)
async def upload_submission_file(
    submission_id: uuid.UUID,
    file: UploadFile,
    request: Request,
    file_type_hint: str | None = Form(None),
    auth: AuthContext = Depends(requires_permission(PERM_LMS_SUBMISSION_FILE_UPLOAD)),
    db: AsyncSession = Depends(get_db),
):
    service = AssignmentService(db)
    return success_response(
        await service.upload_submission_file(
            submission_id=submission_id,
            file=file.file,
            filename=file.filename or "upload",
            mime_type=file.content_type or "application/octet-stream",
            file_type_hint=file_type_hint,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "/{submission_id}/files/{file_id}",
    summary="Download a submission file",
    response_description="File binary content",
)
async def download_submission_file(
    submission_id: uuid.UUID,
    file_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_LMS_SUBMISSION_FILE_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = AssignmentService(db)
    path, media_type, filename = await service.get_submission_file(
        submission_id=submission_id,
        file_id=file_id,
        auth=auth,
    )
    return FileResponse(path=path, media_type=media_type, filename=filename)


@router.post(
    "/{submission_id}/submit",
    summary="Finalize and submit a draft submission",
    response_description="Updated submission",
)
async def finalize_submission(
    submission_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_LMS_SUBMISSION_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    service = AssignmentService(db)
    return success_response(
        await service.finalize_submission(
            submission_id=submission_id,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "/{submission_id}/preview",
    summary="Preview submission files (teacher)",
    response_description="List of files with preview metadata",
)
async def preview_submission_files(
    submission_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_LMS_SUBMISSION_GRADE)),
    db: AsyncSession = Depends(get_db),
):
    service = AssignmentService(db)
    return success_response(
        await service.preview_submission_files(
            submission_id=submission_id,
            auth=auth,
        )
    )
