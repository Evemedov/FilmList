"""
Pydantic schemas for AppSettings entity.
"""

from pydantic import BaseModel, ConfigDict, Field


class AppSettingsRead(BaseModel):
    """Response schema for application settings."""

    model_config = ConfigDict(from_attributes=True)

    tmdb_api_key: str | None = None
    theme: str


class AppSettingsUpdate(BaseModel):
    """Body for updating application settings (partial update)."""

    tmdb_api_key: str | None = Field(default=None, max_length=256)
    theme: str | None = Field(default=None, pattern=r"^(DARK|LIGHT)$")
