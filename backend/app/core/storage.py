"""File storage abstraction — StorageBackend protocol + LocalStorageBackend + S3StorageBackend.

Reference: Phase 3B — File Upload & Storage Pipeline; Phase 2B — MinIO integration.
Provides: save, read, delete, exists, presign_get, stat operations.
Virus scan hook is a no-op placeholder (to be replaced by ClamAV integration later).
"""

from __future__ import annotations

import hashlib
import mimetypes
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, BinaryIO, Protocol, runtime_checkable

from app.core.config import Settings, settings
from app.core.exceptions import ValidationError


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ObjectStat:
    """File/object metadata returned by StorageBackend.stat()."""

    size_bytes: int
    etag: str
    content_type: str
    last_modified: datetime | None


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class StorageBackend(Protocol):
    """Abstract storage backend protocol.

    Implementations: LocalStorageBackend, S3StorageBackend.
    """

    async def save(
        self,
        file: BinaryIO,
        filename: str,
        *,
        subdirectory: str = "",
    ) -> tuple[str, str, int]:
        """Save a file and return (relative_path, sha256_checksum, file_size)."""
        ...

    async def read(self, relative_path: str) -> Path:
        """Return the absolute path to a stored file.

        Note: S3StorageBackend raises NotImplementedError — use presign_get() for S3.
        Raises NotFoundError if missing (local backend only).
        """
        ...

    async def delete(self, relative_path: str) -> None:
        """Delete a stored file. No-op if file does not exist."""
        ...

    async def exists(self, relative_path: str) -> bool:
        """Check if a file exists in storage."""
        ...

    async def presign_get(
        self,
        relative_path: str,
        expires_in: int | None = None,
        *,
        response_filename: str | None = None,
    ) -> str:
        """Return a URL allowing the file to be downloaded without further auth.

        S3/MinIO: returns a presigned URL (expires in `expires_in` seconds).
        Local: returns the relative path as a placeholder (API wiring in Prompt 6).
        """
        ...

    async def presign_put(
        self,
        relative_path: str,
        *,
        expires_in: int,
        content_type: str,
        max_size: int,
    ) -> str:
        """Return a presigned PUT URL for a direct client-to-storage upload.

        S3/MinIO: signs the URL with ContentType; client must send matching header.
        Local: raises NotImplementedError — direct PUT is S3-only.
        `max_size` is used by callers to calculate TTL; not embedded in the URL.
        """
        ...

    async def stat(self, relative_path: str) -> ObjectStat:
        """Return metadata for a stored file. Raises NotFoundError if missing."""
        ...


# ---------------------------------------------------------------------------
# Helpers (unchanged from Phase 3B)
# ---------------------------------------------------------------------------

def validate_mime_type(mime_type: str) -> None:
    """Validate that the MIME type is in the allowed list."""
    allowed = {m.strip() for m in settings.allowed_mime_types.split(",")}
    if mime_type not in allowed:
        raise ValidationError(
            f"File type '{mime_type}' is not allowed",
            error_code="ERR-UPLOAD-415",
        )


def validate_file_size(size: int) -> None:
    """Validate that the file size does not exceed the maximum."""
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if size > max_bytes:
        raise ValidationError(
            f"File size {size} bytes exceeds maximum of {settings.max_file_size_mb} MB",
            error_code="ERR-UPLOAD-413",
        )


async def virus_scan_hook(file_path: Path) -> None:
    """Placeholder virus scan hook.

    In production, replace with ClamAV or similar integration.
    Raises ValidationError if the file is flagged as malicious.
    """
    # No-op — to be implemented with ClamAV in a future phase
    pass


# ---------------------------------------------------------------------------
# LocalStorageBackend
# ---------------------------------------------------------------------------

class LocalStorageBackend:
    """Store files on the local filesystem under UPLOAD_DIR.

    Directory structure: {upload_dir}/{subdirectory}/{uuid}_{filename}
    """

    def __init__(self, upload_dir: str | None = None) -> None:
        self.base_dir = Path(upload_dir or settings.upload_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save(
        self,
        file: BinaryIO,
        filename: str,
        *,
        subdirectory: str = "",
    ) -> tuple[str, str, int]:
        """Save file to local filesystem. Returns (relative_path, sha256, file_size)."""
        target_dir = self.base_dir / subdirectory if subdirectory else self.base_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        safe_name = f"{uuid.uuid4().hex}_{filename}"
        target_path = target_dir / safe_name

        sha256 = hashlib.sha256()
        total_size = 0

        with open(target_path, "wb") as f:
            while True:
                chunk = file.read(8192)
                if not chunk:
                    break
                f.write(chunk)
                sha256.update(chunk)
                total_size += len(chunk)

        validate_file_size(total_size)
        await virus_scan_hook(target_path)

        relative_path = str(target_path.relative_to(self.base_dir))
        return relative_path, sha256.hexdigest(), total_size

    async def read(self, relative_path: str) -> Path:
        """Return absolute path to file. Raises if not found."""
        from app.core.exceptions import NotFoundError

        abs_path = self.base_dir / relative_path
        if not abs_path.exists():
            raise NotFoundError("File not found", error_code="ERR-UPLOAD-404")
        return abs_path

    async def delete(self, relative_path: str) -> None:
        """Delete file from local filesystem."""
        abs_path = self.base_dir / relative_path
        if abs_path.exists():
            abs_path.unlink()

    async def exists(self, relative_path: str) -> bool:
        """Check if file exists."""
        return (self.base_dir / relative_path).exists()

    async def presign_get(
        self,
        relative_path: str,
        expires_in: int | None = None,
        *,
        response_filename: str | None = None,
    ) -> str:
        """Return relative path as a local URL placeholder.

        Full route-based presigning is wired in Prompt 6.  Until then, callers
        on the local backend should continue using read() + FileResponse.
        """
        return relative_path

    async def presign_put(
        self,
        relative_path: str,
        *,
        expires_in: int,
        content_type: str,
        max_size: int,
    ) -> str:
        """Local backend does not support direct client PUT uploads."""
        raise NotImplementedError(
            "LocalStorageBackend does not support presigned PUT. "
            "Set STORAGE_BACKEND=s3 to use direct uploads."
        )

    async def stat(self, relative_path: str) -> ObjectStat:
        """Return metadata for a locally stored file."""
        from app.core.exceptions import NotFoundError

        abs_path = self.base_dir / relative_path
        if not abs_path.exists():
            raise NotFoundError("File not found", error_code="ERR-UPLOAD-404")
        stat_result = abs_path.stat()
        content_type, _ = mimetypes.guess_type(str(abs_path))
        return ObjectStat(
            size_bytes=stat_result.st_size,
            etag=hashlib.md5(abs_path.read_bytes()).hexdigest(),  # noqa: S324
            content_type=content_type or "application/octet-stream",
            last_modified=datetime.fromtimestamp(stat_result.st_mtime),
        )


# ---------------------------------------------------------------------------
# S3StorageBackend
# ---------------------------------------------------------------------------

_s3_session: Any = None  # aioboto3.Session singleton


def _get_s3_session() -> Any:
    """Return (or lazily create) the module-level aioboto3 session singleton."""
    global _s3_session
    if _s3_session is None:
        import aioboto3  # noqa: PLC0415
        _s3_session = aioboto3.Session()
    return _s3_session


class S3StorageBackend:
    """Store files in an S3-compatible object store (MinIO / AWS S3 / R2).

    Configured via Settings.s3_* fields (see app.core.config).
    Uses a module-level aioboto3 session singleton — one session per process.
    """

    def __init__(self, cfg: Settings | None = None) -> None:
        if cfg is None:
            cfg = settings
        self._bucket = cfg.s3_bucket
        self._sse = cfg.s3_sse_enabled
        self._presign_get_ttl = cfg.s3_presign_get_ttl_seconds
        self._client_kwargs: dict[str, Any] = {
            "endpoint_url": cfg.s3_endpoint or None,
            "region_name": cfg.s3_region,
            "aws_access_key_id": cfg.s3_access_key or None,
            "aws_secret_access_key": cfg.s3_secret_key or None,
        }
        if cfg.s3_force_path_style:
            from aiobotocore.config import AioConfig  # noqa: PLC0415
            self._client_kwargs["config"] = AioConfig(s3={"addressing_style": "path"})

    def _client(self) -> Any:
        """Return a new aioboto3 S3 client async context manager."""
        return _get_s3_session().client("s3", **self._client_kwargs)

    async def save(
        self,
        file: BinaryIO,
        filename: str,
        *,
        subdirectory: str = "",
    ) -> tuple[str, str, int]:
        """Upload file to S3. Returns (object_key, sha256, size_bytes)."""
        content = file.read()
        sha256 = hashlib.sha256(content).hexdigest()
        size = len(content)
        validate_file_size(size)

        safe_name = f"{uuid.uuid4().hex}_{filename}"
        key = f"{subdirectory}/{safe_name}".lstrip("/") if subdirectory else safe_name

        content_type, _ = mimetypes.guess_type(filename)
        content_type = content_type or "application/octet-stream"

        put_kwargs: dict[str, Any] = {
            "Bucket": self._bucket,
            "Key": key,
            "Body": content,
            "ContentType": content_type,
            "CacheControl": "private, max-age=300",
        }
        if self._sse:
            put_kwargs["ServerSideEncryption"] = "AES256"

        async with self._client() as s3:
            await s3.put_object(**put_kwargs)

        return key, sha256, size

    async def read(self, relative_path: str) -> Path:
        """Not supported — use presign_get() to obtain a download URL."""
        raise NotImplementedError(
            "S3StorageBackend does not stream to a local Path. "
            "Call presign_get() to obtain a presigned download URL."
        )

    async def delete(self, relative_path: str) -> None:
        """Delete object from bucket. Silently ignores missing objects."""
        from botocore.exceptions import ClientError  # noqa: PLC0415

        async with self._client() as s3:
            try:
                await s3.delete_object(Bucket=self._bucket, Key=relative_path)
            except ClientError:
                pass

    async def exists(self, relative_path: str) -> bool:
        """Return True if the object exists in the bucket."""
        from botocore.exceptions import ClientError  # noqa: PLC0415

        async with self._client() as s3:
            try:
                await s3.head_object(Bucket=self._bucket, Key=relative_path)
                return True
            except ClientError as exc:
                if exc.response["Error"]["Code"] in ("404", "NoSuchKey"):
                    return False
                raise

    async def presign_get(
        self,
        relative_path: str,
        expires_in: int | None = None,
        *,
        response_filename: str | None = None,
    ) -> str:
        """Return a presigned GET URL for the object."""
        params: dict[str, Any] = {"Bucket": self._bucket, "Key": relative_path}
        if response_filename:
            params["ResponseContentDisposition"] = (
                f'attachment; filename="{response_filename}"'
            )
        ttl = expires_in if expires_in is not None else self._presign_get_ttl
        async with self._client() as s3:
            return await s3.generate_presigned_url(
                "get_object", Params=params, ExpiresIn=ttl
            )

    async def presign_put(
        self,
        relative_path: str,
        *,
        expires_in: int,
        content_type: str,
        max_size: int,  # noqa: ARG002 — used by callers for TTL; not embedded in URL
    ) -> str:
        """Return a presigned PUT URL for a direct client upload.

        The URL includes ContentType in the signature so MinIO rejects any PUT
        that sends a different Content-Type header, preventing MIME spoofing.
        SSE-S3 is included when enabled so the object is encrypted at rest.
        """
        params: dict[str, Any] = {
            "Bucket": self._bucket,
            "Key": relative_path,
            "ContentType": content_type,
        }
        if self._sse:
            params["ServerSideEncryption"] = "AES256"
        async with self._client() as s3:
            return await s3.generate_presigned_url(
                "put_object", Params=params, ExpiresIn=expires_in
            )

    async def stat(self, relative_path: str) -> ObjectStat:
        """Return metadata for an S3 object. Raises NotFoundError if missing."""
        from app.core.exceptions import NotFoundError  # noqa: PLC0415
        from botocore.exceptions import ClientError  # noqa: PLC0415

        async with self._client() as s3:
            try:
                resp = await s3.head_object(Bucket=self._bucket, Key=relative_path)
            except ClientError as exc:
                if exc.response["Error"]["Code"] in ("404", "NoSuchKey"):
                    raise NotFoundError("File not found", error_code="ERR-UPLOAD-404")
                raise

        return ObjectStat(
            size_bytes=resp["ContentLength"],
            etag=resp.get("ETag", "").strip('"'),
            content_type=resp.get("ContentType", "application/octet-stream"),
            last_modified=resp.get("LastModified"),
        )


# ---------------------------------------------------------------------------
# Factory + singleton
# ---------------------------------------------------------------------------

def build_storage_backend(cfg: Settings | None = None) -> LocalStorageBackend | S3StorageBackend:
    """Return the configured storage backend driven by STORAGE_BACKEND setting."""
    if cfg is None:
        cfg = settings
    if cfg.storage_backend == "s3":
        return S3StorageBackend(cfg)
    return LocalStorageBackend()


# Singleton — all callers do `from app.core.storage import storage`
storage: LocalStorageBackend | S3StorageBackend = build_storage_backend()
