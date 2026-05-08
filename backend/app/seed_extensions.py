"""Seed extensions for newer features not covered by main seed.py.

Run automatically via `make seed` (called from app.seed.main).
"""

from __future__ import annotations

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
from app.models.documents import Document, DocumentCategory, DocumentVersion, Resource, ResourceType, ResourceVisibility
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
    users = (await session.execute(select(User).where(User.school_id == school.id))).scalars().all()
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
                rsvps.append(EventRSVP(
                    id=uuid.uuid4(),
                    event_id=evt.id,
                    user_id=u.id,
                    status=EventRsvpStatus.ATTENDING.value if u.id == users[1].id else EventRsvpStatus.MAYBE.value,
                    responded_at=now,
                ))
        session.add_all(rsvps)
        rsvp_count = len(rsvps)

    # Reminders for multiple events
    reminders = [
        EventReminder(id=uuid.uuid4(), event_id=events[0].id, remind_at=events[0].start_at - timedelta(days=1), channel=EventReminderChannel.IN_APP.value),
        EventReminder(id=uuid.uuid4(), event_id=events[1].id, remind_at=events[1].start_at - timedelta(hours=2), channel=EventReminderChannel.PUSH.value),
        EventReminder(id=uuid.uuid4(), event_id=events[2].id, remind_at=events[2].start_at - timedelta(days=2), channel=EventReminderChannel.IN_APP.value),
        EventReminder(id=uuid.uuid4(), event_id=events[3].id, remind_at=events[3].start_at - timedelta(days=1), channel=EventReminderChannel.IN_APP.value),
        EventReminder(id=uuid.uuid4(), event_id=events[6].id, remind_at=events[6].start_at - timedelta(days=7), channel=EventReminderChannel.PUSH.value),
    ]
    session.add_all(reminders)

    print(f"    Calendar: {len(events)} events, {rsvp_count} RSVPs, {len(reminders)} reminders")


async def seed_documents(session: AsyncSession) -> None:
    """Seed documents, versions, and shared resources (enhanced: 4 docs, 5 resources)."""
    schools = (await session.execute(select(School))).scalars().all()
    if not schools:
        return

    school = schools[0]
    users = (await session.execute(select(User).where(User.school_id == school.id).limit(3))).scalars().all()
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
            original_filename="Relevé de notes — Omar Benali.pdf",
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
    session.add(DocumentVersion(
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
    ))
    session.add(DocumentVersion(
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
    ))

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

    print(f"    Documents: {len(docs)} documents + 2 versions, {len(resources)} shared resources")


async def seed_reporting(session: AsyncSession) -> None:
    """Seed report schedules and jobs (enhanced: 3 schedules, 6 jobs)."""
    schools = (await session.execute(select(School))).scalars().all()
    if not schools:
        return

    school = schools[0]
    users = (await session.execute(select(User).where(User.school_id == school.id).limit(2))).scalars().all()
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

    print(f"    Reporting: {len(schedules)} schedules, {len(jobs)} jobs (completed, pending, running, failed)")


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
    session.add_all([
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
    ])

    # Program equivalences
    session.add_all([
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
    ])

    print("    Programs: 2 programs + 2 versions, 2 eligibility rules, 2 equivalences")


async def seed_ai_preferences(session: AsyncSession) -> None:
    """Seed AI preferences and writing attempts (enhanced: 3 preferences, 4 attempts)."""
    schools = (await session.execute(select(School))).scalars().all()
    if not schools:
        return

    school = schools[0]
    users = (await session.execute(select(User).where(User.school_id == school.id))).scalars().all()
    if len(users) < 3:
        print("    AI: skipped (need 3 users)")
        return

    # AI preferences for 3 users (parent sets preference for child)
    session.add_all([
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
    ])

    # Writing attempts (4)
    attempts = [
        WritingAttempt(
            id=uuid.uuid4(),
            school_id=school.id,
            student_id=users[1].id,
            subject="Expression ecrite",
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
            subject="Expression ecrite en anglais",
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
            subject="Expression ecrite",
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
            subject="Description",
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
    users = (await session.execute(select(User).where(User.school_id == school.id).limit(5))).scalars().all()

    categories = ["billing", "academic", "attendance", "announcement", "system"]
    for user in users[:3]:
        for category in categories:
            session.add(NotificationPreference(
                id=uuid.uuid4(),
                school_id=school.id,
                user_id=user.id,
                channel="email",
                category=category,
                enabled=category != "system" or user.id == users[0].id,
            ))

    # Device tokens
    if users:
        session.add_all([
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
        ])

    print("    Notifications: 9 preference records, 3 device tokens")
