"""File storage abstraction — StorageBackend protocol + LocalStorageBackend.

Reference: Phase 3B — File Upload & Storage Pipeline
Provides: save, read, delete, exists operations with SHA-256 checksum and MIME validation.
Virus scan hook is a no-op placeholder (to be replaced by ClamAV integration later).
"""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import BinaryIO, Protocol, runtime_checkable

from app.core.config import settings
from app.core.exceptions import ValidationError


@runtime_checkable
class StorageBackend(Protocol):
    """Abstract storage backend protocol.

    Implementations: LocalStorageBackend, (future) S3StorageBackend.
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
        """Return the absolute path to a stored file. Raises NotFoundError if missing."""
        ...

    async def delete(self, relative_path: str) -> None:
        """Delete a stored file. No-op if file does not exist."""
        ...

    async def exists(self, relative_path: str) -> bool:
        """Check if a file exists in storage."""
        ...


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
        # Build target directory
        target_dir = self.base_dir / subdirectory if subdirectory else self.base_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename to prevent collisions
        safe_name = f"{uuid.uuid4().hex}_{filename}"
        target_path = target_dir / safe_name

        # Write file and compute SHA-256 in a single pass
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

        # Validate file size after writing
        validate_file_size(total_size)

        # Virus scan hook
        await virus_scan_hook(target_path)

        # Return path relative to base_dir
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


# Singleton instance — used by endpoints
storage = LocalStorageBackend()
