"""Email service — SMTP dispatch with Jinja2 locale-aware templates.

Reference: Phase 3E — Background Tasks & Email Notifications
Phase 11B: Added payment_failed template subject.
Templates: welcome, otp, invoice_reminder, grade_published, payment_failed (fr/ar/en)

Usage:
    from app.services.email import email_service
    await email_service.send_otp(to="user@example.com", otp_code="123456", lang="fr")

In development (no SMTP configured): emails are logged but not sent.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Jinja2 template environment
# ---------------------------------------------------------------------------
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

_jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)

# ---------------------------------------------------------------------------
# Subject lines per template and language
# ---------------------------------------------------------------------------
SUBJECTS: dict[str, dict[str, str]] = {
    "welcome": {
        "fr": "Bienvenue sur École Platform",
        "ar": "مرحبا بك في منصة المدرسة",
        "en": "Welcome to École Platform",
    },
    "otp": {
        "fr": "Votre code de récupération",
        "ar": "رمز استرداد حسابك",
        "en": "Your recovery code",
    },
    "invoice_reminder": {
        "fr": "Rappel de facture",
        "ar": "تذكير بالفاتورة",
        "en": "Invoice reminder",
    },
    "grade_published": {
        "fr": "Nouvelle note publiée",
        "ar": "تم نشر درجة جديدة",
        "en": "New grade published",
    },
    "payment_failed": {
        "fr": "Échec de paiement — action requise",
        "ar": "فشل الدفع — إجراء مطلوب",
        "en": "Payment failed — action required",
    },
    "notification_alert": {
        "fr": "Nouvelle notification",
        "ar": "إشعار جديد",
        "en": "New notification",
    },
    "notification_digest": {
        "fr": "Résumé des notifications",
        "ar": "ملخص الإشعارات",
        "en": "Notification digest",
    },
}


def _get_subject(template_name: str, lang: str) -> str:
    """Get the email subject line for a template and language."""
    subjects = SUBJECTS.get(template_name, {})
    return subjects.get(lang, subjects.get("en", "École Platform"))


def _render_template(template_name: str, lang: str, **kwargs: Any) -> str:
    """Render a Jinja2 email template with locale context."""
    template = _jinja_env.get_template(f"email/{template_name}.html")
    now = datetime.now(timezone.utc)
    return template.render(
        lang=lang,
        year=now.year,
        header_title="École Platform" if lang != "ar" else "منصة المدرسة",
        **kwargs,
    )


# ---------------------------------------------------------------------------
# Email Service
# ---------------------------------------------------------------------------
class EmailService:
    """Sends emails via SMTP with Jinja2 templates.

    In dev mode (smtp_host=localhost, port=1025): logs email but still attempts
    delivery to Mailhog if available. Never raises on SMTP failure.
    """

    async def _send_raw(self, to: str, subject: str, html_body: str) -> bool:
        """Send an email via SMTP. Returns True on success, False on failure."""
        import aiosmtplib

        msg = MIMEMultipart("alternative")
        msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        try:
            await aiosmtplib.send(
                msg,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_user or None,
                password=settings.smtp_password or None,
                use_tls=settings.smtp_use_tls,
                timeout=settings.smtp_timeout_seconds,
            )
            logger.info("Email sent to %s: %s", to, subject)
            return True
        except Exception:
            logger.warning(
                "Failed to send email to %s: %s (SMTP may not be configured)",
                to,
                subject,
                exc_info=True,
            )
            return False

    async def send_email(
        self,
        to: str,
        template_name: str,
        lang: str = "fr",
        **kwargs: Any,
    ) -> bool:
        """Render a template and send an email.

        Args:
            to: Recipient email address.
            template_name: Template name (welcome, otp, invoice_reminder, grade_published).
            lang: Language code (fr, ar, en). Defaults to fr.
            **kwargs: Template variables.

        Returns:
            True if sent successfully, False otherwise.
        """
        lang = lang if lang in ("fr", "ar", "en") else "fr"
        subject = _get_subject(template_name, lang)
        html_body = _render_template(template_name, lang, **kwargs)

        logger.info(
            "Sending %s email to %s (lang=%s)",
            template_name,
            to,
            lang,
        )

        return await self._send_raw(to, subject, html_body)

    # -------------------------------------------------------------------
    # Convenience methods
    # -------------------------------------------------------------------
    async def send_welcome(
        self,
        to: str,
        user_name: str,
        school_name: str,
        role: str,
        lang: str = "fr",
    ) -> bool:
        """Send a welcome email after account creation."""
        return await self.send_email(
            to=to,
            template_name="welcome",
            lang=lang,
            user_name=user_name,
            school_name=school_name,
            email=to,
            role=role,
        )

    async def send_otp(
        self,
        to: str,
        otp_code: str,
        expire_minutes: int = 15,
        lang: str = "fr",
    ) -> bool:
        """Send an OTP recovery code email."""
        return await self.send_email(
            to=to,
            template_name="otp",
            lang=lang,
            otp_code=otp_code,
            expire_minutes=expire_minutes,
        )

    async def send_invoice_reminder(
        self,
        to: str,
        parent_name: str,
        invoice_id: str,
        amount: str,
        currency: str,
        due_date: str,
        lang: str = "fr",
    ) -> bool:
        """Send an invoice reminder email."""
        return await self.send_email(
            to=to,
            template_name="invoice_reminder",
            lang=lang,
            parent_name=parent_name,
            invoice_id=invoice_id,
            amount=amount,
            currency=currency,
            due_date=due_date,
        )

    async def send_grade_published(
        self,
        to: str,
        student_name: str,
        assignment_title: str,
        score: float,
        total_points: float,
        feedback: str | None = None,
        lang: str = "fr",
    ) -> bool:
        """Send a grade published notification email."""
        return await self.send_email(
            to=to,
            template_name="grade_published",
            lang=lang,
            student_name=student_name,
            assignment_title=assignment_title,
            score=score,
            total_points=total_points,
            feedback=feedback,
        )


# Module-level singleton
email_service = EmailService()
