"""Storage-layer API schemas — Phase 3 (MinIO / S3 API Adaptation)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DownloadMetadata(BaseModel):
    """JSON payload returned when a download endpoint is called with ?as=metadata.

    Example response::

        {
            "download_url": "https://minio.ecole.example.com/...?X-Amz-...",
            "expires_at": "2026-04-30T22:52:00Z",
            "mime_type": "application/pdf",
            "size": 1048576,
            "filename": "exercise_42.pdf",
            "etag": "d41d8cd98f00b204e9800998ecf8427e"
        }

    Notes:
        - ``download_url`` is a short-lived presigned GET URL (TTL ≤ 15 min).
          Clients should cache it for ~80 % of the TTL and refresh on 403.
        - ``expires_at`` is ISO-8601 UTC; cache until that timestamp minus a
          safety margin.
        - ``etag`` is the hex MD5 of the object content (stripped of quotes);
          omitted when the backend cannot provide it cheaply.
        - No MinIO/S3 credentials are embedded in this response.
    """

    download_url: str = Field(
        ...,
        description="Short-lived presigned GET URL for the file.",
        examples=["https://minio.ecole.example.com/ecole-dev-private/schools/42/doc.pdf?X-Amz-..."],
    )
    expires_at: datetime = Field(
        ...,
        description="UTC datetime when the presigned URL expires.",
    )
    mime_type: str = Field(
        ...,
        description="MIME type of the file (e.g. application/pdf, image/png).",
    )
    size: int = Field(
        ...,
        description="File size in bytes.",
        ge=0,
    )
    filename: str = Field(
        ...,
        description="Original filename to use for Content-Disposition on save.",
    )
    etag: str | None = Field(
        default=None,
        description="ETag (hex MD5) of the object; omitted when unavailable.",
    )
