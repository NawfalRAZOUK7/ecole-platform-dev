"""Repository helpers for Phase 16 document management."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Iterable

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.response import decode_cursor, encode_cursor
from app.models.documents import (
    Document,
    Resource,
    ResourceRating,
    StudentDocumentRequirement,
)
from app.models.erp import Enrollment, TeacherAssignment
from app.models.iam import ParentChildLink, User


class DocumentsRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_document(self, document_id: uuid.UUID) -> Document | None:
        result = await self.db.execute(
            select(Document).where(Document.id == document_id)
        )
        return result.scalar_one_or_none()

    async def create_document(self, document: Document) -> Document:
        self.db.add(document)
        await self.db.flush()
        return document

    async def save_document(self, document: Document) -> Document:
        self.db.add(document)
        await self.db.flush()
        return document

    async def find_document_by_sha(
        self,
        *,
        school_id: uuid.UUID,
        sha256: str,
    ) -> Document | None:
        result = await self.db.execute(
            select(Document)
            .where(
                Document.school_id == school_id,
                Document.sha256 == sha256,
                Document.deleted_at.is_(None),
            )
            .order_by(Document.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def count_documents_for_storage_path(
        self,
        *,
        storage_path: str,
        exclude_document_id: uuid.UUID | None = None,
    ) -> int:
        query = select(func.count(Document.id)).where(Document.storage_path == storage_path)
        if exclude_document_id:
            query = query.where(Document.id != exclude_document_id)
        result = await self.db.execute(query)
        return int(result.scalar_one() or 0)

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

    async def list_student_class_ids(
        self,
        *,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> set[uuid.UUID]:
        result = await self.db.execute(
            select(Enrollment.class_id).where(
                Enrollment.student_id == student_id,
                Enrollment.school_id == school_id,
                Enrollment.status == "active",
            )
        )
        return set(result.scalars().all())

    async def list_students_for_classes(
        self,
        *,
        school_id: uuid.UUID,
        class_ids: Iterable[uuid.UUID],
    ) -> set[uuid.UUID]:
        class_ids = list(class_ids)
        if not class_ids:
            return set()
        result = await self.db.execute(
            select(Enrollment.student_id).where(
                Enrollment.school_id == school_id,
                Enrollment.class_id.in_(class_ids),
                Enrollment.status == "active",
            )
        )
        return set(result.scalars().all())

    async def get_user_in_school(
        self,
        *,
        user_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> User | None:
        result = await self.db.execute(
            select(User).where(User.id == user_id, User.school_id == school_id)
        )
        return result.scalar_one_or_none()

    async def list_users_by_ids(
        self,
        *,
        school_id: uuid.UUID,
        user_ids: Iterable[uuid.UUID],
    ) -> list[User]:
        user_ids = list(user_ids)
        if not user_ids:
            return []
        result = await self.db.execute(
            select(User)
            .where(User.school_id == school_id, User.id.in_(user_ids))
            .order_by(User.full_name.asc())
        )
        return list(result.scalars().all())

    async def list_students_in_school(
        self,
        *,
        school_id: uuid.UUID,
    ) -> list[User]:
        result = await self.db.execute(
            select(User)
            .join(Enrollment, Enrollment.student_id == User.id)
            .where(
                User.school_id == school_id,
                Enrollment.school_id == school_id,
                Enrollment.status == "active",
            )
            .distinct()
            .order_by(User.full_name.asc())
        )
        return list(result.scalars().all())

    async def list_documents(
        self,
        *,
        school_id: uuid.UUID,
        role: str,
        user_id: uuid.UUID,
        category: str | None,
        owner_id: uuid.UUID | None,
        mime_type: str | None,
        cursor: str | None,
        limit: int,
        allowed_student_ids: set[uuid.UUID] | None = None,
    ) -> tuple[list[tuple[Document, str | None, str | None]], str | None, bool]:
        uploader = User.__table__.alias("doc_uploader")
        student = User.__table__.alias("doc_student")
        query = (
            select(Document, uploader.c.full_name, student.c.full_name)
            .outerjoin(uploader, uploader.c.id == Document.uploader_id)
            .outerjoin(student, student.c.id == Document.linked_student_id)
            .where(
                Document.school_id == school_id,
                Document.deleted_at.is_(None),
            )
        )

        if category:
            query = query.where(Document.category == category)
        if owner_id:
            query = query.where(Document.uploader_id == owner_id)
        if mime_type:
            query = query.where(Document.mime_type == mime_type)

        allowed_student_ids = allowed_student_ids or set()
        if role == "PAR":
            query = query.where(
                or_(
                    Document.uploader_id == user_id,
                    Document.linked_student_id.in_(allowed_student_ids)
                    if allowed_student_ids
                    else False,
                )
            )
        elif role == "TCH":
            query = query.where(
                or_(
                    Document.uploader_id == user_id,
                    Document.linked_student_id.in_(allowed_student_ids)
                    if allowed_student_ids
                    else False,
                )
            )
        elif role == "STD":
            query = query.where(
                or_(
                    Document.linked_student_id == user_id,
                    Document.uploader_id == user_id,
                )
            )

        query = query.order_by(Document.created_at.desc(), Document.id.desc())
        if cursor:
            last_id, last_created_at = decode_cursor(cursor)
            if last_created_at:
                cursor_dt = datetime.fromisoformat(last_created_at)
                query = query.where(
                    or_(
                        Document.created_at < cursor_dt,
                        and_(Document.created_at == cursor_dt, Document.id < last_id),
                    )
                )

        result = await self.db.execute(query.limit(limit + 1))
        rows = list(result.all())
        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        next_cursor = None
        if rows and has_more:
            next_cursor = encode_cursor(rows[-1][0].id, rows[-1][0].created_at.isoformat())

        return [(document, uploader_name, student_name) for document, uploader_name, student_name in rows], next_cursor, has_more

    async def list_student_documents(
        self,
        *,
        school_id: uuid.UUID,
        student_id: uuid.UUID,
    ) -> list[tuple[Document, str | None]]:
        uploader = User.__table__.alias("student_doc_uploader")
        result = await self.db.execute(
            select(Document, uploader.c.full_name)
            .outerjoin(uploader, uploader.c.id == Document.uploader_id)
            .where(
                Document.school_id == school_id,
                Document.linked_student_id == student_id,
                Document.deleted_at.is_(None),
            )
            .order_by(Document.created_at.desc())
        )
        return list(result.all())

    async def list_student_requirements(
        self,
        *,
        school_id: uuid.UUID,
    ) -> list[StudentDocumentRequirement]:
        result = await self.db.execute(
            select(StudentDocumentRequirement)
            .where(StudentDocumentRequirement.school_id == school_id)
            .order_by(StudentDocumentRequirement.category.asc())
        )
        return list(result.scalars().all())

    async def find_student_requirement(
        self,
        *,
        school_id: uuid.UUID,
        category: str,
    ) -> StudentDocumentRequirement | None:
        result = await self.db.execute(
            select(StudentDocumentRequirement).where(
                StudentDocumentRequirement.school_id == school_id,
                StudentDocumentRequirement.category == category,
            )
        )
        return result.scalar_one_or_none()

    async def save_requirement(
        self,
        requirement: StudentDocumentRequirement,
    ) -> StudentDocumentRequirement:
        self.db.add(requirement)
        await self.db.flush()
        return requirement

    async def list_expiring_documents(
        self,
        *,
        window_start: datetime,
        window_end: datetime,
    ) -> list[Document]:
        result = await self.db.execute(
            select(Document).where(
                Document.deleted_at.is_(None),
                Document.linked_student_id.is_not(None),
                Document.expires_at.is_not(None),
                Document.expires_at >= window_start,
                Document.expires_at <= window_end,
            )
        )
        return list(result.scalars().all())

    async def list_deleted_documents(
        self,
        *,
        before: datetime,
    ) -> list[Document]:
        result = await self.db.execute(
            select(Document).where(
                Document.deleted_at.is_not(None),
                Document.deleted_at <= before,
            )
        )
        return list(result.scalars().all())

    async def create_resource(self, resource: Resource) -> Resource:
        self.db.add(resource)
        await self.db.flush()
        return resource

    async def save_resource(self, resource: Resource) -> Resource:
        self.db.add(resource)
        await self.db.flush()
        return resource

    async def get_resource(self, resource_id: uuid.UUID) -> Resource | None:
        result = await self.db.execute(select(Resource).where(Resource.id == resource_id))
        return result.scalar_one_or_none()

    async def list_resources(
        self,
        *,
        school_id: uuid.UUID,
        role: str,
        user_id: uuid.UUID,
        subject: str | None,
        level: str | None,
        resource_type: str | None,
        tags: list[str],
        search: str | None,
        min_rating: float | None,
        cursor: str | None,
        limit: int,
        visible_class_ids: set[uuid.UUID] | None = None,
    ) -> tuple[list[tuple[Resource, Document]], str | None, bool]:
        query = (
            select(Resource, Document)
            .join(Document, Document.id == Resource.file_id)
            .where(
                Resource.school_id == school_id,
                Resource.deleted_at.is_(None),
                Document.deleted_at.is_(None),
            )
        )
        if subject:
            query = query.where(Resource.subject == subject)
        if level:
            query = query.where(Resource.level == level)
        if resource_type:
            query = query.where(Resource.type == resource_type)
        if tags:
            query = query.where(Resource.tags.overlap(tags))
        if search:
            pattern = f"%{search}%"
            query = query.where(
                or_(
                    Resource.title.ilike(pattern),
                    Resource.description.ilike(pattern),
                    Resource.subject.ilike(pattern),
                    Resource.level.ilike(pattern),
                )
            )
        if min_rating is not None:
            query = query.where(Resource.avg_rating >= min_rating)

        visible_class_ids = visible_class_ids or set()
        if role == "TCH":
            query = query.where(
                or_(
                    Resource.visibility == "school",
                    Resource.class_id.in_(visible_class_ids) if visible_class_ids else False,
                    Resource.uploader_id == user_id,
                )
            )
        elif role in {"PAR", "STD"}:
            query = query.where(
                or_(
                    Resource.visibility == "school",
                    Resource.class_id.in_(visible_class_ids) if visible_class_ids else False,
                )
            )

        query = query.order_by(Resource.created_at.desc(), Resource.id.desc())
        if cursor:
            last_id, last_created_at = decode_cursor(cursor)
            if last_created_at:
                cursor_dt = datetime.fromisoformat(last_created_at)
                query = query.where(
                    or_(
                        Resource.created_at < cursor_dt,
                        and_(Resource.created_at == cursor_dt, Resource.id < last_id),
                    )
                )

        result = await self.db.execute(query.limit(limit + 1))
        rows = list(result.all())
        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        next_cursor = None
        if rows and has_more:
            next_cursor = encode_cursor(rows[-1][0].id, rows[-1][0].created_at.isoformat())
        return rows, next_cursor, has_more

    async def get_resource_with_document(
        self,
        resource_id: uuid.UUID,
    ) -> tuple[Resource, Document] | None:
        result = await self.db.execute(
            select(Resource, Document)
            .join(Document, Document.id == Resource.file_id)
            .where(Resource.id == resource_id)
        )
        return result.first()

    async def get_resource_rating(
        self,
        *,
        resource_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ResourceRating | None:
        result = await self.db.execute(
            select(ResourceRating).where(
                ResourceRating.resource_id == resource_id,
                ResourceRating.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def save_resource_rating(self, rating: ResourceRating) -> ResourceRating:
        self.db.add(rating)
        await self.db.flush()
        return rating

    async def calculate_resource_rating_stats(
        self,
        *,
        resource_id: uuid.UUID,
    ) -> tuple[float, int]:
        result = await self.db.execute(
            select(func.avg(ResourceRating.rating), func.count(ResourceRating.id)).where(
                ResourceRating.resource_id == resource_id
            )
        )
        average, count = result.one()
        return float(average or 0), int(count or 0)
