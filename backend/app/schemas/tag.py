"""
Pydantic schemas for Tag entity.
"""

import uuid

from pydantic import BaseModel, ConfigDict, Field


class TagCreate(BaseModel):
    """Body for creating a new tag."""

    name: str = Field(..., min_length=1, max_length=100)


class TagRead(BaseModel):
    """Response schema for a tag."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
