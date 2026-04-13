"""Repository helpers for rewards and gamification workflows."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import desc, distinct, func, select

from app.models.erp import Class, Enrollment, TeacherAssignment
from app.models.iam import ParentChildLink, User
from app.models.rewards import RewardBadge, RewardEvent, StudentReward
from app.repositories.base import BaseRepository


class RewardsRepository(BaseRepository):
    """Data access for rewards, badges, events, and leaderboard queries."""

    async def get_user(self, user_id: uuid.UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_student_reward(
        self,
        student_id: uuid.UUID,
    ) -> StudentReward | None:
        result = await self.db.execute(
            select(StudentReward).where(StudentReward.student_id == student_id)
        )
        return result.scalar_one_or_none()

    async def create_student_reward(self, **kwargs: Any) -> StudentReward:
        reward = StudentReward(**kwargs)
        self.db.add(reward)
        await self.db.flush()
        return reward

    async def save_student_reward(self, reward: StudentReward) -> StudentReward:
        self.db.add(reward)
        await self.db.flush()
        return reward

    async def create_reward_event(self, **kwargs: Any) -> RewardEvent:
        event = RewardEvent(**kwargs)
        self.db.add(event)
        await self.db.flush()
        return event

    async def list_reward_events(
        self,
        *,
        student_id: uuid.UUID,
        limit: int,
    ) -> list[RewardEvent]:
        result = await self.db.execute(
            select(RewardEvent)
            .where(RewardEvent.student_id == student_id)
            .order_by(RewardEvent.created_at.desc(), RewardEvent.id.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_reward_events_for_badges(
        self,
        *,
        student_id: uuid.UUID,
    ) -> list[RewardEvent]:
        result = await self.db.execute(
            select(RewardEvent)
            .where(RewardEvent.student_id == student_id)
            .order_by(RewardEvent.created_at.asc(), RewardEvent.id.asc())
        )
        return list(result.scalars().all())

    async def get_badge_by_code(self, code: str) -> RewardBadge | None:
        result = await self.db.execute(
            select(RewardBadge).where(RewardBadge.code == code)
        )
        return result.scalar_one_or_none()

    async def list_badges(self, *, active_only: bool = False) -> list[RewardBadge]:
        query = select(RewardBadge)
        if active_only:
            query = query.where(RewardBadge.is_active.is_(True))
        query = query.order_by(RewardBadge.display_order.asc(), RewardBadge.code.asc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_badge(self, **kwargs: Any) -> RewardBadge:
        badge = RewardBadge(**kwargs)
        self.db.add(badge)
        await self.db.flush()
        return badge

    async def get_class_school_id(self, class_id: uuid.UUID) -> uuid.UUID | None:
        result = await self.db.execute(
            select(Class.school_id).where(Class.id == class_id)
        )
        return result.scalar_one_or_none()

    async def list_parent_child_ids(
        self,
        *,
        parent_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> set[uuid.UUID]:
        result = await self.db.execute(
            select(ParentChildLink.child_user_id).where(
                ParentChildLink.parent_user_id == parent_id,
                ParentChildLink.school_id == school_id,
                ParentChildLink.status == "active",
            )
        )
        return set(result.scalars().all())

    async def list_teacher_class_ids(
        self,
        *,
        teacher_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> set[uuid.UUID]:
        result = await self.db.execute(
            select(TeacherAssignment.class_id).where(
                TeacherAssignment.teacher_id == teacher_id,
                TeacherAssignment.school_id == school_id,
            )
        )
        return set(result.scalars().all())

    async def student_is_enrolled_in_classes(
        self,
        *,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
        class_ids: set[uuid.UUID],
    ) -> bool:
        if not class_ids:
            return False
        result = await self.db.execute(
            select(Enrollment.class_id).where(
                Enrollment.student_id == student_id,
                Enrollment.school_id == school_id,
                Enrollment.status == "active",
                Enrollment.class_id.in_(class_ids),
            )
        )
        return result.scalar_one_or_none() is not None

    async def student_is_enrolled_in_class(
        self,
        *,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
        class_id: uuid.UUID,
    ) -> bool:
        result = await self.db.execute(
            select(Enrollment.class_id).where(
                Enrollment.student_id == student_id,
                Enrollment.school_id == school_id,
                Enrollment.class_id == class_id,
                Enrollment.status == "active",
            )
        )
        return result.scalar_one_or_none() is not None

    async def any_students_enrolled_in_class(
        self,
        *,
        student_ids: set[uuid.UUID],
        school_id: uuid.UUID,
        class_id: uuid.UUID,
    ) -> bool:
        if not student_ids:
            return False
        result = await self.db.execute(
            select(Enrollment.student_id).where(
                Enrollment.student_id.in_(student_ids),
                Enrollment.school_id == school_id,
                Enrollment.class_id == class_id,
                Enrollment.status == "active",
            )
        )
        return result.scalar_one_or_none() is not None

    async def list_leaderboard_rows(
        self,
        *,
        class_id: uuid.UUID,
        school_id: uuid.UUID,
        limit: int,
    ) -> list[dict[str, Any]]:
        active_students_subquery = (
            select(distinct(Enrollment.student_id).label("student_id"))
            .where(
                Enrollment.class_id == class_id,
                Enrollment.school_id == school_id,
                Enrollment.status == "active",
            )
            .subquery()
        )

        result = await self.db.execute(
            select(
                active_students_subquery.c.student_id,
                User.full_name,
                func.coalesce(StudentReward.stars, 0).label("stars"),
                func.coalesce(StudentReward.level, 1).label("level"),
            )
            .join(User, User.id == active_students_subquery.c.student_id)
            .outerjoin(
                StudentReward,
                StudentReward.student_id == active_students_subquery.c.student_id,
            )
            .order_by(
                desc("stars"),
                desc("level"),
                User.full_name.asc(),
                active_students_subquery.c.student_id.asc(),
            )
            .limit(limit)
        )

        return [
            {
                "student_id": row.student_id,
                "student_name": row.full_name,
                "stars": int(row.stars or 0),
                "level": int(row.level or 1),
            }
            for row in result
        ]
