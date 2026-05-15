"""Integration tests for Phase 3D — Advanced Query Filters & Full-text Search.

Tests filter, sort, search, and pagination composition on list endpoints.
Requires seed data to be loaded (make seed).
"""

from __future__ import annotations

import pytest


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ======================================================================
# Filtering — ?filter[field__op]=value
# ======================================================================
class TestFiltering:
    @pytest.mark.asyncio
    async def test_filter_courses_by_status(self, client, teacher_token):
        """Filter courses by status using generic filter syntax."""
        resp = await client.get(
            "/courses?filter[status]=published",
            headers=auth_header(teacher_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        # All returned courses should have status=published (if any)
        for item in body["data"]:
            assert item["status"] == "published"

    @pytest.mark.asyncio
    async def test_filter_assessments_by_status(self, client, admin_token):
        """Filter assessments by status."""
        resp = await client.get(
            "/assessments?filter[status]=draft",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        for item in body["data"]:
            assert item["status"] == "draft"

    @pytest.mark.asyncio
    async def test_filter_invoices_by_status(self, client, admin_token):
        """Filter invoices by status using generic filter syntax."""
        resp = await client.get(
            "/invoices?filter[status]=pending",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        for item in body["data"]:
            assert item["status"] == "pending"

    @pytest.mark.asyncio
    async def test_filter_like_operator(self, client, teacher_token):
        """Filter using ILIKE (__like) operator."""
        resp = await client.get(
            "/courses?filter[title__like]=math",
            headers=auth_header(teacher_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        # If results, title should contain 'math' (case-insensitive)
        for item in body["data"]:
            assert "math" in item["title"].lower()

    @pytest.mark.asyncio
    async def test_filter_in_operator(self, client, admin_token):
        """Filter using IN operator with comma-separated values."""
        resp = await client.get(
            "/assessments?filter[status__in]=draft,published",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        for item in body["data"]:
            assert item["status"] in ("draft", "published")

    @pytest.mark.asyncio
    async def test_unknown_filter_field_ignored(self, client, teacher_token):
        """Unknown filter fields are silently ignored (not in allowlist)."""
        resp = await client.get(
            "/courses?filter[nonexistent_field]=foo",
            headers=auth_header(teacher_token),
        )
        assert resp.status_code == 200


# ======================================================================
# Sorting — ?sort=-field,field
# ======================================================================
class TestSorting:
    @pytest.mark.asyncio
    async def test_sort_courses_by_title_asc(self, client, teacher_token):
        """Sort courses by title ascending."""
        resp = await client.get(
            "/courses?sort=title",
            headers=auth_header(teacher_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        titles = [item["title"] for item in body["data"]]
        assert titles == sorted(titles)

    @pytest.mark.asyncio
    async def test_sort_courses_by_title_desc(self, client, teacher_token):
        """Sort courses by title descending."""
        resp = await client.get(
            "/courses?sort=-title",
            headers=auth_header(teacher_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        titles = [item["title"] for item in body["data"]]
        assert titles == sorted(titles, reverse=True)

    @pytest.mark.asyncio
    async def test_sort_unknown_field_uses_default(self, client, teacher_token):
        """Unknown sort fields are ignored; default sort is applied."""
        resp = await client.get(
            "/courses?sort=-bogus_field",
            headers=auth_header(teacher_token),
        )
        assert resp.status_code == 200


# ======================================================================
# Full-text Search — ?search=term
# ======================================================================
class TestSearch:
    @pytest.mark.asyncio
    async def test_search_courses(self, client, teacher_token):
        """Search courses by keyword."""
        resp = await client.get(
            "/courses?search=math",
            headers=auth_header(teacher_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "meta" in body
        assert body["meta"].get("search_term") == "math"

    @pytest.mark.asyncio
    async def test_search_content_items(self, client, student_token):
        """Search content items by keyword."""
        resp = await client.get(
            "/content-items?search=multiplication",
            headers=auth_header(student_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["meta"].get("search_term") == "multiplication"

    @pytest.mark.asyncio
    async def test_search_activities(self, client, student_token):
        """Search activities by keyword."""
        resp = await client.get(
            "/activities?search=quiz",
            headers=auth_header(student_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["meta"].get("search_term") == "quiz"

    @pytest.mark.asyncio
    async def test_search_empty_term_ignored(self, client, teacher_token):
        """Empty search term is treated as no search."""
        resp = await client.get(
            "/courses?search=",
            headers=auth_header(teacher_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["meta"].get("search_term") is None


# ======================================================================
# Meta response fields — filters_applied, sort_by, search_term
# ======================================================================
class TestMetaFields:
    @pytest.mark.asyncio
    async def test_meta_filters_applied(self, client, teacher_token):
        """Meta includes filters_applied when filters are used."""
        resp = await client.get(
            "/courses?filter[status]=published",
            headers=auth_header(teacher_token),
        )
        assert resp.status_code == 200
        meta = resp.json()["meta"]
        assert meta.get("filters_applied") is not None
        assert len(meta["filters_applied"]) == 1
        assert meta["filters_applied"][0]["field"] == "status"
        assert meta["filters_applied"][0]["op"] == "eq"
        assert meta["filters_applied"][0]["value"] == "published"

    @pytest.mark.asyncio
    async def test_meta_sort_by(self, client, teacher_token):
        """Meta includes sort_by when sorting is specified."""
        resp = await client.get(
            "/courses?sort=-title",
            headers=auth_header(teacher_token),
        )
        assert resp.status_code == 200
        meta = resp.json()["meta"]
        assert meta.get("sort_by") == ["-title"]

    @pytest.mark.asyncio
    async def test_meta_search_term(self, client, teacher_token):
        """Meta includes search_term when search is specified."""
        resp = await client.get(
            "/courses?search=algebra",
            headers=auth_header(teacher_token),
        )
        assert resp.status_code == 200
        meta = resp.json()["meta"]
        assert meta.get("search_term") == "algebra"

    @pytest.mark.asyncio
    async def test_meta_no_extras_when_no_filters(self, client, teacher_token):
        """Meta does not include filter/sort/search fields when none are used."""
        resp = await client.get(
            "/courses",
            headers=auth_header(teacher_token),
        )
        assert resp.status_code == 200
        meta = resp.json()["meta"]
        assert meta.get("filters_applied") is None
        assert meta.get("sort_by") is None
        assert meta.get("search_term") is None


# ======================================================================
# Composition — filter + sort + search + pagination
# ======================================================================
class TestComposition:
    @pytest.mark.asyncio
    async def test_filter_and_sort_combined(self, client, admin_token):
        """Filter and sort can be used together."""
        resp = await client.get(
            "/assessments?filter[status]=draft&sort=title",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        titles = [item["title"] for item in body["data"]]
        assert titles == sorted(titles)
        for item in body["data"]:
            assert item["status"] == "draft"

    @pytest.mark.asyncio
    async def test_search_and_filter_combined(self, client, teacher_token):
        """Search and filter can be used together."""
        resp = await client.get(
            "/courses?search=math&filter[status]=published",
            headers=auth_header(teacher_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        meta = body["meta"]
        assert meta.get("search_term") == "math"
        assert meta.get("filters_applied") is not None

    @pytest.mark.asyncio
    async def test_filter_sort_search_with_pagination(self, client, teacher_token):
        """All query features compose with cursor pagination."""
        resp = await client.get(
            "/courses?filter[status]=published&sort=title&search=math&limit=1",
            headers=auth_header(teacher_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        meta = body["meta"]
        # Pagination meta is always present
        assert "has_more" in meta

    @pytest.mark.asyncio
    async def test_pagination_with_limit(self, client, admin_token):
        """Limit parameter works with filters."""
        resp = await client.get(
            "/assessments?limit=1",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) <= 1


# ======================================================================
# All list endpoints accept filter/sort/search params
# ======================================================================
class TestAllEndpointsAcceptParams:
    """Verify all 8 list endpoints accept the new query params without errors."""

    @pytest.mark.asyncio
    async def test_courses_accepts_params(self, client, teacher_token):
        resp = await client.get(
            "/courses?filter[status]=published&sort=-title&search=test",
            headers=auth_header(teacher_token),
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_assignments_accepts_params(self, client, teacher_token):
        resp = await client.get(
            "/assignments?filter[title__like]=test&sort=-due_at&search=homework",
            headers=auth_header(teacher_token),
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_content_items_accepts_params(self, client, student_token):
        resp = await client.get(
            "/content-items?filter[content_type]=video&sort=title&search=math",
            headers=auth_header(student_token),
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_activities_accepts_params(self, client, student_token):
        resp = await client.get(
            "/activities?filter[type]=quiz&sort=-title&search=addition",
            headers=auth_header(student_token),
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_assessments_accepts_params(self, client, admin_token):
        resp = await client.get(
            "/assessments?filter[status]=published&sort=title&search=exam",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_invoices_accepts_params(self, client, admin_token):
        resp = await client.get(
            "/invoices?filter[status]=pending&sort=-status&search=tuition",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_notifications_accepts_params(self, client, admin_token):
        resp = await client.get(
            "/notifications?filter[event_ref__like]=grade&sort=-created_at&search=bulletin",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_feed_accepts_params(self, client, parent_token):
        resp = await client.get(
            "/feed?filter[source_type]=grade&sort=-created_at&search=test",
            headers=auth_header(parent_token),
        )
        assert resp.status_code == 200
