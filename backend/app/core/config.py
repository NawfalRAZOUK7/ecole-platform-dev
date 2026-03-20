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
    upload_dir: str = "/app/uploads"
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

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
