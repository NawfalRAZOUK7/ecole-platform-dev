"""Split LMS service exports."""

from __future__ import annotations

from app.services.lms.assignment_service import AssignmentService
from app.services.lms.content_service import ContentService
from app.services.lms.course_service import CourseService
from app.services.lms.progress_service import ProgressService
from app.services.lms.quiz_service import QuizService


class LMSService:
    """Backward-compatible LMS facade over the split sub-services."""

    def __init__(self, db) -> None:
        self.course_service = CourseService(db)
        self.assignment_service = AssignmentService(db)
        self.quiz_service = QuizService(db)
        self.content_service = ContentService(db)
        self.progress_service = ProgressService(db)
        self._services = (
            self.course_service,
            self.assignment_service,
            self.quiz_service,
            self.content_service,
            self.progress_service,
        )

    def __getattr__(self, name: str):
        for service in self._services:
            if hasattr(service, name):
                return getattr(service, name)
        raise AttributeError(f"{type(self).__name__!s} has no attribute {name!r}")


__all__ = [
    "AssignmentService",
    "ContentService",
    "CourseService",
    "LMSService",
    "ProgressService",
    "QuizService",
]
