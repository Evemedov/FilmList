"""
CRUD operations for Media, Season, and Episode entities.

All queries use explicit relationship loading (selectinload / joinedload)
because models are configured with lazy="raise".
"""

import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.media import Episode, Media, Season
from app.models.metadata import Genre, Screenshot
from app.models.tag import Tag
from app.crud.tag import get_tags_by_ids


# ── Loading helpers ─────────────────────────────────────────────────────

def _brief_load_options():
    """Load options for list/dashboard views – tags + genres only."""
    return [
        selectinload(Media.tags),
        selectinload(Media.genres),
    ]


def _full_load_options():
    """Load options for detail views – everything including seasons→episodes."""
    return [
        selectinload(Media.tags),
        selectinload(Media.genres),
        selectinload(Media.screenshots),
        selectinload(Media.seasons).selectinload(Season.episodes),
    ]


# ── List / Get ──────────────────────────────────────────────────────────


async def get_media_list(session: AsyncSession) -> Sequence[Media]:
    """Return all media entries with brief-load relationships."""
    stmt = (
        select(Media)
        .options(*_brief_load_options())
        .order_by(Media.created_at.desc())
    )
    result = await session.execute(stmt)
    return result.scalars().unique().all()


async def get_media(session: AsyncSession, media_id: uuid.UUID) -> Media | None:
    """Return a single media entry with full-load relationships."""
    stmt = (
        select(Media)
        .options(*_full_load_options())
        .where(Media.id == media_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


# ── Create ──────────────────────────────────────────────────────────────


async def create_media(
    session: AsyncSession,
    *,
    content_type: str,
    title: str,
    description: str | None = None,
    my_rating: int | None = None,
    my_comments: str | None = None,
    watch_status: str = "PLAN_TO_WATCH",
    is_rewatch: bool = False,
    cover_image_url: str | None = None,
    local_cover_url: str | None = None,
    web_url: str | None = None,
    local_network_url: str | None = None,
    local_audio_languages: list[str] | None = None,
    local_subtitle_languages: list[str] | None = None,
    tmdb_id: int | None = None,
    tag_ids: list[uuid.UUID] | None = None,
) -> Media:
    """Create a new media entry, optionally linking tags."""
    media = Media(
        content_type=content_type,
        title=title,
        description=description,
        my_rating=my_rating,
        my_comments=my_comments,
        watch_status=watch_status,
        is_rewatch=is_rewatch,
        cover_image_url=cover_image_url,
        local_cover_url=local_cover_url,
        web_url=web_url,
        local_network_url=local_network_url,
        local_audio_languages=local_audio_languages,
        local_subtitle_languages=local_subtitle_languages,
        tmdb_id=tmdb_id,
    )
    session.add(media)
    await session.flush()

    # Link tags
    if tag_ids:
        tags = await get_tags_by_ids(session, tag_ids)
        media.tags = tags
        await session.flush()

    # Re-load with full options to return a complete object
    return await get_media(session, media.id)  # type: ignore[return-value]


# ── Update ──────────────────────────────────────────────────────────────


async def update_media(
    session: AsyncSession,
    media_id: uuid.UUID,
    **fields,
) -> Media | None:
    """Partially update a media entry. Returns None if not found."""
    media = await get_media(session, media_id)
    if media is None:
        return None

    # Handle tag_ids separately
    tag_ids = fields.pop("tag_ids", None)
    if tag_ids is not None:
        tags = await get_tags_by_ids(session, tag_ids)
        media.tags = tags

    # Apply scalar field updates
    for key, value in fields.items():
        if hasattr(media, key) and value is not None:
            setattr(media, key, value)

    await session.flush()
    return await get_media(session, media.id)  # type: ignore[return-value]


# ── Delete ──────────────────────────────────────────────────────────────


async def delete_media(session: AsyncSession, media_id: uuid.UUID) -> bool:
    """Delete a media entry by ID. Returns True if deleted, False if not found."""
    media = await session.get(Media, media_id)
    if media is None:
        return False
    await session.delete(media)
    await session.flush()
    return True


# ── Episode watch toggle (with cascading) ───────────────────────────────


async def set_episode_watched(
    session: AsyncSession,
    episode_id: uuid.UUID,
    *,
    is_watched: bool,
) -> Episode | None:
    """
    Mark an episode as watched/unwatched.
    """
    episode = await session.get(Episode, episode_id)
    if episode is None:
        return None

    episode.is_watched = is_watched

    if is_watched:
        # Cascade: mark all preceding episodes in the same season as watched
        stmt = (
            select(Episode)
            .where(
                Episode.season_id == episode.season_id,
                Episode.episode_number < episode.episode_number,
                Episode.is_watched.is_(False),
            )
        )
        result = await session.execute(stmt)
        preceding = result.scalars().all()
        for ep in preceding:
            ep.is_watched = True

    await session.flush()
    return episode
