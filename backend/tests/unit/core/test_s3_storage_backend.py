"""Unit tests for storage backends — Phase 2B (MinIO / S3 integration).

Coverage:
  - Protocol conformance for both backends.
  - LocalStorageBackend: save / read / delete / exists / stat / presign_get.
  - S3StorageBackend: save / exists / delete / stat / presign_get (mocked client).
  - build_storage_backend factory returns the correct backend type.
  - Integration smoke test (opt-in via MINIO_INTEGRATION=1).
"""

from __future__ import annotations

import io
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.storage import (
    LocalStorageBackend,
    ObjectStat,
    S3StorageBackend,
    StorageBackend,
    build_storage_backend,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_REQUIRED_SETTINGS = dict(
    database_url="postgresql+asyncpg://u:p@localhost/db",
    redis_url="redis://localhost",
    jwt_secret_key="test",
)


def _file(content: bytes = b"hello storage") -> io.BytesIO:
    return io.BytesIO(content)


def _make_s3_backend(**overrides) -> S3StorageBackend:
    from app.core.config import Settings

    base: dict = {
        **_REQUIRED_SETTINGS,
        "s3_bucket": "test-bucket",
        "s3_endpoint": "http://fake:9000",
        "s3_access_key": "key",
        "s3_secret_key": "secret",
        "s3_force_path_style": True,
        "s3_sse_enabled": True,
        "s3_presign_get_ttl_seconds": 300,
    }
    base.update(overrides)
    return S3StorageBackend(Settings(**base))


def _make_client_ctx(mock_client: MagicMock) -> MagicMock:
    """Wrap a mock client in an async context manager."""
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=mock_client)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


@pytest.fixture()
def tmp_local(tmp_path: Path) -> LocalStorageBackend:
    return LocalStorageBackend(upload_dir=str(tmp_path))


@pytest.fixture()
def s3_backend() -> S3StorageBackend:
    return _make_s3_backend()


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


class TestProtocolConformance:
    def test_local_implements_protocol(self, tmp_local):
        assert isinstance(tmp_local, StorageBackend)

    def test_s3_implements_protocol(self, s3_backend):
        assert isinstance(s3_backend, StorageBackend)


# ---------------------------------------------------------------------------
# LocalStorageBackend
# ---------------------------------------------------------------------------


class TestLocalStorageBackendSave:
    async def test_returns_relative_path_sha256_size(self, tmp_local):
        rel, sha, size = await tmp_local.save(_file(b"data"), "test.pdf")
        assert rel.endswith("test.pdf")
        assert len(sha) == 64
        assert size == 4

    async def test_with_subdirectory(self, tmp_local):
        rel, _, _ = await tmp_local.save(_file(), "doc.pdf", subdirectory="submissions")
        assert rel.startswith("submissions/")

    async def test_unique_filenames_per_save(self, tmp_local):
        r1, _, _ = await tmp_local.save(_file(), "file.pdf")
        r2, _, _ = await tmp_local.save(_file(), "file.pdf")
        assert r1 != r2


class TestLocalStorageBackendExistsReadDelete:
    async def test_exists_after_save(self, tmp_local):
        rel, _, _ = await tmp_local.save(_file(), "x.pdf")
        assert await tmp_local.exists(rel)

    async def test_exists_false_for_missing(self, tmp_local):
        assert not await tmp_local.exists("nonexistent/file.pdf")

    async def test_read_returns_path(self, tmp_local):
        rel, _, _ = await tmp_local.save(_file(), "f.pdf")
        path = await tmp_local.read(rel)
        assert isinstance(path, Path)
        assert path.exists()

    async def test_delete_removes_file(self, tmp_local):
        rel, _, _ = await tmp_local.save(_file(), "del.pdf")
        await tmp_local.delete(rel)
        assert not await tmp_local.exists(rel)

    async def test_delete_noop_for_missing(self, tmp_local):
        await tmp_local.delete("missing.pdf")  # must not raise


class TestLocalStorageBackendStat:
    async def test_stat_returns_object_stat(self, tmp_local):
        content = b"stat test content"
        rel, _, _ = await tmp_local.save(io.BytesIO(content), "stat.txt")
        info = await tmp_local.stat(rel)
        assert isinstance(info, ObjectStat)
        assert info.size_bytes == len(content)
        assert info.content_type == "text/plain"
        assert info.etag != ""
        assert info.last_modified is not None

    async def test_stat_raises_not_found_for_missing(self, tmp_local):
        from app.core.exceptions import NotFoundError

        with pytest.raises(NotFoundError):
            await tmp_local.stat("missing.pdf")


class TestLocalStorageBackendPresignGet:
    async def test_returns_relative_path_string(self, tmp_local):
        rel, _, _ = await tmp_local.save(_file(), "p.pdf")
        result = await tmp_local.presign_get(rel)
        assert isinstance(result, str)
        assert result == rel

    async def test_accepts_optional_args(self, tmp_local):
        rel, _, _ = await tmp_local.save(_file(), "p.pdf")
        result = await tmp_local.presign_get(
            rel, expires_in=60, response_filename="custom.pdf"
        )
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# S3StorageBackend — mocked client
# ---------------------------------------------------------------------------


class TestS3StorageBackendSave:
    async def test_calls_put_object_and_returns_tuple(self, s3_backend):
        client = AsyncMock()
        client.put_object = AsyncMock(return_value={})
        with patch.object(s3_backend, "_client", return_value=_make_client_ctx(client)):
            key, sha, size = await s3_backend.save(_file(b"s3 data"), "upload.pdf")

        assert key.endswith("upload.pdf")
        assert size == 7
        assert len(sha) == 64
        client.put_object.assert_called_once()

    async def test_put_object_kwargs(self, s3_backend):
        client = AsyncMock()
        client.put_object = AsyncMock(return_value={})
        with patch.object(s3_backend, "_client", return_value=_make_client_ctx(client)):
            key, _, _ = await s3_backend.save(_file(b"x"), "doc.pdf")

        kw = client.put_object.call_args.kwargs
        assert kw["Bucket"] == "test-bucket"
        assert kw["Key"] == key
        assert kw["CacheControl"] == "private, max-age=300"
        assert kw["ServerSideEncryption"] == "AES256"
        assert kw["ContentType"] == "application/pdf"

    async def test_subdirectory_prefixes_key(self, s3_backend):
        client = AsyncMock()
        client.put_object = AsyncMock(return_value={})
        with patch.object(s3_backend, "_client", return_value=_make_client_ctx(client)):
            key, _, _ = await s3_backend.save(
                _file(), "f.pdf", subdirectory="schools/1"
            )
        assert key.startswith("schools/1/")
        assert not key.startswith("/")

    async def test_sse_omitted_when_disabled(self):
        backend = _make_s3_backend(s3_sse_enabled=False)
        client = AsyncMock()
        client.put_object = AsyncMock(return_value={})
        with patch.object(backend, "_client", return_value=_make_client_ctx(client)):
            await backend.save(_file(), "f.pdf")
        kw = client.put_object.call_args.kwargs
        assert "ServerSideEncryption" not in kw


class TestS3StorageBackendExists:
    async def test_true_when_head_succeeds(self, s3_backend):
        client = AsyncMock()
        client.head_object = AsyncMock(return_value={"ContentLength": 10})
        with patch.object(s3_backend, "_client", return_value=_make_client_ctx(client)):
            assert await s3_backend.exists("some/key.pdf") is True

    async def test_false_on_404(self, s3_backend):
        from botocore.exceptions import ClientError

        client = AsyncMock()
        err = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadObject"
        )
        client.head_object = AsyncMock(side_effect=err)
        with patch.object(s3_backend, "_client", return_value=_make_client_ctx(client)):
            assert await s3_backend.exists("missing.pdf") is False


class TestS3StorageBackendDelete:
    async def test_calls_delete_object(self, s3_backend):
        client = AsyncMock()
        client.delete_object = AsyncMock(return_value={})
        with patch.object(s3_backend, "_client", return_value=_make_client_ctx(client)):
            await s3_backend.delete("some/key.pdf")
        client.delete_object.assert_called_once_with(
            Bucket="test-bucket", Key="some/key.pdf"
        )

    async def test_suppresses_client_error(self, s3_backend):
        from botocore.exceptions import ClientError

        client = AsyncMock()
        err = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": ""}}, "DeleteObject"
        )
        client.delete_object = AsyncMock(side_effect=err)
        with patch.object(s3_backend, "_client", return_value=_make_client_ctx(client)):
            await s3_backend.delete("missing.pdf")  # must not raise


class TestS3StorageBackendStat:
    async def test_parses_head_response(self, s3_backend):
        client = AsyncMock()
        client.head_object = AsyncMock(
            return_value={
                "ContentLength": 1024,
                "ETag": '"abc123"',
                "ContentType": "application/pdf",
                "LastModified": datetime(2026, 1, 1),
            }
        )
        with patch.object(s3_backend, "_client", return_value=_make_client_ctx(client)):
            info = await s3_backend.stat("doc.pdf")

        assert info.size_bytes == 1024
        assert info.etag == "abc123"
        assert info.content_type == "application/pdf"
        assert info.last_modified == datetime(2026, 1, 1)

    async def test_raises_not_found_on_404(self, s3_backend):
        from app.core.exceptions import NotFoundError
        from botocore.exceptions import ClientError

        client = AsyncMock()
        err = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadObject"
        )
        client.head_object = AsyncMock(side_effect=err)
        with patch.object(s3_backend, "_client", return_value=_make_client_ctx(client)):
            with pytest.raises(NotFoundError):
                await s3_backend.stat("missing.pdf")


class TestS3StorageBackendPresignGet:
    async def test_returns_signed_url(self, s3_backend):
        client = AsyncMock()
        client.generate_presigned_url = AsyncMock(return_value="https://minio/signed")
        with patch.object(s3_backend, "_client", return_value=_make_client_ctx(client)):
            url = await s3_backend.presign_get("doc.pdf")
        assert url == "https://minio/signed"

    async def test_uses_default_ttl(self, s3_backend):
        client = AsyncMock()
        client.generate_presigned_url = AsyncMock(return_value="https://minio/url")
        with patch.object(s3_backend, "_client", return_value=_make_client_ctx(client)):
            await s3_backend.presign_get("doc.pdf")
        assert client.generate_presigned_url.call_args.kwargs["ExpiresIn"] == 300

    async def test_overrides_ttl(self, s3_backend):
        client = AsyncMock()
        client.generate_presigned_url = AsyncMock(return_value="https://minio/url")
        with patch.object(s3_backend, "_client", return_value=_make_client_ctx(client)):
            await s3_backend.presign_get("doc.pdf", expires_in=7200)
        assert client.generate_presigned_url.call_args.kwargs["ExpiresIn"] == 7200

    async def test_adds_response_content_disposition(self, s3_backend):
        client = AsyncMock()
        client.generate_presigned_url = AsyncMock(return_value="https://minio/url")
        with patch.object(s3_backend, "_client", return_value=_make_client_ctx(client)):
            await s3_backend.presign_get("doc.pdf", response_filename="my-doc.pdf")
        params = client.generate_presigned_url.call_args.kwargs["Params"]
        assert "ResponseContentDisposition" in params
        assert "my-doc.pdf" in params["ResponseContentDisposition"]

    async def test_read_raises_not_implemented(self, s3_backend):
        with pytest.raises(NotImplementedError):
            await s3_backend.read("any/path.pdf")


# ---------------------------------------------------------------------------
# build_storage_backend factory
# ---------------------------------------------------------------------------


class TestBuildStorageBackend:
    def test_returns_local_when_storage_backend_local(self, monkeypatch):
        monkeypatch.delenv("STORAGE_BACKEND", raising=False)
        from app.core.config import Settings

        cfg = Settings(**_REQUIRED_SETTINGS, storage_backend="local")
        assert isinstance(build_storage_backend(cfg), LocalStorageBackend)

    def test_returns_s3_when_storage_backend_s3(self, monkeypatch):
        monkeypatch.delenv("STORAGE_BACKEND", raising=False)
        from app.core.config import Settings

        cfg = Settings(
            **_REQUIRED_SETTINGS,
            storage_backend="s3",
            s3_bucket="b",
            s3_endpoint="http://fake:9000",
            s3_access_key="k",
            s3_secret_key="s",
        )
        assert isinstance(build_storage_backend(cfg), S3StorageBackend)


# ---------------------------------------------------------------------------
# Integration test — opt-in with MINIO_INTEGRATION=1
# Requires dev MinIO running: docker compose -f infra/docker-compose.dev.yml up minio
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not os.getenv("MINIO_INTEGRATION"),
    reason="Set MINIO_INTEGRATION=1 to run against dev MinIO",
)
class TestMinIOIntegration:
    @pytest.fixture()
    def minio_backend(self) -> S3StorageBackend:
        from app.core.config import Settings

        endpoint = os.getenv("S3_ENDPOINT", "http://minio:9000")
        return S3StorageBackend(
            Settings(
                **_REQUIRED_SETTINGS,
                s3_bucket=os.getenv("S3_BUCKET", "ecole-dev-private"),
                s3_endpoint=endpoint,
                s3_access_key=os.getenv("S3_ACCESS_KEY", "minioadmin"),
                s3_secret_key=os.getenv("S3_SECRET_KEY", "minioadmin123"),
                s3_force_path_style=True,
                s3_sse_enabled=True,
            )
        )

    async def test_full_round_trip(self, minio_backend):
        content = b"integration test content"
        key, sha, size = await minio_backend.save(io.BytesIO(content), "integ.txt")

        assert size == len(content)
        assert await minio_backend.exists(key)

        info = await minio_backend.stat(key)
        assert info.size_bytes == len(content)
        assert info.content_type == "text/plain"

        url = await minio_backend.presign_get(key, expires_in=60)
        assert url.startswith("http")

        await minio_backend.delete(key)
        assert not await minio_backend.exists(key)
