# repositories/ — Data Access Layer

Repository pattern implementation for async data access. Decouples business logic from database queries, enabling testability and flexibility.

## Overview

The Repository pattern provides an abstraction layer between services and the database:
- **Services** call repositories for data
- **Repositories** execute SQLAlchemy queries
- **Models** define schema and relationships
- **Schemas** validate response serialization

Pattern: `Service → Repository → SQLAlchemy → Database`

## Directory Structure

```
repositories/
├── base.py              # BaseRepository with CRUD template
├── auth.py, school.py, lms.py, billing.py, erp.py, …   # core aggregates
├── lms_quiz.py, lms_question_bank.py, lms_rubric.py
├── communication_calendar.py, communication_messaging.py, communication_notifications.py
├── content_documents.py, content_cms.py
├── academic_*.py        # gradebook, progress, attendance analytics, timetable, skill_passport
├── reports_analytics.py, reports_financial_health.py, reports_schedule.py
├── ai_games.py, ai_rewards.py
├── user_gdpr.py, user_profile.py, auth_login_history.py
├── admin_feature.py, admin_men_compliance.py
├── school_micro_school.py
├── profile_loader.py, …
└── README.md
```

## Base Repository Pattern

### base.py

All repositories inherit from `BaseRepository`, providing CRUD operations:

```python
class BaseRepository(Generic[T]):
    """Base repository with CRUD operations."""

    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model

    async def create(self, obj_in: SchemaType) -> T:
        """Create and persist new record."""
        db_obj = self.model(**obj_in.dict())
        self.session.add(db_obj)
        await self.session.commit()
        return db_obj

    async def get(self, id: int) -> Optional[T]:
        """Fetch record by ID."""
        return await self.session.get(self.model, id)

    async def list(
        self,
        limit: int = 20,
        offset: int = 0,
        filters: Optional[dict] = None,
    ) -> List[T]:
        """List records with pagination & filtering."""
        stmt = select(self.model)
        if filters:
            stmt = self._apply_filters(stmt, filters)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update(self, id: int, obj_in: SchemaType) -> Optional[T]:
        """Update record."""
        db_obj = await self.get(id)
        if not db_obj:
            return None
        for key, value in obj_in.dict(exclude_unset=True).items():
            setattr(db_obj, key, value)
        await self.session.commit()
        return db_obj

    async def delete(self, id: int) -> bool:
        """Delete record."""
        db_obj = await self.get(id)
        if not db_obj:
            return False
        await self.session.delete(db_obj)
        await self.session.commit()
        return True

    async def count(self) -> int:
        """Count total records."""
        stmt = select(func.count()).select_from(self.model)
        result = await self.session.execute(stmt)
        return result.scalar() or 0
```

## Domain-Specific Repositories

### auth.py — Authentication

User & session management queries:

```python
class UserRepository(BaseRepository[User]):
    """User account access."""

    async def get_by_email(self, email: str, school_id: int) -> Optional[User]:
        """Find user by email within school."""
        stmt = select(User).where(
            User.email == email,
            User.school_id == school_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_roles(self, user_id: int) -> Optional[User]:
        """Load user with roles eagerly."""
        stmt = select(User).where(User.id == user_id)
        stmt = stmt.options(
            joinedload(User.roles).joinedload(Role.permissions)
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_active_users_in_school(self, school_id: int) -> List[User]:
        """Get all active users in school."""
        stmt = select(User).where(
            User.school_id == school_id,
            User.is_active == True
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

class SessionRepository(BaseRepository[Session]):
    """JWT session management."""

    async def get_valid_session(self, token_hash: str) -> Optional[Session]:
        """Get non-expired session by token."""
        stmt = select(Session).where(
            Session.token_hash == token_hash,
            Session.expires_at > datetime.now(timezone.utc)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke_user_sessions(self, user_id: int) -> int:
        """Invalidate all sessions for user."""
        stmt = delete(Session).where(Session.user_id == user_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount
```

### lms.py — Learning Management

Course & assignment queries:

```python
class CourseRepository(BaseRepository[Course]):
    """Course access with eager loading."""

    async def get_by_school_and_code(
        self,
        school_id: int,
        code: str
    ) -> Optional[Course]:
        """Find course by school and code."""
        stmt = select(Course).where(
            Course.school_id == school_id,
            Course.code == code
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_courses_for_teacher(
        self,
        teacher_id: int,
        school_id: int,
        academic_year_id: int
    ) -> List[Course]:
        """Get all courses taught by teacher."""
        stmt = select(Course).where(
            Course.teacher_id == teacher_id,
            Course.school_id == school_id,
            Course.academic_year_id == academic_year_id
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_courses_for_student(
        self,
        student_id: int,
        academic_year_id: int
    ) -> List[Course]:
        """Get courses student is enrolled in."""
        stmt = select(Course).select_from(CourseEnrollment).join(Course).where(
            CourseEnrollment.student_id == student_id,
            Course.academic_year_id == academic_year_id
        ).distinct()
        result = await self.session.execute(stmt)
        return result.scalars().all()

class AssignmentRepository(BaseRepository[Assignment]):
    """Assignment queries with submissions."""

    async def get_with_submissions(
        self,
        assignment_id: int
    ) -> Optional[Assignment]:
        """Load assignment with all submissions."""
        stmt = select(Assignment).where(Assignment.id == assignment_id)
        stmt = stmt.options(joinedload(Assignment.submissions))
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_due_assignments(
        self,
        before_date: datetime
    ) -> List[Assignment]:
        """Get assignments due by date."""
        stmt = select(Assignment).where(
            Assignment.due_date <= before_date,
            Assignment.due_date.isnot(None)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
```

### gradebook.py — Grading

Grade entry & reporting:

```python
class GradeRepository(BaseRepository[Grade]):
    """Grade access with filtering."""

    async def get_student_grades(
        self,
        student_id: int,
        course_id: Optional[int] = None
    ) -> List[Grade]:
        """Get all grades for student, optionally by course."""
        stmt = select(Grade).where(Grade.student_id == student_id)
        if course_id:
            stmt = stmt.join(Assignment).where(Assignment.course_id == course_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def calculate_course_average(
        self,
        student_id: int,
        course_id: int
    ) -> Optional[Decimal]:
        """Weighted average grade in course."""
        stmt = select(func.avg(Grade.score)).where(
            Grade.student_id == student_id,
            Assignment.course_id == course_id
        ).select_from(Grade).join(Assignment)
        result = await self.session.execute(stmt)
        return result.scalar()

    async def get_grades_by_rubric(
        self,
        rubric_id: int
    ) -> List[Grade]:
        """Get all grades using specific rubric."""
        stmt = select(Grade).where(Grade.rubric_id == rubric_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
```

### billing.py — Invoicing & Payments

Financial queries:

```python
class InvoiceRepository(BaseRepository[Invoice]):
    """Invoice access with line items."""

    async def get_by_number(
        self,
        number: str,
        school_id: int
    ) -> Optional[Invoice]:
        """Find invoice by number."""
        stmt = select(Invoice).where(
            Invoice.number == number,
            Invoice.school_id == school_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_overdue_invoices(
        self,
        school_id: int,
        as_of_date: datetime = None
    ) -> List[Invoice]:
        """Get unpaid invoices past due date."""
        as_of = as_of_date or datetime.now(timezone.utc)
        stmt = select(Invoice).where(
            Invoice.school_id == school_id,
            Invoice.status.in_(['issued', 'overdue']),
            Invoice.due_date < as_of
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_school_revenue(
        self,
        school_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> Decimal:
        """Total revenue in period."""
        stmt = select(func.sum(Invoice.total_amount)).where(
            Invoice.school_id == school_id,
            Invoice.status == 'paid',
            Invoice.issue_date.between(start_date, end_date)
        )
        result = await self.session.execute(stmt)
        return result.scalar() or Decimal('0')
```

### analytics.py — KPI & Dashboard

Business intelligence queries:

```python
class AnalyticsRepository:
    """Cross-domain KPI computation."""

    async def get_enrollment_trend(
        self,
        school_id: int,
        months: int = 12
    ) -> List[dict]:
        """Student enrollment over time."""
        # Query enrollments grouped by month
        stmt = select(
            func.date_trunc('month', Enrollment.enrollment_date).label('month'),
            func.count(Enrollment.id).label('count')
        ).where(
            School.id == school_id
        ).group_by('month')
        # ... execute and format

    async def get_course_completion_rate(
        self,
        school_id: int,
        academic_year_id: int
    ) -> float:
        """% of courses completed by students."""
        # Count completed assignments vs total
        # ...

    async def get_attendance_rate(
        self,
        school_id: int,
        class_id: Optional[int] = None
    ) -> float:
        """Average attendance percentage."""
        # Calculate from attendance records
        # ...

    async def get_grading_lag(
        self,
        school_id: int
    ) -> timedelta:
        """Average time from submission to grade."""
        # Measure time between submission and grading
        # ...

    async def get_active_users(
        self,
        school_id: int,
        days: int = 30
    ) -> int:
        """Count users active in last N days."""
        since = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = select(func.count(distinct(User.id))).where(
            User.school_id == school_id,
            User.last_login > since
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0
```

### reports.py — Report Generation

Report queries:

```python
class ReportRepository(BaseRepository[Report]):
    """Report access & caching."""

    async def generate_student_report_card(
        self,
        student_id: int,
        academic_year_id: int
    ) -> ReportCardData:
        """Generate report card for student."""
        # Fetch grades, attendance, conduct
        grades = await self._get_grades(student_id, academic_year_id)
        attendance = await self._get_attendance(student_id, academic_year_id)
        return ReportCardData(
            student_id=student_id,
            grades=grades,
            attendance=attendance,
            # ...
        )

    async def get_class_summary(
        self,
        class_id: int,
        academic_year_id: int
    ) -> ClassSummary:
        """Statistical summary for class."""
        # Average grades, top/bottom students, etc.
        # ...
```

## Query Patterns

### Pagination

```python
async def list_courses(
    school_id: int,
    limit: int = 20,
    offset: int = 0
) -> tuple[List[Course], int]:
    """Paginated course listing."""
    # Count total
    count_stmt = select(func.count()).select_from(Course).where(
        Course.school_id == school_id
    )
    total = await self.session.execute(count_stmt)

    # Fetch page
    stmt = select(Course).where(
        Course.school_id == school_id
    ).limit(limit).offset(offset)
    result = await self.session.execute(stmt)
    courses = result.scalars().all()

    return courses, total.scalar()
```

### Eager Loading

```python
# Use joinedload to avoid N+1 queries
stmt = select(Course).where(Course.id == course_id)
stmt = stmt.options(
    joinedload(Course.assignments).joinedload(Assignment.submissions),
    joinedload(Course.teacher)
)
result = await self.session.execute(stmt)
return result.unique().scalar_one_or_none()
```

### Filtering & Search

```python
stmt = select(User).where(User.school_id == school_id)

if email_filter:
    stmt = stmt.where(User.email.ilike(f"%{email_filter}%"))

if created_after:
    stmt = stmt.where(User.created_at > created_after)

if sort_by:
    if sort_by.startswith('-'):
        stmt = stmt.order_by(getattr(User, sort_by[1:]).desc())
    else:
        stmt = stmt.order_by(getattr(User, sort_by).asc())

result = await self.session.execute(stmt)
```

## Testing Repositories

Repositories are easy to test with in-memory database:

```python
@pytest.fixture
async def test_user_repo(test_session):
    return UserRepository(test_session, User)

@pytest.mark.asyncio
async def test_get_by_email(test_user_repo):
    user = await test_user_repo.get_by_email("john@school.edu", school_id=1)
    assert user.id == 1
```

## Next Steps

- See `base.py` for BaseRepository implementation
- See `services/` for how repositories are used
- See `models/` for data structure definitions
- See `alembic/versions/` for schema migrations
