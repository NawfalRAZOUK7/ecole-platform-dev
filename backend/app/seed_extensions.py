"""Seed extensions for newer features not covered by main seed.py.

Run automatically via `make seed` (called from app.seed.main).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import AIPreference, WritingAttempt
from app.models.calendar import (
    Event,
    EventRSVP,
    EventReminder,
    EventRsvpStatus,
    EventType,
    EventVisibility,
)
from app.models.documents import Document, DocumentCategory, DocumentVersion, Resource, ResourceType
from app.models.erp import (
    EligibilityRule,
    Program,
    ProgramEquivalence,
    ProgramEquivalenceKind,
    ProgramVersion,
)
from app.models.iam import User
from app.models.reporting import ReportJob, ReportJobStatus, ReportSchedule, ReportType
from app.models.school import School


async def seed_calendar(session: AsyncSession) -> None:
    """Seed calendar events, RSVPs, and reminders."""
    schools = (await session.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(School)
    )).scalars().all()
    if not schools:
        return

    school = schools[0]
    users = (await session.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(User).where(User.school_id == school.id).limit(5)
    )).scalars().all()

    events = [
        Event(
            id=uuid.uuid4(),
            school_id=school.id,
            title="Journée Portes Ouvertes",
            description="Rencontre parents-enseignants pour le premier trimestre.",
            start_date=datetime.now(timezone.utc) + timedelta(days=7),
            end_date=datetime.now(timezone.utc) + timedelta(days=7, hours=4),
            event_type=EventType.SCHOOL_EVENT,
            visibility=EventVisibility.SCHOOL_WIDE,
            location="Salle des fêtes",
            created_by=users[0].id if users else None,
        ),
        Event(
            id=uuid.uuid4(),
            school_id=school.id,
            title="Examen de Mathématiques — 6ème A",
            description="Contrôle sur les fractions et les équations.",
            start_date=datetime.now(timezone.utc) + timedelta(days=14),
            end_date=datetime.now(timezone.utc) + timedelta(days=14, hours=2),
            event_type=EventType.EXAM,
            visibility=EventVisibility.CLASS_ONLY,
            location="Salle 102",
            created_by=users[0].id if users else None,
        ),
        Event(
            id=uuid.uuid4(),
            school_id=school.id,
            title="Excursion au Musée des Sciences",
            description="Sortie pédagogique pour les classes de CM1 et CM2.",
            start_date=datetime.now(timezone.utc) + timedelta(days=21),
            end_date=datetime.now(timezone.utc) + timedelta(days=21, hours=6),
            event_type=EventType.EXCURSION,
            visibility=EventVisibility.SCHOOL_WIDE,
            location="Musée des Sciences, Casablanca",
            created_by=users[0].id if users else None,
        ),
    ]
    session.add_all(events)
    await session.flush()

    # RSVPs
    if len(users) >= 2:
        session.add_all([
            EventRSVP(id=uuid.uuid4(), event_id=events[0].id, user_id=users[1].id, status=EventRsvpStatus.YES),
            EventRSVP(id=uuid.uuid4(), event_id=events[0].id, user_id=users[2].id if len(users) > 2 else users[1].id, status=EventRsvpStatus.MAYBE),
        ])

    # Reminders
    session.add_all([
        EventReminder(id=uuid.uuid4(), event_id=events[0].id, remind_at=events[0].start_date - timedelta(days=1)),
        EventReminder(id=uuid.uuid4(), event_id=events[1].id, remind_at=events[1].start_date - timedelta(hours=2)),
    ])

    print("    Calendar: 3 events, 2 RSVPs, 2 reminders")


async def seed_documents(session: AsyncSession) -> None:
    """Seed documents, versions, and shared resources."""
    schools = (await session.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(School)
    )).scalars().all()
    if not schools:
        return

    school = schools[0]
    users = (await session.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(User).where(User.school_id == school.id).limit(3)
    )).scalars().all()
    owner_id = users[0].id if users else None

    doc = Document(
        id=uuid.uuid4(),
        school_id=school.id,
        title="Bulletin Trimestriel — Yassine Alaoui",
        category=DocumentCategory.REPORT_CARD,
        file_path="documents/report_cards/bulletin_yassine_t1.pdf",
        mime_type="application/pdf",
        size_bytes=245_760,
        uploaded_by=owner_id,
    )
    session.add(doc)
    await session.flush()

    # Document version
    session.add(DocumentVersion(
        id=uuid.uuid4(),
        document_id=doc.id,
        version_number=1,
        file_path="documents/report_cards/bulletin_yassine_t1.pdf",
        size_bytes=245_760,
        created_by=owner_id,
    ))

    # Shared resources
    session.add_all([
        Resource(
            id=uuid.uuid4(),
            school_id=school.id,
            title="Plan de cours — Mathématiques CP",
            resource_type=ResourceType.LESSON_PLAN,
            file_path="resources/lesson_plans/math_cp_sem1.pdf",
            mime_type="application/pdf",
            size_bytes=512_000,
            uploaded_by=owner_id,
        ),
        Resource(
            id=uuid.uuid4(),
            school_id=school.id,
            title="Fiche d'exercices — Fractions",
            resource_type=ResourceType.WORKSHEET,
            file_path="resources/worksheets/fractions_exercices.pdf",
            mime_type="application/pdf",
            size_bytes=128_000,
            uploaded_by=owner_id,
        ),
    ])

    print("    Documents: 1 document + 1 version, 2 shared resources")


async def seed_reporting(session: AsyncSession) -> None:
    """Seed report schedules and jobs."""
    schools = (await session.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(School)
    )).scalars().all()
    if not schools:
        return

    school = schools[0]
    users = (await session.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(User).where(User.school_id == school.id).limit(2)
    )).scalars().all()
    creator_id = users[0].id if users else None

    schedule = ReportSchedule(
        id=uuid.uuid4(),
        school_id=school.id,
        name="Rapport mensuel d'assiduité",
        report_type=ReportType.ATTENDANCE,
        cron_expression="0 8 1 * *",
        recipients=["directeur@ecole-benani.ma"],
        created_by=creator_id,
        is_active=True,
    )
    session.add(schedule)
    await session.flush()

    session.add_all([
        ReportJob(
            id=uuid.uuid4(),
            school_id=school.id,
            schedule_id=schedule.id,
            status=ReportJobStatus.COMPLETED,
            started_at=datetime.now(timezone.utc) - timedelta(days=30),
            completed_at=datetime.now(timezone.utc) - timedelta(days=30, hours=-1),
            file_path="reports/attendance_2025_04.pdf",
            created_by=creator_id,
        ),
        ReportJob(
            id=uuid.uuid4(),
            school_id=school.id,
            schedule_id=schedule.id,
            status=ReportJobStatus.PENDING,
            created_by=creator_id,
        ),
    ])

    print("    Reporting: 1 schedule, 2 jobs (1 completed, 1 pending)")


async def seed_programs(session: AsyncSession) -> None:
    """Seed academic programs with versions and equivalences."""
    schools = (await session.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(School)
    )).scalars().all()
    if not schools:
        return

    school = schools[0]
    users = (await session.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(User).where(User.school_id == school.id).limit(2)
    )).scalars().all()
    creator_id = users[0].id if users else None

    program = Program(
        id=uuid.uuid4(),
        school_id=school.id,
        name="Programme Bilingue Français-Anglais",
        description="Parcours bilingue renforcé avec 50% des cours en anglais.",
        levels=["CP", "CE1", "CE2", "CM1", "CM2"],
        is_active=True,
        created_by=creator_id,
    )
    session.add(program)
    await session.flush()

    version = ProgramVersion(
        id=uuid.uuid4(),
        school_id=school.id,
        program_id=program.id,
        version_number=1,
        effective_date=date(2024, 9, 1),
        rules={"min_age": 5, "prerequisites": []},
        created_by=creator_id,
    )
    session.add(version)
    await session.flush()

    # Eligibility rule
    session.add(EligibilityRule(
        id=uuid.uuid4(),
        school_id=school.id,
        kind="enrollment",
        target_program_id=program.id,
        condition_type="min_grade_average",
        condition_params={"min_average": 10.0},
        message_key="min_average_required",
        is_active=True,
    ))

    # Program equivalence
    session.add(ProgramEquivalence(
        id=uuid.uuid4(),
        school_id=school.id,
        source_program_id=program.id,
        target_program_id=program.id,
        kind=ProgramEquivalenceKind.CREDIT_TRANSFER,
        rules={"max_credits": 6},
        is_active=True,
    ))

    print("    Programs: 1 program + 1 version, 1 eligibility rule, 1 equivalence")


async def seed_ai_preferences(session: AsyncSession) -> None:
    """Seed AI preferences and writing attempts."""
    schools = (await session.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(School)
    )).scalars().all()
    if not schools:
        return

    school = schools[0]
    users = (await session.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(User).where(User.school_id == school.id).limit(3)
    )).scalars().all()

    if users:
        session.add(AIPreference(
            id=uuid.uuid4(),
            school_id=school.id,
            user_id=users[0].id,
            opt_out=False,
            allow_writing_assist=True,
            allow_recommendations=True,
        ))

    if len(users) >= 2:
        session.add(WritingAttempt(
            id=uuid.uuid4(),
            school_id=school.id,
            student_id=users[1].id,
            text="Le chat est sur la table. Il mange du poisson.",
            language="fr",
            word_count=9,
            feedback_summary="Phrase simple et correcte.",
        ))

    print("    AI: 1 preference, 1 writing attempt")


async def seed_notification_preferences(session: AsyncSession) -> None:
    """Seed notification preferences and device tokens."""
    from app.models.com import DeviceToken, NotificationPreference

    schools = (await session.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(School)
    )).scalars().all()
    if not schools:
        return

    school = schools[0]
    users = (await session.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(User).where(User.school_id == school.id).limit(3)
    )).scalars().all()

    for user in users:
        session.add(NotificationPreference(
            id=uuid.uuid4(),
            school_id=school.id,
            user_id=user.id,
            channel="email",
            category="billing",
            enabled=True,
        ))

    if users:
        session.add(DeviceToken(
            id=uuid.uuid4(),
            user_id=users[0].id,
            token="fcm-demo-token-1234567890abcdef",
            platform="android",
            is_active=True,
        ))

    print("    Notifications: 3 preference records, 1 device token")
