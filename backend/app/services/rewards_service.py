"""Service layer for student rewards and gamification."""

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
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.permissions import ADM, DIR, PAR, STD, SUP, SYS, TCH
from app.core.unit_of_work import UnitOfWork
from app.models.rewards import (
    CriteriaType,
    EventType,
    RewardBadge,
    RewardEvent,
    StudentReward,
)
from app.repositories.rewards import RewardsRepository
from app.schemas.rewards import (
    AwardRewardResponse,
    BadgeCreateRequest,
    BadgeResponse,
    LeaderboardEntry,
    RewardEventResponse,
    StudentRewardResponse,
)

LEVEL_THRESHOLDS: dict[int, int] = {
    1: 0,
    2: 100,
    3: 300,
    4: 600,
    5: 1000,
    6: 1500,
    7: 2100,
    8: 2800,
    9: 3600,
    10: 4500,
}
ADMIN_ROLES = {ADM, DIR, SUP, SYS}


def _iso(value: datetime | None) -> str | None:
    return value.astimezone(UTC).isoformat() if value is not None else None


def _normalize_event_type(raw: str) -> str:
    cleaned = raw.strip().lower()
    allowed = {item.value for item in EventType}
    if cleaned not in allowed:
        raise ValidationError(
            "Unsupported reward event type",
            error_code="ERR-REWARD-422",
            details={"allowed": sorted(allowed), "received": raw},
        )
    return cleaned


def _normalize_source_type(raw: str | None) -> str | None:
    if raw is None:
        return None
    cleaned = raw.strip().lower()
    allowed = {"content", "quiz", "game", "coloring", "system"}
    if cleaned not in allowed:
        raise ValidationError(
            "Unsupported reward source type",
            error_code="ERR-REWARD-422",
            details={"allowed": sorted(allowed), "received": raw},
        )
    return cleaned


def _normalize_criteria_type(raw: str) -> str:
    cleaned = raw.strip().lower()
    allowed = {item.value for item in CriteriaType}
    if cleaned not in allowed:
        raise ValidationError(
            "Unsupported reward badge criteria type",
            error_code="ERR-REWARD-422",
            details={"allowed": sorted(allowed), "received": raw},
        )
    return cleaned


def _normalize_badge_code(code: str) -> str:
    cleaned = code.strip().lower().replace(" ", "_")
    if not cleaned:
        raise ValidationError(
            "Badge code is required",
            error_code="ERR-REWARD-422",
        )
    return cleaned


def _level_from_xp(xp: int) -> int:
    level = 1
    for candidate_level, threshold in LEVEL_THRESHOLDS.items():
        if xp >= threshold:
            level = candidate_level
    return level


def _level_progress(xp: int) -> float:
    level = _level_from_xp(xp)
    current_threshold = LEVEL_THRESHOLDS[level]
    next_level = level + 1
    if next_level not in LEVEL_THRESHOLDS:
        return 100.0
    next_threshold = LEVEL_THRESHOLDS[next_level]
    progress = ((xp - current_threshold) / (next_threshold - current_threshold)) * 100
    return round(max(0.0, min(progress, 100.0)), 1)


def _metadata_number(metadata: dict[str, Any] | None, *keys: str) -> float | None:
    if metadata is None:
        return None
    for key in keys:
        raw = metadata.get(key)
        if isinstance(raw, bool):
            continue
        if isinstance(raw, (int, float)):
            return float(raw)
        if isinstance(raw, str):
            try:
                return float(raw)
            except ValueError:
                continue
    return None


class RewardsService:
    """Business logic for student rewards, events, badges, and leaderboards."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = RewardsRepository(db)

    def _badge_to_response(self, badge: RewardBadge) -> dict[str, Any]:
        return BadgeResponse(
            id=str(badge.id),
            code=badge.code,
            title_fr=badge.title_fr,
            title_ar=badge.title_ar,
            title_en=badge.title_en,
            description_fr=badge.description_fr,
            description_ar=badge.description_ar,
            description_en=badge.description_en,
            icon=badge.icon,
            criteria_type=badge.criteria_type,
            criteria_value=badge.criteria_value,
            display_order=badge.display_order,
            is_active=badge.is_active,
            created_at=_iso(badge.created_at) or "",
        ).model_dump()

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

    def _award_to_response(
        self,
        reward: StudentReward,
        newly_earned_badges: list[RewardBadge],
    ) -> dict[str, Any]:
        payload = self._reward_to_response(reward)
        payload["newly_earned_badges"] = [
            BadgeResponse.model_validate(self._badge_to_response(badge))
            for badge in newly_earned_badges
        ]
        return AwardRewardResponse.model_validate(payload).model_dump()

    def _event_to_response(self, event: RewardEvent) -> dict[str, Any]:
        return RewardEventResponse(
            id=str(event.id),
            event_type=event.event_type,
            stars_earned=event.stars_earned,
            xp_earned=event.xp_earned,
            source_type=event.source_type,
            source_id=str(event.source_id) if event.source_id is not None else None,
            created_at=_iso(event.created_at) or "",
        ).model_dump()

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
            if not enrolled:
                raise NotFoundError("Student not found", error_code="ERR-REWARD-404")
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
            if not enrolled:
                raise NotFoundError("Student not found", error_code="ERR-REWARD-404")
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
            if not enrolled:
                raise NotFoundError("Class not found", error_code="ERR-REWARD-404")
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
            if not enrolled:
                raise NotFoundError("Class not found", error_code="ERR-REWARD-404")
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

    def _update_streak(
        self,
        reward: StudentReward,
        *,
        now: datetime,
    ) -> None:
        last_activity = (
            reward.last_activity_at.astimezone(UTC) if reward.last_activity_at else None
        )
        if last_activity is None:
            reward.streak_days = 1
        else:
            today = now.date()
            if last_activity.date() == today:
                return
            if last_activity.date() == today - timedelta(days=1):
                reward.streak_days += 1
            else:
                reward.streak_days = 1
        reward.longest_streak = max(reward.streak_days, reward.longest_streak)

    def _badge_is_earned(
        self,
        *,
        badge: RewardBadge,
        reward: StudentReward,
        events: list[RewardEvent],
    ) -> bool:
        if badge.criteria_type == CriteriaType.STARS_TOTAL.value:
            return reward.stars >= badge.criteria_value

        if badge.criteria_type == CriteriaType.STREAK_DAYS.value:
            return reward.streak_days >= badge.criteria_value

        if badge.criteria_type == CriteriaType.CONTENT_COMPLETED.value:
            completed = sum(
                1
                for event in events
                if event.event_type == EventType.CONTENT_COMPLETED.value
            )
            return completed >= badge.criteria_value

        if badge.criteria_type == CriteriaType.QUIZ_SCORE.value:
            perfect_quizzes = 0
            for event in events:
                if event.event_type != EventType.QUIZ_PASSED.value:
                    continue
                score = _metadata_number(
                    event.event_metadata,
                    "score_percent",
                    "score",
                    "percent",
                )
                if score is not None and score >= 100:
                    perfect_quizzes += 1
            return perfect_quizzes >= badge.criteria_value

        if badge.criteria_type == CriteriaType.GAMES_WON.value:
            wins = sum(
                1 for event in events if event.event_type == EventType.GAME_WON.value
            )
            return wins >= badge.criteria_value

        if badge.criteria_type == CriteriaType.COLORING_SAVED.value:
            saved = sum(
                1
                for event in events
                if event.event_type == EventType.COLORING_SAVED.value
            )
            return saved >= badge.criteria_value

        if badge.criteria_type == CriteriaType.CONTENT_TYPES.value:
            content_types: set[str] = set()
            for event in events:
                derived_type: str | None = None
                if isinstance(event.event_metadata, dict):
                    raw = event.event_metadata.get("content_type")
                    if isinstance(raw, str) and raw.strip():
                        derived_type = raw.strip().lower()
                if derived_type is None and event.source_type:
                    derived_type = event.source_type
                if derived_type:
                    content_types.add(derived_type)
            return len(content_types) >= badge.criteria_value

        return False

    async def award(
        self,
        *,
        student_id: uuid.UUID,
        event_type: str,
        stars: int,
        xp: int,
        source_type: str | None,
        source_id: uuid.UUID | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
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
                event_metadata=dict(metadata) if metadata is not None else None,
            )

            reward.stars += stars
            reward.xp += xp
            reward.level = _level_from_xp(reward.xp)
            self._update_streak(reward, now=now)
            reward.last_activity_at = now

            active_badges = await repo.list_badges(active_only=True)
            earned_codes = list(reward.badges or [])
            events = await repo.list_reward_events_for_badges(student_id=student_id)
            newly_earned_badges: list[RewardBadge] = []
            for badge in active_badges:
                if badge.code in earned_codes:
                    continue
                if self._badge_is_earned(badge=badge, reward=reward, events=events):
                    earned_codes.append(badge.code)
                    newly_earned_badges.append(badge)

            reward.badges = earned_codes
            await repo.save_student_reward(reward)
            await uow.commit()
            return self._award_to_response(reward, newly_earned_badges)

    async def get_student_rewards(
        self,
        *,
        student_id: uuid.UUID,
    ) -> dict[str, Any]:
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

    async def get_event_history(
        self,
        *,
        student_id: uuid.UUID,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        await self._get_student_or_404(student_id)
        events = await self.repo.list_reward_events(student_id=student_id, limit=limit)
        return [self._event_to_response(event) for event in events]

    async def list_badges(self) -> list[dict[str, Any]]:
        badges = await self.repo.list_badges(active_only=False)
        return [self._badge_to_response(badge) for badge in badges]

    async def create_badge(self, *, body: BadgeCreateRequest) -> dict[str, Any]:
        code = _normalize_badge_code(body.code)
        criteria_type = _normalize_criteria_type(body.criteria_type)
        existing = await self.repo.get_badge_by_code(code)
        if existing is not None:
            raise ConflictError(
                "Reward badge code already exists",
                error_code="ERR-REWARD-409",
                details={"code": code},
            )

        async with UnitOfWork(self.db) as uow:
            repo = RewardsRepository(uow.session)
            badge = await repo.create_badge(
                code=code,
                title_fr=body.title_fr,
                title_ar=body.title_ar,
                title_en=body.title_en,
                description_fr=body.description_fr,
                description_ar=body.description_ar,
                description_en=body.description_en,
                icon=body.icon,
                criteria_type=criteria_type,
                criteria_value=body.criteria_value,
                display_order=0,
                is_active=True,
            )
            await uow.commit()
            return self._badge_to_response(badge)
