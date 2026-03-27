"""Payment retry service — retries failed payments with exponential backoff.

Reference: Phase 11B — Billing Enhancements
- Retries failed PaymentAttempts up to 3 times: 1h, 6h, 24h backoff
- On final failure: marks invoice status as failed, notifies parent
- Runs as ARQ background task every hour

Usage:
    # Registered in core/tasks.py as a cron job
    await task_retry_failed_payments(ctx)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

logger = logging.getLogger(__name__)

# Exponential backoff intervals (in hours) for retry attempts 1, 2, 3
RETRY_BACKOFF_HOURS = [1, 6, 24]
MAX_RETRIES = 3


async def retry_failed_payments() -> int:
    """Find and retry failed payment attempts that are due for retry.

    Returns the number of payments retried.
    """
    from app.core.database import async_session
    from app.models.billing import Invoice, PaymentAttempt
    from app.services.audit import AuditService

    now = datetime.now(timezone.utc)
    retried_count = 0

    async with async_session() as db:
        # Find failed payments where:
        # - retry_count < MAX_RETRIES
        # - next_retry_at <= now (due for retry)
        result = await db.execute(
            select(PaymentAttempt).where(
                PaymentAttempt.status == "failed",
                PaymentAttempt.retry_count < MAX_RETRIES,
                PaymentAttempt.next_retry_at.isnot(None),
                PaymentAttempt.next_retry_at <= now,
            )
        )
        attempts = result.scalars().all()

        for attempt in attempts:
            audit = AuditService(db)

            try:
                # Simulate retry (in production, this would call the payment provider)
                # For now, we increment retry_count and schedule next retry
                attempt.retry_count += 1
                attempt.last_retry_error = (
                    f"Retry #{attempt.retry_count} at {now.isoformat()}"
                )

                if attempt.retry_count >= MAX_RETRIES:
                    # Final failure — mark attempt and invoice
                    attempt.status = "failed"
                    attempt.finalized_at = now
                    attempt.next_retry_at = None

                    # Mark invoice as failed
                    inv_result = await db.execute(
                        select(Invoice).where(Invoice.id == attempt.invoice_id)
                    )
                    invoice = inv_result.scalar_one_or_none()
                    if invoice and invoice.status == "pending":
                        invoice.status = "failed"

                    # Notify parent via email
                    try:
                        from app.core.tasks import enqueue_email
                        from app.models.iam import User

                        parent_result = await db.execute(
                            select(User).where(User.id == attempt.parent_id)
                        )
                        parent = parent_result.scalar_one_or_none()
                        if parent and parent.email:
                            await enqueue_email(
                                to=parent.email,
                                template_name="invoice_reminder",
                                lang="fr",
                                parent_name=parent.first_name or parent.email,
                                invoice_id=str(attempt.invoice_id),
                                amount=str(invoice.total_amount) if invoice else "N/A",
                                currency=invoice.currency if invoice else "MAD",
                                due_date=str(invoice.due_date) if invoice else "N/A",
                            )
                    except Exception:
                        logger.warning(
                            "Failed to send final failure notification for payment %s",
                            attempt.id,
                            exc_info=True,
                        )

                    await audit.log_event(
                        school_id=attempt.school_id,
                        action_type="payment.retry_final_failure",
                        target_type="payment_attempt",
                        target_id=attempt.id,
                        outcome="failed",
                        entity_after={
                            "retry_count": attempt.retry_count,
                            "invoice_id": str(attempt.invoice_id),
                        },
                    )
                else:
                    # Schedule next retry
                    backoff_hours = (
                        RETRY_BACKOFF_HOURS[attempt.retry_count - 1]
                        if attempt.retry_count - 1 < len(RETRY_BACKOFF_HOURS)
                        else RETRY_BACKOFF_HOURS[-1]
                    )
                    attempt.next_retry_at = now + timedelta(hours=backoff_hours)

                    # Reset status to pending for re-processing
                    attempt.status = "pending"
                    attempt.finalized_at = None

                    await audit.log_event(
                        school_id=attempt.school_id,
                        action_type="payment.retry_scheduled",
                        target_type="payment_attempt",
                        target_id=attempt.id,
                        outcome="success",
                        entity_after={
                            "retry_count": attempt.retry_count,
                            "next_retry_at": attempt.next_retry_at.isoformat(),
                        },
                    )

                retried_count += 1

            except Exception:
                logger.exception("Error retrying payment %s", attempt.id)

        await db.commit()

    logger.info("Retried %d failed payments", retried_count)
    return retried_count


async def schedule_retry_for_failed_payment(
    attempt_id,
    db,
) -> None:
    """Schedule the first retry for a newly failed payment.

    Called from the webhook handler when a payment fails.
    """
    from app.models.billing import PaymentAttempt

    result = await db.execute(
        select(PaymentAttempt).where(PaymentAttempt.id == attempt_id)
    )
    attempt = result.scalar_one_or_none()
    if attempt and attempt.retry_count < MAX_RETRIES:
        now = datetime.now(timezone.utc)
        attempt.next_retry_at = now + timedelta(hours=RETRY_BACKOFF_HOURS[0])
        logger.info(
            "Scheduled first retry for payment %s at %s",
            attempt.id,
            attempt.next_retry_at.isoformat(),
        )
