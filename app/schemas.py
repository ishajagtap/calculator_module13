"""Pydantic schemas for request validation and response serialization."""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator, model_validator


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


# ── Calculation Schemas ────────────────────────────────────────────────────────

class CalculationType(str, Enum):
    """Supported arithmetic operation types."""
    add = "add"
    sub = "sub"
    multiply = "multiply"
    divide = "divide"


class CalculationCreate(BaseModel):
    """Schema for creating a new calculation — validated before persisting."""

    a: float
    b: float
    type: CalculationType
    user_id: Optional[int] = None

    @model_validator(mode="after")
    def no_divide_by_zero(self) -> "CalculationCreate":
        if self.type == CalculationType.divide and self.b == 0:
            raise ValueError("b must not be zero when type is 'divide'")
        return self


class CalculationRead(BaseModel):
    """Schema for returning a stored calculation — includes computed result."""

    id: int
    a: float
    b: float
    type: str
    result: float
    user_id: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    """Schema for user login credentials."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for JWT response."""
    access_token: str
    token_type: str


class CalculationUpdate(BaseModel):
    """Schema for updating an existing calculation — all fields are optional."""
    a: Optional[float] = None
    b: Optional[float] = None
    type: Optional[CalculationType] = None
    user_id: Optional[int] = None
