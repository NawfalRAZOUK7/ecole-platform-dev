"""Content item endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    AuthContext,
    get_teacher_class_ids,
    requires_permission,
    verify_teacher_assignment,
)
from app.core.filtering import FilterSpec, SortSpec, parse_filters, parse_sort
from app.core.exceptions import NotFoundError
from app.core.permissions import (
    PERM_LMS_CONTENT_ASSET_DELETE,
    PERM_LMS_CONTENT_ASSET_READ,
    PERM_LMS_CONTENT_ASSET_UPLOAD,
    PERM_LMS_CONTENT_PROGRESS_WRITE,
    PERM_LMS_CONTENT_READ,
)
from app.core.request_utils import get_client_ip
from app.core.response import clamp_page_size, list_response, success_response
from app.core.search import parse_search
from app.core.storage import storage
from app.models.lms import ContentItemAsset
from app.schemas.lms import ContentProgressRequest
from app.schemas.student_work import StudentWorkListResponse
from app.services.lms import ContentService
from app.services.student_work import StudentWorkService

router = APIRouter(prefix="/content-items", tags=["lms-content"])
legacy_router = APIRouter(prefix="/content", tags=["lms-content"])
student_work_router = APIRouter(prefix="/student-work", tags=["student-work"])


@router.get(
    "",
    summary="List content items",
    response_description="Paginated list of learning materials",
)
async def list_content_items(
    content_type: str | None = Query(None),
    level_band: str | None = Query(None),
    language: str | None = Query(None),
    letter: str | None = Query(None),
    target_age: int | None = Query(None),
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    filters: FilterSpec = Depends(parse_filters),
    sort: SortSpec = Depends(parse_sort),
    search: str | None = Depends(parse_search),
    auth: AuthContext = Depends(requires_permission(PERM_LMS_CONTENT_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = ContentService(db)
    items, next_cursor, has_more = await service.list_content_items(
        content_type=content_type,
        level_band=level_band,
        language=language,
        letter=letter,
        target_age=target_age,
        filters=filters,
        sort=sort,
        search=search,
        cursor=cursor,
        limit=clamp_page_size(limit),
        auth=auth,
    )
    return list_response(
        items,
        next_cursor=next_cursor,
        has_more=has_more,
        filters_applied=filters.as_dict() if filters.items else None,
        sort_by=sort.as_list() if sort.fields else None,
        search_term=search,
    )


@legacy_router.get("", include_in_schema=False, summary="Legacy content list alias")
async def legacy_list_content_items(
    content_type: str | None = Query(None),
    level_band: str | None = Query(None),
    language: str | None = Query(None),
    letter: str | None = Query(None),
    target_age: int | None = Query(None),
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    filters: FilterSpec = Depends(parse_filters),
    sort: SortSpec = Depends(parse_sort),
    search: str | None = Depends(parse_search),
    auth: AuthContext = Depends(requires_permission(PERM_LMS_CONTENT_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = ContentService(db)
    items, next_cursor, has_more = await service.list_content_items(
        content_type=content_type,
        level_band=level_band,
        language=language,
        letter=letter,
        target_age=target_age,
        filters=filters,
        sort=sort,
        search=search,
        cursor=cursor,
        limit=clamp_page_size(limit),
        auth=auth,
    )
    return list_response(
        items,
        next_cursor=next_cursor,
        has_more=has_more,
        filters_applied=filters.as_dict() if filters.items else None,
        sort_by=sort.as_list() if sort.fields else None,
        search_term=search,
    )


@router.get(
    "/{content_item_id}",
    summary="Get content item details",
    response_description="Content item with assets",
)
async def get_content_item(
    content_item_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_LMS_CONTENT_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = ContentService(db)
    return success_response(
        await service.get_content_item(content_item_id=content_item_id, auth=auth)
    )


@router.get(
    "/{content_item_id}/stream",
    summary="Compatibility: stream the first content asset",
    response_description="Binary content stream",
)
async def stream_content_item(
    content_item_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_LMS_CONTENT_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Stream the first asset associated with a published content item."""
    service = ContentService(db)
    await service.get_content_item(content_item_id=content_item_id, auth=auth)

    result = await db.execute(
        select(ContentItemAsset)
        .where(ContentItemAsset.content_item_id == content_item_id)
        .order_by(ContentItemAsset.created_at.asc(), ContentItemAsset.id.asc())
        .limit(1)
    )
    asset = result.scalar_one_or_none()
    if asset is None:
        raise NotFoundError("Asset not found", error_code="ERR-UPLOAD-404")

    path = await storage.read(asset.file_path)
    return FileResponse(
        path=path,
        media_type=asset.mime_type or "application/octet-stream",
        filename=path.name,
    )


@router.post(
    "/{content_item_id}/progress",
    status_code=200,
    summary="Update content progress",
    response_description="Updated progress record",
)
async def update_content_progress(
    content_item_id: uuid.UUID,
    body: ContentProgressRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_LMS_CONTENT_PROGRESS_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    service = ContentService(db)
    return success_response(
        await service.update_content_progress(
            content_item_id=content_item_id,
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.post(
    "/{content_item_id}/assets",
    status_code=201,
    summary="Upload a content asset",
    response_description="Uploaded asset metadata",
)
async def upload_content_asset(
    content_item_id: uuid.UUID,
    file: UploadFile,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_LMS_CONTENT_ASSET_UPLOAD)),
    db: AsyncSession = Depends(get_db),
):
    service = ContentService(db)
    return success_response(
        await service.upload_content_asset(
            content_item_id=content_item_id,
            file=file.file,
            filename=file.filename or "asset",
            mime_type=file.content_type or "application/octet-stream",
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "/{content_item_id}/assets/{asset_id}",
    summary="Download a content asset",
    response_description="File binary content",
)
async def download_content_asset(
    content_item_id: uuid.UUID,
    asset_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_LMS_CONTENT_ASSET_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = ContentService(db)
    path, media_type, filename = await service.get_content_asset(
        content_item_id=content_item_id,
        asset_id=asset_id,
        auth=auth,
    )
    return FileResponse(path=path, media_type=media_type, filename=filename)


@router.delete(
    "/{content_item_id}/assets/{asset_id}",
    status_code=200,
    summary="Delete a content asset",
    response_description="Deletion confirmation",
)
async def delete_content_asset(
    content_item_id: uuid.UUID,
    asset_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_LMS_CONTENT_ASSET_DELETE)),
    db: AsyncSession = Depends(get_db),
):
    service = ContentService(db)
    return success_response(
        await service.delete_content_asset(
            content_item_id=content_item_id,
            asset_id=asset_id,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@student_work_router.get(
    "",
    response_model=StudentWorkListResponse,
    summary="List current student's work",
    response_description="Unified assignments, quizzes, and assessments for the student",
)
async def list_student_work(
    auth: AuthContext = Depends(requires_permission(PERM_LMS_CONTENT_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = StudentWorkService(db)
    items = await service.list_all_for_student(
        school_id=auth.school_id,
        student_id=auth.user_id,
    )
    return StudentWorkListResponse(items=items, total=len(items))


@student_work_router.get(
    "/class/{class_id}",
    response_model=StudentWorkListResponse,
    summary="List class work for an assigned teacher",
    response_description="Unified assignments, quizzes, and assessments for a class",
)
async def list_class_student_work(
    class_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_LMS_CONTENT_READ)),
    db: AsyncSession = Depends(get_db),
):
    allowed_class_ids = await get_teacher_class_ids(
        teacher_user_id=auth.user_id,
        school_id=auth.school_id,
        db=db,
    )
    verify_teacher_assignment(class_id, allowed_class_ids)

    service = StudentWorkService(db)
    items = await service.list_all_for_class(
        school_id=auth.school_id,
        class_id=class_id,
    )
    return StudentWorkListResponse(items=items, total=len(items))
