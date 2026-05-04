"""Reusable download-response helper — Phase 3 (MinIO / S3 API Adaptation).

Provides a single ``build_download_response`` function that turns any
``PresignableBackend`` + object metadata into either:

- A ``302 RedirectResponse`` pointing at the presigned URL (default, backwards-
  compatible with all existing web/mobile clients).
- A ``200 JSONResponse`` containing a ``DownloadMetadata`` payload, selected by
  adding ``?as=metadata`` to the request URL.

Usage in an endpoint::

    from fastapi import Depends, Query
    from app.core.downloads import AS_QUERY, build_download_response

    @router.get("/{id}/download")
    async def download(
        id: uuid.UUID,
        as_: str | None = AS_QUERY,
        auth: AuthContext = Depends(get_auth_context),
        db: AsyncSession = Depends(get_db),
    ):
        # 1. Authorize — must happen BEFORE calling build_download_response.
        asset = await _get_and_authorize_asset(id, auth, db)

        # 2. Delegate response building to the helper.
        return await build_download_response(
            backend=storage,             # any PresignableBackend
            storage_path=asset.file_path,
            filename=asset.original_filename,
            mime_type=asset.mime_type,
            size=asset.file_size,
            as_=as_,
        )

Security invariants:
    - **Authorization happens before this function is called.**  The helper
      never accepts arbitrary paths from the client — the ``storage_path`` comes
      from a DB row that has already been ACL-checked by the service layer.
    - The presigned URL is short-lived (default TTL from ``settings``).
    - No S3/MinIO credentials are included in any response.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Protocol, runtime_checkable

from fastapi import Query
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from starlette.responses import Response

from app.core.config import settings
from app.schemas.storage import DownloadMetadata


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class PresignableBackend(Protocol):
    """Minimal interface required by the download helper.

    Both ``LocalStorageBackend`` and ``S3StorageBackend`` (core) satisfy this
    protocol.  ``S3FileStorageBackend`` (file_storage) will be extended in
    Prompt 6 to also satisfy it.
    """

    async def presign_get(
        self,
        relative_path: str,
        expires_in: int | None = None,
        *,
        response_filename: str | None = None,
    ) -> str:
        """Return a URL (presigned for S3, placeholder for local) for the object."""
        ...


# ---------------------------------------------------------------------------
# FastAPI query-param alias
# ---------------------------------------------------------------------------

AS_QUERY: str | None = Query(
    default=None,
    alias="as",
    description='Pass "metadata" to receive JSON instead of a 302 redirect.',
)
"""FastAPI ``Query`` descriptor for the ``?as=`` parameter.

Because ``as`` is a reserved Python keyword, route handlers must name the
parameter ``as_`` and use this alias::

    async def my_endpoint(as_: str | None = AS_QUERY): ...
"""


# ---------------------------------------------------------------------------
# Core helper
# ---------------------------------------------------------------------------

async def build_download_response(
    *,
    backend: PresignableBackend,
    storage_path: str,
    filename: str,
    mime_type: str,
    size: int,
    expires_in: int | None = None,
    etag: str | None = None,
    as_: str | None = None,
) -> Response:
    """Build a download response from an already-authorized storage path.

    Args:
        backend:       Any ``PresignableBackend`` (``storage`` singleton or a
                       ``S3FileStorageBackend`` instance).
        storage_path:  Object key / relative path — **must be ACL-checked by
                       the caller before passing here**.
        filename:      Human-friendly filename; embedded in the presigned URL's
                       ``Content-Disposition`` header so browsers save it
                       correctly.
        mime_type:     MIME type of the stored object.
        size:          Size in bytes.
        expires_in:    Presigned URL TTL in seconds.  Defaults to
                       ``settings.s3_presign_get_ttl_seconds``.
        etag:          Optional object ETag (hex MD5, quotes stripped).
        as_:           Value of the ``?as=`` query parameter.  Pass
                       ``"metadata"`` to get JSON; any other value (including
                       ``None``) returns a 302 redirect.

    Returns:
        - ``RedirectResponse`` (302) when ``as_`` is ``None`` or not
          ``"metadata"``.  The ``Location`` header is the presigned URL.
        - ``JSONResponse`` (200) with a ``DownloadMetadata`` body when
          ``as_ == "metadata"``.

    Security:
        Authorization **must** be enforced by the caller before invoking this
        function.  The helper generates a presigned URL for whatever
        ``storage_path`` is given — it does not re-check ACLs.
    """
    ttl = expires_in if expires_in is not None else settings.s3_presign_get_ttl_seconds
    url = await backend.presign_get(
        storage_path,
        ttl,
        response_filename=filename,
    )
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)

    if as_ == "metadata":
        payload = DownloadMetadata(
            download_url=url,
            expires_at=expires_at,
            mime_type=mime_type,
            size=size,
            filename=filename,
            etag=etag,
        )
        return JSONResponse(
            content=payload.model_dump(mode="json"),
            status_code=200,
        )

    return RedirectResponse(url=url, status_code=302)


async def serve_file(
    *,
    backend: PresignableBackend,
    storage_path: str,
    filename: str,
    mime_type: str,
    size: int = 0,
    as_: str | None = None,
) -> Response:
    """Route-level helper: presigned redirect for S3, FileResponse for local.

    For S3/MinIO:
        - Default: ``302 RedirectResponse`` with presigned ``Location``.
        - ``as_='metadata'``: ``200 JSONResponse`` with ``DownloadMetadata``.

    For local backend (``presign_get`` returns a relative path, not an HTTP
    URL):
        - Falls back to ``FileResponse`` served directly from disk.
        - ``as_`` is ignored in local mode.

    Authorization MUST be enforced by the caller before this function is called.
    The ``storage_path`` must come from an ACL-checked DB row.
    """
    url = await backend.presign_get(storage_path, response_filename=filename)
    if url.startswith(("http://", "https://")):
        return await build_download_response(
            backend=backend,
            storage_path=storage_path,
            filename=filename,
            mime_type=mime_type,
            size=size,
            as_=as_,
        )

    # Local backend: presign_get returned the relative path — serve directly.
    if hasattr(backend, "read"):
        local_path = await backend.read(storage_path)
    elif hasattr(backend, "local_path"):
        local_path = await backend.local_path(storage_path)
    else:  # pragma: no cover
        raise RuntimeError(
            f"Backend {type(backend).__name__} does not support local file access"
        )
    return FileResponse(path=local_path, media_type=mime_type, filename=filename)
