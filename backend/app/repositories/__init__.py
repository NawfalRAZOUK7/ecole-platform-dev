"""Repository layer package."""

from app.repositories.admin import AdminRepository
from app.repositories.ai import AIRepository
from app.repositories.analytics import AnalyticsRepository
from app.repositories.base import BaseRepository
from app.repositories.audit import AuditRepository
from app.repositories.auth import AuthRepository
from app.repositories.billing import BillingRepository
from app.repositories.calendar import CalendarRepository
from app.repositories.cms import CMSRepository
from app.repositories.documents import DocumentsRepository
from app.repositories.erp import ERPRepository
from app.repositories.feature import FeatureRepository
from app.repositories.gdpr import GDPRRepository
from app.repositories.lms import LMSRepository
from app.repositories.messaging import MessagingRepository
from app.repositories.notifications import NotificationRepository
from app.repositories.profile import ProfileRepository
from app.repositories.progress import ProgressRepository
from app.repositories.quiz import QuizRepository
from app.repositories.reports import ReportsRepository

__all__ = [
    "BaseRepository",
    "AdminRepository",
    "AIRepository",
    "AuditRepository",
    "AuthRepository",
    "BillingRepository",
    "CalendarRepository",
    "CMSRepository",
    "DocumentsRepository",
    "ERPRepository",
    "FeatureRepository",
    "GDPRRepository",
    "LMSRepository",
    "MessagingRepository",
    "NotificationRepository",
    "ProfileRepository",
    "ProgressRepository",
    "QuizRepository",
    "AnalyticsRepository",
    "ReportsRepository",
]
