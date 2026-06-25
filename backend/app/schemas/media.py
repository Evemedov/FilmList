"""
Pydantic schemas for Media, Season, and Episode entities.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.media import ContentType, WatchStatus
from app.schemas.genre import GenreRead
from app.schemas.screenshot import ScreenshotRead
from app.schemas.tag import TagRead


# ── Episode ─────────────────────────────────────────────────────────────


class EpisodeRead(BaseModel):
    """Response schema for an episode."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    episode_number: int
    title: str | None = None
    is_watched: bool
    runtime_minutes: int | None = None


class EpisodeUpdate(BaseModel):
    """Body for updating an episode (primarily is_watched toggle)."""

    is_watched: bool


# ── Season ──────────────────────────────────────────────────────────────


class SeasonRead(BaseModel):
    """Response schema for a season with nested episodes."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    season_number: int
    title: str | None = None
    episodes: list[EpisodeRead] = []


# ── Media ───────────────────────────────────────────────────────────────


class MediaCreate(BaseModel):
    """Body for creating a new media entry."""

    content_type: ContentType
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None

    # Personal meta
    my_rating: int | None = Field(default=None, ge=1, le=10)
    my_comments: str | None = None
    watch_status: WatchStatus = WatchStatus.PLAN_TO_WATCH
    is_rewatch: bool = False

    # Cover images
    cover_image_url: str | None = Field(default=None, max_length=2048)
    local_cover_url: str | None = Field(default=None, max_length=2048)

    # Links
    web_url: str | None = Field(default=None, max_length=2048)
    local_network_url: str | None = Field(default=None, max_length=2048)

    # Audio & subtitles (local, user-managed)
    local_audio_languages: list[str] | None = None
    local_subtitle_languages: list[str] | None = None

    # TMDB ID for auto-fetch
    tmdb_id: int | None = None

    # Tags (by existing tag IDs)
    tag_ids: list[uuid.UUID] = []


class MediaUpdate(BaseModel):
    """Body for updating a media entry (partial update – all fields optional)."""

    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    content_type: ContentType | None = None

    # Personal meta
    my_rating: int | None = Field(default=None, ge=1, le=10)
    my_comments: str | None = None
    watch_status: WatchStatus | None = None
    is_rewatch: bool | None = None

    # Cover images
    cover_image_url: str | None = Field(default=None, max_length=2048)
    local_cover_url: str | None = Field(default=None, max_length=2048)

    # Links
    web_url: str | None = Field(default=None, max_length=2048)
    local_network_url: str | None = Field(default=None, max_length=2048)

    # Audio & subtitles (local, user-managed)
    local_audio_languages: list[str] | None = None
    local_subtitle_languages: list[str] | None = None

    # Tags (replace all tags with these IDs)
    tag_ids: list[uuid.UUID] | None = None


class MediaReadBrief(BaseModel):
    """Lightweight response for list/dashboard views (no nested seasons)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    content_type: ContentType
    title: str
    description: str | None = None
    my_rating: int | None = None
    watch_status: WatchStatus
    is_rewatch: bool
    cover_image_url: str | None = None
    local_cover_url: str | None = None
    global_rating: float | None = None
    release_year: int | None = None
    runtime_minutes: int | None = None
    created_at: datetime
    updated_at: datetime | None = None

    # Relationships (loaded explicitly per endpoint)
    tags: list[TagRead] = []
    genres: list[GenreRead] = []


class MediaRead(MediaReadBrief):
    """Full response for detail view (includes seasons, screenshots, links, audio)."""

    # Links
    web_url: str | None = None
    local_network_url: str | None = None

    # Comments
    my_comments: str | None = None

    # Audio & subtitles
    api_audio_languages: list[str] | None = None
    api_subtitle_languages: list[str] | None = None
    local_audio_languages: list[str] | None = None
    local_subtitle_languages: list[str] | None = None

    # TMDB
    tmdb_id: int | None = None

    # Nested relationships
    seasons: list[SeasonRead] = []
    screenshots: list[ScreenshotRead] = []
