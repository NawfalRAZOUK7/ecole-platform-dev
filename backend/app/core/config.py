"""Application configuration loaded from environment variables.

Reference: Pack D3 — Runtime Configuration
"""

import os
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings


BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent
DEFAULT_ENV_FILES = (
    str(PROJECT_ROOT / ".env"),
    str(BACKEND_ROOT / ".env"),
    ".env",
)


def _read_secret_file(env_name: str) -> str | None:
    """Load an optional Docker secret from ENV_NAME_FILE if present."""
    file_path = os.getenv(f"{env_name}_FILE")
    if not file_path:
        return None

    path = Path(file_path)
    if not path.exists():
        return None

    return path.read_text(encoding="utf-8").strip()


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # Application
    app_env: str = "development"
    app_port: int = 8000
    log_level: str = "DEBUG"
    api_base_url: str = "http://localhost:8000/api/v1"

    # Database (PostgreSQL)
    database_url: str = (
        "postgresql+asyncpg://ecole:change-me@localhost:5432/ecole_platform"
    )
    database_replica_url: str | None = None

    # Cache (Redis)
    redis_url: str = "redis://:change-me-dev-redis@localhost:6379/0"

    # Authentication (JWT)
    jwt_secret_key: str = "change-me-in-production-use-a-strong-random-secret"
    jwt_previous_key: str = ""  # Previous key, used during rotation window
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 2
    max_sessions_per_user: int = 5

    # Rate limiting (Phase 2A)
    enable_strict_rate_limit: bool = False  # True in production/staging

    # File uploads (Phase 3B)
    upload_dir: str = "uploads"
    max_file_size_mb: int = 25
    allowed_mime_types: str = (
        "application/pdf,"
        "application/msword,"
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document,"
        "application/vnd.ms-excel,"
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,"
        "application/vnd.ms-powerpoint,"
        "application/vnd.openxmlformats-officedocument.presentationml.presentation,"
        "image/jpeg,"
        "image/png,"
        "image/gif,"
        "image/webp,"
        "video/mp4,"
        "audio/mpeg,"
        "text/plain,"
        "application/zip"
    )

    # -------------------------------------------------------------------------
    # Core storage backend (Phase 2 — MinIO integration)
    # -------------------------------------------------------------------------
    # Values: "local" (default, filesystem) | "s3" (MinIO / AWS S3)
    # Switch to "s3" only after Phase 2 implementation is complete.
    storage_backend: Literal["local", "s3"] = "local"

    # S3 / MinIO connection settings — used when storage_backend = "s3".
    # Also cascade into document_storage_* defaults when those fields
    # are still at their empty/placeholder values (see model_post_init).
    s3_endpoint: str = ""  # http://minio:9000 (dev) | https://... (prod)
    s3_region: str = "us-east-1"
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_bucket: str = ""  # ecole-dev-private / ecole-staging-private / etc.
    s3_force_path_style: bool = False  # True required for MinIO; False for AWS S3
    s3_sse_enabled: bool = False  # Enable AES256 server-side encryption on put

    # Presigned URL TTLs (seconds)
    s3_presign_get_ttl_seconds: int = 600  # 10 min — read / download links
    s3_presign_put_ttl_seconds: int = (
        900  # 15 min — direct client upload links (Phase 8)
    )

    # Phase 8 — per-kind upload size limits (MB)
    max_video_size_mb: int = 2048  # 2 GB
    max_audio_size_mb: int = 200
    max_submission_file_size_mb: int = 100
    max_content_asset_size_mb: int = 200

    # Document management (Phase 16)
    document_storage_backend: str = "local"  # local | s3
    document_storage_subdirectory: str = "documents"
    document_preview_subdirectory: str = "documents/previews"
    document_storage_bucket: str = "ecole-platform"
    document_storage_prefix: str = "documents"
    document_storage_region: str = "us-east-1"
    document_storage_endpoint: str = ""
    document_storage_access_key: str = ""
    document_storage_secret_key: str = ""
    document_storage_force_path_style: bool = True
    max_document_size_mb: int = 50
    allowed_document_mime_types: str = (
        "application/pdf,"
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document,"
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,"
        "application/vnd.openxmlformats-officedocument.presentationml.presentation,"
        "image/jpeg,"
        "image/png,"
        "image/webp,"
        "application/zip"
    )
    document_download_ttl_hours: int = 1
    document_deleted_retention_days: int = 30
    document_expiry_notice_days: int = 30
    virus_scan_enabled: bool = False
    virus_scan_host: str = "localhost"
    virus_scan_port: int = 3310

    # SMTP / Email (Phase 3E)
    smtp_host: str = "localhost"
    smtp_port: int = 1025  # Mailhog default for dev
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = False
    smtp_from_email: str = "noreply@ecole-platform.ma"
    smtp_from_name: str = "École Platform"
    smtp_timeout_seconds: int = 20

    # TestMail API (for email testing)
    testmail_enabled: bool = False
    testmail_api_key: str = ""
    testmail_namespace: str = ""

    # Notifications (Phase 13)
    notifications_digest_timezone: str = "Africa/Casablanca"
    notifications_digest_send_hour: int = 7
    notifications_unsubscribe_ttl_hours: int = 24 * 30
    firebase_service_account_path: str = ""
    firebase_project_id: str = ""
    push_retry_max_attempts: int = 3
    push_retry_base_delay_seconds: int = 1
    web_app_base_url: str = "http://localhost:5173"
    report_storage_subdirectory: str = "reports"
    report_download_ttl_hours: int = 24
    report_cache_ttl_hours: int = 1
    ai_provider: str = "mock"
    ai_api_key: str = ""
    ai_model: str = ""
    analytics_cache_ttl_seconds: int = 300
    attendance_warning_threshold: float = 0.15
    attendance_critical_threshold: float = 0.25
    calendar_ical_ttl_days: int = 30
    calendar_reminder_horizon_days: int = 90
    calendar_reminder_default_offsets: str = "1440,60"
    enable_tracing: bool = False
    otel_exporter_endpoint: str = "http://tempo:4317"

    # Sentry error tracking & performance monitoring
    sentry_dsn: str = ""
    sentry_traces_sample_rate: float = 1.0
    sentry_profiles_sample_rate: float = 1.0

    # WebAuthn / Passkeys (Phase 10)
    webauthn_enabled: bool = False
    webauthn_rp_id: str = "localhost"
    webauthn_rp_name: str = "École Platform"
    webauthn_origin: str = "http://localhost:8000"

    # OAuth / Social Login (Phase 10)
    google_oauth_enabled: bool = True  # Enabled for dev testing with mock server
    google_oauth_client_id: str = "mock-client-id"
    google_oauth_client_secret: str = "mock-client-secret"

    microsoft_oauth_enabled: bool = True  # Enabled for dev testing with mock server
    microsoft_oauth_client_id: str = "mock-client-id"
    microsoft_oauth_client_secret: str = "mock-client-secret"

    apple_oauth_enabled: bool = False
    apple_oauth_client_id: str = ""
    apple_oauth_client_secret: str = ""

    # SMS / Phone Verification (Phase 10)
    sms_enabled: bool = True  # Enabled for dev testing with mock SMS
    sms_provider: str = "twilio"  # twilio, etc.
    twilio_account_sid: str = "mock-account-sid"
    twilio_auth_token: str = "mock-auth-token"
    twilio_from_number: str = "+1234567890"
    mock_sms_enabled: bool = True  # Reveal OTP in logs instead of sending real SMS
    debug_reveal_otp: bool = False  # Reveal OTPs in non-production test responses

    # Mock OAuth / Social Login (Phase 10 — Testing)
    mock_oauth_enabled: bool = True  # Use mock OAuth server instead of real providers
    mock_oauth_base_url: str = "http://mock-oauth:9999"  # Mock OAuth server URL

    # Password Reuse Policy (Phase 11)
    password_history_limit: int = 5  # Number of passwords to remember

    # Account Lockout (Phase 11)
    account_lockout_enabled: bool = False
    account_lockout_max_attempts: int = 5  # Lockout after this many attempts
    account_lockout_duration_minutes: int = 15  # Lockout duration
    account_lockout_progressive_enabled: bool = False  # Enable progressive lockout (5=15min, 10=1hour)

    # Suspicious Activity Detection (Phase 11)
    suspicious_activity_enabled: bool = False
    suspicious_activity_alert_on_new_location: bool = True
    suspicious_activity_alert_on_new_device: bool = True
    geoip_database_path: str = "/app/data/GeoLite2-City.mmdb"

    # Staging / seeding
    seed_on_startup: bool = False

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_staging(self) -> bool:
        return self.app_env == "staging"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    def model_post_init(self, __context: object) -> None:
        secret_overrides = {
            "database_url": _read_secret_file("DATABASE_URL"),
            "database_replica_url": _read_secret_file("DATABASE_REPLICA_URL"),
            "redis_url": _read_secret_file("REDIS_URL"),
            "jwt_secret_key": _read_secret_file("JWT_SECRET_KEY"),
            "jwt_previous_key": _read_secret_file("JWT_PREVIOUS_KEY"),
            "smtp_password": _read_secret_file("SMTP_PASSWORD"),
        }
        for field_name, value in secret_overrides.items():
            if value:
                object.__setattr__(self, field_name, value)

        # ----------------------------------------------------------------
        # Backward-compatibility cascade: generic s3_* → document_storage_*
        #
        # Rationale: document_storage_* (Phase 16) and the new s3_* settings
        # (Phase 2) both describe the same MinIO/S3 service in most deployments.
        # To avoid forcing operators to duplicate credentials, we cascade the
        # generic s3_* values into the document_storage_* slots when those
        # slots are still at their empty / placeholder defaults.
        #
        # Explicit DOCUMENT_STORAGE_* env vars always take precedence.
        # ----------------------------------------------------------------
        _cascade: list[tuple[str, str, str]] = [
            # (s3_field, doc_field, sentinel_meaning_not_explicitly_set)
            ("s3_endpoint", "document_storage_endpoint", ""),
            ("s3_access_key", "document_storage_access_key", ""),
            ("s3_secret_key", "document_storage_secret_key", ""),
        ]
        for s3_field, doc_field, sentinel in _cascade:
            s3_val = getattr(self, s3_field)
            doc_val = getattr(self, doc_field)
            if s3_val and doc_val == sentinel:
                object.__setattr__(self, doc_field, s3_val)

        # Bucket: cascade only when the doc bucket is still the placeholder default.
        _DOC_BUCKET_DEFAULT = "ecole-platform"
        if self.s3_bucket and self.document_storage_bucket == _DOC_BUCKET_DEFAULT:
            object.__setattr__(self, "document_storage_bucket", self.s3_bucket)

    model_config = {
        "env_file": DEFAULT_ENV_FILES,
        "env_file_encoding": "utf-8",
        # Local dev/test .env files include compatibility keys that this
        # settings model does not currently expose.
        "extra": "ignore",
    }


settings = Settings()
