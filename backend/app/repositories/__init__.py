"""Repository layer package."""

from app.repositories.analytics import AnalyticsRepository
from app.repositories.base import BaseRepository
from app.repositories.audit import AuditRepository
from app.repositories.auth import AuthRepository
from app.repositories.billing import BillingRepository
from app.repositories.calendar import CalendarRepository
from app.repositories.cms import CMSRepository
from app.repositories.documents import DocumentsRepository
from app.repositories.erp import ERPRepository
from app.repositories.lms import LMSRepository
from app.repositories.messaging import MessagingRepository
from app.repositories.notifications import NotificationRepository
from app.repositories.progress import ProgressRepository
from app.repositories.quiz import QuizRepository
from app.repositories.reports import ReportsRepository

__all__ = [
    "BaseRepository",
    "AuditRepository",
    "AuthRepository",
    "BillingRepository",
    "CalendarRepository",
    "CMSRepository",
    "DocumentsRepository",
    "ERPRepository",
    "LMSRepository",
    "MessagingRepository",
    "NotificationRepository",
    "ProgressRepository",
    "QuizRepository",
    "AnalyticsRepository",
    "ReportsRepository",
]
