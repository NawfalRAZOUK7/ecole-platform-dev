"""Tests for the readiness probe endpoint."""

from __future__ import annotations

import httpx
import pytest

pytestmark = pytest.mark.asyncio


async def test_readiness_returns_200_when_healthy(client: httpx.AsyncClient):
    """Readiness probe returns 200 with database and Redis checks."""
    response = await client.get("/readiness")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["checks"]["database"] == "ok"
    assert body["checks"]["redis"] == "ok"
    assert "timestamp" in body
