"""Integration tests for the Calculation CRUD (BREAD) API endpoints.

Requires a live PostgreSQL database.
"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.models import User, Calculation
from app.security import hash_password
from fastapi_app import app

# ── Test database setup ────────────────────────────────────────────────────────

TEST_DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/fastapi_db",
)

test_engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def _drop_all_tables(engine):
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS calculations CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
        conn.commit()


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    _drop_all_tables(test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    _drop_all_tables(test_engine)


@pytest.fixture()
def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def test_user(db_session):
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("password123")
    )
    db_session.add(user)
    db_session.commit()
    return user


# ── API-level integration tests ───────────────────────────────────────────────

class TestCalculationAPI:
    def test_add_calculation(self, client, test_user):
        resp = client.post("/calculations", json={
            "a": 10.0,
            "b": 5.0,
            "type": "add",
            "user_id": test_user.id
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["result"] == 15.0
        assert data["user_id"] == test_user.id
        assert "id" in data

    def test_browse_calculations(self, client, test_user):
        # Add two calculations
        client.post("/calculations", json={"a": 1, "b": 2, "type": "add"})
        client.post("/calculations", json={"a": 3, "b": 4, "type": "multiply"})
        
        resp = client.get("/calculations")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 2

    def test_read_calculation(self, client):
        create_resp = client.post("/calculations", json={"a": 10, "b": 2, "type": "divide"})
        calc_id = create_resp.json()["id"]
        
        resp = client.get(f"/calculations/{calc_id}")
        assert resp.status_code == 200
        assert resp.json()["result"] == 5.0

    def test_edit_calculation(self, client):
        create_resp = client.post("/calculations", json={"a": 10, "b": 2, "type": "add"})
        calc_id = create_resp.json()["id"]
        
        resp = client.put(f"/calculations/{calc_id}", json={
            "a": 20,
            "type": "multiply"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["result"] == 40.0 # 20 * 2
        assert data["type"] == "multiply"

    def test_delete_calculation(self, client):
        create_resp = client.post("/calculations", json={"a": 10, "b": 2, "type": "add"})
        calc_id = create_resp.json()["id"]
        
        resp = client.delete(f"/calculations/{calc_id}")
        assert resp.status_code == 204
        
        get_resp = client.get(f"/calculations/{calc_id}")
        assert get_resp.status_code == 404

    def test_invalid_calculation_type(self, client):
        resp = client.post("/calculations", json={
            "a": 10,
            "b": 2,
            "type": "invalid"
        })
        assert resp.status_code == 422 # Pydantic validation error

    def test_divide_by_zero_error(self, client):
        resp = client.post("/calculations", json={
            "a": 10,
            "b": 0,
            "type": "divide"
        })
        assert resp.status_code == 422 # Caught by Pydantic validator in schema
