"""
TMDB search & lookup API endpoints.

These proxy requests to the TMDB API through our Redis caching layer so
the frontend never talks to TMDB directly.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.settings import get_or_create_settings
from app.database import get_session
from app.services.tmdb import (
    search_tmdb,
    get_movie_details,
    get_tv_details,
    get_tv_season,
)

router = APIRouter(prefix="/tmdb", tags=["tmdb"])


# ── Response schemas (TMDB-specific, not DB models) ─────────────────────


class TMDBSearchResultSchema(BaseModel):
    """Single search result from TMDB."""

    tmdb_id: int
    title: str
    description: str | None = None
    cover_image_url: str | None = None
    release_year: int | None = None
    media_type: str


class TMDBMovieDetailSchema(BaseModel):
    """Full movie details from TMDB."""

    tmdb_id: int
    title: str
    description: str | None = None
    cover_image_url: str | None = None
    global_rating: float | None = None
    release_year: int | None = None
    runtime_minutes: int | None = None
    genres: list[str] = []
    screenshots: list[str] = []
    audio_languages: list[str] = []


class TMDBSeasonSummarySchema(BaseModel):
    """Brief season info in a TV show detail response."""

    season_number: int
    title: str | None = None
    episode_count: int = 0


class TMDBTVDetailSchema(BaseModel):
    """Full TV show details from TMDB."""

    tmdb_id: int
    title: str
    description: str | None = None
    cover_image_url: str | None = None
    global_rating: float | None = None
    release_year: int | None = None
    runtime_minutes: int | None = None
    genres: list[str] = []
    screenshots: list[str] = []
    audio_languages: list[str] = []
    seasons: list[TMDBSeasonSummarySchema] = []


class TMDBEpisodeSchema(BaseModel):
    """Single episode from a TMDB season detail."""

    episode_number: int
    title: str | None = None
    runtime_minutes: int | None = None


class TMDBSeasonDetailSchema(BaseModel):
    """Full season details with episode list."""

    season_number: int
    title: str | None = None
    episodes: list[TMDBEpisodeSchema] = []


# ── Helper: get API key from DB settings ────────────────────────────────


async def _require_api_key(session: AsyncSession) -> str:
    """Fetch the TMDB API key from app_settings or raise 400."""
    settings = await get_or_create_settings(session)
    if not settings.tmdb_api_key:
        raise HTTPException(
            status_code=400,
            detail="TMDB API key is not configured. Set it in Settings first.",
        )
    return settings.tmdb_api_key


# ── Endpoints ───────────────────────────────────────────────────────────


@router.get("/search", response_model=list[TMDBSearchResultSchema])
async def search(
    q: str = Query(..., min_length=1, description="Search query"),
    media_type: str = Query(
        "multi",
        pattern=r"^(multi|movie|tv)$",
        description="Filter by movie, tv, or multi (both)",
    ),
    page: int = Query(1, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    """
    Search TMDB for movies and/or TV shows.

    Results are cached in Redis for 1 hour.
    """
    api_key = await _require_api_key(session)
    results = await search_tmdb(
        query=q, api_key=api_key, media_type=media_type, page=page
    )
    return [
        TMDBSearchResultSchema(
            tmdb_id=r.tmdb_id,
            title=r.title,
            description=r.description,
            cover_image_url=r.cover_image_url,
            release_year=r.release_year,
            media_type=r.media_type,
        )
        for r in results
    ]


@router.get("/movie/{tmdb_id}", response_model=TMDBMovieDetailSchema)
async def movie_detail(
    tmdb_id: int,
    session: AsyncSession = Depends(get_session),
):
    """
    Get full movie details from TMDB (cached for 24 hours).

    Use this endpoint to preview metadata before creating a media entry.
    """
    api_key = await _require_api_key(session)
    data = await get_movie_details(tmdb_id, api_key)
    if data is None:
        raise HTTPException(status_code=404, detail="Movie not found on TMDB")
    return TMDBMovieDetailSchema(
        tmdb_id=data.tmdb_id,
        title=data.title,
        description=data.description,
        cover_image_url=data.cover_image_url,
        global_rating=data.global_rating,
        release_year=data.release_year,
        runtime_minutes=data.runtime_minutes,
        genres=data.genres,
        screenshots=data.screenshots,
        audio_languages=data.audio_languages,
    )


@router.get("/tv/{tmdb_id}", response_model=TMDBTVDetailSchema)
async def tv_detail(
    tmdb_id: int,
    session: AsyncSession = Depends(get_session),
):
    """
    Get full TV show details from TMDB (cached for 24 hours).

    Use this endpoint to preview metadata before creating a media entry.
    """
    api_key = await _require_api_key(session)
    data = await get_tv_details(tmdb_id, api_key)
    if data is None:
        raise HTTPException(status_code=404, detail="TV show not found on TMDB")
    return TMDBTVDetailSchema(
        tmdb_id=data.tmdb_id,
        title=data.title,
        description=data.description,
        cover_image_url=data.cover_image_url,
        global_rating=data.global_rating,
        release_year=data.release_year,
        runtime_minutes=data.runtime_minutes,
        genres=data.genres,
        screenshots=data.screenshots,
        audio_languages=data.audio_languages,
        seasons=[
            TMDBSeasonSummarySchema(
                season_number=s.season_number,
                title=s.title,
                episode_count=s.episode_count,
            )
            for s in data.seasons
        ],
    )


@router.get(
    "/tv/{tmdb_id}/season/{season_number}",
    response_model=TMDBSeasonDetailSchema,
)
async def tv_season_detail(
    tmdb_id: int,
    season_number: int,
    session: AsyncSession = Depends(get_session),
):
    """
    Get full season details (with episodes) from TMDB (cached for 24 hours).
    """
    api_key = await _require_api_key(session)
    data = await get_tv_season(tmdb_id, season_number, api_key)
    if data is None:
        raise HTTPException(
            status_code=404,
            detail=f"Season {season_number} not found on TMDB",
        )
    return TMDBSeasonDetailSchema(
        season_number=data.season_number,
        title=data.title,
        episodes=[
            TMDBEpisodeSchema(
                episode_number=ep.episode_number,
                title=ep.title,
                runtime_minutes=ep.runtime_minutes,
            )
            for ep in data.episodes
        ],
    )
