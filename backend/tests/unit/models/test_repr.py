"""Unit tests for model repr output."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from app.models.billing import Invoice, InvoiceStatus
from app.models.calendar import Event
from app.models.com import Notification, NotificationCategory
from app.models.documents import Document, DocumentCategory
from app.models.iam import ParentChildLink, Session, User, UserStatus
from app.models.lms import Assignment, Course, ExerciseType
from app.models.reporting import ReportJob, ReportJobStatus, ReportType
from app.models.school import School, SchoolStatus


def utc_datetime(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, tzinfo=timezone.utc)


class TestModelRepr:
    def test_user_repr_has_email_and_excludes_password_hash(self):
        user = User(
            id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            email="user@example.com",
            status=UserStatus.ACTIVE.value,
            password_hash="super-secret-hash",
        )

        rendered = repr(user)

        assert "11111111" in rendered
        assert "user@example.com" in rendered
        assert "active" in rendered
        assert "password_hash" not in rendered
        assert "super-secret-hash" not in rendered

    def test_school_repr_has_name_and_status(self):
        school = School(
            id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
            name="Ecole Atlas",
            status=SchoolStatus.ACTIVE.value,
        )

        rendered = repr(school)

        assert "22222222" in rendered
        assert "Ecole Atlas" in rendered
        assert "active" in rendered

    def test_invoice_repr_has_identifier_status_and_total(self):
        invoice = Invoice(
            id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
            status=InvoiceStatus.PENDING.value,
            total_amount=500.0,
            due_date=date(2026, 3, 30),
            issued_date=date(2026, 3, 1),
        )

        rendered = repr(invoice)

        assert "33333333" in rendered
        assert "pending" in rendered
        assert "500.0" in rendered

    def test_course_repr_has_title_and_status(self):
        course = Course(
            id=uuid.UUID("44444444-4444-4444-4444-444444444444"),
            title="Mathematiques 6A",
            status="published",
        )

        rendered = repr(course)

        assert "44444444" in rendered
        assert "Mathematiques 6A" in rendered
        assert "published" in rendered

    def test_assignment_repr_has_title_and_exercise_type(self):
        assignment = Assignment(
            id=uuid.UUID("55555555-5555-5555-5555-555555555555"),
            title="Controle continu",
            exercise_type=ExerciseType.QUIZ.value,
        )

        rendered = repr(assignment)

        assert "55555555" in rendered
        assert "Controle continu" in rendered
        assert "QUIZ" in rendered

    def test_notification_repr_has_category_and_read_state(self):
        notification = Notification(
            id=uuid.UUID("66666666-6666-6666-6666-666666666666"),
            category=NotificationCategory.BILLING.value,
            read_at=utc_datetime(2026, 3, 30),
        )

        rendered = repr(notification)

        assert "66666666" in rendered
        assert "billing" in rendered
        assert "is_read=True" in rendered

    def test_document_repr_has_filename_and_category(self):
        document = Document(
            id=uuid.UUID("77777777-7777-7777-7777-777777777777"),
            filename="bulletin.pdf",
            category=DocumentCategory.REPORT_CARD.value,
        )

        rendered = repr(document)

        assert "77777777" in rendered
        assert "bulletin.pdf" in rendered
        assert "report_card" in rendered

    def test_event_repr_has_title_and_start(self):
        event = Event(
            id=uuid.UUID("88888888-8888-8888-8888-888888888888"),
            title_fr="Reunion parents-professeurs",
            start_at=utc_datetime(2026, 4, 2),
        )

        rendered = repr(event)

        assert "88888888" in rendered
        assert "Reunion parents-professeurs" in rendered
        assert "2026-04-02" in rendered

    def test_report_job_repr_has_type_and_status(self):
        job = ReportJob(
            id=uuid.UUID("99999999-9999-9999-9999-999999999999"),
            type=ReportType.ATTENDANCE_REPORT.value,
            status=ReportJobStatus.READY.value,
        )

        rendered = repr(job)

        assert "99999999" in rendered
        assert "attendance_report" in rendered
        assert "ready" in rendered

    def test_session_repr_uses_user_id_and_impersonation_state(self):
        session = Session(
            id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
            user_id=uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
            impersonator_id=uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
        )

        rendered = repr(session)

        assert "aaaaaaaa" in rendered
        assert "bbbbbbbb" in rendered
        assert "impersonated=True" in rendered

    def test_parent_child_link_repr_has_both_participants(self):
        link = ParentChildLink(
            id=uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd"),
            parent_user_id=uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"),
            child_user_id=uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"),
        )

        rendered = repr(link)

        assert "dddddddd" in rendered
        assert "eeeeeeee" in rendered
        assert "ffffffff" in rendered
