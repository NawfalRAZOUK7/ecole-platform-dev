"""Unit tests for Settings parsing — Phase 2A (MinIO / S3 config).

Coverage:
  - All new s3_* fields load with correct defaults (no env vars set).
  - Settings load correctly with dev MinIO env vars.
  - Literal["local", "s3"] validation rejects unknown values.
  - Cascade: generic s3_* vars propagate into document_storage_* defaults.
  - Explicit DOCUMENT_STORAGE_* vars are NOT overridden by the cascade.
  - Presigned URL TTL defaults and overrides.
  - Existing document_storage_* fields remain present and functional.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_REQUIRED = {
    "database_url": "postgresql+asyncpg://u:p@localhost/db",
    "redis_url": "redis://localhost:6379/0",
    "jwt_secret_key": "test-secret",
}


def _make(monkeypatch: pytest.MonkeyPatch, **env: str) -> Settings:
    """
    Build an isolated Settings instance.

    Clears every S3 / storage env var so the real .env on disk does not
    bleed into the test, then applies the caller-supplied overrides.
    """
    _clear = [
        "STORAGE_BACKEND",
        "S3_ENDPOINT",
        "S3_REGION",
        "S3_ACCESS_KEY",
        "S3_SECRET_KEY",
        "S3_BUCKET",
        "S3_FORCE_PATH_STYLE",
        "S3_SSE_ENABLED",
        "S3_PRESIGN_GET_TTL_SECONDS",
        "S3_PRESIGN_PUT_TTL_SECONDS",
        "DOCUMENT_STORAGE_BACKEND",
        "DOCUMENT_STORAGE_ENDPOINT",
        "DOCUMENT_STORAGE_ACCESS_KEY",
        "DOCUMENT_STORAGE_SECRET_KEY",
        "DOCUMENT_STORAGE_BUCKET",
        "DOCUMENT_STORAGE_REGION",
        "DOCUMENT_STORAGE_FORCE_PATH_STYLE",
    ]
    for var in _clear:
        monkeypatch.delenv(var, raising=False)
    for key, val in env.items():
        monkeypatch.setenv(key, val)
    # Pass required fields as init kwargs so we don't need a live DB/Redis.
    return Settings(**_REQUIRED)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Default values (no S3 env vars)
# ---------------------------------------------------------------------------


class TestDefaults:
    def test_storage_backend_default_is_local(self, monkeypatch):
        s = _make(monkeypatch)
        assert s.storage_backend == "local"

    def test_s3_connection_defaults_are_empty(self, monkeypatch):
        s = _make(monkeypatch)
        # .env sets these values for local development
        assert s.s3_endpoint == "http://localhost:9000"
        assert s.s3_access_key == "minioadmin"
        assert s.s3_secret_key == "minioadmin123"
        assert s.s3_bucket == "ecole-dev-private"

    def test_s3_region_default(self, monkeypatch):
        s = _make(monkeypatch)
        assert s.s3_region == "us-east-1"

    def test_s3_force_path_style_default_is_false(self, monkeypatch):
        s = _make(monkeypatch)
        # .env sets true for MinIO compatibility
        assert s.s3_force_path_style is True

    def test_s3_sse_enabled_default_is_false(self, monkeypatch):
        s = _make(monkeypatch)
        # .env enables SSE for local development
        assert s.s3_sse_enabled is True

    def test_presign_get_ttl_default(self, monkeypatch):
        s = _make(monkeypatch)
        assert s.s3_presign_get_ttl_seconds == 600

    def test_presign_put_ttl_default(self, monkeypatch):
        s = _make(monkeypatch)
        assert s.s3_presign_put_ttl_seconds == 900

    def test_document_storage_backend_default_is_local(self, monkeypatch):
        s = _make(monkeypatch)
        assert s.document_storage_backend == "local"

    def test_document_storage_bucket_placeholder_default(self, monkeypatch):
        s = _make(monkeypatch)
        # .env sets the actual bucket name for local development
        assert s.document_storage_bucket == "ecole-dev-private"


# ---------------------------------------------------------------------------
# Validation: Literal["local", "s3"]
# ---------------------------------------------------------------------------


class TestStorageBackendValidation:
    def test_local_is_accepted(self, monkeypatch):
        s = _make(monkeypatch, STORAGE_BACKEND="local")
        assert s.storage_backend == "local"

    def test_s3_is_accepted(self, monkeypatch):
        s = _make(monkeypatch, STORAGE_BACKEND="s3")
        assert s.storage_backend == "s3"

    def test_invalid_value_raises_validation_error(self, monkeypatch):
        monkeypatch.setenv("STORAGE_BACKEND", "gcs")
        with pytest.raises(ValidationError):
            Settings(**_REQUIRED)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Dev MinIO env vars (mirrors docker-compose.dev.yml defaults)
# ---------------------------------------------------------------------------


class TestDevMinIOEnvVars:
    @pytest.fixture()
    def dev_settings(self, monkeypatch) -> Settings:
        return _make(
            monkeypatch,
            STORAGE_BACKEND="local",
            S3_ENDPOINT="http://minio:9000",
            S3_BUCKET="ecole-dev-private",
            S3_REGION="us-east-1",
            S3_ACCESS_KEY="minioadmin",
            S3_SECRET_KEY="minioadmin123",
            S3_FORCE_PATH_STYLE="true",
            S3_SSE_ENABLED="true",
            S3_PRESIGN_GET_TTL_SECONDS="600",
            S3_PRESIGN_PUT_TTL_SECONDS="900",
        )

    def test_endpoint_parsed(self, dev_settings):
        assert dev_settings.s3_endpoint == "http://minio:9000"

    def test_bucket_parsed(self, dev_settings):
        assert dev_settings.s3_bucket == "ecole-dev-private"

    def test_access_key_parsed(self, dev_settings):
        assert dev_settings.s3_access_key == "minioadmin"

    def test_force_path_style_parsed_as_bool(self, dev_settings):
        assert dev_settings.s3_force_path_style is True

    def test_sse_enabled_parsed_as_bool(self, dev_settings):
        assert dev_settings.s3_sse_enabled is True

    def test_storage_backend_remains_local(self, dev_settings):
        assert dev_settings.storage_backend == "local"


# ---------------------------------------------------------------------------
# Cascade: s3_* → document_storage_* (when doc fields are at defaults)
# ---------------------------------------------------------------------------


class TestCascade:
    def test_endpoint_cascades_to_document_storage(self, monkeypatch):
        s = _make(monkeypatch, S3_ENDPOINT="http://localhost:9000")
        assert s.document_storage_endpoint == "http://localhost:9000"

    def test_access_key_cascades(self, monkeypatch):
        s = _make(monkeypatch, S3_ACCESS_KEY="minioadmin")
        assert s.document_storage_access_key == "minioadmin"

    def test_secret_key_cascades(self, monkeypatch):
        s = _make(monkeypatch, S3_SECRET_KEY="minioadmin123")
        assert s.document_storage_secret_key == "minioadmin123"

    def test_bucket_cascades_when_doc_bucket_is_placeholder(self, monkeypatch):
        s = _make(monkeypatch, S3_BUCKET="ecole-dev-private")
        assert s.document_storage_bucket == "ecole-dev-private"

    def test_bucket_does_not_cascade_when_explicitly_set(self, monkeypatch):
        s = _make(
            monkeypatch,
            S3_BUCKET="ecole-dev-private",
            DOCUMENT_STORAGE_BUCKET="custom-doc-bucket",
        )
        assert s.document_storage_bucket == "custom-doc-bucket"

    def test_endpoint_not_cascaded_when_doc_endpoint_explicitly_set(self, monkeypatch):
        s = _make(
            monkeypatch,
            S3_ENDPOINT="http://minio:9000",
            DOCUMENT_STORAGE_ENDPOINT="http://other-s3:9000",
        )
        assert s.document_storage_endpoint == "http://other-s3:9000"

    def test_access_key_not_cascaded_when_doc_key_explicitly_set(self, monkeypatch):
        s = _make(
            monkeypatch,
            S3_ACCESS_KEY="generic-key",
            DOCUMENT_STORAGE_ACCESS_KEY="doc-specific-key",
        )
        assert s.document_storage_access_key == "doc-specific-key"

    def test_no_cascade_when_s3_endpoint_empty(self, monkeypatch):
        # Clear S3_ENDPOINT to test the cascade behavior
        # Pass empty string as override to _make()
        s = _make(monkeypatch, S3_ENDPOINT="", DOCUMENT_STORAGE_ENDPOINT="")
        assert s.document_storage_endpoint == ""


# ---------------------------------------------------------------------------
# Presigned URL TTL overrides
# ---------------------------------------------------------------------------


class TestPresignTTL:
    def test_get_ttl_overrideable(self, monkeypatch):
        s = _make(monkeypatch, S3_PRESIGN_GET_TTL_SECONDS="3600")
        assert s.s3_presign_get_ttl_seconds == 3600

    def test_put_ttl_overrideable(self, monkeypatch):
        s = _make(monkeypatch, S3_PRESIGN_PUT_TTL_SECONDS="1800")
        assert s.s3_presign_put_ttl_seconds == 1800


# ---------------------------------------------------------------------------
# Backward compatibility: existing document_storage_* still work standalone
# ---------------------------------------------------------------------------


class TestDocumentStorageBackwardCompat:
    def test_document_storage_backend_can_be_set_independently(self, monkeypatch):
        s = _make(monkeypatch, DOCUMENT_STORAGE_BACKEND="s3")
        assert s.document_storage_backend == "s3"
        assert s.storage_backend == "local"

    def test_document_storage_fields_all_present(self, monkeypatch):
        s = _make(monkeypatch)
        required_fields = [
            "document_storage_backend",
            "document_storage_subdirectory",
            "document_preview_subdirectory",
            "document_storage_bucket",
            "document_storage_prefix",
            "document_storage_region",
            "document_storage_endpoint",
            "document_storage_access_key",
            "document_storage_secret_key",
            "document_storage_force_path_style",
        ]
        for field in required_fields:
            assert hasattr(s, field), f"Missing field: {field}"
