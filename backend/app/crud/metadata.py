"""
CRUD helpers for Genre and Screenshot entities.

These are populated from TMDB API data, not directly user-managed.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.media import Media, Season, Episode
from app.models.metadata import Genre, Screenshot


# ── Genre helpers ───────────────────────────────────────────────────────


async def get_or_create_genre(session: AsyncSession, name: str) -> Genre:
    """Return an existing Genre by name, or create one if not found."""
    result = await session.execute(
        select(Genre).where(Genre.name == name)
    )
    genre = result.scalar_one_or_none()
    if genre is None:
        genre = Genre(name=name)
        session.add(genre)
        await session.flush()
    return genre


async def sync_media_genres(
    session: AsyncSession,
    media: Media,
    genre_names: list[str],
) -> None:
    """
    Replace the media's genre set with genres matching the given names.

    Creates any genre that doesn't exist yet.
    """
    genres: list[Genre] = []
    for name in genre_names:
        genre = await get_or_create_genre(session, name)
        genres.append(genre)
    media.genres = genres
    await session.flush()


# ── Screenshot helpers ──────────────────────────────────────────────────


async def sync_media_screenshots(
    session: AsyncSession,
    media: Media,
    screenshot_urls: list[str],
) -> None:
    """
    Replace all screenshots for a media entry with the given URLs.

    Removes existing screenshots and inserts new ones with sequential
    sort_order.
    """
    # Clear existing screenshots (cascade will handle DB rows)
    media.screenshots.clear()
    await session.flush()

    for idx, url in enumerate(screenshot_urls):
        screenshot = Screenshot(
            media_id=media.id,
            url=url,
            sort_order=idx,
        )
        session.add(screenshot)
    await session.flush()


# ── Season / Episode helpers ────────────────────────────────────────────


async def sync_media_seasons(
    session: AsyncSession,
    media: Media,
    seasons_data: list[dict],
    episodes_by_season: dict[int, list[dict]] | None = None,
) -> None:
    """
    Upsert seasons (and optionally episodes) for a media entry from TMDB data.

    Args:
        session: DB session.
        media: The parent Media instance (must have seasons loaded).
        seasons_data: List of dicts with keys: season_number, title, episode_count.
        episodes_by_season: Optional mapping of season_number → list of
            episode dicts (episode_number, title, runtime_minutes).
    """
    episodes_map = episodes_by_season or {}

    # Index existing seasons by number for upsert
    existing_seasons = {s.season_number: s for s in media.seasons}

    for s_data in seasons_data:
        season_num = s_data["season_number"]

        if season_num in existing_seasons:
            # Update existing season title
            season = existing_seasons[season_num]
            if s_data.get("title"):
                season.title = s_data["title"]
        else:
            # Create new season
            season = Season(
                media_id=media.id,
                season_number=season_num,
                title=s_data.get("title"),
            )
            session.add(season)
            await session.flush()  # need ID for episodes

        # Sync episodes if data is available for this season
        if season_num in episodes_map:
            await _sync_season_episodes(
                session, season, episodes_map[season_num]
            )

    await session.flush()


async def _sync_season_episodes(
    session: AsyncSession,
    season: Season,
    episodes_data: list[dict],
) -> None:
    """
    Upsert episodes for a season from TMDB data.

    Preserves existing is_watched state if the episode already exists.
    """
    # Need to load episodes if not already loaded
    try:
        existing_episodes = {e.episode_number: e for e in season.episodes}
    except Exception:
        # If episodes weren't loaded, query them
        result = await session.execute(
            select(Episode).where(Episode.season_id == season.id)
        )
        existing_episodes = {
            e.episode_number: e for e in result.scalars().all()
        }

    for ep_data in episodes_data:
        ep_num = ep_data["episode_number"]

        if ep_num in existing_episodes:
            # Update metadata but preserve is_watched
            ep = existing_episodes[ep_num]
            if ep_data.get("title"):
                ep.title = ep_data["title"]
            if ep_data.get("runtime_minutes") is not None:
                ep.runtime_minutes = ep_data["runtime_minutes"]
        else:
            ep = Episode(
                season_id=season.id,
                episode_number=ep_num,
                title=ep_data.get("title"),
                runtime_minutes=ep_data.get("runtime_minutes"),
                is_watched=False,
            )
            session.add(ep)

    await session.flush()


async def mark_season_watched(
    session: AsyncSession,
    season_id: uuid.UUID,
    *,
    is_watched: bool,
) -> Season | None:
    """
    Mark ALL episodes in a season as watched or unwatched.

    Returns the season with episodes loaded, or None if not found.
    """
    from sqlalchemy.orm import selectinload

    stmt = (
        select(Season)
        .options(selectinload(Season.episodes))
        .where(Season.id == season_id)
    )
    result = await session.execute(stmt)
    season = result.scalar_one_or_none()
    if season is None:
        return None

    for episode in season.episodes:
        episode.is_watched = is_watched

    await session.flush()
    return season
