"""Seed data script for development environment.

Creates realistic test data for all 6 domains.
Run with: make seed  (or: docker compose exec backend python -m app.seed)

Reference: Pack C4 (Data Model), Sprint 1 acceptance criteria.
"""

import asyncio
import uuid
from datetime import date, datetime, timedelta, timezone

import bcrypt
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.audit import AuditLog
from app.models.billing import (
    FeeAssignment,
    FeeStructure,
    Invoice,
    InvoiceItem,
    PaymentAttempt,
)
from app.models.com import (
    Announcement,
    ConsentPreference,
    Conversation,
    ConversationParticipant,
    Message,
    MessageReadReceipt,
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
    TimetableException,
    TimetableSlot,
)
from app.models.feature import FeatureToggle
from app.models.games import GameConfig
from app.models.iam import (
    Membership,
    ParentChildLink,
    ParentProfile,
    Session,
    StudentProfile,
    TeacherProfile,
    User,
)
from app.models.lms import (
    Activity,
    ActivitySession,
    Assessment,
    AssessmentResult,
    Assignment,
    ClassContentAssignment,
    ContentItem,
    ContentProgress,
    ContentSubmission,
    Course,
    Grade,
    Quiz,
    QuizAttempt,
    QuizQuestion,
    Submission,
)
from app.models.men_compliance import MenCurriculum, MenObjective
from app.models.rewards import RewardBadge, RewardEvent, StudentReward
from app.models.school import School
from app.models.skill_passport import SkillDimension, SkillMilestone, SkillProgress
from app.models.difficulty_adaptation import DifficultyAdaptation
from app.seed_extensions import (
    seed_ai_preferences,
    seed_calendar,
    seed_documents,
    seed_notification_preferences,
    seed_programs,
    seed_reporting,
)
from app.services.compliance_service import seed_men_reference_data

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
CONTENT_MGR_ID = uuid.UUID("10000000-0000-4000-8000-00000000000b")

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

# Phase 9A — Platform content
PLATFORM_CONTENT_1_ID = uuid.UUID("30000000-0000-4000-8000-000000000010")
PLATFORM_CONTENT_2_ID = uuid.UUID("30000000-0000-4000-8000-000000000011")
PLATFORM_CONTENT_3_ID = uuid.UUID("30000000-0000-4000-8000-000000000012")
PLATFORM_CONTENT_4_ID = uuid.UUID("30000000-0000-4000-8000-000000000013")
PLATFORM_CONTENT_5_ID = uuid.UUID("30000000-0000-4000-8000-000000000014")
PLATFORM_CONTENT_6_ID = uuid.UUID("30000000-0000-4000-8000-000000000015")

# Phase 9B — Quizzes
QUIZ_MATH_ID = uuid.UUID("30000000-0000-4000-8000-000000000020")
QUIZ_FR_ID = uuid.UUID("30000000-0000-4000-8000-000000000021")

# Phase 11A — Timetable
SLOT_MATH_6A_MON_ID = uuid.UUID("50000000-0000-4000-8000-000000000001")
SLOT_FR_6A_MON_ID = uuid.UUID("50000000-0000-4000-8000-000000000002")
SLOT_MATH_6A_WED_ID = uuid.UUID("50000000-0000-4000-8000-000000000003")
SLOT_FR_6A_THU_ID = uuid.UUID("50000000-0000-4000-8000-000000000004")
SLOT_MATH_6B_TUE_ID = uuid.UUID("50000000-0000-4000-8000-000000000005")
SLOT_FR_6B_TUE_ID = uuid.UUID("50000000-0000-4000-8000-000000000006")

# Phase 11B — Fee Structures
FEE_SCOLARITE_ID = uuid.UUID("60000000-0000-4000-8000-000000000001")
FEE_TRANSPORT_ID = uuid.UUID("60000000-0000-4000-8000-000000000002")
FEE_CANTINE_ID = uuid.UUID("60000000-0000-4000-8000-000000000003")

# Phase 11C — Messaging & Announcements
CONV_1_ID = uuid.UUID("70000000-0000-4000-8000-000000000001")
CONV_2_ID = uuid.UUID("70000000-0000-4000-8000-000000000002")
ANN_1_ID = uuid.UUID("70000000-0000-4000-8000-000000000010")
ANN_2_ID = uuid.UUID("70000000-0000-4000-8000-000000000011")

# Billing
INVOICE_1_ID = uuid.UUID("40000000-0000-4000-8000-000000000001")

# Phase G8 — Additional students (different levels for age-banded content testing)
STUDENT_CP_ID = uuid.UUID("10000000-0000-4000-8000-00000000000c")
STUDENT_CE2_ID = uuid.UUID("10000000-0000-4000-8000-00000000000d")
STUDENT_CM2_ID = uuid.UUID("10000000-0000-4000-8000-00000000000e")
STUDENT_3EME_ID = uuid.UUID("10000000-0000-4000-8000-00000000000f")
STUDENT_TERM_ID = uuid.UUID("10000000-0000-4000-8000-000000000010")

PARENT_TAZI_ID = uuid.UUID("10000000-0000-4000-8000-000000000011")
PARENT_FASSI_ID = uuid.UUID("10000000-0000-4000-8000-000000000012")

CLASS_CP_ID = uuid.UUID("20000000-0000-4000-8000-000000000010")
CLASS_CE2_ID = uuid.UUID("20000000-0000-4000-8000-000000000011")
CLASS_CM2_ID = uuid.UUID("20000000-0000-4000-8000-000000000012")
CLASS_3EME_ID = uuid.UUID("20000000-0000-4000-8000-000000000013")
CLASS_TERM_ID = uuid.UUID("20000000-0000-4000-8000-000000000014")

# Skill system
DIM_MATH_ID = uuid.UUID("80000000-0000-4000-8000-000000000001")
DIM_LECTURE_ID = uuid.UUID("80000000-0000-4000-8000-000000000002")
DIM_SCIENCES_ID = uuid.UUID("80000000-0000-4000-8000-000000000003")
DIM_CREATIVITE_ID = uuid.UUID("80000000-0000-4000-8000-000000000004")
DIM_COMM_ID = uuid.UUID("80000000-0000-4000-8000-000000000005")

# Extra announcements / billing for admin demo
ANN_3_ID = uuid.UUID("70000000-0000-4000-8000-000000000012")
ANN_4_ID = uuid.UUID("70000000-0000-4000-8000-000000000013")
ANN_5_ID = uuid.UUID("70000000-0000-4000-8000-000000000014")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


async def clear_all(session: AsyncSession) -> None:
    """Truncate all tables (CASCADE) to allow re-seeding."""
    conn = await session.connection()

    def _get_table_names(sync_conn) -> set[str]:
        return set(inspect(sync_conn).get_table_names())

    existing_tables = await conn.run_sync(_get_table_names)
    tables_in_order = [
        "difficulty_adaptations",
        "skill_progress",
        "skill_milestones",
        "skill_dimensions",
        "skill_passports",
        "feature_toggles",
        "game_configs",
        "reward_badges",
        "reward_events",
        "student_rewards",
        "compliance_reports",
        "curriculum_mappings",
        "men_objectives",
        "men_curricula",
        "schools",
        "audit_logs",
        "provider_webhook_events",
        "payment_proofs",
        "payment_attempts",
        "invoice_items",
        "invoices",
        "announcements",
        "message_read_receipts",
        "messages",
        "conversation_participants",
        "conversations",
        "parent_feed_items",
        "notification_deliveries",
        "notifications",
        "consent_preferences",
        "activity_sessions",
        "activities",
        "content_submissions",
        "class_content_assignments",
        "content_progress",
        "content_item_assets",
        "content_items",
        "student_period_averages",
        "grades",
        "grade_categories",
        "rubric_scores",
        "rubric_levels",
        "rubric_criteria",
        "rubrics",
        "submission_files",
        "submissions",
        "assessment_results",
        "assessments",
        "assignments",
        "courses",
        "justification_reviews",
        "absence_justifications",
        "attendance_records",
        "attendance_sessions",
        "teacher_assignments",
        "enrollments",
        "classes",
        "periods",
        "academic_years",
        "writing_attempts",
        "ai_preferences",
        "student_profiles",
        "parent_profiles",
        "teacher_profiles",
        "parent_child_links",
        "account_recovery_requests",
        "invitation_codes",
        "sessions",
        "memberships",
        "users",
    ]
    present_tables = [table for table in tables_in_order if table in existing_tables]
    if not present_tables:
        await session.commit()
        return

    await session.execute(text(f"TRUNCATE TABLE {', '.join(present_tables)} CASCADE"))
    await session.commit()


async def seed_schools(session: AsyncSession) -> None:
    """Seed tenant schools before any school-scoped rows."""
    schools = [
        School(
            id=SCHOOL_ID,
            name="Ecole Benani",
            name_ar="مدرسة بناني",
            code="ECOLE-BENANI",
            massar_code="MASSAR-BENANI",
            status="active",
            address="12 Rue des Orangers, Casablanca",
            city="Casablanca",
            region="Casablanca-Settat",
            phone="+212522000001",
            email="contact@ecole-benani.ma",
            website="https://ecole-benani.ma",
            max_students=1200,
            max_teachers=120,
            subscription_plan="premium",
            timezone="Africa/Casablanca",
            default_language="fr",
            grading_scale="moroccan_20",
            settings={
                "timezone": "Africa/Casablanca",
                "currency": "MAD",
                "supported_languages": ["fr", "ar"],
            },
        ),
        School(
            id=SCHOOL_ID_2,
            name="Ecole Atlas",
            name_ar="مدرسة الأطلس",
            code="ECOLE-ATLAS",
            massar_code="MASSAR-ATLAS",
            status="trial",
            address="45 Avenue Mohammed V, Rabat",
            city="Rabat",
            region="Rabat-Sale-Kenitra",
            phone="+212537000002",
            email="contact@ecole-atlas.ma",
            website="https://ecole-atlas.ma",
            max_students=600,
            max_teachers=60,
            subscription_plan="trial",
            timezone="Africa/Casablanca",
            default_language="fr",
            grading_scale="moroccan_20",
            settings={
                "timezone": "Africa/Casablanca",
                "currency": "MAD",
                "supported_languages": ["fr", "ar"],
            },
        ),
    ]
    session.add_all(schools)
    await session.flush()
    print("  [School]    2 schools")


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
        User(
            id=CONTENT_MGR_ID,
            email="cms@ecole-platform.ma",
            full_name="Nadia Cherkaoui",
            password_hash=_hash("content123"),
            status="active",
            school_id=SCHOOL_ID,
        ),
    ]
    session.add_all(users)
    await session.flush()

    memberships = [
        Membership(
            user_id=ADMIN_ID, school_id=SCHOOL_ID, role_code="ADM", status="active"
        ),
        Membership(
            user_id=DIRECTOR_ID, school_id=SCHOOL_ID, role_code="DIR", status="active"
        ),
        Membership(
            user_id=TEACHER_1_ID, school_id=SCHOOL_ID, role_code="TCH", status="active"
        ),
        Membership(
            user_id=TEACHER_2_ID, school_id=SCHOOL_ID, role_code="TCH", status="active"
        ),
        Membership(
            user_id=PARENT_1_ID, school_id=SCHOOL_ID, role_code="PAR", status="active"
        ),
        Membership(
            user_id=PARENT_2_ID, school_id=SCHOOL_ID, role_code="PAR", status="active"
        ),
        Membership(
            user_id=STUDENT_1_ID, school_id=SCHOOL_ID, role_code="STD", status="active"
        ),
        Membership(
            user_id=STUDENT_2_ID, school_id=SCHOOL_ID, role_code="STD", status="active"
        ),
        Membership(
            user_id=STUDENT_3_ID, school_id=SCHOOL_ID, role_code="STD", status="active"
        ),
        Membership(
            user_id=SUPERADMIN_ID, school_id=SCHOOL_ID, role_code="SUP", status="active"
        ),
        Membership(
            user_id=CONTENT_MGR_ID,
            school_id=SCHOOL_ID,
            role_code="CONTENT_MGR",
            status="active",
        ),
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
    print("  [IAM] 11 users, 11 memberships, 1 session")


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
        Enrollment(
            student_id=STUDENT_1_ID,
            class_id=CLASS_6A_ID,
            period_id=PERIOD_2_ID,
            school_id=SCHOOL_ID,
            status="active",
        ),
        Enrollment(
            student_id=STUDENT_2_ID,
            class_id=CLASS_6A_ID,
            period_id=PERIOD_2_ID,
            school_id=SCHOOL_ID,
            status="active",
        ),
        Enrollment(
            student_id=STUDENT_3_ID,
            class_id=CLASS_6B_ID,
            period_id=PERIOD_2_ID,
            school_id=SCHOOL_ID,
            status="active",
        ),
    ]
    session.add_all(enrollments)

    # Teacher assignments
    assignments = [
        TeacherAssignment(
            teacher_id=TEACHER_1_ID,
            class_id=CLASS_6A_ID,
            period_id=PERIOD_2_ID,
            school_id=SCHOOL_ID,
        ),
        TeacherAssignment(
            teacher_id=TEACHER_2_ID,
            class_id=CLASS_6A_ID,
            period_id=PERIOD_2_ID,
            school_id=SCHOOL_ID,
        ),
        TeacherAssignment(
            teacher_id=TEACHER_1_ID,
            class_id=CLASS_6B_ID,
            period_id=PERIOD_2_ID,
            school_id=SCHOOL_ID,
        ),
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
        AttendanceRecord(
            attendance_session_id=att_session.id,
            student_id=STUDENT_1_ID,
            school_id=SCHOOL_ID,
            status="present",
        ),
        AttendanceRecord(
            attendance_session_id=att_session.id,
            student_id=STUDENT_2_ID,
            school_id=SCHOOL_ID,
            status="absent",
            absence_reason="Maladie",
        ),
    ]
    session.add_all(att_records)
    await session.flush()
    print(
        "  [ERP] 1 year, 2 periods, 2 classes, 3 enrollments, 3 teacher assignments, 1 attendance session"
    )


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
        score=17.5,
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

    # Phase 9C — PRINTABLE_PDF assignment (exercise PDF path is placeholder, file not on disk)
    pdf_assign = Assignment(
        course_id=COURSE_MATH_ID,
        teacher_id=TEACHER_1_ID,
        title="Exercice imprimable - Equations",
        description="Imprimez le PDF, résolvez les exercices sur papier, puis scannez/photographiez votre copie.",
        due_at=_now() + timedelta(days=10),
        total_points=15,
        exercise_type="PRINTABLE_PDF",
        exercise_pdf_path="exercises/sample_equations.pdf",
    )
    session.add(pdf_assign)
    await session.flush()

    print(
        "  [LMS] 2 courses, 2 assignments (1 STANDARD + 1 PRINTABLE_PDF), 1 submission+grade, 1 assessment+result, 1 content+progress, 1 activity+session"
    )


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


async def seed_messaging(session: AsyncSession) -> None:
    """Seed messaging & announcements (Phase 11C).

    Creates:
    - 2 conversations (parent↔teacher direct, group with admin)
    - 4 messages across conversations
    - 1 read receipt
    - 2 announcements (1 published, 1 draft)
    """
    now = _now()

    # Conversation 1: Parent 1 ↔ Teacher 1 (direct — about student grades)
    conv1 = Conversation(
        id=CONV_1_ID,
        school_id=SCHOOL_ID,
        type="DIRECT",
        created_by=PARENT_1_ID,
        subject="Question sur les notes de Yassine",
    )
    session.add(conv1)
    await session.flush()

    session.add_all(
        [
            ConversationParticipant(
                conversation_id=CONV_1_ID,
                user_id=PARENT_1_ID,
                role_in_conversation="INITIATOR",
                joined_at=now,
                muted=False,
            ),
            ConversationParticipant(
                conversation_id=CONV_1_ID,
                user_id=TEACHER_1_ID,
                role_in_conversation="PARTICIPANT",
                joined_at=now,
                muted=False,
            ),
        ]
    )
    await session.flush()

    msg1 = Message(
        conversation_id=CONV_1_ID,
        sender_id=PARENT_1_ID,
        body="Bonjour M. Kettani, je souhaite discuter des résultats de Yassine en mathématiques.",
        sent_at=now,
    )
    msg2 = Message(
        conversation_id=CONV_1_ID,
        sender_id=TEACHER_1_ID,
        body="Bonjour M. Alaoui, Yassine fait de bons progrès. Son dernier contrôle était excellent (17.5/20).",
        sent_at=now + timedelta(minutes=15),
    )
    session.add_all([msg1, msg2])
    await session.flush()

    # Read receipt: Parent 1 read teacher's reply
    receipt = MessageReadReceipt(
        message_id=msg2.id,
        user_id=PARENT_1_ID,
        read_at=now + timedelta(minutes=30),
    )
    session.add(receipt)

    # Conversation 2: Group conversation — Admin + Teacher 1 + Teacher 2
    conv2 = Conversation(
        id=CONV_2_ID,
        school_id=SCHOOL_ID,
        type="GROUP",
        created_by=ADMIN_ID,
        subject="Réunion pédagogique — préparation examens",
    )
    session.add(conv2)
    await session.flush()

    session.add_all(
        [
            ConversationParticipant(
                conversation_id=CONV_2_ID,
                user_id=ADMIN_ID,
                role_in_conversation="INITIATOR",
                joined_at=now,
                muted=False,
            ),
            ConversationParticipant(
                conversation_id=CONV_2_ID,
                user_id=TEACHER_1_ID,
                role_in_conversation="PARTICIPANT",
                joined_at=now,
                muted=False,
            ),
            ConversationParticipant(
                conversation_id=CONV_2_ID,
                user_id=TEACHER_2_ID,
                role_in_conversation="PARTICIPANT",
                joined_at=now,
                muted=False,
            ),
        ]
    )
    await session.flush()

    msg3 = Message(
        conversation_id=CONV_2_ID,
        sender_id=ADMIN_ID,
        body="Bonjour à tous, merci de préparer les sujets d'examens pour le 15 avril.",
        sent_at=now,
    )
    msg4 = Message(
        conversation_id=CONV_2_ID,
        sender_id=TEACHER_1_ID,
        body="Bien reçu, je prépare le sujet de mathématiques pour la semaine prochaine.",
        sent_at=now + timedelta(minutes=10),
    )
    session.add_all([msg3, msg4])
    await session.flush()

    # Announcement 1: Published — school event
    ann1 = Announcement(
        id=ANN_1_ID,
        school_id=SCHOOL_ID,
        author_id=ADMIN_ID,
        title="Journée portes ouvertes — 25 mars 2026",
        body="Chers parents et élèves, nous vous invitons à la journée portes ouvertes de l'école le 25 mars 2026 de 9h à 16h. Des ateliers, expositions et démonstrations seront organisés.",
        target_roles=["PAR", "STD"],
        target_class_ids=None,
        published_at=now,
        status="PUBLISHED",
    )
    session.add(ann1)

    # Announcement 2: Draft — exam schedule
    ann2 = Announcement(
        id=ANN_2_ID,
        school_id=SCHOOL_ID,
        author_id=DIRECTOR_ID,
        title="Calendrier des examens du 2ème semestre",
        body="Le calendrier des examens du deuxième semestre sera communiqué prochainement. Les examens débuteront le 15 avril 2026.",
        target_roles=["PAR", "STD", "TCH"],
        target_class_ids=None,
        status="DRAFT",
    )
    session.add(ann2)
    await session.flush()

    print(
        "  [Messaging] 2 conversations (4 messages, 1 read receipt), 2 announcements (1 published, 1 draft)"
    )


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
            tva_rate=0.00,
            tva_amount=0.00,
            amount_ht=3000.00,
            amount_ttc=3000.00,
        ),
        InvoiceItem(
            invoice_id=INVOICE_1_ID,
            description="Frais de transport",
            amount=500.00,
            unit_price=500.00,
            quantity=1,
            tva_rate=0.00,
            tva_amount=0.00,
            amount_ht=500.00,
            amount_ttc=500.00,
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


async def seed_profiles(session: AsyncSession) -> None:
    """Seed role-specific profiles for all test users (Phase 1B)."""
    student_profiles = [
        StudentProfile(
            user_id=STUDENT_1_ID,
            school_id=SCHOOL_ID,
            student_number="STD-2025-001",
            date_of_birth=date(2013, 5, 15),
            gender="male",
            class_level="6eme",
            nationality="Marocaine",
        ),
        StudentProfile(
            user_id=STUDENT_2_ID,
            school_id=SCHOOL_ID,
            student_number="STD-2025-002",
            date_of_birth=date(2013, 8, 22),
            gender="female",
            class_level="6eme",
            nationality="Marocaine",
        ),
        StudentProfile(
            user_id=STUDENT_3_ID,
            school_id=SCHOOL_ID,
            student_number="STD-2025-003",
            date_of_birth=date(2013, 11, 3),
            gender="male",
            class_level="6eme",
            nationality="Marocaine",
        ),
    ]
    session.add_all(student_profiles)

    parent_profiles = [
        ParentProfile(
            user_id=PARENT_1_ID,
            school_id=SCHOOL_ID,
            relationship_type="father",
            cin_number="AB123456",
            address="12 Rue des Orangers, Casablanca",
            profession="Ingenieur",
            emergency_phone="+212612345678",
        ),
        ParentProfile(
            user_id=PARENT_2_ID,
            school_id=SCHOOL_ID,
            relationship_type="mother",
            cin_number="CD789012",
            address="45 Avenue Mohammed V, Casablanca",
            profession="Medecin",
            emergency_phone="+212698765432",
        ),
    ]
    session.add_all(parent_profiles)

    teacher_profiles = [
        TeacherProfile(
            user_id=TEACHER_1_ID,
            school_id=SCHOOL_ID,
            employee_id="TCH-2020-001",
            subject_specialty="Mathematiques",
            qualification="Licence en Mathematiques",
            hire_date=date(2020, 9, 1),
        ),
        TeacherProfile(
            user_id=TEACHER_2_ID,
            school_id=SCHOOL_ID,
            employee_id="TCH-2021-002",
            subject_specialty="Francais",
            qualification="Master en Lettres Francaises",
            hire_date=date(2021, 9, 1),
        ),
    ]
    session.add_all(teacher_profiles)
    await session.flush()
    print("  [IAM] 3 student profiles, 2 parent profiles, 2 teacher profiles")


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


async def seed_cms(session: AsyncSession) -> None:
    """Seed CMS domain: platform-wide content, class assignment, teacher submission (Phase 9A)."""
    # Platform-wide content (school_id=NULL) — 2 videos, 2 PDFs, 2 audios
    platform_content = [
        ContentItem(
            id=PLATFORM_CONTENT_1_ID,
            school_id=None,
            title="Les fractions - Cours complet",
            content_type="video",
            level_band="6eme",
            language="fr",
            subject="math",
            description="Cours complet sur les fractions pour le niveau 6eme. Couvre les operations de base et les simplifications.",
            status="published",
            origin="PLATFORM",
            created_by=CONTENT_MGR_ID,
        ),
        ContentItem(
            id=PLATFORM_CONTENT_2_ID,
            school_id=None,
            title="La conjugaison au present",
            content_type="video",
            level_band="6eme",
            language="fr",
            subject="french",
            description="Video pedagogique sur la conjugaison des verbes du premier, deuxieme et troisieme groupe au present de l'indicatif.",
            status="published",
            origin="PLATFORM",
            created_by=CONTENT_MGR_ID,
        ),
        ContentItem(
            id=PLATFORM_CONTENT_3_ID,
            school_id=None,
            title="Exercices de geometrie - Triangles",
            content_type="pdf",
            level_band="6eme",
            language="fr",
            subject="math",
            description="Fiche d'exercices sur les triangles: classification, proprietes, construction.",
            status="published",
            origin="PLATFORM",
            created_by=CONTENT_MGR_ID,
        ),
        ContentItem(
            id=PLATFORM_CONTENT_4_ID,
            school_id=None,
            title="Lecture - Le Petit Prince (extraits)",
            content_type="pdf",
            level_band="6eme",
            language="fr",
            subject="french",
            description="Extraits selectionnes du Petit Prince avec questions de comprehension.",
            status="published",
            origin="PLATFORM",
            created_by=CONTENT_MGR_ID,
        ),
        ContentItem(
            id=PLATFORM_CONTENT_5_ID,
            school_id=None,
            title="Comptines arabes - L'alphabet",
            content_type="audio",
            level_band="primaire",
            language="ar",
            subject="arabic",
            description="Comptines pour apprendre l'alphabet arabe de maniere ludique.",
            status="published",
            origin="PLATFORM",
            created_by=CONTENT_MGR_ID,
        ),
        ContentItem(
            id=PLATFORM_CONTENT_6_ID,
            school_id=None,
            title="Ecoute - Les saisons",
            content_type="audio",
            level_band="6eme",
            language="fr",
            subject="science",
            description="Document audio sur les saisons, les equinoxes et les solstices.",
            status="published",
            origin="PLATFORM",
            created_by=CONTENT_MGR_ID,
        ),
    ]
    session.add_all(platform_content)
    await session.flush()

    # Teacher's school-scoped content (used for submission)
    teacher_content = ContentItem(
        school_id=SCHOOL_ID,
        title="Exercices supplementaires - Fractions",
        content_type="pdf",
        level_band="6eme",
        language="fr",
        subject="math",
        description="Exercices supplementaires crees par le prof. Kettani pour les 6eme A.",
        status="published",
        origin="PLATFORM",
        created_by=TEACHER_1_ID,
    )
    session.add(teacher_content)
    await session.flush()

    # Teacher submits content for platform promotion
    conn = await session.connection()

    def _has_content_submissions(sync_conn) -> bool:
        return "content_submissions" in inspect(sync_conn).get_table_names()

    has_content_submissions = await conn.run_sync(_has_content_submissions)
    if has_content_submissions:
        submission = ContentSubmission(
            content_item_id=teacher_content.id,
            submitted_by=TEACHER_1_ID,
            school_id=SCHOOL_ID,
            status="PENDING",
            submitted_at=_now(),
        )
        session.add(submission)

    # Assign platform content to class 6A
    assignment = ClassContentAssignment(
        teacher_id=TEACHER_1_ID,
        class_id=CLASS_6A_ID,
        content_item_id=PLATFORM_CONTENT_1_ID,
        school_id=SCHOOL_ID,
        assigned_at=_now(),
        notes="A regarder avant le controle de vendredi",
    )
    session.add(assignment)
    await session.flush()

    cms_summary = "  [CMS] 6 platform content, 1 teacher content"
    if has_content_submissions:
        cms_summary += ", 1 submission"
    else:
        cms_summary += ", content submissions skipped (table not migrated)"
    cms_summary += ", 1 class assignment"
    print(cms_summary)


async def seed_quizzes(session: AsyncSession) -> None:
    """Seed sample quizzes with questions — Phase 9B."""

    # ── Quiz 1: Math fractions (platform-wide, by CONTENT_MGR) ──
    quiz_math = Quiz(
        id=QUIZ_MATH_ID,
        school_id=None,  # platform-wide
        created_by=CONTENT_MGR_ID,
        title="Quiz - Les fractions (6ème)",
        description="Quiz de révision sur les fractions pour le niveau 6ème.",
        subject="math",
        level_band="6eme",
        difficulty="MEDIUM",
        time_limit_minutes=15,
        max_attempts=3,
        shuffle_questions=True,
        status="published",
    )
    session.add(quiz_math)

    math_questions = [
        QuizQuestion(
            quiz_id=QUIZ_MATH_ID,
            question_type="MCQ",
            question_text="Quelle fraction est équivalente à 2/4 ?",
            options=[
                {"id": "a", "text": "1/2"},
                {"id": "b", "text": "3/4"},
                {"id": "c", "text": "2/3"},
                {"id": "d", "text": "1/4"},
            ],
            correct_answer=["a"],
            points=2,
            order=0,
            explanation="2/4 simplifié = 1/2 (on divise numérateur et dénominateur par 2).",
        ),
        QuizQuestion(
            quiz_id=QUIZ_MATH_ID,
            question_type="TRUE_FALSE",
            question_text="3/5 est supérieur à 1/2.",
            correct_answer=True,
            points=1,
            order=1,
            explanation="3/5 = 0.6 et 1/2 = 0.5, donc 3/5 > 1/2.",
        ),
        QuizQuestion(
            quiz_id=QUIZ_MATH_ID,
            question_type="FILL_IN",
            question_text="Combien font 1/4 + 1/4 ? (écrire sous forme de fraction simplifiée)",
            correct_answer=["1/2", "2/4"],
            points=2,
            order=2,
            explanation="1/4 + 1/4 = 2/4 = 1/2.",
        ),
        QuizQuestion(
            quiz_id=QUIZ_MATH_ID,
            question_type="MATCHING",
            question_text="Associez chaque fraction à sa valeur décimale.",
            options={
                "left": [
                    {"id": "l1", "text": "1/2"},
                    {"id": "l2", "text": "1/4"},
                    {"id": "l3", "text": "3/4"},
                ],
                "right": [
                    {"id": "r1", "text": "0.25"},
                    {"id": "r2", "text": "0.5"},
                    {"id": "r3", "text": "0.75"},
                ],
            },
            correct_answer={"l1": "r2", "l2": "r1", "l3": "r3"},
            points=3,
            order=3,
            explanation="1/2=0.5, 1/4=0.25, 3/4=0.75.",
        ),
    ]
    for q in math_questions:
        session.add(q)

    # ── Quiz 2: French grammar (school-scoped, by teacher) ──
    quiz_fr = Quiz(
        id=QUIZ_FR_ID,
        school_id=SCHOOL_ID,
        created_by=TEACHER_1_ID,
        title="Quiz - Les accords du participe passé",
        description="Vérifiez vos connaissances sur les accords du participe passé.",
        subject="french",
        level_band="6eme",
        difficulty="EASY",
        time_limit_minutes=10,
        max_attempts=2,
        shuffle_questions=False,
        status="published",
    )
    session.add(quiz_fr)

    fr_questions = [
        QuizQuestion(
            quiz_id=QUIZ_FR_ID,
            question_type="MCQ",
            question_text="Dans la phrase « Les fleurs que j'ai ___ sont belles », quel est le bon accord ?",
            options=[
                {"id": "a", "text": "cueilli"},
                {"id": "b", "text": "cueillis"},
                {"id": "c", "text": "cueillies"},
                {"id": "d", "text": "cueillie"},
            ],
            correct_answer=["c"],
            points=2,
            order=0,
            explanation="Le COD 'les fleurs' (féminin pluriel) est placé avant l'auxiliaire avoir → accord.",
        ),
        QuizQuestion(
            quiz_id=QUIZ_FR_ID,
            question_type="TRUE_FALSE",
            question_text="Avec l'auxiliaire être, le participe passé s'accorde toujours avec le sujet.",
            correct_answer=True,
            points=1,
            order=1,
            explanation="Avec être, le participe passé s'accorde en genre et en nombre avec le sujet.",
        ),
        QuizQuestion(
            quiz_id=QUIZ_FR_ID,
            question_type="FILL_IN",
            question_text="Complétez : « Elle est ___ tôt ce matin. » (partir)",
            correct_answer=["partie"],
            points=2,
            order=2,
            explanation="Auxiliaire être + sujet féminin singulier → partie.",
        ),
    ]
    for q in fr_questions:
        session.add(q)

    await session.flush()
    print("  [Quiz] 2 quizzes (7 questions total), both published")


async def seed_timetable(session: AsyncSession) -> None:
    """Seed timetable domain: slots + exceptions (Phase 11A).

    Creates a realistic Moroccan school schedule:
    - Class 6A: Math (Mon 08:00-09:00, Wed 10:00-11:00), French (Mon 10:00-11:00, Thu 08:00-09:00)
    - Class 6B: Math (Tue 08:00-09:00), French (Tue 10:00-11:00)
    Plus one exception: Math 6A on Wed is CANCELED for a school event.
    """
    from datetime import time

    slots = [
        # Class 6A — Math Monday 08:00-09:00
        TimetableSlot(
            id=SLOT_MATH_6A_MON_ID,
            school_id=SCHOOL_ID,
            class_id=CLASS_6A_ID,
            academic_year_id=YEAR_ID,
            day_of_week=0,  # Monday
            start_time=time(8, 0),
            end_time=time(9, 0),
            subject="Mathématiques",
            teacher_id=TEACHER_1_ID,
            room="Salle 101",
            is_recurring=True,
        ),
        # Class 6A — French Monday 10:00-11:00
        TimetableSlot(
            id=SLOT_FR_6A_MON_ID,
            school_id=SCHOOL_ID,
            class_id=CLASS_6A_ID,
            academic_year_id=YEAR_ID,
            day_of_week=0,  # Monday
            start_time=time(10, 0),
            end_time=time(11, 0),
            subject="Français",
            teacher_id=TEACHER_2_ID,
            room="Salle 102",
            is_recurring=True,
        ),
        # Class 6A — Math Wednesday 10:00-11:00
        TimetableSlot(
            id=SLOT_MATH_6A_WED_ID,
            school_id=SCHOOL_ID,
            class_id=CLASS_6A_ID,
            academic_year_id=YEAR_ID,
            day_of_week=2,  # Wednesday
            start_time=time(10, 0),
            end_time=time(11, 0),
            subject="Mathématiques",
            teacher_id=TEACHER_1_ID,
            room="Salle 101",
            is_recurring=True,
        ),
        # Class 6A — French Thursday 08:00-09:00
        TimetableSlot(
            id=SLOT_FR_6A_THU_ID,
            school_id=SCHOOL_ID,
            class_id=CLASS_6A_ID,
            academic_year_id=YEAR_ID,
            day_of_week=3,  # Thursday
            start_time=time(8, 0),
            end_time=time(9, 0),
            subject="Français",
            teacher_id=TEACHER_2_ID,
            room="Salle 102",
            is_recurring=True,
        ),
        # Class 6B — Math Tuesday 08:00-09:00
        TimetableSlot(
            id=SLOT_MATH_6B_TUE_ID,
            school_id=SCHOOL_ID,
            class_id=CLASS_6B_ID,
            academic_year_id=YEAR_ID,
            day_of_week=1,  # Tuesday
            start_time=time(8, 0),
            end_time=time(9, 0),
            subject="Mathématiques",
            teacher_id=TEACHER_1_ID,
            room="Salle 201",
            is_recurring=True,
        ),
        # Class 6B — French Tuesday 10:00-11:00
        TimetableSlot(
            id=SLOT_FR_6B_TUE_ID,
            school_id=SCHOOL_ID,
            class_id=CLASS_6B_ID,
            academic_year_id=YEAR_ID,
            day_of_week=1,  # Tuesday
            start_time=time(10, 0),
            end_time=time(11, 0),
            subject="Français",
            teacher_id=TEACHER_2_ID,
            room="Salle 202",
            is_recurring=True,
        ),
    ]
    session.add_all(slots)
    await session.flush()

    # One exception: Math 6A Wednesday canceled for school event
    exception = TimetableException(
        timetable_slot_id=SLOT_MATH_6A_WED_ID,
        school_id=SCHOOL_ID,
        exception_date=date(2026, 3, 25),
        exception_type="CANCELED",
        reason="Journée portes ouvertes",
    )
    session.add(exception)
    await session.flush()
    print("  [Timetable] 6 slots (2 classes), 1 exception (canceled)")


async def seed_fees(session: AsyncSession) -> None:
    """Seed fee structures and assignments (Phase 11B).

    Creates realistic Moroccan school fees:
    - Scolarité: annual tuition 15,000 MAD
    - Transport: monthly transport 500 MAD
    - Cantine: trimestrial cafeteria 1,200 MAD
    Assigns scolarité to all 3 students, transport to student 1+2 with 20% sibling discount for student 2.
    """
    fee_scolarite = FeeStructure(
        id=FEE_SCOLARITE_ID,
        school_id=SCHOOL_ID,
        academic_year_id=YEAR_ID,
        name="Frais de scolarité — 6ème année",
        amount=15000.00,
        currency="MAD",
        frequency="ANNUAL",
        due_day=1,
        applies_to_level="6",
        status="ACTIVE",
    )
    fee_transport = FeeStructure(
        id=FEE_TRANSPORT_ID,
        school_id=SCHOOL_ID,
        academic_year_id=YEAR_ID,
        name="Frais de transport scolaire",
        amount=500.00,
        currency="MAD",
        frequency="MONTHLY",
        due_day=5,
        applies_to_level=None,
        status="ACTIVE",
    )
    fee_cantine = FeeStructure(
        id=FEE_CANTINE_ID,
        school_id=SCHOOL_ID,
        academic_year_id=YEAR_ID,
        name="Frais de cantine",
        amount=1200.00,
        currency="MAD",
        frequency="TRIMESTRIAL",
        due_day=10,
        applies_to_level=None,
        status="ACTIVE",
    )
    session.add_all([fee_scolarite, fee_transport, fee_cantine])
    await session.flush()

    # Assignments
    assignments = [
        # All 3 students get tuition
        FeeAssignment(
            fee_structure_id=FEE_SCOLARITE_ID,
            student_id=STUDENT_1_ID,
            school_id=SCHOOL_ID,
            status="ACTIVE",
        ),
        FeeAssignment(
            fee_structure_id=FEE_SCOLARITE_ID,
            student_id=STUDENT_2_ID,
            school_id=SCHOOL_ID,
            status="ACTIVE",
        ),
        FeeAssignment(
            fee_structure_id=FEE_SCOLARITE_ID,
            student_id=STUDENT_3_ID,
            school_id=SCHOOL_ID,
            status="ACTIVE",
        ),
        # Students 1+2 get transport
        FeeAssignment(
            fee_structure_id=FEE_TRANSPORT_ID,
            student_id=STUDENT_1_ID,
            school_id=SCHOOL_ID,
            status="ACTIVE",
        ),
        FeeAssignment(
            fee_structure_id=FEE_TRANSPORT_ID,
            student_id=STUDENT_2_ID,
            school_id=SCHOOL_ID,
            discount_percent=20.0,
            discount_reason="Remise fratrie — 2ème enfant",
            status="ACTIVE",
        ),
        # Student 3 exempted from cantine
        FeeAssignment(
            fee_structure_id=FEE_CANTINE_ID,
            student_id=STUDENT_3_ID,
            school_id=SCHOOL_ID,
            status="EXEMPTED",
        ),
    ]
    session.add_all(assignments)
    await session.flush()
    print("  [Fees] 3 fee structures, 6 assignments (1 with discount, 1 exempted)")


async def seed_feature_toggles(session: AsyncSession) -> None:
    """Seed feature toggles — 6 default features (Phase 11E)."""
    toggles = [
        FeatureToggle(
            feature_key="content_library",
            display_name="Content Library",
            description="Platform-wide content library (CMS) for reusable learning resources",
            enabled_globally=False,
            enabled_school_ids=[str(SCHOOL_ID)],
            enabled_role_codes=["ADM", "TCH", "CONTENT_MGR"],
        ),
        FeatureToggle(
            feature_key="quiz_engine",
            display_name="Quiz Engine",
            description="Interactive quiz creation and attempt engine",
            enabled_globally=False,
            enabled_school_ids=[str(SCHOOL_ID)],
            enabled_role_codes=["ADM", "TCH", "STD", "CONTENT_MGR"],
        ),
        FeatureToggle(
            feature_key="pdf_exercises",
            display_name="PDF Exercises",
            description="PDF exercise generation and submission workflow",
            enabled_globally=False,
            enabled_school_ids=[],
            enabled_role_codes=["ADM", "TCH"],
        ),
        FeatureToggle(
            feature_key="messaging",
            display_name="Messaging",
            description="Parent-teacher direct and group messaging",
            enabled_globally=True,
            enabled_school_ids=[],
            enabled_role_codes=[],
        ),
        FeatureToggle(
            feature_key="announcements",
            display_name="Announcements",
            description="School-wide announcement publish and targeting",
            enabled_globally=True,
            enabled_school_ids=[],
            enabled_role_codes=[],
        ),
        FeatureToggle(
            feature_key="timetable",
            display_name="Timetable",
            description="Weekly timetable management with exceptions",
            enabled_globally=False,
            enabled_school_ids=[str(SCHOOL_ID)],
            enabled_role_codes=[],
        ),
    ]
    session.add_all(toggles)
    await session.flush()
    print("  [Features] 6 feature toggles (messaging + announcements globally enabled)")


async def seed_reward_badges(session: AsyncSession) -> None:
    """Seed default reward badge definitions for the rewards UI."""
    badges = [
        RewardBadge(
            id=uuid.uuid5(uuid.NAMESPACE_URL, "reward-badge-first-login"),
            code="first_login",
            title_en="First Login",
            title_fr="Première connexion",
            title_ar="أول تسجيل دخول",
            description_en="Awarded after the first successful login.",
            description_fr="Attribué après la première connexion réussie.",
            description_ar="يُمنح بعد أول تسجيل دخول ناجح.",
            icon="🎉",
            criteria_type="login_count",
            criteria_value=1,
            display_order=1,
            is_active=True,
        ),
        RewardBadge(
            id=uuid.uuid5(uuid.NAMESPACE_URL, "reward-badge-streak-7"),
            code="streak_7",
            title_en="Seven-Day Streak",
            title_fr="Série de sept jours",
            title_ar="سلسلة سبعة أيام",
            description_en="Awarded for seven consecutive days of activity.",
            description_fr="Attribué après sept jours d'activité consécutifs.",
            description_ar="يُمنح بعد سبعة أيام متتالية من النشاط.",
            icon="🔥",
            criteria_type="streak_days",
            criteria_value=7,
            display_order=2,
            is_active=True,
        ),
        RewardBadge(
            id=uuid.uuid5(uuid.NAMESPACE_URL, "reward-badge-xp-250"),
            code="xp_250",
            title_en="250 XP Club",
            title_fr="Club des 250 XP",
            title_ar="نادي 250 نقطة خبرة",
            description_en="Awarded after earning 250 XP.",
            description_fr="Attribué après avoir obtenu 250 XP.",
            description_ar="يُمنح بعد الحصول على 250 نقطة خبرة.",
            icon="⭐",
            criteria_type="xp_total",
            criteria_value=250,
            display_order=3,
            is_active=True,
        ),
    ]
    session.add_all(badges)
    await session.flush()
    print(f"  [Rewards] {len(badges)} reward badges")


async def seed_game_configs(session: AsyncSession) -> None:
    """Seed sample mobile game configs."""
    configs = [
        GameConfig(
            id=uuid.uuid5(uuid.NAMESPACE_URL, "game-config-memory-match-letters-easy"),
            game_type="memory_match",
            title="Arabic Letters Match - Easy",
            title_ar="مطابقة الحروف العربية - سهل",
            title_fr="Association des lettres arabes - facile",
            subject="arabic_letters",
            difficulty="easy",
            target_age_min=4,
            target_age_max=5,
            config={
                "pairs": [
                    {
                        "front": "أ",
                        "back": "أرنب",
                        "image_url": "https://cdn.ecole-platform.test/games/letters/alif-rabbit.png",
                    },
                    {
                        "front": "ب",
                        "back": "بطة",
                        "image_url": "https://cdn.ecole-platform.test/games/letters/ba-duck.png",
                    },
                    {
                        "front": "ت",
                        "back": "تفاح",
                        "image_url": "https://cdn.ecole-platform.test/games/letters/ta-apple.png",
                    },
                    {
                        "front": "ث",
                        "back": "ثعلب",
                        "image_url": "https://cdn.ecole-platform.test/games/letters/tha-fox.png",
                    },
                    {
                        "front": "ج",
                        "back": "جمل",
                        "image_url": "https://cdn.ecole-platform.test/games/letters/jeem-camel.png",
                    },
                    {
                        "front": "ح",
                        "back": "حصان",
                        "image_url": "https://cdn.ecole-platform.test/games/letters/ha-horse.png",
                    },
                ],
                "grid_cols": 3,
                "grid_rows": 4,
                "time_limit_seconds": 120,
            },
            reward_stars=10,
            reward_xp=15,
            school_id=None,
            is_active=True,
        ),
        GameConfig(
            id=uuid.uuid5(
                uuid.NAMESPACE_URL, "game-config-memory-match-letters-medium"
            ),
            game_type="memory_match",
            title="Arabic Letters Match - Medium",
            title_ar="مطابقة الحروف العربية - متوسط",
            title_fr="Association des lettres arabes - moyen",
            subject="arabic_letters",
            difficulty="medium",
            target_age_min=5,
            target_age_max=6,
            config={
                "pairs": [
                    {
                        "front": "خ",
                        "back": "خبز",
                        "image_url": "https://cdn.ecole-platform.test/games/letters/kha-bread.png",
                    },
                    {
                        "front": "د",
                        "back": "دجاجة",
                        "image_url": "https://cdn.ecole-platform.test/games/letters/dal-hen.png",
                    },
                    {
                        "front": "ذ",
                        "back": "ذرة",
                        "image_url": "https://cdn.ecole-platform.test/games/letters/dhal-corn.png",
                    },
                    {
                        "front": "ر",
                        "back": "رمان",
                        "image_url": "https://cdn.ecole-platform.test/games/letters/ra-pomegranate.png",
                    },
                    {
                        "front": "ز",
                        "back": "زهرة",
                        "image_url": "https://cdn.ecole-platform.test/games/letters/zay-flower.png",
                    },
                    {
                        "front": "س",
                        "back": "سمكة",
                        "image_url": "https://cdn.ecole-platform.test/games/letters/seen-fish.png",
                    },
                    {
                        "front": "ش",
                        "back": "شمس",
                        "image_url": "https://cdn.ecole-platform.test/games/letters/sheen-sun.png",
                    },
                    {
                        "front": "ص",
                        "back": "صقر",
                        "image_url": "https://cdn.ecole-platform.test/games/letters/sad-falcon.png",
                    },
                ],
                "grid_cols": 4,
                "grid_rows": 4,
                "time_limit_seconds": 135,
            },
            reward_stars=14,
            reward_xp=20,
            school_id=None,
            is_active=True,
        ),
        GameConfig(
            id=uuid.uuid5(uuid.NAMESPACE_URL, "game-config-memory-match-letters-hard"),
            game_type="memory_match",
            title="Arabic Letters Match - Hard",
            title_ar="مطابقة الحروف العربية - صعب",
            title_fr="Association des lettres arabes - difficile",
            subject="arabic_letters",
            difficulty="hard",
            target_age_min=6,
            target_age_max=7,
            config={
                "pairs": [
                    {
                        "front": "ض",
                        "back": "ضفدع",
                        "image_url": "https://cdn.ecole-platform.test/games/letters/dad-frog.png",
                    },
                    {
                        "front": "ط",
                        "back": "طائرة",
                        "image_url": "https://cdn.ecole-platform.test/games/letters/ta-plane.png",
                    },
                    {
                        "front": "ظ",
                        "back": "ظرف",
                        "image_url": "https://cdn.ecole-platform.test/games/letters/dha-envelope.png",
                    },
                    {
                        "front": "ع",
                        "back": "عصفور",
                        "image_url": "https://cdn.ecole-platform.test/games/letters/ain-bird.png",
                    },
                    {
                        "front": "غ",
                        "back": "غزال",
                        "image_url": "https://cdn.ecole-platform.test/games/letters/ghain-gazelle.png",
                    },
                    {
                        "front": "ف",
                        "back": "فيل",
                        "image_url": "https://cdn.ecole-platform.test/games/letters/fa-elephant.png",
                    },
                    {
                        "front": "ق",
                        "back": "قمر",
                        "image_url": "https://cdn.ecole-platform.test/games/letters/qaf-moon.png",
                    },
                    {
                        "front": "ك",
                        "back": "كتاب",
                        "image_url": "https://cdn.ecole-platform.test/games/letters/kaf-book.png",
                    },
                    {
                        "front": "ل",
                        "back": "ليمون",
                        "image_url": "https://cdn.ecole-platform.test/games/letters/lam-lemon.png",
                    },
                    {
                        "front": "م",
                        "back": "موز",
                        "image_url": "https://cdn.ecole-platform.test/games/letters/meem-banana.png",
                    },
                ],
                "grid_cols": 4,
                "grid_rows": 5,
                "time_limit_seconds": 150,
            },
            reward_stars=18,
            reward_xp=28,
            school_id=None,
            is_active=True,
        ),
        GameConfig(
            id=uuid.uuid5(uuid.NAMESPACE_URL, "game-config-sorting-letter-types"),
            game_type="sorting",
            title="Sort Letters by Type",
            title_ar="فرز الحروف حسب النوع",
            title_fr="Classer les lettres par type",
            subject="arabic_letters",
            difficulty="easy",
            target_age_min=5,
            target_age_max=7,
            config={
                "categories": [
                    {
                        "name": "حروف شمسية",
                        "items": ["ت", "ث", "د", "ذ", "ر", "ز", "س", "ش"],
                    },
                    {
                        "name": "حروف قمرية",
                        "items": ["أ", "ب", "ج", "ح", "خ", "ع", "غ", "ف"],
                    },
                ]
            },
            reward_stars=12,
            reward_xp=18,
            school_id=None,
            is_active=True,
        ),
        GameConfig(
            id=uuid.uuid5(uuid.NAMESPACE_URL, "game-config-sorting-word-categories"),
            game_type="sorting",
            title="Sort Words by Category",
            title_ar="فرز الكلمات حسب الفئة",
            title_fr="Classer les mots par catégorie",
            subject="vocabulary",
            difficulty="medium",
            target_age_min=5,
            target_age_max=7,
            config={
                "categories": [
                    {"name": "حيوانات", "items": ["أرنب", "أسد", "فيل", "قطة"]},
                    {"name": "فواكه", "items": ["تفاح", "موز", "عنب", "برتقال"]},
                    {"name": "ألوان", "items": ["أحمر", "أزرق", "أصفر", "أخضر"]},
                ]
            },
            reward_stars=15,
            reward_xp=22,
            school_id=None,
            is_active=True,
        ),
        GameConfig(
            id=uuid.uuid5(uuid.NAMESPACE_URL, "game-config-vocabulary-animals"),
            game_type="vocabulary_cards",
            title="Animal Vocabulary Cards",
            title_ar="بطاقات مفردات الحيوانات",
            title_fr="Cartes de vocabulaire - animaux",
            subject="vocabulary",
            difficulty="easy",
            target_age_min=4,
            target_age_max=6,
            config={
                "cards": [
                    {
                        "word_ar": "أرنب",
                        "word_fr": "Lapin",
                        "image_url": "https://cdn.ecole-platform.test/games/vocabulary/rabbit.png",
                        "audio_url": "https://cdn.ecole-platform.test/games/vocabulary/rabbit.mp3",
                    },
                    {
                        "word_ar": "أسد",
                        "word_fr": "Lion",
                        "image_url": "https://cdn.ecole-platform.test/games/vocabulary/lion.png",
                        "audio_url": "https://cdn.ecole-platform.test/games/vocabulary/lion.mp3",
                    },
                    {
                        "word_ar": "فيل",
                        "word_fr": "Elephant",
                        "image_url": "https://cdn.ecole-platform.test/games/vocabulary/elephant.png",
                        "audio_url": "https://cdn.ecole-platform.test/games/vocabulary/elephant.mp3",
                    },
                    {
                        "word_ar": "قطة",
                        "word_fr": "Chat",
                        "image_url": "https://cdn.ecole-platform.test/games/vocabulary/cat.png",
                        "audio_url": "https://cdn.ecole-platform.test/games/vocabulary/cat.mp3",
                    },
                ]
            },
            reward_stars=10,
            reward_xp=15,
            school_id=None,
            is_active=True,
        ),
        GameConfig(
            id=uuid.uuid5(uuid.NAMESPACE_URL, "game-config-vocabulary-colors"),
            game_type="vocabulary_cards",
            title="Color Vocabulary Cards",
            title_ar="بطاقات مفردات الألوان",
            title_fr="Cartes de vocabulaire - couleurs",
            subject="vocabulary",
            difficulty="easy",
            target_age_min=4,
            target_age_max=6,
            config={
                "cards": [
                    {
                        "word_ar": "أحمر",
                        "word_fr": "Rouge",
                        "image_url": "https://cdn.ecole-platform.test/games/vocabulary/red.png",
                        "audio_url": "https://cdn.ecole-platform.test/games/vocabulary/red.mp3",
                    },
                    {
                        "word_ar": "أزرق",
                        "word_fr": "Bleu",
                        "image_url": "https://cdn.ecole-platform.test/games/vocabulary/blue.png",
                        "audio_url": "https://cdn.ecole-platform.test/games/vocabulary/blue.mp3",
                    },
                    {
                        "word_ar": "أصفر",
                        "word_fr": "Jaune",
                        "image_url": "https://cdn.ecole-platform.test/games/vocabulary/yellow.png",
                        "audio_url": "https://cdn.ecole-platform.test/games/vocabulary/yellow.mp3",
                    },
                    {
                        "word_ar": "أخضر",
                        "word_fr": "Vert",
                        "image_url": "https://cdn.ecole-platform.test/games/vocabulary/green.png",
                        "audio_url": "https://cdn.ecole-platform.test/games/vocabulary/green.mp3",
                    },
                ]
            },
            reward_stars=10,
            reward_xp=15,
            school_id=None,
            is_active=True,
        ),
    ]
    session.add_all(configs)
    await session.flush()
    print(f"  [Games] {len(configs)} game configs")


async def seed_men_compliance(session: AsyncSession) -> None:
    """Seed MEN curriculum reference data and objectives."""
    result = await seed_men_reference_data(session)

    extra_curricula = [
        {
            "curriculum_id": uuid.uuid5(
                uuid.NAMESPACE_URL,
                "men-primaire-3-francais-2025-2026",
            ),
            "level": "Primaire",
            "grade": "3eme annee",
            "subject": "Francais",
            "academic_year": "2025-2026",
            "version": "1.0",
            "objectives": [
                ("FRA-P3-01", "Lire un court recit", "قراءة قصة قصيرة"),
                ("FRA-P3-02", "Identifier le verbe", "تحديد الفعل"),
                ("FRA-P3-03", "Rediger une phrase simple", "كتابة جملة بسيطة"),
            ],
        },
        {
            "curriculum_id": uuid.uuid5(
                uuid.NAMESPACE_URL,
                "men-college-1-svt-2025-2026",
            ),
            "level": "College",
            "grade": "1ere annee",
            "subject": "Sciences de la vie et de la terre",
            "academic_year": "2025-2026",
            "version": "1.0",
            "objectives": [
                ("SVT-C1-01", "Observer la cellule", "ملاحظة الخلية"),
                ("SVT-C1-02", "Distinguer les ecosystemes", "تمييز الأنظمة البيئية"),
                ("SVT-C1-03", "Expliquer une chaine alimentaire", "شرح سلسلة غذائية"),
            ],
        },
        {
            "curriculum_id": uuid.uuid5(
                uuid.NAMESPACE_URL,
                "men-lycee-tc-physique-2025-2026",
            ),
            "level": "Lycee",
            "grade": "Tronc commun",
            "subject": "Physique-Chimie",
            "academic_year": "2025-2026",
            "version": "1.0",
            "objectives": [
                ("PHY-L1-01", "Mesurer une vitesse", "قياس السرعة"),
                ("PHY-L1-02", "Identifier un melange", "تحديد خليط"),
                ("PHY-L1-03", "Interpreter un circuit simple", "تفسير دارة بسيطة"),
            ],
        },
    ]

    curricula = [
        MenCurriculum(
            id=payload["curriculum_id"],
            level=payload["level"],
            grade=payload["grade"],
            subject=payload["subject"],
            academic_year=payload["academic_year"],
            version=payload["version"],
            is_active=True,
        )
        for payload in extra_curricula
    ]
    session.add_all(curricula)
    await session.flush()

    objectives: list[MenObjective] = []
    for payload, curriculum in zip(extra_curricula, curricula, strict=True):
        for display_order, (code, title_fr, title_ar) in enumerate(
            payload["objectives"],
            start=1,
        ):
            objectives.append(
                MenObjective(
                    id=uuid.uuid5(
                        uuid.NAMESPACE_URL,
                        f"{payload['subject']}-{code}-{display_order}",
                    ),
                    curriculum_id=curriculum.id,
                    code=code,
                    title_fr=title_fr,
                    title_ar=title_ar,
                    description_fr=(
                        f"Objectif MEN de demonstration pour {payload['subject']}"
                    ),
                    trimester=min(display_order, 3),
                    unit_number=display_order,
                    is_mandatory=True,
                    hours_recommended=2.0,
                    display_order=display_order,
                )
            )

    session.add_all(objectives)
    await session.flush()

    print(
        "  [MEN] "
        f"{result['curricula_created'] + len(curricula)} curricula, "
        f"{result['objectives_created'] + len(objectives)} objectives"
    )


async def seed_demo_student_data(session: AsyncSession) -> None:
    """Seed realistic demo data for student/parent role testing."""
    now = _now()

    # ContentProgress — 2 completed platform items, 1 in_progress
    for content_id, status in [
        (PLATFORM_CONTENT_1_ID, "completed"),
        (PLATFORM_CONTENT_2_ID, "completed"),
        (PLATFORM_CONTENT_3_ID, "in_progress"),
    ]:
        session.add(
            ContentProgress(
                student_id=STUDENT_1_ID,
                content_item_id=content_id,
                status=status,
            )
        )
    await session.flush()

    # StudentReward aggregate
    session.add(
        StudentReward(
            student_id=STUDENT_1_ID,
            stars=25,
            xp=350,
            level=3,
            streak_days=5,
            longest_streak=7,
            last_activity_at=now,
            badges=["first_login", "streak_7", "xp_250"],
        )
    )
    await session.flush()

    # RewardEvent history
    for event_type, stars, xp, delta_days in [
        ("story_complete", 5, 50, 5),
        ("quiz_pass", 3, 30, 3),
        ("game_complete", 2, 20, 2),
        ("login_streak", 1, 10, 1),
    ]:
        session.add(
            RewardEvent(
                student_id=STUDENT_1_ID,
                event_type=event_type,
                stars_earned=stars,
                xp_earned=xp,
                created_at=now - timedelta(days=delta_days),
            )
        )
    await session.flush()

    # QuizAttempt — one completed attempt at the math quiz
    session.add(
        QuizAttempt(
            quiz_id=QUIZ_MATH_ID,
            student_id=STUDENT_1_ID,
            attempt_no=1,
            started_at=now - timedelta(hours=2),
            completed_at=now - timedelta(hours=1),
            score=16.0,
            max_score=20,
            status="COMPLETED",
        )
    )
    await session.flush()

    print(
        "  [Demo] Student demo data: 3 content progress, rewards, 4 events, 1 quiz attempt"
    )


async def seed_additional_students(session: AsyncSession) -> None:
    """Seed 5 students at different levels for age-banded content testing (Phase G8)."""
    new_classes = [
        Class(
            id=CLASS_CP_ID,
            school_id=SCHOOL_ID,
            code="CP-A",
            academic_year_id=YEAR_ID,
            name="CP A",
        ),
        Class(
            id=CLASS_CE2_ID,
            school_id=SCHOOL_ID,
            code="CE2-A",
            academic_year_id=YEAR_ID,
            name="CE2 A",
        ),
        Class(
            id=CLASS_CM2_ID,
            school_id=SCHOOL_ID,
            code="CM2-A",
            academic_year_id=YEAR_ID,
            name="CM2 A",
        ),
        Class(
            id=CLASS_3EME_ID,
            school_id=SCHOOL_ID,
            code="3eme-A",
            academic_year_id=YEAR_ID,
            name="3ème A",
        ),
        Class(
            id=CLASS_TERM_ID,
            school_id=SCHOOL_ID,
            code="Term-A",
            academic_year_id=YEAR_ID,
            name="Terminale A",
        ),
    ]
    session.add_all(new_classes)
    await session.flush()

    student_data = [
        (
            STUDENT_CP_ID,
            "amina.cp@ecole-benani.ma",
            "Amina Tazi",
            date(2020, 3, 10),
            "CP",
            "STD-2025-010",
        ),
        (
            STUDENT_CE2_ID,
            "karim.ce2@ecole-benani.ma",
            "Karim Fassi",
            date(2018, 7, 20),
            "CE2",
            "STD-2025-011",
        ),
        (
            STUDENT_CM2_ID,
            "leila.cm2@ecole-benani.ma",
            "Leila Mansouri",
            date(2016, 11, 5),
            "CM2",
            "STD-2025-012",
        ),
        (
            STUDENT_3EME_ID,
            "mehdi.3eme@ecole-benani.ma",
            "Mehdi Berrada",
            date(2012, 1, 25),
            "3eme",
            "STD-2025-013",
        ),
        (
            STUDENT_TERM_ID,
            "sara.terminale@ecole-benani.ma",
            "Sara Chraibi",
            date(2008, 9, 14),
            "Terminale",
            "STD-2025-014",
        ),
    ]
    class_map = {
        STUDENT_CP_ID: CLASS_CP_ID,
        STUDENT_CE2_ID: CLASS_CE2_ID,
        STUDENT_CM2_ID: CLASS_CM2_ID,
        STUDENT_3EME_ID: CLASS_3EME_ID,
        STUDENT_TERM_ID: CLASS_TERM_ID,
    }

    for uid, email, full_name, dob, level, student_no in student_data:
        session.add(
            User(
                id=uid,
                email=email,
                full_name=full_name,
                password_hash=_hash("student123"),
                status="active",
                school_id=SCHOOL_ID,
            )
        )
    await session.flush()

    for uid, email, full_name, dob, level, student_no in student_data:
        session.add(
            Membership(
                user_id=uid, school_id=SCHOOL_ID, role_code="STD", status="active"
            )
        )
        session.add(
            StudentProfile(
                user_id=uid,
                school_id=SCHOOL_ID,
                student_number=student_no,
                date_of_birth=dob,
                class_level=level,
                nationality="Marocaine",
            )
        )
        session.add(
            Enrollment(
                student_id=uid,
                class_id=class_map[uid],
                period_id=PERIOD_2_ID,
                school_id=SCHOOL_ID,
                status="active",
            )
        )
    await session.flush()
    print("  [G8] 5 additional students + 5 level classes")


async def seed_additional_parents(session: AsyncSession) -> None:
    """Seed 2 additional parents for the new CP and CE2 students (Phase G8)."""
    new_parents = [
        User(
            id=PARENT_TAZI_ID,
            email="parent.tazi@gmail.com",
            full_name="Fatima Tazi",
            phone="+212611111111",
            password_hash=_hash("parent123"),
            status="active",
            school_id=SCHOOL_ID,
        ),
        User(
            id=PARENT_FASSI_ID,
            email="parent.fassi@gmail.com",
            full_name="Omar Fassi",
            phone="+212622222222",
            password_hash=_hash("parent123"),
            status="active",
            school_id=SCHOOL_ID,
        ),
    ]
    session.add_all(new_parents)
    await session.flush()

    session.add_all(
        [
            Membership(
                user_id=PARENT_TAZI_ID,
                school_id=SCHOOL_ID,
                role_code="PAR",
                status="active",
            ),
            Membership(
                user_id=PARENT_FASSI_ID,
                school_id=SCHOOL_ID,
                role_code="PAR",
                status="active",
            ),
        ]
    )
    session.add_all(
        [
            ParentProfile(
                user_id=PARENT_TAZI_ID,
                school_id=SCHOOL_ID,
                relationship_type="mother",
                cin_number="EF112233",
                address="22 Rue Hassan II, Casablanca",
                profession="Enseignante",
                emergency_phone="+212611111111",
            ),
            ParentProfile(
                user_id=PARENT_FASSI_ID,
                school_id=SCHOOL_ID,
                relationship_type="father",
                cin_number="GH445566",
                address="8 Boulevard Zerktouni, Casablanca",
                profession="Comptable",
                emergency_phone="+212622222222",
            ),
        ]
    )
    session.add_all(
        [
            ParentChildLink(
                parent_user_id=PARENT_TAZI_ID,
                child_user_id=STUDENT_CP_ID,
                school_id=SCHOOL_ID,
                status="active",
                linked_at=_now(),
                linked_by=ADMIN_ID,
            ),
            ParentChildLink(
                parent_user_id=PARENT_FASSI_ID,
                child_user_id=STUDENT_CE2_ID,
                school_id=SCHOOL_ID,
                status="active",
                linked_at=_now(),
                linked_by=ADMIN_ID,
            ),
        ]
    )
    await session.flush()
    print("  [G8] 2 additional parents (parent.tazi + parent.fassi)")


async def seed_level_content(session: AsyncSession) -> None:
    """Seed 2 platform ContentItems per school level (Phase G8)."""
    level_specs = [
        (
            "maternelle",
            "Maternelle",
            4,
            5,
            [
                ("Les couleurs - Vidéo éducative", "video", "science", "fr"),
                ("Coloriage - Les animaux", "pdf", "art", "fr"),
            ],
        ),
        (
            "CP",
            "CP",
            6,
            6,
            [
                ("Apprendre à lire - Leçon 1", "video", "french", "fr"),
                ("Exercices d'écriture CP", "pdf", "french", "fr"),
            ],
        ),
        (
            "CE1",
            "CE1",
            7,
            7,
            [
                ("Les additions - Cours", "video", "math", "fr"),
                ("Dictée CE1 - Semaine 1", "audio", "french", "fr"),
            ],
        ),
        (
            "CE2",
            "CE2",
            8,
            8,
            [
                ("La multiplication - Introduction", "video", "math", "fr"),
                ("Sciences - Le corps humain", "pdf", "science", "fr"),
            ],
        ),
        (
            "CM1",
            "CM1",
            9,
            9,
            [
                ("Fractions - Introduction", "video", "math", "fr"),
                ("Géographie du Maroc", "pdf", "geography", "fr"),
            ],
        ),
        (
            "CM2",
            "CM2",
            10,
            10,
            [
                ("Préparation 6ème - Mathématiques", "video", "math", "fr"),
                ("Rédaction - Le conte", "pdf", "french", "fr"),
            ],
        ),
        (
            "5eme",
            "5ème",
            11,
            11,
            [
                ("L'histoire du Maroc médiéval", "video", "history", "fr"),
                ("Anglais - Unit 1 - Greetings", "pdf", "english", "fr"),
            ],
        ),
        (
            "4eme",
            "4ème",
            12,
            12,
            [
                ("Algèbre - Équations du premier degré", "video", "math", "fr"),
                ("Physique - Les forces", "pdf", "science", "fr"),
            ],
        ),
        (
            "3eme",
            "3ème",
            13,
            14,
            [
                ("Brevet blanc - Mathématiques", "pdf", "math", "fr"),
                ("SVT - La cellule et son rôle", "video", "science", "fr"),
            ],
        ),
        (
            "2nde",
            "2nde",
            15,
            15,
            [
                ("Fonctions - Introduction au lycée", "video", "math", "fr"),
                (
                    "Philosophie - Introduction à la pensée critique",
                    "pdf",
                    "philosophy",
                    "fr",
                ),
            ],
        ),
        (
            "1ere",
            "1ère",
            16,
            16,
            [
                ("BAC Français - Méthode du commentaire", "pdf", "french", "fr"),
                ("Chimie organique - Les alcanes", "video", "science", "fr"),
            ],
        ),
        (
            "Terminale",
            "Terminale",
            17,
            18,
            [
                ("BAC Maths - Révisions intégrales", "video", "math", "fr"),
                ("BAC SVT - Génétique et hérédité", "pdf", "science", "fr"),
            ],
        ),
    ]

    count = 0
    for level_band, level_label, age_min, age_max, items in level_specs:
        for title, content_type, subject, language in items:
            session.add(
                ContentItem(
                    school_id=None,
                    title=title,
                    content_type=content_type,
                    level_band=level_band,
                    language=language,
                    subject=subject,
                    description=f"Contenu pédagogique pour le niveau {level_label}.",
                    status="published",
                    origin="PLATFORM",
                    created_by=CONTENT_MGR_ID,
                    target_age_min=age_min,
                    target_age_max=age_max,
                )
            )
            count += 1
    await session.flush()
    print(
        f"  [G8] {count} level-banded platform content items (maternelle → Terminale)"
    )


async def seed_class_content_assignments(session: AsyncSession) -> None:
    """Assign level-appropriate content to the new classes (Phase G8)."""
    from sqlalchemy import select

    # Find all platform content for 6ème math to assign to class 6A
    math_6eme = await session.execute(
        select(ContentItem).where(
            ContentItem.level_band == "6eme",
            ContentItem.subject == "math",
            ContentItem.school_id.is_(None),
            ContentItem.id != PLATFORM_CONTENT_1_ID,  # already assigned in seed_cms
        )
    )
    for item in math_6eme.scalars():
        session.add(
            ClassContentAssignment(
                teacher_id=TEACHER_1_ID,
                class_id=CLASS_6A_ID,
                content_item_id=item.id,
                school_id=SCHOOL_ID,
                assigned_at=_now(),
            )
        )

    # Assign level content to each new class
    level_class_map = [
        ("CP", CLASS_CP_ID),
        ("CE2", CLASS_CE2_ID),
        ("CM2", CLASS_CM2_ID),
        ("3eme", CLASS_3EME_ID),
        ("Terminale", CLASS_TERM_ID),
    ]
    for level_band, class_id in level_class_map:
        level_items = await session.execute(
            select(ContentItem).where(
                ContentItem.level_band == level_band,
                ContentItem.school_id.is_(None),
            )
        )
        for item in level_items.scalars():
            session.add(
                ClassContentAssignment(
                    teacher_id=TEACHER_1_ID,
                    class_id=class_id,
                    content_item_id=item.id,
                    school_id=SCHOOL_ID,
                    assigned_at=_now(),
                )
            )

    await session.flush()
    print("  [G8] Class content assignments for 6A + 5 new level classes")


async def seed_skill_system(session: AsyncSession) -> None:
    """Seed SkillDimension, SkillMilestone, and SkillProgress for demo users (Phase G8)."""
    dims = [
        SkillDimension(
            id=DIM_MATH_ID,
            code="mathematiques",
            name_fr="Mathématiques",
            name_ar="الرياضيات",
            name_en="Mathematics",
            display_order=1,
        ),
        SkillDimension(
            id=DIM_LECTURE_ID,
            code="lecture",
            name_fr="Lecture",
            name_ar="القراءة",
            name_en="Reading",
            display_order=2,
        ),
        SkillDimension(
            id=DIM_SCIENCES_ID,
            code="sciences",
            name_fr="Sciences",
            name_ar="العلوم",
            name_en="Sciences",
            display_order=3,
        ),
        SkillDimension(
            id=DIM_CREATIVITE_ID,
            code="creativite",
            name_fr="Créativité",
            name_ar="الإبداع",
            name_en="Creativity",
            display_order=4,
        ),
        SkillDimension(
            id=DIM_COMM_ID,
            code="communication",
            name_fr="Communication",
            name_ar="التواصل",
            name_en="Communication",
            display_order=5,
        ),
    ]
    session.add_all(dims)
    await session.flush()

    milestone_labels = [
        (1, "debutant", "Débutant", "مبتدئ"),
        (2, "intermediaire", "Intermédiaire", "متوسط"),
        (3, "avance", "Avancé", "متقدم"),
    ]
    milestones: list[SkillMilestone] = []
    for dim in dims:
        for level, code_suffix, name_fr, name_ar in milestone_labels:
            milestones.append(
                SkillMilestone(
                    dimension_id=dim.id,
                    code=f"{dim.code}_{code_suffix}",
                    name_fr=f"{dim.name_fr} — {name_fr}",
                    name_ar=name_ar,
                    level=level,
                    rule_config={"type": "quiz_score", "threshold": level * 30},
                    badge_icon=["🌱", "⭐", "🏆"][level - 1],
                )
            )
    session.add_all(milestones)
    await session.flush()

    # SkillProgress for existing students (milestones[0..2] = math dim milestones)
    # milestone indices: math=0,1,2 | lecture=3,4,5 | sciences=6,7,8 | creativite=9,10,11 | comm=12,13,14
    progress_entries = [
        # Yassine: math (unlocked lvl1+2, in_progress lvl3), lecture (unlocked lvl1), sciences (in_progress lvl1)
        SkillProgress(
            student_id=STUDENT_1_ID,
            milestone_id=milestones[0].id,
            school_id=SCHOOL_ID,
            academic_year_id=YEAR_ID,
            status="unlocked",
            current_value=100,
            unlocked_at=_now() - timedelta(days=30),
        ),
        SkillProgress(
            student_id=STUDENT_1_ID,
            milestone_id=milestones[1].id,
            school_id=SCHOOL_ID,
            academic_year_id=YEAR_ID,
            status="unlocked",
            current_value=100,
            unlocked_at=_now() - timedelta(days=15),
        ),
        SkillProgress(
            student_id=STUDENT_1_ID,
            milestone_id=milestones[2].id,
            school_id=SCHOOL_ID,
            academic_year_id=YEAR_ID,
            status="in_progress",
            current_value=60,
        ),
        SkillProgress(
            student_id=STUDENT_1_ID,
            milestone_id=milestones[3].id,
            school_id=SCHOOL_ID,
            academic_year_id=YEAR_ID,
            status="unlocked",
            current_value=100,
            unlocked_at=_now() - timedelta(days=20),
        ),
        SkillProgress(
            student_id=STUDENT_1_ID,
            milestone_id=milestones[6].id,
            school_id=SCHOOL_ID,
            academic_year_id=YEAR_ID,
            status="in_progress",
            current_value=40,
        ),
        # Salma: lecture (unlocked lvl1+2)
        SkillProgress(
            student_id=STUDENT_2_ID,
            milestone_id=milestones[3].id,
            school_id=SCHOOL_ID,
            academic_year_id=YEAR_ID,
            status="unlocked",
            current_value=100,
            unlocked_at=_now() - timedelta(days=10),
        ),
        SkillProgress(
            student_id=STUDENT_2_ID,
            milestone_id=milestones[4].id,
            school_id=SCHOOL_ID,
            academic_year_id=YEAR_ID,
            status="unlocked",
            current_value=100,
            unlocked_at=_now() - timedelta(days=5),
        ),
        # Omar: math (in_progress lvl1)
        SkillProgress(
            student_id=STUDENT_3_ID,
            milestone_id=milestones[0].id,
            school_id=SCHOOL_ID,
            academic_year_id=YEAR_ID,
            status="in_progress",
            current_value=50,
        ),
    ]
    session.add_all(progress_entries)
    await session.flush()
    print(
        f"  [G8] Skill system: 5 dimensions, {len(milestones)} milestones, {len(progress_entries)} progress entries"
    )


async def seed_all_roles_data(session: AsyncSession) -> None:
    """Seed additional role-specific demo data visible in each dashboard (Phase G8)."""
    now = _now()

    # ── Admin: 3 more announcements (lifecycle demo) ──
    session.add_all(
        [
            Announcement(
                id=ANN_3_ID,
                school_id=SCHOOL_ID,
                author_id=ADMIN_ID,
                title="Résultats du 2ème semestre — Publication imminente",
                body="Les résultats du deuxième semestre seront publiés la semaine prochaine. Préparez-vous à les consulter sur la plateforme.",
                target_roles=["PAR", "STD"],
                status="DRAFT",
            ),
            Announcement(
                id=ANN_4_ID,
                school_id=SCHOOL_ID,
                author_id=DIRECTOR_ID,
                title="Réunion des parents d'élèves — 28 avril 2026",
                body="Une réunion des parents d'élèves est organisée le 28 avril 2026 à 18h00 dans la salle des fêtes de l'école. Votre présence est vivement souhaitée.",
                target_roles=["PAR"],
                published_at=now - timedelta(days=2),
                status="PUBLISHED",
            ),
            Announcement(
                id=ANN_5_ID,
                school_id=SCHOOL_ID,
                author_id=ADMIN_ID,
                title="Fête de l'école 2025 — Programme",
                body="Retrouvez ci-joint le programme de la fête de l'école 2025. Merci à tous les participants.",
                target_roles=["PAR", "STD", "TCH"],
                published_at=now - timedelta(days=60),
                status="PUBLISHED",
            ),
        ]
    )

    # ── Admin: 2 more fee structures ──
    session.add_all(
        [
            FeeStructure(
                school_id=SCHOOL_ID,
                academic_year_id=YEAR_ID,
                name="Frais d'inscription",
                amount=500.00,
                currency="MAD",
                frequency="ANNUAL",
                due_day=1,
                applies_to_level=None,
                status="ACTIVE",
            ),
            FeeStructure(
                school_id=SCHOOL_ID,
                academic_year_id=YEAR_ID,
                name="Frais parascolaires",
                amount=300.00,
                currency="MAD",
                frequency="ANNUAL",
                due_day=15,
                applies_to_level=None,
                status="ACTIVE",
            ),
        ]
    )
    await session.flush()

    # ── Admin: 5 more invoices in different states ──
    # InvoiceStatus enum: pending, paid, failed, canceled
    invoice_specs = [
        ("pending", date(2026, 3, 1), date(2026, 3, 31), 2000.00),
        ("pending", date(2026, 3, 1), date(2026, 4, 30), 3500.00),
        ("paid", date(2026, 2, 1), date(2026, 2, 28), 3500.00),
        ("failed", date(2026, 1, 1), date(2026, 1, 31), 3500.00),
        ("canceled", date(2025, 12, 1), date(2025, 12, 31), 1200.00),
    ]
    for status, issued, due, amount in invoice_specs:
        inv = Invoice(
            school_id=SCHOOL_ID,
            parent_id=PARENT_2_ID,
            period_id=PERIOD_2_ID,
            status=status,
            total_amount=amount,
            currency="MAD",
            issued_date=issued,
            due_date=due,
        )
        session.add(inv)
    await session.flush()

    # ── Director: 5 days of attendance sessions (6A and 6B) ──
    school_days = [
        date(2026, 4, 14),
        date(2026, 4, 15),
        date(2026, 4, 16),
        date(2026, 4, 17),
        date(2026, 4, 18),
    ]
    statuses_6a = [
        ("present", "present", "late"),
        ("present", "absent", "present"),
        ("present", "present", "present"),
        ("late", "present", "absent"),
        ("present", "present", "present"),
    ]
    for i, day in enumerate(school_days):
        for class_id, students in [
            (CLASS_6A_ID, [STUDENT_1_ID, STUDENT_2_ID]),
            (CLASS_6B_ID, [STUDENT_3_ID]),
        ]:
            att = AttendanceSession(
                class_id=class_id,
                period_id=PERIOD_2_ID,
                teacher_id=TEACHER_1_ID,
                school_id=SCHOOL_ID,
                session_date=day,
                slot="08:00-09:00",
            )
            session.add(att)
            await session.flush()
            for j, student_id in enumerate(students):
                st = statuses_6a[i][min(j, 2)]
                session.add(
                    AttendanceRecord(
                        attendance_session_id=att.id,
                        student_id=student_id,
                        school_id=SCHOOL_ID,
                        status=st,
                        absence_reason="Maladie" if st == "absent" else None,
                    )
                )
    await session.flush()

    # ── Teacher: 2 more submissions for different workflow states ──
    submitted_sub = Submission(
        assignment_id=ASSIGN_1_ID,
        student_id=STUDENT_2_ID,
        status="submitted",
        submitted_at=now - timedelta(hours=12),
    )
    session.add(submitted_sub)
    await session.flush()

    graded_sub = Submission(
        assignment_id=ASSIGN_1_ID,
        student_id=STUDENT_3_ID,
        status="graded",
        submitted_at=now - timedelta(days=2),
    )
    session.add(graded_sub)
    await session.flush()

    session.add(
        Grade(
            submission_id=graded_sub.id,
            teacher_id=TEACHER_1_ID,
            score=14.0,
            feedback_text="Bon effort, quelques erreurs de calcul à revoir.",
            published_at=now - timedelta(hours=6),
        )
    )

    # ── Teacher: quiz attempts for 6A students ──
    for student_id, score in [(STUDENT_2_ID, 12.0), (STUDENT_3_ID, 10.0)]:
        session.add(
            QuizAttempt(
                quiz_id=QUIZ_MATH_ID,
                student_id=student_id,
                attempt_no=1,
                started_at=now - timedelta(hours=4),
                completed_at=now - timedelta(hours=3),
                score=score,
                max_score=20,
                status="COMPLETED",
            )
        )

    # ── Student: reward events for leaderboard (Salma + Omar) ──
    session.add(
        StudentReward(
            student_id=STUDENT_2_ID,
            stars=15,
            xp=180,
            level=2,
            streak_days=3,
            longest_streak=5,
            last_activity_at=now,
            badges=["first_login"],
        )
    )
    session.add(
        StudentReward(
            student_id=STUDENT_3_ID,
            stars=8,
            xp=90,
            level=1,
            streak_days=1,
            longest_streak=3,
            last_activity_at=now - timedelta(days=1),
            badges=["first_login"],
        )
    )
    for student_id, delta in [(STUDENT_2_ID, 4), (STUDENT_3_ID, 6)]:
        session.add(
            RewardEvent(
                student_id=student_id,
                event_type="quiz_pass",
                stars_earned=3,
                xp_earned=30,
                created_at=now - timedelta(days=delta),
            )
        )

    # ── Parent: 2 more feed items for parent.alaoui ──
    session.add_all(
        [
            ParentFeedItem(
                school_id=SCHOOL_ID,
                parent_id=PARENT_1_ID,
                student_id=STUDENT_3_ID,
                source_type="grade",
                source_ref=str(graded_sub.id),
                title="Note publiée pour Omar",
                body="Omar a obtenu 14/20 en Exercices - Fractions.",
            ),
            ParentFeedItem(
                school_id=SCHOOL_ID,
                parent_id=PARENT_1_ID,
                student_id=STUDENT_1_ID,
                source_type="attendance",
                source_ref="attendance:absent:2026-04-15",
                title="Absence signalée — Yassine",
                body="Yassine a été signalé absent le 15 avril 2026.",
            ),
        ]
    )

    # ── CMS: 2 draft content items for publish workflow demo ──
    session.add_all(
        [
            ContentItem(
                school_id=None,
                title="Initiation à la robotique - Brouillon",
                content_type="video",
                level_band="6eme",
                language="fr",
                subject="technology",
                description="Présentation de la robotique éducative pour les collégiens.",
                status="draft",
                origin="PLATFORM",
                created_by=CONTENT_MGR_ID,
            ),
            ContentItem(
                school_id=None,
                title="Histoire des sciences au Maroc - Brouillon",
                content_type="pdf",
                level_band="CM2",
                language="fr",
                subject="history",
                description="Dossier sur les grandes découvertes scientifiques au Maroc.",
                status="draft",
                origin="PLATFORM",
                created_by=CONTENT_MGR_ID,
            ),
        ]
    )

    await session.flush()
    print(
        "  [G8] Role-specific data: +3 announcements, +2 fee structures, +5 invoices, +10 attendance sessions, +2 submissions, +quiz attempts, +feed items, +2 draft CMS items"
    )


async def seed_difficulty_adaptations(session: AsyncSession) -> None:
    """Seed difficulty adaptation history and extra quiz attempts for adaptive demo (Phase H2).

    Creates:
    - Extra quiz attempts for Yassine (2 consecutive high scores → promotion pattern)
    - Extra quiz attempts for Omar (2 consecutive low scores → demotion pattern)
    - DifficultyAdaptation audit log entries showing the adaptation trail
    """
    now = _now()

    # ── Yassine: 2 more high-score attempts on EASY quiz → triggers promotion to MEDIUM ──
    session.add(
        QuizAttempt(
            quiz_id=QUIZ_FR_ID,  # EASY difficulty quiz
            student_id=STUDENT_1_ID,
            attempt_no=1,
            started_at=now - timedelta(days=5),
            completed_at=now - timedelta(days=5, hours=-1),
            score=18.0,
            max_score=20,
            status="COMPLETED",
        )
    )
    session.add(
        QuizAttempt(
            quiz_id=QUIZ_FR_ID,
            student_id=STUDENT_1_ID,
            attempt_no=2,
            started_at=now - timedelta(days=3),
            completed_at=now - timedelta(days=3, hours=-1),
            score=17.0,
            max_score=20,
            status="COMPLETED",
        )
    )
    await session.flush()

    # ── Omar: 2 low-score attempts on MEDIUM quiz → triggers demotion to EASY ──
    session.add(
        QuizAttempt(
            quiz_id=QUIZ_MATH_ID,  # MEDIUM difficulty quiz
            student_id=STUDENT_3_ID,
            attempt_no=2,
            started_at=now - timedelta(days=4),
            completed_at=now - timedelta(days=4, hours=-1),
            score=3.0,
            max_score=20,
            status="COMPLETED",
        )
    )
    session.add(
        QuizAttempt(
            quiz_id=QUIZ_MATH_ID,
            student_id=STUDENT_3_ID,
            attempt_no=3,
            started_at=now - timedelta(days=2),
            completed_at=now - timedelta(days=2, hours=-1),
            score=4.0,
            max_score=20,
            status="COMPLETED",
        )
    )
    await session.flush()

    # ── DifficultyAdaptation audit trail ──
    adaptations = [
        # Yassine promoted EASY → MEDIUM in french (2 scores ≥ 80%)
        DifficultyAdaptation(
            student_id=STUDENT_1_ID,
            subject="french",
            previous_difficulty="EASY",
            new_difficulty="MEDIUM",
            reason="promoted_high_scores",
        ),
        # Yassine promoted EASY → MEDIUM in math earlier
        DifficultyAdaptation(
            student_id=STUDENT_1_ID,
            subject="math",
            previous_difficulty="EASY",
            new_difficulty="MEDIUM",
            reason="promoted_high_scores",
        ),
        # Yassine promoted MEDIUM → HARD in math (latest)
        DifficultyAdaptation(
            student_id=STUDENT_1_ID,
            subject="math",
            previous_difficulty="MEDIUM",
            new_difficulty="HARD",
            reason="promoted_high_scores",
        ),
        # Omar demoted MEDIUM → EASY in math (2 scores ≤ 40%)
        DifficultyAdaptation(
            student_id=STUDENT_3_ID,
            subject="math",
            previous_difficulty="MEDIUM",
            new_difficulty="EASY",
            reason="demoted_low_scores",
        ),
    ]
    session.add_all(adaptations)
    await session.flush()
    print(
        f"  [H2] Difficulty adaptations: 4 extra quiz attempts, {len(adaptations)} adaptation records"
    )


async def seed_new_student_rewards(session: AsyncSession) -> None:
    """Seed basic rewards for Phase G8 students so their rewards pages are not empty."""
    now = _now()

    new_student_rewards = [
        # Amina (CP, age 6) — beginner, just started
        StudentReward(
            student_id=STUDENT_CP_ID,
            stars=5,
            xp=40,
            level=1,
            streak_days=2,
            longest_streak=2,
            last_activity_at=now - timedelta(hours=3),
            badges=["first_login"],
        ),
        # Karim (CE2, age 8) — moderate progress
        StudentReward(
            student_id=STUDENT_CE2_ID,
            stars=12,
            xp=150,
            level=2,
            streak_days=4,
            longest_streak=6,
            last_activity_at=now - timedelta(hours=5),
            badges=["first_login", "streak_7"],
        ),
        # Leila (CM2, age 10) — good progress
        StudentReward(
            student_id=STUDENT_CM2_ID,
            stars=20,
            xp=280,
            level=3,
            streak_days=6,
            longest_streak=10,
            last_activity_at=now - timedelta(hours=1),
            badges=["first_login", "streak_7", "xp_250"],
        ),
        # Mehdi (3ème, age 14) — active teenager
        StudentReward(
            student_id=STUDENT_3EME_ID,
            stars=18,
            xp=220,
            level=2,
            streak_days=3,
            longest_streak=8,
            last_activity_at=now - timedelta(hours=8),
            badges=["first_login", "streak_7"],
        ),
        # Sara (Terminale, age 17) — focused on BAC prep
        StudentReward(
            student_id=STUDENT_TERM_ID,
            stars=30,
            xp=400,
            level=4,
            streak_days=7,
            longest_streak=14,
            last_activity_at=now - timedelta(minutes=30),
            badges=["first_login", "streak_7", "xp_250"],
        ),
    ]
    session.add_all(new_student_rewards)

    # A few reward events for activity history
    for student_id, events in [
        (STUDENT_CP_ID, [("story_complete", 2, 15, 2), ("login_streak", 1, 5, 1)]),
        (STUDENT_CE2_ID, [("quiz_pass", 3, 30, 3), ("game_complete", 2, 20, 1)]),
        (
            STUDENT_CM2_ID,
            [
                ("quiz_pass", 4, 40, 4),
                ("story_complete", 3, 25, 2),
                ("game_complete", 3, 25, 1),
            ],
        ),
        (STUDENT_3EME_ID, [("quiz_pass", 3, 35, 3), ("story_complete", 2, 20, 1)]),
        (
            STUDENT_TERM_ID,
            [
                ("quiz_pass", 5, 50, 5),
                ("story_complete", 4, 40, 3),
                ("login_streak", 2, 15, 1),
            ],
        ),
    ]:
        for event_type, stars, xp, delta_days in events:
            session.add(
                RewardEvent(
                    student_id=student_id,
                    event_type=event_type,
                    stars_earned=stars,
                    xp_earned=xp,
                    created_at=now - timedelta(days=delta_days),
                )
            )

    await session.flush()
    print("  [H2] 5 new student rewards + 12 reward events for G8 students")


async def main() -> None:
    print("=" * 60)
    print("Ecole Platform — Seeding development database")
    print("=" * 60)

    async with async_session() as session:
        print("\nClearing existing data...")
        await clear_all(session)

        print("\nSeeding domains:")
        await seed_schools(session)
        await seed_iam(session)
        await seed_profiles(session)
        await seed_parent_child_links(session)
        await seed_erp(session)
        await seed_lms(session)
        await seed_com(session)
        await seed_messaging(session)
        await seed_billing(session)
        await seed_audit(session)
        await seed_cms(session)
        await seed_quizzes(session)
        await seed_timetable(session)
        await seed_fees(session)
        await seed_feature_toggles(session)
        await seed_reward_badges(session)
        await seed_game_configs(session)
        await seed_men_compliance(session)
        await seed_demo_student_data(session)
        await seed_additional_students(session)
        await seed_additional_parents(session)
        await seed_level_content(session)
        await seed_class_content_assignments(session)
        await seed_skill_system(session)
        await seed_all_roles_data(session)
        await seed_difficulty_adaptations(session)
        await seed_new_student_rewards(session)
        await seed_calendar(session)
        await seed_documents(session)
        await seed_reporting(session)
        await seed_programs(session)
        await seed_ai_preferences(session)
        await seed_notification_preferences(session)

        await session.commit()

    print("\n" + "=" * 60)
    print("Seeding complete!")
    print("=" * 60)

    _generate_seed_report()


def _generate_seed_report() -> None:
    """Generate a markdown report with all seeded credentials and data."""
    from pathlib import Path

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    report = f"""# Seed Report — Generated {now}

> Auto-generated by `make seed`. Do not edit manually — re-run `make seed` to refresh.

---

## Login Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@ecole-benani.ma` | `admin123` |
| Director | `directeur@ecole-benani.ma` | `director123` |
| Teacher (Math) | `prof.math@ecole-benani.ma` | `teacher123` |
| Teacher (French) | `prof.francais@ecole-benani.ma` | `teacher123` |
| Parent (Alaoui) | `parent.alaoui@gmail.com` | `parent123` |
| Parent (Idrissi) | `parent.idrissi@gmail.com` | `parent123` |
| Parent (Tazi) | `parent.tazi@gmail.com` | `parent123` |
| Parent (Fassi) | `parent.fassi@gmail.com` | `parent123` |
| Student 6eme (Yassine) | `yassine.alaoui@ecole-benani.ma` | `student123` |
| Student 6eme (Salma) | `salma.idrissi@ecole-benani.ma` | `student123` |
| Student 6eme (Omar) | `omar.benali@ecole-benani.ma` | `student123` |
| Student CP (Amina) | `amina.cp@ecole-benani.ma` | `student123` |
| Student CE2 (Karim) | `karim.ce2@ecole-benani.ma` | `student123` |
| Student CM2 (Leila) | `leila.cm2@ecole-benani.ma` | `student123` |
| Student 3eme (Mehdi) | `mehdi.3eme@ecole-benani.ma` | `student123` |
| Student Terminale (Sara) | `sara.terminale@ecole-benani.ma` | `student123` |
| Superadmin | `superadmin@ecole-platform.ma` | `superadmin123` |
| Content Manager | `cms@ecole-platform.ma` | `content123` |

## Schools

| Name | Code | City | Status | Plan |
|------|------|------|--------|------|
| Ecole Benani | ECOLE-BENANI | Casablanca | active | premium |
| Ecole Atlas | ECOLE-ATLAS | Rabat | trial | trial |

## Classes

| Class | Level | Students |
|-------|-------|----------|
| 6eme A | 6eme | Yassine Alaoui, Salma Idrissi |
| 6eme B | 6eme | Omar Benali |
| CP A | CP | Amina Tazi |
| CE2 A | CE2 | Karim Fassi |
| CM2 A | CM2 | Leila Mansouri |
| 3eme A | 3eme | Mehdi Berrada |
| Terminale A | Terminale | Sara Chraibi |

## Parent → Children

| Parent | Children |
|--------|----------|
| Parent Alaoui | Yassine Alaoui, Omar Benali |
| Parent Idrissi | Salma Idrissi |
| Fatima Tazi | Amina Tazi (CP) |
| Omar Fassi | Karim Fassi (CE2) |

## Academic Year

| Year | Period 1 (closed) | Period 2 (active) |
|------|-------------------|-------------------|
| 2025-2026 | Sep 2025 → Jan 2026 | Feb 2026 → Jun 2026 |

## Courses & Quizzes

| Course | Teacher | Quiz | Questions |
|--------|---------|------|-----------|
| Mathematiques 6eme | Prof Maths | Quiz Fractions (20 pts) | 5 MCQ |
| Francais 6eme | Prof Francais | Quiz Grammaire (20 pts) | 5 MCQ |

## Billing

| Fee | Amount (MAD) | Frequency |
|-----|-------------|-----------|
| Scolarite | 3,500 | Monthly |
| Transport | 800 | Monthly |
| Cantine | 1,200 | Monthly |
| Inscription | 500 | Annual |
| Parascolaire | 300 | Annual |

Invoice statuses seeded: `pending`, `paid`, `failed`, `canceled`

## Gamification

| Student | Stars | XP | Level | Badges |
|---------|-------|-----|-------|--------|
| Yassine | 25 | 350 | 3 | first_login, streak_7, xp_250 |
| Amina (CP) | 12 | 180 | 2 | first_login, streak_3 |
| Karim (CE2) | 18 | 280 | 2 | first_login, streak_3, xp_250 |
| Leila (CM2) | 30 | 450 | 3 | first_login, streak_7, xp_250 |
| Mehdi (3eme) | 22 | 320 | 3 | first_login, streak_3 |
| Sara (Term) | 35 | 520 | 4 | first_login, streak_7, xp_250, xp_500 |

## Skill Passport (5 dimensions x 3 levels)

Dimensions: Mathematiques, Lecture, Sciences, Creativite, Communication

| Student | Highlights |
|---------|-----------|
| Yassine | Maths Avance 60%, Lecture Debutant unlocked |
| Salma | Lecture + Sciences Debutant unlocked |
| Omar | Maths Debutant 50% in progress |

## Difficulty Adaptation

| Student | Subject | Change |
|---------|---------|--------|
| Yassine | math | EASY → MEDIUM → HARD (promoted) |
| Omar | math | MEDIUM → EASY (demoted) |

## Feature Toggles

gamification, rewards, skill_passport, difficulty_adaptation, parent_dashboard_v2 — all **enabled**

## Timetable (6A sample)

Mon 08:00 Maths, Mon 09:45 Francais, Wed 08:00 Maths, Thu 09:45 Francais

## Content Library

6 platform CMS items + 24 level-banded items (maternelle → Terminale) + 2 CMS drafts

---

*For the full detailed reference, see `SEED-REFERENCE.md`*
"""

    # Write inside the container at /app/seed-report.md
    report_path = Path(__file__).resolve().parent.parent / "seed-report.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"\n  Report generated: {report_path}")

    # Also print key credentials to console for quick access
    print("\n  Quick credentials:")
    print("    Admin:      admin@ecole-benani.ma / admin123")
    print("    Teacher:    prof.math@ecole-benani.ma / teacher123")
    print("    Parent:     parent.alaoui@gmail.com / parent123")
    print("    Student:    yassine.alaoui@ecole-benani.ma / student123")
    print("    Superadmin: superadmin@ecole-platform.ma / superadmin123")
    print("    CMS:        cms@ecole-platform.ma / content123")


if __name__ == "__main__":
    asyncio.run(main())
