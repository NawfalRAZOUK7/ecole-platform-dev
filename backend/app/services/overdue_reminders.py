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

from sqlalchemy import select

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
    from app.models.billing import Invoice
    from app.models.com import ConsentPreference
    from app.models.iam import User
    from app.services.audit import AuditService

    now = datetime.now(timezone.utc)
    overdue_cutoff = (now - timedelta(days=OVERDUE_THRESHOLD_DAYS)).date()
    reminder_cooldown = now - timedelta(days=MIN_DAYS_BETWEEN_REMINDERS)
    sent_count = 0

    async with async_session() as db:
        # Find overdue pending invoices:
        # - status = 'pending'
        # - due_date < today - 7 days
        # - reminder_count < MAX_REMINDERS
        # - reminder_sent_at is NULL or > 3 days ago
        query = select(Invoice).where(
            Invoice.status == "pending",
            Invoice.due_date < overdue_cutoff,
            Invoice.reminder_count < MAX_REMINDERS,
            (Invoice.reminder_sent_at.is_(None))
            | (Invoice.reminder_sent_at < reminder_cooldown),
        )

        result = await db.execute(query)
        invoices = result.scalars().all()

        for invoice in invoices:
            audit = AuditService(db)

            try:
                # Get parent
                parent_result = await db.execute(
                    select(User).where(User.id == invoice.parent_id)
                )
                parent = parent_result.scalar_one_or_none()
                if parent is None or not parent.email:
                    continue

                # Check consent: topic="billing", channel="email"
                consent_result = await db.execute(
                    select(ConsentPreference).where(
                        ConsentPreference.user_id == invoice.parent_id,
                        ConsentPreference.topic == "billing",
                        ConsentPreference.channel == "email",
                    )
                )
                consent = consent_result.scalar_one_or_none()
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
                    parent_name=parent.first_name or parent.email,
                    invoice_id=str(invoice.id),
                    amount=f"{float(invoice.total_amount):.2f}",
                    currency=invoice.currency,
                    due_date=str(invoice.due_date),
                )

                # Update invoice reminder tracking
                invoice.reminder_count += 1
                invoice.reminder_sent_at = now

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

        await db.commit()

    logger.info("Sent %d overdue invoice reminders", sent_count)
    return sent_count
