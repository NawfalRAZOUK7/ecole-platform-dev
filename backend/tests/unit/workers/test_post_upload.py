"""Unit tests for app/workers/post_upload.py.

All external I/O is mocked:
  - app.core.database.async_session  → fake async context manager
  - app.core.storage.storage          → AsyncMock
  - app.core.storage.virus_scan_hook  → AsyncMock
  - app.core.metrics.record_virus_scan_result → Mock
  - DB execute / add / flush / commit  → mocked via SimpleNamespace
"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

SCHOOL_ID = uuid.uuid4()
SESSION_ID = str(uuid.uuid4())
OBJECT_KEY = f"schools/{SCHOOL_ID}/submission_file/test.pdf"


def _make_upload_session(
    *,
    state: str = "scanning",
    kind: str = "submission_file",
    scope_data: dict | None = None,
    object_key: str = OBJECT_KEY,
    mime_type: str = "application/pdf",
    sha256: str = "abc123",
    completed_at: datetime | None = None,
    created_at: datetime | None = None,
) -> SimpleNamespace:
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=uuid.uuid4(),
        upload_state=state,
        kind=kind,
        scope_data=scope_data or {"submission_id": str(uuid.uuid4())},
        object_key=object_key,
        mime_type=mime_type,
        sha256=sha256,
        completed_at=completed_at or now,
        created_at=created_at or now,
        scanned_at=None,
        target_id=None,
        target_kind=None,
        error_message=None,
    )


def _make_db(session_obj):
    """Build a fake async DB session context manager."""
    fake_scalars = MagicMock()
    fake_scalars.return_value.all.return_value = []

    fake_result = MagicMock()
    fake_result.scalar_one_or_none.return_value = session_obj
    fake_result.scalars.return_value.all.return_value = []

    db = SimpleNamespace(
        execute=AsyncMock(return_value=fake_result),
        add=Mock(),
        flush=AsyncMock(),
        commit=AsyncMock(),
        rollback=AsyncMock(),
        delete=AsyncMock(),
    )
    return db


def _make_stat(size_bytes: int = 12345) -> SimpleNamespace:
    return SimpleNamespace(size_bytes=size_bytes)


@asynccontextmanager
async def _fake_async_session(db):
    yield db


# Autouse stubs so root conftest fixtures don't try to connect
@pytest.fixture(autouse=True)
def _stub_autouse(monkeypatch):
    monkeypatch.setattr(
        "tests.conftest.clear_analytics_cache", lambda: None, raising=False
    )


# ──────────────────────────────────────────────────────────────────────────────
# _create_target_entity
# ──────────────────────────────────────────────────────────────────────────────

class TestCreateTargetEntity:
    @pytest.mark.asyncio
    async def test_assignment_pdf_kind(self):
        from app.workers.post_upload import _create_target_entity
        assignment_id = uuid.uuid4()
        session = _make_upload_session(
            kind="assignment_pdf",
            scope_data={"assignment_id": str(assignment_id)},
        )
        db = SimpleNamespace(
            execute=AsyncMock(), add=Mock(), flush=AsyncMock()
        )
        target_id, target_kind = await _create_target_entity(db, session, 1024)
        assert target_id == assignment_id
        assert target_kind == "assignment"
        db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_submission_file_kind(self):
        from app.workers.post_upload import _create_target_entity
        submission_id = uuid.uuid4()
        session = _make_upload_session(
            kind="submission_file",
            scope_data={"submission_id": str(submission_id)},
        )
        created_file = SimpleNamespace(id=uuid.uuid4())
        db = SimpleNamespace(
            execute=AsyncMock(),
            add=Mock(),
            flush=AsyncMock(),
        )

        with patch("app.models.lms.SubmissionFile", autospec=False) as MockFile:
            MockFile.return_value = created_file
            target_id, target_kind = await _create_target_entity(db, session, 2048)

        assert target_kind == "submission_file"
        assert target_id == created_file.id
        db.add.assert_called_once_with(created_file)
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("kind,expected_asset_type", [
        ("content_asset", "document"),
        ("video", "video"),
        ("audio", "audio"),
    ])
    async def test_content_asset_kinds(self, kind, expected_asset_type):
        from app.workers.post_upload import _create_target_entity
        content_item_id = uuid.uuid4()
        session = _make_upload_session(
            kind=kind,
            scope_data={"content_item_id": str(content_item_id)},
        )
        created_asset = SimpleNamespace(id=uuid.uuid4())
        db = SimpleNamespace(execute=AsyncMock(), add=Mock(), flush=AsyncMock())

        with patch("app.models.lms.ContentItemAsset", autospec=False) as MockAsset:
            MockAsset.return_value = created_asset
            target_id, target_kind = await _create_target_entity(db, session, 500)

        assert target_kind == "content_item_asset"
        assert target_id == created_asset.id
        call_kwargs = MockAsset.call_args.kwargs
        assert call_kwargs["asset_type"] == expected_asset_type

    @pytest.mark.asyncio
    async def test_unknown_kind_raises(self):
        from app.workers.post_upload import _create_target_entity
        session = _make_upload_session(kind="unknown_kind")
        db = SimpleNamespace(execute=AsyncMock(), add=Mock(), flush=AsyncMock())
        with pytest.raises(ValueError, match="Unknown upload kind"):
            await _create_target_entity(db, session, 100)


# ──────────────────────────────────────────────────────────────────────────────
# _maybe_generate_thumbnail
# ──────────────────────────────────────────────────────────────────────────────

class TestMaybGenerateThumbnail:
    @pytest.mark.asyncio
    async def test_non_content_asset_kind_skips(self):
        from app.workers.post_upload import _maybe_generate_thumbnail
        session = _make_upload_session(kind="submission_file")
        # Should return None immediately without touching storage
        result = await _maybe_generate_thumbnail(session)
        assert result is None

    @pytest.mark.asyncio
    async def test_non_image_mime_skips(self):
        from app.workers.post_upload import _maybe_generate_thumbnail
        session = _make_upload_session(kind="content_asset", mime_type="application/pdf")
        result = await _maybe_generate_thumbnail(session)
        assert result is None

    @pytest.mark.asyncio
    async def test_non_s3_backend_skips(self):
        from app.workers.post_upload import _maybe_generate_thumbnail
        session = _make_upload_session(kind="content_asset", mime_type="image/png")
        non_s3_storage = MagicMock()
        non_s3_storage.__class__ = MagicMock  # not S3StorageBackend
        with patch("app.workers.post_upload.storage", non_s3_storage):
            result = await _maybe_generate_thumbnail(session)
        assert result is None

    @pytest.mark.asyncio
    async def test_thumbnail_exception_is_swallowed(self):
        from app.workers.post_upload import _maybe_generate_thumbnail
        from app.core.storage import S3StorageBackend
        session = _make_upload_session(
            kind="content_asset",
            mime_type="image/jpeg",
            object_key="schools/test/image.jpg",
        )
        mock_storage = MagicMock(spec=S3StorageBackend)
        mock_storage._client.side_effect = Exception("S3 error")
        with patch("app.workers.post_upload.storage", mock_storage):
            # Should not raise — exception is swallowed with a warning
            result = await _maybe_generate_thumbnail(session)
        assert result is None


# ──────────────────────────────────────────────────────────────────────────────
# task_post_upload_scan
# ──────────────────────────────────────────────────────────────────────────────

class TestTaskPostUploadScan:
    def _patch_all(self, db, stat, virus_infected=False, virus_error=False):
        """Return a list of patch context managers for the main task."""
        patches = [
            patch("app.workers.post_upload.async_session",
                  side_effect=lambda: _fake_async_session(db)),
            patch("app.workers.post_upload.storage.stat", AsyncMock(return_value=stat)),
            patch("app.workers.post_upload.storage.delete", AsyncMock()),
            patch("app.workers.post_upload.record_virus_scan_result"),
        ]
        return patches

    @pytest.mark.asyncio
    async def test_session_not_found_returns_false(self):
        from app.workers.post_upload import task_post_upload_scan
        db = _make_db(None)  # session=None
        with patch("app.workers.post_upload.async_session",
                   side_effect=lambda: _fake_async_session(db)):
            result = await task_post_upload_scan({}, str(uuid.uuid4()))
        assert result is False

    @pytest.mark.asyncio
    async def test_session_wrong_state_returns_false(self):
        from app.workers.post_upload import task_post_upload_scan
        session = _make_upload_session(state="available")
        db = _make_db(session)
        with patch("app.workers.post_upload.async_session",
                   side_effect=lambda: _fake_async_session(db)):
            result = await task_post_upload_scan({}, SESSION_ID)
        assert result is False

    @pytest.mark.asyncio
    async def test_object_not_found_marks_failed(self):
        from app.workers.post_upload import task_post_upload_scan
        from app.core.exceptions import NotFoundError
        session = _make_upload_session(state="scanning")
        db = _make_db(session)
        with (
            patch("app.workers.post_upload.async_session",
                  side_effect=lambda: _fake_async_session(db)),
            patch("app.workers.post_upload.storage.stat",
                  AsyncMock(side_effect=NotFoundError("not found"))),
        ):
            result = await task_post_upload_scan({}, SESSION_ID)
        assert result is False
        assert session.upload_state == "failed"
        assert "not found" in session.error_message
        db.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_success_no_virus_scan(self):
        """Virus scanning disabled → clean path, returns True."""
        from app.workers.post_upload import task_post_upload_scan
        submission_id = uuid.uuid4()
        session = _make_upload_session(
            state="scanning",
            kind="submission_file",
            scope_data={"submission_id": str(submission_id)},
        )
        db = _make_db(session)
        stat = _make_stat()
        created_file = SimpleNamespace(id=uuid.uuid4())

        with (
            patch("app.workers.post_upload.async_session",
                  side_effect=lambda: _fake_async_session(db)),
            patch("app.workers.post_upload.storage.stat", AsyncMock(return_value=stat)),
            patch("app.workers.post_upload.settings.virus_scan_enabled", False),
            patch("app.workers.post_upload._maybe_generate_thumbnail", AsyncMock()),
            patch("app.models.lms.SubmissionFile", return_value=created_file),
        ):
            result = await task_post_upload_scan({}, SESSION_ID)

        assert result is True
        assert session.upload_state == "available"
        assert session.target_kind == "submission_file"
        db.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_virus_infected_marks_quarantined(self):
        from app.workers.post_upload import task_post_upload_scan
        from app.core.exceptions import ValidationError
        from app.core.storage import S3StorageBackend

        session = _make_upload_session(state="scanning")
        db = _make_db(session)
        stat = _make_stat()

        mock_storage = MagicMock(spec=S3StorageBackend)
        mock_storage.stat = AsyncMock(return_value=stat)
        mock_storage.delete = AsyncMock()
        body_bytes = b"infected data"

        async def fake_get_object(**kwargs):
            return {"Body": AsyncMock(read=AsyncMock(return_value=body_bytes))}

        ctx_mock = AsyncMock()
        ctx_mock.__aenter__ = AsyncMock(
            return_value=SimpleNamespace(get_object=AsyncMock(side_effect=fake_get_object))
        )
        ctx_mock.__aexit__ = AsyncMock(return_value=None)
        mock_storage._client = MagicMock(return_value=ctx_mock)
        mock_storage._bucket = "test-bucket"

        with (
            patch("app.workers.post_upload.async_session",
                  side_effect=lambda: _fake_async_session(db)),
            patch("app.workers.post_upload.storage", mock_storage),
            patch("app.workers.post_upload.settings.virus_scan_enabled", True),
            patch("app.workers.post_upload.virus_scan_hook",
                  AsyncMock(side_effect=ValidationError("infected"))),
            patch("app.workers.post_upload.record_virus_scan_result"),
        ):
            result = await task_post_upload_scan({}, SESSION_ID)

        assert result is False
        assert session.upload_state == "quarantined"
        assert "virus scan" in session.error_message
        mock_storage.delete.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_virus_scan_error_reraises_for_arq_retry(self):
        from app.workers.post_upload import task_post_upload_scan
        from app.core.storage import S3StorageBackend

        session = _make_upload_session(state="scanning")
        db = _make_db(session)
        stat = _make_stat()

        mock_storage = MagicMock(spec=S3StorageBackend)
        mock_storage.stat = AsyncMock(return_value=stat)
        body_bytes = b"some data"

        async def fake_get_object(**kwargs):
            return {"Body": AsyncMock(read=AsyncMock(return_value=body_bytes))}

        ctx_mock = AsyncMock()
        ctx_mock.__aenter__ = AsyncMock(
            return_value=SimpleNamespace(get_object=AsyncMock(side_effect=fake_get_object))
        )
        ctx_mock.__aexit__ = AsyncMock(return_value=None)
        mock_storage._client = MagicMock(return_value=ctx_mock)
        mock_storage._bucket = "test-bucket"

        with (
            patch("app.workers.post_upload.async_session",
                  side_effect=lambda: _fake_async_session(db)),
            patch("app.workers.post_upload.storage", mock_storage),
            patch("app.workers.post_upload.settings.virus_scan_enabled", True),
            patch("app.workers.post_upload.virus_scan_hook",
                  AsyncMock(side_effect=RuntimeError("scan service down"))),
            patch("app.workers.post_upload.record_virus_scan_result"),
        ):
            with pytest.raises(RuntimeError, match="scan service down"):
                await task_post_upload_scan({}, SESSION_ID)

    @pytest.mark.asyncio
    async def test_entity_creation_failure_marks_failed(self):
        from app.workers.post_upload import task_post_upload_scan
        session = _make_upload_session(state="scanning", kind="submission_file")
        db = _make_db(session)
        stat = _make_stat()

        with (
            patch("app.workers.post_upload.async_session",
                  side_effect=lambda: _fake_async_session(db)),
            patch("app.workers.post_upload.storage.stat", AsyncMock(return_value=stat)),
            patch("app.workers.post_upload.settings.virus_scan_enabled", False),
            patch("app.workers.post_upload._maybe_generate_thumbnail", AsyncMock()),
            patch("app.workers.post_upload._create_target_entity",
                  AsyncMock(side_effect=RuntimeError("DB error"))),
        ):
            result = await task_post_upload_scan({}, SESSION_ID)

        assert result is False
        assert session.upload_state == "failed"
        assert "target entity" in session.error_message

    @pytest.mark.asyncio
    async def test_success_assignment_pdf(self):
        from app.workers.post_upload import task_post_upload_scan
        assignment_id = uuid.uuid4()
        session = _make_upload_session(
            state="scanning",
            kind="assignment_pdf",
            scope_data={"assignment_id": str(assignment_id)},
        )
        db = _make_db(session)
        stat = _make_stat()

        with (
            patch("app.workers.post_upload.async_session",
                  side_effect=lambda: _fake_async_session(db)),
            patch("app.workers.post_upload.storage.stat", AsyncMock(return_value=stat)),
            patch("app.workers.post_upload.settings.virus_scan_enabled", False),
            patch("app.workers.post_upload._maybe_generate_thumbnail", AsyncMock()),
        ):
            result = await task_post_upload_scan({}, SESSION_ID)

        assert result is True
        assert session.upload_state == "available"
        assert session.target_kind == "assignment"


# ──────────────────────────────────────────────────────────────────────────────
# task_cleanup_orphaned_uploads
# ──────────────────────────────────────────────────────────────────────────────

class TestTaskCleanupOrphanedUploads:
    @asynccontextmanager
    async def _session_with_orphans(self, orphans: list):
        fake_result = MagicMock()
        fake_result.scalars.return_value.all.return_value = orphans
        db = SimpleNamespace(
            execute=AsyncMock(return_value=fake_result),
            add=Mock(),
            flush=AsyncMock(),
            commit=AsyncMock(),
        )
        yield db

    @pytest.mark.asyncio
    async def test_no_orphans_returns_zero(self):
        from app.workers.post_upload import task_cleanup_orphaned_uploads
        with patch("app.workers.post_upload.async_session",
                   side_effect=lambda: self._session_with_orphans([])):
            result = await task_cleanup_orphaned_uploads({})
        assert result == 0

    @pytest.mark.asyncio
    async def test_orphaned_uploading_session_is_cleaned(self):
        from app.workers.post_upload import task_cleanup_orphaned_uploads
        datetime.now(timezone.utc)
        old_session = _make_upload_session(state="uploading")

        with (
            patch("app.workers.post_upload.async_session",
                  side_effect=lambda: self._session_with_orphans([old_session])),
            patch("app.workers.post_upload.storage.delete", AsyncMock()),
        ):
            result = await task_cleanup_orphaned_uploads({})

        assert result == 1
        assert old_session.upload_state == "failed"
        assert "expired" in old_session.error_message

    @pytest.mark.asyncio
    async def test_orphaned_scanning_session_is_cleaned(self):
        from app.workers.post_upload import task_cleanup_orphaned_uploads
        stuck_session = _make_upload_session(state="scanning")

        with (
            patch("app.workers.post_upload.async_session",
                  side_effect=lambda: self._session_with_orphans([stuck_session])),
            patch("app.workers.post_upload.storage.delete", AsyncMock()),
        ):
            result = await task_cleanup_orphaned_uploads({})

        assert result == 1
        assert stuck_session.upload_state == "failed"
        assert "timed out" in stuck_session.error_message

    @pytest.mark.asyncio
    async def test_storage_delete_failure_is_swallowed(self):
        from app.workers.post_upload import task_cleanup_orphaned_uploads
        session = _make_upload_session(state="uploading")

        with (
            patch("app.workers.post_upload.async_session",
                  side_effect=lambda: self._session_with_orphans([session])),
            patch("app.workers.post_upload.storage.delete",
                  AsyncMock(side_effect=Exception("MinIO down"))),
        ):
            result = await task_cleanup_orphaned_uploads({})

        assert result == 1
        assert session.upload_state == "failed"

    @pytest.mark.asyncio
    async def test_multiple_orphans_all_cleaned(self):
        from app.workers.post_upload import task_cleanup_orphaned_uploads
        sessions = [
            _make_upload_session(state="uploading"),
            _make_upload_session(state="scanning"),
            _make_upload_session(state="uploading"),
        ]
        with (
            patch("app.workers.post_upload.async_session",
                  side_effect=lambda: self._session_with_orphans(sessions)),
            patch("app.workers.post_upload.storage.delete", AsyncMock()),
        ):
            result = await task_cleanup_orphaned_uploads({})

        assert result == 3
        for s in sessions:
            assert s.upload_state == "failed"


# ──────────────────────────────────────────────────────────────────────────────
# Missing branch coverage
# ──────────────────────────────────────────────────────────────────────────────

class TestPostUploadCoverageBoost:
    """Covers lines 118-131 (thumbnail success), 236 (clean scan else), 239->245 (finally skip)."""

    @pytest.mark.asyncio
    async def test_thumbnail_generation_success_path(self):
        """Lines 118-131: S3 get_object + PIL + S3 put_object happy path."""
        from app.workers.post_upload import _maybe_generate_thumbnail
        from app.core.storage import S3StorageBackend

        session = _make_upload_session(
            kind="content_asset",
            mime_type="image/jpeg",
            object_key="schools/test/photo.jpg",
        )

        body_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 100  # minimal JPEG-ish bytes

        s3_mock = AsyncMock()
        s3_mock.get_object = AsyncMock(
            return_value={"Body": AsyncMock(read=AsyncMock(return_value=body_bytes))}
        )
        s3_mock.put_object = AsyncMock()

        @asynccontextmanager
        async def _fake_client():
            yield s3_mock

        mock_storage = MagicMock(spec=S3StorageBackend)
        mock_storage._client = _fake_client
        mock_storage._bucket = "test-bucket"

        fake_img = MagicMock()
        fake_img.save = MagicMock(side_effect=lambda buf, **kw: buf.write(b"JPEG"))
        fake_img.thumbnail = MagicMock()

        with (
            patch("app.workers.post_upload.storage", mock_storage),
            patch("PIL.Image.open", return_value=fake_img),
        ):
            await _maybe_generate_thumbnail(session)

        s3_mock.put_object.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_virus_scan_clean_else_branch(self):
        """Line 236: virus_scan_hook passes → else: record_virus_scan_result('clean')."""
        from app.workers.post_upload import task_post_upload_scan
        from app.core.storage import S3StorageBackend

        session = _make_upload_session(
            state="scanning",
            kind="submission_file",
            scope_data={"submission_id": str(uuid.uuid4())},
        )
        db = _make_db(session)
        stat = _make_stat()

        mock_storage = MagicMock(spec=S3StorageBackend)
        mock_storage.stat = AsyncMock(return_value=stat)
        mock_storage.delete = AsyncMock()
        body_bytes = b"clean file content"

        s3_mock = AsyncMock()
        s3_mock.get_object = AsyncMock(
            return_value={"Body": AsyncMock(read=AsyncMock(return_value=body_bytes))}
        )

        @asynccontextmanager
        async def _fake_client():
            yield s3_mock

        mock_storage._client = _fake_client
        mock_storage._bucket = "test-bucket"

        created_file = SimpleNamespace(id=uuid.uuid4())
        mock_record = Mock()

        with (
            patch("app.workers.post_upload.async_session",
                  side_effect=lambda: _fake_async_session(db)),
            patch("app.workers.post_upload.storage", mock_storage),
            patch("app.workers.post_upload.settings.virus_scan_enabled", True),
            patch("app.workers.post_upload.virus_scan_hook", AsyncMock()),
            patch("app.workers.post_upload.record_virus_scan_result", mock_record),
            patch("app.workers.post_upload._maybe_generate_thumbnail", AsyncMock()),
            patch("app.models.lms.SubmissionFile", return_value=created_file),
        ):
            result = await task_post_upload_scan({}, SESSION_ID)

        assert result is True
        mock_record.assert_any_call(env=mock_record.call_args_list[0][1].get("env") or
                                    mock_record.call_args_list[0].kwargs.get("env"),
                                    result="clean")

    @pytest.mark.asyncio
    async def test_virus_scan_finally_tmp_path_none(self):
        """Line 239->245: exception before tempfile creation → tmp_path is None → skip unlink."""
        from app.workers.post_upload import task_post_upload_scan
        from app.core.storage import S3StorageBackend

        session = _make_upload_session(state="scanning")
        db = _make_db(session)
        stat = _make_stat()

        mock_storage = MagicMock(spec=S3StorageBackend)
        mock_storage.stat = AsyncMock(return_value=stat)

        @asynccontextmanager
        async def _failing_client():
            raise RuntimeError("S3 connection failed")
            yield  # pragma: no cover

        mock_storage._client = _failing_client
        mock_storage._bucket = "test-bucket"

        with (
            patch("app.workers.post_upload.async_session",
                  side_effect=lambda: _fake_async_session(db)),
            patch("app.workers.post_upload.storage", mock_storage),
            patch("app.workers.post_upload.settings.virus_scan_enabled", True),
            patch("app.workers.post_upload.record_virus_scan_result"),
        ):
            with pytest.raises(RuntimeError, match="S3 connection failed"):
                await task_post_upload_scan({}, SESSION_ID)
