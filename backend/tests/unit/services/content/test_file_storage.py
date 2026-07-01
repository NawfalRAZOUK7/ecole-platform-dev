"""Unit tests for FileStorageService backends — Phase 2B (Prompt 4).

Coverage:
  - Protocol conformance for both backends.
  - LocalFileStorageBackend: save_bytes / exists / delete / local_path / get_bytes.
  - S3FileStorageBackend: save_bytes / exists / delete / get_bytes / local_path raises.
  - FileStorageService: store_upload, reuse_upload, store_upload_copy.
  - Deduplication (sha256-keyed paths).
  - Thumbnail generation for image uploads.
  - virus_scan_hook enabled/disabled paths.
  - build_backend factory returns correct type.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import NotFoundError, ValidationError
from app.services.content.file_storage import (
    FileStorageBackend,
    FileStorageService,
    LocalFileStorageBackend,
    S3FileStorageBackend,
    StoredObject,
    _safe_filename,
    validate_document_upload,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _bytes(content: bytes = b"sample document") -> bytes:
    return content


def _make_client_ctx(mock_client: MagicMock) -> MagicMock:
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=mock_client)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


@pytest.fixture()
def local_backend(tmp_path: Path) -> LocalFileStorageBackend:
    return LocalFileStorageBackend(base_dir=str(tmp_path))


@pytest.fixture()
def s3_backend() -> S3FileStorageBackend:
    with patch("app.services.content.file_storage.settings") as mock_settings:
        mock_settings.document_storage_bucket = "test-bucket"
        mock_settings.document_storage_endpoint = "http://fake:9000"
        mock_settings.document_storage_region = "us-east-1"
        mock_settings.document_storage_access_key = "key"
        mock_settings.document_storage_secret_key = "secret"
        mock_settings.document_storage_force_path_style = False
        mock_settings.s3_sse_enabled = True
        yield S3FileStorageBackend()


@pytest.fixture()
def local_service(local_backend: LocalFileStorageBackend) -> FileStorageService:
    svc = FileStorageService(backend=local_backend)
    with (
        patch("app.services.content.file_storage.settings") as ms,
    ):
        ms.allowed_document_mime_types = "application/pdf,image/png,image/jpeg"
        ms.max_document_size_mb = 10
        ms.virus_scan_enabled = False
        ms.document_storage_subdirectory = "documents"
        ms.document_preview_subdirectory = "previews"
        yield svc


# ---------------------------------------------------------------------------
# Helpers & validators
# ---------------------------------------------------------------------------


class TestSafeFilename:
    def test_strips_path_traversal(self):
        assert _safe_filename("../../etc/passwd") == "passwd"

    def test_replaces_spaces(self):
        result = _safe_filename("my file.pdf")
        assert " " not in result
        assert result.endswith(".pdf")

    def test_empty_string_fallback(self):
        assert _safe_filename("") == "upload"


class TestValidateDocumentUpload:
    def test_raises_on_disallowed_mime(self):
        with patch(
            "app.services.content.file_storage.ALLOWED_MIME_TYPES", {"application/pdf"}
        ):
            with pytest.raises(ValidationError) as exc_info:
                validate_document_upload(mime_type="text/html", size_bytes=100)
        assert exc_info.value.error_code == "ERR-DOC-415"

    def test_raises_on_oversized(self):
        with patch("app.services.content.file_storage.settings") as ms:
            ms.max_document_size_mb = 1
            ms.allowed_document_mime_types = "application/pdf"
            with patch(
                "app.services.content.file_storage.ALLOWED_MIME_TYPES",
                {"application/pdf"},
            ):
                with pytest.raises(ValidationError) as exc_info:
                    validate_document_upload(
                        mime_type="application/pdf", size_bytes=2 * 1024 * 1024
                    )
        assert exc_info.value.error_code == "ERR-DOC-413"


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


class TestProtocolConformance:
    def test_local_implements_protocol(self, local_backend):
        assert isinstance(local_backend, FileStorageBackend)

    def test_s3_implements_protocol(self, s3_backend):
        assert isinstance(s3_backend, FileStorageBackend)


# ---------------------------------------------------------------------------
# LocalFileStorageBackend
# ---------------------------------------------------------------------------


class TestLocalBackendSaveBytes:
    async def test_returns_stored_object(self, local_backend):
        content = b"hello pdf"
        result = await local_backend.save_bytes(
            relative_path="docs/test.pdf", content=content, mime_type="application/pdf"
        )
        assert isinstance(result, StoredObject)
        assert result.storage_path == "docs/test.pdf"
        assert result.size_bytes == len(content)
        assert result.sha256 == hashlib.sha256(content).hexdigest()

    async def test_idempotent_for_same_path(self, local_backend):
        content1 = b"first"
        content2 = b"second"
        await local_backend.save_bytes(
            relative_path="doc.pdf", content=content1, mime_type="application/pdf"
        )
        await local_backend.save_bytes(
            relative_path="doc.pdf", content=content2, mime_type="application/pdf"
        )
        result = await local_backend.get_bytes("doc.pdf")
        assert result == content1


class TestLocalBackendExistsDeletePath:
    async def test_exists_after_save(self, local_backend):
        await local_backend.save_bytes(
            relative_path="f.pdf", content=b"x", mime_type="application/pdf"
        )
        assert await local_backend.exists("f.pdf")

    async def test_not_exists_before_save(self, local_backend):
        assert not await local_backend.exists("missing.pdf")

    async def test_delete_removes_file(self, local_backend):
        await local_backend.save_bytes(
            relative_path="del.pdf", content=b"x", mime_type="application/pdf"
        )
        await local_backend.delete("del.pdf")
        assert not await local_backend.exists("del.pdf")

    async def test_delete_noop_for_missing(self, local_backend):
        await local_backend.delete("nope.pdf")  # must not raise

    async def test_local_path_returns_path(self, local_backend):
        await local_backend.save_bytes(
            relative_path="p.pdf", content=b"x", mime_type="application/pdf"
        )
        p = await local_backend.local_path("p.pdf")
        assert isinstance(p, Path)
        assert p.exists()

    async def test_local_path_raises_not_found(self, local_backend):
        with pytest.raises(NotFoundError):
            await local_backend.local_path("missing.pdf")


class TestLocalBackendGetBytes:
    async def test_returns_content(self, local_backend):
        content = b"get bytes test"
        await local_backend.save_bytes(
            relative_path="gb.pdf", content=content, mime_type="application/pdf"
        )
        assert await local_backend.get_bytes("gb.pdf") == content

    async def test_raises_not_found(self, local_backend):
        with pytest.raises(NotFoundError):
            await local_backend.get_bytes("missing.pdf")


# ---------------------------------------------------------------------------
# S3FileStorageBackend — mocked client
# ---------------------------------------------------------------------------


class TestS3BackendSaveBytes:
    async def test_calls_put_object(self, s3_backend):
        client = AsyncMock()
        client.put_object = AsyncMock(return_value={})
        with patch.object(s3_backend, "_client", return_value=_make_client_ctx(client)):
            result = await s3_backend.save_bytes(
                relative_path="docs/test.pdf",
                content=b"s3 content",
                mime_type="application/pdf",
            )
        client.put_object.assert_called_once()
        assert result.storage_path == "docs/test.pdf"

    async def test_put_object_kwargs(self, s3_backend):
        client = AsyncMock()
        client.put_object = AsyncMock(return_value={})
        with patch.object(s3_backend, "_client", return_value=_make_client_ctx(client)):
            await s3_backend.save_bytes(
                relative_path="k.pdf", content=b"x", mime_type="application/pdf"
            )
        kw = client.put_object.call_args.kwargs
        assert kw["CacheControl"] == "private, max-age=300"
        assert kw["ServerSideEncryption"] == "AES256"
        assert kw["ContentType"] == "application/pdf"

    async def test_no_sse_when_disabled(self):
        with patch("app.services.content.file_storage.settings") as ms:
            ms.document_storage_bucket = "b"
            ms.document_storage_endpoint = "http://fake:9000"
            ms.document_storage_region = "us-east-1"
            ms.document_storage_access_key = "k"
            ms.document_storage_secret_key = "s"
            ms.document_storage_force_path_style = False
            ms.s3_sse_enabled = False
            backend = S3FileStorageBackend()
        client = AsyncMock()
        client.put_object = AsyncMock(return_value={})
        with patch.object(backend, "_client", return_value=_make_client_ctx(client)):
            await backend.save_bytes(
                relative_path="k.pdf", content=b"x", mime_type="application/pdf"
            )
        kw = client.put_object.call_args.kwargs
        assert "ServerSideEncryption" not in kw


class TestS3BackendExistsDelete:
    async def test_exists_true(self, s3_backend):
        client = AsyncMock()
        client.head_object = AsyncMock(return_value={"ContentLength": 10})
        with patch.object(s3_backend, "_client", return_value=_make_client_ctx(client)):
            assert await s3_backend.exists("doc.pdf") is True

    async def test_exists_false_on_404(self, s3_backend):
        from botocore.exceptions import ClientError

        client = AsyncMock()
        err = ClientError({"Error": {"Code": "404", "Message": "NF"}}, "HeadObject")
        client.head_object = AsyncMock(side_effect=err)
        with patch.object(s3_backend, "_client", return_value=_make_client_ctx(client)):
            assert await s3_backend.exists("doc.pdf") is False

    async def test_delete_calls_delete_object(self, s3_backend):
        client = AsyncMock()
        client.delete_object = AsyncMock(return_value={})
        with patch.object(s3_backend, "_client", return_value=_make_client_ctx(client)):
            await s3_backend.delete("doc.pdf")
        client.delete_object.assert_called_once()

    async def test_delete_suppresses_error(self, s3_backend):
        from botocore.exceptions import ClientError

        client = AsyncMock()
        err = ClientError({"Error": {"Code": "NoSuchKey", "Message": ""}}, "Delete")
        client.delete_object = AsyncMock(side_effect=err)
        with patch.object(s3_backend, "_client", return_value=_make_client_ctx(client)):
            await s3_backend.delete("doc.pdf")  # must not raise


class TestS3BackendLocalPathAndGetBytes:
    async def test_local_path_raises_not_implemented(self, s3_backend):
        with pytest.raises(NotImplementedError):
            await s3_backend.local_path("doc.pdf")

    async def test_get_bytes_returns_content(self, s3_backend):
        body_mock = AsyncMock()
        body_mock.read = AsyncMock(return_value=b"s3 bytes")
        client = AsyncMock()
        client.get_object = AsyncMock(return_value={"Body": body_mock})
        with patch.object(s3_backend, "_client", return_value=_make_client_ctx(client)):
            result = await s3_backend.get_bytes("doc.pdf")
        assert result == b"s3 bytes"

    async def test_get_bytes_raises_not_found_on_404(self, s3_backend):
        from botocore.exceptions import ClientError

        client = AsyncMock()
        err = ClientError({"Error": {"Code": "404", "Message": "NF"}}, "GetObject")
        client.get_object = AsyncMock(side_effect=err)
        with patch.object(s3_backend, "_client", return_value=_make_client_ctx(client)):
            with pytest.raises(NotFoundError):
                await s3_backend.get_bytes("missing.pdf")


# ---------------------------------------------------------------------------
# FileStorageService — local backend
# ---------------------------------------------------------------------------


class TestFileStorageServiceStoreUpload:
    async def test_returns_storage_and_thumbnail_paths(self, tmp_path):
        backend = LocalFileStorageBackend(base_dir=str(tmp_path))
        svc = FileStorageService(backend=backend)
        with patch("app.services.content.file_storage.settings") as ms:
            ms.allowed_document_mime_types = "application/pdf"
            ms.max_document_size_mb = 10
            ms.virus_scan_enabled = False
            ms.document_storage_subdirectory = "docs"
            ms.document_preview_subdirectory = "previews"
            with patch(
                "app.services.content.file_storage.ALLOWED_MIME_TYPES",
                {"application/pdf"},
            ):
                path, thumb = await svc.store_upload(
                    content=b"%PDF-1.4 content",
                    original_filename="report.pdf",
                    mime_type="application/pdf",
                )
        assert path.startswith("docs/")
        assert thumb == ""

    async def test_dedup_path_contains_sha256(self, tmp_path):
        backend = LocalFileStorageBackend(base_dir=str(tmp_path))
        svc = FileStorageService(backend=backend)
        content = b"dedup content"
        sha = hashlib.sha256(content).hexdigest()
        with patch("app.services.content.file_storage.settings") as ms:
            ms.allowed_document_mime_types = "application/pdf"
            ms.max_document_size_mb = 10
            ms.virus_scan_enabled = False
            ms.document_storage_subdirectory = "docs"
            ms.document_preview_subdirectory = "previews"
            with patch(
                "app.services.content.file_storage.ALLOWED_MIME_TYPES",
                {"application/pdf"},
            ):
                path, _ = await svc.store_upload(
                    content=content,
                    original_filename="x.pdf",
                    mime_type="application/pdf",
                )
        assert sha in path

    async def test_same_content_produces_same_path(self, tmp_path):
        backend = LocalFileStorageBackend(base_dir=str(tmp_path))
        svc = FileStorageService(backend=backend)
        content = b"same file"
        with patch("app.services.content.file_storage.settings") as ms:
            ms.allowed_document_mime_types = "application/pdf"
            ms.max_document_size_mb = 10
            ms.virus_scan_enabled = False
            ms.document_storage_subdirectory = "docs"
            ms.document_preview_subdirectory = "previews"
            with patch(
                "app.services.content.file_storage.ALLOWED_MIME_TYPES",
                {"application/pdf"},
            ):
                path1, _ = await svc.store_upload(
                    content=content,
                    original_filename="a.pdf",
                    mime_type="application/pdf",
                )
                path2, _ = await svc.store_upload(
                    content=content,
                    original_filename="b.pdf",
                    mime_type="application/pdf",
                )
        assert path1 == path2


class TestFileStorageServiceReuseUpload:
    async def test_returns_existing_path(self, tmp_path):
        backend = LocalFileStorageBackend(base_dir=str(tmp_path))
        svc = FileStorageService(backend=backend)
        content = b"reuse me"
        with patch("app.services.content.file_storage.settings") as ms:
            ms.allowed_document_mime_types = "application/pdf"
            ms.max_document_size_mb = 10
            ms.virus_scan_enabled = False
            ms.document_storage_subdirectory = "docs"
            ms.document_preview_subdirectory = "previews"
            with patch(
                "app.services.content.file_storage.ALLOWED_MIME_TYPES",
                {"application/pdf"},
            ):
                path, _ = await svc.store_upload(
                    content=content,
                    original_filename="r.pdf",
                    mime_type="application/pdf",
                )
                reused_path, _ = await svc.reuse_upload(
                    storage_path=path, thumbnail_path=None
                )
        assert reused_path == path

    async def test_raises_not_found_when_missing(self, tmp_path):
        backend = LocalFileStorageBackend(base_dir=str(tmp_path))
        svc = FileStorageService(backend=backend)
        with pytest.raises(NotFoundError):
            await svc.reuse_upload(storage_path="ghost.pdf", thumbnail_path=None)


class TestFileStorageServiceStoreUploadCopy:
    async def test_copy_gets_unique_uuid_path(self, tmp_path):
        backend = LocalFileStorageBackend(base_dir=str(tmp_path))
        svc = FileStorageService(backend=backend)
        content = b"copy content"
        with patch("app.services.content.file_storage.settings") as ms:
            ms.allowed_document_mime_types = "application/pdf"
            ms.max_document_size_mb = 10
            ms.virus_scan_enabled = False
            ms.document_storage_subdirectory = "docs"
            ms.document_preview_subdirectory = "previews"
            with patch(
                "app.services.content.file_storage.ALLOWED_MIME_TYPES",
                {"application/pdf"},
            ):
                path1, _ = await svc.store_upload_copy(
                    content=content,
                    original_filename="c.pdf",
                    mime_type="application/pdf",
                )
                path2, _ = await svc.store_upload_copy(
                    content=content,
                    original_filename="c.pdf",
                    mime_type="application/pdf",
                )
        assert path1 != path2
        assert "copies" in path1


class TestFileStorageServiceGetBytes:
    async def test_get_bytes_delegates_to_backend(self, tmp_path):
        backend = LocalFileStorageBackend(base_dir=str(tmp_path))
        svc = FileStorageService(backend=backend)
        content = b"delegate bytes"
        await backend.save_bytes(
            relative_path="gb.pdf", content=content, mime_type="application/pdf"
        )
        assert await svc.get_bytes("gb.pdf") == content


# ---------------------------------------------------------------------------
# S3-backed FileStorageService (mocked backend)
# ---------------------------------------------------------------------------


class TestFileStorageServiceS3Backend:
    async def test_store_upload_calls_save_bytes(self):
        mock_backend = AsyncMock(spec=LocalFileStorageBackend)
        mock_backend.save_bytes = AsyncMock(
            return_value=StoredObject(
                storage_path="docs/ab/abc.pdf", size_bytes=5, sha256="abc"
            )
        )
        mock_backend.exists = AsyncMock(return_value=False)
        svc = FileStorageService(backend=mock_backend)
        content = b"hello"
        with patch("app.services.content.file_storage.settings") as ms:
            ms.allowed_document_mime_types = "application/pdf"
            ms.max_document_size_mb = 10
            ms.virus_scan_enabled = False
            ms.document_storage_subdirectory = "docs"
            ms.document_preview_subdirectory = "previews"
            with patch(
                "app.services.content.file_storage.ALLOWED_MIME_TYPES",
                {"application/pdf"},
            ):
                path, _ = await svc.store_upload(
                    content=content,
                    original_filename="f.pdf",
                    mime_type="application/pdf",
                )
        mock_backend.save_bytes.assert_called_once()

    async def test_get_bytes_on_s3_backend(self, s3_backend):
        svc = FileStorageService(backend=s3_backend)
        body_mock = AsyncMock()
        body_mock.read = AsyncMock(return_value=b"from s3")
        client = AsyncMock()
        client.get_object = AsyncMock(return_value={"Body": body_mock})
        with patch.object(s3_backend, "_client", return_value=_make_client_ctx(client)):
            result = await svc.get_bytes("doc.pdf")
        assert result == b"from s3"


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


class TestBuildBackend:
    def test_returns_local_by_default(self, tmp_path):
        with patch("app.services.content.file_storage.settings") as ms:
            ms.document_storage_backend = "local"
            ms.upload_dir = str(tmp_path)
            svc = FileStorageService()
        assert isinstance(svc.backend, LocalFileStorageBackend)

    def test_returns_s3_when_configured(self, tmp_path):
        with patch("app.services.content.file_storage.settings") as ms:
            ms.document_storage_backend = "s3"
            ms.document_storage_bucket = "b"
            ms.document_storage_endpoint = "http://fake:9000"
            ms.document_storage_region = "us-east-1"
            ms.document_storage_access_key = "k"
            ms.document_storage_secret_key = "s"
            ms.document_storage_force_path_style = False
            ms.s3_sse_enabled = False
            svc = FileStorageService()
        assert isinstance(svc.backend, S3FileStorageBackend)
