"""Repository layer package."""

from app.repositories.admin import AdminRepository
from app.repositories.ai import AIRepository
from app.repositories.analytics import AnalyticsRepository
from app.repositories.attendance_analytics import AttendanceAnalyticsRepository
from app.repositories.base import BaseRepository
from app.repositories.audit import AuditRepository
from app.repositories.auth import AuthRepository
from app.repositories.billing import BillingRepository
from app.repositories.billing_enhancements import BillingEnhancementsRepository
from app.repositories.budget import BudgetRepository
from app.repositories.calendar import CalendarRepository
from app.repositories.cms import CMSRepository
from app.repositories.men_compliance import ComplianceRepository
from app.repositories.documents import DocumentsRepository
from app.repositories.erp import ERPRepository
from app.repositories.feature import FeatureRepository
from app.repositories.financial_health import FinancialHealthRepository
from app.repositories.gdpr import GDPRRepository
from app.repositories.gradebook import GradebookRepository
from app.repositories.lms import (
    AssessmentRepository,
    AssignmentRepository,
    LMSRepository,
)
from app.repositories.login_history import LoginHistoryRepository
from app.repositories.messaging import MessagingRepository
from app.repositories.micro_school import MicroSchoolRepository
from app.repositories.notifications import NotificationRepository
from app.repositories.profile import ProfileRepository
from app.repositories.profile_loader import ProfileLoaderRepository
from app.repositories.progress import ProgressRepository
from app.repositories.question_bank import QuestionBankRepository
from app.repositories.quiz import QuizRepository
from app.repositories.reports import ReportsRepository
from app.repositories.report_schedule import ReportScheduleRepository
from app.repositories.rubric import RubricRepository
from app.repositories.school import SchoolRepository
from app.repositories.skill_passport import SkillPassportRepository
from app.repositories.sync_queue import SyncQueueRepository
from app.repositories.timetable_generation import TimetableGenerationRepository

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
