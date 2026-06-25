"""
Tag model and the media ↔ tag many-to-many association table.
"""

import uuid

from typing import TYPE_CHECKING
from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.media import Media

# ── Association table ───────────────────────────────────────────────────

media_tags = Table(
    "media_tags",
    Base.metadata,
    Column(
        "media_id",
        UUID(as_uuid=True),
        ForeignKey("media.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


# ── Tag model ───────────────────────────────────────────────────────────


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    # ── Relationships ───────────────────────────────────────────────────
    media_items: Mapped[list["Media"]] = relationship(  # noqa: F821
        secondary=media_tags,
        back_populates="tags",
        lazy="raise",
    )

    def __repr__(self) -> str:
        return f"<Tag {self.name!r}>"
