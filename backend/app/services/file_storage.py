"""Phase 16 file storage service with local and S3-compatible backends."""

from __future__ import annotations

import hashlib
import io
import mimetypes
import re
import socket
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

from app.core.config import settings
from app.core.exceptions import NotFoundError, ValidationError

try:  # pragma: no cover - optional runtime dependency
    import boto3
except Exception:  # pragma: no cover - handled at runtime
    boto3 = None

try:  # pragma: no cover - optional runtime dependency
    from PIL import Image
except Exception:  # pragma: no cover - handled at runtime
    Image = None


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
    async def save_bytes(self, *, relative_path: str, content: bytes, mime_type: str) -> StoredObject:
        ...

    async def exists(self, relative_path: str) -> bool:
        ...

    async def delete(self, relative_path: str) -> None:
        ...

    async def local_path(self, relative_path: str) -> Path:
        ...


class LocalFileStorageBackend:
    def __init__(self, base_dir: str | None = None) -> None:
        root = Path(base_dir or settings.upload_dir)
        self.base_dir = root
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save_bytes(self, *, relative_path: str, content: bytes, mime_type: str) -> StoredObject:
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


class S3FileStorageBackend:
    def __init__(self, client=None) -> None:
        if client is None:
            if boto3 is None:  # pragma: no cover - optional dependency
                raise RuntimeError("boto3 is required for the S3 storage backend")
            client = boto3.client(
                "s3",
                endpoint_url=settings.document_storage_endpoint or None,
                region_name=settings.document_storage_region,
                aws_access_key_id=settings.document_storage_access_key or None,
                aws_secret_access_key=settings.document_storage_secret_key or None,
            )
        self.client = client
        self.bucket = settings.document_storage_bucket

    async def save_bytes(self, *, relative_path: str, content: bytes, mime_type: str) -> StoredObject:
        self.client.put_object(
            Bucket=self.bucket,
            Key=relative_path,
            Body=content,
            ContentType=mime_type,
        )
        return StoredObject(
            storage_path=relative_path,
            size_bytes=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
        )

    async def exists(self, relative_path: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=relative_path)
            return True
        except Exception:  # pragma: no cover - client-specific
            return False

    async def delete(self, relative_path: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=relative_path)

    async def local_path(self, relative_path: str) -> Path:
        temp_dir = Path(tempfile.gettempdir()) / "ecole-platform-documents"
        temp_dir.mkdir(parents=True, exist_ok=True)
        target = temp_dir / Path(relative_path).name
        with target.open("wb") as handle:
            self.client.download_fileobj(self.bucket, relative_path, handle)
        return target


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

    async def exists(self, relative_path: str) -> bool:
        return await self.backend.exists(relative_path)

    async def delete(self, relative_path: str) -> None:
        await self.backend.delete(relative_path)


file_storage_service = FileStorageService()
