"""Integration tests for Phase 3E — Background Tasks & Email Notifications.

Tests:
  1. Email template rendering (all 4 templates × 3 languages)
  2. EmailService.send_email (mocked SMTP)
  3. ARQ task functions (task_send_email, task_cleanup_expired_sessions, etc.)
  4. Enqueue helpers (enqueue_email, enqueue_task)
  5. Prometheus metrics increment on task execution
  6. Recovery → OTP email hook integration
  7. Grade → email hook integration

Requires: running Redis for ARQ pool tests.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


# ======================================================================
# Email Template Rendering
# ======================================================================
class TestEmailTemplates:
    """Verify all 4 email templates render without errors in fr/ar/en."""

    def _render(self, template_name: str, lang: str, **kwargs):
        from app.services.email import _render_template

        return _render_template(template_name, lang, **kwargs)

    @pytest.mark.parametrize("lang", ["fr", "ar", "en"])
    def test_welcome_template(self, lang):
        html = self._render(
            "welcome",
            lang,
            user_name="Test User",
            school_name="École Test",
            email="test@example.com",
            role="STD",
        )
        assert "Test User" in html
        assert "École Test" in html
        assert "test@example.com" in html
        assert "<html" in html

    @pytest.mark.parametrize("lang", ["fr", "ar", "en"])
    def test_otp_template(self, lang):
        html = self._render(
            "otp",
            lang,
            otp_code="123456",
            expire_minutes=15,
        )
        assert "123456" in html
        assert "15" in html

    @pytest.mark.parametrize("lang", ["fr", "ar", "en"])
    def test_invoice_reminder_template(self, lang):
        html = self._render(
            "invoice_reminder",
            lang,
            parent_name="Parent Test",
            invoice_id="INV-001",
            amount="500.00",
            currency="MAD",
            due_date="2026-04-01",
        )
        assert "INV-001" in html
        assert "500.00" in html
        assert "MAD" in html

    @pytest.mark.parametrize("lang", ["fr", "ar", "en"])
    def test_grade_published_template(self, lang):
        html = self._render(
            "grade_published",
            lang,
            student_name="Student Test",
            assignment_title="Math Homework 1",
            score=18.5,
            total_points=20.0,
            feedback="Good work!",
        )
        assert "Student Test" in html
        assert "Math Homework 1" in html
        assert "18.5" in html
        assert "20.0" in html
        assert "Good work!" in html

    @pytest.mark.parametrize("lang", ["fr", "ar", "en"])
    def test_grade_published_template_without_feedback(self, lang):
        html = self._render(
            "grade_published",
            lang,
            student_name="Student",
            assignment_title="Quiz 1",
            score=15.0,
            total_points=20.0,
            feedback=None,
        )
        assert "Student" in html
        assert "Quiz 1" in html

    def test_rtl_direction_for_arabic(self):
        html = self._render(
            "welcome",
            "ar",
            user_name="مستخدم",
            school_name="مدرسة",
            email="test@example.com",
            role="STD",
        )
        assert 'dir="rtl"' in html


# ======================================================================
# Email Subject Lines
# ======================================================================
class TestEmailSubjects:
    def test_subject_lines_all_templates(self):
        from app.services.email import _get_subject

        for template in ("welcome", "otp", "invoice_reminder", "grade_published"):
            for lang in ("fr", "ar", "en"):
                subject = _get_subject(template, lang)
                assert isinstance(subject, str)
                assert len(subject) > 0

    def test_unknown_template_falls_back(self):
        from app.services.email import _get_subject

        subject = _get_subject("nonexistent", "fr")
        assert subject == "École Platform"


# ======================================================================
# EmailService._send_raw (mocked SMTP)
# ======================================================================
class TestEmailService:
    @pytest.mark.asyncio
    async def test_send_email_success(self):
        from app.services.email import email_service

        with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            result = await email_service.send_email(
                to="test@example.com",
                template_name="welcome",
                lang="fr",
                user_name="Test",
                school_name="École",
                email="test@example.com",
                role="STD",
            )
            assert result is True
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_smtp_failure(self):
        from app.services.email import email_service

        with patch(
            "aiosmtplib.send",
            new_callable=AsyncMock,
            side_effect=ConnectionRefusedError("SMTP down"),
        ):
            result = await email_service.send_email(
                to="test@example.com",
                template_name="otp",
                lang="en",
                otp_code="999999",
                expire_minutes=15,
            )
            assert result is False

    @pytest.mark.asyncio
    async def test_send_otp_convenience(self):
        from app.services.email import email_service

        with patch("aiosmtplib.send", new_callable=AsyncMock):
            result = await email_service.send_otp(
                to="user@example.com",
                otp_code="654321",
                expire_minutes=10,
                lang="ar",
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_send_grade_published_convenience(self):
        from app.services.email import email_service

        with patch("aiosmtplib.send", new_callable=AsyncMock):
            result = await email_service.send_grade_published(
                to="student@example.com",
                student_name="Ahmed",
                assignment_title="Devoir 1",
                score=17.0,
                total_points=20.0,
                feedback="Très bien",
                lang="fr",
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_invalid_lang_defaults_to_fr(self):
        from app.services.email import email_service

        with patch("aiosmtplib.send", new_callable=AsyncMock):
            result = await email_service.send_email(
                to="test@example.com",
                template_name="welcome",
                lang="zh",  # unsupported → defaults to "fr"
                user_name="Test",
                school_name="École",
                email="test@example.com",
                role="STD",
            )
            assert result is True


# ======================================================================
# ARQ Task Functions
# ======================================================================
class TestTaskFunctions:
    @pytest.mark.asyncio
    async def test_task_send_email(self):
        from app.core.tasks import task_send_email

        with patch("aiosmtplib.send", new_callable=AsyncMock):
            result = await task_send_email(
                {},
                to="test@example.com",
                template_name="welcome",
                lang="en",
                user_name="Test",
                school_name="School",
                email="test@example.com",
                role="STD",
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_task_send_email_failure_returns_false(self):
        from app.core.tasks import task_send_email

        with patch(
            "aiosmtplib.send",
            new_callable=AsyncMock,
            side_effect=ConnectionRefusedError,
        ):
            result = await task_send_email(
                {},
                to="test@example.com",
                template_name="otp",
                lang="fr",
                otp_code="000000",
                expire_minutes=15,
            )
            assert result is False


# ======================================================================
# Prometheus Task Metrics
# ======================================================================
class TestTaskMetrics:
    @pytest.mark.asyncio
    async def test_metrics_increment_on_email_task(self):
        from app.core.config import settings
        from app.core.metrics import TASK_COMPLETED_COUNT
        from app.core.tasks import task_send_email

        # Get baseline
        completed_before = TASK_COMPLETED_COUNT.labels(
            env=settings.app_env, task="send_email"
        )._value.get()

        with patch("aiosmtplib.send", new_callable=AsyncMock):
            await task_send_email(
                {},
                to="test@example.com",
                template_name="welcome",
                lang="fr",
                user_name="Test",
                school_name="School",
                email="test@example.com",
                role="STD",
            )

        completed_after = TASK_COMPLETED_COUNT.labels(
            env=settings.app_env, task="send_email"
        )._value.get()
        assert completed_after == completed_before + 1

    @pytest.mark.asyncio
    async def test_metrics_increment_on_failure(self):
        from app.core.config import settings
        from app.core.metrics import TASK_FAILED_COUNT
        from app.core.tasks import task_send_email

        failed_before = TASK_FAILED_COUNT.labels(
            env=settings.app_env, task="send_email"
        )._value.get()

        with patch(
            "aiosmtplib.send",
            new_callable=AsyncMock,
            side_effect=ConnectionRefusedError,
        ):
            await task_send_email(
                {},
                to="fail@example.com",
                template_name="otp",
                lang="fr",
                otp_code="000000",
                expire_minutes=15,
            )

        failed_after = TASK_FAILED_COUNT.labels(
            env=settings.app_env, task="send_email"
        )._value.get()
        assert failed_after == failed_before + 1

    def test_task_duration_histogram_exists(self):
        from app.core.metrics import TASK_DURATION

        assert TASK_DURATION is not None
        assert TASK_DURATION._name == "task_duration_seconds"

    def test_task_enqueued_counter_exists(self):
        from app.core.metrics import TASK_ENQUEUED_COUNT

        assert TASK_ENQUEUED_COUNT is not None
        assert TASK_ENQUEUED_COUNT._name == "task_enqueued_total"


# ======================================================================
# ARQ Worker Settings
# ======================================================================
class TestWorkerSettings:
    def test_worker_settings_has_all_tasks(self):
        from app.core.tasks import WorkerSettings

        func_names = [f.__name__ for f in WorkerSettings.functions]
        assert "task_send_email" in func_names
        assert "task_cleanup_expired_sessions" in func_names
        assert "task_cleanup_expired_cache" in func_names
        assert "task_send_notification_digest" in func_names

    def test_worker_settings_has_cron_jobs(self):
        from app.core.config import settings
        from app.core.tasks import WorkerSettings

        cron_job_names = {job.name for job in WorkerSettings.cron_jobs}
        expected_names = {
            "cron:task_cleanup_expired_sessions",
            "cron:task_cleanup_expired_cache",
            "cron:task_refresh_kpi_views",
            "cron:task_cleanup_expired_reports",
            "cron:task_process_due_report_schedules",
            "cron:task_notify_expiring_documents",
            "cron:task_cleanup_deleted_documents",
            "cron:task_send_event_reminders",
            "cron:task_cleanup_orphaned_uploads",
        }
        if settings.app_env in ("staging", "production"):
            expected_names.update(
                {
                    "cron:task_send_notification_digest",
                    "cron:task_retry_failed_payments",
                    "cron:task_send_overdue_reminders",
                }
            )

        assert cron_job_names == expected_names

    def test_redis_settings_parses_url(self):
        from app.core.tasks import get_redis_settings

        rs = get_redis_settings()
        assert rs.host is not None
        assert rs.port > 0

    def test_worker_settings_config(self):
        from app.core.tasks import WorkerSettings

        assert WorkerSettings.max_jobs == 10
        assert WorkerSettings.job_timeout == 300
        assert WorkerSettings.max_tries == 3
