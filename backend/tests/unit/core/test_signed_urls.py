"""Unit tests for Phase 8 — direct-to-MinIO large file upload.

Coverage:
  - presign_put on S3StorageBackend (mocked client)
  - LocalStorageBackend.presign_put raises NotImplementedError
  - TTL calculation (_calc_ttl)
  - Object key generation (_build_object_key)
  - MIME validation constants (ALLOWED_MIMES)
  - Per-kind size limit helper (_max_size_bytes)
  - task_post_upload_scan: clean scan → available
  - task_post_upload_scan: infected → quarantined + object deleted
  - task_post_upload_scan: object missing → failed (no retry)
  - task_post_upload_scan: wrong state → early return (idempotent)
  - task_cleanup_orphaned_uploads: stale sessions marked failed
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers shared across tests
# ---------------------------------------------------------------------------

_REQUIRED_SETTINGS = dict(
    database_url="postgresql+asyncpg://u:p@localhost/db",
    redis_url="redis://localhost",
    jwt_secret_key="test",
)


def _make_s3_backend(**overrides: Any):
    from app.core.config import Settings
    from app.core.storage import S3StorageBackend

    base: dict = {
        **_REQUIRED_SETTINGS,
        "s3_bucket": "test-bucket",
        "s3_endpoint": "http://fake:9000",
        "s3_access_key": "key",
        "s3_secret_key": "secret",
        "s3_force_path_style": False,  # avoids aiobotocore import in __init__
        "s3_sse_enabled": False,
        "s3_presign_get_ttl_seconds": 300,
        "s3_presign_put_ttl_seconds": 900,
    }
    base.update(overrides)
    return S3StorageBackend(Settings(**base))


def _make_client_ctx(mock_client: MagicMock) -> MagicMock:
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=mock_client)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


def _make_upload_session(
    upload_state: str = "scanning",
    kind: str = "submission_file",
    object_key: str = "schools/s/submissions/sub/abc.pdf",
    mime_type: str = "application/pdf",
    size_bytes: int = 1024,
    sha256: str | None = None,
) -> MagicMock:
    session = MagicMock()
    session.id = uuid.uuid4()
    session.upload_state = upload_state
    session.kind = kind
    session.object_key = object_key
    session.mime_type = mime_type
    session.size_bytes = size_bytes
    session.sha256 = sha256
    session.scope_data = {
        "assignment_id": None,
        "submission_id": str(uuid.uuid4()),
        "content_item_id": None,
    }
    session.school_id = uuid.uuid4()
    session.uploader_id = uuid.uuid4()
    return session


# ---------------------------------------------------------------------------
# presign_put — S3StorageBackend
# ---------------------------------------------------------------------------


class TestS3PresignPut:
    @pytest.mark.asyncio
    async def test_returns_presigned_url(self):
        backend = _make_s3_backend()
        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url = AsyncMock(
            return_value="https://minio/signed-url"
        )

        with patch.object(backend, "_client", return_value=_make_client_ctx(mock_s3)):
            url = await backend.presign_put(
                "schools/s1/videos/ci1/abc.mp4",
                expires_in=3600,
                content_type="video/mp4",
                max_size=500 * 1024 * 1024,
            )

        assert url == "https://minio/signed-url"
        mock_s3.generate_presigned_url.assert_called_once()
        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args.args[0] == "put_object"
        params = call_args.kwargs["Params"]
        assert params["Bucket"] == "test-bucket"
        assert params["Key"] == "schools/s1/videos/ci1/abc.mp4"
        assert params["ContentType"] == "video/mp4"
        assert call_args.kwargs["ExpiresIn"] == 3600

    @pytest.mark.asyncio
    async def test_sse_included_when_enabled(self):
        backend = _make_s3_backend(s3_sse_enabled=True)
        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url = AsyncMock(return_value="https://minio/url")

        with patch.object(backend, "_client", return_value=_make_client_ctx(mock_s3)):
            await backend.presign_put(
                "schools/s/content/ci/file.pdf",
                expires_in=900,
                content_type="application/pdf",
                max_size=5 * 1024 * 1024,
            )

        params = mock_s3.generate_presigned_url.call_args.kwargs["Params"]
        assert params.get("ServerSideEncryption") == "AES256"

    @pytest.mark.asyncio
    async def test_sse_omitted_when_disabled(self):
        backend = _make_s3_backend(s3_sse_enabled=False)
        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url = AsyncMock(return_value="https://minio/url")

        with patch.object(backend, "_client", return_value=_make_client_ctx(mock_s3)):
            await backend.presign_put(
                "schools/s/content/ci/file.pdf",
                expires_in=900,
                content_type="application/pdf",
                max_size=5 * 1024 * 1024,
            )

        params = mock_s3.generate_presigned_url.call_args.kwargs["Params"]
        assert "ServerSideEncryption" not in params


# ---------------------------------------------------------------------------
# presign_put — LocalStorageBackend
# ---------------------------------------------------------------------------


class TestLocalPresignPut:
    @pytest.mark.asyncio
    async def test_raises_not_implemented(self, tmp_path: Path):
        from app.core.storage import LocalStorageBackend

        backend = LocalStorageBackend(upload_dir=str(tmp_path))
        with pytest.raises(NotImplementedError, match="STORAGE_BACKEND=s3"):
            await backend.presign_put(
                "some/key.pdf",
                expires_in=900,
                content_type="application/pdf",
                max_size=1024,
            )


# ---------------------------------------------------------------------------
# TTL calculation
# ---------------------------------------------------------------------------


class TestCalcTtl:
    def test_minimum_is_900(self):
        from app.api.v1.uploads import _calc_ttl

        assert _calc_ttl(1) == 900
        assert _calc_ttl(100 * 1024) == 900  # exactly 100 KB/s = 1 s → min 900

    def test_large_file_scales_up(self):
        from app.api.v1.uploads import _calc_ttl

        # 2 GB at 100 KB/s = 20480 s
        result = _calc_ttl(2 * 1024 * 1024 * 1024)
        assert result == min(86400, math.ceil(2 * 1024 * 1024 * 1024 / 102400))

    def test_capped_at_24h(self):
        from app.api.v1.uploads import _calc_ttl

        # Enormous file
        assert _calc_ttl(10 * 1024 * 1024 * 1024 * 1024) == 86400

    def test_50mb_gets_at_least_15_min(self):
        from app.api.v1.uploads import _calc_ttl

        result = _calc_ttl(50 * 1024 * 1024)
        assert result >= 900


# ---------------------------------------------------------------------------
# Object key generation
# ---------------------------------------------------------------------------


class TestBuildObjectKey:
    def setup_method(self):
        from app.schemas.uploads import UploadScope

        self.school_id = uuid.UUID("00000000-0000-4000-8000-000000000001")
        self.assignment_id = uuid.UUID("10000000-0000-4000-8000-000000000001")
        self.submission_id = uuid.UUID("20000000-0000-4000-8000-000000000001")
        self.content_item_id = uuid.UUID("30000000-0000-4000-8000-000000000001")
        self.scope = UploadScope(
            school_id=self.school_id,
            assignment_id=self.assignment_id,
            submission_id=self.submission_id,
            content_item_id=self.content_item_id,
        )

    def test_assignment_pdf_key(self):
        from app.api.v1.uploads import _build_object_key

        key = _build_object_key(
            "assignment_pdf", self.scope, "application/pdf", "abc123"
        )
        assert (
            key == f"schools/{self.school_id}/exercises/{self.assignment_id}/abc123.pdf"
        )

    def test_submission_file_key(self):
        from app.api.v1.uploads import _build_object_key

        key = _build_object_key("submission_file", self.scope, "image/jpeg", "def456")
        assert (
            key
            == f"schools/{self.school_id}/submissions/{self.submission_id}/def456.jpg"
        )

    def test_video_key(self):
        from app.api.v1.uploads import _build_object_key

        key = _build_object_key("video", self.scope, "video/mp4", "ghi789")
        assert (
            key == f"schools/{self.school_id}/videos/{self.content_item_id}/ghi789.mp4"
        )

    def test_audio_key_mpeg(self):
        from app.api.v1.uploads import _build_object_key

        key = _build_object_key("audio", self.scope, "audio/mpeg", "jkl012")
        assert (
            key == f"schools/{self.school_id}/audio/{self.content_item_id}/jkl012.mp3"
        )

    def test_content_asset_pdf(self):
        from app.api.v1.uploads import _build_object_key

        key = _build_object_key(
            "content_asset", self.scope, "application/pdf", "mno345"
        )
        assert (
            key == f"schools/{self.school_id}/content/{self.content_item_id}/mno345.pdf"
        )

    def test_unknown_kind_raises(self):
        from app.api.v1.uploads import _build_object_key

        with pytest.raises(ValueError, match="Unknown upload kind"):
            _build_object_key("unknown_kind", self.scope, "application/pdf", "x")


# ---------------------------------------------------------------------------
# MIME allowlists
# ---------------------------------------------------------------------------


class TestMimeAllowlists:
    def test_assignment_pdf_allows_only_pdf(self):
        from app.api.v1.uploads import ALLOWED_MIMES

        assert ALLOWED_MIMES["assignment_pdf"] == {"application/pdf"}

    def test_video_allows_only_mp4(self):
        from app.api.v1.uploads import ALLOWED_MIMES

        assert ALLOWED_MIMES["video"] == {"video/mp4"}

    def test_submission_file_excludes_video(self):
        from app.api.v1.uploads import ALLOWED_MIMES

        assert "video/mp4" not in ALLOWED_MIMES["submission_file"]

    def test_audio_includes_four_types(self):
        from app.api.v1.uploads import ALLOWED_MIMES

        assert ALLOWED_MIMES["audio"] == {
            "audio/mpeg",
            "audio/mp4",
            "audio/ogg",
            "audio/wav",
        }


# ---------------------------------------------------------------------------
# Per-kind size limits
# ---------------------------------------------------------------------------


class TestMaxSizeBytes:
    def test_video_uses_max_video_size_mb(self):
        from app.api.v1.uploads import _max_size_bytes
        from app.core.config import settings

        assert _max_size_bytes("video") == settings.max_video_size_mb * 1024 * 1024

    def test_audio_uses_max_audio_size_mb(self):
        from app.api.v1.uploads import _max_size_bytes
        from app.core.config import settings

        assert _max_size_bytes("audio") == settings.max_audio_size_mb * 1024 * 1024

    def test_submission_file_uses_max_submission_file_size_mb(self):
        from app.api.v1.uploads import _max_size_bytes
        from app.core.config import settings

        assert (
            _max_size_bytes("submission_file")
            == settings.max_submission_file_size_mb * 1024 * 1024
        )

    def test_assignment_pdf_uses_max_document_size_mb(self):
        from app.api.v1.uploads import _max_size_bytes
        from app.core.config import settings

        assert (
            _max_size_bytes("assignment_pdf")
            == settings.max_document_size_mb * 1024 * 1024
        )


# ---------------------------------------------------------------------------
# task_post_upload_scan — clean path → available
# ---------------------------------------------------------------------------


def _make_db_ctx(session_obj):
    """Return a mock async_session context manager yielding a mock DB."""
    mock_db = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.flush = AsyncMock()
    mock_db.add = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=session_obj)
    mock_result.scalars = MagicMock(
        return_value=MagicMock(all=MagicMock(return_value=[session_obj]))
    )
    mock_db.execute = AsyncMock(return_value=mock_result)

    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=mock_db)
    cm.__aexit__ = AsyncMock(return_value=False)

    def _factory():
        return cm

    return _factory, mock_db


class TestPostUploadScanClean:
    @pytest.mark.asyncio
    async def test_scan_clean_marks_available(self):
        from app.workers.post_upload import task_post_upload_scan

        session = _make_upload_session(
            upload_state="scanning",
            kind="submission_file",
        )

        mock_stat = MagicMock()
        mock_stat.size_bytes = session.size_bytes

        db_factory, mock_db = _make_db_ctx(session)

        with (
            patch("app.workers.post_upload.async_session", db_factory),
            patch("app.workers.post_upload.storage") as mock_storage,
            patch("app.workers.post_upload.settings") as mock_settings,
            patch(
                "app.workers.post_upload._create_target_entity",
                AsyncMock(return_value=(uuid.uuid4(), "submission_file")),
            ),
            patch(
                "app.workers.post_upload._maybe_generate_thumbnail",
                AsyncMock(),
            ),
        ):
            mock_storage.stat = AsyncMock(return_value=mock_stat)
            mock_settings.virus_scan_enabled = False

            result = await task_post_upload_scan({}, str(session.id))

        assert result is True
        assert session.upload_state == "available"
        assert session.target_kind == "submission_file"
        assert session.scanned_at is not None

    @pytest.mark.asyncio
    async def test_wrong_state_returns_false(self):
        """Idempotent: session not in 'scanning' state returns False immediately."""
        from app.workers.post_upload import task_post_upload_scan

        session = _make_upload_session(upload_state="available")
        db_factory, _ = _make_db_ctx(session)

        with patch("app.workers.post_upload.async_session", db_factory):
            result = await task_post_upload_scan({}, str(session.id))

        assert result is False


# ---------------------------------------------------------------------------
# task_post_upload_scan — infected → quarantined
# ---------------------------------------------------------------------------


class TestPostUploadScanInfected:
    @pytest.mark.asyncio
    async def test_infected_file_quarantined_and_object_deleted(self):
        from app.core.exceptions import ValidationError
        from app.core.storage import S3StorageBackend
        from app.workers.post_upload import task_post_upload_scan

        session = _make_upload_session(upload_state="scanning")
        db_factory, mock_db = _make_db_ctx(session)

        # Use spec=S3StorageBackend so isinstance(mock_storage, S3StorageBackend) is True
        mock_storage = MagicMock(spec=S3StorageBackend)
        mock_stat_obj = MagicMock()
        mock_stat_obj.size_bytes = session.size_bytes
        mock_storage.stat = AsyncMock(return_value=mock_stat_obj)
        mock_storage.delete = AsyncMock()
        mock_storage._bucket = "test-bucket"

        mock_s3_client = MagicMock()
        mock_s3_client.get_object = AsyncMock(
            return_value={"Body": AsyncMock(read=AsyncMock(return_value=b"EICAR-TEST"))}
        )
        mock_storage._client = MagicMock(return_value=_make_client_ctx(mock_s3_client))

        with (
            patch("app.workers.post_upload.async_session", db_factory),
            patch("app.workers.post_upload.storage", mock_storage),
            patch("app.workers.post_upload.settings") as mock_settings,
            patch(
                "app.workers.post_upload.virus_scan_hook",
                AsyncMock(side_effect=ValidationError("Virus found")),
            ),
        ):
            mock_settings.virus_scan_enabled = True

            result = await task_post_upload_scan({}, str(session.id))

        assert result is False
        assert session.upload_state == "quarantined"
        assert "virus" in (session.error_message or "").lower()
        mock_storage.delete.assert_called_once_with(session.object_key)


# ---------------------------------------------------------------------------
# task_post_upload_scan — object missing → failed
# ---------------------------------------------------------------------------


class TestPostUploadScanObjectMissing:
    @pytest.mark.asyncio
    async def test_missing_object_marks_failed(self):
        from app.core.exceptions import NotFoundError
        from app.workers.post_upload import task_post_upload_scan

        session = _make_upload_session(upload_state="scanning")
        db_factory, mock_db = _make_db_ctx(session)

        with (
            patch("app.workers.post_upload.async_session", db_factory),
            patch("app.workers.post_upload.storage") as mock_storage,
        ):
            mock_storage.stat = AsyncMock(side_effect=NotFoundError("not found"))

            result = await task_post_upload_scan({}, str(session.id))

        assert result is False
        assert session.upload_state == "failed"
        assert "not found" in (session.error_message or "").lower()


# ---------------------------------------------------------------------------
# task_cleanup_orphaned_uploads
# ---------------------------------------------------------------------------


class TestCleanupOrphanedUploads:
    @pytest.mark.asyncio
    async def test_stale_uploading_sessions_marked_failed(self):
        from app.workers.post_upload import task_cleanup_orphaned_uploads

        old_session = _make_upload_session(upload_state="uploading")
        old_session.created_at = datetime.now(timezone.utc) - timedelta(hours=30)
        old_session.completed_at = None

        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars = MagicMock(
            return_value=MagicMock(all=MagicMock(return_value=[old_session]))
        )
        mock_db.execute = AsyncMock(return_value=mock_result)

        cm = MagicMock()
        cm.__aenter__ = AsyncMock(return_value=mock_db)
        cm.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("app.workers.post_upload.async_session", return_value=cm),
            patch("app.workers.post_upload.storage") as mock_storage,
        ):
            mock_storage.delete = AsyncMock()
            count = await task_cleanup_orphaned_uploads({})

        assert count == 1
        assert old_session.upload_state == "failed"
        mock_storage.delete.assert_called_once_with(old_session.object_key)

    @pytest.mark.asyncio
    async def test_no_orphans_returns_zero(self):
        from app.workers.post_upload import task_cleanup_orphaned_uploads

        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars = MagicMock(
            return_value=MagicMock(all=MagicMock(return_value=[]))
        )
        mock_db.execute = AsyncMock(return_value=mock_result)

        cm = MagicMock()
        cm.__aenter__ = AsyncMock(return_value=mock_db)
        cm.__aexit__ = AsyncMock(return_value=False)

        with patch("app.workers.post_upload.async_session", return_value=cm):
            count = await task_cleanup_orphaned_uploads({})

        assert count == 0
