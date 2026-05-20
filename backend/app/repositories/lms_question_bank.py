"""Repository helpers for question bank workflows."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import String, cast, func, or_, select, update

from app.core.response import decode_cursor
from app.models.lms import QuestionBankItem
from app.repositories.base import BaseRepository


class QuestionBankRepository(BaseRepository):
    """Data access helpers for reusable quiz questions."""

    async def _paginate_scalars(
        self,
        query,
        *,
        limit: int,
    ) -> tuple[list[Any], bool]:
        result = await self.db.execute(query.limit(limit + 1))
        items = list(result.scalars().all())
        has_more = len(items) > limit
        if has_more:
            items = items[:limit]
        return items, has_more

    async def create_question_bank_item(self, **kwargs: Any) -> QuestionBankItem:
        item = QuestionBankItem(**kwargs)
        self.db.add(item)
        await self.db.flush()
        return item

    async def get_question_bank_item(
        self,
        item_id: uuid.UUID,
    ) -> QuestionBankItem | None:
        result = await self.db.execute(
            select(QuestionBankItem).where(QuestionBankItem.id == item_id)
        )
        return result.scalar_one_or_none()

    async def list_question_bank_items(
        self,
        *,
        school_id: uuid.UUID,
        subject: str | None,
        level: str | None,
        difficulty: str | None,
        tags: list[str] | None,
        search: str | None,
        cursor: str | None,
        limit: int,
        include_archived: bool = False,
    ) -> tuple[list[QuestionBankItem], bool]:
        query = select(QuestionBankItem).where(QuestionBankItem.school_id == school_id)
        if not include_archived:
            query = query.where(QuestionBankItem.is_archived.is_(False))
        if subject:
            query = query.where(QuestionBankItem.subject == subject)
        if level:
            query = query.where(QuestionBankItem.level == level)
        if difficulty:
            query = query.where(QuestionBankItem.difficulty == difficulty)
        if tags:
            query = query.where(QuestionBankItem.tags.contains(tags))
        if search:
            pattern = f"%{search}%"
            query = query.where(
                or_(
                    QuestionBankItem.subject.ilike(pattern),
                    QuestionBankItem.question_type.ilike(pattern),
                    cast(QuestionBankItem.question_data, String).ilike(pattern),
                )
            )

        query = query.order_by(QuestionBankItem.id.asc())
        if cursor:
            last_id, _ = decode_cursor(cursor)
            query = query.where(QuestionBankItem.id > last_id)

        return await self._paginate_scalars(query, limit=limit)

    async def list_generation_candidates(
        self,
        *,
        school_id: uuid.UUID,
        subject: str,
        level: str | None,
        difficulty: str,
    ) -> list[QuestionBankItem]:
        query = select(QuestionBankItem).where(
            QuestionBankItem.school_id == school_id,
            QuestionBankItem.subject == subject,
            QuestionBankItem.difficulty == difficulty,
            QuestionBankItem.is_archived.is_(False),
        )
        if level is not None:
            query = query.where(QuestionBankItem.level == level)

        result = await self.db.execute(query.order_by(QuestionBankItem.id.asc()))
        return list(result.scalars().all())

    async def increment_usage_counts(
        self,
        item_ids: list[uuid.UUID],
    ) -> None:
        if not item_ids:
            return
        await self.db.execute(
            update(QuestionBankItem)
            .where(QuestionBankItem.id.in_(item_ids))
            .values(usage_count=QuestionBankItem.usage_count + 1)
        )
        await self.db.flush()

    async def get_question_stats(
        self,
        *,
        school_id: uuid.UUID,
    ) -> list[dict[str, Any]]:
        result = await self.db.execute(
            select(
                QuestionBankItem.subject,
                QuestionBankItem.difficulty,
                func.count(QuestionBankItem.id).label("question_count"),
                func.coalesce(func.sum(QuestionBankItem.usage_count), 0).label(
                    "total_usage"
                ),
            )
            .where(
                QuestionBankItem.school_id == school_id,
                QuestionBankItem.is_archived.is_(False),
            )
            .group_by(QuestionBankItem.subject, QuestionBankItem.difficulty)
            .order_by(QuestionBankItem.subject.asc(), QuestionBankItem.difficulty.asc())
        )
        return [
            {
                "subject": subject,
                "difficulty": difficulty,
                "question_count": int(question_count or 0),
                "total_usage": int(total_usage or 0),
            }
            for subject, difficulty, question_count, total_usage in result.all()
        ]
