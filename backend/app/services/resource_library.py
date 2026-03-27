"""Phase 16 teacher resource library service."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import BinaryIO

from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.models.documents import DocumentCategory, Resource, ResourceRating
from app.repositories.documents import DocumentsRepository
from app.schemas.resources import ResourceCreateRequest, ResourceUpdateRequest
from app.services.student_documents import StudentDocumentsService

RESOURCE_DOWNLOAD_ACTION = "resource.download"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ResourceLibraryService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = DocumentsRepository(db)
        self.documents = StudentDocumentsService(db)

    async def create_resource(
        self,
        *,
        school_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_role: str,
        file: BinaryIO,
        original_filename: str,
        mime_type: str,
        payload: ResourceCreateRequest,
    ) -> dict:
        if actor_role not in {"TCH", "ADM", "DIR"}:
            raise AuthorizationError(
                "Only teachers and administrators can upload resources",
                error_code="ERR-DOC-403",
            )
        if payload.visibility == "class":
            if payload.class_id is None:
                raise ValidationError("class_id is required", error_code="ERR-DOC-422")
            await self._verify_class_access(
                school_id=school_id,
                actor_id=actor_id,
                actor_role=actor_role,
                class_id=payload.class_id,
            )

        upload = await self.documents.upload_document(
            school_id=school_id,
            user_id=actor_id,
            role=actor_role,
            file=file,
            original_filename=original_filename,
            mime_type=mime_type,
            category=DocumentCategory.OTHER.value,
        )
        document = await self.repo.get_document(uuid.UUID(upload["id"]))
        if document is None:
            raise NotFoundError("Document not found", error_code="ERR-DOC-404")

        resource = Resource(
            school_id=school_id,
            uploader_id=actor_id,
            title=payload.title,
            description=payload.description,
            subject=payload.subject,
            level=payload.level,
            type=payload.type,
            tags=payload.tags,
            file_id=document.id,
            visibility=payload.visibility,
            class_id=payload.class_id,
        )
        await self.repo.create_resource(resource)
        return await self.serialize_resource(resource=resource, document=document, actor_id=actor_id, actor_role=actor_role)

    async def list_resources(
        self,
        *,
        school_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_role: str,
        subject: str | None,
        level: str | None,
        resource_type: str | None,
        tags: list[str],
        search: str | None,
        min_rating: float | None,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[dict], str | None, bool]:
        visible_class_ids = await self._visible_class_ids(
            school_id=school_id,
            actor_id=actor_id,
            actor_role=actor_role,
        )
        rows, next_cursor, has_more = await self.repo.list_resources(
            school_id=school_id,
            role=actor_role,
            user_id=actor_id,
            subject=subject,
            level=level,
            resource_type=resource_type,
            tags=tags,
            search=search,
            min_rating=min_rating,
            cursor=cursor,
            limit=limit,
            visible_class_ids=visible_class_ids,
        )
        items = [
            await self.serialize_resource(
                resource=resource,
                document=document,
                actor_id=actor_id,
                actor_role=actor_role,
            )
            for resource, document in rows
        ]
        return items, next_cursor, has_more

    async def get_resource_for_actor(
        self,
        *,
        resource_id: uuid.UUID,
        school_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_role: str,
    ) -> tuple[Resource, object]:
        row = await self.repo.get_resource_with_document(resource_id)
        if row is None:
            raise NotFoundError("Resource not found", error_code="ERR-DOC-404")
        resource, document = row
        if resource.school_id != school_id or resource.deleted_at is not None:
            raise NotFoundError("Resource not found", error_code="ERR-DOC-404")
        await self._enforce_resource_visibility(
            resource=resource,
            school_id=school_id,
            actor_id=actor_id,
            actor_role=actor_role,
        )
        return resource, document

    async def get_resource_detail(
        self,
        *,
        resource_id: uuid.UUID,
        school_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_role: str,
    ) -> dict:
        resource, document = await self.get_resource_for_actor(
            resource_id=resource_id,
            school_id=school_id,
            actor_id=actor_id,
            actor_role=actor_role,
        )
        return await self.serialize_resource(
            resource=resource,
            document=document,
            actor_id=actor_id,
            actor_role=actor_role,
            include_my_rating=True,
        )

    async def update_resource(
        self,
        *,
        resource_id: uuid.UUID,
        school_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_role: str,
        payload: ResourceUpdateRequest,
    ) -> dict:
        resource, document = await self.get_resource_for_actor(
            resource_id=resource_id,
            school_id=school_id,
            actor_id=actor_id,
            actor_role=actor_role,
        )
        if actor_role not in {"ADM", "DIR"} and resource.uploader_id != actor_id:
            raise NotFoundError("Resource not found", error_code="ERR-DOC-404")
        updates = payload.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(resource, field, value)
        if resource.visibility == "class" and resource.class_id is None:
            raise ValidationError("class_id is required", error_code="ERR-DOC-422")
        await self.repo.save_resource(resource)
        return await self.serialize_resource(
            resource=resource,
            document=document,
            actor_id=actor_id,
            actor_role=actor_role,
            include_my_rating=True,
        )

    async def delete_resource(
        self,
        *,
        resource_id: uuid.UUID,
        school_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_role: str,
    ) -> dict:
        resource, document = await self.get_resource_for_actor(
            resource_id=resource_id,
            school_id=school_id,
            actor_id=actor_id,
            actor_role=actor_role,
        )
        if actor_role not in {"ADM", "DIR"} and resource.uploader_id != actor_id:
            raise NotFoundError("Resource not found", error_code="ERR-DOC-404")
        resource.deleted_at = _utc_now()
        document.deleted_at = _utc_now()
        await self.repo.save_resource(resource)
        await self.repo.save_document(document)
        return {"id": str(resource.id), "deleted": True}

    async def rate_resource(
        self,
        *,
        resource_id: uuid.UUID,
        school_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_role: str,
        rating_value: int,
    ) -> dict:
        if actor_role != "TCH":
            raise AuthorizationError(
                "Only teachers can rate resources",
                error_code="ERR-DOC-403",
            )
        resource, _document = await self.get_resource_for_actor(
            resource_id=resource_id,
            school_id=school_id,
            actor_id=actor_id,
            actor_role=actor_role,
        )
        rating = await self.repo.get_resource_rating(
            resource_id=resource.id,
            user_id=actor_id,
        )
        if rating is None:
            rating = ResourceRating(
                resource_id=resource.id,
                user_id=actor_id,
                rating=rating_value,
            )
        else:
            rating.rating = rating_value
        await self.repo.save_resource_rating(rating)
        average, count = await self.repo.calculate_resource_rating_stats(resource_id=resource.id)
        resource.avg_rating = average
        resource.rating_count = count
        await self.repo.save_resource(resource)
        return {
            "resource_id": str(resource.id),
            "rating": rating_value,
            "avg_rating": average,
            "rating_count": count,
        }

    async def get_rating_summary(
        self,
        *,
        resource_id: uuid.UUID,
        school_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_role: str,
    ) -> dict:
        resource, _document = await self.get_resource_for_actor(
            resource_id=resource_id,
            school_id=school_id,
            actor_id=actor_id,
            actor_role=actor_role,
        )
        rating = await self.repo.get_resource_rating(
            resource_id=resource.id,
            user_id=actor_id,
        )
        return {
            "resource_id": str(resource.id),
            "avg_rating": resource.avg_rating,
            "rating_count": resource.rating_count,
            "my_rating": rating.rating if rating else None,
        }

    async def read_resource_file(
        self,
        *,
        resource: Resource,
        document,
    ):
        resource.download_count += 1
        await self.repo.save_resource(resource)
        return await self.documents.read_document_file(document=document)

    def build_download_token(self, *, resource_id: uuid.UUID) -> str:
        exp = _utc_now() + timedelta(hours=settings.document_download_ttl_hours)
        return jwt.encode(
            {
                "resource_id": str(resource_id),
                "action": RESOURCE_DOWNLOAD_ACTION,
                "exp": exp,
            },
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

    def parse_download_token(self, token: str) -> uuid.UUID:
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
            )
        except JWTError as exc:
            raise NotFoundError("Resource not found", error_code="ERR-DOC-404") from exc
        if payload.get("action") != RESOURCE_DOWNLOAD_ACTION:
            raise NotFoundError("Resource not found", error_code="ERR-DOC-404")
        return uuid.UUID(payload["resource_id"])

    async def get_resource_for_token(self, *, token: str) -> tuple[Resource, object]:
        resource_id = self.parse_download_token(token)
        row = await self.repo.get_resource_with_document(resource_id)
        if row is None:
            raise NotFoundError("Resource not found", error_code="ERR-DOC-404")
        resource, document = row
        if resource.deleted_at is not None:
            raise NotFoundError("Resource not found", error_code="ERR-DOC-404")
        return resource, document

    async def serialize_resource(
        self,
        *,
        resource: Resource,
        document,
        actor_id: uuid.UUID,
        actor_role: str,
        include_my_rating: bool = False,
    ) -> dict:
        my_rating = None
        if include_my_rating:
            existing_rating = await self.repo.get_resource_rating(
                resource_id=resource.id,
                user_id=actor_id,
            )
            my_rating = existing_rating.rating if existing_rating else None
        preview = await self.documents.serialize_document(
            document,
            role=actor_role,
            actor_id=actor_id,
        )
        download_token = self.build_download_token(resource_id=resource.id)
        can_manage = actor_role in {"ADM", "DIR"} or resource.uploader_id == actor_id
        return {
            "id": str(resource.id),
            "title": resource.title,
            "description": resource.description,
            "subject": resource.subject,
            "level": resource.level,
            "type": resource.type,
            "tags": resource.tags,
            "visibility": resource.visibility,
            "class_id": str(resource.class_id) if resource.class_id else None,
            "file_id": str(resource.file_id),
            "download_count": resource.download_count,
            "avg_rating": resource.avg_rating,
            "rating_count": resource.rating_count,
            "download_url": f"/api/v1/resources/{resource.id}/download?token={download_token}",
            "preview_url": preview.get("preview_url") if preview else None,
            "thumbnail_url": preview.get("thumbnail_url") if preview else None,
            "document": preview,
            "my_rating": my_rating,
            "created_at": resource.created_at.isoformat(),
            "updated_at": resource.updated_at.isoformat() if resource.updated_at else None,
            "can_edit": can_manage,
            "can_delete": can_manage,
            "can_rate": actor_role == "TCH",
        }

    async def _verify_class_access(
        self,
        *,
        school_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_role: str,
        class_id: uuid.UUID,
    ) -> None:
        if actor_role in {"ADM", "DIR"}:
            return
        class_ids = await self.repo.list_teacher_class_ids(
            teacher_id=actor_id,
            school_id=school_id,
        )
        if class_id not in class_ids:
            raise NotFoundError("Class not found", error_code="ERR-DOC-404")

    async def _visible_class_ids(
        self,
        *,
        school_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_role: str,
    ) -> set[uuid.UUID]:
        if actor_role == "TCH":
            return await self.repo.list_teacher_class_ids(
                teacher_id=actor_id,
                school_id=school_id,
            )
        if actor_role == "PAR":
            child_ids = await self.repo.list_parent_child_ids(
                parent_id=actor_id,
                school_id=school_id,
            )
            class_ids: set[uuid.UUID] = set()
            for child_id in child_ids:
                class_ids.update(
                    await self.repo.list_student_class_ids(
                        student_id=child_id,
                        school_id=school_id,
                    )
                )
            return class_ids
        if actor_role == "STD":
            return await self.repo.list_student_class_ids(
                student_id=actor_id,
                school_id=school_id,
            )
        return set()

    async def _enforce_resource_visibility(
        self,
        *,
        resource: Resource,
        school_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_role: str,
    ) -> None:
        if resource.school_id != school_id:
            raise NotFoundError("Resource not found", error_code="ERR-DOC-404")
        if actor_role in {"ADM", "DIR"}:
            return
        if resource.uploader_id == actor_id:
            return
        if resource.visibility == "school":
            return
        visible_class_ids = await self._visible_class_ids(
            school_id=school_id,
            actor_id=actor_id,
            actor_role=actor_role,
        )
        if resource.class_id not in visible_class_ids:
            raise NotFoundError("Resource not found", error_code="ERR-DOC-404")
