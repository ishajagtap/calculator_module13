"""Pydantic schemas for request validation and response serialization."""
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator


class UserCreate(BaseModel):
    """Schema for creating a new user — includes plain-text password."""

    username: str
    email: EmailStr
    password: str

    @field_validator("username")
    @classmethod
    def username_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("username must not be blank")
        return v

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("password must be at least 6 characters")
        return v


class UserRead(BaseModel):
    """Schema for returning user data — password_hash is intentionally omitted."""

    id: int
    username: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}
