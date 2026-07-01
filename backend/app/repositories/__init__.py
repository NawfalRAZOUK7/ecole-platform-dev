"""Repository layer package."""

from app.repositories.admin import AdminRepository
from app.repositories.ai import AIRepository
from app.repositories.reports_analytics import AnalyticsRepository
from app.repositories.academic_attendance_analytics import AttendanceAnalyticsRepository
from app.repositories.base import BaseRepository
from app.repositories.audit import AuditRepository
from app.repositories.auth import AuthRepository
from app.repositories.billing import BillingRepository
from app.repositories.billing_enhancements import BillingEnhancementsRepository
from app.repositories.budget import BudgetRepository
from app.repositories.communication_calendar import CalendarRepository
from app.repositories.content_cms import CMSRepository
from app.repositories.admin_men_compliance import ComplianceRepository
from app.repositories.content_documents import DocumentsRepository
from app.repositories.erp import ERPRepository
from app.repositories.admin_feature import FeatureRepository
from app.repositories.reports_financial_health import FinancialHealthRepository
from app.repositories.user_gdpr import GDPRRepository
from app.repositories.academic_gradebook import GradebookRepository
from app.repositories.lms import (
    AssessmentRepository,
    AssignmentRepository,
    LMSRepository,
)
from app.repositories.auth_login_history import LoginHistoryRepository
from app.repositories.communication_messaging import MessagingRepository
from app.repositories.school_micro_school import MicroSchoolRepository
from app.repositories.communication_notifications import NotificationRepository
from app.repositories.user_profile import ProfileRepository
from app.repositories.profile_loader import ProfileLoaderRepository
from app.repositories.academic_progress import ProgressRepository
from app.repositories.lms_question_bank import QuestionBankRepository
from app.repositories.lms_quiz import QuizRepository
from app.repositories.reports import ReportsRepository
from app.repositories.reports_schedule import ReportScheduleRepository
from app.repositories.lms_rubric import RubricRepository
from app.repositories.school import SchoolRepository
from app.repositories.academic_skill_passport import SkillPassportRepository
from app.repositories.sync_queue import SyncQueueRepository
from app.repositories.academic_timetable_generation import TimetableGenerationRepository

__all__ = [
    "BaseRepository",
    "AdminRepository",
    "AIRepository",
    "AuditRepository",
    "AuthRepository",
    "AttendanceAnalyticsRepository",
    "BillingRepository",
    "BillingEnhancementsRepository",
    "BudgetRepository",
    "CalendarRepository",
    "CMSRepository",
    "ComplianceRepository",
    "DocumentsRepository",
    "ERPRepository",
    "FeatureRepository",
    "FinancialHealthRepository",
    "GDPRRepository",
    "GradebookRepository",
    "LMSRepository",
    "AssignmentRepository",
    "AssessmentRepository",
    "LoginHistoryRepository",
    "MessagingRepository",
    "MicroSchoolRepository",
    "NotificationRepository",
    "ProfileRepository",
    "ProfileLoaderRepository",
    "ProgressRepository",
    "QuestionBankRepository",
    "QuizRepository",
    "RubricRepository",
    "SchoolRepository",
    "SkillPassportRepository",
    "SyncQueueRepository",
    "TimetableGenerationRepository",
    "AnalyticsRepository",
    "ReportsRepository",
    "ReportScheduleRepository",
]
