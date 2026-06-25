"""
Pydantic schemas for Genre entity.
"""

import uuid

from pydantic import BaseModel, ConfigDict


class GenreRead(BaseModel):
    """Response schema for a genre (API-fetched, read-only for user)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
