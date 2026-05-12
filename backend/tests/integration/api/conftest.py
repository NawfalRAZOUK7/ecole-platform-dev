"""Legacy API integration fixtures for isolated endpoint tests.

These older tests authenticate via ``/auth/login`` using fixed seed credentials.
Populate the disposable test database with the matching baseline rows before the
shared API client is used.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import httpx
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

import app.models  # noqa: F401
from app.core.database import Base, get_db
from app.core.security import hash_password
from app.models.billing import Invoice, InvoiceItem
from app.main import app
from app.models.erp import (
    AcademicYear,
    AttendanceRecord,
    AttendanceSession,
    Class,
    Enrollment,
    Period,
    TeacherAssignment,
)
from app.models.iam import ParentChildLink, RoleCode, User
from app.models.com import ParentFeedItem
from app.models.lms import (
    Activity,
    Assessment,
    AssessmentResult,
    Assignment,
    ContentItem,
    Course,
    Grade,
    Submission,
)
from app.models.school import School
from tests.factories.erp import (
    AcademicYearFactory,
    AttendanceRecordFactory,
    AttendanceSessionFactory,
    ClassFactory,
    EnrollmentFactory,
    PeriodFactory,
)
from tests.factories.iam import MembershipFactory, ParentChildLinkFactory, UserFactory
from tests.factories.school import SchoolFactory

SCHOOL_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")
YEAR_ID = uuid.UUID("20000000-0000-4000-8000-000000000001")
PERIOD_ID = uuid.UUID("20000000-0000-4000-8000-000000000003")
CLASS_ID = uuid.UUID("20000000-0000-4000-8000-000000000004")
PARENT_CHILD_LINK_ID = uuid.UUID("71000000-0000-4000-8000-000000000001")
ENROLLMENT_ID = uuid.UUID("72000000-0000-4000-8000-000000000001")
TEACHER_ASSIGNMENT_ID = uuid.UUID("73000000-0000-4000-8000-000000000001")
ATTENDANCE_SESSION_ID = uuid.UUID("74000000-0000-4000-8000-000000000001")
ATTENDANCE_RECORD_ID = uuid.UUID("75000000-0000-4000-8000-000000000001")
INVOICE_ID = uuid.UUID("40000000-0000-4000-8000-000000000001")
INVOICE_ITEM_ID = uuid.UUID("41000000-0000-4000-8000-000000000001")
COURSE_ID = uuid.UUID("30000000-0000-4000-8000-000000000001")
SUBMISSION_ID = uuid.UUID("30000000-0000-4000-8000-000000000002")
ASSIGNMENT_ID = uuid.UUID("30000000-0000-4000-8000-000000000003")
ASSESSMENT_ID = uuid.UUID("30000000-0000-4000-8000-000000000004")
CONTENT_ITEM_ID = uuid.UUID("30000000-0000-4000-8000-000000000005")
ACTIVITY_ID = uuid.UUID("30000000-0000-4000-8000-000000000006")
GRADE_ID = uuid.UUID("30000000-0000-4000-8000-000000000007")
ASSESSMENT_RESULT_ID = uuid.UUID("30000000-0000-4000-8000-000000000008")
PARENT_FEED_ITEM_ID = uuid.UUID("30000000-0000-4000-8000-000000000009")

ADMIN_ID = uuid.UUID("10000000-0000-4000-8000-000000000001")
TEACHER_ID = uuid.UUID("10000000-0000-4000-8000-000000000003")
PARENT_ID = uuid.UUID("10000000-0000-4000-8000-000000000005")
STUDENT_ID = uuid.UUID("10000000-0000-4000-8000-000000000007")
SUPERADMIN_ID = uuid.UUID("10000000-0000-4000-8000-00000000000a")

ADMIN_EMAIL = "admin@ecole-benani.ma"
ADMIN_PASSWORD = "admin123"
TEACHER_EMAIL = "prof.math@ecole-benani.ma"
TEACHER_PASSWORD = "teacher123"
PARENT_EMAIL = "parent.alaoui@gmail.com"
PARENT_PASSWORD = "parent123"
STUDENT_EMAIL = "yassine.alaoui@ecole-benani.ma"
STUDENT_PASSWORD = "student123"
SUPERADMIN_EMAIL = "superadmin@ecole-platform.ma"
SUPERADMIN_PASSWORD = "superadmin123"

TRUNCATE_ALL_TABLES_SQL = text(
    "TRUNCATE TABLE "
    + ", ".join(f'"{table.name}"' for table in Base.metadata.sorted_tables)
    + " RESTART IDENTITY CASCADE"
)


async def _create_actor(
    session: AsyncSession,
    *,
    school,
    user_id: uuid.UUID,
    email: str,
    password: str,
    full_name: str,
    role_code: str,
):
    user = await UserFactory.create(
        session=session,
        school=school,
        id=user_id,
        email=email,
        full_name=full_name,
        password_hash=hash_password(password),
    )
    await MembershipFactory.create(
        session=session,
        user=user,
        school_id=school.id,
        role_code=role_code,
    )
    return user


@pytest_asyncio.fixture(loop_scope="function")
async def session_factory(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(loop_scope="function")
async def isolated_legacy_api_db(session_factory):
    async with session_factory() as session:
        await session.execute(TRUNCATE_ALL_TABLES_SQL)
        await session.commit()
    try:
        yield
    finally:
        async with session_factory() as session:
            await session.execute(TRUNCATE_ALL_TABLES_SQL)
            await session.commit()


@pytest_asyncio.fixture(loop_scope="function")
async def legacy_api_seed(isolated_legacy_api_db, session_factory):
    _ = isolated_legacy_api_db

    async with session_factory() as session:
        school = await session.get(School, SCHOOL_ID)
        if school is None:
            school = await SchoolFactory.create(
                session=session,
                id=SCHOOL_ID,
                code="ecole-benani",
                name="Ecole Benani",
                city="Casablanca",
                email="contact@ecole-benani.ma",
            )
        academic_year = await session.get(AcademicYear, YEAR_ID)
        if academic_year is None:
            academic_year = await AcademicYearFactory.create(
                session=session,
                id=YEAR_ID,
                school=school,
                label="2025-2026",
            )
        period = await session.get(Period, PERIOD_ID)
        if period is None:
            period = await PeriodFactory.create(
                session=session,
                id=PERIOD_ID,
                school=school,
                academic_year=academic_year,
                label="Trimester 2",
            )
        school_class = await session.get(Class, CLASS_ID)
        if school_class is None:
            school_class = await ClassFactory.create(
                session=session,
                id=CLASS_ID,
                school=school,
                academic_year=academic_year,
                code="6eme-A",
                name="6eme A",
            )

        admin = await session.get(User, ADMIN_ID)
        if admin is None:
            admin = await _create_actor(
                session,
                school=school,
                user_id=ADMIN_ID,
                email=ADMIN_EMAIL,
                password=ADMIN_PASSWORD,
                full_name="Admin Benani",
                role_code=RoleCode.ADM.value,
            )
        teacher = await session.get(User, TEACHER_ID)
        if teacher is None:
            teacher = await _create_actor(
                session,
                school=school,
                user_id=TEACHER_ID,
                email=TEACHER_EMAIL,
                password=TEACHER_PASSWORD,
                full_name="Prof Math",
                role_code=RoleCode.TCH.value,
            )
        parent = await session.get(User, PARENT_ID)
        if parent is None:
            parent = await _create_actor(
                session,
                school=school,
                user_id=PARENT_ID,
                email=PARENT_EMAIL,
                password=PARENT_PASSWORD,
                full_name="Parent Alaoui",
                role_code=RoleCode.PAR.value,
            )
        student = await session.get(User, STUDENT_ID)
        if student is None:
            student = await _create_actor(
                session,
                school=school,
                user_id=STUDENT_ID,
                email=STUDENT_EMAIL,
                password=STUDENT_PASSWORD,
                full_name="Yassine Alaoui",
                role_code=RoleCode.STD.value,
            )
        if await session.get(User, SUPERADMIN_ID) is None:
            await _create_actor(
                session,
                school=school,
                user_id=SUPERADMIN_ID,
                email=SUPERADMIN_EMAIL,
                password=SUPERADMIN_PASSWORD,
                full_name="Platform Superadmin",
                role_code=RoleCode.SUP.value,
            )

        if await session.get(ParentChildLink, PARENT_CHILD_LINK_ID) is None:
            await ParentChildLinkFactory.create(
                session=session,
                id=PARENT_CHILD_LINK_ID,
                school=school,
                parent=parent,
                child=student,
                linked_by=admin.id,
            )
        if await session.get(Enrollment, ENROLLMENT_ID) is None:
            await EnrollmentFactory.create(
                session=session,
                id=ENROLLMENT_ID,
                school=school,
                academic_year=academic_year,
                class_obj=school_class,
                period=period,
                student=student,
            )
        if await session.get(TeacherAssignment, TEACHER_ASSIGNMENT_ID) is None:
            session.add(
                TeacherAssignment(
                    id=TEACHER_ASSIGNMENT_ID,
                    school_id=school.id,
                    teacher_id=teacher.id,
                    class_id=school_class.id,
                    period_id=period.id,
                )
            )
        attendance_session = await session.get(AttendanceSession, ATTENDANCE_SESSION_ID)
        if attendance_session is None:
            attendance_session = await AttendanceSessionFactory.create(
                session=session,
                id=ATTENDANCE_SESSION_ID,
                school=school,
                academic_year=academic_year,
                class_obj=school_class,
                period=period,
                teacher=teacher,
                session_date=date(2026, 1, 15),
                slot="morning",
            )
        if await session.get(AttendanceRecord, ATTENDANCE_RECORD_ID) is None:
            await AttendanceRecordFactory.create(
                session=session,
                id=ATTENDANCE_RECORD_ID,
                attendance_session=attendance_session,
                student=student,
                status="absent",
            )
        if await session.get(Invoice, INVOICE_ID) is None:
            session.add(
                Invoice(
                    id=INVOICE_ID,
                    school_id=school.id,
                    parent_id=parent.id,
                    period_id=period.id,
                    status="pending",
                    total_amount=Decimal("3500.00"),
                    currency="MAD",
                    issued_date=date(2026, 2, 1),
                    due_date=date(2026, 2, 28),
                )
            )
        if await session.get(InvoiceItem, INVOICE_ITEM_ID) is None:
            session.add(
                InvoiceItem(
                    id=INVOICE_ITEM_ID,
                    invoice_id=INVOICE_ID,
                    description="Frais de scolarite - Semestre 2",
                    amount=Decimal("3500.00"),
                    unit_price=Decimal("3500.00"),
                    quantity=1,
                    tva_rate=Decimal("0.00"),
                    tva_amount=Decimal("0.00"),
                    amount_ht=Decimal("3500.00"),
                    amount_ttc=Decimal("3500.00"),
                )
            )
        if await session.get(Course, COURSE_ID) is None:
            session.add(
                Course(
                    id=COURSE_ID,
                    school_id=school.id,
                    class_id=school_class.id,
                    teacher_id=teacher.id,
                    title="Mathematiques 6eme",
                    description="Cours de mathematiques de reference",
                    status="published",
                )
            )
        if await session.get(Assignment, ASSIGNMENT_ID) is None:
            session.add(
                Assignment(
                    id=ASSIGNMENT_ID,
                    course_id=COURSE_ID,
                    teacher_id=teacher.id,
                    title="Devoir de fractions",
                    description="Exercices de fractions",
                    total_points=20,
                    grace_period_hours=0,
                    late_penalty_per_day=0.0,
                    max_late_days=3,
                    allow_late=True,
                    exercise_type="STANDARD",
                )
            )
        if await session.get(Submission, SUBMISSION_ID) is None:
            session.add(
                Submission(
                    id=SUBMISSION_ID,
                    assignment_id=ASSIGNMENT_ID,
                    student_id=student.id,
                    status="submitted",
                    submitted_at=datetime.now(timezone.utc),
                )
            )
        if await session.get(Grade, GRADE_ID) is None:
            session.add(
                Grade(
                    id=GRADE_ID,
                    submission_id=SUBMISSION_ID,
                    teacher_id=teacher.id,
                    score=Decimal("16.00"),
                    original_score=Decimal("16.00"),
                    late_penalty=0.0,
                    late_days=0,
                    penalty_overridden=False,
                    feedback_text="Bon travail",
                    published_at=datetime.now(timezone.utc),
                )
            )
        if await session.get(ContentItem, CONTENT_ITEM_ID) is None:
            session.add(
                ContentItem(
                    id=CONTENT_ITEM_ID,
                    school_id=school.id,
                    title="Lecture guidee",
                    content_type="document",
                    level_band="6eme",
                    language="fr",
                    status="published",
                    subject="Francais",
                    created_by=teacher.id,
                    description="Support de lecture pour les eleves",
                    origin="PLATFORM",
                )
            )
        if await session.get(Activity, ACTIVITY_ID) is None:
            session.add(
                Activity(
                    id=ACTIVITY_ID,
                    school_id=school.id,
                    type="quiz",
                    difficulty="easy",
                    title="Activite fractions",
                    pedagogical_objective="Reviser les fractions",
                )
            )
        if await session.get(Assessment, ASSESSMENT_ID) is None:
            session.add(
                Assessment(
                    id=ASSESSMENT_ID,
                    class_id=school_class.id,
                    teacher_id=teacher.id,
                    title="Evaluation diagnostique",
                    total_points=100,
                    status="published",
                )
            )
        if await session.get(AssessmentResult, ASSESSMENT_RESULT_ID) is None:
            session.add(
                AssessmentResult(
                    id=ASSESSMENT_RESULT_ID,
                    assessment_id=ASSESSMENT_ID,
                    student_id=student.id,
                    score=Decimal("15.00"),
                    status="submitted",
                )
            )
        if await session.get(ParentFeedItem, PARENT_FEED_ITEM_ID) is None:
            session.add(
                ParentFeedItem(
                    id=PARENT_FEED_ITEM_ID,
                    school_id=school.id,
                    parent_id=parent.id,
                    student_id=student.id,
                    source_type="grade_published",
                    source_ref=str(GRADE_ID),
                    title="Nouvelle note publiee",
                    body="Yassine a recu une nouvelle note en mathematiques.",
                )
            )

        # Seed default level-age mappings (G46) so /levels endpoints work
        _DEFAULT_LEVEL_MAPPINGS = [
            ("maternelle", "Maternelle", "ما قبل المدرسة", "Preschool", 3, 5, 0),
            ("cp", "Cours Préparatoire", "السنة الأولى ابتدائي", "1st Grade", 5, 6, 1),
            (
                "ce1",
                "Cours Élémentaire 1",
                "السنة الثانية ابتدائي",
                "2nd Grade",
                6,
                7,
                2,
            ),
            (
                "ce2",
                "Cours Élémentaire 2",
                "السنة الثالثة ابتدائي",
                "3rd Grade",
                7,
                8,
                3,
            ),
            ("cm1", "Cours Moyen 1", "السنة الرابعة ابتدائي", "4th Grade", 8, 9, 4),
            ("cm2", "Cours Moyen 2", "السنة الخامسة ابتدائي", "5th Grade", 9, 10, 5),
            ("6eme", "6ème", "السادسة إعدادي", "6th Grade", 10, 11, 6),
            ("5eme", "5ème", "الخامسة إعدادي", "7th Grade", 11, 12, 7),
            ("4eme", "4ème", "الرابعة إعدادي", "8th Grade", 12, 13, 8),
            ("3eme", "3ème", "الثالثة إعدادي", "9th Grade", 13, 14, 9),
            ("2nde", "Seconde", "الثانية ثانوي", "10th Grade", 14, 15, 10),
            ("1ere", "Première", "الأولى ثانوي", "11th Grade", 15, 16, 11),
            ("terminale", "Terminale", "الجذع المشترك", "12th Grade", 16, 17, 12),
        ]
        result = await session.execute(
            text("SELECT COUNT(*) FROM level_age_mappings WHERE school_id IS NULL")
        )
        count = result.scalar_one()
        if count < len(_DEFAULT_LEVEL_MAPPINGS):
            for (
                level_code,
                label_fr,
                label_ar,
                label_en,
                age_min,
                age_max,
                order,
            ) in _DEFAULT_LEVEL_MAPPINGS:
                await session.execute(
                    text(
                        """
                        INSERT INTO level_age_mappings
                          (id, level_code, label_fr, label_ar, label_en,
                           default_age_min, default_age_max, display_order, created_at)
                        VALUES
                          (gen_random_uuid(), :level_code, :label_fr, :label_ar, :label_en,
                           :age_min, :age_max, :order, now())
                        ON CONFLICT DO NOTHING
                        """
                    ),
                    {
                        "level_code": level_code,
                        "label_fr": label_fr,
                        "label_ar": label_ar,
                        "label_en": label_en,
                        "age_min": age_min,
                        "age_max": age_max,
                        "order": order,
                    },
                )

        await session.commit()

    return {
        "school": school,
        "academic_year": academic_year,
        "period": period,
        "class": school_class,
        "admin": admin,
        "teacher": teacher,
        "parent": parent,
        "student": student,
    }


@pytest_asyncio.fixture(loop_scope="function")
async def client(legacy_api_seed, session_factory):
    _ = legacy_api_seed

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver/api/v1",
    ) as api_client:
        yield api_client
    app.dependency_overrides.clear()
