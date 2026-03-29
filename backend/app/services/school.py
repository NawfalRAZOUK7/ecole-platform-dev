"""School management service."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import AuthContext, verify_school_boundary
from app.core.exceptions import NotFoundError
from app.core.permissions import ADM, DIR, SUP
from app.core.unit_of_work import UnitOfWork
from app.repositories.school import SchoolRepository
from app.schemas.school import SchoolCreateRequest, SchoolUpdateRequest


class SchoolService:
    """Business logic for school CRUD and scoped reads."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = SchoolRepository(db)

    def _to_response(self, school) -> dict:
        return {
            "id": str(school.id),
            "name": school.name,
            "name_ar": school.name_ar,
            "code": school.code,
            "massar_code": school.massar_code,
            "status": school.status,
            "address": school.address,
            "city": school.city,
            "region": school.region,
            "phone": school.phone,
            "email": school.email,
            "website": school.website,
            "logo_path": school.logo_path,
            "max_students": school.max_students,
            "max_teachers": school.max_teachers,
            "subscription_plan": school.subscription_plan,
            "subscription_expires_at": (
                school.subscription_expires_at.isoformat()
                if school.subscription_expires_at
                else None
            ),
            "timezone": school.timezone,
            "default_language": school.default_language,
            "grading_scale": school.grading_scale,
            "settings": school.settings or {},
            "is_active": school.is_active,
            "is_subscription_valid": school.is_subscription_valid,
            "deleted_at": school.deleted_at.isoformat() if school.deleted_at else None,
            "created_at": school.created_at.isoformat(),
            "updated_at": school.updated_at.isoformat() if school.updated_at else None,
        }

    def _ensure_read_scope(self, school, auth: AuthContext) -> None:
        if auth.role == SUP:
            return
        verify_school_boundary(school.id, auth)

    def _ensure_manage_scope(self, school, auth: AuthContext) -> None:
        if auth.role == SUP:
            return
        if auth.role != ADM:
            raise NotFoundError("School not found", error_code="ERR-RES-404")
        verify_school_boundary(school.id, auth)

    async def create_school(
        self,
        *,
        body: SchoolCreateRequest,
        auth: AuthContext,
    ) -> dict:
        if auth.role != SUP:
            raise NotFoundError("School not found", error_code="ERR-RES-404")

        async with UnitOfWork(self.db) as uow:
            repo = SchoolRepository(uow.session)
            school = await repo.create_school(body.model_dump())
            await uow.commit()
        return self._to_response(school)

    async def get_school(
        self,
        *,
        school_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict:
        school = await self.repo.get_school(school_id)
        if school is None:
            raise NotFoundError("School not found", error_code="ERR-RES-404")
        self._ensure_read_scope(school, auth)
        return self._to_response(school)

    async def list_schools(
        self,
        *,
        auth: AuthContext,
        cursor: str | None,
        limit: int,
        status: str | None = None,
    ) -> tuple[list[dict], str | None, bool]:
        if auth.role == SUP:
            schools, next_cursor, has_more = await self.repo.list_schools(
                cursor,
                limit,
                {"status": status},
            )
            return [self._to_response(school) for school in schools], next_cursor, has_more

        if auth.role not in {ADM, DIR}:
            raise NotFoundError("School not found", error_code="ERR-RES-404")

        school = await self.repo.get_school(auth.school_id)
        if school is None:
            return [], None, False
        if status and school.status != status:
            return [], None, False
        return [self._to_response(school)], None, False

    async def update_school(
        self,
        *,
        school_id: uuid.UUID,
        body: SchoolUpdateRequest,
        auth: AuthContext,
    ) -> dict:
        existing = await self.repo.get_school(school_id)
        if existing is None:
            raise NotFoundError("School not found", error_code="ERR-RES-404")
        self._ensure_manage_scope(existing, auth)

        async with UnitOfWork(self.db) as uow:
            repo = SchoolRepository(uow.session)
            school = await repo.update_school(
                school_id,
                body.model_dump(exclude_unset=True),
            )
            if school is None:
                raise NotFoundError("School not found", error_code="ERR-RES-404")
            await uow.commit()
        return self._to_response(school)

    async def deactivate_school(
        self,
        *,
        school_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict:
        if auth.role != SUP:
            raise NotFoundError("School not found", error_code="ERR-RES-404")

        async with UnitOfWork(self.db) as uow:
            repo = SchoolRepository(uow.session)
            school = await repo.soft_delete_school(school_id)
            if school is None:
                raise NotFoundError("School not found", error_code="ERR-RES-404")
            await uow.commit()
        return self._to_response(school)
