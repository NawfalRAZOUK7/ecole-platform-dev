"""Shared fixtures for rewards, games, and story integration tests."""

from __future__ import annotations

import uuid
from pathlib import Path

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

import app.models  # noqa: F401
from app.core.database import get_db
from app.core.security import create_access_token
from app.core.storage import storage
from app.main import app
from app.models.erp import TeacherAssignment
from app.models.iam import RoleCode
from app.services.file_storage import LocalFileStorageBackend, file_storage_service
from tests.factories.erp import (
    AcademicYearFactory,
    ClassFactory,
    EnrollmentFactory,
    PeriodFactory,
)
from tests.factories.iam import (
    MembershipFactory,
    ParentChildLinkFactory,
    SessionFactory,
    UserFactory,
)
from tests.factories.school import SchoolFactory

# Default level-age mappings — mirrors the G46 migration seed data
_DEFAULT_LEVEL_MAPPINGS = [
    ("maternelle", "Maternelle", "ما قبل المدرسة", "Preschool", 3, 5, 0),
    ("cp", "Cours Préparatoire", "السنة الأولى ابتدائي", "1st Grade", 5, 6, 1),
    ("ce1", "Cours Élémentaire 1", "السنة الثانية ابتدائي", "2nd Grade", 6, 7, 2),
    ("ce2", "Cours Élémentaire 2", "السنة الثالثة ابتدائي", "3rd Grade", 7, 8, 3),
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


async def _create_actor(
    session: AsyncSession,
    *,
    school,
    role: str,
    label: str,
) -> dict[str, object]:
    suffix = uuid.uuid4().hex[:8]
    user = await UserFactory.create(
        session=session,
        school=school,
        email=f"{label}-{suffix}@integration.ecole.ma",
        full_name=f"{label.title()} Integration {suffix}",
    )
    await MembershipFactory.create(
        session=session,
        user=user,
        school_id=school.id,
        role_code=role,
    )
    auth_session = await SessionFactory.create(
        session=session,
        user=user,
        school_id=school.id,
        source=f"pytest-{label}",
    )
    token = create_access_token(user.id, role, school.id, auth_session.id)
    return {"user": user, "token": token}


@pytest.fixture
def isolated_storage(tmp_path: Path):
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    original_storage_dir = storage.base_dir
    original_backend = file_storage_service.backend

    storage.base_dir = upload_dir
    file_storage_service.backend = LocalFileStorageBackend(base_dir=str(upload_dir))

    try:
        yield upload_dir
    finally:
        storage.base_dir = original_storage_dir
        file_storage_service.backend = original_backend


@pytest_asyncio.fixture(loop_scope="function")
async def session_factory(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(loop_scope="function", autouse=True)
async def seed_level_mappings(session_factory):
    """Seed the default level-age mappings for every test.

    The integration test DB is created via Base.metadata.create_all (not Alembic),
    so the migration-level seed INSERT is not run automatically.
    """
    async with session_factory() as session:
        # Check if already seeded to avoid duplicates across test functions
        result = await session.execute(
            text("SELECT COUNT(*) FROM level_age_mappings WHERE school_id IS NULL")
        )
        count = result.scalar_one()
        if count >= len(_DEFAULT_LEVEL_MAPPINGS):
            return

        for level_code, label_fr, label_ar, label_en, age_min, age_max, order in _DEFAULT_LEVEL_MAPPINGS:
            await session.execute(
                text(
                    """
                    INSERT INTO level_age_mappings
                      (id, level_code, label_fr, label_ar, label_en,
                       default_age_min, default_age_max, display_order, created_at)
                    VALUES
                      (gen_random_uuid(), :level_code, :label_fr, :label_ar, :label_en,
                       :age_min, :age_max, :order, now())
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


@pytest_asyncio.fixture(loop_scope="function")
async def client(session_factory):
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


@pytest_asyncio.fixture(loop_scope="function")
async def api_context(session_factory, isolated_storage):
    async with session_factory() as session:
        school = await SchoolFactory.create(
            session=session,
            code=f"INT-{uuid.uuid4().hex[:6].upper()}",
            name="Integration School",
            city="Casablanca",
        )
        academic_year = await AcademicYearFactory.create(
            session=session,
            school=school,
            label="2025-2026",
        )
        period = await PeriodFactory.create(
            session=session,
            school=school,
            academic_year=academic_year,
            label="Trimester 1",
        )
        school_class = await ClassFactory.create(
            session=session,
            school=school,
            academic_year=academic_year,
            code="CLS-INT",
            name="Classe Integration",
        )

        admin = await _create_actor(
            session,
            school=school,
            role=RoleCode.ADM.value,
            label="admin",
        )
        teacher = await _create_actor(
            session,
            school=school,
            role=RoleCode.TCH.value,
            label="teacher",
        )
        parent = await _create_actor(
            session,
            school=school,
            role=RoleCode.PAR.value,
            label="parent",
        )
        student = await _create_actor(
            session,
            school=school,
            role=RoleCode.STD.value,
            label="student",
        )
        peer_student = await _create_actor(
            session,
            school=school,
            role=RoleCode.STD.value,
            label="peer-student",
        )
        peer_student_two = await _create_actor(
            session,
            school=school,
            role=RoleCode.STD.value,
            label="peer-student-two",
        )
        content_manager = await _create_actor(
            session,
            school=school,
            role=RoleCode.CONTENT_MGR.value,
            label="content-manager",
        )

        await ParentChildLinkFactory.create(
            session=session,
            school=school,
            parent=parent["user"],
            child=student["user"],
            linked_by=admin["user"].id,
        )

        for actor in (student, peer_student, peer_student_two):
            await EnrollmentFactory.create(
                session=session,
                school=school,
                academic_year=academic_year,
                class_obj=school_class,
                period=period,
                student=actor["user"],
            )

        session.add(
            TeacherAssignment(
                school_id=school.id,
                teacher_id=teacher["user"].id,
                class_id=school_class.id,
                period_id=period.id,
            )
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
        "peer_student": peer_student,
        "peer_student_two": peer_student_two,
        "content_manager": content_manager,
    }
