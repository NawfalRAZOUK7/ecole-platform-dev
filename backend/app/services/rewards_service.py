"""Service layer for the kid-facing rewards system."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    AuthContext,
    verify_parent_child_ownership,
    verify_school_boundary,
    verify_teacher_assignment,
)
from app.core.exceptions import NotFoundError, ValidationError
from app.core.permissions import ADM, DIR, PAR, STD, SUP, SYS, TCH
from app.core.unit_of_work import UnitOfWork
from app.models.rewards import StudentReward
from app.repositories.rewards import RewardsRepository
from app.schemas.rewards import (
    AwardRewardResponse,
    LeaderboardEntry,
    StudentRewardResponse,
)

ADMIN_ROLES = {ADM, DIR, SUP, SYS}
ALLOWED_SOURCE_TYPES = {"content", "quiz", "game", "coloring", "login"}


def _iso(value: datetime | None) -> str | None:
    return value.astimezone(UTC).isoformat() if value is not None else None


def _normalize_event_type(raw: str) -> str:
    cleaned = raw.strip().lower()
    if not cleaned:
        raise ValidationError(
            "Reward event type is required",
            error_code="ERR-REWARD-422",
        )
    return cleaned


def _normalize_source_type(raw: str | None) -> str | None:
    if raw is None:
        return None
    cleaned = raw.strip().lower()
    if cleaned not in ALLOWED_SOURCE_TYPES:
        raise ValidationError(
            "Unsupported reward source type",
            error_code="ERR-REWARD-422",
            details={"allowed": sorted(ALLOWED_SOURCE_TYPES), "received": raw},
        )
    return cleaned


def _xp_threshold_for_level(level: int) -> int:
    if level <= 1:
        return 0
    return 50 * (level - 1) * level


def _level_from_xp(xp: int) -> int:
    level = 1
    while _xp_threshold_for_level(level + 1) <= xp:
        level += 1
    return level


def _level_progress(xp: int) -> float:
    level = _level_from_xp(xp)
    current_threshold = _xp_threshold_for_level(level)
    next_threshold = _xp_threshold_for_level(level + 1)
    if next_threshold <= current_threshold:
        return 100.0
    progress = ((xp - current_threshold) / (next_threshold - current_threshold)) * 100
    return round(max(0.0, min(progress, 100.0)), 1)


class RewardsService:
    """Business logic for student rewards and leaderboards."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = RewardsRepository(db)

    def _reward_to_response(self, reward: StudentReward) -> dict[str, Any]:
        return StudentRewardResponse(
            id=str(reward.id),
            student_id=str(reward.student_id),
            stars=reward.stars,
            xp=reward.xp,
            level=reward.level,
            streak_days=reward.streak_days,
            longest_streak=reward.longest_streak,
            badges=list(reward.badges or []),
            last_activity_at=_iso(reward.last_activity_at),
            level_progress=_level_progress(reward.xp),
        ).model_dump()

    def _award_to_response(self, reward: StudentReward) -> dict[str, Any]:
        payload = self._reward_to_response(reward)
        payload["newly_earned_badges"] = []
        return AwardRewardResponse.model_validate(payload).model_dump()

    async def _get_student_or_404(self, student_id: uuid.UUID):
        student = await self.repo.get_user(student_id)
        if student is None:
            raise NotFoundError("Student not found", error_code="ERR-REWARD-404")
        return student

    async def _get_class_school_id_or_404(self, class_id: uuid.UUID) -> uuid.UUID:
        school_id = await self.repo.get_class_school_id(class_id)
        if school_id is None:
            raise NotFoundError("Class not found", error_code="ERR-REWARD-404")
        return school_id

    async def verify_student_view_access(
        self,
        *,
        student_id: uuid.UUID,
        auth: AuthContext,
    ) -> None:
        student = await self._get_student_or_404(student_id)
        verify_school_boundary(student.school_id, auth)

        if auth.role in ADMIN_ROLES:
            return

        if auth.role == STD and auth.user_id == student_id:
            return

        if auth.role == TCH:
            teacher_class_ids = await self.repo.list_teacher_class_ids(
                teacher_id=auth.user_id,
                school_id=auth.school_id,
            )
            enrolled = await self.repo.student_is_enrolled_in_classes(
                student_id=student_id,
                school_id=auth.school_id,
                class_ids=teacher_class_ids,
            )
            if enrolled:
                return

        if auth.role == PAR:
            child_ids = await self.repo.list_parent_child_ids(
                parent_id=auth.user_id,
                school_id=auth.school_id,
            )
            verify_parent_child_ownership(student_id, child_ids)
            return

        raise NotFoundError("Student not found", error_code="ERR-REWARD-404")

    async def verify_student_award_access(
        self,
        *,
        student_id: uuid.UUID,
        auth: AuthContext,
    ) -> None:
        student = await self._get_student_or_404(student_id)
        verify_school_boundary(student.school_id, auth)

        if auth.role in ADMIN_ROLES:
            return

        if auth.role == STD and auth.user_id == student_id:
            return

        if auth.role == TCH:
            teacher_class_ids = await self.repo.list_teacher_class_ids(
                teacher_id=auth.user_id,
                school_id=auth.school_id,
            )
            enrolled = await self.repo.student_is_enrolled_in_classes(
                student_id=student_id,
                school_id=auth.school_id,
                class_ids=teacher_class_ids,
            )
            if enrolled:
                return

        raise NotFoundError("Student not found", error_code="ERR-REWARD-404")

    async def verify_class_access(
        self,
        *,
        class_id: uuid.UUID,
        auth: AuthContext,
    ) -> None:
        class_school_id = await self._get_class_school_id_or_404(class_id)
        verify_school_boundary(class_school_id, auth)

        if auth.role in ADMIN_ROLES:
            return

        if auth.role == TCH:
            teacher_class_ids = await self.repo.list_teacher_class_ids(
                teacher_id=auth.user_id,
                school_id=auth.school_id,
            )
            verify_teacher_assignment(class_id, teacher_class_ids)
            return

        if auth.role == STD:
            enrolled = await self.repo.student_is_enrolled_in_class(
                student_id=auth.user_id,
                school_id=auth.school_id,
                class_id=class_id,
            )
            if enrolled:
                return

        if auth.role == PAR:
            child_ids = await self.repo.list_parent_child_ids(
                parent_id=auth.user_id,
                school_id=auth.school_id,
            )
            enrolled = await self.repo.any_students_enrolled_in_class(
                student_ids=child_ids,
                school_id=auth.school_id,
                class_id=class_id,
            )
            if enrolled:
                return

        raise NotFoundError("Class not found", error_code="ERR-REWARD-404")

    async def _get_or_create_reward_with_repo(
        self,
        repo: RewardsRepository,
        *,
        student_id: uuid.UUID,
    ) -> StudentReward:
        reward = await repo.get_student_reward(student_id)
        if reward is not None:
            return reward
        return await repo.create_student_reward(
            student_id=student_id,
            stars=0,
            xp=0,
            level=1,
            streak_days=0,
            longest_streak=0,
            badges=[],
        )

    def _update_streak(self, reward: StudentReward, *, now: datetime) -> None:
        last_activity = (
            reward.last_activity_at.astimezone(UTC) if reward.last_activity_at else None
        )
        if last_activity is None:
            reward.streak_days = 1
        else:
            today = now.date()
            if last_activity.date() == today:
                pass  # Same day — no change to streak
            elif last_activity.date() == today - timedelta(days=1):
                reward.streak_days += 1
            else:
                reward.streak_days = 1

        # Keep longest_streak as the all-time high
        if reward.streak_days > reward.longest_streak:
            reward.longest_streak = reward.streak_days

    async def award(
        self,
        *,
        student_id: uuid.UUID,
        event_type: str,
        stars: int,
        xp: int,
        source_type: str | None,
        source_id: uuid.UUID | None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        del metadata

        await self._get_student_or_404(student_id)
        normalized_event_type = _normalize_event_type(event_type)
        normalized_source_type = _normalize_source_type(source_type)
        now = datetime.now(UTC)

        async with UnitOfWork(self.db) as uow:
            repo = RewardsRepository(uow.session)
            reward = await self._get_or_create_reward_with_repo(
                repo,
                student_id=student_id,
            )

            await repo.create_reward_event(
                student_id=student_id,
                event_type=normalized_event_type,
                stars_earned=stars,
                xp_earned=xp,
                source_type=normalized_source_type,
                source_id=source_id,
            )

            reward.stars += stars
            reward.xp += xp
            reward.level = _level_from_xp(reward.xp)
            self._update_streak(reward, now=now)
            reward.last_activity_at = now

            await repo.save_student_reward(reward)
            await uow.commit()
            return self._award_to_response(reward)

    async def get_student_rewards(self, *, student_id: uuid.UUID) -> dict[str, Any]:
        await self._get_student_or_404(student_id)
        reward = await self.repo.get_student_reward(student_id)
        if reward is not None:
            return self._reward_to_response(reward)

        async with UnitOfWork(self.db) as uow:
            repo = RewardsRepository(uow.session)
            reward = await self._get_or_create_reward_with_repo(
                repo,
                student_id=student_id,
            )
            await uow.commit()
            return self._reward_to_response(reward)

    async def get_leaderboard(
        self,
        *,
        class_id: uuid.UUID,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        school_id = await self._get_class_school_id_or_404(class_id)
        rows = await self.repo.list_leaderboard_rows(
            class_id=class_id,
            school_id=school_id,
            limit=limit,
        )
        return [
            LeaderboardEntry(
                student_id=str(row["student_id"]),
                student_name=row["student_name"],
                stars=row["stars"],
                level=row["level"],
                rank=index,
            ).model_dump()
            for index, row in enumerate(rows, start=1)
        ]
