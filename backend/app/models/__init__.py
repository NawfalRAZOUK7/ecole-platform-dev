"""Import all domain models so Alembic can detect them.

Migration group order: G1-IAM -> G2-ERP -> G3-LMS -> G4-COM -> G5-Billing -> G6-Audit
"""

# G0 — Schools
from app.models.school import School, SchoolStatus

# G1 — IAM
from app.models.iam import (
    AccountRecoveryRequest,
    AdminProfile,
    ContentManagerProfile,
    InvitationCode,
    LoginHistory,
    Membership,
    ParentChildLink,
    ParentProfile,
    Session,
    StudentProfile,
    TeacherProfile,
    User,
)

# G2 — ERP
from app.models.erp import (
    AbsenceJustification,
    AcademicYear,
    AttendanceAlert,
    AttendanceRecord,
    AttendanceSession,
    Class,
    Enrollment,
    JustificationReview,
    Period,
    TeacherAssignment,
    TimetableConstraint,
    TimetableGenerationJob,
    TimetableException,
    TimetableSlot,
)

# G2B — Calendar
from app.models.calendar import (
    Event,
    EventReminder,
    EventReminderPreference,
    EventRSVP,
    MoroccanHoliday,
)

# G3 — LMS
from app.models.lms import (
    Activity,
    ActivitySession,
    Assessment,
    AssessmentResult,
    Assignment,
    ClassContentAssignment,
    ContentItem,
    ContentItemAsset,
    ContentProgress,
    ContentSubmission,
    Course,
    GradeCategory,
    Grade,
    QuestionBankItem,
    Quiz,
    QuizAttempt,
    QuizQuestion,
    QuizResponse,
    Rubric,
    RubricCriterion,
    RubricLevel,
    RubricScore,
    StudentPeriodAverage,
    Submission,
    SubmissionFile,
)

# G4 — COM
from app.models.com import (
    Announcement,
    ConsentPreference,
    Conversation,
    ConversationParticipant,
    DeviceToken,
    Message,
    MessageReadReceipt,
    Notification,
    NotificationDelivery,
    NotificationPreference,
    ParentFeedItem,
)

# G5 — Billing
from app.models.billing import (
    FeeAssignment,
    FeeStructure,
    Installment,
    Invoice,
    InvoiceItem,
    LateFeePolicy,
    PaymentAttempt,
    PaymentPlan,
    PaymentProof,
    ProviderWebhookEvent,
    SiblingDiscountPolicy,
)

# G5B — Micro-school
from app.models.micro_school import (
    MicroEnrollment,
    MicroEnrollmentStatus,
    MicroGroup,
    MicroPayment,
    MicroPaymentPeriodType,
    MicroPaymentStatus,
    MicroProgressLog,
    MicroResource,
    MicroResourceType,
    MicroSchool,
    MicroSchoolStatus,
)

# G5C — Budget
from app.models.budget import (
    BudgetAllocation,
    BudgetAllocationStatus,
    BudgetRequest,
    BudgetRequestStatus,
    BudgetTransaction,
    BudgetTransactionType,
    MicroBudget,
    MicroBudgetStatus,
)

# G5D — Skills
from app.models.skill_passport import (
    SkillDimension,
    SkillMilestone,
    SkillPassport,
    SkillProgress,
    SkillProgressStatus,
)

# G6 — Audit
from app.models.audit import AuditLog

# G7 — AI
from app.models.ai import (
    AIPreference,
    WritingAttempt,
)

# G8 — Feature Toggles
from app.models.feature import FeatureToggle

# G9 — Reporting
from app.models.reporting import (
    DataExport,
    ReportJob,
    ReportSchedule,
)

# G10 — Document management
from app.models.documents import (
    Document,
    DocumentVersion,
    Resource,
    ResourceRating,
    StudentDocumentRequirement,
)

__all__ = [
    # Schools
    "School",
    "SchoolStatus",
    # IAM
    "User",
    "Membership",
    "Session",
    "InvitationCode",
    "AccountRecoveryRequest",
    "LoginHistory",
    "ParentChildLink",
    "StudentProfile",
    "ParentProfile",
    "TeacherProfile",
    "AdminProfile",
    "ContentManagerProfile",
    # ERP
    "AcademicYear",
    "Period",
    "Class",
    "Enrollment",
    "TeacherAssignment",
    "AttendanceSession",
    "AttendanceRecord",
    "AttendanceAlert",
    "AbsenceJustification",
    "JustificationReview",
    "TimetableConstraint",
    "TimetableGenerationJob",
    "TimetableSlot",
    "TimetableException",
    "Event",
    "EventRSVP",
    "EventReminder",
    "EventReminderPreference",
    "MoroccanHoliday",
    # LMS
    "Course",
    "Assignment",
    "Submission",
    "SubmissionFile",
    "Grade",
    "GradeCategory",
    "QuestionBankItem",
    "StudentPeriodAverage",
    "Assessment",
    "AssessmentResult",
    "ContentItem",
    "ContentItemAsset",
    "ContentProgress",
    "ClassContentAssignment",
    "ContentSubmission",
    "Quiz",
    "QuizQuestion",
    "QuizAttempt",
    "QuizResponse",
    "Rubric",
    "RubricCriterion",
    "RubricLevel",
    "RubricScore",
    "Activity",
    "ActivitySession",
    # COM
    "ConsentPreference",
    "Notification",
    "NotificationDelivery",
    "NotificationPreference",
    "DeviceToken",
    "ParentFeedItem",
    "Conversation",
    "ConversationParticipant",
    "Message",
    "MessageReadReceipt",
    "Announcement",
    # Billing
    "FeeStructure",
    "FeeAssignment",
    "SiblingDiscountPolicy",
    "LateFeePolicy",
    "Invoice",
    "InvoiceItem",
    "PaymentPlan",
    "Installment",
    "PaymentAttempt",
    "PaymentProof",
    "ProviderWebhookEvent",
    # Micro-school
    "MicroSchool",
    "MicroSchoolStatus",
    "MicroGroup",
    "MicroEnrollment",
    "MicroEnrollmentStatus",
    "MicroPayment",
    "MicroPaymentPeriodType",
    "MicroPaymentStatus",
    "MicroResource",
    "MicroResourceType",
    "MicroProgressLog",
    # Budget
    "MicroBudget",
    "MicroBudgetStatus",
    "BudgetAllocation",
    "BudgetAllocationStatus",
    "BudgetRequest",
    "BudgetRequestStatus",
    "BudgetTransaction",
    "BudgetTransactionType",
    # Skills
    "SkillDimension",
    "SkillMilestone",
    "SkillProgress",
    "SkillProgressStatus",
    "SkillPassport",
    # Audit
    "AuditLog",
    # AI
    "WritingAttempt",
    "AIPreference",
    # Feature Toggles
    "FeatureToggle",
    # Reporting
    "ReportJob",
    "DataExport",
    "ReportSchedule",
    # Documents
    "Document",
    "DocumentVersion",
    "Resource",
    "ResourceRating",
    "StudentDocumentRequirement",
]
