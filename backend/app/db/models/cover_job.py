"""Cover job database model."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CoverJob(Base):
    """Model for asynchronous AI cover generation jobs."""

    __tablename__ = "cover_jobs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="queued", index=True)
    stage: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    task_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    model_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    pitch_shift: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    input_voice_path: Mapped[str] = mapped_column(Text, nullable=False)
    input_song_path: Mapped[str] = mapped_column(Text, nullable=False)

    output_vocal_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output_inst_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output_mix_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
