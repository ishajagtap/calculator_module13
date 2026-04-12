"""Unit tests for password hashing and Pydantic user schemas.

These tests do NOT require a database — they run purely in-memory.
"""
import pytest
from pydantic import ValidationError

from app.security import hash_password, verify_password
from app.schemas import UserCreate, UserRead
from datetime import datetime


# ── Password Hashing ───────────────────────────────────────────────────────────

class TestHashPassword:
    def test_returns_string(self):
        result = hash_password("secret123")
        assert isinstance(result, str)

    def test_hash_differs_from_plain(self):
        plain = "mysecretpassword"
        assert hash_password(plain) != plain

    def test_same_password_produces_different_hashes(self):
        """bcrypt uses a random salt — two hashes of the same password differ."""
        h1 = hash_password("password")
        h2 = hash_password("password")
        assert h1 != h2

    def test_hash_starts_with_bcrypt_prefix(self):
        h = hash_password("anypassword")
        assert h.startswith("$2b$") or h.startswith("$2a$")


class TestVerifyPassword:
    def test_correct_password_returns_true(self):
        plain = "correct_horse"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_wrong_password_returns_false(self):
        hashed = hash_password("correct_horse")
        assert verify_password("wrong_horse", hashed) is False

    def test_empty_string_does_not_match_non_empty_hash(self):
        hashed = hash_password("notempty")
        assert verify_password("", hashed) is False

    def test_verify_is_consistent_across_calls(self):
        plain = "stable_password"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True
        assert verify_password(plain, hashed) is True


# ── UserCreate Schema ──────────────────────────────────────────────────────────

class TestUserCreateSchema:
    def test_valid_data_passes(self):
        user = UserCreate(username="alice", email="alice@example.com", password="secret123")
        assert user.username == "alice"
        assert user.email == "alice@example.com"
        assert user.password == "secret123"

    def test_invalid_email_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(username="bob", email="not-an-email", password="secret123")
        assert "email" in str(exc_info.value).lower()

    def test_missing_username_raises(self):
        with pytest.raises(ValidationError):
            UserCreate(email="alice@example.com", password="secret123")

    def test_missing_email_raises(self):
        with pytest.raises(ValidationError):
            UserCreate(username="alice", password="secret123")

    def test_missing_password_raises(self):
        with pytest.raises(ValidationError):
            UserCreate(username="alice", email="alice@example.com")

    def test_blank_username_raises(self):
        with pytest.raises(ValidationError):
            UserCreate(username="   ", email="alice@example.com", password="secret123")

    def test_short_password_raises(self):
        with pytest.raises(ValidationError):
            UserCreate(username="alice", email="alice@example.com", password="abc")

    def test_password_exactly_six_chars_passes(self):
        user = UserCreate(username="alice", email="alice@example.com", password="123456")
        assert user.password == "123456"


# ── UserRead Schema ────────────────────────────────────────────────────────────

class TestUserReadSchema:
    def _make_user_dict(self, **overrides):
        base = {
            "id": 1,
            "username": "alice",
            "email": "alice@example.com",
            "created_at": datetime(2024, 1, 1, 12, 0, 0),
        }
        base.update(overrides)
        return base

    def test_valid_data_passes(self):
        user = UserRead(**self._make_user_dict())
        assert user.id == 1
        assert user.username == "alice"
        assert user.email == "alice@example.com"

    def test_password_hash_not_in_schema(self):
        """UserRead must not expose password_hash."""
        user = UserRead(**self._make_user_dict())
        assert not hasattr(user, "password_hash")

    def test_created_at_is_datetime(self):
        user = UserRead(**self._make_user_dict())
        assert isinstance(user.created_at, datetime)

    def test_missing_id_raises(self):
        data = self._make_user_dict()
        del data["id"]
        with pytest.raises(ValidationError):
            UserRead(**data)
