# Testing Architecture — Ecole Platform

> Professional test suite design targeting 90%+ coverage with branch tracking.
> Infrastructure: pytest + factories + testcontainers.
> Covers: Unit, Integration, Security, Edge Case, Performance, Contract tests.

---

## Table of Contents

- [Current State Assessment](#current-state-assessment)
- [Target Architecture](#target-architecture)
- [Test Infrastructure](#test-infrastructure)
- [Category 1: Unit Tests](#category-1-unit-tests)
- [Category 2: Integration Tests](#category-2-integration-tests)
- [Category 3: Security Tests (RBAC + ABAC)](#category-3-security-tests)
- [Category 4: Edge Case Tests](#category-4-edge-case-tests)
- [Category 5: Performance Tests](#category-5-performance-tests)
- [Category 6: Contract Tests](#category-6-contract-tests)
- [Directory Structure](#directory-structure)
- [Configuration](#configuration)
- [Execution Plan](#execution-plan)

---

## Current State Assessment

| Metric | Current | Target |
|--------|---------|--------|
| Total tests | 430 | ~1,200+ |
| Line coverage | 67.8% | 90%+ |
| Branch coverage | Not tracked | 85%+ |
| Service coverage | 34.8% | 90%+ |
| API endpoint coverage | 46.8% | 95%+ |
| Unit test ratio | ~17% (74/430) | ~50% |
| Test execution time | ~45s | <60s (unit), <5min (full) |

**Key gaps to fill:**
1. Service layer business logic (34.8% → 90%+)
2. Branch coverage (0% → 85%+)
3. Unit tests with mocking (17% → 50%)
4. ABAC validation tests (0 → comprehensive)
5. Edge case / error path tests
6. Performance regression tests

---

## Target Architecture

### Test Pyramid

```
        ┌─────────────────┐
        │   E2E (existing) │  ~30 tests  — keep as-is
        │   WebSocket, flows│
        ├─────────────────┤
        │  Integration     │  ~300 tests — enhanced
        │  API + DB + Redis│
        ├─────────────────┤
        │  Unit Tests      │  ~600 tests — NEW
        │  Services, Domain│
        │  Pure functions  │
        ├─────────────────┤
        │  Security Matrix │  ~150 tests — enhanced
        │  RBAC + ABAC     │
        ├─────────────────┤
        │  Edge / Contract │  ~120 tests — NEW
        │  Performance     │
        └─────────────────┘
```

### Execution Tiers

| Tier | What | When | Time |
|------|------|------|------|
| `fast` | Unit tests only (mocked DB) | Every save / pre-commit | <15s |
| `integration` | Unit + Integration (real DB) | Pre-push / CI | <90s |
| `full` | All tests including performance | CI main branch | <5min |
| `security` | RBAC + ABAC matrix only | Weekly / pre-release | <60s |

---

## Test Infrastructure

### 1. Dependencies (add to requirements-test.txt)

```txt
# Testing framework
pytest==8.3.*
pytest-asyncio==0.24.*
pytest-cov==6.0.*

# NEW additions
pytest-factoryboy==2.7.*       # Model factories
testcontainers[postgres]==4.*  # Disposable PostgreSQL
pytest-xdist==3.5.*            # Parallel test execution
pytest-timeout==2.3.*          # Timeout per test
pytest-mock==3.14.*            # Enhanced mocking
respx==0.21.*                  # HTTP mock for external APIs
freezegun==1.4.*               # Time travel for date tests
hypothesis==6.100.*            # Property-based testing
faker==24.*                    # Realistic fake data
pytest-benchmark==4.0.*        # Performance benchmarks
```

### 2. Testcontainers Setup (conftest.py)

```python
"""Root conftest — disposable PostgreSQL + async session."""

import asyncio
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

from app.core.database import Base


@pytest.fixture(scope="session")
def event_loop():
    """Single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def postgres_url():
    """Spin up a disposable PostgreSQL container for the test session."""
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg.get_connection_url().replace("postgresql://", "postgresql+asyncpg://")


@pytest.fixture(scope="session")
async def engine(postgres_url):
    """Create async engine against test container."""
    eng = create_async_engine(postgres_url, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Per-test session with automatic rollback — full isolation."""
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        async with session.begin():
            yield session
            await session.rollback()  # Automatic cleanup
```

### 3. Model Factories (tests/factories/)

```python
"""tests/factories/iam.py — User and role factories."""

import factory
from faker import Faker

from app.models.iam import User, Membership, UserStatus, RoleCode
from tests.factories.base import AsyncSQLAlchemyFactory

fake = Faker("fr_FR")  # Moroccan-appropriate fake data


class UserFactory(AsyncSQLAlchemyFactory):
    class Meta:
        model = User

    email = factory.LazyFunction(lambda: fake.email())
    full_name = factory.LazyFunction(lambda: fake.name())
    phone = factory.LazyFunction(lambda: f"+212{fake.msisdn()[4:]}")
    password_hash = "$2b$12$test_hash_placeholder"
    status = UserStatus.ACTIVE.value
    school_id = factory.LazyFunction(lambda: uuid.uuid4())


class MembershipFactory(AsyncSQLAlchemyFactory):
    class Meta:
        model = Membership

    user = factory.SubFactory(UserFactory)
    role_code = RoleCode.STD.value
    status = "active"
```

**Factories to create for ALL domains:**

| Factory File | Models |
|-------------|--------|
| `factories/iam.py` | UserFactory, MembershipFactory, SessionFactory, InvitationCodeFactory, ParentChildLinkFactory, StudentProfileFactory, TeacherProfileFactory |
| `factories/school.py` | SchoolFactory |
| `factories/lms.py` | CourseFactory, AssignmentFactory, SubmissionFactory, GradeFactory, QuizFactory, QuizQuestionFactory, QuizAttemptFactory, ContentItemFactory |
| `factories/erp.py` | AcademicYearFactory, ClassFactory, EnrollmentFactory, AttendanceSessionFactory, AttendanceRecordFactory, TimetableSlotFactory |
| `factories/billing.py` | InvoiceFactory, InvoiceItemFactory, PaymentAttemptFactory, FeeStructureFactory, PaymentPlanFactory, InstallmentFactory |
| `factories/com.py` | NotificationFactory, ConversationFactory, MessageFactory, AnnouncementFactory |
| `factories/documents.py` | DocumentFactory, ResourceFactory, DocumentVersionFactory |
| `factories/calendar.py` | EventFactory, EventRSVPFactory |

---

## Category 1: Unit Tests

### 1A. Domain Value Object Tests (`tests/unit/domain/`)

```python
"""Test MoroccanGrade value object — exhaustive boundary testing."""

import pytest
from app.domain.value_objects.grade import MoroccanGrade


class TestMoroccanGrade:
    def test_valid_grade_zero(self):
        assert MoroccanGrade(0).value == 0

    def test_valid_grade_twenty(self):
        assert MoroccanGrade(20).value == 20

    def test_valid_grade_decimal(self):
        assert MoroccanGrade(15.75).value == 15.75

    def test_invalid_negative(self):
        with pytest.raises(ValueError, match="0-20"):
            MoroccanGrade(-1)

    def test_invalid_above_twenty(self):
        with pytest.raises(ValueError, match="0-20"):
            MoroccanGrade(21)

    def test_mention_tres_bien(self):
        assert MoroccanGrade(16).mention == "Très Bien"

    def test_mention_bien(self):
        assert MoroccanGrade(14).mention == "Bien"

    def test_mention_assez_bien(self):
        assert MoroccanGrade(12).mention == "Assez Bien"

    def test_mention_passable(self):
        assert MoroccanGrade(10).mention == "Passable"

    def test_mention_insuffisant(self):
        assert MoroccanGrade(9).mention == "Insuffisant"
```

**Files to create:**

| File | Tests | What |
|------|-------|------|
| `test_grade.py` | ~15 | MoroccanGrade boundaries, mentions, edge cases |
| `test_money.py` | ~12 | Money validation, MAD currency, arithmetic |
| `test_typed_id.py` | ~8 | UserId, SchoolId creation and validation |
| `test_role_set.py` | ~10 | RoleSet validation, membership checks |

### 1B. Service Unit Tests (`tests/unit/services/`)

**Pattern: Mock the repository, test only service logic.**

```python
"""Test GradingService — late penalty calculation, grade creation."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from app.services.lms.grading_service import GradingService
from app.services.lms._helpers import calculate_late_penalty


class TestCalculateLatePenalty:
    """Pure function — no mocking needed."""

    def test_no_penalty_within_grace_period(self):
        assignment = MagicMock(
            due_at=datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc),
            grace_period_hours=2,
            allow_late=True,
            late_penalty_per_day=5.0,
            max_late_days=3,
        )
        submission = MagicMock(
            submitted_at=datetime(2026, 3, 1, 13, 0, tzinfo=timezone.utc),
        )
        result = calculate_late_penalty(
            assignment=assignment, submission=submission, original_score=18.0
        )
        assert result["late_penalty"] == 0.0
        assert result["adjusted_score"] == 18.0

    def test_penalty_applied_after_grace(self):
        assignment = MagicMock(
            due_at=datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc),
            grace_period_hours=0,
            allow_late=True,
            late_penalty_per_day=2.0,
            max_late_days=5,
        )
        submission = MagicMock(
            submitted_at=datetime(2026, 3, 3, 12, 0, tzinfo=timezone.utc),
        )
        result = calculate_late_penalty(
            assignment=assignment, submission=submission, original_score=18.0
        )
        assert result["late_days"] == 2
        assert result["late_penalty"] == 4.0
        assert result["adjusted_score"] == 14.0

    def test_late_not_allowed_raises(self):
        assignment = MagicMock(
            due_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
            grace_period_hours=0,
            allow_late=False,
        )
        submission = MagicMock(
            submitted_at=datetime(2026, 3, 2, tzinfo=timezone.utc),
        )
        with pytest.raises(Exception, match="Late submissions are not allowed"):
            calculate_late_penalty(
                assignment=assignment, submission=submission, original_score=15.0
            )

    def test_max_late_days_exceeded_raises(self):
        assignment = MagicMock(
            due_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
            grace_period_hours=0,
            allow_late=True,
            late_penalty_per_day=1.0,
            max_late_days=2,
        )
        submission = MagicMock(
            submitted_at=datetime(2026, 3, 5, tzinfo=timezone.utc),
        )
        with pytest.raises(Exception, match="exceeded the maximum"):
            calculate_late_penalty(
                assignment=assignment, submission=submission, original_score=15.0
            )

    def test_score_cannot_go_below_zero(self):
        assignment = MagicMock(
            due_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
            grace_period_hours=0,
            allow_late=True,
            late_penalty_per_day=10.0,
            max_late_days=10,
        )
        submission = MagicMock(
            submitted_at=datetime(2026, 3, 4, tzinfo=timezone.utc),
        )
        result = calculate_late_penalty(
            assignment=assignment, submission=submission, original_score=5.0
        )
        assert result["adjusted_score"] == 0.0
```

**Service unit test files to create:**

| File | Service | Tests | Key scenarios |
|------|---------|-------|---------------|
| `test_grading_service.py` | GradingService | ~25 | Late penalty calc, grade create/update, override penalty, rubric rejection |
| `test_assignment_service.py` | AssignmentService | ~20 | CRUD, submission flow, file upload, finalization |
| `test_course_service.py` | CourseService | ~15 | CRUD, teacher ownership validation |
| `test_quiz_service.py` | QuizService | ~20 | Quiz creation, attempt flow, auto-grading, time limits |
| `test_billing_service.py` | BillingService | ~25 | Invoice generation, sibling discounts, late fees, payment plans |
| `test_attendance_service.py` | AttendanceAnalytics | ~15 | Threshold alerts, rate calculation, trends |
| `test_auth_service.py` | AuthService | ~20 | Login, impersonation, session limits, device detection |
| `test_communication_service.py` | CommunicationService | ~15 | STD messaging ABAC, conversation creation |
| `test_school_service.py` | SchoolService | ~10 | CRUD, subscription validation |
| `test_timetable_service.py` | TimetableGenerator | ~15 | Constraint validation, backtracking, preview vs apply |
| `test_gradebook_service.py` | GradebookService | ~15 | Weighted averages, GPA calc, Moroccan mentions |
| `test_report_service.py` | ReportService | ~10 | Schedule processing, format validation |

### 1C. Model Validator Tests (`tests/unit/models/`)

```python
"""Test SQLAlchemy validators on model fields."""

import pytest
from app.models.iam import User
from app.models.lms import Grade
from app.models.billing import Invoice


class TestUserValidators:
    def test_email_lowercased(self):
        user = User()
        result = user.validate_email("email", "JoHn@Example.COM")
        assert result == "john@example.com"

    def test_email_stripped(self):
        user = User()
        result = user.validate_email("email", " test@mail.com ")
        assert result == "test@mail.com"

    def test_email_invalid_raises(self):
        user = User()
        with pytest.raises(ValueError, match="Invalid email"):
            user.validate_email("email", "not-an-email")

    def test_phone_normalized(self):
        user = User()
        result = user.validate_phone("phone", "+212 6-12-34-56-78")
        assert result == "+212612345678"

    def test_phone_missing_country_code(self):
        user = User()
        with pytest.raises(ValueError, match="country code"):
            user.validate_phone("phone", "0612345678")


class TestGradeValidators:
    def test_score_valid_boundary(self):
        grade = Grade()
        assert grade.validate_score("score", 0) == 0
        assert grade.validate_score("score", 20) == 20

    def test_score_above_twenty_raises(self):
        grade = Grade()
        with pytest.raises(ValueError):
            grade.validate_score("score", 21)

    def test_score_negative_raises(self):
        grade = Grade()
        with pytest.raises(ValueError):
            grade.validate_score("score", -1)
```

### 1D. Permission & ABAC Unit Tests (`tests/unit/core/`)

```python
"""Test role hierarchy and effective permissions."""

from app.core.permissions import (
    get_effective_permissions,
    role_has_permission,
    ROLE_HIERARCHY,
    PERM_LMS_ASSIGNMENT_CREATE,
    PERM_ADM_SCHOOL_MANAGE,
    PERM_ERP_ATTENDANCE_ANALYTICS_READ,
)


class TestRoleHierarchy:
    def test_dir_inherits_tch(self):
        dir_perms = get_effective_permissions("DIR")
        tch_perms = get_effective_permissions("TCH")
        assert tch_perms.issubset(dir_perms)

    def test_adm_inherits_dir_and_tch(self):
        adm_perms = get_effective_permissions("ADM")
        dir_perms = get_effective_permissions("DIR")
        assert dir_perms.issubset(adm_perms)

    def test_sup_inherits_full_chain(self):
        sup_perms = get_effective_permissions("SUP")
        assert role_has_permission("SUP", PERM_LMS_ASSIGNMENT_CREATE)  # inherited from TCH
        assert role_has_permission("SUP", PERM_ADM_SCHOOL_MANAGE)  # direct

    def test_std_does_not_inherit_tch(self):
        assert not role_has_permission("STD", PERM_ERP_ATTENDANCE_ANALYTICS_READ)

    def test_par_independent_branch(self):
        par_perms = get_effective_permissions("PAR")
        tch_perms = get_effective_permissions("TCH")
        assert not tch_perms.issubset(par_perms)

    def test_circular_hierarchy_raises(self):
        """Verify circular reference detection works."""
        import pytest
        # This would only happen if someone misconfigures ROLE_HIERARCHY
        from app.core.permissions import get_effective_permissions
        # Current hierarchy should NOT raise
        get_effective_permissions("SYS")  # SYS → SUP → ADM → DIR → TCH
```

---

## Category 2: Integration Tests

### 2A. Database Integration (`tests/integration/`)

**Pattern: Real DB (testcontainer), real models, test full repository + service stack.**

```python
"""Test billing integration — invoice generation with sibling discounts."""

import pytest
from uuid import uuid4
from tests.factories.billing import InvoiceFactory, FeeStructureFactory
from tests.factories.iam import UserFactory
from tests.factories.erp import EnrollmentFactory


@pytest.mark.asyncio
class TestBillingIntegration:
    async def test_generate_invoice_applies_sibling_discount(self, db_session):
        school_id = uuid4()
        parent = await UserFactory.create(session=db_session, school_id=school_id)
        child1 = await UserFactory.create(session=db_session, school_id=school_id)
        child2 = await UserFactory.create(session=db_session, school_id=school_id)
        # ... setup parent-child links, enrollments, fee structures
        # ... call BillingService.generate_invoices()
        # ... assert discount applied to second child

    async def test_late_fee_applied_after_due_date(self, db_session):
        # ... test late fee calculation with real DB
        pass

    async def test_payment_plan_installment_tracking(self, db_session):
        # ... test payment plan lifecycle
        pass
```

### 2B. API Integration (`tests/integration/api/`)

**Pattern: Real FastAPI TestClient, real DB, test full request → response.**

```python
"""Test school API endpoints — full stack integration."""

@pytest.mark.asyncio
class TestSchoolAPI:
    async def test_create_school_as_sup(self, client, sup_token):
        response = await client.post(
            "/api/v1/schools",
            json={"name": "Ecole Test", "code": "TEST-001", "city": "Casablanca"},
            headers={"Authorization": f"Bearer {sup_token}"},
        )
        assert response.status_code == 201
        assert response.json()["data"]["name"] == "Ecole Test"

    async def test_create_school_as_teacher_forbidden(self, client, teacher_token):
        response = await client.post(
            "/api/v1/schools",
            json={"name": "Ecole Test", "code": "TEST-001"},
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert response.status_code == 403
```

---

## Category 3: Security Tests (RBAC + ABAC)

### 3A. Enhanced RBAC Matrix (`tests/security/`)

Expand the existing 56-test RBAC matrix to cover ALL new endpoints:

| Endpoint Group | Endpoints | Tests |
|----------------|-----------|-------|
| /schools | 5 | 40 (5 endpoints × 8 roles) |
| /gradebook | 6 | 48 |
| /rubrics | 5 | 40 |
| /question-bank | 4 | 32 |
| /billing/payment-plans | 4 | 32 |
| /analytics/attendance | 3 | 24 |
| /timetable-generation | 3 | 24 |
| /messages/search | 1 | 8 |

### 3B. ABAC Relationship Tests

```python
"""Test attribute-based access control — relationship validation."""

@pytest.mark.asyncio
class TestParentChildABAC:
    async def test_parent_can_view_own_child_grades(self, ...):
        """PAR with verified link → 200."""
        pass

    async def test_parent_cannot_view_other_child_grades(self, ...):
        """PAR without link to student → 403."""
        pass

    async def test_unverified_link_blocks_access(self, ...):
        """PAR with pending (not active) link → 403."""
        pass


@pytest.mark.asyncio
class TestStudentTeacherABAC:
    async def test_student_can_message_own_teacher(self, ...):
        """STD enrolled in class with teacher → message allowed."""
        pass

    async def test_student_cannot_message_unrelated_teacher(self, ...):
        """STD not enrolled in teacher's class → 403."""
        pass

    async def test_student_cannot_create_group_conversation(self, ...):
        """STD trying to create GROUP conversation → 400."""
        pass


@pytest.mark.asyncio
class TestTeacherClassABAC:
    async def test_teacher_can_grade_own_course(self, ...):
        pass

    async def test_teacher_cannot_grade_other_course(self, ...):
        pass
```

### 3C. Role Hierarchy Regression Tests

```python
"""Verify role hierarchy doesn't break permission resolution."""

@pytest.mark.parametrize("role,permission,expected", [
    ("TCH", "PERM-LMS:assignment:create", True),
    ("DIR", "PERM-LMS:assignment:create", True),   # inherited from TCH
    ("ADM", "PERM-LMS:assignment:create", True),   # inherited from DIR→TCH
    ("SUP", "PERM-LMS:assignment:create", True),   # inherited from ADM→DIR→TCH
    ("STD", "PERM-LMS:assignment:create", False),   # not in hierarchy
    ("PAR", "PERM-LMS:assignment:create", False),   # not in hierarchy
])
def test_hierarchy_permission_inheritance(role, permission, expected):
    assert role_has_permission(role, permission) == expected
```

---

## Category 4: Edge Case Tests

### 4A. Concurrency Tests

```python
"""Test concurrent operations don't cause race conditions."""

@pytest.mark.asyncio
class TestConcurrency:
    async def test_concurrent_session_limit(self, db_session):
        """6 concurrent logins with MAX_SESSIONS=5 → oldest revoked."""
        pass

    async def test_concurrent_grade_updates(self, db_session):
        """Two teachers grading same submission simultaneously."""
        pass

    async def test_concurrent_enrollment(self, db_session):
        """Same student enrolled twice in same class → unique constraint."""
        pass
```

### 4B. Boundary Value Tests

```python
"""Test extreme and boundary values."""

class TestBoundaryValues:
    def test_grade_score_exactly_zero(self): ...
    def test_grade_score_exactly_twenty(self): ...
    def test_invoice_total_zero(self): ...
    def test_discount_percent_zero(self): ...
    def test_discount_percent_hundred(self): ...
    def test_empty_string_email(self): ...
    def test_max_length_fields(self): ...
    def test_unicode_names(self):
        """Moroccan names with Arabic characters."""
        ...
    def test_pagination_limit_zero(self): ...
    def test_pagination_limit_max(self): ...
```

### 4C. Time-Based Tests (freezegun)

```python
"""Test time-dependent logic with frozen time."""

from freezegun import freeze_time

class TestTimeDependentLogic:
    @freeze_time("2026-09-01 08:00:00")  # School year start
    def test_session_not_expired_within_window(self): ...

    @freeze_time("2026-09-01 08:00:00")
    def test_assignment_is_past_due(self): ...

    @freeze_time("2026-12-31 23:59:59")
    def test_subscription_expires_at_midnight(self): ...

    @freeze_time("2026-06-15")
    def test_school_year_transition(self): ...
```

---

## Category 5: Performance Tests

### 5A. Benchmark Tests (pytest-benchmark)

```python
"""Performance benchmarks for critical operations."""

def test_permission_resolution_speed(benchmark):
    """get_effective_permissions should resolve in <1ms."""
    result = benchmark(get_effective_permissions, "SUP")
    assert len(result) > 50

def test_pagination_1000_records(benchmark, db_session):
    """Paginating 1000 records should complete in <100ms."""
    pass

def test_timetable_generation_20_classes(benchmark, db_session):
    """Generate timetable for 20 classes × 10 teachers in <30s."""
    pass
```

### 5B. Load Pattern Tests

```python
"""Simulate realistic load patterns."""

@pytest.mark.slow
class TestLoadPatterns:
    async def test_morning_login_burst(self):
        """Simulate 500 concurrent logins (school morning rush)."""
        pass

    async def test_grade_publishing_batch(self):
        """Teacher publishing 40 grades at once."""
        pass

    async def test_notification_fan_out(self):
        """Announcement to 1000 students generates 1000 notifications."""
        pass
```

---

## Category 6: Contract Tests

### 6A. API Response Contract Tests

```python
"""Verify API responses match schema contracts."""

from pydantic import TypeAdapter
from app.schemas.school import SchoolResponse


class TestSchoolContract:
    async def test_school_response_matches_schema(self, client, sup_token):
        response = await client.get(
            "/api/v1/schools",
            headers={"Authorization": f"Bearer {sup_token}"},
        )
        data = response.json()["data"]
        for school in data:
            TypeAdapter(SchoolResponse).validate_python(school)
```

### 6B. Migration Contract Tests

```python
"""Verify migrations are reversible and consistent."""

class TestMigrations:
    def test_all_migrations_have_downgrade(self): ...
    def test_migration_chain_is_linear(self): ...
    def test_enum_values_match_python_enums(self): ...
```

---

## Directory Structure

```
backend/tests/
├── conftest.py                          # Root: testcontainer setup, shared fixtures
├── factories/                           # Model factories
│   ├── __init__.py
│   ├── base.py                          # AsyncSQLAlchemyFactory base
│   ├── iam.py                           # User, Membership, Session, etc.
│   ├── school.py                        # School
│   ├── lms.py                           # Course, Assignment, Grade, Quiz, etc.
│   ├── erp.py                           # Class, Enrollment, Attendance, etc.
│   ├── billing.py                       # Invoice, Payment, etc.
│   ├── com.py                           # Notification, Conversation, etc.
│   ├── documents.py                     # Document, Resource, etc.
│   └── calendar.py                      # Event, RSVP, etc.
├── unit/                                # Fast, mocked tests
│   ├── __init__.py
│   ├── domain/                          # Value objects, events, protocols
│   │   ├── test_grade.py
│   │   ├── test_money.py
│   │   ├── test_typed_id.py
│   │   └── test_role_set.py
│   ├── models/                          # Validator tests, helper property tests
│   │   ├── test_validators.py
│   │   ├── test_helper_properties.py
│   │   └── test_repr.py
│   ├── core/                            # Permissions, ABAC, UoW
│   │   ├── test_permissions.py
│   │   ├── test_abac.py
│   │   └── test_role_hierarchy.py
│   └── services/                        # Service logic with mocked repos
│       ├── test_grading_service.py
│       ├── test_assignment_service.py
│       ├── test_course_service.py
│       ├── test_quiz_service.py
│       ├── test_billing_service.py
│       ├── test_attendance_service.py
│       ├── test_auth_service.py
│       ├── test_communication_service.py
│       ├── test_school_service.py
│       ├── test_timetable_service.py
│       ├── test_gradebook_service.py
│       └── test_report_service.py
├── integration/                         # Real DB tests
│   ├── __init__.py
│   ├── api/                             # Full API stack tests
│   │   ├── test_schools_api.py
│   │   ├── test_gradebook_api.py
│   │   ├── test_rubrics_api.py
│   │   ├── test_billing_api.py
│   │   ├── test_attendance_api.py
│   │   └── test_timetable_api.py
│   └── db/                              # Repository + DB tests
│       ├── test_school_repo.py
│       ├── test_lms_repo.py
│       └── test_billing_repo.py
├── security/                            # RBAC + ABAC tests
│   ├── test_rbac_matrix.py              # Enhanced existing
│   ├── test_abac_parent_child.py
│   ├── test_abac_student_teacher.py
│   ├── test_abac_teacher_class.py
│   ├── test_role_hierarchy.py
│   └── test_permission_escalation.py
├── edge/                                # Edge cases
│   ├── test_concurrency.py
│   ├── test_boundary_values.py
│   ├── test_time_dependent.py
│   └── test_error_paths.py
├── performance/                         # Benchmarks + load
│   ├── test_benchmarks.py
│   └── test_load_patterns.py
├── contract/                            # Schema + migration contracts
│   ├── test_api_contracts.py
│   └── test_migration_contracts.py
└── existing/                            # Move current tests here
    ├── test_auth.py
    ├── test_contract.py
    ├── test_phase*.py
    ├── test_rbac_security.py
    ├── test_security_audit.py
    └── test_unit_*.py
```

---

## Configuration

### pyproject.toml (pytest section)

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "session"
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "security: RBAC/ABAC security matrix tests",
    "performance: benchmark and load tests",
    "unit: fast unit tests with mocked dependencies",
    "integration: tests requiring real database",
]
addopts = [
    "--strict-markers",
    "--tb=short",
    "-q",
]

[tool.coverage.run]
source = ["app"]
branch = true
omit = [
    "app/alembic/*",
    "app/core/config.py",
]

[tool.coverage.report]
fail_under = 90
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "if __name__",
]
```

### Makefile additions

```makefile
test-unit:
	pytest tests/unit -m unit --timeout=10 -q

test-integration:
	pytest tests/unit tests/integration -m "unit or integration" --timeout=30

test-security:
	pytest tests/security -m security --timeout=60

test-full:
	pytest --cov=app --cov-branch --cov-report=html --cov-report=term-missing

test-perf:
	pytest tests/performance -m performance --timeout=300 --benchmark-enable
```

---

## Execution Plan

| Phase | Prompt | What | New tests | Cumulative |
|-------|--------|------|-----------|-----------|
| T-A | T-A1 | Infrastructure setup (conftest, factories, config) | 0 | 430 |
| T-B | T-B1 | Domain value object unit tests | ~45 | ~475 |
| T-B | T-B2 | Model validator + property unit tests | ~60 | ~535 |
| T-B | T-B3 | Permission + ABAC unit tests | ~40 | ~575 |
| T-C | T-C1 | Service unit tests (LMS: grading, assignment, quiz) | ~65 | ~640 |
| T-C | T-C2 | Service unit tests (billing, attendance, auth) | ~60 | ~700 |
| T-C | T-C3 | Service unit tests (communication, school, timetable, gradebook) | ~50 | ~750 |
| T-D | T-D1 | Integration tests (API endpoints) | ~80 | ~830 |
| T-D | T-D2 | Integration tests (DB repositories) | ~40 | ~870 |
| T-E | T-E1 | Security matrix expansion (RBAC + ABAC) | ~120 | ~990 |
| T-F | T-F1 | Edge case + boundary + time tests | ~80 | ~1,070 |
| T-F | T-F2 | Performance + contract tests | ~50 | ~1,120 |
| T-G | T-G1 | Coverage gap analysis + fill remaining to 90% | ~80 | ~1,200 |

**Total: 13 prompts, ~770 new tests, target 90%+ coverage with branch tracking.**
