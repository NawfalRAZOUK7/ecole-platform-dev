# domain/ — Domain-Driven Design Layer

Domain-driven design (DDD) artifacts modeling core business concepts. Captures ubiquitous language, domain rules, and structural contracts independent of application infrastructure.

## Directory Structure

```
domain/
├── events/          # Domain events (event sourcing patterns)
│   ├── base.py      # BaseEvent abstract class
│   ├── auth.py      # Authentication domain events
│   ├── billing.py   # Billing domain events
│   ├── calendar.py  # Calendar domain events
│   ├── documents.py # Document domain events
│   ├── erp.py       # ERP domain events
│   └── lms.py       # Learning management domain events
│
├── protocols/       # Protocol interfaces (structural typing)
│   ├── evaluatable.py    # Gradeable work protocol
│   └── grading.py        # Grading engine protocol
│
└── value_objects/   # Immutable value objects
    ├── grade.py         # Moroccan grade scale (0-20)
    ├── money.py         # MAD currency with cents
    ├── role_set.py      # Role combinations
    └── typed_id.py      # Type-safe entity IDs
```

## Events Layer (events/)

Domain events represent important business occurrences that other parts of the system need to react to. Used for:
- Triggering side effects (email notifications, audit logs)
- Event sourcing & audit trails
- Async workflows
- Inter-domain communication

### base.py — BaseEvent

Abstract event class that all domain events inherit from:

```python
class BaseEvent(ABC):
    """Base for all domain events."""

    id: UUID                    # Unique event ID
    aggregate_id: str          # Entity ID (user, course, invoice)
    aggregate_type: str        # Entity type (User, Course, Invoice)
    event_type: str            # Event class name
    timestamp: datetime        # When event occurred
    user_id: int              # Who triggered event (optional)
    school_id: int            # Which school (for multi-tenancy)
    metadata: dict[str, Any]  # Additional context

    @abstractmethod
    async def apply(self, repository) -> None:
        """Apply side effects of this event."""
```

### auth.py — Authentication Events

Events triggered during authentication workflows:

- `UserRegisteredEvent` — New user account created
- `UserLoggedInEvent` — User authenticated
- `UserLoggedOutEvent` — User session ended
- `PasswordResetRequestedEvent` — Password reset initiated
- `PasswordResetConfirmedEvent` — Password changed
- `TwoFactorEnabledEvent` — 2FA activated
- `TwoFactorDisabledEvent` — 2FA deactivated
- `SessionTerminatedEvent` — Session invalidated

Each event carries context:
```python
UserRegisteredEvent(
    aggregate_id="user:123",
    aggregate_type="User",
    user_id=123,
    school_id=45,
    metadata={
        "email": "student@school.edu",
        "role": "STD",
        "invited_by": 67  # Inviter user ID
    }
)
```

### billing.py — Billing Events

Financial transaction events:

- `InvoiceGeneratedEvent` — Invoice created
- `InvoiceIssuedEvent` — Invoice sent to parent
- `InvoicePaidEvent` — Invoice payment received
- `InvoiceOverdueEvent` — Payment deadline passed
- `PaymentRefundedEvent` — Refund issued
- `SubscriptionActivatedEvent` — School subscription started
- `SubscriptionCancelledEvent` — Subscription ended
- `PaymentPlanCreatedEvent` — Payment arrangement setup

Example:
```python
InvoiceGeneratedEvent(
    aggregate_id="invoice:INV-2024-001",
    aggregate_type="Invoice",
    user_id=1,  # Created by admin
    school_id=45,
    metadata={
        "amount_mad": 2500,
        "student_id": 678,
        "due_date": "2024-04-30",
        "items": [
            {"description": "Tuition", "amount": 2000},
            {"description": "Lab Fee", "amount": 500}
        ]
    }
)
```

### lms.py — Learning Management Events

Course & assignment events:

- `CourseCreatedEvent` — Course published
- `CourseEnrolledEvent` — Student enrolled in course
- `AssignmentCreatedEvent` — Assignment posted
- `AssignmentSubmittedEvent` — Student submission received
- `SubmissionGradedEvent` — Teacher provided grade
- `GradePublishedEvent` — Grade visible to student
- `QuizCompletedEvent` — Student finished quiz
- `CourseCompletedEvent` — Student finished course

### calendar.py — Calendar Events

Calendar scheduling events:

- `EventCreatedEvent` — Meeting/event scheduled
- `EventUpdatedEvent` — Event details changed
- `EventCancelledEvent` — Event cancelled
- `RSVPAcceptedEvent` — Attendee confirmed
- `RSVPDeclinedEvent` — Attendee declined
- `ReminderSentEvent` — Reminder notification sent

### documents.py — Document Events

Document management events:

- `DocumentUploadedEvent` — File added
- `DocumentAccessedEvent` — Document viewed/downloaded
- `DocumentDeletedEvent` — Document removed
- `DocumentScanCompletedEvent` — Virus scan finished
- `StudentFileSubmittedEvent` — Student uploaded file

### erp.py — ERP (Enterprise) Events

School operations events:

- `AttendanceMarkedEvent` — Attendance recorded
- `TimetableGeneratedEvent` — Schedule created
- `ClassEnrollmentChangedEvent` — Class roster updated
- `TeacherAssignedEvent` — Teacher assigned to class

## Protocols Layer (protocols/)

Structural typing contracts defining how domain objects should behave. These are like interfaces without explicit inheritance.

### evaluatable.py — Evaluatable Protocol

Defines what objects can be graded:

```python
class Evaluatable(Protocol):
    """Something that can be evaluated/graded."""

    def get_submission_data(self) -> dict:
        """Extract evaluatable content."""

    def get_evaluation_criteria(self) -> list[EvaluationCriterion]:
        """Expected grading criteria."""

    def is_due(self) -> bool:
        """Whether evaluation deadline passed."""
```

Implementations:
- `Assignment` — Student work submissions
- `Quiz` — Quiz attempts
- `FinalExam` — Exam papers
- `ProjectDeliverable` — Group project submissions

### grading.py — Grading Protocol

Defines grading engine contracts:

```python
class GradingStrategy(Protocol):
    """How something gets graded."""

    async def calculate_grade(
        self,
        submission: Evaluatable,
        rubric: Rubric,
    ) -> Grade:
        """Compute grade from submission + rubric."""

    async def apply_weights(
        self,
        grades: list[Grade],
        weights: dict[str, float],
    ) -> Grade:
        """Combine weighted grades."""
```

Implementations:
- `RubricGradingStrategy` — Score against rubric
- `AutoGradingStrategy` — Automatic quiz scoring
- `WeightedAverageStrategy` — Weighted grade calculation

## Value Objects Layer (value_objects/)

Immutable domain values with built-in business logic. Unlike entities, value objects have no identity—two instances with same values are equal.

### grade.py — Grade (Moroccan 0-20 Scale)

Immutable grade value object following Moroccan education standards:

```python
class Grade(ValueObject):
    """Grade on 0-20 scale (Moroccan standard)."""

    value: Decimal  # 0.00 to 20.00
    scale: Literal["20"] = "20"

    def __post_init__(self):
        if not (0 <= self.value <= 20):
            raise ValueError("Grade must be 0-20")

    def to_percentage(self) -> float:
        """Convert to 0-100 percentage."""
        return float(self.value) * 5

    def to_letter(self) -> str:
        """Convert to letter grade (A-F)."""
        if self.value >= 18: return "A"
        if self.value >= 16: return "B"
        if self.value >= 14: return "C"
        if self.value >= 12: return "D"
        return "F"

    def is_passing(self) -> bool:
        """Moroccan passing threshold (10+)."""
        return self.value >= 10
```

Usage:
```python
grade = Grade(18.5)
print(grade.is_passing())    # True
print(grade.to_letter())     # "A"
print(grade.to_percentage()) # 92.5
```

### money.py — Money (MAD Currency)

Immutable currency value object:

```python
class Money(ValueObject):
    """Amount in Moroccan Dirham (MAD)."""

    amount: Decimal     # Amount in whole units
    currency: Literal["MAD"] = "MAD"

    @classmethod
    def from_cents(cls, cents: int) -> "Money":
        """Create from cents (100 cents = 1 MAD)."""
        return cls(amount=Decimal(cents) / 100)

    def to_cents(self) -> int:
        """Convert to cents."""
        return int(self.amount * 100)

    def __add__(self, other: "Money") -> "Money":
        """Add two money amounts."""
        if other.currency != self.currency:
            raise ValueError("Currency mismatch")
        return Money(amount=self.amount + other.amount)
```

### role_set.py — RoleSet

Immutable set of user roles:

```python
class RoleSet(ValueObject):
    """Set of roles a user holds."""

    roles: frozenset[str]  # ADM, DIR, TCH, PAR, STD, etc.

    def has_permission(self, permission: str) -> bool:
        """Check if role set grants permission."""
        # Lookup permission in permissions catalog

    def has_any(self, role_codes: list[str]) -> bool:
        """Has at least one role in list."""

    def has_all(self, role_codes: list[str]) -> bool:
        """Has all roles in list."""
```

### typed_id.py — TypedId

Type-safe entity ID to prevent mixing IDs:

```python
class TypedId(Generic[T]):
    """Type-safe ID preventing ID confusion."""

    value: int
    entity_type: str

    def __eq__(self, other):
        if not isinstance(other, TypedId):
            return False
        return self.value == other.value

    def __hash__(self):
        return hash(self.value)
```

Usage:
```python
user_id: TypedId[User] = TypedId(123, entity_type="User")
course_id: TypedId[Course] = TypedId(456, entity_type="Course")

# Type checkers prevent mixing IDs
# user_id = course_id  # Type error!
```

## Event Handling

Events are typically published from services and handled by:

1. **Audit logging** — Record in AuditLog table
2. **Notifications** — Send email/SMS/push
3. **Analytics** — Update KPI metrics
4. **Webhooks** — Call external systems
5. **Event store** — Immutable event log (optional)

```python
# In a service:
event = InvoiceGeneratedEvent(...)
await event_dispatcher.publish(event)

# Handlers automatically triggered:
# - AuditLogHandler: records event in audit log
# - EmailNotificationHandler: sends email to parent
# - InvoiceMetricsHandler: updates invoice count KPI
```

## Integration with Application

Domain events connect layers:

```
Service (creates event)
    ↓
EventDispatcher (services/event_dispatcher.py)
    ↓
EventHandlers (listeners across app)
    ├→ Audit (repositories/audit.py)
    ├→ Email (services/email.py)
    ├→ Notifications (services/notification_hub.py)
    └→ WebSocket (core/ws_manager.py)
```

## Design Principles

- **Immutability** — Value objects never change
- **Ubiquitous Language** — Names match business terminology
- **Side-effect Free** — Domain logic has no I/O
- **Testability** — Easy to unit test without mocks
- **Aggregates** — Events grouped by entity boundaries

## Next Steps

- See `services/event_dispatcher.py` for event publishing
- See `repositories/audit.py` for audit log storage
- See `services/notifications.py` for event handlers
