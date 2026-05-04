#!/usr/bin/env python3
"""One-shot idempotent migration of local uploads/ → MinIO (S3-compatible).

Safety rules:
  - HEAD before PUT; skip when remote size == local size.
  - Never deletes local files.
  - Never mutates the database.
  - Streams files from disk; never buffers an entire file in memory.
  - Bounded concurrency via asyncio.Semaphore (default 8).
  - Re-running is safe: already-migrated objects are skipped.
  - Every error is reported; one failure never aborts the whole run.

Run order
---------
1. Always dry-run first to preview scope.
2. Run for real.
3. Re-run to confirm zero uploads remain.
4. Spot-check the app end-to-end before flipping STORAGE_BACKEND=s3.

Commands (fill in env-specific bucket / source):

  # dev — dry-run
  python scripts/migrate_local_to_minio.py \\
      --dry-run --source uploads/ --bucket ecole-dev-private

  # dev — real run with verification sample
  python scripts/migrate_local_to_minio.py \\
      --source uploads/ --bucket ecole-dev-private --verify-sample 50

  # staging — real run
  S3_ENDPOINT=https://minio.staging.example.com \\
  S3_ACCESS_KEY=... S3_SECRET_KEY=... \\
  python scripts/migrate_local_to_minio.py \\
      --source uploads/ --bucket ecole-staging-private --verify-sample 50

  # prod — real run (run during maintenance window)
  S3_ENDPOINT=https://minio.prod.example.com \\
  S3_ACCESS_KEY=... S3_SECRET_KEY=... \\
  python scripts/migrate_local_to_minio.py \\
      --source uploads/ --bucket ecole-prod-private --verify-sample 100 --concurrency 4
"""

from __future__ import annotations

import argparse
import asyncio
import datetime
import hashlib
import json
import logging
import mimetypes
import os
import random
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import NamedTuple

# ---------------------------------------------------------------------------
# Resolve repository root; bootstrap import of backend settings
# ---------------------------------------------------------------------------

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent
_BACKEND_DIR = _REPO_ROOT / "backend"

if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

try:
    from app.core.config import settings as _cfg

    _S3_ENDPOINT: str = _cfg.s3_endpoint
    _S3_REGION: str = _cfg.s3_region
    _S3_ACCESS_KEY: str = _cfg.s3_access_key
    _S3_SECRET_KEY: str = _cfg.s3_secret_key
    _DEFAULT_BUCKET: str = _cfg.s3_bucket
    _DEFAULT_SOURCE: Path = _REPO_ROOT / _cfg.upload_dir
    _SSE_ENABLED: bool = _cfg.s3_sse_enabled
    _FORCE_PATH_STYLE: bool = _cfg.s3_force_path_style
    _APP_ENV: str = _cfg.app_env
except Exception:
    _S3_ENDPOINT = os.environ.get("S3_ENDPOINT", "")
    _S3_REGION = os.environ.get("S3_REGION", "us-east-1")
    _S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY", "")
    _S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY", "")
    _DEFAULT_BUCKET = os.environ.get("S3_BUCKET", "")
    _DEFAULT_SOURCE = _REPO_ROOT / os.environ.get("UPLOAD_DIR", "uploads")
    _SSE_ENABLED = os.environ.get("S3_SSE_ENABLED", "false").lower() == "true"
    _FORCE_PATH_STYLE = os.environ.get("S3_FORCE_PATH_STYLE", "true").lower() == "true"
    _APP_ENV = os.environ.get("APP_ENV", "development")

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class MigrationStats:
    scanned: int = 0
    uploaded: int = 0
    skipped: int = 0
    failed: int = 0
    sample_passed: bool = False
    total_bytes: int = 0
    duration_seconds: float = 0.0
    errors: list[dict] = field(default_factory=list)


class _FileRecord(NamedTuple):
    local_path: Path
    key: str  # S3 object key (relative POSIX path from source dir)


# ---------------------------------------------------------------------------
# Pure helper functions (no I/O; easily unit-testable)
# ---------------------------------------------------------------------------


def guess_mime(path: Path) -> str:
    """Return MIME type for *path*; falls back to ``application/octet-stream``."""
    mime, _ = mimetypes.guess_type(str(path))
    return mime or "application/octet-stream"


def collect_files(source: Path, prefix: str | None = None) -> list[_FileRecord]:
    """Walk *source* recursively and return ``(local_path, key)`` tuples.

    Object key = POSIX relative path from *source*.  Optionally filter to
    keys that start with *prefix*.
    """
    records: list[_FileRecord] = []
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        key = path.relative_to(source).as_posix()
        if prefix and not key.startswith(prefix):
            continue
        records.append(_FileRecord(local_path=path, key=key))
    return records


def sha256_of_path(path: Path) -> str:
    """Compute SHA-256 of a local file reading in 64 KiB chunks."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Async helpers (I/O — need mocking in tests)
# ---------------------------------------------------------------------------


async def sha256_of_url(url: str) -> str:
    """Stream *url* via httpx and compute SHA-256 without buffering in memory."""
    import httpx

    h = hashlib.sha256()
    async with httpx.AsyncClient(follow_redirects=True, timeout=120) as client:
        async with client.stream("GET", url) as resp:
            resp.raise_for_status()
            async for chunk in resp.aiter_bytes(chunk_size=65536):
                h.update(chunk)
    return h.hexdigest()


async def _head_object(s3, bucket: str, key: str) -> dict | None:
    """Return HEAD metadata dict or ``None`` if the object does not exist."""
    from botocore.exceptions import ClientError

    try:
        return await s3.head_object(Bucket=bucket, Key=key)
    except ClientError as exc:
        code = exc.response["Error"]["Code"]
        if code in ("404", "NoSuchKey", "403"):
            return None
        raise


async def upload_one(
    s3,
    bucket: str,
    record: _FileRecord,
    sse_enabled: bool,
    sem: asyncio.Semaphore,
    stats: MigrationStats,
) -> bool:
    """Upload *record* to *bucket*; skip on size match.

    Streams the file from disk via ``upload_fileobj`` — never reads the
    whole file into memory.  Returns ``True`` if the object was uploaded
    (new or re-uploaded due to size mismatch), ``False`` if skipped or
    if an error was recorded.
    """
    local_path, key = record
    async with sem:
        try:
            file_size = local_path.stat().st_size
            stats.scanned += 1

            head = await _head_object(s3, bucket, key)
            if head is not None:
                remote_size = head.get("ContentLength", -1)
                if remote_size == file_size:
                    stats.skipped += 1
                    logger.debug("SKIP     %s  (size=%d matches)", key, file_size)
                    return False
                logger.info(
                    "MISMATCH  %s  (local=%d  remote=%d) — re-uploading",
                    key,
                    file_size,
                    remote_size,
                )

            mime = guess_mime(local_path)
            extra_args: dict[str, str] = {
                "ContentType": mime,
                "CacheControl": "private, max-age=300",
            }
            if sse_enabled:
                extra_args["ServerSideEncryption"] = "AES256"

            with local_path.open("rb") as fh:
                await s3.upload_fileobj(fh, bucket, key, ExtraArgs=extra_args)

            stats.uploaded += 1
            stats.total_bytes += file_size
            logger.info("UPLOAD   %s  (%d bytes, %s)", key, file_size, mime)
            return True

        except Exception as exc:
            stats.failed += 1
            stats.errors.append(
                {"key": key, "path": str(local_path), "error": str(exc)}
            )
            logger.error("FAILED   %s: %s", key, exc)
            return False


async def verify_sample(
    s3,
    bucket: str,
    candidates: list[_FileRecord],
    n: int,
    stats: MigrationStats,
) -> None:
    """Download *n* random objects via presigned URL; compare SHA-256 to local.

    Sets ``stats.sample_passed = True`` only when every sampled file matches.
    """
    if not candidates or n <= 0:
        stats.sample_passed = True
        return

    sample = random.sample(candidates, min(n, len(candidates)))
    mismatches = 0

    for record in sample:
        local_path, key = record
        try:
            url = await s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=300,
            )
            local_sha = await asyncio.to_thread(sha256_of_path, local_path)
            remote_sha = await sha256_of_url(url)
            if local_sha == remote_sha:
                logger.info("VERIFY OK  %s", key)
            else:
                mismatches += 1
                logger.error(
                    "VERIFY MISMATCH  %s  local=%s…  remote=%s…",
                    key,
                    local_sha[:12],
                    remote_sha[:12],
                )
        except Exception as exc:
            mismatches += 1
            logger.error("VERIFY ERROR  %s: %s", key, exc)

    stats.sample_passed = mismatches == 0
    if stats.sample_passed:
        logger.info("Verification: %d/%d samples OK ✓", len(sample), len(sample))
    else:
        logger.error(
            "Verification: %d/%d samples FAILED ✗", mismatches, len(sample)
        )


# ---------------------------------------------------------------------------
# Summary reporting
# ---------------------------------------------------------------------------


def write_summary(
    stats: MigrationStats,
    env: str,
    bucket: str,
    source: Path,
    dry_run: bool,
) -> Path:
    """Write a JSON summary to ``artifacts/`` and return the file path."""
    ts = datetime.datetime.now(tz=datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    artifacts_dir = _REPO_ROOT / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    outfile = artifacts_dir / f"minio_migration_{env}_{ts}.json"

    summary: dict = {
        "env": env,
        "bucket": bucket,
        "source": str(source),
        "dry_run": dry_run,
        "timestamp": ts,
        "scanned": stats.scanned,
        "uploaded": stats.uploaded,
        "skipped": stats.skipped,
        "failed": stats.failed,
        "sample_passed": stats.sample_passed,
        "total_bytes": stats.total_bytes,
        "duration_seconds": round(stats.duration_seconds, 2),
        "errors": stats.errors,
    }
    outfile.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    logger.info("Summary written to %s", outfile)
    return outfile


# ---------------------------------------------------------------------------
# Core migration runner
# ---------------------------------------------------------------------------


async def run_migration(
    source: Path,
    bucket: str,
    dry_run: bool = False,
    verify_n: int = 50,
    concurrency: int = 8,
    prefix: str | None = None,
    *,
    _session=None,
) -> MigrationStats:
    """Run the full migration and return :class:`MigrationStats`.

    This is the main programmatic entry point (also used by tests).
    Set ``dry_run=True`` to list planned operations without touching S3.
    """
    stats = MigrationStats()
    start = time.monotonic()

    source = source.resolve()
    if not source.exists():
        raise FileNotFoundError(f"Source directory not found: {source}")

    records = collect_files(source, prefix)
    scope_msg = f" (prefix={prefix!r})" if prefix else ""
    logger.info(
        "Found %d files under %s%s", len(records), source, scope_msg
    )

    # ------------------------------------------------------------------
    # Dry-run path — no S3 connection required
    # ------------------------------------------------------------------
    if dry_run:
        logger.info(
            "[DRY-RUN] Would migrate %d file(s) → s3://%s", len(records), bucket
        )
        for record in records:
            local_path, key = record
            file_size = local_path.stat().st_size
            stats.scanned += 1
            stats.total_bytes += file_size
            logger.info(
                "[DRY-RUN] WOULD UPLOAD  %-70s  %10d bytes  %s",
                key,
                file_size,
                guess_mime(local_path),
            )
        stats.duration_seconds = time.monotonic() - start
        return stats

    # ------------------------------------------------------------------
    # Real-run path
    # ------------------------------------------------------------------
    if _session is None:
        try:
            import aioboto3 as _aioboto3
        except ImportError as exc:
            raise RuntimeError(
                "aioboto3 is required: pip install aioboto3"
            ) from exc
        _session = _aioboto3.Session()

    client_kwargs: dict = {
        "endpoint_url": _S3_ENDPOINT or None,
        "region_name": _S3_REGION,
        "aws_access_key_id": _S3_ACCESS_KEY or None,
        "aws_secret_access_key": _S3_SECRET_KEY or None,
    }
    if _FORCE_PATH_STYLE:
        try:
            from aiobotocore.config import AioConfig

            client_kwargs["config"] = AioConfig(s3={"addressing_style": "path"})
        except ImportError:
            pass

    sem = asyncio.Semaphore(concurrency)
    session = _session

    async with session.client("s3", **client_kwargs) as s3:
        tasks = [
            upload_one(s3, bucket, record, _SSE_ENABLED, sem, stats)
            for record in records
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Catch any unhandled exceptions that escaped upload_one
        for record, result in zip(records, results):
            if isinstance(result, BaseException):
                stats.failed += 1
                stats.errors.append(
                    {
                        "key": record.key,
                        "path": str(record.local_path),
                        "error": f"Unhandled: {result}",
                    }
                )
                logger.error("UNHANDLED  %s: %s", record.key, result)

        # Verification sample — covers all records that didn't fail
        if verify_n > 0:
            failed_keys = {e["key"] for e in stats.errors}
            verify_candidates = [r for r in records if r.key not in failed_keys]
            if verify_candidates:
                logger.info(
                    "Running verification sample (n=%d from %d candidates)…",
                    verify_n,
                    len(verify_candidates),
                )
                await verify_sample(s3, bucket, verify_candidates, verify_n, stats)
            else:
                logger.warning("All files failed — skipping verification sample.")
                stats.sample_passed = False
        else:
            stats.sample_passed = True

    stats.duration_seconds = time.monotonic() - start
    return stats


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Idempotent migration of local uploads/ → MinIO.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=_DEFAULT_SOURCE,
        metavar="DIR",
        help=f"Local directory to migrate (default: {_DEFAULT_SOURCE})",
    )
    parser.add_argument(
        "--bucket",
        default=_DEFAULT_BUCKET,
        metavar="NAME",
        help=f"Target S3/MinIO bucket (default: {_DEFAULT_BUCKET or '<S3_BUCKET env var>'})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List planned uploads without touching S3",
    )
    parser.add_argument(
        "--verify-sample",
        type=int,
        default=50,
        metavar="N",
        help="Number of random files to verify via SHA-256 after upload (default: 50, 0 to skip)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=8,
        metavar="N",
        help="Max parallel S3 operations (default: 8)",
    )
    parser.add_argument(
        "--prefix",
        default=None,
        metavar="PREFIX",
        help="Only migrate keys starting with this prefix (optional)",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if not args.bucket:
        parser.error(
            "No bucket specified. Pass --bucket or set S3_BUCKET in the environment."
        )

    logger.info(
        "migrate_local_to_minio | env=%s | bucket=%s | source=%s | dry_run=%s | "
        "concurrency=%d | verify_sample=%d",
        _APP_ENV,
        args.bucket,
        args.source,
        args.dry_run,
        args.concurrency,
        args.verify_sample,
    )

    stats = asyncio.run(
        run_migration(
            source=args.source,
            bucket=args.bucket,
            dry_run=args.dry_run,
            verify_n=args.verify_sample,
            concurrency=args.concurrency,
            prefix=args.prefix,
        )
    )

    outfile = write_summary(
        stats=stats,
        env=_APP_ENV,
        bucket=args.bucket,
        source=args.source,
        dry_run=args.dry_run,
    )

    # Final report
    print("\n" + "=" * 60)
    print(f"  scanned  : {stats.scanned}")
    print(f"  uploaded : {stats.uploaded}")
    print(f"  skipped  : {stats.skipped}")
    print(f"  failed   : {stats.failed}")
    if not args.dry_run:
        print(f"  verified : {'PASS' if stats.sample_passed else 'FAIL'}")
    print(f"  bytes    : {stats.total_bytes:,}")
    print(f"  duration : {stats.duration_seconds:.1f}s")
    print(f"  report   : {outfile}")
    print("=" * 60)

    if stats.failed:
        logger.error("%d file(s) failed — check errors in %s", stats.failed, outfile)
        sys.exit(1)
    if not args.dry_run and not stats.sample_passed:
        logger.error("Verification sample FAILED — check %s", outfile)
        sys.exit(2)


if __name__ == "__main__":
    main()
