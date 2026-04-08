"""Repository helpers for the micro-school domain."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.models.iam import Membership, User
from app.models.micro_school import (
    MicroEnrollment,
    MicroGroup,
    MicroPayment,
    MicroProgressLog,
    MicroResource,
    MicroSchool,
)
from app.repositories.base import BaseRepository


class MicroSchoolRepository(BaseRepository):
    """Data access for micro-schools, cohorts, payments, and progress logs."""

    async def get_user(self, user_id: uuid.UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_membership_role(self, user_id: uuid.UUID) -> str | None:
        result = await self.db.execute(
            select(Membership.role_code)
            .where(
                Membership.user_id == user_id,
                Membership.status == "active",
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_micro_school(
        self,
        micro_school_id: uuid.UUID,
        *,
        school_id: uuid.UUID | None = None,
        include_groups: bool = False,
        include_payments: bool = False,
    ) -> MicroSchool | None:
        query = select(MicroSchool).where(MicroSchool.id == micro_school_id)
        if school_id is not None:
            query = query.join(User, User.id == MicroSchool.educator_id).where(
                User.school_id == school_id
            )
        if include_groups:
            query = query.options(selectinload(MicroSchool.groups))
        if include_payments:
            query = query.options(selectinload(MicroSchool.payments))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_micro_schools(
        self,
        *,
        school_id: uuid.UUID | None = None,
        educator_id: uuid.UUID | None = None,
        city: str | None = None,
        status: str | None = None,
    ) -> list[MicroSchool]:
        query = select(MicroSchool)
        if school_id is not None:
            query = query.join(User, User.id == MicroSchool.educator_id).where(
                User.school_id == school_id
            )
        if educator_id is not None:
            query = query.where(MicroSchool.educator_id == educator_id)
        if city:
            query = query.where(MicroSchool.city.ilike(city))
        if status:
            query = query.where(MicroSchool.status == status)
        result = await self.db.execute(
            query.order_by(MicroSchool.created_at.desc(), MicroSchool.id.asc())
        )
        return list(result.scalars().all())

    async def create_micro_school(self, micro_school: MicroSchool) -> MicroSchool:
        self.db.add(micro_school)
        await self.db.flush()
        return micro_school

    async def save_micro_school(self, micro_school: MicroSchool) -> MicroSchool:
        self.db.add(micro_school)
        await self.db.flush()
        return micro_school

    async def delete_micro_school(self, micro_school: MicroSchool) -> None:
        await self.db.delete(micro_school)
        await self.db.flush()

    async def get_micro_group(
        self,
        micro_group_id: uuid.UUID,
        *,
        school_id: uuid.UUID | None = None,
        include_school: bool = False,
        include_enrollments: bool = False,
    ) -> MicroGroup | None:
        query = select(MicroGroup).where(MicroGroup.id == micro_group_id)
        if school_id is not None:
            query = (
                query.join(MicroSchool, MicroSchool.id == MicroGroup.micro_school_id)
                .join(User, User.id == MicroSchool.educator_id)
                .where(User.school_id == school_id)
            )
        if include_school:
            query = query.options(selectinload(MicroGroup.micro_school))
        if include_enrollments:
            query = query.options(selectinload(MicroGroup.enrollments))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_micro_groups(
        self,
        *,
        school_id: uuid.UUID | None = None,
        micro_school_id: uuid.UUID | None = None,
    ) -> list[MicroGroup]:
        query = select(MicroGroup)
        if school_id is not None:
            query = (
                query.join(MicroSchool, MicroSchool.id == MicroGroup.micro_school_id)
                .join(User, User.id == MicroSchool.educator_id)
                .where(User.school_id == school_id)
            )
        if micro_school_id is not None:
            query = query.where(MicroGroup.micro_school_id == micro_school_id)
        result = await self.db.execute(
            query.order_by(MicroGroup.created_at.asc(), MicroGroup.id.asc())
        )
        return list(result.scalars().all())

    async def create_micro_group(self, micro_group: MicroGroup) -> MicroGroup:
        self.db.add(micro_group)
        await self.db.flush()
        return micro_group

    async def save_micro_group(self, micro_group: MicroGroup) -> MicroGroup:
        self.db.add(micro_group)
        await self.db.flush()
        return micro_group

    async def delete_micro_group(self, micro_group: MicroGroup) -> None:
        await self.db.delete(micro_group)
        await self.db.flush()

    async def get_micro_enrollment(
        self,
        micro_enrollment_id: uuid.UUID,
        *,
        school_id: uuid.UUID | None = None,
        include_group: bool = False,
        include_payments: bool = False,
        include_progress_logs: bool = False,
    ) -> MicroEnrollment | None:
        query = select(MicroEnrollment).where(MicroEnrollment.id == micro_enrollment_id)
        if school_id is not None:
            query = (
                query.join(MicroGroup, MicroGroup.id == MicroEnrollment.micro_group_id)
                .join(MicroSchool, MicroSchool.id == MicroGroup.micro_school_id)
                .join(User, User.id == MicroSchool.educator_id)
                .where(User.school_id == school_id)
            )
        if include_group:
            query = query.options(
                selectinload(MicroEnrollment.micro_group).selectinload(
                    MicroGroup.micro_school
                )
            )
        if include_payments:
            query = query.options(selectinload(MicroEnrollment.payments))
        if include_progress_logs:
            query = query.options(selectinload(MicroEnrollment.progress_logs))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_micro_enrollments(
        self,
        *,
        school_id: uuid.UUID | None = None,
        micro_group_id: uuid.UUID | None = None,
        parent_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> list[MicroEnrollment]:
        query = select(MicroEnrollment)
        if school_id is not None:
            query = (
                query.join(MicroGroup, MicroGroup.id == MicroEnrollment.micro_group_id)
                .join(MicroSchool, MicroSchool.id == MicroGroup.micro_school_id)
                .join(User, User.id == MicroSchool.educator_id)
                .where(User.school_id == school_id)
            )
        if micro_group_id is not None:
            query = query.where(MicroEnrollment.micro_group_id == micro_group_id)
        if parent_id is not None:
            query = query.where(MicroEnrollment.parent_id == parent_id)
        if status:
            query = query.where(MicroEnrollment.status == status)
        result = await self.db.execute(
            query.order_by(
                MicroEnrollment.enrolled_at.desc(),
                MicroEnrollment.id.asc(),
            )
        )
        return list(result.scalars().all())

    async def create_micro_enrollment(
        self,
        micro_enrollment: MicroEnrollment,
    ) -> MicroEnrollment:
        self.db.add(micro_enrollment)
        await self.db.flush()
        return micro_enrollment

    async def save_micro_enrollment(
        self,
        micro_enrollment: MicroEnrollment,
    ) -> MicroEnrollment:
        self.db.add(micro_enrollment)
        await self.db.flush()
        return micro_enrollment

    async def delete_micro_enrollment(self, micro_enrollment: MicroEnrollment) -> None:
        await self.db.delete(micro_enrollment)
        await self.db.flush()

    async def get_micro_payment(
        self,
        micro_payment_id: uuid.UUID,
        *,
        school_id: uuid.UUID | None = None,
        include_school: bool = False,
        include_enrollment: bool = False,
    ) -> MicroPayment | None:
        query = select(MicroPayment).where(MicroPayment.id == micro_payment_id)
        if school_id is not None:
            query = (
                query.join(MicroSchool, MicroSchool.id == MicroPayment.micro_school_id)
                .join(User, User.id == MicroSchool.educator_id)
                .where(User.school_id == school_id)
            )
        if include_school:
            query = query.options(selectinload(MicroPayment.micro_school))
        if include_enrollment:
            query = query.options(selectinload(MicroPayment.child_enrollment))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_micro_payments(
        self,
        *,
        school_id: uuid.UUID | None = None,
        micro_school_id: uuid.UUID | None = None,
        parent_id: uuid.UUID | None = None,
        child_enrollment_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> list[MicroPayment]:
        query = select(MicroPayment)
        if school_id is not None:
            query = (
                query.join(MicroSchool, MicroSchool.id == MicroPayment.micro_school_id)
                .join(User, User.id == MicroSchool.educator_id)
                .where(User.school_id == school_id)
            )
        if micro_school_id is not None:
            query = query.where(MicroPayment.micro_school_id == micro_school_id)
        if parent_id is not None:
            query = query.where(MicroPayment.parent_id == parent_id)
        if child_enrollment_id is not None:
            query = query.where(MicroPayment.child_enrollment_id == child_enrollment_id)
        if status:
            query = query.where(MicroPayment.status == status)
        result = await self.db.execute(
            query.order_by(MicroPayment.period_start.desc(), MicroPayment.id.asc())
        )
        return list(result.scalars().all())

    async def create_micro_payment(self, micro_payment: MicroPayment) -> MicroPayment:
        self.db.add(micro_payment)
        await self.db.flush()
        return micro_payment

    async def save_micro_payment(self, micro_payment: MicroPayment) -> MicroPayment:
        self.db.add(micro_payment)
        await self.db.flush()
        return micro_payment

    async def delete_micro_payment(self, micro_payment: MicroPayment) -> None:
        await self.db.delete(micro_payment)
        await self.db.flush()

    async def get_micro_resource(
        self, micro_resource_id: uuid.UUID
    ) -> MicroResource | None:
        result = await self.db.execute(
            select(MicroResource).where(MicroResource.id == micro_resource_id)
        )
        return result.scalar_one_or_none()

    async def list_micro_resources(
        self,
        *,
        resource_type: str | None = None,
        language: str | None = None,
        age_group: str | None = None,
        is_premium: bool | None = None,
    ) -> list[MicroResource]:
        query = select(MicroResource)
        if resource_type:
            query = query.where(MicroResource.resource_type == resource_type)
        if language:
            query = query.where(MicroResource.language == language)
        if age_group:
            query = query.where(MicroResource.age_group == age_group)
        if is_premium is not None:
            query = query.where(MicroResource.is_premium == is_premium)
        result = await self.db.execute(
            query.order_by(MicroResource.created_at.desc(), MicroResource.id.asc())
        )
        return list(result.scalars().all())

    async def create_micro_resource(
        self, micro_resource: MicroResource
    ) -> MicroResource:
        self.db.add(micro_resource)
        await self.db.flush()
        return micro_resource

    async def save_micro_resource(self, micro_resource: MicroResource) -> MicroResource:
        self.db.add(micro_resource)
        await self.db.flush()
        return micro_resource

    async def delete_micro_resource(self, micro_resource: MicroResource) -> None:
        await self.db.delete(micro_resource)
        await self.db.flush()

    async def get_micro_progress_log(
        self,
        micro_progress_log_id: uuid.UUID,
        *,
        school_id: uuid.UUID | None = None,
        include_enrollment: bool = False,
    ) -> MicroProgressLog | None:
        query = select(MicroProgressLog).where(
            MicroProgressLog.id == micro_progress_log_id
        )
        if school_id is not None:
            query = (
                query.join(
                    MicroEnrollment,
                    MicroEnrollment.id == MicroProgressLog.micro_enrollment_id,
                )
                .join(MicroGroup, MicroGroup.id == MicroEnrollment.micro_group_id)
                .join(MicroSchool, MicroSchool.id == MicroGroup.micro_school_id)
                .join(User, User.id == MicroSchool.educator_id)
                .where(User.school_id == school_id)
            )
        if include_enrollment:
            query = query.options(
                selectinload(MicroProgressLog.micro_enrollment)
                .selectinload(MicroEnrollment.micro_group)
                .selectinload(MicroGroup.micro_school)
            )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_micro_progress_logs(
        self,
        *,
        school_id: uuid.UUID | None = None,
        micro_enrollment_id: uuid.UUID | None = None,
        educator_id: uuid.UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[MicroProgressLog]:
        query = select(MicroProgressLog)
        if school_id is not None:
            query = (
                query.join(
                    MicroEnrollment,
                    MicroEnrollment.id == MicroProgressLog.micro_enrollment_id,
                )
                .join(MicroGroup, MicroGroup.id == MicroEnrollment.micro_group_id)
                .join(MicroSchool, MicroSchool.id == MicroGroup.micro_school_id)
                .join(User, User.id == MicroSchool.educator_id)
                .where(User.school_id == school_id)
            )
        if micro_enrollment_id is not None:
            query = query.where(
                MicroProgressLog.micro_enrollment_id == micro_enrollment_id
            )
        if educator_id is not None:
            query = query.where(MicroProgressLog.educator_id == educator_id)
        if date_from is not None:
            query = query.where(MicroProgressLog.date >= date_from)
        if date_to is not None:
            query = query.where(MicroProgressLog.date <= date_to)
        result = await self.db.execute(
            query.order_by(MicroProgressLog.date.desc(), MicroProgressLog.id.asc())
        )
        return list(result.scalars().all())

    async def create_micro_progress_log(
        self,
        micro_progress_log: MicroProgressLog,
    ) -> MicroProgressLog:
        self.db.add(micro_progress_log)
        await self.db.flush()
        return micro_progress_log

    async def save_micro_progress_log(
        self,
        micro_progress_log: MicroProgressLog,
    ) -> MicroProgressLog:
        self.db.add(micro_progress_log)
        await self.db.flush()
        return micro_progress_log

    async def delete_micro_progress_log(
        self, micro_progress_log: MicroProgressLog
    ) -> None:
        await self.db.delete(micro_progress_log)
        await self.db.flush()

    async def parent_has_school_access(
        self,
        *,
        parent_id: uuid.UUID,
        micro_school_id: uuid.UUID,
        school_id: uuid.UUID | None = None,
    ) -> bool:
        query = (
            select(func.count(MicroEnrollment.id))
            .select_from(MicroEnrollment)
            .join(MicroGroup, MicroGroup.id == MicroEnrollment.micro_group_id)
            .where(
                MicroGroup.micro_school_id == micro_school_id,
                MicroEnrollment.parent_id == parent_id,
            )
        )
        if school_id is not None:
            query = query.join(User, User.id == MicroEnrollment.parent_id).where(
                User.school_id == school_id
            )
        result = await self.db.execute(query)
        return (result.scalar_one() or 0) > 0

    async def get_micro_school_for_enrollment(
        self,
        micro_enrollment_id: uuid.UUID,
        *,
        school_id: uuid.UUID | None = None,
    ) -> MicroSchool | None:
        query = (
            select(MicroSchool)
            .join(MicroGroup, MicroGroup.micro_school_id == MicroSchool.id)
            .join(MicroEnrollment, MicroEnrollment.micro_group_id == MicroGroup.id)
            .where(MicroEnrollment.id == micro_enrollment_id)
        )
        if school_id is not None:
            query = query.join(User, User.id == MicroSchool.educator_id).where(
                User.school_id == school_id
            )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()


__all__ = ["MicroSchoolRepository"]
