"""
TMDB enrichment service – orchestrates metadata fetch, merge, and DB writes.

This is the single entry point for "enrich a media item from TMDB".
It wires together the TMDB API client, the merge utility, and the
Genre/Screenshot/Season CRUD helpers.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.metadata import (
    sync_media_genres,
    sync_media_screenshots,
    sync_media_seasons,
)
from app.models.media import ContentType, Media, Season
from app.services.merge import merge_tmdb_into_media
from app.services.tmdb import (
    TMDBMovieData,
    TMDBTVData,
    get_movie_details,
    get_tv_details,
    get_tv_season,
)

logger = logging.getLogger(__name__)

# ContentType values that map to TMDB's "tv" category
_TV_CONTENT_TYPES = frozenset({
    ContentType.TV_SHOW,
    ContentType.ANIME,
    ContentType.CARTOON,
})


async def enrich_media_from_tmdb(
    session: AsyncSession,
    media: Media,
    api_key: str,
    *,
    local_overrides: dict[str, Any] | None = None,
) -> Media:
    """
    Fetch metadata from TMDB and apply it to a Media record.

    This function:
    1. Determines whether to call the movie or TV endpoint based on content_type.
    2. Fetches full details (with images) from TMDB.
    3. Merges API data with local overrides via ``merge_tmdb_into_media()``.
    4. Applies scalar fields to the Media model.
    5. Syncs genres, screenshots, and (for TV) seasons/episodes.

    The Media instance is flushed but NOT committed – the caller controls
    the transaction.

    Args:
        session: Active DB session.
        media: The Media ORM instance to enrich (must have tmdb_id set).
        api_key: TMDB API key.
        local_overrides: User-supplied fields that override API values.

    Returns:
        The enriched Media instance.
    """
    if media.tmdb_id is None:
        logger.warning("enrich_media_from_tmdb called with tmdb_id=None for %s", media.id)
        return media

    tmdb_id = media.tmdb_id
    is_tv = media.content_type in _TV_CONTENT_TYPES

    # ── Step 1: Fetch from TMDB ─────────────────────────────────────────
    tmdb_data: TMDBMovieData | TMDBTVData | None

    if is_tv:
        tmdb_data = await get_tv_details(tmdb_id, api_key)
    else:
        tmdb_data = await get_movie_details(tmdb_id, api_key)

    if tmdb_data is None:
        logger.error("TMDB returned no data for tmdb_id=%d", tmdb_id)
        return media

    # ── Step 2: Merge API + local overrides ─────────────────────────────
    merged = merge_tmdb_into_media(tmdb_data, local_overrides)

    # ── Step 3: Apply scalar fields to Media model ──────────────────────
    _SCALAR_FIELDS = [
        "title",
        "description",
        "cover_image_url",
        "global_rating",
        "release_year",
        "runtime_minutes",
        "api_audio_languages",
        "api_subtitle_languages",
    ]
    for field_name in _SCALAR_FIELDS:
        value = merged.get(field_name)
        if value is not None:
            setattr(media, field_name, value)

    # Apply user-managed overrides (only if explicitly provided)
    _USER_FIELDS = [
        "local_cover_url",
        "local_audio_languages",
        "local_subtitle_languages",
        "web_url",
        "local_network_url",
    ]
    for field_name in _USER_FIELDS:
        if field_name in merged:
            setattr(media, field_name, merged[field_name])

    await session.flush()

    # ── Step 4: Sync genres ─────────────────────────────────────────────
    genre_names = merged.get("_genres", [])
    if genre_names:
        await sync_media_genres(session, media, genre_names)

    # ── Step 5: Sync screenshots ────────────────────────────────────────
    screenshot_urls = merged.get("_screenshots", [])
    if screenshot_urls:
        await sync_media_screenshots(session, media, screenshot_urls)

    # ── Step 6: For TV content, sync seasons and fetch episodes ─────────
    if is_tv and isinstance(tmdb_data, TMDBTVData) and tmdb_data.seasons:
        seasons_data = merged.get("_seasons", [])

        # Fetch episode data for each season
        episodes_by_season: dict[int, list[dict]] = {}
        for s_summary in tmdb_data.seasons:
            season_detail = await get_tv_season(
                tmdb_id, s_summary.season_number, api_key
            )
            if season_detail and season_detail.episodes:
                episodes_by_season[s_summary.season_number] = [
                    {
                        "episode_number": ep.episode_number,
                        "title": ep.title,
                        "runtime_minutes": ep.runtime_minutes,
                    }
                    for ep in season_detail.episodes
                ]

        # Need seasons loaded for upsert logic
        await session.refresh(media, attribute_names=["seasons"])
        # Load existing seasons with episodes
        from sqlalchemy import select

        stmt = (
            select(Season)
            .where(Season.media_id == media.id)
            .options(selectinload(Season.episodes))
            .order_by(Season.season_number)
        )
        result = await session.execute(stmt)
        media.seasons = list(result.scalars().unique().all())

        await sync_media_seasons(
            session, media, seasons_data, episodes_by_season
        )

    await session.flush()
    logger.info(
        "Enriched media %s (%s) from TMDB ID %d",
        media.id,
        media.title,
        tmdb_id,
    )
    return media
