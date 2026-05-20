"""Service layer for CMS content management and announcements."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import AuthContext, verify_school_boundary
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.permissions import ADM, DIR, PAR, STD, TCH
from app.core.response import encode_cursor
from app.core.unit_of_work import UnitOfWork
from app.models.com import Announcement
from app.models.lms import ContentItem
from app.repositories.content_cms import CMSRepository
from app.schemas.content.cms import (
    CmsContentCreateRequest,
    CmsContentUpdateRequest,
    ReviewDecisionRequest,
)
from app.schemas.communication import (
    AnnouncementCreateRequest,
    AnnouncementResponse,
    AnnouncementUpdateRequest,
)
from app.services.platform.audit import AuditService
from app.services.communication.realtime import publish_announcement_published


class CMSService:
    """Business logic for platform content, review queue, and announcements."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = CMSRepository(db)
        self.audit = AuditService(db)

    def _content_to_dict(self, content_item: ContentItem) -> dict:
        return {
            "id": str(content_item.id),
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
            "thumbnail_path": content_item.thumbnail_path,
            "origin": content_item.origin,
            "status": content_item.status,
            "created_by": str(content_item.created_by)
            if content_item.created_by
            else None,
            "original_content_id": str(content_item.original_content_id)
            if content_item.original_content_id
            else None,
        }

    def _announcement_to_response(self, announcement: Announcement) -> dict:
        return AnnouncementResponse(
            id=str(announcement.id),
            school_id=str(announcement.school_id),
            author_id=str(announcement.author_id),
            title=announcement.title,
            body=announcement.body,
            target_roles=announcement.target_roles or [],
            target_class_ids=[
                str(class_id) for class_id in announcement.target_class_ids
            ]
            if announcement.target_class_ids
            else None,
            published_at=announcement.published_at.isoformat()
            if announcement.published_at
            else None,
            status=announcement.status,
            created_at=announcement.created_at.isoformat(),
            updated_at=announcement.updated_at.isoformat()
            if announcement.updated_at
            else None,
        ).model_dump()

    async def create_platform_content(
        self,
        *,
        body: CmsContentCreateRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        async with UnitOfWork(self.db) as uow:
            repo = CMSRepository(uow.session)
            audit = AuditService(uow.session)
            content_item = await repo.create_content_item(
                school_id=None,
                title=body.title,
                content_type=body.content_type,
                level_band=body.level_band,
                language=body.language,
                subject=body.subject,
                description=body.description,
                page_count=body.page_count,
                letter=body.letter,
                target_age_min=body.target_age_min,
                target_age_max=body.target_age_max,
                theme_color=body.theme_color,
                status=body.status,
                origin="PLATFORM",
                created_by=auth.user_id,
            )
            response = self._content_to_dict(content_item)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="CMS_CONTENT_CREATED",
                outcome="success",
                target_type="content_item",
                target_id=content_item.id,
                entity_after=response,
                ip_address=ip_address,
            )
            await uow.commit()
        return response

    async def list_platform_content(
        self,
        *,
        content_type: str | None,
        level_band: str | None,
        subject: str | None,
        status: str | None,
        origin: str | None,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[dict], str | None, bool]:
        items, has_more = await self.repo.list_platform_content(
            content_type=content_type,
            level_band=level_band,
            subject=subject,
            status=status,
            origin=origin,
            cursor=cursor,
            limit=limit,
        )
        response = [self._content_to_dict(item) for item in items]
        next_cursor = encode_cursor(items[-1].id) if has_more and items else None
        return response, next_cursor, has_more

    async def update_platform_content(
        self,
        *,
        content_id: uuid.UUID,
        body: CmsContentUpdateRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        content_item = await self.repo.get_platform_content(content_id)
        if content_item is None:
            raise NotFoundError("Platform content not found", error_code="ERR-CMS-404")

        entity_before = self._content_to_dict(content_item)
        for field, value in body.model_dump(exclude_unset=True).items():
            setattr(content_item, field, value)
        async with UnitOfWork(self.db) as uow:
            repo = CMSRepository(uow.session)
            audit = AuditService(uow.session)
            await repo.save_content_item(content_item)
            response = self._content_to_dict(content_item)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="CMS_CONTENT_UPDATED",
                outcome="success",
                target_type="content_item",
                target_id=content_item.id,
                entity_before=entity_before,
                entity_after=response,
                ip_address=ip_address,
            )
            await uow.commit()
        return response

    async def archive_platform_content(
        self,
        *,
        content_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        content_item = await self.repo.get_platform_content(content_id)
        if content_item is None:
            raise NotFoundError("Platform content not found", error_code="ERR-CMS-404")

        entity_before = self._content_to_dict(content_item)
        content_item.status = "archived"
        async with UnitOfWork(self.db) as uow:
            repo = CMSRepository(uow.session)
            audit = AuditService(uow.session)
            await repo.save_content_item(content_item)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="CMS_CONTENT_ARCHIVED",
                outcome="success",
                target_type="content_item",
                target_id=content_item.id,
                entity_before=entity_before,
                entity_after=self._content_to_dict(content_item),
                ip_address=ip_address,
            )
            await uow.commit()
        return {"deleted": True, "id": str(content_id)}

    async def list_review_submissions(
        self,
        *,
        status: str | None,
        subject: str | None,
        level_band: str | None,
        school_id: str | None,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[dict], str | None, bool]:
        school_id_filter = uuid.UUID(school_id) if school_id else None
        rows, has_more = await self.repo.list_submission_review_queue(
            status=status,
            subject=subject,
            level_band=level_band,
            school_id_filter=school_id_filter,
            cursor=cursor,
            limit=limit,
        )
        items = [
            {
                "id": str(submission.id),
                "content_item_id": str(submission.content_item_id),
                "content_title": content_item.title,
                "submitted_by": str(submission.submitted_by),
                "submitter_name": user.full_name,
                "school_id": str(submission.school_id),
                "status": submission.status,
                "submitted_at": submission.submitted_at.isoformat()
                if submission.submitted_at
                else None,
                "reviewed_by": str(submission.reviewed_by)
                if submission.reviewed_by
                else None,
                "reviewed_at": submission.reviewed_at.isoformat()
                if submission.reviewed_at
                else None,
                "review_notes": submission.review_notes,
                "promoted_content_id": str(submission.promoted_content_id)
                if submission.promoted_content_id
                else None,
            }
            for submission, content_item, user in rows
        ]
        next_cursor = encode_cursor(rows[-1][0].id) if has_more and rows else None
        return items, next_cursor, has_more

    async def review_submission(
        self,
        *,
        submission_id: uuid.UUID,
        body: ReviewDecisionRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        submission = await self.repo.get_content_submission(submission_id)
        if submission is None:
            raise NotFoundError("Submission not found", error_code="ERR-CMS-404")
        if submission.status in ("APPROVED", "REJECTED"):
            raise ValidationError(
                f"Submission already {submission.status.lower()}",
                error_code="ERR-CMS-409",
            )

        now = datetime.now(timezone.utc)
        submission.reviewed_by = auth.user_id
        submission.reviewed_at = now
        submission.review_notes = body.review_notes

        original = await self.repo.get_content_item(submission.content_item_id)
        if original is None:
            raise NotFoundError("Original content not found", error_code="ERR-CMS-404")

        async with UnitOfWork(self.db) as uow:
            repo = CMSRepository(uow.session)
            audit = AuditService(uow.session)

            if body.decision == "APPROVED":
                submission.status = "APPROVED"
                promoted = await repo.create_content_item(
                    school_id=None,
                    title=original.title,
                    content_type=original.content_type,
                    level_band=original.level_band,
                    language=original.language,
                    subject=original.subject,
                    description=original.description,
                    page_count=original.page_count,
                    letter=original.letter,
                    target_age_min=original.target_age_min,
                    target_age_max=original.target_age_max,
                    theme_color=original.theme_color,
                    status="published",
                    origin="PROMOTED",
                    created_by=original.created_by,
                    original_content_id=original.id,
                )
                submission.promoted_content_id = promoted.id

                teacher_profile = await repo.get_teacher_profile(
                    submission.submitted_by
                )
                if teacher_profile is not None:
                    teacher_profile.reward_points += body.reward_points

                try:
                    await repo.create_notification(
                        school_id=submission.school_id,
                        parent_id=submission.submitted_by,
                        event_ref=f"content:submission:approved:{submission.id}",
                        idempotency_key=f"cms-approved-{submission.id}",
                        title="Contenu approuve",
                        body=(
                            f'Votre contenu "{original.title}" a ete approuve et ajoute '
                            "a la bibliotheque de la plateforme."
                        ),
                    )
                except Exception:
                    pass
            else:
                submission.status = "REJECTED"
                try:
                    feedback_text = (
                        f" Retour: {body.review_notes}" if body.review_notes else ""
                    )
                    await repo.create_notification(
                        school_id=submission.school_id,
                        parent_id=submission.submitted_by,
                        event_ref=f"content:submission:rejected:{submission.id}",
                        idempotency_key=f"cms-rejected-{submission.id}",
                        title="Contenu non retenu",
                        body=(
                            f'Votre contenu "{original.title}" n\'a pas ete retenu '
                            f"pour la bibliotheque.{feedback_text}"
                        ),
                    )
                except Exception:
                    pass

            await repo.save_content_submission(submission)

            response = {
                "id": str(submission.id),
                "status": submission.status,
                "reviewed_by": str(submission.reviewed_by),
                "reviewed_at": submission.reviewed_at.isoformat()
                if submission.reviewed_at
                else None,
                "review_notes": submission.review_notes,
                "promoted_content_id": str(submission.promoted_content_id)
                if submission.promoted_content_id
                else None,
            }
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type=f"CMS_SUBMISSION_{body.decision}",
                outcome="success",
                target_type="content_submission",
                target_id=submission.id,
                entity_after=response,
                ip_address=ip_address,
            )
            await uow.commit()
        return response

    async def create_announcement(
        self,
        *,
        body: AnnouncementCreateRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        valid_roles = {ADM, DIR, TCH, PAR, STD}
        for role in body.target_roles:
            if role not in valid_roles:
                raise ValidationError(
                    f"Invalid target role: {role}. Must be one of {valid_roles}",
                    error_code="ERR-COM-422",
                )

        async with UnitOfWork(self.db) as uow:
            repo = CMSRepository(uow.session)
            audit = AuditService(uow.session)
            announcement = await repo.create_announcement(
                school_id=auth.school_id,
                author_id=auth.user_id,
                title=body.title,
                body=body.body,
                target_roles=body.target_roles,
                target_class_ids=[str(class_id) for class_id in body.target_class_ids]
                if body.target_class_ids
                else None,
                status="DRAFT",
            )
            response = self._announcement_to_response(announcement)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="announcement.create",
                target_type="announcement",
                target_id=announcement.id,
                outcome="success",
                entity_after=response,
                ip_address=ip_address,
            )
            await uow.commit()
        return response

    async def list_announcements(
        self,
        *,
        status: str | None,
        cursor: str | None,
        limit: int,
        auth: AuthContext,
    ) -> tuple[list[dict], str | None, bool]:
        announcements, has_more = await self.repo.list_announcements(
            school_id=auth.school_id,
            requester_role=auth.role,
            status=status,
            cursor=cursor,
            limit=limit,
        )
        items = [self._announcement_to_response(item) for item in announcements]
        next_cursor = (
            encode_cursor(announcements[-1].id) if has_more and announcements else None
        )
        return items, next_cursor, has_more

    async def update_announcement(
        self,
        *,
        announcement_id: uuid.UUID,
        body: AnnouncementUpdateRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        announcement = await self.repo.get_announcement(announcement_id)
        if announcement is None:
            raise NotFoundError("Announcement not found", error_code="ERR-COM-404")
        verify_school_boundary(announcement.school_id, auth)
        if announcement.status != "DRAFT":
            raise ConflictError(
                "Only draft announcements can be updated",
                error_code="ERR-COM-409",
            )

        entity_before = self._announcement_to_response(announcement)
        if body.title is not None:
            announcement.title = body.title
        if body.body is not None:
            announcement.body = body.body
        if body.target_roles is not None:
            valid_roles = {ADM, DIR, TCH, PAR, STD}
            for role in body.target_roles:
                if role not in valid_roles:
                    raise ValidationError(
                        f"Invalid target role: {role}",
                        error_code="ERR-COM-422",
                    )
            announcement.target_roles = body.target_roles
        if body.target_class_ids is not None:
            announcement.target_class_ids = [
                str(class_id) for class_id in body.target_class_ids
            ]

        async with UnitOfWork(self.db) as uow:
            repo = CMSRepository(uow.session)
            audit = AuditService(uow.session)
            await repo.save_announcement(announcement)
            response = self._announcement_to_response(announcement)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="announcement.update",
                target_type="announcement",
                target_id=announcement.id,
                outcome="success",
                entity_before=entity_before,
                entity_after=response,
                ip_address=ip_address,
            )
            await uow.commit()
        return response

    async def publish_announcement(
        self,
        *,
        announcement_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        announcement = await self.repo.get_announcement(announcement_id)
        if announcement is None:
            raise NotFoundError("Announcement not found", error_code="ERR-COM-404")
        verify_school_boundary(announcement.school_id, auth)
        if announcement.status != "DRAFT":
            raise ConflictError(
                "Only draft announcements can be published",
                error_code="ERR-COM-409",
            )

        entity_before = self._announcement_to_response(announcement)
        now = datetime.now(timezone.utc)
        announcement.status = "PUBLISHED"
        announcement.published_at = now

        target_user_ids = set(
            await self.repo.list_membership_user_ids_by_roles(
                school_id=auth.school_id,
                roles=announcement.target_roles or [],
            )
        )
        if announcement.target_class_ids and STD in (announcement.target_roles or []):
            class_ids = [
                uuid.UUID(class_id) for class_id in announcement.target_class_ids
            ]
            class_student_ids = await self.repo.list_student_ids_in_classes(
                class_ids=class_ids,
                school_id=auth.school_id,
            )
            non_student_roles = [
                role for role in announcement.target_roles if role != STD
            ]
            non_student_ids = set(
                await self.repo.list_membership_user_ids_by_roles(
                    school_id=auth.school_id,
                    roles=non_student_roles,
                )
            )
            target_user_ids = non_student_ids | class_student_ids

        notification_data = [
            {
                "school_id": auth.school_id,
                "parent_id": user_id,
                "event_ref": f"announcement:{announcement.id}",
                "idempotency_key": f"ann-{announcement.id}-{user_id}",
                "title": announcement.title,
                "body": announcement.body[:500]
                if len(announcement.body) > 500
                else announcement.body,
            }
            for user_id in target_user_ids
            if user_id != auth.user_id
        ]
        async with UnitOfWork(self.db) as uow:
            repo = CMSRepository(uow.session)
            audit = AuditService(uow.session)
            await repo.save_announcement(announcement)
            await repo.create_notifications(notification_data)
            notifications_sent = len(notification_data)

            response = {
                **self._announcement_to_response(announcement),
                "notifications_sent": notifications_sent,
            }
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="announcement.publish",
                target_type="announcement",
                target_id=announcement.id,
                outcome="success",
                entity_before=entity_before,
                entity_after=response,
                ip_address=ip_address,
            )
            await uow.commit()

        for user_id in target_user_ids:
            if user_id != auth.user_id:
                await publish_announcement_published(
                    recipient_id=user_id,
                    announcement_id=announcement.id,
                    title=announcement.title,
                    author_id=auth.user_id,
                )

        return response
