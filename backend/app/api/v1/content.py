"""Content Items API endpoints.

Reference:
  S-056 — GET /content-items, GET /content-items/{id} (STD, PAR)
  S-057 — POST /content-items/{id}/progress (STD)
  Phase 3B — POST /content-items/{id}/assets — Upload asset (TCH, ADM)
  Phase 3B — GET /content-items/{id}/assets/{asset_id} — Download asset
  Phase 3B — DELETE /content-items/{id}/assets/{asset_id} — Delete asset (TCH owner, ADM)
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission, verify_school_boundary
from app.core.exceptions import AuthorizationError, NotFoundError
from app.core.filtering import FilterSpec, SortSpec, apply_filters, apply_sort, parse_filters, parse_sort
from app.core.response import (
    clamp_page_size,
    decode_cursor,
    encode_cursor,
    list_response,
    success_response,
)
from app.core.search import apply_search, parse_search
from app.core.storage import storage, validate_file_size, validate_mime_type
from app.models.lms import ContentItem, ContentItemAsset, ContentProgress
from app.schemas.lms import ContentProgressRequest
from app.services.audit import AuditService

router = APIRouter(prefix="/content-items", tags=["lms-content"])


def _get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


# ---------------------------------------------------------------------------
# S-056: GET /content-items — List content items (STD, PAR)
# ---------------------------------------------------------------------------
@router.get("", summary="List content items", response_description="Paginated list of learning materials")
async def list_content_items(
    content_type: str | None = Query(None),
    level_band: str | None = Query(None),
    language: str | None = Query(None),
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    filters: FilterSpec = Depends(parse_filters),
    sort: SortSpec = Depends(parse_sort),
    search: str | None = Depends(parse_search),
    auth: AuthContext = Depends(requires_permission("PERM-LMS:content:read")),
    db: AsyncSession = Depends(get_db),
):
    """List published content items with filtering, sorting, and full-text search.

    Filters: ?filter[content_type]=video&filter[level_band]=college
    Sort: ?sort=-created_at
    Search: ?search=mathematiques
    Legacy params content_type, level_band, language still supported.
    """
    page_size = clamp_page_size(limit)

    # School-specific or platform-wide content
    query = select(ContentItem).where(
        ContentItem.status == "published",
        (ContentItem.school_id == auth.school_id) | (ContentItem.school_id.is_(None)),
    )

    # Legacy explicit filters
    if content_type:
        query = query.where(ContentItem.content_type == content_type)
    if level_band:
        query = query.where(ContentItem.level_band == level_band)
    if language:
        query = query.where(ContentItem.language == language)

    # Phase 3D: generic filters, search, sort
    query = apply_filters(query, ContentItem, filters)
    if search:
        query = apply_search(query, ContentItem, search)
    query = apply_sort(query, ContentItem, sort, default_column=ContentItem.id)

    if cursor:
        last_id, _ = decode_cursor(cursor)
        query = query.where(ContentItem.id > last_id)

    query = query.limit(page_size + 1)
    result = await db.execute(query)
    items_list = list(result.scalars().all())

    has_more = len(items_list) > page_size
    if has_more:
        items_list = items_list[:page_size]

    items = [
        {
            "id": str(ci.id),
            "school_id": str(ci.school_id) if ci.school_id else None,
            "title": ci.title,
            "content_type": ci.content_type,
            "level_band": ci.level_band,
            "language": ci.language,
            "status": ci.status,
        }
        for ci in items_list
    ]

    next_cursor = encode_cursor(items_list[-1].id) if has_more and items_list else None
    return list_response(
        items,
        next_cursor=next_cursor,
        has_more=has_more,
        filters_applied=filters.as_dict() if filters.items else None,
        sort_by=sort.as_list() if sort.fields else None,
        search_term=search,
    )


# ---------------------------------------------------------------------------
# S-056: GET /content-items/{id} — Get content item detail (STD, PAR)
# ---------------------------------------------------------------------------
@router.get("/{content_item_id}", summary="Get content item details", response_description="Content item with assets")
async def get_content_item(
    content_item_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission("PERM-LMS:content:read")),
    db: AsyncSession = Depends(get_db),
):
    """Get a content item by ID.

    Only published items visible. School boundary or platform-wide.
    """
    result = await db.execute(
        select(ContentItem).where(ContentItem.id == content_item_id)
    )
    ci = result.scalar_one_or_none()
    if ci is None:
        raise NotFoundError("Content item not found", error_code="ERR-LMS-404")

    # School boundary: must be same school or platform-wide (school_id IS NULL)
    if ci.school_id is not None:
        verify_school_boundary(ci.school_id, auth)

    # Only published items
    if ci.status != "published":
        raise NotFoundError("Content item not found", error_code="ERR-LMS-404")

    return success_response({
        "id": str(ci.id),
        "school_id": str(ci.school_id) if ci.school_id else None,
        "title": ci.title,
        "content_type": ci.content_type,
        "level_band": ci.level_band,
        "language": ci.language,
        "status": ci.status,
    })


# ---------------------------------------------------------------------------
# S-057: POST /content-items/{id}/progress — Track progress (STD)
# ---------------------------------------------------------------------------
@router.post("/{content_item_id}/progress", status_code=200, summary="Update content progress", response_description="Updated progress record")
async def update_content_progress(
    content_item_id: uuid.UUID,
    body: ContentProgressRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-LMS:content-progress:write")),
    db: AsyncSession = Depends(get_db),
):
    """Update student progress on a content item.

    Upsert: creates or updates progress record.
    Unique per (student_id, content_item_id).
    """
    audit = AuditService(db)

    # Validate content item exists
    ci_result = await db.execute(
        select(ContentItem).where(ContentItem.id == content_item_id)
    )
    ci = ci_result.scalar_one_or_none()
    if ci is None:
        raise NotFoundError("Content item not found", error_code="ERR-LMS-404")

    if ci.school_id is not None:
        verify_school_boundary(ci.school_id, auth)

    # Upsert progress
    existing_result = await db.execute(
        select(ContentProgress).where(
            ContentProgress.student_id == auth.user_id,
            ContentProgress.content_item_id == content_item_id,
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing is not None:
        existing.status = body.status
        await db.flush()
        progress = existing
    else:
        progress = ContentProgress(
            student_id=auth.user_id,
            content_item_id=content_item_id,
            status=body.status,
        )
        db.add(progress)
        await db.flush()

    # Audit
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="CONTENT_PROGRESS_UPDATED",
        outcome="success",
        target_type="content_progress",
        target_id=progress.id,
        entity_after={
            "content_item_id": str(content_item_id),
            "status": body.status,
        },
        ip_address=_get_client_ip(request),
    )

    return success_response({
        "id": str(progress.id),
        "student_id": str(progress.student_id),
        "content_item_id": str(progress.content_item_id),
        "status": progress.status,
    })


# ---------------------------------------------------------------------------
# Phase 3B: POST /content-items/{id}/assets — Upload asset (TCH, ADM)
# ---------------------------------------------------------------------------
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
    auth: AuthContext = Depends(requires_permission("PERM-LMS:content-asset:upload")),
    db: AsyncSession = Depends(get_db),
):
    """Upload a file asset to a content item.

    Access: TCH (school-bound), ADM.
    Validates MIME whitelist, file size limit, computes SHA-256 checksum.
    """
    audit = AuditService(db)

    # 1. Validate content item exists
    ci_result = await db.execute(
        select(ContentItem).where(ContentItem.id == content_item_id)
    )
    ci = ci_result.scalar_one_or_none()
    if ci is None:
        raise NotFoundError("Content item not found", error_code="ERR-LMS-404")

    # School boundary (if school-specific)
    if ci.school_id is not None:
        verify_school_boundary(ci.school_id, auth)

    # 2. MIME validation
    mime = file.content_type or "application/octet-stream"
    validate_mime_type(mime)

    # 3. Save via storage backend
    relative_path, checksum, file_size = await storage.save(
        file.file,
        file.filename or "asset",
        subdirectory=f"content/{content_item_id}",
    )

    # 4. Persist to content_item_assets table
    asset = ContentItemAsset(
        content_item_id=content_item_id,
        file_path=relative_path,
        checksum=checksum,
        mime_type=mime,
        file_size=file_size,
    )
    db.add(asset)
    await db.flush()

    # 5. Audit
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="CONTENT_ASSET_UPLOADED",
        outcome="success",
        target_type="content_item_asset",
        target_id=asset.id,
        entity_after={
            "content_item_id": str(content_item_id),
            "file_path": relative_path,
            "mime_type": mime,
            "file_size": file_size,
            "checksum": checksum,
        },
        ip_address=_get_client_ip(request),
    )

    return success_response({
        "id": str(asset.id),
        "content_item_id": str(asset.content_item_id),
        "file_path": asset.file_path,
        "checksum": asset.checksum,
        "mime_type": asset.mime_type,
        "file_size": asset.file_size,
    })


# ---------------------------------------------------------------------------
# Phase 3B: GET /content-items/{id}/assets/{asset_id} — Download asset
# ---------------------------------------------------------------------------
@router.get(
    "/{content_item_id}/assets/{asset_id}",
    summary="Download a content asset",
    response_description="File binary content",
)
async def download_content_asset(
    content_item_id: uuid.UUID,
    asset_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission("PERM-LMS:content-asset:read")),
    db: AsyncSession = Depends(get_db),
):
    """Download a content item asset.

    Access: all authenticated users with content-asset:read (STD, PAR, TCH, ADM).
    School boundary enforced for school-specific content.
    """
    # 1. Validate asset exists
    asset_result = await db.execute(
        select(ContentItemAsset).where(
            ContentItemAsset.id == asset_id,
            ContentItemAsset.content_item_id == content_item_id,
        )
    )
    asset = asset_result.scalar_one_or_none()
    if asset is None:
        raise NotFoundError("Asset not found", error_code="ERR-UPLOAD-404")

    # 2. Validate content item + school boundary
    ci_result = await db.execute(
        select(ContentItem).where(ContentItem.id == content_item_id)
    )
    ci = ci_result.scalar_one_or_none()
    if ci is None:
        raise NotFoundError("Content item not found", error_code="ERR-LMS-404")

    if ci.school_id is not None:
        verify_school_boundary(ci.school_id, auth)

    # 3. Serve file
    abs_path = await storage.read(asset.file_path)
    return FileResponse(
        path=str(abs_path),
        media_type=asset.mime_type or "application/octet-stream",
        filename=abs_path.name,
    )


# ---------------------------------------------------------------------------
# Phase 3B: DELETE /content-items/{id}/assets/{asset_id} — Delete asset
# ---------------------------------------------------------------------------
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
    auth: AuthContext = Depends(requires_permission("PERM-LMS:content-asset:delete")),
    db: AsyncSession = Depends(get_db),
):
    """Delete a content item asset.

    Access: TCH (school-bound), ADM.
    Removes from storage and database.
    """
    audit = AuditService(db)

    # 1. Validate asset exists
    asset_result = await db.execute(
        select(ContentItemAsset).where(
            ContentItemAsset.id == asset_id,
            ContentItemAsset.content_item_id == content_item_id,
        )
    )
    asset = asset_result.scalar_one_or_none()
    if asset is None:
        raise NotFoundError("Asset not found", error_code="ERR-UPLOAD-404")

    # 2. Validate content item + school boundary
    ci_result = await db.execute(
        select(ContentItem).where(ContentItem.id == content_item_id)
    )
    ci = ci_result.scalar_one_or_none()
    if ci is None:
        raise NotFoundError("Content item not found", error_code="ERR-LMS-404")

    if ci.school_id is not None:
        verify_school_boundary(ci.school_id, auth)

    # 3. Delete from storage
    await storage.delete(asset.file_path)

    # 4. Delete from database
    entity_before = {
        "id": str(asset.id),
        "file_path": asset.file_path,
        "mime_type": asset.mime_type,
        "file_size": asset.file_size,
    }
    await db.delete(asset)
    await db.flush()

    # 5. Audit
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="CONTENT_ASSET_DELETED",
        outcome="success",
        target_type="content_item_asset",
        target_id=uuid.UUID(entity_before["id"]),
        entity_before=entity_before,
        ip_address=_get_client_ip(request),
    )

    return success_response({"deleted": True, "id": entity_before["id"]})
