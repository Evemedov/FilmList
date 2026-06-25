"""
Pydantic schemas package – re-exports all request/response schemas.
"""

from app.schemas.genre import GenreRead
from app.schemas.media import (
    EpisodeRead,
    EpisodeUpdate,
    MediaCreate,
    MediaRead,
    MediaReadBrief,
    MediaUpdate,
    SeasonRead,
)
from app.schemas.screenshot import ScreenshotRead
from app.schemas.settings import AppSettingsRead, AppSettingsUpdate
from app.schemas.tag import TagCreate, TagRead

__all__ = [
    "MediaCreate",
    "MediaUpdate",
    "MediaRead",
    "MediaReadBrief",
    "SeasonRead",
    "EpisodeRead",
    "EpisodeUpdate",
    "TagCreate",
    "TagRead",
    "GenreRead",
    "ScreenshotRead",
    "AppSettingsRead",
    "AppSettingsUpdate",
]
