"""Phase 8 — Direct-to-MinIO upload endpoints.

POST /uploads/init       Authorize, validate, generate presigned PUT URL, create
                         UploadSession row in 'uploading' state.
POST /uploads/complete   HEAD-verify the object, transition to 'scanning',
                         enqueue post-upload scan ARQ job.
GET  /uploads/{id}/status  Poll upload lifecycle state (uploading → scanning →
                           available | quarantined | failed).

Clients never receive S3 credentials. The presigned URL is signed with
ContentType so MinIO enforces MIME on the PUT. Size enforcement comes from
the declared size_bytes validated at /init and re-verified via HEAD at /complete.
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import AuthContext, get_current_user
from app.core.exceptions import (
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.core.permissions import (
    PERM_LMS_CONTENT_ASSET_UPLOAD,
    PERM_LMS_SUBMISSION_FILE_UPLOAD,
    STD,
)
from app.core.response import success_response
from app.core.storage import S3StorageBackend, storage
from app.core.tasks import enqueue_task
from app.models.uploads import UploadSession
from app.schemas.uploads import (
    CompleteUploadRequest,
    CompleteUploadResponse,
    InitUploadRequest,
    InitUploadResponse,
    UploadKind,
    UploadScope,
    UploadStatusResponse,
)

router = APIRouter(prefix="/uploads", tags=["uploads"])

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ALLOWED_MIMES: dict[str, set[str]] = {
    "assignment_pdf": {"application/pdf"},
    "submission_file": {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/zip",
        "text/plain",
    },
    "content_asset": {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.ms-powerpoint",
        "application/zip",
        "text/plain",
    },
    "video": {"video/mp4"},
    "audio": {"audio/mpeg", "audio/mp4", "audio/ogg", "audio/wav"},
}

_MIME_TO_EXT: dict[str, str] = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "video/mp4": ".mp4",
    "audio/mpeg": ".mp3",
    "audio/mp4": ".m4a",
    "audio/ogg": ".ogg",
    "audio/wav": ".wav",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    "application/vnd.ms-powerpoint": ".ppt",
    "application/zip": ".zip",
    "text/plain": ".txt",
}

_KIND_PERMISSIONS: dict[str, str] = {
    "assignment_pdf": PERM_LMS_CONTENT_ASSET_UPLOAD,
    "submission_file": PERM_LMS_SUBMISSION_FILE_UPLOAD,
    "content_asset": PERM_LMS_CONTENT_ASSET_UPLOAD,
    "video": PERM_LMS_CONTENT_ASSET_UPLOAD,
    "audio": PERM_LMS_CONTENT_ASSET_UPLOAD,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _max_size_bytes(kind: str) -> int:
    match kind:
        case "assignment_pdf":
            return settings.max_document_size_mb * 1024 * 1024
        case "submission_file":
            return settings.max_submission_file_size_mb * 1024 * 1024
        case "content_asset":
            return settings.max_content_asset_size_mb * 1024 * 1024
        case "video":
            return settings.max_video_size_mb * 1024 * 1024
        case "audio":
            return settings.max_audio_size_mb * 1024 * 1024
    return 50 * 1024 * 1024


def _calc_ttl(size_bytes: int) -> int:
    """Dynamic TTL: max(15 min, ceil(size_bytes / 100 KB/s)) capped at 24 h."""
    return min(86400, max(900, math.ceil(size_bytes / 102400)))


def _build_object_key(
    kind: str, scope: UploadScope, mime_type: str, file_id: str
) -> str:
    ext = _MIME_TO_EXT.get(mime_type, ".bin")
    sid = str(scope.school_id)
    match kind:
        case "assignment_pdf":
            return f"schools/{sid}/exercises/{scope.assignment_id}/{file_id}.pdf"
        case "submission_file":
            return f"schools/{sid}/submissions/{scope.submission_id}/{file_id}{ext}"
        case "content_asset":
            return f"schools/{sid}/content/{scope.content_item_id}/{file_id}{ext}"
        case "video":
            return f"schools/{sid}/videos/{scope.content_item_id}/{file_id}.mp4"
        case "audio":
            return f"schools/{sid}/audio/{scope.content_item_id}/{file_id}{ext}"
    raise ValueError(f"Unknown upload kind: {kind!r}")


async def _verify_scope(
    db: AsyncSession,
    kind: UploadKind,
    scope: UploadScope,
    auth: AuthContext,
) -> None:
    """Load the scope entity from DB and verify school boundary + basic ownership."""
    from app.models.lms import Assignment, ContentItem, Submission

    if kind == UploadKind.assignment_pdf:
        if not scope.assignment_id:
            raise ValidationError(
                "scope.assignment_id is required for assignment_pdf uploads",
                error_code="ERR-UPLOAD-400",
            )
        result = await db.execute(
            select(Assignment).where(Assignment.id == scope.assignment_id)
        )
        entity = result.scalar_one_or_none()
        if entity is None or entity.school_id != auth.school_id:
            raise NotFoundError("Assignment not found", error_code="ERR-UPLOAD-404")

    elif kind == UploadKind.submission_file:
        if not scope.submission_id:
            raise ValidationError(
                "scope.submission_id is required for submission_file uploads",
                error_code="ERR-UPLOAD-400",
            )
        result = await db.execute(
            select(Submission).where(Submission.id == scope.submission_id)
        )
        entity = result.scalar_one_or_none()
        if entity is None or entity.school_id != auth.school_id:
            raise NotFoundError("Submission not found", error_code="ERR-UPLOAD-404")
        if auth.role == STD and entity.student_id != auth.user_id:
            raise AuthorizationError(
                "Cannot upload to another student's submission",
                error_code="ERR-UPLOAD-403",
            )

    elif kind in (UploadKind.content_asset, UploadKind.video, UploadKind.audio):
        if not scope.content_item_id:
            raise ValidationError(
                "scope.content_item_id is required for content_asset/video/audio uploads",
                error_code="ERR-UPLOAD-400",
            )
        result = await db.execute(
            select(ContentItem).where(ContentItem.id == scope.content_item_id)
        )
        entity = result.scalar_one_or_none()
        if entity is None or entity.school_id != auth.school_id:
            raise NotFoundError("Content item not found", error_code="ERR-UPLOAD-404")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/init",
    status_code=200,
    summary="Initialise a direct upload",
    response_description="Presigned PUT URL and upload session ID",
)
async def init_upload(
    body: InitUploadRequest,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Authorise and initialise a direct-to-MinIO upload.

    Returns a presigned PUT URL the client should use directly.
    The object is not visible to users until POST /uploads/complete is called
    and the post-upload virus scan passes.
    """
    # Permission check (kind-specific)
    required_perm = _KIND_PERMISSIONS[body.kind.value]
    if required_perm not in auth.permissions:
        raise AuthorizationError(
            f"Role {auth.role!r} cannot upload {body.kind.value}",
            error_code="ERR-UPLOAD-403",
        )

    # School boundary
    if body.scope.school_id != auth.school_id:
        raise AuthorizationError(
            "Cross-school uploads are not permitted",
            error_code="ERR-UPLOAD-403",
        )

    # MIME validation
    if body.mime_type not in ALLOWED_MIMES[body.kind.value]:
        raise ValidationError(
            f"MIME type {body.mime_type!r} is not allowed for {body.kind.value} uploads",
            error_code="ERR-UPLOAD-415",
        )

    # Size validation
    max_bytes = _max_size_bytes(body.kind.value)
    if body.size_bytes > max_bytes:
        raise ValidationError(
            f"Declared size {body.size_bytes} bytes exceeds the "
            f"{max_bytes // (1024 * 1024)} MB limit for {body.kind.value}",
            error_code="ERR-UPLOAD-413",
        )

    # Scope entity validation (DB lookup)
    await _verify_scope(db, body.kind, body.scope, auth)

    # Direct upload requires S3 backend
    if not isinstance(storage, S3StorageBackend):
        raise ValidationError(
            "Direct upload is only available when STORAGE_BACKEND=s3",
            error_code="ERR-UPLOAD-501",
        )

    # Generate object key and presigned URL
    file_id = uuid.uuid4().hex
    object_key = _build_object_key(body.kind.value, body.scope, body.mime_type, file_id)
    ttl = _calc_ttl(body.size_bytes)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)

    upload_url = await storage.presign_put(
        object_key,
        expires_in=ttl,
        content_type=body.mime_type,
        max_size=body.size_bytes,
    )

    # Persist session row
    session = UploadSession(
        upload_state="uploading",
        kind=body.kind.value,
        object_key=object_key,
        mime_type=body.mime_type,
        size_bytes=body.size_bytes,
        school_id=auth.school_id,
        uploader_id=auth.user_id,
        scope_data={
            "assignment_id": str(body.scope.assignment_id)
            if body.scope.assignment_id
            else None,
            "submission_id": str(body.scope.submission_id)
            if body.scope.submission_id
            else None,
            "content_item_id": str(body.scope.content_item_id)
            if body.scope.content_item_id
            else None,
        },
        expires_at=expires_at,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return success_response(
        InitUploadResponse(
            upload_id=session.id,
            upload_url=upload_url,
            object_key=object_key,
            expires_at=expires_at,
            max_size_bytes=max_bytes,
            required_headers={
                "Content-Type": body.mime_type,
                "Content-Length": str(body.size_bytes),
            },
        ).model_dump(mode="json")
    )


@router.post(
    "/complete",
    status_code=202,
    summary="Complete a direct upload",
    response_description="Upload session transitioned to scanning state",
)
async def complete_upload(
    body: CompleteUploadRequest,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Signal upload completion and enqueue the post-upload scan job.

    The backend HEAD-verifies the object exists in MinIO and matches the
    declared size before transitioning state. The upload is NOT yet visible
    to users — that happens only after the scan passes.
    """
    result = await db.execute(
        select(UploadSession).where(UploadSession.id == body.upload_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise NotFoundError("Upload session not found", error_code="ERR-UPLOAD-404")

    # School boundary (scope-masking: looks like 404)
    if session.school_id != auth.school_id:
        raise NotFoundError("Upload session not found", error_code="ERR-UPLOAD-404")

    # Only the original uploader may complete
    if session.uploader_id != auth.user_id:
        raise AuthorizationError(
            "Only the uploader can complete this session",
            error_code="ERR-UPLOAD-403",
        )

    # State guard
    if session.upload_state == "failed":
        raise ConflictError(
            "Upload session has expired or failed",
            error_code="ERR-UPLOAD-410",
        )
    if session.upload_state != "uploading":
        raise ConflictError(
            f"Upload session is already in {session.upload_state!r} state",
            error_code="ERR-UPLOAD-409",
        )

    # HEAD verify — object must exist in MinIO
    try:
        stat = await storage.stat(session.object_key)
    except NotFoundError:
        raise ConflictError(
            "Object not yet present in storage. "
            "Ensure the presigned PUT completed before calling /complete.",
            error_code="ERR-UPLOAD-409",
        )

    # Size integrity
    if stat.size_bytes != body.size_bytes:
        raise ValidationError(
            f"Size mismatch: declared {body.size_bytes} bytes, "
            f"actual {stat.size_bytes} bytes",
            error_code="ERR-UPLOAD-422",
        )

    # Transition state
    session.upload_state = "scanning"
    session.completed_at = datetime.now(timezone.utc)
    if body.sha256:
        session.sha256 = body.sha256
    db.add(session)
    await db.commit()

    # Enqueue scan job (fire-and-forget)
    await enqueue_task("task_post_upload_scan", upload_id=str(body.upload_id))

    return success_response(
        CompleteUploadResponse(
            upload_id=body.upload_id,
            state="scanning",
            status_url=f"/api/v1/uploads/{body.upload_id}/status",
        ).model_dump(mode="json"),
        status_code=202,
    )


@router.get(
    "/{upload_id}/status",
    summary="Poll upload state",
    response_description="Current upload session state",
)
async def get_upload_status(
    upload_id: uuid.UUID,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return the current state of an upload session.

    `target_id` is populated only when `state == available`.
    The client should use `target_id` + `target_kind` to reload the
    finalised entity (e.g. ContentItemAsset, SubmissionFile).
    """
    result = await db.execute(
        select(UploadSession).where(UploadSession.id == upload_id)
    )
    session = result.scalar_one_or_none()
    if session is None or session.school_id != auth.school_id:
        raise NotFoundError("Upload session not found", error_code="ERR-UPLOAD-404")

    return success_response(
        UploadStatusResponse(
            upload_id=session.id,
            state=session.upload_state,
            kind=session.kind,
            target_id=session.target_id,
            target_kind=session.target_kind,
            error_message=session.error_message,
            created_at=session.created_at,
            completed_at=session.completed_at,
            scanned_at=session.scanned_at,
        ).model_dump(mode="json")
    )
