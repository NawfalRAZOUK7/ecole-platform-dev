"""Error-path tests for missing entities, duplicates, and cascading deletes."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.dependencies import AuthContext
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.repositories.calendar import CalendarRepository
from app.repositories.lms import LMSRepository
from app.schemas.billing import FeeAssignmentCreateRequest, FeeStructureUpdateRequest
from app.schemas.billing_enhancements import PaymentPlanCreateRequest
from app.schemas.school import SchoolUpdateRequest
from app.services import billing as billing_module
from app.services import payment_plan as payment_plan_module
from app.services.billing import BillingService
from app.services.lms._helpers import LMSServiceBase, calculate_late_penalty
from app.services.payment_plan import PaymentPlanService
from app.services.school import SchoolService
from tests.factories.billing import FeeStructureFactory
from tests.factories.erp import AcademicYearFactory, ClassFactory, EnrollmentFactory, PeriodFactory
from tests.factories.iam import InvitationCodeFactory, UserFactory
from tests.factories.school import SchoolFactory


def make_auth(role: str = "ADM", school_id: uuid.UUID | None = None) -> AuthContext:
    return AuthContext(
        user_id=uuid.uuid4(),
        role=role,
        school_id=school_id or uuid.uuid4(),
        session_id=uuid.uuid4(),
        permissions=set(),
    )


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.session = AsyncMock()
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def commit(self) -> None:
        self.committed = True


def make_school_stub(school_id: uuid.UUID) -> SimpleNamespace:
    now = datetime(2026, 3, 30, tzinfo=timezone.utc)
    return SimpleNamespace(
        id=school_id,
        name="Edge School",
        name_ar=None,
        code="EDGE-001",
        massar_code=None,
        status="active",
        address=None,
        city="Casablanca",
        region=None,
        phone="+212600000000",
        email="contact@edge.ma",
        website=None,
        logo_path=None,
        max_students=100,
        max_teachers=20,
        subscription_plan="standard",
        subscription_expires_at=None,
        timezone="Africa/Casablanca",
        default_language="fr",
        grading_scale="moroccan_20",
        settings={},
        is_active=True,
        is_subscription_valid=True,
        deleted_at=None,
        created_at=now,
        updated_at=now,
    )


def setup_school_service() -> SchoolService:
    service = SchoolService(AsyncMock())
    service.repo = AsyncMock()
    return service


def setup_payment_plan_service(monkeypatch: pytest.MonkeyPatch) -> PaymentPlanService:
    service = PaymentPlanService(AsyncMock())
    service.billing_repo = AsyncMock()
    service.repo = AsyncMock()
    service.audit = AsyncMock()
    uow = FakeUnitOfWork()
    repo_in_uow = AsyncMock()
    audit_in_uow = AsyncMock()

    monkeypatch.setattr(payment_plan_module, "UnitOfWork", lambda _db: uow)
    monkeypatch.setattr(
        payment_plan_module,
        "BillingEnhancementsRepository",
        lambda _session: repo_in_uow,
    )
    monkeypatch.setattr(payment_plan_module, "AuditService", lambda _session: audit_in_uow)
    return service


def setup_billing_service(monkeypatch: pytest.MonkeyPatch) -> BillingService:
    service = BillingService(AsyncMock())
    service.repo = AsyncMock()
    service.enhancements_repo = AsyncMock()
    service.audit = AsyncMock()
    service._dispatcher = SimpleNamespace(dispatch=AsyncMock())
    uow = FakeUnitOfWork()

    monkeypatch.setattr(billing_module, "UnitOfWork", lambda _db: uow)
    monkeypatch.setattr(billing_module, "BillingRepository", lambda _session: AsyncMock())
    monkeypatch.setattr(
        billing_module,
        "BillingEnhancementsRepository",
        lambda _session: AsyncMock(),
    )
    monkeypatch.setattr(billing_module, "AuditService", lambda _session: AsyncMock())
    return service


class TestServiceErrorPaths:
    @pytest.mark.asyncio
    async def test_school_get_school_raises_not_found(self) -> None:
        service = setup_school_service()
        service.repo.get_school.return_value = None

        with pytest.raises(NotFoundError, match="School not found"):
            await service.get_school(school_id=uuid.uuid4(), auth=make_auth("SUP"))

    @pytest.mark.asyncio
    async def test_school_update_raises_not_found_for_missing_school(self) -> None:
        service = setup_school_service()
        service.repo.get_school.return_value = None

        with pytest.raises(NotFoundError, match="School not found"):
            await service.update_school(
                school_id=uuid.uuid4(),
                body=SchoolUpdateRequest(city="Rabat"),
                auth=make_auth("SUP"),
            )

    @pytest.mark.asyncio
    async def test_school_list_returns_empty_when_current_school_missing(self) -> None:
        auth = make_auth("ADM")
        service = setup_school_service()
        service.repo.get_school.return_value = None

        items, next_cursor, has_more = await service.list_schools(
            auth=auth,
            cursor=None,
            limit=20,
            status=None,
        )

        assert items == []
        assert next_cursor is None
        assert has_more is False

    @pytest.mark.asyncio
    async def test_school_list_returns_empty_for_status_mismatch(self) -> None:
        school_id = uuid.uuid4()
        auth = make_auth("ADM", school_id=school_id)
        service = setup_school_service()
        service.repo.get_school.return_value = make_school_stub(school_id)

        items, next_cursor, has_more = await service.list_schools(
            auth=auth,
            cursor=None,
            limit=20,
            status="suspended",
        )

        assert items == []
        assert next_cursor is None
        assert has_more is False

    @pytest.mark.asyncio
    async def test_payment_plan_get_plan_raises_not_found(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        service = setup_payment_plan_service(monkeypatch)
        service.repo.get_payment_plan.return_value = None

        with pytest.raises(NotFoundError, match="Payment plan not found"):
            await service.get_plan(plan_id=uuid.uuid4(), auth=make_auth("ADM"))

    @pytest.mark.asyncio
    async def test_payment_plan_mark_installment_paid_raises_not_found(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        service = setup_payment_plan_service(monkeypatch)
        service.repo.get_installment.return_value = None

        with pytest.raises(NotFoundError, match="Installment not found"):
            await service.mark_installment_paid(installment_id=uuid.uuid4())

    @pytest.mark.asyncio
    async def test_payment_plan_create_plan_raises_when_invoice_missing(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        service = setup_payment_plan_service(monkeypatch)
        service.billing_repo.get_invoice_by_id.return_value = None

        with pytest.raises(NotFoundError, match="Invoice not found"):
            await service.create_plan(
                body=PaymentPlanCreateRequest(
                    invoice_id=uuid.uuid4(),
                    num_installments=3,
                ),
                auth=make_auth("ADM"),
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_billing_update_fee_structure_raises_not_found(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        service = setup_billing_service(monkeypatch)
        service.repo.get_fee_structure.return_value = None

        with pytest.raises(NotFoundError, match="Fee structure not found"):
            await service.update_fee_structure(
                fee_structure_id=uuid.uuid4(),
                body=FeeStructureUpdateRequest(name="Updated"),
                auth=make_auth("ADM"),
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_billing_create_fee_assignment_raises_when_fee_structure_missing(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        service = setup_billing_service(monkeypatch)
        service.repo.get_fee_structure.return_value = None

        with pytest.raises(NotFoundError, match="Fee structure not found"):
            await service.create_fee_assignment(
                body=FeeAssignmentCreateRequest(
                    fee_structure_id=uuid.uuid4(),
                    student_id=uuid.uuid4(),
                    discount_percent=0,
                ),
                auth=make_auth("ADM"),
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_billing_create_fee_assignment_raises_when_student_missing(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("ADM")
        service = setup_billing_service(monkeypatch)
        service.repo.get_fee_structure.return_value = SimpleNamespace(
            id=uuid.uuid4(),
            school_id=auth.school_id,
        )
        service.repo.get_user_by_id.return_value = None

        with pytest.raises(NotFoundError, match="Student not found"):
            await service.create_fee_assignment(
                body=FeeAssignmentCreateRequest(
                    fee_structure_id=uuid.uuid4(),
                    student_id=uuid.uuid4(),
                    discount_percent=0,
                ),
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_billing_create_fee_assignment_raises_for_duplicate_assignment(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("ADM")
        student_id = uuid.uuid4()
        fee_structure_id = uuid.uuid4()
        service = setup_billing_service(monkeypatch)
        service.repo.get_fee_structure.return_value = SimpleNamespace(
            id=fee_structure_id,
            school_id=auth.school_id,
        )
        service.repo.get_user_by_id.return_value = SimpleNamespace(id=student_id)
        service.repo.get_fee_assignment.return_value = SimpleNamespace(id=uuid.uuid4())

        with pytest.raises(ConflictError, match="Fee already assigned"):
            await service.create_fee_assignment(
                body=FeeAssignmentCreateRequest(
                    fee_structure_id=fee_structure_id,
                    student_id=student_id,
                    discount_percent=100,
                ),
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_lms_get_exercise_pdf_raises_when_assignment_missing(self) -> None:
        service = LMSServiceBase(AsyncMock())
        service.repo = AsyncMock()
        service.repo.get_assignment_with_course.return_value = None

        with pytest.raises(NotFoundError, match="Assignment not found"):
            await service.get_exercise_pdf(
                assignment_id=uuid.uuid4(),
                auth=make_auth("TCH"),
            )

    @pytest.mark.asyncio
    async def test_lms_get_submission_file_raises_when_file_missing(self) -> None:
        service = LMSServiceBase(AsyncMock())
        service.repo = AsyncMock()
        service.repo.get_submission_file.return_value = None

        with pytest.raises(NotFoundError, match="File not found"):
            await service.get_submission_file(
                submission_id=uuid.uuid4(),
                file_id=uuid.uuid4(),
                auth=make_auth("STD"),
            )

    def test_calculate_late_penalty_rejects_disallowed_late_submission(self) -> None:
        assignment = SimpleNamespace(
            due_at=datetime(2026, 3, 29, 10, 0, tzinfo=timezone.utc),
            grace_period_hours=0,
            allow_late=False,
            max_late_days=3,
            late_penalty_per_day=2.0,
        )
        submission = SimpleNamespace(
            submitted_at=datetime(2026, 3, 30, 10, 0, tzinfo=timezone.utc)
        )

        with pytest.raises(ValidationError, match="Late submissions are not allowed"):
            calculate_late_penalty(
                assignment=assignment,
                submission=submission,
                original_score=18.0,
            )

    def test_calculate_late_penalty_rejects_submission_beyond_max_days(self) -> None:
        assignment = SimpleNamespace(
            due_at=datetime(2026, 3, 29, 10, 0, tzinfo=timezone.utc),
            grace_period_hours=0,
            allow_late=True,
            max_late_days=1,
            late_penalty_per_day=2.0,
        )
        submission = SimpleNamespace(
            submitted_at=datetime(2026, 3, 31, 10, 0, tzinfo=timezone.utc)
        )

        with pytest.raises(ValidationError, match="maximum allowed late days"):
            calculate_late_penalty(
                assignment=assignment,
                submission=submission,
                original_score=18.0,
            )


class TestRepositoryAndDatabaseErrorPaths:
    @pytest.mark.asyncio
    async def test_duplicate_school_code_raises_integrity_error(self, db_session) -> None:
        school_id = uuid.uuid4()
        await SchoolFactory.create(
            session=db_session,
            id=school_id,
            code="EDGE-DUP-SCHOOL",
            email="first@edge.ma",
        )

        with pytest.raises(IntegrityError):
            await SchoolFactory.create(
                session=db_session,
                id=uuid.uuid4(),
                code="EDGE-DUP-SCHOOL",
                email="second@edge.ma",
            )

    @pytest.mark.asyncio
    async def test_duplicate_invitation_code_hash_raises_integrity_error(self, db_session) -> None:
        school = await SchoolFactory.create(
            session=db_session,
            code="EDGE-INV-SCHOOL",
            email="invites@edge.ma",
        )
        await InvitationCodeFactory.create(
            session=db_session,
            school_id=school.id,
            code_hash="fixed-hash",
        )

        with pytest.raises(IntegrityError):
            await InvitationCodeFactory.create(
                session=db_session,
                school_id=school.id,
                code_hash="fixed-hash",
            )

    @pytest.mark.asyncio
    async def test_duplicate_active_enrollment_raises_integrity_error(self, db_session) -> None:
        school = await SchoolFactory.create(
            session=db_session,
            code="EDGE-ENROLL-SCHOOL",
            email="enrollments@edge.ma",
        )
        year = await AcademicYearFactory.create(session=db_session, school_id=school.id)
        period = await PeriodFactory.create(
            session=db_session,
            school_id=school.id,
            academic_year_id=year.id,
        )
        klass = await ClassFactory.create(
            session=db_session,
            school_id=school.id,
            academic_year_id=year.id,
            code="EDGE-CLS-001",
        )
        student = await UserFactory.create(
            session=db_session,
            school_id=school.id,
            email="student-enrollment@edge.ma",
        )
        await EnrollmentFactory.create(
            session=db_session,
            school_id=school.id,
            academic_year=year,
            period=period,
            class_obj=klass,
            student=student,
        )

        with pytest.raises(IntegrityError):
            await EnrollmentFactory.create(
                session=db_session,
                school_id=school.id,
                academic_year=year,
                period=period,
                class_obj=klass,
                student=student,
            )

    @pytest.mark.asyncio
    async def test_duplicate_fee_assignment_unique_key_raises_integrity_error(
        self,
        db_session,
    ) -> None:
        auth = make_auth("ADM")
        service = BillingService(db_session)
        school = await SchoolFactory.create(
            session=db_session,
            id=auth.school_id,
            code="EDGE-FEE-SCHOOL",
            email="fees@edge.ma",
        )
        year = await AcademicYearFactory.create(session=db_session, school_id=school.id)
        student = await UserFactory.create(
            session=db_session,
            school_id=school.id,
            email="student-fee@edge.ma",
        )
        await UserFactory.create(
            session=db_session,
            id=auth.user_id,
            school_id=school.id,
            email="admin-fee@edge.ma",
        )
        fee_structure = await FeeStructureFactory.create(
            session=db_session,
            school_id=school.id,
            academic_year_id=year.id,
        )

        await service.create_fee_assignment(
            body=FeeAssignmentCreateRequest(
                fee_structure_id=fee_structure.id,
                student_id=student.id,
                discount_percent=0,
            ),
            auth=auth,
            ip_address=None,
        )

        with pytest.raises(ConflictError, match="Fee already assigned"):
            await service.create_fee_assignment(
                body=FeeAssignmentCreateRequest(
                    fee_structure_id=fee_structure.id,
                    student_id=student.id,
                    discount_percent=0,
                ),
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_deleting_course_cascades_assignments(self, db_session) -> None:
        school = await SchoolFactory.create(
            session=db_session,
            code="EDGE-CASCADE-SCHOOL",
            email="cascade@edge.ma",
        )
        year = await AcademicYearFactory.create(session=db_session, school_id=school.id)
        klass = await ClassFactory.create(
            session=db_session,
            school_id=school.id,
            academic_year_id=year.id,
            code="EDGE-CASCADE-CLS",
        )
        teacher = await UserFactory.create(
            session=db_session,
            school_id=school.id,
            email="teacher-cascade@edge.ma",
        )
        repo = LMSRepository(db_session)
        course = await repo.create_course(
            id=uuid.uuid4(),
            school_id=school.id,
            class_id=klass.id,
            teacher_id=teacher.id,
            title="Cascade Course",
            description="Cascade test",
            status="published",
        )
        assignment = await repo.create_assignment(
            id=uuid.uuid4(),
            course_id=course.id,
            teacher_id=teacher.id,
            title="Cascade Assignment",
            description="Cascade body",
            total_points=20,
            grace_period_hours=0,
            late_penalty_per_day=2.0,
            max_late_days=3,
            allow_late=True,
            exercise_type="STANDARD",
        )
        await db_session.flush()

        await db_session.delete(course)
        await db_session.flush()

        result = await db_session.execute(
            select(type(assignment)).where(type(assignment).id == assignment.id)
        )

        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_current_academic_year_returns_none_when_no_matching_record(
        self,
        db_session,
    ) -> None:
        school = await SchoolFactory.create(
            session=db_session,
            code="EDGE-CALENDAR-SCHOOL",
            email="calendar@edge.ma",
        )
        repo = CalendarRepository(db_session)

        result = await repo.get_current_academic_year(
            school_id=school.id,
            on_date=date(2026, 3, 30),
        )

        assert result is None
