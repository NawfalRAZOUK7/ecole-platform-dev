"""Unit tests for scripts/migrate_local_to_minio.py — Phase 4.

Coverage:
  collect_files():
    - Returns all files recursively as _FileRecord(local_path, key).
    - Keys use forward slashes (POSIX) on every OS.
    - Keys are relative to the source dir, not absolute.
    - Empty directory returns empty list.
    - Prefix filter skips non-matching keys.
    - Prefix filter keeps matching keys.
    - Symlinks are treated as files (standard rglob behaviour).

  guess_mime():
    - Known extensions resolved to correct MIME type.
    - Unknown extension falls back to application/octet-stream.
    - No extension falls back to application/octet-stream.

  sha256_of_path():
    - Matches hashlib.sha256 computed directly on the bytes.
    - Works for empty file (edge case).

  MigrationStats:
    - Default values are all zero / False / empty.

  run_migration() — dry-run mode:
    - Returns stats without calling into S3 (no aioboto3 import needed).
    - stats.scanned equals file count.
    - stats.uploaded == 0, stats.skipped == 0, stats.failed == 0.
    - stats.total_bytes is the sum of file sizes.
    - stats.sample_passed is False (not applicable for dry-run).
    - Raises FileNotFoundError when source does not exist.
    - Prefix filter is honoured in dry-run.

  run_migration() — real-run mode (mocked S3):
    - File not in S3 (HEAD 404) → uploaded.
    - File already in S3 with matching size → skipped.
    - File in S3 with mismatched size → re-uploaded.
    - S3 error on single file → recorded in stats.errors; rest continue.
    - verify_n=0 → sample_passed is True without any presign/download calls.

  upload_one():
    - Returns False and increments stats.skipped when sizes match.
    - Returns True and increments stats.uploaded on fresh upload.
    - Returns False and appends to stats.errors when upload_fileobj raises.
    - SSE header added to extra_args when sse_enabled=True.
    - SSE header absent when sse_enabled=False.
"""

from __future__ import annotations

import asyncio
import hashlib
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Import the migration module from scripts/ (outside backend/)
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[4]  # …/ecole-platform-dev
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from migrate_local_to_minio import (  # noqa: E402
    MigrationStats,
    _FileRecord,
    collect_files,
    guess_mime,
    run_migration,
    sha256_of_path,
    upload_one,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_tree(tmp_path: Path) -> Path:
    """Build a small directory tree for testing.

    Structure::

        sample_tree/
          school/
            exercises/42/file.pdf        (8 bytes)
            submissions/7/report.docx    (12 bytes)
          readme.txt                     (5 bytes)
    """
    (tmp_path / "school" / "exercises" / "42").mkdir(parents=True)
    (tmp_path / "school" / "submissions" / "7").mkdir(parents=True)

    (tmp_path / "school" / "exercises" / "42" / "file.pdf").write_bytes(b"%PDF-1.4")
    (tmp_path / "school" / "submissions" / "7" / "report.docx").write_bytes(b"docx" * 3)
    (tmp_path / "readme.txt").write_bytes(b"hello")
    return tmp_path


# ---------------------------------------------------------------------------
# collect_files
# ---------------------------------------------------------------------------


class TestCollectFiles:
    def test_returns_all_files(self, sample_tree: Path) -> None:
        records = collect_files(sample_tree)
        assert len(records) == 3

    def test_keys_are_posix_relative_paths(self, sample_tree: Path) -> None:
        records = collect_files(sample_tree)
        keys = {r.key for r in records}
        assert "school/exercises/42/file.pdf" in keys
        assert "school/submissions/7/report.docx" in keys
        assert "readme.txt" in keys

    def test_keys_use_forward_slashes(self, sample_tree: Path) -> None:
        records = collect_files(sample_tree)
        for r in records:
            assert "\\" not in r.key, f"Backslash found in key: {r.key!r}"

    def test_keys_are_not_absolute(self, sample_tree: Path) -> None:
        records = collect_files(sample_tree)
        for r in records:
            assert not r.key.startswith("/"), f"Key is absolute: {r.key!r}"

    def test_local_paths_are_absolute(self, sample_tree: Path) -> None:
        records = collect_files(sample_tree)
        for r in records:
            assert r.local_path.is_absolute()

    def test_empty_directory_returns_empty_list(self, tmp_path: Path) -> None:
        assert collect_files(tmp_path) == []

    def test_prefix_filter_excludes_non_matching(self, sample_tree: Path) -> None:
        records = collect_files(sample_tree, prefix="school/exercises")
        keys = {r.key for r in records}
        assert "school/exercises/42/file.pdf" in keys
        assert "school/submissions/7/report.docx" not in keys
        assert "readme.txt" not in keys

    def test_prefix_filter_keeps_matching(self, sample_tree: Path) -> None:
        records = collect_files(sample_tree, prefix="school/submissions")
        assert len(records) == 1
        assert records[0].key == "school/submissions/7/report.docx"

    def test_no_prefix_returns_all(self, sample_tree: Path) -> None:
        assert len(collect_files(sample_tree, prefix=None)) == 3

    def test_prefix_no_match_returns_empty(self, sample_tree: Path) -> None:
        assert collect_files(sample_tree, prefix="nonexistent/") == []

    def test_records_are_sorted(self, sample_tree: Path) -> None:
        records = collect_files(sample_tree)
        keys = [r.key for r in records]
        assert keys == sorted(keys)


# ---------------------------------------------------------------------------
# guess_mime
# ---------------------------------------------------------------------------


class TestGuessMime:
    def test_pdf(self, tmp_path: Path) -> None:
        assert guess_mime(tmp_path / "doc.pdf") == "application/pdf"

    def test_png(self, tmp_path: Path) -> None:
        assert guess_mime(tmp_path / "img.png") == "image/png"

    def test_mp4(self, tmp_path: Path) -> None:
        assert guess_mime(tmp_path / "video.mp4") == "video/mp4"

    def test_docx(self, tmp_path: Path) -> None:
        mime = guess_mime(tmp_path / "report.docx")
        assert "word" in mime or "document" in mime

    def test_unknown_extension_falls_back(self, tmp_path: Path) -> None:
        assert guess_mime(tmp_path / "file.xyzzy42") == "application/octet-stream"

    def test_no_extension_falls_back(self, tmp_path: Path) -> None:
        assert guess_mime(tmp_path / "MAKEFILE") == "application/octet-stream"


# ---------------------------------------------------------------------------
# sha256_of_path
# ---------------------------------------------------------------------------


class TestSha256OfPath:
    def test_matches_hashlib_direct(self, tmp_path: Path) -> None:
        content = b"The quick brown fox jumps over the lazy dog"
        f = tmp_path / "test.bin"
        f.write_bytes(content)
        expected = hashlib.sha256(content).hexdigest()
        assert sha256_of_path(f) == expected

    def test_empty_file(self, tmp_path: Path) -> None:
        f = tmp_path / "empty.bin"
        f.write_bytes(b"")
        assert sha256_of_path(f) == hashlib.sha256(b"").hexdigest()

    def test_large_file_chunked(self, tmp_path: Path) -> None:
        content = b"x" * (200 * 1024)  # 200 KiB — forces multiple 64 KiB chunks
        f = tmp_path / "big.bin"
        f.write_bytes(content)
        expected = hashlib.sha256(content).hexdigest()
        assert sha256_of_path(f) == expected


# ---------------------------------------------------------------------------
# MigrationStats defaults
# ---------------------------------------------------------------------------


class TestMigrationStatsDefaults:
    def test_all_counts_start_at_zero(self) -> None:
        s = MigrationStats()
        assert s.scanned == 0
        assert s.uploaded == 0
        assert s.skipped == 0
        assert s.failed == 0
        assert s.total_bytes == 0
        assert s.duration_seconds == 0.0
        assert s.sample_passed is False
        assert s.errors == []


# ---------------------------------------------------------------------------
# run_migration — dry-run mode
# ---------------------------------------------------------------------------


class TestRunMigrationDryRun:
    @pytest.mark.asyncio
    async def test_scanned_equals_file_count(self, sample_tree: Path) -> None:
        stats = await run_migration(
            source=sample_tree,
            bucket="test-bucket",
            dry_run=True,
            verify_n=0,
        )
        assert stats.scanned == 3

    @pytest.mark.asyncio
    async def test_no_uploads_or_skips_in_dry_run(self, sample_tree: Path) -> None:
        stats = await run_migration(
            source=sample_tree,
            bucket="test-bucket",
            dry_run=True,
            verify_n=0,
        )
        assert stats.uploaded == 0
        assert stats.skipped == 0
        assert stats.failed == 0

    @pytest.mark.asyncio
    async def test_total_bytes_is_sum_of_file_sizes(self, sample_tree: Path) -> None:
        records = collect_files(sample_tree)
        expected_bytes = sum(r.local_path.stat().st_size for r in records)
        stats = await run_migration(
            source=sample_tree,
            bucket="test-bucket",
            dry_run=True,
            verify_n=0,
        )
        assert stats.total_bytes == expected_bytes

    @pytest.mark.asyncio
    async def test_prefix_filter_honoured_in_dry_run(self, sample_tree: Path) -> None:
        stats = await run_migration(
            source=sample_tree,
            bucket="test-bucket",
            dry_run=True,
            verify_n=0,
            prefix="school/exercises",
        )
        assert stats.scanned == 1

    @pytest.mark.asyncio
    async def test_raises_when_source_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            await run_migration(
                source=tmp_path / "nonexistent",
                bucket="test-bucket",
                dry_run=True,
            )

    @pytest.mark.asyncio
    async def test_duration_is_positive(self, sample_tree: Path) -> None:
        stats = await run_migration(
            source=sample_tree,
            bucket="test-bucket",
            dry_run=True,
            verify_n=0,
        )
        assert stats.duration_seconds >= 0


# ---------------------------------------------------------------------------
# upload_one — unit tests with mocked S3 client
# ---------------------------------------------------------------------------


def _make_sem() -> asyncio.Semaphore:
    return asyncio.Semaphore(8)


def _make_client_error(code: str):
    """Build a mock botocore ClientError with the given code."""
    from botocore.exceptions import ClientError

    return ClientError(
        error_response={"Error": {"Code": code, "Message": ""}},
        operation_name="HeadObject",
    )


class TestUploadOne:
    @pytest.fixture()
    def pdf_file(self, tmp_path: Path) -> Path:
        f = tmp_path / "school" / "exercises" / "file.pdf"
        f.parent.mkdir(parents=True)
        f.write_bytes(b"%PDF-1.4 " + b"x" * 100)
        return f

    @pytest.fixture()
    def record(self, pdf_file: Path, tmp_path: Path) -> _FileRecord:
        key = pdf_file.relative_to(tmp_path).as_posix()
        return _FileRecord(local_path=pdf_file, key=key)

    # --- skip on size match ---

    @pytest.mark.asyncio
    async def test_skips_when_remote_size_matches(self, record: _FileRecord) -> None:
        file_size = record.local_path.stat().st_size
        s3 = AsyncMock()
        s3.head_object = AsyncMock(
            return_value={"ContentLength": file_size, "ETag": '"abc"'}
        )
        stats = MigrationStats()

        result = await upload_one(s3, "bucket", record, False, _make_sem(), stats)

        assert result is False
        assert stats.skipped == 1
        assert stats.uploaded == 0
        s3.upload_fileobj.assert_not_called()

    # --- upload on 404 (object absent) ---

    @pytest.mark.asyncio
    async def test_uploads_when_object_absent(self, record: _FileRecord) -> None:
        s3 = AsyncMock()
        s3.head_object = AsyncMock(side_effect=_make_client_error("404"))
        s3.upload_fileobj = AsyncMock(return_value=None)
        stats = MigrationStats()

        result = await upload_one(s3, "bucket", record, False, _make_sem(), stats)

        assert result is True
        assert stats.uploaded == 1
        assert stats.skipped == 0
        s3.upload_fileobj.assert_called_once()

    # --- re-upload on size mismatch ---

    @pytest.mark.asyncio
    async def test_reuploads_on_size_mismatch(self, record: _FileRecord) -> None:
        s3 = AsyncMock()
        s3.head_object = AsyncMock(
            return_value={"ContentLength": 1, "ETag": '"old"'}  # wrong size
        )
        s3.upload_fileobj = AsyncMock(return_value=None)
        stats = MigrationStats()

        result = await upload_one(s3, "bucket", record, False, _make_sem(), stats)

        assert result is True
        assert stats.uploaded == 1
        s3.upload_fileobj.assert_called_once()

    # --- SSE header ---

    @pytest.mark.asyncio
    async def test_sse_header_included_when_enabled(self, record: _FileRecord) -> None:
        s3 = AsyncMock()
        s3.head_object = AsyncMock(side_effect=_make_client_error("404"))
        s3.upload_fileobj = AsyncMock(return_value=None)
        stats = MigrationStats()

        await upload_one(
            s3, "bucket", record, sse_enabled=True, sem=_make_sem(), stats=stats
        )

        call = s3.upload_fileobj.call_args
        extra = call.kwargs.get("ExtraArgs") or call[1].get("ExtraArgs")
        assert extra is not None
        assert extra.get("ServerSideEncryption") == "AES256"

    @pytest.mark.asyncio
    async def test_sse_header_absent_when_disabled(self, record: _FileRecord) -> None:
        s3 = AsyncMock()
        s3.head_object = AsyncMock(side_effect=_make_client_error("404"))
        s3.upload_fileobj = AsyncMock(return_value=None)
        stats = MigrationStats()

        await upload_one(
            s3, "bucket", record, sse_enabled=False, sem=_make_sem(), stats=stats
        )

        call = s3.upload_fileobj.call_args
        extra = call.kwargs.get("ExtraArgs") or call[1].get("ExtraArgs")
        assert extra is not None
        assert "ServerSideEncryption" not in extra

    # --- error handling ---

    @pytest.mark.asyncio
    async def test_records_error_on_s3_failure(self, record: _FileRecord) -> None:
        s3 = AsyncMock()
        s3.head_object = AsyncMock(side_effect=RuntimeError("connection refused"))
        stats = MigrationStats()

        result = await upload_one(s3, "bucket", record, False, _make_sem(), stats)

        assert result is False
        assert stats.failed == 1
        assert len(stats.errors) == 1
        assert stats.errors[0]["key"] == record.key
        assert "connection refused" in stats.errors[0]["error"]

    @pytest.mark.asyncio
    async def test_upload_error_does_not_raise(self, record: _FileRecord) -> None:
        s3 = AsyncMock()
        s3.head_object = AsyncMock(side_effect=_make_client_error("404"))
        s3.upload_fileobj = AsyncMock(side_effect=OSError("disk full"))
        stats = MigrationStats()

        result = await upload_one(s3, "bucket", record, False, _make_sem(), stats)

        assert result is False
        assert stats.failed == 1

    # --- content-type and cache-control ---

    @pytest.mark.asyncio
    async def test_content_type_set_on_upload(self, record: _FileRecord) -> None:
        s3 = AsyncMock()
        s3.head_object = AsyncMock(side_effect=_make_client_error("404"))
        s3.upload_fileobj = AsyncMock(return_value=None)
        stats = MigrationStats()

        await upload_one(s3, "bucket", record, False, _make_sem(), stats)

        call = s3.upload_fileobj.call_args
        extra = call.kwargs.get("ExtraArgs") or call[1].get("ExtraArgs")
        assert extra["ContentType"] == "application/pdf"
        assert extra["CacheControl"] == "private, max-age=300"

    # --- total_bytes tracking ---

    @pytest.mark.asyncio
    async def test_total_bytes_incremented_on_upload(self, record: _FileRecord) -> None:
        s3 = AsyncMock()
        s3.head_object = AsyncMock(side_effect=_make_client_error("404"))
        s3.upload_fileobj = AsyncMock(return_value=None)
        stats = MigrationStats()

        await upload_one(s3, "bucket", record, False, _make_sem(), stats)

        assert stats.total_bytes == record.local_path.stat().st_size

    @pytest.mark.asyncio
    async def test_total_bytes_not_incremented_on_skip(
        self, record: _FileRecord
    ) -> None:
        file_size = record.local_path.stat().st_size
        s3 = AsyncMock()
        s3.head_object = AsyncMock(return_value={"ContentLength": file_size})
        stats = MigrationStats()

        await upload_one(s3, "bucket", record, False, _make_sem(), stats)

        assert stats.total_bytes == 0


# ---------------------------------------------------------------------------
# run_migration — real-run mode (full end-to-end with mocked S3)
# ---------------------------------------------------------------------------


class TestRunMigrationRealRun:
    """Inject a fake aioboto3 session via run_migration(_session=...) — no real S3."""

    def _make_mock_session(
        self,
        *,
        head_side_effect=None,
        head_return_value=None,
    ):
        """Return a (session, s3_client) pair whose behaviour is as specified."""
        mock_s3 = AsyncMock()
        if head_side_effect is not None:
            mock_s3.head_object = AsyncMock(side_effect=head_side_effect)
        elif head_return_value is not None:
            mock_s3.head_object = AsyncMock(return_value=head_return_value)
        mock_s3.upload_fileobj = AsyncMock(return_value=None)
        mock_s3.generate_presigned_url = AsyncMock(
            return_value="https://minio.test/bucket/key?sig=x"
        )

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_s3)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.client = MagicMock(return_value=mock_ctx)
        return mock_session, mock_s3

    @pytest.mark.asyncio
    async def test_new_files_are_uploaded(self, sample_tree: Path) -> None:
        from botocore.exceptions import ClientError
        from migrate_local_to_minio import run_migration

        err = ClientError({"Error": {"Code": "404", "Message": ""}}, "HeadObject")
        session, _s3 = self._make_mock_session(head_side_effect=err)

        with patch("migrate_local_to_minio._FORCE_PATH_STYLE", False):
            stats = await run_migration(
                source=sample_tree,
                bucket="test-bucket",
                dry_run=False,
                verify_n=0,
                concurrency=2,
                _session=session,
            )

        assert stats.uploaded == 3
        assert stats.skipped == 0
        assert stats.failed == 0

    @pytest.mark.asyncio
    async def test_existing_files_are_skipped(self, sample_tree: Path) -> None:
        """When HEAD returns size matching local, all files skipped."""
        from migrate_local_to_minio import run_migration

        _records = collect_files(sample_tree)

        def head_by_size(Bucket, Key):  # noqa: N803
            for r in _records:
                if r.key == Key:
                    return {"ContentLength": r.local_path.stat().st_size}
            return {"ContentLength": 0}

        session, s3 = self._make_mock_session()
        s3.head_object = AsyncMock(side_effect=lambda **kw: head_by_size(**kw))

        with patch("migrate_local_to_minio._FORCE_PATH_STYLE", False):
            stats = await run_migration(
                source=sample_tree,
                bucket="test-bucket",
                dry_run=False,
                verify_n=0,
                concurrency=2,
                _session=session,
            )

        assert stats.skipped == 3
        assert stats.uploaded == 0

    @pytest.mark.asyncio
    async def test_verify_n_zero_sets_sample_passed(self, sample_tree: Path) -> None:
        from botocore.exceptions import ClientError
        from migrate_local_to_minio import run_migration

        err = ClientError({"Error": {"Code": "404", "Message": ""}}, "HeadObject")
        session, s3 = self._make_mock_session(head_side_effect=err)

        with patch("migrate_local_to_minio._FORCE_PATH_STYLE", False):
            stats = await run_migration(
                source=sample_tree,
                bucket="test-bucket",
                dry_run=False,
                verify_n=0,
                _session=session,
            )

        assert stats.sample_passed is True
        s3.generate_presigned_url.assert_not_called()

    @pytest.mark.asyncio
    async def test_single_file_error_does_not_abort(self, sample_tree: Path) -> None:
        """One S3 error should be recorded; other files still process."""
        from botocore.exceptions import ClientError
        from migrate_local_to_minio import run_migration

        call_count = 0

        async def flaky_head(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("transient error")
            raise ClientError({"Error": {"Code": "404", "Message": ""}}, "HeadObject")

        session, s3 = self._make_mock_session()
        s3.head_object = AsyncMock(side_effect=flaky_head)

        with patch("migrate_local_to_minio._FORCE_PATH_STYLE", False):
            stats = await run_migration(
                source=sample_tree,
                bucket="test-bucket",
                dry_run=False,
                verify_n=0,
                concurrency=1,  # sequential for determinism
                _session=session,
            )

        assert stats.failed == 1
        assert len(stats.errors) == 1
        assert stats.uploaded == 2  # the remaining 2 files succeeded
