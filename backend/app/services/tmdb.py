"""
TMDB API service – fetches movie/TV metadata and caches responses in Redis.

Cache key patterns and TTLs (from implementation plan):
    tmdb:search:{query}        → 1 hour   (search results change frequently)
    tmdb:movie:{tmdb_id}       → 24 hours  (movie details are stable)
    tmdb:tv:{tmdb_id}          → 24 hours  (TV show details are stable)
    tmdb:tv:{tmdb_id}:s{n}     → 24 hours  (season details are stable)
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.services.redis import get_redis

logger = logging.getLogger(__name__)

# ── Constants ───────────────────────────────────────────────────────────

TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p"

# TTLs in seconds
TTL_SEARCH = 3600       # 1 hour
TTL_DETAIL = 86400      # 24 hours

# Image size presets used when building full URLs
POSTER_SIZE = "w500"
BACKDROP_SIZE = "w1280"
STILL_SIZE = "w780"


# ── Data containers ─────────────────────────────────────────────────────


@dataclass
class TMDBMovieData:
    """Parsed metadata for a movie from TMDB."""

    tmdb_id: int
    title: str
    description: str | None = None
    cover_image_url: str | None = None
    global_rating: float | None = None
    release_year: int | None = None
    runtime_minutes: int | None = None
    genres: list[str] = field(default_factory=list)
    screenshots: list[str] = field(default_factory=list)
    audio_languages: list[str] = field(default_factory=list)
    subtitle_languages: list[str] | None = None


@dataclass
class TMDBTVData:
    """Parsed metadata for a TV show from TMDB."""

    tmdb_id: int
    title: str
    description: str | None = None
    cover_image_url: str | None = None
    global_rating: float | None = None
    release_year: int | None = None
    runtime_minutes: int | None = None  # average episode runtime
    genres: list[str] = field(default_factory=list)
    screenshots: list[str] = field(default_factory=list)
    audio_languages: list[str] = field(default_factory=list)
    subtitle_languages: list[str] | None = None
    seasons: list[TMDBSeasonSummary] = field(default_factory=list)


@dataclass
class TMDBSeasonSummary:
    """Brief season info returned with TV show details."""

    season_number: int
    title: str | None = None
    episode_count: int = 0


@dataclass
class TMDBSeasonDetail:
    """Full season detail with episode list."""

    season_number: int
    title: str | None = None
    episodes: list[TMDBEpisode] = field(default_factory=list)


@dataclass
class TMDBEpisode:
    """Single episode from a TMDB season response."""

    episode_number: int
    title: str | None = None
    runtime_minutes: int | None = None


@dataclass
class TMDBSearchResult:
    """Single item in a search result list."""

    tmdb_id: int
    title: str
    description: str | None = None
    cover_image_url: str | None = None
    release_year: int | None = None
    media_type: str = "movie"  # "movie" or "tv"


# ── Image URL helpers ───────────────────────────────────────────────────


def _poster_url(path: str | None) -> str | None:
    """Build a full poster URL from a TMDB relative path."""
    if not path:
        return None
    return f"{TMDB_IMAGE_BASE}/{POSTER_SIZE}{path}"


def _backdrop_url(path: str | None) -> str | None:
    """Build a full backdrop URL from a TMDB relative path."""
    if not path:
        return None
    return f"{TMDB_IMAGE_BASE}/{BACKDROP_SIZE}{path}"


def _still_url(path: str | None) -> str | None:
    """Build a full still URL from a TMDB relative path."""
    if not path:
        return None
    return f"{TMDB_IMAGE_BASE}/{STILL_SIZE}{path}"


# ── Redis cache helpers ─────────────────────────────────────────────────


async def _cache_get(key: str) -> dict | list | None:
    """Try to read a value from Redis. Returns parsed JSON or None."""
    try:
        redis = await get_redis()
        raw = await redis.get(key)
        if raw is not None:
            logger.debug("Cache HIT: %s", key)
            return json.loads(raw)
    except Exception:
        logger.warning("Redis read failed for key %s, falling through to API", key)
    return None


async def _cache_set(key: str, data: Any, ttl: int) -> None:
    """Write a value to Redis with a TTL. Failures are silently logged."""
    try:
        redis = await get_redis()
        await redis.set(key, json.dumps(data, default=str), ex=ttl)
        logger.debug("Cache SET: %s (TTL=%ds)", key, ttl)
    except Exception:
        logger.warning("Redis write failed for key %s", key, exc_info=True)


# ── HTTP client ─────────────────────────────────────────────────────────

# Reusable async client with connection pooling and reasonable timeouts.
_http_client: httpx.AsyncClient | None = None


def _get_http_client() -> httpx.AsyncClient:
    """Return the shared httpx async client (lazy init)."""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(
            base_url=TMDB_BASE_URL,
            timeout=httpx.Timeout(10.0, connect=5.0),
            follow_redirects=True,
        )
    return _http_client


async def close_http_client() -> None:
    """Gracefully close the httpx client (call on app shutdown)."""
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None


def _is_bearer_token(api_key: str) -> bool:
    """Detect if the key is a TMDB v4 Bearer token (JWT) vs a v3 API key."""
    return api_key.startswith("eyJ") or len(api_key) > 64


async def _tmdb_get(
    endpoint: str,
    api_key: str,
    *,
    params: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """
    Make an authenticated GET request to TMDB.

    Supports both v3 API keys (passed as query param) and v4 Bearer
    tokens (passed as Authorization header).

    Returns the parsed JSON body, or None if the request failed.
    """
    client = _get_http_client()
    request_params = {**(params or {})}
    headers: dict[str, str] = {}

    if _is_bearer_token(api_key):
        headers["Authorization"] = f"Bearer {api_key}"
    else:
        request_params["api_key"] = api_key

    try:
        resp = await client.get(endpoint, params=request_params, headers=headers)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as exc:
        logger.error(
            "TMDB API error: %s %s → %s",
            exc.request.method,
            exc.request.url,
            exc.response.status_code,
        )
    except httpx.RequestError as exc:
        logger.error("TMDB request failed: %s", exc)
    return None


# ── Public API: Search ──────────────────────────────────────────────────


async def search_tmdb(
    query: str,
    api_key: str,
    *,
    media_type: str = "multi",
    page: int = 1,
) -> list[TMDBSearchResult]:
    """
    Search TMDB for movies and/or TV shows.

    Args:
        query: User search string.
        api_key: TMDB API key.
        media_type: "movie", "tv", or "multi" (searches both).
        page: Result page number.

    Returns:
        List of TMDBSearchResult dataclasses.
    """
    cache_key = f"tmdb:search:{query.lower().strip()}:{media_type}:{page}"

    # Check cache
    cached = await _cache_get(cache_key)
    if cached is not None:
        return [TMDBSearchResult(**item) for item in cached]

    # Call TMDB
    if media_type == "multi":
        endpoint = "/search/multi"
    elif media_type == "tv":
        endpoint = "/search/tv"
    else:
        endpoint = "/search/movie"

    data = await _tmdb_get(
        endpoint, api_key, params={"query": query, "page": page}
    )
    if data is None:
        return []

    results: list[TMDBSearchResult] = []
    for item in data.get("results", []):
        item_type = item.get("media_type", media_type)
        # Skip non-movie/tv results from multi-search (e.g. person)
        if item_type not in ("movie", "tv"):
            continue

        title = item.get("title") or item.get("name") or ""
        release_date = item.get("release_date") or item.get("first_air_date") or ""
        release_year = int(release_date[:4]) if len(release_date) >= 4 else None

        results.append(
            TMDBSearchResult(
                tmdb_id=item["id"],
                title=title,
                description=item.get("overview"),
                cover_image_url=_poster_url(item.get("poster_path")),
                release_year=release_year,
                media_type=item_type,
            )
        )

    # Cache the results
    await _cache_set(
        cache_key,
        [
            {
                "tmdb_id": r.tmdb_id,
                "title": r.title,
                "description": r.description,
                "cover_image_url": r.cover_image_url,
                "release_year": r.release_year,
                "media_type": r.media_type,
            }
            for r in results
        ],
        TTL_SEARCH,
    )

    return results


# ── Public API: Movie Details ───────────────────────────────────────────


async def get_movie_details(
    tmdb_id: int,
    api_key: str,
) -> TMDBMovieData | None:
    """
    Fetch full movie details from TMDB (with images in a single request).

    Uses ``append_to_response=images`` to minimise API calls.
    """
    cache_key = f"tmdb:movie:{tmdb_id}"

    # Check cache
    cached = await _cache_get(cache_key)
    if cached is not None and isinstance(cached, dict):
        return TMDBMovieData(**cached)

    data = await _tmdb_get(
        f"/movie/{tmdb_id}",
        api_key,
        params={"append_to_response": "images"},
    )
    if data is None:
        return None

    release_date = data.get("release_date", "")
    release_year = int(release_date[:4]) if len(release_date) >= 4 else None

    # Extract up to 10 backdrop images as "screenshots"
    images = data.get("images", {})
    backdrops = images.get("backdrops", [])[:10]
    screenshots = [
        url
        for bd in backdrops
        if (url := _backdrop_url(bd.get("file_path")))
    ]

    # Extract spoken languages
    audio_langs = [
        lang.get("iso_639_1", "")
        for lang in data.get("spoken_languages", [])
        if lang.get("iso_639_1")
    ]

    result = TMDBMovieData(
        tmdb_id=data["id"],
        title=data.get("title", ""),
        description=data.get("overview"),
        cover_image_url=_poster_url(data.get("poster_path")),
        global_rating=data.get("vote_average"),
        release_year=release_year,
        runtime_minutes=data.get("runtime"),
        genres=[g["name"] for g in data.get("genres", [])],
        screenshots=screenshots,
        audio_languages=audio_langs,
    )

    # Cache the full result
    await _cache_set(cache_key, result.__dict__, TTL_DETAIL)
    return result


# ── Public API: TV Show Details ─────────────────────────────────────────


async def get_tv_details(
    tmdb_id: int,
    api_key: str,
) -> TMDBTVData | None:
    """
    Fetch full TV show details from TMDB (with images in a single request).
    """
    cache_key = f"tmdb:tv:{tmdb_id}"

    # Check cache
    cached = await _cache_get(cache_key)
    if cached is not None and isinstance(cached, dict):
        # Reconstruct nested dataclasses from dicts
        seasons_raw = cached.pop("seasons", [])
        tv = TMDBTVData(**cached)
        tv.seasons = [TMDBSeasonSummary(**s) for s in seasons_raw]
        return tv

    data = await _tmdb_get(
        f"/tv/{tmdb_id}",
        api_key,
        params={"append_to_response": "images"},
    )
    if data is None:
        return None

    first_air = data.get("first_air_date", "")
    release_year = int(first_air[:4]) if len(first_air) >= 4 else None

    # Average episode runtime (TMDB returns a list; take the first value)
    runtimes = data.get("episode_run_time", [])
    runtime = runtimes[0] if runtimes else None

    # Extract backdrops
    images = data.get("images", {})
    backdrops = images.get("backdrops", [])[:10]
    screenshots = [
        url
        for bd in backdrops
        if (url := _backdrop_url(bd.get("file_path")))
    ]

    # Extract spoken languages
    audio_langs = [
        lang.get("iso_639_1", "")
        for lang in data.get("spoken_languages", [])
        if lang.get("iso_639_1")
    ]

    # Parse season summaries (skip specials / season 0)
    season_summaries = [
        TMDBSeasonSummary(
            season_number=s["season_number"],
            title=s.get("name"),
            episode_count=s.get("episode_count", 0),
        )
        for s in data.get("seasons", [])
        if s.get("season_number", 0) > 0
    ]

    result = TMDBTVData(
        tmdb_id=data["id"],
        title=data.get("name", ""),
        description=data.get("overview"),
        cover_image_url=_poster_url(data.get("poster_path")),
        global_rating=data.get("vote_average"),
        release_year=release_year,
        runtime_minutes=runtime,
        genres=[g["name"] for g in data.get("genres", [])],
        screenshots=screenshots,
        audio_languages=audio_langs,
        seasons=season_summaries,
    )

    # Cache – serialise nested dataclasses
    cache_payload = {
        **result.__dict__,
        "seasons": [s.__dict__ for s in result.seasons],
    }
    await _cache_set(cache_key, cache_payload, TTL_DETAIL)

    return result


# ── Public API: TV Season Detail (episodes) ─────────────────────────────


async def get_tv_season(
    tmdb_id: int,
    season_number: int,
    api_key: str,
) -> TMDBSeasonDetail | None:
    """
    Fetch episode list for a specific season of a TV show.
    """
    cache_key = f"tmdb:tv:{tmdb_id}:s{season_number}"

    # Check cache
    cached = await _cache_get(cache_key)
    if cached is not None and isinstance(cached, dict):
        episodes_raw = cached.pop("episodes", [])
        detail = TMDBSeasonDetail(**cached)
        detail.episodes = [TMDBEpisode(**e) for e in episodes_raw]
        return detail

    data = await _tmdb_get(
        f"/tv/{tmdb_id}/season/{season_number}",
        api_key,
    )
    if data is None:
        return None

    episodes = [
        TMDBEpisode(
            episode_number=ep["episode_number"],
            title=ep.get("name"),
            runtime_minutes=ep.get("runtime"),
        )
        for ep in data.get("episodes", [])
    ]

    result = TMDBSeasonDetail(
        season_number=data.get("season_number", season_number),
        title=data.get("name"),
        episodes=episodes,
    )

    # Cache
    cache_payload = {
        **result.__dict__,
        "episodes": [e.__dict__ for e in result.episodes],
    }
    await _cache_set(cache_key, cache_payload, TTL_DETAIL)

    return result
