"""Quiz LMS service."""

from __future__ import annotations

import uuid

from app.core.dependencies import AuthContext
from app.core.exceptions import NotFoundError, ValidationError
from app.core.permissions import ADM, CONTENT_MGR, STD, TCH
from app.core.response import encode_cursor
from app.core.unit_of_work import UnitOfWork
from app.repositories.quiz import QuizRepository
from app.schemas.quiz import QuizCreateRequest, QuizRespondRequest, QuizUpdateRequest
from app.services.audit import AuditService
from app.services.lms._helpers import LMSServiceBase, _utc_now
from app.services.quiz_grading import grade_attempt


class QuizService(LMSServiceBase):
    """Handles quiz CRUD, attempts, auto-grading, and analytics."""

    async def create_quiz(
        self,
        *,
        body: QuizCreateRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        school_id = None if auth.role == CONTENT_MGR else auth.school_id
        async with UnitOfWork(self.db) as uow:
            quiz_repo = QuizRepository(uow.session)
            audit = AuditService(uow.session)
            quiz = await quiz_repo.create_quiz(
                school_id=school_id,
                created_by=auth.user_id,
                title=body.title,
                description=body.description,
                subject=body.subject,
                level_band=body.level_band,
                difficulty=body.difficulty,
                time_limit_minutes=body.time_limit_minutes,
                max_attempts=body.max_attempts,
                shuffle_questions=body.shuffle_questions,
                status="draft",
            )
            questions = await quiz_repo.create_quiz_questions(
                [
                    {
                        "quiz_id": quiz.id,
                        "question_type": question.question_type,
                        "question_text": question.question_text,
                        "question_media_path": question.question_media_path,
                        "options": question.options,
                        "correct_answer": question.correct_answer,
                        "points": question.points,
                        "order": question.order if question.order > 0 else index,
                        "explanation": question.explanation,
                    }
                    for index, question in enumerate(body.questions)
                ]
            )
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="QUIZ_CREATED",
                outcome="success",
                target_type="quiz",
                target_id=quiz.id,
                entity_after={"title": quiz.title, "question_count": len(questions)},
                ip_address=ip_address,
            )
            await uow.commit()

        payload = self._quiz_to_dict(quiz, questions)
        payload["questions"] = [
            self._quiz_question_to_dict(question, include_answer=True)
            for question in questions
        ]
        return payload

    async def list_quizzes(
        self,
        *,
        subject: str | None,
        level_band: str | None,
        status: str | None,
        difficulty: str | None,
        cursor: str | None,
        limit: int,
        auth: AuthContext,
    ) -> tuple[list[dict], str | None, bool]:
        quizzes, has_more = await self.quiz_repo.list_quizzes_for_actor(
            role=auth.role,
            school_id=auth.school_id,
            user_id=auth.user_id,
            subject=subject,
            level_band=level_band,
            status=status,
            difficulty=difficulty,
            cursor=cursor,
            limit=limit,
        )
        counts = await self.quiz_repo.get_question_counts([quiz.id for quiz in quizzes])
        items = []
        for quiz in quizzes:
            question_count, total_points = counts.get(quiz.id, (0, 0))
            items.append(
                {
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
                    "total_points": total_points,
                    "question_count": question_count,
                }
            )
        next_cursor = encode_cursor(quizzes[-1].id) if has_more and quizzes else None
        return items, next_cursor, has_more

    async def get_quiz(
        self,
        *,
        quiz_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict:
        quiz = await self.quiz_repo.get_quiz(quiz_id)
        if quiz is None:
            raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")
        if quiz.school_id is not None and quiz.school_id != auth.school_id:
            raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")
        if auth.role == STD and quiz.status != "published":
            raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")

        questions = await self.quiz_repo.list_quiz_questions(quiz_id)
        include_answer = auth.role in (CONTENT_MGR, TCH, ADM)
        payload = self._quiz_to_dict(quiz, questions)
        payload["questions"] = [
            self._quiz_question_to_dict(question, include_answer=include_answer)
            for question in questions
        ]
        return payload

    async def update_quiz(
        self,
        *,
        quiz_id: uuid.UUID,
        body: QuizUpdateRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        quiz = await self.quiz_repo.get_quiz(quiz_id)
        if quiz is None:
            raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")
        if quiz.status != "draft":
            raise ValidationError(
                "Can only edit draft quizzes", error_code="ERR-QUIZ-400"
            )
        if auth.role == TCH and quiz.created_by != auth.user_id:
            raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")

        update_data = body.model_dump(exclude_unset=True, exclude={"questions"})
        async with UnitOfWork(self.db) as uow:
            quiz_repo = QuizRepository(uow.session)
            audit = AuditService(uow.session)
            for field, value in update_data.items():
                setattr(quiz, field, value)
            await quiz_repo.save_quiz(quiz)

            if body.questions is not None:
                await quiz_repo.delete_quiz_questions(quiz_id)
                await quiz_repo.create_quiz_questions(
                    [
                        {
                            "quiz_id": quiz.id,
                            "question_type": question.question_type,
                            "question_text": question.question_text,
                            "question_media_path": question.question_media_path,
                            "options": question.options,
                            "correct_answer": question.correct_answer,
                            "points": question.points,
                            "order": question.order if question.order > 0 else index,
                            "explanation": question.explanation,
                        }
                        for index, question in enumerate(body.questions)
                    ]
                )

            questions = await quiz_repo.list_quiz_questions(quiz_id)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="QUIZ_UPDATED",
                outcome="success",
                target_type="quiz",
                target_id=quiz.id,
                entity_after={"title": quiz.title},
                ip_address=ip_address,
            )
            await uow.commit()

        payload = self._quiz_to_dict(quiz, questions)
        payload["questions"] = [
            self._quiz_question_to_dict(question, include_answer=True)
            for question in questions
        ]
        return payload

    async def publish_quiz(
        self,
        *,
        quiz_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        quiz = await self.quiz_repo.get_quiz(quiz_id)
        if quiz is None:
            raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")
        if auth.role == TCH and quiz.created_by != auth.user_id:
            raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")
        if quiz.status != "draft":
            raise ValidationError(
                "Quiz is not in draft status", error_code="ERR-QUIZ-400"
            )

        question_count = await self.quiz_repo.count_quiz_questions(quiz_id)
        if question_count == 0:
            raise ValidationError(
                "Cannot publish a quiz with no questions",
                error_code="ERR-QUIZ-400",
            )

        async with UnitOfWork(self.db) as uow:
            quiz_repo = QuizRepository(uow.session)
            audit = AuditService(uow.session)
            quiz.status = "published"
            await quiz_repo.save_quiz(quiz)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="QUIZ_PUBLISHED",
                outcome="success",
                target_type="quiz",
                target_id=quiz.id,
                entity_after={"status": "published"},
                ip_address=ip_address,
            )
            await uow.commit()

        return {"id": str(quiz.id), "status": "published"}

    async def start_quiz_attempt(
        self,
        *,
        quiz_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        quiz = await self.quiz_repo.get_quiz(quiz_id)
        if quiz is None or quiz.status != "published":
            raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")
        if quiz.school_id is not None and quiz.school_id != auth.school_id:
            raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")

        existing_count = await self.quiz_repo.count_student_attempts(
            quiz_id=quiz_id,
            student_id=auth.user_id,
        )
        if existing_count >= quiz.max_attempts:
            raise ValidationError(
                f"Maximum attempts ({quiz.max_attempts}) reached",
                error_code="ERR-QUIZ-429",
            )

        active = await self.quiz_repo.get_active_attempt(
            quiz_id=quiz_id,
            student_id=auth.user_id,
        )
        if active is not None:
            return self._attempt_to_dict(active)

        async with UnitOfWork(self.db) as uow:
            quiz_repo = QuizRepository(uow.session)
            audit = AuditService(uow.session)
            max_score = await quiz_repo.sum_quiz_points(quiz_id)
            attempt = await quiz_repo.create_quiz_attempt(
                quiz_id=quiz_id,
                student_id=auth.user_id,
                attempt_no=existing_count + 1,
                started_at=_utc_now(),
                max_score=max_score,
                status="STARTED",
            )
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="QUIZ_ATTEMPT_STARTED",
                outcome="success",
                target_type="quiz_attempt",
                target_id=attempt.id,
                entity_after={
                    "quiz_id": str(quiz_id),
                    "attempt_no": attempt.attempt_no,
                },
                ip_address=ip_address,
            )
            await uow.commit()

        return self._attempt_to_dict(attempt)

    async def respond_to_quiz_question(
        self,
        *,
        attempt_id: uuid.UUID,
        body: QuizRespondRequest,
        auth: AuthContext,
    ) -> dict:
        attempt = await self.quiz_repo.get_quiz_attempt(attempt_id)
        if attempt is None or attempt.student_id != auth.user_id:
            raise NotFoundError("Attempt not found", error_code="ERR-QUIZ-404")
        if attempt.status != "STARTED":
            raise ValidationError(
                "Attempt already completed", error_code="ERR-QUIZ-400"
            )

        quiz = await self.quiz_repo.get_quiz(attempt.quiz_id)
        if quiz is None:
            raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")

        if quiz.time_limit_minutes and quiz.time_limit_minutes > 0:
            elapsed = (_utc_now() - attempt.started_at).total_seconds()
            if elapsed > quiz.time_limit_minutes * 60:
                async with UnitOfWork(self.db) as uow:
                    quiz_repo = QuizRepository(uow.session)
                    attempt.status = "TIMED_OUT"
                    attempt.completed_at = _utc_now()
                    await quiz_repo.save_quiz_attempt(attempt)
                    await uow.commit()
                raise ValidationError("Time limit exceeded", error_code="ERR-QUIZ-408")

        question = await self.quiz_repo.get_quiz_question(
            quiz_id=attempt.quiz_id,
            question_id=body.question_id,
        )
        if question is None:
            raise NotFoundError(
                "Question not found in this quiz",
                error_code="ERR-QUIZ-404",
            )

        response = await self.quiz_repo.get_quiz_response(
            attempt_id=attempt_id,
            question_id=body.question_id,
        )
        now = _utc_now()
        async with UnitOfWork(self.db) as uow:
            quiz_repo = QuizRepository(uow.session)
            if response is not None:
                response.student_answer = body.student_answer
                response.answered_at = now
                response.is_correct = None
                response.points_earned = None
                await quiz_repo.save_quiz_response(response)
            else:
                response = await quiz_repo.create_quiz_response(
                    attempt_id=attempt_id,
                    question_id=body.question_id,
                    student_answer=body.student_answer,
                    answered_at=now,
                )
            await uow.commit()

        return {
            "id": str(response.id),
            "attempt_id": str(attempt_id),
            "question_id": str(body.question_id),
            "answered_at": now.isoformat(),
        }

    async def submit_quiz_attempt(
        self,
        *,
        attempt_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        attempt = await self.quiz_repo.get_quiz_attempt(attempt_id)
        if attempt is None or attempt.student_id != auth.user_id:
            raise NotFoundError("Attempt not found", error_code="ERR-QUIZ-404")
        if attempt.status != "STARTED":
            raise ValidationError(
                "Attempt already completed", error_code="ERR-QUIZ-400"
            )

        async with UnitOfWork(self.db) as uow:
            quiz_repo = QuizRepository(uow.session)
            audit = AuditService(uow.session)
            total_score, max_score = await grade_attempt(attempt_id, uow.session)
            attempt = await quiz_repo.get_quiz_attempt(attempt_id)
            if attempt is None:
                raise NotFoundError("Attempt not found", error_code="ERR-QUIZ-404")
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="QUIZ_ATTEMPT_SUBMITTED",
                outcome="success",
                target_type="quiz_attempt",
                target_id=attempt.id,
                entity_after={
                    "score": float(total_score),
                    "max_score": max_score,
                    "status": "COMPLETED",
                },
                ip_address=ip_address,
            )
            await uow.commit()

        await self._dispatch_quiz_completed(
            attempt=attempt,
            actor_id=auth.user_id,
            school_id=auth.school_id,
            total_score=float(total_score),
            max_score=max_score,
        )
        return self._attempt_to_dict(attempt)

    async def get_quiz_analytics(
        self,
        *,
        quiz_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict:
        quiz = await self.quiz_repo.get_quiz(quiz_id)
        if quiz is None:
            raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")

        if auth.role == TCH and quiz.created_by != auth.user_id:
            if quiz.school_id is not None and quiz.school_id != auth.school_id:
                raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")

        (
            total_attempts,
            completed,
            avg_score,
            max_achieved,
            min_achieved,
        ) = await self.quiz_repo.get_attempt_stats(quiz_id)
        max_possible = await self.quiz_repo.sum_quiz_points(quiz_id)
        avg_pct = (
            round(avg_score / max_possible * 100, 1)
            if avg_score is not None and max_possible > 0
            else None
        )

        questions = await self.quiz_repo.list_quiz_questions(quiz_id)
        question_stats = []
        for question in questions:
            (
                total_responses,
                correct_responses,
            ) = await self.quiz_repo.get_question_response_stats(question.id)
            question_stats.append(
                {
                    "question_id": str(question.id),
                    "question_text": question.question_text[:100],
                    "question_type": question.question_type,
                    "total_responses": total_responses,
                    "correct_responses": correct_responses,
                    "accuracy": (
                        round(correct_responses / total_responses * 100, 1)
                        if total_responses > 0
                        else None
                    ),
                }
            )

        return {
            "quiz_id": str(quiz_id),
            "title": quiz.title,
            "total_attempts": total_attempts,
            "completed_attempts": completed,
            "average_score": round(avg_score, 2) if avg_score is not None else None,
            "max_score_achieved": max_achieved,
            "min_score_achieved": min_achieved,
            "average_percentage": avg_pct,
            "question_stats": question_stats,
        }
