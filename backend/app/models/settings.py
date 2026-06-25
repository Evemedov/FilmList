"""
Application settings model – singleton (single-row) table.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AppSettings(Base):
    """Single-row table storing server-side application settings."""

    __tablename__ = "app_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tmdb_api_key: Mapped[str | None] = mapped_column(String(256), nullable=True)
    theme: Mapped[str] = mapped_column(String(10), nullable=False, default="DARK")

    # ── Timestamps ──────────────────────────────────────────────────────
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    def __repr__(self) -> str:
        return f"<AppSettings theme={self.theme!r}>"
