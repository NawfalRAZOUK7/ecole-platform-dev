"""Unit tests for model helper properties and mixins."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from freezegun import freeze_time

from app.models.billing import Invoice, InvoiceStatus, Installment, PaymentPlan
from app.models.calendar import Event
from app.models.com import (
    Conversation,
    ConversationType,
    Notification,
    NotificationDelivery,
)
from app.models.documents import Document
from app.models.erp import AttendanceAlert, Enrollment, EnrollmentStatus
from app.models.iam import (
    AccountRecoveryRequest,
    InvitationCode,
    Membership,
    MembershipStatus,
    Session,
    User,
    UserStatus,
)
from app.models.lms import Assignment, Quiz, QuizStatus, Submission, SubmissionStatus
from app.models.reporting import ReportJob, ReportJobStatus
from app.models.school import School, SchoolStatus


def utc_datetime(
    year: int,
    month: int,
    day: int,
    hour: int = 0,
    minute: int = 0,
    second: int = 0,
) -> datetime:
    return datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)


class TestUserProperties:
    def test_is_active_reflects_status(self):
        assert User(status=UserStatus.ACTIVE.value).is_active is True
        assert User(status=UserStatus.SUSPENDED.value).is_active is False

    def test_has_2fa_reflects_totp_secret(self):
        assert User(totp_secret="secret").has_2fa is True
        assert User(totp_secret=None).has_2fa is False

    def test_is_email_verified_reflects_timestamp(self):
        assert User(email_verified_at=utc_datetime(2026, 3, 1)).is_email_verified is True
        assert User(email_verified_at=None).is_email_verified is False


class TestMembershipProperties:
    def test_is_active_reflects_membership_status(self):
        assert Membership(status=MembershipStatus.ACTIVE.value).is_active is True
        assert Membership(status=MembershipStatus.INACTIVE.value).is_active is False


class TestSessionProperties:
    @freeze_time("2026-03-30 12:00:00")
    def test_is_expired_uses_legacy_expires_at_when_present(self):
        session = Session()
        session.expires_at = utc_datetime(2026, 3, 30, 11, 59, 59)

        assert session.is_expired is True

    @freeze_time("2026-03-30 12:00:00")
    def test_is_expired_is_false_without_or_before_expiry(self):
        session_without_expiry = Session()
        session_future = Session()
        session_future.expires_at = utc_datetime(2026, 3, 30, 12, 0, 1)

        assert session_without_expiry.is_expired is False
        assert session_future.is_expired is False

    def test_is_impersonated_reflects_impersonator_id(self):
        assert Session(impersonator_id=uuid.uuid4()).is_impersonated is True
        assert Session(impersonator_id=None).is_impersonated is False

    def test_is_revoked_supports_current_and_legacy_fields(self):
        revoked_session = Session(revoke_at=utc_datetime(2026, 3, 30, 8))
        legacy_session = Session()
        legacy_session.revoked_at = utc_datetime(2026, 3, 30, 8)
        active_session = Session(revoke_at=None)

        assert revoked_session.is_revoked is True
        assert legacy_session.is_revoked is True
        assert active_session.is_revoked is False


class TestInvitationCodeProperties:
    @freeze_time("2026-03-30 12:00:00")
    def test_is_expired_reflects_expires_at(self):
        assert InvitationCode(expires_at=utc_datetime(2026, 3, 29, 12)).is_expired is True
        assert InvitationCode(expires_at=utc_datetime(2026, 3, 31, 12)).is_expired is False

    def test_is_fully_used_supports_current_schema(self):
        assert InvitationCode(consumed_at=utc_datetime(2026, 3, 30, 9)).is_fully_used is True
        assert InvitationCode(consumed_by=uuid.uuid4()).is_fully_used is True
        assert InvitationCode(consumed_at=None, consumed_by=None).is_fully_used is False

    def test_is_fully_used_supports_legacy_usage_counters(self):
        invitation = InvitationCode(consumed_at=None, consumed_by=None)
        invitation.current_uses = 2
        invitation.max_uses = 2

        assert invitation.is_fully_used is True

        invitation.current_uses = 1
        assert invitation.is_fully_used is False


class TestAccountRecoveryRequestProperties:
    @freeze_time("2026-03-30 12:00:00")
    def test_is_expired_reflects_expires_at(self):
        assert AccountRecoveryRequest(expires_at=utc_datetime(2026, 3, 29, 12)).is_expired is True
        assert AccountRecoveryRequest(expires_at=utc_datetime(2026, 3, 31, 12)).is_expired is False


class TestSchoolProperties:
    @freeze_time("2026-03-30 12:00:00")
    def test_is_subscription_valid_handles_none_future_and_past(self):
        assert School(subscription_expires_at=None).is_subscription_valid is True
        assert School(subscription_expires_at=utc_datetime(2026, 4, 1)).is_subscription_valid is True
        assert School(subscription_expires_at=utc_datetime(2026, 3, 1)).is_subscription_valid is False

    def test_is_active_requires_active_status_and_not_deleted(self):
        assert School(status=SchoolStatus.ACTIVE.value, deleted_at=None).is_active is True
        assert School(status=SchoolStatus.SUSPENDED.value, deleted_at=None).is_active is False
        assert (
            School(
                status=SchoolStatus.ACTIVE.value,
                deleted_at=utc_datetime(2026, 3, 1),
            ).is_active
            is False
        )


class TestAssignmentProperties:
    @freeze_time("2026-03-30 12:00:00")
    def test_is_past_due_reflects_due_at(self):
        assert Assignment(due_at=utc_datetime(2026, 3, 29, 12)).is_past_due is True
        assert Assignment(due_at=utc_datetime(2026, 3, 31, 12)).is_past_due is False
        assert Assignment(due_at=None).is_past_due is False

    @freeze_time("2026-03-30 12:00:00")
    def test_accepts_late_honors_policy_window(self):
        assert (
            Assignment(
                allow_late=True,
                due_at=utc_datetime(2026, 3, 30, 8),
                grace_period_hours=2,
                max_late_days=2,
            ).accepts_late
            is True
        )
        assert (
            Assignment(
                allow_late=False,
                due_at=utc_datetime(2026, 3, 30, 8),
                grace_period_hours=0,
                max_late_days=2,
            ).accepts_late
            is False
        )
        assert (
            Assignment(
                allow_late=True,
                due_at=utc_datetime(2026, 3, 30, 11),
                grace_period_hours=2,
                max_late_days=2,
            ).accepts_late
            is False
        )
        assert (
            Assignment(
                allow_late=True,
                due_at=utc_datetime(2026, 3, 25, 8),
                grace_period_hours=2,
                max_late_days=2,
            ).accepts_late
            is False
        )
        assert Assignment(allow_late=True, due_at=None).accepts_late is False


class TestSubmissionProperties:
    def test_is_graded_reflects_submission_status(self):
        assert Submission(status=SubmissionStatus.GRADED.value).is_graded is True
        assert Submission(status=SubmissionStatus.RETURNED.value).is_graded is True
        assert Submission(status=SubmissionStatus.DRAFT.value).is_graded is False


class TestQuizProperties:
    @freeze_time("2026-03-30 12:00:00")
    def test_is_active_requires_published_status_and_schedule_window(self):
        assert Quiz(status=QuizStatus.DRAFT.value).is_active is False
        assert Quiz(status=QuizStatus.PUBLISHED.value).is_active is True

        future_quiz = Quiz(status=QuizStatus.PUBLISHED.value)
        future_quiz.start_at = utc_datetime(2026, 3, 31, 12)
        assert future_quiz.is_active is False

        expired_quiz = Quiz(status=QuizStatus.PUBLISHED.value)
        expired_quiz.ends_at = utc_datetime(2026, 3, 29, 12)
        assert expired_quiz.is_active is False


class TestEnrollmentAndAttendanceProperties:
    def test_enrollment_is_active_reflects_status(self):
        assert Enrollment(status=EnrollmentStatus.ACTIVE.value).is_active is True
        assert Enrollment(status=EnrollmentStatus.DROPPED.value).is_active is False

    def test_attendance_alert_is_resolved_uses_legacy_field(self):
        unresolved = AttendanceAlert()
        resolved = AttendanceAlert()
        resolved.resolved_at = utc_datetime(2026, 3, 30, 10)

        assert unresolved.is_resolved is False
        assert resolved.is_resolved is True


class TestInvoiceProperties:
    @freeze_time("2026-03-30 12:00:00")
    def test_is_overdue_requires_pending_and_past_due_date(self):
        assert (
            Invoice(status=InvoiceStatus.PENDING.value, due_date=date(2026, 3, 29)).is_overdue
            is True
        )
        assert (
            Invoice(status=InvoiceStatus.PENDING.value, due_date=date(2026, 3, 31)).is_overdue
            is False
        )
        assert (
            Invoice(status=InvoiceStatus.PAID.value, due_date=date(2026, 3, 29)).is_overdue
            is False
        )

    def test_is_paid_reflects_invoice_status(self):
        assert Invoice(status=InvoiceStatus.PAID.value).is_paid is True
        assert Invoice(status=InvoiceStatus.PENDING.value).is_paid is False


class TestPaymentPlanAndInstallmentProperties:
    def test_is_completed_reflects_plan_status(self):
        assert PaymentPlan(status="completed").is_completed is True
        assert PaymentPlan(status="active").is_completed is False

    @freeze_time("2026-03-30 12:00:00")
    def test_installment_is_overdue_requires_unpaid_past_due_date(self):
        assert Installment(due_date=utc_datetime(2026, 3, 29), paid_at=None).is_overdue is True
        assert Installment(due_date=utc_datetime(2026, 3, 31), paid_at=None).is_overdue is False
        assert (
            Installment(
                due_date=utc_datetime(2026, 3, 29),
                paid_at=utc_datetime(2026, 3, 29, 12),
            ).is_overdue
            is False
        )


class TestCommunicationProperties:
    def test_notification_is_read_reflects_read_at(self):
        assert Notification(read_at=utc_datetime(2026, 3, 30, 9)).is_read is True
        assert Notification(read_at=None).is_read is False

    def test_notification_delivery_status_returns_status(self):
        delivery = NotificationDelivery(status="delivered")

        assert delivery.delivery_status == "delivered"

    def test_conversation_is_group_reflects_type(self):
        assert Conversation(type=ConversationType.GROUP.value).is_group is True
        assert Conversation(type=ConversationType.DIRECT.value).is_group is False


class TestDocumentAndCalendarProperties:
    @freeze_time("2026-03-30 12:00:00")
    def test_document_is_expired_reflects_expires_at(self):
        assert Document(expires_at=utc_datetime(2026, 3, 29, 12)).is_expired is True
        assert Document(expires_at=utc_datetime(2026, 3, 31, 12)).is_expired is False
        assert Document(expires_at=None).is_expired is False

    @freeze_time("2026-03-30 12:00:00")
    def test_event_is_past_reflects_end_time(self):
        assert Event(end_at=utc_datetime(2026, 3, 29, 12)).is_past is True
        assert Event(end_at=utc_datetime(2026, 3, 31, 12)).is_past is False


class TestReportingProperties:
    def test_report_job_is_complete_reflects_status(self):
        assert ReportJob(status=ReportJobStatus.READY.value).is_complete is True
        assert ReportJob(status=ReportJobStatus.GENERATING.value).is_complete is False

    @freeze_time("2026-03-30 12:00:00")
    def test_report_job_is_expired_reflects_expires_at(self):
        assert ReportJob(expires_at=utc_datetime(2026, 3, 29, 12)).is_expired is True
        assert ReportJob(expires_at=utc_datetime(2026, 3, 31, 12)).is_expired is False
        assert ReportJob(expires_at=None).is_expired is False


class TestSoftDeleteMixin:
    def test_is_deleted_reflects_deleted_at(self):
        assert Document(deleted_at=utc_datetime(2026, 3, 1)).is_deleted is True
        assert Document(deleted_at=None).is_deleted is False

    def test_soft_delete_sets_deleted_at(self):
        document = Document(deleted_at=None)

        document.soft_delete()

        assert document.deleted_at is not None
        assert document.is_deleted is True

    def test_restore_clears_deleted_at(self):
        document = Document(deleted_at=utc_datetime(2026, 3, 1))

        document.restore()

        assert document.deleted_at is None
        assert document.is_deleted is False
