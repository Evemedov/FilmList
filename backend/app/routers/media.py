"""
Media API endpoints.

Handles CRUD operations for media entries.  When a new media item is created
with a ``tmdb_id``, the backend automatically fetches metadata from TMDB
(cover, genres, screenshots, runtime, seasons/episodes for TV content) and
merges it into the record.
"""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.media import (
    create_media,
    delete_media,
    get_media,
    get_media_list,
    update_media,
)
from app.crud.settings import get_or_create_settings
from app.database import get_session
from app.schemas.media import MediaCreate, MediaRead, MediaReadBrief, MediaUpdate
from app.services.enrich import enrich_media_from_tmdb

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/media", tags=["media"])


@router.get("", response_model=list[MediaReadBrief])
async def list_media(session: AsyncSession = Depends(get_session)):
    """Return all media entries (brief view for dashboard)."""
    return await get_media_list(session)


@router.get("/{media_id}", response_model=MediaRead)
async def read_media(
    media_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Return a single media entry with full details."""
    media = await get_media(session, media_id)
    if media is None:
        raise HTTPException(status_code=404, detail="Media not found")
    return media


@router.post("", response_model=MediaRead, status_code=status.HTTP_201_CREATED)
async def create_new_media(
    body: MediaCreate,
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new media entry.

    If ``tmdb_id`` is provided and a TMDB API key is configured, metadata
    (cover, genres, screenshots, runtime, seasons/episodes) is automatically
    fetched and merged into the record.  User-supplied values always take
    precedence over API data.
    """
    media = await create_media(
        session,
        content_type=body.content_type,
        title=body.title,
        description=body.description,
        my_rating=body.my_rating,
        my_comments=body.my_comments,
        watch_status=body.watch_status,
        is_rewatch=body.is_rewatch,
        cover_image_url=body.cover_image_url,
        local_cover_url=body.local_cover_url,
        web_url=body.web_url,
        local_network_url=body.local_network_url,
        local_audio_languages=body.local_audio_languages,
        local_subtitle_languages=body.local_subtitle_languages,
        tmdb_id=body.tmdb_id,
        tag_ids=body.tag_ids,
    )

    # ── Auto-fetch TMDB metadata if tmdb_id is provided ─────────────────
    if body.tmdb_id is not None:
        api_key = await _get_api_key_or_none(session)
        if api_key:
            local_overrides = body.model_dump(
                include={
                    "local_cover_url",
                    "local_audio_languages",
                    "local_subtitle_languages",
                    "web_url",
                    "local_network_url",
                },
                exclude_unset=True,
            )
            await enrich_media_from_tmdb(
                session,
                media,
                api_key,
                local_overrides=local_overrides,
            )
            # Re-load with full relationships after enrichment
            reloaded_media = await get_media(session, media.id)
            if reloaded_media is not None:
                media = reloaded_media
        else:
            logger.info(
                "Skipping TMDB enrichment for media %s: no API key configured",
                media.id,
            )

    await session.commit()
    return media


@router.patch("/{media_id}", response_model=MediaRead)
async def patch_media(
    media_id: uuid.UUID,
    body: MediaUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Partially update a media entry."""
    update_data = body.model_dump(exclude_unset=True)
    media = await update_media(session, media_id, **update_data)
    if media is None:
        raise HTTPException(status_code=404, detail="Media not found")
    await session.commit()
    return media


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_media(
    media_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Delete a media entry."""
    deleted = await delete_media(session, media_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Media not found")
    await session.commit()


@router.post("/{media_id}/refresh-tmdb", response_model=MediaRead)
async def refresh_tmdb_metadata(
    media_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Re-fetch metadata from TMDB and update the media entry.

    This is useful to pick up changes on TMDB (e.g. new seasons, updated
    ratings) without deleting and re-creating the media entry.

    Requires the media to have a ``tmdb_id`` set and a TMDB API key to be
    configured in settings.
    """
    media = await get_media(session, media_id)
    if media is None:
        raise HTTPException(status_code=404, detail="Media not found")

    if media.tmdb_id is None:
        raise HTTPException(
            status_code=400,
            detail="Media has no TMDB ID. Cannot refresh.",
        )

    api_key = await _get_api_key_or_none(session)
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="TMDB API key is not configured. Set it in Settings first.",
        )

    await enrich_media_from_tmdb(session, media, api_key)
    # Re-load with full relationships after enrichment
    reloaded_media = await get_media(session, media.id)
    if reloaded_media is not None:
        media = reloaded_media
    await session.commit()
    return media


# ── Internal helpers ────────────────────────────────────────────────────


async def _get_api_key_or_none(session: AsyncSession) -> str | None:
    """Return the TMDB API key from settings, or None if not configured."""
    settings = await get_or_create_settings(session)
    return settings.tmdb_api_key or None
