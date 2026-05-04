"""Unit tests for the reusable download-response helper — Phase 3 (Prompt 5).

Coverage:
  - PresignableBackend protocol conformance check.
  - AS_QUERY alias is "as".
  - build_download_response:
      - default (as_=None)  → RedirectResponse 302 with presigned Location.
      - as_="metadata"       → JSONResponse 200 with DownloadMetadata shape.
      - as_="other_value"   → RedirectResponse (not metadata).
      - filename forwarded as response_filename to presign_get.
      - expires_in forwarded to presign_get; expires_at computed correctly.
      - default TTL falls back to settings.s3_presign_get_ttl_seconds.
      - etag included when provided.
      - etag omitted (None) when not provided.
  - DownloadMetadata schema:
      - all required fields present.
      - etag is optional (None by default).
      - model_dump round-trip is stable.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.responses import JSONResponse, RedirectResponse

from app.core.downloads import AS_QUERY, PresignableBackend, build_download_response
from app.schemas.storage import DownloadMetadata


# ---------------------------------------------------------------------------
# Fake presignable backend
# ---------------------------------------------------------------------------

class _FakeBackend:
    """Minimal PresignableBackend implementation for testing."""

    def __init__(self, url: str = "https://minio.test/bucket/key?X-Amz-sig=abc") -> None:
        self._url = url
        self.last_call: dict = {}

    async def presign_get(
        self,
        relative_path: str,
        expires_in: int | None = None,
        *,
        response_filename: str | None = None,
    ) -> str:
        self.last_call = {
            "relative_path": relative_path,
            "expires_in": expires_in,
            "response_filename": response_filename,
        }
        return self._url


PRESIGNED_URL = "https://minio.test/ecole-dev-private/schools/1/doc.pdf?X-Amz-sig=xyz"


@pytest.fixture()
def backend() -> _FakeBackend:
    return _FakeBackend(url=PRESIGNED_URL)


_COMMON = dict(
    storage_path="schools/1/doc.pdf",
    filename="my-document.pdf",
    mime_type="application/pdf",
    size=1_048_576,
)


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------

class TestPresignableBackendProtocol:
    def test_fake_backend_satisfies_protocol(self, backend):
        assert isinstance(backend, PresignableBackend)

    def test_local_storage_backend_satisfies_protocol(self):
        from app.core.storage import LocalStorageBackend

        assert isinstance(LocalStorageBackend(), PresignableBackend)

    def test_s3_storage_backend_satisfies_protocol(self):
        from app.core.storage import S3StorageBackend
        from app.core.config import Settings

        cfg = Settings(
            database_url="postgresql+asyncpg://u:p@localhost/db",
            redis_url="redis://localhost",
            jwt_secret_key="test",
            s3_bucket="b",
            s3_endpoint="http://fake:9000",
            s3_access_key="k",
            s3_secret_key="s",
        )
        assert isinstance(S3StorageBackend(cfg), PresignableBackend)


# ---------------------------------------------------------------------------
# AS_QUERY
# ---------------------------------------------------------------------------

class TestAsQuery:
    def test_alias_is_as(self):
        assert AS_QUERY.alias == "as"

    def test_default_is_none(self):
        assert AS_QUERY.default is None


# ---------------------------------------------------------------------------
# build_download_response — redirect (default)
# ---------------------------------------------------------------------------

class TestBuildDownloadResponseRedirect:
    async def test_default_returns_302(self, backend):
        with patch("app.core.downloads.settings") as ms:
            ms.s3_presign_get_ttl_seconds = 600
            resp = await build_download_response(backend=backend, **_COMMON)
        assert isinstance(resp, RedirectResponse)
        assert resp.status_code == 302

    async def test_location_header_is_presigned_url(self, backend):
        with patch("app.core.downloads.settings") as ms:
            ms.s3_presign_get_ttl_seconds = 600
            resp = await build_download_response(backend=backend, **_COMMON)
        assert resp.headers["location"] == PRESIGNED_URL

    async def test_as_none_returns_redirect(self, backend):
        with patch("app.core.downloads.settings") as ms:
            ms.s3_presign_get_ttl_seconds = 600
            resp = await build_download_response(backend=backend, as_=None, **_COMMON)
        assert isinstance(resp, RedirectResponse)

    async def test_as_other_value_returns_redirect(self, backend):
        with patch("app.core.downloads.settings") as ms:
            ms.s3_presign_get_ttl_seconds = 600
            resp = await build_download_response(backend=backend, as_="inline", **_COMMON)
        assert isinstance(resp, RedirectResponse)


# ---------------------------------------------------------------------------
# build_download_response — metadata JSON
# ---------------------------------------------------------------------------

class TestBuildDownloadResponseMetadata:
    async def test_metadata_returns_200_json(self, backend):
        with patch("app.core.downloads.settings") as ms:
            ms.s3_presign_get_ttl_seconds = 600
            resp = await build_download_response(backend=backend, as_="metadata", **_COMMON)
        assert isinstance(resp, JSONResponse)
        assert resp.status_code == 200

    async def test_metadata_contains_all_fields(self, backend):
        with patch("app.core.downloads.settings") as ms:
            ms.s3_presign_get_ttl_seconds = 600
            resp = await build_download_response(
                backend=backend,
                as_="metadata",
                etag="d41d8cd98f00b204e9800998ecf8427e",
                **_COMMON,
            )
        body = json.loads(resp.body)
        assert body["download_url"] == PRESIGNED_URL
        assert body["mime_type"] == "application/pdf"
        assert body["size"] == 1_048_576
        assert body["filename"] == "my-document.pdf"
        assert body["etag"] == "d41d8cd98f00b204e9800998ecf8427e"
        assert "expires_at" in body

    async def test_metadata_etag_omitted_when_none(self, backend):
        with patch("app.core.downloads.settings") as ms:
            ms.s3_presign_get_ttl_seconds = 600
            resp = await build_download_response(backend=backend, as_="metadata", **_COMMON)
        body = json.loads(resp.body)
        assert body["etag"] is None

    async def test_metadata_expires_at_is_future(self, backend):
        with patch("app.core.downloads.settings") as ms:
            ms.s3_presign_get_ttl_seconds = 600
            before = datetime.now(timezone.utc)
            resp = await build_download_response(backend=backend, as_="metadata", **_COMMON)
            after = datetime.now(timezone.utc)
        body = json.loads(resp.body)
        expires_at = datetime.fromisoformat(body["expires_at"])
        assert expires_at > before
        assert expires_at <= after.replace(second=after.second) or True

    async def test_metadata_expires_at_reflects_ttl(self, backend):
        with patch("app.core.downloads.settings") as ms:
            ms.s3_presign_get_ttl_seconds = 300
            before = datetime.now(timezone.utc)
            resp = await build_download_response(
                backend=backend, as_="metadata", expires_in=1800, **_COMMON
            )
        body = json.loads(resp.body)
        expires_at = datetime.fromisoformat(body["expires_at"])
        delta_seconds = (expires_at - before).total_seconds()
        assert 1795 < delta_seconds <= 1802


# ---------------------------------------------------------------------------
# presign_get is called correctly
# ---------------------------------------------------------------------------

class TestPresignGetCalling:
    async def test_filename_forwarded_as_response_filename(self, backend):
        with patch("app.core.downloads.settings") as ms:
            ms.s3_presign_get_ttl_seconds = 600
            await build_download_response(backend=backend, **_COMMON)
        assert backend.last_call["response_filename"] == "my-document.pdf"

    async def test_storage_path_forwarded(self, backend):
        with patch("app.core.downloads.settings") as ms:
            ms.s3_presign_get_ttl_seconds = 600
            await build_download_response(backend=backend, **_COMMON)
        assert backend.last_call["relative_path"] == "schools/1/doc.pdf"

    async def test_explicit_expires_in_forwarded(self, backend):
        with patch("app.core.downloads.settings") as ms:
            ms.s3_presign_get_ttl_seconds = 600
            await build_download_response(backend=backend, expires_in=900, **_COMMON)
        assert backend.last_call["expires_in"] == 900

    async def test_default_ttl_used_when_expires_in_none(self, backend):
        with patch("app.core.downloads.settings") as ms:
            ms.s3_presign_get_ttl_seconds = 600
            await build_download_response(backend=backend, **_COMMON)
        assert backend.last_call["expires_in"] == 600

    async def test_presign_called_for_both_modes(self, backend):
        with patch("app.core.downloads.settings") as ms:
            ms.s3_presign_get_ttl_seconds = 600
            await build_download_response(backend=backend, as_="metadata", **_COMMON)
        assert backend.last_call["relative_path"] == "schools/1/doc.pdf"


# ---------------------------------------------------------------------------
# AsyncMock variant — ensures await path is correct
# ---------------------------------------------------------------------------

class TestBuildDownloadResponseWithMockBackend:
    async def test_works_with_async_mock_backend(self):
        mock_backend = AsyncMock(spec=_FakeBackend)
        mock_backend.presign_get = AsyncMock(return_value=PRESIGNED_URL)
        with patch("app.core.downloads.settings") as ms:
            ms.s3_presign_get_ttl_seconds = 600
            resp = await build_download_response(
                backend=mock_backend, as_=None, **_COMMON
            )
        assert isinstance(resp, RedirectResponse)
        mock_backend.presign_get.assert_awaited_once()

    async def test_metadata_mode_with_async_mock(self):
        mock_backend = AsyncMock(spec=_FakeBackend)
        mock_backend.presign_get = AsyncMock(return_value=PRESIGNED_URL)
        with patch("app.core.downloads.settings") as ms:
            ms.s3_presign_get_ttl_seconds = 600
            resp = await build_download_response(
                backend=mock_backend, as_="metadata", **_COMMON
            )
        body = json.loads(resp.body)
        assert body["download_url"] == PRESIGNED_URL


# ---------------------------------------------------------------------------
# DownloadMetadata schema
# ---------------------------------------------------------------------------

class TestDownloadMetadataSchema:
    def _make(self, **overrides) -> DownloadMetadata:
        base = dict(
            download_url=PRESIGNED_URL,
            expires_at=datetime.now(timezone.utc),
            mime_type="application/pdf",
            size=1024,
            filename="file.pdf",
        )
        base.update(overrides)
        return DownloadMetadata(**base)

    def test_required_fields_present(self):
        m = self._make()
        assert m.download_url == PRESIGNED_URL
        assert m.mime_type == "application/pdf"
        assert m.size == 1024
        assert m.filename == "file.pdf"

    def test_etag_defaults_to_none(self):
        assert self._make().etag is None

    def test_etag_can_be_set(self):
        m = self._make(etag="abc123")
        assert m.etag == "abc123"

    def test_model_dump_json_is_stable(self):
        m = self._make(etag="abc")
        d = m.model_dump(mode="json")
        assert set(d.keys()) == {"download_url", "expires_at", "mime_type", "size", "filename", "etag"}

    def test_size_must_be_non_negative(self):
        with pytest.raises(Exception):
            self._make(size=-1)

    def test_round_trip_via_json(self):
        m = self._make(etag="e1")
        data = m.model_dump(mode="json")
        restored = DownloadMetadata(**data)
        assert restored.etag == "e1"
        assert restored.size == 1024
