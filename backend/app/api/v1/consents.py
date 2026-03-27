"""Consent API endpoint: PUT /consents/{consent_id}.

Reference: S-066 — Update consent preference (PAR, ADM).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    AuthContext,
    requires_permission,
    verify_school_boundary,
)
from app.core.exceptions import NotFoundError
from app.core.response import (
    clamp_page_size,
    decode_cursor,
    encode_cursor,
    list_response,
    success_response,
)
from app.models.com import ConsentPreference
from app.schemas.com import ConsentUpdateRequest
from app.services.audit import AuditService

router = APIRouter(prefix="/consents", tags=["com-consents"])


def _get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


@router.get(
    "",
    summary="List consent preferences",
    response_description="List of consent settings",
)
async def list_consents(
    cursor: str | None = Query(None),
    limit: int | None = Query(None),
    auth: AuthContext = Depends(requires_permission("PERM-COM:consent:update")),
    db: AsyncSession = Depends(get_db),
):
    """List consent preferences.

    PAR: sees own consents only.
    ADM: sees all school consents.
    """
    page_size = clamp_page_size(limit)

    query = select(ConsentPreference).where(
        ConsentPreference.school_id == auth.school_id
    )

    # PAR: only own consents
    if auth.role == "PAR":
        query = query.where(ConsentPreference.user_id == auth.user_id)

    if cursor:
        last_id, _ = decode_cursor(cursor)
        query = query.where(ConsentPreference.id > last_id)

    query = query.order_by(ConsentPreference.id).limit(page_size + 1)
    result = await db.execute(query)
    consents = list(result.scalars().all())

    has_more = len(consents) > page_size
    if has_more:
        consents = consents[:page_size]

    items = [
        {
            "id": str(c.id),
            "user_id": str(c.user_id),
            "school_id": str(c.school_id),
            "topic": c.topic,
            "channel": c.channel,
            "scope_type": c.scope_type,
            "scope_ref_id": str(c.scope_ref_id) if c.scope_ref_id else None,
            "status": c.status,
        }
        for c in consents
    ]

    next_cursor = encode_cursor(consents[-1].id) if has_more and consents else None
    return list_response(items, next_cursor=next_cursor, has_more=has_more)


@router.put(
    "/{consent_id}",
    summary="Update consent preference",
    response_description="Updated consent record",
)
async def update_consent(
    consent_id: uuid.UUID,
    body: ConsentUpdateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-COM:consent:update")),
    db: AsyncSession = Depends(get_db),
):
    """Update a consent preference.

    PAR: can only update own consents.
    ADM: can update any consent in the school.
    """
    audit = AuditService(db)

    result = await db.execute(
        select(ConsentPreference).where(ConsentPreference.id == consent_id)
    )
    consent = result.scalar_one_or_none()
    if consent is None:
        raise NotFoundError("Consent preference not found", error_code="ERR-COM-404")

    verify_school_boundary(consent.school_id, auth)

    # PAR can only update own consents
    if auth.role == "PAR" and consent.user_id != auth.user_id:
        raise NotFoundError("Consent preference not found", error_code="ERR-COM-404")

    # Track old status for audit
    old_status = consent.status

    # Update
    consent.status = body.status
    await db.flush()

    # Audit
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="CONSENT_UPDATED",
        outcome="success",
        target_type="consent_preference",
        target_id=consent.id,
        entity_before={"status": old_status},
        entity_after={"status": body.status},
        ip_address=_get_client_ip(request),
    )

    return success_response(
        {
            "id": str(consent.id),
            "user_id": str(consent.user_id),
            "school_id": str(consent.school_id),
            "topic": consent.topic,
            "channel": consent.channel,
            "scope_type": consent.scope_type,
            "scope_ref_id": str(consent.scope_ref_id) if consent.scope_ref_id else None,
            "status": consent.status,
        }
    )
