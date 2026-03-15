"""Import all domain models so Alembic can detect them.

Migration group order: G1-IAM -> G2-ERP -> G3-LMS -> G4-COM -> G5-Billing -> G6-Audit
"""

# G1 — IAM
from app.models.iam import (
    AccountRecoveryRequest,
    InvitationCode,
    Membership,
    Session,
    User,
)

# G2 — ERP
from app.models.erp import (
    AbsenceJustification,
    AcademicYear,
    AttendanceRecord,
    AttendanceSession,
    Class,
    Enrollment,
    JustificationReview,
    Period,
    TeacherAssignment,
)

# G3 — LMS
from app.models.lms import (
    Activity,
    ActivitySession,
    Assessment,
    AssessmentResult,
    Assignment,
    ContentItem,
    ContentItemAsset,
    ContentProgress,
    Course,
    Grade,
    Submission,
    SubmissionFile,
)

# G4 — COM
from app.models.com import (
    ConsentPreference,
    Notification,
    NotificationDelivery,
    ParentFeedItem,
)

# G5 — Billing
from app.models.billing import (
    Invoice,
    InvoiceItem,
    PaymentAttempt,
    PaymentProof,
    ProviderWebhookEvent,
)

# G6 — Audit
from app.models.audit import AuditLog

# G7 — AI
from app.models.ai import (
    AIPreference,
    WritingAttempt,
)

__all__ = [
    # IAM
    "User",
    "Membership",
    "Session",
    "InvitationCode",
    "AccountRecoveryRequest",
    # ERP
    "AcademicYear",
    "Period",
    "Class",
    "Enrollment",
    "TeacherAssignment",
    "AttendanceSession",
    "AttendanceRecord",
    "AbsenceJustification",
    "JustificationReview",
    # LMS
    "Course",
    "Assignment",
    "Submission",
    "SubmissionFile",
    "Grade",
    "Assessment",
    "AssessmentResult",
    "ContentItem",
    "ContentItemAsset",
    "ContentProgress",
    "Activity",
    "ActivitySession",
    # COM
    "ConsentPreference",
    "Notification",
    "NotificationDelivery",
    "ParentFeedItem",
    # Billing
    "Invoice",
    "InvoiceItem",
    "PaymentAttempt",
    "PaymentProof",
    "ProviderWebhookEvent",
    # Audit
    "AuditLog",
    # AI
    "WritingAttempt",
    "AIPreference",
]
