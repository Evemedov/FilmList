"""
Core models: Media, Season, Episode and related enums.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from typing import TYPE_CHECKING
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.metadata import Genre, Screenshot
    from app.models.tag import Tag


# ── Enums ───────────────────────────────────────────────────────────────


class ContentType(str, enum.Enum):
    """Type of media content."""
    MOVIE = "MOVIE"
    TV_SHOW = "TV_SHOW"
    CARTOON = "CARTOON"
    ANIME = "ANIME"


class WatchStatus(str, enum.Enum):
    """Personal watch-status for a media entry."""
    PLAN_TO_WATCH = "PLAN_TO_WATCH"
    WATCHING = "WATCHING"
    COMPLETED = "COMPLETED"
    FAVORITE = "FAVORITE"
    DROPPED = "DROPPED"


# ── Media ───────────────────────────────────────────────────────────────


class Media(Base):
    __tablename__ = "media"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Classification ──────────────────────────────────────────────────
    content_type: Mapped[ContentType] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Personal meta ───────────────────────────────────────────────────
    my_rating: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    my_comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    watch_status: Mapped[WatchStatus] = mapped_column(
        nullable=False, default=WatchStatus.PLAN_TO_WATCH
    )
    is_rewatch: Mapped[bool] = mapped_column(Boolean, default=False)

    # ── Cover images ────────────────────────────────────────────────────
    cover_image_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    local_cover_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # ── Links ───────────────────────────────────────────────────────────
    web_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    local_network_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # ── Audio & Subtitles ───────────────────────────────────────────────
    api_audio_languages: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )
    api_subtitle_languages: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )
    local_audio_languages: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )
    local_subtitle_languages: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )

    # ── API-fetched metadata ────────────────────────────────────────────
    global_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    release_year: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    runtime_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tmdb_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, unique=True
    )

    # ── Timestamps ──────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # ── Relationships ───────────────────────────────────────────────────
    seasons: Mapped[list["Season"]] = relationship(
        back_populates="media",
        cascade="all, delete-orphan",
        order_by="Season.season_number",
        lazy="raise",
    )
    tags: Mapped[list["Tag"]] = relationship(  # noqa: F821
        secondary="media_tags",
        back_populates="media_items",
        lazy="raise",
    )
    genres: Mapped[list["Genre"]] = relationship(  # noqa: F821
        secondary="media_genres",
        back_populates="media_items",
        lazy="raise",
    )
    screenshots: Mapped[list["Screenshot"]] = relationship(  # noqa: F821
        back_populates="media",
        cascade="all, delete-orphan",
        order_by="Screenshot.sort_order",
        lazy="raise",
    )

    # ── Table-level constraints ─────────────────────────────────────────
    __table_args__ = (
        CheckConstraint(
            "my_rating IS NULL OR (my_rating >= 1 AND my_rating <= 10)",
            name="ck_media_rating_range",
        ),
    )

    def __repr__(self) -> str:
        return f"<Media {self.title!r} ({self.content_type.value})>"


# ── Season ──────────────────────────────────────────────────────────────


class Season(Base):
    __tablename__ = "seasons"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    media_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("media.id", ondelete="CASCADE"), nullable=False
    )
    season_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # ── Relationships ───────────────────────────────────────────────────
    media: Mapped["Media"] = relationship(back_populates="seasons")
    episodes: Mapped[list["Episode"]] = relationship(
        back_populates="season",
        cascade="all, delete-orphan",
        order_by="Episode.episode_number",
        lazy="raise",
    )

    __table_args__ = (
        UniqueConstraint("media_id", "season_number", name="uq_season_media_number"),
    )

    def __repr__(self) -> str:
        return f"<Season {self.season_number} of media={self.media_id}>"


# ── Episode ─────────────────────────────────────────────────────────────


class Episode(Base):
    __tablename__ = "episodes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    season_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False
    )
    episode_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_watched: Mapped[bool] = mapped_column(Boolean, default=False)
    runtime_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ── Relationships ───────────────────────────────────────────────────
    season: Mapped["Season"] = relationship(back_populates="episodes")

    __table_args__ = (
        UniqueConstraint(
            "season_id", "episode_number", name="uq_episode_season_number"
        ),
    )

    def __repr__(self) -> str:
        return f"<Episode {self.episode_number} of season={self.season_id}>"
