"""SQLAlchemy ORM models."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
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

    calculations = relationship("Calculation", back_populates="user", cascade="all, delete-orphan")


class Calculation(Base):
    """Stores a single arithmetic calculation (Add, Sub, Multiply, Divide)."""

    __tablename__ = "calculations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    a = Column(Float, nullable=False)
    b = Column(Float, nullable=False)
    type = Column(String(20), nullable=False)
    result = Column(Float, nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    user = relationship("User", back_populates="calculations")
