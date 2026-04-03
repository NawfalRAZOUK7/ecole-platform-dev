"""Service layer for the micro-school domain."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import AuthContext
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.core.permissions import ADM, EDUCATOR, PAR, SUP, SYS, TCH
from app.core.unit_of_work import UnitOfWork
from app.domain.events.micro_school import (
    MicroEnrollmentCreated,
    MicroGroupCreated,
    MicroPaymentRecorded,
    MicroProgressLogged,
    MicroSchoolCreated,
)
from app.models.micro_school import (
    MicroEnrollment,
    MicroGroup,
    MicroPayment,
    MicroProgressLog,
    MicroResource,
    MicroSchool,
)
from app.repositories.micro_school import MicroSchoolRepository
from app.schemas.micro_school import (
    MicroEnrollmentCreateRequest,
    MicroEnrollmentResponse,
    MicroEnrollmentUpdateRequest,
    MicroGroupCreateRequest,
    MicroGroupResponse,
    MicroGroupUpdateRequest,
    MicroPaymentCreateRequest,
    MicroPaymentResponse,
    MicroPaymentUpdateRequest,
    MicroProgressLogCreateRequest,
    MicroProgressLogResponse,
    MicroProgressLogUpdateRequest,
    MicroResourceCreateRequest,
    MicroResourceResponse,
    MicroResourceUpdateRequest,
    MicroSchoolCreateRequest,
    MicroSchoolResponse,
    MicroSchoolUpdateRequest,
)
from app.services.audit import AuditService
from app.services.event_dispatcher import EventDispatcher

ADMIN_ROLES = {ADM, SUP, SYS}
EDUCATOR_ROLES = {EDUCATOR, TCH}
EDUCATOR_CAPABLE_ROLES = ADMIN_ROLES | EDUCATOR_ROLES


def _iso(value: datetime | None) -> str | None:
    return value.astimezone(timezone.utc).isoformat() if value is not None else None


class _MicroServiceBase:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = MicroSchoolRepository(db)
        self.audit = AuditService(db)
        self._dispatcher = EventDispatcher(db)

    def _is_admin(self, auth: AuthContext) -> bool:
        return auth.role in ADMIN_ROLES

    def _is_educator_actor(self, auth: AuthContext) -> bool:
        return auth.role in EDUCATOR_ROLES

    async def _validate_educator_actor(
        self,
        educator_id: uuid.UUID,
        auth: AuthContext,
    ) -> None:
        if self._is_admin(auth):
            return
        if auth.user_id != educator_id:
            raise AuthorizationError(
                "Cannot act on behalf of another educator",
                error_code="ERR-MICRO-403",
            )

    async def _ensure_educator_role(self, educator_id: uuid.UUID) -> None:
        user = await self.repo.get_user(educator_id)
        if user is None:
            raise NotFoundError("Educator not found", error_code="ERR-MICRO-404")
        role = await self.repo.get_membership_role(educator_id)
        if role not in EDUCATOR_CAPABLE_ROLES:
            raise ValidationError(
                "Target user must hold an educator-capable role",
                error_code="ERR-MICRO-422",
            )

    async def _get_school_or_404(
        self,
        micro_school_id: uuid.UUID,
        *,
        include_groups: bool = False,
        include_payments: bool = False,
    ) -> MicroSchool:
        school = await self.repo.get_micro_school(
            micro_school_id,
            include_groups=include_groups,
            include_payments=include_payments,
        )
        if school is None:
            raise NotFoundError("Micro-school not found", error_code="ERR-MICRO-404")
        return school

    async def _ensure_school_view_access(
        self,
        school: MicroSchool,
        auth: AuthContext,
    ) -> None:
        if self._is_admin(auth) or school.educator_id == auth.user_id:
            return
        if auth.role == PAR and await self.repo.parent_has_school_access(
            parent_id=auth.user_id,
            micro_school_id=school.id,
        ):
            return
        raise AuthorizationError(
            "You do not have access to this micro-school",
            error_code="ERR-MICRO-403",
        )

    async def _ensure_school_manage_access(
        self,
        school: MicroSchool,
        auth: AuthContext,
    ) -> None:
        if self._is_admin(auth) or school.educator_id == auth.user_id:
            return
        raise AuthorizationError(
            "You do not have permission to manage this micro-school",
            error_code="ERR-MICRO-403",
        )

    def _school_to_response(self, micro_school: MicroSchool) -> dict[str, Any]:
        return MicroSchoolResponse(
            id=str(micro_school.id),
            educator_id=str(micro_school.educator_id),
            name=micro_school.name,
            neighborhood=micro_school.neighborhood,
            city=micro_school.city,
            phone=micro_school.phone,
            max_capacity=micro_school.max_capacity,
            status=micro_school.status,
            created_at=_iso(micro_school.created_at) or "",
            updated_at=_iso(micro_school.updated_at),
        ).model_dump()

    def _group_to_response(self, micro_group: MicroGroup) -> dict[str, Any]:
        return MicroGroupResponse(
            id=str(micro_group.id),
            micro_school_id=str(micro_group.micro_school_id),
            name=micro_group.name,
            age_range_min=micro_group.age_range_min,
            age_range_max=micro_group.age_range_max,
            created_at=_iso(micro_group.created_at) or "",
            updated_at=_iso(micro_group.updated_at),
        ).model_dump()

    def _enrollment_to_response(
        self,
        micro_enrollment: MicroEnrollment,
    ) -> dict[str, Any]:
        return MicroEnrollmentResponse(
            id=str(micro_enrollment.id),
            micro_group_id=str(micro_enrollment.micro_group_id),
            parent_id=str(micro_enrollment.parent_id),
            child_name=micro_enrollment.child_name,
            date_of_birth=micro_enrollment.date_of_birth.isoformat(),
            enrolled_at=_iso(micro_enrollment.enrolled_at) or "",
            status=micro_enrollment.status,
            created_at=_iso(micro_enrollment.created_at) or "",
            updated_at=_iso(micro_enrollment.updated_at),
        ).model_dump()

    def _payment_to_response(self, micro_payment: MicroPayment) -> dict[str, Any]:
        return MicroPaymentResponse(
            id=str(micro_payment.id),
            micro_school_id=str(micro_payment.micro_school_id),
            parent_id=str(micro_payment.parent_id),
            child_enrollment_id=str(micro_payment.child_enrollment_id),
            amount=float(micro_payment.amount),
            currency=micro_payment.currency,
            period_type=micro_payment.period_type,
            period_start=micro_payment.period_start.isoformat(),
            period_end=micro_payment.period_end.isoformat(),
            paid_at=_iso(micro_payment.paid_at),
            status=micro_payment.status,
            created_at=_iso(micro_payment.created_at) or "",
            updated_at=_iso(micro_payment.updated_at),
        ).model_dump()

    def _resource_to_response(self, micro_resource: MicroResource) -> dict[str, Any]:
        return MicroResourceResponse(
            id=str(micro_resource.id),
            title=micro_resource.title,
            description=micro_resource.description,
            resource_type=micro_resource.resource_type,
            age_group=micro_resource.age_group,
            language=micro_resource.language,
            file_url=micro_resource.file_url,
            is_premium=micro_resource.is_premium,
            created_at=_iso(micro_resource.created_at) or "",
            updated_at=_iso(micro_resource.updated_at),
        ).model_dump()

    def _progress_to_response(
        self,
        micro_progress_log: MicroProgressLog,
    ) -> dict[str, Any]:
        return MicroProgressLogResponse(
            id=str(micro_progress_log.id),
            micro_enrollment_id=str(micro_progress_log.micro_enrollment_id),
            educator_id=str(micro_progress_log.educator_id),
            date=micro_progress_log.date.isoformat(),
            note=micro_progress_log.note,
            photo_url=micro_progress_log.photo_url,
            milestone_tag=micro_progress_log.milestone_tag,
            created_at=_iso(micro_progress_log.created_at) or "",
            updated_at=_iso(micro_progress_log.updated_at),
        ).model_dump()


class MicroSchoolService(_MicroServiceBase):
    """Business logic for micro-schools and learning resources."""

    async def create_micro_school(
        self,
        *,
        body: MicroSchoolCreateRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        educator_id = body.educator_id or auth.user_id
        await self._validate_educator_actor(educator_id, auth)
        await self._ensure_educator_role(educator_id)

        async with UnitOfWork(self.db) as uow:
            repo = MicroSchoolRepository(uow.session)
            audit = AuditService(uow.session)
            dispatcher = EventDispatcher(uow.session)
            micro_school = MicroSchool(
                educator_id=educator_id,
                name=body.name,
                neighborhood=body.neighborhood,
                city=body.city,
                phone=body.phone,
                max_capacity=body.max_capacity,
                status=body.status,
            )
            created = await repo.create_micro_school(micro_school)
            response = self._school_to_response(created)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="micro_school.create",
                outcome="success",
                target_type="micro_school",
                target_id=created.id,
                entity_after=response,
                ip_address=ip_address,
            )
            await dispatcher.dispatch(
                MicroSchoolCreated(
                    school_id=auth.school_id,
                    micro_school_id=created.id,
                    educator_id=created.educator_id,
                    name=created.name,
                )
            )
            await uow.commit()
        return response

    async def list_micro_schools(
        self,
        *,
        auth: AuthContext,
        educator_id: uuid.UUID | None = None,
        city: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        target_educator = educator_id
        if self._is_educator_actor(auth):
            target_educator = auth.user_id
        schools = await self.repo.list_micro_schools(
            educator_id=target_educator,
            city=city,
            status=status,
        )
        if auth.role == PAR:
            visible: list[MicroSchool] = []
            for school in schools:
                if await self.repo.parent_has_school_access(
                    parent_id=auth.user_id,
                    micro_school_id=school.id,
                ):
                    visible.append(school)
            schools = visible
        return [self._school_to_response(item) for item in schools]

    async def get_micro_school(
        self,
        *,
        micro_school_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict[str, Any]:
        school = await self._get_school_or_404(
            micro_school_id,
            include_groups=True,
            include_payments=True,
        )
        await self._ensure_school_view_access(school, auth)
        return self._school_to_response(school)

    async def update_micro_school(
        self,
        *,
        micro_school_id: uuid.UUID,
        body: MicroSchoolUpdateRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        school = await self._get_school_or_404(micro_school_id)
        await self._ensure_school_manage_access(school, auth)

        async with UnitOfWork(self.db) as uow:
            repo = MicroSchoolRepository(uow.session)
            audit = AuditService(uow.session)
            school = await repo.get_micro_school(micro_school_id)
            if school is None:
                raise NotFoundError("Micro-school not found", error_code="ERR-MICRO-404")
            before = self._school_to_response(school)
            for field, value in body.model_dump(exclude_unset=True).items():
                setattr(school, field, value)
            saved = await repo.save_micro_school(school)
            response = self._school_to_response(saved)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="micro_school.update",
                outcome="success",
                target_type="micro_school",
                target_id=saved.id,
                entity_before=before,
                entity_after=response,
                ip_address=ip_address,
            )
            await uow.commit()
        return response

    async def delete_micro_school(
        self,
        *,
        micro_school_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        school = await self._get_school_or_404(micro_school_id)
        await self._ensure_school_manage_access(school, auth)

        async with UnitOfWork(self.db) as uow:
            repo = MicroSchoolRepository(uow.session)
            audit = AuditService(uow.session)
            school = await repo.get_micro_school(micro_school_id)
            if school is None:
                raise NotFoundError("Micro-school not found", error_code="ERR-MICRO-404")
            before = self._school_to_response(school)
            await repo.delete_micro_school(school)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="micro_school.delete",
                outcome="success",
                target_type="micro_school",
                target_id=micro_school_id,
                entity_before=before,
                ip_address=ip_address,
            )
            await uow.commit()
        return before

    async def create_resource(
        self,
        *,
        body: MicroResourceCreateRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        if not (self._is_admin(auth) or self._is_educator_actor(auth)):
            raise AuthorizationError(
                "Only staff and educators can manage micro resources",
                error_code="ERR-MICRO-403",
            )
        async with UnitOfWork(self.db) as uow:
            repo = MicroSchoolRepository(uow.session)
            audit = AuditService(uow.session)
            resource = MicroResource(**body.model_dump())
            created = await repo.create_micro_resource(resource)
            response = self._resource_to_response(created)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="micro_resource.create",
                outcome="success",
                target_type="micro_resource",
                target_id=created.id,
                entity_after=response,
                ip_address=ip_address,
            )
            await uow.commit()
        return response

    async def list_resources(
        self,
        *,
        auth: AuthContext,
        resource_type: str | None = None,
        language: str | None = None,
        age_group: str | None = None,
        is_premium: bool | None = None,
    ) -> list[dict[str, Any]]:
        resources = await self.repo.list_micro_resources(
            resource_type=resource_type,
            language=language,
            age_group=age_group,
            is_premium=is_premium,
        )
        return [self._resource_to_response(item) for item in resources]

    async def update_resource(
        self,
        *,
        micro_resource_id: uuid.UUID,
        body: MicroResourceUpdateRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        if not (self._is_admin(auth) or self._is_educator_actor(auth)):
            raise AuthorizationError(
                "Only staff and educators can manage micro resources",
                error_code="ERR-MICRO-403",
            )
        async with UnitOfWork(self.db) as uow:
            repo = MicroSchoolRepository(uow.session)
            audit = AuditService(uow.session)
            resource = await repo.get_micro_resource(micro_resource_id)
            if resource is None:
                raise NotFoundError("Micro resource not found", error_code="ERR-MICRO-404")
            before = self._resource_to_response(resource)
            for field, value in body.model_dump(exclude_unset=True).items():
                setattr(resource, field, value)
            saved = await repo.save_micro_resource(resource)
            response = self._resource_to_response(saved)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="micro_resource.update",
                outcome="success",
                target_type="micro_resource",
                target_id=saved.id,
                entity_before=before,
                entity_after=response,
                ip_address=ip_address,
            )
            await uow.commit()
        return response

    async def delete_resource(
        self,
        *,
        micro_resource_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        if not (self._is_admin(auth) or self._is_educator_actor(auth)):
            raise AuthorizationError(
                "Only staff and educators can manage micro resources",
                error_code="ERR-MICRO-403",
            )
        async with UnitOfWork(self.db) as uow:
            repo = MicroSchoolRepository(uow.session)
            audit = AuditService(uow.session)
            resource = await repo.get_micro_resource(micro_resource_id)
            if resource is None:
                raise NotFoundError("Micro resource not found", error_code="ERR-MICRO-404")
            before = self._resource_to_response(resource)
            await repo.delete_micro_resource(resource)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="micro_resource.delete",
                outcome="success",
                target_type="micro_resource",
                target_id=micro_resource_id,
                entity_before=before,
                ip_address=ip_address,
            )
            await uow.commit()
        return before


class MicroGroupService(_MicroServiceBase):
    """Business logic for groups and enrollments inside a micro-school."""

    async def create_group(
        self,
        *,
        body: MicroGroupCreateRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        school = await self._get_school_or_404(body.micro_school_id)
        await self._ensure_school_manage_access(school, auth)

        async with UnitOfWork(self.db) as uow:
            repo = MicroSchoolRepository(uow.session)
            audit = AuditService(uow.session)
            dispatcher = EventDispatcher(uow.session)
            group = MicroGroup(**body.model_dump())
            created = await repo.create_micro_group(group)
            response = self._group_to_response(created)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="micro_group.create",
                outcome="success",
                target_type="micro_group",
                target_id=created.id,
                entity_after=response,
                ip_address=ip_address,
            )
            await dispatcher.dispatch(
                MicroGroupCreated(
                    school_id=auth.school_id,
                    micro_group_id=created.id,
                    micro_school_id=created.micro_school_id,
                    group_name=created.name,
                )
            )
            await uow.commit()
        return response

    async def list_groups(
        self,
        *,
        micro_school_id: uuid.UUID,
        auth: AuthContext,
    ) -> list[dict[str, Any]]:
        school = await self._get_school_or_404(micro_school_id)
        await self._ensure_school_view_access(school, auth)
        groups = await self.repo.list_micro_groups(micro_school_id=micro_school_id)
        return [self._group_to_response(item) for item in groups]

    async def update_group(
        self,
        *,
        micro_group_id: uuid.UUID,
        body: MicroGroupUpdateRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        group = await self.repo.get_micro_group(micro_group_id, include_school=True)
        if group is None or group.micro_school is None:
            raise NotFoundError("Micro group not found", error_code="ERR-MICRO-404")
        await self._ensure_school_manage_access(group.micro_school, auth)

        async with UnitOfWork(self.db) as uow:
            repo = MicroSchoolRepository(uow.session)
            audit = AuditService(uow.session)
            group = await repo.get_micro_group(micro_group_id)
            if group is None:
                raise NotFoundError("Micro group not found", error_code="ERR-MICRO-404")
            before = self._group_to_response(group)
            payload = body.model_dump(exclude_unset=True)
            if (
                "age_range_min" in payload
                and "age_range_max" in payload
                and payload["age_range_max"] < payload["age_range_min"]
            ):
                raise ValidationError(
                    "age_range_max must be greater than or equal to age_range_min",
                    error_code="ERR-MICRO-422",
                )
            for field, value in payload.items():
                setattr(group, field, value)
            saved = await repo.save_micro_group(group)
            response = self._group_to_response(saved)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="micro_group.update",
                outcome="success",
                target_type="micro_group",
                target_id=saved.id,
                entity_before=before,
                entity_after=response,
                ip_address=ip_address,
            )
            await uow.commit()
        return response

    async def delete_group(
        self,
        *,
        micro_group_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        group = await self.repo.get_micro_group(micro_group_id, include_school=True)
        if group is None or group.micro_school is None:
            raise NotFoundError("Micro group not found", error_code="ERR-MICRO-404")
        await self._ensure_school_manage_access(group.micro_school, auth)

        async with UnitOfWork(self.db) as uow:
            repo = MicroSchoolRepository(uow.session)
            audit = AuditService(uow.session)
            group = await repo.get_micro_group(micro_group_id)
            if group is None:
                raise NotFoundError("Micro group not found", error_code="ERR-MICRO-404")
            before = self._group_to_response(group)
            await repo.delete_micro_group(group)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="micro_group.delete",
                outcome="success",
                target_type="micro_group",
                target_id=micro_group_id,
                entity_before=before,
                ip_address=ip_address,
            )
            await uow.commit()
        return before

    async def create_enrollment(
        self,
        *,
        body: MicroEnrollmentCreateRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        group = await self.repo.get_micro_group(body.micro_group_id, include_school=True)
        if group is None or group.micro_school is None:
            raise NotFoundError("Micro group not found", error_code="ERR-MICRO-404")
        if auth.role == PAR:
            if body.parent_id != auth.user_id:
                raise AuthorizationError(
                    "Parents can only enroll their own child",
                    error_code="ERR-MICRO-403",
                )
        else:
            await self._ensure_school_manage_access(group.micro_school, auth)
        if await self.repo.get_user(body.parent_id) is None:
            raise NotFoundError("Parent user not found", error_code="ERR-MICRO-404")

        async with UnitOfWork(self.db) as uow:
            repo = MicroSchoolRepository(uow.session)
            audit = AuditService(uow.session)
            dispatcher = EventDispatcher(uow.session)
            enrollment = MicroEnrollment(
                micro_group_id=body.micro_group_id,
                child_name=body.child_name,
                parent_id=body.parent_id,
                date_of_birth=body.date_of_birth,
                enrolled_at=body.enrolled_at or datetime.now(timezone.utc),
                status=body.status,
            )
            created = await repo.create_micro_enrollment(enrollment)
            response = self._enrollment_to_response(created)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="micro_enrollment.create",
                outcome="success",
                target_type="micro_enrollment",
                target_id=created.id,
                entity_after=response,
                ip_address=ip_address,
            )
            await dispatcher.dispatch(
                MicroEnrollmentCreated(
                    school_id=auth.school_id,
                    micro_enrollment_id=created.id,
                    micro_group_id=created.micro_group_id,
                    parent_id=created.parent_id,
                    child_name=created.child_name,
                )
            )
            await uow.commit()
        return response

    async def list_enrollments(
        self,
        *,
        auth: AuthContext,
        micro_group_id: uuid.UUID | None = None,
        parent_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        target_parent = parent_id
        if auth.role == PAR:
            target_parent = auth.user_id
        if micro_group_id is not None:
            group = await self.repo.get_micro_group(micro_group_id, include_school=True)
            if group is None or group.micro_school is None:
                raise NotFoundError("Micro group not found", error_code="ERR-MICRO-404")
            await self._ensure_school_view_access(group.micro_school, auth)
        enrollments = await self.repo.list_micro_enrollments(
            micro_group_id=micro_group_id,
            parent_id=target_parent,
            status=status,
        )
        if auth.role == PAR:
            enrollments = [item for item in enrollments if item.parent_id == auth.user_id]
        return [self._enrollment_to_response(item) for item in enrollments]

    async def update_enrollment(
        self,
        *,
        micro_enrollment_id: uuid.UUID,
        body: MicroEnrollmentUpdateRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        enrollment = await self.repo.get_micro_enrollment(
            micro_enrollment_id,
            include_group=True,
        )
        if (
            enrollment is None
            or enrollment.micro_group is None
            or enrollment.micro_group.micro_school is None
        ):
            raise NotFoundError("Micro enrollment not found", error_code="ERR-MICRO-404")
        school = enrollment.micro_group.micro_school
        if auth.role == PAR:
            if enrollment.parent_id != auth.user_id:
                raise AuthorizationError(
                    "You do not have access to this enrollment",
                    error_code="ERR-MICRO-403",
                )
        else:
            await self._ensure_school_manage_access(school, auth)
        payload = body.model_dump(exclude_unset=True)
        if auth.role == PAR:
            allowed_parent_fields = {"child_name", "date_of_birth", "status"}
            disallowed = set(payload) - allowed_parent_fields
            if disallowed:
                raise AuthorizationError(
                    "Parents can only update enrollment identity and status fields",
                    error_code="ERR-MICRO-403",
                )

        async with UnitOfWork(self.db) as uow:
            repo = MicroSchoolRepository(uow.session)
            audit = AuditService(uow.session)
            enrollment = await repo.get_micro_enrollment(micro_enrollment_id)
            if enrollment is None:
                raise NotFoundError("Micro enrollment not found", error_code="ERR-MICRO-404")
            before = self._enrollment_to_response(enrollment)
            for field, value in payload.items():
                setattr(enrollment, field, value)
            saved = await repo.save_micro_enrollment(enrollment)
            response = self._enrollment_to_response(saved)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="micro_enrollment.update",
                outcome="success",
                target_type="micro_enrollment",
                target_id=saved.id,
                entity_before=before,
                entity_after=response,
                ip_address=ip_address,
            )
            await uow.commit()
        return response

    async def delete_enrollment(
        self,
        *,
        micro_enrollment_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        enrollment = await self.repo.get_micro_enrollment(
            micro_enrollment_id,
            include_group=True,
        )
        if (
            enrollment is None
            or enrollment.micro_group is None
            or enrollment.micro_group.micro_school is None
        ):
            raise NotFoundError("Micro enrollment not found", error_code="ERR-MICRO-404")
        await self._ensure_school_manage_access(enrollment.micro_group.micro_school, auth)

        async with UnitOfWork(self.db) as uow:
            repo = MicroSchoolRepository(uow.session)
            audit = AuditService(uow.session)
            enrollment = await repo.get_micro_enrollment(micro_enrollment_id)
            if enrollment is None:
                raise NotFoundError("Micro enrollment not found", error_code="ERR-MICRO-404")
            before = self._enrollment_to_response(enrollment)
            await repo.delete_micro_enrollment(enrollment)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="micro_enrollment.delete",
                outcome="success",
                target_type="micro_enrollment",
                target_id=micro_enrollment_id,
                entity_before=before,
                ip_address=ip_address,
            )
            await uow.commit()
        return before


class MicroPaymentService(_MicroServiceBase):
    """Business logic for micro-school payments and payment analytics."""

    async def create_payment(
        self,
        *,
        body: MicroPaymentCreateRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        school = await self._get_school_or_404(body.micro_school_id)
        enrollment = await self.repo.get_micro_enrollment(body.child_enrollment_id)
        if enrollment is None:
            raise NotFoundError("Micro enrollment not found", error_code="ERR-MICRO-404")
        if auth.role == PAR:
            if body.parent_id != auth.user_id or enrollment.parent_id != auth.user_id:
                raise AuthorizationError(
                    "Parents can only record their own micro-school payments",
                    error_code="ERR-MICRO-403",
                )
        else:
            await self._ensure_school_manage_access(school, auth)
        if enrollment.parent_id != body.parent_id:
            raise ValidationError(
                "Enrollment parent does not match payment parent",
                error_code="ERR-MICRO-422",
            )

        async with UnitOfWork(self.db) as uow:
            repo = MicroSchoolRepository(uow.session)
            audit = AuditService(uow.session)
            dispatcher = EventDispatcher(uow.session)
            payment = MicroPayment(
                micro_school_id=body.micro_school_id,
                parent_id=body.parent_id,
                child_enrollment_id=body.child_enrollment_id,
                amount=body.amount,
                currency=body.currency,
                period_type=body.period_type,
                period_start=body.period_start,
                period_end=body.period_end,
                paid_at=body.paid_at
                or (datetime.now(timezone.utc) if body.status == "paid" else None),
                status=body.status,
            )
            created = await repo.create_micro_payment(payment)
            response = self._payment_to_response(created)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="micro_payment.create",
                outcome="success",
                target_type="micro_payment",
                target_id=created.id,
                entity_after=response,
                ip_address=ip_address,
            )
            await dispatcher.dispatch(
                MicroPaymentRecorded(
                    school_id=auth.school_id,
                    micro_payment_id=created.id,
                    micro_school_id=created.micro_school_id,
                    parent_id=created.parent_id,
                    amount=float(created.amount),
                )
            )
            await uow.commit()
        return response

    async def list_payments(
        self,
        *,
        auth: AuthContext,
        micro_school_id: uuid.UUID | None = None,
        parent_id: uuid.UUID | None = None,
        child_enrollment_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        target_parent = parent_id
        if auth.role == PAR:
            target_parent = auth.user_id
        if micro_school_id is not None:
            school = await self._get_school_or_404(micro_school_id)
            await self._ensure_school_view_access(school, auth)
        payments = await self.repo.list_micro_payments(
            micro_school_id=micro_school_id,
            parent_id=target_parent,
            child_enrollment_id=child_enrollment_id,
            status=status,
        )
        if auth.role == PAR:
            payments = [item for item in payments if item.parent_id == auth.user_id]
        return [self._payment_to_response(item) for item in payments]

    async def update_payment(
        self,
        *,
        micro_payment_id: uuid.UUID,
        body: MicroPaymentUpdateRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        payment = await self.repo.get_micro_payment(micro_payment_id, include_school=True)
        if payment is None or payment.micro_school is None:
            raise NotFoundError("Micro payment not found", error_code="ERR-MICRO-404")
        if auth.role == PAR:
            if payment.parent_id != auth.user_id:
                raise AuthorizationError(
                    "You do not have access to this payment",
                    error_code="ERR-MICRO-403",
                )
        else:
            await self._ensure_school_manage_access(payment.micro_school, auth)

        async with UnitOfWork(self.db) as uow:
            repo = MicroSchoolRepository(uow.session)
            audit = AuditService(uow.session)
            payment = await repo.get_micro_payment(micro_payment_id)
            if payment is None:
                raise NotFoundError("Micro payment not found", error_code="ERR-MICRO-404")
            before = self._payment_to_response(payment)
            payload = body.model_dump(exclude_unset=True)
            for field, value in payload.items():
                setattr(payment, field, value)
            if payment.status == "paid" and payment.paid_at is None:
                payment.paid_at = datetime.now(timezone.utc)
            saved = await repo.save_micro_payment(payment)
            response = self._payment_to_response(saved)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="micro_payment.update",
                outcome="success",
                target_type="micro_payment",
                target_id=saved.id,
                entity_before=before,
                entity_after=response,
                ip_address=ip_address,
            )
            await uow.commit()
        return response

    async def delete_payment(
        self,
        *,
        micro_payment_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        payment = await self.repo.get_micro_payment(micro_payment_id, include_school=True)
        if payment is None or payment.micro_school is None:
            raise NotFoundError("Micro payment not found", error_code="ERR-MICRO-404")
        await self._ensure_school_manage_access(payment.micro_school, auth)

        async with UnitOfWork(self.db) as uow:
            repo = MicroSchoolRepository(uow.session)
            audit = AuditService(uow.session)
            payment = await repo.get_micro_payment(micro_payment_id)
            if payment is None:
                raise NotFoundError("Micro payment not found", error_code="ERR-MICRO-404")
            before = self._payment_to_response(payment)
            await repo.delete_micro_payment(payment)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="micro_payment.delete",
                outcome="success",
                target_type="micro_payment",
                target_id=micro_payment_id,
                entity_before=before,
                ip_address=ip_address,
            )
            await uow.commit()
        return before

    async def get_payment_analytics(
        self,
        *,
        auth: AuthContext,
        micro_school_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        target_parent = auth.user_id if auth.role == PAR else None
        if micro_school_id is not None:
            school = await self._get_school_or_404(micro_school_id)
            await self._ensure_school_view_access(school, auth)
        payments = await self.repo.list_micro_payments(
            micro_school_id=micro_school_id,
            parent_id=target_parent,
        )
        total_amount = sum(float(item.amount) for item in payments)
        collected_amount = sum(
            float(item.amount) for item in payments if item.status == "paid"
        )
        overdue_amount = sum(
            float(item.amount) for item in payments if item.status == "overdue"
        )
        pending_amount = sum(
            float(item.amount) for item in payments if item.status == "pending"
        )
        paid_count = sum(1 for item in payments if item.status == "paid")
        overdue_count = sum(1 for item in payments if item.status == "overdue")
        pending_count = sum(1 for item in payments if item.status == "pending")
        return {
            "total_amount": round(total_amount, 2),
            "collected_amount": round(collected_amount, 2),
            "overdue_amount": round(overdue_amount, 2),
            "pending_amount": round(pending_amount, 2),
            "paid_count": paid_count,
            "overdue_count": overdue_count,
            "pending_count": pending_count,
            "collection_rate": round(
                (collected_amount / total_amount) * 100 if total_amount else 0.0,
                2,
            ),
        }


class MicroProgressService(_MicroServiceBase):
    """Business logic for progress logs and lightweight progress summaries."""

    async def create_progress_log(
        self,
        *,
        body: MicroProgressLogCreateRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        enrollment = await self.repo.get_micro_enrollment(
            body.micro_enrollment_id,
            include_group=True,
        )
        if (
            enrollment is None
            or enrollment.micro_group is None
            or enrollment.micro_group.micro_school is None
        ):
            raise NotFoundError("Micro enrollment not found", error_code="ERR-MICRO-404")
        school = enrollment.micro_group.micro_school
        await self._ensure_school_manage_access(school, auth)
        educator_id = body.educator_id or auth.user_id
        await self._validate_educator_actor(educator_id, auth)
        await self._ensure_educator_role(educator_id)

        async with UnitOfWork(self.db) as uow:
            repo = MicroSchoolRepository(uow.session)
            audit = AuditService(uow.session)
            dispatcher = EventDispatcher(uow.session)
            progress = MicroProgressLog(
                micro_enrollment_id=body.micro_enrollment_id,
                educator_id=educator_id,
                date=body.date,
                note=body.note,
                photo_url=body.photo_url,
                milestone_tag=body.milestone_tag,
            )
            created = await repo.create_micro_progress_log(progress)
            response = self._progress_to_response(created)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="micro_progress.create",
                outcome="success",
                target_type="micro_progress",
                target_id=created.id,
                entity_after=response,
                ip_address=ip_address,
            )
            await dispatcher.dispatch(
                MicroProgressLogged(
                    school_id=auth.school_id,
                    micro_progress_log_id=created.id,
                    micro_enrollment_id=created.micro_enrollment_id,
                    educator_id=created.educator_id,
                    milestone_tag=created.milestone_tag or "",
                )
            )
            await uow.commit()
        return response

    async def list_progress_logs(
        self,
        *,
        auth: AuthContext,
        micro_enrollment_id: uuid.UUID | None = None,
        educator_id: uuid.UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[dict[str, Any]]:
        target_educator = educator_id
        if self._is_educator_actor(auth):
            target_educator = auth.user_id
        if micro_enrollment_id is not None:
            enrollment = await self.repo.get_micro_enrollment(
                micro_enrollment_id,
                include_group=True,
            )
            if (
                enrollment is None
                or enrollment.micro_group is None
                or enrollment.micro_group.micro_school is None
            ):
                raise NotFoundError(
                    "Micro enrollment not found",
                    error_code="ERR-MICRO-404",
                )
            school = enrollment.micro_group.micro_school
            if auth.role == PAR:
                if enrollment.parent_id != auth.user_id:
                    raise AuthorizationError(
                        "You do not have access to this progress log feed",
                        error_code="ERR-MICRO-403",
                    )
            else:
                await self._ensure_school_view_access(school, auth)
        logs = await self.repo.list_micro_progress_logs(
            micro_enrollment_id=micro_enrollment_id,
            educator_id=target_educator,
            date_from=date_from,
            date_to=date_to,
        )
        if auth.role == PAR:
            allowed_enrollment_ids: set[uuid.UUID] = set()
            for log in logs:
                enrollment = await self.repo.get_micro_enrollment(log.micro_enrollment_id)
                if enrollment is not None and enrollment.parent_id == auth.user_id:
                    allowed_enrollment_ids.add(enrollment.id)
            logs = [
                item for item in logs if item.micro_enrollment_id in allowed_enrollment_ids
            ]
        return [self._progress_to_response(item) for item in logs]

    async def update_progress_log(
        self,
        *,
        micro_progress_log_id: uuid.UUID,
        body: MicroProgressLogUpdateRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        progress = await self.repo.get_micro_progress_log(
            micro_progress_log_id,
            include_enrollment=True,
        )
        if (
            progress is None
            or progress.micro_enrollment is None
            or progress.micro_enrollment.micro_group is None
            or progress.micro_enrollment.micro_group.micro_school is None
        ):
            raise NotFoundError("Micro progress log not found", error_code="ERR-MICRO-404")
        school = progress.micro_enrollment.micro_group.micro_school
        if not self._is_admin(auth) and progress.educator_id != auth.user_id:
            await self._ensure_school_manage_access(school, auth)

        async with UnitOfWork(self.db) as uow:
            repo = MicroSchoolRepository(uow.session)
            audit = AuditService(uow.session)
            progress = await repo.get_micro_progress_log(micro_progress_log_id)
            if progress is None:
                raise NotFoundError("Micro progress log not found", error_code="ERR-MICRO-404")
            before = self._progress_to_response(progress)
            for field, value in body.model_dump(exclude_unset=True).items():
                setattr(progress, field, value)
            saved = await repo.save_micro_progress_log(progress)
            response = self._progress_to_response(saved)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="micro_progress.update",
                outcome="success",
                target_type="micro_progress",
                target_id=saved.id,
                entity_before=before,
                entity_after=response,
                ip_address=ip_address,
            )
            await uow.commit()
        return response

    async def delete_progress_log(
        self,
        *,
        micro_progress_log_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        progress = await self.repo.get_micro_progress_log(
            micro_progress_log_id,
            include_enrollment=True,
        )
        if (
            progress is None
            or progress.micro_enrollment is None
            or progress.micro_enrollment.micro_group is None
            or progress.micro_enrollment.micro_group.micro_school is None
        ):
            raise NotFoundError("Micro progress log not found", error_code="ERR-MICRO-404")
        school = progress.micro_enrollment.micro_group.micro_school
        if not self._is_admin(auth) and progress.educator_id != auth.user_id:
            await self._ensure_school_manage_access(school, auth)

        async with UnitOfWork(self.db) as uow:
            repo = MicroSchoolRepository(uow.session)
            audit = AuditService(uow.session)
            progress = await repo.get_micro_progress_log(micro_progress_log_id)
            if progress is None:
                raise NotFoundError("Micro progress log not found", error_code="ERR-MICRO-404")
            before = self._progress_to_response(progress)
            await repo.delete_micro_progress_log(progress)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="micro_progress.delete",
                outcome="success",
                target_type="micro_progress",
                target_id=micro_progress_log_id,
                entity_before=before,
                ip_address=ip_address,
            )
            await uow.commit()
        return before

    async def summarize_progress(
        self,
        *,
        micro_enrollment_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict[str, Any]:
        enrollment = await self.repo.get_micro_enrollment(
            micro_enrollment_id,
            include_group=True,
            include_progress_logs=True,
        )
        if (
            enrollment is None
            or enrollment.micro_group is None
            or enrollment.micro_group.micro_school is None
        ):
            raise NotFoundError("Micro enrollment not found", error_code="ERR-MICRO-404")
        school = enrollment.micro_group.micro_school
        if auth.role == PAR:
            if enrollment.parent_id != auth.user_id:
                raise AuthorizationError(
                    "You do not have access to this progress summary",
                    error_code="ERR-MICRO-403",
                )
        else:
            await self._ensure_school_view_access(school, auth)
        logs = sorted(enrollment.progress_logs, key=lambda item: (item.date, item.created_at))
        latest = logs[-1] if logs else None
        return {
            "micro_enrollment_id": str(enrollment.id),
            "child_name": enrollment.child_name,
            "total_logs": len(logs),
            "latest_log_date": latest.date.isoformat() if latest is not None else None,
            "milestone_tags": [
                item.milestone_tag for item in logs if item.milestone_tag is not None
            ],
        }


__all__ = [
    "MicroSchoolService",
    "MicroGroupService",
    "MicroPaymentService",
    "MicroProgressService",
]
