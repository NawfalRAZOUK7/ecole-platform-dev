# OOP Architecture Standard — Ecole Platform

> Single source of truth for all OOP patterns applied during the OOP refactoring phase.
> This document complements ARCHITECTURE_STANDARD.md (3-tier patterns).

---

## Table of Contents

- [Part A: Unit of Work](#part-a-unit-of-work)
- [Part B: Value Objects](#part-b-value-objects)
- [Part C: ProfileLoader (User/Role Composition)](#part-c-profileloader)
- [Part D: Domain Events + Delivery Strategy (Communication)](#part-d-domain-events)
- [Part E: Evaluatable Protocol (Quiz/Assignment/Assessment)](#part-e-evaluatable-protocol)
- [Part F: LMS Service Splitting](#part-f-lms-service-splitting)
- [Naming Conventions](#naming-conventions)
- [File Structure](#file-structure)

---

## Part A: Unit of Work

### Purpose
Centralizes transaction management. Services NEVER call `db.commit()` or `db.rollback()` directly — they use `UnitOfWork` instead.

### Location
`backend/app/core/unit_of_work.py`

### Implementation

```python
"""Unit of Work — transaction boundary for services."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession


class UnitOfWork:
    """Manages a single database transaction.

    Usage:
        async with UnitOfWork(db) as uow:
            repo = UserRepository(uow.session)
            await repo.create(...)
            await uow.commit()
        # If exception occurs, rollback is automatic.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._committed = False

    @property
    def session(self) -> AsyncSession:
        return self._session

    async def commit(self) -> None:
        await self._session.commit()
        self._committed = True

    async def rollback(self) -> None:
        await self._session.rollback()

    async def __aenter__(self) -> UnitOfWork:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None and not self._committed:
            await self.rollback()
```

### Service Usage Pattern

```python
# BEFORE (scattered commits):
class AuthService:
    async def register(self, ...):
        user = User(...)
        self.db.add(user)
        await self.db.commit()           # commit #1
        membership = Membership(...)
        self.db.add(membership)
        await self.db.commit()           # commit #2 — if this fails, user is orphaned!

# AFTER (UnitOfWork):
class AuthService:
    async def register(self, ...):
        async with UnitOfWork(self.db) as uow:
            user_repo = UserRepository(uow.session)
            membership_repo = MembershipRepository(uow.session)
            user = await user_repo.create(...)
            await membership_repo.create(user_id=user.id, ...)
            await uow.commit()  # ALL or NOTHING
```

### Rules
1. Services receive `AsyncSession` via dependency injection (no change).
2. Services create `UnitOfWork(self.db)` at the start of write operations.
3. Read-only operations do NOT need UnitOfWork — just use the repository directly.
4. Repositories NEVER call `commit()` or `rollback()` — only UnitOfWork does.
5. One UnitOfWork per HTTP request (one transaction boundary).

---

## Part B: Value Objects

### Purpose
Type-safe wrappers for domain-specific values. Prevent bugs like assigning grade 25 on a 0-20 scale, mixing school_id with user_id, or calculating money without rounding.

### Location
`backend/app/domain/value_objects/`

### MoroccanGrade

```python
"""Moroccan grading scale (0-20)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass(frozen=True, slots=True)
class MoroccanGrade:
    """Immutable grade value on the 0-20 Moroccan scale."""

    value: Decimal

    def __post_init__(self) -> None:
        if not (Decimal("0") <= self.value <= Decimal("20")):
            raise ValueError(f"Grade must be 0-20, got {self.value}")

    @classmethod
    def from_float(cls, v: float) -> MoroccanGrade:
        return cls(Decimal(str(v)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    @classmethod
    def average(cls, grades: list[MoroccanGrade]) -> MoroccanGrade:
        if not grades:
            raise ValueError("Cannot average empty list")
        total = sum(g.value for g in grades)
        avg = (total / len(grades)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return cls(avg)

    @property
    def mention(self) -> str:
        """Moroccan mention based on grade."""
        if self.value >= Decimal("16"):
            return "Très Bien"
        if self.value >= Decimal("14"):
            return "Bien"
        if self.value >= Decimal("12"):
            return "Assez Bien"
        if self.value >= Decimal("10"):
            return "Passable"
        return "Insuffisant"

    def __float__(self) -> float:
        return float(self.value)

    def __str__(self) -> str:
        return f"{self.value}/20"
```

### Money

```python
"""Moroccan Dirham money value object."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass(frozen=True, slots=True)
class Money:
    """Immutable monetary value in MAD (Moroccan Dirham)."""

    amount: Decimal
    currency: str = "MAD"

    def __post_init__(self) -> None:
        if self.amount < Decimal("0"):
            raise ValueError(f"Money cannot be negative: {self.amount}")

    @classmethod
    def from_float(cls, v: float, currency: str = "MAD") -> Money:
        return cls(
            Decimal(str(v)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            currency,
        )

    @classmethod
    def zero(cls, currency: str = "MAD") -> Money:
        return cls(Decimal("0.00"), currency)

    def __add__(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} + {other.currency}")
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract {self.currency} - {other.currency}")
        result = self.amount - other.amount
        if result < Decimal("0"):
            raise ValueError("Result would be negative")
        return Money(result, self.currency)

    def __mul__(self, factor: int | float | Decimal) -> Money:
        result = (self.amount * Decimal(str(factor))).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        return Money(result, self.currency)

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"
```

### TypedId

```python
"""Typed UUID wrappers to prevent ID mixups."""

from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UserId:
    value: uuid.UUID

    @classmethod
    def from_str(cls, s: str) -> UserId:
        return cls(uuid.UUID(s))

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class SchoolId:
    value: uuid.UUID

    @classmethod
    def from_str(cls, s: str) -> SchoolId:
        return cls(uuid.UUID(s))

    def __str__(self) -> str:
        return str(self.value)
```

### RoleSet

```python
"""Type-safe role set with validation."""

from __future__ import annotations

from dataclasses import dataclass

VALID_ROLES = {"STD", "PAR", "TCH", "ADM", "DIR", "SYS", "CONTENT_MGR", "SUP"}

ROLE_COMPATIBILITY = {
    # Roles that can coexist on the same user
    "TCH": {"PAR", "CONTENT_MGR"},
    "ADM": {"DIR"},
    "DIR": {"ADM"},
    "PAR": {"TCH"},
    "CONTENT_MGR": {"TCH"},
}


@dataclass(frozen=True, slots=True)
class RoleSet:
    """Immutable set of validated roles for a user."""

    roles: frozenset[str]

    def __post_init__(self) -> None:
        invalid = self.roles - VALID_ROLES
        if invalid:
            raise ValueError(f"Invalid roles: {invalid}")

    def has(self, role: str) -> bool:
        return role in self.roles

    def has_any(self, *roles: str) -> bool:
        return bool(self.roles & set(roles))

    @property
    def is_staff(self) -> bool:
        return self.has_any("ADM", "DIR", "SYS", "SUP")

    @property
    def is_educator(self) -> bool:
        return self.has_any("TCH", "CONTENT_MGR")

    @property
    def primary_role(self) -> str:
        """Highest-priority role for display purposes."""
        priority = ["SUP", "SYS", "DIR", "ADM", "CONTENT_MGR", "TCH", "PAR", "STD"]
        for role in priority:
            if role in self.roles:
                return role
        return "STD"
```

### Rules
1. Value objects are IMMUTABLE (`frozen=True`).
2. All validation happens in `__post_init__`.
3. Services use value objects for business logic, convert to/from primitives at repository boundary.
4. Repositories accept and return primitives (the DB doesn't know about value objects).
5. Conversion happens in the service layer: `grade = MoroccanGrade.from_float(row.score)`.

---

## Part C: ProfileLoader

### Purpose
Dynamically loads role-specific profiles for a user based on their active memberships. Replaces scattered profile queries across services.

### Location
`backend/app/services/profile_loader.py`

### New Profile Tables

```python
# Add to backend/app/models/iam.py:

class AdminProfile(TimestampMixin, Base):
    """Extended profile for ADM/DIR roles."""
    __tablename__ = "admin_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    management_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    can_approve_budgets: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(foreign_keys=[user_id])

    __table_args__ = (
        Index("idx_admin_profiles_user", "user_id"),
        Index("idx_admin_profiles_school", "school_id"),
    )


class ContentManagerProfile(TimestampMixin, Base):
    """Extended profile for CONTENT_MGR role."""
    __tablename__ = "content_manager_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    specialization: Mapped[str | None] = mapped_column(String(200), nullable=True)
    languages_managed: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    approved_subjects: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list

    user: Mapped["User"] = relationship(foreign_keys=[user_id])

    __table_args__ = (
        Index("idx_content_manager_profiles_user", "user_id"),
        Index("idx_content_manager_profiles_school", "school_id"),
    )
```

### ProfileLoader Service

```python
"""Loads role-specific profiles for a user."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.profile import ProfileRepository


# Maps role codes to the profile model they need
ROLE_PROFILE_MAP: dict[str, str] = {
    "STD": "student",
    "PAR": "parent",
    "TCH": "teacher",
    "ADM": "admin",
    "DIR": "admin",       # Directors share AdminProfile
    "CONTENT_MGR": "content_manager",
}


class ProfileLoader:
    """Loads all applicable profiles for a user based on their roles."""

    def __init__(self, db: AsyncSession) -> None:
        self._repo = ProfileRepository(db)

    async def load(self, user_id: UUID, role_codes: list[str]) -> dict[str, Any]:
        """Returns {profile_type: profile_data} for all roles that have profiles.

        Example: {"teacher": TeacherProfile(...), "parent": ParentProfile(...)}
        """
        profiles: dict[str, Any] = {}
        seen_types: set[str] = set()

        for role in role_codes:
            profile_type = ROLE_PROFILE_MAP.get(role)
            if profile_type and profile_type not in seen_types:
                seen_types.add(profile_type)
                profile = await self._repo.find_profile(user_id, profile_type)
                if profile:
                    profiles[profile_type] = profile

        return profiles

    async def ensure_profile(self, user_id: UUID, school_id: UUID, role: str) -> Any:
        """Creates a profile for the role if it doesn't exist yet."""
        profile_type = ROLE_PROFILE_MAP.get(role)
        if not profile_type:
            return None
        existing = await self._repo.find_profile(user_id, profile_type)
        if existing:
            return existing
        return await self._repo.create_profile(user_id, school_id, profile_type)
```

### Rules
1. SUP and SYS roles do NOT get profiles — they are platform-level system accounts.
2. DIR uses AdminProfile (same table as ADM) — distinguished by `management_level`.
3. When a user gains a new role (e.g., teacher becomes parent), `ensure_profile()` auto-creates.
4. ProfileLoader is used by AuthService (login/me endpoint) and ProfileService (profile editing).
5. New Alembic migration required for `admin_profiles` and `content_manager_profiles` tables.

---

## Part D: Domain Events + Delivery Strategy

### Purpose
Decouples "what happened" from "how to notify." Services emit domain events; the event dispatcher routes them to delivery strategies (push, email, SMS, in-app).

### Location
```
backend/app/domain/events/          # Event definitions
backend/app/domain/events/base.py
backend/app/domain/events/lms.py
backend/app/domain/events/calendar.py
backend/app/domain/events/billing.py
backend/app/domain/events/documents.py
backend/app/domain/events/auth.py

backend/app/services/event_dispatcher.py   # Dispatcher
backend/app/services/delivery/             # Strategies
backend/app/services/delivery/base.py
backend/app/services/delivery/push.py
backend/app/services/delivery/email.py
backend/app/services/delivery/sms.py
backend/app/services/delivery/in_app.py
```

### Event Base

```python
"""Base domain event."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events."""
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    school_id: UUID | None = None
    actor_id: UUID | None = None  # User who triggered the event
```

### Concrete Events

```python
# backend/app/domain/events/lms.py
from dataclasses import dataclass
from uuid import UUID
from app.domain.events.base import DomainEvent

@dataclass(frozen=True)
class GradePublished(DomainEvent):
    student_id: UUID = None
    course_title: str = ""
    score: float = 0.0
    teacher_name: str = ""

@dataclass(frozen=True)
class AssignmentCreated(DomainEvent):
    assignment_id: UUID = None
    course_title: str = ""
    due_at: str = ""
    class_id: UUID = None

@dataclass(frozen=True)
class QuizCompleted(DomainEvent):
    student_id: UUID = None
    quiz_title: str = ""
    score_percent: float = 0.0

@dataclass(frozen=True)
class SubmissionReceived(DomainEvent):
    submission_id: UUID = None
    student_name: str = ""
    assignment_title: str = ""
    teacher_id: UUID = None
```

### Delivery Strategy Base

```python
# backend/app/services/delivery/base.py
from __future__ import annotations
from abc import ABC, abstractmethod
from uuid import UUID
from app.domain.events.base import DomainEvent

class DeliveryStrategy(ABC):
    """Abstract delivery strategy for domain events."""

    @abstractmethod
    async def deliver(
        self,
        event: DomainEvent,
        recipients: list[UUID],
        template_key: str,
        context: dict,
    ) -> None:
        """Deliver notification to recipients."""
        ...
```

### Event Dispatcher

```python
# backend/app/services/event_dispatcher.py
from __future__ import annotations

from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.events.base import DomainEvent
from app.services.delivery.push import PushDeliveryStrategy
from app.services.delivery.email import EmailDeliveryStrategy
from app.services.delivery.in_app import InAppDeliveryStrategy


# Registry: event type -> list of (strategy, template_key, recipient_resolver)
EVENT_HANDLERS: dict[type, list[dict[str, Any]]] = {
    "GradePublished": [
        {"strategy": PushDeliveryStrategy, "template": "grade_published"},
        {"strategy": EmailDeliveryStrategy, "template": "grade_published"},
        {"strategy": InAppDeliveryStrategy, "template": "grade_published"},
    ],
    "AssignmentCreated": [
        {"strategy": PushDeliveryStrategy, "template": "assignment_created"},
        {"strategy": InAppDeliveryStrategy, "template": "assignment_created"},
    ],
    "DocumentExpiring": [
        {"strategy": PushDeliveryStrategy, "template": "document_expiring"},
        {"strategy": EmailDeliveryStrategy, "template": "document_expiring"},
    ],
    # ... register all events
}


class EventDispatcher:
    """Routes domain events to delivery strategies."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def dispatch(self, event: DomainEvent) -> None:
        event_type = type(event).__name__
        handlers = EVENT_HANDLERS.get(event_type, [])

        for handler in handlers:
            strategy = handler["strategy"](self._db)
            recipients = await self._resolve_recipients(event)
            context = self._build_context(event)
            await strategy.deliver(event, recipients, handler["template"], context)

    async def _resolve_recipients(self, event: DomainEvent) -> list:
        """Determines who should receive this event's notifications.

        Uses consent preferences to filter out opted-out users.
        """
        # Implementation reads ConsentPreference + NotificationPreference
        # to determine which users want which channels
        ...

    def _build_context(self, event: DomainEvent) -> dict:
        """Converts event fields to template context dict."""
        from dataclasses import asdict
        return asdict(event)
```

### Service Usage (Before vs After)

```python
# BEFORE — tight coupling:
class LMSService:
    async def publish_grade(self, ...):
        grade = await self._repo.update_grade(...)
        # Direct notification call — LMS knows about notifications
        await self.notification_hub.create_notification(
            recipient_id=grade.student_id,
            title="Grade published",
            body=f"Score: {grade.score}/20",
            category="academic",
        )
        await self.email_service.send_grade_email(...)

# AFTER — decoupled:
class LMSService:
    async def publish_grade(self, ...):
        async with UnitOfWork(self.db) as uow:
            grade = await self._repo.update_grade(...)
            await uow.commit()
        # Emit event — LMS doesn't know about notifications
        await self._dispatcher.dispatch(
            GradePublished(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                student_id=grade.student_id,
                course_title=course.title,
                score=float(grade.score),
                teacher_name=auth.full_name,
            )
        )
```

### Rules
1. Services NEVER import notification/email services directly — they emit events.
2. Event classes are IMMUTABLE (frozen dataclass).
3. Each event carries enough context for ALL delivery strategies to work.
4. Recipient resolution checks ConsentPreference and NotificationPreference.
5. Strategies are independent — push failure doesn't block email delivery.
6. New events are added by: (a) define dataclass, (b) register in EVENT_HANDLERS, (c) emit from service.

---

## Part E: Evaluatable Protocol

### Purpose
Unifies Quiz, Assignment, and Assessment under a shared interface so services can work with any "student work" type polymorphically.

### Location
```
backend/app/domain/protocols/evaluatable.py
backend/app/domain/protocols/grading.py
```

### Evaluatable Protocol

```python
"""Protocol for any gradeable student work."""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from datetime import datetime
from uuid import UUID


@runtime_checkable
class Evaluatable(Protocol):
    """Interface implemented by Quiz, Assignment, and Assessment repositories."""

    async def list_for_class(
        self, school_id: UUID, class_id: UUID, *, status: str | None = None
    ) -> list[dict]:
        """List all evaluatables for a class."""
        ...

    async def list_for_student(
        self, school_id: UUID, student_id: UUID
    ) -> list[dict]:
        """List all evaluatables assigned to a student."""
        ...

    async def get_detail(self, item_id: UUID) -> dict | None:
        """Get full detail of one evaluatable."""
        ...

    async def get_results(self, item_id: UUID) -> list[dict]:
        """Get all student results/submissions for this item."""
        ...
```

### Grading Strategy

```python
"""Grading strategies for different evaluatable types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.value_objects.grade import MoroccanGrade


class GradingStrategy(ABC):
    """Abstract grading strategy."""

    @abstractmethod
    async def grade(self, item_id: UUID, student_id: UUID, **kwargs) -> MoroccanGrade:
        ...

    @abstractmethod
    async def can_auto_grade(self) -> bool:
        ...


class QuizAutoGradeStrategy(GradingStrategy):
    """Auto-grades quiz based on correct answers in JSONB."""

    async def grade(self, item_id: UUID, student_id: UUID, **kwargs) -> MoroccanGrade:
        # Read quiz questions + student answers from attempt
        # Calculate score as (correct / total) * 20
        ...

    async def can_auto_grade(self) -> bool:
        return True


class ManualGradeStrategy(GradingStrategy):
    """Manual grading by teacher — used for assignments and assessments."""

    async def grade(self, item_id: UUID, student_id: UUID, **kwargs) -> MoroccanGrade:
        score = kwargs.get("score")
        if score is None:
            raise ValueError("Manual grading requires a score")
        return MoroccanGrade.from_float(score)

    async def can_auto_grade(self) -> bool:
        return False
```

### Unified Student Work Service

```python
"""Unified view of all student work (quizzes, assignments, assessments)."""

from __future__ import annotations

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.lms import AssignmentRepository
from app.repositories.quiz import QuizRepository
from app.repositories.lms import AssessmentRepository


class StudentWorkService:
    """Provides a unified view across all evaluatable types."""

    def __init__(self, db: AsyncSession) -> None:
        self._assignment_repo = AssignmentRepository(db)
        self._quiz_repo = QuizRepository(db)
        self._assessment_repo = AssessmentRepository(db)

    async def list_all_for_student(
        self, school_id: UUID, student_id: UUID
    ) -> list[dict]:
        """Returns unified list of all work items for a student, sorted by due date."""
        assignments = await self._assignment_repo.list_for_student(school_id, student_id)
        quizzes = await self._quiz_repo.list_for_student(school_id, student_id)
        assessments = await self._assessment_repo.list_for_student(school_id, student_id)

        unified = []
        for item in assignments:
            unified.append({"type": "assignment", "grading": "manual", **item})
        for item in quizzes:
            unified.append({"type": "quiz", "grading": "auto", **item})
        for item in assessments:
            unified.append({"type": "assessment", "grading": "manual", **item})

        unified.sort(key=lambda x: x.get("due_at") or "", reverse=True)
        return unified
```

### Rules
1. Repositories for Quiz, Assignment, Assessment each implement the Evaluatable protocol methods.
2. StudentWorkService provides the unified view for parent/student dashboards.
3. GradingStrategy is chosen based on evaluatable type, not hardcoded in services.
4. No database changes required — protocol is Python-only.
5. New evaluatable types (e.g., ProjectWork) just implement the protocol.

---

## Part F: LMS Service Splitting

### Purpose
Split `lms.py` (76KB, largest file) into focused sub-services.

### New Structure
```
backend/app/services/lms/
    __init__.py          # Re-exports for backward compat
    course_service.py    # Course CRUD, status management
    assignment_service.py # Assignment CRUD, submissions, grading
    quiz_service.py      # Quiz engine, attempts, auto-grading
    content_service.py   # Content items, assets, progress tracking
    progress_service.py  # Student progress aggregation, reporting
```

### Migration Strategy
1. Create `services/lms/` directory.
2. Move methods from `lms.py` to appropriate sub-service (keep signatures identical).
3. `services/lms/__init__.py` re-exports all classes:
   ```python
   from app.services.lms.course_service import CourseService
   from app.services.lms.assignment_service import AssignmentService
   from app.services.lms.quiz_service import QuizService
   from app.services.lms.content_service import ContentService
   from app.services.lms.progress_service import ProgressService
   ```
4. Update router imports from `app.services.lms import LMSService` to specific sub-service.
5. Each sub-service receives `AsyncSession` and uses `UnitOfWork` for writes.

### Rules
1. Keep the `__init__.py` re-exports so existing imports don't break during migration.
2. Each sub-service should be under 500 lines.
3. Shared LMS helpers go in `services/lms/_helpers.py` (private module).
4. Repositories are NOT split — `LMSRepository` stays as one file (it's data access, not business logic).

---

## Naming Conventions

| Concept | Pattern | Example |
|---------|---------|---------|
| Value Object | `PascalCase`, in `domain/value_objects/` | `MoroccanGrade`, `Money` |
| Domain Event | `PastTense` verb, in `domain/events/` | `GradePublished`, `AssignmentCreated` |
| Protocol | `PascalCase` noun, in `domain/protocols/` | `Evaluatable`, `GradingStrategy` |
| Delivery Strategy | `*DeliveryStrategy`, in `services/delivery/` | `PushDeliveryStrategy` |
| Sub-service | `*Service`, in `services/lms/` | `CourseService`, `QuizService` |

---

## File Structure (New Files)

```
backend/app/
├── core/
│   └── unit_of_work.py              # NEW
├── domain/                           # NEW directory
│   ├── __init__.py
│   ├── value_objects/
│   │   ├── __init__.py
│   │   ├── grade.py                  # MoroccanGrade
│   │   ├── money.py                  # Money
│   │   ├── typed_id.py              # UserId, SchoolId
│   │   └── role_set.py             # RoleSet
│   ├── events/
│   │   ├── __init__.py
│   │   ├── base.py                  # DomainEvent
│   │   ├── lms.py                   # GradePublished, AssignmentCreated, ...
│   │   ├── calendar.py             # EventCreated, HolidayAdded, ...
│   │   ├── billing.py             # PaymentReceived, InvoiceGenerated, ...
│   │   ├── documents.py           # DocumentExpiring, DocumentUploaded, ...
│   │   └── auth.py                # UserRegistered, PasswordChanged, ...
│   └── protocols/
│       ├── __init__.py
│       ├── evaluatable.py          # Evaluatable protocol
│       └── grading.py             # GradingStrategy ABC
├── services/
│   ├── profile_loader.py           # NEW
│   ├── event_dispatcher.py         # NEW
│   ├── student_work.py             # NEW — unified student work view
│   ├── delivery/                    # NEW directory
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── push.py
│   │   ├── email_delivery.py
│   │   ├── sms_delivery.py
│   │   └── in_app.py
│   └── lms/                         # REPLACES services/lms.py
│       ├── __init__.py
│       ├── course_service.py
│       ├── assignment_service.py
│       ├── quiz_service.py
│       ├── content_service.py
│       └── progress_service.py
├── models/
│   └── iam.py                       # ADD AdminProfile, ContentManagerProfile
└── alembic/versions/
    └── xxxx_g26_oop_profiles.py     # NEW migration
```
