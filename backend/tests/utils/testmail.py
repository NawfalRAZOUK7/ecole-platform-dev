"""Testmail client for E2E email testing.

Reference: STUDENT_PACK_ROADMAP.md — Testmail integration.

Usage:
    from tests.utils.testmail import fresh_email, wait_email

    to = fresh_email("invite-test")
    # trigger API that sends email to `to`
    email = wait_email("invite-test")
    assert "invitation" in email["subject"].lower()
"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx

NAMESPACE = os.getenv("TESTMAIL_NAMESPACE", "ibatt")
API_KEY = os.getenv("TESTMAIL_API_KEY", "")
BASE_URL = "https://api.testmail.app/api/json"


def fresh_email(tag: str) -> str:
    """Generate a fresh Testmail address with the given tag.

    Args:
        tag: Unique tag for this test (e.g. "invite-test-42").
    """
    return f"{NAMESPACE}.{tag}@inbox.testmail.app"


def wait_email(
    tag: str,
    timeout: int = 30,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Poll Testmail API until an email with the given tag arrives.

    Args:
        tag: Tag portion of the email address.
        timeout: Max seconds to wait.
        api_key: Override API key (defaults to TESTMAIL_API_KEY env var).

    Returns:
        The first email object from Testmail.

    Raises:
        TimeoutError: If no email arrives within timeout.
        RuntimeError: If TESTMAIL_API_KEY is not configured.
    """
    key = api_key or API_KEY
    if not key:
        raise RuntimeError(
            "TESTMAIL_API_KEY is not set. " "Add it to your .env or Doppler secrets."
        )

    url = f"{BASE_URL}?" f"apikey={key}&" f"namespace={NAMESPACE}&" f"tag={tag}"

    for _ in range(timeout):
        resp = httpx.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("count", 0) > 0:
            return data["emails"][0]
        time.sleep(1)

    raise TimeoutError(f"No email received for tag {tag!r} within {timeout}s")


def clear_inbox(tag: str | None = None, api_key: str | None = None) -> None:
    """Delete emails from the Testmail inbox.

    Args:
        tag: Optional tag to filter by. If None, clears all.
        api_key: Override API key.
    """
    key = api_key or API_KEY
    if not key:
        return

    url = f"{BASE_URL}?apikey={key}&namespace={NAMESPACE}"
    if tag:
        url += f"&tag={tag}"
    url += "&delete=true"

    resp = httpx.get(url, timeout=10)
    resp.raise_for_status()
