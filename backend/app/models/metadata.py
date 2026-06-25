"""
API-fetched metadata models: Genre (many-to-many) and Screenshot (one-to-many).
"""

import uuid

from typing import TYPE_CHECKING
from sqlalchemy import Column, ForeignKey, SmallInteger, String, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.media import Media

# ── Association table (media ↔ genre) ───────────────────────────────────

media_genres = Table(
    "media_genres",
    Base.metadata,
    Column(
        "media_id",
        UUID(as_uuid=True),
        ForeignKey("media.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "genre_id",
        UUID(as_uuid=True),
        ForeignKey("genres.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


# ── Genre model ─────────────────────────────────────────────────────────


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    # ── Relationships ───────────────────────────────────────────────────
    media_items: Mapped[list["Media"]] = relationship(  # noqa: F821
        secondary=media_genres,
        back_populates="genres",
        lazy="raise",
    )

    def __repr__(self) -> str:
        return f"<Genre {self.name!r}>"


# ── Screenshot model ────────────────────────────────────────────────────


class Screenshot(Base):
    __tablename__ = "screenshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    media_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("media.id", ondelete="CASCADE"), nullable=False
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0)

    # ── Relationships ───────────────────────────────────────────────────
    media: Mapped["Media"] = relationship(back_populates="screenshots")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Screenshot {self.url[:60]}>"
