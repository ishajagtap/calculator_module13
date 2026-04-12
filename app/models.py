"""SQLAlchemy ORM models."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    """User account with hashed password storage."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
