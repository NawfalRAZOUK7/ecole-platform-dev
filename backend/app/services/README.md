# services/ — Business Logic Layer

Service layer implementing core business rules, workflows, and domain logic. Services orchestrate repositories, external integrations, and event publishing.

## Overview

The Service layer is the business logic heart of the application:
- **Orchestration** — Coordinate multiple repositories
- **Domain Rules** — Enforce business constraints
- **Side Effects** — Trigger notifications, emails, events
- **Transactions** — Multi-step atomic operations
- **Integrations** — Call external services (email, payment gateways)

Pattern: `Router → Service → Repository → Database`

## Directory Structure

```
services/
├── auth.py              # User registration, login, JWT refresh
├── school.py            # School & class operations
├── lms.py/              # Learning management subdomain
│   ├── course_service.py      # Course creation & enrollment
│   ├── assignment_service.py  # Assignment management
│   ├── quiz_service.py        # Quiz execution & scoring
│   ├── grading_service.py     # Grade calculation & publishing
│   ├── progress_service.py    # Student progress tracking
│   ├── content_service.py     # Course content management
│   ├── _helpers.py            # Shared LMS utilities
│   └── _serializers.py        # LMS response formatting
│
├── billing.py           # Invoice generation, payment processing
├── gradebook.py         # Grade entry, reporting, rubrics
├── analytics.py         # Dashboard metrics, KPIs
├── communication.py     # Message routing & coordination
├── email.py            # Email composition & sending
├── email_digest.py     # Digest email compilation
├── sms.py              # SMS delivery via provider
├── calendar.py         # Calendar events & RSVP logic
├── cms.py              # Content management system
├── erp.py              # Enterprise operations (timetable, etc.)
├── gdpr.py             # GDPR compliance (export, delete)
├── reports.py          # Report generation & export
├── kpi.py              # KPI computation & tracking
├── notification_hub.py # Notification aggregation & routing
├── event_dispatcher.py # Domain event publishing & handling
├── file_storage.py     # File upload/download, virus scanning
├── quiz_grading.py     # Quiz answer evaluation
├── realtime.py         # WebSocket real-time features
├── timetable_generator.py  # Schedule generation algorithm
├── data_export.py      # Data export (CSV, Excel, PDF)
├── profile.py          # User profile & preferences
├── profile_loader.py   # Cached profile data (Redis)
├── question_bank.py    # Quiz question library management
├── rubric.py           # Rubric & evaluation criteria
├── resource_library.py # Reusable resource catalog
├── student_documents.py # Student file management
├── student_work.py     # Unified student work view
├── progress.py         # Progress tracking & visualization
├── rsvp.py             # RSVP handling for events
├── feature.py          # Feature flag management
├── admin.py            # Admin operations
├── audit.py            # Audit logging
├── attendance_analytics.py  # Attendance reports
├── dashboard_analytics.py   # Dashboard KPIs
├── overdue_reminders.py    # Overdue item reminders
├── payment_plan.py     # Payment plan management
├── payment_retry.py    # Failed payment retry logic
├── push_config.py      # Push notification configuration
├── reminders.py        # Reminder scheduling & sending
├── report_scheduler.py # Scheduled report generation
│
├── ai/                 # AI provider abstraction (Strategy pattern)
│   ├── provider_base.py       # AbstractProvider
│   ├── claude_provider.py     # Claude API integration
│   ├── mock_provider.py       # Mock provider for testing
│   ├── provider_factory.py    # Provider selection logic
│   └── ai_service.py          # AI business logic
│
├── delivery/           # Notification delivery channels (Strategy pattern)
│   ├── base.py        # AbstractDeliveryChannel
│   ├── email_delivery.py     # Email delivery
│   ├── sms_delivery.py       # SMS delivery
│   ├── push.py               # Push notification delivery
│   └── in_app.py             # In-app notification delivery
│
└── lms/               # Learning management subsystem (organized above)
```

## Core Services

### auth.py — Authentication

User registration, login, and session management:

```python
class AuthService:
    """Authentication business logic."""

    async def register_user(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        school_id: int,
        role_code: str
    ) -> User:
        """Register new user."""
        # Validate password strength
        # Hash password
        # Create user
        # Publish UserRegisteredEvent
        # Send welcome email
        # ...

    async def login(self, email: str, password: str, school_id: int) -> LoginResponse:
        """Authenticate user, return JWT."""
        # Verify email exists in school
        # Check password hash
        # Create session
        # Generate JWT token
        # Publish UserLoggedInEvent
        # ...

    async def refresh_token(self, user_id: int) -> str:
        """Issue new JWT from refresh token."""
        # Verify session active
        # Generate new JWT
        # ...

    async def logout(self, user_id: int) -> None:
        """Invalidate user sessions."""
        # Revoke all sessions
        # Publish UserLoggedOutEvent
        # ...

    async def enable_2fa(self, user_id: int) -> str:
        """Generate 2FA secret & QR code."""
        # Generate TOTP secret
        # Create QR code
        # Return for display
        # ...

    async def verify_2fa_code(self, user_id: int, code: str) -> bool:
        """Verify TOTP code."""
        # Check code against time window
        # ...

    async def request_password_reset(self, email: str, school_id: int) -> None:
        """Send password reset OTP."""
        # Generate OTP
        # Send via email
        # Publish PasswordResetRequestedEvent
        # ...

    async def reset_password(
        self,
        email: str,
        otp: str,
        new_password: str,
        school_id: int
    ) -> User:
        """Reset password with OTP."""
        # Verify OTP
        # Validate password strength
        # Update password
        # Publish PasswordResetConfirmedEvent
        # ...
```

### lms/ — Learning Management Subsystem

#### course_service.py

```python
class CourseService:
    """Course lifecycle management."""

    async def create_course(
        self,
        req: CourseCreateRequest,
        teacher_id: int,
        school_id: int
    ) -> Course:
        """Create course."""
        # Validate teacher exists
        # Check course code uniqueness
        # Create course record
        # Publish CourseCreatedEvent
        # ...

    async def enroll_student(
        self,
        student_id: int,
        course_id: int
    ) -> CourseEnrollment:
        """Enroll student in course."""
        # Check student exists
        # Check course active
        # Create enrollment
        # Publish CourseEnrolledEvent
        # Send welcome email to student
        # ...

    async def update_course(
        self,
        course_id: int,
        req: CourseUpdateRequest,
        teacher_id: int
    ) -> Course:
        """Update course details."""
        # Verify teacher owns course
        # Update fields
        # Publish CourseUpdatedEvent
        # ...

    async def archive_course(self, course_id: int) -> Course:
        """Archive completed course."""
        # Mark as archived
        # Disable enrollments
        # Publish CourseArchivedEvent
        # ...
```

#### assignment_service.py

```python
class AssignmentService:
    """Assignment management & grading."""

    async def create_assignment(
        self,
        req: AssignmentCreateRequest,
        course_id: int,
        teacher_id: int
    ) -> Assignment:
        """Create assignment."""
        # Validate course exists
        # Validate rubric exists
        # Set default weighting
        # Create assignment
        # Publish AssignmentCreatedEvent
        # Notify enrolled students
        # ...

    async def submit_assignment(
        self,
        assignment_id: int,
        student_id: int,
        submission_data: dict
    ) -> Submission:
        """Student submits assignment."""
        # Check student enrolled in course
        # Check deadline not passed
        # Create submission record
        # Scan files for viruses
        # Publish SubmissionCreatedEvent
        # Notify teacher
        # ...

    async def grade_submission(
        self,
        submission_id: int,
        grade_req: GradeRequest,
        teacher_id: int
    ) -> Grade:
        """Teacher grades submission."""
        # Verify teacher teaches course
        # Apply rubric scoring
        # Calculate weighted score
        # Create grade record
        # Publish SubmissionGradedEvent
        # Send to notification queue
        # ...

    async def bulk_grade_submissions(
        self,
        submission_ids: list[int],
        grades: list[GradeRequest],
        teacher_id: int
    ) -> list[Grade]:
        """Bulk grade multiple submissions."""
        # Iterate & grade each
        # Collect grades
        # Publish BatchGradeCompletedEvent
        # ...
```

#### grading_service.py

```python
class GradingService:
    """Grade calculation & reporting."""

    async def calculate_course_grade(
        self,
        student_id: int,
        course_id: int
    ) -> Grade:
        """Calculate weighted course grade."""
        # Get assignments with weights
        # Fetch student grades
        # Apply weights
        # Calculate final grade
        # Return Grade value object
        # ...

    async def publish_grades(
        self,
        assignment_id: int
    ) -> None:
        """Make grades visible to students."""
        # Get all grades for assignment
        # Set visible_to_student=true
        # Publish GradePublishedEvent
        # Send notifications to students
        # ...

    async def get_transcript(
        self,
        student_id: int,
        academic_year_id: int
    ) -> StudentTranscript:
        """Generate academic transcript."""
        # Get all courses
        # Get all grades
        # Calculate GPA
        # Format transcript
        # Return formatted response
        # ...
```

### billing.py — Billing & Invoicing

```python
class BillingService:
    """Invoice generation & payment processing."""

    async def generate_invoice(
        self,
        req: InvoiceRequest,
        school_id: int,
        created_by: int
    ) -> Invoice:
        """Create invoice."""
        # Validate fees
        # Create invoice record
        # Add line items
        # Calculate total
        # Publish InvoiceGeneratedEvent
        # ...

    async def issue_invoice(
        self,
        invoice_id: int
    ) -> Invoice:
        """Send invoice to parent."""
        # Get invoice
        # Send email with PDF
        # Mark as issued
        # Publish InvoiceIssuedEvent
        # ...

    async def record_payment(
        self,
        invoice_id: int,
        amount: Decimal,
        method: str,
        reference: str
    ) -> Payment:
        """Record payment received."""
        # Verify amount
        # Update invoice balance
        # Create payment record
        # Check if paid-in-full
        # Publish InvoicePaidEvent
        # Send receipt email
        # ...

    async def send_overdue_reminders(
        self,
        school_id: int
    ) -> int:
        """Send overdue invoice reminders."""
        # Get overdue invoices
        # For each: send reminder email
        # Count sent
        # Publish OverdueReminderEvent
        # ...
```

### gradebook.py — Grade Management

```python
class GradebookService:
    """Grade entry, viewing, and reporting."""

    async def enter_grades(
        self,
        req: BulkGradeRequest,
        teacher_id: int
    ) -> list[Grade]:
        """Enter multiple grades."""
        # Validate teacher teaches class
        # For each grade: validate score
        # Create grade records
        # Publish GradesEnteredEvent
        # ...

    async def get_student_gradebook(
        self,
        student_id: int,
        course_id: int
    ) -> StudentGradebook:
        """Get grades for student in course."""
        # Get all assignments
        # Get student grades
        # Calculate weighted average
        # Format for display
        # ...

    async def get_class_gradebook(
        self,
        class_id: int,
        academic_year_id: int
    ) -> ClassGradebook:
        """Get all grades in class (for teacher)."""
        # Get all students
        # Get all assignments
        # Get all grades
        # Format matrix
        # ...
```

### notification_hub.py — Notification Routing

```python
class NotificationHubService:
    """Route notifications to delivery channels."""

    async def send_notification(
        self,
        user_id: int,
        notification_type: str,
        title: str,
        message: str,
        data: dict
    ) -> Notification:
        """Send notification via all active channels."""
        # Create notification record
        # Get user preferences
        # For each enabled channel:
        #   - Route to EmailDelivery / SMSDelivery / etc.
        # Update delivery status
        # Publish NotificationSentEvent
        # ...

    async def get_user_notifications(
        self,
        user_id: int,
        limit: int = 50
    ) -> list[Notification]:
        """Get user's notification inbox."""
        # Fetch from repo
        # Filter unread/read
        # Order by date
        # Return paginated
        # ...

    async def mark_as_read(
        self,
        notification_id: int,
        user_id: int
    ) -> Notification:
        """Mark notification read."""
        # Verify ownership
        # Update read status
        # Publish NotificationReadEvent
        # ...
```

### email.py — Email Service

```python
class EmailService:
    """Email composition & delivery."""

    async def send_email(
        self,
        to: str,
        subject: str,
        template_name: str,
        context: dict
    ) -> bool:
        """Send templated email."""
        # Load Jinja2 template
        # Render with context
        # Connect to SMTP
        # Send email
        # Log delivery
        # Return success
        # ...

    async def send_bulk_email(
        self,
        recipients: list[str],
        subject: str,
        template_name: str,
        context: dict
    ) -> int:
        """Send email to multiple recipients."""
        # For each recipient:
        #   - Render template with personalization
        #   - Queue delivery
        # Return count queued
        # ...

    async def send_welcome_email(self, user: User) -> bool:
        """Send welcome email to new user."""
        # ...

    async def send_grade_notification(
        self,
        student_id: int,
        assignment: Assignment,
        grade: Grade
    ) -> bool:
        """Notify student of grade."""
        # Get student user
        # Render grade template
        # Send email
        # ...
```

### ai/ai_service.py — AI Provider Abstraction

```python
class AIService:
    """AI assistant coordination."""

    async def ask_question(
        self,
        user_id: int,
        question: str,
        context: Optional[dict] = None
    ) -> AIResponse:
        """Ask AI a question."""
        # Get configured provider (Claude, GPT-4, mock)
        # Call provider.ask(question, context)
        # Create AIInteraction record
        # Track tokens & cost
        # Publish AIQuestionAskedEvent
        # ...

    async def generate_assignment_help(
        self,
        student_id: int,
        assignment: Assignment
    ) -> str:
        """Generate assignment help from AI."""
        # Get provider
        # Call with assignment context
        # Return generated content
        # ...

    async def generate_grading_suggestions(
        self,
        submission: Submission,
        rubric: Rubric
    ) -> dict:
        """AI suggests grades for submission."""
        # Get provider
        # Send submission + rubric
        # Return score suggestions
        # ...
```

### delivery/ — Notification Delivery Channels

```python
class DeliveryChannel(ABC):
    """Base delivery channel."""

    @abstractmethod
    async def send(self, notification: Notification) -> bool:
        """Send notification via channel."""

class EmailDeliveryChannel(DeliveryChannel):
    """Send via email."""

    async def send(self, notification: Notification) -> bool:
        # Format email
        # Call EmailService
        # Return success

class SMSDeliveryChannel(DeliveryChannel):
    """Send via SMS."""

    async def send(self, notification: Notification) -> bool:
        # Format SMS text
        # Call SMS provider
        # Return success

class PushDeliveryChannel(DeliveryChannel):
    """Send via push notification."""

    async def send(self, notification: Notification) -> bool:
        # Format push payload
        # Call push service
        # Return success

class InAppDeliveryChannel(DeliveryChannel):
    """Store as in-app notification."""

    async def send(self, notification: Notification) -> bool:
        # Store in DB
        # Notify via WebSocket
        # Return success
```

## Patterns

### Unit of Work

Multi-step operations with atomicity:

```python
async def transfer_student(
    self,
    student_id: int,
    from_class: int,
    to_class: int
) -> None:
    """Atomic class transfer."""
    async with self.uow.transaction():
        # Remove from old class
        await self.uow.enrollments.remove(student_id, from_class)
        # Add to new class
        await self.uow.enrollments.create(student_id, to_class)
        # Publish event
        await self.event_dispatcher.publish(StudentTransferredEvent(...))
        # Automatic commit on exit
```

### Event Publishing

Services publish domain events:

```python
# In service method
event = GradePublishedEvent(
    aggregate_id=f"grade:{grade.id}",
    user_id=teacher_id,
    school_id=school_id,
    metadata={"grade_value": grade.value, "student_id": grade.student_id}
)
await self.event_dispatcher.publish(event)
# Handlers automatically triggered
```

## Testing Services

Services are tested with mocked repositories:

```python
@pytest.mark.asyncio
async def test_register_user():
    repo = Mock(UserRepository)
    service = AuthService(repo, ...)
    user = await service.register_user(...)
    repo.create.assert_called_once()
```

## Next Steps

- See `repositories/` for data access layer
- See `domain/events/` for domain events
- See `api/v1/` for endpoint handlers
- See `core/` for infrastructure services
