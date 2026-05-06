"""Contract tests use the isolated legacy API client and seed data."""

from tests.integration.api.conftest import (  # noqa: F401
    client,
    isolated_legacy_api_db,
    legacy_api_seed,
    session_factory,
)
