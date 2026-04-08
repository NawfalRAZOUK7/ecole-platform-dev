"""Model-to-dict serialization helpers for LMS sub-services."""

from __future__ import annotations

from app.models.lms import (
    Activity,
    ActivitySession,
    Assessment,
    Assignment,
    ContentItem,
    Course,
    Grade,
    Quiz,
    QuizAttempt,
    QuizQuestion,
    Submission,
)


class LMSSerializerMixin:
    """Provides model → dict serialization for all LMS entity types.

    Inherited by LMSServiceBase so all sub-services can serialize models.
    """

    @staticmethod
    def _course_to_dict(course: Course) -> dict:
        return {
            "id": str(course.id),
            "school_id": str(course.school_id),
            "class_id": str(course.class_id),
            "teacher_id": str(course.teacher_id),
            "title": course.title,
            "description": course.description,
            "status": course.status,
        }

    @staticmethod
    def _assignment_to_dict(assignment: Assignment) -> dict:
        return {
            "id": str(assignment.id),
            "course_id": str(assignment.course_id),
            "teacher_id": str(assignment.teacher_id),
            "title": assignment.title,
            "description": assignment.description,
            "due_at": assignment.due_at.isoformat() if assignment.due_at else None,
            "total_points": assignment.total_points,
            "exercise_type": assignment.exercise_type,
            "quiz_id": str(assignment.quiz_id) if assignment.quiz_id else None,
            "exercise_pdf_path": assignment.exercise_pdf_path,
        }

    @staticmethod
    def _submission_to_dict(submission: Submission) -> dict:
        return {
            "id": str(submission.id),
            "assignment_id": str(submission.assignment_id),
            "student_id": str(submission.student_id),
            "status": submission.status,
            "submitted_at": (
                submission.submitted_at.isoformat() if submission.submitted_at else None
            ),
        }

    @staticmethod
    def _grade_to_dict(grade: Grade) -> dict:
        return {
            "id": str(grade.id),
            "submission_id": str(grade.submission_id),
            "teacher_id": str(grade.teacher_id),
            "score": float(grade.score),
            "feedback_text": grade.feedback_text,
            "published_at": grade.published_at.isoformat()
            if grade.published_at
            else None,
        }

    @staticmethod
    def _content_item_to_dict(content_item: ContentItem) -> dict:
        return {
            "id": str(content_item.id),
            "school_id": str(content_item.school_id)
            if content_item.school_id
            else None,
            "title": content_item.title,
            "content_type": content_item.content_type,
            "level_band": content_item.level_band,
            "language": content_item.language,
            "status": content_item.status,
        }

    @staticmethod
    def _assessment_to_dict(assessment: Assessment) -> dict:
        return {
            "id": str(assessment.id),
            "class_id": str(assessment.class_id),
            "teacher_id": str(assessment.teacher_id),
            "title": assessment.title,
            "due_at": assessment.due_at.isoformat() if assessment.due_at else None,
            "window_end": (
                assessment.window_end.isoformat() if assessment.window_end else None
            ),
            "total_points": assessment.total_points,
            "status": assessment.status,
        }

    @staticmethod
    def _activity_to_dict(activity: Activity) -> dict:
        return {
            "id": str(activity.id),
            "school_id": str(activity.school_id) if activity.school_id else None,
            "type": activity.type,
            "difficulty": activity.difficulty,
            "title": activity.title,
            "pedagogical_objective": activity.pedagogical_objective,
        }

    @staticmethod
    def _activity_session_to_dict(session: ActivitySession) -> dict:
        return {
            "id": str(session.id),
            "student_id": str(session.student_id),
            "activity_id": str(session.activity_id),
            "status": session.status,
            "score": float(session.score) if session.score is not None else None,
            "attempt_no": session.attempt_no,
        }

    @staticmethod
    def _quiz_to_dict(
        quiz: Quiz,
        questions: list[QuizQuestion] | None = None,
    ) -> dict:
        questions = questions or []
        return {
            "id": str(quiz.id),
            "school_id": str(quiz.school_id) if quiz.school_id else None,
            "created_by": str(quiz.created_by),
            "title": quiz.title,
            "description": quiz.description,
            "subject": quiz.subject,
            "level_band": quiz.level_band,
            "difficulty": quiz.difficulty,
            "time_limit_minutes": quiz.time_limit_minutes,
            "max_attempts": quiz.max_attempts,
            "shuffle_questions": quiz.shuffle_questions,
            "status": quiz.status,
            "total_points": sum(question.points for question in questions),
            "question_count": len(questions),
        }

    @staticmethod
    def _quiz_question_to_dict(
        question: QuizQuestion,
        *,
        include_answer: bool = False,
    ) -> dict:
        payload = {
            "id": str(question.id),
            "question_type": question.question_type,
            "question_text": question.question_text,
            "question_media_path": question.question_media_path,
            "options": question.options,
            "points": question.points,
            "order": question.order,
            "explanation": question.explanation if include_answer else None,
        }
        if include_answer:
            payload["correct_answer"] = question.correct_answer
        return payload

    @staticmethod
    def _attempt_to_dict(attempt: QuizAttempt) -> dict:
        return {
            "id": str(attempt.id),
            "quiz_id": str(attempt.quiz_id),
            "student_id": str(attempt.student_id),
            "attempt_no": attempt.attempt_no,
            "started_at": attempt.started_at.isoformat()
            if attempt.started_at
            else None,
            "completed_at": (
                attempt.completed_at.isoformat() if attempt.completed_at else None
            ),
            "score": float(attempt.score) if attempt.score is not None else None,
            "max_score": attempt.max_score,
            "status": attempt.status,
        }
