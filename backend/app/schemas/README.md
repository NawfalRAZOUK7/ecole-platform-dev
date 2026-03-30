# schemas/ — Pydantic Request/Response Models

Pydantic v2 validation schemas for HTTP request/response serialization. Defines API contracts and ensures data integrity at boundaries.

## Overview

Schemas provide:
- **Input validation** — Validate HTTP request bodies
- **Type safety** — Type hints for requests and responses
- **Documentation** — OpenAPI schema generation
- **Serialization** — Convert ORM models to JSON
- **Error handling** — Automatic validation error responses

All schemas inherit from `BaseModel` and use Pydantic v2 features.

## Directory Structure

```
schemas/
├── auth.py              # Login, token, user profile
├── school.py            # School, class, enrollment
├── lms.py               # Course, assignment, submission
├── billing.py           # Invoice, payment, subscription
├── billing_enhancements.py  # Advanced billing schemas
├── calendar.py          # Event, RSVP
├── com.py               # Message, notification
├── documents.py         # Document, file upload
├── erp.py               # Timetable, resource
├── feature.py           # Feature flag
├── gradebook.py         # Grade, rubric
├── lms.py               # Course, assignment, quiz
├── notifications.py     # Notification preferences
├── profile.py           # User profile
├── question_bank.py     # Quiz question
├── quiz.py              # Quiz, attempt, result
├── reports.py           # Report, report schedule
├── rubric.py            # Rubric, evaluation criteria
└── (more domain schemas)
```

## Schema Patterns

### Request Schema (Input Validation)

Validates and documents API request bodies:

```python
from pydantic import BaseModel, Field, EmailStr, constr

class UserRegisterRequest(BaseModel):
    """User registration request."""

    email: EmailStr = Field(..., description="Email address")
    password: constr(min_length=8) = Field(
        ...,
        description="Password (min 8 chars)"
    )
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    school_id: int = Field(..., gt=0)

    class Config:
        # Pydantic v2 config
        json_schema_extra = {
            "example": {
                "email": "student@school.ma",
                "password": "SecurePass123!",
                "first_name": "Mohammed",
                "last_name": "Benaziz",
                "school_id": 1
            }
        }
```

FastAPI automatically validates:
```python
@router.post("/register")
async def register(req: UserRegisterRequest):
    # req.email is valid
    # req.password min_length=8
    # req.school_id is positive integer
    # Invalid requests return 422 with error details
```

### Response Schema (Output Serialization)

Serializes ORM models to JSON responses:

```python
from datetime import datetime

class UserResponse(BaseModel):
    """User response model."""

    id: int
    email: str
    first_name: str
    last_name: str
    school_id: int
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        # Allow ORM model serialization
        from_attributes = True
```

Usage in endpoint:
```python
@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, service: UserService = Depends()):
    user = await service.get_user(user_id)
    # Automatic serialization: User ORM → UserResponse JSON
    return user
```

### List Response Schema

Paginated response wrapper:

```python
from typing import TypeVar, Generic

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response."""

    items: list[T]
    total: int
    limit: int
    offset: int

    @property
    def page(self) -> int:
        return self.offset // self.limit + 1

    @property
    def total_pages(self) -> int:
        return (self.total + self.limit - 1) // self.limit
```

Example:
```python
@router.get("/courses", response_model=PaginatedResponse[CourseResponse])
async def list_courses(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: CourseService = Depends()
):
    courses, total = await service.list_courses(limit, offset)
    return PaginatedResponse(items=courses, total=total, limit=limit, offset=offset)
```

## Domain-Specific Schemas

### auth.py

```python
class LoginRequest(BaseModel):
    """User login."""
    email: EmailStr
    password: str
    school_id: int

class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: Literal["bearer"]
    expires_in: int  # seconds

class LoginResponse(BaseModel):
    """Login response with token & user."""
    token: TokenResponse
    user: UserResponse

class ProfileResponse(BaseModel):
    """User profile with roles."""
    id: int
    email: str
    first_name: str
    last_name: str
    school_id: int
    roles: list[RoleResponse]
    created_at: datetime

class PasswordResetRequest(BaseModel):
    """Password reset request."""
    email: EmailStr
    new_password: constr(min_length=8)
    otp: constr(regex=r'^\d{6}$')

class OTPResponse(BaseModel):
    """OTP delivery response."""
    message: str
    email_masked: str  # john***@example.com
```

### lms.py — Learning Management

```python
class CourseCreateRequest(BaseModel):
    """Create course."""
    code: constr(regex=r'^[A-Z0-9]{3,10}$')
    name: str = Field(..., min_length=1, max_length=255)
    description: str
    start_date: datetime
    end_date: datetime
    class_ids: list[int] = []

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "code": "MATH101",
            "name": "Mathematics - Grade 9",
            "description": "Core mathematics curriculum",
            "start_date": "2024-09-01T00:00:00Z",
            "end_date": "2025-06-30T00:00:00Z",
            "class_ids": [1, 2, 3]
        }
    })

class CourseResponse(BaseModel):
    """Course details."""
    id: int
    code: str
    name: str
    description: str
    teacher_id: int
    teacher_name: str  # Computed from relationship
    start_date: datetime
    end_date: datetime
    status: Literal["draft", "published", "archived"]
    student_count: int
    assignment_count: int
    created_at: datetime

    class Config:
        from_attributes = True

class AssignmentCreateRequest(BaseModel):
    """Create assignment."""
    title: str
    description: str
    due_date: datetime
    max_score: Decimal = Field(..., ge=0, decimal_places=2)
    submission_type: Literal["file", "text", "url"]
    rubric_id: Optional[int] = None
    weighting: float = Field(default=1.0, ge=0, le=1)

class SubmissionResponse(BaseModel):
    """Student submission."""
    id: int
    student_id: int
    student_name: str
    assignment_id: int
    submission_date: datetime
    status: Literal["draft", "submitted", "graded"]
    file_urls: list[str] = []
    text_content: Optional[str] = None
    grade: Optional[Decimal] = None
    graded_at: Optional[datetime] = None
    feedback: Optional[str] = None

    class Config:
        from_attributes = True
```

### billing.py — Invoicing

```python
class InvoiceCreateRequest(BaseModel):
    """Create invoice."""
    student_id: Optional[int] = None  # Null = school invoice
    items: list[LineItemRequest]
    due_date: datetime
    notes: Optional[str] = None

class LineItemRequest(BaseModel):
    """Invoice line item."""
    description: str
    quantity: Decimal = Field(default=1, ge=0)
    unit_price: Decimal = Field(..., ge=0, decimal_places=2)

class InvoiceResponse(BaseModel):
    """Invoice details."""
    id: int
    number: str
    student_id: Optional[int]
    student_name: Optional[str]
    issue_date: datetime
    due_date: datetime
    items: list[LineItemResponse]
    total_amount: Decimal
    paid_amount: Decimal
    status: Literal["draft", "issued", "paid", "overdue", "cancelled"]
    created_at: datetime

class PaymentRequest(BaseModel):
    """Record payment."""
    invoice_id: int
    amount: Decimal = Field(..., ge=0, decimal_places=2)
    method: Literal["credit_card", "bank_transfer", "cash", "cheque"]
    reference: str = Field(..., min_length=1, max_length=50)

class PaymentResponse(BaseModel):
    """Payment confirmation."""
    id: int
    invoice_id: int
    amount: Decimal
    method: str
    reference: str
    paid_at: datetime
    status: Literal["completed", "pending", "failed", "refunded"]
```

### gradebook.py — Grading

```python
class GradeEntryRequest(BaseModel):
    """Enter grade for student."""
    student_id: int
    assignment_id: int
    score: Decimal = Field(..., ge=0, le=20)  # Moroccan 0-20 scale
    feedback: Optional[str] = None
    rubric_scores: Optional[dict[int, Decimal]] = None  # rubric_criterion_id → score

class GradeResponse(BaseModel):
    """Grade details."""
    id: int
    student_id: int
    student_name: str
    assignment_id: int
    assignment_name: str
    score: Decimal
    percentage: float  # Calculated 0-100
    grade_letter: Literal["A", "B", "C", "D", "F"]
    is_passing: bool  # >= 10 on Moroccan scale
    graded_by: int
    graded_at: datetime
    feedback: Optional[str]
    rubric_scores: Optional[dict[str, Decimal]]

    class Config:
        from_attributes = True

class StudentGradebookResponse(BaseModel):
    """Student's complete gradebook in course."""
    student_id: int
    course_id: int
    course_name: str
    assignments: list[GradeResponse]
    weighted_average: Decimal
    course_grade_letter: str
    course_percentage: float
```

### calendar.py — Events

```python
class EventCreateRequest(BaseModel):
    """Create calendar event."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    start_datetime: datetime
    end_datetime: datetime
    location: Optional[str] = None
    event_type: Literal["meeting", "holiday", "exam", "parent_day", "assembly"]
    attendee_ids: list[int] = []

    @field_validator('end_datetime')
    @classmethod
    def validate_end_time(cls, v: datetime, info: ValidationInfo) -> datetime:
        if info.data.get('start_datetime') and v <= info.data['start_datetime']:
            raise ValueError('end_datetime must be after start_datetime')
        return v

class EventResponse(BaseModel):
    """Event details."""
    id: int
    title: str
    description: Optional[str]
    start_datetime: datetime
    end_datetime: datetime
    location: Optional[str]
    event_type: str
    attendees: list[AttendeeResponse]
    created_at: datetime

class RSVPRequest(BaseModel):
    """RSVP to event."""
    event_id: int
    response: Literal["accepted", "declined", "tentative"]
    notes: Optional[str] = None

class RSVPResponse(BaseModel):
    """RSVP details."""
    id: int
    event_id: int
    user_id: int
    response: str
    responded_at: datetime
```

### documents.py — File Management

```python
class DocumentUploadRequest(BaseModel):
    """Upload document request."""
    document_type: Literal["course_material", "syllabus", "policy", "certificate"]
    is_public: bool = False
    title: Optional[str] = None

class DocumentResponse(BaseModel):
    """Document details."""
    id: int
    filename: str
    document_type: str
    mime_type: str
    file_size: int
    uploader_id: int
    uploader_name: str
    is_public: bool
    created_at: datetime
    download_url: str

class SubmissionFileRequest(BaseModel):
    """Upload assignment submission file."""
    assignment_id: int
    notes: Optional[str] = None

class SubmissionFileResponse(BaseModel):
    """Submitted file."""
    id: int
    filename: str
    file_size: int
    uploaded_at: datetime
    file_url: str
```

## Validators

Custom validation logic:

```python
from pydantic import field_validator, model_validator

class CourseCreateRequest(BaseModel):
    name: str
    max_students: int

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError('Course name must be at least 3 characters')
        return v.strip()

    @model_validator(mode='after')
    def validate_model(self) -> 'CourseCreateRequest':
        if self.max_students < 1:
            raise ValueError('max_students must be positive')
        return self
```

## Computed Fields

Return derived values in responses:

```python
from pydantic import computed_field

class GradeResponse(BaseModel):
    score: Decimal
    max_score: Decimal = 20

    @computed_field
    @property
    def percentage(self) -> float:
        """Calculate percentage."""
        return float(self.score / self.max_score * 100)

    @computed_field
    @property
    def letter_grade(self) -> str:
        """Convert to letter grade."""
        if self.percentage >= 90:
            return "A"
        if self.percentage >= 80:
            return "B"
        # ...
```

## Error Responses

Validation errors automatically formatted:

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "email"],
      "msg": "invalid email format",
      "input": "invalid-email"
    },
    {
      "type": "value_error",
      "loc": ["body", "password"],
      "msg": "ensure this value has at least 8 characters",
      "input": "short"
    }
  ]
}
```

## OpenAPI Documentation

Schemas automatically generate OpenAPI definitions:

```bash
# View OpenAPI spec
curl http://localhost:8000/openapi.json

# Swagger UI
http://localhost:8000/docs

# ReDoc
http://localhost:8000/redoc
```

## Testing Schemas

```python
from schemas.auth import UserRegisterRequest

def test_valid_registration():
    req = UserRegisterRequest(
        email="student@school.ma",
        password="SecurePass123!",
        first_name="Ahmed",
        last_name="Hassan",
        school_id=1
    )
    assert req.email == "student@school.ma"

def test_invalid_email():
    with pytest.raises(ValidationError) as exc_info:
        UserRegisterRequest(
            email="invalid-email",
            password="SecurePass123!",
            first_name="Ahmed",
            last_name="Hassan",
            school_id=1
        )
    assert "email" in str(exc_info.value)
```

## Serialization Config

Common Pydantic config patterns:

```python
class Config:
    # Deserialize from ORM models
    from_attributes = True

    # Forbid extra fields
    extra = "forbid"

    # Custom JSON encoder
    json_encoders = {
        datetime: lambda v: v.isoformat(),
        Decimal: lambda v: float(v)
    }

    # JSON schema examples
    json_schema_extra = {
        "example": {
            "name": "Mathematics 101",
            "description": "Core curriculum"
        }
    }
```

## Next Steps

- See `api/v1/` for endpoint usage
- See `models/` for ORM model definitions
- See Pydantic docs: https://docs.pydantic.dev/
