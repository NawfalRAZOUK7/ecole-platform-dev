"""Audit seeded demo data coverage.

Run after migrations and seeding:
    python -m app.seed_audit
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterable

from sqlalchemy import text

from app.core.database import async_session


def _quote_identifier(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _print_table(
    title: str, headers: Iterable[str], rows: Iterable[Iterable[object]]
) -> None:
    rows = [tuple(row) for row in rows]
    headers = tuple(headers)
    print(f"\n{title}")
    print("-" * len(title))
    print(" | ".join(headers))
    print(" | ".join("-" * len(header) for header in headers))
    for row in rows:
        print(" | ".join(str(value) for value in row))
    if not rows:
        print("(none)")


async def _count_tables() -> tuple[list[tuple[str, int]], list[str]]:
    async with async_session() as session:
        result = await session.execute(
            text(
                """
                select table_name
                from information_schema.tables
                where table_schema = 'public'
                  and table_type = 'BASE TABLE'
                  and table_name <> 'alembic_version'
                order by table_name
                """
            )
        )
        tables = [row[0] for row in result.all()]

        counts: list[tuple[str, int]] = []
        for table in tables:
            count_result = await session.execute(
                text(f"select count(*) from public.{_quote_identifier(table)}")
            )
            counts.append((table, int(count_result.scalar_one())))

    empty = [table for table, count in counts if count == 0]
    return counts, empty


async def main() -> None:
    counts, empty = await _count_tables()

    print("=" * 72)
    print("Ecole Platform seed audit")
    print("=" * 72)
    print(f"Tables checked: {len(counts)}")
    print(f"Empty app tables: {len(empty)}")
    if empty:
        print("Empty:", ", ".join(empty))
    else:
        print("Empty: none")

    async with async_session() as session:
        role_counts = (
            await session.execute(
                text(
                    """
                    select role_code, count(*) as memberships
                    from memberships
                    group by role_code
                    order by role_code
                    """
                )
            )
        ).all()
        _print_table("Role Memberships", ["role", "count"], role_counts)

        class_coverage = (
            await session.execute(
                text(
                    """
                    select
                        c.name,
                        count(distinct ta.teacher_id) as teachers,
                        count(distinct e.student_id) as students
                    from classes c
                    left join teacher_assignments ta on ta.class_id = c.id
                    left join enrollments e on e.class_id = c.id
                    group by c.id, c.name
                    order by c.name
                    """
                )
            )
        ).all()
        _print_table(
            "Class Coverage", ["class", "teachers", "students"], class_coverage
        )

        family_coverage = (
            await session.execute(
                text(
                    """
                    select
                        count(*) as links,
                        count(distinct parent_user_id) as parents,
                        count(distinct child_user_id) as students
                    from parent_child_links
                    """
                )
            )
        ).all()
        _print_table(
            "Parent/Child Coverage",
            ["links", "parents", "students"],
            family_coverage,
        )

        orphan_students = (
            await session.execute(
                text(
                    """
                    select count(*) as students_without_parent_link
                    from student_profiles sp
                    left join parent_child_links pcl on pcl.child_user_id = sp.user_id
                    where pcl.child_user_id is null
                    """
                )
            )
        ).all()
        _print_table("Student Link Gaps", ["students_without_parent"], orphan_students)

        content_review = (
            await session.execute(
                text(
                    """
                    select status, count(*)
                    from content_submissions
                    group by status
                    order by status
                    """
                )
            )
        ).all()
        _print_table("Content Review States", ["status", "count"], content_review)

        content_languages = (
            await session.execute(
                text(
                    """
                    select coalesce(language, 'none') as language, status, count(*)
                    from content_items
                    group by language, status
                    order by language, status
                    """
                )
            )
        ).all()
        _print_table(
            "Content Languages", ["language", "status", "count"], content_languages
        )

        micro_coverage = (
            await session.execute(
                text(
                    """
                    select
                        ms.name,
                        ms.status,
                        u.email as educator,
                        count(distinct mg.id) as groups,
                        count(distinct me.id) as enrollments,
                        count(distinct mp.id) as payments
                    from micro_schools ms
                    join users u on u.id = ms.educator_id
                    left join micro_groups mg on mg.micro_school_id = ms.id
                    left join micro_enrollments me on me.micro_group_id = mg.id
                    left join micro_payments mp on mp.micro_school_id = ms.id
                    group by ms.id, ms.name, ms.status, u.email
                    order by ms.name
                    """
                )
            )
        ).all()
        _print_table(
            "Micro-School Coverage",
            [
                "micro_school",
                "status",
                "educator",
                "groups",
                "enrollments",
                "payments",
            ],
            micro_coverage,
        )

        micro_resources = (
            await session.execute(
                text(
                    """
                    select language, resource_type, count(*)
                    from micro_resources
                    group by language, resource_type
                    order by language, resource_type
                    """
                )
            )
        ).all()
        _print_table(
            "Micro Resource Library",
            ["language", "resource_type", "count"],
            micro_resources,
        )


if __name__ == "__main__":
    asyncio.run(main())
