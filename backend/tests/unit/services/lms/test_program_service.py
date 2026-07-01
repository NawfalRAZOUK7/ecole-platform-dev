"""Unit tests for ProgramService — Academic Program Management & History (G49).

These tests exercise the assignment branching logic in isolation by stubbing
the database access layer. They do NOT require a running PostgreSQL or
Redis instance; an integration-level smoke test against the real schema
lives next to the migration in tests/integration/test_program_g49.py.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.dependencies import AuthContext
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.erp import EnrollmentStatus, ProgramAssignmentReason
import app.services.lms.program_service as program_module
from app.services.lms.program_service import ProgramService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def make_auth(role: str = "ADM", school_id: uuid.UUID | None = None) -> AuthContext:
    return AuthContext(
        user_id=uuid.uuid4(),
        role=role,
        school_id=school_id or uuid.uuid4(),
        session_id=uuid.uuid4(),
        permissions=set(),
    )


class FakeUnitOfWork:
    """Minimal UnitOfWork double that records a `commit()` and lets the test
    inspect/mutate the in-flight session via ``self.session``."""

    def __init__(self) -> None:
        self.session = SimpleNamespace()
        self.committed = False
        # Per-test override hooks
        self.added: list[object] = []
        self.gotten: dict[tuple, object | None] = {}

        async def _get(model, oid):
            return self.gotten.get((model, oid))

        self.session.add = lambda obj: self.added.append(obj)
        self.session.get = AsyncMock(side_effect=_get)
        self.session.flush = AsyncMock()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def commit(self) -> None:
        self.committed = True


def make_program(
    *,
    school_id: uuid.UUID,
    code: str = "SCI-MATH",
    is_active: bool = True,
):
    return SimpleNamespace(
        id=uuid.uuid4(),
        school_id=school_id,
        code=code,
        name="Sciences Mathématiques",
        level="lycee",
        description=None,
        is_active=is_active,
        version_label="1.0",
        effective_from=None,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated_at=None,
    )


def make_enrollment(
    *,
    school_id: uuid.UUID,
    student_id: uuid.UUID,
    period_id: uuid.UUID | None = None,
    program_id: uuid.UUID | None = None,
    program_version_id: uuid.UUID | None = None,
    status: str = EnrollmentStatus.ACTIVE.value,
):
    return SimpleNamespace(
        id=uuid.uuid4(),
        school_id=school_id,
        student_id=student_id,
        class_id=uuid.uuid4(),
        period_id=period_id or uuid.uuid4(),
        program_id=program_id,
        program_version_id=program_version_id,
        status=status,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated_at=None,
    )


def make_period(school_id: uuid.UUID):
    return SimpleNamespace(
        id=uuid.uuid4(),
        school_id=school_id,
        academic_year_id=uuid.uuid4(),
        status="active",
    )


def setup_service(monkeypatch: pytest.MonkeyPatch):
    service = ProgramService(AsyncMock())
    service.repo = AsyncMock()
    service.audit = AsyncMock()
    uow = FakeUnitOfWork()

    monkeypatch.setattr(program_module, "UnitOfWork", lambda _db: uow)
    monkeypatch.setattr(program_module, "AuditService", lambda _session: AsyncMock())
    return service, uow


# ---------------------------------------------------------------------------
# assign_program_to_enrollment — branching invariants
# ---------------------------------------------------------------------------
class TestAssignProgramInvariants:
    @pytest.mark.asyncio
    async def test_invalid_reason_code_raises_validation_error(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        service, _uow = setup_service(monkeypatch)
        auth = make_auth("ADM")

        with pytest.raises(ValidationError):
            await service.assign_program_to_enrollment(
                enrollment_id=uuid.uuid4(),
                program_id=uuid.uuid4(),
                reason_code="not-a-real-reason",
                reason_note=None,
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_missing_enrollment_raises_404(self, monkeypatch: pytest.MonkeyPatch):
        service, _uow = setup_service(monkeypatch)
        auth = make_auth("ADM")
        service._fetch_enrollment = AsyncMock(return_value=None)

        with pytest.raises(NotFoundError):
            await service.assign_program_to_enrollment(
                enrollment_id=uuid.uuid4(),
                program_id=uuid.uuid4(),
                reason_code="INITIAL",
                reason_note=None,
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_inactive_program_raises_409(self, monkeypatch: pytest.MonkeyPatch):
        service, _uow = setup_service(monkeypatch)
        auth = make_auth("ADM")

        enrollment = make_enrollment(school_id=auth.school_id, student_id=uuid.uuid4())
        program = make_program(school_id=auth.school_id, is_active=False)
        service._fetch_enrollment = AsyncMock(return_value=enrollment)
        service._fetch_program = AsyncMock(return_value=program)

        with pytest.raises(ConflictError):
            await service.assign_program_to_enrollment(
                enrollment_id=enrollment.id,
                program_id=program.id,
                reason_code="INITIAL",
                reason_note=None,
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_same_program_no_op_raises_409(self, monkeypatch: pytest.MonkeyPatch):
        service, _uow = setup_service(monkeypatch)
        auth = make_auth("ADM")

        program = make_program(school_id=auth.school_id)
        enrollment = make_enrollment(
            school_id=auth.school_id,
            student_id=uuid.uuid4(),
            program_id=program.id,  # already on this program
        )
        period = make_period(auth.school_id)
        service._fetch_enrollment = AsyncMock(return_value=enrollment)
        service._fetch_program = AsyncMock(return_value=program)
        service.repo.get_period.return_value = period
        service._academic_year_id_for_period = AsyncMock(
            return_value=period.academic_year_id
        )

        with pytest.raises(ConflictError):
            await service.assign_program_to_enrollment(
                enrollment_id=enrollment.id,
                program_id=program.id,
                reason_code="TRANSFER",
                reason_note=None,
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_initial_assignment_in_place_writes_event(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        """First-time program assignment updates in place + writes one event."""
        service, uow = setup_service(monkeypatch)
        auth = make_auth("ADM")

        program = make_program(school_id=auth.school_id)
        enrollment = make_enrollment(
            school_id=auth.school_id,
            student_id=uuid.uuid4(),
            program_id=None,  # programless
        )
        period = make_period(auth.school_id)

        service._fetch_enrollment = AsyncMock(return_value=enrollment)
        service._fetch_program = AsyncMock(return_value=program)
        service.repo.get_period.return_value = period
        service._academic_year_id_for_period = AsyncMock(
            return_value=period.academic_year_id
        )

        # session.get(Enrollment, ...) returns the same enrollment object so
        # the in-place update path mutates it.
        from app.models.erp import Enrollment as EnrollmentModel

        uow.gotten[(EnrollmentModel, enrollment.id)] = enrollment

        result = await service.assign_program_to_enrollment(
            enrollment_id=enrollment.id,
            program_id=program.id,
            reason_code="INITIAL",
            reason_note="first program",
            auth=auth,
            ip_address=None,
        )

        # In-place update assigned the program on the existing row.
        assert enrollment.program_id == program.id
        assert enrollment.status == EnrollmentStatus.ACTIVE.value

        # Exactly one event was added (no replacement enrollment, since this
        # is the first assignment).
        from app.models.erp import ProgramAssignmentEvent

        events = [o for o in uow.added if isinstance(o, ProgramAssignmentEvent)]
        assert len(events) == 1
        event = events[0]
        assert event.from_program_id is None
        assert event.to_program_id == program.id
        assert event.from_enrollment_id == enrollment.id
        assert event.to_enrollment_id == enrollment.id  # same row
        assert event.reason_code == ProgramAssignmentReason.INITIAL.value
        assert event.actor_user_id == auth.user_id

        # Response dict points at the event row.
        assert result["reason_code"] == "INITIAL"
        assert result["from_program_id"] is None
        assert result["to_program_id"] == str(program.id)

        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_real_change_soft_replaces_old_enrollment(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        """Mid-period TRANSFER: old enrollment marked TRANSFERRED, new active row
        created with the new program, one event written."""
        service, uow = setup_service(monkeypatch)
        auth = make_auth("ADM")

        old_program = make_program(school_id=auth.school_id, code="SCI-MATH")
        new_program = make_program(school_id=auth.school_id, code="LM")
        student_id = uuid.uuid4()
        enrollment = make_enrollment(
            school_id=auth.school_id,
            student_id=student_id,
            program_id=old_program.id,
        )
        period = make_period(auth.school_id)

        service._fetch_enrollment = AsyncMock(return_value=enrollment)
        service._fetch_program = AsyncMock(return_value=new_program)
        service.repo.get_period.return_value = period
        service._academic_year_id_for_period = AsyncMock(
            return_value=period.academic_year_id
        )

        from app.models.erp import Enrollment as EnrollmentModel

        uow.gotten[(EnrollmentModel, enrollment.id)] = enrollment

        await service.assign_program_to_enrollment(
            enrollment_id=enrollment.id,
            program_id=new_program.id,
            reason_code="TRANSFER",
            reason_note="parent request",
            auth=auth,
            ip_address=None,
        )

        # Old enrollment was demoted (soft-replace), not deleted.
        assert enrollment.status == EnrollmentStatus.TRANSFERRED.value

        # A new active enrollment with the new program was inserted.
        new_enrollments = [
            o
            for o in uow.added
            if isinstance(o, EnrollmentModel)
            and getattr(o, "program_id", None) == new_program.id
        ]
        assert len(new_enrollments) == 1
        replacement = new_enrollments[0]
        assert replacement.student_id == student_id
        assert replacement.school_id == auth.school_id
        assert replacement.class_id == enrollment.class_id
        assert replacement.period_id == enrollment.period_id
        assert replacement.status == EnrollmentStatus.ACTIVE.value

        # Exactly one event row, from old → new, linking both enrollments.
        from app.models.erp import ProgramAssignmentEvent

        events = [o for o in uow.added if isinstance(o, ProgramAssignmentEvent)]
        assert len(events) == 1
        event = events[0]
        assert event.from_program_id == old_program.id
        assert event.to_program_id == new_program.id
        assert event.from_enrollment_id == enrollment.id
        assert event.to_enrollment_id == replacement.id
        assert event.reason_code == "TRANSFER"
        assert event.reason_note == "parent request"

        assert uow.committed is True


# ---------------------------------------------------------------------------
# School boundary masking (404, not 403)
# ---------------------------------------------------------------------------
class TestSchoolBoundary:
    @pytest.mark.asyncio
    async def test_cross_school_enrollment_is_masked_to_404(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        service, _uow = setup_service(monkeypatch)
        auth = make_auth("ADM", school_id=uuid.uuid4())

        # Enrollment belongs to a *different* school.
        enrollment = make_enrollment(school_id=uuid.uuid4(), student_id=uuid.uuid4())
        service._fetch_enrollment = AsyncMock(return_value=enrollment)

        with pytest.raises(NotFoundError):
            await service.assign_program_to_enrollment(
                enrollment_id=enrollment.id,
                program_id=uuid.uuid4(),
                reason_code="INITIAL",
                reason_note=None,
                auth=auth,
                ip_address=None,
            )


# ---------------------------------------------------------------------------
# Reason-code enum surface
# ---------------------------------------------------------------------------
class TestReasonEnum:
    def test_reason_codes_match_the_db_check_constraint(self):
        """If this list ever drifts from the ck_prog_assignment_events_reason_code
        Postgres CHECK, the schema and the application enum disagree."""
        assert {r.value for r in ProgramAssignmentReason} == {
            "INITIAL",
            "TRANSFER",
            "PROMOTION",
            "CORRECTION",
            "READMISSION",
        }
