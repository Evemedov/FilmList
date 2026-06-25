"""
Pydantic schemas for Screenshot entity.
"""

import uuid

from pydantic import BaseModel, ConfigDict


class ScreenshotRead(BaseModel):
    """Response schema for a screenshot (API-fetched, read-only for user)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    url: str
    sort_order: int
