"""
AniList GraphQL API service – searches for anime and caches responses in Redis.

AniList's public API requires NO authentication for search queries.
Endpoint: https://graphql.anilist.co  (POST, application/json)

Cache key pattern and TTL:
    anilist:search:{query}  → 1 hour
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.services.redis import get_redis

logger = logging.getLogger(__name__)

ANILIST_URL = "https://graphql.anilist.co"
TTL_SEARCH = 3600  # 1 hour

# GraphQL query for searching anime
SEARCH_QUERY = """
query ($search: String, $page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    media(search: $search, type: ANIME, sort: POPULARITY_DESC) {
      id
      title {
        english
        romaji
        native
      }
      description(asHtml: false)
      coverImage {
        large
      }
      seasonYear
      averageScore
      genres
      episodes
      format
      status
    }
  }
}
"""


@dataclass
class AniListSearchResult:
    """Single anime search result from AniList."""

    anilist_id: int
    title: str
    description: str | None = None
    cover_image_url: str | None = None
    release_year: int | None = None
    genres: list[str] = field(default_factory=list)
    average_score: int | None = None  # 0-100 scale
    episodes_count: int | None = None


# ── Redis cache helpers ─────────────────────────────────────────────────


async def _cache_get(key: str) -> list | None:
    """Try to read a value from Redis. Returns parsed JSON or None."""
    try:
        redis = await get_redis()
        raw = await redis.get(key)
        if raw is not None:
            logger.debug("AniList cache HIT: %s", key)
            return json.loads(raw)
    except Exception:
        logger.warning("Redis read failed for key %s, falling through to API", key)
    return None


async def _cache_set(key: str, data: Any, ttl: int) -> None:
    """Write a value to Redis with a TTL. Failures are silently logged."""
    try:
        redis = await get_redis()
        await redis.set(key, json.dumps(data, default=str), ex=ttl)
        logger.debug("AniList cache SET: %s (TTL=%ds)", key, ttl)
    except Exception:
        logger.warning("Redis write failed for key %s", key, exc_info=True)


# ── HTTP client ─────────────────────────────────────────────────────────

_http_client: httpx.AsyncClient | None = None


def _get_http_client() -> httpx.AsyncClient:
    """Return the shared httpx async client (lazy init)."""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(
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


def _strip_html(text: str | None) -> str | None:
    """Remove basic HTML tags from AniList descriptions."""
    if not text:
        return text
    import re
    clean = re.sub(r"<[^>]+>", "", text)
    # Collapse multiple newlines
    clean = re.sub(r"\n{3,}", "\n\n", clean)
    return clean.strip()


# ── Public API: Search ──────────────────────────────────────────────────


async def search_anilist(
    query: str,
    *,
    page: int = 1,
    per_page: int = 20,
) -> list[AniListSearchResult]:
    """
    Search AniList for anime titles.

    Args:
        query: User search string.
        page: Result page number.
        per_page: Results per page (max 50).

    Returns:
        List of AniListSearchResult dataclasses.
    """
    cache_key = f"anilist:search:{query.lower().strip()}:{page}"

    # Check cache
    cached = await _cache_get(cache_key)
    if cached is not None:
        return [AniListSearchResult(**item) for item in cached]

    # Call AniList GraphQL
    client = _get_http_client()
    try:
        resp = await client.post(
            ANILIST_URL,
            json={
                "query": SEARCH_QUERY,
                "variables": {
                    "search": query,
                    "page": page,
                    "perPage": per_page,
                },
            },
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPStatusError as exc:
        logger.error("AniList API error: %s", exc.response.status_code)
        return []
    except httpx.RequestError as exc:
        logger.error("AniList request failed: %s", exc)
        return []

    results: list[AniListSearchResult] = []
    media_list = (
        data.get("data", {}).get("Page", {}).get("media", [])
    )

    for item in media_list:
        title_obj = item.get("title", {})
        # Prefer English title, fall back to romaji, then native
        title = (
            title_obj.get("english")
            or title_obj.get("romaji")
            or title_obj.get("native")
            or ""
        )

        cover = (item.get("coverImage") or {}).get("large")

        results.append(
            AniListSearchResult(
                anilist_id=item["id"],
                title=title,
                description=_strip_html(item.get("description")),
                cover_image_url=cover,
                release_year=item.get("seasonYear"),
                genres=item.get("genres", []),
                average_score=item.get("averageScore"),
                episodes_count=item.get("episodes"),
            )
        )

    # Cache the results
    await _cache_set(
        cache_key,
        [
            {
                "anilist_id": r.anilist_id,
                "title": r.title,
                "description": r.description,
                "cover_image_url": r.cover_image_url,
                "release_year": r.release_year,
                "genres": r.genres,
                "average_score": r.average_score,
                "episodes_count": r.episodes_count,
            }
            for r in results
        ],
        TTL_SEARCH,
    )

    return results
