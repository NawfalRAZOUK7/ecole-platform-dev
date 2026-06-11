"""Scenario seeders for role coverage and realistic workflow states.

These rows sit on top of the core domain seed. Keep this file focused on data
that makes screens and review queues useful for demos:
- reference lists used by filters/forms,
- non-empty tabs for role navigation,
- approval/rejection states,
- relationship-heavy micro-school data.
"""

from __future__ import annotations

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
    levels = [
        ("maternelle", "Maternelle", "الروضة", "Preschool", 3, 5, 1),
        ("CP", "CP", "الأول ابتدائي", "Grade 1", 6, 6, 2),
        ("CE2", "CE2", "الثالث ابتدائي", "Grade 3", 8, 8, 4),
        ("CM2", "CM2", "الخامس ابتدائي", "Grade 5", 10, 10, 6),
        ("6eme", "6ème", "الأولى إعدادي", "Grade 6", 11, 12, 7),
        ("3eme", "3ème", "الثالثة إعدادي", "Grade 9", 14, 15, 10),
        ("Terminale", "Terminale", "الثانية باكالوريا", "Grade 12", 17, 18, 13),
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
            "science",
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
                level_band="6eme" if subject == "math" else "CE2",
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
                    level_band="6eme",
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
