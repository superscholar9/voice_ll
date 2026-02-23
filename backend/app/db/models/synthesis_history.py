"""Synthesis history database model."""
from datetime import datetime
from typing import Optional
import uuid
from sqlalchemy import String, Float, Text, DateTime, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class SynthesisHistory(Base):
    """Model for tracking synthesis job history."""

    __tablename__ = "synthesis_history"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    job_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20), nullable=False
    )

    input_text: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    language: Mapped[str] = mapped_column(
        String(10), nullable=False
    )

    speed: Mapped[float] = mapped_column(
        Float, nullable=False
    )

    temperature: Mapped[float] = mapped_column(
        Float, nullable=False
    )

    duration_seconds: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
