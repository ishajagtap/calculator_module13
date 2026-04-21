"""Security utilities for password hashing and JWT token generation."""
import os
from datetime import datetime, timedelta
import bcrypt
from jose import jwt

# ── JWT Configuration ─────────────────────────────────────────────────────────
# In a real app, these should be loaded from environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "7b9e1d8f3c5a4b2e1f0d9c8b7a6f5e4d")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def hash_password(plain_password: str) -> str:
    """Return a bcrypt hash of the plain-text password."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if plain_password matches the stored hash, False otherwise."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Generate a JWT access token with an expiration time."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
