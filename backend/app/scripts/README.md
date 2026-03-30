# scripts/ — Application Utility Scripts

One-off scripts and utilities for development, testing, and maintenance tasks.

## Directory Structure

```
scripts/
└── seed_demo.py    # Demo data generation script
```

## seed_demo.py — Demo Data Generation

Populates database with realistic Moroccan test data for development and testing.

### Purpose

- Quick local environment setup
- QA testing with meaningful data
- Demo presentations
- Load testing baseline
- Resetting database state

### Data Generated

```
Schools
├─ École Primaire Al-Farabi (Casablanca)
├─ Lycée Ibn Sina (Marrakech)
└─ Collège Mohammed VI (Rabat)

Users (by role)
├─ Administrators (ADM) × 2
├─ Directors (DIR) × 3
├─ Teachers (TCH) × 15
├─ Parents (PAR) × 30
├─ Students (STD) × 100
├─ Support (SUP) × 2
└─ System (SYS) × 1

Academic Structure
├─ Academic Year 2023-2024
├─ Classes: 6ème A-D, 5ème A-D, etc. × 12 classes
├─ Enrollments: ~8-10 students per class
└─ Class assignments: Teachers → Classes

Learning Content
├─ Courses: Mathematics, French, Science, History, etc.
├─ Assignments: 3-5 per course
├─ Quizzes: 2-3 per course
├─ Grades: Mix of scores (40-100%)
├─ Content items: 5-10 per course
└─ Submissions: Various completion states

Financial Data
├─ Invoices: Monthly tuition (2,500-3,500 MAD)
├─ Line items: Tuition, lab fees, materials
├─ Payments: Some paid, some overdue
├─ Subscriptions: Active school plans
└─ Payment plans: Sample arrangements

Calendar Events
├─ Parent-teacher conferences
├─ School holidays (Moroccan calendar)
├─ Exams and assessments
├─ Assembly meetings
└─ Sports events

Communication
├─ Messages: Teacher → Parent conversations
├─ Notifications: Grade published, payment due, etc.
├─ Announcements: School-wide updates
└─ Email logs: Delivery history
```

### Usage

```bash
# Run from backend directory
python -m app.scripts.seed_demo

# With custom options
python -m app.scripts.seed_demo --force --school-count 5 --students-per-class 25

# Reset and reseed
python -m app.scripts.seed_demo --truncate --seed
```

### Command-line Options

```
--force             Overwrite existing data (default: check for existing)
--school-count N    Number of schools to create (default: 3)
--classes-per-year N  Classes per academic year (default: 12)
--students-per-class N  Students per class (default: 9)
--grades-per-student N  Grades per student (default: 15)
--include-invoices  Create invoices (default: true)
--include-payments  Create some paid invoices (default: true)
--include-messages  Create sample messages (default: true)
--clean            Remove all data before seeding (use with caution)
```

### Features

#### Moroccan Data

- School names authentic to Morocco
- Student names in Arabic/French conventions
- Academic calendar aligned with Morocco (Sep-Jun)
- Currency in MAD (Moroccan Dirham)
- Regional organization (Casablanca, Marrakech, Rabat, etc.)
- Grade scale 0-20 (Moroccan standard)

#### Realistic Relationships

- Teachers assigned to multiple classes
- Parents linked to multiple students (siblings)
- Students enrolled in various courses
- Grades distributed across assignments
- Invoices with multiple line items
- Payment history with partial/full payments

#### Temporal Variety

- Dates spread across academic year
- Past, present, and future assignments
- Overdue and paid invoices
- Recent and older messages
- Graduated students (archived)

#### Role-Based Access

- Students see only their data
- Teachers see their classes
- Parents see their children
- Admins see all school data
- Support sees all schools

### Generated User Accounts

Test accounts created for manual testing:

```
School: École Al-Farabi

Admin
├─ Email: admin@ecole.test
├─ Password: AdminPass123!
└─ Role: ADM (Administrator)

Director
├─ Email: director@ecole.test
├─ Password: DirectorPass123!
└─ Role: DIR (Director)

Teacher
├─ Email: teacher@ecole.test
├─ Password: TeacherPass123!
└─ Role: TCH (Teacher)

Student
├─ Email: student@ecole.test
├─ Password: StudentPass123!
└─ Role: STD (Student)

Parent
├─ Email: parent@ecole.test
├─ Password: ParentPass123!
└─ Role: PAR (Parent)
```

### Implementation Details

The script:

1. **Checks existing data** — Won't overwrite unless `--force` flag
2. **Creates schools** — Sets up school hierarchy
3. **Generates users** — Creates users by role with realistic names
4. **Sets up academic structure** — Classes, enrollments, academic years
5. **Populates courses** — Courses with teachers and content
6. **Creates assignments** — With due dates spread throughout year
7. **Generates grades** — Mix of high/medium/low scores
8. **Creates invoices** — Monthly billing with payment history
9. **Adds events** — Calendar events, holidays, exams
10. **Logs completion** — Reports statistics (e.g., "Created 100 students, 300 invoices")

### Output

```
Seeding demo data...
✓ Created 3 schools
✓ Created 52 users
✓ Created 12 classes
✓ Created 108 enrollments
✓ Created 24 courses
✓ Created 72 assignments
✓ Created 900 grades
✓ Created 36 invoices
✓ Created 18 payments
✓ Created 50 messages
✓ Created 120 notifications
✓ Created 45 events

Total records created: 1,447
Time elapsed: 5.3 seconds
Database ready for development!
```

### Idempotency

Safe to run multiple times:
- Checks for existing test data
- Skips if data already seeded
- Use `--force` to regenerate
- Use `--clean` to start fresh (careful!)

### Performance

Optimized for large datasets:
- Batch inserts (100 records at a time)
- Minimal validation (seed data is trusted)
- Single database commit per batch
- Parallel processing for independent entities

### Testing with Seeds

```python
@pytest.fixture
async def seeded_db(db_session):
    """Database with demo data."""
    # seed_demo already ran
    # Use test accounts:
    # admin@ecole.test / AdminPass123!
    # student@ecole.test / StudentPass123!
    yield db_session

@pytest.mark.asyncio
async def test_student_can_view_grades(seeded_db):
    student = await seeded_db.get_by_email("student@ecole.test")
    grades = await service.get_student_grades(student.id)
    assert len(grades) > 0
```

### Cleanup

Remove seed data:

```bash
# Reset database to clean schema
alembic downgrade base
alembic upgrade head

# Re-seed with fresh data
python -m app.scripts.seed_demo
```

Or programmatically:

```python
# In development only!
async def cleanup_test_data():
    async with AsyncSession() as session:
        # Delete all users except system user
        await session.execute(delete(User).where(User.id != 1))
        await session.commit()
```

## Next Steps

- See `models/` for data structure definitions
- See `repositories/` for data access patterns
- See tests for usage examples
