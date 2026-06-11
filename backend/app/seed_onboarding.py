"""Seed onboarding applications for SuperAdmin approval workflows."""

from __future__ import annotations

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
            id=uuid.uuid5(uuid.NAMESPACE_URL, "onboarding:micro:needs-info:rawd-yasmine"),
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
