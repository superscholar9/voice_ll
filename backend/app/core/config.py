"""Application configuration management."""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Voice Cloning API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    API_KEY: str = Field(..., description="API key for authentication")

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins"
    )

    # GPT-SoVITS Configuration
    SOVITS_BASE_URL: str = Field(
        default="http://localhost:9880",
        description="GPT-SoVITS service base URL"
    )
    SOVITS_TIMEOUT: int = Field(
        default=300,
        description="Request timeout in seconds"
    )

    # Queue / Background Jobs
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL used for Celery broker and backend",
    )
    COVER_QUEUE_NAME: str = Field(
        default="cover",
        description="Celery queue name for cover generation jobs",
    )
    CELERY_TASK_ALWAYS_EAGER: bool = Field(
        default=False,
        description="Run Celery tasks locally in request process (testing only)",
    )

    # Cover pipeline storage & limits
    COVER_ASSET_ROOT: str = Field(
        default="./cover_assets",
        description="Base directory for cover job files",
    )
    COVER_ALLOWED_FORMATS: List[str] = Field(
        default=["wav", "mp3", "flac", "ogg", "m4a", "aac"],
        description="Allowed audio extensions for cover endpoints",
    )
    COVER_MAX_DURATION_SECONDS: int = Field(
        default=8 * 60,
        description="Maximum song duration allowed for one cover job",
    )
    COVER_RESULT_TTL_HOURS: int = Field(
        default=24,
        description="Recommended retention for generated cover results",
    )

    # GPT-SoVITS command integration
    GPT_SOVITS_PYTHON: str = Field(
        default="python",
        description="Python executable used for GPT-SoVITS runtime commands",
    )
    GPT_SOVITS_PROJECT_ROOT: str = Field(
        default="",
        description="Path to GPT-SoVITS project root on the server",
    )
    COVER_UVR_MODEL: str = Field(
        default="HP2_all_vocals",
        description="Default UVR model name for vocal separation",
    )
    COVER_SEPARATE_CMD_TEMPLATE: str = Field(
        default="",
        description=(
            "Command template for separation. Available placeholders: "
            "{python_exec}, {project_root}, {song_input}, {vocal_output}, {inst_output}, {uvr_model}"
        ),
    )
    COVER_INFER_CMD_TEMPLATE: str = Field(
        default="",
        description=(
            "Command template for conversion/inference. Available placeholders: "
            "{python_exec}, {project_root}, {reference_voice}, {input_vocal}, "
            "{output_vocal}, {model_id}, {pitch_shift}"
        ),
    )

    # File Upload
    MAX_UPLOAD_SIZE: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="Maximum upload file size in bytes"
    )
    ALLOWED_AUDIO_FORMATS: List[str] = Field(
        default=["wav", "mp3", "flac", "ogg"],
        description="Allowed audio file formats"
    )

    # Logging
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level"
    )

    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./voice_clone.db",
        description="Database connection URL"
    )

    # JWT Authentication
    JWT_SECRET_KEY: str = Field(..., description="Secret key for JWT access tokens")
    JWT_REFRESH_SECRET_KEY: str = Field(..., description="Secret key for JWT refresh tokens")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Access token expiry in minutes")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiry in days")

    # Cloudflare Turnstile
    TURNSTILE_SECRET_KEY: str = Field(..., description="Cloudflare Turnstile secret key")

    # Email Configuration
    SMTP_HOST: str = Field(default="smtp.gmail.com", description="SMTP server host")
    SMTP_PORT: int = Field(default=587, description="SMTP server port")
    SMTP_USER: str = Field(..., description="SMTP username")
    SMTP_PASSWORD: str = Field(..., description="SMTP password")
    VERIFICATION_TOKEN_EXPIRE_MINUTES: int = Field(default=60, description="Email verification token expiry")
    VERIFICATION_EMAIL_FROM: str = Field(default="noreply@voiceclone.ai", description="Sender email address")
    FRONTEND_URL: str = Field(default="http://localhost:3000", description="Frontend URL for email links")

    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()
