"""Phase 16 file storage service — local and S3-compatible backends.

Phase 2B (MinIO): S3FileStorageBackend now uses aioboto3 (fully async).
The old sync boto3 client and tempfile-download pattern have been removed.
"""

from __future__ import annotations

import hashlib
import io
import mimetypes
import re
import socket
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from app.core.config import settings
from app.core.exceptions import NotFoundError, ValidationError

try:  # pragma: no cover - optional runtime dependency
    from PIL import Image
except Exception:  # pragma: no cover - handled at runtime
    Image = None


# ---------------------------------------------------------------------------
# aioboto3 session singleton (document storage)
# ---------------------------------------------------------------------------

_s3_doc_session: Any = None


def _get_s3_doc_session() -> Any:
    """Return (or lazily create) the module-level aioboto3 session for document storage."""
    global _s3_doc_session
    if _s3_doc_session is None:
        import aioboto3  # noqa: PLC0415
        _s3_doc_session = aioboto3.Session()
    return _s3_doc_session


ALLOWED_MIME_TYPES = {
    mime.strip()
    for mime in settings.allowed_document_mime_types.split(",")
    if mime.strip()
}


def _safe_filename(filename: str) -> str:
    name = Path(filename).name.strip() or "upload"
    stem = Path(name).stem or "upload"
    suffix = Path(name).suffix.lower()
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._") or "upload"
    return f"{cleaned}{suffix}"


def _extension_for(filename: str, mime_type: str) -> str:
    suffix = Path(filename).suffix
    if suffix:
        return suffix.lower()
    guessed = mimetypes.guess_extension(mime_type or "")
    return guessed or ""


def validate_document_upload(*, mime_type: str, size_bytes: int) -> None:
    if mime_type not in ALLOWED_MIME_TYPES:
        raise ValidationError(
            f"File type '{mime_type}' is not allowed",
            error_code="ERR-DOC-415",
        )
    max_bytes = settings.max_document_size_mb * 1024 * 1024
    if size_bytes > max_bytes:
        raise ValidationError(
            f"File size {size_bytes} bytes exceeds maximum of {settings.max_document_size_mb} MB",
            error_code="ERR-DOC-413",
        )


async def virus_scan_hook(content: bytes) -> None:
    """Optional ClamAV integration point.

    The default dev path keeps this disabled. When enabled, this function
    performs a lightweight `INSTREAM` probe against a ClamAV daemon.
    """

    if not settings.virus_scan_enabled:
        return

    try:  # pragma: no cover - depends on runtime service
        with socket.create_connection(
            (settings.virus_scan_host, settings.virus_scan_port),
            timeout=5,
        ) as sock:
            sock.sendall(b"zINSTREAM\0")
            for offset in range(0, len(content), 8192):
                chunk = content[offset : offset + 8192]
                sock.sendall(len(chunk).to_bytes(4, "big"))
                sock.sendall(chunk)
            sock.sendall((0).to_bytes(4, "big"))
            response = sock.recv(4096)
        if b"FOUND" in response:
            raise ValidationError(
                "The uploaded file failed malware scanning",
                error_code="ERR-DOC-422",
            )
    except ValidationError:
        raise
    except OSError as exc:  # pragma: no cover - depends on runtime service
        raise ValidationError(
            "Virus scanning is unavailable",
            error_code="ERR-DOC-503",
        ) from exc


@dataclass(slots=True)
class StoredObject:
    storage_path: str
    size_bytes: int
    sha256: str


@runtime_checkable
class FileStorageBackend(Protocol):
    async def save_bytes(
        self, *, relative_path: str, content: bytes, mime_type: str
    ) -> StoredObject: ...

    async def exists(self, relative_path: str) -> bool: ...

    async def delete(self, relative_path: str) -> None: ...

    async def local_path(self, relative_path: str) -> Path:
        """Return absolute local Path for a stored file.

        S3 backend raises NotImplementedError — use presign_get (Prompt 6)
        for download responses or get_bytes for server-side processing.
        """
        ...

    async def get_bytes(self, relative_path: str) -> bytes:
        """Return the raw content of a stored file as bytes.

        Suitable for server-side processing (e.g. version restore, zip assembly).
        Not suitable for very large objects (>100 MB) — use presigned URLs instead.
        """
        ...

    async def presign_get(
        self,
        relative_path: str,
        expires_in: int | None = None,
        *,
        response_filename: str | None = None,
    ) -> str:
        """Return a presigned GET URL (S3) or relative-path placeholder (local).

        Routes should call serve_file() from app.core.downloads, which dispatches
        to a 302 redirect for S3 or FileResponse for local.
        """
        ...


class LocalFileStorageBackend:
    def __init__(self, base_dir: str | None = None) -> None:
        root = Path(base_dir or settings.upload_dir)
        self.base_dir = root
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save_bytes(
        self, *, relative_path: str, content: bytes, mime_type: str
    ) -> StoredObject:
        target = self.base_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_bytes(content)
        return StoredObject(
            storage_path=relative_path,
            size_bytes=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
        )

    async def exists(self, relative_path: str) -> bool:
        return (self.base_dir / relative_path).exists()

    async def delete(self, relative_path: str) -> None:
        target = self.base_dir / relative_path
        if target.exists():
            target.unlink()

    async def local_path(self, relative_path: str) -> Path:
        target = self.base_dir / relative_path
        if not target.exists():
            raise NotFoundError("Stored file not found", error_code="ERR-DOC-404")
        return target

    async def get_bytes(self, relative_path: str) -> bytes:
        """Return raw file content. Raises NotFoundError if missing."""
        target = self.base_dir / relative_path
        if not target.exists():
            raise NotFoundError("Stored file not found", error_code="ERR-DOC-404")
        return target.read_bytes()

    async def presign_get(
        self,
        relative_path: str,
        expires_in: int | None = None,
        *,
        response_filename: str | None = None,
    ) -> str:
        """Return relative path as a local placeholder (no real presigning).

        serve_file() detects that this is not an HTTP URL and falls back to
        FileResponse via local_path().
        """
        return relative_path


class S3FileStorageBackend:
    """Async S3-compatible document storage backend using aioboto3.

    Phase 2B: replaced blocking boto3 client + tempfile download with a fully
    async aioboto3 session.  local_path() is intentionally not implemented —
    callers that need a local file for download responses will be updated to
    presigned URLs in Prompt 6.  Server-side callers (version restore, etc.)
    should use get_bytes() instead.
    """

    def __init__(self) -> None:
        self._bucket = settings.document_storage_bucket
        self._client_kwargs: dict[str, Any] = {
            "endpoint_url": settings.document_storage_endpoint or None,
            "region_name": settings.document_storage_region,
            "aws_access_key_id": settings.document_storage_access_key or None,
            "aws_secret_access_key": settings.document_storage_secret_key or None,
        }
        if settings.document_storage_force_path_style:
            from aiobotocore.config import AioConfig  # noqa: PLC0415
            self._client_kwargs["config"] = AioConfig(s3={"addressing_style": "path"})

    def _client(self) -> Any:
        """Return a new aioboto3 S3 client async context manager."""
        return _get_s3_doc_session().client("s3", **self._client_kwargs)

    async def save_bytes(
        self, *, relative_path: str, content: bytes, mime_type: str
    ) -> StoredObject:
        put_kwargs: dict[str, Any] = {
            "Bucket": self._bucket,
            "Key": relative_path,
            "Body": content,
            "ContentType": mime_type,
            "CacheControl": "private, max-age=300",
        }
        if settings.s3_sse_enabled:
            put_kwargs["ServerSideEncryption"] = "AES256"
        async with self._client() as s3:
            await s3.put_object(**put_kwargs)
        return StoredObject(
            storage_path=relative_path,
            size_bytes=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
        )

    async def exists(self, relative_path: str) -> bool:
        from botocore.exceptions import ClientError  # noqa: PLC0415

        async with self._client() as s3:
            try:
                await s3.head_object(Bucket=self._bucket, Key=relative_path)
                return True
            except ClientError as exc:
                if exc.response["Error"]["Code"] in ("404", "NoSuchKey"):
                    return False
                raise

    async def delete(self, relative_path: str) -> None:
        from botocore.exceptions import ClientError  # noqa: PLC0415

        async with self._client() as s3:
            try:
                await s3.delete_object(Bucket=self._bucket, Key=relative_path)
            except ClientError:
                pass

    async def local_path(self, relative_path: str) -> Path:
        """Not implemented on S3 backend.

        Download routes must use presigned URLs (Prompt 6).
        For server-side byte access use get_bytes() instead.
        """
        raise NotImplementedError(
            "S3FileStorageBackend does not support local_path(). "
            "Call get_bytes() for server-side processing or obtain a presigned "
            "URL via storage.presign_get() for download responses (Prompt 6)."
        )

    async def get_bytes(self, relative_path: str) -> bytes:
        """Download S3 object body into memory.

        Suitable for server-side processing (version restore, zip assembly).
        Warning: reads the full object into memory; avoid for objects >100 MB.
        For large streaming downloads, use presigned URLs (Prompt 6).
        """
        from botocore.exceptions import ClientError  # noqa: PLC0415

        async with self._client() as s3:
            try:
                response = await s3.get_object(Bucket=self._bucket, Key=relative_path)
                return await response["Body"].read()
            except ClientError as exc:
                if exc.response["Error"]["Code"] in ("404", "NoSuchKey"):
                    raise NotFoundError("Stored file not found", error_code="ERR-DOC-404")
                raise

    async def presign_get(
        self,
        relative_path: str,
        expires_in: int | None = None,
        *,
        response_filename: str | None = None,
    ) -> str:
        """Return a short-lived presigned GET URL for the S3 object.

        Args:
            relative_path:     S3 object key.
            expires_in:        TTL in seconds; defaults to
                               ``settings.s3_presign_get_ttl_seconds``.
            response_filename: When set, embeds a ``Content-Disposition:
                               attachment; filename*=UTF-8''...`` header in the
                               presigned URL so browsers save with the right name.
        """
        from urllib.parse import quote  # noqa: PLC0415

        ttl = expires_in if expires_in is not None else settings.s3_presign_get_ttl_seconds
        params: dict[str, Any] = {"Bucket": self._bucket, "Key": relative_path}
        if response_filename:
            params["ResponseContentDisposition"] = (
                f"attachment; filename*=UTF-8''{quote(response_filename)}"
            )
        async with self._client() as s3:
            return await s3.generate_presigned_url(
                "get_object",
                Params=params,
                ExpiresIn=ttl,
            )


class FileStorageService:
    """Storage abstraction + image preview generation."""

    def __init__(self, backend: FileStorageBackend | None = None) -> None:
        self.backend = backend or self._build_backend()

    def _build_backend(self) -> FileStorageBackend:
        if settings.document_storage_backend.lower() == "s3":
            return S3FileStorageBackend()
        return LocalFileStorageBackend()

    def compute_sha256(self, content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    async def store_upload(
        self,
        *,
        content: bytes,
        original_filename: str,
        mime_type: str,
        sha256: str | None = None,
    ) -> tuple[str, str]:
        validate_document_upload(mime_type=mime_type, size_bytes=len(content))
        await virus_scan_hook(content)
        digest = sha256 or self.compute_sha256(content)
        safe_name = _safe_filename(original_filename)
        extension = _extension_for(safe_name, mime_type)
        relative_path = (
            f"{settings.document_storage_subdirectory}/{digest[:2]}/{digest}{extension}"
        )
        await self.backend.save_bytes(
            relative_path=relative_path,
            content=content,
            mime_type=mime_type,
        )
        thumbnail_path = await self._maybe_generate_thumbnail(
            content=content,
            sha256=digest,
            mime_type=mime_type,
        )
        return relative_path, thumbnail_path or ""

    async def reuse_upload(
        self,
        *,
        storage_path: str,
        thumbnail_path: str | None,
    ) -> tuple[str, str | None]:
        if not await self.backend.exists(storage_path):
            raise NotFoundError("Stored file not found", error_code="ERR-DOC-404")
        if thumbnail_path and not await self.backend.exists(thumbnail_path):
            thumbnail_path = None
        return storage_path, thumbnail_path

    async def store_upload_copy(
        self,
        *,
        content: bytes,
        original_filename: str,
        mime_type: str,
    ) -> tuple[str, str]:
        validate_document_upload(mime_type=mime_type, size_bytes=len(content))
        await virus_scan_hook(content)
        digest = self.compute_sha256(content)
        safe_name = _safe_filename(original_filename)
        extension = _extension_for(safe_name, mime_type)
        relative_path = (
            f"{settings.document_storage_subdirectory}/copies/"
            f"{uuid.uuid4().hex}{extension}"
        )
        await self.backend.save_bytes(
            relative_path=relative_path,
            content=content,
            mime_type=mime_type,
        )
        thumbnail_path = await self._maybe_generate_thumbnail(
            content=content,
            sha256=digest,
            mime_type=mime_type,
        )
        return relative_path, thumbnail_path or ""

    async def _maybe_generate_thumbnail(
        self,
        *,
        content: bytes,
        sha256: str,
        mime_type: str,
    ) -> str | None:
        if not mime_type.startswith("image/") or Image is None:
            return None

        try:
            with Image.open(io.BytesIO(content)) as image:
                image.thumbnail((200, 200))
                if image.mode not in ("RGB", "RGBA"):
                    image = image.convert("RGB")
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
        except Exception:  # pragma: no cover - corrupt image edge case
            return None

        relative_path = (
            f"{settings.document_preview_subdirectory}/{sha256[:2]}/{sha256}.png"
        )
        await self.backend.save_bytes(
            relative_path=relative_path,
            content=buffer.getvalue(),
            mime_type="image/png",
        )
        return relative_path

    async def local_path(self, relative_path: str) -> Path:
        return await self.backend.local_path(relative_path)

    async def get_bytes(self, relative_path: str) -> bytes:
        return await self.backend.get_bytes(relative_path)

    async def presign_get(
        self,
        relative_path: str,
        expires_in: int | None = None,
        *,
        response_filename: str | None = None,
    ) -> str:
        return await self.backend.presign_get(
            relative_path,
            expires_in,
            response_filename=response_filename,
        )

    async def exists(self, relative_path: str) -> bool:
        return await self.backend.exists(relative_path)

    async def delete(self, relative_path: str) -> None:
        await self.backend.delete(relative_path)


file_storage_service = FileStorageService()
