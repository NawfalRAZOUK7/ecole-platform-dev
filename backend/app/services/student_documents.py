"""Phase 16 student documents and generic document lifecycle service."""

from __future__ import annotations

import os
import tempfile
import uuid
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import BinaryIO, Iterable

from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.core.metrics import (
    DOCUMENT_STORAGE_TOTAL_BYTES,
    DOCUMENT_UPLOAD_COUNT,
    DOCUMENT_UPLOAD_SIZE_BYTES,
)
from app.models.com import NotificationCategory
from app.models.documents import Document, DocumentCategory, StudentDocumentRequirement
from app.models.iam import User
from app.repositories.documents import DocumentsRepository
from app.services.file_storage import file_storage_service
from app.services.notification_hub import NotificationHubService

DOCUMENT_DOWNLOAD_ACTION = "document.download"
DOCUMENT_PREVIEW_ACTION = "document.preview"
DOCUMENT_BULK_DOWNLOAD_ACTION = "document.bulk-download"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


DEFAULT_REQUIREMENTS: tuple[tuple[str, bool, str], ...] = (
    ("certificate", True, "Birth or enrollment certificate"),
    ("identity", True, "Student identity document"),
    ("medical", True, "Medical certificate or health record"),
    ("report_card", False, "Most recent report card"),
    ("transcript", False, "Transfer transcript when applicable"),
)


class StudentDocumentsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = DocumentsRepository(db)
        self.notification_hub = NotificationHubService(db)

    async def upload_document(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
        file: BinaryIO,
        original_filename: str,
        mime_type: str,
        category: str | None = None,
        linked_student_id: uuid.UUID | None = None,
        expires_at: datetime | None = None,
    ) -> dict:
        if role == "STD":
            raise AuthorizationError(
                "Students cannot upload documents",
                error_code="ERR-DOC-403",
            )
        if linked_student_id is not None and role not in {"PAR", "ADM", "DIR"}:
            raise AuthorizationError(
                "Only parents and administrators can link uploads to students",
                error_code="ERR-DOC-403",
            )

        category = category or DocumentCategory.OTHER.value
        content = file.read()
        if not isinstance(content, bytes):
            content = bytes(content)
        sha256 = file_storage_service.compute_sha256(content)
        deduplicated = False
        existing = await self.repo.find_document_by_sha(school_id=school_id, sha256=sha256)

        thumbnail_path: str | None = None
        if existing:
            storage_path, thumbnail_path = await file_storage_service.reuse_upload(
                storage_path=existing.storage_path,
                thumbnail_path=existing.thumbnail_path,
            )
            deduplicated = True
        else:
            storage_path, thumbnail_path = await file_storage_service.store_upload(
                content=content,
                original_filename=original_filename,
                mime_type=mime_type,
                sha256=sha256,
            )
            thumbnail_path = thumbnail_path or None

        if linked_student_id is not None:
            await self._verify_student_access_for_link(
                school_id=school_id,
                actor_id=user_id,
                actor_role=role,
                student_id=linked_student_id,
            )

        document = Document(
            school_id=school_id,
            uploader_id=user_id,
            filename=os.path.basename(storage_path),
            original_filename=original_filename,
            mime_type=mime_type,
            size_bytes=len(content),
            sha256=sha256,
            storage_path=storage_path,
            thumbnail_path=thumbnail_path,
            category=category,
            linked_student_id=linked_student_id,
            expires_at=expires_at,
        )
        await self.repo.create_document(document)
        DOCUMENT_UPLOAD_COUNT.labels(
            env=settings.app_env,
            mime_type=mime_type,
            deduplicated=str(deduplicated).lower(),
        ).inc()
        DOCUMENT_UPLOAD_SIZE_BYTES.labels(
            env=settings.app_env,
            mime_type=mime_type,
        ).inc(len(content))
        if not deduplicated:
            DOCUMENT_STORAGE_TOTAL_BYTES.labels(env=settings.app_env).inc(len(content))
        return await self.serialize_document(
            document,
            role=role,
            actor_id=user_id,
            deduplicated=deduplicated,
        )

    async def list_documents(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
        category: str | None,
        owner: str | None,
        mime_type: str | None,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[dict], str | None, bool]:
        owner_id: uuid.UUID | None = None
        if owner:
            if owner == "me":
                owner_id = user_id
            else:
                if role not in {"ADM", "DIR"}:
                    raise AuthorizationError(
                        "Only administrators can filter by another owner",
                        error_code="ERR-DOC-403",
                    )
                owner_id = uuid.UUID(owner)

        allowed_students = await self._allowed_student_ids(
            school_id=school_id,
            actor_id=user_id,
            actor_role=role,
        )
        rows, next_cursor, has_more = await self.repo.list_documents(
            school_id=school_id,
            role=role,
            user_id=user_id,
            category=category,
            owner_id=owner_id,
            mime_type=mime_type,
            cursor=cursor,
            limit=limit,
            allowed_student_ids=allowed_students,
        )
        items = [
            await self.serialize_document(
                document,
                role=role,
                actor_id=user_id,
                uploader_name=uploader_name,
                student_name=student_name,
            )
            for document, uploader_name, student_name in rows
        ]
        return items, next_cursor, has_more

    async def get_document_options(
        self,
        *,
        school_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_role: str,
    ) -> dict:
        if actor_role in {"ADM", "DIR"}:
            students = await self.repo.list_students_in_school(school_id=school_id)
        else:
            student_ids = await self._allowed_student_ids(
                school_id=school_id,
                actor_id=actor_id,
                actor_role=actor_role,
            )
            students = await self.repo.list_users_by_ids(
                school_id=school_id,
                user_ids=student_ids,
            )
        return {
            "students": [
                {
                    "id": str(student.id),
                    "full_name": student.full_name,
                    "email": student.email,
                }
                for student in students
            ],
            "categories": [item.value for item in DocumentCategory],
        }

    async def get_document_for_actor(
        self,
        *,
        document_id: uuid.UUID,
        school_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_role: str,
    ) -> Document:
        document = await self.repo.get_document(document_id)
        if document is None or document.school_id != school_id or document.deleted_at is not None:
            raise NotFoundError("Document not found", error_code="ERR-DOC-404")
        await self._enforce_document_visibility(
            document=document,
            school_id=school_id,
            actor_id=actor_id,
            actor_role=actor_role,
        )
        return document

    async def link_document_to_student(
        self,
        *,
        document_id: uuid.UUID,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_role: str,
        category: str,
        expires_at: datetime | None,
    ) -> dict:
        if actor_role not in {"PAR", "ADM", "DIR"}:
            raise AuthorizationError(
                "Only parents and administrators can link student documents",
                error_code="ERR-DOC-403",
            )
        await self._verify_student_access_for_link(
            school_id=school_id,
            actor_id=actor_id,
            actor_role=actor_role,
            student_id=student_id,
        )
        document = await self.get_document_for_actor(
            document_id=document_id,
            school_id=school_id,
            actor_id=actor_id,
            actor_role=actor_role,
        )
        document.linked_student_id = student_id
        document.category = category
        document.expires_at = expires_at
        await self.repo.save_document(document)
        return await self.serialize_document(
            document,
            role=actor_role,
            actor_id=actor_id,
        )

    async def list_student_documents(
        self,
        *,
        school_id: uuid.UUID,
        student_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_role: str,
    ) -> list[dict]:
        await self._verify_student_view_access(
            school_id=school_id,
            actor_id=actor_id,
            actor_role=actor_role,
            student_id=student_id,
        )
        rows = await self.repo.list_student_documents(
            school_id=school_id,
            student_id=student_id,
        )
        return [
            await self.serialize_document(
                document,
                role=actor_role,
                actor_id=actor_id,
                uploader_name=uploader_name,
            )
            for document, uploader_name in rows
        ]

    async def get_student_checklist(
        self,
        *,
        school_id: uuid.UUID,
        student_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_role: str,
    ) -> list[dict]:
        await self._verify_student_view_access(
            school_id=school_id,
            actor_id=actor_id,
            actor_role=actor_role,
            student_id=student_id,
        )
        requirements = await self.ensure_default_requirements(school_id=school_id)
        documents = await self.repo.list_student_documents(
            school_id=school_id,
            student_id=student_id,
        )
        latest_by_category: dict[str, Document] = {}
        uploader_names: dict[uuid.UUID, str | None] = {}
        for document, uploader_name in documents:
            if document.category not in latest_by_category:
                latest_by_category[document.category] = document
                uploader_names[document.id] = uploader_name

        items: list[dict] = []
        now = _utc_now()
        for requirement in requirements:
            document = latest_by_category.get(requirement.category)
            status = "missing"
            if document:
                status = "expired" if document.expires_at and document.expires_at <= now else "uploaded"
            items.append(
                {
                    "category": requirement.category,
                    "required": requirement.required,
                    "description": requirement.description,
                    "status": status,
                    "expires_at": document.expires_at.isoformat() if document and document.expires_at else None,
                    "document": await self.serialize_document(
                        document,
                        role=actor_role,
                        actor_id=actor_id,
                        uploader_name=uploader_names.get(document.id) if document else None,
                    )
                    if document
                    else None,
                }
            )
        return items

    async def delete_document(
        self,
        *,
        document_id: uuid.UUID,
        school_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_role: str,
        hard_delete: bool,
    ) -> dict:
        document = await self.get_document_for_actor(
            document_id=document_id,
            school_id=school_id,
            actor_id=actor_id,
            actor_role=actor_role,
        )
        if hard_delete:
            if actor_role not in {"ADM", "DIR"}:
                raise AuthorizationError(
                    "Only administrators can hard delete documents",
                    error_code="ERR-DOC-403",
                )
        elif actor_role not in {"ADM", "DIR"} and document.uploader_id != actor_id:
            raise NotFoundError("Document not found", error_code="ERR-DOC-404")

        if hard_delete:
            await self.repo.hard_delete_document(document)
            await self._delete_underlying_files_if_unused(document=document)
        else:
            document.deleted_at = _utc_now()
            await self.repo.save_document(document)
        return {
            "id": str(document.id),
            "deleted": True,
            "hard_deleted": hard_delete,
        }

    async def bulk_delete_documents(
        self,
        *,
        document_ids: Iterable[uuid.UUID],
        school_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_role: str,
    ) -> dict:
        if actor_role != "ADM":
            raise AuthorizationError(
                "Only administrators can bulk delete documents",
                error_code="ERR-DOC-403",
            )
        unique_ids = list(dict.fromkeys(document_ids))
        documents = {
            document.id: document
            for document in await self.repo.list_documents_by_ids(
                school_id=school_id,
                document_ids=unique_ids,
            )
        }

        deleted_ids: list[str] = []
        for document_id in unique_ids:
            document = documents.get(document_id)
            if document is None or document.deleted_at is not None:
                raise NotFoundError("Document not found", error_code="ERR-DOC-404")
            document.deleted_at = _utc_now()
            await self.repo.save_document(document)
            deleted_ids.append(str(document.id))

        return {
            "deleted": len(deleted_ids),
            "ids": deleted_ids,
            "hard_deleted": False,
        }

    async def create_bulk_download(
        self,
        *,
        document_ids: Iterable[uuid.UUID],
        school_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_role: str,
    ) -> dict:
        unique_ids = list(dict.fromkeys(document_ids))
        if not unique_ids:
            raise ValidationError("document_ids are required", error_code="ERR-DOC-422")

        documents = {
            document.id: document
            for document in await self.repo.list_documents_by_ids(
                school_id=school_id,
                document_ids=unique_ids,
            )
        }
        scoped_documents: list[Document] = []
        for document_id in unique_ids:
            document = documents.get(document_id)
            if document is None or document.deleted_at is not None:
                raise NotFoundError("Document not found", error_code="ERR-DOC-404")
            await self._enforce_document_visibility(
                document=document,
                school_id=school_id,
                actor_id=actor_id,
                actor_role=actor_role,
            )
            scoped_documents.append(document)

        archive_dir = Path(tempfile.gettempdir()) / "ecole-platform-bulk-downloads"
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive_name = (
            f"documents_{_utc_now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}.zip"
        )
        archive_path = archive_dir / archive_name
        used_names: set[str] = set()
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for document in scoped_documents:
                local_path = await self.read_document_file(document=document)
                archive.write(
                    local_path,
                    arcname=self._unique_archive_name(
                        document.original_filename,
                        used_names,
                    ),
                )

        token = self.build_bulk_download_token(
            archive_path=str(archive_path),
            filename=archive_name,
        )
        return {
            "document_count": len(scoped_documents),
            "filename": archive_name,
            "download_url": f"/api/v1/documents/bulk-download?token={token}",
        }

    def build_access_token(
        self,
        *,
        document_id: uuid.UUID,
        action: str,
    ) -> str:
        exp = _utc_now() + timedelta(hours=settings.document_download_ttl_hours)
        return jwt.encode(
            {
                "document_id": str(document_id),
                "action": action,
                "exp": exp,
            },
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

    def parse_access_token(self, *, token: str, action: str) -> uuid.UUID:
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
            )
        except JWTError as exc:
            raise NotFoundError("Document not found", error_code="ERR-DOC-404") from exc
        if payload.get("action") != action:
            raise NotFoundError("Document not found", error_code="ERR-DOC-404")
        return uuid.UUID(payload["document_id"])

    def build_bulk_download_token(
        self,
        *,
        archive_path: str,
        filename: str,
    ) -> str:
        exp = _utc_now() + timedelta(hours=settings.document_download_ttl_hours)
        return jwt.encode(
            {
                "archive_path": archive_path,
                "filename": filename,
                "action": DOCUMENT_BULK_DOWNLOAD_ACTION,
                "exp": exp,
            },
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

    def parse_bulk_download_token(self, *, token: str) -> tuple[Path, str]:
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
            )
        except JWTError as exc:
            raise NotFoundError("Bulk download not found", error_code="ERR-DOC-404") from exc
        if payload.get("action") != DOCUMENT_BULK_DOWNLOAD_ACTION:
            raise NotFoundError("Bulk download not found", error_code="ERR-DOC-404")
        archive_path = Path(str(payload["archive_path"]))
        if not archive_path.exists():
            raise NotFoundError("Bulk download not found", error_code="ERR-DOC-404")
        return archive_path, str(payload.get("filename") or archive_path.name)

    async def get_document_for_token(
        self,
        *,
        token: str,
        action: str,
    ) -> Document:
        document_id = self.parse_access_token(token=token, action=action)
        document = await self.repo.get_document(document_id)
        if document is None or document.deleted_at is not None:
            raise NotFoundError("Document not found", error_code="ERR-DOC-404")
        return document

    async def read_document_file(
        self,
        *,
        document: Document,
    ):
        document.download_count += 1
        await self.repo.save_document(document)
        return await file_storage_service.local_path(document.storage_path)

    async def read_document_preview(
        self,
        *,
        document: Document,
    ):
        preview_path = document.thumbnail_path
        if preview_path and await file_storage_service.exists(preview_path):
            return await file_storage_service.local_path(preview_path)
        if document.mime_type.startswith("image/") or document.mime_type == "application/pdf":
            return await file_storage_service.local_path(document.storage_path)
        raise NotFoundError("Preview not available", error_code="ERR-DOC-404")

    async def get_bulk_download_archive(
        self,
        *,
        token: str,
    ) -> tuple[Path, str]:
        return self.parse_bulk_download_token(token=token)

    async def ensure_default_requirements(
        self,
        *,
        school_id: uuid.UUID,
    ) -> list[StudentDocumentRequirement]:
        existing = await self.repo.list_student_requirements(school_id=school_id)
        if existing:
            return existing
        for category, required, description in DEFAULT_REQUIREMENTS:
            await self.repo.save_requirement(
                StudentDocumentRequirement(
                    school_id=school_id,
                    category=category,
                    required=required,
                    description=description,
                )
            )
        return await self.repo.list_student_requirements(school_id=school_id)

    async def check_expiring_documents(self, *, now: datetime | None = None) -> int:
        now = now or _utc_now()
        window_end = now + timedelta(days=settings.document_expiry_notice_days)
        documents = await self.repo.list_expiring_documents(
            window_start=now,
            window_end=window_end,
        )
        created = 0
        for document in documents:
            if document.linked_student_id is None:
                continue
            recipient_ids = {document.uploader_id}
            recipient_ids.update(
                await self.repo.list_parent_ids_for_student(
                    student_id=document.linked_student_id,
                    school_id=document.school_id,
                )
            )
            message = (
                f"Document {document.original_filename} expires on "
                f"{document.expires_at.date().isoformat()}"
                if document.expires_at
                else f"Document {document.original_filename} expires soon"
            )
            expiry_key = (
                document.expires_at.date().isoformat()
                if document.expires_at
                else "unknown"
            )
            for recipient_id in recipient_ids:
                idempotency_key = (
                    f"document-expiry:{document.id}:{recipient_id}:{expiry_key}"
                )
                if await self.repo.notification_exists(idempotency_key=idempotency_key):
                    continue
                await self.notification_hub.create_single_notification(
                    school_id=document.school_id,
                    user_id=recipient_id,
                    title="Document expiration reminder",
                    body=message,
                    category=NotificationCategory.SYSTEM.value,
                    action_url=f"/documents?student={document.linked_student_id}",
                    event_ref="document.expiring",
                    preferred_channels=["in_app", "push"],
                    idempotency_key=idempotency_key,
                )
                created += 1
        return created

    async def notify_expiring_documents(self, *, now: datetime | None = None) -> int:
        return await self.check_expiring_documents(now=now)

    async def cleanup_deleted_documents(self, *, now: datetime | None = None) -> int:
        now = now or _utc_now()
        cutoff = now - timedelta(days=settings.document_deleted_retention_days)
        documents = await self.repo.list_deleted_documents(before=cutoff)
        deleted = 0
        for document in documents:
            await self.repo.hard_delete_document(document)
            await self._delete_underlying_files_if_unused(document=document)
            deleted += 1
        return deleted

    async def serialize_document(
        self,
        document: Document | None,
        *,
        role: str,
        actor_id: uuid.UUID,
        uploader_name: str | None = None,
        student_name: str | None = None,
        deduplicated: bool = False,
    ) -> dict | None:
        if document is None:
            return None
        now = _utc_now()
        download_token = self.build_access_token(
            document_id=document.id,
            action=DOCUMENT_DOWNLOAD_ACTION,
        )
        preview_token = self.build_access_token(
            document_id=document.id,
            action=DOCUMENT_PREVIEW_ACTION,
        )
        can_hard_delete = role in {"ADM", "DIR"}
        can_delete = can_hard_delete or document.uploader_id == actor_id
        preview_url = None
        if document.thumbnail_path or document.mime_type.startswith("image/") or document.mime_type == "application/pdf":
            preview_url = f"/api/v1/documents/{document.id}/preview?token={preview_token}"
        return {
            "id": str(document.id),
            "filename": document.filename,
            "original_filename": document.original_filename,
            "mime_type": document.mime_type,
            "size_bytes": document.size_bytes,
            "sha256": document.sha256,
            "category": document.category,
            "linked_student_id": str(document.linked_student_id) if document.linked_student_id else None,
            "linked_student_name": student_name,
            "uploader_id": str(document.uploader_id),
            "uploader_name": uploader_name,
            "expires_at": document.expires_at.isoformat() if document.expires_at else None,
            "is_expired": bool(document.expires_at and document.expires_at <= now),
            "is_expiring_soon": bool(
                document.expires_at
                and now < document.expires_at <= now + timedelta(days=settings.document_expiry_notice_days)
            ),
            "download_count": document.download_count,
            "thumbnail_url": preview_url if document.thumbnail_path else None,
            "preview_url": preview_url,
            "download_url": f"/api/v1/documents/{document.id}/download?token={download_token}",
            "created_at": document.created_at.isoformat(),
            "deleted_at": document.deleted_at.isoformat() if document.deleted_at else None,
            "deduplicated": deduplicated,
            "can_delete": can_delete,
            "can_hard_delete": can_hard_delete,
        }

    async def _verify_student_access_for_link(
        self,
        *,
        school_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_role: str,
        student_id: uuid.UUID,
    ) -> None:
        student = await self.repo.get_user_in_school(user_id=student_id, school_id=school_id)
        if student is None:
            raise NotFoundError("Student not found", error_code="ERR-DOC-404")
        await self._verify_student_view_access(
            school_id=school_id,
            actor_id=actor_id,
            actor_role=actor_role,
            student_id=student_id,
        )

    async def _verify_student_view_access(
        self,
        *,
        school_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_role: str,
        student_id: uuid.UUID,
    ) -> None:
        if actor_role in {"ADM", "DIR"}:
            return
        if actor_role == "STD":
            if student_id != actor_id:
                raise NotFoundError("Student not found", error_code="ERR-DOC-404")
            return
        allowed_students = await self._allowed_student_ids(
            school_id=school_id,
            actor_id=actor_id,
            actor_role=actor_role,
        )
        if student_id not in allowed_students:
            raise NotFoundError("Student not found", error_code="ERR-DOC-404")

    async def _allowed_student_ids(
        self,
        *,
        school_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_role: str,
    ) -> set[uuid.UUID]:
        if actor_role == "PAR":
            return await self.repo.list_parent_child_ids(
                parent_id=actor_id,
                school_id=school_id,
            )
        if actor_role == "TCH":
            class_ids = await self.repo.list_teacher_class_ids(
                teacher_id=actor_id,
                school_id=school_id,
            )
            return await self.repo.list_students_for_classes(
                school_id=school_id,
                class_ids=class_ids,
            )
        if actor_role == "STD":
            return {actor_id}
        return set()

    async def _enforce_document_visibility(
        self,
        *,
        document: Document,
        school_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_role: str,
    ) -> None:
        if document.school_id != school_id:
            raise NotFoundError("Document not found", error_code="ERR-DOC-404")
        if actor_role in {"ADM", "DIR"}:
            return
        if document.uploader_id == actor_id:
            return
        if document.linked_student_id is None:
            raise NotFoundError("Document not found", error_code="ERR-DOC-404")
        await self._verify_student_view_access(
            school_id=school_id,
            actor_id=actor_id,
            actor_role=actor_role,
            student_id=document.linked_student_id,
        )

    def _unique_archive_name(self, original_filename: str, used_names: set[str]) -> str:
        candidate = original_filename or "document"
        stem = Path(candidate).stem or "document"
        suffix = Path(candidate).suffix
        counter = 1
        while candidate in used_names:
            candidate = f"{stem}_{counter}{suffix}"
            counter += 1
        used_names.add(candidate)
        return candidate

    async def _delete_underlying_files_if_unused(self, *, document: Document) -> None:
        remaining = await self.repo.count_documents_for_storage_path(
            storage_path=document.storage_path,
            exclude_document_id=document.id,
        )
        if remaining == 0:
            await file_storage_service.delete(document.storage_path)
            DOCUMENT_STORAGE_TOTAL_BYTES.labels(env=settings.app_env).dec(document.size_bytes)
            if document.thumbnail_path:
                await file_storage_service.delete(document.thumbnail_path)
