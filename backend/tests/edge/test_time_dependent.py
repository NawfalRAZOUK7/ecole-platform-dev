"""Time-dependent tests covering expiry, late penalties, and timezone edges."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest
from freezegun import freeze_time

from app.models.billing import Invoice, InvoiceStatus
from app.models.documents import Document
from app.models.iam import AccountRecoveryRequest, InvitationCode, Session
from app.models.lms import Assignment
from app.models.reporting import ReportJob
from app.models.school import School
from app.repositories.calendar import CalendarRepository
from app.services.lms._helpers import calculate_late_penalty
from tests.factories.erp import AcademicYearFactory
from tests.factories.school import SchoolFactory


CASABLANCA = ZoneInfo("Africa/Casablanca")


def local_midnight_utc(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, 0, 0, tzinfo=CASABLANCA).astimezone(
        timezone.utc
    )


def make_late_penalty_assignment(
    *,
    due_at: datetime,
    grace_period_hours: int = 0,
    allow_late: bool = True,
    max_late_days: int | None = 3,
    late_penalty_per_day: float = 2.0,
) -> Assignment:
    return Assignment(
        due_at=due_at,
        grace_period_hours=grace_period_hours,
        allow_late=allow_late,
        max_late_days=max_late_days,
        late_penalty_per_day=late_penalty_per_day,
        total_points=20,
    )


class TestExpiryEdges:
    @freeze_time("2026-03-30T10:00:00Z")
    def test_session_expiry_is_false_at_exact_second(self) -> None:
        session = Session()
        session.expires_at = datetime(2026, 3, 30, 10, 0, tzinfo=timezone.utc)

        assert session.is_expired is False

    @freeze_time("2026-03-30T10:00:01Z")
    def test_session_expiry_turns_true_after_exact_second(self) -> None:
        session = Session()
        session.expires_at = datetime(2026, 3, 30, 10, 0, tzinfo=timezone.utc)

        assert session.is_expired is True

    @freeze_time("2026-03-30T12:00:00Z")
    def test_invitation_code_is_not_expired_at_exact_second(self) -> None:
        invite = InvitationCode(expires_at=datetime(2026, 3, 30, 12, 0, tzinfo=timezone.utc))

        assert invite.is_expired is False

    @freeze_time("2026-03-30T12:00:01Z")
    def test_account_recovery_request_expires_after_deadline(self) -> None:
        request = AccountRecoveryRequest(
            expires_at=datetime(2026, 3, 30, 12, 0, tzinfo=timezone.utc)
        )

        assert request.is_expired is True

    @freeze_time("2026-03-30T08:59:59Z")
    def test_school_subscription_is_valid_before_expiration(self) -> None:
        school = School(
            subscription_expires_at=datetime(2026, 3, 30, 9, 0, tzinfo=timezone.utc)
        )

        assert school.is_subscription_valid is True

    @freeze_time("2026-03-30T09:00:00Z")
    def test_school_subscription_becomes_invalid_at_exact_expiration(self) -> None:
        school = School(
            subscription_expires_at=datetime(2026, 3, 30, 9, 0, tzinfo=timezone.utc)
        )

        assert school.is_subscription_valid is False

    @freeze_time("2026-03-30T14:00:00Z")
    def test_report_job_is_not_expired_at_exact_deadline(self) -> None:
        job = ReportJob(expires_at=datetime(2026, 3, 30, 14, 0, tzinfo=timezone.utc))

        assert job.is_expired is False

    @freeze_time("2026-03-30T14:00:01Z")
    def test_document_is_expired_after_deadline(self) -> None:
        document = Document(expires_at=datetime(2026, 3, 30, 14, 0, tzinfo=timezone.utc))

        assert document.is_expired is True


class TestCasablancaBoundaries:
    @freeze_time((local_midnight_utc(2026, 6, 30) - timedelta(seconds=1)).isoformat())
    def test_assignment_is_not_past_due_before_casablanca_midnight(self) -> None:
        due_at = local_midnight_utc(2026, 6, 30)
        assignment = Assignment(due_at=due_at)

        assert assignment.is_past_due is False

    @freeze_time((local_midnight_utc(2026, 6, 30) + timedelta(seconds=1)).isoformat())
    def test_assignment_is_past_due_after_casablanca_midnight(self) -> None:
        due_at = local_midnight_utc(2026, 6, 30)
        assignment = Assignment(due_at=due_at)

        assert assignment.is_past_due is True

    @freeze_time("2026-03-30T12:00:00Z")
    def test_assignment_accepts_late_is_false_at_exact_grace_deadline(self) -> None:
        assignment = Assignment(
            due_at=datetime(2026, 3, 30, 10, 0, tzinfo=timezone.utc),
            allow_late=True,
            grace_period_hours=2,
            max_late_days=3,
            total_points=20,
            late_penalty_per_day=2.0,
        )

        assert assignment.accepts_late is False

    @freeze_time("2026-03-30T12:00:01Z")
    def test_assignment_accepts_late_is_true_after_grace_deadline(self) -> None:
        assignment = Assignment(
            due_at=datetime(2026, 3, 30, 10, 0, tzinfo=timezone.utc),
            allow_late=True,
            grace_period_hours=2,
            max_late_days=3,
            total_points=20,
            late_penalty_per_day=2.0,
        )

        assert assignment.accepts_late is True

    @freeze_time("2026-03-20T12:00:00Z")
    def test_invoice_is_not_overdue_on_due_date(self) -> None:
        invoice = Invoice(
            status=InvoiceStatus.PENDING.value,
            due_date=date(2026, 3, 20),
        )

        assert invoice.is_overdue is False

    @freeze_time("2026-03-21T00:00:01Z")
    def test_invoice_is_overdue_after_due_date_rolls_over(self) -> None:
        invoice = Invoice(
            status=InvoiceStatus.PENDING.value,
            due_date=date(2026, 3, 20),
        )

        assert invoice.is_overdue is True

    @freeze_time("2026-03-30T00:00:00Z")
    def test_late_penalty_counts_one_day_at_23_59_59_boundary(self) -> None:
        due_at = datetime(2026, 3, 29, 0, 0, tzinfo=timezone.utc)
        assignment = make_late_penalty_assignment(due_at=due_at)
        submission = type(
            "SubmissionStub",
            (),
            {"submitted_at": datetime(2026, 3, 29, 23, 59, 59, tzinfo=timezone.utc)},
        )()

        result = calculate_late_penalty(
            assignment=assignment,
            submission=submission,
            original_score=20.0,
        )

        assert result["late_days"] == 1
        assert result["late_penalty"] == 2.0

    @freeze_time("2026-03-30T00:00:00Z")
    def test_late_penalty_rolls_to_two_days_after_day_boundary(self) -> None:
        due_at = datetime(2026, 3, 29, 0, 0, tzinfo=timezone.utc)
        assignment = make_late_penalty_assignment(due_at=due_at)
        submission = type(
            "SubmissionStub",
            (),
            {"submitted_at": datetime(2026, 3, 30, 0, 0, 1, tzinfo=timezone.utc)},
        )()

        result = calculate_late_penalty(
            assignment=assignment,
            submission=submission,
            original_score=20.0,
        )

        assert result["late_days"] == 2
        assert result["late_penalty"] == 4.0

    @freeze_time("2026-03-01T12:00:00Z")
    def test_casablanca_timezone_has_ramadan_offset_transition(self) -> None:
        offsets = {
            (
                datetime(2026, 2, 1, 12, 0, tzinfo=CASABLANCA) + timedelta(days=offset)
            ).utcoffset()
            for offset in range(0, 140)
        }

        assert len(offsets) >= 2

    @pytest.mark.asyncio
    @freeze_time("2026-06-30T12:00:00Z")
    async def test_current_academic_year_matches_before_july_transition(self, db_session) -> None:
        repo = CalendarRepository(db_session)
        school = await SchoolFactory.create(session=db_session, code="CAL-EDGE-001")
        current_year = await AcademicYearFactory.create(
            session=db_session,
            school_id=school.id,
            label="2025-2026",
            date_start=date(2025, 9, 1),
            date_end=date(2026, 6, 30),
        )
        await AcademicYearFactory.create(
            session=db_session,
            school_id=school.id,
            label="2026-2027",
            date_start=date(2026, 7, 1),
            date_end=date(2027, 6, 30),
        )

        found = await repo.get_current_academic_year(
            school_id=school.id,
            on_date=date.today(),
        )

        assert found is not None
        assert found.id == current_year.id

    @pytest.mark.asyncio
    @freeze_time("2026-07-01T12:00:00Z")
    async def test_current_academic_year_switches_on_july_first(self, db_session) -> None:
        repo = CalendarRepository(db_session)
        school = await SchoolFactory.create(session=db_session, code="CAL-EDGE-002")
        await AcademicYearFactory.create(
            session=db_session,
            school_id=school.id,
            label="2025-2026",
            date_start=date(2025, 9, 1),
            date_end=date(2026, 6, 30),
        )
        next_year = await AcademicYearFactory.create(
            session=db_session,
            school_id=school.id,
            label="2026-2027",
            date_start=date(2026, 7, 1),
            date_end=date(2027, 6, 30),
        )

        found = await repo.get_current_academic_year(
            school_id=school.id,
            on_date=date.today(),
        )

        assert found is not None
        assert found.id == next_year.id
