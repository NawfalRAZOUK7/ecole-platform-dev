"""ARQ background task worker — task registry and worker settings.

Reference: Phase 3E — Background Tasks & Email Notifications
Phase 11B: Added payment retry and overdue reminder tasks.
Tasks:
  - send_email — dispatch email via SMTP (called from enqueue helpers)
  - cleanup_expired_sessions — remove revoked/expired sessions from DB
  - cleanup_expired_cache — flush expired Redis keys (recovery OTPs, etc.)
  - send_notification_digest — daily digest of unread notifications
  - retry_failed_payments — retry failed payments with exponential backoff (Phase 11B)
  - send_overdue_reminders — send email reminders for overdue invoices (Phase 11B)

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
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

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

        cutoff = datetime.now(timezone.utc) - timedelta(
            days=settings.refresh_token_expire_days
        )

        async with async_session() as db:
            result = await db.execute(
                delete(Session).where(
                    (Session.revoked_at.isnot(None)) | (Session.created_at < cutoff)
                )
            )
            await db.commit()
            count = result.rowcount

        duration = time.perf_counter() - start
        TASK_DURATION.labels(
            env=settings.app_env, task="cleanup_expired_sessions"
        ).observe(duration)
        TASK_COMPLETED_COUNT.labels(
            env=settings.app_env, task="cleanup_expired_sessions"
        ).inc()
        logger.info("Cleaned up %d expired/revoked sessions", count)
        return count
    except Exception:
        duration = time.perf_counter() - start
        TASK_DURATION.labels(
            env=settings.app_env, task="cleanup_expired_sessions"
        ).observe(duration)
        TASK_FAILED_COUNT.labels(
            env=settings.app_env, task="cleanup_expired_sessions"
        ).inc()
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
        TASK_DURATION.labels(
            env=settings.app_env, task="cleanup_expired_cache"
        ).observe(duration)
        TASK_COMPLETED_COUNT.labels(
            env=settings.app_env, task="cleanup_expired_cache"
        ).inc()
        logger.info("Cleaned up %d expired cache keys", count)
        return count
    except Exception:
        duration = time.perf_counter() - start
        TASK_DURATION.labels(
            env=settings.app_env, task="cleanup_expired_cache"
        ).observe(duration)
        TASK_FAILED_COUNT.labels(
            env=settings.app_env, task="cleanup_expired_cache"
        ).inc()
        logger.exception("task_cleanup_expired_cache failed")
        return 0


# ---------------------------------------------------------------------------
# Task: send_notification_digest
# ---------------------------------------------------------------------------
async def task_send_notification_digest(ctx: dict) -> int:
    """Send digest emails at the configured Africa/Casablanca send hour.

    The worker runs hourly and the service decides whether daily/weekly users
    are due based on local timezone rules.
    """
    from app.core.metrics import TASK_COMPLETED_COUNT, TASK_DURATION, TASK_FAILED_COUNT

    start = time.perf_counter()
    try:
        from app.core.database import async_session
        from app.repositories.notifications import NotificationRepository
        from app.services.email_digest import EmailDigestService

        sent_count = 0
        now = datetime.now(timezone.utc)

        async with async_session() as db:
            repo = NotificationRepository(db)
            email_digest = EmailDigestService(db)

            daily_targets = await email_digest.users_due_for_digest(
                now=now,
                frequency="daily",
            )
            weekly_targets = await email_digest.users_due_for_digest(
                now=now,
                frequency="weekly",
            )

            users = await repo.list_user_contacts(
                [user_id for _, user_id in [*daily_targets, *weekly_targets]]
            )

            for frequency, targets in (
                ("daily", daily_targets),
                ("weekly", weekly_targets),
            ):
                since = now - timedelta(days=1 if frequency == "daily" else 7)
                for school_id, user_id in targets:
                    user = users.get(user_id)
                    if user is None or not user.email:
                        continue

                    notifications = await repo.list_unread_digest_notifications(
                        school_id=school_id,
                        user_id=user_id,
                        since=since,
                    )
                    if not notifications:
                        continue

                    success = await email_digest.send_digest_email(
                        user=user,
                        school_id=school_id,
                        notifications=notifications,
                        locale="fr",
                    )
                    if success:
                        sent_count += 1

            await db.commit()

        duration = time.perf_counter() - start
        TASK_DURATION.labels(
            env=settings.app_env, task="send_notification_digest"
        ).observe(duration)
        TASK_COMPLETED_COUNT.labels(
            env=settings.app_env, task="send_notification_digest"
        ).inc()
        logger.info("Sent %d notification digest emails", sent_count)
        return sent_count
    except Exception:
        duration = time.perf_counter() - start
        TASK_DURATION.labels(
            env=settings.app_env, task="send_notification_digest"
        ).observe(duration)
        TASK_FAILED_COUNT.labels(
            env=settings.app_env, task="send_notification_digest"
        ).inc()
        logger.exception("task_send_notification_digest failed")
        return 0


# ---------------------------------------------------------------------------
# Task: refresh_kpi_views (Phase 8A)
# ---------------------------------------------------------------------------
async def task_refresh_kpi_views(ctx: dict) -> bool:
    """Refresh materialized KPI views daily.

    Refreshes mv_kpi_daily materialized view for fast KPI dashboard reads.
    Falls back to computing KPIs for all schools if the view doesn't exist yet.
    """
    from app.core.metrics import TASK_COMPLETED_COUNT, TASK_DURATION, TASK_FAILED_COUNT

    start = time.perf_counter()
    try:
        from sqlalchemy import text

        from app.core.database import async_session

        async with async_session() as db:
            # Try refreshing materialized view
            try:
                await db.execute(
                    text("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_kpi_daily")
                )
                await db.commit()
                logger.info("Refreshed mv_kpi_daily materialized view")
            except Exception as mv_err:
                await db.rollback()
                # View may not exist yet — create it
                logger.warning(
                    "mv_kpi_daily refresh failed (%s), attempting to create view",
                    mv_err,
                )
                try:
                    await db.execute(
                        text("""
                        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_kpi_daily AS
                        SELECT
                            s.school_id,
                            current_date AS computed_date,
                            -- KPI-G1-001: adoption (active users / total users)
                            COUNT(DISTINCT CASE
                                WHEN sess.created_at >= current_date - interval '7 days'
                                THEN sess.user_id
                            END) AS active_users_7d,
                            COUNT(DISTINCT u.id) AS total_users,
                            -- KPI-G1-003: auth error rate
                            COUNT(CASE
                                WHEN a.action_type IN ('AUTH_LOGIN_FAILED', 'AUTH_REFRESH_FAILED')
                                AND a.created_at >= current_date - interval '1 day'
                                THEN 1
                            END) AS auth_errors_24h,
                            COUNT(CASE
                                WHEN a.action_type IN ('AUTH_LOGIN', 'AUTH_REFRESH', 'AUTH_LOGOUT',
                                    'AUTH_LOGIN_FAILED', 'AUTH_REFRESH_FAILED')
                                AND a.created_at >= current_date - interval '1 day'
                                THEN 1
                            END) AS auth_total_24h,
                            -- KPI-G1-006: invitation conversion
                            COUNT(CASE
                                WHEN i.created_at >= current_date - interval '7 days'
                                THEN 1
                            END) AS invites_created_7d,
                            COUNT(CASE
                                WHEN i.created_at >= current_date - interval '7 days'
                                AND i.consumed_at IS NOT NULL
                                THEN 1
                            END) AS invites_consumed_7d
                        FROM (SELECT DISTINCT school_id FROM users) s
                        LEFT JOIN users u ON u.school_id = s.school_id AND u.status = 'active'
                        LEFT JOIN sessions sess ON sess.school_id = s.school_id
                        LEFT JOIN audit_logs a ON a.school_id = s.school_id
                        LEFT JOIN invitation_codes i ON i.school_id = s.school_id
                        GROUP BY s.school_id
                    """)
                    )
                    await db.execute(
                        text(
                            "CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_kpi_daily_school "
                            "ON mv_kpi_daily (school_id)"
                        )
                    )
                    await db.commit()
                    logger.info("Created mv_kpi_daily materialized view")
                except Exception as create_err:
                    await db.rollback()
                    logger.error("Failed to create mv_kpi_daily: %s", create_err)
                    raise

        duration = time.perf_counter() - start
        TASK_DURATION.labels(env=settings.app_env, task="refresh_kpi_views").observe(
            duration
        )
        TASK_COMPLETED_COUNT.labels(
            env=settings.app_env, task="refresh_kpi_views"
        ).inc()
        return True
    except Exception:
        duration = time.perf_counter() - start
        TASK_DURATION.labels(env=settings.app_env, task="refresh_kpi_views").observe(
            duration
        )
        TASK_FAILED_COUNT.labels(env=settings.app_env, task="refresh_kpi_views").inc()
        logger.exception("task_refresh_kpi_views failed")
        return False


# ---------------------------------------------------------------------------
# Task: retry_failed_payments (Phase 11B)
# ---------------------------------------------------------------------------
async def task_retry_failed_payments(ctx: dict) -> int:
    """Retry failed payment attempts with exponential backoff.

    Runs hourly. Retries up to 3 times: 1h, 6h, 24h.
    On final failure: marks invoice as failed, notifies parent.
    """
    from app.core.metrics import TASK_COMPLETED_COUNT, TASK_DURATION, TASK_FAILED_COUNT

    start = time.perf_counter()
    try:
        from app.services.payment_retry import retry_failed_payments

        count = await retry_failed_payments()

        duration = time.perf_counter() - start
        TASK_DURATION.labels(
            env=settings.app_env, task="retry_failed_payments"
        ).observe(duration)
        TASK_COMPLETED_COUNT.labels(
            env=settings.app_env, task="retry_failed_payments"
        ).inc()
        logger.info("Retried %d failed payments", count)
        return count
    except Exception:
        duration = time.perf_counter() - start
        TASK_DURATION.labels(
            env=settings.app_env, task="retry_failed_payments"
        ).observe(duration)
        TASK_FAILED_COUNT.labels(
            env=settings.app_env, task="retry_failed_payments"
        ).inc()
        logger.exception("task_retry_failed_payments failed")
        return 0


# ---------------------------------------------------------------------------
# Task: send_overdue_reminders (Phase 11B)
# ---------------------------------------------------------------------------
async def task_send_overdue_reminders(ctx: dict) -> int:
    """Send email reminders for overdue invoices.

    Runs daily at 09:00 UTC (10:00 Morocco time).
    Sends to parents for invoices overdue > 7 days.
    Respects consent preferences, max 3 reminders per invoice.
    """
    from app.core.metrics import TASK_COMPLETED_COUNT, TASK_DURATION, TASK_FAILED_COUNT

    start = time.perf_counter()
    try:
        from app.services.overdue_reminders import send_overdue_reminders

        count = await send_overdue_reminders()

        duration = time.perf_counter() - start
        TASK_DURATION.labels(
            env=settings.app_env, task="send_overdue_reminders"
        ).observe(duration)
        TASK_COMPLETED_COUNT.labels(
            env=settings.app_env, task="send_overdue_reminders"
        ).inc()
        logger.info("Sent %d overdue reminders", count)
        return count
    except Exception:
        duration = time.perf_counter() - start
        TASK_DURATION.labels(
            env=settings.app_env, task="send_overdue_reminders"
        ).observe(duration)
        TASK_FAILED_COUNT.labels(
            env=settings.app_env, task="send_overdue_reminders"
        ).inc()
        logger.exception("task_send_overdue_reminders failed")
        return 0


# ---------------------------------------------------------------------------
# Task: generate_report (Phase 14)
# ---------------------------------------------------------------------------
async def task_generate_report(ctx: dict, job_id: str) -> bool:
    """Generate a queued PDF report job."""
    from app.core.metrics import (
        REPORT_GENERATION_COUNT,
        REPORT_GENERATION_DURATION,
        TASK_COMPLETED_COUNT,
        TASK_DURATION,
        TASK_FAILED_COUNT,
    )

    start = time.perf_counter()
    job_type = "unknown"
    try:
        from app.core.database import async_session
        from app.models.reporting import ReportJobStatus
        from app.services.reports import ReportsService

        async with async_session() as db:
            service = ReportsService(db)
            job = await service.generate_report_job(uuid.UUID(job_id))
            await db.commit()

        duration = time.perf_counter() - start
        TASK_DURATION.labels(env=settings.app_env, task="generate_report").observe(
            duration
        )

        if job is None:
            REPORT_GENERATION_DURATION.labels(
                env=settings.app_env,
                report_type=job_type,
            ).observe(duration)
            REPORT_GENERATION_COUNT.labels(
                env=settings.app_env,
                report_type=job_type,
                status="not_found",
            ).inc()
            TASK_FAILED_COUNT.labels(env=settings.app_env, task="generate_report").inc()
            return False

        job_type = job.type
        REPORT_GENERATION_DURATION.labels(
            env=settings.app_env,
            report_type=job_type,
        ).observe(duration)
        REPORT_GENERATION_COUNT.labels(
            env=settings.app_env,
            report_type=job_type,
            status=job.status,
        ).inc()

        if job.status == ReportJobStatus.READY.value:
            TASK_COMPLETED_COUNT.labels(
                env=settings.app_env,
                task="generate_report",
            ).inc()
            logger.info("Generated report %s (%s)", job.id, job.type)
            return True

        TASK_FAILED_COUNT.labels(env=settings.app_env, task="generate_report").inc()
        logger.warning("Report generation failed for job %s", job.id)
        return False
    except Exception:
        duration = time.perf_counter() - start
        REPORT_GENERATION_DURATION.labels(
            env=settings.app_env,
            report_type=job_type,
        ).observe(duration)
        REPORT_GENERATION_COUNT.labels(
            env=settings.app_env,
            report_type=job_type,
            status="error",
        ).inc()
        TASK_DURATION.labels(env=settings.app_env, task="generate_report").observe(
            duration
        )
        TASK_FAILED_COUNT.labels(env=settings.app_env, task="generate_report").inc()
        logger.exception("task_generate_report failed for %s", job_id)
        return False


# ---------------------------------------------------------------------------
# Task: cleanup_expired_reports (Phase 14)
# ---------------------------------------------------------------------------
async def task_cleanup_expired_reports(ctx: dict) -> int:
    """Delete expired report files and clear their file references."""
    from app.core.metrics import TASK_COMPLETED_COUNT, TASK_DURATION, TASK_FAILED_COUNT

    start = time.perf_counter()
    try:
        from app.core.database import async_session
        from app.services.reports import ReportsService

        async with async_session() as db:
            service = ReportsService(db)
            count = await service.cleanup_expired_reports()
            await db.commit()

        duration = time.perf_counter() - start
        TASK_DURATION.labels(
            env=settings.app_env,
            task="cleanup_expired_reports",
        ).observe(duration)
        TASK_COMPLETED_COUNT.labels(
            env=settings.app_env,
            task="cleanup_expired_reports",
        ).inc()
        logger.info("Cleaned up %d expired report files", count)
        return count
    except Exception:
        duration = time.perf_counter() - start
        TASK_DURATION.labels(
            env=settings.app_env,
            task="cleanup_expired_reports",
        ).observe(duration)
        TASK_FAILED_COUNT.labels(
            env=settings.app_env,
            task="cleanup_expired_reports",
        ).inc()
        logger.exception("task_cleanup_expired_reports failed")
        return 0


# ---------------------------------------------------------------------------
# Task: send_event_reminders
# ---------------------------------------------------------------------------
async def task_send_event_reminders(ctx: dict) -> int:
    """Send due calendar reminders through the notification hub."""
    from app.core.metrics import TASK_COMPLETED_COUNT, TASK_DURATION, TASK_FAILED_COUNT

    start = time.perf_counter()
    try:
        from app.core.database import async_session
        from app.services.reminders import ReminderService

        async with async_session() as db:
            service = ReminderService(db)
            sent_count = await service.send_due_reminders()
            await db.commit()

        duration = time.perf_counter() - start
        TASK_DURATION.labels(
            env=settings.app_env, task="send_event_reminders"
        ).observe(duration)
        TASK_COMPLETED_COUNT.labels(
            env=settings.app_env, task="send_event_reminders"
        ).inc()
        logger.info("Sent %d event reminders", sent_count)
        return sent_count
    except Exception:
        duration = time.perf_counter() - start
        TASK_DURATION.labels(
            env=settings.app_env, task="send_event_reminders"
        ).observe(duration)
        TASK_FAILED_COUNT.labels(
            env=settings.app_env, task="send_event_reminders"
        ).inc()
        logger.exception("task_send_event_reminders failed")
        return 0


# ---------------------------------------------------------------------------
# Task: notify_expiring_documents (Phase 16)
# ---------------------------------------------------------------------------
async def task_notify_expiring_documents(ctx: dict) -> int:
    """Send in-app/push reminders for documents expiring soon at 08:00 Casablanca."""
    from app.core.metrics import TASK_COMPLETED_COUNT, TASK_DURATION, TASK_FAILED_COUNT

    start = time.perf_counter()
    try:
        from app.core.database import async_session
        from app.services.student_documents import StudentDocumentsService

        local_now = datetime.now(ZoneInfo("Africa/Casablanca"))
        if local_now.hour != 8:
            return 0

        async with async_session() as db:
            service = StudentDocumentsService(db)
            sent_count = await service.check_expiring_documents(
                now=local_now.astimezone(timezone.utc)
            )
            await db.commit()

        duration = time.perf_counter() - start
        TASK_DURATION.labels(
            env=settings.app_env, task="notify_expiring_documents"
        ).observe(duration)
        TASK_COMPLETED_COUNT.labels(
            env=settings.app_env, task="notify_expiring_documents"
        ).inc()
        logger.info("Sent %d expiring document reminders", sent_count)
        return sent_count
    except Exception:
        duration = time.perf_counter() - start
        TASK_DURATION.labels(
            env=settings.app_env, task="notify_expiring_documents"
        ).observe(duration)
        TASK_FAILED_COUNT.labels(
            env=settings.app_env, task="notify_expiring_documents"
        ).inc()
        logger.exception("task_notify_expiring_documents failed")
        return 0


# ---------------------------------------------------------------------------
# Task: cleanup_deleted_documents (Phase 16)
# ---------------------------------------------------------------------------
async def task_cleanup_deleted_documents(ctx: dict) -> int:
    """Permanently delete soft-deleted documents after retention."""
    from app.core.metrics import TASK_COMPLETED_COUNT, TASK_DURATION, TASK_FAILED_COUNT

    start = time.perf_counter()
    try:
        from app.core.database import async_session
        from app.services.student_documents import StudentDocumentsService

        async with async_session() as db:
            service = StudentDocumentsService(db)
            deleted_count = await service.cleanup_deleted_documents()
            await db.commit()

        duration = time.perf_counter() - start
        TASK_DURATION.labels(
            env=settings.app_env, task="cleanup_deleted_documents"
        ).observe(duration)
        TASK_COMPLETED_COUNT.labels(
            env=settings.app_env, task="cleanup_deleted_documents"
        ).inc()
        logger.info("Cleaned up %d deleted documents", deleted_count)
        return deleted_count
    except Exception:
        duration = time.perf_counter() - start
        TASK_DURATION.labels(
            env=settings.app_env, task="cleanup_deleted_documents"
        ).observe(duration)
        TASK_FAILED_COUNT.labels(
            env=settings.app_env, task="cleanup_deleted_documents"
        ).inc()
        logger.exception("task_cleanup_deleted_documents failed")
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
        task_refresh_kpi_views,
        task_retry_failed_payments,
        task_send_overdue_reminders,
        task_generate_report,
        task_cleanup_expired_reports,
        task_send_event_reminders,
        task_notify_expiring_documents,
        task_cleanup_deleted_documents,
    ]

    # Cron jobs
    cron_jobs = [
        # Cleanup expired sessions daily at 03:00 UTC
        cron(task_cleanup_expired_sessions, hour=3, minute=0),
        # Cleanup expired cache keys daily at 03:15 UTC
        cron(task_cleanup_expired_cache, hour=3, minute=15),
        # Refresh KPI materialized views daily at 03:30 UTC (Phase 8A)
        cron(task_refresh_kpi_views, hour=3, minute=30),
        # Cleanup expired report files daily at 04:00 UTC (Phase 14)
        cron(task_cleanup_expired_reports, hour=4, minute=0),
        # Phase 16: Evaluate hourly and only send at 08:00 Africa/Casablanca.
        cron(task_notify_expiring_documents, minute=0),
        # Phase 16: Hard cleanup of deleted documents daily at 04:30 UTC
        cron(task_cleanup_deleted_documents, hour=4, minute=30),
        # Phase 15: Event reminder dispatch every 5 minutes
        cron(task_send_event_reminders, minute=set(range(0, 60, 5))),
    ]

    if settings.app_env in ("staging", "production"):
        cron_jobs.extend(
            [
                # Digest scheduling is evaluated hourly against Africa/Casablanca.
                cron(task_send_notification_digest, minute=0),
                # Phase 11B: Retry failed payments every hour
                cron(task_retry_failed_payments, minute=30),
                # Phase 11B: Send overdue reminders daily at 09:00 UTC (10:00 Morocco time)
                cron(task_send_overdue_reminders, hour=9, minute=0),
            ]
        )

    # Worker config
    max_jobs = 10
    job_timeout = 300  # 5 minutes max per task
    keep_result = 3600  # Keep results for 1 hour
    retry_jobs = True
    max_tries = 3
