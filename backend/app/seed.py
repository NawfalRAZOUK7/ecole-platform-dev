"""Seed data script for development environment.

Creates realistic test data for all 6 domains.
Run with: make seed  (or: docker compose exec backend python -m app.seed)

Reference: Pack C4 (Data Model), Sprint 1 acceptance criteria.
"""

import asyncio
import uuid
from datetime import date, datetime, timedelta, timezone

import bcrypt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session, engine
from app.models.audit import AuditLog
from app.models.billing import Invoice, InvoiceItem, PaymentAttempt
from app.models.com import (
    ConsentPreference,
    Notification,
    NotificationDelivery,
    ParentFeedItem,
)
from app.models.erp import (
    AcademicYear,
    AttendanceRecord,
    AttendanceSession,
    Class,
    Enrollment,
    Period,
    TeacherAssignment,
)
from app.models.iam import (
    AccountRecoveryRequest,
    InvitationCode,
    Membership,
    ParentChildLink,
    Session,
    User,
)
from app.models.lms import (
    Activity,
    ActivitySession,
    Assessment,
    AssessmentResult,
    Assignment,
    ContentItem,
    ContentProgress,
    Course,
    Grade,
    Submission,
)

# ── Fixed UUIDs for deterministic seeding ──────────────────────────────────

SCHOOL_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")
SCHOOL_ID_2 = uuid.UUID("00000000-0000-4000-8000-000000000002")

# Users
ADMIN_ID = uuid.UUID("10000000-0000-4000-8000-000000000001")
DIRECTOR_ID = uuid.UUID("10000000-0000-4000-8000-000000000002")
TEACHER_1_ID = uuid.UUID("10000000-0000-4000-8000-000000000003")
TEACHER_2_ID = uuid.UUID("10000000-0000-4000-8000-000000000004")
PARENT_1_ID = uuid.UUID("10000000-0000-4000-8000-000000000005")
PARENT_2_ID = uuid.UUID("10000000-0000-4000-8000-000000000006")
STUDENT_1_ID = uuid.UUID("10000000-0000-4000-8000-000000000007")
STUDENT_2_ID = uuid.UUID("10000000-0000-4000-8000-000000000008")
STUDENT_3_ID = uuid.UUID("10000000-0000-4000-8000-000000000009")
SUPERADMIN_ID = uuid.UUID("10000000-0000-4000-8000-00000000000a")

# ERP
YEAR_ID = uuid.UUID("20000000-0000-4000-8000-000000000001")
PERIOD_1_ID = uuid.UUID("20000000-0000-4000-8000-000000000002")
PERIOD_2_ID = uuid.UUID("20000000-0000-4000-8000-000000000003")
CLASS_6A_ID = uuid.UUID("20000000-0000-4000-8000-000000000004")
CLASS_6B_ID = uuid.UUID("20000000-0000-4000-8000-000000000005")

# LMS
COURSE_MATH_ID = uuid.UUID("30000000-0000-4000-8000-000000000001")
COURSE_FR_ID = uuid.UUID("30000000-0000-4000-8000-000000000002")
ASSIGN_1_ID = uuid.UUID("30000000-0000-4000-8000-000000000003")
ASSESS_1_ID = uuid.UUID("30000000-0000-4000-8000-000000000004")
CONTENT_1_ID = uuid.UUID("30000000-0000-4000-8000-000000000005")
ACTIVITY_1_ID = uuid.UUID("30000000-0000-4000-8000-000000000006")

# Billing
INVOICE_1_ID = uuid.UUID("40000000-0000-4000-8000-000000000001")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


async def clear_all(session: AsyncSession) -> None:
    """Truncate all tables (CASCADE) to allow re-seeding."""
    await session.execute(
        text(
            "TRUNCATE TABLE audit_logs, provider_webhook_events, payment_proofs, "
            "payment_attempts, invoice_items, invoices, parent_feed_items, "
            "notification_deliveries, notifications, consent_preferences, "
            "activity_sessions, activities, content_progress, content_item_assets, "
            "content_items, grades, submission_files, submissions, assessment_results, "
            "assessments, assignments, courses, justification_reviews, "
            "absence_justifications, attendance_records, attendance_sessions, "
            "teacher_assignments, enrollments, classes, periods, academic_years, "
            "writing_attempts, ai_preferences, parent_child_links, "
            "account_recovery_requests, invitation_codes, sessions, memberships, "
            "users CASCADE"
        )
    )
    await session.commit()


async def seed_iam(session: AsyncSession) -> None:
    """Seed IAM domain: users, memberships, sessions."""
    users = [
        User(
            id=ADMIN_ID,
            email="admin@ecole-benani.ma",
            full_name="Youssef El Amrani",
            password_hash=_hash("admin123"),
            status="active",
            school_id=SCHOOL_ID,
        ),
        User(
            id=DIRECTOR_ID,
            email="directeur@ecole-benani.ma",
            full_name="Fatima Zahra Bennani",
            password_hash=_hash("director123"),
            status="active",
            school_id=SCHOOL_ID,
        ),
        User(
            id=TEACHER_1_ID,
            email="prof.math@ecole-benani.ma",
            full_name="Ahmed Kettani",
            password_hash=_hash("teacher123"),
            status="active",
            school_id=SCHOOL_ID,
        ),
        User(
            id=TEACHER_2_ID,
            email="prof.francais@ecole-benani.ma",
            full_name="Marie Dupont",
            password_hash=_hash("teacher123"),
            status="active",
            school_id=SCHOOL_ID,
        ),
        User(
            id=PARENT_1_ID,
            email="parent.alaoui@gmail.com",
            full_name="Hassan Alaoui",
            phone="+212612345678",
            password_hash=_hash("parent123"),
            status="active",
            school_id=SCHOOL_ID,
        ),
        User(
            id=PARENT_2_ID,
            email="parent.idrissi@gmail.com",
            full_name="Khadija Idrissi",
            phone="+212698765432",
            password_hash=_hash("parent123"),
            status="active",
            school_id=SCHOOL_ID,
        ),
        User(
            id=STUDENT_1_ID,
            email="yassine.alaoui@ecole-benani.ma",
            full_name="Yassine Alaoui",
            password_hash=_hash("student123"),
            status="active",
            school_id=SCHOOL_ID,
        ),
        User(
            id=STUDENT_2_ID,
            email="salma.idrissi@ecole-benani.ma",
            full_name="Salma Idrissi",
            password_hash=_hash("student123"),
            status="active",
            school_id=SCHOOL_ID,
        ),
        User(
            id=STUDENT_3_ID,
            email="omar.benali@ecole-benani.ma",
            full_name="Omar Benali",
            password_hash=_hash("student123"),
            status="active",
            school_id=SCHOOL_ID,
        ),
        User(
            id=SUPERADMIN_ID,
            email="superadmin@ecole-platform.ma",
            full_name="System Admin",
            password_hash=_hash("superadmin123"),
            status="active",
            school_id=SCHOOL_ID,
        ),
    ]
    session.add_all(users)
    await session.flush()

    memberships = [
        Membership(user_id=ADMIN_ID, school_id=SCHOOL_ID, role_code="ADM", status="active"),
        Membership(user_id=DIRECTOR_ID, school_id=SCHOOL_ID, role_code="DIR", status="active"),
        Membership(user_id=TEACHER_1_ID, school_id=SCHOOL_ID, role_code="TCH", status="active"),
        Membership(user_id=TEACHER_2_ID, school_id=SCHOOL_ID, role_code="TCH", status="active"),
        Membership(user_id=PARENT_1_ID, school_id=SCHOOL_ID, role_code="PAR", status="active"),
        Membership(user_id=PARENT_2_ID, school_id=SCHOOL_ID, role_code="PAR", status="active"),
        Membership(user_id=STUDENT_1_ID, school_id=SCHOOL_ID, role_code="STD", status="active"),
        Membership(user_id=STUDENT_2_ID, school_id=SCHOOL_ID, role_code="STD", status="active"),
        Membership(user_id=STUDENT_3_ID, school_id=SCHOOL_ID, role_code="STD", status="active"),
        Membership(user_id=SUPERADMIN_ID, school_id=SCHOOL_ID, role_code="SUP", status="active"),
    ]
    session.add_all(memberships)

    # Create an active session for admin
    session.add(
        Session(
            user_id=ADMIN_ID,
            school_id=SCHOOL_ID,
            source="seed",
            correlation_id=uuid.uuid4(),
        )
    )
    await session.flush()
    print("  [IAM] 10 users, 10 memberships, 1 session")


async def seed_erp(session: AsyncSession) -> None:
    """Seed ERP domain: academic year, periods, classes, enrollments, attendance."""
    # Academic year 2025-2026
    year = AcademicYear(
        id=YEAR_ID,
        school_id=SCHOOL_ID,
        label="2025-2026",
        date_start=date(2025, 9, 1),
        date_end=date(2026, 6, 30),
    )
    session.add(year)
    await session.flush()

    # Two semesters
    p1 = Period(
        id=PERIOD_1_ID,
        academic_year_id=YEAR_ID,
        school_id=SCHOOL_ID,
        label="Semestre 1",
        status="closed",
        date_start=date(2025, 9, 1),
        date_end=date(2026, 1, 31),
    )
    p2 = Period(
        id=PERIOD_2_ID,
        academic_year_id=YEAR_ID,
        school_id=SCHOOL_ID,
        label="Semestre 2",
        status="active",
        date_start=date(2026, 2, 1),
        date_end=date(2026, 6, 30),
    )
    session.add_all([p1, p2])
    await session.flush()

    # Two classes
    c6a = Class(
        id=CLASS_6A_ID,
        school_id=SCHOOL_ID,
        code="6A",
        academic_year_id=YEAR_ID,
        name="6eme A",
    )
    c6b = Class(
        id=CLASS_6B_ID,
        school_id=SCHOOL_ID,
        code="6B",
        academic_year_id=YEAR_ID,
        name="6eme B",
    )
    session.add_all([c6a, c6b])
    await session.flush()

    # Enrollments (students in classes for current period)
    enrollments = [
        Enrollment(student_id=STUDENT_1_ID, class_id=CLASS_6A_ID, period_id=PERIOD_2_ID, school_id=SCHOOL_ID, status="active"),
        Enrollment(student_id=STUDENT_2_ID, class_id=CLASS_6A_ID, period_id=PERIOD_2_ID, school_id=SCHOOL_ID, status="active"),
        Enrollment(student_id=STUDENT_3_ID, class_id=CLASS_6B_ID, period_id=PERIOD_2_ID, school_id=SCHOOL_ID, status="active"),
    ]
    session.add_all(enrollments)

    # Teacher assignments
    assignments = [
        TeacherAssignment(teacher_id=TEACHER_1_ID, class_id=CLASS_6A_ID, period_id=PERIOD_2_ID, school_id=SCHOOL_ID),
        TeacherAssignment(teacher_id=TEACHER_2_ID, class_id=CLASS_6A_ID, period_id=PERIOD_2_ID, school_id=SCHOOL_ID),
        TeacherAssignment(teacher_id=TEACHER_1_ID, class_id=CLASS_6B_ID, period_id=PERIOD_2_ID, school_id=SCHOOL_ID),
    ]
    session.add_all(assignments)

    # One attendance session with records
    att_session = AttendanceSession(
        class_id=CLASS_6A_ID,
        period_id=PERIOD_2_ID,
        teacher_id=TEACHER_1_ID,
        school_id=SCHOOL_ID,
        session_date=date(2026, 3, 10),
        slot="08:00-09:00",
    )
    session.add(att_session)
    await session.flush()

    att_records = [
        AttendanceRecord(attendance_session_id=att_session.id, student_id=STUDENT_1_ID, school_id=SCHOOL_ID, status="present"),
        AttendanceRecord(attendance_session_id=att_session.id, student_id=STUDENT_2_ID, school_id=SCHOOL_ID, status="absent", absence_reason="Maladie"),
    ]
    session.add_all(att_records)
    await session.flush()
    print("  [ERP] 1 year, 2 periods, 2 classes, 3 enrollments, 3 teacher assignments, 1 attendance session")


async def seed_lms(session: AsyncSession) -> None:
    """Seed LMS domain: courses, assignments, submissions, grades, content, activities."""
    # Courses
    math_course = Course(
        id=COURSE_MATH_ID,
        school_id=SCHOOL_ID,
        class_id=CLASS_6A_ID,
        teacher_id=TEACHER_1_ID,
        title="Mathematiques - 6eme A",
        description="Cours de mathematiques pour la classe de 6eme A",
        status="published",
    )
    fr_course = Course(
        id=COURSE_FR_ID,
        school_id=SCHOOL_ID,
        class_id=CLASS_6A_ID,
        teacher_id=TEACHER_2_ID,
        title="Francais - 6eme A",
        description="Cours de francais pour la classe de 6eme A",
        status="published",
    )
    session.add_all([math_course, fr_course])
    await session.flush()

    # Assignment
    assign = Assignment(
        id=ASSIGN_1_ID,
        course_id=COURSE_MATH_ID,
        teacher_id=TEACHER_1_ID,
        title="Exercices - Fractions",
        description="Resoudre les exercices du chapitre 5 sur les fractions",
        due_at=_now() + timedelta(days=7),
        total_points=20,
    )
    session.add(assign)
    await session.flush()

    # Submission + Grade
    sub = Submission(
        assignment_id=ASSIGN_1_ID,
        student_id=STUDENT_1_ID,
        status="graded",
        submitted_at=_now() - timedelta(days=1),
    )
    session.add(sub)
    await session.flush()

    grade = Grade(
        submission_id=sub.id,
        teacher_id=TEACHER_1_ID,
        score=17.5,
        feedback_text="Tres bon travail, attention aux simplifications.",
        published_at=_now(),
    )
    session.add(grade)

    # Assessment
    assess = Assessment(
        id=ASSESS_1_ID,
        class_id=CLASS_6A_ID,
        teacher_id=TEACHER_1_ID,
        title="Controle - Geometrie",
        due_at=_now() + timedelta(days=14),
        window_end=_now() + timedelta(days=14, hours=2),
        total_points=40,
        status="published",
    )
    session.add(assess)
    await session.flush()

    result = AssessmentResult(
        assessment_id=ASSESS_1_ID,
        student_id=STUDENT_1_ID,
        score=35.0,
        status="published",
    )
    session.add(result)

    # Content item
    content = ContentItem(
        id=CONTENT_1_ID,
        school_id=SCHOOL_ID,
        title="Introduction aux fractions",
        content_type="video",
        level_band="6eme",
        language="fr",
        status="published",
    )
    session.add(content)
    await session.flush()

    progress = ContentProgress(
        student_id=STUDENT_1_ID,
        content_item_id=CONTENT_1_ID,
        status="completed",
    )
    session.add(progress)

    # Activity
    activity = Activity(
        id=ACTIVITY_1_ID,
        school_id=SCHOOL_ID,
        type="quiz",
        difficulty="medium",
        title="Quiz - Fractions",
        pedagogical_objective="Verifier la comprehension des fractions",
    )
    session.add(activity)
    await session.flush()

    act_session = ActivitySession(
        student_id=STUDENT_1_ID,
        activity_id=ACTIVITY_1_ID,
        status="completed",
        score=8.0,
        attempt_no=1,
    )
    session.add(act_session)
    await session.flush()
    print("  [LMS] 2 courses, 1 assignment, 1 submission+grade, 1 assessment+result, 1 content+progress, 1 activity+session")


async def seed_com(session: AsyncSession) -> None:
    """Seed COM domain: consent, notifications, feed."""
    # Consent preferences
    consent = ConsentPreference(
        user_id=PARENT_1_ID,
        school_id=SCHOOL_ID,
        topic="attendance",
        channel="email",
        scope_type="student",
        scope_ref_id=STUDENT_1_ID,
        status="opted_in",
    )
    session.add(consent)

    # Notification
    notif = Notification(
        school_id=SCHOOL_ID,
        parent_id=PARENT_1_ID,
        event_ref="attendance:absent:2026-03-10",
        idempotency_key=f"att-absent-{STUDENT_1_ID}-2026-03-10",
        title="Absence signalee",
        body="Votre enfant Yassine a ete signale absent le 10 mars 2026.",
    )
    session.add(notif)
    await session.flush()

    delivery = NotificationDelivery(
        notification_id=notif.id,
        school_id=SCHOOL_ID,
        channel="email",
        status="delivered",
    )
    session.add(delivery)

    # Feed item
    feed = ParentFeedItem(
        school_id=SCHOOL_ID,
        parent_id=PARENT_1_ID,
        student_id=STUDENT_1_ID,
        source_type="grade",
        source_ref=str(ASSIGN_1_ID),
        title="Nouvelle note en Mathematiques",
        body="Yassine a obtenu 17.5/20 en Exercices - Fractions.",
    )
    session.add(feed)
    await session.flush()
    print("  [COM] 1 consent, 1 notification+delivery, 1 feed item")


async def seed_billing(session: AsyncSession) -> None:
    """Seed Billing domain: invoice, items, payment attempt."""
    invoice = Invoice(
        id=INVOICE_1_ID,
        school_id=SCHOOL_ID,
        parent_id=PARENT_1_ID,
        period_id=PERIOD_2_ID,
        status="pending",
        total_amount=3500.00,
        currency="MAD",
        issued_date=date(2026, 2, 1),
        due_date=date(2026, 2, 28),
    )
    session.add(invoice)
    await session.flush()

    items = [
        InvoiceItem(
            invoice_id=INVOICE_1_ID,
            description="Frais de scolarite - Semestre 2",
            amount=3000.00,
            unit_price=3000.00,
            quantity=1,
        ),
        InvoiceItem(
            invoice_id=INVOICE_1_ID,
            description="Frais de transport",
            amount=500.00,
            unit_price=500.00,
            quantity=1,
        ),
    ]
    session.add_all(items)

    payment = PaymentAttempt(
        invoice_id=INVOICE_1_ID,
        parent_id=PARENT_1_ID,
        school_id=SCHOOL_ID,
        idempotency_key=f"pay-{INVOICE_1_ID}-001",
        status="pending",
    )
    session.add(payment)
    await session.flush()
    print("  [Billing] 1 invoice, 2 items, 1 payment attempt")


async def seed_audit(session: AsyncSession) -> None:
    """Seed Audit domain: sample audit log entries."""
    logs = [
        AuditLog(
            school_id=SCHOOL_ID,
            actor_id=ADMIN_ID,
            action_type="user.create",
            target_type="user",
            target_id=TEACHER_1_ID,
            entity_after={"email": "prof.math@ecole-benani.ma", "role": "TCH"},
            outcome="success",
            correlation_id=uuid.uuid4(),
            ip_address="192.168.1.10",
        ),
        AuditLog(
            school_id=SCHOOL_ID,
            actor_id=PARENT_1_ID,
            action_type="auth.login",
            target_type="session",
            outcome="success",
            correlation_id=uuid.uuid4(),
            ip_address="105.159.2.45",
        ),
        AuditLog(
            school_id=SCHOOL_ID,
            actor_id=PARENT_2_ID,
            action_type="enrollment.view",
            target_type="enrollment",
            target_id=STUDENT_1_ID,
            outcome="denied",
            error_code="ERR-IAM-403",
            correlation_id=uuid.uuid4(),
            ip_address="105.159.3.88",
        ),
    ]
    session.add_all(logs)
    await session.flush()
    print("  [Audit] 3 audit log entries")


async def seed_parent_child_links(session: AsyncSession) -> None:
    """Seed parent-child links — explicit parent-student relationships (Phase 1A)."""
    links = [
        # Parent 1 (Hassan Alaoui) -> Student 1 (Yassine Alaoui) — father-son
        ParentChildLink(
            parent_user_id=PARENT_1_ID,
            child_user_id=STUDENT_1_ID,
            school_id=SCHOOL_ID,
            status="active",
            linked_at=_now(),
            linked_by=ADMIN_ID,
        ),
        # Parent 1 (Hassan Alaoui) -> Student 3 (Omar Benali) — second child
        ParentChildLink(
            parent_user_id=PARENT_1_ID,
            child_user_id=STUDENT_3_ID,
            school_id=SCHOOL_ID,
            status="active",
            linked_at=_now(),
            linked_by=ADMIN_ID,
        ),
        # Parent 2 (Khadija Idrissi) -> Student 2 (Salma Idrissi) — mother-daughter
        ParentChildLink(
            parent_user_id=PARENT_2_ID,
            child_user_id=STUDENT_2_ID,
            school_id=SCHOOL_ID,
            status="active",
            linked_at=_now(),
            linked_by=ADMIN_ID,
        ),
    ]
    session.add_all(links)
    await session.flush()
    print("  [IAM] 3 parent-child links (2 parents -> 3 students)")


async def main() -> None:
    print("=" * 60)
    print("Ecole Platform — Seeding development database")
    print("=" * 60)

    async with async_session() as session:
        print("\nClearing existing data...")
        await clear_all(session)

        print("\nSeeding domains:")
        await seed_iam(session)
        await seed_parent_child_links(session)
        await seed_erp(session)
        await seed_lms(session)
        await seed_com(session)
        await seed_billing(session)
        await seed_audit(session)

        await session.commit()

    print("\n" + "=" * 60)
    print("Seeding complete!")
    print("=" * 60)
    print("\nTest credentials:")
    print("  Admin:      admin@ecole-benani.ma / admin123")
    print("  Director:   directeur@ecole-benani.ma / director123")
    print("  Teacher:    prof.math@ecole-benani.ma / teacher123")
    print("  Parent:     parent.alaoui@gmail.com / parent123")
    print("  Student:    yassine.alaoui@ecole-benani.ma / student123")
    print("  Superadmin: superadmin@ecole-platform.ma / superadmin123")


if __name__ == "__main__":
    asyncio.run(main())
