"""Phase 16 student documents and generic document lifecycle service."""

from __future__ import annotations

import logging
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
from app.core.unit_of_work import UnitOfWork
from app.domain.events.documents import DocumentExpiring, DocumentUploaded
from app.models.com import NotificationCategory
from app.models.documents import (
    Document,
    DocumentCategory,
    DocumentVersion,
    StudentDocumentRequirement,
)
from app.repositories.documents import DocumentsRepository
from app.schemas.documents import DocumentVersionResponse
from app.services.delivery.base import DeliveryStrategy
from app.services.audit import AuditService
from app.services.event_dispatcher import EventDispatcher
from app.services.file_storage import file_storage_service
from app.services.notification_hub import NotificationHubService

DOCUMENT_DOWNLOAD_ACTION = "document.download"
DOCUMENT_PREVIEW_ACTION = "document.preview"
DOCUMENT_BULK_DOWNLOAD_ACTION = "document.bulk-download"
logger = logging.getLogger(__name__)


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
        self._dispatcher = EventDispatcher(self.db)
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
        if self.db.info.get("_uow_depth"):
            payload = await self._upload_document_with_repo(
                repo=DocumentsRepository(self.db),
                school_id=school_id,
                user_id=user_id,
                role=role,
                file=file,
                original_filename=original_filename,
                mime_type=mime_type,
                category=category,
                linked_student_id=linked_student_id,
                expires_at=expires_at,
            )
            self.db.info.setdefault("_pending_domain_events", []).append(
                self._build_document_uploaded_event(
                    school_id=school_id,
                    actor_id=user_id,
                    payload=payload,
                    linked_student_id=linked_student_id,
                )
            )
            return payload

        async with UnitOfWork(self.db) as uow:
            payload = await self._upload_document_with_repo(
                repo=DocumentsRepository(uow.session),
                school_id=school_id,
                user_id=user_id,
                role=role,
                file=file,
                original_filename=original_filename,
                mime_type=mime_type,
                category=category,
                linked_student_id=linked_student_id,
                expires_at=expires_at,
            )
            await uow.commit()

        try:
            await self._dispatcher.dispatch(
                self._build_document_uploaded_event(
                    school_id=school_id,
                    actor_id=user_id,
                    payload=payload,
                    linked_student_id=linked_student_id,
                )
            )
        except Exception:
            logger.exception(
                "Failed to dispatch DocumentUploaded for %s",
                payload["id"],
            )

        return payload

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

    async def list_versions(
        self,
        *,
        document_id: uuid.UUID,
        school_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_role: str,
    ) -> list[dict]:
        document = await self.get_document_for_actor(
            document_id=document_id,
            school_id=school_id,
            actor_id=actor_id,
            actor_role=actor_role,
        )
        versions = await self.repo.list_document_versions(document_id=document.id)
        return [self._version_to_response(version) for version in versions]

    async def get_version(
        self,
        *,
        document_id: uuid.UUID,
        version_number: int,
        school_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_role: str,
    ) -> tuple[DocumentVersion, Path]:
        document = await self.get_document_for_actor(
            document_id=document_id,
            school_id=school_id,
            actor_id=actor_id,
            actor_role=actor_role,
        )
        version = await self.repo.get_document_version(
            document_id=document.id,
            version_number=version_number,
        )
        if version is None:
            raise NotFoundError("Document version not found", error_code="ERR-DOC-404")
        return version, await file_storage_service.local_path(version.storage_path)

    async def restore_version(
        self,
        *,
        document_id: uuid.UUID,
        version_number: int,
        school_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_role: str,
        ip_address: str | None,
    ) -> dict:
        document = await self.get_document_for_actor(
            document_id=document_id,
            school_id=school_id,
            actor_id=actor_id,
            actor_role=actor_role,
        )
        if actor_role not in {"ADM", "DIR"} and document.uploader_id != actor_id:
            raise AuthorizationError(
                "Only the uploader or an administrator can restore document versions",
                error_code="ERR-DOC-403",
            )

        version = await self.repo.get_document_version(
            document_id=document.id,
            version_number=version_number,
        )
        if version is None:
            raise NotFoundError("Document version not found", error_code="ERR-DOC-404")

        content = (await file_storage_service.local_path(version.storage_path)).read_bytes()
        async with UnitOfWork(self.db) as uow:
            repo = DocumentsRepository(uow.session)
            audit = AuditService(uow.session)
            stored_document = await repo.get_document(document.id)
            await self._capture_document_version(
                repo=repo,
                document=stored_document,
                change_note=f"Snapshot before restoring v{version_number}",
            )
            storage_path, thumbnail_path = await file_storage_service.store_upload_copy(
                content=content,
                original_filename=version.original_filename,
                mime_type=version.mime_type,
            )
            stored_document.uploader_id = actor_id
            stored_document.filename = os.path.basename(storage_path)
            stored_document.original_filename = version.original_filename
            stored_document.mime_type = version.mime_type
            stored_document.size_bytes = version.size_bytes
            stored_document.sha256 = version.sha256
            stored_document.storage_path = storage_path
            stored_document.thumbnail_path = thumbnail_path or None
            await repo.save_document(stored_document)
            await audit.log_event(
                school_id=school_id,
                actor_id=actor_id,
                action_type="document.version.restore",
                target_type="document",
                target_id=stored_document.id,
                outcome="success",
                entity_after={
                    "document_id": str(stored_document.id),
                    "restored_version": version_number,
                },
                ip_address=ip_address,
            )
            await uow.commit()

        DOCUMENT_STORAGE_TOTAL_BYTES.labels(env=settings.app_env).inc(version.size_bytes)
        return await self.serialize_document(
            stored_document,
            role=actor_role,
            actor_id=actor_id,
        )

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
        async with UnitOfWork(self.db) as uow:
            repo = DocumentsRepository(uow.session)
            await repo.save_document(document)
            await uow.commit()
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

        version_assets = []
        if hard_delete:
            version_assets = [
                (version.storage_path, version.size_bytes, version.thumbnail_path)
                for version in await self.repo.list_document_versions(document_id=document.id)
            ]

        async with UnitOfWork(self.db) as uow:
            repo = DocumentsRepository(uow.session)
            if hard_delete:
                await repo.hard_delete_document(document)
            else:
                document.deleted_at = _utc_now()
                await repo.save_document(document)
            await uow.commit()
        if hard_delete:
            seen_storage_paths = {document.storage_path}
            await self._delete_underlying_files_if_unused(
                storage_path=document.storage_path,
                size_bytes=document.size_bytes,
                thumbnail_path=document.thumbnail_path,
                exclude_document_id=document.id,
            )
            for storage_path, size_bytes, thumbnail_path in version_assets:
                if storage_path in seen_storage_paths:
                    continue
                seen_storage_paths.add(storage_path)
                await self._delete_underlying_files_if_unused(
                    storage_path=storage_path,
                    size_bytes=size_bytes,
                    thumbnail_path=thumbnail_path,
                )
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
        async with UnitOfWork(self.db) as uow:
            repo = DocumentsRepository(uow.session)
            for document_id in unique_ids:
                document = documents.get(document_id)
                if document is None or document.deleted_at is not None:
                    raise NotFoundError("Document not found", error_code="ERR-DOC-404")
                document.deleted_at = _utc_now()
                await repo.save_document(document)
                deleted_ids.append(str(document.id))
            await uow.commit()

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
        if self.db.info.get("_uow_depth"):
            document.download_count += 1
            await DocumentsRepository(self.db).save_document(document)
            return await file_storage_service.local_path(document.storage_path)

        async with UnitOfWork(self.db) as uow:
            repo = DocumentsRepository(uow.session)
            document.download_count += 1
            await repo.save_document(document)
            await uow.commit()
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
        if self.db.info.get("_uow_depth"):
            return await self._ensure_default_requirements_with_repo(
                repo=DocumentsRepository(self.db),
                school_id=school_id,
            )

        async with UnitOfWork(self.db) as uow:
            repo = DocumentsRepository(uow.session)
            requirements = await self._ensure_default_requirements_with_repo(
                repo=repo,
                school_id=school_id,
            )
            await uow.commit()
            return requirements

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
            event = DocumentExpiring(
                school_id=document.school_id,
                actor_id=document.uploader_id,
                document_id=document.id,
                student_id=document.linked_student_id,
                document_name=document.original_filename,
                expires_at=document.expires_at.isoformat() if document.expires_at else "",
            )
            pending_recipients: list[tuple[uuid.UUID, str]] = []
            for recipient_id in recipient_ids:
                domain_key = DeliveryStrategy.build_notification_idempotency_key(
                    event=event,
                    recipient_id=recipient_id,
                    template_key="document_expiring",
                )
                if await self.repo.notification_exists(idempotency_key=domain_key):
                    continue
                pending_recipients.append((recipient_id, domain_key))

            if not pending_recipients:
                continue

            try:
                await self._dispatcher.dispatch(event)
                created += len(pending_recipients)
            except Exception:
                logger.exception(
                    "Failed to dispatch DocumentExpiring for %s",
                    document.id,
                )
                for recipient_id, _domain_key in pending_recipients:
                    idempotency_key = (
                        f"document-expiry:{document.id}:{recipient_id}:{expiry_key}"
                    )
                    # TODO: Remove after event dispatcher verification
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
        asset_cleanup_queue: list[tuple[str, int, str | None, uuid.UUID | None]] = []
        async with UnitOfWork(self.db) as uow:
            repo = DocumentsRepository(uow.session)
            for document in documents:
                versions = await repo.list_document_versions(document_id=document.id)
                asset_cleanup_queue.append(
                    (
                        document.storage_path,
                        document.size_bytes,
                        document.thumbnail_path,
                        document.id,
                    )
                )
                asset_cleanup_queue.extend(
                    (version.storage_path, version.size_bytes, version.thumbnail_path, None)
                    for version in versions
                )
                await repo.hard_delete_document(document)
                deleted += 1
            await uow.commit()
        seen_storage_paths: set[str] = set()
        for storage_path, size_bytes, thumbnail_path, exclude_document_id in asset_cleanup_queue:
            if storage_path in seen_storage_paths:
                continue
            seen_storage_paths.add(storage_path)
            await self._delete_underlying_files_if_unused(
                storage_path=storage_path,
                size_bytes=size_bytes,
                thumbnail_path=thumbnail_path,
                exclude_document_id=exclude_document_id,
            )
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

    async def _delete_underlying_files_if_unused(
        self,
        *,
        storage_path: str,
        size_bytes: int,
        thumbnail_path: str | None,
        exclude_document_id: uuid.UUID | None = None,
    ) -> None:
        remaining = await self.repo.count_documents_for_storage_path(
            storage_path=storage_path,
            exclude_document_id=exclude_document_id,
        )
        if remaining == 0:
            await file_storage_service.delete(storage_path)
            DOCUMENT_STORAGE_TOTAL_BYTES.labels(env=settings.app_env).dec(size_bytes)
            if thumbnail_path:
                thumb_refs = await self.repo.count_thumbnail_references(
                    thumbnail_path=thumbnail_path,
                    exclude_document_id=exclude_document_id,
                )
                if thumb_refs == 0:
                    await file_storage_service.delete(thumbnail_path)

    def _version_to_response(self, version: DocumentVersion) -> dict:
        return DocumentVersionResponse(
            document_id=str(version.document_id),
            version_number=version.version_number,
            uploader_id=str(version.uploader_id),
            filename=version.filename,
            original_filename=version.original_filename,
            mime_type=version.mime_type,
            size_bytes=version.size_bytes,
            sha256=version.sha256,
            change_note=version.change_note,
            created_at=version.created_at.isoformat(),
        ).model_dump()

    async def _capture_document_version(
        self,
        *,
        repo: DocumentsRepository,
        document: Document,
        change_note: str | None,
    ) -> DocumentVersion:
        version_number = await repo.get_next_document_version_number(document_id=document.id)
        version = DocumentVersion(
            document_id=document.id,
            version_number=version_number,
            uploader_id=document.uploader_id,
            filename=document.filename,
            original_filename=document.original_filename,
            mime_type=document.mime_type,
            storage_path=document.storage_path,
            thumbnail_path=document.thumbnail_path,
            size_bytes=document.size_bytes,
            sha256=document.sha256,
            change_note=change_note,
        )
        return await repo.create_document_version(version)

    async def _upload_document_with_repo(
        self,
        *,
        repo: DocumentsRepository,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
        file: BinaryIO,
        original_filename: str,
        mime_type: str,
        category: str | None,
        linked_student_id: uuid.UUID | None,
        expires_at: datetime | None,
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
        existing_document: Document | None = None
        if linked_student_id is not None:
            await self._verify_student_access_for_link(
                school_id=school_id,
                actor_id=user_id,
                actor_role=role,
                student_id=linked_student_id,
            )
            existing_document = await repo.find_document_for_student_category(
                school_id=school_id,
                linked_student_id=linked_student_id,
                category=category,
            )

        content = file.read()
        if not isinstance(content, bytes):
            content = bytes(content)
        sha256 = file_storage_service.compute_sha256(content)
        deduplicated = False
        existing = await repo.find_document_by_sha(school_id=school_id, sha256=sha256)

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
        if existing_document is not None:
            await self._capture_document_version(
                repo=repo,
                document=existing_document,
                change_note="Superseded by a newer upload",
            )
            existing_document.uploader_id = user_id
            existing_document.filename = os.path.basename(storage_path)
            existing_document.original_filename = original_filename
            existing_document.mime_type = mime_type
            existing_document.size_bytes = len(content)
            existing_document.sha256 = sha256
            existing_document.storage_path = storage_path
            existing_document.thumbnail_path = thumbnail_path
            existing_document.category = category
            existing_document.linked_student_id = linked_student_id
            existing_document.expires_at = expires_at
            document = await repo.save_document(existing_document)
        else:
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
            await repo.create_document(document)
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

    def _build_document_uploaded_event(
        self,
        *,
        school_id: uuid.UUID,
        actor_id: uuid.UUID,
        payload: dict,
        linked_student_id: uuid.UUID | None,
    ) -> DocumentUploaded:
        student_id = linked_student_id
        if student_id is None and payload.get("linked_student_id"):
            student_id = uuid.UUID(payload["linked_student_id"])
        return DocumentUploaded(
            school_id=school_id,
            actor_id=actor_id,
            document_id=uuid.UUID(payload["id"]),
            filename=payload["original_filename"],
            student_id=student_id,
        )

    async def _ensure_default_requirements_with_repo(
        self,
        *,
        repo: DocumentsRepository,
        school_id: uuid.UUID,
    ) -> list[StudentDocumentRequirement]:
        existing = await repo.list_student_requirements(school_id=school_id)
        if existing:
            return existing
        for category, required, description in DEFAULT_REQUIREMENTS:
            await repo.save_requirement(
                StudentDocumentRequirement(
                    school_id=school_id,
                    category=category,
                    required=required,
                    description=description,
                )
            )
        return await repo.list_student_requirements(school_id=school_id)
