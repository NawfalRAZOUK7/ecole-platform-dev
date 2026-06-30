"""Content-scope ABAC tests (D3 — anti-IDOR on CMS content).

A student/parent must only reach a `content_item` that is assigned to their
class — even with a valid id via a direct API call (404 otherwise). A teacher's
public library is filtered to the level bands they actually teach.

Backing logic: `ContentService` + `LMSServiceBase._content_assigned_to_user`
(`app/services/lms/_helpers.py`, `app/services/lms/content_service.py`).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.models.lms import ClassContentAssignment, ContentItem
from tests.security.conftest import (
    CLASS_UUID,
    SCHOOL_UUID,
    TEACHER_UUID,
    _security_session,
    auth_header,
)


async def _create_content(
    *,
    level_band: str = "6eme",
    subject: str = "math",
    assign_class: uuid.UUID | None = None,
    status: str = "published",
    school_id: uuid.UUID | None = SCHOOL_UUID,
) -> uuid.UUID:
    """Create a content item, optionally assigned to a class. Returns its id."""
    item_id = uuid.uuid4()
    async with _security_session() as db:
        db.add(
            ContentItem(
                id=item_id,
                school_id=school_id,
                title=f"Scope fixture {item_id.hex[:8]}",
                content_type="pdf",
                level_band=level_band,
                language="fr",
                subject=subject,
                description="content-scope security fixture",
                status=status,
                origin="PLATFORM",
                created_by=TEACHER_UUID,
            )
        )
        await db.flush()
        if assign_class is not None:
            db.add(
                ClassContentAssignment(
                    teacher_id=TEACHER_UUID,
                    class_id=assign_class,
                    content_item_id=item_id,
                    school_id=SCHOOL_UUID,
                    assigned_at=datetime.now(timezone.utc),
                )
            )
        await db.commit()
    return item_id


# --------------------------------------------------------------------------- #
# Student — direct-id access must respect class assignment                      #
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_student_can_read_content_assigned_to_their_class(client, student_token):
    item = await _create_content(assign_class=CLASS_UUID)
    r = await client.get(
        f"/content-items/{item}", headers=auth_header(student_token)
    )
    assert r.status_code == 200, r.text


@pytest.mark.asyncio
async def test_student_cannot_read_unassigned_content_by_id(client, student_token):
    item = await _create_content(assign_class=None)
    r = await client.get(
        f"/content-items/{item}", headers=auth_header(student_token)
    )
    assert r.status_code == 404, r.text


@pytest.mark.asyncio
async def test_student_cannot_stream_unassigned_content(client, student_token):
    item = await _create_content(assign_class=None)
    r = await client.get(
        f"/content-items/{item}/stream", headers=auth_header(student_token)
    )
    assert r.status_code == 404, r.text


@pytest.mark.asyncio
async def test_student_cannot_progress_unassigned_content(client, student_token):
    item = await _create_content(assign_class=None)
    r = await client.post(
        f"/content-items/{item}/progress",
        headers=auth_header(student_token),
        json={"status": "in_progress"},
    )
    assert r.status_code == 404, r.text


@pytest.mark.asyncio
async def test_student_cannot_complete_unassigned_content(client, student_token):
    item = await _create_content(assign_class=None)
    r = await client.post(
        f"/content-items/{item}/complete",
        headers=auth_header(student_token),
        json={"time_spent_seconds": 30},
    )
    assert r.status_code == 404, r.text


@pytest.mark.asyncio
async def test_student_library_excludes_unassigned_includes_assigned(
    client, student_token
):
    assigned = await _create_content(assign_class=CLASS_UUID)
    unassigned = await _create_content(assign_class=None)
    r = await client.get(
        "/content-items", headers=auth_header(student_token), params={"limit": 100}
    )
    assert r.status_code == 200, r.text
    ids = {item["id"] for item in r.json()["data"]}
    assert str(assigned) in ids
    assert str(unassigned) not in ids


# --------------------------------------------------------------------------- #
# Parent — inherits the linked child's class scope                              #
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_parent_can_read_content_assigned_to_child_class(client, parent_token):
    item = await _create_content(assign_class=CLASS_UUID)
    r = await client.get(
        f"/content-items/{item}", headers=auth_header(parent_token)
    )
    assert r.status_code == 200, r.text


@pytest.mark.asyncio
async def test_parent_cannot_read_unassigned_content_by_id(client, parent_token):
    item = await _create_content(assign_class=None)
    r = await client.get(
        f"/content-items/{item}", headers=auth_header(parent_token)
    )
    assert r.status_code == 404, r.text


# --------------------------------------------------------------------------- #
# Teacher — CMS library filtered to the level bands they teach (class 6eme-A)   #
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_teacher_library_filtered_to_taught_level_bands(client, teacher_token):
    cp_item = await _create_content(level_band="1AEP", school_id=None)
    sixeme_item = await _create_content(level_band="1AC", school_id=None)
    r = await client.get(
        "/content-items", headers=auth_header(teacher_token), params={"limit": 100}
    )
    assert r.status_code == 200, r.text
    ids = {item["id"] for item in r.json()["data"]}
    # Teacher of 6eme-A must not see another level's library, but must see 6eme.
    assert str(cp_item) not in ids
    assert str(sixeme_item) in ids
