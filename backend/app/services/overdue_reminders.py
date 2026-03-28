"""Overdue invoice reminder service — sends email reminders to parents.

Reference: Phase 11B — Billing Enhancements
- Runs daily at 09:00 UTC (10:00 Morocco time) via ARQ cron
- Emails parents for invoices overdue > 7 days
- Respects consent preferences (topic="billing", channel="email")
- Max 3 reminders per invoice (min 3 days between reminders)

Usage:
    # Registered in core/tasks.py as a cron job
    await task_send_overdue_reminders(ctx)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

MAX_REMINDERS = 3
OVERDUE_THRESHOLD_DAYS = 7
MIN_DAYS_BETWEEN_REMINDERS = 3


async def send_overdue_reminders() -> int:
    """Find overdue invoices and send reminder emails to parents.

    Returns the number of reminders sent.
    """
    from app.core.database import async_session
    from app.core.tasks import enqueue_email
    from app.core.unit_of_work import UnitOfWork
    from app.repositories.billing import BillingRepository
    from app.services.audit import AuditService

    now = datetime.now(timezone.utc)
    overdue_cutoff = (now - timedelta(days=OVERDUE_THRESHOLD_DAYS)).date()
    reminder_cooldown = now - timedelta(days=MIN_DAYS_BETWEEN_REMINDERS)
    sent_count = 0

    async with async_session() as db:
        async with UnitOfWork(db) as uow:
            repo = BillingRepository(uow.session)
            invoices = await repo.get_overdue_invoices(
                overdue_cutoff=overdue_cutoff,
                reminder_cooldown=reminder_cooldown,
                max_reminders=MAX_REMINDERS,
                limit=500,
            )

            for invoice in invoices:
                audit = AuditService(uow.session)

                try:
                    # Get parent
                    parent = await repo.get_user_by_id(invoice.parent_id)
                    if parent is None or not parent.email:
                        continue

                    # Check consent: topic="billing", channel="email"
                    consent = await repo.get_billing_email_consent(user_id=invoice.parent_id)
                    # If consent exists and is opted_out, skip
                    if consent and consent.status == "opted_out":
                        logger.info(
                            "Skipping reminder for invoice %s — parent %s opted out of billing emails",
                            invoice.id,
                            parent.email,
                        )
                        continue

                    # Send reminder email
                    await enqueue_email(
                        to=parent.email,
                        template_name="invoice_reminder",
                        lang="fr",
                        parent_name=(
                            getattr(parent, "first_name", None)
                            or parent.full_name
                            or parent.email
                        ),
                        invoice_id=str(invoice.id),
                        amount=f"{float(invoice.total_amount):.2f}",
                        currency=invoice.currency,
                        due_date=str(invoice.due_date),
                    )

                    # Update invoice reminder tracking
                    invoice.reminder_count += 1
                    invoice.reminder_sent_at = now
                    await repo.save_invoice(invoice)

                    await audit.log_event(
                        school_id=invoice.school_id,
                        action_type="invoice.overdue_reminder_sent",
                        target_type="invoice",
                        target_id=invoice.id,
                        outcome="success",
                        entity_after={
                            "reminder_count": invoice.reminder_count,
                            "parent_email": parent.email,
                            "overdue_days": (now.date() - invoice.due_date).days,
                        },
                    )

                    sent_count += 1

                except Exception:
                    logger.exception("Error sending reminder for invoice %s", invoice.id)

            await uow.commit()

    logger.info("Sent %d overdue invoice reminders", sent_count)
    return sent_count
