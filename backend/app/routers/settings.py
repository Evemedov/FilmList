"""
Settings API endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.settings import get_or_create_settings, update_settings
from app.database import get_session
from app.schemas.settings import AppSettingsRead, AppSettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=AppSettingsRead)
async def read_settings(session: AsyncSession = Depends(get_session)):
    """Return the current application settings."""
    settings = await get_or_create_settings(session)
    await session.commit()
    return settings


@router.patch("", response_model=AppSettingsRead)
async def patch_settings(
    body: AppSettingsUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Partially update application settings."""
    kwargs: dict = {}
    if body.tmdb_api_key is not None:
        kwargs["tmdb_api_key"] = body.tmdb_api_key
    if body.theme is not None:
        kwargs["theme"] = body.theme

    settings = await update_settings(session, **kwargs)
    await session.commit()
    return settings
