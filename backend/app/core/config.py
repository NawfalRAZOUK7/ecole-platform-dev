"""Application configuration loaded from environment variables.

Reference: Pack D3 — Runtime Configuration
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # Application
    app_env: str = "development"
    app_port: int = 8000
    log_level: str = "DEBUG"

    # Database (PostgreSQL)
    database_url: str = "postgresql+asyncpg://ecole:ecole@localhost:5432/ecole_platform"

    # Cache (Redis)
    redis_url: str = "redis://localhost:6379/0"

    # Authentication (JWT)
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

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

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
