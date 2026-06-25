"""
Merge utility – reconciles TMDB API data with local database records.
"""

from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any

from app.services.tmdb import TMDBMovieData, TMDBTVData

logger = logging.getLogger(__name__)

# Fields that are exclusively user-managed and must NEVER be overwritten by
# API data, even if the API returns a value for them.
_LOCAL_ONLY_FIELDS = frozenset({
    "my_rating",
    "my_comments",
    "watch_status",
    "is_rewatch",
    "local_cover_url",
    "local_audio_languages",
    "local_subtitle_languages",
    "web_url",
    "local_network_url",
    "tag_ids",
})


def merge_tmdb_into_media(
    tmdb_data: TMDBMovieData | TMDBTVData,
    local_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build a merged field dict suitable for creating/updating a Media record.

    Produces a flat dict that maps directly to Media model columns.  The
    merge follows these rules:

    1. **API-sourced scalar fields** (description, global_rating, release_year,
       runtime_minutes, tmdb_id) are taken from ``tmdb_data``.
    2. **Cover image precedence**: ``local_cover_url`` (from ``local_overrides``)
       wins over ``cover_image_url`` (from API).  Both are stored separately so
       the user can "remove local cover" and fall back to the API cover.
    3. **Audio & subtitle languages**: API values go into ``api_audio_languages``
       / ``api_subtitle_languages``.  Local values from ``local_overrides`` go
       into ``local_audio_languages`` / ``local_subtitle_languages``.  They
       never cross-contaminate.
    4. **Genres** are returned as a list of genre **name strings** (to be
       resolved into Genre rows by the caller).
    5. **Screenshots** are returned as a list of URL strings (to be resolved
       into Screenshot rows by the caller).
    6. **Seasons/episodes** (TV only) are returned under a ``seasons`` key as a
       list of dicts — the caller should iterate and upsert Season/Episode rows.
    7. Any key present in ``local_overrides`` that is also user-managed
       (e.g. ``my_rating``, ``watch_status``) is forwarded verbatim.

    Args:
        tmdb_data: Parsed TMDB response (movie or TV).
        local_overrides: Optional dict of user-supplied values that should
            override or supplement the API data.

    Returns:
        A dict ready to be unpacked into ``create_media()`` or applied via
        ``update_media()``.
    """
    overrides = local_overrides or {}

    # ── Start with API-sourced scalar fields ────────────────────────────
    merged: dict[str, Any] = {
        "tmdb_id": tmdb_data.tmdb_id,
        "title": tmdb_data.title,
        "description": tmdb_data.description,
        "cover_image_url": tmdb_data.cover_image_url,
        "global_rating": tmdb_data.global_rating,
        "release_year": tmdb_data.release_year,
        "runtime_minutes": tmdb_data.runtime_minutes,
    }

    # ── Audio & subtitles (API → api_* columns only) ────────────────────
    merged["api_audio_languages"] = tmdb_data.audio_languages or None
    merged["api_subtitle_languages"] = getattr(
        tmdb_data, "subtitle_languages", None
    )

    # ── Relational metadata (returned for the caller to process) ────────
    merged["_genres"] = tmdb_data.genres  # list[str]
    merged["_screenshots"] = tmdb_data.screenshots  # list[str]

    # TV-specific: season/episode structure
    if isinstance(tmdb_data, TMDBTVData) and tmdb_data.seasons:
        merged["_seasons"] = [asdict(s) for s in tmdb_data.seasons]

    # ── Apply local overrides ───────────────────────────────────────────
    # User-managed fields are simply forwarded as-is.
    for key, value in overrides.items():
        if key in _LOCAL_ONLY_FIELDS:
            merged[key] = value

    # Title override: if the user explicitly provides a title, prefer it.
    if "title" in overrides and overrides["title"]:
        merged["title"] = overrides["title"]

    # Description override: if the user explicitly provides one, prefer it.
    if "description" in overrides and overrides["description"] is not None:
        merged["description"] = overrides["description"]

    return merged


def resolve_cover_url(
    *,
    local_cover_url: str | None = None,
    api_cover_url: str | None = None,
) -> str | None:
    """
    Determine the effective cover URL to display.

    This is a pure display-time helper – both URLs remain stored separately
    in the database so the user can remove the local cover and revert.

    Args:
        local_cover_url: User-uploaded or user-specified cover URL.
        api_cover_url: TMDB-sourced cover URL.

    Returns:
        The URL to use for display, or None if neither is set.
    """
    return local_cover_url or api_cover_url


def diff_api_vs_local(
    tmdb_data: TMDBMovieData | TMDBTVData,
    local_record: dict[str, Any],
) -> dict[str, Any]:
    """
    Compare TMDB data with the current local DB record and return only the
    fields where the API provides a new/different value.

    Useful for showing users what will change before confirming an update,
    or for selectively updating only stale fields.

    Rules:
        - User-managed fields are NEVER included in the diff.
        - ``cover_image_url`` is included if the API cover changed, but
          it will NOT override ``local_cover_url`` at the application level.
        - Genre and screenshot changes are reported under ``_genres`` and
          ``_screenshots`` keys.

    Args:
        tmdb_data: Fresh TMDB response.
        local_record: Current DB record as a dict (e.g. from
            ``MediaRead.model_dump()``).

    Returns:
        Dict of field_name → new_value for fields that differ.
    """
    full_merge = merge_tmdb_into_media(tmdb_data)
    changes: dict[str, Any] = {}

    # Compare scalar API-sourced fields
    api_fields = [
        "tmdb_id",
        "title",
        "description",
        "cover_image_url",
        "global_rating",
        "release_year",
        "runtime_minutes",
        "api_audio_languages",
        "api_subtitle_languages",
    ]
    for field_name in api_fields:
        new_val = full_merge.get(field_name)
        old_val = local_record.get(field_name)
        if new_val != old_val and new_val is not None:
            changes[field_name] = new_val

    # Compare genre names
    new_genres = set(full_merge.get("_genres", []))
    old_genres = {g["name"] if isinstance(g, dict) else g for g in local_record.get("genres", [])}
    if new_genres != old_genres:
        changes["_genres"] = sorted(new_genres)

    # Compare screenshot URLs
    new_screenshots = set(full_merge.get("_screenshots", []))
    old_screenshots = {
        s["url"] if isinstance(s, dict) else s for s in local_record.get("screenshots", [])
    }
    if new_screenshots != old_screenshots:
        changes["_screenshots"] = sorted(new_screenshots)

    return changes
