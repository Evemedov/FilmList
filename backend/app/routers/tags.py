"""
Tag API endpoints.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.tag import create_tag, delete_tag, get_tag, get_tags
from app.database import get_session
from app.schemas.tag import TagCreate, TagRead

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=list[TagRead])
async def list_tags(session: AsyncSession = Depends(get_session)):
    """Return all tags."""
    return await get_tags(session)


@router.post("", response_model=TagRead, status_code=status.HTTP_201_CREATED)
async def create_new_tag(
    body: TagCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new tag."""
    tag = await create_tag(session, name=body.name)
    await session.commit()
    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_tag(
    tag_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Delete a tag by ID."""
    deleted = await delete_tag(session, tag_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Tag not found")
    await session.commit()
