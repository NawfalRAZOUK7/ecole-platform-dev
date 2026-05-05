"""Phase 3 integration tests — program versions, equivalences, snapshots,
and eligibility rules. Smoke-level coverage that exercises each new
endpoint's happy path + the most important error paths.

Run with:
    pytest tests/integration/test_program_g50_phase3.py
"""

from __future__ import annotations

import pytest

from tests.integration.api.helpers import auth_header


# ---------------------------------------------------------------------------
# 3.1 — program_versions
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_program_versions_crud(client, api_context):
    admin_token = api_context["admin"]["token"]

    program = (
        await client.post(
            "/programs",
            headers=auth_header(admin_token),
            json={"code": "SCI-MATH", "name": "Sciences Mathématiques"},
        )
    ).json()["data"]

    # Backfill: a v1.0 should already exist via the migration. Listing
    # must include at least one row.
    list_resp = await client.get(
        f"/programs/{program['id']}/versions",
        headers=auth_header(admin_token),
    )
    assert list_resp.status_code == 200, list_resp.text
    assert any(v["version_label"] == "1.0" for v in list_resp.json()["data"])

    # Create a new version.
    create_resp = await client.post(
        f"/programs/{program['id']}/versions",
        headers=auth_header(admin_token),
        json={"version_label": "2.0", "description": "2026 revision"},
    )
    assert create_resp.status_code == 201, create_resp.text
    new_version = create_resp.json()["data"]
    assert new_version["version_label"] == "2.0"
    assert new_version["is_active"] is True

    # Idempotent re-create returns the same row.
    again_resp = await client.post(
        f"/programs/{program['id']}/versions",
        headers=auth_header(admin_token),
        json={"version_label": "2.0", "description": "2026 revision"},
    )
    assert again_resp.json()["data"]["id"] == new_version["id"]

    # Patch.
    patch_resp = await client.patch(
        f"/programs/{program['id']}/versions/{new_version['id']}",
        headers=auth_header(admin_token),
        json={"is_active": False, "retired_at": "2026-12-31"},
    )
    assert patch_resp.status_code == 200, patch_resp.text
    body = patch_resp.json()["data"]
    assert body["is_active"] is False
    assert body["retired_at"] == "2026-12-31"


@pytest.mark.asyncio
async def test_teacher_cannot_create_version(client, api_context):
    teacher_token = api_context["teacher"]["token"]
    admin_token = api_context["admin"]["token"]

    program = (
        await client.post(
            "/programs",
            headers=auth_header(admin_token),
            json={"code": "LM", "name": "Lettres Modernes"},
        )
    ).json()["data"]

    response = await client.post(
        f"/programs/{program['id']}/versions",
        headers=auth_header(teacher_token),
        json={"version_label": "2.0"},
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# 3.2 — program_equivalences
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_program_equivalences_crud_and_filter(client, api_context):
    admin_token = api_context["admin"]["token"]

    p1 = (
        await client.post(
            "/programs",
            headers=auth_header(admin_token),
            json={"code": "SCI-MATH", "name": "Sciences Mathématiques"},
        )
    ).json()["data"]
    p2 = (
        await client.post(
            "/programs",
            headers=auth_header(admin_token),
            json={"code": "SCI-MATH-V2", "name": "Sciences Maths v2"},
        )
    ).json()["data"]

    create_resp = await client.post(
        "/program-equivalences",
        headers=auth_header(admin_token),
        json={
            "from_program_id": p1["id"],
            "to_program_id": p2["id"],
            "kind": "EQUIVALENT",
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    eq = create_resp.json()["data"]
    assert eq["kind"] == "EQUIVALENT"

    # Idempotent on (school, from, to).
    again = await client.post(
        "/program-equivalences",
        headers=auth_header(admin_token),
        json={
            "from_program_id": p1["id"],
            "to_program_id": p2["id"],
            "kind": "EQUIVALENT",
        },
    )
    assert again.json()["data"]["id"] == eq["id"]

    # Reject self-equivalence (422).
    bad = await client.post(
        "/program-equivalences",
        headers=auth_header(admin_token),
        json={
            "from_program_id": p1["id"],
            "to_program_id": p1["id"],
            "kind": "EQUIVALENT",
        },
    )
    assert bad.status_code == 422

    # Filter by program: each side of the pair surfaces the row.
    filtered = await client.get(
        f"/program-equivalences?program_id={p1['id']}",
        headers=auth_header(admin_token),
    )
    assert filtered.status_code == 200
    assert any(e["id"] == eq["id"] for e in filtered.json()["data"])

    # Delete.
    delete_resp = await client.delete(
        f"/program-equivalences/{eq['id']}",
        headers=auth_header(admin_token),
    )
    assert delete_resp.status_code == 204


# ---------------------------------------------------------------------------
# 3.3 — academic_snapshots
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_academic_snapshot_take_and_read(client, api_context, session_factory):
    """Take a snapshot for the api_context student + their academic year,
    read it back, then list snapshots for that student.
    """
    admin_token = api_context["admin"]["token"]
    student_id = str(api_context["student"]["user"].id)
    if "academic_year" not in api_context:
        pytest.skip("api_context does not surface academic_year")
    academic_year_id = str(api_context["academic_year"].id)

    take_resp = await client.post(
        "/academic-snapshots",
        headers=auth_header(admin_token),
        json={
            "student_id": student_id,
            "academic_year_id": academic_year_id,
            "snapshot_kind": "MANUAL",
        },
    )
    assert take_resp.status_code == 201, take_resp.text
    snapshot = take_resp.json()["data"]
    assert snapshot["snapshot_kind"] == "MANUAL"
    assert snapshot["snapshot_data"]["schema_version"] == 1
    assert "enrollments" in snapshot["snapshot_data"]
    assert "grades_summary" in snapshot["snapshot_data"]
    assert "attendance_summary" in snapshot["snapshot_data"]

    # Read by id.
    get_resp = await client.get(
        f"/academic-snapshots/{snapshot['id']}",
        headers=auth_header(admin_token),
    )
    assert get_resp.status_code == 200

    # List for student.
    list_resp = await client.get(
        f"/students/{student_id}/snapshots",
        headers=auth_header(admin_token),
    )
    assert list_resp.status_code == 200
    items = list_resp.json()["data"]
    assert any(s["id"] == snapshot["id"] for s in items)


@pytest.mark.asyncio
async def test_transcript_preview_and_snapshot_modes(
    client, api_context, session_factory
):
    admin_token = api_context["admin"]["token"]
    student_token = api_context["student"]["token"]
    student_id = str(api_context["student"]["user"].id)
    academic_year_id = str(api_context["academic_year"].id)

    take_resp = await client.post(
        "/academic-snapshots",
        headers=auth_header(admin_token),
        json={
            "student_id": student_id,
            "academic_year_id": academic_year_id,
            "snapshot_kind": "YEAR_END",
        },
    )
    assert take_resp.status_code == 201, take_resp.text
    snapshot = take_resp.json()["data"]

    preview_resp = await client.get(
        f"/students/{student_id}/transcript?academic_year_id={academic_year_id}&mode=preview",
        headers=auth_header(student_token),
    )
    assert preview_resp.status_code == 200, preview_resp.text
    preview = preview_resp.json()["data"]
    assert preview["source"]["mode"] == "preview"
    assert preview["student"]["id"] == student_id
    assert preview["academic_year"]["id"] == academic_year_id
    assert "school" in preview
    assert "equivalence_resolutions" in preview

    snapshot_mode_resp = await client.get(
        f"/students/{student_id}/transcript?academic_year_id={academic_year_id}&mode=snapshot",
        headers=auth_header(student_token),
    )
    assert snapshot_mode_resp.status_code == 200, snapshot_mode_resp.text
    snapshot_mode = snapshot_mode_resp.json()["data"]
    assert snapshot_mode["source"]["mode"] == "snapshot"
    assert snapshot_mode["source"]["snapshot_id"] == snapshot["id"]
    assert snapshot_mode["source"]["snapshot_kind"] == "YEAR_END"

    direct_snapshot_resp = await client.get(
        f"/academic-snapshots/{snapshot['id']}/transcript",
        headers=auth_header(student_token),
    )
    assert direct_snapshot_resp.status_code == 200, direct_snapshot_resp.text
    direct = direct_snapshot_resp.json()["data"]
    assert direct["source"]["snapshot_id"] == snapshot["id"]

    preview_html_resp = await client.get(
        f"/students/{student_id}/transcript/html?academic_year_id={academic_year_id}&mode=preview&lang=fr",
        headers=auth_header(student_token),
    )
    assert preview_html_resp.status_code == 200, preview_html_resp.text
    assert "Releve academique" in preview_html_resp.text
    assert "Classe" in preview_html_resp.text

    snapshot_html_resp = await client.get(
        f"/academic-snapshots/{snapshot['id']}/transcript/html?lang=en",
        headers=auth_header(student_token),
    )
    assert snapshot_html_resp.status_code == 200, snapshot_html_resp.text
    assert "Academic Transcript" in snapshot_html_resp.text

    preview_pdf_resp = await client.get(
        f"/students/{student_id}/transcript/pdf?academic_year_id={academic_year_id}&mode=preview&lang=fr",
        headers=auth_header(student_token),
    )
    assert preview_pdf_resp.status_code == 200, preview_pdf_resp.text
    assert preview_pdf_resp.headers["content-type"].startswith("application/pdf")
    assert preview_pdf_resp.content.startswith(b"%PDF")

    snapshot_pdf_resp = await client.get(
        f"/academic-snapshots/{snapshot['id']}/transcript/pdf?lang=en",
        headers=auth_header(student_token),
    )
    assert snapshot_pdf_resp.status_code == 200, snapshot_pdf_resp.text
    assert snapshot_pdf_resp.headers["content-type"].startswith("application/pdf")
    assert snapshot_pdf_resp.content.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_transcript_resolves_program_equivalences(
    client, api_context, session_factory
):
    admin_token = api_context["admin"]["token"]
    student_token = api_context["student"]["token"]
    student_uuid = api_context["student"]["user"].id
    student_id = str(student_uuid)
    academic_year_id = str(api_context["academic_year"].id)

    from tests.integration.test_program_g49 import _active_enrollment_id

    enrollment_id = await _active_enrollment_id(session_factory, student_uuid)

    p1 = (
        await client.post(
            "/programs",
            headers=auth_header(admin_token),
            json={"code": "SCI-MATH", "name": "Sciences Mathématiques"},
        )
    ).json()["data"]
    p2 = (
        await client.post(
            "/programs",
            headers=auth_header(admin_token),
            json={"code": "SCI-MATH-V2", "name": "Sciences Maths v2"},
        )
    ).json()["data"]

    assign_resp = await client.post(
        f"/enrollments/{enrollment_id}/program",
        headers=auth_header(admin_token),
        json={"program_id": p1["id"], "reason_code": "INITIAL"},
    )
    assert assign_resp.status_code == 201, assign_resp.text

    eq_resp = await client.post(
        "/program-equivalences",
        headers=auth_header(admin_token),
        json={
            "from_program_id": p1["id"],
            "to_program_id": p2["id"],
            "kind": "EQUIVALENT",
        },
    )
    assert eq_resp.status_code == 201, eq_resp.text

    transcript_resp = await client.get(
        f"/students/{student_id}/transcript?academic_year_id={academic_year_id}&mode=preview",
        headers=auth_header(student_token),
    )
    assert transcript_resp.status_code == 200, transcript_resp.text
    transcript = transcript_resp.json()["data"]
    assert len(transcript["equivalence_resolutions"]) >= 1
    resolution = next(
        item
        for item in transcript["equivalence_resolutions"]
        if item["program"]["id"] == p1["id"]
    )
    resolved_ids = set(resolution["resolved_program_ids"])
    assert p1["id"] in resolved_ids
    assert p2["id"] in resolved_ids


# ---------------------------------------------------------------------------
# 3.4 — eligibility rules
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eligibility_rule_crud_and_check(client, api_context):
    admin_token = api_context["admin"]["token"]
    student_id = str(api_context["student"]["user"].id)

    program = (
        await client.post(
            "/programs",
            headers=auth_header(admin_token),
            json={"code": "SCI-MATH", "name": "Sciences Mathématiques"},
        )
    ).json()["data"]

    # Create a rule that always evaluates against attendance — student has
    # no attendance records in the fixture so the rule fails by default,
    # which is fine for this smoke test (we just verify the contract).
    create_resp = await client.post(
        "/eligibility/rules",
        headers=auth_header(admin_token),
        json={
            "kind": "PROMOTION",
            "target_program_id": program["id"],
            "condition_type": "min_attendance_rate",
            "condition_params": {"min_rate": 0.8},
            "message_key": "eligibility.attendance.required",
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    rule = create_resp.json()["data"]

    # Reject unknown condition_type (422).
    bad = await client.post(
        "/eligibility/rules",
        headers=auth_header(admin_token),
        json={
            "kind": "PROMOTION",
            "target_program_id": program["id"],
            "condition_type": "i_made_this_up",
            "message_key": "x",
        },
    )
    assert bad.status_code == 422

    # Run the check.
    check_resp = await client.get(
        f"/students/{student_id}/eligibility"
        f"?kind=PROMOTION&target_program_id={program['id']}",
        headers=auth_header(admin_token),
    )
    assert check_resp.status_code == 200, check_resp.text
    body = check_resp.json()["data"]
    assert body["student_id"] == student_id
    assert body["target_program_id"] == program["id"]
    assert isinstance(body["rules"], list) and len(body["rules"]) >= 1

    # Delete.
    delete_resp = await client.delete(
        f"/eligibility/rules/{rule['id']}",
        headers=auth_header(admin_token),
    )
    assert delete_resp.status_code == 204


@pytest.mark.asyncio
async def test_min_attendance_rate_honours_academic_year_id(client, api_context):
    """Polish #5: a rule scoped to an academic_year_id must filter the
    attendance window. We exercise the contract via the public API:
    creating a rule with academic_year_id should yield a check whose
    `detail` mentions the year scope (not the all-time scope)."""
    admin_token = api_context["admin"]["token"]
    student_id = str(api_context["student"]["user"].id)
    if "academic_year" not in api_context:
        pytest.skip("api_context does not surface academic_year")
    academic_year_id = str(api_context["academic_year"].id)

    program = (
        await client.post(
            "/programs",
            headers=auth_header(admin_token),
            json={"code": "SCI-MATH", "name": "Sciences Mathématiques"},
        )
    ).json()["data"]

    await client.post(
        "/eligibility/rules",
        headers=auth_header(admin_token),
        json={
            "kind": "PROMOTION",
            "target_program_id": program["id"],
            "condition_type": "min_attendance_rate",
            "condition_params": {
                "min_rate": 0.8,
                "academic_year_id": academic_year_id,
            },
            "message_key": "eligibility.attendance.year",
        },
    )

    check_resp = await client.get(
        f"/students/{student_id}/eligibility"
        f"?kind=PROMOTION&target_program_id={program['id']}",
        headers=auth_header(admin_token),
    )
    assert check_resp.status_code == 200, check_resp.text
    body = check_resp.json()["data"]
    rule_results = [
        r for r in body["rules"] if r["condition_type"] == "min_attendance_rate"
    ]
    assert rule_results, "expected at least one min_attendance_rate result"
    # The detail must contain the "year=" marker — proves the year filter
    # actually ran rather than silently defaulting to all-time.
    assert any("year=" in (r.get("detail") or "") for r in rule_results)
