"""Domain protocol exports."""

from app.domain.protocols.evaluatable import Evaluatable
from app.domain.protocols.grading import (
    GradingStrategy,
    ManualGradeStrategy,
    QuizAutoGradeStrategy,
)

__all__ = [
    "Evaluatable",
    "GradingStrategy",
    "QuizAutoGradeStrategy",
    "ManualGradeStrategy",
]
