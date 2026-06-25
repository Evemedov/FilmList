"""
Models package – re-exports every model and the Base for convenient imports.

Usage:
    from app.models import Base, Media, Season, Episode, Tag, Genre, Screenshot, AppSettings
"""

from app.models.base import Base
from app.models.media import ContentType, Episode, Media, Season, WatchStatus
from app.models.metadata import Genre, Screenshot, media_genres
from app.models.settings import AppSettings
from app.models.tag import Tag, media_tags

__all__ = [
    "Base",
    "ContentType",
    "WatchStatus",
    "Media",
    "Season",
    "Episode",
    "Tag",
    "media_tags",
    "Genre",
    "Screenshot",
    "media_genres",
    "AppSettings",
]
