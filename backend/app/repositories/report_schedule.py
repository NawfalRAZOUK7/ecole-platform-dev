"""Repository helpers for scheduled report generation."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select

from app.models.iam import Membership, User
from app.models.reporting import ReportSchedule
from app.repositories.base import BaseRepository


class ReportScheduleRepository(BaseRepository):
    """Persistence helpers for report schedules and recipient resolution."""

    async def create_schedule(self, schedule: ReportSchedule) -> ReportSchedule:
        self.db.add(schedule)
        await self.db.flush()
        return schedule

    async def save_schedule(self, schedule: ReportSchedule) -> ReportSchedule:
        self.db.add(schedule)
        await self.db.flush()
        return schedule

    async def get_schedule(self, schedule_id: uuid.UUID) -> ReportSchedule | None:
        result = await self.db.execute(
            select(ReportSchedule).where(ReportSchedule.id == schedule_id)
        )
        return result.scalar_one_or_none()

    async def list_schedules(self, *, school_id: uuid.UUID) -> list[ReportSchedule]:
        result = await self.db.execute(
            select(ReportSchedule)
            .where(ReportSchedule.school_id == school_id)
            .order_by(ReportSchedule.created_at.desc(), ReportSchedule.id.desc())
        )
        return list(result.scalars().all())

    async def list_due_schedules(
        self,
        *,
        now: datetime,
        limit: int = 100,
    ) -> list[ReportSchedule]:
        result = await self.db.execute(
            select(ReportSchedule)
            .where(
                ReportSchedule.enabled.is_(True),
                ReportSchedule.next_run_at.is_not(None),
                ReportSchedule.next_run_at <= now,
            )
            .order_by(ReportSchedule.next_run_at.asc(), ReportSchedule.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_active_role(
        self,
        *,
        user_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> str | None:
        result = await self.db.execute(
            select(Membership.role_code)
            .where(
                Membership.user_id == user_id,
                Membership.school_id == school_id,
                Membership.status == "active",
            )
            .order_by(Membership.created_at.asc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_recipient_users(
        self,
        *,
        school_id: uuid.UUID,
        roles: list[str],
    ) -> list[User]:
        if not roles:
            return []
        result = await self.db.execute(
            select(User)
            .join(Membership, Membership.user_id == User.id)
            .where(
                User.school_id == school_id,
                User.email.is_not(None),
                Membership.school_id == school_id,
                Membership.status == "active",
                Membership.role_code.in_(roles),
            )
            .distinct()
            .order_by(User.full_name.asc(), User.email.asc())
        )
        return list(result.scalars().all())
