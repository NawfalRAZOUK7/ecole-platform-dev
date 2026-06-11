# Seeding

Development data is split by responsibility so relationship-heavy demos stay
readable and easy to audit.

## Commands

```bash
make seed-all
```

Runs `alembic upgrade head`, then the full seed flow.

```bash
make seed
```

Runs the core application seed and then imports friend educational content when
assets are available.

```bash
make seed-core
```

Runs only `python -m app.seed`.

```bash
make seed-friend-content
```

Imports friend stories, PDFs, and coloring content from available assets.

```bash
make seed-audit
```

Prints table counts and relationship coverage after a seed run: role
memberships, class teacher/student coverage, parent-child links, content review
states, content languages, and micro-school coverage.

## File Map

- `backend/app/seed.py`: main deterministic core seed and execution order.
- `backend/app/seed_enhanced.py`: larger demo data modules for existing domains
  such as students, attendance, billing, messaging, security, and micro-school.
- `backend/app/seed_extensions.py`: extension domains such as calendar,
  documents, reporting, programs, and notification preferences.
- `backend/app/seed_demo_scenarios.py`: scenario data layered on top of the core
  seed for role tabs, review states, reference lists, and micro-school edge
  cases.
- `backend/scripts/seed_friend_content.py`: optional imported educational
  content package backed by local assets.
- `backend/app/seed_audit.py`: read-only post-seed coverage report.

## Relationship Coverage

The seed keeps these relationships explicit:

- schools own classes, academic years, staff memberships, students, parents,
  billing, attendance, and school-scoped content.
- classes have both teacher assignments and enrolled students.
- parents are linked to children through `parent_child_links`.
- teachers own assignments, assessments, content, and review submissions.
- content review includes pending, under-review, approved, rejected, and
  promoted platform content states.
- micro-schools have educator memberships, groups, enrollments, payments,
  progress logs, and multilingual resources.

## Expected Flow

After schema changes or a fresh checkout:

```bash
make seed-all
make seed-audit
```

For trilingual audio and generated quizzes, the database must be migrated first
so the language columns exist before seeding.
