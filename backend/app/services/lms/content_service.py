"""Content LMS service."""

from __future__ import annotations

import uuid
from typing import BinaryIO

from app.core.dependencies import (
    AuthContext,
    verify_school_boundary,
    verify_teacher_assignment,
)
from app.core.exceptions import NotFoundError, ValidationError
from app.core.filtering import FilterSpec, SortSpec
from app.core.response import encode_cursor
from app.core.storage import storage, validate_mime_type
from app.core.unit_of_work import UnitOfWork
from app.repositories.lms import LMSRepository
from app.schemas.cms import ContentAssignRequest, ContentSubmitForReviewRequest
from app.schemas.lms import ContentProgressRequest
from app.services.audit import AuditService
from app.services.lms._helpers import LMSServiceBase, _utc_now


class ContentService(LMSServiceBase):
    """Handles content items, assets, progress, and library workflows."""

    async def list_content_items(
        self,
        *,
        content_type: str | None,
        level_band: str | None,
        language: str | None,
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
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        content_item = await self.repo.get_content_item(content_item_id)
        if content_item is None:
            raise NotFoundError("Content item not found", error_code="ERR-LMS-404")
        if content_item.school_id is not None:
            verify_school_boundary(content_item.school_id, auth)

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
            )
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
                },
                ip_address=ip_address,
            )
            await uow.commit()

        return {
            "id": str(asset.id),
            "content_item_id": str(asset.content_item_id),
            "file_path": asset.file_path,
            "checksum": asset.checksum,
            "mime_type": asset.mime_type,
            "file_size": asset.file_size,
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
        if content_item.school_id is not None:
            verify_school_boundary(content_item.school_id, auth)

        entity_before = {
            "id": str(asset.id),
            "file_path": asset.file_path,
            "mime_type": asset.mime_type,
            "file_size": asset.file_size,
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
                "assigned_at": assignment.assigned_at.isoformat()
                if assignment.assigned_at
                else None,
                "teacher_notes": assignment.notes,
            }
            for assignment, content_item in rows
        ]
        next_cursor = encode_cursor(rows[-1][0].id) if has_more and rows else None
        return items, next_cursor, has_more
