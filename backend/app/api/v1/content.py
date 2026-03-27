"""Content item endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.filtering import FilterSpec, SortSpec, parse_filters, parse_sort
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
from app.schemas.lms import ContentProgressRequest
from app.services.lms import LMSService

router = APIRouter(prefix="/content-items", tags=["lms-content"])
legacy_router = APIRouter(prefix="/content", tags=["lms-content"])


@router.get(
    "",
    summary="List content items",
    response_description="Paginated list of learning materials",
)
async def list_content_items(
    content_type: str | None = Query(None),
    level_band: str | None = Query(None),
    language: str | None = Query(None),
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    filters: FilterSpec = Depends(parse_filters),
    sort: SortSpec = Depends(parse_sort),
    search: str | None = Depends(parse_search),
    auth: AuthContext = Depends(requires_permission(PERM_LMS_CONTENT_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = LMSService(db)
    items, next_cursor, has_more = await service.list_content_items(
        content_type=content_type,
        level_band=level_band,
        language=language,
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
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    filters: FilterSpec = Depends(parse_filters),
    sort: SortSpec = Depends(parse_sort),
    search: str | None = Depends(parse_search),
    auth: AuthContext = Depends(requires_permission(PERM_LMS_CONTENT_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = LMSService(db)
    items, next_cursor, has_more = await service.list_content_items(
        content_type=content_type,
        level_band=level_band,
        language=language,
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
    service = LMSService(db)
    return success_response(
        await service.get_content_item(content_item_id=content_item_id, auth=auth)
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
    service = LMSService(db)
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
    service = LMSService(db)
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
    service = LMSService(db)
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
    service = LMSService(db)
    return success_response(
        await service.delete_content_asset(
            content_item_id=content_item_id,
            asset_id=asset_id,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )
