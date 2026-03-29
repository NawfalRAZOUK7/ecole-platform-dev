"""Question bank service for reusable quiz questions and quiz generation."""

from __future__ import annotations

import random
import uuid
from typing import Any

from app.core.dependencies import AuthContext, verify_school_boundary
from app.core.exceptions import NotFoundError, ValidationError
from app.core.permissions import TCH
from app.core.response import encode_cursor
from app.core.unit_of_work import UnitOfWork
from app.repositories.question_bank import QuestionBankRepository
from app.repositories.quiz import QuizRepository
from app.schemas.question_bank import (
    GenerateQuizFromBankRequest,
    QuestionBankCreateRequest,
)
from app.services.audit import AuditService
from app.services.lms._helpers import LMSServiceBase


class QuestionBankService(LMSServiceBase):
    """Handles question bank CRUD, import, generation, and analytics."""

    def __init__(self, db) -> None:
        super().__init__(db)
        self.question_bank_repo = QuestionBankRepository(db)

    def _item_to_dict(self, item) -> dict[str, Any]:
        return {
            "id": str(item.id),
            "school_id": str(item.school_id),
            "teacher_id": str(item.teacher_id),
            "subject": item.subject,
            "level": item.level,
            "difficulty": item.difficulty,
            "question_type": item.question_type,
            "question_data": item.question_data,
            "tags": list(item.tags or []),
            "usage_count": item.usage_count,
            "is_archived": item.is_archived,
        }

    def _validate_distribution(self, distribution: dict[str, int]) -> dict[str, int]:
        if not distribution:
            raise ValidationError(
                "Question distribution is required",
                error_code="ERR-QUIZ-400",
            )

        normalized: dict[str, int] = {}
        valid_keys = {"easy", "medium", "hard"}
        for key, value in distribution.items():
            normalized_key = key.lower()
            if normalized_key not in valid_keys:
                raise ValidationError(
                    "Distribution keys must be easy, medium, or hard",
                    error_code="ERR-QUIZ-400",
                )
            if value < 0:
                raise ValidationError(
                    "Distribution counts cannot be negative",
                    error_code="ERR-QUIZ-400",
                )
            if value > 0:
                normalized[normalized_key] = value

        if not normalized:
            raise ValidationError(
                "At least one distribution count must be greater than zero",
                error_code="ERR-QUIZ-400",
            )
        return normalized

    def _question_payload_from_bank_item(self, item, *, order: int) -> dict[str, Any]:
        question_data = dict(item.question_data or {})
        return {
            "quiz_id": None,
            "question_type": question_data.get("question_type", item.question_type),
            "question_text": question_data.get("question_text"),
            "question_media_path": question_data.get("question_media_path"),
            "options": question_data.get("options"),
            "correct_answer": question_data.get("correct_answer"),
            "points": int(question_data.get("points", 1) or 0),
            "order": order,
            "explanation": question_data.get("explanation"),
        }

    async def add_question(
        self,
        *,
        body: QuestionBankCreateRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict[str, Any]:
        async with UnitOfWork(self.db) as uow:
            repo = QuestionBankRepository(uow.session)
            audit = AuditService(uow.session)
            item = await repo.create_question_bank_item(
                school_id=auth.school_id,
                teacher_id=auth.user_id,
                subject=body.subject,
                level=body.level,
                difficulty=body.difficulty,
                question_type=body.question_data.question_type,
                question_data=body.question_data.model_dump(),
                tags=body.tags,
                usage_count=0,
                is_archived=False,
            )
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="QUESTION_BANK_ITEM_CREATED",
                outcome="success",
                target_type="question_bank_item",
                target_id=item.id,
                entity_after={
                    "subject": item.subject,
                    "difficulty": item.difficulty,
                    "question_type": item.question_type,
                },
                ip_address=ip_address,
            )
            await uow.commit()

        return self._item_to_dict(item)

    async def list_questions(
        self,
        *,
        subject: str | None,
        level: str | None,
        difficulty: str | None,
        tags: list[str] | None,
        search: str | None,
        cursor: str | None,
        limit: int,
        auth: AuthContext,
    ) -> tuple[list[dict[str, Any]], str | None, bool]:
        items, has_more = await self.question_bank_repo.list_question_bank_items(
            school_id=auth.school_id,
            subject=subject,
            level=level,
            difficulty=difficulty,
            tags=tags,
            search=search,
            cursor=cursor,
            limit=limit,
        )
        next_cursor = encode_cursor(items[-1].id) if has_more and items else None
        return [self._item_to_dict(item) for item in items], next_cursor, has_more

    async def import_from_quiz(
        self,
        *,
        quiz_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict[str, Any]:
        quiz = await self.quiz_repo.get_quiz(quiz_id)
        if quiz is None:
            raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")
        if quiz.school_id is not None:
            verify_school_boundary(quiz.school_id, auth)
        elif quiz.status != "published" and quiz.created_by != auth.user_id:
            raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")

        if auth.role == TCH and quiz.created_by != auth.user_id and quiz.status != "published":
            raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")

        questions = await self.quiz_repo.list_quiz_questions(quiz_id)
        if not questions:
            raise ValidationError(
                "Quiz has no questions to import",
                error_code="ERR-QUIZ-400",
            )

        difficulty = (quiz.difficulty or "MEDIUM").lower()
        async with UnitOfWork(self.db) as uow:
            repo = QuestionBankRepository(uow.session)
            audit = AuditService(uow.session)
            created_items = []
            for question in questions:
                created_items.append(
                    await repo.create_question_bank_item(
                        school_id=auth.school_id,
                        teacher_id=auth.user_id,
                        subject=quiz.subject or "General",
                        level=quiz.level_band,
                        difficulty=difficulty if difficulty in {"easy", "medium", "hard"} else "medium",
                        question_type=question.question_type,
                        question_data={
                            "question_type": question.question_type,
                            "question_text": question.question_text,
                            "question_media_path": question.question_media_path,
                            "options": question.options,
                            "correct_answer": question.correct_answer,
                            "points": question.points,
                            "explanation": question.explanation,
                        },
                        tags=[],
                        usage_count=0,
                        is_archived=False,
                    )
                )

            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="QUESTION_BANK_IMPORTED_FROM_QUIZ",
                outcome="success",
                target_type="quiz",
                target_id=quiz.id,
                entity_after={"imported_count": len(created_items)},
                ip_address=ip_address,
            )
            await uow.commit()

        return {"quiz_id": str(quiz.id), "imported_count": len(created_items)}

    async def generate_quiz_from_bank(
        self,
        *,
        body: GenerateQuizFromBankRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict[str, Any]:
        distribution = self._validate_distribution(body.distribution)

        selected_items = []
        for difficulty, required_count in distribution.items():
            candidates = await self.question_bank_repo.list_generation_candidates(
                school_id=auth.school_id,
                subject=body.subject,
                level=body.level,
                difficulty=difficulty,
            )
            if len(candidates) < required_count:
                raise ValidationError(
                    f"Not enough {difficulty} questions available for generation",
                    error_code="ERR-QUIZ-400",
                    details={
                        "difficulty": difficulty,
                        "required": required_count,
                        "available": len(candidates),
                    },
                )
            selected_items.extend(random.sample(candidates, required_count))

        if not selected_items:
            raise ValidationError(
                "No question bank items matched the requested distribution",
                error_code="ERR-QUIZ-400",
            )

        async with UnitOfWork(self.db) as uow:
            quiz_repo = QuizRepository(uow.session)
            qb_repo = QuestionBankRepository(uow.session)
            audit = AuditService(uow.session)
            quiz = await quiz_repo.create_quiz(
                school_id=auth.school_id,
                created_by=auth.user_id,
                title=body.title or f"Generated Quiz - {body.subject}",
                description=body.description or "Generated from question bank",
                subject=body.subject,
                level_band=body.level,
                difficulty=(
                    next(iter(distribution.keys())).upper()
                    if len(distribution) == 1
                    else None
                ),
                time_limit_minutes=body.time_limit_minutes,
                max_attempts=body.max_attempts,
                shuffle_questions=body.shuffle_questions,
                status="draft",
            )
            questions = await quiz_repo.create_quiz_questions(
                [
                    {
                        **self._question_payload_from_bank_item(item, order=index),
                        "quiz_id": quiz.id,
                    }
                    for index, item in enumerate(selected_items)
                ]
            )
            await qb_repo.increment_usage_counts([item.id for item in selected_items])
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="QUESTION_BANK_GENERATED_QUIZ",
                outcome="success",
                target_type="quiz",
                target_id=quiz.id,
                entity_after={
                    "question_count": len(questions),
                    "distribution": distribution,
                },
                ip_address=ip_address,
            )
            await uow.commit()

        payload = self._quiz_to_dict(quiz, questions)
        payload["questions"] = [
            self._quiz_question_to_dict(question, include_answer=True)
            for question in questions
        ]
        return payload

    async def get_question_stats(
        self,
        *,
        auth: AuthContext,
    ) -> list[dict[str, Any]]:
        return await self.question_bank_repo.get_question_stats(school_id=auth.school_id)
