"""Integration tests for the Calculation model.

Requires a live PostgreSQL database.  DATABASE_URL is set automatically
inside GitHub Actions.  To run locally (with docker-compose):

    DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fastapi_db \
        pytest tests/test_calculation_integration.py -v
"""
import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from pydantic import ValidationError

from app.database import Base
from app.models import User, Calculation
from app.schemas import CalculationCreate, CalculationType
from app.calculation_factory import CalculationFactory
from app.security import hash_password
from app.exceptions import DivisionByZeroError

# ── Database setup ─────────────────────────────────────────────────────────────

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
    """Recreate all tables fresh before the module runs."""
    _drop_all_tables(test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    _drop_all_tables(test_engine)


@pytest.fixture()
def db_session():
    """Transactional session that rolls back after every test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def saved_user(db_session):
    """A persisted User to attach calculations to."""
    user = User(
        username="calc_owner",
        email="calc_owner@example.com",
        password_hash=hash_password("password123"),
    )
    db_session.add(user)
    db_session.flush()
    return user


# ── Helper ─────────────────────────────────────────────────────────────────────

def _make_calc(db_session, *, a, b, calc_type, user_id=None):
    """Validate via Pydantic, compute via factory, persist via SQLAlchemy."""
    calc_in = CalculationCreate(a=a, b=b, type=calc_type, user_id=user_id)
    result = CalculationFactory.compute(calc_in.type, calc_in.a, calc_in.b)
    record = Calculation(
        a=calc_in.a,
        b=calc_in.b,
        type=calc_in.type.value,
        result=result,
        user_id=calc_in.user_id,
    )
    db_session.add(record)
    db_session.flush()
    return record


# ── Model-level tests ──────────────────────────────────────────────────────────

class TestCalculationModel:
    def test_create_add_record(self, db_session):
        record = _make_calc(db_session, a=3, b=4, calc_type="add")
        assert record.id is not None
        assert record.result == 7.0
        assert record.type == "add"

    def test_create_sub_record(self, db_session):
        record = _make_calc(db_session, a=10, b=3, calc_type="sub")
        assert record.result == 7.0

    def test_create_multiply_record(self, db_session):
        record = _make_calc(db_session, a=6, b=7, calc_type="multiply")
        assert record.result == 42.0

    def test_create_divide_record(self, db_session):
        record = _make_calc(db_session, a=15, b=3, calc_type="divide")
        assert record.result == 5.0

    def test_created_at_is_set(self, db_session):
        record = _make_calc(db_session, a=1, b=1, calc_type="add")
        assert record.created_at is not None

    def test_user_id_nullable(self, db_session):
        record = _make_calc(db_session, a=2, b=2, calc_type="multiply")
        assert record.user_id is None

    def test_user_id_foreign_key(self, db_session, saved_user):
        record = _make_calc(
            db_session, a=8, b=4, calc_type="divide", user_id=saved_user.id
        )
        assert record.user_id == saved_user.id

    def test_result_stored_correctly(self, db_session):
        record = _make_calc(db_session, a=7, b=2, calc_type="divide")
        assert record.result == 3.5

    def test_negative_operands_stored(self, db_session):
        record = _make_calc(db_session, a=-5, b=-3, calc_type="add")
        assert record.result == -8.0

    def test_float_operands_stored(self, db_session):
        record = _make_calc(db_session, a=1.5, b=2.5, calc_type="add")
        assert record.result == 4.0

    def test_multiple_calculations_same_user(self, db_session, saved_user):
        r1 = _make_calc(db_session, a=1, b=2, calc_type="add", user_id=saved_user.id)
        r2 = _make_calc(db_session, a=3, b=4, calc_type="multiply", user_id=saved_user.id)
        assert r1.id != r2.id
        assert r1.user_id == r2.user_id == saved_user.id

    def test_querying_by_type(self, db_session):
        _make_calc(db_session, a=1, b=2, calc_type="add")
        _make_calc(db_session, a=3, b=4, calc_type="multiply")
        adds = db_session.query(Calculation).filter(Calculation.type == "add").all()
        assert all(c.type == "add" for c in adds)

    def test_querying_by_user(self, db_session, saved_user):
        _make_calc(db_session, a=9, b=3, calc_type="divide", user_id=saved_user.id)
        results = (
            db_session.query(Calculation)
            .filter(Calculation.user_id == saved_user.id)
            .all()
        )
        assert len(results) >= 1


# ── Validation / error-case tests ──────────────────────────────────────────────

class TestCalculationErrorCases:
    def test_schema_rejects_divide_by_zero(self):
        with pytest.raises(ValidationError) as exc_info:
            CalculationCreate(a=5, b=0, type="divide")
        assert "zero" in str(exc_info.value).lower()

    def test_schema_rejects_invalid_type(self):
        with pytest.raises(ValidationError):
            CalculationCreate(a=1, b=2, type="power")

    def test_schema_rejects_missing_a(self):
        with pytest.raises(ValidationError):
            CalculationCreate(b=2, type="add")

    def test_schema_rejects_missing_b(self):
        with pytest.raises(ValidationError):
            CalculationCreate(a=1, type="add")

    def test_factory_raises_on_divide_by_zero(self):
        with pytest.raises(DivisionByZeroError):
            CalculationFactory.compute(CalculationType.divide, 10, 0)

    def test_invalid_fk_user_raises(self, db_session):
        """Inserting a calculation with a non-existent user_id should fail."""
        record = Calculation(a=1, b=2, type="add", result=3, user_id=999999)
        db_session.add(record)
        with pytest.raises(Exception):
            db_session.flush()
