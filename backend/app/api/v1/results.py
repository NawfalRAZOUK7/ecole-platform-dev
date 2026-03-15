"""Results API endpoint: GET /results.

Reference: S-055 — View results (STD, PAR).
Role: STD (PERM-LMS:result:read), PAR (PERM-LMS:result:read)
STD sees own results. PAR sees child results.
Cursor pagination on assignment_id.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    AuthContext,
    get_parent_child_ids,
    requires_permission,
)
from app.core.response import (
    clamp_page_size,
    decode_cursor,
    encode_cursor,
    list_response,
)
from app.models.lms import Assignment, Course, Grade, Submission

router = APIRouter(prefix="/results", tags=["lms-results"])


@router.get("")
async def list_results(
    student_id: uuid.UUID | None = Query(None),
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    auth: AuthContext = Depends(requires_permission("PERM-LMS:result:read")),
    db: AsyncSession = Depends(get_db),
):
    """List graded results for a student.

    STD: sees own results (student_id ignored, uses auth.user_id).
    PAR: must specify student_id, which must be a linked child.
    """
    page_size = clamp_page_size(limit)

    # Determine target student
    if auth.role == "STD":
        target_student_id = auth.user_id
    elif auth.role == "PAR":
        if student_id is None:
            # Default: get all children's results
            child_ids = await get_parent_child_ids(auth.user_id, auth.school_id, db)
            target_student_id = None  # Will filter by set of children
        else:
            # Verify parent-child link
            child_ids = await get_parent_child_ids(auth.user_id, auth.school_id, db)
            from app.core.dependencies import verify_parent_child_ownership
            verify_parent_child_ownership(student_id, child_ids)
            target_student_id = student_id
    else:
        # ADM or other roles — use student_id or return empty
        target_student_id = student_id

    # Build query: join Submission → Grade → Assignment → Course
    query = (
        select(Assignment, Submission, Grade, Course)
        .join(Submission, Submission.assignment_id == Assignment.id)
        .join(Grade, Grade.submission_id == Submission.id)
        .join(Course, Course.id == Assignment.course_id)
        .where(Course.school_id == auth.school_id)
    )

    if target_student_id is not None:
        query = query.where(Submission.student_id == target_student_id)
    elif auth.role == "PAR" and child_ids:
        query = query.where(Submission.student_id.in_(child_ids))

    # Only show published grades
    query = query.where(Grade.published_at.is_not(None))

    # Cursor pagination
    if cursor:
        last_id, _ = decode_cursor(cursor)
        query = query.where(Assignment.id > last_id)

    query = query.order_by(Assignment.id).limit(page_size + 1)
    result = await db.execute(query)
    rows = list(result.all())

    has_more = len(rows) > page_size
    if has_more:
        rows = rows[:page_size]

    items = [
        {
            "assignment_id": str(assignment.id),
            "assignment_title": assignment.title,
            "course_title": course.title,
            "submission_id": str(submission.id),
            "status": submission.status,
            "score": float(grade.score) if grade.score is not None else None,
            "feedback_text": grade.feedback_text,
            "total_points": assignment.total_points,
            "due_at": assignment.due_at.isoformat() if assignment.due_at else None,
        }
        for assignment, submission, grade, course in rows
    ]

    next_cursor = (
        encode_cursor(rows[-1][0].id)
        if has_more and rows
        else None
    )
    return list_response(items, next_cursor=next_cursor, has_more=has_more)
