"""Application configuration loaded from environment variables.

Reference: Pack D3 — Runtime Configuration
"""

import os
from pathlib import Path

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

    model_config = {
        "env_file": DEFAULT_ENV_FILES,
        "env_file_encoding": "utf-8",
        # Local dev/test .env files include compatibility keys that this
        # settings model does not currently expose.
        "extra": "ignore",
    }


settings = Settings()
