"""Shared fixtures and helpers for security integration tests."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone

import httpx
import pytest_asyncio
from sqlalchemy import select

from app.core.database import async_session
from app.core.security import create_access_token, hash_password
from app.models.erp import AttendanceRecord, AttendanceSession
from app.models.iam import Membership, ParentChildLink, Session, User
from app.models.lms import Assignment, Course, GradeCategory, Submission

SCHOOL_ID = "00000000-0000-4000-8000-000000000001"
YEAR_ID = "20000000-0000-4000-8000-000000000001"
PERIOD_ID = "20000000-0000-4000-8000-000000000003"
CLASS_ID = "20000000-0000-4000-8000-000000000004"
STUDENT_ID = "10000000-0000-4000-8000-000000000007"
TEACHER_ID = "10000000-0000-4000-8000-000000000003"
PARENT_ID = "10000000-0000-4000-8000-000000000005"
ADMIN_ID = "10000000-0000-4000-8000-000000000001"

SUPERADMIN_EMAIL = "superadmin@ecole-platform.ma"
SUPERADMIN_PASSWORD = "superadmin123"
CONTENT_MGR_EMAIL = "cms@ecole-platform.ma"
CONTENT_MGR_PASSWORD = "content123"

SCHOOL_UUID = uuid.UUID(SCHOOL_ID)
YEAR_UUID = uuid.UUID(YEAR_ID)
PERIOD_UUID = uuid.UUID(PERIOD_ID)
CLASS_UUID = uuid.UUID(CLASS_ID)
STUDENT_UUID = uuid.UUID(STUDENT_ID)
TEACHER_UUID = uuid.UUID(TEACHER_ID)
PARENT_UUID = uuid.UUID(PARENT_ID)
ADMIN_UUID = uuid.UUID(ADMIN_ID)


@dataclass(frozen=True)
class SecurityActor:
    user_id: uuid.UUID
    token: str
    email: str
    role: str


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def login_token(
    client: httpx.AsyncClient,
    *,
    email: str,
    password: str,
) -> str:
    response = await client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
            "school_id": SCHOOL_ID,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]["access_token"]


async def ensure_role_actor(
    *,
    role: str,
    key: str,
    full_name: str,
) -> SecurityActor:
    user_id = uuid.uuid5(uuid.NAMESPACE_URL, f"security-user:{key}")
    session_id = uuid.uuid4()
    email = f"{key}@security.ecole.ma"

    async with async_session() as db:
        user = await db.get(User, user_id)
        if user is None:
            user = User(
                id=user_id,
                email=email,
                full_name=full_name,
                password_hash=hash_password("Security123!"),
                status="active",
                school_id=SCHOOL_UUID,
            )
            db.add(user)
            await db.flush()

        membership = (
            await db.execute(
                select(Membership).where(
                    Membership.user_id == user_id,
                    Membership.school_id == SCHOOL_UUID,
                    Membership.role_code == role,
                )
            )
        ).scalar_one_or_none()
        if membership is None:
            db.add(
                Membership(
                    user_id=user_id,
                    school_id=SCHOOL_UUID,
                    role_code=role,
                    status="active",
                )
            )

        db.add(
            Session(
                id=session_id,
                user_id=user_id,
                school_id=SCHOOL_UUID,
                source="pytest-security",
                correlation_id=uuid.uuid4(),
            )
        )
        await db.commit()

    return SecurityActor(
        user_id=user_id,
        token=create_access_token(user_id, role, SCHOOL_UUID, session_id),
        email=email,
        role=role,
    )


async def ensure_parent_link(
    *,
    parent_id: uuid.UUID,
    student_id: uuid.UUID,
    status: str,
) -> None:
    async with async_session() as db:
        link = (
            await db.execute(
                select(ParentChildLink).where(
                    ParentChildLink.parent_user_id == parent_id,
                    ParentChildLink.child_user_id == student_id,
                    ParentChildLink.school_id == SCHOOL_UUID,
                )
            )
        ).scalar_one_or_none()
        if link is None:
            db.add(
                ParentChildLink(
                    parent_user_id=parent_id,
                    child_user_id=student_id,
                    school_id=SCHOOL_UUID,
                    status=status,
                    linked_at=datetime.now(timezone.utc),
                    linked_by=ADMIN_UUID,
                )
            )
        else:
            link.status = status
        await db.commit()


async def create_absence_record() -> uuid.UUID:
    attendance_session_id = uuid.uuid4()
    attendance_record_id = uuid.uuid4()
    async with async_session() as db:
        db.add(
            AttendanceSession(
                id=attendance_session_id,
                school_id=SCHOOL_UUID,
                class_id=CLASS_UUID,
                period_id=PERIOD_UUID,
                teacher_id=TEACHER_UUID,
                session_date=date(2026, 3, 30),
                slot=f"security-{uuid.uuid4().hex[:8]}",
            )
        )
        db.add(
            AttendanceRecord(
                id=attendance_record_id,
                school_id=SCHOOL_UUID,
                attendance_session_id=attendance_session_id,
                student_id=STUDENT_UUID,
                status="absent",
                absence_reason="Security test absence",
            )
        )
        await db.commit()
    return attendance_record_id


async def ensure_grade_category() -> uuid.UUID:
    """Create a grade category for the security test class/period if missing."""
    category_id = uuid.uuid5(uuid.NAMESPACE_URL, "security-grade-category")
    async with async_session() as db:
        existing = await db.get(GradeCategory, category_id)
        if existing is None:
            db.add(
                GradeCategory(
                    id=category_id,
                    school_id=SCHOOL_UUID,
                    class_id=CLASS_UUID,
                    period_id=PERIOD_UUID,
                    name="Contrôle continu",
                    weight=1.0,
                    position=0,
                )
            )
            await db.commit()
    return category_id


async def create_grading_scope_submission(*, teacher_id: uuid.UUID) -> dict[str, uuid.UUID]:
    course_id = uuid.uuid4()
    assignment_id = uuid.uuid4()
    submission_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    async with async_session() as db:
        db.add(
            Course(
                id=course_id,
                school_id=SCHOOL_UUID,
                class_id=CLASS_UUID,
                teacher_id=teacher_id,
                title=f"Security Course {course_id.hex[:8]}",
                description="RBAC grading scope fixture",
                status="published",
            )
        )
        db.add(
            Assignment(
                id=assignment_id,
                course_id=course_id,
                teacher_id=teacher_id,
                title=f"Security Assignment {assignment_id.hex[:8]}",
                description="Teacher-class ABAC fixture",
                due_at=now,
                total_points=20,
                grace_period_hours=0,
                late_penalty_per_day=2.0,
                max_late_days=5,
                allow_late=True,
                exercise_type="STANDARD",
            )
        )
        db.add(
            Submission(
                id=submission_id,
                assignment_id=assignment_id,
                student_id=STUDENT_UUID,
                status="submitted",
                submitted_at=now,
            )
        )
        await db.commit()

    return {
        "course_id": course_id,
        "assignment_id": assignment_id,
        "submission_id": submission_id,
    }


@pytest_asyncio.fixture(loop_scope="function")
async def superadmin_token(client: httpx.AsyncClient) -> str:
    return await login_token(
        client,
        email=SUPERADMIN_EMAIL,
        password=SUPERADMIN_PASSWORD,
    )


@pytest_asyncio.fixture(loop_scope="function")
async def content_mgr_token(client: httpx.AsyncClient) -> str:
    return await login_token(
        client,
        email=CONTENT_MGR_EMAIL,
        password=CONTENT_MGR_PASSWORD,
    )


@pytest_asyncio.fixture(loop_scope="function")
async def director_actor() -> SecurityActor:
    return await ensure_role_actor(
        role="DIR",
        key="director-role",
        full_name="Security Director",
    )


@pytest_asyncio.fixture(loop_scope="function")
async def director_token(director_actor: SecurityActor) -> str:
    return director_actor.token


@pytest_asyncio.fixture(loop_scope="function")
async def sys_actor() -> SecurityActor:
    return await ensure_role_actor(
        role="SYS",
        key="sys-role",
        full_name="Security System User",
    )


@pytest_asyncio.fixture(loop_scope="function")
async def sys_token(sys_actor: SecurityActor) -> str:
    return sys_actor.token


@pytest_asyncio.fixture(loop_scope="function")
async def other_teacher_actor() -> SecurityActor:
    return await ensure_role_actor(
        role="TCH",
        key="other-teacher",
        full_name="Security Other Teacher",
    )


@pytest_asyncio.fixture(loop_scope="function")
async def other_teacher_token(other_teacher_actor: SecurityActor) -> str:
    return other_teacher_actor.token


@pytest_asyncio.fixture(loop_scope="function")
async def unlinked_parent_actor() -> SecurityActor:
    actor = await ensure_role_actor(
        role="PAR",
        key="unlinked-parent",
        full_name="Security Unlinked Parent",
    )
    other_child = await ensure_role_actor(
        role="STD",
        key="unlinked-parent-child",
        full_name="Security Other Child",
    )
    await ensure_parent_link(
        parent_id=actor.user_id,
        student_id=other_child.user_id,
        status="active",
    )
    return actor


@pytest_asyncio.fixture(loop_scope="function")
async def unlinked_parent_token(unlinked_parent_actor: SecurityActor) -> str:
    return unlinked_parent_actor.token


@pytest_asyncio.fixture(loop_scope="function")
async def revoked_parent_actor() -> SecurityActor:
    actor = await ensure_role_actor(
        role="PAR",
        key="revoked-parent",
        full_name="Security Revoked Parent",
    )
    other_child = await ensure_role_actor(
        role="STD",
        key="revoked-parent-child",
        full_name="Security Revoked Parent Other Child",
    )
    await ensure_parent_link(
        parent_id=actor.user_id,
        student_id=other_child.user_id,
        status="active",
    )
    await ensure_parent_link(
        parent_id=actor.user_id,
        student_id=STUDENT_UUID,
        status="revoked",
    )
    return actor


@pytest_asyncio.fixture(loop_scope="function")
async def revoked_parent_token(revoked_parent_actor: SecurityActor) -> str:
    return revoked_parent_actor.token


@pytest_asyncio.fixture(loop_scope="function")
async def absence_record_id() -> uuid.UUID:
    return await create_absence_record()


@pytest_asyncio.fixture(loop_scope="function")
async def teacher_owned_submission() -> dict[str, uuid.UUID]:
    return await create_grading_scope_submission(teacher_id=TEACHER_UUID)


@pytest_asyncio.fixture(loop_scope="function")
async def other_teacher_owned_submission(
    other_teacher_actor: SecurityActor,
) -> dict[str, uuid.UUID]:
    return await create_grading_scope_submission(teacher_id=other_teacher_actor.user_id)


@pytest_asyncio.fixture(autouse=True, loop_scope="function")
async def _grade_category_for_abac() -> uuid.UUID:
    """Ensure a grade category exists so transcript endpoints don't 422."""
    return await ensure_grade_category()
