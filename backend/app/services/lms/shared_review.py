"""Shared review service — parent sees child's recent activity sessions and adds comments.

Phase B1: Interface de révision partagée parent-enfant.
Allows parents to browse recent quiz attempts, content progress, writing attempts,
and activity sessions for their linked children, and post encouragement comments.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import AuthContext, verify_parent_child_ownership
from app.core.exceptions import NotFoundError
from app.models.ai import WritingAttempt
from app.models.iam import ParentChildLink
from app.models.lms import (
    ActivitySession,
    ContentItem,
    ContentProgress,
    Quiz,
    QuizAttempt,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# In-memory comment store (backed by a simple table later or JSON column)
# For now we use a lightweight model — see SharedReviewComment below.
# ---------------------------------------------------------------------------

# We'll store comments directly in the shared_review_comments table.
# The model is defined at the bottom of this file for import convenience.


class SharedReviewService:
    """Service for parent-child shared review sessions."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Helper: verify parent owns this child
    # ------------------------------------------------------------------
    async def _get_child_ids(
        self, parent_id: uuid.UUID, school_id: uuid.UUID
    ) -> set[uuid.UUID]:
        result = await self.db.execute(
            select(ParentChildLink.child_user_id).where(
                ParentChildLink.parent_user_id == parent_id,
                ParentChildLink.school_id == school_id,
                ParentChildLink.status == "active",
            )
        )
        return set(result.scalars().all())

    async def _verify_child(self, child_id: uuid.UUID, auth: AuthContext) -> None:
        child_ids = await self._get_child_ids(auth.user_id, auth.school_id)
        verify_parent_child_ownership(child_id, child_ids)

    # ------------------------------------------------------------------
    # List recent sessions for a child (unified across session types)
    # ------------------------------------------------------------------
    async def list_child_sessions(
        self,
        *,
        child_id: uuid.UUID,
        auth: AuthContext,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Return a unified list of the child's recent learning sessions."""
        await self._verify_child(child_id, auth)

        sessions: list[dict[str, Any]] = []

        # 1) Quiz attempts
        quiz_q = (
            select(
                QuizAttempt.id,
                QuizAttempt.quiz_id,
                QuizAttempt.score,
                QuizAttempt.max_score,
                QuizAttempt.status,
                QuizAttempt.started_at,
                QuizAttempt.completed_at,
                Quiz.title.label("quiz_title"),
            )
            .join(Quiz, QuizAttempt.quiz_id == Quiz.id)
            .where(QuizAttempt.student_id == child_id)
            .order_by(desc(QuizAttempt.started_at))
            .limit(limit)
        )
        quiz_results = await self.db.execute(quiz_q)
        for row in quiz_results.all():
            sessions.append(
                {
                    "id": str(row.id),
                    "type": "quiz",
                    "title": row.quiz_title or "Quiz",
                    "score": float(row.score) if row.score is not None else None,
                    "max_score": row.max_score,
                    "status": row.status,
                    "started_at": row.started_at.isoformat()
                    if row.started_at
                    else None,
                    "completed_at": (
                        row.completed_at.isoformat() if row.completed_at else None
                    ),
                }
            )

        # 2) Content progress
        content_q = (
            select(
                ContentProgress.id,
                ContentProgress.status,
                ContentProgress.created_at,
                ContentProgress.updated_at,
                ContentItem.title.label("content_title"),
                ContentItem.content_type.label("content_type"),
            )
            .join(ContentItem, ContentProgress.content_item_id == ContentItem.id)
            .where(ContentProgress.student_id == child_id)
            .order_by(desc(ContentProgress.updated_at))
            .limit(limit)
        )
        content_results = await self.db.execute(content_q)
        for row in content_results.all():
            sessions.append(
                {
                    "id": str(row.id),
                    "type": "content",
                    "title": row.content_title or "Content",
                    "content_type": row.content_type,
                    "status": row.status,
                    "started_at": (
                        row.created_at.isoformat() if row.created_at else None
                    ),
                    "completed_at": (
                        row.updated_at.isoformat()
                        if row.status == "completed" and row.updated_at
                        else None
                    ),
                }
            )

        # 3) Writing attempts
        writing_q = (
            select(
                WritingAttempt.id,
                WritingAttempt.subject,
                WritingAttempt.status,
                WritingAttempt.hints,
                WritingAttempt.created_at,
            )
            .where(WritingAttempt.student_id == child_id)
            .order_by(desc(WritingAttempt.created_at))
            .limit(limit)
        )
        writing_results = await self.db.execute(writing_q)
        for row in writing_results.all():
            hints = row.hints or {}
            sessions.append(
                {
                    "id": str(row.id),
                    "type": "writing",
                    "title": row.subject or "Writing",
                    "score": hints.get("score"),
                    "status": row.status or "completed",
                    "started_at": (
                        row.created_at.isoformat() if row.created_at else None
                    ),
                    "completed_at": (
                        row.created_at.isoformat() if row.created_at else None
                    ),
                }
            )

        # 4) Activity sessions
        from app.models.lms import Activity

        activity_q = (
            select(
                ActivitySession.id,
                ActivitySession.status,
                ActivitySession.score,
                ActivitySession.created_at,
                ActivitySession.updated_at,
                Activity.title.label("activity_title"),
            )
            .join(Activity, ActivitySession.activity_id == Activity.id)
            .where(ActivitySession.student_id == child_id)
            .order_by(desc(ActivitySession.created_at))
            .limit(limit)
        )
        activity_results = await self.db.execute(activity_q)
        for row in activity_results.all():
            sessions.append(
                {
                    "id": str(row.id),
                    "type": "activity",
                    "title": row.activity_title or "Activity",
                    "score": float(row.score) if row.score is not None else None,
                    "status": row.status,
                    "started_at": (
                        row.created_at.isoformat() if row.created_at else None
                    ),
                    "completed_at": (
                        row.updated_at.isoformat()
                        if row.status == "completed" and row.updated_at
                        else None
                    ),
                }
            )

        # Sort all sessions by started_at descending
        sessions.sort(
            key=lambda s: s.get("started_at") or "",
            reverse=True,
        )

        # Apply offset + limit to the merged result
        paginated = sessions[offset : offset + limit]

        return {
            "child_id": str(child_id),
            "sessions": paginated,
            "total": len(sessions),
        }

    # ------------------------------------------------------------------
    # Get detail of a specific session
    # ------------------------------------------------------------------
    async def get_session_detail(
        self,
        *,
        child_id: uuid.UUID,
        session_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict[str, Any]:
        """Return detailed info about a specific session."""
        await self._verify_child(child_id, auth)

        # Try each session type
        # 1) Quiz attempt
        quiz = await self.db.execute(
            select(QuizAttempt).where(
                QuizAttempt.id == session_id,
                QuizAttempt.student_id == child_id,
            )
        )
        qa = quiz.scalar_one_or_none()
        if qa:
            quiz_info = await self.db.execute(select(Quiz).where(Quiz.id == qa.quiz_id))
            quiz_obj = quiz_info.scalar_one_or_none()
            return {
                "id": str(qa.id),
                "type": "quiz",
                "title": quiz_obj.title if quiz_obj else "Quiz",
                "score": float(qa.score) if qa.score is not None else None,
                "max_score": qa.max_score,
                "status": qa.status,
                "started_at": qa.started_at.isoformat() if qa.started_at else None,
                "completed_at": (
                    qa.completed_at.isoformat() if qa.completed_at else None
                ),
                "comments": await self._get_comments(session_id),
            }

        # 2) Content progress
        cp_result = await self.db.execute(
            select(ContentProgress).where(
                ContentProgress.id == session_id,
                ContentProgress.student_id == child_id,
            )
        )
        cp = cp_result.scalar_one_or_none()
        if cp:
            ci_result = await self.db.execute(
                select(ContentItem).where(ContentItem.id == cp.content_item_id)
            )
            ci = ci_result.scalar_one_or_none()
            return {
                "id": str(cp.id),
                "type": "content",
                "title": ci.title if ci else "Content",
                "content_type": ci.content_type if ci else None,
                "status": cp.status,
                "started_at": cp.created_at.isoformat() if cp.created_at else None,
                "comments": await self._get_comments(session_id),
            }

        # 3) Writing attempt
        wa_result = await self.db.execute(
            select(WritingAttempt).where(
                WritingAttempt.id == session_id,
                WritingAttempt.student_id == child_id,
            )
        )
        wa = wa_result.scalar_one_or_none()
        if wa:
            hints = wa.hints or {}
            return {
                "id": str(wa.id),
                "type": "writing",
                "title": wa.subject or "Writing",
                "text": wa.input_text,
                "suggestion": wa.suggestion,
                "hints": hints,
                "score": hints.get("score"),
                "status": wa.status or "completed",
                "started_at": wa.created_at.isoformat() if wa.created_at else None,
                "comments": await self._get_comments(session_id),
            }

        # 4) Activity session
        as_result = await self.db.execute(
            select(ActivitySession).where(
                ActivitySession.id == session_id,
                ActivitySession.student_id == child_id,
            )
        )
        act = as_result.scalar_one_or_none()
        if act:
            from app.models.lms import Activity

            act_info = await self.db.execute(
                select(Activity).where(Activity.id == act.activity_id)
            )
            activity_obj = act_info.scalar_one_or_none()
            return {
                "id": str(act.id),
                "type": "activity",
                "title": activity_obj.title if activity_obj else "Activity",
                "score": float(act.score) if act.score is not None else None,
                "status": act.status,
                "started_at": (act.created_at.isoformat() if act.created_at else None),
                "completed_at": (
                    act.updated_at.isoformat()
                    if act.status == "completed" and act.updated_at
                    else None
                ),
                "comments": await self._get_comments(session_id),
            }

        raise NotFoundError("Session not found", error_code="ERR-RES-404")

    # ------------------------------------------------------------------
    # Comments
    # ------------------------------------------------------------------
    async def _get_comments(self, session_id: uuid.UUID) -> list[dict[str, Any]]:
        """Get all comments for a session."""
        from app.models.com import SharedReviewComment

        result = await self.db.execute(
            select(SharedReviewComment)
            .where(SharedReviewComment.session_id == session_id)
            .order_by(SharedReviewComment.created_at)
        )
        comments = result.scalars().all()
        return [
            {
                "id": str(c.id),
                "author_id": str(c.author_id),
                "text": c.text,
                "emoji": c.emoji,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in comments
        ]

    async def add_comment(
        self,
        *,
        child_id: uuid.UUID,
        session_id: uuid.UUID,
        text: str,
        emoji: str | None = None,
        auth: AuthContext,
    ) -> dict[str, Any]:
        """Parent adds an encouragement comment to a session."""
        await self._verify_child(child_id, auth)

        # Verify session exists for this child (quick check via get_session_detail)
        await self.get_session_detail(
            child_id=child_id, session_id=session_id, auth=auth
        )

        from app.models.com import SharedReviewComment

        comment = SharedReviewComment(
            session_id=session_id,
            child_id=child_id,
            author_id=auth.user_id,
            school_id=auth.school_id,
            text=text,
            emoji=emoji,
        )
        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)

        return {
            "id": str(comment.id),
            "author_id": str(comment.author_id),
            "text": comment.text,
            "emoji": comment.emoji,
            "created_at": (
                comment.created_at.isoformat() if comment.created_at else None
            ),
        }
