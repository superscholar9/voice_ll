"""User database model."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from app.db.base import Base


class User(SQLAlchemyBaseUserTableUUID, Base):
    """User model with FastAPI Users integration."""
    
    __tablename__ = "users"
    
    # Additional fields beyond FastAPI Users defaults
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
