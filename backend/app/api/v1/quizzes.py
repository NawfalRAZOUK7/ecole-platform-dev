"""Quiz Engine endpoints — Phase 9B.

- POST /quizzes — create quiz (CONTENT_MGR platform / TCH school-scoped)
- GET /quizzes — list quizzes
- GET /quizzes/{id} — quiz detail with questions
- PUT /quizzes/{id} — update quiz (DRAFT only)
- POST /quizzes/{id}/publish — publish quiz
- POST /quizzes/{id}/start — student starts attempt
- POST /attempts/{id}/respond — student answers one question
- POST /attempts/{id}/submit — student submits attempt → auto-grade
- GET /attempts/{id}/results — student views graded results
- GET /quizzes/{id}/analytics — teacher/CONTENT_MGR analytics
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.exceptions import NotFoundError, ValidationError
from app.core.request_utils import get_client_ip
from app.core.response import (
    clamp_page_size,
    decode_cursor,
    encode_cursor,
    list_response,
    success_response,
)
from app.models.lms import Quiz, QuizAttempt, QuizQuestion, QuizResponse
from app.schemas.quiz import (
    QuizCreateRequest,
    QuizRespondRequest,
    QuizUpdateRequest,
)
from app.services.audit import AuditService
from app.services.quiz_grading import grade_attempt

router = APIRouter(tags=["quiz-engine"])



def _quiz_to_dict(q: Quiz, questions: list | None = None) -> dict:
    total_points = sum(qq.points for qq in (questions or []))
    d = {
        "id": str(q.id),
        "school_id": str(q.school_id) if q.school_id else None,
        "created_by": str(q.created_by),
        "title": q.title,
        "description": q.description,
        "subject": q.subject,
        "level_band": q.level_band,
        "difficulty": q.difficulty,
        "time_limit_minutes": q.time_limit_minutes,
        "max_attempts": q.max_attempts,
        "shuffle_questions": q.shuffle_questions,
        "status": q.status,
        "total_points": total_points,
        "question_count": len(questions or []),
    }
    return d


def _question_to_dict(qq: QuizQuestion, include_answer: bool = False) -> dict:
    d = {
        "id": str(qq.id),
        "question_type": qq.question_type,
        "question_text": qq.question_text,
        "question_media_path": qq.question_media_path,
        "options": qq.options,
        "points": qq.points,
        "order": qq.order,
        "explanation": qq.explanation if include_answer else None,
    }
    if include_answer:
        d["correct_answer"] = qq.correct_answer
    return d


def _attempt_to_dict(a: QuizAttempt) -> dict:
    return {
        "id": str(a.id),
        "quiz_id": str(a.quiz_id),
        "student_id": str(a.student_id),
        "attempt_no": a.attempt_no,
        "started_at": a.started_at.isoformat() if a.started_at else None,
        "completed_at": a.completed_at.isoformat() if a.completed_at else None,
        "score": float(a.score) if a.score is not None else None,
        "max_score": a.max_score,
        "status": a.status,
    }


# ---------------------------------------------------------------------------
# POST /quizzes — Create quiz
# ---------------------------------------------------------------------------
@router.post("/quizzes", status_code=201, summary="Create a quiz")
async def create_quiz(
    body: QuizCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-QUIZ:quiz:create")),
    db: AsyncSession = Depends(get_db),
):
    """CONTENT_MGR creates platform-wide (school_id=NULL), TCH creates school-scoped."""
    audit = AuditService(db)

    # CONTENT_MGR → platform-wide, TCH → school-scoped
    school_id = None if auth.role == "CONTENT_MGR" else auth.school_id

    quiz = Quiz(
        school_id=school_id,
        created_by=auth.user_id,
        title=body.title,
        description=body.description,
        subject=body.subject,
        level_band=body.level_band,
        difficulty=body.difficulty,
        time_limit_minutes=body.time_limit_minutes,
        max_attempts=body.max_attempts,
        shuffle_questions=body.shuffle_questions,
        status="draft",
    )
    db.add(quiz)
    await db.flush()

    # Add questions
    questions = []
    for i, q_input in enumerate(body.questions):
        qq = QuizQuestion(
            quiz_id=quiz.id,
            question_type=q_input.question_type,
            question_text=q_input.question_text,
            question_media_path=q_input.question_media_path,
            options=q_input.options,
            correct_answer=q_input.correct_answer,
            points=q_input.points,
            order=q_input.order if q_input.order > 0 else i,
            explanation=q_input.explanation,
        )
        db.add(qq)
        questions.append(qq)
    await db.flush()

    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="QUIZ_CREATED",
        outcome="success",
        target_type="quiz",
        target_id=quiz.id,
        entity_after={"title": quiz.title, "question_count": len(questions)},
        ip_address=get_client_ip(request),
    )

    result = _quiz_to_dict(quiz, questions)
    result["questions"] = [
        _question_to_dict(qq, include_answer=True) for qq in questions
    ]
    return success_response(result)


# ---------------------------------------------------------------------------
# GET /quizzes — List quizzes
# ---------------------------------------------------------------------------
@router.get("/quizzes", summary="List quizzes")
async def list_quizzes(
    subject: str | None = Query(None),
    level_band: str | None = Query(None),
    status: str | None = Query(None),
    difficulty: str | None = Query(None),
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    auth: AuthContext = Depends(requires_permission("PERM-QUIZ:quiz:read")),
    db: AsyncSession = Depends(get_db),
):
    """List quizzes visible to the user (platform + school-scoped)."""
    page_size = clamp_page_size(limit)

    # Students see only published, creators see all their own + published
    if auth.role == "STD":
        query = select(Quiz).where(
            Quiz.status == "published",
            (Quiz.school_id == auth.school_id) | (Quiz.school_id.is_(None)),
        )
    elif auth.role == "CONTENT_MGR":
        query = select(Quiz).where(Quiz.school_id.is_(None))
    else:
        # TCH — their own + published platform quizzes
        query = select(Quiz).where(
            (Quiz.created_by == auth.user_id)
            | ((Quiz.status == "published") & (Quiz.school_id.is_(None)))
        )

    if subject:
        query = query.where(Quiz.subject == subject)
    if level_band:
        query = query.where(Quiz.level_band == level_band)
    if status:
        query = query.where(Quiz.status == status)
    if difficulty:
        query = query.where(Quiz.difficulty == difficulty)

    query = query.order_by(Quiz.id)

    if cursor:
        last_id, _ = decode_cursor(cursor)
        query = query.where(Quiz.id > last_id)

    query = query.limit(page_size + 1)
    result = await db.execute(query)
    quizzes = list(result.scalars().all())

    has_more = len(quizzes) > page_size
    if has_more:
        quizzes = quizzes[:page_size]

    # Batch-load question counts
    quiz_ids = [q.id for q in quizzes]
    if quiz_ids:
        counts_result = await db.execute(
            select(
                QuizQuestion.quiz_id,
                func.count(QuizQuestion.id),
                func.sum(QuizQuestion.points),
            )
            .where(QuizQuestion.quiz_id.in_(quiz_ids))
            .group_by(QuizQuestion.quiz_id)
        )
        counts = {row[0]: (row[1], row[2] or 0) for row in counts_result.all()}
    else:
        counts = {}

    items = []
    for q in quizzes:
        qcount, total_pts = counts.get(q.id, (0, 0))
        d = {
            "id": str(q.id),
            "school_id": str(q.school_id) if q.school_id else None,
            "created_by": str(q.created_by),
            "title": q.title,
            "description": q.description,
            "subject": q.subject,
            "level_band": q.level_band,
            "difficulty": q.difficulty,
            "time_limit_minutes": q.time_limit_minutes,
            "max_attempts": q.max_attempts,
            "shuffle_questions": q.shuffle_questions,
            "status": q.status,
            "total_points": int(total_pts),
            "question_count": qcount,
        }
        items.append(d)

    next_cursor = encode_cursor(quizzes[-1].id) if has_more and quizzes else None
    return list_response(items, next_cursor=next_cursor, has_more=has_more)


# ---------------------------------------------------------------------------
# GET /quizzes/{id} — Quiz detail
# ---------------------------------------------------------------------------
@router.get("/quizzes/{quiz_id}", summary="Get quiz details with questions")
async def get_quiz(
    quiz_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission("PERM-QUIZ:quiz:read")),
    db: AsyncSession = Depends(get_db),
):
    """Get quiz detail. Students don't see correct_answer or explanation."""
    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    if quiz is None:
        raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")

    # Visibility check
    if quiz.school_id is not None and quiz.school_id != auth.school_id:
        raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")
    if auth.role == "STD" and quiz.status != "published":
        raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")

    # Load questions
    q_result = await db.execute(
        select(QuizQuestion)
        .where(QuizQuestion.quiz_id == quiz_id)
        .order_by(QuizQuestion.order)
    )
    questions = list(q_result.scalars().all())

    is_creator = auth.role in ("CONTENT_MGR", "TCH", "ADM")
    d = _quiz_to_dict(quiz, questions)
    d["questions"] = [
        _question_to_dict(qq, include_answer=is_creator) for qq in questions
    ]
    return success_response(d)


# ---------------------------------------------------------------------------
# PUT /quizzes/{id} — Update quiz (DRAFT only)
# ---------------------------------------------------------------------------
@router.put("/quizzes/{quiz_id}", summary="Update quiz")
async def update_quiz(
    quiz_id: uuid.UUID,
    body: QuizUpdateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-QUIZ:quiz:manage")),
    db: AsyncSession = Depends(get_db),
):
    """Update quiz metadata and questions. Only if status is DRAFT."""
    audit = AuditService(db)

    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    if quiz is None:
        raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")

    if quiz.status != "draft":
        raise ValidationError("Can only edit draft quizzes", error_code="ERR-QUIZ-400")

    # Ownership check
    if auth.role == "TCH" and quiz.created_by != auth.user_id:
        raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")

    update_data = body.model_dump(exclude_unset=True, exclude={"questions"})
    for field, value in update_data.items():
        setattr(quiz, field, value)

    # Replace questions if provided
    if body.questions is not None:
        # Delete old questions
        old_q_result = await db.execute(
            select(QuizQuestion).where(QuizQuestion.quiz_id == quiz_id)
        )
        for old_q in old_q_result.scalars().all():
            await db.delete(old_q)
        await db.flush()

        # Add new questions
        for i, q_input in enumerate(body.questions):
            qq = QuizQuestion(
                quiz_id=quiz.id,
                question_type=q_input.question_type,
                question_text=q_input.question_text,
                question_media_path=q_input.question_media_path,
                options=q_input.options,
                correct_answer=q_input.correct_answer,
                points=q_input.points,
                order=q_input.order if q_input.order > 0 else i,
                explanation=q_input.explanation,
            )
            db.add(qq)

    await db.flush()

    # Reload questions
    q_result = await db.execute(
        select(QuizQuestion)
        .where(QuizQuestion.quiz_id == quiz_id)
        .order_by(QuizQuestion.order)
    )
    questions = list(q_result.scalars().all())

    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="QUIZ_UPDATED",
        outcome="success",
        target_type="quiz",
        target_id=quiz.id,
        entity_after={"title": quiz.title},
        ip_address=get_client_ip(request),
    )

    d = _quiz_to_dict(quiz, questions)
    d["questions"] = [_question_to_dict(qq, include_answer=True) for qq in questions]
    return success_response(d)


# ---------------------------------------------------------------------------
# POST /quizzes/{id}/publish — Publish quiz
# ---------------------------------------------------------------------------
@router.post("/quizzes/{quiz_id}/publish", summary="Publish a quiz")
async def publish_quiz(
    quiz_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-QUIZ:quiz:publish")),
    db: AsyncSession = Depends(get_db),
):
    """Publish a draft quiz. Must have at least one question."""
    audit = AuditService(db)

    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    if quiz is None:
        raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")

    if auth.role == "TCH" and quiz.created_by != auth.user_id:
        raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")

    if quiz.status != "draft":
        raise ValidationError("Quiz is not in draft status", error_code="ERR-QUIZ-400")

    # Check has questions
    count_result = await db.execute(
        select(func.count(QuizQuestion.id)).where(QuizQuestion.quiz_id == quiz_id)
    )
    question_count = count_result.scalar() or 0
    if question_count == 0:
        raise ValidationError(
            "Cannot publish a quiz with no questions", error_code="ERR-QUIZ-400"
        )

    quiz.status = "published"
    await db.flush()

    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="QUIZ_PUBLISHED",
        outcome="success",
        target_type="quiz",
        target_id=quiz.id,
        entity_after={"status": "published"},
        ip_address=get_client_ip(request),
    )

    return success_response({"id": str(quiz.id), "status": "published"})


# ---------------------------------------------------------------------------
# POST /quizzes/{id}/start — Student starts attempt
# ---------------------------------------------------------------------------
@router.post(
    "/quizzes/{quiz_id}/start", status_code=201, summary="Start a quiz attempt"
)
async def start_attempt(
    quiz_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-QUIZ:quiz:attempt")),
    db: AsyncSession = Depends(get_db),
):
    """Student starts a new quiz attempt. Checks max_attempts limit."""
    audit = AuditService(db)

    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    if quiz is None or quiz.status != "published":
        raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")

    # School boundary
    if quiz.school_id is not None and quiz.school_id != auth.school_id:
        raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")

    # Check max attempts
    count_result = await db.execute(
        select(func.count(QuizAttempt.id)).where(
            QuizAttempt.quiz_id == quiz_id,
            QuizAttempt.student_id == auth.user_id,
        )
    )
    existing_count = count_result.scalar() or 0
    if existing_count >= quiz.max_attempts:
        raise ValidationError(
            f"Maximum attempts ({quiz.max_attempts}) reached",
            error_code="ERR-QUIZ-429",
        )

    # Check no in-progress attempt
    active_result = await db.execute(
        select(QuizAttempt).where(
            QuizAttempt.quiz_id == quiz_id,
            QuizAttempt.student_id == auth.user_id,
            QuizAttempt.status == "STARTED",
        )
    )
    active = active_result.scalar_one_or_none()
    if active is not None:
        # Return existing active attempt
        return success_response(_attempt_to_dict(active))

    # Compute max_score
    pts_result = await db.execute(
        select(func.sum(QuizQuestion.points)).where(QuizQuestion.quiz_id == quiz_id)
    )
    max_score = int(pts_result.scalar() or 0)

    attempt = QuizAttempt(
        quiz_id=quiz_id,
        student_id=auth.user_id,
        attempt_no=existing_count + 1,
        started_at=datetime.now(timezone.utc),
        max_score=max_score,
        status="STARTED",
    )
    db.add(attempt)
    await db.flush()

    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="QUIZ_ATTEMPT_STARTED",
        outcome="success",
        target_type="quiz_attempt",
        target_id=attempt.id,
        entity_after={"quiz_id": str(quiz_id), "attempt_no": attempt.attempt_no},
        ip_address=get_client_ip(request),
    )

    return success_response(_attempt_to_dict(attempt))


# ---------------------------------------------------------------------------
# POST /attempts/{id}/respond — Student answers one question
# ---------------------------------------------------------------------------
@router.post("/attempts/{attempt_id}/respond", summary="Submit answer for one question")
async def respond_to_question(
    attempt_id: uuid.UUID,
    body: QuizRespondRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-QUIZ:quiz:attempt")),
    db: AsyncSession = Depends(get_db),
):
    """Student submits an answer for one question in an active attempt."""
    result = await db.execute(select(QuizAttempt).where(QuizAttempt.id == attempt_id))
    attempt = result.scalar_one_or_none()
    if attempt is None:
        raise NotFoundError("Attempt not found", error_code="ERR-QUIZ-404")

    if attempt.student_id != auth.user_id:
        raise NotFoundError("Attempt not found", error_code="ERR-QUIZ-404")

    if attempt.status != "STARTED":
        raise ValidationError("Attempt already completed", error_code="ERR-QUIZ-400")

    # Check time limit
    quiz_result = await db.execute(select(Quiz).where(Quiz.id == attempt.quiz_id))
    quiz = quiz_result.scalar_one()
    if quiz.time_limit_minutes and quiz.time_limit_minutes > 0:
        elapsed = (datetime.now(timezone.utc) - attempt.started_at).total_seconds()
        if elapsed > quiz.time_limit_minutes * 60:
            attempt.status = "TIMED_OUT"
            attempt.completed_at = datetime.now(timezone.utc)
            await db.flush()
            raise ValidationError("Time limit exceeded", error_code="ERR-QUIZ-408")

    # Verify question belongs to this quiz
    q_result = await db.execute(
        select(QuizQuestion).where(
            QuizQuestion.id == body.question_id,
            QuizQuestion.quiz_id == attempt.quiz_id,
        )
    )
    question = q_result.scalar_one_or_none()
    if question is None:
        raise NotFoundError(
            "Question not found in this quiz", error_code="ERR-QUIZ-404"
        )

    # Upsert response
    existing_resp = await db.execute(
        select(QuizResponse).where(
            QuizResponse.attempt_id == attempt_id,
            QuizResponse.question_id == body.question_id,
        )
    )
    resp = existing_resp.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if resp is not None:
        resp.student_answer = body.student_answer
        resp.answered_at = now
        resp.is_correct = None  # reset — will be graded on submit
        resp.points_earned = None
    else:
        resp = QuizResponse(
            attempt_id=attempt_id,
            question_id=body.question_id,
            student_answer=body.student_answer,
            answered_at=now,
        )
        db.add(resp)

    await db.flush()

    return success_response(
        {
            "id": str(resp.id),
            "attempt_id": str(attempt_id),
            "question_id": str(body.question_id),
            "answered_at": now.isoformat(),
        }
    )


# ---------------------------------------------------------------------------
# POST /attempts/{id}/submit — Submit attempt → auto-grade
# ---------------------------------------------------------------------------
@router.post("/attempts/{attempt_id}/submit", summary="Submit attempt for grading")
async def submit_attempt(
    attempt_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-QUIZ:quiz:attempt")),
    db: AsyncSession = Depends(get_db),
):
    """Student submits attempt. Triggers auto-grading for all responses."""
    audit = AuditService(db)

    result = await db.execute(select(QuizAttempt).where(QuizAttempt.id == attempt_id))
    attempt = result.scalar_one_or_none()
    if attempt is None:
        raise NotFoundError("Attempt not found", error_code="ERR-QUIZ-404")

    if attempt.student_id != auth.user_id:
        raise NotFoundError("Attempt not found", error_code="ERR-QUIZ-404")

    if attempt.status != "STARTED":
        raise ValidationError("Attempt already completed", error_code="ERR-QUIZ-400")

    # Auto-grade
    total_score, max_score = await grade_attempt(attempt_id, db)

    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="QUIZ_ATTEMPT_SUBMITTED",
        outcome="success",
        target_type="quiz_attempt",
        target_id=attempt.id,
        entity_after={
            "score": float(total_score),
            "max_score": max_score,
            "status": "COMPLETED",
        },
        ip_address=get_client_ip(request),
    )

    return success_response(_attempt_to_dict(attempt))


# ---------------------------------------------------------------------------
# GET /attempts/{id}/results — View graded results
# ---------------------------------------------------------------------------
@router.get("/attempts/{attempt_id}/results", summary="View attempt results")
async def get_attempt_results(
    attempt_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission("PERM-QUIZ:quiz:read")),
    db: AsyncSession = Depends(get_db),
):
    """View graded attempt results with explanations."""
    result = await db.execute(select(QuizAttempt).where(QuizAttempt.id == attempt_id))
    attempt = result.scalar_one_or_none()
    if attempt is None:
        raise NotFoundError("Attempt not found", error_code="ERR-QUIZ-404")

    # Students can only view own attempts
    if auth.role == "STD" and attempt.student_id != auth.user_id:
        raise NotFoundError("Attempt not found", error_code="ERR-QUIZ-404")

    if attempt.status == "STARTED":
        raise ValidationError("Attempt not yet submitted", error_code="ERR-QUIZ-400")

    # Load responses with questions
    resp_result = await db.execute(
        select(QuizResponse, QuizQuestion)
        .join(QuizQuestion, QuizResponse.question_id == QuizQuestion.id)
        .where(QuizResponse.attempt_id == attempt_id)
        .order_by(QuizQuestion.order)
    )
    rows = list(resp_result.all())

    responses = [
        {
            "question_id": str(resp.question_id),
            "question_type": q.question_type,
            "question_text": q.question_text,
            "student_answer": resp.student_answer,
            "correct_answer": q.correct_answer,
            "is_correct": resp.is_correct,
            "points_earned": float(resp.points_earned)
            if resp.points_earned is not None
            else None,
            "points": q.points,
            "explanation": q.explanation,
        }
        for resp, q in rows
    ]

    return success_response(
        {
            "attempt": _attempt_to_dict(attempt),
            "responses": responses,
        }
    )


# ---------------------------------------------------------------------------
# GET /quizzes/{id}/analytics — Class performance stats
# ---------------------------------------------------------------------------
@router.get("/quizzes/{quiz_id}/analytics", summary="Quiz analytics")
async def quiz_analytics(
    quiz_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission("PERM-QUIZ:quiz:analytics")),
    db: AsyncSession = Depends(get_db),
):
    """Teacher/CONTENT_MGR sees aggregate quiz performance stats."""
    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    if quiz is None:
        raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")

    if auth.role == "TCH" and quiz.created_by != auth.user_id:
        if quiz.school_id is not None and quiz.school_id != auth.school_id:
            raise NotFoundError("Quiz not found", error_code="ERR-QUIZ-404")

    # Attempt stats
    stats_result = await db.execute(
        select(
            func.count(QuizAttempt.id),
            func.count(QuizAttempt.id).filter(QuizAttempt.status == "COMPLETED"),
            func.avg(QuizAttempt.score).filter(QuizAttempt.status == "COMPLETED"),
            func.max(QuizAttempt.score).filter(QuizAttempt.status == "COMPLETED"),
            func.min(QuizAttempt.score).filter(QuizAttempt.status == "COMPLETED"),
        ).where(QuizAttempt.quiz_id == quiz_id)
    )
    row = stats_result.one()
    total_attempts, completed, avg_score, max_achieved, min_achieved = row

    # Max possible score
    pts_result = await db.execute(
        select(func.sum(QuizQuestion.points)).where(QuizQuestion.quiz_id == quiz_id)
    )
    max_possible = int(pts_result.scalar() or 0)

    avg_pct = None
    if avg_score is not None and max_possible > 0:
        avg_pct = round(float(avg_score) / max_possible * 100, 1)

    # Per-question stats
    question_stats = []
    q_result = await db.execute(
        select(QuizQuestion)
        .where(QuizQuestion.quiz_id == quiz_id)
        .order_by(QuizQuestion.order)
    )
    questions = list(q_result.scalars().all())

    for q in questions:
        q_stats_result = await db.execute(
            select(
                func.count(QuizResponse.id),
                func.count(QuizResponse.id).filter(QuizResponse.is_correct),
            ).where(QuizResponse.question_id == q.id)
        )
        total_resp, correct_resp = q_stats_result.one()
        question_stats.append(
            {
                "question_id": str(q.id),
                "question_text": q.question_text[:100],
                "question_type": q.question_type,
                "total_responses": total_resp,
                "correct_responses": correct_resp,
                "accuracy": round(correct_resp / total_resp * 100, 1)
                if total_resp > 0
                else None,
            }
        )

    return success_response(
        {
            "quiz_id": str(quiz_id),
            "title": quiz.title,
            "total_attempts": total_attempts,
            "completed_attempts": completed,
            "average_score": round(float(avg_score), 2)
            if avg_score is not None
            else None,
            "max_score_achieved": float(max_achieved)
            if max_achieved is not None
            else None,
            "min_score_achieved": float(min_achieved)
            if min_achieved is not None
            else None,
            "average_percentage": avg_pct,
            "question_stats": question_stats,
        }
    )
