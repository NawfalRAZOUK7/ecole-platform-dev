"""Seed data script for development environment.

Creates realistic test data for all 6 domains.
Run with: make seed  (or: docker compose exec backend python -m app.seed)

Reference: Pack C4 (Data Model), Sprint 1 acceptance criteria.
"""

from __future__ import annotations

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
    Installment,
    Invoice,
    InvoiceItem,
    PaymentAttempt,
    PaymentPlan,
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
    ContentItemAsset,
    ContentProgress,
    ContentSubmission,
    Course,
    Grade,
    StudentPeriodAverage,
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
from app.services.admin.compliance import seed_men_reference_data

# ── Fixed UUIDs for deterministic seeding ──────────────────────────────────

SCHOOL_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")
SCHOOL_ID_2 = uuid.UUID("00000000-0000-4000-8000-000000000002")
MICRO_SCHOOL_TENANT_ID = uuid.UUID("00000000-0000-4000-8000-000000000003")

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
# Contenu CMS par niveau pour démontrer la portée D3 (élève CP vs élève 3e).
# CLASS_CP_ID / CLASS_3EME_ID ont déjà des élèves inscrits + l'affectation
# automatique par niveau (seed_class_content_assignments) ; il manquait le
# contenu CP/3e lui-même → chaque élève voyait une bibliothèque vide.
PLATFORM_CONTENT_CP_1_ID = uuid.UUID("30000000-0000-4000-8000-000000000016")
PLATFORM_CONTENT_CP_2_ID = uuid.UUID("30000000-0000-4000-8000-000000000017")
PLATFORM_CONTENT_3EME_1_ID = uuid.UUID("30000000-0000-4000-8000-000000000018")
PLATFORM_CONTENT_3EME_2_ID = uuid.UUID("30000000-0000-4000-8000-000000000019")
PLATFORM_CONTENT_CE2_1_ID = uuid.UUID("30000000-0000-4000-8000-00000000001a")
PLATFORM_CONTENT_CE2_2_ID = uuid.UUID("30000000-0000-4000-8000-00000000001b")
PLATFORM_CONTENT_CE2_3_ID = uuid.UUID("30000000-0000-4000-8000-00000000001c")
PLATFORM_CONTENT_3EME_3_ID = uuid.UUID("30000000-0000-4000-8000-00000000001d")
# CM2 (Leila) et Terminale (Sara) n'avaient AUCUN contenu publié → bibliothèques
# vides. Ajout d'un fonds par niveau (math / langues / sciences) pour que chaque
# classe de démo ait une bibliothèque cohérente, affectée via le niveau.
PLATFORM_CONTENT_CM2_1_ID = uuid.UUID("30000000-0000-4000-8000-00000000001e")
PLATFORM_CONTENT_CM2_2_ID = uuid.UUID("30000000-0000-4000-8000-00000000001f")
PLATFORM_CONTENT_CM2_3_ID = uuid.UUID("30000000-0000-4000-8000-000000000020")
PLATFORM_CONTENT_TERM_1_ID = uuid.UUID("30000000-0000-4000-8000-000000000021")
PLATFORM_CONTENT_TERM_2_ID = uuid.UUID("30000000-0000-4000-8000-000000000022")
PLATFORM_CONTENT_TERM_3_ID = uuid.UUID("30000000-0000-4000-8000-000000000023")
PLATFORM_CONTENT_3_AUDIO_ID = uuid.UUID("30000000-0000-4000-8000-000000000016")
PLATFORM_CONTENT_5_AUDIO_ID = uuid.UUID("30000000-0000-4000-8000-000000000017")

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
PARENT_MANSOURI_ID = uuid.UUID("10000000-0000-4000-8000-000000000013")
PARENT_BERRADA_ID = uuid.UUID("10000000-0000-4000-8000-000000000014")
PARENT_CHRAIBI_ID = uuid.UUID("10000000-0000-4000-8000-000000000015")

CLASS_CP_ID = uuid.UUID("20000000-0000-4000-8000-000000000010")
CLASS_CE2_ID = uuid.UUID("20000000-0000-4000-8000-000000000011")
CLASS_CM2_ID = uuid.UUID("20000000-0000-4000-8000-000000000012")
CLASS_3EME_ID = uuid.UUID("20000000-0000-4000-8000-000000000013")
CLASS_TERM_ID = uuid.UUID("20000000-0000-4000-8000-000000000014")
# MEN coverage classes (one per content level_band that lacked a class)
CLASS_GS_ID = uuid.UUID("20000000-0000-4000-8000-000000000016")
CLASS_2AEP_ID = uuid.UUID("20000000-0000-4000-8000-000000000017")
CLASS_4AEP_ID = uuid.UUID("20000000-0000-4000-8000-000000000018")
CLASS_2AC_ID = uuid.UUID("20000000-0000-4000-8000-000000000019")
CLASS_TC_ID = uuid.UUID("20000000-0000-4000-8000-00000000001a")
CLASS_1BAC_ID = uuid.UUID("20000000-0000-4000-8000-00000000001b")

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
        "attendance_alerts",
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
        "micro_progress_logs",
        "micro_resources",
        "micro_payments",
        "micro_enrollments",
        "micro_groups",
        "micro_schools",
        "budget_transactions",
        "budget_requests",
        "budget_allocations",
        "school_budgets",
        "financial_snapshots",
        "cost_per_student",
        "cashflow_forecasts",
        "retention_metrics",
        "sync_checkpoints",
        "sync_conflicts",
        "sync_queue",
        "sync_devices",
        "installments",
        "payment_plans",
        "late_fee_policies",
        "sibling_discount_policies",
        "shared_review_comments",
        "upload_sessions",
        "device_tokens",
        "notification_preferences",
        "quiz_responses",
        "question_bank_items",
        "program_assignment_events",
        "timetable_generation_jobs",
        "timetable_constraints",
        "event_reminders",
        "event_rsvps",
        "events",
        "resource_ratings",
        "resources",
        "document_versions",
        "documents",
        "student_document_requirements",
        "data_exports",
        "report_jobs",
        "report_schedules",
        "event_reminder_preferences",
        "moroccan_holidays",
        "program_equivalences",
        "program_versions",
        "programs",
        "eligibility_rules",
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
            school_type="formal",
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
                "design_mode": "formal",
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
            school_type="formal",
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
                "design_mode": "formal",
                "timezone": "Africa/Casablanca",
                "currency": "MAD",
                "supported_languages": ["fr", "ar"],
            },
        ),
        School(
            id=MICRO_SCHOOL_TENANT_ID,
            name="Petite Ecole des Orangers",
            name_ar="روضة البرتقال",
            code="MICRO-ORANGERS",
            massar_code=None,
            status="active",
            school_type="informal",
            address="Hay Orangers, Casablanca",
            city="Casablanca",
            region="Casablanca-Settat",
            phone="+212612345999",
            email="educateur.micro@ecole-benani.ma",
            website=None,
            max_students=40,
            max_teachers=3,
            subscription_plan="micro",
            timezone="Africa/Casablanca",
            default_language="fr",
            grading_scale="skills",
            settings={
                "design_mode": "informal",
                "timezone": "Africa/Casablanca",
                "currency": "MAD",
                "supported_languages": ["fr", "ar"],
                "informal": True,
            },
        ),
    ]
    session.add_all(schools)
    await session.flush()
    print("  [School]    3 schools")


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
            full_name="Hajar Cherkaoui",
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
            email="omar.alaoui@ecole-benani.ma",
            full_name="Omar Alaoui",
            password_hash=_hash("student123"),
            status="active",
            school_id=SCHOOL_ID,
        ),
        User(
            id=SUPERADMIN_ID,
            email="superadmin@ecole-platform.ma",
            full_name="Nawfal RAZOUK",
            password_hash=_hash("superadmin123"),
            status="active",
            school_id=SCHOOL_ID,
        ),
        User(
            id=CONTENT_MGR_ID,
            email="cms@ecole-platform.ma",
            full_name="Khawla RAZOUK",
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
        code="1AC-A",
        academic_year_id=YEAR_ID,
        name="1ère Année Collège - A",
        level_band="1AC",
        cycle="college",
    )
    c6b = Class(
        id=CLASS_6B_ID,
        school_id=SCHOOL_ID,
        code="1AC-B",
        academic_year_id=YEAR_ID,
        name="1ère Année Collège - B",
        level_band="1AC",
        cycle="college",
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
        level_band="1AC",
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
        difficulty="MEDIUM",
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
        subject_line="Question sur les notes de Yassine",
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
        subject_line="Réunion pédagogique — préparation examens",
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
        # Parent 1 (Hassan Alaoui) -> Student 3 (Omar Alaoui) — second child
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
            level_band="1AC",
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
            level_band="1AC",
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
            level_band="1AC",
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
            level_band="1AC",
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
            # Re-niveau : l'alphabet arabe = niveau CP (était "primaire", orphelin —
            # aucune classe de démo n'utilise la bande "primaire"). Désormais
            # rattaché à CLASS_CP_ID → visible par l'élève CP (Amina).
            level_band="1AEP",
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
            level_band="1AC",
            language="fr",
            subject="activite_scientifique",
            description="Document audio sur les saisons, les equinoxes et les solstices.",
            status="published",
            origin="PLATFORM",
            created_by=CONTENT_MGR_ID,
        ),
        # --- Niveau CP (affecté à CLASS_CP_ID → vu par STUDENT_CP_ID) ---
        ContentItem(
            id=PLATFORM_CONTENT_CP_1_ID,
            school_id=None,
            title="Apprendre les lettres - L'alphabet francais",
            content_type="video",
            level_band="1AEP",
            language="fr",
            subject="french",
            description="Video pour decouvrir les lettres de l'alphabet et leurs sons, adaptee aux eleves de CP.",
            status="published",
            origin="PLATFORM",
            created_by=CONTENT_MGR_ID,
        ),
        ContentItem(
            id=PLATFORM_CONTENT_CP_2_ID,
            school_id=None,
            title="Compter de 1 a 20",
            content_type="pdf",
            level_band="1AEP",
            language="fr",
            subject="math",
            description="Fiche d'activites pour apprendre a compter de 1 a 20 avec des illustrations.",
            status="published",
            origin="PLATFORM",
            created_by=CONTENT_MGR_ID,
        ),
        # --- Niveau 3eme (affecté à CLASS_3EME_ID → vu par STUDENT_3EME_ID) ---
        ContentItem(
            id=PLATFORM_CONTENT_3EME_1_ID,
            school_id=None,
            title="Le theoreme de Pythagore",
            content_type="video",
            level_band="3AC",
            language="fr",
            subject="math",
            description="Demonstration et applications du theoreme de Pythagore pour le niveau 3eme.",
            status="published",
            origin="PLATFORM",
            created_by=CONTENT_MGR_ID,
        ),
        ContentItem(
            id=PLATFORM_CONTENT_3EME_2_ID,
            school_id=None,
            title="Analyse litteraire - La poesie engagee",
            content_type="pdf",
            level_band="3AC",
            language="fr",
            subject="french",
            description="Etude de textes de poesie engagee avec methodologie d'analyse pour le brevet.",
            status="published",
            origin="PLATFORM",
            created_by=CONTENT_MGR_ID,
        ),
        # --- Niveau CE2 / 3e année primaire (affecté à CLASS_CE2_ID) ---
        ContentItem(
            id=PLATFORM_CONTENT_CE2_1_ID,
            school_id=None,
            title="Les tables de multiplication",
            content_type="video",
            level_band="3AEP",
            language="fr",
            subject="math",
            description="Methode pour memoriser les tables de multiplication de 1 a 10, niveau CE2.",
            status="published",
            origin="PLATFORM",
            created_by=CONTENT_MGR_ID,
        ),
        ContentItem(
            id=PLATFORM_CONTENT_CE2_2_ID,
            school_id=None,
            title="Lecture - Contes du Maroc",
            content_type="pdf",
            level_band="3AEP",
            language="fr",
            subject="french",
            description="Recueil de contes traditionnels marocains avec questions de comprehension, niveau CE2.",
            status="published",
            origin="PLATFORM",
            created_by=CONTENT_MGR_ID,
        ),
        ContentItem(
            id=PLATFORM_CONTENT_CE2_3_ID,
            school_id=None,
            title="الخط العربي - الحروف المتصلة",
            content_type="pdf",
            level_band="3AEP",
            language="ar",
            subject="arabic",
            description="تمارين في الخط العربي لتعلم وصل الحروف، مستوى السنة الثالثة ابتدائي.",
            status="published",
            origin="PLATFORM",
            created_by=CONTENT_MGR_ID,
        ),
        # --- Niveau CM2 (affecté à CLASS_CM2_ID → vu par STUDENT_CM2_ID / Leila) ---
        ContentItem(
            id=PLATFORM_CONTENT_CM2_1_ID,
            school_id=None,
            title="Les nombres decimaux",
            content_type="video",
            level_band="6AEP",
            language="fr",
            subject="math",
            description="Comprendre, lire et comparer les nombres decimaux ; addition et soustraction, niveau CM2.",
            status="published",
            origin="PLATFORM",
            created_by=CONTENT_MGR_ID,
        ),
        ContentItem(
            id=PLATFORM_CONTENT_CM2_2_ID,
            school_id=None,
            title="Le corps humain - La digestion",
            content_type="video",
            level_band="6AEP",
            language="fr",
            subject="activite_scientifique",
            description="Le trajet des aliments et le role des organes de la digestion, niveau CM2.",
            status="published",
            origin="PLATFORM",
            created_by=CONTENT_MGR_ID,
        ),
        ContentItem(
            id=PLATFORM_CONTENT_CM2_3_ID,
            school_id=None,
            title="القراءة - نصوص مغربية",
            content_type="pdf",
            level_band="6AEP",
            language="ar",
            subject="arabic",
            description="نصوص قرائية من التراث المغربي مع أسئلة الفهم، مستوى السنة السادسة ابتدائي.",
            status="published",
            origin="PLATFORM",
            created_by=CONTENT_MGR_ID,
        ),
        # --- Niveau Terminale (affecté à CLASS_TERM_ID → vu par STUDENT_TERM_ID / Sara) ---
        ContentItem(
            id=PLATFORM_CONTENT_TERM_1_ID,
            school_id=None,
            title="Les limites de fonctions",
            content_type="video",
            level_band="2BAC",
            language="fr",
            subject="math",
            description="Notion de limite, limites usuelles et formes indeterminees, niveau Terminale.",
            status="published",
            origin="PLATFORM",
            created_by=CONTENT_MGR_ID,
        ),
        ContentItem(
            id=PLATFORM_CONTENT_TERM_2_ID,
            school_id=None,
            title="La dissertation philosophique - Methode",
            content_type="pdf",
            level_band="2BAC",
            language="fr",
            subject="philosophy",
            description="Methodologie de la dissertation : problematisation, plan, argumentation, niveau Terminale.",
            status="published",
            origin="PLATFORM",
            created_by=CONTENT_MGR_ID,
        ),
        ContentItem(
            id=PLATFORM_CONTENT_TERM_3_ID,
            school_id=None,
            title="Physique - Les ondes mecaniques",
            content_type="video",
            level_band="2BAC",
            language="fr",
            subject="physique_chimie",
            description="Propagation, periode et longueur d'onde des ondes mecaniques, niveau Terminale.",
            status="published",
            origin="PLATFORM",
            created_by=CONTENT_MGR_ID,
        ),
        # --- Complement 3eme : sciences (langue + matiere variees) ---
        ContentItem(
            id=PLATFORM_CONTENT_3EME_3_ID,
            school_id=None,
            title="Chimie - Les transformations chimiques",
            content_type="video",
            level_band="3AC",
            language="fr",
            subject="physique_chimie",
            description="Reactifs, produits et conservation de la masse lors d'une transformation chimique, niveau 3eme.",
            status="published",
            origin="PLATFORM",
            created_by=CONTENT_MGR_ID,
        ),
    ]
    session.add_all(platform_content)
    await session.flush()

    # NOTE: PDFs are intentionally seeded WITHOUT an audio_narration asset.
    # Narration for PDF content is produced at read-time by the in-code TTS
    # (web: useSpeech / speechSynthesis, mobile: TtsService / flutter_tts), so
    # no pre-recorded .mp3 file exists on disk. Registering an audio_narration
    # row here would point at a missing file (orphan → 404 in the reader).
    # Story audio (real recorded files under content/audio/<story>/) is kept.

    # Teacher's school-scoped content (used for submission)
    teacher_content = ContentItem(
        school_id=SCHOOL_ID,
        title="Exercices supplementaires - Fractions",
        content_type="pdf",
        level_band="1AC",
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
        level_band="1AC",
        language="fr",
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
        level_band="1AC",
        language="fr",
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
            subject="math",
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
            subject="french",
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
            subject="math",
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
            subject="french",
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
            subject="math",
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
            subject="french",
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
        applies_to_level="6eme",
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
            difficulty="EASY",
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
            difficulty="MEDIUM",
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
            difficulty="HARD",
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
            difficulty="EASY",
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
            difficulty="MEDIUM",
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
            difficulty="EASY",
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
            difficulty="EASY",
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

    # ── Letter puzzles (procedural jigsaw) ──
    # config: {letter, language, grid{rows,cols}, pieces[{word,emoji,image_url,audio_url}]}
    # 6 pieces → 2×3 grid. Arabic from maternelle; English gated to age >= 8.
    # (letter shapes are generated client-side, so config stays lightweight.)
    _letter_puzzles: list[tuple[str, str, str, int, int, list[tuple[str, str]]]] = [
        (
            "ar",
            "أ",
            "Alif",
            4,
            7,
            [
                ("أَرْنَبٌ", "🐰"),
                ("أَسَدٌ", "🦁"),
                ("أَنَانَاسٌ", "🍍"),
                ("أَفْعَى", "🐍"),
                ("أَزْهَارٌ", "🌸"),
                ("أُذُنٌ", "👂"),
            ],
        ),
        (
            "ar",
            "ب",
            "Baa",
            4,
            7,
            [
                ("بُرْتُقَالٌ", "🍊"),
                ("بَصَلٌ", "🧅"),
                ("بَيْتٌ", "🏠"),
                ("بِطِّيخٌ", "🍉"),
                ("بَاذِنْجَانٌ", "🍆"),
                ("بِطْرِيقٌ", "🐧"),
            ],
        ),
        (
            "ar",
            "ت",
            "Taa",
            4,
            7,
            [
                ("تُفَّاحٌ", "🍎"),
                ("تَاجٌ", "👑"),
                ("تِمْسَاحٌ", "🐊"),
                ("تُوتٌ", "🫐"),
                ("تِينٌ", "🪴"),
                ("تَلٌّ", "⛰️"),
            ],
        ),
        (
            "ar",
            "ث",
            "Thaa",
            4,
            7,
            [
                ("ثُعْبَانٌ", "🐍"),
                ("ثَلْجٌ", "❄️"),
                ("ثَوْرٌ", "🐂"),
                ("ثَعْلَبٌ", "🦊"),
                ("ثُومٌ", "🧄"),
                ("ثَوْبٌ", "👗"),
            ],
        ),
        (
            "ar",
            "ز",
            "Zay",
            4,
            7,
            [
                ("زَيْتُونٌ", "🫒"),
                ("زَيْتٌ", "🍶"),
                ("زَرَافَةٌ", "🦒"),
                ("زَهْرَةٌ", "🌸"),
                ("زَوْرَقٌ", "⛵"),
                ("زُجَاجٌ", "🥃"),
            ],
        ),
        (
            "fr",
            "A",
            "A",
            4,
            7,
            [
                ("Avion", "✈️"),
                ("Abeille", "🐝"),
                ("Arbre", "🌳"),
                ("Ananas", "🍍"),
                ("Âne", "🫏"),
                ("Arc", "🏹"),
            ],
        ),
        (
            "fr",
            "B",
            "B",
            4,
            7,
            [
                ("Banane", "🍌"),
                ("Ballon", "🎈"),
                ("Bateau", "⛵"),
                ("Bébé", "👶"),
                ("Bougie", "🕯️"),
                ("Bague", "💍"),
            ],
        ),
        (
            "fr",
            "C",
            "C",
            4,
            7,
            [
                ("Chat", "🐱"),
                ("Chien", "🐶"),
                ("Carotte", "🥕"),
                ("Citron", "🍋"),
                ("Clé", "🔑"),
                ("Cœur", "❤️"),
            ],
        ),
        (
            "fr",
            "M",
            "M",
            4,
            7,
            [
                ("Maison", "🏠"),
                ("Montagne", "⛰️"),
                ("Main", "✋"),
                ("Mangue", "🥭"),
                ("Moto", "🏍️"),
                ("Mouton", "🐑"),
            ],
        ),
        (
            "fr",
            "S",
            "S",
            4,
            7,
            [
                ("Soleil", "☀️"),
                ("Serpent", "🐍"),
                ("Singe", "🐒"),
                ("Sac", "🎒"),
                ("Souris", "🐭"),
                ("Salade", "🥗"),
            ],
        ),
        (
            "en",
            "A",
            "A (anglais)",
            8,
            12,
            [
                ("Apple", "🍎"),
                ("Ant", "🐜"),
                ("Airplane", "✈️"),
                ("Apricot", "🍑"),
                ("Arm", "💪"),
                ("Arrow", "🏹"),
            ],
        ),
        (
            "en",
            "B",
            "B (anglais)",
            8,
            12,
            [
                ("Ball", "⚽"),
                ("Banana", "🍌"),
                ("Bear", "🐻"),
                ("Book", "📖"),
                ("Bee", "🐝"),
                ("Boat", "⛵"),
            ],
        ),
        (
            "en",
            "C",
            "C (anglais)",
            8,
            12,
            [
                ("Cat", "🐱"),
                ("Car", "🚗"),
                ("Cake", "🍰"),
                ("Cloud", "☁️"),
                ("Cow", "🐄"),
                ("Crown", "👑"),
            ],
        ),
        (
            "en",
            "S",
            "S (anglais)",
            8,
            12,
            [
                ("Sun", "☀️"),
                ("Star", "⭐"),
                ("Snake", "🐍"),
                ("Ship", "🚢"),
                ("Sheep", "🐑"),
                ("Strawberry", "🍓"),
            ],
        ),
    ]
    for lang, letter, label, age_min, age_max, words in _letter_puzzles:
        configs.append(
            GameConfig(
                id=uuid.uuid5(
                    uuid.NAMESPACE_URL, f"game-config-letter-puzzle-{lang}-{label}"
                ),
                game_type="letter_puzzle",
                title=f"Letter Puzzle - {label}",
                title_ar=f"لغز الحرف - {letter}",
                title_fr=f"Puzzle de lettre - {label}",
                subject="literacy",
                difficulty="EASY",
                target_age_min=age_min,
                target_age_max=age_max,
                config={
                    "letter": letter,
                    "language": lang,
                    "grid": {"rows": 2, "cols": 3},
                    "letter_audio_url": None,
                    "pieces": [
                        {
                            "word": word,
                            "emoji": emoji,
                            "image_url": None,
                            "audio_url": None,
                        }
                        for (word, emoji) in words
                    ],
                },
                reward_stars=10,
                reward_xp=15,
                school_id=None,
                is_active=True,
            )
        )

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
        # Préscolaire (التعليم الأولي)
        Class(
            id=CLASS_GS_ID,
            school_id=SCHOOL_ID,
            code="GS-A",
            academic_year_id=YEAR_ID,
            name="Grande Section - A",
            level_band="GS",
            cycle="maternelle",
        ),
        # Primaire (الابتدائي)
        Class(
            id=CLASS_CP_ID,
            school_id=SCHOOL_ID,
            code="1AEP-A",
            academic_year_id=YEAR_ID,
            name="1ère Année Primaire - A",
            level_band="1AEP",
            cycle="primaire",
        ),
        Class(
            id=CLASS_2AEP_ID,
            school_id=SCHOOL_ID,
            code="2AEP-A",
            academic_year_id=YEAR_ID,
            name="2ème Année Primaire - A",
            level_band="2AEP",
            cycle="primaire",
        ),
        Class(
            id=CLASS_CE2_ID,
            school_id=SCHOOL_ID,
            code="3AEP-A",
            academic_year_id=YEAR_ID,
            name="3ème Année Primaire - A",
            level_band="3AEP",
            cycle="primaire",
        ),
        Class(
            id=CLASS_4AEP_ID,
            school_id=SCHOOL_ID,
            code="4AEP-A",
            academic_year_id=YEAR_ID,
            name="4ème Année Primaire - A",
            level_band="4AEP",
            cycle="primaire",
        ),
        Class(
            id=CLASS_CM2_ID,
            school_id=SCHOOL_ID,
            code="6AEP-A",
            academic_year_id=YEAR_ID,
            name="6ème Année Primaire - A",
            level_band="6AEP",
            cycle="primaire",
        ),
        # Collège (الإعدادي)
        Class(
            id=CLASS_2AC_ID,
            school_id=SCHOOL_ID,
            code="2AC-A",
            academic_year_id=YEAR_ID,
            name="2ème Année Collège - A",
            level_band="2AC",
            cycle="college",
        ),
        Class(
            id=CLASS_3EME_ID,
            school_id=SCHOOL_ID,
            code="3AC-A",
            academic_year_id=YEAR_ID,
            name="3ème Année Collège - A",
            level_band="3AC",
            cycle="college",
        ),
        # Lycée (التأهيلي)
        Class(
            id=CLASS_TC_ID,
            school_id=SCHOOL_ID,
            code="TC-A",
            academic_year_id=YEAR_ID,
            name="Tronc Commun - A",
            level_band="TC",
            cycle="lycee",
        ),
        Class(
            id=CLASS_1BAC_ID,
            school_id=SCHOOL_ID,
            code="1BAC-A",
            academic_year_id=YEAR_ID,
            name="1ère Année Bac - A",
            level_band="1BAC",
            cycle="lycee",
        ),
        Class(
            id=CLASS_TERM_ID,
            school_id=SCHOOL_ID,
            code="2BAC-A",
            academic_year_id=YEAR_ID,
            name="2ème Année Bac - A",
            level_band="2BAC",
            cycle="lycee",
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
    # Niveaux officiels marocains (MEN). Le 2e champ reste le libellé d'affichage
    # (équivalent français usuel) ; le 1er champ est le code stocké (enum).
    # FK-critique : 1AEP↔CLASS_CP, 3AEP↔CLASS_CE2, 6AEP↔CLASS_CM2,
    # 1AC↔CLASS_6A, 3AC↔CLASS_3EME, 2BAC↔CLASS_TERM.
    level_specs = [
        (
            "GS",
            "Maternelle (GS)",
            4,
            5,
            [
                ("Les couleurs - Vidéo éducative", "video", "activite_scientifique", "fr"),
                ("Coloriage - Les animaux", "pdf", "art", "fr"),
            ],
        ),
        (
            "1AEP",
            "1AEP (CP)",
            6,
            6,
            [
                ("Apprendre à lire - Leçon 1", "video", "french", "fr"),
                ("Exercices d'écriture CP", "pdf", "french", "fr"),
            ],
        ),
        (
            "2AEP",
            "2AEP (CE1)",
            7,
            7,
            [
                ("Les additions - Cours", "video", "math", "fr"),
                ("Dictée CE1 - Semaine 1", "audio", "french", "fr"),
            ],
        ),
        (
            "3AEP",
            "3AEP (CE2)",
            8,
            8,
            [
                ("La multiplication - Introduction", "video", "math", "fr"),
                ("Sciences - Le corps humain", "pdf", "activite_scientifique", "fr"),
            ],
        ),
        (
            "4AEP",
            "4AEP (CM1)",
            9,
            9,
            [
                ("Fractions - Introduction", "video", "math", "fr"),
                ("Géographie du Maroc", "pdf", "histoire_geo", "fr"),
            ],
        ),
        (
            "6AEP",
            "6AEP (CM2)",
            10,
            10,
            [
                ("Préparation 6ème - Mathématiques", "video", "math", "fr"),
                ("Rédaction - Le conte", "pdf", "french", "fr"),
            ],
        ),
        (
            "2AC",
            "2AC (5ème)",
            11,
            11,
            [
                ("L'histoire du Maroc médiéval", "video", "histoire_geo", "fr"),
                ("Anglais - Unit 1 - Greetings", "pdf", "english", "en"),
            ],
        ),
        (
            "2AC",
            "2AC (4ème)",
            12,
            12,
            [
                ("Algèbre - Équations du premier degré", "video", "math", "fr"),
                ("Physique - Les forces", "pdf", "physique_chimie", "fr"),
            ],
        ),
        (
            "3AC",
            "3AC (3ème)",
            13,
            14,
            [
                ("Brevet blanc - Mathématiques", "pdf", "math", "fr"),
                ("SVT - La cellule et son rôle", "video", "svt", "fr"),
            ],
        ),
        (
            "TC",
            "Tronc commun (2nde)",
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
            "1BAC",
            "1BAC (1ère)",
            16,
            16,
            [
                ("BAC Français - Méthode du commentaire", "pdf", "french", "fr"),
                ("Chimie organique - Les alcanes", "video", "physique_chimie", "fr"),
            ],
        ),
        (
            "2BAC",
            "2BAC (Terminale)",
            17,
            18,
            [
                ("BAC Maths - Révisions intégrales", "video", "math", "fr"),
                ("BAC SVT - Génétique et hérédité", "pdf", "svt", "fr"),
            ],
        ),
    ]

    count = 0
    for level_band, level_label, age_min, age_max, items in level_specs:
        for title, content_type, subject, language in items:
            content_item = ContentItem(
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
            session.add(content_item)
            # PDFs are seeded without an audio_narration asset; narration is
            # produced at read-time by the in-code TTS (no .mp3 on disk).
            count += 1
    await session.flush()
    print(
        f"  [G8] {count} level-banded platform content items (GS → 2BAC)"
    )


async def seed_class_content_assignments(session: AsyncSession) -> None:
    """Assign level-appropriate content to the new classes (Phase G8)."""
    from sqlalchemy import select

    # Find all platform content for 6ème (1AC) math to assign to class 6A
    math_6eme = await session.execute(
        select(ContentItem).where(
            ContentItem.level_band == "1AC",
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
        ("GS", CLASS_GS_ID),
        ("1AEP", CLASS_CP_ID),
        ("2AEP", CLASS_2AEP_ID),
        ("3AEP", CLASS_CE2_ID),
        ("4AEP", CLASS_4AEP_ID),
        ("6AEP", CLASS_CM2_ID),
        ("2AC", CLASS_2AC_ID),
        ("3AC", CLASS_3EME_ID),
        ("TC", CLASS_TC_ID),
        ("1BAC", CLASS_1BAC_ID),
        ("2BAC", CLASS_TERM_ID),
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


async def normalize_student_class_levels(session: AsyncSession) -> None:
    """Keep student_profiles.class_level consistent with the MEN level_band of
    the class the student is actually enrolled in.

    The mobile app (parent home, student home, profile "Niveau …") reads
    class_level directly. Seed literals historically used legacy French grade
    labels ("6eme", "3eme", "CP", "Terminale"); this derives the MEN code from
    the enrollment so code ↔ level_band ↔ cycle ↔ class name stay aligned.
    Informal-education students (class_level like 'informal-%') and students
    without an enrolled class keep their existing value.
    """
    result = await session.execute(
        text(
            """
            UPDATE student_profiles AS sp
            SET class_level = c.level_band::text
            FROM enrollments e
            JOIN classes c ON c.id = e.class_id
            WHERE e.student_id = sp.user_id
              AND c.level_band IS NOT NULL
              AND (sp.class_level IS NULL OR sp.class_level NOT LIKE 'informal-%')
            """
        )
    )
    await session.flush()
    print(f"  [MEN] Normalized class_level on {result.rowcount} student profiles")


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
                level_band="1AC",
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
                level_band="6AEP",
                language="fr",
                subject="histoire_geo",
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


async def seed_demo_coverage_data(session: AsyncSession) -> None:
    """Fill demo-facing gaps so role tabs have coherent, non-empty data."""
    from datetime import time

    from sqlalchemy import select

    now = _now()

    # Parents for the remaining age-tier demo students.
    parent_specs = [
        (
            PARENT_MANSOURI_ID,
            "parent.mansouri@gmail.com",
            "Nadia Mansouri",
            "+212633333333",
            "mother",
            "IJ778899",
            "14 Rue Ibn Sina, Casablanca",
            "Pharmacienne",
            STUDENT_CM2_ID,
        ),
        (
            PARENT_BERRADA_ID,
            "parent.berrada@gmail.com",
            "Samir Berrada",
            "+212644444444",
            "father",
            "KL990011",
            "31 Rue Al Massira, Casablanca",
            "Ingénieur",
            STUDENT_3EME_ID,
        ),
        (
            PARENT_CHRAIBI_ID,
            "parent.chraibi@gmail.com",
            "Meryem Chraibi",
            "+212655555555",
            "mother",
            "MN223344",
            "6 Avenue Zerktouni, Casablanca",
            "Médecin",
            STUDENT_TERM_ID,
        ),
    ]
    for uid, email, full_name, phone, *_ in parent_specs:
        session.add(
            User(
                id=uid,
                email=email,
                full_name=full_name,
                phone=phone,
                password_hash=_hash("parent123"),
                status="active",
                school_id=SCHOOL_ID,
            )
        )
    await session.flush()

    for (
        uid,
        _email,
        _name,
        phone,
        relation,
        cin,
        address,
        job,
        child_id,
    ) in parent_specs:
        session.add(
            Membership(
                user_id=uid,
                school_id=SCHOOL_ID,
                role_code="PAR",
                status="active",
            )
        )
        session.add(
            ParentProfile(
                user_id=uid,
                school_id=SCHOOL_ID,
                relationship_type=relation,
                cin_number=cin,
                address=address,
                profession=job,
                emergency_phone=phone,
            )
        )
        session.add(
            ParentChildLink(
                parent_user_id=uid,
                child_user_id=child_id,
                school_id=SCHOOL_ID,
                status="active",
                linked_at=now - timedelta(days=12),
                linked_by=ADMIN_ID,
            )
        )
    await session.flush()

    # Make every age-tier class visible in teacher/director workflows.
    class_teacher_specs = [
        (CLASS_CP_ID, TEACHER_2_ID, "Lecture", "Salle CP"),
        (CLASS_CE2_ID, TEACHER_1_ID, "Mathématiques", "Salle CE2"),
        (CLASS_CM2_ID, TEACHER_2_ID, "Français", "Salle CM2"),
        (CLASS_3EME_ID, TEACHER_1_ID, "Mathématiques", "Salle 3A"),
        (CLASS_TERM_ID, TEACHER_1_ID, "Mathématiques", "Salle BAC"),
    ]
    for class_id, teacher_id, _subject, _room in class_teacher_specs:
        session.add(
            TeacherAssignment(
                school_id=SCHOOL_ID,
                teacher_id=teacher_id,
                class_id=class_id,
                period_id=PERIOD_2_ID,
            )
        )

    for index, (class_id, teacher_id, subject, room) in enumerate(class_teacher_specs):
        session.add(
            TimetableSlot(
                school_id=SCHOOL_ID,
                class_id=class_id,
                academic_year_id=YEAR_ID,
                day_of_week=index % 5,
                start_time=time(9, 0),
                end_time=time(10, 0),
                subject=subject,
                teacher_id=teacher_id,
                room=room,
                is_recurring=True,
            )
        )
        session.add(
            TimetableSlot(
                school_id=SCHOOL_ID,
                class_id=class_id,
                academic_year_id=YEAR_ID,
                day_of_week=(index + 2) % 5,
                start_time=time(11, 0),
                end_time=time(12, 0),
                subject="activite_scientifique" if index < 3 else "preparation_examen",
                teacher_id=teacher_id,
                room=room,
                is_recurring=True,
            )
        )

    # 3e champ = code niveau MEN (sert au libellé d'éval ET à la requête
    # content_items.level_band ci-dessous → doit être une valeur enum valide).
    age_students = [
        (STUDENT_CP_ID, CLASS_CP_ID, "1AEP", 16.5, "Très bien"),
        (STUDENT_CE2_ID, CLASS_CE2_ID, "3AEP", 15.2, "Bien"),
        (STUDENT_CM2_ID, CLASS_CM2_ID, "6AEP", 14.7, "Bien"),
        (STUDENT_3EME_ID, CLASS_3EME_ID, "3AC", 13.4, "Assez bien"),
        (STUDENT_TERM_ID, CLASS_TERM_ID, "2BAC", 15.8, "Très bien"),
    ]

    for index, (student_id, class_id, _level, average, mention) in enumerate(
        age_students
    ):
        session.add(
            StudentPeriodAverage(
                school_id=SCHOOL_ID,
                student_id=student_id,
                class_id=class_id,
                period_id=PERIOD_2_ID,
                weighted_average=average,
                mention=mention,
                class_rank=1,
                total_students=1,
                computed_at=now - timedelta(days=index + 1),
            )
        )

        att = AttendanceSession(
            class_id=class_id,
            period_id=PERIOD_2_ID,
            teacher_id=TEACHER_1_ID if index >= 1 else TEACHER_2_ID,
            school_id=SCHOOL_ID,
            session_date=date(2026, 4, 20 + index),
            slot="09:00-10:00",
        )
        session.add(att)
        await session.flush()
        session.add(
            AttendanceRecord(
                attendance_session_id=att.id,
                student_id=student_id,
                school_id=SCHOOL_ID,
                status="late" if index == 3 else "present",
                absence_reason=None,
            )
        )

        assessment = Assessment(
            class_id=class_id,
            teacher_id=TEACHER_1_ID if index >= 1 else TEACHER_2_ID,
            title=f"Évaluation diagnostique {_level}",
            due_at=now - timedelta(days=7 - index),
            total_points=20,
            status="published",
        )
        session.add(assessment)
        await session.flush()
        session.add(
            AssessmentResult(
                assessment_id=assessment.id,
                student_id=student_id,
                score=average,
                status="published",
            )
        )

    # Content progress per level so Student/Parent progress and shared review tabs show data.
    for student_id, _class_id, level, _average, _mention in age_students:
        result = await session.execute(
            select(ContentItem)
            .where(ContentItem.level_band == level)
            .order_by(ContentItem.title.asc())
            .limit(2)
        )
        for idx, content in enumerate(result.scalars().all()):
            session.add(
                ContentProgress(
                    student_id=student_id,
                    content_item_id=content.id,
                    status="completed" if idx == 0 else "in_progress",
                )
            )

    # Billing coverage for all parent demo accounts, including payment plans.
    billing_specs = [
        (PARENT_TAZI_ID, STUDENT_CP_ID, "CP", 1800.00),
        (PARENT_FASSI_ID, STUDENT_CE2_ID, "CE2", 2200.00),
        (PARENT_MANSOURI_ID, STUDENT_CM2_ID, "CM2", 2600.00),
        (PARENT_BERRADA_ID, STUDENT_3EME_ID, "3ème", 3000.00),
        (PARENT_CHRAIBI_ID, STUDENT_TERM_ID, "Terminale", 3500.00),
    ]
    for index, (parent_id, _student_id, level, amount) in enumerate(billing_specs):
        invoice = Invoice(
            school_id=SCHOOL_ID,
            parent_id=parent_id,
            period_id=PERIOD_2_ID,
            status="pending",
            total_amount=amount,
            currency="MAD",
            issued_date=date(2026, 5, 1),
            due_date=date(2026, 5, 30),
        )
        session.add(invoice)
        await session.flush()
        session.add(
            InvoiceItem(
                invoice_id=invoice.id,
                description=f"Scolarité et services — {level}",
                amount=amount,
                unit_price=amount,
                quantity=1,
                tva_rate=0,
                tva_amount=0,
                amount_ht=amount,
                amount_ttc=amount,
            )
        )
        plan = PaymentPlan(
            school_id=SCHOOL_ID,
            invoice_id=invoice.id,
            total_installments=3,
            status="active",
        )
        session.add(plan)
        await session.flush()
        installment_amount = round(amount / 3, 2)
        for number in range(1, 4):
            session.add(
                Installment(
                    plan_id=plan.id,
                    installment_number=number,
                    amount=installment_amount,
                    due_date=now + timedelta(days=(number - 1) * 20 + index),
                    paid_at=now - timedelta(days=2)
                    if number == 1 and index < 2
                    else None,
                    status="paid" if number == 1 and index < 2 else "pending",
                )
            )
        session.add(
            PaymentAttempt(
                school_id=SCHOOL_ID,
                invoice_id=invoice.id,
                parent_id=parent_id,
                idempotency_key=f"demo-coverage-{parent_id}",
                status="processing" if index == 0 else "pending",
            )
        )

    # Parent feed and notifications for the new family accounts.
    for parent_id, student_id, level, amount in billing_specs:
        session.add(
            ParentFeedItem(
                school_id=SCHOOL_ID,
                parent_id=parent_id,
                student_id=student_id,
                source_type="progress",
                source_ref=f"progress:{student_id}",
                title=f"Progression {level} mise à jour",
                body="Les contenus récents, notes et présences sont disponibles.",
            )
        )
        session.add(
            Notification(
                school_id=SCHOOL_ID,
                parent_id=parent_id,
                event_ref=f"billing:{student_id}",
                idempotency_key=f"demo-coverage-billing-{parent_id}",
                category="billing",
                priority="normal",
                title="Plan de paiement disponible",
                body=f"Un plan de paiement de {amount:.0f} MAD est prêt à consulter.",
                action_url="/billing/payment-plans",
                action_payload={"student_id": str(student_id)},
            )
        )

    await session.flush()
    print(
        "  [Demo Coverage] +3 parents, +5 payment plans, +10 timetable slots, "
        "+5 assessments/results, +5 averages, +content progress for all age-tier students"
    )


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
        await seed_onboarding_applications(session)
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
        await seed_auth_security_showcase(session)

        # ── Enhanced seeders (high-volume demo data) ──
        print("\n  [Enhanced] Seeding high-volume demo data:")
        await seed_enhanced_students(session)
        await seed_enhanced_invoices(session)
        await seed_payment_plans(session)
        await seed_billing_policies(session)
        await seed_rubrics(session)
        await seed_submission_files(session)
        await seed_question_bank(session)
        await seed_quiz_responses(session)
        await seed_grade_categories_and_averages(session)
        await seed_enhanced_attendance(session)
        await seed_absence_justifications(session)
        await seed_budget(session)
        await seed_financial_health(session)
        await seed_micro_school(session)
        await seed_sync_queue(session)
        await seed_men_compliance_extra(session)
        await seed_upload_sessions(session)
        await seed_shared_reviews(session)
        await seed_enhanced_messaging(session)
        await seed_enhanced_notifications(session)
        await seed_school_2_minimal(session)
        await seed_timetable_extras(session)
        await seed_program_assignment_events(session)
        await seed_demo_scenarios(session)
        await seed_demo_coverage_data(session)
        await seed_misc_empty_tables(session)

        # Run last: every student + enrollment now exists, so derive each
        # student_profiles.class_level from its enrolled class's MEN level_band.
        await normalize_student_class_levels(session)

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
| Parent (Mansouri) | `parent.mansouri@gmail.com` | `parent123` |
| Parent (Berrada) | `parent.berrada@gmail.com` | `parent123` |
| Parent (Chraibi) | `parent.chraibi@gmail.com` | `parent123` |
| Student 6eme (Yassine) | `yassine.alaoui@ecole-benani.ma` | `student123` |
| Student 6eme (Salma) | `salma.idrissi@ecole-benani.ma` | `student123` |
| Student 6eme (Omar) | `omar.alaoui@ecole-benani.ma` | `student123` |
| Student CP (Amina) | `amina.cp@ecole-benani.ma` | `student123` |
| Student CE2 (Karim) | `karim.ce2@ecole-benani.ma` | `student123` |
| Student CM2 (Leila) | `leila.cm2@ecole-benani.ma` | `student123` |
| Student 3eme (Mehdi) | `mehdi.3eme@ecole-benani.ma` | `student123` |
| Student Terminale (Sara) | `sara.terminale@ecole-benani.ma` | `student123` |
| Micro-school Educator (Said El Fassi) | `educateur.micro@ecole-benani.ma` | `teacher123` |
| Superadmin (Nawfal RAZOUK) | `superadmin@ecole-platform.ma` | `superadmin123` |
| Content Manager (Khawla RAZOUK) | `cms@ecole-platform.ma` | `content123` |
| Atlas Admin (Karim Naciri) | `admin@ecole-atlas.ma` | `admin123` |
| Atlas Teacher (Leila Saidi) | `prof@ecole-atlas.ma` | `teacher123` |
| Atlas Parent (Ahmed Lahlou) | `parent@ecole-atlas.ma` | `parent123` |
| Atlas Student (Youssef Lahlou) | `enfant@ecole-atlas.ma` | `student123` |

## Schools

| Name | Code | City | Status | Plan |
|------|------|------|--------|------|
| Ecole Benani | ECOLE-BENANI | Casablanca | active | premium |
| Ecole Atlas | ECOLE-ATLAS | Rabat | trial | trial |

## Classes

| Class | Level | Students |
|-------|-------|----------|
| 6eme A | 6eme | 8 students (Yassine, Salma, + 6 more) |
| 6eme B | 6eme | 6 students (Omar, + 5 more) |
| 5eme A | 5eme | 4 students |
| CP A | CP | Amina Tazi |
| CE2 A | CE2 | Karim Fassi |
| CM2 A | CM2 | Leila Mansouri |
| 3eme A | 3eme | Mehdi Berrada |
| Terminale A | Terminale | Sara Chraibi |

## Parent → Children

| Parent | Children |
|--------|----------|
| Parent Alaoui | Yassine Alaoui, Omar Alaoui |
| Parent Idrissi | Salma Idrissi |
| Fatima Tazi | Amina Tazi (CP) |
| Omar Fassi | Karim Fassi (CE2) |
| Nadia Mansouri | Leila Mansouri (CM2) |
| Samir Berrada | Mehdi Berrada (3ème) |
| Meryem Chraibi | Sara Chraibi (Terminale) |

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

Invoices: 23 total (pending, paid, failed, canceled) + payment proofs + webhook events
Payment Plans: 7 active plans with installments, including all age-tier demo families
Billing Policies: Sibling discount + Late fee policies configured

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

## Rubrics

2 rubrics: "Presentation orale — Mathematiques" (template) + "Redaction — Expression ecrite"
6 criteria, 18 levels, sample rubric scores on graded submissions

## Budget

1 micro-budget: 50,000 MAD (35k allocated, 15k remaining)
3 allocations, 2 requests, 4 transactions

## Financial Health

Retention rate: 95.83% | Cost/student: 2,800 MAD | Margin: 700 MAD
Cashflow forecasts: 3 months | Financial snapshots: 2 (Mar + Apr 2026)

## Micro-School

1 micro-school: "Petite Ecole des Orangers" (Casablanca)
2 groups, 4 enrollments, 4 payments, 3 resources, 6 progress logs

## Attendance

~45 sessions across 3 weeks (6A, 6B, 5A)
2 attendance alerts triggered for high absence rates
2 absence justifications (1 pending, 1 approved)

## Messaging

5 conversations (2 direct + 3 group)
~18 messages total, 10+ read receipts

## Calendar

8 events (portes ouvertes, examens, excursion, fete de fin d'annee...)
9 RSVPs, 5 reminders

## Documents

4 documents (bulletins, certificats, autorisations) + 2 versions
5 shared resources (lesson plans, worksheets, exam templates)

## Reporting

3 schedules (assiduite, notes, financier)
6 jobs (completed, pending, generating, failed)

## Notifications

12+ notifications across all categories (academic, billing, attendance, system, announcement)
20+ delivery records (email + in-app)

## Multi-Tenant

School 1 (Ecole Benani): Full dataset (~90% table coverage)
School 2 (Ecole Atlas): Minimal demo data (4 loginable users, 1 class, 1 invoice, 1 announcement)

## Auth & Security Showcase

Seeded for profile/security demos:
- Register demo invitation codes: `PARDMO01` (parent), `TCHDMO02` (teacher), `USEDPAR3` (already consumed parent code)
- Verified emails for core demo accounts + verified phone for Parent Alaoui
- Login history: success, new device, failed attempt
- Known devices and known locations, including one suspicious example
- Failed login attempt for account-lockout demo
- Password history rows for password-change validation
- Pending recovery request for password-reset flow context
- Mock OAuth link for Yassine (Google) and mock WebAuthn/passkey row for Admin

## Feature Toggles

gamification, rewards, skill_passport, difficulty_adaptation, parent_dashboard_v2 — all **enabled**

## Timetable

6A/6B base timetable + extra slots for CP, CE2, CM2, 3ème and Terminale.
Every demo student has at least one class slot and attendance record for timetable/progress demos.

## Content Library

6 platform CMS items + 24 level-banded items (maternelle → Terminale) + 2 CMS drafts

## Fixture Files

PDF/Excel/JPG stubs in `backend/app/templates/fixtures/`:
- sample_bulletin.pdf, sample_worksheet_math.pdf, sample_submission_yassine.pdf
- sample_coloring_page.pdf, sample_national_id.jpg
- sample_invoice_template.xlsx, sample_attendance_export.xlsx

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
    print("    Atlas ADM:  admin@ecole-atlas.ma / admin123")


# ====================== merged from seed_enhanced.py ======================
"""Enhanced seed data for convincing multi-persona demo coverage.

Covers previously unseeded or under-seeded tables:
- Rubrics, question bank, quiz responses, submission files
- Budget / micro-budgets, financial health metrics
- Micro-schools (informal education)
- Attendance alerts, absence justifications, reviews
- Enhanced messaging, notifications, feed
- Compliance reports, curriculum mappings
- Sync queue, upload sessions
- Payment plans, billing policies
- School 2 minimal multi-tenant data

Called from app.seed.main() after core seeders.
"""


import random
import uuid
import hashlib
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password

# ── LMS ──
from app.models.lms import (
    ContentItemAsset,
    GradeCategory,
    QuestionBankItem,
    QuizResponse,
    Rubric,
    RubricCriterion,
    RubricLevel,
    RubricScore,
    StudentPeriodAverage,
    SubmissionFile,
)

# ── ERP ──
from app.models.erp import (
    AbsenceJustification,
    AcademicYear,
    AttendanceAlert,
    AttendanceRecord,
    AttendanceSession,
    Class,
    Enrollment,
    JustificationReview,
    JustificationStatus,
    Period,
    ProgramAssignmentEvent,
    TeacherAssignment,
    TimetableConstraint,
    TimetableGenerationJob,
    TimetableJobStatus,
)

# ── Budget ──
from app.models.budget import (
    BudgetAllocation,
    BudgetAllocationStatus,
    BudgetRequest,
    BudgetRequestStatus,
    BudgetTransaction,
    BudgetTransactionType,
    SchoolBudget,
    SchoolBudgetStatus,
)

# ── Financial Health ──
from app.models.financial_health import (
    CashflowForecast,
    CostPerStudent,
    FinancialSnapshot,
    RetentionMetric,
)

# ── Micro School ──
from app.models.micro_school import (
    MicroEnrollment,
    MicroEnrollmentStatus,
    MicroGroup,
    MicroPayment,
    MicroPaymentPeriodType,
    MicroPaymentStatus,
    MicroProgressLog,
    MicroResource,
    MicroResourceType,
    MicroSchool,
    MicroSchoolStatus,
    MicroSchoolType,
)

# ── Sync Queue ──
from app.models.sync_queue import (
    SyncCheckpoint,
    SyncConflict,
    SyncConflictResolution,
    SyncDevice,
    SyncDeviceType,
    SyncQueue,
    SyncQueueOperation,
    SyncQueueStatus,
)

# ── MEN Compliance ──
from app.models.men_compliance import (
    ComplianceReport,
    CurriculumMapping,
    MenCurriculum,
    MenObjective,
)

# ── Billing ──
from app.models.billing import (
    Installment,
    Invoice,
    InvoiceItem,
    LateFeePolicy,
    PaymentAttempt,
    PaymentAttemptStatus,
    PaymentPlan,
    ProviderWebhookEvent,
    SiblingDiscountPolicy,
    WebhookEventStatus,
)

# ── COM ──
from app.models.com import (
    Announcement,
    Conversation,
    ConversationParticipant,
    Message,
    MessageReadReceipt,
    Notification,
    NotificationDelivery,
    SharedReviewComment,
)

# ── Uploads ──
from app.models.uploads import UploadSession

# ── IAM / School ──
from app.models.iam import (
    AccountRecoveryRequest,
    AdminProfile,
    ContentManagerProfile,
    FailedLoginAttempt,
    KnownDevice,
    KnownLocation,
    LoginHistory,
    Membership,
    OAuthAccount,
    ParentChildLink,
    ParentProfile,
    PasswordHistory,
    RecoveryStatus,
    StudentProfile,
    TeacherProfile,
    User,
    WebAuthnCredential,
)

# ── Shared constants from seed.py (duplicated to avoid circular import) ──
SCHOOL_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")
SCHOOL_ID_2 = uuid.UUID("00000000-0000-4000-8000-000000000002")
MICRO_SCHOOL_TENANT_ID = uuid.UUID("00000000-0000-4000-8000-000000000003")
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
YEAR_ID = uuid.UUID("20000000-0000-4000-8000-000000000001")
PERIOD_1_ID = uuid.UUID("20000000-0000-4000-8000-000000000002")
PERIOD_2_ID = uuid.UUID("20000000-0000-4000-8000-000000000003")
CLASS_6A_ID = uuid.UUID("20000000-0000-4000-8000-000000000004")
CLASS_6B_ID = uuid.UUID("20000000-0000-4000-8000-000000000005")
CLASS_CP_ID = uuid.UUID("20000000-0000-4000-8000-000000000010")
CLASS_CE2_ID = uuid.UUID("20000000-0000-4000-8000-000000000011")
CLASS_CM2_ID = uuid.UUID("20000000-0000-4000-8000-000000000012")
CLASS_3EME_ID = uuid.UUID("20000000-0000-4000-8000-000000000013")
CLASS_TERM_ID = uuid.UUID("20000000-0000-4000-8000-000000000014")
COURSE_MATH_ID = uuid.UUID("30000000-0000-4000-8000-000000000001")
COURSE_FR_ID = uuid.UUID("30000000-0000-4000-8000-000000000002")
ASSIGN_1_ID = uuid.UUID("30000000-0000-4000-8000-000000000003")
QUIZ_MATH_ID = uuid.UUID("30000000-0000-4000-8000-000000000020")
QUIZ_FR_ID = uuid.UUID("30000000-0000-4000-8000-000000000021")
PLATFORM_CONTENT_FRACTIONS_VIDEO_ID = uuid.UUID("30000000-0000-4000-8000-000000000010")
PLATFORM_CONTENT_TRIANGLES_PDF_ID = uuid.UUID("30000000-0000-4000-8000-000000000012")

# New IDs for enhanced seed
STUDENT_4_ID = uuid.UUID("10000000-0000-4000-8000-000000000020")
STUDENT_5_ID = uuid.UUID("10000000-0000-4000-8000-000000000021")
STUDENT_6_ID = uuid.UUID("10000000-0000-4000-8000-000000000022")
STUDENT_7_ID = uuid.UUID("10000000-0000-4000-8000-000000000023")
STUDENT_8_ID = uuid.UUID("10000000-0000-4000-8000-000000000024")
STUDENT_9_ID = uuid.UUID("10000000-0000-4000-8000-000000000025")
STUDENT_10_ID = uuid.UUID("10000000-0000-4000-8000-000000000026")
STUDENT_11_ID = uuid.UUID("10000000-0000-4000-8000-000000000027")
STUDENT_12_ID = uuid.UUID("10000000-0000-4000-8000-000000000028")
STUDENT_13_ID = uuid.UUID("10000000-0000-4000-8000-000000000029")
STUDENT_14_ID = uuid.UUID("10000000-0000-4000-8000-00000000002a")
STUDENT_15_ID = uuid.UUID("10000000-0000-4000-8000-00000000002b")
CLASS_5EME_ID = uuid.UUID("20000000-0000-4000-8000-000000000015")
MICRO_PARENT_1_ID = uuid.UUID("10000000-0000-4000-8000-000000000032")
MICRO_PARENT_2_ID = uuid.UUID("10000000-0000-4000-8000-000000000033")
MICRO_STUDENT_CRECHE_ID = uuid.UUID("10000000-0000-4000-8000-000000000034")
MICRO_STUDENT_MSID_ID = uuid.UUID("10000000-0000-4000-8000-000000000035")
MICRO_STUDENT_KOUTTAB_ID = uuid.UUID("10000000-0000-4000-8000-000000000036")
MICRO_STUDENT_PRESCHOOL_ID = uuid.UUID("10000000-0000-4000-8000-000000000037")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _demo_password_hash(password: str) -> str:
    """Hash demo passwords with the same bcrypt helper used by production auth."""
    return hash_password(password)


def _invitation_code_hash(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


async def seed_auth_security_showcase(session: AsyncSession) -> None:
    """Seed auth/security records used by login, register, profile, and security demos."""
    now = _now()

    main_users = [
        (ADMIN_ID, SCHOOL_ID),
        (DIRECTOR_ID, SCHOOL_ID),
        (TEACHER_1_ID, SCHOOL_ID),
        (PARENT_1_ID, SCHOOL_ID),
        (STUDENT_1_ID, SCHOOL_ID),
        (CONTENT_MGR_ID, SCHOOL_ID),
    ]

    for user_id, _school_id in main_users:
        user = await session.get(User, user_id)
        if user is not None:
            user.email_verified_at = now - timedelta(days=30)

    parent = await session.get(User, PARENT_1_ID)
    if parent is not None:
        parent.phone_verified_at = now - timedelta(days=20)

    session.add_all(
        [
            LoginHistory(
                user_id=ADMIN_ID,
                school_id=SCHOOL_ID,
                ip_address="196.12.221.10",
                user_agent="Mozilla/5.0 Demo Chrome",
                device_name="Admin MacBook Pro",
                device_fingerprint="admin-device-main",
                city="Casablanca",
                country="MA",
                success=True,
                is_new_device=False,
            ),
            LoginHistory(
                user_id=TEACHER_1_ID,
                school_id=SCHOOL_ID,
                ip_address="196.12.221.20",
                user_agent="Mozilla/5.0 Demo Chrome",
                device_name="Teacher Windows Laptop",
                device_fingerprint="teacher-device-main",
                city="Casablanca",
                country="MA",
                success=True,
                is_new_device=True,
            ),
            LoginHistory(
                user_id=PARENT_1_ID,
                school_id=SCHOOL_ID,
                ip_address="105.158.10.22",
                user_agent="EcolePlatformMobile/1.0",
                device_name="Hassan iPhone",
                device_fingerprint="parent-device-mobile",
                city="Casablanca",
                country="MA",
                success=True,
                is_new_device=False,
            ),
            LoginHistory(
                user_id=STUDENT_1_ID,
                school_id=SCHOOL_ID,
                ip_address="105.158.10.23",
                user_agent="EcolePlatformMobile/1.0",
                device_name="Yassine Tablet",
                device_fingerprint="student-device-tablet",
                city="Casablanca",
                country="MA",
                success=True,
                is_new_device=False,
            ),
            LoginHistory(
                user_id=ADMIN_ID,
                school_id=SCHOOL_ID,
                ip_address="203.0.113.44",
                user_agent="Mozilla/5.0 Unknown",
                device_name="Unknown browser",
                device_fingerprint="unknown-device",
                city="Unknown",
                country="ZZ",
                success=False,
                failure_reason="wrong_password",
                is_new_device=True,
            ),
        ]
    )

    session.add_all(
        [
            KnownDevice(
                user_id=ADMIN_ID,
                school_id=SCHOOL_ID,
                device_fingerprint="admin-device-main",
                device_name="Admin MacBook Pro",
                user_agent="Mozilla/5.0 Demo Chrome",
                last_seen_at=now - timedelta(hours=2),
                is_suspicious=False,
            ),
            KnownDevice(
                user_id=PARENT_1_ID,
                school_id=SCHOOL_ID,
                device_fingerprint="parent-device-mobile",
                device_name="Hassan iPhone",
                user_agent="EcolePlatformMobile/1.0",
                last_seen_at=now - timedelta(hours=8),
                is_suspicious=False,
            ),
            KnownDevice(
                user_id=ADMIN_ID,
                school_id=SCHOOL_ID,
                device_fingerprint="unknown-device",
                device_name="Unknown browser",
                user_agent="Mozilla/5.0 Unknown",
                last_seen_at=now - timedelta(days=1),
                is_suspicious=True,
            ),
            KnownLocation(
                user_id=ADMIN_ID,
                school_id=SCHOOL_ID,
                ip_address="196.12.221.10",
                country_code="MA",
                city="Casablanca",
                region="Casablanca-Settat",
                last_seen_at=now - timedelta(hours=2),
                is_suspicious=False,
            ),
            KnownLocation(
                user_id=ADMIN_ID,
                school_id=SCHOOL_ID,
                ip_address="203.0.113.44",
                country_code="ZZ",
                city="Unknown",
                region="Unknown",
                last_seen_at=now - timedelta(days=1),
                is_suspicious=True,
            ),
            FailedLoginAttempt(
                user_id=ADMIN_ID,
                school_id=SCHOOL_ID,
                email="admin@ecole-benani.ma",
                ip_address="203.0.113.44",
                user_agent="Mozilla/5.0 Unknown",
                failure_reason="wrong_password",
            ),
        ]
    )

    session.add_all(
        [
            PasswordHistory(
                user_id=ADMIN_ID,
                school_id=SCHOOL_ID,
                password_hash=_demo_password_hash("OldAdmin123!"),
            ),
            PasswordHistory(
                user_id=TEACHER_1_ID,
                school_id=SCHOOL_ID,
                password_hash=_demo_password_hash("OldTeacher123!"),
            ),
            PasswordHistory(
                user_id=PARENT_1_ID,
                school_id=SCHOOL_ID,
                password_hash=_demo_password_hash("OldParent123!"),
            ),
            AccountRecoveryRequest(
                user_id=PARENT_1_ID,
                school_id=SCHOOL_ID,
                status=RecoveryStatus.PENDING.value,
                attempts=1,
                expires_at=now + timedelta(minutes=15),
            ),
        ]
    )

    session.add_all(
        [
            WebAuthnCredential(
                user_id=ADMIN_ID,
                school_id=SCHOOL_ID,
                credential_id="demo-admin-passkey-credential",
                public_key="demo-public-key-for-ui-only",
                sign_count=12,
                device_type="multi_device",
                device_name="Admin MacBook Touch ID",
                transports="internal",
                is_backup=False,
                is_active=True,
            ),
            OAuthAccount(
                user_id=STUDENT_1_ID,
                school_id=SCHOOL_ID,
                provider="google",
                provider_user_id="demo-google-yassine-alaoui",
                provider_email="yassine.alaoui@ecole-benani.ma",
                access_token="demo-access-token",
                refresh_token=None,
                token_expires_at=now + timedelta(hours=1),
            ),
        ]
    )

    print(
        "    Auth/Security: login history, known devices/locations, failed login, "
        "password history, recovery request, OAuth link, WebAuthn mock"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Enhanced Students (+15 across 6A, 6B, new 5eme A)
# ═══════════════════════════════════════════════════════════════════════════════


async def seed_enhanced_students(session: AsyncSession) -> None:
    """Add 15 more students to fill classes realistically (8-10 per class)."""
    from app.models.erp import AcademicYear

    # Ensure academic year exists
    year = await session.get(AcademicYear, YEAR_ID)
    if year is None:
        return

    # Create 5ème année primaire class (MEN: 5AEP)
    c5a = Class(
        id=CLASS_5EME_ID,
        school_id=SCHOOL_ID,
        code="5AEP-A",
        academic_year_id=YEAR_ID,
        name="5ème Année Primaire - A",
        level_band="5AEP",
        cycle="primaire",
    )
    session.add(c5a)
    await session.flush()

    new_students = [
        # 6A additions (6 more → total 8)
        (
            STUDENT_4_ID,
            "nadia.bennani@ecole-benani.ma",
            "Nadia Bennani",
            "STD-2025-020",
            date(2013, 2, 10),
        ),
        (
            STUDENT_5_ID,
            "kamal.fassi@ecole-benani.ma",
            "Kamal Fassi",
            "STD-2025-021",
            date(2013, 6, 15),
        ),
        (
            STUDENT_6_ID,
            "laila.tazi@ecole-benani.ma",
            "Laila Tazi",
            "STD-2025-022",
            date(2013, 9, 20),
        ),
        (
            STUDENT_7_ID,
            "amine.raji@ecole-benani.ma",
            "Amine Raji",
            "STD-2025-023",
            date(2013, 11, 5),
        ),
        (
            STUDENT_8_ID,
            "soumaya.daoudi@ecole-benani.ma",
            "Soumaya Daoudi",
            "STD-2025-024",
            date(2013, 4, 8),
        ),
        (
            STUDENT_9_ID,
            "younes.elamrani@ecole-benani.ma",
            "Younes El Amrani",
            "STD-2025-025",
            date(2013, 7, 30),
        ),
        # 6B additions (5 more → total 6)
        (
            STUDENT_10_ID,
            "hafsa.moussaoui@ecole-benani.ma",
            "Hafsa Moussaoui",
            "STD-2025-026",
            date(2013, 1, 12),
        ),
        (
            STUDENT_11_ID,
            "brahim.ouazzani@ecole-benani.ma",
            "Brahim Ouazzani",
            "STD-2025-027",
            date(2013, 3, 25),
        ),
        (
            STUDENT_12_ID,
            "hiba.chafik@ecole-benani.ma",
            "Hiba Chafik",
            "STD-2025-028",
            date(2013, 8, 18),
        ),
        (
            STUDENT_13_ID,
            "mehdi.lahlou@ecole-benani.ma",
            "Mehdi Lahlou",
            "STD-2025-029",
            date(2013, 10, 3),
        ),
        (
            STUDENT_14_ID,
            "rachida.benkirane@ecole-benani.ma",
            "Rachida Benkirane",
            "STD-2025-030",
            date(2013, 12, 14),
        ),
        # 5A (4 students)
        (
            STUDENT_15_ID,
            "adam.sahli@ecole-benani.ma",
            "Adam Sahli",
            "STD-2025-031",
            date(2014, 5, 22),
        ),
    ]

    for uid, email, full_name, student_no, dob in new_students:
        session.add(
            User(
                id=uid,
                email=email,
                full_name=full_name,
                password_hash=_demo_password_hash("student123"),
                status="active",
                school_id=SCHOOL_ID,
            )
        )
    await session.flush()

    for index, (uid, email, full_name, student_no, dob) in enumerate(new_students):
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
                gender="female"
                if full_name.split()[0]
                in ["Nadia", "Laila", "Soumaya", "Hafsa", "Hiba", "Rachida"]
                else "male",
                class_level="6eme"
                if uid
                in [
                    STUDENT_4_ID,
                    STUDENT_5_ID,
                    STUDENT_6_ID,
                    STUDENT_7_ID,
                    STUDENT_8_ID,
                    STUDENT_9_ID,
                ]
                else (
                    "6eme"
                    if uid
                    in [
                        STUDENT_10_ID,
                        STUDENT_11_ID,
                        STUDENT_12_ID,
                        STUDENT_13_ID,
                        STUDENT_14_ID,
                    ]
                    else "5eme"
                ),
                nationality="Marocaine",
            )
        )
        # NOTE: these are roster-fill classmates (varied family names) used only
        # to give classes a realistic size. They are intentionally NOT linked to
        # the demo parents — otherwise a single parent (e.g. Alaoui) ends up with
        # 8 "children" of different surnames. Real parent-child links are seeded
        # explicitly in seed_parent_child_links (Hassan Alaoui -> Yassine + Omar).

    # Enrollments
    class_6a = [
        STUDENT_4_ID,
        STUDENT_5_ID,
        STUDENT_6_ID,
        STUDENT_7_ID,
        STUDENT_8_ID,
        STUDENT_9_ID,
    ]
    class_6b = [
        STUDENT_10_ID,
        STUDENT_11_ID,
        STUDENT_12_ID,
        STUDENT_13_ID,
        STUDENT_14_ID,
    ]
    class_5a = [STUDENT_15_ID]

    for student_id in class_6a:
        session.add(
            Enrollment(
                student_id=student_id,
                class_id=CLASS_6A_ID,
                period_id=PERIOD_2_ID,
                school_id=SCHOOL_ID,
                status="active",
            )
        )
    for student_id in class_6b:
        session.add(
            Enrollment(
                student_id=student_id,
                class_id=CLASS_6B_ID,
                period_id=PERIOD_2_ID,
                school_id=SCHOOL_ID,
                status="active",
            )
        )
    for student_id in class_5a:
        session.add(
            Enrollment(
                student_id=student_id,
                class_id=CLASS_5EME_ID,
                period_id=PERIOD_2_ID,
                school_id=SCHOOL_ID,
                status="active",
            )
        )

    # Teacher assignment for 5A
    session.add(
        TeacherAssignment(
            teacher_id=TEACHER_1_ID,
            class_id=CLASS_5EME_ID,
            period_id=PERIOD_2_ID,
            school_id=SCHOOL_ID,
        )
    )

    await session.flush()
    print("    Enhanced: +15 students (6A→8, 6B→6, 5A→4)")


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Enhanced Invoices (+12, all statuses, with proofs & webhooks)
# ═══════════════════════════════════════════════════════════════════════════════


async def seed_enhanced_invoices(session: AsyncSession) -> None:
    """Add 12 more invoices across all statuses, with payment proofs and webhooks."""
    invoice_specs = [
        # (status, issued, due, amount, parent_id, fee_structure_id)
        ("pending", date(2026, 3, 1), date(2026, 3, 31), 1500.00, PARENT_1_ID, None),
        ("pending", date(2026, 4, 1), date(2026, 4, 30), 3500.00, PARENT_1_ID, None),
        ("paid", date(2026, 1, 1), date(2026, 1, 31), 3500.00, PARENT_1_ID, None),
        ("paid", date(2026, 2, 1), date(2026, 2, 28), 3500.00, PARENT_2_ID, None),
        ("failed", date(2026, 1, 1), date(2026, 1, 31), 800.00, PARENT_1_ID, None),
        ("failed", date(2026, 2, 1), date(2026, 2, 28), 1200.00, PARENT_2_ID, None),
        ("canceled", date(2025, 11, 1), date(2025, 11, 30), 500.00, PARENT_1_ID, None),
        ("canceled", date(2025, 10, 1), date(2025, 10, 31), 300.00, PARENT_2_ID, None),
        ("pending", date(2026, 3, 1), date(2026, 3, 31), 2000.00, PARENT_2_ID, None),
        ("paid", date(2025, 9, 1), date(2025, 9, 30), 3500.00, PARENT_1_ID, None),
        ("paid", date(2025, 10, 1), date(2025, 10, 31), 3500.00, PARENT_2_ID, None),
        ("pending", date(2026, 5, 1), date(2026, 5, 31), 3500.00, PARENT_1_ID, None),
    ]

    created_invoices: list[Invoice] = []
    for status, issued, due, amount, parent_id, fee_id in invoice_specs:
        inv = Invoice(
            school_id=SCHOOL_ID,
            parent_id=parent_id,
            period_id=PERIOD_2_ID,
            status=status,
            total_amount=amount,
            currency="MAD",
            issued_date=issued,
            due_date=due,
            fee_structure_id=fee_id,
        )
        session.add(inv)
        created_invoices.append(inv)
    await session.flush()

    # Invoice items for each
    for inv in created_invoices:
        session.add(
            InvoiceItem(
                invoice_id=inv.id,
                description="Frais de scolarite",
                amount=inv.total_amount * 0.9,
                unit_price=inv.total_amount * 0.9,
                quantity=1,
                tva_rate=0.0,
                tva_amount=0.0,
                amount_ht=inv.total_amount * 0.9,
                amount_ttc=inv.total_amount * 0.9,
            )
        )
        session.add(
            InvoiceItem(
                invoice_id=inv.id,
                description="Frais annexes",
                amount=inv.total_amount * 0.1,
                unit_price=inv.total_amount * 0.1,
                quantity=1,
                tva_rate=0.0,
                tva_amount=0.0,
                amount_ht=inv.total_amount * 0.1,
                amount_ttc=inv.total_amount * 0.1,
            )
        )

    # Payment attempts for pending & failed invoices
    for inv in created_invoices:
        if inv.status in ("pending", "failed"):
            pa = PaymentAttempt(
                invoice_id=inv.id,
                parent_id=inv.parent_id,
                school_id=SCHOOL_ID,
                idempotency_key=f"pay-{inv.id}-001",
                status=PaymentAttemptStatus.PROCESSING.value
                if inv.status == "pending"
                else PaymentAttemptStatus.FAILED.value,
                finalized_at=_now() if inv.status == "failed" else None,
            )
            session.add(pa)

    await session.flush()

    # Payment proofs for 3 paid invoices
    paid_invs = [inv for inv in created_invoices if inv.status == "paid"][:3]
    for i, inv in enumerate(paid_invs):
        # Get the payment attempt (created separately, need to query)
        pa = PaymentAttempt(
            invoice_id=inv.id,
            parent_id=inv.parent_id,
            school_id=SCHOOL_ID,
            idempotency_key=f"pay-proof-{inv.id}-001",
            status=PaymentAttemptStatus.PAID.value,
            finalized_at=_now() - timedelta(days=i),
        )
        session.add(pa)
        await session.flush()

    # Webhook events for 2 invoices
    for i, inv in enumerate(created_invoices[:2]):
        pa = await session.execute(
            select(PaymentAttempt).where(PaymentAttempt.invoice_id == inv.id).limit(1)
        )
        pa_obj = pa.scalar_one_or_none()
        if pa_obj:
            session.add(
                ProviderWebhookEvent(
                    payment_attempt_id=pa_obj.id,
                    school_id=SCHOOL_ID,
                    provider_event_id=f"webhook-event-{i}-{uuid.uuid4()}",
                    status=WebhookEventStatus.PROCESSED.value,
                    provider_event_received_at=_now() - timedelta(hours=i),
                )
            )

    await session.flush()
    print("    Enhanced: +12 invoices, +webhook events")


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Payment Plans & Installments
# ═══════════════════════════════════════════════════════════════════════════════


async def seed_payment_plans(session: AsyncSession) -> None:
    """Seed 2 payment plans with installments."""
    # Find 2 pending invoices for parents
    result = await session.execute(
        select(Invoice)
        .where(Invoice.school_id == SCHOOL_ID, Invoice.status == "pending")
        .limit(2)
    )
    invoices = result.scalars().all()
    if len(invoices) < 2:
        print("    Payment plans: skipped (need 2 pending invoices)")
        return

    for i, inv in enumerate(invoices[:2]):
        plan = PaymentPlan(
            school_id=SCHOOL_ID,
            invoice_id=inv.id,
            total_installments=3,
            status="active",
        )
        session.add(plan)
        await session.flush()

        for j in range(1, 4):
            session.add(
                Installment(
                    plan_id=plan.id,
                    installment_number=j,
                    amount=round(inv.total_amount / 3, 2),
                    due_date=datetime(
                        inv.due_date.year,
                        inv.due_date.month,
                        inv.due_date.day,
                        tzinfo=timezone.utc,
                    )
                    - timedelta(days=(3 - j) * 10),
                    paid_at=_now() - timedelta(days=j * 2) if j == 1 else None,
                    status="paid" if j == 1 else "pending",
                )
            )

    await session.flush()
    print("    Enhanced: 2 payment plans with 6 installments")


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Billing Policies
# ═══════════════════════════════════════════════════════════════════════════════


async def seed_billing_policies(session: AsyncSession) -> None:
    """Seed sibling discount and late fee policies."""
    session.add(
        SiblingDiscountPolicy(
            school_id=SCHOOL_ID,
            enabled=True,
            second_child_percent=10.0,
            third_child_percent=20.0,
            fourth_plus_percent=30.0,
            apply_to_oldest_first=True,
        )
    )
    session.add(
        LateFeePolicy(
            school_id=SCHOOL_ID,
            enabled=True,
            fee_type="fixed",
            amount=50.0,
            frequency="weekly",
            grace_days=7,
            max_fee=200.0,
        )
    )
    await session.flush()
    print("    Enhanced: billing policies (sibling discount + late fee)")


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Rubrics (with criteria, levels, scores)
# ═══════════════════════════════════════════════════════════════════════════════


async def seed_rubrics(session: AsyncSession) -> None:
    """Seed 2 rubrics with criteria, levels, and sample scores on submissions."""
    from app.models.lms import Submission

    # Rubric 1: Oral math presentation
    rubric_math = Rubric(
        school_id=SCHOOL_ID,
        teacher_id=TEACHER_1_ID,
        title="Presentation orale — Mathematiques",
        description="Evaluation de la presentation orale d'un probleme mathematique.",
        total_points=20,
        is_template=True,
    )
    session.add(rubric_math)
    await session.flush()

    crit_clarte = RubricCriterion(
        rubric_id=rubric_math.id, title="Clarte de l'expose", weight=1.0, position=0
    )
    crit_method = RubricCriterion(
        rubric_id=rubric_math.id, title="Methodologie", weight=1.0, position=1
    )
    crit_lang = RubricCriterion(
        rubric_id=rubric_math.id, title="Langage mathematique", weight=1.0, position=2
    )
    session.add_all([crit_clarte, crit_method, crit_lang])
    await session.flush()

    for crit in [crit_clarte, crit_method, crit_lang]:
        for level_idx, (label, points) in enumerate(
            [("Insuffisant", 1.0), ("Passable", 2.0), ("Bien", 3.0), ("Tres bien", 4.0)]
        ):
            session.add(
                RubricLevel(
                    criterion_id=crit.id, label=label, points=points, position=level_idx
                )
            )

    # Rubric 2: French essay
    rubric_fr = Rubric(
        school_id=SCHOOL_ID,
        teacher_id=TEACHER_2_ID,
        title="Redaction — Expression ecrite",
        description="Grille d'evaluation pour les productions ecrites.",
        total_points=20,
        is_template=False,
    )
    session.add(rubric_fr)
    await session.flush()

    crit_orth = RubricCriterion(
        rubric_id=rubric_fr.id, title="Orthographe et grammaire", weight=1.0, position=0
    )
    crit_struct = RubricCriterion(
        rubric_id=rubric_fr.id, title="Structure et coherence", weight=1.0, position=1
    )
    crit_creat = RubricCriterion(
        rubric_id=rubric_fr.id, title="Creativite et style", weight=1.0, position=2
    )
    session.add_all([crit_orth, crit_struct, crit_creat])
    await session.flush()

    for crit in [crit_orth, crit_struct, crit_creat]:
        for level_idx, (label, points) in enumerate(
            [("A travailler", 1.0), ("Correct", 2.0), ("Bon", 3.0), ("Excellent", 4.0)]
        ):
            session.add(
                RubricLevel(
                    criterion_id=crit.id, label=label, points=points, position=level_idx
                )
            )

    await session.flush()

    # Score existing submissions with rubric 1 (math)
    subs = await session.execute(
        select(Submission).where(Submission.status == "graded").limit(2)
    )
    for sub in subs.scalars():
        for crit in [crit_clarte, crit_method, crit_lang]:
            level = await session.execute(
                select(RubricLevel)
                .where(RubricLevel.criterion_id == crit.id)
                .offset(2)
                .limit(1)
            )
            lvl = level.scalar_one_or_none()
            if lvl:
                session.add(
                    RubricScore(
                        submission_id=sub.id,
                        criterion_id=crit.id,
                        level_id=lvl.id,
                        points_awarded=lvl.points,
                        comment="Bonne maitrise du critere.",
                    )
                )

    await session.flush()
    print("    Enhanced: 2 rubrics (6 criteria, 18 levels), sample rubric scores")


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Submission Files & Content Item Assets
# ═══════════════════════════════════════════════════════════════════════════════


async def seed_submission_files(session: AsyncSession) -> None:
    """Seed file attachments for submissions and content items."""
    from app.models.lms import ContentItem, Submission

    # Submission files for graded submissions
    subs = await session.execute(select(Submission).limit(3))
    for i, sub in enumerate(subs.scalars()):
        session.add(
            SubmissionFile(
                submission_id=sub.id,
                file_path=f"submissions/student_{sub.student_id}/devoir_{i+1}.pdf",
                checksum=f"sha256:{uuid.uuid4().hex}",
                mime_type="application/pdf",
                file_size=245_760 + i * 10000,
                file_type_hint="SOLUTION_SCAN" if i == 0 else "SOLUTION_PHOTO",
            )
        )

    # Content item assets used by the student content player.
    # These paths exist under backend/uploads and are mounted into /app/uploads
    # by the development compose file.
    content_assets = [
        ContentItemAsset(
            content_item_id=PLATFORM_CONTENT_FRACTIONS_VIDEO_ID,
            file_path="content/videos/zay_video.mp4",
            mime_type="video/mp4",
            file_size=100_861_906,
            asset_type="video",
        ),
        ContentItemAsset(
            content_item_id=PLATFORM_CONTENT_TRIANGLES_PDF_ID,
            file_path="content/pdfs/intro.pdf",
            mime_type="application/pdf",
            file_size=10_040_524,
            asset_type="document",
        ),
    ]

    teacher_pdf = await session.execute(
        select(ContentItem).where(
            ContentItem.title == "Exercices supplementaires - Fractions"
        )
    )
    teacher_content = teacher_pdf.scalar_one_or_none()
    if teacher_content is not None:
        content_assets.append(
            ContentItemAsset(
                content_item_id=teacher_content.id,
                file_path="content/pdfs/coloring_animal_letters.pdf",
                mime_type="application/pdf",
                file_size=13_239_385,
                asset_type="document",
            )
        )
        # Assign this COMPLETE PDF (file exists on disk) to class 1AC-A
        # (CLASS_6A_ID = where the demo student Yassine is enrolled) so a clean
        # PDF renders in the student reader.
        session.add(
            ClassContentAssignment(
                teacher_id=TEACHER_1_ID,
                class_id=CLASS_6A_ID,
                content_item_id=teacher_content.id,
                school_id=SCHOOL_ID,
                assigned_at=_now(),
                notes="Exercices PDF de fractions pour la 1ère année collège.",
            )
        )

    session.add_all(content_assets)

    await session.flush()
    print(f"    Enhanced: 3 submission files, {len(content_assets)} content assets")


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Question Bank
# ═══════════════════════════════════════════════════════════════════════════════


async def seed_question_bank(session: AsyncSession) -> None:
    """Seed 5 reusable question bank items."""
    questions = [
        QuestionBankItem(
            school_id=SCHOOL_ID,
            teacher_id=TEACHER_1_ID,
            subject="math",
            level_band="1AC",
            difficulty="MEDIUM",
            question_type="MCQ",
            question_data={
                "text": "Quelle est la valeur de pi approximative?",
                "options": ["3.12", "3.14", "3.16", "3.18"],
                "correct": "3.14",
            },
            tags=["geometrie", "cercle"],
        ),
        QuestionBankItem(
            school_id=SCHOOL_ID,
            teacher_id=TEACHER_1_ID,
            subject="math",
            level_band="1AC",
            difficulty="EASY",
            question_type="FILL_IN",
            question_data={
                "text": "L'aire d'un rectangle = longueur x _____",
                "correct": "largeur",
            },
            tags=["geometrie", "aire"],
        ),
        QuestionBankItem(
            school_id=SCHOOL_ID,
            teacher_id=TEACHER_2_ID,
            subject="french",
            level_band="1AC",
            difficulty="MEDIUM",
            question_type="MCQ",
            question_data={
                "text": "Quel est le participe passe de 'prendre'?",
                "options": ["pris", "prend", "prenant", "prendu"],
                "correct": "pris",
            },
            tags=["grammaire", "participe_passe"],
        ),
        QuestionBankItem(
            school_id=SCHOOL_ID,
            teacher_id=TEACHER_2_ID,
            subject="french",
            level_band="1AC",
            difficulty="HARD",
            question_type="TRUE_FALSE",
            question_data={
                "text": "Le passe compose s'emploie pour une action terminee dans le passe.",
                "correct": True,
            },
            tags=["grammaire", "temps_verbaux"],
        ),
        QuestionBankItem(
            school_id=SCHOOL_ID,
            teacher_id=TEACHER_1_ID,
            subject="math",
            level_band="2AC",
            difficulty="HARD",
            question_type="MCQ",
            question_data={
                "text": "Un triangle rectangle a un angle de:",
                "options": ["60°", "90°", "120°", "180°"],
                "correct": "90°",
            },
            tags=["geometrie", "triangle"],
        ),
    ]
    session.add_all(questions)
    await session.flush()
    print("    Enhanced: 5 question bank items")


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Quiz Responses
# ═══════════════════════════════════════════════════════════════════════════════


async def seed_quiz_responses(session: AsyncSession) -> None:
    """Seed detailed quiz responses for existing attempts."""
    from app.models.lms import QuizAttempt, QuizQuestion

    attempts = await session.execute(select(QuizAttempt).limit(2))
    attempt_list = list(attempts.scalars())
    if not attempt_list:
        print("    Quiz responses: skipped (no attempts)")
        return

    for attempt in attempt_list:
        questions = await session.execute(
            select(QuizQuestion).where(QuizQuestion.quiz_id == attempt.quiz_id)
        )
        for q in questions.scalars():
            session.add(
                QuizResponse(
                    attempt_id=attempt.id,
                    question_id=q.id,
                    student_answer=q.correct_answer,
                    is_correct=True,
                    points_earned=q.points,
                    answered_at=attempt.completed_at or attempt.started_at,
                )
            )

    await session.flush()
    print(f"    Enhanced: {len(attempt_list)} quiz attempts with full responses")


# ═══════════════════════════════════════════════════════════════════════════════
# 9. Grade Categories & Student Period Averages
# ═══════════════════════════════════════════════════════════════════════════════


async def seed_grade_categories_and_averages(session: AsyncSession) -> None:
    """Seed grade categories and cached period averages."""
    categories = [
        GradeCategory(
            school_id=SCHOOL_ID,
            class_id=CLASS_6A_ID,
            period_id=PERIOD_2_ID,
            name="Controles",
            weight=0.5,
            position=0,
        ),
        GradeCategory(
            school_id=SCHOOL_ID,
            class_id=CLASS_6A_ID,
            period_id=PERIOD_2_ID,
            name="Devoirs",
            weight=0.3,
            position=1,
        ),
        GradeCategory(
            school_id=SCHOOL_ID,
            class_id=CLASS_6A_ID,
            period_id=PERIOD_2_ID,
            name="Participation",
            weight=0.2,
            position=2,
        ),
    ]
    session.add_all(categories)
    await session.flush()

    # Student period averages for 6A students
    averages = [
        (STUDENT_1_ID, 16.5, "Tres bien", 1),
        (STUDENT_2_ID, 14.0, "Bien", 2),
        (STUDENT_4_ID, 15.5, "Bien", 3),
        (STUDENT_5_ID, 12.5, "Passable", 4),
    ]
    for student_id, avg, mention, rank in averages:
        session.add(
            StudentPeriodAverage(
                student_id=student_id,
                class_id=CLASS_6A_ID,
                period_id=PERIOD_2_ID,
                school_id=SCHOOL_ID,
                weighted_average=avg,
                mention=mention,
                class_rank=rank,
                total_students=len(averages),
                computed_at=_now(),
            )
        )

    # Also for 6B
    averages_6b = [
        (STUDENT_3_ID, 13.0, "Passable", 1),
        (STUDENT_10_ID, 11.5, "Passable", 2),
        (STUDENT_11_ID, 14.5, "Bien", 3),
    ]
    for student_id, avg, mention, rank in averages_6b:
        session.add(
            StudentPeriodAverage(
                student_id=student_id,
                class_id=CLASS_6B_ID,
                period_id=PERIOD_2_ID,
                school_id=SCHOOL_ID,
                weighted_average=avg,
                mention=mention,
                class_rank=rank,
                total_students=len(averages_6b),
                computed_at=_now(),
            )
        )

    await session.flush()
    print("    Enhanced: 3 grade categories, 7 student period averages")


# ═══════════════════════════════════════════════════════════════════════════════
# 10. Enhanced Attendance (+15 sessions, alerts)
# ═══════════════════════════════════════════════════════════════════════════════


async def seed_enhanced_attendance(session: AsyncSession) -> None:
    """Add 15 more attendance sessions across 3 weeks with alerts."""

    # 3 weeks of school days (Mon-Fri)
    school_days = []
    base = date(2026, 4, 6)
    for week in range(3):
        for day in range(5):
            d = base + timedelta(weeks=week, days=day)
            if d.weekday() < 5:  # Mon-Fri
                school_days.append(d)

    # Limit to 15 days
    school_days = school_days[:15]

    classes = [CLASS_6A_ID, CLASS_6B_ID, CLASS_5EME_ID]
    class_students = {
        CLASS_6A_ID: [
            STUDENT_1_ID,
            STUDENT_2_ID,
            STUDENT_4_ID,
            STUDENT_5_ID,
            STUDENT_6_ID,
            STUDENT_7_ID,
            STUDENT_8_ID,
            STUDENT_9_ID,
        ],
        CLASS_6B_ID: [
            STUDENT_3_ID,
            STUDENT_10_ID,
            STUDENT_11_ID,
            STUDENT_12_ID,
            STUDENT_13_ID,
            STUDENT_14_ID,
        ],
        CLASS_5EME_ID: [STUDENT_15_ID],
    }

    all_records: list[AttendanceRecord] = []
    for day in school_days:
        for class_id in classes:
            students = class_students[class_id]
            att = AttendanceSession(
                class_id=class_id,
                period_id=PERIOD_2_ID,
                teacher_id=TEACHER_1_ID if class_id != CLASS_6B_ID else TEACHER_2_ID,
                school_id=SCHOOL_ID,
                session_date=day,
                slot="09:00-10:00",
            )
            session.add(att)
            await session.flush()

            for student_id in students:
                # Simulate some absences and lates
                random.seed(int(student_id.int % 1000) + day.toordinal())
                rand = random.random()
                if rand < 0.75:
                    st = "present"
                elif rand < 0.90:
                    st = "late"
                elif rand < 0.97:
                    st = "absent"
                else:
                    st = "excused"

                rec = AttendanceRecord(
                    attendance_session_id=att.id,
                    student_id=student_id,
                    school_id=SCHOOL_ID,
                    status=st,
                    absence_reason="Maladie" if st == "absent" else None,
                )
                session.add(rec)
                all_records.append(rec)

    await session.flush()

    # Create attendance alerts for students with high absence rate
    student_absences: dict[uuid.UUID, int] = {}
    student_sessions: dict[uuid.UUID, int] = {}
    for rec in all_records:
        student_sessions[rec.student_id] = student_sessions.get(rec.student_id, 0) + 1
        if rec.status in ("absent",):
            student_absences[rec.student_id] = (
                student_absences.get(rec.student_id, 0) + 1
            )

    for student_id, abs_count in student_absences.items():
        total = student_sessions.get(student_id, 1)
        rate = abs_count / total
        if rate > 0.15:
            session.add(
                AttendanceAlert(
                    school_id=SCHOOL_ID,
                    student_id=student_id,
                    period_id=PERIOD_2_ID,
                    absence_count=abs_count,
                    total_sessions=total,
                    absence_rate=round(rate, 2),
                    threshold_exceeded="warning" if rate < 0.25 else "critical",
                    notified_at=_now() if rate > 0.20 else None,
                )
            )

    await session.flush()
    print(
        f"    Enhanced: +{len(school_days) * len(classes)} attendance sessions, attendance alerts"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 11. Absence Justifications & Reviews
# ═══════════════════════════════════════════════════════════════════════════════


async def seed_absence_justifications(session: AsyncSession) -> None:
    """Seed absence justifications and teacher reviews."""
    # Find 2 absent records
    records = await session.execute(
        select(AttendanceRecord)
        .where(
            AttendanceRecord.school_id == SCHOOL_ID,
            AttendanceRecord.status == "absent",
        )
        .limit(2)
    )
    rec_list = list(records.scalars())
    if len(rec_list) < 2:
        print("    Absence justifications: skipped (need 2 absent records)")
        return

    # Justification 1: pending
    just1 = AbsenceJustification(
        school_id=SCHOOL_ID,
        attendance_record_id=rec_list[0].id,
        parent_id=PARENT_1_ID,
        status=JustificationStatus.PENDING.value,
        reason="Mon enfant a eu une fievre et n'a pas pu se rendre a l'ecole.",
        attachment_url="documents/justifications/certificat_medical_001.pdf",
    )
    session.add(just1)

    # Justification 2: justified
    just2 = AbsenceJustification(
        school_id=SCHOOL_ID,
        attendance_record_id=rec_list[1].id,
        parent_id=PARENT_2_ID,
        status=JustificationStatus.JUSTIFIED.value,
        reason="Absence pour raison familiale — mariage du cousin.",
    )
    session.add(just2)
    await session.flush()

    # Review for justified
    session.add(
        JustificationReview(
            school_id=SCHOOL_ID,
            justification_id=just2.id,
            reviewer_id=DIRECTOR_ID,
            decision="approved",
        )
    )

    await session.flush()
    print("    Enhanced: 2 absence justifications (1 pending, 1 approved)")


# ═══════════════════════════════════════════════════════════════════════════════
# 12. Budget (micro-budgets, allocations, requests, transactions)
# ═══════════════════════════════════════════════════════════════════════════════


async def seed_budget(session: AsyncSession) -> None:
    """Seed school budget with allocations, requests, and transactions."""
    budget = SchoolBudget(
        school_id=SCHOOL_ID,
        academic_year_id=YEAR_ID,
        total_amount=50000.00,
        allocated_amount=35000.00,
        remaining_amount=15000.00,
        currency="MAD",
        status=SchoolBudgetStatus.ACTIVE.value,
        created_by=ADMIN_ID,
    )
    session.add(budget)
    await session.flush()

    # Allocations
    allocations = [
        BudgetAllocation(
            budget_id=budget.id,
            class_id=CLASS_6A_ID,
            teacher_id=None,
            label="Fournitures 6eme A",
            amount=10000.00,
            spent=4000.00,
            remaining=6000.00,
            currency="MAD",
            allocated_by=ADMIN_ID,
            status=BudgetAllocationStatus.ACTIVE.value,
        ),
        BudgetAllocation(
            budget_id=budget.id,
            class_id=CLASS_6B_ID,
            teacher_id=None,
            label="Fournitures 6eme B",
            amount=8000.00,
            spent=2000.00,
            remaining=6000.00,
            currency="MAD",
            allocated_by=ADMIN_ID,
            status=BudgetAllocationStatus.ACTIVE.value,
        ),
        BudgetAllocation(
            budget_id=budget.id,
            class_id=None,
            teacher_id=TEACHER_1_ID,
            label="Formation prof. Kettani",
            amount=5000.00,
            spent=5000.00,
            remaining=0.00,
            currency="MAD",
            allocated_by=ADMIN_ID,
            status=BudgetAllocationStatus.EXHAUSTED.value,
        ),
    ]
    session.add_all(allocations)
    await session.flush()

    # Requests
    req1 = BudgetRequest(
        allocation_id=allocations[0].id,
        requester_id=TEACHER_1_ID,
        amount=1500.00,
        currency="MAD",
        description="Achat de calculatrices scientifiques pour la classe.",
        justification="Les eleves n'ont pas assez de calculatrices pour le controle.",
        status=BudgetRequestStatus.APPROVED.value,
        reviewed_by=ADMIN_ID,
        reviewed_at=_now() - timedelta(days=2),
        review_comment="Approuve — achat urgent.",
    )
    req2 = BudgetRequest(
        allocation_id=allocations[1].id,
        requester_id=TEACHER_2_ID,
        amount=3000.00,
        currency="MAD",
        description="Achat de livres de lecture pour la bibliotheque de classe.",
        justification="Renouvellement du fonds de lecture recommande par l'inspection.",
        status=BudgetRequestStatus.PENDING.value,
    )
    session.add_all([req1, req2])
    await session.flush()

    # Transactions
    transactions = [
        BudgetTransaction(
            allocation_id=allocations[0].id,
            request_id=req1.id,
            amount=1500.00,
            transaction_type=BudgetTransactionType.EXPENSE.value,
            description="Achat calculatrices",
            recorded_by=ADMIN_ID,
        ),
        BudgetTransaction(
            allocation_id=allocations[0].id,
            request_id=None,
            amount=2500.00,
            transaction_type=BudgetTransactionType.EXPENSE.value,
            description="Achat papier et crayons",
            recorded_by=ADMIN_ID,
        ),
        BudgetTransaction(
            allocation_id=allocations[2].id,
            request_id=None,
            amount=5000.00,
            transaction_type=BudgetTransactionType.EXPENSE.value,
            description="Formation externe — prof. Kettani",
            recorded_by=ADMIN_ID,
        ),
        BudgetTransaction(
            allocation_id=allocations[0].id,
            request_id=None,
            amount=10000.00,
            transaction_type=BudgetTransactionType.ALLOCATION.value,
            description="Allocation initiale",
            recorded_by=ADMIN_ID,
        ),
    ]
    session.add_all(transactions)

    await session.flush()
    print("    Enhanced: 1 micro-budget, 3 allocations, 2 requests, 4 transactions")


# ═══════════════════════════════════════════════════════════════════════════════
# 13. Financial Health
# ═══════════════════════════════════════════════════════════════════════════════


async def seed_financial_health(session: AsyncSession) -> None:
    """Seed retention, cashflow, cost-per-student, and financial snapshots."""
    # Retention metric
    session.add(
        RetentionMetric(
            school_id=SCHOOL_ID,
            academic_year_from="2024-2025",
            academic_year_to="2025-2026",
            total_students_start=120,
            total_students_end=125,
            retained=115,
            new_enrollments=15,
            withdrawals=5,
            retention_rate=95.83,
        )
    )

    # Cashflow forecasts (3 months)
    base_month = date(2026, 3, 1)
    for i in range(3):
        forecast_month = base_month + timedelta(days=32 * i)
        forecast_month = forecast_month.replace(day=1)
        session.add(
            CashflowForecast(
                school_id=SCHOOL_ID,
                forecast_month=forecast_month,
                expected_income=45000.00 + i * 2000,
                expected_expenses=28000.00 + i * 500,
                actual_income=42000.00 + i * 1500 if i < 2 else None,
                actual_expenses=27500.00 + i * 400 if i < 2 else None,
                currency="MAD",
                confidence_score=0.85 - i * 0.05,
            )
        )

    # Cost per student
    session.add(
        CostPerStudent(
            school_id=SCHOOL_ID,
            academic_year_id=YEAR_ID,
            total_operational_cost=350000.00,
            total_students=125,
            cost_per_student=2800.00,
            revenue_per_student=3500.00,
            margin_per_student=700.00,
            currency="MAD",
        )
    )

    # Financial snapshots
    session.add(
        FinancialSnapshot(
            school_id=SCHOOL_ID,
            snapshot_date=date(2026, 3, 31),
            total_receivable=125000.00,
            total_collected=98000.00,
            collection_rate=78.4,
            overdue_amount=27000.00,
            overdue_count=12,
            avg_payment_delay_days=8.5,
            currency="MAD",
        )
    )
    session.add(
        FinancialSnapshot(
            school_id=SCHOOL_ID,
            snapshot_date=date(2026, 4, 30),
            total_receivable=135000.00,
            total_collected=110000.00,
            collection_rate=81.5,
            overdue_amount=25000.00,
            overdue_count=10,
            avg_payment_delay_days=7.2,
            currency="MAD",
        )
    )

    await session.flush()
    print(
        "    Enhanced: financial health (retention, cashflow, cost/student, 2 snapshots)"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 14. Micro-School
# ═══════════════════════════════════════════════════════════════════════════════


async def seed_micro_school(session: AsyncSession) -> None:
    """Seed informal micro-school with groups, enrollments, payments, resources."""
    # Create educator user
    EDUCATOR_ID = uuid.UUID("10000000-0000-4000-8000-000000000030")
    session.add(
        User(
            id=EDUCATOR_ID,
            email="educateur.micro@ecole-benani.ma",
            full_name="Said El Fassi",
            password_hash=_demo_password_hash("teacher123"),
            status="active",
            school_id=MICRO_SCHOOL_TENANT_ID,
        )
    )
    session.add(
        Membership(
            user_id=EDUCATOR_ID,
            school_id=MICRO_SCHOOL_TENANT_ID,
            role_code="EDUCATOR",
            status="active",
        )
    )
    session.add_all(
        [
            User(
                id=MICRO_PARENT_1_ID,
                email="parent.micro1@ecole-benani.ma",
                full_name="Brahim Souane",
                phone="+212600100101",
                password_hash=_demo_password_hash("parent123"),
                status="active",
                school_id=MICRO_SCHOOL_TENANT_ID,
            ),
            User(
                id=MICRO_PARENT_2_ID,
                email="parent.micro2@ecole-benani.ma",
                full_name="Hanae Toulni",
                phone="+212600100102",
                password_hash=_demo_password_hash("parent123"),
                status="active",
                school_id=MICRO_SCHOOL_TENANT_ID,
            ),
            Membership(
                user_id=MICRO_PARENT_1_ID,
                school_id=MICRO_SCHOOL_TENANT_ID,
                role_code="PAR",
                status="active",
            ),
            Membership(
                user_id=MICRO_PARENT_2_ID,
                school_id=MICRO_SCHOOL_TENANT_ID,
                role_code="PAR",
                status="active",
            ),
            User(
                id=MICRO_STUDENT_CRECHE_ID,
                email="adam.creche@ecole-micro.ma",
                full_name="Adam Souane",
                password_hash=_demo_password_hash("student123"),
                status="active",
                school_id=MICRO_SCHOOL_TENANT_ID,
            ),
            User(
                id=MICRO_STUDENT_MSID_ID,
                email="lina.msid@ecole-micro.ma",
                full_name="Lina Toulni",
                password_hash=_demo_password_hash("student123"),
                status="active",
                school_id=MICRO_SCHOOL_TENANT_ID,
            ),
            User(
                id=MICRO_STUDENT_KOUTTAB_ID,
                email="youssef.kouttab@ecole-micro.ma",
                full_name="Youssef Souane",
                password_hash=_demo_password_hash("student123"),
                status="active",
                school_id=MICRO_SCHOOL_TENANT_ID,
            ),
            User(
                id=MICRO_STUDENT_PRESCHOOL_ID,
                email="sara.prescolaire@ecole-micro.ma",
                full_name="Sara Toulni",
                password_hash=_demo_password_hash("student123"),
                status="active",
                school_id=MICRO_SCHOOL_TENANT_ID,
            ),
            Membership(
                user_id=MICRO_STUDENT_CRECHE_ID,
                school_id=MICRO_SCHOOL_TENANT_ID,
                role_code="STD",
                status="active",
            ),
            Membership(
                user_id=MICRO_STUDENT_MSID_ID,
                school_id=MICRO_SCHOOL_TENANT_ID,
                role_code="STD",
                status="active",
            ),
            Membership(
                user_id=MICRO_STUDENT_KOUTTAB_ID,
                school_id=MICRO_SCHOOL_TENANT_ID,
                role_code="STD",
                status="active",
            ),
            Membership(
                user_id=MICRO_STUDENT_PRESCHOOL_ID,
                school_id=MICRO_SCHOOL_TENANT_ID,
                role_code="STD",
                status="active",
            ),
        ]
    )
    await session.flush()

    session.add_all(
        [
            ParentProfile(
                user_id=MICRO_PARENT_1_ID,
                school_id=MICRO_SCHOOL_TENANT_ID,
                relationship_type="father",
                cin_number="MI100101",
                address="Hay Orangers, Casablanca",
                profession="Artisan",
                emergency_phone="+212600100101",
            ),
            ParentProfile(
                user_id=MICRO_PARENT_2_ID,
                school_id=MICRO_SCHOOL_TENANT_ID,
                relationship_type="mother",
                cin_number="MI100102",
                address="Hay Orangers, Casablanca",
                profession="Commercante",
                emergency_phone="+212600100102",
            ),
            StudentProfile(
                user_id=MICRO_STUDENT_CRECHE_ID,
                school_id=MICRO_SCHOOL_TENANT_ID,
                student_number="MICRO-CRECHE-001",
                date_of_birth=date(2022, 3, 10),
                gender="male",
                class_level="informal-creche",
                nationality="Marocaine",
            ),
            StudentProfile(
                user_id=MICRO_STUDENT_MSID_ID,
                school_id=MICRO_SCHOOL_TENANT_ID,
                student_number="MICRO-MSID-001",
                date_of_birth=date(2022, 7, 15),
                gender="female",
                class_level="informal-msid",
                nationality="Marocaine",
            ),
            StudentProfile(
                user_id=MICRO_STUDENT_KOUTTAB_ID,
                school_id=MICRO_SCHOOL_TENANT_ID,
                student_number="MICRO-KOUTTAB-001",
                date_of_birth=date(2020, 1, 20),
                gender="male",
                class_level="informal-kouttab",
                nationality="Marocaine",
            ),
            StudentProfile(
                user_id=MICRO_STUDENT_PRESCHOOL_ID,
                school_id=MICRO_SCHOOL_TENANT_ID,
                student_number="MICRO-PRESCO-001",
                date_of_birth=date(2019, 11, 5),
                gender="female",
                class_level="informal-prescolaire",
                nationality="Marocaine",
            ),
            ParentChildLink(
                parent_user_id=MICRO_PARENT_1_ID,
                child_user_id=MICRO_STUDENT_CRECHE_ID,
                school_id=MICRO_SCHOOL_TENANT_ID,
                status="active",
                linked_at=_now(),
                linked_by=EDUCATOR_ID,
            ),
            ParentChildLink(
                parent_user_id=MICRO_PARENT_2_ID,
                child_user_id=MICRO_STUDENT_MSID_ID,
                school_id=MICRO_SCHOOL_TENANT_ID,
                status="active",
                linked_at=_now(),
                linked_by=EDUCATOR_ID,
            ),
            ParentChildLink(
                parent_user_id=MICRO_PARENT_1_ID,
                child_user_id=MICRO_STUDENT_KOUTTAB_ID,
                school_id=MICRO_SCHOOL_TENANT_ID,
                status="active",
                linked_at=_now(),
                linked_by=EDUCATOR_ID,
            ),
            ParentChildLink(
                parent_user_id=MICRO_PARENT_2_ID,
                child_user_id=MICRO_STUDENT_PRESCHOOL_ID,
                school_id=MICRO_SCHOOL_TENANT_ID,
                status="active",
                linked_at=_now(),
                linked_by=EDUCATOR_ID,
            ),
        ]
    )
    await session.flush()

    micro = MicroSchool(
        educator_id=EDUCATOR_ID,
        name="Petite Ecole des Orangers",
        neighborhood="Hay Orangers",
        city="Casablanca",
        phone="+212612345999",
        max_capacity=20,
        status=MicroSchoolStatus.ACTIVE.value,
        type=MicroSchoolType.RAWD.value,
    )
    session.add(micro)
    await session.flush()

    # Groups
    g1 = MicroGroup(
        micro_school_id=micro.id,
        name="Crèche / Msid",
        age_range_min=2,
        age_range_max=4,
    )
    g2 = MicroGroup(
        micro_school_id=micro.id,
        name="Kouttab / Préscolaire",
        age_range_min=4,
        age_range_max=6,
    )
    session.add_all([g1, g2])
    await session.flush()

    # Enrollments
    enrollments_data = [
        (
            g1.id,
            "Adam Souane",
            MICRO_PARENT_1_ID,
            MICRO_STUDENT_CRECHE_ID,
            date(2022, 3, 10),
        ),
        (
            g1.id,
            "Lina Toulni",
            MICRO_PARENT_2_ID,
            MICRO_STUDENT_MSID_ID,
            date(2022, 7, 15),
        ),
        (
            g2.id,
            "Youssef Souane",
            MICRO_PARENT_1_ID,
            MICRO_STUDENT_KOUTTAB_ID,
            date(2020, 1, 20),
        ),
        (
            g2.id,
            "Sara Toulni",
            MICRO_PARENT_2_ID,
            MICRO_STUDENT_PRESCHOOL_ID,
            date(2019, 11, 5),
        ),
    ]
    enrollment_objs: list[MicroEnrollment] = []
    for gid, child_name, parent_id, student_user_id, dob in enrollments_data:
        me = MicroEnrollment(
            micro_group_id=gid,
            child_name=child_name,
            parent_id=parent_id,
            student_user_id=student_user_id,
            date_of_birth=dob,
            status=MicroEnrollmentStatus.ACTIVE.value,
        )
        session.add(me)
        enrollment_objs.append(me)
    await session.flush()

    # Payments
    for i, me in enumerate(enrollment_objs):
        session.add(
            MicroPayment(
                micro_school_id=micro.id,
                parent_id=me.parent_id,
                child_enrollment_id=me.id,
                amount=400.00 + i * 50,
                currency="MAD",
                period_type=MicroPaymentPeriodType.MONTHLY.value,
                period_start=date(2026, 4, 1),
                period_end=date(2026, 4, 30),
                paid_at=_now() - timedelta(days=i) if i < 2 else None,
                status=MicroPaymentStatus.PAID.value
                if i < 2
                else MicroPaymentStatus.PENDING.value,
            )
        )

    # Resources
    session.add_all(
        [
            MicroResource(
                title="Fiche coloriage — Animaux de la ferme",
                resource_type=MicroResourceType.ACTIVITY_SHEET,
                age_group="2-4",
                language="fr",
                file_url="micro_resources/coloriage_ferme.pdf",
                is_premium=False,
            ),
            MicroResource(
                title="Chanson — L'alphabet arabe",
                resource_type=MicroResourceType.SONG,
                age_group="4-6",
                language="ar",
                file_url="micro_resources/alphabet_arabe.mp3",
                is_premium=True,
            ),
            MicroResource(
                title="Plan de lecon — Les formes geometriques",
                resource_type=MicroResourceType.LESSON_PLAN,
                age_group="4-6",
                language="fr",
                file_url="micro_resources/formes_geometriques.pdf",
                is_premium=False,
            ),
        ]
    )

    # Progress logs
    for i, me in enumerate(enrollment_objs[:3]):
        for day_offset in range(1, 3):
            session.add(
                MicroProgressLog(
                    micro_enrollment_id=me.id,
                    educator_id=EDUCATOR_ID,
                    date=date(2026, 4, day_offset + i),
                    note=f"Progression positive — {me.child_name} a participe activement aux activites.",
                    milestone_tag="social" if i % 2 == 0 else "cognitive",
                )
            )

    await session.flush()
    print(
        "    Enhanced: 1 micro-school, 2 groups, 4 enrollments, 4 payments, 3 resources, 6 progress logs"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 15. Sync Queue
# ═══════════════════════════════════════════════════════════════════════════════


async def seed_sync_queue(session: AsyncSession) -> None:
    """Seed sync devices, queue items, conflicts, and checkpoints."""
    d1 = SyncDevice(
        school_id=SCHOOL_ID,
        device_name="Tablette Salle 101",
        device_type=SyncDeviceType.MOBILE.value,
        firmware_version="1.2.3",
        is_active=True,
    )
    d2 = SyncDevice(
        school_id=SCHOOL_ID,
        device_name="Chromebook Bibliotheque",
        device_type=SyncDeviceType.BROWSER.value,
        firmware_version=None,
        is_active=True,
    )
    session.add_all([d1, d2])
    await session.flush()

    # Queue items
    for i in range(5):
        session.add(
            SyncQueue(
                school_id=SCHOOL_ID,
                device_id=d1.id if i % 2 == 0 else d2.id,
                entity_type="attendance_record" if i < 2 else "grade",
                entity_id=uuid.uuid4(),
                operation=SyncQueueOperation.CREATE.value
                if i < 3
                else SyncQueueOperation.UPDATE.value,
                payload={"id": str(uuid.uuid4()), "status": "synced"},
                status=SyncQueueStatus.SYNCED.value
                if i < 3
                else SyncQueueStatus.PENDING.value,
                retry_count=i,
            )
        )

    # Conflict
    queue_items = await session.execute(select(SyncQueue).limit(1))
    qi = queue_items.scalar_one_or_none()
    if qi:
        session.add(
            SyncConflict(
                school_id=SCHOOL_ID,
                queue_item_id=qi.id,
                entity_type=qi.entity_type,
                entity_id=qi.entity_id,
                client_payload={"score": 15.0},
                server_payload={"score": 14.5},
                resolution=SyncConflictResolution.PENDING.value,
                resolved_by=None,
                resolved_at=None,
            )
        )

    # Checkpoints
    for d in [d1, d2]:
        session.add(
            SyncCheckpoint(
                school_id=SCHOOL_ID,
                device_id=d.id,
                last_sync_at=_now() - timedelta(hours=2),
                last_entity_type="attendance_record",
                last_entity_id=uuid.uuid4(),
                records_synced=150,
            )
        )

    await session.flush()
    print("    Enhanced: 2 sync devices, 5 queue items, 1 conflict, 2 checkpoints")


# ═══════════════════════════════════════════════════════════════════════════════
# 16. MEN Compliance Extra (curriculum mappings + compliance report)
# ═══════════════════════════════════════════════════════════════════════════════


async def seed_men_compliance_extra(session: AsyncSession) -> None:
    """Seed curriculum mappings and a compliance report."""
    # Find existing MEN curriculum and objectives
    curricula = await session.execute(select(MenCurriculum).limit(1))
    curriculum = curricula.scalar_one_or_none()
    if curriculum is None:
        print("    MEN compliance extra: skipped (no curriculum)")
        return

    objectives = await session.execute(
        select(MenObjective).where(MenObjective.curriculum_id == curriculum.id).limit(3)
    )
    obj_list = list(objectives.scalars())
    if len(obj_list) < 3:
        print("    MEN compliance extra: skipped (need 3 objectives)")
        return

    # Find a course and content item to map
    from app.models.lms import ContentItem, Course

    courses = await session.execute(select(Course).limit(1))
    course = courses.scalar_one_or_none()
    contents = await session.execute(select(ContentItem).limit(1))
    content = contents.scalar_one_or_none()

    for i, obj in enumerate(obj_list):
        session.add(
            CurriculumMapping(
                school_id=SCHOOL_ID,
                objective_id=obj.id,
                course_id=course.id if course and i == 0 else None,
                content_item_id=content.id if content and i > 0 else None,
                mapped_by=TEACHER_1_ID,
                coverage_percent=75 + i * 10,
                notes=f"Mapping demo pour l'objectif {obj.code}",
            )
        )

    # Compliance report
    session.add(
        ComplianceReport(
            school_id=SCHOOL_ID,
            curriculum_id=curriculum.id,
            generated_at=_now(),
            generated_by=ADMIN_ID,
            total_objectives=len(obj_list),
            mapped_objectives=3,
            compliance_percent=100.0,
            unmapped_objectives=[],
            pdf_url="reports/compliance_2025_2026.pdf",
            academic_year_id=YEAR_ID,
        )
    )

    await session.flush()
    print("    Enhanced: 3 curriculum mappings, 1 compliance report")


# ═══════════════════════════════════════════════════════════════════════════════
# 17. Upload Sessions
# ═══════════════════════════════════════════════════════════════════════════════


async def seed_upload_sessions(session: AsyncSession) -> None:
    """Seed upload session tracking records."""
    uploads = [
        UploadSession(
            upload_state="available",
            kind="assignment_pdf",
            object_key="uploads/assignments/devoir_math_001.pdf",
            mime_type="application/pdf",
            size_bytes=245_760,
            sha256="a" * 64,
            school_id=SCHOOL_ID,
            uploader_id=TEACHER_1_ID,
            scope_data={"assignment_id": str(uuid.uuid4())},
            expires_at=_now() + timedelta(days=7),
            completed_at=_now(),
            scanned_at=_now(),
            target_kind="assignment",
        ),
        UploadSession(
            upload_state="available",
            kind="content_asset",
            object_key="uploads/content/coloriage_animaux.pdf",
            mime_type="application/pdf",
            size_bytes=128_000,
            sha256="b" * 64,
            school_id=SCHOOL_ID,
            uploader_id=CONTENT_MGR_ID,
            scope_data={"content_item_id": str(uuid.uuid4())},
            expires_at=_now() + timedelta(days=7),
            completed_at=_now(),
            scanned_at=_now(),
            target_kind="content_item_asset",
        ),
        UploadSession(
            upload_state="available",
            kind="submission_file",
            object_key="uploads/submissions/copie_yassine.jpg",
            mime_type="image/jpeg",
            size_bytes=512_000,
            sha256="c" * 64,
            school_id=SCHOOL_ID,
            uploader_id=STUDENT_1_ID,
            scope_data={"submission_id": str(uuid.uuid4())},
            expires_at=_now() + timedelta(days=7),
            completed_at=_now(),
            scanned_at=_now(),
            target_kind="submission_file",
        ),
    ]
    session.add_all(uploads)
    await session.flush()
    print("    Enhanced: 3 upload sessions (PDF, image)")


# ═══════════════════════════════════════════════════════════════════════════════
# 18. Shared Review Comments (parent encouragement)
# ═══════════════════════════════════════════════════════════════════════════════


async def seed_shared_reviews(session: AsyncSession) -> None:
    """Seed parent comments on child learning sessions."""
    from app.models.lms import QuizAttempt

    attempts = await session.execute(select(QuizAttempt).limit(3))
    for i, att in enumerate(attempts.scalars()):
        parent_id = PARENT_1_ID if att.student_id == STUDENT_1_ID else PARENT_2_ID
        session.add(
            SharedReviewComment(
                school_id=SCHOOL_ID,
                session_id=att.id,
                child_id=att.student_id,
                author_id=parent_id,
                text=[
                    "Bravo mon cheri !",
                    "Excellent travail, continue comme ca !",
                    "Je suis fier de toi.",
                ][i % 3],
                emoji=["❤️", "⭐", "👏"][i % 3],
            )
        )

    await session.flush()
    print("    Enhanced: 3 shared review comments")


# ═══════════════════════════════════════════════════════════════════════════════
# 19. Enhanced Messaging (+3 conversations, +12 messages, +6 receipts)
# ═══════════════════════════════════════════════════════════════════════════════


async def seed_enhanced_messaging(session: AsyncSession) -> None:
    """Add more conversations, messages, and read receipts."""
    now = _now()

    # Conversation 3: Parent 2 ↔ Teacher 2 (about Salma's French grades)
    conv3 = Conversation(
        school_id=SCHOOL_ID,
        type="DIRECT",
        created_by=PARENT_2_ID,
        subject_line="Progres de Salma en Francais",
    )
    session.add(conv3)
    await session.flush()

    session.add_all(
        [
            ConversationParticipant(
                conversation_id=conv3.id,
                user_id=PARENT_2_ID,
                role_in_conversation="INITIATOR",
                joined_at=now,
                muted=False,
            ),
            ConversationParticipant(
                conversation_id=conv3.id,
                user_id=TEACHER_2_ID,
                role_in_conversation="PARTICIPANT",
                joined_at=now,
                muted=False,
            ),
        ]
    )

    msgs_conv3 = [
        Message(
            conversation_id=conv3.id,
            sender_id=PARENT_2_ID,
            body="Bonjour Mme Cherkaoui, comment se porte Salma en redaction?",
            sent_at=now,
        ),
        Message(
            conversation_id=conv3.id,
            sender_id=TEACHER_2_ID,
            body="Bonjour Mme Idrissi, Salma fait de reels progres. Sa derniere redaction etait tres creative.",
            sent_at=now + timedelta(minutes=20),
        ),
        Message(
            conversation_id=conv3.id,
            sender_id=PARENT_2_ID,
            body="C'est une excellente nouvelle, merci beaucoup!",
            sent_at=now + timedelta(minutes=35),
        ),
    ]
    session.add_all(msgs_conv3)
    await session.flush()

    # Read receipts for conv3
    for msg in msgs_conv3[1:]:
        session.add(
            MessageReadReceipt(
                message_id=msg.id,
                user_id=PARENT_2_ID if msg.sender_id == TEACHER_2_ID else TEACHER_2_ID,
                read_at=msg.sent_at + timedelta(minutes=5),
            )
        )

    # Conversation 4: Admin → All teachers (broadcast)
    conv4 = Conversation(
        school_id=SCHOOL_ID,
        type="GROUP",
        created_by=ADMIN_ID,
        subject_line="Nouvelles directives — evaluation du 2eme semestre",
    )
    session.add(conv4)
    await session.flush()

    for uid in [ADMIN_ID, TEACHER_1_ID, TEACHER_2_ID, DIRECTOR_ID]:
        session.add(
            ConversationParticipant(
                conversation_id=conv4.id,
                user_id=uid,
                role_in_conversation="INITIATOR" if uid == ADMIN_ID else "PARTICIPANT",
                joined_at=now,
                muted=False,
            )
        )

    msgs_conv4 = [
        Message(
            conversation_id=conv4.id,
            sender_id=ADMIN_ID,
            body="Chers collegues, merci de respecter les nouvelles grilles d'evaluation pour le 2eme semestre.",
            sent_at=now,
        ),
        Message(
            conversation_id=conv4.id,
            sender_id=TEACHER_1_ID,
            body="Bien recu. Les grilles sont deja integrees dans mes controles.",
            sent_at=now + timedelta(minutes=5),
        ),
        Message(
            conversation_id=conv4.id,
            sender_id=DIRECTOR_ID,
            body="Merci pour la reactivite de tous.",
            sent_at=now + timedelta(minutes=15),
        ),
    ]
    session.add_all(msgs_conv4)
    await session.flush()

    # Conversation 5: Parent 1 ↔ Admin (billing inquiry)
    conv5 = Conversation(
        school_id=SCHOOL_ID,
        type="DIRECT",
        created_by=PARENT_1_ID,
        subject_line="Question sur la facture de mars",
    )
    session.add(conv5)
    await session.flush()

    session.add_all(
        [
            ConversationParticipant(
                conversation_id=conv5.id,
                user_id=PARENT_1_ID,
                role_in_conversation="INITIATOR",
                joined_at=now,
                muted=False,
            ),
            ConversationParticipant(
                conversation_id=conv5.id,
                user_id=ADMIN_ID,
                role_in_conversation="PARTICIPANT",
                joined_at=now,
                muted=False,
            ),
        ]
    )

    msgs_conv5 = [
        Message(
            conversation_id=conv5.id,
            sender_id=PARENT_1_ID,
            body="Bonjour, je ne comprends pas le montant de la derniere facture. Pouvez-vous m'expliquer?",
            sent_at=now,
        ),
        Message(
            conversation_id=conv5.id,
            sender_id=ADMIN_ID,
            body="Bonjour M. Alaoui, il s'agit des frais de scolarite du semestre 2 + les frais de transport. Je vous envoie le detail.",
            sent_at=now + timedelta(minutes=10),
        ),
        Message(
            conversation_id=conv5.id,
            sender_id=PARENT_1_ID,
            body="Merci pour la clarification.",
            sent_at=now + timedelta(minutes=25),
        ),
        Message(
            conversation_id=conv5.id,
            sender_id=ADMIN_ID,
            body="Je vous en prie. N'hesitez pas si vous avez d'autres questions.",
            sent_at=now + timedelta(minutes=30),
        ),
    ]
    session.add_all(msgs_conv5)
    await session.flush()

    # Read receipts
    for msg in msgs_conv5[1:]:
        reader = PARENT_1_ID if msg.sender_id == ADMIN_ID else ADMIN_ID
        session.add(
            MessageReadReceipt(
                message_id=msg.id,
                user_id=reader,
                read_at=msg.sent_at + timedelta(minutes=3),
            )
        )

    await session.flush()
    print("    Enhanced: +3 conversations, +10 messages, +6 read receipts")


# ═══════════════════════════════════════════════════════════════════════════════
# 20. Enhanced Notifications (+8 across all categories)
# ═══════════════════════════════════════════════════════════════════════════════


async def seed_enhanced_notifications(session: AsyncSession) -> None:
    """Add more notifications with varied categories and delivery statuses."""
    from app.models.com import (
        DeliveryChannel,
        DeliveryStatus,
        NotificationCategory,
        NotificationPriority,
    )

    notifications = [
        Notification(
            school_id=SCHOOL_ID,
            parent_id=PARENT_1_ID,
            event_ref="grade:published:math",
            idempotency_key=f"notif-grade-{uuid.uuid4()}",
            category=NotificationCategory.ACADEMIC.value,
            priority=NotificationPriority.NORMAL.value,
            title="Nouvelle note publiee — Mathematiques",
            body="La note du controle de geometrie de Yassine a ete publiee: 16.5/20.",
            read_at=_now() - timedelta(hours=2),
        ),
        Notification(
            school_id=SCHOOL_ID,
            parent_id=PARENT_1_ID,
            event_ref="invoice:overdue",
            idempotency_key=f"notif-bill-{uuid.uuid4()}",
            category=NotificationCategory.BILLING.value,
            priority=NotificationPriority.HIGH.value,
            title="Facture en retard de paiement",
            body="Votre facture de mars 2026 est arrivee a echeance. Merci de regulariser votre situation.",
        ),
        Notification(
            school_id=SCHOOL_ID,
            parent_id=PARENT_2_ID,
            event_ref="attendance:late",
            idempotency_key=f"notif-att-{uuid.uuid4()}",
            category=NotificationCategory.ATTENDANCE.value,
            priority=NotificationPriority.NORMAL.value,
            title="Retard signale — Salma",
            body="Salma a ete signalee en retard ce matin (15 min).",
            read_at=_now() - timedelta(days=1),
        ),
        Notification(
            school_id=SCHOOL_ID,
            parent_id=PARENT_2_ID,
            event_ref="announcement:school_event",
            idempotency_key=f"notif-ann-{uuid.uuid4()}",
            category=NotificationCategory.ANNOUNCEMENT.value,
            priority=NotificationPriority.LOW.value,
            title="Nouvelle annonce: Sortie pedagogique",
            body="Une sortie au musee des sciences est prevue le 15 mai 2026.",
            read_at=_now() - timedelta(hours=5),
        ),
        Notification(
            school_id=SCHOOL_ID,
            parent_id=PARENT_1_ID,
            event_ref="system:password_changed",
            idempotency_key=f"notif-sys-{uuid.uuid4()}",
            category=NotificationCategory.SYSTEM.value,
            priority=NotificationPriority.CRITICAL.value,
            title="Changement de mot de passe",
            body="Votre mot de passe a ete modifie avec succes.",
            read_at=_now() - timedelta(minutes=30),
        ),
        Notification(
            school_id=SCHOOL_ID,
            parent_id=PARENT_2_ID,
            event_ref="grade:published:french",
            idempotency_key=f"notif-grade2-{uuid.uuid4()}",
            category=NotificationCategory.ACADEMIC.value,
            priority=NotificationPriority.NORMAL.value,
            title="Nouvelle note — Francais",
            body="La note de redaction de Salma a ete publiee: 14/20.",
        ),
        Notification(
            school_id=SCHOOL_ID,
            parent_id=PARENT_1_ID,
            event_ref="billing:payment_received",
            idempotency_key=f"notif-pay-{uuid.uuid4()}",
            category=NotificationCategory.BILLING.value,
            priority=NotificationPriority.NORMAL.value,
            title="Paiement recu",
            body="Nous avons bien recu votre paiement de 3 500 MAD. Merci!",
            read_at=_now() - timedelta(days=2),
        ),
        Notification(
            school_id=SCHOOL_ID,
            parent_id=PARENT_2_ID,
            event_ref="system:maintenance",
            idempotency_key=f"notif-maint-{uuid.uuid4()}",
            category=NotificationCategory.SYSTEM.value,
            priority=NotificationPriority.HIGH.value,
            title="Maintenance planifiee",
            body="La plateforme sera indisponible le 10 mai 2026 de 2h a 4h du matin.",
            read_at=_now() - timedelta(hours=12),
        ),
    ]
    session.add_all(notifications)
    await session.flush()

    # Delivery records
    for notif in notifications:
        for channel in [DeliveryChannel.IN_APP.value, DeliveryChannel.EMAIL.value]:
            session.add(
                NotificationDelivery(
                    school_id=SCHOOL_ID,
                    notification_id=notif.id,
                    channel=channel,
                    status=DeliveryStatus.DELIVERED.value
                    if notif.read_at
                    else DeliveryStatus.SENT.value,
                    delivered_at=notif.read_at,
                )
            )

    await session.flush()
    print("    Enhanced: +8 notifications, +16 delivery records")


# ═══════════════════════════════════════════════════════════════════════════════
# 21. School 2 Minimal Multi-Tenant Data
# ═══════════════════════════════════════════════════════════════════════════════


async def seed_school_2_minimal(session: AsyncSession) -> None:
    """Seed minimal data for School 2 (Ecole Atlas) to demo multi-tenancy."""
    # Users for School 2
    s2_admin = uuid.UUID("10000000-0000-4000-8000-000000000040")
    s2_teacher = uuid.UUID("10000000-0000-4000-8000-000000000041")
    s2_parent = uuid.UUID("10000000-0000-4000-8000-000000000042")
    s2_student = uuid.UUID("10000000-0000-4000-8000-000000000043")
    s2_year = uuid.UUID("20000000-0000-4000-8000-000000000020")
    s2_period = uuid.UUID("20000000-0000-4000-8000-000000000021")
    s2_class = uuid.UUID("20000000-0000-4000-8000-000000000022")

    session.add_all(
        [
            User(
                id=s2_admin,
                email="admin@ecole-atlas.ma",
                full_name="Karim Naciri",
                password_hash=_demo_password_hash("admin123"),
                status="active",
                school_id=SCHOOL_ID_2,
            ),
            User(
                id=s2_teacher,
                email="prof@ecole-atlas.ma",
                full_name="Leila Saidi",
                password_hash=_demo_password_hash("teacher123"),
                status="active",
                school_id=SCHOOL_ID_2,
            ),
            User(
                id=s2_parent,
                email="parent@ecole-atlas.ma",
                full_name="Ahmed Lahlou",
                phone="+212611111222",
                password_hash=_demo_password_hash("parent123"),
                status="active",
                school_id=SCHOOL_ID_2,
            ),
            User(
                id=s2_student,
                email="enfant@ecole-atlas.ma",
                full_name="Youssef Lahlou",
                password_hash=_demo_password_hash("student123"),
                status="active",
                school_id=SCHOOL_ID_2,
            ),
        ]
    )
    await session.flush()

    session.add_all(
        [
            Membership(
                user_id=s2_admin,
                school_id=SCHOOL_ID_2,
                role_code="ADM",
                status="active",
            ),
            Membership(
                user_id=s2_teacher,
                school_id=SCHOOL_ID_2,
                role_code="TCH",
                status="active",
            ),
            Membership(
                user_id=s2_parent,
                school_id=SCHOOL_ID_2,
                role_code="PAR",
                status="active",
            ),
            Membership(
                user_id=s2_student,
                school_id=SCHOOL_ID_2,
                role_code="STD",
                status="active",
            ),
        ]
    )

    # Academic year & period
    session.add(
        AcademicYear(
            id=s2_year,
            school_id=SCHOOL_ID_2,
            label="2025-2026",
            date_start=date(2025, 9, 1),
            date_end=date(2026, 6, 30),
        )
    )
    await session.flush()
    session.add(
        Period(
            id=s2_period,
            school_id=SCHOOL_ID_2,
            academic_year_id=s2_year,
            label="Semestre 1",
            status="active",
            date_start=date(2025, 9, 1),
            date_end=date(2026, 1, 31),
        )
    )
    await session.flush()

    # Class
    session.add(
        Class(
            id=s2_class,
            school_id=SCHOOL_ID_2,
            code="3AC-A",
            academic_year_id=s2_year,
            name="3ème Année Collège - A",
            level_band="3AC",
            cycle="college",
        )
    )
    await session.flush()

    session.add(
        TeacherAssignment(
            teacher_id=s2_teacher,
            class_id=s2_class,
            period_id=s2_period,
            school_id=SCHOOL_ID_2,
        )
    )

    # Enrollment
    session.add(
        Enrollment(
            student_id=s2_student,
            class_id=s2_class,
            period_id=s2_period,
            school_id=SCHOOL_ID_2,
            status="active",
        )
    )

    # Profiles
    session.add(
        StudentProfile(
            user_id=s2_student,
            school_id=SCHOOL_ID_2,
            student_number="STD-ATLAS-001",
            date_of_birth=date(2012, 5, 10),
            gender="male",
            class_level="3eme",
            nationality="Marocaine",
        )
    )
    session.add(
        ParentProfile(
            user_id=s2_parent,
            school_id=SCHOOL_ID_2,
            relationship_type="father",
            cin_number="XY123456",
            address="45 Avenue Mohammed V, Rabat",
            profession="Fonctionnaire",
            emergency_phone="+212611111222",
        )
    )
    session.add(
        TeacherProfile(
            user_id=s2_teacher,
            school_id=SCHOOL_ID_2,
            employee_id="TCH-ATLAS-001",
            subject_specialty="Sciences",
            qualification="Licence en Sciences",
            hire_date=date(2022, 9, 1),
        )
    )

    # Parent-child link
    session.add(
        ParentChildLink(
            parent_user_id=s2_parent,
            child_user_id=s2_student,
            school_id=SCHOOL_ID_2,
            status="active",
            linked_at=_now(),
            linked_by=s2_admin,
        )
    )

    # One invoice
    inv = Invoice(
        school_id=SCHOOL_ID_2,
        parent_id=s2_parent,
        period_id=s2_period,
        status="pending",
        total_amount=4000.00,
        currency="MAD",
        issued_date=date(2026, 3, 1),
        due_date=date(2026, 3, 31),
    )
    session.add(inv)
    await session.flush()

    session.add(
        InvoiceItem(
            invoice_id=inv.id,
            description="Frais de scolarite",
            amount=4000.00,
            unit_price=4000.00,
            quantity=1,
            tva_rate=0.0,
            tva_amount=0.0,
            amount_ht=4000.00,
            amount_ttc=4000.00,
        )
    )

    # One announcement
    session.add(
        Announcement(
            school_id=SCHOOL_ID_2,
            author_id=s2_admin,
            title="Bienvenue a Ecole Atlas",
            body="Cheres familles, bienvenue sur la plateforme Ecole Atlas pour l'annee scolaire 2025-2026.",
            target_roles=["PAR", "STD", "TCH"],
            published_at=_now(),
            status="PUBLISHED",
        )
    )

    await session.flush()
    print(
        "    Enhanced: School 2 (Ecole Atlas) — 4 users, 1 class, 1 invoice, 1 announcement"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 22. Timetable Extras (constraints, generation jobs)
# ═══════════════════════════════════════════════════════════════════════════════


async def seed_timetable_extras(session: AsyncSession) -> None:
    """Seed timetable constraints and a generation job."""
    session.add_all(
        [
            TimetableConstraint(
                school_id=SCHOOL_ID,
                academic_year_id=YEAR_ID,
                constraint_type="max_hours_per_day",
                entity_id=TEACHER_1_ID,
                params={"max_hours": 6},
            ),
            TimetableConstraint(
                school_id=SCHOOL_ID,
                academic_year_id=YEAR_ID,
                constraint_type="no_consecutive_same_subject",
                entity_id=None,
                params={"apply_to_all_classes": True},
            ),
        ]
    )

    session.add(
        TimetableGenerationJob(
            school_id=SCHOOL_ID,
            academic_year_id=YEAR_ID,
            status=TimetableJobStatus.COMPLETED.value,
            constraints_snapshot={"max_hours_per_day": 6, "no_consecutive": True},
            result_payload={"slots": 24, "conflicts": 0},
            result_slot_count=24,
            conflicts_found=0,
            started_at=_now() - timedelta(hours=2),
            completed_at=_now() - timedelta(hours=1),
        )
    )

    await session.flush()
    print("    Enhanced: 2 timetable constraints, 1 generation job")


# ═══════════════════════════════════════════════════════════════════════════════
# 23. Program Assignment Events
# ═══════════════════════════════════════════════════════════════════════════════


async def seed_program_assignment_events(session: AsyncSession) -> None:
    """Seed program assignment history for audit trail."""
    from app.models.erp import Program, ProgramVersion

    programs = (
        (
            await session.execute(
                select(Program).where(Program.school_id == SCHOOL_ID).limit(2)
            )
        )
        .scalars()
        .all()
    )
    if not programs:
        print("    Program assignment events: skipped (no program)")
        return

    program = programs[0]
    program2 = programs[1] if len(programs) > 1 else None

    versions = await session.execute(
        select(ProgramVersion).where(ProgramVersion.program_id == program.id).limit(1)
    )
    version = versions.scalar_one_or_none()

    # Find an enrollment for Yassine
    enrollments = await session.execute(
        select(Enrollment)
        .where(Enrollment.student_id == STUDENT_1_ID, Enrollment.school_id == SCHOOL_ID)
        .limit(1)
    )
    enrollment = enrollments.scalar_one_or_none()

    # Initial assignment
    session.add(
        ProgramAssignmentEvent(
            school_id=SCHOOL_ID,
            student_id=STUDENT_1_ID,
            academic_year_id=YEAR_ID,
            period_id=PERIOD_1_ID,
            from_program_id=None,
            to_program_id=program.id,
            from_program_version_id=None,
            to_program_version_id=version.id if version else None,
            from_enrollment_id=None,
            to_enrollment_id=enrollment.id if enrollment else None,
            reason_code="INITIAL",
            reason_note="Inscription initiale au programme bilingue.",
            actor_user_id=ADMIN_ID,
            occurred_at=_now() - timedelta(days=180),
            created_at=_now() - timedelta(days=180),
        )
    )

    # Transfer to a different program (or skip if only one program exists)
    if program2:
        session.add(
            ProgramAssignmentEvent(
                school_id=SCHOOL_ID,
                student_id=STUDENT_1_ID,
                academic_year_id=YEAR_ID,
                period_id=PERIOD_2_ID,
                from_program_id=program.id,
                to_program_id=program2.id,
                from_program_version_id=version.id if version else None,
                to_program_version_id=None,
                from_enrollment_id=enrollment.id if enrollment else None,
                to_enrollment_id=enrollment.id if enrollment else None,
                reason_code="TRANSFER",
                reason_note="Changement de programme pour l'annee scolaire.",
                actor_user_id=DIRECTOR_ID,
                occurred_at=_now() - timedelta(days=30),
                created_at=_now() - timedelta(days=30),
            )
        )

    await session.flush()
    print("    Enhanced: 2 program assignment events")


# ═══════════════════════════════════════════════════════════════════════════════
# 22. Misc empty tables — push coverage over 90%
# ═══════════════════════════════════════════════════════════════════════════════


async def seed_misc_empty_tables(session: AsyncSession) -> None:
    """Seed remaining empty tables to reach ~90%+ coverage."""
    from app.models.iam import InvitationCode
    from app.models.documents import Resource, ResourceRating

    # Admin + Content Manager profiles
    session.add_all(
        [
            AdminProfile(
                id=uuid.uuid4(),
                school_id=SCHOOL_ID,
                user_id=ADMIN_ID,
                department="Direction",
                management_level="senior",
                can_approve_budgets=True,
            ),
            ContentManagerProfile(
                id=uuid.uuid4(),
                school_id=SCHOOL_ID,
                user_id=CONTENT_MGR_ID,
                specialization="Contenus pédagogiques K-12",
                languages_managed='["fr", "ar"]',
                approved_subjects='["math", "french", "activite_scientifique"]',
            ),
        ]
    )

    # Invitation codes
    session.add_all(
        [
            InvitationCode(
                id=uuid.uuid4(),
                school_id=SCHOOL_ID,
                issuer_user_id=ADMIN_ID,
                code_hash=_invitation_code_hash("PARDMO01"),
                role_target="PAR",
                expires_at=_now() + timedelta(days=30),
            ),
            InvitationCode(
                id=uuid.uuid4(),
                school_id=SCHOOL_ID,
                issuer_user_id=ADMIN_ID,
                code_hash=_invitation_code_hash("TCHDMO02"),
                role_target="TCH",
                expires_at=_now() + timedelta(days=30),
            ),
            InvitationCode(
                id=uuid.uuid4(),
                school_id=SCHOOL_ID,
                issuer_user_id=ADMIN_ID,
                code_hash=_invitation_code_hash("USEDPAR3"),
                role_target="PAR",
                consumed_by=PARENT_1_ID,
                consumed_at=_now() - timedelta(days=10),
                expires_at=_now() + timedelta(days=20),
            ),
        ]
    )

    # Resource ratings (need existing resources)
    resources = (
        (
            await session.execute(
                select(Resource).where(Resource.school_id == SCHOOL_ID).limit(3)
            )
        )
        .scalars()
        .all()
    )
    if resources:
        session.add_all(
            [
                ResourceRating(
                    id=uuid.uuid4(),
                    resource_id=resources[0].id,
                    user_id=TEACHER_1_ID,
                    rating=5,
                ),
                ResourceRating(
                    id=uuid.uuid4(),
                    resource_id=resources[0].id,
                    user_id=TEACHER_2_ID,
                    rating=4,
                ),
                ResourceRating(
                    id=uuid.uuid4(),
                    resource_id=resources[1].id
                    if len(resources) > 1
                    else resources[0].id,
                    user_id=TEACHER_1_ID,
                    rating=4,
                ),
            ]
        )

    await session.flush()
    print(
        "    Enhanced: +2 admin/CM profiles, +3 invitation codes, +3 resource ratings"
    )


# ====================== merged from seed_extensions.py ======================
"""Seed extensions for newer features not covered by main seed.py.

Run automatically via `make seed` (called from app.seed.main).
"""


import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import AIPreference, WritingAttempt
from app.models.calendar import (
    Event,
    EventRSVP,
    EventReminder,
    EventReminderChannel,
    EventRsvpStatus,
    EventType,
    EventVisibility,
)
from app.models.documents import (
    Document,
    DocumentCategory,
    DocumentVersion,
    Resource,
    ResourceType,
    ResourceVisibility,
)
from app.models.erp import (
    EligibilityRule,
    EligibilityRuleKind,
    Program,
    ProgramEquivalence,
    ProgramEquivalenceKind,
    ProgramVersion,
)
from app.models.iam import User
from app.models.reporting import ReportJob, ReportJobStatus, ReportSchedule, ReportType
from app.models.school import School

SCHOOL_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")


async def seed_calendar(session: AsyncSession) -> None:
    """Seed calendar events, RSVPs, and reminders (enhanced: 8 events)."""
    schools = (await session.execute(select(School))).scalars().all()
    if not schools:
        return

    school = schools[0]
    users = (
        (await session.execute(select(User).where(User.school_id == school.id)))
        .scalars()
        .all()
    )
    creator_id = users[0].id if users else None
    now = datetime.now(timezone.utc)

    events = [
        Event(
            id=uuid.uuid4(),
            school_id=school.id,
            title_fr="Journée Portes Ouvertes",
            title_ar="يوم الأبواب المفتوحة",
            description="Rencontre parents-enseignants pour le premier trimestre.",
            type=EventType.MEETING.value,
            visibility=EventVisibility.SCHOOL.value,
            start_at=now + timedelta(days=7),
            end_at=now + timedelta(days=7, hours=4),
            location="Salle des fêtes",
            created_by=creator_id,
        ),
        Event(
            id=uuid.uuid4(),
            school_id=school.id,
            title_fr="Examen de Mathématiques — 6ème A",
            title_ar="امتحان الرياضيات — السادس أ",
            description="Contrôle sur les fractions et les équations.",
            type=EventType.EXAM.value,
            visibility=EventVisibility.CLASS.value,
            start_at=now + timedelta(days=14),
            end_at=now + timedelta(days=14, hours=2),
            location="Salle 102",
            created_by=creator_id,
            class_id=None,
        ),
        Event(
            id=uuid.uuid4(),
            school_id=school.id,
            title_fr="Excursion au Musée des Sciences",
            title_ar="رحلة إلى متحف العلوم",
            description="Sortie pédagogique pour les classes de CM1 et CM2.",
            type=EventType.EXCURSION.value,
            visibility=EventVisibility.SCHOOL.value,
            start_at=now + timedelta(days=21),
            end_at=now + timedelta(days=21, hours=6),
            location="Musée des Sciences, Casablanca",
            created_by=creator_id,
        ),
        Event(
            id=uuid.uuid4(),
            school_id=school.id,
            title_fr="Réunion des parents d'élèves",
            title_ar="اجتماع أولياء التلاميذ",
            description="Réunion trimestrielle pour discuter des progrès des élèves.",
            type=EventType.MEETING.value,
            visibility=EventVisibility.SCHOOL.value,
            start_at=now + timedelta(days=28),
            end_at=now + timedelta(days=28, hours=3),
            location="Amphithéâtre",
            created_by=creator_id,
        ),
        Event(
            id=uuid.uuid4(),
            school_id=school.id,
            title_fr="Concours de lecture — 5ème",
            title_ar="مسابقة القراءة — الخامس",
            description="Compétition inter-classes de lecture à voix haute.",
            type=EventType.CEREMONY.value,
            visibility=EventVisibility.CLASS.value,
            start_at=now + timedelta(days=10),
            end_at=now + timedelta(days=10, hours=2),
            location="Bibliothèque",
            created_by=creator_id,
        ),
        Event(
            id=uuid.uuid4(),
            school_id=school.id,
            title_fr="Atelier robotique — Maternelle",
            title_ar="ورشة الروبوتات — التمهيدي",
            description="Découverte de la robotique éducative pour les plus jeunes.",
            type=EventType.CUSTOM.value,
            visibility=EventVisibility.SCHOOL.value,
            start_at=now + timedelta(days=35),
            end_at=now + timedelta(days=35, hours=3),
            location="Salle informatique",
            created_by=creator_id,
        ),
        Event(
            id=uuid.uuid4(),
            school_id=school.id,
            title_fr="Fête de fin d'année",
            title_ar="حفلة نهاية السنة",
            description="Célébration de fin d'année scolaire avec spectacles et remise des prix.",
            type=EventType.CEREMONY.value,
            visibility=EventVisibility.SCHOOL.value,
            start_at=now + timedelta(days=60),
            end_at=now + timedelta(days=60, hours=5),
            location="Cour de l'école",
            created_by=creator_id,
        ),
        Event(
            id=uuid.uuid4(),
            school_id=school.id,
            title_fr="Examen de Français — 6ème B",
            title_ar="امتحان الفرنسية — السادس ب",
            description="Contrôle de grammaire et conjugaison.",
            type=EventType.EXAM.value,
            visibility=EventVisibility.CLASS.value,
            start_at=now + timedelta(days=16),
            end_at=now + timedelta(days=16, hours=2),
            location="Salle 103",
            created_by=creator_id,
        ),
    ]
    session.add_all(events)
    await session.flush()

    # RSVPs for first 3 events
    rsvp_count = 0
    if len(users) >= 3:
        rsvps = []
        for evt in events[:3]:
            for u in users[1:4]:
                rsvps.append(
                    EventRSVP(
                        id=uuid.uuid4(),
                        event_id=evt.id,
                        user_id=u.id,
                        status=EventRsvpStatus.ATTENDING.value
                        if u.id == users[1].id
                        else EventRsvpStatus.MAYBE.value,
                        responded_at=now,
                    )
                )
        session.add_all(rsvps)
        rsvp_count = len(rsvps)

    # Reminders for multiple events
    reminders = [
        EventReminder(
            id=uuid.uuid4(),
            event_id=events[0].id,
            remind_at=events[0].start_at - timedelta(days=1),
            channel=EventReminderChannel.IN_APP.value,
        ),
        EventReminder(
            id=uuid.uuid4(),
            event_id=events[1].id,
            remind_at=events[1].start_at - timedelta(hours=2),
            channel=EventReminderChannel.PUSH.value,
        ),
        EventReminder(
            id=uuid.uuid4(),
            event_id=events[2].id,
            remind_at=events[2].start_at - timedelta(days=2),
            channel=EventReminderChannel.IN_APP.value,
        ),
        EventReminder(
            id=uuid.uuid4(),
            event_id=events[3].id,
            remind_at=events[3].start_at - timedelta(days=1),
            channel=EventReminderChannel.IN_APP.value,
        ),
        EventReminder(
            id=uuid.uuid4(),
            event_id=events[6].id,
            remind_at=events[6].start_at - timedelta(days=7),
            channel=EventReminderChannel.PUSH.value,
        ),
    ]
    session.add_all(reminders)

    print(
        f"    Calendar: {len(events)} events, {rsvp_count} RSVPs, {len(reminders)} reminders"
    )


async def seed_documents(session: AsyncSession) -> None:
    """Seed documents, versions, and shared resources (enhanced: 4 docs, 5 resources)."""
    schools = (await session.execute(select(School))).scalars().all()
    if not schools:
        return

    school = schools[0]
    users = (
        (
            await session.execute(
                select(User).where(User.school_id == school.id).limit(3)
            )
        )
        .scalars()
        .all()
    )
    owner_id = users[0].id if users else None

    docs = [
        Document(
            id=uuid.uuid4(),
            school_id=school.id,
            filename="bulletin_yassine_t1.pdf",
            original_filename="Bulletin Trimestriel — Yassine Alaoui.pdf",
            mime_type="application/pdf",
            size_bytes=245_760,
            sha256="a" * 64,
            storage_path="documents/report_cards/bulletin_yassine_t1.pdf",
            category=DocumentCategory.REPORT_CARD.value,
            uploader_id=owner_id,
        ),
        Document(
            id=uuid.uuid4(),
            school_id=school.id,
            filename="certificat_salma.pdf",
            original_filename="Certificat de scolarité — Salma Idrissi.pdf",
            mime_type="application/pdf",
            size_bytes=128_000,
            sha256="b" * 64,
            storage_path="documents/admin/certificat_salma.pdf",
            category=DocumentCategory.CERTIFICATE.value,
            uploader_id=owner_id,
        ),
        Document(
            id=uuid.uuid4(),
            school_id=school.id,
            filename="autorisation_excursion_mai.pdf",
            original_filename="Autorisation parentale — Excursion mai 2026.pdf",
            mime_type="application/pdf",
            size_bytes=95_000,
            sha256="c" * 64,
            storage_path="documents/admin/autorisation_excursion_mai.pdf",
            category=DocumentCategory.OTHER.value,
            uploader_id=owner_id,
        ),
        Document(
            id=uuid.uuid4(),
            school_id=school.id,
            filename="releve_omar_s2.pdf",
            original_filename="Relevé de notes — Omar Alaoui.pdf",
            mime_type="application/pdf",
            size_bytes=210_000,
            sha256="d" * 64,
            storage_path="documents/report_cards/releve_omar_s2.pdf",
            category=DocumentCategory.REPORT_CARD.value,
            uploader_id=owner_id,
        ),
    ]
    session.add_all(docs)
    await session.flush()

    # Document versions (2 versions for first doc)
    session.add(
        DocumentVersion(
            id=uuid.uuid4(),
            document_id=docs[0].id,
            version_number=1,
            uploader_id=owner_id,
            filename="bulletin_yassine_t1.pdf",
            original_filename="Bulletin Trimestriel — Yassine Alaoui.pdf",
            mime_type="application/pdf",
            storage_path="documents/report_cards/bulletin_yassine_t1.pdf",
            size_bytes=245_760,
            sha256="a" * 64,
        )
    )
    session.add(
        DocumentVersion(
            id=uuid.uuid4(),
            document_id=docs[0].id,
            version_number=2,
            uploader_id=owner_id,
            filename="bulletin_yassine_t1_v2.pdf",
            original_filename="Bulletin Trimestriel — Yassine Alaoui (v2).pdf",
            mime_type="application/pdf",
            storage_path="documents/report_cards/bulletin_yassine_t1_v2.pdf",
            size_bytes=248_000,
            sha256="e" * 64,
            change_note="Correction de la moyenne generale",
        )
    )

    # Shared resources — each resource needs a file_id pointing to a document
    resources = [
        Resource(
            id=uuid.uuid4(),
            school_id=school.id,
            uploader_id=owner_id,
            title="Plan de cours — Mathématiques CP",
            description="Plan detaille pour le premier semestre",
            subject="math",
            level="CP",
            type=ResourceType.LESSON_PLAN.value,
            tags=["math", "CP", "semestre1"],
            file_id=docs[0].id,
            visibility=ResourceVisibility.SCHOOL.value,
        ),
        Resource(
            id=uuid.uuid4(),
            school_id=school.id,
            uploader_id=owner_id,
            title="Fiche d'exercices — Fractions",
            description="Exercices sur les fractions pour 6eme",
            subject="math",
            level="6eme",
            type=ResourceType.WORKSHEET.value,
            tags=["math", "6eme", "fractions"],
            file_id=docs[1].id,
            visibility=ResourceVisibility.SCHOOL.value,
        ),
        Resource(
            id=uuid.uuid4(),
            school_id=school.id,
            uploader_id=owner_id,
            title="Guide pédagogique — Lecture CE1",
            description="Guide complet pour l'enseignement de la lecture",
            subject="french",
            level="CE1",
            type=ResourceType.REFERENCE.value,
            tags=["lecture", "CE1", "guide"],
            file_id=docs[2].id,
            visibility=ResourceVisibility.SCHOOL.value,
        ),
        Resource(
            id=uuid.uuid4(),
            school_id=school.id,
            uploader_id=owner_id,
            title="Évaluation diagnostic — 6ème Maths",
            description="Test de positionnement en debut d'annee",
            subject="math",
            level="6eme",
            type=ResourceType.EXAM_TEMPLATE.value,
            tags=["math", "6eme", "diagnostic"],
            file_id=docs[3].id,
            visibility=ResourceVisibility.CLASS.value,
        ),
        Resource(
            id=uuid.uuid4(),
            school_id=school.id,
            uploader_id=owner_id,
            title="Fiche de suivi comportemental",
            description="Outil de suivi du comportement en classe",
            subject="pedagogy",
            level="all",
            type=ResourceType.WORKSHEET.value,
            tags=["comportement", "suivi", "classe"],
            file_id=docs[0].id,
            visibility=ResourceVisibility.SCHOOL.value,
        ),
    ]
    session.add_all(resources)

    print(
        f"    Documents: {len(docs)} documents + 2 versions, {len(resources)} shared resources"
    )


async def seed_reporting(session: AsyncSession) -> None:
    """Seed report schedules and jobs (enhanced: 3 schedules, 6 jobs)."""
    schools = (await session.execute(select(School))).scalars().all()
    if not schools:
        return

    school = schools[0]
    users = (
        (
            await session.execute(
                select(User).where(User.school_id == school.id).limit(2)
            )
        )
        .scalars()
        .all()
    )
    creator_id = users[0].id if users else None

    schedules = [
        ReportSchedule(
            id=uuid.uuid4(),
            school_id=school.id,
            created_by=creator_id,
            report_type=ReportType.ATTENDANCE_REPORT.value,
            frequency="monthly",
            parameters={"period": "current_month"},
            recipient_roles=["ADM", "DIR"],
            enabled=True,
        ),
        ReportSchedule(
            id=uuid.uuid4(),
            school_id=school.id,
            created_by=creator_id,
            report_type=ReportType.STUDENT_REPORT_CARD.value,
            frequency="trimestrial",
            parameters={"trimester": 2},
            recipient_roles=["ADM", "DIR", "PAR"],
            enabled=True,
        ),
        ReportSchedule(
            id=uuid.uuid4(),
            school_id=school.id,
            created_by=creator_id,
            report_type=ReportType.BILLING_STATEMENT.value,
            frequency="monthly",
            parameters={"month": "current"},
            recipient_roles=["ADM"],
            enabled=True,
        ),
    ]
    session.add_all(schedules)
    await session.flush()

    jobs = [
        ReportJob(
            id=uuid.uuid4(),
            school_id=school.id,
            requester_id=creator_id,
            type=ReportType.ATTENDANCE_REPORT.value,
            parameters={"period": "2025-04"},
            parameters_hash="hash1",
            status=ReportJobStatus.READY.value,
            file_path="reports/attendance_2025_04.pdf",
            file_size=128000,
            mime_type="application/pdf",
            completed_at=datetime.now(timezone.utc) - timedelta(days=30),
            expires_at=datetime.now(timezone.utc) + timedelta(days=60),
        ),
        ReportJob(
            id=uuid.uuid4(),
            school_id=school.id,
            requester_id=creator_id,
            type=ReportType.ATTENDANCE_REPORT.value,
            parameters={"period": "2025-05"},
            parameters_hash="hash2",
            status=ReportJobStatus.PENDING.value,
        ),
        ReportJob(
            id=uuid.uuid4(),
            school_id=school.id,
            requester_id=creator_id,
            type=ReportType.STUDENT_REPORT_CARD.value,
            parameters={"trimester": 1},
            parameters_hash="hash3",
            status=ReportJobStatus.READY.value,
            file_path="reports/grades_s1_2025_2026.pdf",
            file_size=256000,
            mime_type="application/pdf",
            completed_at=datetime.now(timezone.utc) - timedelta(days=90),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        ),
        ReportJob(
            id=uuid.uuid4(),
            school_id=school.id,
            requester_id=creator_id,
            type=ReportType.STUDENT_REPORT_CARD.value,
            parameters={"trimester": 2},
            parameters_hash="hash4",
            status=ReportJobStatus.GENERATING.value,
            completed_at=None,
        ),
        ReportJob(
            id=uuid.uuid4(),
            school_id=school.id,
            requester_id=creator_id,
            type=ReportType.BILLING_STATEMENT.value,
            parameters={"month": "2026-03"},
            parameters_hash="hash5",
            status=ReportJobStatus.READY.value,
            file_path="reports/financial_march_2026.pdf",
            file_size=192000,
            mime_type="application/pdf",
            completed_at=datetime.now(timezone.utc) - timedelta(days=35),
            expires_at=datetime.now(timezone.utc) + timedelta(days=90),
        ),
        ReportJob(
            id=uuid.uuid4(),
            school_id=school.id,
            requester_id=creator_id,
            type=ReportType.BILLING_STATEMENT.value,
            parameters={"month": "2026-04"},
            parameters_hash="hash6",
            status=ReportJobStatus.FAILED.value,
            error_message="Connection timeout to MinIO storage backend.",
            completed_at=datetime.now(timezone.utc) - timedelta(days=5),
        ),
    ]
    session.add_all(jobs)

    print(
        f"    Reporting: {len(schedules)} schedules, {len(jobs)} jobs (completed, pending, running, failed)"
    )


async def seed_programs(session: AsyncSession) -> None:
    """Seed academic programs with versions and equivalences (enhanced: 2 programs)."""
    schools = (await session.execute(select(School))).scalars().all()
    if not schools:
        return

    school = schools[0]

    program1 = Program(
        id=uuid.uuid4(),
        school_id=school.id,
        code="BIL-FR-EN",
        name="Programme Bilingue Français-Anglais",
        level="Primaire",
        description="Parcours bilingue renforcé avec 50% des cours en anglais.",
        is_active=True,
        version_label="1.0",
        effective_from=date(2024, 9, 1),
    )
    program2 = Program(
        id=uuid.uuid4(),
        school_id=school.id,
        code="SCI-RENFORCE",
        name="Programme Scientifique Renforcé",
        level="Secondaire",
        description="Parcours avec emphasis sur les sciences, technologie et mathématiques.",
        is_active=True,
        version_label="1.0",
        effective_from=date(2025, 9, 1),
    )
    session.add_all([program1, program2])
    await session.flush()

    version1 = ProgramVersion(
        id=uuid.uuid4(),
        school_id=school.id,
        program_id=program1.id,
        version_label="1.0",
        description="Version initiale du programme bilingue.",
        effective_from=date(2024, 9, 1),
        is_active=True,
    )
    version2 = ProgramVersion(
        id=uuid.uuid4(),
        school_id=school.id,
        program_id=program2.id,
        version_label="1.0",
        description="Version initiale du programme scientifique.",
        effective_from=date(2025, 9, 1),
        is_active=True,
    )
    session.add_all([version1, version2])
    await session.flush()

    # Eligibility rules
    session.add_all(
        [
            EligibilityRule(
                id=uuid.uuid4(),
                school_id=school.id,
                kind=EligibilityRuleKind.ADMISSION.value,
                target_program_id=program1.id,
                condition_type="min_grade_average",
                condition_params={"min_average": 10.0},
                message_key="min_average_required",
                is_active=True,
            ),
            EligibilityRule(
                id=uuid.uuid4(),
                school_id=school.id,
                kind=EligibilityRuleKind.ADMISSION.value,
                target_program_id=program2.id,
                condition_type="min_grade_average",
                condition_params={"min_average": 12.0},
                message_key="min_average_science_required",
                is_active=True,
            ),
        ]
    )

    # Program equivalences
    session.add_all(
        [
            ProgramEquivalence(
                id=uuid.uuid4(),
                school_id=school.id,
                from_program_id=program1.id,
                to_program_id=program2.id,
                kind=ProgramEquivalenceKind.EQUIVALENT.value,
                note="Transfert de credits vers le programme scientifique.",
                ratified_at=date(2025, 1, 15),
            ),
            ProgramEquivalence(
                id=uuid.uuid4(),
                school_id=school.id,
                from_program_id=program2.id,
                to_program_id=program1.id,
                kind=ProgramEquivalenceKind.PARTIAL.value,
                note="Equivalence partielle pour les matieres communes.",
                ratified_at=date(2025, 2, 1),
            ),
        ]
    )

    print("    Programs: 2 programs + 2 versions, 2 eligibility rules, 2 equivalences")


async def seed_ai_preferences(session: AsyncSession) -> None:
    """Seed AI preferences and writing attempts (enhanced: 3 preferences, 4 attempts)."""
    schools = (await session.execute(select(School))).scalars().all()
    if not schools:
        return

    school = schools[0]
    users = (
        (await session.execute(select(User).where(User.school_id == school.id)))
        .scalars()
        .all()
    )
    if len(users) < 3:
        print("    AI: skipped (need 3 users)")
        return

    # AI preferences for 3 users (parent sets preference for child)
    session.add_all(
        [
            AIPreference(
                id=uuid.uuid4(),
                school_id=school.id,
                user_id=users[0].id,
                target_user_id=users[1].id,
                opt_out=False,
            ),
            AIPreference(
                id=uuid.uuid4(),
                school_id=school.id,
                user_id=users[1].id,
                target_user_id=users[2].id,
                opt_out=False,
            ),
            AIPreference(
                id=uuid.uuid4(),
                school_id=school.id,
                user_id=users[2].id,
                target_user_id=users[0].id,
                opt_out=True,
            ),
        ]
    )

    # Writing attempts (4)
    attempts = [
        WritingAttempt(
            id=uuid.uuid4(),
            school_id=school.id,
            student_id=users[1].id,
            topic="Expression ecrite",
            input_text="Le chat est sur la table. Il mange du poisson.",
            input_word_count=9,
            status="completed",
            suggestion="Phrase simple et correcte. Essayez d'ajouter un adjectif.",
            hints={"grammar": "ok", "vocabulary": "simple"},
        ),
        WritingAttempt(
            id=uuid.uuid4(),
            school_id=school.id,
            student_id=users[1].id,
            topic="Expression ecrite en anglais",
            input_text="My name is Yassine. I am twelve years old. I like football.",
            input_word_count=13,
            status="completed",
            suggestion="Simple sentences. Good structure. Try using more connectors.",
            hints={"grammar": "ok", "style": "simple"},
        ),
        WritingAttempt(
            id=uuid.uuid4(),
            school_id=school.id,
            student_id=users[2].id if len(users) > 2 else users[1].id,
            topic="Expression ecrite",
            input_text="Je vais à l'école avec mon ami. Nous aimons les mathématiques.",
            input_word_count=12,
            status="completed",
            suggestion="Bonne utilisation du verbe aller. Essayez d'elaborer.",
            hints={"grammar": "ok", "vocabulary": "good"},
        ),
        WritingAttempt(
            id=uuid.uuid4(),
            school_id=school.id,
            student_id=users[0].id,
            topic="Description",
            input_text="Le soleil brille. Les oiseaux chantent dans le jardin.",
            input_word_count=10,
            status="completed",
            suggestion="Beau vocabulaire descriptif. Continuez dans cette voie.",
            hints={"style": "excellent", "vocabulary": "rich"},
        ),
    ]
    session.add_all(attempts)

    print("    AI: 3 preferences, 4 writing attempts")


async def seed_notification_preferences(session: AsyncSession) -> None:
    """Seed notification preferences and device tokens (enhanced: 9 prefs, 3 devices)."""
    from app.models.com import DeviceToken, NotificationPreference

    schools = (await session.execute(select(School))).scalars().all()
    if not schools:
        return

    school = schools[0]
    users = (
        (
            await session.execute(
                select(User).where(User.school_id == school.id).limit(5)
            )
        )
        .scalars()
        .all()
    )

    categories = ["billing", "academic", "attendance", "announcement", "system"]
    for user in users[:3]:
        for category in categories:
            session.add(
                NotificationPreference(
                    id=uuid.uuid4(),
                    school_id=school.id,
                    user_id=user.id,
                    channel="email",
                    category=category,
                    enabled=category != "system" or user.id == users[0].id,
                )
            )

    # Device tokens
    if users:
        session.add_all(
            [
                DeviceToken(
                    id=uuid.uuid4(),
                    school_id=school.id,
                    user_id=users[0].id,
                    token="fcm-demo-token-android-001",
                    platform="android",
                    device_name="Samsung Galaxy A54",
                    last_active_at=datetime.now(timezone.utc),
                ),
                DeviceToken(
                    id=uuid.uuid4(),
                    school_id=school.id,
                    user_id=users[1].id if len(users) > 1 else users[0].id,
                    token="fcm-demo-token-ios-002",
                    platform="ios",
                    device_name="iPhone 14 Pro",
                    last_active_at=datetime.now(timezone.utc) - timedelta(hours=2),
                ),
                DeviceToken(
                    id=uuid.uuid4(),
                    school_id=school.id,
                    user_id=users[2].id if len(users) > 2 else users[0].id,
                    token="fcm-demo-token-web-003",
                    platform="web",
                    device_name="Chrome Desktop",
                    last_active_at=datetime.now(timezone.utc) - timedelta(days=1),
                ),
            ]
        )

    print("    Notifications: 9 preference records, 3 device tokens")


# ====================== merged from seed_demo_scenarios.py ======================
"""Scenario seeders for role coverage and realistic workflow states.

These rows sit on top of the core domain seed. Keep this file focused on data
that makes screens and review queues useful for demos:
- reference lists used by filters/forms,
- non-empty tabs for role navigation,
- approval/rejection states,
- relationship-heavy micro-school data.
"""


import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.calendar import EventReminderPreference, MoroccanHoliday
from app.models.documents import StudentDocumentRequirement
from app.models.erp import AcademicSnapshot
from app.models.iam import Membership, TeacherProfile, User
from app.models.levels import LevelAgeMapping
from app.models.lms import ContentItem, ContentItemAsset, ContentSubmission
from app.models.micro_school import (
    MicroEnrollment,
    MicroEnrollmentStatus,
    MicroGroup,
    MicroPayment,
    MicroPaymentPeriodType,
    MicroPaymentStatus,
    MicroProgressLog,
    MicroResource,
    MicroResourceType,
    MicroSchool,
    MicroSchoolStatus,
    MicroSchoolType,
)
from app.models.reporting import DataExport, DataExportFormat
from app.models.skill_passport import SkillPassport


SCHOOL_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")
MICRO_SCHOOL_TENANT_ID = uuid.UUID("00000000-0000-4000-8000-000000000003")
YEAR_ID = uuid.UUID("20000000-0000-4000-8000-000000000001")
ADMIN_ID = uuid.UUID("10000000-0000-4000-8000-000000000001")
TEACHER_1_ID = uuid.UUID("10000000-0000-4000-8000-000000000003")
TEACHER_2_ID = uuid.UUID("10000000-0000-4000-8000-000000000004")
PARENT_1_ID = uuid.UUID("10000000-0000-4000-8000-000000000005")
PARENT_2_ID = uuid.UUID("10000000-0000-4000-8000-000000000006")
MICRO_PARENT_2_ID = uuid.UUID("10000000-0000-4000-8000-000000000033")
STUDENT_1_ID = uuid.UUID("10000000-0000-4000-8000-000000000007")
STUDENT_2_ID = uuid.UUID("10000000-0000-4000-8000-000000000008")
STUDENT_CP_ID = uuid.UUID("10000000-0000-4000-8000-00000000000c")
CONTENT_MGR_ID = uuid.UUID("10000000-0000-4000-8000-00000000000b")
MICRO_EDUCATOR_2_ID = uuid.UUID("10000000-0000-4000-8000-000000000031")


def _now() -> datetime:
    return datetime.now(UTC)


async def _add_if_missing(session: AsyncSession, obj: object) -> bool:
    existing = await session.get(type(obj), obj.id)
    if existing is not None:
        return False
    session.add(obj)
    return True


async def seed_demo_scenarios(session: AsyncSession) -> None:
    """Seed demo scenarios that exercise all role tabs and approval states."""

    await _seed_reference_tables(session)
    await _seed_role_tab_coverage(session)
    await _seed_content_review_workflow(session)
    await _seed_micro_school_workflow(session)
    await session.flush()
    print(
        "    Scenarios: reference rows, content review states, "
        "skill passports, document requirements, exports, and micro-school states"
    )


async def _seed_reference_tables(session: AsyncSession) -> None:
    # Catalogue de niveaux : code = valeur MEN officielle ; label_fr garde
    # l'équivalent français usuel pour l'affichage.
    levels = [
        ("GS", "Maternelle (GS)", "الروضة", "Preschool", 3, 5, 1),
        ("1AEP", "CP", "الأول ابتدائي", "Grade 1", 6, 6, 2),
        ("3AEP", "CE2", "الثالث ابتدائي", "Grade 3", 8, 8, 4),
        ("6AEP", "CM2", "الخامس ابتدائي", "Grade 5", 10, 10, 6),
        ("1AC", "6ème", "الأولى إعدادي", "Grade 6", 11, 12, 7),
        ("3AC", "3ème", "الثالثة إعدادي", "Grade 9", 14, 15, 10),
        ("2BAC", "Terminale", "الثانية باكالوريا", "Grade 12", 17, 18, 13),
    ]
    for code, label_fr, label_ar, label_en, age_min, age_max, order in levels:
        await _add_if_missing(
            session,
            LevelAgeMapping(
                id=uuid.uuid5(uuid.NAMESPACE_URL, f"level-age:{code}:platform"),
                school_id=None,
                level_code=code,
                label_fr=label_fr,
                label_ar=label_ar,
                label_en=label_en,
                default_age_min=age_min,
                default_age_max=age_max,
                display_order=order,
            ),
        )

    holidays = [
        ("manifesto-independence", date(2026, 1, 11), "Manifeste de l'indépendance"),
        ("labour-day", date(2026, 5, 1), "Fête du travail"),
        ("throne-day", date(2026, 7, 30), "Fête du Trône"),
        ("revolution-king-people", date(2026, 8, 20), "Révolution du Roi et du Peuple"),
        ("youth-day", date(2026, 8, 21), "Fête de la jeunesse"),
        ("green-march", date(2026, 11, 6), "Marche verte"),
        ("independence-day", date(2026, 11, 18), "Fête de l'indépendance"),
    ]
    for code, holiday_date, name_fr in holidays:
        await _add_if_missing(
            session,
            MoroccanHoliday(
                id=uuid.uuid5(uuid.NAMESPACE_URL, f"holiday:{code}:{holiday_date}"),
                code=code,
                holiday_date=holiday_date,
                name_fr=name_fr,
                name_ar=None,
                name_en=name_fr,
                description="Seed demo holiday used by calendar setup.",
                is_all_day=True,
            ),
        )


async def _seed_role_tab_coverage(session: AsyncSession) -> None:
    for user_id, event_type, enabled in [
        (ADMIN_ID, "school_event", True),
        (TEACHER_1_ID, "class_event", True),
        (PARENT_1_ID, "billing", True),
        (STUDENT_1_ID, "assignment", True),
    ]:
        await _add_if_missing(
            session,
            EventReminderPreference(
                id=uuid.uuid5(
                    uuid.NAMESPACE_URL, f"event-reminder:{user_id}:{event_type}"
                ),
                school_id=SCHOOL_ID,
                user_id=user_id,
                event_type=event_type,
                enabled=enabled,
            ),
        )

    for category, required, description in [
        ("birth_certificate", True, "Acte de naissance de l'élève."),
        ("vaccination_record", True, "Carnet de vaccination à jour."),
        ("parent_cin", True, "CIN du parent ou tuteur légal."),
        ("transfer_certificate", False, "Certificat de radiation si transfert."),
    ]:
        await _add_if_missing(
            session,
            StudentDocumentRequirement(
                id=uuid.uuid5(uuid.NAMESPACE_URL, f"student-doc-req:{category}"),
                school_id=SCHOOL_ID,
                category=category,
                required=required,
                description=description,
            ),
        )

    snapshot_data = {
        "level": "6eme",
        "average": 15.4,
        "attendance_rate": 0.94,
        "skills": ["communication", "autonomie", "raisonnement"],
    }
    for student_id, kind, score in [
        (STUDENT_1_ID, "MID_YEAR", 15.4),
        (STUDENT_2_ID, "MANUAL", 13.8),
    ]:
        await _add_if_missing(
            session,
            AcademicSnapshot(
                id=uuid.uuid5(
                    uuid.NAMESPACE_URL, f"academic-snapshot:{student_id}:{kind}"
                ),
                school_id=SCHOOL_ID,
                student_id=student_id,
                academic_year_id=YEAR_ID,
                snapshot_kind=kind,
                snapshot_data={**snapshot_data, "average": score},
                taken_at=_now() - timedelta(days=20),
                taken_by=ADMIN_ID,
                created_at=_now() - timedelta(days=20),
            ),
        )

    for requester_id, entity, fmt, row_count in [
        (ADMIN_ID, "students", DataExportFormat.XLSX.value, 21),
        (TEACHER_1_ID, "attendance", DataExportFormat.CSV.value, 247),
        (CONTENT_MGR_ID, "content_items", DataExportFormat.CSV.value, 34),
    ]:
        await _add_if_missing(
            session,
            DataExport(
                id=uuid.uuid5(
                    uuid.NAMESPACE_URL, f"data-export:{requester_id}:{entity}"
                ),
                school_id=SCHOOL_ID,
                requester_id=requester_id,
                entity=entity,
                filters={"seed": True, "scope": "demo"},
                format=fmt,
                row_count=row_count,
            ),
        )

    for student_id, total, unlocked, score in [
        (STUDENT_1_ID, 15, 8, 72.5),
        (STUDENT_2_ID, 15, 5, 58.0),
        (STUDENT_CP_ID, 15, 4, 51.0),
    ]:
        await _add_if_missing(
            session,
            SkillPassport(
                id=uuid.uuid5(
                    uuid.NAMESPACE_URL, f"skill-passport:{student_id}:{YEAR_ID}"
                ),
                school_id=SCHOOL_ID,
                student_id=student_id,
                academic_year_id=YEAR_ID,
                generated_at=_now() - timedelta(days=3),
                pdf_url=f"reports/skill-passports/{student_id}.pdf",
                total_milestones=total,
                unlocked_milestones=unlocked,
                overall_score=score,
            ),
        )


async def _seed_content_review_workflow(session: AsyncSession) -> None:
    specs = [
        (
            "pending",
            "Expérience sciences - Germination",
            "activite_scientifique",
            "PENDING",
            None,
            "En attente de première revue CMS.",
        ),
        (
            "under-review",
            "Atelier lecture - Inférences",
            "french",
            "UNDER_REVIEW",
            CONTENT_MGR_ID,
            "Vérifier les consignes et le niveau CE2.",
        ),
        (
            "approved",
            "Capsule fractions - Partages équitables",
            "math",
            "APPROVED",
            CONTENT_MGR_ID,
            "Approuvé pour promotion plateforme.",
        ),
        (
            "rejected",
            "Jeu grammaire - Accord brouillon",
            "french",
            "REJECTED",
            CONTENT_MGR_ID,
            "Refusé: ajouter sources et corriger deux consignes.",
        ),
    ]
    for key, title, subject, status, reviewer_id, notes in specs:
        source_id = uuid.uuid5(uuid.NAMESPACE_URL, f"content-review-source:{key}")
        promoted_id = uuid.uuid5(uuid.NAMESPACE_URL, f"content-review-promoted:{key}")
        await _add_if_missing(
            session,
            ContentItem(
                id=source_id,
                school_id=SCHOOL_ID,
                title=title,
                content_type="pdf",
                level_band="1AC" if subject == "math" else "3AEP",
                language="fr",
                subject=subject,
                description=f"Contenu enseignant pour scénario de revue: {status}.",
                status="published"
                if status in {"PENDING", "UNDER_REVIEW", "APPROVED"}
                else "draft",
                origin="PLATFORM",
                created_by=TEACHER_1_ID if subject != "french" else TEACHER_2_ID,
                target_age_min=8,
                target_age_max=12,
            ),
        )
        await _add_if_missing(
            session,
            ContentItemAsset(
                id=uuid.uuid5(uuid.NAMESPACE_URL, f"content-review-asset:{key}"),
                content_item_id=source_id,
                file_path=f"content/review/{key}.pdf",
                mime_type="application/pdf",
                file_size=220000,
                page_number=1,
                narration_text=f"Support pédagogique: {title}.",
                has_activity=True,
                asset_type="teacher_pdf",
            ),
        )
        if status == "APPROVED":
            await _add_if_missing(
                session,
                ContentItem(
                    id=promoted_id,
                    school_id=None,
                    title=f"{title} (promu)",
                    content_type="pdf",
                    level_band="1AC",
                    language="fr",
                    subject=subject,
                    description="Copie plateforme issue d'une approbation CMS.",
                    status="published",
                    origin="PROMOTED",
                    original_content_id=source_id,
                    created_by=CONTENT_MGR_ID,
                    target_age_min=11,
                    target_age_max=12,
                ),
            )
        await _add_if_missing(
            session,
            ContentSubmission(
                id=uuid.uuid5(uuid.NAMESPACE_URL, f"content-submission:{key}"),
                school_id=SCHOOL_ID,
                content_item_id=source_id,
                submitted_by=TEACHER_1_ID if subject != "french" else TEACHER_2_ID,
                status=status,
                submitted_at=_now() - timedelta(days=4),
                reviewed_by=reviewer_id,
                reviewed_at=_now() - timedelta(days=1) if reviewer_id else None,
                review_notes=notes,
                promoted_content_id=promoted_id if status == "APPROVED" else None,
            ),
        )


async def _seed_micro_school_workflow(session: AsyncSession) -> None:
    await _add_if_missing(
        session,
        User(
            id=MICRO_EDUCATOR_2_ID,
            email="educatrice.micro@ecole-benani.ma",
            full_name="Imane Bakkali",
            password_hash=hash_password("teacher123"),
            status="active",
            school_id=MICRO_SCHOOL_TENANT_ID,
        ),
    )
    await _add_if_missing(
        session,
        Membership(
            id=uuid.uuid5(
                uuid.NAMESPACE_URL, f"membership:{MICRO_EDUCATOR_2_ID}:EDUCATOR"
            ),
            user_id=MICRO_EDUCATOR_2_ID,
            school_id=MICRO_SCHOOL_TENANT_ID,
            role_code="EDUCATOR",
            status="active",
        ),
    )
    await _add_if_missing(
        session,
        TeacherProfile(
            id=uuid.uuid5(uuid.NAMESPACE_URL, f"teacher-profile:{MICRO_EDUCATOR_2_ID}"),
            user_id=MICRO_EDUCATOR_2_ID,
            school_id=MICRO_SCHOOL_TENANT_ID,
            employee_id="EDU-002",
            subject_specialty="micro-school,preschool",
            hire_date=date(2025, 9, 1),
        ),
    )

    micro_id = uuid.uuid5(uuid.NAMESPACE_URL, "micro-school:atelier-lumiere")
    group_id = uuid.uuid5(uuid.NAMESPACE_URL, "micro-group:atelier-lumiere:petits")
    enrollment_id = uuid.uuid5(
        uuid.NAMESPACE_URL, "micro-enrollment:atelier-lumiere:nour"
    )
    await _add_if_missing(
        session,
        MicroSchool(
            id=micro_id,
            educator_id=MICRO_EDUCATOR_2_ID,
            name="Atelier Lumiere",
            neighborhood="Sidi Maarouf",
            city="Casablanca",
            phone="+212699111222",
            max_capacity=12,
            status=MicroSchoolStatus.SUSPENDED.value,
            type=MicroSchoolType.GENERAL.value,
        ),
    )
    await _add_if_missing(
        session,
        MicroGroup(
            id=group_id,
            micro_school_id=micro_id,
            name="Petits curieux",
            age_range_min=3,
            age_range_max=5,
        ),
    )
    await _add_if_missing(
        session,
        MicroEnrollment(
            id=enrollment_id,
            micro_group_id=group_id,
            child_name="Nour Bakkali",
            parent_id=MICRO_PARENT_2_ID,
            date_of_birth=date(2022, 2, 12),
            enrolled_at=_now() - timedelta(days=50),
            status=MicroEnrollmentStatus.WITHDRAWN.value,
        ),
    )
    await _add_if_missing(
        session,
        MicroPayment(
            id=uuid.uuid5(
                uuid.NAMESPACE_URL, "micro-payment:atelier-lumiere:nour:overdue"
            ),
            micro_school_id=micro_id,
            parent_id=MICRO_PARENT_2_ID,
            child_enrollment_id=enrollment_id,
            amount=450.0,
            currency="MAD",
            period_type=MicroPaymentPeriodType.MONTHLY.value,
            period_start=date(2026, 3, 1),
            period_end=date(2026, 3, 31),
            paid_at=None,
            status=MicroPaymentStatus.OVERDUE.value,
        ),
    )
    await _add_if_missing(
        session,
        MicroProgressLog(
            id=uuid.uuid5(uuid.NAMESPACE_URL, "micro-progress:atelier-lumiere:nour:1"),
            micro_enrollment_id=enrollment_id,
            educator_id=MICRO_EDUCATOR_2_ID,
            date=date(2026, 3, 12),
            note="Nour identifie les couleurs primaires mais a besoin d'un suivi régulier.",
            photo_url="micro/progress/nour-colors.jpg",
            milestone_tag="language",
        ),
    )

    for key, title, resource_type, age_group, language, premium in [
        (
            "game-colors",
            "Jeu - Trier les couleurs",
            MicroResourceType.GAME.value,
            "3-5",
            "fr",
            False,
        ),
        (
            "song-cleanup",
            "Song - Clean up time",
            MicroResourceType.SONG.value,
            "4-6",
            "en",
            True,
        ),
        (
            "activity-ar-shapes",
            "نشاط - الأشكال",
            MicroResourceType.ACTIVITY_SHEET.value,
            "3-5",
            "ar",
            False,
        ),
    ]:
        await _add_if_missing(
            session,
            MicroResource(
                id=uuid.uuid5(uuid.NAMESPACE_URL, f"micro-resource:{key}"),
                title=title,
                description="Ressource micro-école pour filtres type/langue/âge.",
                resource_type=resource_type,
                age_group=age_group,
                language=language,
                file_url=f"micro_resources/{key}",
                is_premium=premium,
            ),
        )


# ====================== merged from seed_onboarding.py ======================
"""Seed onboarding applications for SuperAdmin approval workflows."""


import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.onboarding import ApplicationStatus, ApplicationType, SchoolApplication

SUPERADMIN_ID = uuid.UUID("10000000-0000-4000-8000-00000000000a")
SCHOOL_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")
MICRO_SCHOOL_TENANT_ID = uuid.UUID("00000000-0000-4000-8000-000000000003")


def _now() -> datetime:
    return datetime.now(UTC)


async def _add_if_missing(session: AsyncSession, app: SchoolApplication) -> bool:
    existing = await session.get(SchoolApplication, app.id)
    if existing is not None:
        return False
    session.add(app)
    return True


async def seed_onboarding_applications(session: AsyncSession) -> None:
    """Seed public registration requests across all review states.

    These are platform-scoped requests, before a tenant exists. Approved examples
    point to existing seeded schools so the SuperAdmin console shows historical
    approvals without creating duplicate tenants.
    """

    now = _now()
    rows = [
        SchoolApplication(
            id=uuid.uuid5(uuid.NAMESPACE_URL, "onboarding:formal:pending:al-manar"),
            application_type=ApplicationType.FORMAL_SCHOOL.value,
            status=ApplicationStatus.PENDING.value,
            applicant_name="Mme Alami",
            applicant_email="alami@example.ma",
            applicant_phone="+212600000001",
            city="Rabat",
            language="fr",
            org_name="Ecole Al Manar",
            address="12 Rue des Ecoles",
            level_band="primaire",
            subjects=["arabe", "francais", "mathematiques"],
            notes="Nouvelle ecole privee souhaitant rejoindre la plateforme.",
        ),
        SchoolApplication(
            id=uuid.uuid5(uuid.NAMESPACE_URL, "onboarding:micro:pending:rawd-nour"),
            application_type=ApplicationType.MICRO_SCHOOL.value,
            status=ApplicationStatus.PENDING.value,
            applicant_name="M. Idrissi",
            applicant_email="idrissi@example.ma",
            applicant_phone="+212600000002",
            city="Sale",
            language="ar",
            org_name="Rawd An Nour",
            neighborhood="Hay Salam",
            address="Bloc C, Hay Salam",
            max_capacity=20,
            notes="Micro-ecole pour enfants de 3 a 6 ans.",
        ),
        SchoolApplication(
            id=uuid.uuid5(uuid.NAMESPACE_URL, "onboarding:formal:needs-info:atlas"),
            application_type=ApplicationType.FORMAL_SCHOOL.value,
            status=ApplicationStatus.NEEDS_INFO.value,
            applicant_name="M. Bennani",
            applicant_email="bennani-ecole@example.ma",
            applicant_phone="+212600000003",
            city="Casablanca",
            language="fr",
            org_name="Groupe Scolaire Atlas",
            address="Boulevard Al Qods",
            level_band="primaire-college",
            subjects=["sciences", "mathematiques", "anglais"],
            notes="Demande complete sauf autorisation administrative.",
            review_notes="Merci d'ajouter l'autorisation MEN et le registre de commerce.",
            reviewed_by=SUPERADMIN_ID,
            reviewed_at=now - timedelta(days=2),
        ),
        SchoolApplication(
            id=uuid.uuid5(
                uuid.NAMESPACE_URL, "onboarding:micro:needs-info:rawd-yasmine"
            ),
            application_type=ApplicationType.MICRO_SCHOOL.value,
            status=ApplicationStatus.NEEDS_INFO.value,
            applicant_name="Mme Yasmine Farah",
            applicant_email="yasmine.rawd@example.ma",
            applicant_phone="+212600000004",
            city="Marrakech",
            language="fr",
            org_name="Rawd Yasmine",
            neighborhood="Gueliz",
            max_capacity=15,
            notes="Educatrice independante avec local familial.",
            review_notes="Ajouter une photo du local et une piece d'identite.",
            reviewed_by=SUPERADMIN_ID,
            reviewed_at=now - timedelta(days=1),
        ),
        SchoolApplication(
            id=uuid.uuid5(uuid.NAMESPACE_URL, "onboarding:formal:rejected:bad-docs"),
            application_type=ApplicationType.FORMAL_SCHOOL.value,
            status=ApplicationStatus.REJECTED.value,
            applicant_name="M. Karim Haddad",
            applicant_email="karim-haddad@example.ma",
            applicant_phone="+212600000005",
            city="Tanger",
            language="fr",
            org_name="Institut Horizon",
            address="Rue Ibn Battouta",
            level_band="lycee",
            notes="Documents fournis non conformes.",
            review_notes="Identite de l'organisme non verifiable.",
            reviewed_by=SUPERADMIN_ID,
            reviewed_at=now - timedelta(days=6),
        ),
        SchoolApplication(
            id=uuid.uuid5(uuid.NAMESPACE_URL, "onboarding:micro:rejected:capacity"),
            application_type=ApplicationType.MICRO_SCHOOL.value,
            status=ApplicationStatus.REJECTED.value,
            applicant_name="Mme Ait Lahcen",
            applicant_email="aitlahcen.rawd@example.ma",
            applicant_phone="+212600000006",
            city="Agadir",
            language="ar",
            org_name="Petits Pas Agadir",
            neighborhood="Dakhla",
            max_capacity=45,
            notes="Capacite annoncee trop elevee pour le local decrit.",
            review_notes="Demande rejetee en attendant un local adapte.",
            reviewed_by=SUPERADMIN_ID,
            reviewed_at=now - timedelta(days=5),
        ),
        SchoolApplication(
            id=uuid.uuid5(uuid.NAMESPACE_URL, "onboarding:formal:approved:benani"),
            application_type=ApplicationType.FORMAL_SCHOOL.value,
            status=ApplicationStatus.APPROVED.value,
            applicant_name="Admin Benani",
            applicant_email="admin@ecole-benani.ma",
            applicant_phone="+212522000001",
            city="Casablanca",
            language="fr",
            org_name="Ecole Benani",
            address="Casablanca",
            level_band="primaire-college-lycee",
            notes="Historique d'approbation seed pour l'ecole formelle principale.",
            review_notes="Approuvee et tenant formal cree.",
            reviewed_by=SUPERADMIN_ID,
            reviewed_at=now - timedelta(days=30),
            created_school_id=SCHOOL_ID,
        ),
        SchoolApplication(
            id=uuid.uuid5(uuid.NAMESPACE_URL, "onboarding:micro:approved:demo"),
            application_type=ApplicationType.MICRO_SCHOOL.value,
            status=ApplicationStatus.APPROVED.value,
            applicant_name="Said El Fassi",
            applicant_email="educateur.micro@ecole-benani.ma",
            applicant_phone="+212612345999",
            city="Casablanca",
            language="fr",
            org_name="Petite Ecole des Orangers",
            neighborhood="Hay Orangers",
            max_capacity=20,
            notes="Historique d'approbation seed pour une micro-ecole.",
            review_notes="Approuvee, role EDUCATOR cree via invitation onboarding.",
            reviewed_by=SUPERADMIN_ID,
            reviewed_at=now - timedelta(days=20),
            created_school_id=MICRO_SCHOOL_TENANT_ID,
        ),
    ]

    created = 0
    for row in rows:
        if await _add_if_missing(session, row):
            created += 1

    await session.flush()
    print(f"  [Onboarding] {created} demo applications")


if __name__ == "__main__":
    asyncio.run(main())
