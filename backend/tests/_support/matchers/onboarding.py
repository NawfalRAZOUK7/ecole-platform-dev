"""Onboarding/activation-specific matchers."""

from __future__ import annotations


def assert_activation_url(
    url: str, *, token: str | None = None, base: str | None = None
) -> str:
    """Assert an activation URL has the expected shape and return its token.

    Shape: ``<base>/activate?token=<token>``.
    """
    assert (
        isinstance(url, str) and url
    ), f"activation_url is empty/not a string: {url!r}"
    assert (
        "/activate?token=" in url
    ), f"activation_url missing /activate?token=: {url!r}"
    if base is not None:
        assert url.startswith(
            base
        ), f"activation_url does not start with {base!r}: {url!r}"
    extracted = url.split("/activate?token=", 1)[1]
    assert extracted, f"activation_url has empty token: {url!r}"
    if token is not None:
        assert (
            extracted == token
        ), f"activation_url token {extracted!r} != expected {token!r}"
    return extracted
