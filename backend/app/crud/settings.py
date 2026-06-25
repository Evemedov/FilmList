"""
CRUD operations for the AppSettings singleton.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings import AppSettings


async def get_or_create_settings(session: AsyncSession) -> AppSettings:
    """Return the single AppSettings row, creating it if it doesn't exist."""
    result = await session.execute(select(AppSettings).limit(1))
    settings = result.scalar_one_or_none()
    if settings is None:
        settings = AppSettings(id=uuid.uuid4())
        session.add(settings)
        await session.flush()
    return settings


async def update_settings(
    session: AsyncSession,
    *,
    tmdb_api_key: str | None = ...,  # type: ignore[assignment]
    theme: str | None = None,
) -> AppSettings:
    """Partially update application settings."""
    settings = await get_or_create_settings(session)

    # Use sentinel `...` to distinguish "not provided" from explicit `None`
    if tmdb_api_key is not ...:
        settings.tmdb_api_key = tmdb_api_key
    if theme is not None:
        settings.theme = theme

    await session.flush()
    return settings
