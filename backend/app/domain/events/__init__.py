"""Domain event exports."""

from app.domain.events.auth import (
    NewDeviceLogin,
    PasswordChanged,
    TwoFactorEnabled,
    UserRegistered,
)
from app.domain.events.base import DomainEvent
from app.domain.events.billing import InvoiceGenerated, PaymentFailed, PaymentReceived
from app.domain.events.calendar import (
    EventCreated,
    EventRSVPReceived,
    EventUpdated,
    HolidayAdded,
)
from app.domain.events.documents import (
    DocumentExpiring,
    DocumentUploaded,
    ResourceShared,
)
from app.domain.events.erp import AttendanceThresholdExceeded
from app.domain.events.lms import (
    AssignmentCreated,
    ContentPublished,
    GradePublished,
    QuizCompleted,
    SubmissionReceived,
)

__all__ = [
    "DomainEvent",
    "GradePublished",
    "AssignmentCreated",
    "QuizCompleted",
    "SubmissionReceived",
    "ContentPublished",
    "EventCreated",
    "EventUpdated",
    "HolidayAdded",
    "EventRSVPReceived",
    "InvoiceGenerated",
    "PaymentReceived",
    "PaymentFailed",
    "DocumentUploaded",
    "DocumentExpiring",
    "ResourceShared",
    "AttendanceThresholdExceeded",
    "UserRegistered",
    "PasswordChanged",
    "TwoFactorEnabled",
    "NewDeviceLogin",
]
