"""Post-upload ARQ worker — virus scan and entity creation for Phase 8 direct uploads.

task_post_upload_scan:
  1. Verify object still exists in MinIO (HEAD).
  2. Run virus_scan_hook (no-op when VIRUS_SCAN_ENABLED=false; real ClamAV scan when enabled).
  3. On CLEAN  → create target entity (SubmissionFile / ContentItemAsset / update Assignment),
               mark upload_session.upload_state = 'available'.
  4. On INFECTED → delete object from MinIO, mark state = 'quarantined'.
  5. On error   → mark state = 'failed' (ARQ retries up to WorkerSettings.max_tries).

task_cleanup_orphaned_uploads:
  Delete objects and mark sessions as 'failed' when state='uploading' for > 24 h.
  Runs daily as a cron. Complements the MinIO lifecycle rule that expires objects
  under schools/*/uploading/ after 24 h.
"""

from __future__ import annotations

import logging
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import or_, select, update

from app.core.config import settings
from app.core.database import async_session
from app.core.exceptions import NotFoundError, ValidationError
from app.core.metrics import record_virus_scan_result
from app.core.storage import S3StorageBackend, storage, virus_scan_hook
from app.models.uploads import UploadSession

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Target-entity creation helpers
# ---------------------------------------------------------------------------


async def _create_target_entity(
    db,
    session: UploadSession,
    size_bytes: int,
) -> tuple[uuid.UUID, str]:
    """Create the appropriate domain record for a successfully scanned upload.

    Returns (target_id, target_kind) to store on the UploadSession.
    """
    from app.models.lms import Assignment, ContentItemAsset, SubmissionFile

    kind = session.kind
    scope = session.scope_data

    if kind == "assignment_pdf":
        assignment_id = uuid.UUID(scope["assignment_id"])
        await db.execute(
            update(Assignment)
            .where(Assignment.id == assignment_id)
            .values(exercise_pdf_path=session.object_key)
        )
        return assignment_id, "assignment"

    if kind == "submission_file":
        submission_id = uuid.UUID(scope["submission_id"])
        file = SubmissionFile(
            submission_id=submission_id,
            file_path=session.object_key,
            mime_type=session.mime_type,
            file_size=size_bytes,
            checksum=session.sha256,
        )
        db.add(file)
        await db.flush()
        return file.id, "submission_file"

    if kind in ("content_asset", "video", "audio"):
        content_item_id = uuid.UUID(scope["content_item_id"])
        asset_type = {"video": "video", "audio": "audio", "content_asset": "document"}[
            kind
        ]
        asset = ContentItemAsset(
            content_item_id=content_item_id,
            file_path=session.object_key,
            mime_type=session.mime_type,
            file_size=size_bytes,
            checksum=session.sha256,
            asset_type=asset_type,
        )
        db.add(asset)
        await db.flush()
        return asset.id, "content_item_asset"

    raise ValueError(f"Unknown upload kind: {kind!r}")


# ---------------------------------------------------------------------------
# Thumbnail generation (images only; video thumbnails are future work)
# ---------------------------------------------------------------------------


async def _maybe_generate_thumbnail(session: UploadSession) -> None:
    """Generate and store a 200×200 JPEG thumbnail for image content assets."""
    if session.kind != "content_asset":
        return
    if not session.mime_type.startswith("image/"):
        return
    if not isinstance(storage, S3StorageBackend):
        return

    try:
        from io import BytesIO

        from PIL import Image  # type: ignore[import]

        async with storage._client() as s3:
            response = await s3.get_object(
                Bucket=storage._bucket, Key=session.object_key
            )
            body_bytes = await response["Body"].read()

        img = Image.open(BytesIO(body_bytes))
        img.thumbnail((200, 200))
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=85)
        buf.seek(0)

        thumb_key = session.object_key.rsplit(".", 1)[0] + "_thumb.jpg"
        async with storage._client() as s3:
            await s3.put_object(
                Bucket=storage._bucket,
                Key=thumb_key,
                Body=buf.read(),
                ContentType="image/jpeg",
            )
    except Exception:
        logger.warning(
            "Thumbnail generation failed for session %s — continuing without thumbnail",
            session.id,
            exc_info=True,
        )


# ---------------------------------------------------------------------------
# task_post_upload_scan
# ---------------------------------------------------------------------------


async def task_post_upload_scan(ctx: dict, upload_id: str) -> bool:
    """Post-upload virus scan and entity creation.

    State transitions:
      scanning → available   (clean scan)
      scanning → quarantined (infected)
      scanning → failed      (error / object missing)

    Idempotent: returns False immediately if session is not in 'scanning' state.
    ARQ retries on exception up to WorkerSettings.max_tries times.
    """
    now = datetime.now(timezone.utc)

    async with async_session() as db:
        result = await db.execute(
            select(UploadSession).where(UploadSession.id == uuid.UUID(upload_id))
        )
        session = result.scalar_one_or_none()

        if session is None or session.upload_state != "scanning":
            logger.warning(
                "task_post_upload_scan: session %s not in 'scanning' state (state=%s)",
                upload_id,
                getattr(session, "upload_state", "not_found"),
            )
            return False

        # ------------------------------------------------------------------
        # 1. Verify object is still present in MinIO
        # ------------------------------------------------------------------
        try:
            stat = await storage.stat(session.object_key)
        except NotFoundError:
            logger.error(
                "task_post_upload_scan: object %s not found for session %s",
                session.object_key,
                upload_id,
            )
            session.upload_state = "failed"
            session.error_message = (
                "object not found in storage after upload completion"
            )
            session.scanned_at = now
            await db.commit()
            return False

        # ------------------------------------------------------------------
        # 2. Virus scan (only when enabled and using S3 backend)
        # ------------------------------------------------------------------
        if settings.virus_scan_enabled and isinstance(storage, S3StorageBackend):
            tmp_path: Path | None = None
            try:
                async with storage._client() as s3:
                    response = await s3.get_object(
                        Bucket=storage._bucket, Key=session.object_key
                    )
                    body_bytes = await response["Body"].read()

                with tempfile.NamedTemporaryFile(delete=False, suffix=".scan") as tmp:
                    tmp.write(body_bytes)
                    tmp_path = Path(tmp.name)

                await virus_scan_hook(tmp_path)

            except ValidationError:
                logger.warning(
                    "Infected file detected: session=%s key=%s",
                    upload_id,
                    session.object_key,
                )
                record_virus_scan_result(env=settings.app_env, result="infected")
                await storage.delete(session.object_key)
                session.upload_state = "quarantined"
                session.error_message = "file failed virus scan"
                session.scanned_at = now
                await db.commit()
                return False

            except Exception:
                logger.exception(
                    "Virus scan error for session %s — will retry", upload_id
                )
                record_virus_scan_result(env=settings.app_env, result="error")
                raise  # Let ARQ retry

            else:
                record_virus_scan_result(env=settings.app_env, result="clean")

            finally:
                if tmp_path and tmp_path.exists():
                    tmp_path.unlink(missing_ok=True)

        # ------------------------------------------------------------------
        # 3. Generate thumbnail (best-effort; never blocks completion)
        # ------------------------------------------------------------------
        await _maybe_generate_thumbnail(session)

        # ------------------------------------------------------------------
        # 4. Create target entity and mark available
        # ------------------------------------------------------------------
        try:
            target_id, target_kind = await _create_target_entity(
                db, session, stat.size_bytes
            )
        except Exception:
            logger.exception("Failed to create target entity for session %s", upload_id)
            session.upload_state = "failed"
            session.error_message = "failed to create target entity after scan"
            session.scanned_at = now
            await db.commit()
            return False

        session.upload_state = "available"
        session.target_id = target_id
        session.target_kind = target_kind
        session.scanned_at = now
        await db.commit()

        logger.info(
            "Upload %s available: %s %s (key=%s)",
            upload_id,
            target_kind,
            target_id,
            session.object_key,
        )
        return True


# ---------------------------------------------------------------------------
# task_cleanup_orphaned_uploads
# ---------------------------------------------------------------------------


async def task_cleanup_orphaned_uploads(ctx: dict) -> int:
    """Mark stale upload sessions as failed and delete their objects.

    Targets:
    - state='uploading'  older than 24 h (client never called /complete)
    - state='scanning'   completed_at older than 1 h (scan worker stuck)
    """
    now = datetime.now(timezone.utc)
    upload_cutoff = now - timedelta(hours=24)
    scan_cutoff = now - timedelta(hours=1)
    count = 0

    async with async_session() as db:
        result = await db.execute(
            select(UploadSession).where(
                or_(
                    (UploadSession.upload_state == "uploading")
                    & (UploadSession.created_at < upload_cutoff),
                    (UploadSession.upload_state == "scanning")
                    & (UploadSession.completed_at < scan_cutoff),
                )
            )
        )
        orphans = result.scalars().all()

        for session in orphans:
            try:
                await storage.delete(session.object_key)
            except Exception:
                pass  # object may never have been written

            was_uploading = session.upload_state == "uploading"
            session.upload_state = "failed"
            session.error_message = (
                "upload session expired without completion"
                if was_uploading
                else "scan job timed out"
            )
            count += 1

        if count:
            await db.commit()
            logger.info("Cleaned up %d orphaned upload sessions", count)

    return count
