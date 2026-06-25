"""
Application settings loaded from environment variables / .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration – values are read from env vars or a .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Database ────────────────────────────────────────────────────────
    DATABASE_URL: str  # e.g. postgresql+asyncpg://user:pass@localhost:5432/filmlist

    # ── Redis ───────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── TMDB ────────────────────────────────────────────────────────────
    TMDB_API_KEY: str | None = None

    # ── General ─────────────────────────────────────────────────────────
    DEBUG: bool = False

    # ── File Uploads ────────────────────────────────────────────────────
    UPLOAD_DIR: str = "/tmp/filmlist_uploads"


# Singleton – import this instance throughout the app
settings = Settings()  # type: ignore[call-arg]
