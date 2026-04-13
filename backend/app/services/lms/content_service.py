"""Content LMS service."""

from __future__ import annotations

import os
import uuid
from typing import BinaryIO

from app.core.permissions import PLATFORM_ROLES
from app.core.dependencies import (
    AuthContext,
    verify_school_boundary,
    verify_teacher_assignment,
)
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.core.filtering import FilterSpec, SortSpec
from app.core.response import encode_cursor
from app.core.storage import storage, validate_mime_type
from app.core.unit_of_work import UnitOfWork
from app.models.documents import Document, DocumentCategory
from app.models.lms import ContentProgressStatus
from app.repositories.documents import DocumentsRepository
from app.repositories.lms import LMSRepository
from app.schemas.cms import ContentAssignRequest, ContentSubmitForReviewRequest
from app.schemas.lms import ContentCompleteRequest, ContentProgressRequest
from app.services.audit import AuditService
from app.services.file_storage import file_storage_service
from app.services.lms._helpers import LMSServiceBase, _utc_now
from app.services.rewards_service import RewardsService


class ContentService(LMSServiceBase):
    """Handles content items, assets, progress, and library workflows."""

    @staticmethod
    def _ensure_content_manage_scope(content_item, auth: AuthContext) -> None:
        if content_item.school_id is None:
            if auth.role not in PLATFORM_ROLES:
                raise AuthorizationError(
                    "Only platform roles can manage platform content assets",
                    error_code="ERR-LMS-403",
                )
            return
        verify_school_boundary(content_item.school_id, auth)

    async def list_content_items(
        self,
        *,
        content_type: str | None,
        level_band: str | None,
        language: str | None,
        letter: str | None,
        target_age: int | None,
        filters: FilterSpec,
        sort: SortSpec,
        search: str | None,
        cursor: str | None,
        limit: int,
        auth: AuthContext,
    ) -> tuple[list[dict], str | None, bool]:
        items_list, has_more = await self.repo.list_content_items(
            school_id=auth.school_id,
            content_type=content_type,
            level_band=level_band,
            language=language,
            letter=letter,
            target_age=target_age,
            filters=filters,
            sort=sort,
            search=search,
            cursor=cursor,
            limit=limit,
        )
        items = [self._content_item_to_dict(item) for item in items_list]
        next_cursor = (
            encode_cursor(items_list[-1].id) if has_more and items_list else None
        )
        return items, next_cursor, has_more

    async def update_content_progress(
        self,
        *,
        content_item_id: uuid.UUID,
        body: ContentProgressRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        content_item = await self.repo.get_content_item(content_item_id)
        if content_item is None:
            raise NotFoundError("Content item not found", error_code="ERR-LMS-404")
        if content_item.school_id is not None:
            verify_school_boundary(content_item.school_id, auth)

        async with UnitOfWork(self.db) as uow:
            repo = LMSRepository(uow.session)
            audit = AuditService(uow.session)
            progress = await repo.get_content_progress(
                student_id=auth.user_id,
                content_item_id=content_item_id,
            )
            if progress is not None:
                progress.status = body.status
                await repo.save_content_progress(progress)
            else:
                progress = await repo.create_content_progress(
                    student_id=auth.user_id,
                    content_item_id=content_item_id,
                    status=body.status,
                )
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="CONTENT_PROGRESS_UPDATED",
                outcome="success",
                target_type="content_progress",
                target_id=progress.id,
                entity_after={
                    "content_item_id": str(content_item_id),
                    "status": body.status,
                },
                ip_address=ip_address,
            )
            await uow.commit()

        return {
            "id": str(progress.id),
            "student_id": str(progress.student_id),
            "content_item_id": str(progress.content_item_id),
            "status": progress.status,
        }

    async def upload_content_asset(
        self,
        *,
        content_item_id: uuid.UUID,
        file: BinaryIO,
        filename: str,
        mime_type: str,
        page_number: int | None = None,
        narration_text: str | None = None,
        has_activity: bool = False,
        asset_type: str | None = None,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        content_item = await self.repo.get_content_item(content_item_id)
        if content_item is None:
            raise NotFoundError("Content item not found", error_code="ERR-LMS-404")
        self._ensure_content_manage_scope(content_item, auth)

        validate_mime_type(mime_type)
        relative_path, checksum, file_size = await storage.save(
            file,
            filename or "asset",
            subdirectory=f"content/{content_item_id}",
        )
        async with UnitOfWork(self.db) as uow:
            repo = LMSRepository(uow.session)
            audit = AuditService(uow.session)
            asset = await repo.create_content_asset(
                content_item_id=content_item_id,
                file_path=relative_path,
                checksum=checksum,
                mime_type=mime_type,
                file_size=file_size,
                page_number=page_number,
                narration_text=narration_text,
                has_activity=has_activity,
                asset_type=asset_type,
            )
            if page_number is not None:
                current_page_count = content_item.page_count or 0
                if page_number > current_page_count:
                    content_item.page_count = page_number
                    await repo.save_content_item(content_item)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="CONTENT_ASSET_UPLOADED",
                outcome="success",
                target_type="content_item_asset",
                target_id=asset.id,
                entity_after={
                    "content_item_id": str(content_item_id),
                    "file_path": relative_path,
                    "mime_type": mime_type,
                    "file_size": file_size,
                    "checksum": checksum,
                    "page_number": page_number,
                    "narration_text": narration_text,
                    "has_activity": has_activity,
                    "asset_type": asset_type,
                },
                ip_address=ip_address,
            )
            await uow.commit()

        return self._content_item_asset_to_dict(asset)

    async def list_story_pages(
        self,
        *,
        content_item_id: uuid.UUID,
        auth: AuthContext,
    ) -> list[dict]:
        await self.get_content_item(content_item_id=content_item_id, auth=auth)
        assets = await self.repo.list_content_assets(
            content_item_id=content_item_id,
            page_only=True,
        )
        return [self._content_item_asset_to_dict(asset) for asset in assets]

    async def complete_content_item(
        self,
        *,
        content_item_id: uuid.UUID,
        body: ContentCompleteRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        content_item = await self.repo.get_content_item(content_item_id)
        if content_item is None or content_item.status != "published":
            raise NotFoundError("Content item not found", error_code="ERR-LMS-404")
        if content_item.school_id is not None:
            verify_school_boundary(content_item.school_id, auth)

        async with UnitOfWork(self.db) as uow:
            repo = LMSRepository(uow.session)
            audit = AuditService(uow.session)
            rewards = RewardsService(uow.session)
            progress = await repo.get_content_progress(
                student_id=auth.user_id,
                content_item_id=content_item_id,
            )

            should_award = (
                progress is None
                or progress.status != ContentProgressStatus.COMPLETED.value
            )
            if progress is None:
                progress = await repo.create_content_progress(
                    student_id=auth.user_id,
                    content_item_id=content_item_id,
                    status=ContentProgressStatus.COMPLETED.value,
                )
            else:
                progress.status = ContentProgressStatus.COMPLETED.value
                await repo.save_content_progress(progress)

            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="CONTENT_COMPLETED",
                outcome="success",
                target_type="content_progress",
                target_id=progress.id,
                entity_after={
                    "content_item_id": str(content_item_id),
                    "status": progress.status,
                    "time_spent_seconds": body.time_spent_seconds,
                },
                ip_address=ip_address,
            )

            if should_award:
                reward_payload = await rewards.award(
                    student_id=auth.user_id,
                    event_type="content_completed",
                    stars=10,
                    xp=15,
                    source_type="content",
                    source_id=content_item_id,
                    metadata={
                        "time_spent_seconds": body.time_spent_seconds,
                        "content_type": content_item.content_type,
                    },
                )
            else:
                reward_payload = await rewards.get_student_rewards(
                    student_id=auth.user_id
                )
                reward_payload = {
                    **reward_payload,
                    "newly_earned_badges": [],
                }

            await uow.commit()

        return {
            "progress": {
                "id": str(progress.id),
                "student_id": str(progress.student_id),
                "content_item_id": str(progress.content_item_id),
                "status": progress.status,
            },
            "reward": {
                key: value
                for key, value in reward_payload.items()
                if key != "newly_earned_badges"
            },
            "newly_earned_badges": reward_payload.get("newly_earned_badges", []),
        }

    async def save_coloring_page(
        self,
        *,
        content_item_id: uuid.UUID,
        file: BinaryIO,
        filename: str,
        mime_type: str,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        content_item = await self.repo.get_content_item(content_item_id)
        if content_item is None or content_item.status != "published":
            raise NotFoundError("Content item not found", error_code="ERR-LMS-404")
        if content_item.school_id is not None:
            verify_school_boundary(content_item.school_id, auth)

        content = file.read()
        if not isinstance(content, bytes):
            content = bytes(content)
        sha256 = file_storage_service.compute_sha256(content)

        async with UnitOfWork(self.db) as uow:
            audit = AuditService(uow.session)
            documents_repo = DocumentsRepository(uow.session)
            rewards = RewardsService(uow.session)
            storage_path, thumbnail_path = await file_storage_service.store_upload(
                content=content,
                original_filename=filename or "coloring.png",
                mime_type=mime_type,
                sha256=sha256,
            )
            document = await documents_repo.create_document(
                Document(
                    school_id=auth.school_id,
                    uploader_id=auth.user_id,
                    filename=os.path.basename(storage_path),
                    original_filename=filename or "coloring.png",
                    mime_type=mime_type,
                    size_bytes=len(content),
                    sha256=sha256,
                    storage_path=storage_path,
                    thumbnail_path=thumbnail_path or None,
                    category=DocumentCategory.OTHER.value,
                    linked_student_id=auth.user_id,
                )
            )
            reward_payload = await rewards.award(
                student_id=auth.user_id,
                event_type="coloring_saved",
                stars=5,
                xp=8,
                source_type="coloring",
                source_id=content_item_id,
                metadata={
                    "content_type": content_item.content_type,
                    "mime_type": mime_type,
                },
            )
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="COLORING_SAVED",
                outcome="success",
                target_type="document",
                target_id=document.id,
                entity_after={
                    "document_id": str(document.id),
                    "content_item_id": str(content_item_id),
                    "storage_path": storage_path,
                    "mime_type": mime_type,
                },
                ip_address=ip_address,
            )
            await uow.commit()

        return {
            "document_id": str(document.id),
            "reward": {
                key: value
                for key, value in reward_payload.items()
                if key != "newly_earned_badges"
            },
            "newly_earned_badges": reward_payload.get("newly_earned_badges", []),
        }

    async def delete_content_asset(
        self,
        *,
        content_item_id: uuid.UUID,
        asset_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        asset = await self.repo.get_content_asset(
            content_item_id=content_item_id,
            asset_id=asset_id,
        )
        if asset is None:
            raise NotFoundError("Asset not found", error_code="ERR-UPLOAD-404")

        content_item = await self.repo.get_content_item(content_item_id)
        if content_item is None:
            raise NotFoundError("Content item not found", error_code="ERR-LMS-404")
        self._ensure_content_manage_scope(content_item, auth)

        entity_before = {
            "id": str(asset.id),
            "file_path": asset.file_path,
            "mime_type": asset.mime_type,
            "file_size": asset.file_size,
            "page_number": asset.page_number,
            "narration_text": asset.narration_text,
            "has_activity": asset.has_activity,
            "asset_type": asset.asset_type,
        }
        await storage.delete(asset.file_path)
        async with UnitOfWork(self.db) as uow:
            repo = LMSRepository(uow.session)
            audit = AuditService(uow.session)
            await repo.delete_content_asset(asset)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="CONTENT_ASSET_DELETED",
                outcome="success",
                target_type="content_item_asset",
                target_id=asset.id,
                entity_before=entity_before,
                ip_address=ip_address,
            )
            await uow.commit()

        return {"deleted": True, "id": entity_before["id"]}

    async def browse_content_library(
        self,
        *,
        content_type: str | None,
        level_band: str | None,
        subject: str | None,
        language: str | None,
        origin: str | None,
        letter: str | None,
        target_age: int | None,
        cursor: str | None,
        limit: int,
        auth: AuthContext,
    ) -> tuple[list[dict], str | None, bool]:
        items_list, has_more = await self.repo.browse_content_library(
            school_id=auth.school_id,
            content_type=content_type,
            level_band=level_band,
            subject=subject,
            language=language,
            origin=origin,
            letter=letter,
            target_age=target_age,
            cursor=cursor,
            limit=limit,
        )
        items = [
            {
                "id": str(content_item.id),
                "school_id": str(content_item.school_id)
                if content_item.school_id
                else None,
                "title": content_item.title,
                "content_type": content_item.content_type,
                "level_band": content_item.level_band,
                "language": content_item.language,
                "subject": content_item.subject,
                "description": content_item.description,
                "page_count": content_item.page_count,
                "letter": content_item.letter,
                "target_age_min": content_item.target_age_min,
                "target_age_max": content_item.target_age_max,
                "theme_color": content_item.theme_color,
                "origin": content_item.origin,
                "status": content_item.status,
            }
            for content_item in items_list
        ]
        next_cursor = (
            encode_cursor(items_list[-1].id) if has_more and items_list else None
        )
        return items, next_cursor, has_more

    async def assign_content_to_class(
        self,
        *,
        body: ContentAssignRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        teacher_classes = await self.repo.list_teacher_class_ids(
            teacher_id=auth.user_id,
            school_id=auth.school_id,
        )
        verify_teacher_assignment(body.class_id, teacher_classes)

        content_item = await self.repo.get_content_item(body.content_item_id)
        if content_item is None or content_item.status != "published":
            raise NotFoundError("Content item not found", error_code="ERR-CMS-404")
        if (
            content_item.school_id is not None
            and content_item.school_id != auth.school_id
        ):
            raise NotFoundError("Content item not found", error_code="ERR-CMS-404")

        duplicate = await self.repo.find_class_content_assignment(
            class_id=body.class_id,
            content_item_id=body.content_item_id,
        )
        if duplicate is not None:
            raise ValidationError(
                "Content already assigned to this class",
                error_code="ERR-CMS-409",
            )

        async with UnitOfWork(self.db) as uow:
            repo = LMSRepository(uow.session)
            audit = AuditService(uow.session)
            assignment = await repo.create_class_content_assignment(
                teacher_id=auth.user_id,
                class_id=body.class_id,
                content_item_id=body.content_item_id,
                school_id=auth.school_id,
                assigned_at=_utc_now(),
                notes=body.notes,
            )
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="CONTENT_ASSIGNED_TO_CLASS",
                outcome="success",
                target_type="class_content_assignment",
                target_id=assignment.id,
                entity_after={
                    "class_id": str(body.class_id),
                    "content_item_id": str(body.content_item_id),
                },
                ip_address=ip_address,
            )
            await uow.commit()

        return {
            "id": str(assignment.id),
            "teacher_id": str(assignment.teacher_id),
            "class_id": str(assignment.class_id),
            "content_item_id": str(assignment.content_item_id),
            "school_id": str(assignment.school_id),
            "assigned_at": assignment.assigned_at.isoformat(),
            "notes": assignment.notes,
        }

    async def unassign_content(
        self,
        *,
        assignment_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        assignment = await self.repo.get_class_content_assignment(assignment_id)
        if assignment is None:
            raise NotFoundError("Assignment not found", error_code="ERR-CMS-404")

        verify_school_boundary(assignment.school_id, auth)
        teacher_classes = await self.repo.list_teacher_class_ids(
            teacher_id=auth.user_id,
            school_id=auth.school_id,
        )
        verify_teacher_assignment(assignment.class_id, teacher_classes)

        entity_before = {
            "id": str(assignment.id),
            "class_id": str(assignment.class_id),
            "content_item_id": str(assignment.content_item_id),
        }
        async with UnitOfWork(self.db) as uow:
            repo = LMSRepository(uow.session)
            audit = AuditService(uow.session)
            await repo.delete_class_content_assignment(assignment)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="CONTENT_UNASSIGNED_FROM_CLASS",
                outcome="success",
                target_type="class_content_assignment",
                target_id=assignment.id,
                entity_before=entity_before,
                ip_address=ip_address,
            )
            await uow.commit()

        return {"deleted": True, "id": entity_before["id"]}

    async def submit_content_for_review(
        self,
        *,
        body: ContentSubmitForReviewRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        content_item = await self.repo.get_content_item(body.content_item_id)
        if content_item is None:
            raise NotFoundError("Content item not found", error_code="ERR-CMS-404")
        if content_item.school_id is None:
            raise ValidationError(
                "Platform-wide content cannot be submitted for review",
                error_code="ERR-CMS-400",
            )
        verify_school_boundary(content_item.school_id, auth)

        existing = await self.repo.find_active_content_submission(
            content_item_id=body.content_item_id,
            submitted_by=auth.user_id,
        )
        if existing is not None:
            raise ValidationError(
                "A submission for this content is already pending review",
                error_code="ERR-CMS-409",
            )

        async with UnitOfWork(self.db) as uow:
            repo = LMSRepository(uow.session)
            audit = AuditService(uow.session)
            submission = await repo.create_content_submission(
                content_item_id=body.content_item_id,
                submitted_by=auth.user_id,
                school_id=auth.school_id,
                status="PENDING",
                submitted_at=_utc_now(),
            )
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="CONTENT_SUBMITTED_FOR_REVIEW",
                outcome="success",
                target_type="content_submission",
                target_id=submission.id,
                entity_after={
                    "content_item_id": str(body.content_item_id),
                    "status": "PENDING",
                },
                ip_address=ip_address,
            )
            await uow.commit()

        return {
            "id": str(submission.id),
            "content_item_id": str(submission.content_item_id),
            "status": submission.status,
            "submitted_at": submission.submitted_at.isoformat()
            if submission.submitted_at
            else None,
        }

    async def list_my_content_submissions(
        self,
        *,
        status: str | None,
        cursor: str | None,
        limit: int,
        auth: AuthContext,
    ) -> tuple[list[dict], str | None, bool]:
        rows, has_more = await self.repo.list_my_content_submissions(
            submitted_by=auth.user_id,
            status=status,
            cursor=cursor,
            limit=limit,
        )
        items = [
            {
                "id": str(submission.id),
                "content_item_id": str(submission.content_item_id),
                "content_title": content_item.title,
                "status": submission.status,
                "submitted_at": submission.submitted_at.isoformat()
                if submission.submitted_at
                else None,
                "review_notes": submission.review_notes,
                "promoted_content_id": (
                    str(submission.promoted_content_id)
                    if submission.promoted_content_id
                    else None
                ),
            }
            for submission, content_item in rows
        ]
        next_cursor = encode_cursor(rows[-1][0].id) if has_more and rows else None
        return items, next_cursor, has_more

    async def list_class_content(
        self,
        *,
        class_id: uuid.UUID,
        cursor: str | None,
        limit: int,
        auth: AuthContext,
    ) -> tuple[list[dict], str | None, bool]:
        rows, has_more = await self.repo.list_class_content(
            class_id=class_id,
            school_id=auth.school_id,
            cursor=cursor,
            limit=limit,
        )
        items = [
            {
                "id": str(assignment.id),
                "content_item_id": str(assignment.content_item_id),
                "title": content_item.title,
                "content_type": content_item.content_type,
                "level_band": content_item.level_band,
                "language": content_item.language,
                "subject": content_item.subject,
                "description": content_item.description,
                "page_count": content_item.page_count,
                "letter": content_item.letter,
                "target_age_min": content_item.target_age_min,
                "target_age_max": content_item.target_age_max,
                "theme_color": content_item.theme_color,
                "assigned_at": assignment.assigned_at.isoformat()
                if assignment.assigned_at
                else None,
                "teacher_notes": assignment.notes,
            }
            for assignment, content_item in rows
        ]
        next_cursor = encode_cursor(rows[-1][0].id) if has_more and rows else None
        return items, next_cursor, has_more
