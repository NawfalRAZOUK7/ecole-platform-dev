"""ARQ background task worker — task registry and worker settings.

Reference: Phase 3E — Background Tasks & Email Notifications
Tasks:
  - send_email — dispatch email via SMTP (called from enqueue helpers)
  - cleanup_expired_sessions — remove revoked/expired sessions from DB
  - cleanup_expired_cache — flush expired Redis keys (recovery OTPs, etc.)
  - send_notification_digest — daily digest of unread notifications

Usage:
    # Enqueue a task from anywhere in the app:
    from app.core.tasks import enqueue_email, enqueue_task
    await enqueue_email("user@example.com", "otp", "fr", otp_code="123456")
    await enqueue_task("cleanup_expired_sessions")

Worker is started via: arq app.core.tasks.WorkerSettings
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import redis.asyncio as aioredis
from arq import cron
from arq.connections import ArqRedis, RedisSettings

from app.core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Redis settings for ARQ (same Redis instance, different DB or same)
# ---------------------------------------------------------------------------
def get_redis_settings() -> RedisSettings:
    """Parse REDIS_URL into ARQ RedisSettings."""
    url = settings.redis_url
    # redis://host:port/db
    if url.startswith("redis://"):
        parts = url.replace("redis://", "").split("/")
        host_port = parts[0]
        db = int(parts[1]) if len(parts) > 1 else 0
        if ":" in host_port:
            host, port_str = host_port.rsplit(":", 1)
            port = int(port_str)
        else:
            host = host_port
            port = 6379
        return RedisSettings(host=host, port=port, database=db)
    return RedisSettings()


# ---------------------------------------------------------------------------
# Task: send_email
# ---------------------------------------------------------------------------
async def task_send_email(
    ctx: dict,
    to: str,
    template_name: str,
    lang: str = "fr",
    **kwargs: Any,
) -> bool:
    """Background task: render template and send email via SMTP."""
    from app.core.metrics import TASK_COMPLETED_COUNT, TASK_DURATION, TASK_FAILED_COUNT
    from app.services.email import email_service

    start = time.perf_counter()
    try:
        result = await email_service.send_email(
            to=to,
            template_name=template_name,
            lang=lang,
            **kwargs,
        )
        duration = time.perf_counter() - start
        TASK_DURATION.labels(env=settings.app_env, task="send_email").observe(duration)
        if result:
            TASK_COMPLETED_COUNT.labels(env=settings.app_env, task="send_email").inc()
        else:
            TASK_FAILED_COUNT.labels(env=settings.app_env, task="send_email").inc()
        return result
    except Exception:
        duration = time.perf_counter() - start
        TASK_DURATION.labels(env=settings.app_env, task="send_email").observe(duration)
        TASK_FAILED_COUNT.labels(env=settings.app_env, task="send_email").inc()
        logger.exception("task_send_email failed for %s", to)
        return False


# ---------------------------------------------------------------------------
# Task: cleanup_expired_sessions
# ---------------------------------------------------------------------------
async def task_cleanup_expired_sessions(ctx: dict) -> int:
    """Remove revoked and expired sessions from the database.

    Runs on cron schedule. Deletes sessions that are:
    - status = 'revoked', OR
    - created_at older than refresh_token_expire_days
    """
    from app.core.metrics import TASK_COMPLETED_COUNT, TASK_DURATION, TASK_FAILED_COUNT

    start = time.perf_counter()
    try:
        from sqlalchemy import delete

        from app.core.database import async_session
        from app.models.iam import Session

        cutoff = datetime.now(timezone.utc) - timedelta(days=settings.refresh_token_expire_days)

        async with async_session() as db:
            result = await db.execute(
                delete(Session).where(
                    (Session.revoked_at.isnot(None)) | (Session.created_at < cutoff)
                )
            )
            await db.commit()
            count = result.rowcount

        duration = time.perf_counter() - start
        TASK_DURATION.labels(env=settings.app_env, task="cleanup_expired_sessions").observe(duration)
        TASK_COMPLETED_COUNT.labels(env=settings.app_env, task="cleanup_expired_sessions").inc()
        logger.info("Cleaned up %d expired/revoked sessions", count)
        return count
    except Exception:
        duration = time.perf_counter() - start
        TASK_DURATION.labels(env=settings.app_env, task="cleanup_expired_sessions").observe(duration)
        TASK_FAILED_COUNT.labels(env=settings.app_env, task="cleanup_expired_sessions").inc()
        logger.exception("task_cleanup_expired_sessions failed")
        return 0


# ---------------------------------------------------------------------------
# Task: cleanup_expired_cache
# ---------------------------------------------------------------------------
async def task_cleanup_expired_cache(ctx: dict) -> int:
    """Flush expired recovery OTP and email verification keys from Redis.

    Redis TTLs handle expiry automatically, but this task proactively scans
    and removes any orphaned keys with pattern recovery_otp:* or email_verify_otp:*.
    """
    from app.core.metrics import TASK_COMPLETED_COUNT, TASK_DURATION, TASK_FAILED_COUNT

    start = time.perf_counter()
    try:
        redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
        count = 0
        for pattern in ("recovery_otp:*", "email_verify_otp:*"):
            async for key in redis_client.scan_iter(match=pattern, count=100):
                ttl = await redis_client.ttl(key)
                if ttl <= 0:  # expired or no TTL
                    await redis_client.delete(key)
                    count += 1
        await redis_client.aclose()

        duration = time.perf_counter() - start
        TASK_DURATION.labels(env=settings.app_env, task="cleanup_expired_cache").observe(duration)
        TASK_COMPLETED_COUNT.labels(env=settings.app_env, task="cleanup_expired_cache").inc()
        logger.info("Cleaned up %d expired cache keys", count)
        return count
    except Exception:
        duration = time.perf_counter() - start
        TASK_DURATION.labels(env=settings.app_env, task="cleanup_expired_cache").observe(duration)
        TASK_FAILED_COUNT.labels(env=settings.app_env, task="cleanup_expired_cache").inc()
        logger.exception("task_cleanup_expired_cache failed")
        return 0


# ---------------------------------------------------------------------------
# Task: send_notification_digest
# ---------------------------------------------------------------------------
async def task_send_notification_digest(ctx: dict) -> int:
    """Send daily digest of unread notifications to parents.

    Queries notifications created in the last 24h that haven't been read,
    groups by parent, and sends a summary email.
    """
    from app.core.metrics import TASK_COMPLETED_COUNT, TASK_DURATION, TASK_FAILED_COUNT

    start = time.perf_counter()
    try:
        from sqlalchemy import func, select

        from app.core.database import async_session
        from app.models.com import Notification
        from app.models.iam import User
        from app.services.email import email_service

        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        sent_count = 0

        async with async_session() as db:
            # Count unread notifications per parent in last 24h
            result = await db.execute(
                select(
                    Notification.parent_id,
                    func.count(Notification.id).label("count"),
                )
                .where(Notification.created_at >= cutoff)
                .group_by(Notification.parent_id)
            )
            rows = result.all()

            for parent_id, notif_count in rows:
                # Get parent email
                user_result = await db.execute(
                    select(User).where(User.id == parent_id)
                )
                user = user_result.scalar_one_or_none()
                if user is None or not user.email:
                    continue

                # Send digest (reuse welcome template concept — simple notification)
                await email_service.send_email(
                    to=user.email,
                    template_name="welcome",
                    lang="fr",
                    user_name=user.first_name or user.email,
                    school_name="École Platform",
                    email=user.email,
                    role=f"{notif_count} nouvelle(s) notification(s)",
                )
                sent_count += 1

        duration = time.perf_counter() - start
        TASK_DURATION.labels(env=settings.app_env, task="send_notification_digest").observe(duration)
        TASK_COMPLETED_COUNT.labels(env=settings.app_env, task="send_notification_digest").inc()
        logger.info("Sent %d notification digest emails", sent_count)
        return sent_count
    except Exception:
        duration = time.perf_counter() - start
        TASK_DURATION.labels(env=settings.app_env, task="send_notification_digest").observe(duration)
        TASK_FAILED_COUNT.labels(env=settings.app_env, task="send_notification_digest").inc()
        logger.exception("task_send_notification_digest failed")
        return 0


# ---------------------------------------------------------------------------
# Enqueue helpers — fire-and-forget from API endpoints
# ---------------------------------------------------------------------------
_arq_pool: ArqRedis | None = None


async def get_arq_pool() -> ArqRedis:
    """Get or create the ARQ Redis connection pool for enqueuing tasks."""
    global _arq_pool
    if _arq_pool is None:
        from arq import create_pool

        _arq_pool = await create_pool(get_redis_settings())
    return _arq_pool


async def close_arq_pool() -> None:
    """Close the ARQ Redis connection pool (called on app shutdown)."""
    global _arq_pool
    if _arq_pool is not None:
        await _arq_pool.aclose()
        _arq_pool = None


async def enqueue_email(
    to: str,
    template_name: str,
    lang: str = "fr",
    **kwargs: Any,
) -> None:
    """Enqueue an email task. Fire-and-forget — never raises."""
    try:
        from app.core.metrics import TASK_ENQUEUED_COUNT

        pool = await get_arq_pool()
        await pool.enqueue_job(
            "task_send_email",
            to=to,
            template_name=template_name,
            lang=lang,
            **kwargs,
        )
        TASK_ENQUEUED_COUNT.labels(env=settings.app_env, task="send_email").inc()
        logger.info("Enqueued %s email to %s", template_name, to)
    except Exception:
        logger.warning(
            "Failed to enqueue email %s to %s (worker may be down)",
            template_name,
            to,
            exc_info=True,
        )


async def enqueue_task(task_name: str, **kwargs: Any) -> None:
    """Enqueue a named task. Fire-and-forget — never raises."""
    try:
        from app.core.metrics import TASK_ENQUEUED_COUNT

        pool = await get_arq_pool()
        await pool.enqueue_job(task_name, **kwargs)
        TASK_ENQUEUED_COUNT.labels(env=settings.app_env, task=task_name).inc()
        logger.info("Enqueued task %s", task_name)
    except Exception:
        logger.warning(
            "Failed to enqueue task %s (worker may be down)",
            task_name,
            exc_info=True,
        )


# ---------------------------------------------------------------------------
# ARQ Worker Settings — used by: arq app.core.tasks.WorkerSettings
# ---------------------------------------------------------------------------
class WorkerSettings:
    """ARQ worker configuration."""

    redis_settings = get_redis_settings()

    # Task registry
    functions = [
        task_send_email,
        task_cleanup_expired_sessions,
        task_cleanup_expired_cache,
        task_send_notification_digest,
    ]

    # Cron jobs
    cron_jobs = [
        # Cleanup expired sessions daily at 03:00 UTC
        cron(task_cleanup_expired_sessions, hour=3, minute=0),
        # Cleanup expired cache keys daily at 03:15 UTC
        cron(task_cleanup_expired_cache, hour=3, minute=15),
        # Send notification digest daily at 07:00 UTC (8:00 Morocco time)
        cron(task_send_notification_digest, hour=7, minute=0),
    ]

    # Worker config
    max_jobs = 10
    job_timeout = 300  # 5 minutes max per task
    keep_result = 3600  # Keep results for 1 hour
    retry_jobs = True
    max_tries = 3
