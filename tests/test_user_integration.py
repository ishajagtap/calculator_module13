"""Integration tests for the User model and /users API endpoints.

These tests require a real PostgreSQL database.  The DATABASE_URL environment
variable must point to a live Postgres instance (set automatically in GitHub
Actions via the postgres service container).

Run locally (with docker-compose db running):
    DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fastapi_db \
        pytest tests/test_user_integration.py -v
"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.models import User
from app.security import hash_password, verify_password
from fastapi_app import app

# ── Test database setup ────────────────────────────────────────────────────────

TEST_DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/fastapi_db",
)

test_engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def _drop_all_tables(engine):
    """Drop users (and dependent tables) using CASCADE to avoid FK conflicts."""
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS calculations CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
        conn.commit()


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Drop and recreate tables before tests; clean up afterward."""
    _drop_all_tables(test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    _drop_all_tables(test_engine)


@pytest.fixture()
def db_session():
    """Provide a clean database session; rolls back after each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    """FastAPI test client wired to the rollback session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Model-level integration tests ─────────────────────────────────────────────

class TestUserModel:
    def test_create_user_in_db(self, db_session):
        user = User(
            username="alice",
            email="alice@example.com",
            password_hash=hash_password("secret123"),
        )
        db_session.add(user)
        db_session.flush()
        assert user.id is not None
        assert user.created_at is not None

    def test_password_stored_as_hash_not_plain(self, db_session):
        plain = "plainpassword"
        user = User(
            username="bob",
            email="bob@example.com",
            password_hash=hash_password(plain),
        )
        db_session.add(user)
        db_session.flush()
        assert user.password_hash != plain

    def test_verify_stored_hash(self, db_session):
        plain = "verifyMe99"
        user = User(
            username="carol",
            email="carol@example.com",
            password_hash=hash_password(plain),
        )
        db_session.add(user)
        db_session.flush()
        assert verify_password(plain, user.password_hash) is True
        assert verify_password("wrongpass", user.password_hash) is False

    def test_duplicate_username_raises(self, db_session):
        from sqlalchemy.exc import IntegrityError
        db_session.add(User(username="dave", email="dave@example.com", password_hash=hash_password("pw1234")))
        db_session.flush()
        db_session.add(User(username="dave", email="dave2@example.com", password_hash=hash_password("pw1234")))
        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_duplicate_email_raises(self, db_session):
        from sqlalchemy.exc import IntegrityError
        db_session.add(User(username="eve", email="shared@example.com", password_hash=hash_password("pw1234")))
        db_session.flush()
        db_session.add(User(username="frank", email="shared@example.com", password_hash=hash_password("pw1234")))
        with pytest.raises(IntegrityError):
            db_session.flush()


# ── API-level integration tests ───────────────────────────────────────────────

class TestUserAPI:
    def test_create_user_returns_201(self, client):
        resp = client.post("/users/register", json={
            "username": "grace",
            "email": "grace@example.com",
            "password": "secret123",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "grace"
        assert data["email"] == "grace@example.com"
        assert "id" in data
        assert "created_at" in data

    def test_create_user_does_not_return_password(self, client):
        resp = client.post("/users/register", json={
            "username": "henry",
            "email": "henry@example.com",
            "password": "secret123",
        })
        assert resp.status_code == 201
        assert "password" not in resp.json()
        assert "password_hash" not in resp.json()

    def test_duplicate_username_returns_400(self, client):
        payload = {"username": "irene", "email": "irene@example.com", "password": "secret123"}
        client.post("/users/register", json=payload)
        resp = client.post("/users/register", json={**payload, "email": "irene2@example.com"})
        assert resp.status_code == 400

    def test_duplicate_email_returns_400(self, client):
        payload = {"username": "jack", "email": "jack@example.com", "password": "secret123"}
        client.post("/users/register", json=payload)
        resp = client.post("/users/register", json={**payload, "username": "jack2"})
        assert resp.status_code == 400

    def test_invalid_email_returns_422(self, client):
        resp = client.post("/users/register", json={
            "username": "kate",
            "email": "not-valid-email",
            "password": "secret123",
        })
        assert resp.status_code == 422

    def test_get_user_by_id(self, client):
        create_resp = client.post("/users/register", json={
            "username": "liam",
            "email": "liam@example.com",
            "password": "secret123",
        })
        user_id = create_resp.json()["id"]
        resp = client.get(f"/users/{user_id}")
        assert resp.status_code == 200
        assert resp.json()["username"] == "liam"

    def test_get_nonexistent_user_returns_404(self, client):
        resp = client.get("/users/999999")
        assert resp.status_code == 404

    def test_get_user_does_not_return_password(self, client):
        create_resp = client.post("/users/register", json={
            "username": "mia",
            "email": "mia@example.com",
            "password": "secret123",
        })
        user_id = create_resp.json()["id"]
        resp = client.get(f"/users/{user_id}")
        assert "password" not in resp.json()
        assert "password_hash" not in resp.json()

    def test_login_success(self, client):
        # Register first
        client.post("/users/register", json={
            "username": "oscar",
            "email": "oscar@example.com",
            "password": "password123"
        })
        # Login
        resp = client.post("/users/login", json={
            "username": "oscar",
            "password": "password123"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Login successful"
        assert data["username"] == "oscar"

    def test_login_invalid_password(self, client):
        client.post("/users/register", json={
            "username": "papa",
            "email": "papa@example.com",
            "password": "password123"
        })
        resp = client.post("/users/login", json={
            "username": "papa",
            "password": "wrongpassword"
        })
        assert resp.status_code == 401
        assert "Invalid" in resp.json()["detail"]

    def test_login_nonexistent_user(self, client):
        resp = client.post("/users/login", json={
            "username": "nobody",
            "password": "password123"
        })
        assert resp.status_code == 401
