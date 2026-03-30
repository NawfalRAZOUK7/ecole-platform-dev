"""Seed a lightweight demo environment for local development."""

from __future__ import annotations

import asyncio
import uuid
from datetime import date, datetime, timedelta, timezone

import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.billing import FeeAssignment, FeeStructure
from app.models.erp import AcademicYear, Class, Enrollment, Period, TeacherAssignment
from app.models.iam import Membership, ParentChildLink, User
from app.models.lms import Assignment, Course, Grade, Submission
from app.models.school import School

DEMO_NAMESPACE = uuid.UUID("2d73fc1d-85ab-4c54-a337-876a8d7f4f46")
DEMO_PASSWORD = "Demo1234!"


def demo_id(name: str) -> uuid.UUID:
    return uuid.uuid5(DEMO_NAMESPACE, name)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def hash_password(raw_password: str) -> str:
    return bcrypt.hashpw(raw_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


async def upsert(session: AsyncSession, model) -> None:
    await session.merge(model)


async def seed_demo(session: AsyncSession) -> None:
    today = date.today()
    academic_year_start = today.year if today.month >= 9 else today.year - 1
    period_start = date(academic_year_start, 9, 1)
    period_end = date(academic_year_start + 1, 6, 30)

    school_id = demo_id("school")
    admin_id = demo_id("user-admin")
    teacher_ids = [demo_id("user-teacher-1"), demo_id("user-teacher-2"), demo_id("user-teacher-3")]
    parent_ids = [demo_id("user-parent-1"), demo_id("user-parent-2")]
    student_ids = [
        demo_id("user-student-1"),
        demo_id("user-student-2"),
        demo_id("user-student-3"),
        demo_id("user-student-4"),
        demo_id("user-student-5"),
    ]
    academic_year_id = demo_id("academic-year")
    period_id = demo_id("period-main")
    class_ids = [demo_id("class-1"), demo_id("class-2"), demo_id("class-3")]
    course_ids = [
        demo_id("course-math"),
        demo_id("course-physics"),
        demo_id("course-french"),
        demo_id("course-arabic"),
        demo_id("course-informatics"),
    ]
    fee_structure_id = demo_id("fee-structure")

    await upsert(
        session,
        School(
            id=school_id,
            name="Lycée Mohammed V",
            name_ar="ثانوية محمد الخامس",
            code="LMV-001",
            massar_code="MASSAR-LMV-001",
            status="active",
            address="10 Boulevard Mohammed V, Casablanca",
            city="Casablanca",
            region="Casablanca-Settat",
            phone="+212522100500",
            email="contact@ecole-demo.ma",
            website="https://demo.ecole-platform.ma",
            max_students=1500,
            max_teachers=150,
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
    )

    users = [
        (
            admin_id,
            "admin@ecole-demo.ma",
            "Nadia El Idrissi",
            "+212600000001",
            "ADM",
        ),
        (
            teacher_ids[0],
            "maths@ecole-demo.ma",
            "Youssef Kabbaj",
            "+212600000101",
            "TCH",
        ),
        (
            teacher_ids[1],
            "sciences@ecole-demo.ma",
            "Salma Benyoussef",
            "+212600000102",
            "TCH",
        ),
        (
            teacher_ids[2],
            "langues@ecole-demo.ma",
            "Omar El Fassi",
            "+212600000103",
            "TCH",
        ),
        (
            parent_ids[0],
            "parent1@ecole-demo.ma",
            "Karim Alaoui",
            "+212600000201",
            "PAR",
        ),
        (
            parent_ids[1],
            "parent2@ecole-demo.ma",
            "Meryem Bennani",
            "+212600000202",
            "PAR",
        ),
        (
            student_ids[0],
            "student1@ecole-demo.ma",
            "Amine Alaoui",
            "+212600000301",
            "STD",
        ),
        (
            student_ids[1],
            "student2@ecole-demo.ma",
            "Lina Alaoui",
            "+212600000302",
            "STD",
        ),
        (
            student_ids[2],
            "student3@ecole-demo.ma",
            "Sara Bennani",
            "+212600000303",
            "STD",
        ),
        (
            student_ids[3],
            "student4@ecole-demo.ma",
            "Zakaria Bennani",
            "+212600000304",
            "STD",
        ),
        (
            student_ids[4],
            "student5@ecole-demo.ma",
            "Aya El Mansouri",
            "+212600000305",
            "STD",
        ),
    ]

    for user_id, email, full_name, phone, role_code in users:
        await upsert(
            session,
            User(
                id=user_id,
                school_id=school_id,
                email=email,
                phone=phone,
                full_name=full_name,
                password_hash=hash_password(DEMO_PASSWORD),
                status="active",
            ),
        )
        await upsert(
            session,
            Membership(
                id=demo_id(f"membership-{role_code.lower()}-{user_id}"),
                user_id=user_id,
                school_id=school_id,
                role_code=role_code,
                status="active",
            ),
        )

    parent_links = [
        (parent_ids[0], student_ids[0]),
        (parent_ids[0], student_ids[1]),
        (parent_ids[1], student_ids[2]),
        (parent_ids[1], student_ids[3]),
        (parent_ids[1], student_ids[4]),
    ]
    for index, (parent_id, child_id) in enumerate(parent_links, start=1):
        await upsert(
            session,
            ParentChildLink(
                id=demo_id(f"parent-child-{index}"),
                parent_user_id=parent_id,
                child_user_id=child_id,
                school_id=school_id,
                status="active",
                linked_at=utc_now(),
                linked_by=admin_id,
            ),
        )

    await upsert(
        session,
        AcademicYear(
            id=academic_year_id,
            school_id=school_id,
            label=f"{academic_year_start}-{academic_year_start + 1}",
            date_start=period_start,
            date_end=period_end,
        ),
    )
    await upsert(
        session,
        Period(
            id=period_id,
            school_id=school_id,
            academic_year_id=academic_year_id,
            label="Année complète",
            status="active",
            date_start=period_start,
            date_end=period_end,
        ),
    )

    classes = [
        (class_ids[0], "1A", "1ère Année A"),
        (class_ids[1], "2A", "2ème Année A"),
        (class_ids[2], "3A", "3ème Année A"),
    ]
    for class_id, code, name in classes:
        await upsert(
            session,
            Class(
                id=class_id,
                school_id=school_id,
                code=code,
                academic_year_id=academic_year_id,
                name=name,
            ),
        )

    enrollments = [
        (student_ids[0], class_ids[0]),
        (student_ids[1], class_ids[0]),
        (student_ids[2], class_ids[1]),
        (student_ids[3], class_ids[1]),
        (student_ids[4], class_ids[2]),
    ]
    for index, (student_id, class_id) in enumerate(enrollments, start=1):
        await upsert(
            session,
            Enrollment(
                id=demo_id(f"enrollment-{index}"),
                student_id=student_id,
                class_id=class_id,
                period_id=period_id,
                school_id=school_id,
                status="active",
            ),
        )

    teacher_assignments = [
        (teacher_ids[0], class_ids[0]),
        (teacher_ids[1], class_ids[1]),
        (teacher_ids[2], class_ids[2]),
    ]
    for index, (teacher_id, class_id) in enumerate(teacher_assignments, start=1):
        await upsert(
            session,
            TeacherAssignment(
                id=demo_id(f"teacher-assignment-{index}"),
                teacher_id=teacher_id,
                class_id=class_id,
                period_id=period_id,
                school_id=school_id,
            ),
        )

    courses = [
        (course_ids[0], class_ids[0], teacher_ids[0], "Mathématiques", "Algèbre et logique"),
        (course_ids[1], class_ids[1], teacher_ids[1], "Physique", "Mécanique et mesures"),
        (course_ids[2], class_ids[0], teacher_ids[2], "Français", "Expression écrite et lecture"),
        (course_ids[3], class_ids[2], teacher_ids[2], "Arabe", "Langue et littérature"),
        (course_ids[4], class_ids[2], teacher_ids[0], "Informatique", "Initiation au numérique"),
    ]
    for course_id, class_id, teacher_id, title, description in courses:
        await upsert(
            session,
            Course(
                id=course_id,
                school_id=school_id,
                class_id=class_id,
                teacher_id=teacher_id,
                title=title,
                description=description,
                status="published",
            ),
        )

    assignment_id = demo_id("assignment-math")
    submission_id = demo_id("submission-math-student-1")
    grade_id = demo_id("grade-math-student-1")
    await upsert(
        session,
        Assignment(
            id=assignment_id,
            course_id=course_ids[0],
            teacher_id=teacher_ids[0],
            title="Devoir - Fonctions",
            description="Résoudre les exercices sur les fonctions linéaires.",
            due_at=utc_now() + timedelta(days=7),
            total_points=20,
            allow_late=True,
            late_penalty_per_day=2.0,
        ),
    )
    await upsert(
        session,
        Submission(
            id=submission_id,
            assignment_id=assignment_id,
            student_id=student_ids[0],
            status="graded",
            submitted_at=utc_now() - timedelta(days=1),
        ),
    )
    await upsert(
        session,
        Grade(
            id=grade_id,
            submission_id=submission_id,
            teacher_id=teacher_ids[0],
            score=16.5,
            feedback_text="Bon travail, continue ainsi.",
            published_at=utc_now(),
        ),
    )

    await upsert(
        session,
        FeeStructure(
            id=fee_structure_id,
            school_id=school_id,
            academic_year_id=academic_year_id,
            name="Plan Établissement",
            amount=500.0,
            currency="MAD",
            frequency="MONTHLY",
            due_day=5,
            applies_to_level=None,
            status="ACTIVE",
        ),
    )
    for index, student_id in enumerate(student_ids, start=1):
        await upsert(
            session,
            FeeAssignment(
                id=demo_id(f"fee-assignment-{index}"),
                fee_structure_id=fee_structure_id,
                student_id=student_id,
                school_id=school_id,
                status="ACTIVE",
            ),
        )

    await session.commit()

    print("Demo seed ready")
    print("  School: Lycée Mohammed V (LMV-001)")
    print("  Admin: admin@ecole-demo.ma / Demo1234!")
    print("  Teachers: 3 | Parents: 2 | Students: 5")
    print("  Classes: 3 | Courses: 5 | Billing plan: 500 MAD/month")


async def main() -> None:
    async with async_session() as session:
        await seed_demo(session)


if __name__ == "__main__":
    asyncio.run(main())
