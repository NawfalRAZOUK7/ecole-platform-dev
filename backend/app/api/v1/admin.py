"""Admin API endpoints — dashboard stats, user management, audit logs, settings, justifications.

Reference: Phase 4A — Admin Dashboard backend endpoints
All endpoints require ADM or DIR role. School boundary enforced on all queries.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.response import list_response, success_response
from app.core.security import hash_password
from app.models.audit import AuditLog
from app.models.erp import AbsenceJustification
from app.models.iam import InvitationCode, Membership, ParentChildLink, Session, User
from app.schemas.auth import BatchRegisterRequest
from app.services.audit import AuditService

router = APIRouter(prefix="/admin", tags=["admin"])

# Admin requires at minimum session:list (both ADM and DIR have this)
ADMIN_PERM = "PERM-IAM:session:list"


def _get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


# ---------------------------------------------------------------------------
# GET /admin/dashboard — Summary statistics
# ---------------------------------------------------------------------------
@router.get("/dashboard", summary="Admin dashboard statistics")
async def dashboard_stats(
    auth: AuthContext = Depends(requires_permission(ADMIN_PERM)),
    db: AsyncSession = Depends(get_db),
):
    """Return summary counts for the admin dashboard: users, sessions, invitations, audit events."""
    sid = auth.school_id

    # Users count
    user_count = (
        await db.execute(
            select(func.count()).select_from(User).where(User.school_id == sid)
        )
    ).scalar() or 0

    # Active sessions count
    active_sessions = (
        await db.execute(
            select(func.count())
            .select_from(Session)
            .where(Session.school_id == sid, Session.revoke_at.is_(None))
        )
    ).scalar() or 0

    # Invitations count (active = not consumed, not expired)
    now = datetime.now(timezone.utc)
    active_invitations = (
        await db.execute(
            select(func.count())
            .select_from(InvitationCode)
            .where(
                InvitationCode.school_id == sid,
                InvitationCode.consumed_at.is_(None),
                InvitationCode.expires_at > now,
            )
        )
    ).scalar() or 0

    # Audit events count (last 24h)
    from datetime import timedelta

    audit_cutoff = now - timedelta(hours=24)
    audit_events_24h = (
        await db.execute(
            select(func.count())
            .select_from(AuditLog)
            .where(
                AuditLog.school_id == sid,
                AuditLog.created_at >= audit_cutoff,
            )
        )
    ).scalar() or 0

    # Pending justifications count
    pending_justifications = (
        await db.execute(
            select(func.count())
            .select_from(AbsenceJustification)
            .where(
                AbsenceJustification.school_id == sid,
                AbsenceJustification.status == "pending",
            )
        )
    ).scalar() or 0

    # Users by role
    role_counts_result = await db.execute(
        select(Membership.role_code, func.count())
        .where(Membership.school_id == sid, Membership.status == "active")
        .group_by(Membership.role_code)
    )
    users_by_role = {row[0]: row[1] for row in role_counts_result.all()}

    return success_response(
        {
            "users": user_count,
            "active_sessions": active_sessions,
            "active_invitations": active_invitations,
            "audit_events_24h": audit_events_24h,
            "pending_justifications": pending_justifications,
            "users_by_role": users_by_role,
        }
    )


# ---------------------------------------------------------------------------
# GET /admin/users — List users in school
# ---------------------------------------------------------------------------
@router.get("/users", summary="List users in school")
async def list_users(
    auth: AuthContext = Depends(requires_permission(ADMIN_PERM)),
    db: AsyncSession = Depends(get_db),
    search: str | None = Query(None, description="Search by name or email"),
    role: str | None = Query(None, description="Filter by role code"),
    status: str | None = Query(None, description="Filter by status"),
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    """List users in the authenticated user's school with optional search/filter."""
    query = select(User).where(User.school_id == auth.school_id)

    if search:
        pattern = f"%{search}%"
        query = query.where(User.full_name.ilike(pattern) | User.email.ilike(pattern))

    if status:
        query = query.where(User.status == status)

    if role:
        # Filter by role via membership join
        query = query.where(
            User.id.in_(
                select(Membership.user_id).where(
                    Membership.school_id == auth.school_id,
                    Membership.role_code == role,
                    Membership.status == "active",
                )
            )
        )

    query = query.order_by(User.created_at.desc())

    # Cursor pagination
    if cursor:
        try:
            cursor_dt = datetime.fromisoformat(cursor)
            query = query.where(User.created_at < cursor_dt)
        except ValueError:
            pass

    query = query.limit(limit + 1)
    result = await db.execute(query)
    rows = list(result.scalars().all())

    has_more = len(rows) > limit
    if has_more:
        rows = rows[:limit]

    # Get memberships for these users
    user_ids = [u.id for u in rows]
    memberships_result = await db.execute(
        select(Membership).where(
            Membership.user_id.in_(user_ids),
            Membership.school_id == auth.school_id,
            Membership.status == "active",
        )
    )
    memberships_map: dict[uuid.UUID, str] = {}
    for m in memberships_result.scalars().all():
        memberships_map[m.user_id] = m.role_code

    data = [
        {
            "id": str(u.id),
            "email": u.email,
            "full_name": u.full_name,
            "status": u.status,
            "role": memberships_map.get(u.id, ""),
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "email_verified": u.email_verified_at is not None,
            "totp_enabled": u.totp_enabled,
        }
        for u in rows
    ]

    next_cursor = rows[-1].created_at.isoformat() if has_more and rows else None
    return list_response(data, next_cursor=next_cursor, has_more=has_more)


# ---------------------------------------------------------------------------
# PUT /admin/users/{user_id}/suspend — Suspend user
# ---------------------------------------------------------------------------
@router.put("/users/{user_id}/suspend", summary="Suspend a user")
async def suspend_user(
    user_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission(ADMIN_PERM)),
    db: AsyncSession = Depends(get_db),
):
    """Suspend a user in the school. ADM only."""
    if auth.role not in ("ADM",):
        raise ValidationError(
            "Only administrators can suspend users", error_code="ERR-ADMIN-403"
        )

    user = (
        await db.execute(
            select(User).where(User.id == user_id, User.school_id == auth.school_id)
        )
    ).scalar_one_or_none()
    if user is None:
        raise NotFoundError("User not found", error_code="ERR-ADMIN-404")

    if user.id == auth.user_id:
        raise ValidationError("Cannot suspend yourself", error_code="ERR-ADMIN-422")

    user.status = "suspended"
    await db.flush()

    audit = AuditService(db)
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="USER_SUSPENDED",
        outcome="success",
        target_type="user",
        target_id=user_id,
        ip_address=_get_client_ip(request),
    )
    return success_response({"id": str(user_id), "status": "suspended"})


# ---------------------------------------------------------------------------
# PUT /admin/users/{user_id}/activate — Activate user
# ---------------------------------------------------------------------------
@router.put("/users/{user_id}/activate", summary="Activate a user")
async def activate_user(
    user_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission(ADMIN_PERM)),
    db: AsyncSession = Depends(get_db),
):
    """Activate a suspended user. ADM only."""
    if auth.role not in ("ADM",):
        raise ValidationError(
            "Only administrators can activate users", error_code="ERR-ADMIN-403"
        )

    user = (
        await db.execute(
            select(User).where(User.id == user_id, User.school_id == auth.school_id)
        )
    ).scalar_one_or_none()
    if user is None:
        raise NotFoundError("User not found", error_code="ERR-ADMIN-404")

    user.status = "active"
    await db.flush()

    audit = AuditService(db)
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="USER_ACTIVATED",
        outcome="success",
        target_type="user",
        target_id=user_id,
        ip_address=_get_client_ip(request),
    )
    return success_response({"id": str(user_id), "status": "active"})


# ---------------------------------------------------------------------------
# PUT /admin/users/{user_id}/role — Change user role
# ---------------------------------------------------------------------------
@router.put("/users/{user_id}/role", summary="Change user role")
async def change_user_role(
    user_id: uuid.UUID,
    request: Request,
    role: str = Query(..., description="New role code"),
    auth: AuthContext = Depends(requires_permission(ADMIN_PERM)),
    db: AsyncSession = Depends(get_db),
):
    """Change a user's role. ADM only. Valid roles: TCH, PAR, STD."""
    if auth.role not in ("ADM",):
        raise ValidationError(
            "Only administrators can change roles", error_code="ERR-ADMIN-403"
        )

    valid_targets = {"TCH", "PAR", "STD", "DIR"}
    if role not in valid_targets:
        raise ValidationError(
            f"Invalid role. Must be one of: {', '.join(sorted(valid_targets))}",
            error_code="ERR-ADMIN-422",
        )

    user = (
        await db.execute(
            select(User).where(User.id == user_id, User.school_id == auth.school_id)
        )
    ).scalar_one_or_none()
    if user is None:
        raise NotFoundError("User not found", error_code="ERR-ADMIN-404")

    if user.id == auth.user_id:
        raise ValidationError("Cannot change your own role", error_code="ERR-ADMIN-422")

    # Update the active membership
    await db.execute(
        update(Membership)
        .where(
            Membership.user_id == user_id,
            Membership.school_id == auth.school_id,
            Membership.status == "active",
        )
        .values(role_code=role)
    )
    await db.flush()

    audit = AuditService(db)
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="USER_ROLE_CHANGED",
        outcome="success",
        target_type="user",
        target_id=user_id,
        entity_after={"role": role},
        ip_address=_get_client_ip(request),
    )
    return success_response({"id": str(user_id), "role": role})


# ---------------------------------------------------------------------------
# GET /admin/invitations — List invitation codes
# ---------------------------------------------------------------------------
@router.get("/invitations", summary="List invitation codes")
async def list_invitations(
    auth: AuthContext = Depends(requires_permission(ADMIN_PERM)),
    db: AsyncSession = Depends(get_db),
    status: str | None = Query(None, description="Filter: active, consumed, expired"),
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    """List invitation codes for the school."""
    now = datetime.now(timezone.utc)
    query = select(InvitationCode).where(InvitationCode.school_id == auth.school_id)

    if status == "active":
        query = query.where(
            InvitationCode.consumed_at.is_(None),
            InvitationCode.expires_at > now,
        )
    elif status == "consumed":
        query = query.where(InvitationCode.consumed_at.isnot(None))
    elif status == "expired":
        query = query.where(
            InvitationCode.consumed_at.is_(None),
            InvitationCode.expires_at <= now,
        )

    query = query.order_by(InvitationCode.created_at.desc())

    if cursor:
        try:
            cursor_dt = datetime.fromisoformat(cursor)
            query = query.where(InvitationCode.created_at < cursor_dt)
        except ValueError:
            pass

    query = query.limit(limit + 1)
    result = await db.execute(query)
    rows = list(result.scalars().all())

    has_more = len(rows) > limit
    if has_more:
        rows = rows[:limit]

    data = [
        {
            "id": str(inv.id),
            "role_target": inv.role_target,
            "consumed_at": inv.consumed_at.isoformat() if inv.consumed_at else None,
            "consumed_by": str(inv.consumed_by) if inv.consumed_by else None,
            "expires_at": inv.expires_at.isoformat(),
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
            "issuer_user_id": str(inv.issuer_user_id) if inv.issuer_user_id else None,
            "status": (
                "consumed"
                if inv.consumed_at
                else ("expired" if inv.expires_at <= now else "active")
            ),
        }
        for inv in rows
    ]

    next_cursor = rows[-1].created_at.isoformat() if has_more and rows else None
    return list_response(data, next_cursor=next_cursor, has_more=has_more)


# ---------------------------------------------------------------------------
# GET /admin/audit-logs — List audit logs
# ---------------------------------------------------------------------------
@router.get("/audit-logs", summary="List audit logs")
async def list_audit_logs(
    auth: AuthContext = Depends(requires_permission(ADMIN_PERM)),
    db: AsyncSession = Depends(get_db),
    action_type: str | None = Query(None),
    correlation_id: str | None = Query(None),
    date_from: str | None = Query(None, description="ISO date"),
    date_to: str | None = Query(None, description="ISO date"),
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    """List audit logs for the school with optional filters."""
    query = select(AuditLog).where(AuditLog.school_id == auth.school_id)

    if action_type:
        query = query.where(AuditLog.action_type == action_type)

    if correlation_id:
        try:
            cid = uuid.UUID(correlation_id)
            query = query.where(AuditLog.correlation_id == cid)
        except ValueError:
            pass

    if date_from:
        try:
            query = query.where(
                AuditLog.created_at >= datetime.fromisoformat(date_from)
            )
        except ValueError:
            pass

    if date_to:
        try:
            query = query.where(AuditLog.created_at <= datetime.fromisoformat(date_to))
        except ValueError:
            pass

    query = query.order_by(AuditLog.created_at.desc())

    if cursor:
        try:
            cursor_dt = datetime.fromisoformat(cursor)
            query = query.where(AuditLog.created_at < cursor_dt)
        except ValueError:
            pass

    query = query.limit(limit + 1)
    result = await db.execute(query)
    rows = list(result.scalars().all())

    has_more = len(rows) > limit
    if has_more:
        rows = rows[:limit]

    data = [
        {
            "id": str(log.id),
            "action_type": log.action_type,
            "outcome": log.outcome,
            "actor_id": str(log.actor_id) if log.actor_id else None,
            "target_type": log.target_type,
            "target_id": str(log.target_id) if log.target_id else None,
            "error_code": log.error_code,
            "correlation_id": str(log.correlation_id) if log.correlation_id else None,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in rows
    ]

    next_cursor = rows[-1].created_at.isoformat() if has_more and rows else None
    return list_response(data, next_cursor=next_cursor, has_more=has_more)


# ---------------------------------------------------------------------------
# GET /admin/justifications — List pending justifications
# ---------------------------------------------------------------------------
@router.get("/justifications", summary="List absence justifications")
async def list_justifications(
    auth: AuthContext = Depends(requires_permission("PERM-ERP:absence:review")),
    db: AsyncSession = Depends(get_db),
    status: str | None = Query("pending", description="Filter by status"),
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    """List absence justifications for review."""
    query = select(AbsenceJustification).where(
        AbsenceJustification.school_id == auth.school_id
    )

    if status:
        query = query.where(AbsenceJustification.status == status)

    query = query.order_by(AbsenceJustification.created_at.desc())

    if cursor:
        try:
            cursor_dt = datetime.fromisoformat(cursor)
            query = query.where(AbsenceJustification.created_at < cursor_dt)
        except ValueError:
            pass

    query = query.limit(limit + 1)
    result = await db.execute(query)
    rows = list(result.scalars().all())

    has_more = len(rows) > limit
    if has_more:
        rows = rows[:limit]

    data = [
        {
            "id": str(j.id),
            "attendance_record_id": str(j.attendance_record_id),
            "parent_id": str(j.parent_id),
            "status": j.status,
            "reason": j.reason,
            "rejection_reason": j.rejection_reason,
            "created_at": j.created_at.isoformat() if j.created_at else None,
        }
        for j in rows
    ]

    next_cursor = rows[-1].created_at.isoformat() if has_more and rows else None
    return list_response(data, next_cursor=next_cursor, has_more=has_more)


# ---------------------------------------------------------------------------
# POST /admin/register-batch — Bulk create accounts (Phase 2C)
# ---------------------------------------------------------------------------
@router.post("/register-batch", status_code=201, summary="Bulk register users")
async def register_batch(
    body: BatchRegisterRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(ADMIN_PERM)),
    db: AsyncSession = Depends(get_db),
):
    """Bulk-create user accounts from a list.

    For each entry: creates user with a generated password, membership, and
    invitation code (consumed immediately). Skips entries where email already exists.
    Returns created accounts with their temporary passwords.
    """
    import secrets
    import hashlib
    from datetime import datetime, timezone

    audit = AuditService(db)
    school_id = auth.school_id
    results: list[dict] = []
    errors: list[dict] = []

    for item in body.users:
        # Check email uniqueness
        existing = await db.execute(
            select(User).where(User.email == item.email, User.school_id == school_id)
        )
        if existing.scalar_one_or_none() is not None:
            errors.append(
                {
                    "email": item.email,
                    "error": "Email already exists for this school",
                }
            )
            continue

        # Validate role
        if item.role not in ("STD", "PAR", "TCH", "ADM", "DIR"):
            errors.append(
                {
                    "email": item.email,
                    "error": f"Invalid role: {item.role}",
                }
            )
            continue

        # Generate temporary password (16 chars, meets policy)
        temp_password = secrets.token_urlsafe(12) + "A1!"

        # Create user
        user = User(
            email=item.email,
            full_name=item.full_name,
            phone=item.phone,
            password_hash=hash_password(temp_password),
            status="active",
            school_id=school_id,
        )
        db.add(user)
        await db.flush()

        # Create membership
        membership = Membership(
            user_id=user.id,
            school_id=school_id,
            role_code=item.role,
            status="active",
        )
        db.add(membership)

        # Create a consumed invitation code for audit trail
        code = secrets.token_hex(4).upper()
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        invite = InvitationCode(
            school_id=school_id,
            issuer_user_id=auth.user_id,
            code_hash=code_hash,
            role_target=item.role,
            consumed_by=user.id,
            consumed_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc),
            target_student_id=item.target_student_id if item.role == "PAR" else None,
        )
        db.add(invite)
        await db.flush()

        # Phase 2D: Auto-create parent-child link for PAR with target_student_id
        if item.role == "PAR" and item.target_student_id:
            # Validate student exists in the same school
            std_check = await db.execute(
                select(User)
                .join(Membership)
                .where(
                    User.id == item.target_student_id,
                    User.school_id == school_id,
                    Membership.role_code == "STD",
                    Membership.school_id == school_id,
                )
            )
            if std_check.scalar_one_or_none() is not None:
                link = ParentChildLink(
                    parent_user_id=user.id,
                    child_user_id=item.target_student_id,
                    school_id=school_id,
                    status="active",
                    linked_at=datetime.now(timezone.utc),
                    linked_by=auth.user_id,
                )
                db.add(link)
                await db.flush()

        # Audit
        await audit.log_event(
            school_id=school_id,
            actor_id=auth.user_id,
            action_type="USER_BATCH_REGISTERED",
            outcome="success",
            target_type="user",
            target_id=user.id,
            ip_address=_get_client_ip(request),
        )

        results.append(
            {
                "user_id": str(user.id),
                "email": item.email,
                "full_name": item.full_name,
                "role": item.role,
                "temp_password": temp_password,
            }
        )

    await db.commit()

    return success_response(
        {
            "created": results,
            "errors": errors,
            "total_created": len(results),
            "total_errors": len(errors),
        }
    )


# ---------------------------------------------------------------------------
# POST /admin/parent-child-links — Manually link parent ↔ student (Phase 2D)
# ---------------------------------------------------------------------------
@router.post("/parent-child-links", status_code=201, summary="Create parent-child link")
async def create_parent_child_link(
    request: Request,
    parent_user_id: uuid.UUID = Query(..., description="Parent user ID"),
    child_user_id: uuid.UUID = Query(..., description="Student user ID"),
    auth: AuthContext = Depends(requires_permission("PERM-IAM:parent-link:create")),
    db: AsyncSession = Depends(get_db),
):
    """Admin manually links a parent to a student within the same school."""
    school_id = auth.school_id

    # Validate parent exists with PAR role in this school
    par_result = await db.execute(
        select(User)
        .join(Membership)
        .where(
            User.id == parent_user_id,
            User.school_id == school_id,
            Membership.role_code == "PAR",
            Membership.school_id == school_id,
        )
    )
    if par_result.scalar_one_or_none() is None:
        raise NotFoundError(
            "Parent user not found in this school", error_code="ERR-RES-404"
        )

    # Validate student exists with STD role in this school
    std_result = await db.execute(
        select(User)
        .join(Membership)
        .where(
            User.id == child_user_id,
            User.school_id == school_id,
            Membership.role_code == "STD",
            Membership.school_id == school_id,
        )
    )
    if std_result.scalar_one_or_none() is None:
        raise NotFoundError(
            "Student user not found in this school", error_code="ERR-RES-404"
        )

    # Check for existing active link
    existing = await db.execute(
        select(ParentChildLink).where(
            ParentChildLink.parent_user_id == parent_user_id,
            ParentChildLink.child_user_id == child_user_id,
            ParentChildLink.school_id == school_id,
            ParentChildLink.status == "active",
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictError(
            "Parent-child link already exists", error_code="ERR-CONFLICT-001"
        )

    link = ParentChildLink(
        parent_user_id=parent_user_id,
        child_user_id=child_user_id,
        school_id=school_id,
        status="active",
        linked_at=datetime.now(timezone.utc),
        linked_by=auth.user_id,
    )
    db.add(link)

    audit = AuditService(db)
    await audit.log_event(
        school_id=school_id,
        actor_id=auth.user_id,
        action_type="PARENT_CHILD_LINKED",
        outcome="success",
        target_type="parent_child_link",
        target_id=link.id,
        ip_address=_get_client_ip(request),
    )

    await db.commit()

    return success_response(
        {
            "id": str(link.id),
            "parent_user_id": str(link.parent_user_id),
            "child_user_id": str(link.child_user_id),
            "school_id": str(link.school_id),
            "status": link.status,
            "linked_at": link.linked_at.isoformat(),
            "linked_by": str(link.linked_by),
        }
    )


# ---------------------------------------------------------------------------
# GET /admin/parent-child-links — List links (filtered, cursor-paginated) (Phase 2D)
# ---------------------------------------------------------------------------
@router.get("/parent-child-links", summary="List parent-child links")
async def list_parent_child_links(
    parent_id: uuid.UUID | None = Query(None, description="Filter by parent user ID"),
    student_id: uuid.UUID | None = Query(None, description="Filter by student user ID"),
    status: str | None = Query(None, description="Filter by status (active, revoked)"),
    cursor: str | None = Query(
        None, description="Cursor for pagination (linked_at ISO)"
    ),
    limit: int = Query(20, ge=1, le=100),
    auth: AuthContext = Depends(requires_permission("PERM-IAM:parent-link:read")),
    db: AsyncSession = Depends(get_db),
):
    """List parent-child links within the admin's school, with optional filters."""
    school_id = auth.school_id

    query = select(ParentChildLink).where(ParentChildLink.school_id == school_id)

    if parent_id is not None:
        query = query.where(ParentChildLink.parent_user_id == parent_id)
    if student_id is not None:
        query = query.where(ParentChildLink.child_user_id == student_id)
    if status is not None:
        query = query.where(ParentChildLink.status == status)

    if cursor:
        cursor_dt = datetime.fromisoformat(cursor)
        query = query.where(ParentChildLink.linked_at < cursor_dt)

    query = query.order_by(ParentChildLink.linked_at.desc()).limit(limit + 1)

    result = await db.execute(query)
    rows = list(result.scalars().all())

    has_more = len(rows) > limit
    if has_more:
        rows = rows[:limit]

    data = [
        {
            "id": str(link.id),
            "parent_user_id": str(link.parent_user_id),
            "child_user_id": str(link.child_user_id),
            "school_id": str(link.school_id),
            "status": link.status,
            "linked_at": link.linked_at.isoformat() if link.linked_at else None,
            "linked_by": str(link.linked_by) if link.linked_by else None,
        }
        for link in rows
    ]

    next_cursor = rows[-1].linked_at.isoformat() if has_more and rows else None
    return list_response(data, next_cursor=next_cursor, has_more=has_more)


# ---------------------------------------------------------------------------
# DELETE /admin/parent-child-links/{link_id} — Revoke link (Phase 2D)
# ---------------------------------------------------------------------------
@router.delete("/parent-child-links/{link_id}", summary="Revoke parent-child link")
async def revoke_parent_child_link(
    link_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-IAM:parent-link:delete")),
    db: AsyncSession = Depends(get_db),
):
    """Soft-revoke a parent-child link (sets status to 'revoked')."""
    school_id = auth.school_id

    result = await db.execute(
        select(ParentChildLink).where(
            ParentChildLink.id == link_id,
            ParentChildLink.school_id == school_id,
        )
    )
    link = result.scalar_one_or_none()
    if link is None:
        raise NotFoundError("Parent-child link not found", error_code="ERR-RES-404")

    if link.status == "revoked":
        return success_response({"message": "Link already revoked", "id": str(link.id)})

    link.status = "revoked"

    audit = AuditService(db)
    await audit.log_event(
        school_id=school_id,
        actor_id=auth.user_id,
        action_type="PARENT_CHILD_UNLINKED",
        outcome="success",
        target_type="parent_child_link",
        target_id=link.id,
        ip_address=_get_client_ip(request),
    )

    await db.commit()

    return success_response(
        {
            "id": str(link.id),
            "status": link.status,
            "message": "Parent-child link revoked",
        }
    )
