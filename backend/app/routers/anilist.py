"""
AniList search API endpoint.

Proxies search requests to the AniList GraphQL API through our Redis
caching layer. No API key is required for public queries.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.services.anilist import search_anilist

router = APIRouter(prefix="/anilist", tags=["anilist"])


# ── Response schema ─────────────────────────────────────────────────────


class AniListSearchResultSchema(BaseModel):
    """Single anime search result from AniList."""

    anilist_id: int
    title: str
    description: str | None = None
    cover_image_url: str | None = None
    release_year: int | None = None
    genres: list[str] = []
    average_score: int | None = None
    episodes_count: int | None = None


# ── Endpoints ───────────────────────────────────────────────────────────


@router.get("/search", response_model=list[AniListSearchResultSchema])
async def search(
    q: str = Query(..., min_length=2, description="Search query"),
    page: int = Query(1, ge=1, le=50),
):
    """
    Search AniList for anime titles.

    Results are cached in Redis for 1 hour. No API key is required.
    """
    results = await search_anilist(query=q, page=page)
    return [
        AniListSearchResultSchema(
            anilist_id=r.anilist_id,
            title=r.title,
            description=r.description,
            cover_image_url=r.cover_image_url,
            release_year=r.release_year,
            genres=r.genres,
            average_score=r.average_score,
            episodes_count=r.episodes_count,
        )
        for r in results
    ]
