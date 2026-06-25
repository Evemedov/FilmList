"""
Season & Episode API endpoints.

Includes:
- List seasons (with episodes) for a media entry
- Toggle individual episode watched status (with cascading logic)
- Mark all episodes in a season as watched/unwatched
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.media import set_episode_watched
from app.crud.metadata import mark_season_watched
from app.database import get_session
from app.models.media import Media, Season
from app.schemas.media import EpisodeRead, EpisodeUpdate, SeasonRead

router = APIRouter(prefix="/media/{media_id}", tags=["seasons & episodes"])


@router.get("/seasons", response_model=list[SeasonRead])
async def list_seasons(
    media_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Return all seasons (with episodes) for a media entry."""
    stmt = (
        select(Season)
        .where(Season.media_id == media_id)
        .options(selectinload(Season.episodes))
        .order_by(Season.season_number)
    )
    result = await session.execute(stmt)
    seasons = result.scalars().unique().all()
    if not seasons:
        # Check if media exists at all
        media = await session.get(Media, media_id)
        if media is None:
            raise HTTPException(status_code=404, detail="Media not found")
    return seasons


@router.patch(
    "/episodes/{episode_id}",
    response_model=EpisodeRead,
)
async def toggle_episode_watched(
    media_id: uuid.UUID,
    episode_id: uuid.UUID,
    body: EpisodeUpdate,
    session: AsyncSession = Depends(get_session),
):
    """
    Toggle an episode's watched status.
    """
    episode = await set_episode_watched(
        session, episode_id, is_watched=body.is_watched
    )
    if episode is None:
        raise HTTPException(status_code=404, detail="Episode not found")
    await session.commit()
    return episode


@router.patch(
    "/seasons/{season_id}/watch-all",
    response_model=SeasonRead,
)
async def toggle_season_watched(
    media_id: uuid.UUID,
    season_id: uuid.UUID,
    body: EpisodeUpdate,
    session: AsyncSession = Depends(get_session),
):
    """
    Mark ALL episodes in a season as watched or unwatched.

    Accepts the same ``EpisodeUpdate`` body (``is_watched: bool``).
    Returns the full season with updated episodes.
    """
    season = await mark_season_watched(
        session, season_id, is_watched=body.is_watched
    )
    if season is None:
        raise HTTPException(status_code=404, detail="Season not found")
    await session.commit()
    return season
