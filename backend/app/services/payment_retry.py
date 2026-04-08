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

logger = logging.getLogger(__name__)

# Exponential backoff intervals (in hours) for retry attempts 1, 2, 3
RETRY_BACKOFF_HOURS = [1, 6, 24]
MAX_RETRIES = 3


async def retry_failed_payments() -> int:
    """Find and retry failed payment attempts that are due for retry.

    Returns the number of payments retried.
    """
    from app.core.database import async_session
    from app.core.unit_of_work import UnitOfWork
    from app.repositories.billing import BillingRepository
    from app.services.audit import AuditService

    now = datetime.now(timezone.utc)
    retried_count = 0

    async with async_session() as db:
        async with UnitOfWork(db) as uow:
            repo = BillingRepository(uow.session)
            attempts = await repo.get_failed_attempts(
                now=now,
                max_retries=MAX_RETRIES,
                limit=500,
            )

            for attempt in attempts:
                audit = AuditService(uow.session)

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
                        invoice = await repo.get_invoice_by_id(attempt.invoice_id)
                        if invoice and invoice.status == "pending":
                            invoice.status = "failed"
                            await repo.save_invoice(invoice)

                        # Notify parent via email
                        try:
                            from app.core.tasks import enqueue_email

                            parent = await repo.get_user_by_id(attempt.parent_id)
                            if parent and parent.email:
                                await enqueue_email(
                                    to=parent.email,
                                    template_name="invoice_reminder",
                                    lang="fr",
                                    parent_name=(
                                        getattr(parent, "first_name", None)
                                        or parent.full_name
                                        or parent.email
                                    ),
                                    invoice_id=str(attempt.invoice_id),
                                    amount=str(invoice.total_amount)
                                    if invoice
                                    else "N/A",
                                    currency=invoice.currency if invoice else "MAD",
                                    due_date=str(invoice.due_date)
                                    if invoice
                                    else "N/A",
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

                    await repo.save_payment(attempt)
                    retried_count += 1

                except Exception:
                    logger.exception("Error retrying payment %s", attempt.id)

            await uow.commit()

    logger.info("Retried %d failed payments", retried_count)
    return retried_count


async def schedule_retry_for_failed_payment(
    attempt_id,
    db,
) -> None:
    """Schedule the first retry for a newly failed payment.

    Called from the webhook handler when a payment fails.
    """
    from app.repositories.billing import BillingRepository

    from app.core.unit_of_work import UnitOfWork

    if db.info.get("_uow_depth"):
        repo = BillingRepository(db)
        attempt = await repo.get_payment_by_id(attempt_id)
        if attempt and attempt.retry_count < MAX_RETRIES:
            now = datetime.now(timezone.utc)
            attempt.next_retry_at = now + timedelta(hours=RETRY_BACKOFF_HOURS[0])
            await repo.save_payment(attempt)
            logger.info(
                "Scheduled first retry for payment %s at %s",
                attempt.id,
                attempt.next_retry_at.isoformat(),
            )
        return

    async with UnitOfWork(db) as uow:
        repo = BillingRepository(uow.session)
        attempt = await repo.get_payment_by_id(attempt_id)
        if attempt and attempt.retry_count < MAX_RETRIES:
            now = datetime.now(timezone.utc)
            attempt.next_retry_at = now + timedelta(hours=RETRY_BACKOFF_HOURS[0])
            await repo.save_payment(attempt)
            logger.info(
                "Scheduled first retry for payment %s at %s",
                attempt.id,
                attempt.next_retry_at.isoformat(),
            )
            await uow.commit()
