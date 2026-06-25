"""
CRUD operations for Tag entity.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag


async def get_tags(session: AsyncSession) -> list[Tag]:
    """Return all tags ordered by name."""
    result = await session.execute(select(Tag).order_by(Tag.name))
    return list(result.scalars().all())


async def get_tag(session: AsyncSession, tag_id: uuid.UUID) -> Tag | None:
    """Return a single tag by ID."""
    return await session.get(Tag, tag_id)


async def get_tags_by_ids(session: AsyncSession, tag_ids: list[uuid.UUID]) -> list[Tag]:
    """Return tags matching the given IDs."""
    if not tag_ids:
        return []
    result = await session.execute(select(Tag).where(Tag.id.in_(tag_ids)))
    return list(result.scalars().all())


async def create_tag(session: AsyncSession, *, name: str) -> Tag:
    """Create a new tag."""
    tag = Tag(name=name)
    session.add(tag)
    await session.flush()
    return tag


async def delete_tag(session: AsyncSession, tag_id: uuid.UUID) -> bool:
    """Delete a tag by ID. Returns True if deleted, False if not found."""
    tag = await session.get(Tag, tag_id)
    if tag is None:
        return False
    await session.delete(tag)
    await session.flush()
    return True
