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

from __future__ import annotations

import random
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
    MicroBudget,
    MicroBudgetStatus,
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
    PaymentProof,
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
    AdminProfile,
    ContentManagerProfile,
    Membership,
    ParentChildLink,
    ParentProfile,
    StudentProfile,
    TeacherProfile,
    User,
)

# ── Shared constants from seed.py (duplicated to avoid circular import) ──
SCHOOL_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")
SCHOOL_ID_2 = uuid.UUID("00000000-0000-4000-8000-000000000002")
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


def _now() -> datetime:
    return datetime.now(timezone.utc)


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

    # Create 5eme A class
    c5a = Class(
        id=CLASS_5EME_ID,
        school_id=SCHOOL_ID,
        code="5A",
        academic_year_id=YEAR_ID,
        name="5eme A",
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
                password_hash="$2b$12$dummyhashforseed",  # placeholder — seeded users use seed.py hashes
                status="active",
                school_id=SCHOOL_ID,
            )
        )
    await session.flush()

    for uid, email, full_name, student_no, dob in new_students:
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
        session.add(
            PaymentProof(
                payment_attempt_id=pa.id,
                proof_hash=f"hash-{pa.id}",
                provider_ref=f"PROV-{i+100}",
                source="bank_transfer",
                received_at=_now() - timedelta(days=i),
            )
        )

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
    print("    Enhanced: +12 invoices, +payment proofs, +webhook events")


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
            level="6eme",
            difficulty="medium",
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
            level="6eme",
            difficulty="easy",
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
            level="6eme",
            difficulty="medium",
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
            level="6eme",
            difficulty="hard",
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
            level="5eme",
            difficulty="hard",
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
    budget = MicroBudget(
        school_id=SCHOOL_ID,
        academic_year_id=YEAR_ID,
        total_amount=50000.00,
        allocated_amount=35000.00,
        remaining_amount=15000.00,
        currency="MAD",
        status=MicroBudgetStatus.ACTIVE.value,
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
            password_hash="$2b$12$dummyhashforseed",
            status="active",
            school_id=SCHOOL_ID,
        )
    )
    session.add(
        Membership(
            user_id=EDUCATOR_ID, school_id=SCHOOL_ID, role_code="TCH", status="active"
        )
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
    )
    session.add(micro)
    await session.flush()

    # Groups
    g1 = MicroGroup(
        micro_school_id=micro.id,
        name="Groupe des Petits",
        age_range_min=2,
        age_range_max=4,
    )
    g2 = MicroGroup(
        micro_school_id=micro.id,
        name="Groupe des Moyens",
        age_range_min=4,
        age_range_max=6,
    )
    session.add_all([g1, g2])
    await session.flush()

    # Enrollments
    enrollments_data = [
        (g1.id, "Adam", PARENT_1_ID, date(2022, 3, 10)),
        (g1.id, "Lina", PARENT_2_ID, date(2022, 7, 15)),
        (g2.id, "Youssef", PARENT_1_ID, date(2020, 1, 20)),
        (g2.id, "Sara", PARENT_2_ID, date(2019, 11, 5)),
    ]
    enrollment_objs: list[MicroEnrollment] = []
    for gid, child_name, parent_id, dob in enrollments_data:
        me = MicroEnrollment(
            micro_group_id=gid,
            child_name=child_name,
            parent_id=parent_id,
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
        subject="Progres de Salma en Francais",
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
            body="Bonjour Mme Dupont, comment se porte Salma en redaction?",
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
        subject="Nouvelles directives — evaluation du 2eme semestre",
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
        subject="Question sur la facture de mars",
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
                full_name="Karim Atlas",
                password_hash="$2b$12$dummyhashforseed",
                status="active",
                school_id=SCHOOL_ID_2,
            ),
            User(
                id=s2_teacher,
                email="prof@ecole-atlas.ma",
                full_name="Leila Atlas",
                password_hash="$2b$12$dummyhashforseed",
                status="active",
                school_id=SCHOOL_ID_2,
            ),
            User(
                id=s2_parent,
                email="parent@ecole-atlas.ma",
                full_name="Ahmed Atlas",
                phone="+212611111222",
                password_hash="$2b$12$dummyhashforseed",
                status="active",
                school_id=SCHOOL_ID_2,
            ),
            User(
                id=s2_student,
                email="enfant@ecole-atlas.ma",
                full_name="Youssef Atlas",
                password_hash="$2b$12$dummyhashforseed",
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
            code="3A",
            academic_year_id=s2_year,
            name="3eme A",
        )
    )
    await session.flush()

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
                approved_subjects='["math", "french", "science"]',
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
                code_hash="$2b$12$invitehashforparent001",
                role_target="PAR",
                expires_at=_now() + timedelta(days=30),
            ),
            InvitationCode(
                id=uuid.uuid4(),
                school_id=SCHOOL_ID,
                issuer_user_id=ADMIN_ID,
                code_hash="$2b$12$invitehashforteacher002",
                role_target="TCH",
                expires_at=_now() + timedelta(days=30),
            ),
            InvitationCode(
                id=uuid.uuid4(),
                school_id=SCHOOL_ID,
                issuer_user_id=ADMIN_ID,
                code_hash="$2b$12$invitehashforparent003",
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
