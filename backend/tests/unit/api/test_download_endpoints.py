"""Unit tests for Phase 3B — download endpoint refactoring (Prompt 6).

Coverage:
  serve_file() helper:
    - S3 mode (presign_get returns HTTP URL) → 302 RedirectResponse.
    - S3 mode + as_="metadata" → 200 JSONResponse with DownloadMetadata shape.
    - Local mode (presign_get returns relative path) dispatched via read().
    - Local mode dispatched via local_path() when read() is absent.
    - Local mode ignores as_="metadata" and always returns FileResponse.
    - Backend with neither read() nor local_path() raises RuntimeError.

  LocalFileStorageBackend.presign_get:
    - Returns the relative_path unchanged.
    - TTL and response_filename params are accepted but ignored.

  S3FileStorageBackend.presign_get (mocked aioboto3):
    - Returns the HTTP URL produced by generate_presigned_url.
    - Adds ResponseContentDisposition when response_filename is provided.
    - Falls back to settings.s3_presign_get_ttl_seconds when expires_in=None.
    - Uses caller-supplied expires_in when provided.

  FileStorageService.presign_get:
    - Delegates to backend.presign_get with all keyword arguments.

  Refactored service-method return types:
    - get_submission_file returns (str, str, str, int) — not a Path.
    - get_exercise_pdf returns (str, str, str, int) — not a Path.
    - get_content_asset returns (str, str, str, int) — not a Path.
    - read_document_file returns (str, str, str) — not a Path.
    - get_version returns (version_obj, str) — not a Path.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse

from app.core.downloads import serve_file


# ---------------------------------------------------------------------------
# Helpers / fake backends
# ---------------------------------------------------------------------------


class _S3Backend:
    """Fake backend that behaves like an S3 backend (no read/local_path)."""

    def __init__(
        self, url: str = "https://minio.test/bucket/key?X-Amz-sig=abc"
    ) -> None:
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


class _LocalBackendWithRead:
    """Fake backend that has presign_get (returns relative path) + read()."""

    def __init__(self, local_file: Path) -> None:
        self._local_file = local_file

    async def presign_get(
        self,
        relative_path: str,
        expires_in: int | None = None,
        *,
        response_filename: str | None = None,
    ) -> str:
        return relative_path

    async def read(self, relative_path: str) -> Path:
        return self._local_file


class _LocalBackendWithLocalPath:
    """Fake backend that has presign_get + local_path() but no read()."""

    def __init__(self, local_file: Path) -> None:
        self._local_file = local_file

    async def presign_get(
        self,
        relative_path: str,
        expires_in: int | None = None,
        *,
        response_filename: str | None = None,
    ) -> str:
        return relative_path

    async def local_path(self, relative_path: str) -> Path:
        return self._local_file


class _NoLocalAccessBackend:
    """Fake backend with presign_get that returns a relative path but has no
    local file access method — should trigger RuntimeError in serve_file."""

    async def presign_get(
        self,
        relative_path: str,
        expires_in: int | None = None,
        *,
        response_filename: str | None = None,
    ) -> str:
        return relative_path


PRESIGNED_URL = "https://minio.test/ecole-dev-private/schools/1/doc.pdf?X-Amz-sig=xyz"
STORAGE_PATH = "schools/1/doc.pdf"
FILENAME = "my_document.pdf"
MIME = "application/pdf"
SIZE = 1_048_576


# ---------------------------------------------------------------------------
# serve_file — S3 mode
# ---------------------------------------------------------------------------


class TestServeFileS3Mode:
    @pytest.fixture()
    def backend(self) -> _S3Backend:
        return _S3Backend(url=PRESIGNED_URL)

    @pytest.mark.asyncio
    async def test_default_returns_302_redirect(self, backend: _S3Backend) -> None:
        response = await serve_file(
            backend=backend,
            storage_path=STORAGE_PATH,
            filename=FILENAME,
            mime_type=MIME,
            size=SIZE,
        )
        assert isinstance(response, RedirectResponse)
        assert response.status_code == 302
        assert response.headers["location"] == PRESIGNED_URL

    @pytest.mark.asyncio
    async def test_as_metadata_returns_200_json(self, backend: _S3Backend) -> None:
        response = await serve_file(
            backend=backend,
            storage_path=STORAGE_PATH,
            filename=FILENAME,
            mime_type=MIME,
            size=SIZE,
            as_="metadata",
        )
        assert isinstance(response, JSONResponse)
        assert response.status_code == 200
        body = json.loads(response.body)
        assert body["download_url"] == PRESIGNED_URL
        assert body["mime_type"] == MIME
        assert body["size"] == SIZE
        assert body["filename"] == FILENAME
        assert "expires_at" in body

    @pytest.mark.asyncio
    async def test_as_other_value_returns_redirect(self, backend: _S3Backend) -> None:
        response = await serve_file(
            backend=backend,
            storage_path=STORAGE_PATH,
            filename=FILENAME,
            mime_type=MIME,
            as_="attachment",
        )
        assert isinstance(response, RedirectResponse)
        assert response.status_code == 302

    @pytest.mark.asyncio
    async def test_filename_forwarded_to_presign(self, backend: _S3Backend) -> None:
        await serve_file(
            backend=backend,
            storage_path=STORAGE_PATH,
            filename=FILENAME,
            mime_type=MIME,
        )
        assert backend.last_call["response_filename"] == FILENAME

    @pytest.mark.asyncio
    async def test_storage_path_forwarded_to_presign(self, backend: _S3Backend) -> None:
        await serve_file(
            backend=backend,
            storage_path=STORAGE_PATH,
            filename=FILENAME,
            mime_type=MIME,
        )
        assert backend.last_call["relative_path"] == STORAGE_PATH


# ---------------------------------------------------------------------------
# serve_file — local mode (via read)
# ---------------------------------------------------------------------------


class TestServeFileLocalModeRead:
    @pytest.fixture()
    def tmp_file(self, tmp_path: Path) -> Path:
        f = tmp_path / "doc.pdf"
        f.write_bytes(b"%PDF-1.4")
        return f

    @pytest.fixture()
    def backend(self, tmp_file: Path) -> _LocalBackendWithRead:
        return _LocalBackendWithRead(local_file=tmp_file)

    @pytest.mark.asyncio
    async def test_returns_file_response(
        self, backend: _LocalBackendWithRead, tmp_file: Path
    ) -> None:
        response = await serve_file(
            backend=backend,
            storage_path="schools/1/doc.pdf",
            filename="doc.pdf",
            mime_type="application/pdf",
        )
        assert isinstance(response, FileResponse)

    @pytest.mark.asyncio
    async def test_metadata_param_ignored_returns_file_response(
        self, backend: _LocalBackendWithRead
    ) -> None:
        response = await serve_file(
            backend=backend,
            storage_path="schools/1/doc.pdf",
            filename="doc.pdf",
            mime_type="application/pdf",
            as_="metadata",
        )
        assert isinstance(response, FileResponse)


# ---------------------------------------------------------------------------
# serve_file — local mode (via local_path)
# ---------------------------------------------------------------------------


class TestServeFileLocalModeLocalPath:
    @pytest.fixture()
    def tmp_file(self, tmp_path: Path) -> Path:
        f = tmp_path / "doc.pdf"
        f.write_bytes(b"%PDF-1.4")
        return f

    @pytest.fixture()
    def backend(self, tmp_file: Path) -> _LocalBackendWithLocalPath:
        return _LocalBackendWithLocalPath(local_file=tmp_file)

    @pytest.mark.asyncio
    async def test_returns_file_response(
        self, backend: _LocalBackendWithLocalPath
    ) -> None:
        response = await serve_file(
            backend=backend,
            storage_path="schools/1/doc.pdf",
            filename="doc.pdf",
            mime_type="application/pdf",
        )
        assert isinstance(response, FileResponse)


# ---------------------------------------------------------------------------
# serve_file — no local access raises RuntimeError
# ---------------------------------------------------------------------------


class TestServeFileNoLocalAccess:
    @pytest.mark.asyncio
    async def test_raises_runtime_error(self) -> None:
        backend = _NoLocalAccessBackend()
        with pytest.raises(RuntimeError, match="does not support local file access"):
            await serve_file(
                backend=backend,
                storage_path="schools/1/doc.pdf",
                filename="doc.pdf",
                mime_type="application/pdf",
            )


# ---------------------------------------------------------------------------
# LocalFileStorageBackend.presign_get
# ---------------------------------------------------------------------------


class TestLocalFileStorageBackendPresignGet:
    @pytest.fixture()
    def backend(self, tmp_path: Path):
        from app.services.file_storage import LocalFileStorageBackend

        return LocalFileStorageBackend(base_dir=str(tmp_path))

    @pytest.mark.asyncio
    async def test_returns_relative_path(self, backend) -> None:
        result = await backend.presign_get("schools/1/doc.pdf")
        assert result == "schools/1/doc.pdf"

    @pytest.mark.asyncio
    async def test_ignores_expires_in(self, backend) -> None:
        result = await backend.presign_get("schools/1/doc.pdf", expires_in=600)
        assert result == "schools/1/doc.pdf"

    @pytest.mark.asyncio
    async def test_ignores_response_filename(self, backend) -> None:
        result = await backend.presign_get(
            "schools/1/doc.pdf", response_filename="my_file.pdf"
        )
        assert result == "schools/1/doc.pdf"

    @pytest.mark.asyncio
    async def test_does_not_start_with_http(self, backend) -> None:
        result = await backend.presign_get("schools/1/doc.pdf")
        assert not result.startswith(("http://", "https://"))


# ---------------------------------------------------------------------------
# S3FileStorageBackend.presign_get
# ---------------------------------------------------------------------------


class TestS3FileStorageBackendPresignGet:
    """All aioboto3 calls are mocked — no real S3 connection."""

    def _make_backend(self, **overrides):
        from app.services.file_storage import S3FileStorageBackend

        with patch("app.services.file_storage.settings") as mock_settings:
            mock_settings.document_storage_bucket = "test-bucket"
            mock_settings.document_storage_endpoint = None
            mock_settings.document_storage_region = "us-east-1"
            mock_settings.document_storage_access_key = "key"
            mock_settings.document_storage_secret_key = "secret"
            mock_settings.document_storage_force_path_style = False
            mock_settings.s3_presign_get_ttl_seconds = 600
            for k, v in overrides.items():
                setattr(mock_settings, k, v)
            backend = S3FileStorageBackend.__new__(S3FileStorageBackend)
            backend._bucket = "test-bucket"
            backend._client_kwargs = {}
            return backend

    @pytest.mark.asyncio
    async def test_returns_presigned_url(self) -> None:
        backend = self._make_backend()
        expected_url = "https://minio.test/test-bucket/schools/1/doc.pdf?X-Amz-sig=abc"
        mock_s3 = AsyncMock()
        mock_s3.generate_presigned_url = AsyncMock(return_value=expected_url)
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_s3)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch.object(backend, "_client", return_value=mock_ctx):
            with patch("app.services.file_storage.settings") as ms:
                ms.s3_presign_get_ttl_seconds = 600
                result = await backend.presign_get("schools/1/doc.pdf")

        assert result == expected_url

    @pytest.mark.asyncio
    async def test_includes_content_disposition_when_filename_set(self) -> None:
        backend = self._make_backend()
        mock_s3 = AsyncMock()
        mock_s3.generate_presigned_url = AsyncMock(
            return_value="https://example.com/presigned"
        )
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_s3)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch.object(backend, "_client", return_value=mock_ctx):
            with patch("app.services.file_storage.settings") as ms:
                ms.s3_presign_get_ttl_seconds = 600
                await backend.presign_get(
                    "schools/1/doc.pdf", response_filename="my doc.pdf"
                )

        call_kwargs = mock_s3.generate_presigned_url.call_args
        params = call_kwargs[1]["Params"]
        assert "ResponseContentDisposition" in params
        assert "my%20doc.pdf" in params["ResponseContentDisposition"]

    @pytest.mark.asyncio
    async def test_uses_settings_ttl_by_default(self) -> None:
        backend = self._make_backend()
        mock_s3 = AsyncMock()
        mock_s3.generate_presigned_url = AsyncMock(return_value="https://example.com/x")
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_s3)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch.object(backend, "_client", return_value=mock_ctx):
            with patch("app.services.file_storage.settings") as ms:
                ms.s3_presign_get_ttl_seconds = 999
                await backend.presign_get("schools/1/doc.pdf")

        call_kwargs = mock_s3.generate_presigned_url.call_args
        assert call_kwargs[1]["ExpiresIn"] == 999

    @pytest.mark.asyncio
    async def test_uses_custom_expires_in(self) -> None:
        backend = self._make_backend()
        mock_s3 = AsyncMock()
        mock_s3.generate_presigned_url = AsyncMock(return_value="https://example.com/x")
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_s3)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch.object(backend, "_client", return_value=mock_ctx):
            with patch("app.services.file_storage.settings") as ms:
                ms.s3_presign_get_ttl_seconds = 600
                await backend.presign_get("schools/1/doc.pdf", expires_in=120)

        call_kwargs = mock_s3.generate_presigned_url.call_args
        assert call_kwargs[1]["ExpiresIn"] == 120


# ---------------------------------------------------------------------------
# FileStorageService.presign_get
# ---------------------------------------------------------------------------


class TestFileStorageServicePresignGet:
    @pytest.fixture()
    def service(self, tmp_path: Path):
        from app.services.file_storage import (
            FileStorageService,
            LocalFileStorageBackend,
        )

        return FileStorageService(
            backend=LocalFileStorageBackend(base_dir=str(tmp_path))
        )

    @pytest.mark.asyncio
    async def test_delegates_to_backend(self, service) -> None:
        result = await service.presign_get(
            "schools/1/doc.pdf",
            expires_in=300,
            response_filename="doc.pdf",
        )
        assert result == "schools/1/doc.pdf"

    @pytest.mark.asyncio
    async def test_passthrough_matches_backend_directly(
        self, service, tmp_path: Path
    ) -> None:
        path = "schools/1/test.pdf"
        service_result = await service.presign_get(path)
        backend_result = await service.backend.presign_get(path)
        assert service_result == backend_result


# ---------------------------------------------------------------------------
# Refactored service methods return storage_path strings (not Paths)
# ---------------------------------------------------------------------------


class TestRefactoredServiceReturnTypes:
    """Smoke-tests that the refactored service methods return
    (storage_path: str, ...) not local abs Paths."""

    @pytest.mark.asyncio
    async def test_get_submission_file_returns_str(self) -> None:
        """get_submission_file must return a 4-tuple where [0] is str."""
        from app.services.lms._helpers import LMSServiceBase

        mock_file = MagicMock()
        mock_file.file_path = "submissions/abc/upload.pdf"
        mock_file.mime_type = "application/pdf"
        mock_file.file_size = 1024

        mock_submission = MagicMock()
        mock_submission.student_id = uuid.uuid4()

        mock_assignment = MagicMock()
        mock_course = MagicMock()
        mock_course.school_id = uuid.uuid4()
        mock_course.teacher_id = uuid.uuid4()

        mock_repo = AsyncMock()
        mock_repo.get_submission_file = AsyncMock(return_value=mock_file)
        mock_repo.get_submission_with_context = AsyncMock(
            return_value=(mock_submission, mock_assignment, mock_course)
        )

        mock_auth = MagicMock()
        mock_auth.role = "ADM"
        mock_auth.school_id = mock_course.school_id
        mock_auth.user_id = uuid.uuid4()

        svc = LMSServiceBase.__new__(LMSServiceBase)
        svc.repo = mock_repo

        result = await svc.get_submission_file(
            submission_id=uuid.uuid4(),
            file_id=uuid.uuid4(),
            auth=mock_auth,
        )
        storage_path, mime_type, filename, size = result
        assert isinstance(storage_path, str), "storage_path must be str, not Path"
        assert storage_path == "submissions/abc/upload.pdf"
        assert isinstance(size, int)

    @pytest.mark.asyncio
    async def test_get_exercise_pdf_returns_str(self) -> None:
        """get_exercise_pdf must return a 4-tuple where [0] is str."""
        from app.services.lms._helpers import LMSServiceBase

        mock_assignment = MagicMock()
        mock_assignment.exercise_pdf_path = "exercises/abc/exercise.pdf"

        mock_course = MagicMock()
        mock_course.school_id = uuid.uuid4()
        mock_course.teacher_id = uuid.uuid4()
        mock_course.class_id = uuid.uuid4()

        mock_repo = AsyncMock()
        mock_repo.get_assignment_with_course = AsyncMock(
            return_value=(mock_assignment, mock_course)
        )

        mock_auth = MagicMock()
        mock_auth.role = "ADM"
        mock_auth.school_id = mock_course.school_id
        mock_auth.user_id = uuid.uuid4()

        svc = LMSServiceBase.__new__(LMSServiceBase)
        svc.repo = mock_repo

        assignment_id = uuid.uuid4()
        result = await svc.get_exercise_pdf(assignment_id=assignment_id, auth=mock_auth)
        storage_path, mime_type, filename, size = result
        assert isinstance(storage_path, str), "storage_path must be str, not Path"
        assert storage_path == "exercises/abc/exercise.pdf"
        assert mime_type == "application/pdf"
        assert filename == f"exercise_{assignment_id}.pdf"

    @pytest.mark.asyncio
    async def test_get_content_asset_returns_str(self) -> None:
        """get_content_asset must return a 4-tuple where [0] is str."""
        from app.services.lms._helpers import LMSServiceBase

        mock_asset = MagicMock()
        mock_asset.file_path = "content/abc/page1.png"
        mock_asset.mime_type = "image/png"
        mock_asset.file_size = 2048

        mock_content = MagicMock()
        mock_content.school_id = None
        mock_content.status = "published"

        mock_repo = AsyncMock()
        mock_repo.get_content_asset = AsyncMock(return_value=mock_asset)
        mock_repo.get_content_item = AsyncMock(return_value=mock_content)

        mock_auth = MagicMock()
        mock_auth.role = "ADM"
        mock_auth.school_id = uuid.uuid4()

        svc = LMSServiceBase.__new__(LMSServiceBase)
        svc.repo = mock_repo

        result = await svc.get_content_asset(
            content_item_id=uuid.uuid4(),
            asset_id=uuid.uuid4(),
            auth=mock_auth,
        )
        storage_path, mime_type, filename, size = result
        assert isinstance(storage_path, str), "storage_path must be str, not Path"
        assert storage_path == "content/abc/page1.png"
        assert filename == "page1.png"
        assert size == 2048

    @pytest.mark.asyncio
    async def test_read_document_file_returns_tuple_str(self) -> None:
        """read_document_file must return (str, str, str) not a Path."""
        from app.services.student_documents import StudentDocumentsService

        mock_document = MagicMock()
        mock_document.storage_path = "documents/ab/abc.pdf"
        mock_document.mime_type = "application/pdf"
        mock_document.original_filename = "school_report.pdf"
        mock_document.download_count = 0

        mock_repo = AsyncMock()
        mock_repo.save_document = AsyncMock(return_value=None)

        mock_db = MagicMock()
        mock_db.info = {"_uow_depth": 1}

        svc = StudentDocumentsService.__new__(StudentDocumentsService)
        svc.db = mock_db

        with patch(
            "app.services.student_documents.DocumentsRepository",
            return_value=mock_repo,
        ):
            result = await svc.read_document_file(document=mock_document)

        storage_path, mime_type, filename = result
        assert isinstance(storage_path, str), "storage_path must be str, not Path"
        assert storage_path == "documents/ab/abc.pdf"
        assert mime_type == "application/pdf"
        assert filename == "school_report.pdf"

    @pytest.mark.asyncio
    async def test_get_version_returns_storage_path_str(self) -> None:
        """get_version must return (DocumentVersion, str) not (version, Path)."""
        from app.services.student_documents import StudentDocumentsService

        mock_version = MagicMock()
        mock_version.storage_path = "documents/ab/v2.pdf"

        mock_document = MagicMock()
        mock_document.id = uuid.uuid4()

        mock_repo = AsyncMock()
        mock_repo.get_document_version = AsyncMock(return_value=mock_version)

        svc = StudentDocumentsService.__new__(StudentDocumentsService)
        svc.repo = mock_repo

        with patch.object(
            svc,
            "get_document_for_actor",
            AsyncMock(return_value=mock_document),
        ):
            version, storage_path = await svc.get_version(
                document_id=uuid.uuid4(),
                version_number=2,
                school_id=uuid.uuid4(),
                actor_id=uuid.uuid4(),
                actor_role="TCH",
            )

        assert isinstance(storage_path, str), "storage_path must be str, not Path"
        assert storage_path == "documents/ab/v2.pdf"
