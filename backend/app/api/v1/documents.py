"""Phase 16 document management and resource library API."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.exceptions import AuthenticationError, ValidationError
from app.core.permissions import (
    PERM_DOC_BULK_DELETE,
    PERM_DOC_BULK_DOWNLOAD,
    PERM_DOC_DOCUMENT_DELETE,
    PERM_DOC_DOCUMENT_READ,
    PERM_DOC_DOCUMENT_UPLOAD,
    PERM_DOC_RESOURCE_CREATE,
    PERM_DOC_RESOURCE_DELETE,
    PERM_DOC_RESOURCE_RATE,
    PERM_DOC_RESOURCE_READ,
    PERM_DOC_RESOURCE_UPDATE,
    PERM_DOC_STUDENT_DOCUMENT_LINK,
)
from app.core.response import clamp_page_size, list_response, success_response
from app.core.request_utils import get_client_ip, optional_current_user
from app.schemas.documents import DocumentBulkRequest, DocumentLinkRequest
from app.schemas.resources import (
    ResourceCreateRequest,
    ResourceRatingRequest,
    ResourceUpdateRequest,
)
from app.services.audit import AuditService
from app.services.resource_library import ResourceLibraryService
from app.services.student_documents import (
    DOCUMENT_DOWNLOAD_ACTION,
    DOCUMENT_PREVIEW_ACTION,
    StudentDocumentsService,
)

router = APIRouter(tags=["documents"])


@router.post(
    "/documents/upload",
    status_code=201,
    summary="Upload a document",
    response_description="Uploaded document metadata",
)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    category: str | None = Form(None),
    linked_student_id: uuid.UUID | None = Form(None),
    expires_at: datetime | None = Form(None),
    auth: AuthContext = Depends(requires_permission(PERM_DOC_DOCUMENT_UPLOAD)),
    db: AsyncSession = Depends(get_db),
):
    service = StudentDocumentsService(db)
    audit = AuditService(db)
    payload = await service.upload_document(
        school_id=auth.school_id,
        user_id=auth.user_id,
        role=auth.role,
        file=file.file,
        original_filename=file.filename or "upload",
        mime_type=file.content_type or "application/octet-stream",
        category=category,
        linked_student_id=linked_student_id,
        expires_at=expires_at,
    )
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="document.upload",
        target_type="document",
        target_id=uuid.UUID(payload["id"]),
        outcome="success",
        entity_after=payload,
        ip_address=get_client_ip(request),
    )
    await db.commit()
    return success_response(payload)


@router.get(
    "/documents",
    summary="List documents",
    response_description="Cursor-paginated document list",
)
async def list_documents(
    category: str | None = Query(None),
    owner: str | None = Query(None),
    type: str | None = Query(None, description="Exact MIME type filter"),
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    auth: AuthContext = Depends(requires_permission(PERM_DOC_DOCUMENT_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = StudentDocumentsService(db)
    items, next_cursor, has_more = await service.list_documents(
        school_id=auth.school_id,
        user_id=auth.user_id,
        role=auth.role,
        category=category,
        owner=owner,
        mime_type=type,
        cursor=cursor,
        limit=clamp_page_size(limit),
    )
    return list_response(items, next_cursor=next_cursor, has_more=has_more)


@router.get(
    "/documents/options",
    summary="Get role-filtered document options",
    response_description="Students and categories available to the current user",
)
async def get_document_options(
    auth: AuthContext = Depends(requires_permission(PERM_DOC_DOCUMENT_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = StudentDocumentsService(db)
    return success_response(
        await service.get_document_options(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            actor_role=auth.role,
        )
    )


@router.get(
    "/documents/{document_id}/versions",
    summary="List stored versions for a document",
    response_description="Document version history",
)
async def list_document_versions(
    document_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_DOC_DOCUMENT_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = StudentDocumentsService(db)
    return list_response(
        await service.list_versions(
            document_id=document_id,
            school_id=auth.school_id,
            actor_id=auth.user_id,
            actor_role=auth.role,
        )
    )


@router.get(
    "/documents/{document_id}/versions/{version_number}",
    summary="Download a specific document version",
    response_description="Document version binary",
)
async def get_document_version(
    document_id: uuid.UUID,
    version_number: int,
    auth: AuthContext = Depends(requires_permission(PERM_DOC_DOCUMENT_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = StudentDocumentsService(db)
    version, abs_path = await service.get_version(
        document_id=document_id,
        version_number=version_number,
        school_id=auth.school_id,
        actor_id=auth.user_id,
        actor_role=auth.role,
    )
    return FileResponse(
        path=str(abs_path),
        media_type=version.mime_type,
        filename=version.original_filename,
    )


@router.post(
    "/documents/{document_id}/versions/{version_number}/restore",
    summary="Restore a previous document version",
    response_description="Restored current document metadata",
)
async def restore_document_version(
    document_id: uuid.UUID,
    version_number: int,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_DOC_DOCUMENT_UPLOAD)),
    db: AsyncSession = Depends(get_db),
):
    service = StudentDocumentsService(db)
    return success_response(
        await service.restore_version(
            document_id=document_id,
            version_number=version_number,
            school_id=auth.school_id,
            actor_id=auth.user_id,
            actor_role=auth.role,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "/documents/{document_id}",
    summary="Get document metadata",
    response_description="Single document metadata",
)
async def get_document(
    document_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_DOC_DOCUMENT_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = StudentDocumentsService(db)
    document = await service.get_document_for_actor(
        document_id=document_id,
        school_id=auth.school_id,
        actor_id=auth.user_id,
        actor_role=auth.role,
    )
    return success_response(
        await service.serialize_document(
            document,
            role=auth.role,
            actor_id=auth.user_id,
        )
    )


@router.get(
    "/documents/{document_id}/download",
    summary="Download a document",
    response_description="Document file binary",
)
async def download_document(
    document_id: uuid.UUID,
    request: Request,
    token: str | None = Query(None),
    auth: AuthContext | None = Depends(optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = StudentDocumentsService(db)
    audit = AuditService(db)
    if token:
        document = await service.get_document_for_token(
            token=token,
            action=DOCUMENT_DOWNLOAD_ACTION,
        )
        actor_id = auth.user_id if auth else document.uploader_id
    else:
        if auth is None:
            raise AuthenticationError(
                "Missing Authorization header",
                error_code="ERR-IAM-401",
            )
        document = await service.get_document_for_actor(
            document_id=document_id,
            school_id=auth.school_id,
            actor_id=auth.user_id,
            actor_role=auth.role,
        )
        actor_id = auth.user_id

    if document.id != document_id:
        raise ValidationError("Document token mismatch", error_code="ERR-DOC-422")
    abs_path = await service.read_document_file(document=document)
    await audit.log_event(
        school_id=document.school_id,
        actor_id=actor_id,
        action_type="document.download",
        target_type="document",
        target_id=document.id,
        outcome="success",
        entity_after={"original_filename": document.original_filename},
        ip_address=get_client_ip(request),
    )
    await db.commit()
    return FileResponse(
        path=str(abs_path),
        media_type=document.mime_type,
        filename=document.original_filename,
    )


@router.get(
    "/documents/{document_id}/preview",
    summary="Preview a document",
    response_description="Preview binary for an image thumbnail or PDF/image content",
)
async def preview_document(
    document_id: uuid.UUID,
    token: str | None = Query(None),
    auth: AuthContext | None = Depends(optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = StudentDocumentsService(db)
    if token:
        document = await service.get_document_for_token(
            token=token,
            action=DOCUMENT_PREVIEW_ACTION,
        )
    else:
        if auth is None:
            raise AuthenticationError(
                "Missing Authorization header",
                error_code="ERR-IAM-401",
            )
        document = await service.get_document_for_actor(
            document_id=document_id,
            school_id=auth.school_id,
            actor_id=auth.user_id,
            actor_role=auth.role,
        )
    if document.id != document_id:
        raise ValidationError("Document token mismatch", error_code="ERR-DOC-422")
    abs_path = await service.read_document_preview(document=document)
    media_type = "image/png" if abs_path.suffix.lower() == ".png" else document.mime_type
    return FileResponse(path=str(abs_path), media_type=media_type, filename=abs_path.name)


@router.delete(
    "/documents/{document_id}",
    summary="Delete a document",
    response_description="Deletion outcome",
)
async def delete_document(
    document_id: uuid.UUID,
    request: Request,
    hard: bool = Query(False),
    auth: AuthContext = Depends(requires_permission(PERM_DOC_DOCUMENT_DELETE)),
    db: AsyncSession = Depends(get_db),
):
    service = StudentDocumentsService(db)
    audit = AuditService(db)
    result = await service.delete_document(
        document_id=document_id,
        school_id=auth.school_id,
        actor_id=auth.user_id,
        actor_role=auth.role,
        hard_delete=hard,
    )
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="document.delete",
        target_type="document",
        target_id=document_id,
        outcome="success",
        entity_after=result,
        ip_address=get_client_ip(request),
    )
    await db.commit()
    return success_response(result)


@router.post(
    "/documents/bulk-download",
    summary="Prepare a bulk ZIP download",
    response_description="Signed ZIP download URL",
)
async def create_bulk_download(
    body: DocumentBulkRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_DOC_BULK_DOWNLOAD)),
    db: AsyncSession = Depends(get_db),
):
    service = StudentDocumentsService(db)
    audit = AuditService(db)
    payload = await service.create_bulk_download(
        document_ids=body.document_ids,
        school_id=auth.school_id,
        actor_id=auth.user_id,
        actor_role=auth.role,
    )
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="document.bulk_download",
        target_type="document",
        target_id=auth.user_id,
        outcome="success",
        entity_after=payload,
        ip_address=get_client_ip(request),
    )
    await db.commit()
    return success_response(payload)


@router.get(
    "/documents/bulk-download",
    summary="Download a prepared document ZIP",
    response_description="ZIP file for multiple documents",
)
async def download_bulk_archive(
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    service = StudentDocumentsService(db)
    archive_path, filename = await service.get_bulk_download_archive(token=token)
    return FileResponse(
        path=str(archive_path),
        media_type="application/zip",
        filename=filename,
    )


@router.post(
    "/documents/bulk-delete",
    summary="Soft delete multiple documents",
    response_description="Bulk deletion outcome",
)
async def bulk_delete_documents(
    body: DocumentBulkRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_DOC_BULK_DELETE)),
    db: AsyncSession = Depends(get_db),
):
    service = StudentDocumentsService(db)
    audit = AuditService(db)
    payload = await service.bulk_delete_documents(
        document_ids=body.document_ids,
        school_id=auth.school_id,
        actor_id=auth.user_id,
        actor_role=auth.role,
    )
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="document.bulk_delete",
        target_type="document",
        target_id=auth.user_id,
        outcome="success",
        entity_after=payload,
        ip_address=get_client_ip(request),
    )
    await db.commit()
    return success_response(payload)


@router.post(
    "/students/{student_id}/documents",
    summary="Link a document to a student",
    response_description="Linked student document metadata",
)
async def link_student_document(
    student_id: uuid.UUID,
    body: DocumentLinkRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_DOC_STUDENT_DOCUMENT_LINK)),
    db: AsyncSession = Depends(get_db),
):
    service = StudentDocumentsService(db)
    audit = AuditService(db)
    payload = await service.link_document_to_student(
        document_id=body.document_id,
        student_id=student_id,
        school_id=auth.school_id,
        actor_id=auth.user_id,
        actor_role=auth.role,
        category=body.category,
        expires_at=body.expires_at,
    )
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="student_document.link",
        target_type="document",
        target_id=body.document_id,
        outcome="success",
        entity_after=payload,
        ip_address=get_client_ip(request),
    )
    await db.commit()
    return success_response(payload)


@router.get(
    "/students/{student_id}/documents",
    summary="List documents for a student",
    response_description="Student-linked documents",
)
async def list_student_documents(
    student_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_DOC_DOCUMENT_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = StudentDocumentsService(db)
    return list_response(
        await service.list_student_documents(
            school_id=auth.school_id,
            student_id=student_id,
            actor_id=auth.user_id,
            actor_role=auth.role,
        )
    )


@router.get(
    "/students/{student_id}/documents/checklist",
    summary="Get the student document checklist",
    response_description="Required documents and completion status",
)
async def get_student_document_checklist(
    student_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_DOC_DOCUMENT_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = StudentDocumentsService(db)
    return success_response(
        await service.get_student_checklist(
            school_id=auth.school_id,
            student_id=student_id,
            actor_id=auth.user_id,
            actor_role=auth.role,
        )
    )


@router.post(
    "/resources",
    status_code=201,
    summary="Create a resource",
    response_description="Created resource metadata",
)
async def create_resource(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str | None = Form(None),
    subject: str | None = Form(None),
    level: str | None = Form(None),
    type: str = Form(...),
    visibility: str = Form(...),
    class_id: uuid.UUID | None = Form(None),
    tags: str | None = Form(None),
    auth: AuthContext = Depends(requires_permission(PERM_DOC_RESOURCE_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    service = ResourceLibraryService(db)
    audit = AuditService(db)
    payload = await service.create_resource(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        actor_role=auth.role,
        file=file.file,
        original_filename=file.filename or "resource",
        mime_type=file.content_type or "application/octet-stream",
        payload=ResourceCreateRequest(
            title=title,
            description=description,
            subject=subject,
            level=level,
            type=type,
            visibility=visibility,
            class_id=class_id,
            tags=[item.strip() for item in (tags or "").split(",") if item.strip()],
        ),
    )
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="resource.create",
        target_type="resource",
        target_id=uuid.UUID(payload["id"]),
        outcome="success",
        entity_after=payload,
        ip_address=get_client_ip(request),
    )
    await db.commit()
    return success_response(payload)


@router.get(
    "/resources",
    summary="List resources",
    response_description="Cursor-paginated resource list",
)
async def list_resources(
    subject: str | None = Query(None),
    level: str | None = Query(None),
    type: str | None = Query(None),
    tags: str | None = Query(None),
    q: str | None = Query(None),
    rating: float | None = Query(None),
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    auth: AuthContext = Depends(requires_permission(PERM_DOC_RESOURCE_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = ResourceLibraryService(db)
    items, next_cursor, has_more = await service.list_resources(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        actor_role=auth.role,
        subject=subject,
        level=level,
        resource_type=type,
        tags=[item.strip() for item in (tags or "").split(",") if item.strip()],
        search=q,
        min_rating=rating,
        cursor=cursor,
        limit=clamp_page_size(limit),
    )
    return list_response(items, next_cursor=next_cursor, has_more=has_more)


@router.get(
    "/resources/{resource_id}",
    summary="Get resource detail",
    response_description="Single resource metadata",
)
async def get_resource(
    resource_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_DOC_RESOURCE_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = ResourceLibraryService(db)
    return success_response(
        await service.get_resource_detail(
            resource_id=resource_id,
            school_id=auth.school_id,
            actor_id=auth.user_id,
            actor_role=auth.role,
        )
    )


@router.put(
    "/resources/{resource_id}",
    summary="Update a resource",
    response_description="Updated resource metadata",
)
async def update_resource(
    resource_id: uuid.UUID,
    body: ResourceUpdateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_DOC_RESOURCE_UPDATE)),
    db: AsyncSession = Depends(get_db),
):
    service = ResourceLibraryService(db)
    audit = AuditService(db)
    payload = await service.update_resource(
        resource_id=resource_id,
        school_id=auth.school_id,
        actor_id=auth.user_id,
        actor_role=auth.role,
        payload=body,
    )
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="resource.update",
        target_type="resource",
        target_id=resource_id,
        outcome="success",
        entity_after=payload,
        ip_address=get_client_ip(request),
    )
    await db.commit()
    return success_response(payload)


@router.delete(
    "/resources/{resource_id}",
    summary="Delete a resource",
    response_description="Deletion outcome",
)
async def delete_resource(
    resource_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_DOC_RESOURCE_DELETE)),
    db: AsyncSession = Depends(get_db),
):
    service = ResourceLibraryService(db)
    audit = AuditService(db)
    payload = await service.delete_resource(
        resource_id=resource_id,
        school_id=auth.school_id,
        actor_id=auth.user_id,
        actor_role=auth.role,
    )
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="resource.delete",
        target_type="resource",
        target_id=resource_id,
        outcome="success",
        entity_after=payload,
        ip_address=get_client_ip(request),
    )
    await db.commit()
    return success_response(payload)


@router.get(
    "/resources/{resource_id}/download",
    summary="Download a resource file",
    response_description="Resource file binary",
)
async def download_resource(
    resource_id: uuid.UUID,
    request: Request,
    token: str | None = Query(None),
    auth: AuthContext | None = Depends(optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ResourceLibraryService(db)
    audit = AuditService(db)
    if token:
        resource, document = await service.get_resource_for_token(token=token)
        actor_id = auth.user_id if auth else resource.uploader_id
    else:
        if auth is None:
            raise AuthenticationError(
                "Missing Authorization header",
                error_code="ERR-IAM-401",
            )
        resource, document = await service.get_resource_for_actor(
            resource_id=resource_id,
            school_id=auth.school_id,
            actor_id=auth.user_id,
            actor_role=auth.role,
        )
        actor_id = auth.user_id
    if resource.id != resource_id:
        raise ValidationError("Resource token mismatch", error_code="ERR-DOC-422")
    abs_path = await service.read_resource_file(resource=resource, document=document)
    await audit.log_event(
        school_id=resource.school_id,
        actor_id=actor_id,
        action_type="resource.download",
        target_type="resource",
        target_id=resource.id,
        outcome="success",
        entity_after={"title": resource.title},
        ip_address=get_client_ip(request),
    )
    await db.commit()
    return FileResponse(
        path=str(abs_path),
        media_type=document.mime_type,
        filename=document.original_filename,
    )


@router.post(
    "/resources/{resource_id}/rate",
    summary="Rate a resource",
    response_description="Updated rating summary",
)
async def rate_resource(
    resource_id: uuid.UUID,
    body: ResourceRatingRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_DOC_RESOURCE_RATE)),
    db: AsyncSession = Depends(get_db),
):
    service = ResourceLibraryService(db)
    audit = AuditService(db)
    payload = await service.rate_resource(
        resource_id=resource_id,
        school_id=auth.school_id,
        actor_id=auth.user_id,
        actor_role=auth.role,
        rating_value=body.rating,
    )
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="resource.rate",
        target_type="resource",
        target_id=resource_id,
        outcome="success",
        entity_after=payload,
        ip_address=get_client_ip(request),
    )
    await db.commit()
    return success_response(payload)


@router.get(
    "/resources/{resource_id}/rating",
    summary="Get a resource rating summary",
    response_description="Average and current-user rating",
)
async def get_resource_rating(
    resource_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_DOC_RESOURCE_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = ResourceLibraryService(db)
    return success_response(
        await service.get_rating_summary(
            resource_id=resource_id,
            school_id=auth.school_id,
            actor_id=auth.user_id,
            actor_role=auth.role,
        )
    )
